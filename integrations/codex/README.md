# Forge + Codex integration

This is a **skill pack** for Codex-style environments. Skills are thin wrappers that run the global **`forge` CLI**. Layout follows OpenAI Codex agent skills: each skill is a directory **`forge-<cli-subcommand>/`** containing **`SKILL.md`** with **`name`** and **`description`** in YAML frontmatter.

The set of skills matches **[`integrations/spec/commands.json`](../spec/commands.json)** (same coverage as the Cursor plugin and Claude command pack).

## Prerequisite

Install the CLI:

```bash
pipx install forge-next
```

Verify:

```bash
forge doctor
```

## Skills (installed)

| Skill folder | CLI entry |
|--------------|-----------|
| `forge-develop` | `forge develop` |
| `forge-plan` | `forge plan` |
| `forge-evaluate` | `forge evaluate` |
| `forge-implement` | `forge implement` |
| `forge-code-review` | `forge code-review` |
| `forge-test` | `forge test` |
| `forge-diagnose` | `forge diagnose` |
| `forge-resume` | `forge resume` |
| `forge-status` | `forge status` |
| `forge-doctor` | `forge doctor` |

## Default install location (via `forge install`)

By default, `forge install --codex` installs to:

- Windows: `%USERPROFILE%\.codex\skills\forge\`
- macOS/Linux/WSL: `~/.codex/skills/forge/`

Override with `forge install --codex-dir <path>`.

Restart Codex after installing so skills appear in the picker.
