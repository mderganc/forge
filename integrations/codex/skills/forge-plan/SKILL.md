---
name: forge:plan
description: Run the Forge planning workflow via the global forge CLI. Use when starting or continuing multi-step feature planning with Forge plan steps.
---

<invoke cmd="forge plan --step 1" />

## Safety Guardrails (plan phase)

- `forge:plan` is planning-only: do not edit product source code.
- Do not run git mutation commands during this workflow: `git add`,
  `git commit`, `git push`, `git reset`, `git rebase`, `git checkout`,
  `git restore`, `git cherry-pick`, `git merge`, `git stash`, `git tag`.
- Never use `--no-verify`.
- Keep final summaries command-free; describe outcomes in plain language.
