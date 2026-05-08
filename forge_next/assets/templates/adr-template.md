# Architecture Decision Records (ADRs)

Lightweight records of significant architectural decisions. Based on Michael Nygard's ADR format.

## When to Create an ADR

Create an ADR when:
- Choosing between competing approaches (framework, library, pattern)
- Introducing a new architectural pattern or convention
- Making a decision that constrains future work
- Deviating from an established pattern for a specific reason

Do NOT create an ADR for trivial decisions (variable naming, formatting, single-line fixes).

## Location

Store in `.codex/forge-codex/adr/` with sequential numbering:
```
.codex/forge-codex/adr/
├── 0001-use-event-sourcing-for-audit.md
├── 0002-adopt-repository-pattern.md
└── 0003-jwt-over-session-cookies.md
```

## Template

```markdown
# [NUMBER]. [TITLE]

**Date:** [YYYY-MM-DD]
**Status:** proposed | accepted | deprecated | superseded by [ADR-NNNN]
**Beads:** [bd-xxx.adrN] (if beads tracking is active)

## Context

What is the issue that we're seeing that is motivating this decision or change?
What forces are at play (technical, business, team)?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

### Positive
- [benefit]

### Negative
- [trade-off or cost]

### Neutral
- [side effect that is neither good nor bad]
```

## Lifecycle

1. **proposed** — ADR written, under review
2. **accepted** — Team/user approved, decision is in effect
3. **deprecated** — Decision is no longer relevant (technology removed, feature deleted)
4. **superseded** — A newer ADR replaces this one (link to replacement)

## Rules

1. **ADRs are immutable once accepted.** To change a decision, write a new ADR that supersedes the old one. Update the old ADR's status to "superseded by [new ADR number]."
2. **Context section must explain the "why."** Future readers need to understand what constraints and trade-offs led to this decision.
3. **Consequences must be honest.** Every decision has trade-offs. An ADR with only positive consequences is incomplete.
4. **Keep them short.** An ADR should be one page. If it's longer, the decision might need to be split.
