# Scope Assessment & Team Composition

{{DEVELOP_NO_EDIT_POLICY}}

**Studio (internal):** {{STUDIO_STATUS}} — see `templates/studio.md`. If enabling, use a **separate** opt-in message; users open a URL only, never run `forge studio`.

**Studio log (if any):** {{STUDIO_LOG}}

## Dialogue before labels

Treat this step as **discovery**, not a form to fill. Before fixing task type and layers:

- **Surface opportunities:** What could be better, faster, simpler, or newly possible—even if the user started with a narrow bug or chore?
- **Co-develop the problem statement:** Reframe once or twice with the user (“Are we solving X, or is the real goal Y?”).
- **Brainstorm requirements at a high level:** Success signals, non-goals, and “delighters” belong here as much as acceptance criteria.

Stay in conversation until the user confirms the framing—or explicitly asks to move on.

## Prior sketch session

If `.codex/forge-codex/memory/sketch-decisions.md` exists:

- Read it before fixing scope tier and task type.
- Carry **Resolved** decisions into `project.md` and investigation framing.
- Do not re-litigate branches already closed in sketch unless the user asks.

If intent is still unclear and there is no sketch artifact, suggest **`forge sketch`** before continuing deep investigation.

## Scope tier (required — dual track)

After dialogue, classify **`trivial`**, **`medium`**, or **`large`** using **all** signals below (deterministic).

### Signals

Count **high-risk** and **medium-risk** indicators:

| Risk | Indicator |
|------|-----------|
| **High** | Security / auth / data-integrity / compliance / PII |
| **High** | Breaking API or schema change, or migration with rollback difficulty |
| **High** | Cross-cutting architecture (multiple bounded contexts or subsystems) |
| **Medium** | 3–10 files or multiple packages touched |
| **Medium** | New observability, SLO, or operational runbook burden |
| **Medium** | Significant UX or workflow change for end users |
| **Low** | 1–2 files, localized change, clear rollback |

### Tier rules

- **`large`:** ≥2 **high-risk** signals.
- **`medium`:** 1 **high-risk** OR ≥2 **medium-risk** signals (and not `large`).
- **`trivial`:** everything else after honest assessment.

### What each tier means

- **`trivial`:** Session memory artifacts only; **no** formal `docs/forge/specs/...` design spec required before `plan`.
- **`medium` | `large`:** Formal design spec + self-review + user approval **before** `forge develop --step 7` (see `develop/spec_gate` appended at step 6).

## Record scope for the orchestrator

Write **`develop-scope.json`** in the **Forge runtime memory directory** (same tree as `project.md`; typically `.codex/forge/memory/`, or legacy `.codex/forge-codex/memory/`):

```json
{
  "scope_tier": "trivial",
  "scope_rationale": "1–2 sentences: which signals fired and why."
}
```

Valid `scope_tier` values: `trivial`, `medium`, `large`.

Also log the same tier and rationale under a `## Scope tier` section in `project.md`.

## Original task questions

First, infer task type and layers from the user's initial description. If
anything is unclear, ask the user directly to confirm (per
`templates/user-questions.md`).

- Question 1: `What type of task is this?`
  - `Feature` — new functionality or enhancement
  - `Bugfix` — fix broken behavior
  - `Refactor` — improve structure without changing behavior
- Question 2: `Which layers does this task touch?`
  - `Frontend` — UI or client-side changes
  - `Backend` — API or server-side changes
  - `Infra` — infrastructure, CI/CD, or deploy
  - `Something else` — let the user specify manually

### File-count hint (secondary)

Estimate breadth (does **not** override risk-based tiering):

- Small (1-2 files)
- Medium (3-10 files)
- Large (10+ files)

## Team Composition

Base roles for every task: **Architect, Investigator, QA, Critic, Doc-writer.**

**Security activation rule:** Add the Security role whenever *any* selected layer includes Backend or Infra, or when auth/data-integrity concerns are present regardless of layer.

| Task Type | Additional Roles |
|-----------|-----------------|
| Feature | +Security (if Backend or Infra selected) |
| Bugfix | +Security (if auth/data) |
| Refactor | +Security (if auth/data) |

Record team composition in project.md.
