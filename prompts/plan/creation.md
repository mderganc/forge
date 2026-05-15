Dispatch the **Planner** to create the detailed implementation plan.

{{MODE_CONTRACT}}

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

## Architecture
{{ARCHITECTURE_NOTES}}

## Instructions for Planner

Open `{{PLAN_FILE}}` — the orchestrator has already created it with section
markers, and the Architect has already filled in the `Architecture Overview`
section. Add the **Plan Header** block from `templates/writing-plans.md` (Goal,
Spec reference, In scope, Out of scope, **Plan mode: {{PLAN_MODE}}**).

Replace each remaining `<!-- FORGE_SKELETON: ... -->` marker with content per
`templates/writing-plans.md` and `templates/plan-modes.md`:

1. **`BRANCH-STRATEGY`** — Branch structure per the template's diagram and rules.
2. **`TASK-BREAKDOWN`** — Tasks with exact file paths, agents, TDD steps, **Verify**
   command + expected outcome per task. No placeholders. INVEST validation.
3. **`PARALLELIZATION-MAP`** — Wave table and dependencies (`lite`: only if >1 task).
4. **`INTERFACE-CONTRACTS`** — Concrete signatures/schemas when tasks depend on each other.
5. **`RISK-REGISTER`** — At least 2 risks with specific mitigations (`lite`: may be compact).
   Run a pre-mortem per `templates/pre-mortem.md` first.
6. **`ROLLBACK-STRATEGY`** — Specific steps, not "revert commits."

Run the **Self-Review Checklist** in `templates/writing-plans.md` before handing off to review.

Do not leave any `<!-- FORGE_SKELETON: ... -->` markers in the file — the
step-7 completion gate will refuse to mark the plan complete while any remain.

## Agents to Dispatch
- **Planner** (lead): Plan creation
- **Architect** (available): Architecture clarification
