# Design: Parallel sessions (independent + shared global context)

**Date:** 2026-07-10  
**Slug:** `parallel-sessions`  
**Scope:** medium  
**Sketch:** `.forge/memory/sketch-decisions.md`  
**Solutions:** `.forge/memory/solutions.md` (Family B selected)

## Context

Forge already allocates `.forge/sessions/{id}/session.json` on step 1 for most skills, but parallel work still collides because:

1. **implement** discards the allocated session path and may write flat `.forge/state/implement.json`.
2. **diagnose** / **implement** continuations often omit `--session`, so steps 2+ cannot disambiguate.
3. Global artifacts (`handoff-{skill}.md`, `resume-context.json`, synthesis) are **last-writer-wins**, so sessions cannot collaborate without erasing each other.

Who is affected: agents running multiple Forge skills in one repo; `forge status` / `forge takeover` users; anyone relying on handoffs between skills.

Investigation: `.forge/memory/investigation.md`, `.forge/memory/investigator.md`.

## Goals and non-goals

**Goals:**

- Two (or more) concurrent workflow sessions never share state files, sidecars, or ambiguous continuations.
- Sessions collaborate through a **shared global context** (project narrative, multi-session synthesis, resume index with focus, handoff pointers).
- Clear agent directions: every `next_cmd` includes `--session <id>` (or equivalent `--state`).
- Backward-compatible reads for one release (v1 resume blob → single-entry index; full handoff files still readable if present).

**Non-goals:**

- Distributed locking / multi-user concurrent writers beyond attribution.
- Migrating evaluate onto session directories.
- Changing `/forge:` vs `$forge:` invocation prefixes.
- Deleting historical `.codex/forge*` archives.
- CRDT or automatic three-way merge for `project.md`.

## Constraints

**Hard:**

- Canonical runtime remains `.forge/` (legacy `.codex/forge*` migrate+archive).
- Steps 2+ must keep requiring `--session` when multiple same-skill sessions are active.
- Do not break single-session repos (default path when only one active session).

**Soft:**

- YAGNI / smallest correct change (Family B waves).
- Prefer pointer/index over deleting global filenames agents already know.
- Section-level LWW + session attribution for `project.md`, not a new merge engine.

## Candidate comparison snapshot

| Direction | Trade-off |
|-----------|-----------|
| **A Isolation-only** | Fixes collisions fast; fails shared global context goal. |
| **B Incremental dual-layer** (chosen) | Meets both goals in shippable waves; two careful migrations. |
| **C Big-bang session OS** | Clean end state; too large / speculative for this effort. |

Weighted score favored **B** (82 vs 54 / 64) — see `solutions.md`.

## Chosen design

### Decision

Adopt a **dual-layer** model:

1. **Isolation layer** — all active skill state and sidecars live only under `.forge/sessions/{id}/`.
2. **Collaboration layer** — sessions contribute to shared global files via merge/pointer/index APIs, never by overwriting another session’s directory.

```text
Independent session tree                 Shared global context
.forge/sessions/{id}/                    .forge/memory/project.md
  session.json                             (merge/append + attribution)
  handoff.md                             .forge/memory/forge-memory-synthesis.md
  sidecars/                                (multi-session table)
                                         .forge/memory/handoff-{skill}.md
                                           (thin pointer → session handoff)
                                         .forge/state/resume-context.json
                                           (sessions[] + focus)
```

### Wave 1 — Isolation (must ship first)

1. **implement step 1:** After `resolve_step1_state_path`, use that `Path` for init/load/save. Remove fallback to `_get_state_path()` / `find_state_file` on fresh step 1. Do not call `resolve_step1_state_path` twice inside `_load_or_init_state`.
2. **Continuations:** Pass `state=sp` (or `state_path=sp`) into every `build_next_command` / `_next_command` for **diagnose** and **implement** (all steps). Audit other skills; design/plan/test/code-review/sketch already pass state.
3. **`parse_continuation_command`:** Recognize `--session <id>` and resolve to the session state path for resume hints.
4. **Sidecars:** Keep diagnose/probe JSON under the session directory (parent of `session.json`). Prefer writing under `sidecars/` when that directory exists; gates must read `sidecars/` first, then session root (backward compatible). Document the chosen rule in `docs/sessions.md`.

### Wave 2 — Global collaboration

1. **`write_handoff`:** Always write full narrative to `sessions/{id}/handoff.md`. Write global `handoff-{skill}.md` as a **pointer document** (YAML frontmatter or short markdown) listing `session_id`, `path`, `updated_at`, optional `label` — not the full narrative. If multiple same-skill completions exist, pointer lists newest first (or all active pointers).
2. **`consume_handoff`:** Resolve pointer → read session handoff content; do **not** delete the session handoff. May clear or update the global pointer after consume. Legacy full-content global files remain readable for one release.
3. **`resume-context.json` schema v2:**
   - `schema_version`: `2`
   - `focus`: session id last touched (or explicitly set)
   - `sessions`: array of `{session_id, skill, state_path, current_step, last_completed_step, max_step, label, updated_at}`
   - Preserve evaluate extras on evaluate entries when present
   - **Migration:** On read, if v1, wrap as single-element `sessions` and set `focus` from that entry.
