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
- `cursor-plugin/`: Cursor plugin bundle (`/forge:<subcommand>` slash commands).
- `claude/`: Claude Code command pack (v1).
- `codex/`: Codex skill pack (v1).

Layout for Cursor/Claude slash commands and Codex skills is enforced by `pytest tests/test_integration_install_layout.py` (matching `<cli_subcommand>.md` files under `cursor-plugin/commands/` and `claude/commands/` to `spec/commands.json`, and Codex `SKILL.md` folders).

### Slash command naming (Cursor / Claude)

- **Supported:** `/forge:<subcommand>` (for example `/forge:diagnose`). Command files are named `<subcommand>.md`; the plugin namespace is `forge` (see `cursor-plugin/.cursor-plugin/plugin.json`).
- **Not supported** by current Cursor plugin schema: alias fields, `/f:<subcommand>`, or unscoped `/diagnose`. Codex uses `$forge:<subcommand>` via skill `name:` in each `SKILL.md` (skill folders remain `forge-<subcommand>/` on disk).

### Graphify (optional codebase map)

When a repo has `graphify-out/`, Forge enforces Graphify during workflow skills:

| Environment | Setup |
|-------------|--------|
| **All** | Debounced background `forge graphify refresh` on workflow `--step` when `graphify-out/` exists; **GRAPHIFY** orchestrator banner on **`forge ship --step 1`** only — see [`docs/graphify.md`](../docs/graphify.md) |
| **Claude** | `forge install --claude` or `forge claude-graphify` → `~/.claude/settings.json` hooks |
| **Codex** | `forge install --codex` or `forge codex-agents --force` → `~/.codex/config.toml` |
| **Cursor** | Command bodies + repo `.cursor/rules/graphify.mdc`; no global hook installer |

After upgrading **forge-next**: `pipx upgrade forge-next`, then re-run `forge claude-graphify` and `forge codex-agents --force`.

### Structural quality probes (optional)

`forge install` installs **knip**, **madge**, and **pyscn** by default for Pass B review in code-review and evaluate (warns on any missing). See [`docs/structural-quality.md`](../docs/structural-quality.md).

