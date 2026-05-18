---
name: forge:plan
description: Turn direction into a detailed implementation plan.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow. No argv, no flag dumps—only plain-English progress and choices.

## What to tell the user first

- **Plan** produces architecture, tasks, waves, risks, rollback, and documentation scope.
- **Modes:** `default` (full governance) or `lite` (concise, same task rigor). If they did not pick a mode, step 1 will recommend one and ask them to confirm.
- Confirm starting a **new** planning session or send them to **forge:resume** if state already exists.
- Offer normal-language recap between phases.

## What you run (agent)

Run the **plan** workflow from the repo root starting at step one; use abbreviated pacing only when they ask. Advance stepwise via the launcher; never paste subsequent launcher lines into chat—summarize the next phase name and intent.

Optional: `--mode default|lite` when scope is already clear. `--quick` abbreviates review loops only; it does not relax task verification requirements.

---
