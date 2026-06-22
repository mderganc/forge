# Graphify integration (optional)

Forge works without Graphify. When a repo has a knowledge graph (`graphify-out/` or `GRAPH_REPORT.md`), Forge **enforces** using it during workflow skills so agents read the map before raw search.

This document covers:

1. **Building the graph** (CLI, refresh, git hook)
2. **Takeover context** (`forge takeover`)
3. **Ship-time enforcement** (GRAPHIFY on `forge ship` only)
4. **Claude Code hooks** (`forge claude-graphify`)
5. **Codex policy** (`forge codex-agents`)
6. **CI / automation** (`FORGE_SKIP_GRAPHIFY`)

Canonical contract text: [`templates/graphify-contract.md`](../templates/graphify-contract.md).  
Policy source for Codex: [`forge_next/graphify_policy.py`](../forge_next/graphify_policy.py).

---

## 1. Build and refresh the graph

### Install Graphify

Install the Graphify tooling your project uses. If `graphify` is on `PATH`, Forge can invoke it during refresh.

Or set a full command line:

- **`FORGE_GRAPHIFY_COMMAND`** — shell command to rebuild the graph (POSIX split). When unset, Forge defaults to `graphify update .`.

### Refresh status file (per clone)

From the repository root (or `forge graphify refresh --repo <path>`):

```bash
forge graphify refresh              # background (default)
forge graphify refresh --foreground # wait in this process
forge graphify refresh --force      # spawn even when status looks fresh
```

Forge writes **`.codex/forge/state/graphify-status.json`** (fail-soft on errors). `forge takeover` reads this file and any `GRAPH_REPORT.md` it finds.

**Automatic background refresh** (when Graphify is on PATH and status is missing, stale, or behind `git HEAD`; ship also uses `--force` when an index exists):

| Trigger | Environment |
|---------|-------------|
| **Claude SessionStart** hook | After `forge claude-graphify` (when graph present) |
| **Any `forge <skill> --step`** | Debounced spawn when `graphify-out/` exists |
| **`forge ship --step 1`** | Background refresh + GRAPHIFY banner (do not wait) |
| **Post-commit hook** | `forge graphify install-hook` |
| **`$forge:graphify`** skill | Manual refresh / hook setup |

Suppress auto-spawn with **`FORGE_SKIP_GRAPHIFY_REFRESH=1`** (CI). Debounced ~2 minutes per repo via `graphify-refresh.lock` under the Forge state dir.

### Auto-refresh on commit (optional)

```bash
forge graphify install-hook    # fail-soft post-commit snippet
forge graphify uninstall-hook  # remove Forge-managed block only
```

---

## 2. Agent rules (all environments)

When `graphify-out/` or `GRAPH_REPORT.md` exists:

| Do | Instead of |
|----|------------|
| Read **`graphify-out/GRAPH_REPORT.md`** first | Grep/glob/semantic search for architecture questions |
| Use **`graphify query`**, **`graphify path`**, **`graphify explain`** | Scanning the tree for cross-module relationships |
| Navigate **`graphify-out/wiki/index.md`** if present | Reading many raw files |
| Run **`graphify update .`** after editing tracked code | Leaving the graph stale (AST-only, no API cost) |

Project-level reminders:

- **Cursor:** `.cursor/rules/graphify.mdc` (when present in the repo)
- **Claude Code:** `CLAUDE.md` in the repo
- **This repo:** [`AGENTS.md`](../AGENTS.md) → graphify section

---

## 3. Ship-time enforcement (orchestrator)

**`forge ship --step 1`** prints a **GRAPHIFY** banner and starts **`forge graphify refresh`** in the background when an index is present — continue commit/PR without waiting.

Workflow skills spawn **debounced** background refresh on each `--step` when `graphify-out/` exists; they **do not** print per-step GRAPHIFY banners (ship only).

**Disable:**

| Goal | Command |
|------|---------|
| Turn off ship banner and refresh for this clone | `forge graphify off` (prefs under `.codex/forge/state/graphify-prefs.json`) |
| Turn back on | `forge graphify on` |
| Check state | `forge graphify status` |
| Legacy implement wave defer (no effect on banners after ship-only change) | `forge graphify defer-waves` |

**Suppress in CI or automation (no prefs file):**

```bash
export FORGE_SKIP_GRAPHIFY=1
```

Also suppresses automatic background refresh (same as setting both skip flags). Accepts `true`, `yes`, `on`.

**Claude Code SessionStart:** spawns background refresh when `graphify-out/` exists. Opt out with `FORGE_SKIP_GRAPHIFY_SESSION_REFRESH=1`.

**Refresh only** (keep banners, skip auto-spawn):

```bash
export FORGE_SKIP_GRAPHIFY_REFRESH=1
```

