---
name: forge:iterate
description: Run the Forge iterate meta-workflow via the global forge CLI.
---

Use when the user wants a **multi-skill delivery loop**: diagnose, plan, evaluate, implement, code review, and tests with repeated quality passes until targets are met.

If `graphify-out/` exists: read `graphify-out/GRAPH_REPORT.md` before grep/glob/semantic search; refresh at ship (`forge ship --step 1`); workflow `--step` does not print per-step GRAPHIFY banners. After code edits run `graphify update .`.

Run **iterate** from the repo root starting at step one. Follow each phase prompt; gate files under `.iterate-gates/` record progress.

---
