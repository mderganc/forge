# Design spec: `forge takeover`

**Date:** 2026-06-20  
**Status:** Approved  
**Sketch:** `.codex/forge/memory/sketch-decisions.md`  
**Scope tier:** large

---

## Context

### Problem / opportunity

Forge today exposes two overlapping “what next?” entry points:

- **`forge resume`** — detects active sessions and prints a single resume command. It does not chain skills or drive an epic to completion.
- **`forge iterate`** — meta-workflow with gate polling, but requires explicit goal setup and a fixed diagnose-first chain.

Users want **one command** that accepts optional input (issue, design spec, or nothing), infers the correct entry point, auto-invokes Forge skills, anti-stalls through the pipeline, and stops at ship-ready quality gates—with assumptions summarized at the end, not mid-flight questionnaires.

### Who is affected

- Developers using Forge via Cursor (`/forge:*`), Codex (`$forge:*`), or Claude
- Agents following the Forge delegation contract (auto-dispatch child skills)
- Maintainers of CLI, integrations, session store, and docs

### Investigation links

- `.codex/forge/memory/investigator.md`
- `.codex/forge/memory/investigation.md`
- `.codex/forge/memory/solutions.md`

---

## Goals and non-goals

### Goals

1. **`forge takeover`** as the sole continuity + drive entry (replaces `resume` and `iterate`).
2. **Infer by default** — bare `forge takeover` reads sessions, handoffs, specs, and issues to choose work.
3. **Optional steering** — `--issue`, `--design`, `--goal` without requiring a mode flag.
4. **Default goal** — ship-ready (plan + evaluate pre/post + implement + code-review + test green) unless `--goal` overrides.
5. **Anti-stall** — auto-advance child skill steps, bounded retries, session hygiene, loop on review/test failures.
6. **Best-effort infer** — pause only on hard/unfixable blockers; record deviations for end-of-run summary.
7. **Deviations artifact** — auditable sidecar of inferences, retries, and blockers.
8. **Agent dispatch model** — same as iterate: instruct agent to run child `forge` commands; no subprocess orchestration in v1.

### Non-goals

- Auto-commit, auto-push, or auto-merge (`ship` remains separate).
- Keeping `resume` or `iterate` as aliases (hard removal per sketch).
- Subprocess-based child skill execution in v1.
- Replacing individual workflow skills (plan, implement, etc.).

---

## Constraints

### Hard

- **Breaking change:** remove `resume` and `iterate` CLI commands, skills, and integrations → **major** semver bump.
- **Delegation contract:** agents must auto-dispatch child skills; takeover prompts must emit actionable `forge` invocations via `build_next_command`.
- **Session store:** continue using `.codex/forge/sessions/{id}/session.json` as canonical state.
- **No surprise git ops:** completion handoff is `ship`, not automatic publish.

### Soft

- Command name locked: **`takeover`**.
- Reuse `infer_resume_step` as canonical step inference (dedupe `_resume_step` in resume.py).
- Preserve legacy cleanup behavior (move to `forge session cleanup` or `takeover --cleanup`).

---

## Candidate comparison snapshot

| Option | Summary | Trade-off |
|--------|---------|-----------|
| **A — Extend iterate** | Add router to iterate | Wrong UX; resume still separate |
| **B — Extend resume** | Make resume drive loops | Stateless resume awkward for SkillState driver |
| **C — New takeover skill** ✓ | Router + driver + deviations | Largest build; cleanest fit |
| **D — Stateless script** | Print command list only | No anti-stall polling |

**Chosen:** Option C (Pugh winner in `solutions.md`).

---

## Chosen design

### Overview