Skill packs repeat the same contract: [`skills/`](../skills/), [`integrations/cursor-plugin/commands/`](../integrations/cursor-plugin/commands/), [`integrations/claude/commands/`](../integrations/claude/commands/), [`integrations/codex/skills/`](../integrations/codex/skills/).

### Sandbox path aliases (Codex / WSL)

The same repo may appear as ``H:\Code\forge`` (writable) and ``/mnt/h/Code/forge`` (read-only). Forge resolves a **writable** git root and remaps ``--state`` paths via ``scripts/shared/repo_paths.py``. Override with **`FORGE_REPO`** if needed.

---

## 4. Claude Code

### Install

```bash
pipx install forge-next
forge install --claude          # commands + hooks
# or re-apply hooks only:
forge claude-graphify
```

Restart Claude Code after changing `~/.claude/settings.json`.

### What hooks do

`forge claude-graphify` merges into **`~/.claude/settings.json`** using the **absolute path to your `forge` executable** (pipx), not `python -m forge_next` on `/usr/bin/python`:

```json
"/home/you/.local/bin/forge" claude-graphify-hook SessionStart
```

Events:

| Event | When |
|-------|------|
| **SessionStart** | Remind if `graphify-out/` exists; spawn **`forge graphify refresh`** in the background when metadata is stale |
| **PreToolUse** | All tools — sub-agent lifecycle reminder; **Grep**, **Glob**, **Read**, search-like **Bash** also get Graphify context when `graphify-out/` exists |
| **UserPromptSubmit** | Prompt mentions `forge:` / `$forge:` |

Each workflow slash command includes **Hard rule — Graphify** in its body.

**Troubleshooting:** If hooks error with `No module named 'forge_next'`, your `settings.json` still points at system Python. Fix:

```bash
pipx upgrade forge-next
pipx run forge-next claude-graphify   # or: forge claude-graphify if pipx bin is on PATH
forge doctor                          # warns if hooks still use python -m forge_next
```

Restart Claude Code. Debug manually: `forge claude-graphify-hook SessionStart` (reads hook JSON from stdin).

Details: [`integrations/claude/README.md`](../integrations/claude/README.md).

---

## 5. OpenAI Codex

### Install

```bash
pipx install forge-next
forge install --codex
forge codex-agents --force   # after upgrades or if you had custom developer_instructions
```

Restart Codex after editing `~/.codex/config.toml`.

### What gets configured

`forge install --codex` merges **`developer_instructions`** into **`~/.codex/config.toml`** when empty or matching the prior Forge snippet. Text **leads with mandatory Graphify rules**, then Forge delegation (sub-agents + session opt-in).

Every `forge-*` skill `SKILL.md` and YAML `description` remind agents to follow **GRAPHIFY** blocks in step output.

Details: [`integrations/codex/README.md`](../integrations/codex/README.md), [README → OpenAI Codex](../README.md#openai-codex).

---

## 6. Cursor

Cursor enforcement comes from:

- **GRAPHIFY** blocks in every `forge … --step` output
- **Hard rule — Graphify** in each `/forge:*` command under `integrations/cursor-plugin/commands/`
- Repo rule **`.cursor/rules/graphify.mdc`** when you add it to the project
- **Sub-agent lifecycle hooks** (optional per repo):

```bash
forge cursor-subagent-hooks    # writes .cursor/hooks.json in cwd
```

`preToolUse` reminds the agent to close unused Task sub-agents before every tool call; `subagentStart`/`subagentStop` track completed background agents in `.cursor/forge-subagent-lifecycle.json`. Suppress with `FORGE_SKIP_SUBAGENT_LIFECYCLE=1`.

```bash
forge install --cursor
```

---

## 7. `forge install` onboarding

`forge install` (any of `--cursor`, `--claude`, `--codex`, `--all`) prints Graphify next steps and, for Claude/Codex, applies hooks or `developer_instructions` as above. JSON output includes `graphify_onboarding` when you pass `--json`.

---

## 8. Upgrade path

After a new **forge-next** release on PyPI:

```bash
pipx upgrade forge-next
forge claude-graphify
forge codex-agents --force
forge install --claude --codex   # optional: refresh command/skill packs
```

Restart Claude Code and Codex.

---

## Quick reference

| Command | Purpose |
|---------|---------|
| `forge graphify refresh` | Update `graphify-status.json` |
| `forge graphify install-hook` | Post-commit refresh (fail-soft) |
| `forge claude-graphify` | Merge Claude Graphify hooks |
| `forge codex-agents` | Merge Codex `developer_instructions` |
| `forge graphify off` / `on` / `status` | Persist disable or show enforcement state per repo |
| `forge graphify defer-waves` / `undefer-waves` | Defer implement wave-step banners (steps 3–5) |
| `FORGE_SKIP_GRAPHIFY=1` | Disable banners, hooks, and auto-refresh (CI) |
| `FORGE_SKIP_GRAPHIFY_REFRESH=1` | Suppress auto-refresh only (keep banners) |
