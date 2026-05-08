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

- Install the command pack in your Claude Code environment.
- Run:
  - `forge:status`
  - `forge:evaluate`

## 5) Codex skill pack

- Add skills from `integrations/codex/skills/`.
- Invoke:
  - `evaluate`
  - `plan`

