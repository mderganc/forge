---
title: "Evaluation: Fix forge-codex skill workflow defects (step caps, plan-writing, state finalization, evaluate findings)"
plan: /home/matt/.claude/plans/i-m-having-some-issues-composed-hedgehog.md
mode: pre
date: 2026-05-07
---

# Evaluation: Fix forge-codex skill workflow defects

## Summary

Pre-implementation evaluation of a 5-fix plan addressing step-cap errors, missing plan-file authoring, state-file leaks, the `implement.py` clear-then-resave bug, and a newly discovered evaluate-skill findings-persistence bug surfaced during this very evaluation run. After Phases 1-4 produced 32 findings (6 critical, 16 warning, 5 suggestion, 5 already-aligned), the user directed "fix all findings" and the plan was revised to address every one. The revised plan is ready for implementation.

## Findings

### Critical

All six critical findings were addressed in the plan revision rather than dismissed.

- **F5 — Pre-flight session-conflict check breaks manual `--state` resume.**
  *Resolution:* Same-skill abort scoped to `handle_step_1` only. Subsequent steps require `--state <path>` (explicit resume signal) and bypass the check.

- **F11 — Evaluate skill silently drops findings between phases.**
  *Resolution:* New Fix 4 added. Phase prompts emit findings as `findings-json` blocks; orchestrator persists them via per-step sidecar files (`.evaluate-findings-step<N>.json`); step 5 renders from `EvalState.findings`. Discovered during this evaluation when "No findings yet" appeared in steps 3, 4, and 5 despite 32 findings being produced.

- **F12 — New state fields break legacy state files.**
  *Resolution:* Audit of `SkillState.from_dict` for `.get(key, default)` usage on every new field; regression test loads a hand-crafted JSON without `failure_count` to verify defaults.

- **F13/F24 — Re-running step 1 generates a new timestamp, orphaning prior skeleton.**
  *Resolution:* Reuse existing `generate_plan_filename` (plan.py:149); patch lands at line 248. If `state.custom["plan_file"]` exists from a prior session, reuse the path rather than regenerating.

- **F26 — Schema drift: `state.custom["mode_max_step"]` parallels existing `SkillState.max_step`.**
  *Resolution:* Reuse the existing `max_step` first-class field; add `failure_count: int = 0` as a first-class field on `SkillState` rather than burying it in `state.custom`.

### Warnings

All 16 warning findings addressed in the plan revision.

- **F1** — Skeleton uses the 7 sections from `templates/writing-plans.md:9-15` verbatim (no Context, no Verification).
- **F2** — Fix 1 scope narrowed to `implement.py:467,485` and `develop.py` manual next-cmd; evaluate already caps correctly.
- **F3** — `load_template` reordered to run *before* `save_state` so missing-template doesn't leave half-written state.
- **F4** — Test-fixture scaffolding added as a precursor task (`tests/test_shared_orchestrator.py` is currently 46 lines).
- **F6** — New `validate_step_or_complete` helper instead of mutating the existing `validate_step` (preserves test contract).
- **F8** — Wave-loop next-cmd uses explicit `waves_completed` vs `total_waves` branching.
- **F14** — Skeleton overwrite policy: refuse on non-marker content, allow on stub, `--force` flag for explicit override.
- **F15** — `--cleanup` defaults to dry-run; `--force` required to delete.
- **F16, F31** — `_build_variables` (`plan.py:156`) explicitly named in critical files; `{{HANDOFF_FILE}}` added there.
- **F17** — `README.md` and `AGENTS.md` updates folded into Fix 5.
- **F18** — `--cleanup --all-stale --force` migration mode for users with existing leaked state.
- **F23** — Existing `format_active_session_warning` cross-skill warning preserved; same-skill abort *added* (not replacing) at step 1.
- **F25** — Per-skill `_next_command` retained; `mode` threaded through. Migration to shared `build_next_command` deferred as out-of-scope refactor.
- **F27** — Warnings to stderr, hard aborts via `sys.exit(1)` — matches existing convention at `plan.py:235`.
- **F32** — Hardcoded fallback path `runtime_memory_dir() / "plans" / "plan.md"` removed; missing `state.custom["plan_file"]` now hard-errors instead of silently falling back.

### Suggestions

All 5 suggestions addressed; some scoped out as separate work.

- **F19** — `failure_count` resets to 0 on every successful step completion.
- **F20** — Specific marker `<!-- FORGE_SKELETON: <SECTION-NAME> -->` chosen to avoid false-positive matches against legitimate HTML comments in plan content.
- **F21** — TOCTOU race noted in code comment; deferred until concurrent-CLI usage observed.
- **F22** — 0-wave plans handled by jumping from `handle_step_3` directly to step 6.
- **F28** — `_state_path()` boilerplate dedup across 6 skills called out as follow-up refactor; not in this plan.

### Already Aligned (Feasible Without Changes)

- **F7** — HTML-comment placeholders survive `render_template` (regex matches only `{{VAR}}` syntax).
- **F9** — `state.custom: dict[str, Any]` accepts arbitrary keys (though plan now prefers first-class fields).
- **F10** — `clear_state_file` is idempotent (`unlink(missing_ok=True)`) — confirms `implement.py:516-517` is dead code.
- **F29** — `EvalState` is the mode-bearing class; `state.max_step` change applies there for evaluate.
- **F30** — `write_handoff` (orchestrator.py:827) is the right precedent for `write_plan_skeleton`.

## Dismissed Items

None. The user directed "fix all findings" and the plan revision incorporated each one — either as an in-scope plan change, an explicit out-of-scope deferral with rationale, or a confirmation that the existing code already handles the case.

Out-of-scope deferrals (all noted in the plan):
- F21 — TOCTOU concurrency
- F25 — `_next_command` consolidation
- F28 — `_state_path` dedup

## Conclusion

The plan is **ready for implementation** in pre mode.

Strengths:
- Reuses existing helpers (`generate_plan_filename`, `format_active_session_warning`, `SkillState.max_step`, `write_handoff`) rather than parallel-storing data or reinventing primitives.
- Discovers and addresses a real bug (F11/Fix 4) that the user did not initially report — surfaced through dogfooding the evaluate skill on this plan.
- Each fix is localized to specific file:line targets verified against the codebase.
- Test scaffolding precursor task acknowledged before behavioral tests (F4).
- Out-of-scope items called out with rationale rather than silently dropped.

Recommended next steps:
1. Approve the plan via `ExitPlanMode`.
2. Begin implementation in dependency order: Fix 5 test scaffolding → Fix 1 → Fix 3 → Fix 2 → Fix 4 → Fix 5 docs.
3. After implementation, run a post-mode evaluation against the same plan to verify completeness and correctness.
