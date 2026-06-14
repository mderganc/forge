# Sketch protocol (pre-design)

Organize **intent** before `forge design`. Iterative conversation — not a checklist. Design owns investigation, solutions, and `docs/forge/specs/*-design.md`.

## Conversation loop

1. **One question at a time** with a **recommended answer** the user can accept or correct.
2. **Synthesis every 2–3 exchanges** — briefly reflect what you heard; ask “What did I get wrong?” before the next question.
3. **Loop-back** — when new context changes an earlier answer, update `sketch-decisions.md` and name which decision you are revising.
4. **Thread pacing** — stay on a topic until settled; allow follow-ups. Do not force-advance to the next coverage area.
5. **User digressions** — park in **Deferred** or explore immediately if blocking; resume prior thread with a one-line recap.
6. **Codebase first** — read the repo when that answers faster than asking.
7. **No design spec** — do not write `docs/forge/specs/*-design.md` in sketch.

## Coverage hints (not mandatory order)

Use when helpful; skip what conversation already settled:

- Outcome and who is affected
- Constraints and non-goals
- Scope boundary
- Terminology
- Dependencies before approach
- Risks and unknowns

## Session artifact

Maintain **`sketch-decisions.md`** in Forge memory (typically `.codex/forge/memory/`):

```md
# Sketch decisions

## Topic
(one line)

## Resolved
- [decision]: [chosen answer] — [brief rationale]

## Deferred
- [open branch]: [what blocks resolution]

## Handoff notes for design
- [bullets design must not lose]
```

Update after each resolved branch; do not batch silently.

## Domain docs mode

When **`--with-domain-docs`**: apply `templates/CONTEXT-FORMAT.md` and `templates/ADR-FORMAT.md`. Otherwise record terminology only in `sketch-decisions.md`.

## Collaborative stop (before step 3)

Summarize **locked vs still open**. Ask: “Ready for **design**, or keep talking?”

Only run **`forge sketch --step 3`** after the user confirms (or says “ready for design”).

## Re-entrant step 2

Step 2 does not auto-advance to handoff. Re-run **`forge sketch --step 2`** to continue the dialogue.
