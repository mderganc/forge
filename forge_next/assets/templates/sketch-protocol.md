# Sketch protocol (pre-develop)

Organize **intent** before `forge design`. This is not solution brainstorming (no SCAMPER/Pugh here). Design owns investigation, solution families, and `docs/forge/specs/*-design.md`.

Protocol inspired by [mattpocock/skills](https://github.com/mattpocock/skills) grill-me / grill-with-docs (interview loop only; no "grill" in user-facing copy).

## Rules

1. **One question at a time.** Wait for the user's answer before the next question.
2. **Recommended answer** on every question — your best guess they can accept or correct.
3. **Decision tree** — walk branches until each dependency is resolved or explicitly deferred.
4. **Codebase first** — if a question can be answered by reading the repo, explore instead of asking.
5. **Do not** write `docs/forge/specs/*-design.md` in sketch; develop writes the design spec.

## Session artifact

Maintain **`sketch-decisions.md`** in the Forge memory directory (typically `.codex/forge-codex/memory/`):

```md
# Sketch decisions

## Topic
(one line)

## Resolved
- [decision]: [chosen answer] — [brief rationale]

## Deferred
- [open branch]: [what blocks resolution]

## Handoff notes for develop
- [bullets the Architect/PM must not lose]
```

Update after each resolved branch; do not batch silently.

## Question flow (suggested order)

Adapt to the topic; skip sections that are already clear.

1. **Outcome** — What does success look like? Who is affected?
2. **Constraints** — Hard vs soft? Non-goals?
3. **Scope boundary** — What's explicitly out of this change?
4. **Terminology** — Fuzzy words (account, user, cancel, …)? Pick canonical terms.
5. **Dependencies** — What must be decided before approach (data model, API shape, rollout)?
6. **Risks & unknowns** — What could invalidate the plan?
7. **Stop check** — Any unresolved branches left? If yes, keep asking one at a time.

## Domain docs mode

Check orchestrator output: **Domain docs mode** yes/no (or `--with-domain-docs` on step 1).

When **yes**:

- Challenge terms against existing `CONTEXT.md` (see `templates/CONTEXT-FORMAT.md`).
- Update glossary **inline** when a term is resolved — do not batch.
- Offer ADRs only when hard-to-reverse, surprising, and a real trade-off (see `templates/ADR-FORMAT.md`).
- `CONTEXT.md` is glossary only — not a spec or scratch pad.

When **no**:

- Record terminology only in `sketch-decisions.md`.

## Completion criteria (step 2 → 3)

- `sketch-decisions.md` exists with **Resolved** section populated.
- User confirms they are ready for **develop** (or **plan** if direction is fully locked).
- Unresolved items are listed under **Deferred** with owner/next action.
