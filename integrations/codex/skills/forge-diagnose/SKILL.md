---
name: forge:diagnose
description: Run the Forge diagnose workflow for deep root-cause analysis. When graphify-out/ exists, read GRAPH_REPORT.md before codebase search; follow GRAPHIFY blocks in each step.
---

When `graphify-out/` exists, follow every **GRAPHIFY** block in step output before grep/glob/search; read `graphify-out/GRAPH_REPORT.md` first; after code edits run `graphify update .`.

**Hypothesis register:** Phase 3 writes `.diagnose-hypotheses.json` (≥10 falsifiable candidates, ≥4 fishbone categories). Phase 4 eliminates every entry before confirming root cause. Steps 4–5 may gate until the user confirms.

<invoke cmd="forge diagnose --step 1" />
