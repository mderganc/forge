# UX review criteria

Use during `forge ux-review` steps 3–5. Keep findings tied to observed evidence.

## Mandate

Begin by understanding the app’s purpose, intended users, information architecture, major features, and critical user journeys. Then develop a structured review plan and maintain a coverage checklist while testing.

Walk through the application in a real browser as an actual user would. Visit every accessible page and state, click every relevant button, link, menu, tab, filter, and control, and exercise each available feature and workflow. Capture screenshots of every page and important state, including empty, loading, success, validation, and error states. Where appropriate, review the experience at multiple screen sizes.

Evaluate functional correctness, ease of use, navigation, discoverability, accessibility, visual hierarchy, content clarity, feedback, error prevention and recovery, responsiveness, and consistency across the application. Identify broken controls, dead ends, confusing interactions, missing states, inconsistent patterns, and unnecessary friction.

## Severity

| Severity | Meaning |
|----------|---------|
| **Blocker** | Task cannot be completed; data loss; serious privacy exposure in UI |
| **High** | Major friction or frequent failure on a critical journey |
| **Medium** | Clear UX defect on a common path; workaround exists |
| **Low** | Polish, minor inconsistency, rare edge |
| **Nit** | Taste / microcopy; optional |

## Dimensions (quick prompts)

| Dimension | Look for |
|-----------|----------|
| Functional correctness | Controls match labels; data persists |
| Ease of use | Steps, defaults, irreversible actions |
| Navigation | Wayfinding, back/cancel land sensibly |
| Discoverability | Features findable without hunting |
| Accessibility | Names, keyboard, focus, contrast (spot-check) |
| Visual hierarchy | Primary action clear |
| Content clarity | Labels, empty states, errors |
| Feedback | Pending / success / error |
| Error prevention & recovery | Validation, confirms, recoverable errors |
| Responsiveness | Usable at agreed viewports |
| Consistency | Patterns and terminology |

Accessibility spot-check ≠ full WCAG audit unless the user asks.

## States to force

| State | How |
|-------|-----|
| Empty | New account, cleared filters, zero results |
| Loading | Slow network / large lists when possible |
| Populated | Typical data |
| Validation | Empty required / invalid formats |
| Error | Failed auth, 4xx/5xx if safe |
| Success | Happy-path completion |

## Finding fields (required)

- Location, severity, user impact, reproduction steps, evidence (screenshot), actionable recommendation