4. **`memory_synthesis`:** Include an “Active sessions” table from resume index / `list_active_sessions`; prefer session `handoff.md` excerpts over global full files; keep `project.md` rollup.
5. **`project.md`:** Agents may update sections; when rewriting a section, append or replace that section only and add attribution `<!-- forge-session:{id} -->` (or equivalent). No whole-file clobber from a single session without reading existing content first.
6. **`forge status` / `forge takeover`:** Show all active sessions + highlight `focus`; continuation suggestions include `--session`.

### Wave 3 — Docs and cleanup

1. Update `docs/sessions.md`, `docs/environment.md` (correct `FORGE_AUTO_PARALLEL_ON_CONFLICT` = evaluate-only), `AGENTS.md` State Lifecycle as needed.
2. Align agent/templates that still imply single global handoff narrative.
3. Regression tests listed below.

### Boundaries

| Owner | Owns |
|-------|------|
| `session_store` / skill orchestrators | Isolation paths, `--session` threading |
| `handoff_io` | Pointer vs full handoff write/consume |
| `resume_context` | Index + focus schema |
| `memory_synthesis` | Multi-session rollup |
| takeover / status | Presentation of multi-session global context |
| evaluate | Unchanged parallel model (plan-dir state files) |

## Data / API / schema impact

### resume-context v2 (illustrative)

```json
{
  "schema_version": 2,
  "focus": "dd6c05",
  "updated_at": "2026-07-10T20:00:00+00:00",
  "sessions": [
    {
      "session_id": "dd6c05",
      "skill": "design",
      "state_path": ".forge/sessions/dd6c05/session.json",
      "current_step": 6,
      "last_completed_step": 5,
      "max_step": 8,
      "label": "parallel-sessions",
      "updated_at": "2026-07-10T20:00:00+00:00"
    }
  ]
}
```

### Global handoff pointer (illustrative)

```markdown
---
forge_handoff_pointer: 1
skill: design
session_id: dd6c05
path: .forge/sessions/dd6c05/handoff.md
updated_at: 2026-07-10T20:00:00+00:00
---

# Handoff pointer: design

Full handoff: `.forge/sessions/dd6c05/handoff.md`
```

### CLI / agent contract

- Step 1: always new session (unchanged).
- Steps 2+: `--session <id>` required when >1 active same-skill session (unchanged enforcement; fixed emission).
- `FORGE_AUTO_PARALLEL_ON_CONFLICT`: document as evaluate-only; pipeline skills already always allocate new sessions.

## Error handling and operational behavior

- Multiple sessions without `--session` on step 2+: keep hard error + session table (clear directions).
- Corrupt resume v2: fall back to `list_active_sessions` filesystem scan; warn on stderr.
- Pointer handoff missing target file: warn and search newest `sessions/*/handoff.md` for that skill; do not invent content.
- implement must never create flat `.forge/state/implement.json` for new runs; legacy flat files remain readable until migrated/archived.

## Test strategy

Must prove before shipping:

1. Two `resolve_step1_state_path("implement")` + simulated step-1 save → two distinct session paths; no `.forge/state/implement.json` created.
2. diagnose/implement `build_next_command` output contains `--session` when `state_path` is a session.json.
3. `parse_continuation_command` extracts `--session`.
4. Two `write_handoff` calls for same skill different sessions → two session handoffs intact; global pointer points at latest (or lists both).
5. `consume_handoff` reads via pointer without deleting session handoff.
6. resume v1 file loads as v2 single-entry index.
7. synthesis includes ≥2 active sessions when two exist.
8. Existing single-session happy paths still pass (plan/design/test smoke subset).

## Rollout / rollback

**Rollout:** Land Wave 1 first (safe, high value). Wave 2 behind normal release; readers accept v1+v2 resume and full-or-pointer handoffs. Wave 3 docs in same or follow-up PR.

**Rollback:** Revert PR; v2 resume files remain readable if writers are reverted only after dual-read ships. Pointer handoffs: if writers reverted, old full-content writers restore LWW behavior.

**Versioning:** Patch or minor per AGENTS.md — capability is backward-compatible → **minor** when shipping Wave 2 CLI/schema behavior users rely on; Wave 1 bugfix alone can be **patch**.

## Assumptions

- Users/agents will copy printed continuation lines that include `--session`.
- One machine / one primary agent is enough; no multi-writer file locks required.
- Evaluate remaining on plan-dir state is acceptable for this effort.
- Plan approval of “independent + shared global context” constitutes product direction approval for this spec.

## Decision record

- **Date:** 2026-07-10
- **Direction:** Independent sessions + shared global context (user-locked in sketch/plan).
- **Solution family:** B Incremental dual-layer.
- **Approval:** Approved for plan handoff via executed Forge sketch→design plan (user: implement plan to completion). Spec gate `user_approved: true` recorded with design session `dd6c05`.

## Open questions

- Exact pointer frontmatter keys (finalize in plan/implement; illustrative format above is normative enough to start).
- Whether `sidecars/` becomes the **only** write target after one release (gates already dual-read).
- Optional later: explicit `forge focus --session <id>` to set resume focus without a save.
