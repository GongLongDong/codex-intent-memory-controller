# Codex Intent Memory Controller

This repository contains a Codex skill for intent-state memory, goal-node tracking, minimal expansion, and execution-boundary control.

## Install

Install with Codex's skill installer from this GitHub repository:

```bash
install-skill-from-github --repo GongLongDong/codex-intent-memory-controller --path skills/intent-memory-controller
```

If you use Codex's built-in `$skill-installer`, provide:

```text
repo: GongLongDong/codex-intent-memory-controller
path: skills/intent-memory-controller
```

After installing, restart Codex to pick up the skill if your Codex surface does not reload skills automatically.

## Optional Runtime Hooks

The skill also includes a hook controller for realtime injection:

```text
skills/intent-memory-controller/scripts/intent_memory_hook.py
```

It can be connected to Codex lifecycle hooks:

```text
UserPromptSubmit  -> assess intent state and inject minimal rules
PreToolUse        -> prevent implementation without explicit authorization
PreCompact        -> protect high-value intent memory
PostCompact       -> restore current-node awareness
Stop              -> update local turn memory
```

Use the template:

```text
hooks/hooks.example.json
```

Copy it into an active Codex hook config location and replace `<CODEX_HOME>` with your Codex home directory. Runtime memory is stored locally at:

```text
$CODEX_HOME/intent-memory-controller/intent-graph.json
```

This runtime file is private local state and should not be committed.

## Skill

Path:

```text
skills/intent-memory-controller
```

Use it explicitly with:

```text
$intent-memory-controller
```

The skill is designed for long, complex user-AI alignment conversations where Codex must distinguish discussion, planning, and implementation.
