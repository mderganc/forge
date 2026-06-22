---
name: forge:takeover
description: Infer work and drive Forge skills until ship-ready.
---

## Hard rule — what the user sees

**Never show terminal commands** for this workflow unless the user asks.

## What to tell the user first

- **Takeover** infers the epic from sessions, handoffs, specs, or flags (`--issue`, `--design`).
- It drives child Forge skills until ship-ready quality gates pass.
- Assumptions and inferences are summarized at the end (deviations artifact).

## What you run (agent)

Invoke **takeover** through the launcher; auto-dispatch child skills per step output.

---
