# Autonomy Levels

Three tiers of user interaction during the forge-codex team workflow.

## Level Definitions

### Level 1 — Full Approval (Default)
Pause at every stage gate for user approval. Maximum user control.

Best for: First time using the toolkit, high-stakes work, learning the workflow.

### Level 2 — Key Decisions Only
Pause at Stage 3 (solution approval), Stage 4 (pre-implementation), and Stage 7 (merge decision). Auto-proceed through investigation, solution generation, implementation waves, and review loops.

Best for: Experienced users who trust the investigation/review process but want control over what gets built and how it ships.

### Level 3 — Full Auto
Auto-proceed through all stages. Only pause at Stage 7 for the merge decision. PM auto-selects recommended solutions when the user doesn't intervene.

Best for: Well-understood tasks, trusted codebase, time-sensitive work.

## Per-Skill Autonomy Gates

| Skill | Level 1 (Full Approval) | Level 2 (Key Decisions) | Level 3 (Full Auto) |
|-------|------------------------|------------------------|---------------------|
| develop | Pause after investigation, at brainstorming Gate 1 (framing + techniques), at brainstorming Gate 2 (families + priority + tiebreak), at approval | Pause at brainstorming Gate 2 priority-dim question, at approval | Auto-proceed with logged defaults, pause only at approval (unless escalation forces tiebreak) |
| plan | Pause after architecture, after plan creation, at approval | Pause at approval only | Auto-proceed, pause at approval |
| evaluate | Pause after each phase | Pause at discussion only | Auto-proceed all phases |
| implement | Pause after each wave, at documentation | Pause at documentation only | Auto-proceed all waves |
| code-review | Pause after analysis, at discussion | Pause at discussion only | Auto-proceed to report |
| test | Pause after execution, after analysis | Pause after analysis only | Auto-proceed to report |
| diagnose | Pause after Phase 2, 4, before Phase 6 | Pause before Phase 6 only | Auto-proceed, pause before implementation |

## Gate Behavior Matrix (Legacy 7-Stage Workflow)

| Stage | Level 1 | Level 2 | Level 3 |
|-------|---------|---------|---------|
| 1 - Investigation | Pause, present summary | Auto-proceed | Auto-proceed |
| 2 - Solutions | Pause at Gate 1 (framing + advanced techniques) and Gate 2 Q1+Q2 (families + priority dim), plus conditional Q3 tiebreak after Dispatch 3; present summary | Auto-proceed except **Gate 2 Q2 priority-dim question** and conditional Q3 tiebreak | Auto-proceed with logged defaults; escalation rule may still force a Q3 tiebreak pause |
| 3 - Approval | Pause (always) | Pause (always) | Auto-select recommended, log summary |

### Stage 2 Level 3 Defaults (Deterministic)

When Level 3 skips the brainstorming gates, the PM must log these defaults in `.codex/forge-codex/memory/project.md` so the decision is reproducible:

- **Driver HMW:** the Architect's suggested driver from `solution-requirements.md`
- **Advanced divergent techniques:** none additional — the Architect runs only the always-on core (SCAMPER + Reverse Brainstorming + Constraint Removal), plus any task-type auto-adds from `templates/brainstorming.md` Method Selection Guide:
  - Bugfix auto-adds: 5W1H/Starbursting (First Principles is an advanced opt-in, skipped at Level 3)
  - Refactor auto-adds: none beyond core
  - Feature auto-adds: none beyond core
  - Mixed / Unclear auto-adds: none beyond core
- **Solution families to score:** keep all draft candidates if ≤4; otherwise top 4 by the ICE pre-filter in Dispatch 2
- **Scoring priority dimension:** Balanced (all weights 1.0, per the Gate 2 Q2 weight-translation table in `templates/brainstorming-gates.md`)
- **Pugh tiebreak:** keep the datum
- **Escalation override:** if Dispatch 3's Pugh Matrix returns a net-zero winner or the top two weighted rubric scores are within 0.5, force Gate 2 Q3 (tiebreak) regardless of level
| 4 - Planning | Pause, present plan | Pause, present plan | Auto-proceed |
| 5 - Implementation | Pause between waves | Auto-proceed, summary after all waves | Auto-proceed |
| 6 - Review | Pause, present summary | Present summary, auto-proceed | Auto-proceed |
| 7 - Documentation & Merge | Pause for merge decision | Pause for merge decision | Pause for merge decision |

## Selection

At startup, the PM presents:

How much autonomy should the team have?

  Level 1 (Default): Pause at every stage gate for your approval
  Level 2: Only pause at solution approval (Stage 3),
           before implementation (Stage 4), and merge (Stage 7)
  Level 3: Full auto — report at end, pause only for merge

  Enter 1, 2, or 3 (or pass --auto1/--auto2/--auto3 next time):

## Keyword Detection

If the user's prompt contains autonomy-related keywords, suggest the appropriate level:
- "autonomous", "go ahead", "don't wait", "continue without me", "full auto" → Suggest Level 3
- "check with me", "I want to approve", "pause for me" → Suggest Level 1
- Default (no keywords): Level 1

Always confirm the suggestion — never auto-set based on keywords alone.

## Mid-Session Changes

The user can change autonomy at any time:
- "switch to level 2" / "go autonomous" / "pause for approvals" / "level 3"
- PM acknowledges, updates project.md, applies immediately to the next gate

Changes are logged in project.md:

## Autonomy
**Current level:** 2
### Changes
- [2026-03-30 14:00] Set to Level 1 (initial)
- [2026-03-30 14:35] Changed to Level 2 (user: "skip minor gates")

Reminder shown after every change:
Autonomy set to Level [N]. Change anytime: 'switch to level 1/2/3'
or 'go autonomous' / 'pause for approvals'.
