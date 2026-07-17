Dispatch the **Architect** to design the unified architecture.

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

## Context
{{PLAN_CONTEXT}}

## Structural focus (this step)
- **Complexity:** Design seams so new/changed functions stay under the complexity budget (`min-complexity=15`)
- **Clones:** Prefer one shared module over parallel copy-prone shapes
- **Cycles:** Keep dependency direction acyclic
- **Unused exports:** No speculative public APIs
- If a structural probes baseline sidecar is present, design around or repay in-scope hotspots
See `templates/structural-build-charter.md`.

## Instructions for Architect

1. Read approved solutions and investigation findings.
2. Design how solutions fit together architecturally.
3. Define component boundaries, data flow, API contracts.
4. Open `{{PLAN_FILE}}` — the orchestrator has already created it with section markers.
5. **Replace the `<!-- FORGE_SKELETON: ARCHITECTURE-OVERVIEW -->` marker** under
   the `## Architecture Overview` heading with your architecture content. Do
   not overwrite other sections; the Planner will fill those in step 3.

## Agents to Dispatch
- **Architect** (lead): Architecture design
