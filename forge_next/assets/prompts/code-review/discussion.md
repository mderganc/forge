# Phase 5: Discussion

You have completed the analysis phases. Present your findings to the user for interactive review.

## Review Mode: {{MODE}} ({{MODE_DISPLAY}})
## Target: {{TARGET}}

## Accumulated Findings

{{FINDINGS}}

## Your Task

Present findings organized by severity:

1. **Critical** — Issues that must be fixed before merging or proceeding
2. **Warnings** — Issues that are concerning but may be acceptable with justification
3. **Suggestions** — Improvements that would make the code better

Include code references (file:line) and explain the "why" for each finding.

### Per-Finding Triage

For each **critical** or **warning** finding, ask the user directly how to
handle it (per `templates/user-questions.md`).

- Question: `How should we handle finding [ID] ([severity]): [title]?`
- Options:
  - `Fix now` — block the workflow until this is resolved
  - `Defer` — create a follow-up issue and proceed
  - `Dismiss` — document why this is not a real issue and continue
  - `Drill in` — investigate deeper before deciding

Record the user's decision in the finding tracker. "Drill in" re-enters the
discussion for that finding with deeper analysis before re-asking.

### Overall Progress

After triaging the highest-severity findings, ask the user directly whether to
continue or proceed to the report.

- Question: `Done triaging findings?`
- Options:
  - `Proceed` — all important findings are handled, so write the report
  - `More triage` — keep discussing remaining findings
  - `Re-scan` — dispatch reviewers again with updated focus

When the user chooses "Proceed", advance to the next phase.
