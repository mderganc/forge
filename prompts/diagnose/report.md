# Phase 7: Diagnostic Wrap-up & Prevention

{{DIAGNOSE_ARTIFACT_GATE}}

## Agents to Dispatch
- **Doc-writer (lead):** Write diagnostic output
- **Investigator (support):** Methodology summary
- **Architect (support):** Architecture recommendations

## Core closure (every run)

Confirm:

1. **Problem framing** — `.diagnose-problem-spec.json` — {{PROBLEM_SPEC_SUMMARY}}
2. **Feedback loop** — `.diagnose-feedback-loop.json` — {{REPRO_LOOP_SUMMARY}}
3. **5 Whys** — `.diagnose-five-whys.json` — {{FIVE_WHYS_SUMMARY}}

## Cleanup (before handoff)

- [ ] Re-run the Phase 2 feedback loop — original failure no longer reproduces (or document residual flake rate).
- [ ] Remove all `[DEBUG-…]` instrumentation (grep the prefix used in Phase 4).
- [ ] Delete or relocate throwaway harnesses/scripts used only for debugging.
- [ ] State which hypothesis or 5-Whys chain was correct in the report / commit message.

## Prevention

Ask: **What would have prevented this bug?** If the answer is architectural (no test seam, hidden coupling), note it for develop/plan — after the fix is in, not before.

## Optional artifacts (only if activated)

Document only techniques that were in `activated_techniques`:

| Technique | Sidecar / pointer |
|-----------|-------------------|
| First-principles thinking | `.diagnose-first-principles.json` — {{FIRST_PRINCIPLES_SUMMARY}} |
| Hypothesis-driven problem solving | `.diagnose-hypotheses.json` — {{HYPOTHESIS_REGISTER_SUMMARY}} |
| MECE issue tree | `.diagnose-mece-tree.json` — {{MECE_SUMMARY}} |

If a technique was never activated, do not fabricate its sidecar — note “not activated” in the report.

## Technique Coverage Matrix (final)

Persist `.diagnose-technique-coverage.json` with a row for **each activated technique** (not all 20 by default). Orchestrator validates activated rows at step 7.

Summary: {{TECHNIQUE_COVERAGE_SUMMARY}}

| technique | applied / skipped / deferred | evidence or rationale |
|-----------|------------------------------|------------------------|

- **applied:** pointer to sidecar, memory file, log, or script output
- **skipped:** cost/signal trade-off (allowed for non-activated techniques you considered and rejected)
- **deferred:** trigger for later application

High-severity: **Kepner-Tregoe Problem Analysis**, **Barrier Analysis**, and **FMEA** or **Fault Tree Analysis** must be **applied** when profile requires (not skippable via override).

## Hypothesis Register (if activated)

Include a table of register entries only when hypothesis technique was in play.

## Preferred routing audit

State which incident-profile buckets matched and whether follow-on techniques beyond framing + 5 Whys were justified.

## Diagnostic report

Use `python3 {{SCRIPT_DIR}}/diagnostic_report.py` or write equivalent sections: symptom, framing, 5 Whys root cause, fixes, prevention.

## Handoff

Set `fix_complexity` in state when known (`simple` \| `complex` \| `large`) for the workflow handoff menu.

{{AUTONOMY_GATE}}
