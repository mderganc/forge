---
name: forge:evaluate
description: Run Forge evaluate (pre/post/review) via the global forge CLI. When graphify-out/ exists, read GRAPH_REPORT.md before codebase search; follow GRAPHIFY blocks in each step.
---

When `graphify-out/` exists, follow every **GRAPHIFY** block in step output before grep/glob/search; read `graphify-out/GRAPH_REPORT.md` first; after code edits run `graphify update .`.

Invoke:

<invoke cmd="forge evaluate --step 1 --mode review" />

Or pre/post mode:

<invoke cmd="forge evaluate --step 1 --mode pre --plan '<plan path or keywords>'" />
<invoke cmd="forge evaluate --step 1 --mode post --plan '<plan path or keywords>'" />
