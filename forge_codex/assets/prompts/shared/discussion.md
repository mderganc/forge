# Phase 5: Discussion

You have completed the analysis phases. Present your findings to the user for interactive review.

## Evaluation Mode: {{MODE}}

## Accumulated Findings

{{PREVIOUS_FINDINGS}}

## Your Task

Present findings organized by severity:

1. **Critical** — Issues that would cause the plan to fail or produce incorrect results
2. **Warnings** — Issues that are concerning but not blocking
3. **Suggestions** — Improvements that would make the plan or implementation better

Each finding has an ID (F1, F2, etc.). The user can:
- **Dismiss** a finding: "F2 is fine because..." — mark it dismissed with their reason
- **Drill in**: "Tell me more about F3" — read relevant code and provide deeper analysis
- **Escalate**: "F5 is actually critical" — update severity
- **Ask for alternatives**: "What would you suggest instead for F4?"
- **Move on**: "Looks good, write the report" — proceed to report phase

Stay in this discussion until the user says to write the report.
When ready, tell the user to run the next step.
