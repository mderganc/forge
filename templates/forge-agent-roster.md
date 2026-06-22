# Forge agent roster (canonical)

When a workflow step says **dispatch** or **spawn** an agent, use **only** these roles. Read the matching brief under `agents/` before delegating.

| Role | Brief | Typical phases |
|------|-------|------------------|
| **Architect** | `agents/architect.md` | Design investigation & solutions; plan architecture; code-review architecture mode |
| **Investigator** | `agents/investigator.md` | Design investigation evidence; diagnose evidence |
| **Planner** | `agents/planner.md` | Plan creation & task breakdown |
| **Backend Dev** | `agents/backend-dev.md` | Implement — backend tasks from the plan |
| **Frontend Dev** | `agents/frontend-dev.md` | Implement — frontend tasks from the plan |
| **QA Reviewer** | `agents/qa-reviewer.md` | Per-task / per-wave review |
| **Security Reviewer** | `agents/security-reviewer.md` | Auth, data, API, infra-sensitive work |
| **Critic** | `agents/critic.md` | Devil's-advocate challenge |
| **Doc-writer** | `agents/doc-writer.md` | Documentation capture at skill end |

## Hard rules

1. **Never invent agent names.** Forbidden examples: `backend-architect`, `Backend Architect`, `frontend-architect`, `backend-architect-agent`, or any `{layer}-{role}` composite.
2. **Layers ≠ roles.** In scope assessment, `Backend`, `Frontend`, and `Infra` describe *which parts of the stack* are touched — they are **not** spawn targets. One **Architect** covers all layers during design; **Backend Dev** / **Frontend Dev** are assigned later from the plan during implement.
3. **Sketch is dialogue-only.** `forge sketch` does **not** dispatch Forge agents or Task sub-agents — 1:1 with the user only.
4. **Spawn = roster row.** Match the orchestrator step (e.g. "Dispatch Architect") to the **Role** column exactly; pass `agents/<file>.md` as context.
