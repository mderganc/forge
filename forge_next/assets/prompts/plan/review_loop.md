Run the review loop on the plan per `templates/review-loop.md`.

## Plan to Review
Read `{{PLAN_FILE}}`

## Review Assignments

{{REVIEW_ASSIGNMENTS}}

| Step | Agent | Focus |
|------|-------|-------|
| Self-review | Planner | Are file paths real? Are TDD steps complete? Dependencies consistent? |
| Cross-review | QA Reviewer | Is every task testable? Acceptance criteria concrete? Test strategy covers integration? |
| Critic challenge | Critic | Hidden dependencies? Weakest assumption? Rollback realistic? |
| PM validation | PM | All solutions covered? Interfaces match? Beads cross-referenced? |

Loop until all four pass cleanly in the same round.
