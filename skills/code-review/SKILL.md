---
description: |
  Multi-mode code review: PR, deep, or architecture. Full agent team.
  Optional structural probes at step 3. Supports --effort light|standard|thorough
  (--quick is an alias for --effort light).
---

# Forge Code Review — Multi-Mode Review

Two-axis review aligned with [mattpocock/skills code-review](https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md): **Pass A — Spec** (intent/requirements) and **Pass B — Standards** (repo standards + `templates/standards-review-baseline.md`). Structural probes at step 3 are Pass B tooling. Findings are reported per axis — do not merge or rerank across axes.

Shared runtime: [templates/workflow-skill-preamble.md](../../templates/workflow-skill-preamble.md).

**Structural probes are optional** and controlled by `--structural` / `--no-structural`, defaulting from `--effort` (off for `light`/`standard`, on for `thorough`). When enabled, the orchestrator runs **pyscn** (Python) and **knip** (Node) at **step 3** when applicable and writes `.structural-probes.json`.

**Steps 4–6 are blocked** only when structural probes are enabled and have not yet run (`pass` or `fail`, not `skip`). Re-run step 3 or use `--allow-structural-probes-incomplete` with override reason/follow-up to bypass. When structural probes are disabled, steps 4–6 proceed without a probe gate.

## Simplicity

Preamble § Simplicity (YAGNI). Flag over-engineering and **Speculative Generality** (`templates/standards-review-baseline.md`, `templates/code-smells.md`).

<invoke cmd="forge code-review" />

| Argument | Required | Description |
|----------|----------|-------------|
| `--step` | Yes | Phase 1–6 |
| `--mode` | No | `pr`, `deep`, or `architecture` (auto-detected) |
| `--target` | Step 1 | PR, branch, or file paths |
| `--effort` | No | `light`, `standard` (default), or `thorough` — replaces `--quick`. `light` = Architect + QA Reviewer only |
| `--structural` / `--no-structural` | No | Force structural probes + eight-agents on/off at step 3. Optional — defaults from `--effort`: **off** for `light`/`standard`, **on** for `thorough` |
| `--quick` | No | Alias for `--effort light` (kept for backward compatibility) |

At **step 1**, the orchestrator **recommends** `--effort` and `--structural` from mode, implement handoff scope, and target (printed in the prompt). CLI flags override the recommendation. Restart step 1 to change config mid-session.

Default handoff: **`forge:test`**.
