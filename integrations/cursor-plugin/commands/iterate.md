---
name: forge:iterate
description: Run the Forge iterate meta-workflow (chained skills with quality loops).
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow. Summarize the current phase, gate files, and next action in plain English.

## Graphify

Runs at **ship** only (forge ship --step 1 / $forge:ship). This workflow does not print GRAPHIFY per step.


## What to tell the user first

- **Iterate** coordinates diagnose → plan → evaluate (pre) → implement → evaluate (post) → code-review → test, with inner loops for clean reviews and outer loops until a target metric is met or a max loop count.
- They must write small JSON **gate files** under Forge runtime memory (see iterate step output) so progress stays auditable.
- If the target metric is unclear, pause and ask them to define how it will be measured.

## What you run (agent)

Start the **iterate** workflow at step one from the repository root; pass goal, target, and max outer loops when available. Advance step by step; never paste launcher tokens into chat—describe the next phase only.

---