`scripts/takeover/takeover.py` — SkillState meta-workflow with ~6 phases:

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1: ROUTE                                        │
│  cleanup → detect sessions/handoffs/specs/issues       │
│  → epic plan (entry skill, step, goal)                 │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Phases 2–5: DRIVE                                     │
│  Poll child state/gates → emit next forge command        │
│  Loop: upstream → plan → implement → review → test     │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Phase 6: REPORT                                       │
│  deviations JSON + summary MD → handoff ship             │
└─────────────────────────────────────────────────────────┘
```

### Phase map

| Step | Name | Behavior |
|------|------|----------|
| 1 | Initialize + route | Parse flags; `run_session_cleanup`; `detect_active_sessions`; read handoffs, latest design spec, optional issue; write route plan to `state.custom` |
| 2 | Upstream | If needed: sketch/design/diagnose — poll until handoff or hard blocker |
| 3 | Plan + evaluate (pre) | Drive plan; inner loop on evaluate-pre gate until clean |
| 4 | Implement + evaluate (post) | Drive implement waves; evaluate-post loop |
| 5 | Code-review + test | Inner loops; test must pass for ship-ready |
| 6 | Report | Write `.takeover-deviations.json`, `takeover-summary.md`; `build_skill_handoff_menu` → default `ship` |

### Entry router rules

| Signal | Route |
|--------|-------|
| `--design <path>` | Validate spec exists → plan pipeline (skip upstream if approved) |
| `--issue <n\|url>` | Fetch/parse issue; bug signals → optional diagnose; else plan |
| Active single session | Continue that skill at `infer_resume_step` |
| Multiple sessions | Best-effort: newest matching `--goal` or latest `started_at`; log deviation |
| No session; handoff chain | `PIPELINE_SKILL_ORDER` successor from `handoff-{skill}.md` |
| No intent artifacts | Hard blocker OR infer from branch/PR/issue linked in memory |
| No spec for medium/large feature | Route design (record deviation if user skipped sketch) |

### Gate / completion model

Reuse iterate gate pattern generalized to `.takeover-gates/` or poll child skill state directly:

- **Ship-ready** = plan handoff exists + evaluate pre/post clean + implement complete + code-review clean + test `failed == 0`
- **Inner loop cap:** default 50 (from iterate); record in deviations on cap
- **Retry:** inherit `failure_count` pattern; max 2 same-step retries before escalate to diagnose or hard blocker

### Deviations artifact

Path: `<session>/sidecars/.takeover-deviations.json`

```json
{
  "inferences": [{"field": "epic_session", "chosen": "e497ff", "reason": "newest design session"}],
  "retries": [{"skill": "plan", "step": 4, "count": 1}],
  "blockers": [],
  "assumptions": ["Default goal: ship-ready"]
}
```

End-of-run: render human-readable summary in `takeover-summary.md` under session or memory dir.

### Interfaces

| Component | Owns |
|-----------|------|
| `takeover.py` | Meta SkillState, routing, drive loops, deviations |
| `session_store` | Session lifecycle (unchanged) |
| `session_hygiene` | `detect_active_sessions` (unchanged API) |
| `skill_phases` | `infer_resume_step` (canonical) |
| `orchestrator` | `build_next_command`, `run_workflow_step`, handoff menus |
| Child skills | Unchanged step logic |

### CLI

```bash
forge takeover [--issue URL|N] [--design PATH] [--goal TEXT] [--step N] [--session ID] [--state PATH]
forge takeover --cleanup [--force]   # migrated from resume --cleanup
```

Register in `forge_next/cli.py` and `cli_dispatch._WORKFLOW_MODULES`.

### Removal list

- `scripts/shared/resume.py`
- `scripts/iterate/` (iterate.py, iterate_step1.py, target_compare.py)
- `skills/resume/`, `skills/iterate/`
- Integration commands/skills for resume and iterate (Cursor, Claude, Codex)
- `skill_chain.py` iterate entry → `takeover` entry
- Update: AGENTS.md, docs/sessions.md, docs/graphify.md, README, tests

---

## Data / API / schema impact

- New skill name `takeover` in `KNOWN_SKILLS`, session migration lists
- New sidecars: `.takeover-deviations.json`, optional `.takeover-gates/*.json`
- `skill_chain.py`: `takeover` → default handoff `ship`
- **Removed** public API: `forge resume`, `forge iterate`
- `resume_context.py`: rename references in docs; snapshot may feed takeover router
- `validate_step_or_complete` hint strings → `forge takeover`

---

## Error handling and operational behavior

| Condition | Behavior |
|-----------|----------|
| 0 sessions, 0 handoffs, no flags | Hard blocker: prompt once for issue/design/goal; deviation if infer fails |
| N>1 sessions, no disambiguation | Best-effort pick + deviation entry |
| Child gate fails after cap | Record blocker; stop with summary |
| Missing credentials (issue fetch) | Hard blocker |
| Stale duplicate sessions | Auto-archive per session_store; deviation log |
| `failure_count` > MAX | Stop with diagnose suggestion in deviations |

---

## Test strategy

1. **Router unit tests:** 0/1/N sessions; handoff successor; flag parsing
2. **Step inference:** parity with existing resume tests via `infer_resume_step`
3. **Drive loops:** mock gate files; inner cap; ship-ready detection
4. **Deviations:** schema write/read; end summary generation
5. **Removal regressions:** no remaining `forge resume` / `forge iterate` in CLI help; integration spec updated
6. **Migration:** `test_regressions.py` cleanup paths under `takeover --cleanup`

---

## Rollout / rollback

1. Ship in single major release with changelog migration note: “use `forge takeover` instead of resume/iterate”
2. Bump `pyproject.toml` MAJOR + `plugin.json` MAJOR
3. `forge install --cursor|--codex|--claude` refreshes integrations
4. Rollback: reinstall previous forge-next version (old state files still readable)

---

## Assumptions

- Agents in Cursor/Codex will follow takeover prompts and invoke child skills without user saying “use sub-agents”
- Ship-ready is sufficient default goal for most epics
- Issue body parsing uses `gh issue view` when available
- Design specs follow `docs/forge/specs/*-design.md` convention

---

## Decision record

- **2026-06-20:** Sketch locked `takeover` intent; design recommends Option C (new skill)
- **Approval:** pending user sign-off on this spec

---

## Open questions

1. Should `.takeover-gates/` mirror iterate exactly or poll child `session.json` only? *(Recommend: poll child state first; gates for evaluate/review only)*
2. `forge session cleanup` vs `takeover --cleanup` as home for legacy flat-file cleanup? *(Recommend: `forge session cleanup`)*
