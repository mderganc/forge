# ADR format (sparse, high-bar)

Adapted from [mattpocock/skills grill-with-docs](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/ADR-FORMAT.md).

## When to offer an ADR

Only when **all three** are true:

1. **Hard to reverse** — changing mind later is costly.
2. **Surprising without context** — future readers will ask "why this way?"
3. **Real trade-off** — credible alternatives existed; you picked one for specific reasons.

Otherwise record the decision in `sketch-decisions.md` only.

## File location

`docs/adr/NNNN-short-title.md` (increment number; create `docs/adr/` lazily).

## Suggested sections

```md
# NNNN. Title

## Status
Accepted

## Context
What forced a decision.

## Decision
What we chose.

## Consequences
Positive and negative outcomes.
```

Keep ADRs short. Link from sketch handoff if develop must honor them.
