# Stage 2 — Solution Generation

Stage 2 is a **PM-orchestrated three-dispatch loop**, not a single Architect run. The PM wraps the Architect's brainstorming work with interactive decision gates so the user's judgment shapes framing, technique choice, candidate selection, and scoring weights.

- Methods catalog: `templates/brainstorming.md` (read by the Architect)
- Decision gates: `templates/brainstorming-gates.md` (read by the PM only)
- Scoring rubric: `templates/scoring-rubric.md`

Intermediate artifacts written to `.codex/forge-codex/memory/`:
- `solution-requirements.md` — Requirements Context + How-Might-We framings (after Dispatch 1)
- `divergent-ideas.md` — raw ideas grouped into families (after Dispatch 2)
- `solutions.md` — draft candidates after Dispatch 2 (unscored); final candidates + scores + recommendation after Dispatch 3

## Overview

```
Dispatch 1 → Gate 1 → Dispatch 2 → Gate 2 Q1+Q2 → Dispatch 3 → Gate 2 Q3 (conditional)
 Phase 1     HMW +     Phase 2 +     Families +     Pugh +       Tiebreak
             techniques Phase 3 1–3   priority dim   weighted
                        (draft)                      scoring
```

Each gate is PM-owned and runs via `templates/brainstorming-gates.md`. Each dispatch is Architect-owned and reads only `templates/brainstorming.md` plus prior artifacts — the Architect never touches the gates file.

## 1. Dispatch 1 — Requirements Exploration (Phase 1 only)

Dispatch **Architect** with:

> **Task: Brainstorm Phase 1 only — Requirements Exploration**
>
> Read `.codex/forge-codex/memory/investigation.md` for the confirmed root causes.
>
> Follow `templates/brainstorming.md` **Phase 1 only**:
>
> - Answer the 6 exploration questions (affected parties / success criteria / hard constraints / soft constraints / adjacent systems / prior art).
> - Emit the Requirements Context block.
> - Generate 3–5 How-Might-We framings per the HMW rules. Mark your suggested driver.
> - If the task type is `feature`, append a Job Story.
>
> Write everything to `.codex/forge-codex/memory/solution-requirements.md` and return.
>
> **Do not run Phase 2 or Phase 3. Do not generate ideas or candidates.** Stop at the Phase 1 → Phase 2 boundary.

## 2. Gate 1 — Pre-Divergence (PM)

Execute `templates/brainstorming-gates.md` **Gate 1**:

1. Write `.codex/forge-codex/memory/current-step.md` with `Step: gate-1-waiting` before asking the user.
2. Read `solution-requirements.md` to populate Q1 options (HMW candidates) with the Architect's suggested driver first + `(Recommended)`.
3. Apply the Autonomy Routing table — Level 2/3 skip the gate, use the suggested HMW, and log the choice in `project.md`.
4. Record user answers (or chosen defaults) in `project.md` under the Stage 2 marker and in `current-step.md` with `Step: gate-1-answered`.

## 3. Dispatch 2 — Divergence + Candidate Development (draft `solutions.md`)

Dispatch **Architect** with:

> **Task: Brainstorm Phases 2 and 3 Steps 1–3 — divergent ideas + draft candidates**
>
> User decisions from Gate 1:
> - Driver HMW: [exact HMW text from user]
> - Advanced techniques to add: [list from user, or "none"] (core SCAMPER + Reverse Brainstorming + Constraint Removal are always applied; bugfix tasks also auto-apply 5W1H/Starbursting)
>
> Read `.codex/forge-codex/memory/investigation.md` and `.codex/forge-codex/memory/solution-requirements.md`.
>
> Follow `templates/brainstorming.md`:
>
> **Phase 2 — Divergent Thinking.** Apply each selected technique and generate raw ideas in the required output format. Cluster into solution families (one family per `###` header) and tag each idea with the technique that produced it. Write to `.codex/forge-codex/memory/divergent-ideas.md`.
>
> **Phase 3 Steps 1–3 only:**
> 1. Group ideas into families.
> 2. Eliminate obvious non-starters (record reasoning).
> 3. If >4 families survive, apply the ICE pre-filter (`brainstorming.md` Step 2b) to cut to 4.
> 4. Develop each surviving family into a full candidate with approach / pros / cons / open questions.
>
> Write the developed candidates to `.codex/forge-codex/memory/solutions.md` as a **draft** — no scoring tables, no Pugh Matrix, no recommendation yet.
>
> **Stop at the Phase 3 Step 3 → Step 3b boundary.** Do not run the Pugh Matrix. Do not score. Do not recommend. Return once `divergent-ideas.md` and draft `solutions.md` both exist.

