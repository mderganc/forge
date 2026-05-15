# Phase 6: Documentation Planning

Design and confirm documentation scope **before** handoff to implement. Output feeds the implement documentation gate and audience applicability.

{{MODE_CONTRACT}}

**Plan mode `{{PLAN_MODE}}`:** `lite` still requires complete applicability matrix and DoD rows (concise text OK). `default` requires full narrative detail.

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

## Plan file requirement

Ensure the plan file `{{PLAN_FILE}}` contains a filled **Documentation** section (see `templates/writing-plans.md`). Replace the `<!-- FORGE_SKELETON: DOCUMENTATION -->` marker with concrete content — the orchestrator blocks completion while that marker remains.

## Audience applicability (three tiers)

For each change, decide which audiences apply. **Do not assume all three every time.**

| Audience | Typical content |
|----------|-----------------|
| **Architect / Expert** | ADRs, architecture, interfaces, tradeoffs, constraints |
| **Technical Operator** | Runbooks, deploy, ops, troubleshooting, observability |
| **User** | End-user behavior, workflows, limits, migration, UX |

### Audience Applicability Matrix (required in plan)

Include a markdown table in the Documentation section:

| audience_level | applicable | justification |
|----------------|------------|---------------|
| architect_expert | yes/no | … |
| technical_operator | yes/no | … |
| user | yes/no | … |

## Documentation Definition of Done (required in plan)

Include a table listing each documentation target:

| audience_level | applicable | applicability_reason | target_path_or_system | change_type | acceptance_check | owner | status | evidence |
|----------------|------------|----------------------|-------------------------|-------------|------------------|-------|--------|----------|

- **target_path_or_system:** repo path (`README.md`, `docs/...`) or external system name (`GitHub Wiki`, `Confluence/...`).
- **change_type:** `create` | `update` | `na`
- **status:** `planned` → becomes `done` during implement documentation phase
- **evidence:** link, PR path, or note for external wikis

## Inventory targets

Scan and list:

1. **Tracked docs:** `README.md`, `docs/**`, `CHANGELOG*`, ADRs, markdown under repo root.
2. **Wiki mirrors:** `wiki/`, `.wiki/`, `docs/wiki/` if present.
3. **External wikis:** checklist rows with owner, intended URL or space, and update scope.

## External wiki checklist

| system | page/slug | owner | status | evidence_link |

## Implement gate linkage

Implementation step 7 (documentation) will verify updates against this section. Agents must write `.implement-documentation-gate.json` beside the implement state file — schema is described in `prompts/implement/documentation.md`.

## Quick Mode

{{QUICK_MODE_NOTE}}
