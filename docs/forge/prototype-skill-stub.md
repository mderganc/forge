# forge:prototype — design stub (NOT YET INVOKABLE)

> **Status: future build.** This document is a contract placeholder only.
> There is no `forge prototype` CLI, skill package, or runnable workflow yet.
> Sketch and Design must still **offer** this option when its criteria apply so
> users see the intended path; agents must not claim the skill exists today.

## Trigger (offer rule)

Sketch and Design **must explicitly offer** `forge:prototype` when they identify
**one** unresolved **logic/state** or **UI-shape** question that cannot be
settled reliably from discussion, codebase evidence, or written options.

This is a **decision aid**, not a scope expansion. Do not offer prototype
merely “to be thorough.”

## Use when / do not use when

| Use when | Do not use when |
|----------|-----------------|
| One named design question remains hard to settle on paper | Behavior is already broken → use `forge:diagnose` |
| User needs to feel a state model or see UI variants | Intent is still foggy → use `forge:sketch` |
| Answer will unlock Recommended scope | Question is already answered by evidence/options |

## Branches (future)

1. **Logic** — tiny interactive CLI/TUI around a pure reducer/state machine/function set; surface full state after each action.
2. **UI** — 2–3 structurally different read-only variants (prefer host page + `?variant=`); throwaway route only if no host exists.

## Guardrails (future)

- State the question, assumption, and exit criterion before code.
- One command to run; project’s existing runtime only.
- In-memory/stubbed data; no production persistence or live mutations.
- No production tests, polish, agent team, or full review loop while disposable.
- Structural review applies **before promoting** any prototype logic into product code.
- Capture a **verdict** (question + answer); delete or park prototype on a throwaway branch — never merge TUI/switcher/losing variants to main.

## Verdict schema (future artifact)

```markdown
# Prototype verdict
**Question:** …
**Branch:** logic | ui
**Run:** <one command or URL>
**Observed:** …
**Decision:** …
**Cleanup:** deleted | throwaway branch <name>
```

## Routing

- **Sketch:** offer when destination depends on the unresolved question; record under Not yet specified.
- **Design:** offer after investigation leaves a blocked candidate choice; verdict becomes evidence only — cannot introduce new requirements.

## Stops at

A captured verdict feeding sketch/design memory. Does **not** replace design, plan, or implement.
