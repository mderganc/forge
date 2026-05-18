---
name: forge:implement
description: Run the Forge implement workflow to execute a plan in waves. When graphify-out/ exists, read GRAPH_REPORT.md before codebase search; follow GRAPHIFY blocks in each step.
---

When `graphify-out/` exists, follow every **GRAPHIFY** block in step output before grep/glob/search; read `graphify-out/GRAPH_REPORT.md` first; after code edits run `graphify update .`.

<invoke cmd="forge implement --step 1" />
