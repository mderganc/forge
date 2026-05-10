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
forge evaluate --step 1 --mode review --json
```

Expected:
- JSON only on stdout
- `next_cmd` (when present) starts with `forge `

## 3) Cursor plugin (local)

- Install the plugin from `integrations/cursor-plugin/` in Cursor.
- Run:
  - `forge:doctor`
  - `forge:evaluate`

## 4) Claude command pack

- Run `forge install --claude` (copies `integrations/claude/commands/` to `~/.claude/commands/forge/` on macOS/Linux/WSL, or `%USERPROFILE%\.claude\commands\forge\` on Windows), then restart Claude Code.
- Each command file must be Markdown with `---` YAML frontmatter and a non-empty body (validated by `pytest tests/test_integration_install_layout.py`).
- Exercise at least:
  - `forge:doctor`
  - `forge:status`
  - `forge:evaluate`

## 5) Codex skill pack

- Install with `forge install --codex` (copies `integrations/codex/skills/` under `~/.codex/skills/forge/`), then restart Codex.
- Expect **11** skill folders (`forge-develop`, `forge-plan`, … — same list as [`integrations/spec/commands.json`](integrations/spec/commands.json)); each contains `SKILL.md`.
- Invoke via `/use forge-plan` (etc.) or implicit matching on the skill description.
- Run `codex-agents` or `forge codex-agents` so delegation policy is written to `~/.codex/config.toml` (see README **OpenAI Codex**).

