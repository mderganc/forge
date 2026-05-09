# Forge + Claude Code integration (v1)

This is a **command pack** for Claude Code. Commands are **Markdown files with YAML frontmatter** (`---` … `---`) and a **body that instructs Claude** what to do (same shape as `integrations/cursor-plugin/commands/`). Invalid YAML-only stubs without frontmatter delimiters are **not** loaded as slash commands.

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

### Default location (via `forge install`)

By default, `forge install --claude` copies this folder to:

- Windows: `%USERPROFILE%\.claude\commands\forge\`
- macOS/Linux/WSL: `~/.claude/commands/forge/`

Override with `forge install --claude-dir <path>`.

Restart Claude Code after installing so `/help` picks up new commands.

## Commands

Definitions live in `integrations/claude/commands/` as `forge-<subcommand>.md`. They align with `integrations/spec/commands.json`:

| Slash command (frontmatter `name`) | Runs |
| --- | --- |
| `forge:develop` | `forge develop …` |
| `forge:evaluate` | `forge evaluate …` |
| `forge:plan` | `forge plan …` |
| `forge:implement` | `forge implement …` |
| `forge:code-review` | `forge code-review …` |
| `forge:test` | `forge test …` |
| `forge:diagnose` | `forge diagnose …` |
| `forge:resume` | `forge resume …` |
| `forge:status` | `forge status …` |
| `forge:doctor` | `forge doctor …` |

How Claude surfaces these depends on version/UI (often under a `forge` namespace from the install directory). If a command does not appear, confirm files are under `~/.claude/commands/forge/` and each file begins with `---` frontmatter plus a non-empty markdown body.
