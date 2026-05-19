---
name: forge:plan
description: Run the Forge planning workflow via the global forge CLI. When graphify-out/ exists, read GRAPH_REPORT.md before codebase search; follow GRAPHIFY blocks in each step.
---

When `graphify-out/` exists, follow every **GRAPHIFY** block in step output before grep/glob/search; read `graphify-out/GRAPH_REPORT.md` first; after code edits run `graphify update .`.

<invoke cmd="forge plan --step 1" />

## Plan modes

- **`default`** — Full governance (architecture depth, waves, contracts, risk/rollback, documentation tables).
- **`lite`** — Lower ceremony for short ad hoc work; **same task rigor** (exact paths, verify command + expected outcome, no placeholders).

If mode is not specified, step 1 asks the user to confirm with a recommendation. CLI: `--mode default|lite`. Persist default: `--mode lite --save-mode-preference`.

See `templates/plan-modes.md`.

**Forge Studio** is agent-internal only (optional visual approval) — see `templates/studio.md`.

## Safety Guardrails (plan phase)

- `forge:plan` is planning-only: do not edit product source code.
- Do not run git mutation commands during this workflow: `git add`,
  `git commit`, `git push`, `git reset`, `git rebase`, `git checkout`,
  `git restore`, `git cherry-pick`, `git merge`, `git stash`, `git tag`.
- Never use `--no-verify`.
- Keep final summaries command-free; describe outcomes in plain language.
