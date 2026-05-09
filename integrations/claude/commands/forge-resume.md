---
name: forge:resume
description: Continue or clean up saved Forge workflow state.
---

## What to tell the user first

- **Resume** shows what’s in progress and the **next command** to continue a workflow, or helps **clean up** old state files safely.
- Ask whether they want to **continue** work or **inspect/cleanup** sessions.

Explain options in plain language before terminal details.

## What you run (agent)

Run `forge resume` (and `--cleanup` / `--cleanup --force` only when they explicitly want deletion). Interpret output into “here’s what’s active” / “here’s what was removed.”

## Exact CLI (reference)

- Status / next steps: `forge resume`
- Cleanup dry-run: `forge resume --cleanup`
- Cleanup delete: `forge resume --cleanup --force`
