# Phase 1: Define & Classify

## Agents to Dispatch
- **Investigator (lead):** Build IS/IS-NOT matrix, classify with Cynefin, perform Change Analysis
- **Architect (support):** Provide architecture context, identify affected components

## IS/IS-NOT Matrix
| Dimension | IS | IS NOT | Distinction |
|-----------|-----|--------|------------|
| WHAT | | | |
| WHERE | | | |
| WHEN | | | |
| EXTENT | | | |

## Cynefin Classification

After gathering initial evidence, ask the user directly to confirm the problem
domain classification (per `templates/user-questions.md`).

- Question: `Which Cynefin domain best fits this problem?`
- Options:
  - `Clear` — cause and effect are obvious
  - `Complicated` — expert analysis is needed
  - `Complex` — cause and effect are only visible in retrospect
  - `Chaotic` — act first and stabilize before deeper analysis

The classification determines diagnostic strategy for subsequent phases.

## Change Analysis
- What changed immediately before the problem?
- Last known good state?
- Difference between working and broken?

## First-principles checkpoint (mandatory)

Before narrowing hypotheses:

1. **System invariants** — What must always hold for this system to be “healthy”?
2. **Expected vs observed** — Which invariants are violated by observations?
3. **Causal chain from fundamentals** — From physics/architecture/data-flow basics, what must be true upstream for the symptom to appear?

Separate **observations** (logged facts) from **assumptions** (beliefs). Tag each assumption with how it will be validated or falsified.

## Incident profile → technique routing (use-case first)

Summarize the incident in one short paragraph (severity, sudden vs gradual, scope, safety/compliance touchpoints). Then pick **preferred** techniques using `prompts/diagnose/technique_catalog.md` § preferred-use-case routing **before** expanding to the full toolbox.

You must still execute the **mandatory core quartet** (first-principles, hypothesis-driven, 5 Whys, MECE tree) in later phases — this section records the **routing intent**.

## Technique Coverage Matrix (draft)

| technique | status (applied/skip/defer) | rationale |
|-----------|-----------------------------|-----------|

Populate minimally here; finalize in Phase 7 report.

Write to `.codex/forge-codex/memory/investigator.md`
