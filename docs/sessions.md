# Workflow session directories

Forge stores workflow state under the **runtime root** (default `.codex/forge/` in the target repo; legacy `.codex/forge-codex/` if the canonical tree does not exist yet; `.forge/` when `.codex` is a file, read-only — common in Codex sandboxes — or its runtime subtree is not writable).

Implementation: [`scripts/shared/session_store.py`](../scripts/shared/session_store.py).

## Primary layout (new runs)

Step 1 of a workflow allocates a new directory under `sessions/`:

```
.codex/forge/
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

Resume with:

```bash
forge resume
forge <skill> --step N --state .codex/forge/sessions/<id>/session.json
```

## Legacy layout (still supported)

Older clones may still use flat files:

- `.codex/forge/state/plan.json`, `plan-foo.json`, …
- Global `memory/handoff-{skill}.md`

`forge resume --cleanup` and `forge status` scan **both** session directories and legacy flat JSON.

## Environment

| Variable | Default | Effect |
|----------|---------|--------|
| `FORGE_SESSION_MAX_AGE_DAYS` | `7` | Age threshold for automatic session archive |
| `FORGE_SKIP_SESSION_CLEANUP` | off | Disable automatic archive of old sessions |
| `FORGE_STALE_SESSION_HOURS` | `24` | Stale detection for resume/status |
| `FORGE_SKIP_AUTO_CLOSE` | off | Disable step-1 removal of superseded sessions |
| `FORGE_STEP1_ABANDON_HOURS` | `1` | Idle step-1 sessions eligible for auto-close |

See also [environment.md](environment.md) and [AGENTS.md](../AGENTS.md) (State Lifecycle).
