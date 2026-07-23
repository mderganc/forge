Run the review loop on the plan per `templates/review-loop.md`.

{{MODE_CONTRACT}}

## Plan-Phase Safety Contract (mandatory)

- This is a planning-only phase. Do not edit product code.
- Allowed edits are limited to planning artifacts (`{{PLAN_FILE}}` and
  `{{MEMORY_DIR}}/*.md` notes referenced by this workflow).
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
| Self-review | Planner | File paths real? No placeholders? Verify command + expected outcome on every task? |
| Cross-review | QA Reviewer | Every task testable? Verification evidence concrete? Integration covered? |
| Critic challenge | Critic | Hidden dependencies? Weakest assumption? Rollback realistic? **Scope creep?** **Over-decomposition?** Planned complexity growth, duplication, cycles, or unused surfaces? |
| PM validation | PM | All **In scope** solutions covered (and nothing outside)? Mode-appropriate depth? Interfaces match? Bloat check? |

Apply `templates/review-loop.md` loop-reduction: batch findings, suggestions advisory, two-round cap for low-risk.

## Structural focus (this step)
Challenge planned tasks that would grow complexity past budget, duplicate logic, create cycles, or add speculative exports. See `templates/structural-build-charter.md`.

Loop until all four pass cleanly in the same round.
