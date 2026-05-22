# Phase 1: Define & Classify

Read `templates/diagnose-execution-playbooks.md` § Kepner-Tregoe, Cynefin, Change analysis before this phase.

## Agents to Dispatch
- **Investigator (lead):** Build IS/IS-NOT matrix, classify with Cynefin, perform Change Analysis
- **Architect (support):** Provide architecture context, identify affected components

## Problem specification sidecar (mandatory)

Persist **before step 2** to `.diagnose-problem-spec.json` beside diagnose state:

- `is_isnot`: WHAT / WHERE / WHEN / EXTENT — each with `is`, `is_not`, `distinction`
- `cynefin_domain`: Clear | Complicated | Complex | Chaotic
- `last_known_good`, `change_window`, `candidate_changes[]` (category + evidence)
- `routing_preferred`: technique names from `prompts/diagnose/technique_catalog.md` (exact spelling)
- `incident_profile` / `severity` tags for coverage matrix (e.g. `high_severity`, `sudden_deviation`)

Summary: {{PROBLEM_SPEC_SUMMARY}}

## IS/IS-NOT Matrix (mirror in sidecar)

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

Start `.diagnose-first-principles.json` (`invariants[]`; add `violations[]` in Phase 2–4).

Separate **observations** (logged facts) from **assumptions** (beliefs). Tag each assumption with how it will be validated or falsified.

## Incident profile → technique routing (use-case first)

Summarize the incident in one short paragraph (severity, sudden vs gradual, scope, safety/compliance touchpoints). Then pick **preferred** techniques using `prompts/diagnose/technique_catalog.md` § preferred-use-case routing **before** expanding to the full toolbox.

Copy `routing_preferred` into `.diagnose-technique-coverage.json` when you create it in Phase 3–7.

You must still execute the **mandatory core quartet** (first-principles, hypothesis-driven, 5 Whys, MECE tree) in later phases — this section records the **routing intent**.

**Phases 3–5** require a **{{HYPOTHESIS_MIN}}-candidate hypothesis register** (`.diagnose-hypotheses.json`), full elimination in Phase 4, and solutions only for **confirmed** root causes in Phase 5.

## Technique Coverage Matrix (draft)

Begin `.diagnose-technique-coverage.json` with all **20** catalog technique names (see playbooks § Coverage matrix).

| technique | status (applied/skip/defer) | rationale |
|-----------|-----------------------------|-----------|

Populate minimally here; finalize in Phase 7 report.

Write to `.codex/forge-codex/memory/investigator.md`