## 4. Gate 2 Q1 + Q2 — Pre-Scoring (PM)

Execute `templates/brainstorming-gates.md` **Gate 2 Q1 + Q2**:

1. Write `current-step.md` with `Step: gate-2-q1q2-waiting`.
2. Read the draft `solutions.md` to populate Q1 options (candidate titles + 1-line summaries). If there are >4 draft candidates (rare — Dispatch 2's ICE filter should have cut to 4, but belt-and-braces), apply ICE again before presenting.
3. Ask Q1 (family selection) + Q2 (priority dimension) together in a concise user prompt.
4. Apply the Autonomy Routing table: Level 2 skips Q1 but still asks Q2; Level 3 skips both and uses "Balanced" weights.
5. Record answers in `project.md` and update `current-step.md` with `Step: gate-2-q1q2-answered` plus the selected weights.

## 5. Dispatch 3 — Convergence Scoring (finalize `solutions.md`)

Dispatch **Architect** with:

> **Task: Score candidates and recommend (Phase 3 Steps 3b–5)**
>
> User decisions from Gate 2:
> - Candidates to score: [list from Q1, or "all candidates" if Level 2/3]
> - Scoring weights (per `brainstorming-gates.md` weight translation): Q=[w], T=[w], C=[w], R=[w], E=[w]
>
> Read `.codex/forge-codex/memory/solutions.md` (draft) and `.codex/forge-codex/memory/investigation.md`.
>
> Remove any candidates the user did not pick from the main candidate list — move them to an "Also Considered" section at the bottom of `solutions.md` with their draft approach preserved.
>
> Follow `templates/brainstorming.md` Phase 3 **Steps 3b–5 only**:
> 1. Run the Pugh Matrix head-to-head comparison on the selected candidates.
> 2. Score every selected candidate using `templates/scoring-rubric.md`, applying the user's weights when computing Priority. Justify every raw score.
> 3. Cross-solution check: any conflicts? Any compound solutions worth highlighting?
> 4. State a recommendation per root cause with rationale that explicitly references the user's priority dimension.
>
> Overwrite `.codex/forge-codex/memory/solutions.md` with the final version: draft candidates → candidates with Pugh row + scoring table + recommendation, plus the "Also Considered" section and a note recording the user's weights. Create beads issues per scored option and label the recommended one.

## 6. Gate 2 Q3 — Tiebreak (conditional, PM)

After Dispatch 3 returns, the PM reads the final `solutions.md` and checks:

- Does the Pugh Matrix return a net-zero winner (no candidate dominates)?
- OR are the top two weighted rubric scores within 0.5 of each other?

If **yes** to either, Gate 2 Q3 fires **regardless of autonomy level** (this is the escalation override from the develop workflow rules). Write `current-step.md` with `Step: gate-2-q3-waiting`, ask the user the Q3 tiebreak question, and record the winner in `solutions.md` and `project.md`.

If **no**, skip Q3 and proceed to finalize.

## 7. Finalize

Update `.codex/forge-codex/memory/solutions.md` with a closing block:

```
## Stage 2 Decision Record
- Driver HMW: [selected framing]
- Divergent techniques applied: [core set + user adds]
- Priority dimension: [Quality / Time / Risk / Balanced]
- Weights applied: Q=[w] T=[w] C=[w] R=[w] E=[w]
- Candidates scored: [list]
- Also considered: [list]
- Tiebreak fired: [yes/no, winner if yes]
- Recommended: [Candidate title + rationale]
```

Record stage completion in `project.md`:

```
## Stage 2: COMPLETE [timestamp]
- Driver HMW: [...]
- Techniques applied: [...]
- Priority dimension: [...]
- Recommended: [Candidate title]
```

Write `.codex/forge-codex/memory/current-step.md` with `Step: stage-2-complete`, `Next: run stage-3 approval`.
