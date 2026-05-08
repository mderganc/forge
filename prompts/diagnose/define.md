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

Write to `.codex/forge-codex/memory/investigator.md`
