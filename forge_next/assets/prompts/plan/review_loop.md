Run the review loop on the plan per `templates/review-loop.md`.

## Plan-Phase Safety Contract (mandatory)

- This is a planning-only phase. Do not edit product code.
- Allowed edits are limited to planning artifacts (`{{PLAN_FILE}}` and
  `.codex/forge-codex/memory/*.md` notes referenced by this workflow).
- Do not run git mutation commands: `git add`, `git commit`, `git push`,
  `git reset`, `git rebase`, `git checkout`, `git restore`, `git cherry-pick`,
  `git merge`, `git stash`, `git tag`.
- Never use `--no-verify` in any context during plan workflow steps.
- In final summaries, do not include terminal command snippets; report outcomes
  in plain language.

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
