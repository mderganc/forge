# Workflow session directories

Forge stores workflow state under **`<repo>/.forge/`** (repo-local only). Legacy trees under `.codex/forge/` and `.codex/forge-codex/` are migrated into `.forge/` on the next workflow step 1 and remain readable until archived.

Implementation: [`scripts/shared/session_store.py`](../scripts/shared/session_store.py).

## Primary layout (new runs)

Step 1 of a workflow allocates a new directory under `sessions/`:

```
.forge/
  adaptation.json           # runtime profile (writable alias, mount class)
  sessions/
    index.json              # fast listing of active sessions
    {session_id}/
      session.json          # SkillState (skill, step, custom, …)
      handoff.md            # per-session handoff (when written)
      sidecars/             # step artifacts (e.g. diagnose JSON)
    _archive/
      {session_id}/         # completed or auto-cleaned sessions
  memory/                   # project.md, handoffs, synthesis, run logs
  state/                    # resume-context.json, graphify-status.json, …
```

Continue interrupted work with:

```bash
forge takeover
forge <skill> --step N --session <id>
forge <skill> --step N --state .forge/sessions/<id>/session.json
```

When **multiple active sessions** exist for the same skill, steps 2+ require **`--session <id>`** (or an explicit `--state` path). `forge takeover` and `forge status` list session IDs.

**Design / develop:** new sessions use skill name `design`. Legacy flat files such as `develop.json` and `skill_name: develop` in session JSON still resolve when you run `forge design` (alias: deprecated `forge develop`).

## Legacy layout (still supported)

Older clones may still use flat files:

- `.codex/forge/state/plan.json`, `plan-foo.json`, …
- Global `memory/handoff-{skill}.md`

`forge takeover --cleanup` and `forge status` scan **both** session directories and legacy flat JSON.

## Environment

| Variable | Default | Effect |
|----------|---------|--------|
| `FORGE_SESSION_MAX_AGE_DAYS` | `7` | Age threshold for automatic session archive |
| `FORGE_SKIP_SESSION_CLEANUP` | off | Disable automatic archive of old sessions |
| `FORGE_STALE_SESSION_HOURS` | `24` | Stale detection for takeover/status |
| `FORGE_SKIP_AUTO_CLOSE` | off | Disable step-1 removal of superseded sessions |
| `FORGE_STEP1_ABANDON_HOURS` | `1` | Idle step-1 sessions eligible for auto-close |

See also [environment.md](environment.md) and [AGENTS.md](../AGENTS.md) (State Lifecycle).
