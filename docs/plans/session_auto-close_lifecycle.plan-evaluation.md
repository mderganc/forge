# Pre-implementation evaluation: Session auto-close lifecycle

**Plan:** `docs/plans/session_auto-close_lifecycle.plan.md`  
**Mode:** PRE  
**Verdict:** **Proceed with revisions** — design is sound and aligned with the leak you hit in `ssa-project-toolkit`; address gaps below before implementation.

---

## Plan parsing summary

| Item | Content |
|------|---------|
| **Goals** | Stop leaked workflow JSON; auto-close on skill transitions; expand cleanup; surface leaks in `forge status` / `forge doctor` |
| **Main steps** | Orchestrator helper → wire 6 skills’ step 1 → expand `resume.py` cleanup → status/doctor warnings → tests → docs |
| **Files touched** | `orchestrator.py`, `plan.py`, `develop.py`, `implement.py`, `code_review.py`, `test.py`, `diagnose/orchestrate.py`, `resume.py`, `forge_next/cli.py`, `test_regressions.py`, `AGENTS.md`, `skills/resume/SKILL.md`, README, `pyproject.toml` |
| **Assumptions** | Agents skip final CLI steps; handoffs imply “done”; pipeline order is linear; deleting JSON is acceptable (no archive) |
| **Dependencies** | `detect_active_sessions`, `_state_path_candidates`, `clear_state_file`, `PIPELINE_FLOW`, handoff files under runtime memory |

**Mode:** PRE (forced) — evaluating before implementation.

---

## Feasibility — Pass

- All extension points exist: step-1 handlers already call `get_conflicting_sessions` + `format_active_session_warning`.
- `clear_state_file` is idempotent (`unlink(missing_ok=True)`).
- `detect_active_sessions` already scans `skill-*.json` via `_state_path_candidates`; gap is only in `_all_state_files` / cleanup.
- Patch-level semver is appropriate.

---

## Completeness — Gaps to fix in plan

### Critical

1. **Pipeline order must be explicit** — `PIPELINE_SKILLS` is a **set**, not ordered (`orchestrator.py` L492–499). The plan must introduce an ordered tuple, e.g. `PIPELINE_SKILL_ORDER = ("develop", "plan", "implement", "code-review", "test", "diagnose")`, and derive upstream comparisons from index — not from set iteration.

2. **Protect the session being started** — `auto_close_superseded_sessions` must accept `preserve_paths: set[Path]` (at minimum the resolved step-1 `sp` from `resolve_step1_state_path`) so a fresh step-1 init is never deleted by the handoff or step-1-stale rules.

3. **Same-skill parallel files** — Handoff rule is per skill name; closing only `plan.json` leaves `plan-outstanding-cqa.json` active (your real-world case). Auto-close must iterate **all** `_state_path_candidates(skill)` for each skill being closed, not only entries from `detect_active_sessions`.

### Important

4. **`implement.py` ordering** — Implement step 1 does **not** call `check_same_skill_clobber` today; wire auto-close **before** `_load_or_init_state` and add clobber check for parity with `plan.py`.

5. **`iterate` skill** — Plan excludes evaluate/iterate; if `iterate` step 1 exists, document explicit exclusion or narrow auto-close (avoid closing child workflow state unexpectedly).

6. **Upstream-close false positive** — Starting `implement` while a legitimate `plan` at step 5 is still intended (rare) will be closed. Mitigation options to document: `FORGE_SKIP_AUTO_CLOSE=1`, or only upstream-close when `last_completed_step < 2` (less aggressive than plan’s “any upstream active”). **Recommend:** keep aggressive policy but stderr-log every `AUTO-CLOSED` with reason so users can diagnose.

7. **No soft-complete** — Plan only deletes files. Consider setting `completed_at` + moving to `.codex/forge/state/.archive/` before unlink for audit (optional stretch).

### Minor

8. **Evaluate state location** — Plans under `.cursor/plans/` write `.evaluate-state.json` outside the repo; step 2+ fails. Document “copy plan into `docs/plans/` or repo path” or fix evaluate to store state under `runtime_state_dir` when plan is external.

9. **Tests for `implement` without clobber** — Add regression that implement step 1 runs auto-close when handoff-plan exists.

---

## Codebase alignment — Pass with notes

| Plan claim | Code reality |
|------------|--------------|
| Cross-skill warn-only at plan step 1 | Confirmed (`plan.py` L400–406) |
| `clear_state_file` only on final step | Confirmed across plan/diagnose/code_review |
| Cleanup misses parallel variants | Confirmed — `_all_state_files` only canonical names (`resume.py` L522–530) |
| `detect_active_sessions` finds parallel | Confirmed — uses `_state_path_candidates` |
| `implement` same as plan step 1 | **Partial** — warning only, no `check_same_skill_clobber` |

**Wire order (recommended):**

```
check_same_skill_clobber (where present)
→ auto_close_superseded_sessions(starting_skill, preserve={sp})
→ get_conflicting_sessions (remaining)
→ format_active_session_warning (if any)
```

---

## Risk and dependencies

| Risk | Severity | Mitigation |
|------|----------|------------|
| Upstream auto-close kills paused in-progress plan | Medium | 1h step-1 rule + stderr audit; env opt-out |
| Handoff exists but work not actually done | Medium | Only auto-close when handoff file exists (conservative rule already in plan) |
| CI/automation surprised by deletes | Low | `FORGE_SKIP_AUTO_CLOSE=1` |
| Dual runtime roots (`forge` vs `forge-codex`) | Medium | `search_dir` / `_detect_repo_root()` already used — auto-close must use same cwd as step 1 |
| Agent-written handoffs without orchestrator | Low | Same handoff-file rule |

**Rollback:** Revert patch; users run `forge resume --cleanup` manually. No schema migration.

---

## Discussion — recommended plan edits

Add to implementation plan:

1. `PIPELINE_SKILL_ORDER` tuple (ordered upstream index).
2. `preserve_paths` parameter on auto-close.
3. Close **all** state paths per skill from `_state_path_candidates`, not only `detect_active_sessions` list.
4. Implement `check_same_skill_clobber` on `implement` step 1 (or document intentional omission).
5. Test: `plan-outstanding-cqa.json` removed when `handoff-plan.md` exists and `forge implement --step 1` runs.
6. Optional: `forge doctor` leak section lists count + `forge resume --cleanup --force` hint (plan section 3 — keep).

---

## Verdict

| Criterion | Result |
|-----------|--------|
| Solves stated problem | Yes |
| Ready to implement as written | **No** — fix ordering, preserve_paths, parallel file closure |
| Regression risk | Low–medium (behavior change on step 1 stderr) |
| Recommended next step | Update plan → `forge:plan` or implement with revised todos |

**Suggested handoff:** After plan revision, run `forge:implement` or `forge:develop` with this evaluation attached.
