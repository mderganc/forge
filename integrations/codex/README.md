# Forge + Codex integration (v1)

This is a **skill pack** for Codex-style environments. Skills are thin wrappers that run the global `forge` CLI.

## Prerequisite

Install the CLI:

```bash
pipx install forge-next
```

Verify:

```bash
forge doctor
```

## Skills

Skill definitions live in `integrations/codex/skills/` and invoke `forge ...`.

### Default install location (via `forge install`)

By default, `forge install --codex` installs to:

- Windows: `%USERPROFILE%\.codex\skills\forge\`
- macOS/Linux/WSL: `~/.codex/skills/forge/`

Override with `forge install --codex-dir <path>`.

