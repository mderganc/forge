# Stage 3 — Solution Review & User Approval

## Review Loop
Per `templates/review-loop.md`:
| Step | Agent | Focus |
|------|-------|-------|
| Self-review | Architect | Honest cons? Consistent scores? |
| Cross-review | Security Reviewer + QA | Security implications? Testability? |
| Critic challenge | Critic | Worst-case outcome? Understated risks? |
| PM validation | PM | Enough info for user to choose? |
| Pre-mortem | All agents | Imagine this solution failed — what happened? |

Before presenting to the user, run a pre-mortem per `templates/pre-mortem.md`. Each agent generates 2-3 failure scenarios. Categorize, prioritize, and add mitigations to the risk assessment. Record any findings that change the recommendation.

## User Approval

Present scored solutions summary:
{{SOLUTIONS_SUMMARY}}

Then ask the user directly for approval (per `templates/user-questions.md`).
Use this question and these options:

- Question: `Approve the recommended solution for implementation?`
- Options:
  - `Approve` — accept the recommendation and hand off to `plan`
  - `Revise` — return to Stage 2 with feedback
  - `Alternate` — pick a different scored alternative
  - `Reject` — stop here because no solution is acceptable

Record the user's decision in `project.md` and branch accordingly.
