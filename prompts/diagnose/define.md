# Phase 1: Frame the Problem

Read `templates/diagnose-execution-playbooks.md` for the entry technique you choose.

## Agents to Dispatch
- **Investigator (lead):** Pick **one** framing path, write the problem spec, list follow-on techniques
- **Architect (support):** Architecture context for affected components (when structural)

## Adaptive spine (every run)

1. **Pick exactly one `framing_entry`** to identify and bound the problem (do **not** run all framing methods).
2. **Always** plan **5 Whys** as the primary deepen step (Phase 3).
3. Add other catalog techniques only when they are good options — record them in `activated_techniques` / `routing_preferred`.

## Problem specification sidecar (mandatory)

Persist **before step 2** to `.diagnose-problem-spec.json` beside diagnose state:

| Field | Required |
|-------|----------|
| `problem_statement` | One paragraph: symptom, impact, scope |
| `framing_entry` | Exactly one: `kepner_tregoe` \| `cynefin` \| `first_principles` \| `evidence_snapshot` \| `mece_sketch` |
| `activated_techniques` | Catalog names in play (must include **5 Whys**) |
| `routing_preferred` | Techniques you may add in later phases if signal warrants |
| `incident_profile` / `severity` | Tags for high-severity policy (e.g. `high_severity`, `sudden_deviation`) |

Summary: {{PROBLEM_SPEC_SUMMARY}}

## Choose ONE entry framing path

### A. `kepner_tregoe` — sudden deviation / “worked before”

Use when discrimination (IS vs IS-NOT) will narrow the problem fastest.

- Fill `is_isnot`: WHAT / WHERE / WHEN / EXTENT — each with `is`, `is_not`, `distinction`
- Include change analysis: `last_known_good`, `change_window`, `candidate_changes[]`
- Add **Kepner-Tregoe Problem Analysis** to `activated_techniques`

### B. `cynefin` — strategy / uncertainty about approach

Use when the main question is *how* to investigate, not yet *what* broke.

- Set `cynefin_domain`: Clear \| Complicated \| Complex \| Chaotic
- Set `cynefin_strategy_note`: one line on how the domain shapes next steps
- Ask the user to confirm domain when interactive (`templates/user-questions.md`)

### C. `first_principles` — assumptions need challenging

- Set `first_principles_snapshot.invariants[]` (or start `.diagnose-first-principles.json`)
- Add **First-principles thinking** to `activated_techniques` only if you will use the sidecar in later phases

### D. `evidence_snapshot` — repro/logs already tell the story

- Set `observations[]`: timestamp, source, fact (≥1)
- Add **Gemba Observation** when repro/UI-heavy

### E. `mece_sketch` — large ambiguous problem space

- Set `mece_sketch.nodes[]` with ≥2 nodes **or** plan `.diagnose-mece-tree.json` in Phase 3
- Add **MECE issue tree** to `activated_techniques` only when you will build the tree

## Follow-on routing (not mandatory upfront)

After framing, list `routing_preferred` techniques you **might** apply later (exact catalog spelling from `prompts/diagnose/technique_catalog.md`). Examples:

- Messy multi-driver → **Fishbone / Ishikawa** + **Hypothesis-driven problem solving**
- Competing causes → **Hypothesis-driven problem solving**
- Executive decomposition → **MECE issue tree**
- Metric spike → **Control Charts / Run Charts**

Do **not** add MECE, hypothesis register, or first-principles sidecars in Phase 1 unless they are in `activated_techniques`.

## Technique coverage (start small)

Create `.diagnose-technique-coverage.json` with a row per **activated** technique only (not all 20). Minimum: **5 Whys** + your framing technique when it maps to a catalog name.

| technique | status (applied/skip/defer) | rationale |
|-----------|-----------------------------|-----------|

## Phase 3–5 expectations

- **5 Whys** — always: draft Phase 3, finalize Phase 4 (`templates/five-why-protocol.md` § Diagnose RCA).
- **Hypothesis register** — only if **Hypothesis-driven problem solving** or **Fishbone / Ishikawa** is activated (minimum **{{HYPOTHESIS_MIN}}** candidates when active).
- **MECE tree** — only if **MECE issue tree** is activated.

Write to `{{MEMORY_DIR}}/investigator.md`
