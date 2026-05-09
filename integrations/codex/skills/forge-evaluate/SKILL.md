---
name: forge:evaluate
description: Run Forge evaluate (pre/post/review) via the global forge CLI. Use when evaluating work against a plan or running Forge evaluation steps.
---

Invoke:

<invoke cmd="forge evaluate --step 1 --mode review" />

Or pre/post mode:

<invoke cmd="forge evaluate --step 1 --mode pre --plan '<plan path or keywords>'" />
<invoke cmd="forge evaluate --step 1 --mode post --plan '<plan path or keywords>'" />
