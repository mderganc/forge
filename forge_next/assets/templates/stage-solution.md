# Stage 2 — Solution Generation & Evaluation

## Purpose
Generate 2-4 meaningfully distinct solution options per root cause, score each on 5 rubric dimensions (with auto-calculated Priority), and recommend a preferred approach — with cons/risks explicit for every option. Stage 2 is **user-interactive**: the PM pauses at two decision gates so the user's judgment shapes framing, technique choice, candidate selection, and scoring weights.

## Lead Agent
**Architect** — generates, develops, and scores solutions across **three** PM-orchestrated dispatches (one per phase of `templates/brainstorming.md`).

## Superpowers Integration
- Invoke `superpowers:brainstorming` if available to explore solution space
- Read `templates/brainstorming-gates.md` for the PM-owned decision gates that wrap the Architect's brainstorming runs. **Gates are PM-only** — dispatched sub-agents must not execute the gates file.

## PM Actions

### 1. Three-Dispatch Brainstorming Loop

Stage 2 is no longer a single Architect dispatch. It's a loop of **Dispatch 1 → Gate 1 → Dispatch 2 → Gate 2 Q1+Q2 → Dispatch 3 → Gate 2 Q3 (conditional)** driven by the PM. The full protocol and exact dispatch prompts live in `prompts/develop/solution.md`; summary below.

**Dispatch 1 — Requirements Exploration (Phase 1 only).** Architect runs only Phase 1 of `templates/brainstorming.md`: 6 exploration questions, Requirements Context block, 3–5 HMW framings with a suggested driver, optional Job Story. Writes `.codex/forge-codex/memory/solution-requirements.md` and stops at the Phase 1 → Phase 2 boundary. No ideas, no candidates yet.

**Gate 1 — Pre-Divergence (PM).** Execute `templates/brainstorming-gates.md` Gate 1. Ask the user which HMW framing drives divergence (Q1) and which **advanced** divergent techniques to add on top of the always-on core (SCAMPER + Reverse Brainstorming + Constraint Removal) (Q2). Keep the options short and concrete. Respects autonomy: Level 1 asks; Level 2/3 skip and use the suggested HMW + task-type defaults.

**Dispatch 2 — Divergence + Candidate Development (draft `solutions.md`).** Architect runs Phase 2 (with the user's selected techniques) and Phase 3 Steps 1–3 (group → eliminate → ICE → develop candidates). Writes `.codex/forge-codex/memory/divergent-ideas.md` and a **draft** `.codex/forge-codex/memory/solutions.md` with candidates but **no scoring, no Pugh Matrix, no recommendation**. Architect stops at the Phase 3 Step 3 → Step 3b boundary.

**Gate 2 Q1 + Q2 — Pre-Scoring (PM).** Execute `templates/brainstorming-gates.md` Gate 2. Q1 asks the user which developed candidates (2–4) to carry into full scoring; Q2 asks which scoring dimension matters most (Quality / Time / Risk / Balanced — 4 options, collapsed from the rubric's 5 dimensions per the Q2 weight-translation table). Respects autonomy: Level 1 asks Q1 + Q2; Level 2 asks only Q2 and auto-keeps all ≤4 candidates; Level 3 skips both and uses Balanced weights.

**Dispatch 3 — Convergence Scoring (finalize `solutions.md`).** Architect runs Phase 3 Steps 3b–5 only: Pugh Matrix head-to-head → weighted rubric scoring with the user's Gate 2 Q2 weights → cross-solution conflict check → recommendation with rationale referencing the priority dimension. Overwrites `solutions.md` with the final version + "Also Considered" section. Creates beads issues per scored option.

**Gate 2 Q3 — Tiebreak (PM, conditional).** After Dispatch 3, the PM checks whether the Pugh Matrix is net-zero or the top two weighted scores are within 0.5. If so, fire Q3 **regardless of autonomy level** (this is the escalation override from the develop workflow rules). Record the tiebreak winner in `solutions.md` and `project.md`.

**Resume safety.** If a session is resumed and the intermediate artifacts are partially present, skip whichever dispatches have already run based on which artifacts exist (see `brainstorming-gates.md` Intermediate Artifact Contract). If a legacy session has `solutions.md` *with* scores but no `solution-requirements.md`, treat Stage 2 as complete and proceed to Stage 3.

### 2. Task Type Framing

| Task Type | Solution Framing |
|-----------|-----------------|
| Bugfix | "Here are N ways to fix root cause X" |
| Refactor | "Here are N approaches to restructure around root cause X" |
| Feature | "Here are N architectural approaches to address core challenge X" |

### 3. Run Review Loop

Per `templates/review-loop.md`. **Run the review loop only after Dispatch 3 completes** — reviewing raw divergent ideas from Dispatch 1/2 is low-value and would thrash the loop. The critic and cross-reviewers evaluate the final `solutions.md` against its intermediate inputs (`solution-requirements.md`, `divergent-ideas.md`, draft `solutions.md`) and the user's Gate 1 / Gate 2 answers.

| Step | Agent | Focus |
|------|-------|-------|
| Self-review | Architect | Each option genuinely distinct? Cons honest? Scores defensible? Compound solutions considered? User's selected techniques actually applied? User's priority weights actually used? |
| Cross-review | Security (if activated), QA | New attack surface? Risk scores accurate? Solutions testable? Effort realistic? |
| Critic challenge | Critic | Worst case for recommended? Cons understated? When would non-recommended be better? Did the user's priority dimension actually shift the ranking or was it ignored? |
| PM validation | PM | Every root cause has ≥2 options? Scores consistent? Cons specific enough for user? Gate 1 / Gate 2 decisions captured in `project.md` and in the `solutions.md` Decision Record? |

Loop until all pass cleanly in the same round.

### 4. Beads Tracking

For each solution option:
bd create "[solution description]" -t task --parent [epic-id] -l "solution,stage-2,option"
bd dep add [solution-id] [root-cause-id] --type blocks
bd comments add [solution-id] "Scores: Q=N T=N C=N R=N E=N P=N"

Mark recommended: bd label add [solution-id] recommended

### 5. Stage Gate

| Autonomy | Behavior |
|----------|----------|
| Level 1 | Hit Gate 1 and Gate 2 interactively; present solution summary to user; proceed to Stage 3 |
| Level 2 | Skip Gate 1 (task-type defaults logged); hit **Gate 2 priority-dim question** and tiebreak; auto-proceed to Stage 3 (always pauses there) |
| Level 3 | Skip Gate 1 and Gate 2 (defaults logged); PM auto-selects recommended; pauses Stage 3 only for final approval |

**Footnote — Level 2 now has one mandatory in-stage gate** (scoring priority dimension + conditional tiebreak). This is a deliberate break from the original "Level 2 auto-proceeds through Stage 2" contract. The reason: the priority dimension is the single highest-leverage user decision in Stage 2, and asking one question is strictly better than asking zero and then having the user reject a recommendation at Stage 3 because the wrong dimension was optimized. See `templates/autonomy-levels.md` for the updated matrix.

**Footnote — Escalation overrides autonomy.** The Pugh-tie / score-within-0.5 escalation from the develop workflow rules forces the tiebreak question regardless of autonomy level. A Level 3 session can still pause if the Architect cannot produce a confident winner.

### 6. Git Checkpoint

git add .codex/forge-codex/ && git commit -m "workflow: Stage 2 complete — solutions evaluated"

Record in project.md: `## Stage 2: COMPLETE [timestamp]`
