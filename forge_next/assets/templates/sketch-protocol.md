# Sketch protocol (pre-design)

Organize **intent** before `forge design`. Iterative conversation — not a checklist. Design owns investigation, solutions, and `docs/forge/specs/*-design.md`.

Inspired by [mattpocock/skills wayfinder](https://github.com/mattpocock/skills/blob/main/skills/engineering/wayfinder/SKILL.md) map structure — adapted for 1:1 memory-only sessions (no issue tracker).

Size and expansion rules: **`templates/scope-size-model.md`**.

## Plan, don't do

Sketch records **decisions**, not deliverables. The pull to implement or write a design spec is usually the signal to hand off to **design**. Do not write `docs/forge/specs/*-design.md` in sketch.

## Conversation loop

1. **One question at a time** with a **recommended answer** that stays inside the user's original ask (Recommended scope).
2. **Synthesis every 2–3 exchanges** — briefly reflect what you heard; ask “What did I get wrong?” before the next question.
3. **Loop-back** — when new context changes an earlier answer, update `sketch-decisions.md` and name which section you are revising (Decisions so far / Not yet specified / Out of scope / Scope expansion / Size).
4. **Thread pacing** — stay on a topic until settled; allow follow-ups. Do not force-advance to the next coverage area.
5. **User digressions** — park in **Not yet specified** or explore immediately if blocking; resume prior thread with a one-line recap.
6. **Codebase first** — read the repo when that answers faster than asking.
7. **No design spec** — do not write `docs/forge/specs/*-design.md` in sketch.
8. **Provisional size** — record **small / medium / large** early under `## Size`. When unsure, pick the lower tier. Escalating size needs an explicit user yes.

## Coverage hints (not mandatory order)

Use when helpful; skip what conversation already settled. For **small** size, keep coverage minimal (destination + locked decisions + size).

- Destination and who is affected
- Constraints
- Scope boundary (Recommended vs expansion)
- Terminology
- Dependencies before approach
- Risks and unknowns

## Session artifact

Maintain **`sketch-decisions.md`** in Forge runtime memory (path from orchestrator output — typically `.forge/memory/`):

```md
# Sketch decisions

## Destination
<1–2 lines: what “ready for design” looks like — spec, locked decision, or change>

## Size
<small | medium | large> — <one-line rationale; bias lower when unsure>

## Recommended scope (original ask)
- <what we are actually doing>

## Decisions so far
- [decision]: <one-line gist> — <brief rationale>

## Not yet specified
<!-- fog: in-scope but too vague to decide; graduates when frontier advances -->
- <suspected question / area>

## Scope expansion (optional — not recommended unless user opts in)
<!-- opportunities / delighters; never the default path -->
- Opportunity: <gist>
- Delighter: <gist>

## Out of scope
<!-- consciously ruled out for this effort; never graduates -->
- <gist> — <why out of scope>

## Handoff notes for design
- <bullets design must not lose>
- Prototype offer (if applicable): <question> — future forge:prototype (not yet invokable); see docs/forge/prototype-skill-stub.md
```

Update after each resolved branch; do not batch silently.

### Fog vs resolved vs expansion vs out of scope

- **Decisions so far** — question is sharp and answered (even if the answer is “we'll decide in design”).
- **Not yet specified** — in-scope fog you cannot phrase precisely yet. Graduates into Decisions so far or new questions as the conversation advances.
- **Scope expansion** — optional upsizing (opportunities/delighters). Not recommended unless the user opts in. Distinct from Out of scope.
- **Out of scope** — consciously ruled out for this effort. A scoping act, not a deferred decision — does not move to Decisions so far.

## Prototype offer (mandatory when applicable)

If one unresolved **logic/state** or **UI-shape** question cannot be settled from discussion, codebase evidence, or written options, **explicitly offer** the future `forge:prototype` skill as a decision aid (not a scope expansion). Record the question under Not yet specified. The skill is **not yet invokable** — see `docs/forge/prototype-skill-stub.md`. If discussion already answers the question, do not offer prototype “to be thorough.”

## Domain docs mode

When **`--with-domain-docs`**: apply `templates/CONTEXT-FORMAT.md` and `templates/ADR-FORMAT.md`. Otherwise record terminology only in `sketch-decisions.md`.

## Collaborative stop (before step 3)

Summarize **destination**, **size**, **recommended scope**, **decisions locked**, **not yet specified**, **scope expansion** (if any), and **out of scope**. Ask: “Ready for **design**, or keep talking?”

Only run **`forge sketch --step 3`** after the user confirms (or says “ready for design”). Destination must be filled.

## Re-entrant step 2

Step 2 does not auto-advance to handoff. Re-run **`forge sketch --step 2`** to continue the dialogue.
