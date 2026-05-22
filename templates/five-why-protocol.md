# Five-Why Investigation Protocol

Primary investigation methodology for the forge-codex team. Combines the five-why framework with systematic-debugging's pattern analysis and hypothesis testing at each layer.

## Core Principle

> Always assume you're wrong and validate. Every hypothesis must be tested before being accepted as a cause.

## Task Type Framing

| Task Type | Investigation Question | "Root Cause" Means |
|-----------|----------------------|-------------------|
| Bugfix | What's broken, why, and what's the chain of causation? | Actual root cause of the defect |
| Refactor | What's wrong with the current design, and why did it get this way? | Underlying design decisions causing the pain |
| Feature | What technical challenges exist, what requirements are underspecified? | Core technical risks and requirement gaps |

## The Five-Why Process

For each identified issue or challenge, drill through up to 5 layers. Stop when you reach a cause that is **actionable** and **explains the full chain above it**.

### Layer Template

Why [N]: [Statement of cause at this layer]
  → Pattern Analysis: Compare against working examples in the codebase.
     What works elsewhere that doesn't work here? Is this pattern repeated?
  → Hypothesis: "I think [X] because [Y]"
  → Test: [Minimal test to confirm or deny — specific command, code check, or grep]
  → Evidence: [Result of the test — paste actual output, not summaries]
  → Verdict: Confirmed / Denied / Inconclusive
     If Denied → form new hypothesis at this layer
     If Confirmed → proceed to next Why layer
     If Inconclusive → gather more evidence before proceeding

### Bugfix Example

Why 1: Login fails with 500 error
  → Pattern Analysis: Other auth endpoints (register, reset) work fine
  → Hypothesis: "Login handler has a unique code path that crashes"
  → Test: Check logs for stack trace on login endpoint
  → Evidence: "TypeError: Cannot read property 'hash' of undefined at auth.js:47"
  → Verdict: Confirmed — the user object is undefined

Why 2: User object is undefined in login handler
  → Pattern Analysis: Register handler fetches user the same way and works
  → Hypothesis: "Login query has a different WHERE clause that returns no results"
  → Test: Compare login vs register SQL queries
  → Evidence: Login uses `email` column, register uses `username` — but the login form sends `username`
  → Verdict: Confirmed — column/field mismatch

Why 3: Login query uses wrong column
  → Pattern Analysis: The query was correct in the previous version (git blame)
  → Hypothesis: "Recent migration renamed the column but login query wasn't updated"
  → Test: git log --oneline -10 -- db/migrations/
  → Evidence: Migration 20260325 renamed `username` to `email` in users table
  → Verdict: Confirmed — migration broke the login query

ROOT CAUSE: Migration 20260325 renamed column without updating the login query.

### Feature Example (Requirements Deepening)

Why 1: "We need OAuth2" → Why?
  → Hypothesis: "Users need SSO with corporate identity providers"
  → Test: Ask user to confirm
  → Evidence: User confirms — enterprise customers require SSO

Why 2: "Users can't SSO with corporate IdPs" → Why not?
  → Pattern Analysis: Current auth only supports username/password
  → Hypothesis: "No OAuth2/OIDC support exists in the codebase"
  → Test: Grep for OAuth, OIDC, identity provider references
  → Evidence: Zero results — no OAuth infrastructure exists

Why 3: "No OAuth infrastructure" → Why is this a problem now?
  → Hypothesis: "New enterprise customer requirement"
  → Test: Ask user about driver
  → Evidence: SOC2 audit requires centralized identity management

ROOT REQUIREMENT: SOC2-compliant identity federation for enterprise customers.

## Rules

1. **Never skip the test step.** A hypothesis without evidence is a guess.
2. **Stop when actionable.** Not every issue needs 5 layers. If layer 3 reveals an actionable root cause, stop there.
3. **One root cause per chain.** If an issue has multiple contributing causes, run separate five-why chains for each.
4. **Evidence must be specific.** "I checked and it looks wrong" is not evidence. Paste the output, cite the line number, quote the log entry.
5. **Failed hypotheses are valuable.** Record denied hypotheses — they narrow the search space and prevent revisiting.
6. **Source data over synthesis.** At every layer, the Evidence field must contain first-hand data (actual output, file:line, log entries). If a prior agent or LLM judge has already assessed this area, include their assessment as context but anchor the verdict in your own direct observation of the source data.

## Integration with Superpowers

If `superpowers:systematic-debugging` is available (bugfix tasks):
- Invoke it to structure the initial evidence gathering (Phase 1: Root Cause Investigation)
- Its pattern analysis and hypothesis testing phases map directly to each Why layer
- The five-why framework adds the "keep going deeper" discipline that systematic-debugging alone may not enforce

If `superpowers:brainstorming` is available (feature tasks):
- Invoke it to explore requirements with the user during Why 1-2
- The five-why deepening happens within the brainstorming dialogue

## Diagnose RCA (mandatory for `forge:diagnose`)

Sidecar: `.diagnose-five-whys.json` beside diagnose state. Playbook: `templates/diagnose-execution-playbooks.md` § Five Whys.

### Causal linkage (non-negotiable)

Each layer answers **why the previous `because` occurred** — not a new topic.

- **Question formula:** `Why did [specific mechanism from layer N because] happen?`
- Layer N+1 `why_question` must reference the parent `because` (shared subject/mechanism terms).
- **Forbidden:** meta questions (“why is this important?”), blame, unrelated subsystems, symptom re-labeling.

### Stop checklist (validated early stop)

Stop only when the bottom `because` / `root_cause` is:

1. **Actionable** — a person can change code, config, process, or test.
2. **Specific** — file:line, migration id, config key, or named process step.
3. **But-for** — if this cause were absent, the failure would not occur (`but_for` field required).
4. **Not symptom-level** — not “server crashed”, “API returned 500”, “test failed”.

Record `stop_reason`: `actionable_process_gap` | `defect` | `config` | `data` | `dependency` | `infrastructure` | `design`.

Minimum **3** linked layers per chain unless stop checklist passes with evidence at layer 2 (rare).

### Phase timing

| Phase | Action |
|-------|--------|
| **3 Decompose** | Draft 1–2 chains on **leading** register branches (exploratory). |
| **4 Analyze** | **Finalize** chains only for `confirmed` hypothesis IDs; extend until stop checklist passes. |
| **5+** | Orchestrator gates validate sidecar before solutions. |

### Good vs lazy chain

**Good:** Why 1 because → Why 2 explains that mechanism → Why 3 explains deeper mechanism → root = missing migration update.

**Lazy (reject):** Why 1 API 500 → Why 2 users unhappy → Why 3 business impact → Why 4 management pressure (topic drift).
