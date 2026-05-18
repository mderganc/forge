---
name: forge:iterate
description: Meta-workflow chaining diagnose, plan, evaluate, implement, code-review, and test with loops. When graphify-out/ exists, read GRAPH_REPORT.md before codebase search; follow GRAPHIFY blocks in each step.
---

When `graphify-out/` exists, follow every **GRAPHIFY** block in step output before grep/glob/search; read `graphify-out/GRAPH_REPORT.md` first; after code edits run `graphify update .`.

<invoke cmd="forge iterate --step 1" />

Use additional flags as needed for goal, target, and max loops (see forge CLI help). Advance `--step` as the orchestrator indicates.
