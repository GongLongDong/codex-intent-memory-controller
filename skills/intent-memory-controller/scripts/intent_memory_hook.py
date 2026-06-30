#!/usr/bin/env python3
"""Codex hook controller for intent memory and execution boundaries.

The script is intentionally conservative. It injects small, state-specific
developer context and only blocks obvious implementation tool calls when the
latest user prompt did not contain implementation authorization.
"""

from __future__ import annotations

import json
import locale
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_DOUBT = "doubt"
STATE_TENDENCY = "tendency"
STATE_CORE = "core-clear"
STATE_DETAIL = "detail-clear"

IMPLEMENTATION_TERMS = [
    "实施",
    "执行",
    "开始实现",
    "写入",
    "修改",
    "运行",
    "创建",
    "生成",
    "初始化",
    "安装",
    "删除",
    "提交",
    "implement",
    "execute",
    "write file",
    "modify",
    "run",
    "create",
    "generate",
    "initialize",
    "install",
    "delete",
    "commit",
]

GENERIC_DO_TERMS = ["做", "搞", "弄", "do it", "make it"]

TENDENCY_TERMS = [
    "想",
    "感觉",
    "可能",
    "考虑",
    "倾向",
    "或许",
    "大概",
    "觉得",
    "maybe",
    "probably",
    "consider",
]

CORE_TERMS = [
    "我要",
    "我需要",
    "目标",
    "希望",
    "设计",
    "方案",
    "体系",
    "总结",
    "规则",
    "实现",
    "需要",
    "want",
    "need",
    "goal",
    "design",
    "plan",
]

DETAIL_MARKERS = [
    "：",
    ":",
    "，",
    ",",
    "1.",
    "2.",
    "3.",
    "- ",
    "比如",
    "例如",
    "路径",
    "文件",
    "数量",
    "范围",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def data_dir() -> Path:
    return codex_home() / "intent-memory-controller"


def memory_path() -> Path:
    return data_dir() / "intent-graph.json"


def default_memory() -> dict[str, Any]:
    return {
        "version": 1,
        "current_node": None,
        "history_path": [],
        "nodes": {},
        "turns": [],
        "last_assessment": None,
        "disabled_path_trace": [],
    }


def load_memory() -> dict[str, Any]:
    path = memory_path()
    if not path.exists():
        return default_memory()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        base = default_memory()
        base.update(data if isinstance(data, dict) else {})
        return base
    except Exception:
        return default_memory()


def save_memory(memory: dict[str, Any]) -> None:
    data_dir().mkdir(parents=True, exist_ok=True)
    tmp = memory_path().with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)
    tmp.replace(memory_path())


