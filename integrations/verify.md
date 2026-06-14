# Verification checklist (end-to-end)

## 1) CLI install

```bash
pipx install forge-next
forge doctor
forge status
```

## 2) JSON output contract

```bash
forge status --json
forge doctor --json
forge code-review --step 1 --mode pr --json
```

Expected:
- JSON only on stdout
- `next_cmd` (when present) starts with `forge `

## 3) Cursor plugin (local)

- Install the plugin from `integrations/cursor-plugin/` in Cursor.
- Confirm command files are `<subcommand>.md` under `commands/` (not `forge-<subcommand>.md`).
- Run:
  - `/forge:doctor`
  - `/forge:evaluate`

## 4) Claude command pack

- Run `forge install --claude` (copies `integrations/claude/commands/` to `~/.claude/commands/forge/` on macOS/Linux/WSL, or `%USERPROFILE%\.claude\commands\forge\` on Windows), then restart Claude Code.
- Each command file must be Markdown with `---` YAML frontmatter and a non-empty body (validated by `pytest tests/test_integration_install_layout.py`).
- Exercise at least:
  - `forge:doctor`
  - `forge:status`
  - `forge:evaluate`

## 5) Codex skill pack

- Install with `forge install --codex` (copies `integrations/codex/skills/` under `~/.codex/skills/forge/`), then restart Codex.
- Expect one **`forge-<cli_subcommand>/`** skill folder per workflow entry in [`integrations/spec/commands.json`](integrations/spec/commands.json) (includes `forge-sketch`, `forge-design`, …); each contains `SKILL.md`.
- Invoke via `/use forge-plan` (etc.) or implicit matching on the skill description.
- Run `forge codex-agents --force` so Graphify + delegation policy is written to `~/.codex/config.toml` (see README **OpenAI Codex**, [`docs/graphify.md`](../docs/graphify.md)).

## 6) Graphify enforcement (when `graphify-out/` exists)

- Run a workflow step: `forge design --step 1` — workflow steps do not print GRAPHIFY; refresh at `forge ship --step 1`.
- **Claude:** `forge claude-graphify` — confirm `~/.claude/settings.json` hook commands use your **pipx Python** path (not `/usr/bin/python`). Restart Claude Code.
- **Codex:** `forge codex-agents --force` — confirm `developer_instructions` in `~/.codex/config.toml` mentions Graphify first.
- **CI:** `FORGE_SKIP_GRAPHIFY=1 forge ship --step 1` — GRAPHIFY banner can be suppressed.

See [`docs/graphify.md`](../docs/graphify.md).

