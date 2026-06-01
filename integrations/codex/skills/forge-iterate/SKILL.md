---
name: forge:iterate
description: Meta-workflow chaining diagnose, plan, evaluate, implement, code-review, and test with loops. When graphify-out/ exists, read GRAPH_REPORT.md before codebase search; Graphify refresh runs at ship, not per workflow step.
---

When `graphify-out/` exists, read `graphify-out/GRAPH_REPORT.md` before grep/glob/search; refresh at ship (`forge ship --step 1` / `$forge:ship`). Workflow `forge … --step` skills do not print per-step GRAPHIFY banners. After code edits run `graphify update .`.

<invoke cmd="forge iterate --step 1" />

Use additional flags as needed for goal, target, and max loops (see forge CLI help). Advance `--step` as the orchestrator indicates.
