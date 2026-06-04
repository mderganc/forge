---
name: forge:develop
description: Run the Forge develop (investigation) workflow via the global forge CLI. Use when exploring a problem or feature before planning. When graphify-out/ exists, read GRAPH_REPORT.md before codebase search; Graphify refresh runs at ship, not per workflow step.
---

Do **not** modify repository files unless the user explicitly permits it; follow phase output for session memory under `.codex/forge/memory/` only (legacy `.codex/forge-codex/memory/`).

When `graphify-out/` exists, read `graphify-out/GRAPH_REPORT.md` before grep/glob/search; refresh at ship (`forge ship --step 1` / `$forge:ship`). Workflow `forge … --step` skills do not print per-step GRAPHIFY banners. After code edits run `graphify update .`.

Medium/large scope may require a design spec and `.develop-spec-gate.json` before step 7; see phase output.

**Forge Studio** is agent-internal only (visual develop gates) — see `templates/studio.md`; not a user command.

**When to use (process-first):** Open-ended features, unclear problem shape, or multiple credible approaches → develop before plan. Narrow bug with known fix may skip; failing tests or unknown root cause → consider `forge:diagnose` or `forge:test` first.

<invoke cmd="forge develop --step 1" />
