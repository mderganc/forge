# Forge design spec (template)

Use this structure when writing a design spec under `docs/forge/specs/YYYY-MM-DD-<slug>-design.md`.

## Review with the user in chunks

Do not dump the full spec in one message. **Present 2–4 digestible chunks** for review, get explicit acknowledgement on each before the next (short overview counts as chunk zero if helpful):

1. **Goals, non-goals, constraints** (this document through **Constraints**).
2. **Chosen design** + candidate snapshot — **Chosen design** and **Candidate comparison snapshot**.
3. **Risks and operations** — **Data / API / schema impact**, **Error handling and operational behavior**, **Test strategy**.
4. **Rollout, assumptions, open questions** — **Rollout / rollback** through **Open questions**.

After each chunk: “Any changes before we lock this section?” Then proceed. Final sign-off happens again at **Decision record** / gate JSON (see `develop/spec_gate`).

## Context

- Problem / opportunity
- Who is affected
- Links to investigation (`investigation.md`, diagnose report, etc.)

## Goals and non-goals

**Goals:**

- …

**Non-goals:**

- …

## Constraints

- Hard (security, compatibility, SLA, compliance)
- Soft (preferences, conventions)

## Candidate comparison snapshot

- Brief summary of 2–3 directions (from `solutions.md` / Stage 2)
- Trade-offs (1–2 bullets each)

## Chosen design

- Decision
- Rationale tied to constraints and user priorities
- Boundaries and interfaces (what owns what)

## Data / API / schema impact

- …

## Error handling and operational behavior

- …

## Test strategy

- What must be proven before shipping

## Rollout / rollback

- …

## Assumptions

- Explicit assumptions (challengeable)

## Decision record

- Date, participants (if any), approval note

## Open questions

- …
