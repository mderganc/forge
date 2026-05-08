# Forge integrations

This folder contains wrapper artifacts for editor/agent environments that call the global `forge` CLI.

## Prerequisite (all environments)

Install the CLI once:

```bash
pipx install forge-next
```

Verify:

```bash
forge doctor
```

## Contents

- `spec/commands.json`: single source of truth for supported commands and examples.
- `cursor-plugin/`: Cursor plugin bundle (`forge:*` commands).
- `claude/`: Claude Code command pack (v1).
- `codex/`: Codex skill pack (v1).

