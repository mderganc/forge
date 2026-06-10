---
name: forge:sketch
description: Organize intent and open decisions before design via the global forge CLI. Optional --with-domain-docs for CONTEXT.md/ADRs. Design writes named design specs, not sketch.
---

Do **not** write `docs/forge/specs/*-design.md` in sketch — design owns that.

When `graphify-out/` exists, you may read `graphify-out/GRAPH_REPORT.md` before codebase search; refresh at ship (`forge ship --step 1`).

**When to use:** Messy intent before investigation — problem framing, constraints, terminology. **Not** for solution brainstorming (use `forge:design`).

<invoke cmd="forge sketch --step 1" />

Add `--with-domain-docs` on step 1 when glossary/ADR updates are desired.
