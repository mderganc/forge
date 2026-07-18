# Workflow session directories

Forge stores workflow state under **`<repo>/.forge/`** (repo-local only). Legacy trees under `.codex/forge/` and `.codex/forge-codex/` are copied into `.forge/` on the next workflow step 1, then moved to `.forge/_archive/legacy-*` (unless `FORGE_KEEP_LEGACY_RUNTIME=1`).

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

When **multiple active sessions** exist for the same skill, steps 2+ require **`--session <id>`** (or an explicit `--state` path). Continuations printed by orchestrators include `--session` automatically. `forge takeover` and `forge status` list session IDs and the resume **focus** pointer (last touched).

### Handoff pointers survive archive

The global `memory/handoff-{skill}.md` file is a small **pointer** (front-matter `path:` and a `Full handoff:` line) to the per-session `sessions/{id}/handoff.md`. When `forge session close <id>` (or automatic archive) moves that session directory to `sessions/_archive/{id}/`, `archive_session_dir()` calls `_rewrite_handoff_pointers_for_archive()` to rewrite any pointer that still references the live `sessions/{id}/handoff.md` path to `sessions/_archive/{id}/handoff.md`, so downstream reads keep resolving without a dangling link. As a defensive fallback, handoff reads (`scripts/shared/handoff_io.py`) also retry the archived path when the recorded pointer predates the rewrite. Implementation: [`scripts/shared/session_store.py`](../scripts/shared/session_store.py) and [`scripts/shared/handoff_io.py`](../scripts/shared/handoff_io.py).

### Dual-layer model

- **Isolation:** state + sidecars under `.forge/sessions/{id}/` (prefer `sidecars/` for step artifacts; gates also read files beside `session.json` for legacy).
- **Collaboration:** shared `memory/project.md` (section merge with `<!-- forge-session:{id} -->` attribution), multi-session `forge-memory-synthesis.md`, `state/resume-context.json` (schema v2: `sessions[]` + `focus`), and global `handoff-{skill}.md` as a **pointer** to `sessions/{id}/handoff.md`.

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
| `FORGE_KEEP_LEGACY_RUNTIME` | off | Keep `.codex/forge*` after copy into `.forge/` (skip archive) |
| `FORGE_STALE_SESSION_HOURS` | `24` | Stale detection for takeover/status |
| `FORGE_SKIP_AUTO_CLOSE` | off | Disable step-1 removal of superseded sessions |
| `FORGE_STEP1_ABANDON_HOURS` | `1` | Idle step-1 sessions eligible for auto-close |

**`FORGE_STEP1_ABANDON_HOURS` only applies to step-1-only sessions.** A session that has advanced past step 1 is never auto-closed for being idle — it can only be superseded by a matching handoff or an upstream-pipeline move-forward (`is_pipeline_session_abandoned()` in [`scripts/shared/session_hygiene.py`](../scripts/shared/session_hygiene.py) delegates to the step-1-only check; mid-pipeline sessions must be closed explicitly, e.g. `forge session close <id>`).

See also [environment.md](environment.md) and [AGENTS.md](../AGENTS.md) (State Lifecycle).
