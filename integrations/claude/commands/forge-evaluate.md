---
name: forge:evaluate
description: Run `forge evaluate` (pre/post/review).
---

Run the Forge CLI from the current workspace repo.

Start evaluate (examples):
- Review current branch (no plan): `forge evaluate --step 1 --mode review`
- Pre-implementation: `forge evaluate --step 1 --mode pre --plan "<plan keywords or path>"`
- Post-implementation: `forge evaluate --step 1 --mode post --plan "<plan keywords or path>"`

Notes:
- If this workspace isn’t the repo you want, pass `--repo "<path>"`.
- The orchestrator will print the **next command** to run (step 2, 3, ...). Run it immediately.
