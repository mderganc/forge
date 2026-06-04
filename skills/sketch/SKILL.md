---
description: |
  Organize intent and open decisions before develop. One question at a time with
  recommended answers; optional CONTEXT.md/ADRs with --with-domain-docs. Develop
  (not sketch) writes docs/forge/specs design specs.
---

# forge sketch — Pre-develop intent

When this skill activates, invoke the orchestrator via the `forge` launcher.

Invoking this skill authorizes running the sketch dialogue. Do not require separate
wording for delegation after `forge:sketch` has been invoked.

## When to use

| Situation | Prefer |
|-----------|--------|
| Fuzzy idea, pitch, or half-plan before investigation | **`forge:sketch`** |
| Ready for evidence + solution brainstorming + design spec | **`forge:develop`** |
| Direction fully locked; skip develop | **`forge:plan`** (rare from sketch) |

**Sketch** = intent organization. **Develop** = investigation, solution brainstorming, and **`docs/forge/specs/...-design.md`** for medium/large scope.

## Graphify

Optional: read `graphify-out/GRAPH_REPORT.md` before broad search. Refresh at ship (`forge ship --step 1`).

## Invocation

<invoke cmd="forge sketch --step 1" />

| Argument | When | Description |
|----------|------|-------------|
| `--step` | Always | Phase 1–3 |
| `--with-domain-docs` | Step 1+ | Allow `CONTEXT.md` glossary and sparse `docs/adr/` |
| `--state` | Resume | Path to sketch state file |

## Handoff

Default next: **`forge:develop`**. Develop reads `sketch-decisions.md` when present and authors the design spec — not sketch.
