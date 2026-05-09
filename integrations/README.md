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

Layout for Cursor/Claude slash commands and Codex skills is enforced by `pytest tests/test_integration_install_layout.py` (matching files under `cursor-plugin/commands/` and `claude/commands/` to `spec/commands.json`, and Codex `SKILL.md` folders).

