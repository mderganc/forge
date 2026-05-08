# Forge + Claude Code integration (v1)

This is a **command pack** for Claude Code-style environments. It provides thin wrapper commands that run the global `forge` CLI.

## Prerequisite

Install the CLI:

```bash
pipx install forge-next
```

Verify:

```bash
forge doctor
```

## Install

The exact install location/mechanism depends on your Claude Code environment.
This pack is intentionally simple: each command definition just runs `forge …`.

- Command definitions: `integrations/claude/commands/`

### Default install location (via `forge install`)

By default, `forge install --claude` installs to:

- Windows: `%USERPROFILE%\.claude\commands\forge\`
- macOS/Linux/WSL: `~/.claude/commands/forge/`

Override with `forge install --claude-dir <path>`.

## Commands

- `forge:evaluate` → `forge evaluate ...`
- `forge:plan` → `forge plan ...`
- `forge:status` → `forge status`
- `forge:resume` → `forge resume`

