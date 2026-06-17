---
name: forge:evaluate
description: Plan review (pre) or implementation audit (post). Use code-review for full-team review.
---

<invoke cmd="forge evaluate --mode pre --plan '<plan path>'" />
<invoke cmd="forge evaluate --mode post --plan '<plan path>'" />

When `graphify-out/` exists, read `graphify-out/GRAPH_REPORT.md` before search; refresh at ship (`forge ship --step 1`).

