Present the plan to the user for approval.

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

## Pre-Mortem (required before approval)

Run a pre-mortem analysis per `templates/pre-mortem.md`:
1. Imagine this plan was executed 6 months from now and **failed catastrophically**.
2. Each team member generates 2-3 failure scenarios (technical, process, integration, assumption, external).
3. Categorize and prioritize by likelihood Ã— impact.
4. Add any new risks to the plan's risk register before presenting.

## Plan Summary

Read `{{PLAN_FILE}}` and present:
1. Architecture overview
2. Task breakdown (count, assigned agents, INVEST validation status)
3. Parallelization map
4. Risk register highlights (including new risks from pre-mortem)
5. Rollback strategy
6. Estimated complexity

## User Approval

Ask the user directly for approval (per `templates/user-questions.md`).
Use this question and these options:

- Question: `Approve the implementation plan?`
- Options:
  - `Approve` â€” accept the plan and hand off to `implement`
  - `Revise` â€” return to step 3 with feedback
  - `Simplify` â€” scope the plan down before approval
  - `Reject` â€” stop here because the plan is not viable

Record the user's decision in `project.md`. If approved, proceed to handoff.
If changes requested, return to step 3 (plan creation).
