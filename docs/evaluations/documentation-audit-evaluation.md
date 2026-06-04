---
title: "Evaluation: Documentation full review"
plan: documentation-audit (working tree)
mode: review
date: 2026-06-04
---

# Evaluation: Documentation full review

## Summary

Reviewed the uncommitted documentation audit against the attached plan (post PRs #27–#29). The README, AGENTS, skills, new docs, and regression tests align with **forge-next 0.18.0** behavior (sessions layout, ship-only Graphify, 14 commands). During review, **integration command bundles** had pre-existing defects (form-feed typo, stale Graphify copy) — remediated in the same session. **Verdict: approve with notes** — safe to commit; bump `plugin.json` patch when shipping integration text changes.

## Structural probes (Pass B)

_Structural probes: not run for evaluate review mode (doc-only scope)._

## Findings

### Critical

_None._

### Warnings

| ID | Title | Detail |
|----|-------|--------|
| EVAL-003 | Form-feed typo in integration commands | 15 files had `\x0corge` instead of `forge ship` — **fixed** during review. |
| EVAL-004 | Stale Graphify in integrations | `graphify.md`, `forge-graphify` SKILL, `iterate.md`, `develop.md` — **fixed** during review. |
| EVAL-005 | Global Codex skills may lag | Re-run `pipx upgrade forge-next` and `forge install --codex` so `~/.codex/skills` matches repo. |
| EVAL-006 | Narrow Graphify test scope | **Addressed** — `test_docs_graphify_consistency.py` now scans integration command `.md` files. |

### Suggestions

| ID | Title | Detail |
|----|-------|--------|
| EVAL-001 | Plan implementation complete | Command table, sessions, ship, env docs, audit matrix. |
| EVAL-002 | Tests pass | 49 tests including new doc guards. |

## Dismissed Items

_None._

## Conclusion

The documentation audit deliverable meets plan success criteria. Commit the doc + test + integration fixes together. Before PyPI/plugin publish, bump **`integrations/cursor-plugin/.cursor-plugin/plugin.json`** (patch) because command markdown changed. Optional follow-up: add `skills/ship/` and `skills/iterate/` for symmetry with `integrations/codex/skills/`.

**Recommended next:** `$forge:ship` or commit locally, then merge.
