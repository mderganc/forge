---
name: forge:code-review
description: Run the Forge code-review workflow via the global forge CLI. When graphify-out/ exists, read GRAPH_REPORT.md before codebase search; Graphify refresh runs at ship, not per workflow step.
---

When `graphify-out/` exists, read `graphify-out/GRAPH_REPORT.md` before grep/glob/search; refresh at ship (`forge ship --step 1` / `$forge:ship`). Workflow `forge … --step` skills do not print per-step GRAPHIFY banners. After code edits run `graphify update .`.

<invoke cmd="forge code-review --step 1" />
