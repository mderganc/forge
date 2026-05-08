Dispatch the **Planner** to create the detailed implementation plan.

## Architecture
{{ARCHITECTURE_NOTES}}

## Instructions for Planner

Open `{{PLAN_FILE}}` — the orchestrator has already created it with section
markers, and the Architect has already filled in the `Architecture Overview`
section. Replace each remaining `<!-- FORGE_SKELETON: ... -->` marker with the
content described in `templates/writing-plans.md`:

1. **`BRANCH-STRATEGY`** — Branch structure per the template's diagram and rules.
2. **`TASK-BREAKDOWN`** — Tasks with exact file paths, agents, TDD steps.
   Validate each against INVEST (Independent, Negotiable, Valuable, Estimable,
   Small, Testable).
3. **`PARALLELIZATION-MAP`** — Wave table and dependencies.
4. **`INTERFACE-CONTRACTS`** — Concrete signatures/schemas where tasks depend on each other.
5. **`RISK-REGISTER`** — At least 2 risks with specific mitigations.
   Run a pre-mortem per `templates/pre-mortem.md` first.
6. **`ROLLBACK-STRATEGY`** — Specific commands, not "revert commits."

Do not leave any `<!-- FORGE_SKELETON: ... -->` markers in the file — the
step-6 completion gate will refuse to mark the plan complete while any
remain.

## Agents to Dispatch
- **Planner** (lead): Plan creation
- **Architect** (available): Architecture clarification
