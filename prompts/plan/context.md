Read context for plan creation.

{{HANDOFF_CONTENT}}

## Plan-Phase Safety Contract (mandatory)

- This is a planning-only phase. Do not edit product code.
- Allowed edits are limited to planning artifacts in
  `.codex/forge-codex/memory/`.
- Do not run git mutation commands: `git add`, `git commit`, `git push`,
  `git reset`, `git rebase`, `git checkout`, `git restore`, `git cherry-pick`,
  `git merge`, `git stash`, `git tag`.
- Never use `--no-verify` in any context during plan workflow steps.
- In final summaries, do not include terminal command snippets; report outcomes
  in plain language.

## Instructions

1. If handoff from develop exists, read approved solutions and scope
2. Read `.codex/forge-codex/memory/project.md` for team state and autonomy level
3. Read all `.codex/forge-codex/memory/` files for context
4. If no handoff, ask the user what needs to be planned

Record the planning context in `.codex/forge-codex/memory/planner.md`.
