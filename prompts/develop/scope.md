# Scope Assessment & Team Composition

{{DEVELOP_NO_EDIT_POLICY}}

## Dialogue before labels

Treat this step as **discovery**, not a form to fill. Before fixing task type and layers:

- **Surface opportunities:** What could be better, faster, simpler, or newly possible—even if the user started with a narrow bug or chore?
- **Co-develop the problem statement:** Reframe once or twice with the user (“Are we solving X, or is the real goal Y?”).
- **Brainstorm requirements at a high level:** Success signals, non-goals, and “delighters” belong here as much as acceptance criteria.

Stay in conversation until the user confirms the framing—or explicitly asks to move on.

## Scope

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

### Complexity

Estimate automatically from scope:
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
