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

### Graphify hooks (codebase map)

`forge install --claude` also merges **Graphify hooks** into `~/.claude/settings.json` (or re-run anytime):

```bash
forge claude-graphify
```

Hooks invoke **`/path/to/forge claude-graphify-hook <event>`** (absolute pipx `forge` binary written by `forge claude-graphify` — never bare `python -m forge_next` on `/usr/bin/python`).

- **SessionStart** — remind when `graphify-out/` exists
- **PreToolUse** — all tools (close unused sub-agents); **Grep**, **Glob**, **Read**, and search-like **Bash** also get Graphify context when indexed
- **UserPromptSubmit** — when the prompt mentions `forge:` / `$forge:`

After `pipx upgrade forge-next`, re-run `forge claude-graphify` and restart Claude Code.

Workflow slash commands include **Hard rule — Graphify**. Forge step output prints a **GRAPHIFY** block on every `--step` when an index is present.

See [`docs/graphify.md`](../../docs/graphify.md) for the full picture (Codex policy, `FORGE_SKIP_GRAPHIFY`, troubleshooting).

## Commands

Definitions live in `integrations/claude/commands/` as `<subcommand>.md` (for example `diagnose.md`, `code-review.md`). They align with [`integrations/spec/commands.json`](../spec/commands.json) and [README.md](../../README.md#commands-in-your-apps):

| Slash command (frontmatter `name`) | Runs |
| --- | --- |
| `forge:sketch` | `forge sketch …` |
| `forge:design` | `forge design …` |
| `forge:plan` | `forge plan …` |
| `forge:evaluate` | `forge evaluate …` |
| `forge:implement` | `forge implement …` |
| `forge:code-review` | `forge code-review …` |
| `forge:test` | `forge test …` |
| `forge:diagnose` | `forge diagnose …` |
| `forge:iterate` | `forge iterate …` |
| `forge:resume` | `forge resume …` |
| `forge:status` | `forge status …` |
| `forge:doctor` | `forge doctor …` |
| `forge:graphify` | `forge graphify …` |
| `forge:ship` | `forge ship …` |

How Claude surfaces these depends on version/UI (often under a `forge` namespace from the install directory). If a command does not appear, confirm files are under `~/.claude/commands/forge/` and each file begins with `---` frontmatter plus a non-empty markdown body.

**Aliases:** Claude does not load separate `/f:…` or bare `/diagnose` aliases from this pack; use the `forge:<subcommand>` id in frontmatter (same as Cursor’s `/forge:<subcommand>` intent). **`forge develop`** is a deprecated CLI alias for **`forge design`** only (not a separate slash command).