def read_stdin_json() -> dict[str, Any]:
    raw_bytes = sys.stdin.buffer.read()
    if not raw_bytes.strip():
        return {}
    for encoding in ("utf-8-sig", locale.getpreferredencoding(False), "utf-16", "gb18030"):
        try:
            raw = raw_bytes.decode(encoding)
            break
        except Exception:
            raw = ""
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def first_text(data: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def extract_prompt(data: dict[str, Any]) -> str:
    prompt = first_text(
        data,
        [
            "prompt",
            "user_prompt",
            "userPrompt",
            "message",
            "input",
            "text",
        ],
    )
    if prompt:
        return prompt
    payload = data.get("payload")
    if isinstance(payload, dict):
        return first_text(payload, ["prompt", "message", "input", "text"])
    return ""


def contains_any(text: str, terms: list[str]) -> bool:
    low = text.lower()
    return any(term.lower() in low for term in terms)


def is_short_fragment(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    if len(stripped) <= 8 and not re.search(r"[？?。.!！]", stripped):
        return True
    return False


def assess_prompt(prompt: str, memory: dict[str, Any]) -> dict[str, Any]:
    implementation = contains_any(prompt, IMPLEMENTATION_TERMS)
    generic_do = contains_any(prompt, GENERIC_DO_TERMS)
    has_tendency = contains_any(prompt, TENDENCY_TERMS)
    has_core = contains_any(prompt, CORE_TERMS)
    has_detail = sum(1 for marker in DETAIL_MARKERS if marker in prompt) >= 2 or len(prompt) > 80

    if is_short_fragment(prompt) and not has_core and not implementation:
        state = STATE_DOUBT
    elif has_detail and (has_core or implementation):
        state = STATE_DETAIL
    elif has_core or implementation:
        state = STATE_CORE
    elif has_tendency:
        state = STATE_TENDENCY
    else:
        state = STATE_DOUBT

    current_node = memory.get("current_node")
    if state in (STATE_CORE, STATE_DETAIL):
        node_label = infer_node_label(prompt)
        if node_label:
            current_node = ensure_node(memory, node_label, state)

    return {
        "state": state,
        "implementation_confirmed": implementation,
        "generic_do_only": generic_do and not implementation,
        "current_node": current_node,
        "prompt_excerpt": prompt[:200],
        "time": now_iso(),
    }


def infer_node_label(prompt: str) -> str | None:
    text = re.sub(r"\s+", " ", prompt).strip()
    if not text:
        return None
    text = re.sub(r"^(请|帮我|你|现在|下面|接下来)[，,\s]*", "", text)
    return text[:40]


def ensure_node(memory: dict[str, Any], label: str, state: str) -> str:
    nodes = memory.setdefault("nodes", {})
    for node_id, node in nodes.items():
        if node.get("label") == label:
            node["state"] = state
            node["last_seen"] = now_iso()
            node["active"] = True
            return node_id

    node_id = f"n{len(nodes) + 1:04d}"
    parent = memory.get("current_node")
    nodes[node_id] = {
        "id": node_id,
        "label": label,
        "parent": parent,
        "state": state,
        "weight": 1,
        "active": True,
        "confirmation": "medium" if state == STATE_DETAIL else "low",
        "implementable": "unknown",
        "created": now_iso(),
        "last_seen": now_iso(),
    }
    memory["current_node"] = node_id
    path = memory.setdefault("history_path", [])
    path.append(node_id)
    memory["history_path"] = path[-50:]
    return node_id


def node_path(memory: dict[str, Any], node_id: str | None) -> str:
    if not node_id:
        return ""
    nodes = memory.get("nodes", {})
    parts: list[str] = []
    seen: set[str] = set()
    cur = node_id
    while cur and cur not in seen:
        seen.add(cur)
        node = nodes.get(cur)
        if not node:
            break
        parts.append(str(node.get("label") or cur))
        cur = node.get("parent")
    return " > ".join(reversed(parts[-4:]))


def context_for_assessment(assessment: dict[str, Any], memory: dict[str, Any]) -> str:
    state = assessment["state"]
    path = node_path(memory, assessment.get("current_node"))
    lines = ["Intent Memory Controller active."]
    if path and state in (STATE_CORE, STATE_DETAIL):
        lines.append(f"Current discussion goal path: {path}")

    if state == STATE_DOUBT:
        lines.append("State strategy: doubt/listening. Do not recommend, expand, list directions, or classify intent. Ask at most one short non-leading question only if scene memory strongly supports it.")
    elif state == STATE_TENDENCY:
        lines.append("State strategy: tendency. Give at most 1-2 evidence-based guesses, never more than 3. Do not implement or enter implementation details. Keep a correction path open.")
    elif state == STATE_CORE:
        lines.append("State strategy: core-clear. First distinguish discussion/analysis/planning from implementation. Core clarity does not imply execution.")
    else:
        lines.append("State strategy: detail-clear. Assess whether details are enough for the current stage; do not demand exhaustive detail.")

    if assessment.get("generic_do_only"):
        lines.append('"Do" is generic continuation only: analysis/discussion/organization/planning. It is not implementation authorization.')
    if assessment.get("implementation_confirmed"):
        lines.append("Implementation language detected. Before acting, assess feasibility, missing information, user involvement, and proxy boundary. Continue under the confirmed node unless a boundary/risk/permission issue appears.")
    else:
        lines.append("No explicit implementation authorization detected. Do not modify files, run implementation commands, or create artifacts unless the user has clearly authorized that target.")

    return "\n".join(lines)


def common_output(additional_context: str | None = None, system_message: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"continue": True}
    if system_message:
        out["systemMessage"] = system_message
    if additional_context:
        out["hookSpecificOutput"] = {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional_context,
        }
    return out


def handle_user_prompt(data: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    prompt = extract_prompt(data)
    assessment = assess_prompt(prompt, memory)
    memory["last_assessment"] = assessment
    turns = memory.setdefault("turns", [])
    turns.append({"event": "UserPromptSubmit", **assessment})
    memory["turns"] = turns[-100:]
    save_memory(memory)
    return common_output(additional_context=context_for_assessment(assessment, memory))


def tool_is_implementation(tool_name: str, tool_input: Any) -> bool:
    if tool_name in {"apply_patch"}:
        return True
    if "apply_patch" in tool_name:
        return True
    if tool_name in {"Bash"}:
        command = ""
        if isinstance(tool_input, dict):
            command = str(tool_input.get("command") or tool_input.get("cmd") or "")
        destructive_or_write = [
            "rm ",
            "del ",
            "move ",
            "mv ",
            "copy ",
            "cp ",
            "git commit",
            "git push",
            "npm install",
            "pip install",
            "mkdir",
            "New-Item",
            "Set-Content",
            "Add-Content",
            "Out-File",
        ]
        return contains_any(command, destructive_or_write)
    return False


def handle_pre_tool_use(data: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    tool_name = str(data.get("tool_name") or data.get("toolName") or "")
    tool_input = data.get("tool_input") or data.get("toolInput") or {}
    assessment = memory.get("last_assessment") or {}
    authorized = bool(assessment.get("implementation_confirmed"))
    if tool_is_implementation(tool_name, tool_input) and not authorized:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Intent Memory Controller: implementation-like tool use blocked because the latest user prompt did not contain explicit implementation authorization. Continue discussion or ask for execution confirmation.",
            }
        }
    return common_output()


def handle_stop(data: dict[str, Any], memory: dict[str, Any]) -> dict[str, Any]:
    turns = memory.setdefault("turns", [])
    turns.append({"event": "Stop", "time": now_iso()})
    memory["turns"] = turns[-100:]
    save_memory(memory)
    return common_output()


def handle_compact(event: str, memory: dict[str, Any]) -> dict[str, Any]:
    current = memory.get("current_node")
    path = node_path(memory, current)
    if event == "PreCompact":
        msg = "Preserve active/high-weight intent nodes; do not preserve disabled node content except minimal path trace."
    else:
        msg = "After compaction, restore the current intent node and keep stale memory dormant unless relevant."
    if path:
        msg += f" Current discussion goal path: {path}."
    return common_output(system_message=msg)


def main() -> int:
    data = read_stdin_json()
    event = str(data.get("hook_event_name") or data.get("hookEventName") or (sys.argv[1] if len(sys.argv) > 1 else ""))
    memory = load_memory()

    if event == "UserPromptSubmit":
        out = handle_user_prompt(data, memory)
    elif event == "PreToolUse":
        out = handle_pre_tool_use(data, memory)
    elif event == "Stop":
        out = handle_stop(data, memory)
    elif event in {"PreCompact", "PostCompact"}:
        out = handle_compact(event, memory)
    else:
        out = common_output()

    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
