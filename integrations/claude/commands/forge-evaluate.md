---
name: forge:evaluate
description: Review work against a plan (evaluate workflow).
---

## What to tell the user first (plain language)

- **Evaluate** walks through structured review phases (plan understanding, completeness, correctness, quality, operational readiness, discussion, report).
- Help them choose a **mode**:
  - **Post-implementation** — compare what was built to the plan (most common after coding).
  - **Pre-implementation** — sanity-check the plan before implementation.
  - **Review** — quick pass on the current branch when there is no plan file.
- Ask which **plan** applies (path or keywords), or confirm **review-only** on the branch.
- Promise step-by-step progress: after each phase, summarize **what you found** in normal language before continuing.

**Do not** open your reply with backticked terminal commands. Offer short choices (“Post-review with `docs/plan.md`”, “Pre-review only”, “Branch review, no plan”).

## What you run (agent)

From the repo root, drive `forge evaluate` starting at step 1 with the chosen `--mode` and `--plan` when required. Use `--repo` if this workspace root is not the target repo. After each orchestrator step, paraphrase the prompt/output for the user, then run the next step they confirm.

## Exact CLI (reference — share only if they ask or use the terminal)

- Review (no plan): `forge evaluate --step 1 --mode review`
- Pre: `forge evaluate --step 1 --mode pre --plan "<plan path or keywords>"`
- Post: `forge evaluate --step 1 --mode post --plan "<plan path or keywords>"`

The orchestrator prints the next step command (2, 3, …); continue the chain after summarizing each phase for the user.
