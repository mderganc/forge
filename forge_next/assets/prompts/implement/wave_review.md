# Phase 4: Wave Review

Run per-task review loop for Wave {{CURRENT_WAVE}} tasks.

Size model: `templates/scope-size-model.md`. Loop policy: `templates/review-loop.md`.

## Structural focus (this step)
- Checklist: complexity budget, no new clones, no dead arms, no new cycles, no speculative exports
- Read `.structural-probes.json` when present; triage `J*`/`P*` (and knip/madge/skylos if present)
- Fix high-confidence complexity/clone hits **before advancing the wave**; cite finding IDs
- Structural review stays **on**; scale fan-out with task size (small → quick subset)
See `templates/structural-build-charter.md` and `templates/structural-quality-probes.md`.

## Review Protocol (scale by task **Size**)

For each completed task in Wave {{CURRENT_WAVE}}, read the task's **Size:** field (`small` | `medium` | `large`; default `small` for lite plans).

### Small tasks
| Step | Agent | Focus |
|------|-------|-------|
| Self-review | Implementing Dev | Match plan? TDD? Tests? Charter? |
| Combined cross/critic | QA + Critic (one pass) | Edge cases + production failure risk |
| PM validation | PM | Plan adherence? Scope fidelity? |

Cap at **two rounds**, then escalate. Skip Mutation / Performance / Operational Readiness sections below. Suggestions advisory.

### Medium / large tasks
| Step | Agent | Focus |
|------|-------|-------|
| Self-review | Implementing Dev | Match plan? TDD followed? Tests pass? Charter lenses held? |
| Cross-review | QA Reviewer | Edge cases? Test quality? Coverage? |
| Critic challenge | Critic | Production failure? Untested assumptions? Complexity/clone debt deferred? Scope creep? |
| PM validation | PM | Plan adherence? Beads updated? Memory current? |

Batch findings; re-review only changed files and unresolved blockers. Full extra rounds only for material design/API/security/structural changes.

## Review Checklist per Task (all sizes)

- [ ] Implementation matches plan specification (**In scope** only)
- [ ] TDD log shows proper Red-Green-Refactor cycles (or explicit exemption)
- [ ] All new tests pass
- [ ] Relevant test suite passes (full suite for medium/large; targeted OK for small)
- [ ] Code follows project conventions
- [ ] No hardcoded values, secrets, or debug artifacts
- [ ] Beads updated (if available)
- [ ] Memory file updated with task status
- [ ] Structural charter: complexity under budget; no new clones; no dead arms; no new cycles; no speculative exports
- [ ] High-confidence probe hits (`J*`/`P*`) addressed or explicitly deferred with reason

### Performance & Efficiency *(medium/large only)*
- [ ] No N+1 queries or database calls inside loops
- [ ] No O(n^2+) algorithms on unbounded inputs
- [ ] Hot paths avoid unnecessary allocations or redundant computation

### Mutation Testing Audit *(medium/large only; skip for small)*
- [ ] For each critical function: mentally mutate — verify a test would catch it
- [ ] If a mutation would pass undetected, write a test before proceeding

### Backward Compatibility *(when public surface changes)*
- [ ] Public function signatures unchanged (or all callers updated)
- [ ] Data format changes are backward-compatible (or migration provided)

### Operational Readiness *(medium/large only)*
- [ ] Error paths produce meaningful messages
- [ ] Key decision points logged; resources cleaned up; no sensitive data in logs

### Risk
- [ ] Rollback-safe
- [ ] No implicit dependencies on execution order of other wave tasks

## Quick Mode

{{QUICK_MODE_NOTE}}
