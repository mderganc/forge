# CONTEXT.md format (domain glossary)

Adapted from [mattpocock/skills grill-with-docs](https://github.com/mattpocock/skills/blob/main/skills/engineering/grill-with-docs/CONTEXT-FORMAT.md).

## Structure

```md
# {Context Name}

{One or two sentences: what this context is.}

## Language

**Term**:
Definition in one or two sentences.
_Avoid_: overloaded alternatives
```

## Rules

- **Opinionated** — pick one canonical term; list alternatives under `_Avoid_`.
- **Tight definitions** — what it IS, not implementation detail.
- **Project-specific terms only** — not general programming jargon.
- **Glossary only** — no specs, tickets, or implementation decisions in `CONTEXT.md`.

## Single vs multi-context

- One `CONTEXT.md` at repo root (most repos).
- `CONTEXT-MAP.md` at root when multiple bounded contexts exist; each context has its own `CONTEXT.md`.

Create files lazily when the first term is resolved.
