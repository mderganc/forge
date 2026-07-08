Read context for plan creation.

{{HANDOFF_CONTENT}}

## Plan mode

{{MODE_CONTRACT}}

## Plan-Phase Safety Contract (mandatory)

- This is a planning-only phase. Do not edit product code.
- Allowed edits are limited to planning artifacts in
  `{{MEMORY_DIR}}/`.
- Do not run git mutation commands: `git add`, `git commit`, `git push`,
  `git reset`, `git rebase`, `git checkout`, `git restore`, `git cherry-pick`,
  `git merge`, `git stash`, `git tag`.
- Never use `--no-verify` in any context during plan workflow steps.
- In final summaries, do not include terminal command snippets; report outcomes
  in plain language.

## Instructions

1. If handoff from develop exists, read approved solutions, scope, and **spec issues** (`.design-spec-issues.json` beside the design session when present)
2. Read `{{MEMORY_DIR}}/project.md` for team state and autonomy level
3. Read all `{{MEMORY_DIR}}/` files for context
4. When a design spec exists, read it **and** map plan tasks to the issue rows from `.design-spec-issues.json` (do not re-decompose scope from scratch unless the sidecar is missing)
5. If no handoff, ask the user what needs to be planned
6. Capture scope signals in `plan_context` for mode recommendation (modules touched, risk, size)

Record the planning context in `{{MEMORY_DIR}}/planner.md`.
Include **`plan_mode`** (`default` or `lite`) once confirmed.
