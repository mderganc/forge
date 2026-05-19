# Graphify integration (optional)

Forge works without Graphify. When a repo has a knowledge graph (`graphify-out/` or `GRAPH_REPORT.md`), Forge **enforces** using it during workflow skills so agents read the map before raw search.

This document covers:

1. **Building the graph** (CLI, refresh, git hook)
2. **Resume context** (`forge resume`)
3. **Workflow enforcement** (GRAPHIFY blocks every step)
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
forge graphify refresh
```

Forge writes **`.codex/forge/state/graphify-status.json`** (fail-soft on errors). `forge resume` reads this file and any `GRAPH_REPORT.md` it finds.

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

## 3. Forge workflow enforcement (orchestrator)

Every `forge <skill> --step N` prints a **GRAPHIFY** banner when an index is present — **before** phase todos and the step body.

- Investigation skills (develop, diagnose, plan, test, evaluate) use stronger wording.
- Includes a short excerpt from `GRAPH_REPORT.md` when available.

**Suppress in CI or automation:**

```bash
export FORGE_SKIP_GRAPHIFY=1
```

(Accepts `true`, `yes`, `on`.)

Skill packs repeat the same contract: [`skills/`](../skills/), [`integrations/cursor-plugin/commands/`](../integrations/cursor-plugin/commands/), [`integrations/claude/commands/`](../integrations/claude/commands/), [`integrations/codex/skills/`](../integrations/codex/skills/).

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

`forge claude-graphify` merges into **`~/.claude/settings.json`** using the **same Python interpreter as your `forge` CLI** (pipx venv), not bare `/usr/bin/python`:

```json
"/home/you/.local/pipx/venvs/forge-next/bin/python" -m forge_next.hooks.claude_graphify_hook SessionStart
```

Events:

| Event | When |
|-------|------|
| **SessionStart** | Remind if `graphify-out/` exists |
| **PreToolUse** | **Grep**, **Glob**, **Read**, search-like **Bash** |
| **UserPromptSubmit** | Prompt mentions `forge:` / `$forge:` |

Each workflow slash command includes **Hard rule — Graphify** in its body.

**Troubleshooting:** If hooks error with `No module named 'forge_next'`, upgrade Forge and re-run hooks **via pipx** (so the correct interpreter is recorded):

```bash
pipx upgrade forge-next
forge claude-graphify
```

Debug manually: `forge claude-graphify-hook SessionStart` (reads hook JSON from stdin).

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

Cursor has no global hook installer in Forge. Enforcement comes from:

- **GRAPHIFY** blocks in every `forge … --step` output
- **Hard rule — Graphify** in each `/forge:*` command under `integrations/cursor-plugin/commands/`
- Repo rule **`.cursor/rules/graphify.mdc`** when you add it to the project

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
| `FORGE_SKIP_GRAPHIFY=1` | Suppress per-step GRAPHIFY banner |
