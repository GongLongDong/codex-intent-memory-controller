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
