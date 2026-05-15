---
name: forge:develop
description: Run the Forge develop (investigation) workflow via the global forge CLI. Use when exploring a problem or feature before planning, with multi-step develop phases.
---

Do **not** modify repository files unless the user explicitly permits it; follow phase output for session memory under `.codex/forge-codex/memory/` only.

Medium/large scope may require a design spec and `.develop-spec-gate.json` before step 7; see phase output.

**When to use (process-first):** Open-ended features, unclear problem shape, or multiple credible approaches → develop before plan. Narrow bug with known fix may skip; failing tests or unknown root cause → consider `forge:diagnose` or `forge:test` first.

<invoke cmd="forge develop --step 1" />
