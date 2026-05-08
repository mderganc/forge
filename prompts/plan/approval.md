Present the plan to the user for approval.

## Pre-Mortem (required before approval)

Run a pre-mortem analysis per `templates/pre-mortem.md`:
1. Imagine this plan was executed 6 months from now and **failed catastrophically**.
2. Each team member generates 2-3 failure scenarios (technical, process, integration, assumption, external).
3. Categorize and prioritize by likelihood × impact.
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
  - `Approve` — accept the plan and hand off to `implement`
  - `Revise` — return to step 3 with feedback
  - `Simplify` — scope the plan down before approval
  - `Reject` — stop here because the plan is not viable

Record the user's decision in `project.md`. If approved, proceed to handoff.
If changes requested, return to step 3 (plan creation).
