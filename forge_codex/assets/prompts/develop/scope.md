# Scope Assessment & Team Composition

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
