# Documentation audit matrix (2026-06)

Baseline: `main` after PRs #27–#29 (`forge-next` **0.18.0**).  
Sources of truth: [`integrations/spec/commands.json`](../../integrations/spec/commands.json), [`scripts/shared/session_store.py`](../../scripts/shared/session_store.py), [`forge_next/graphify_enforcement.py`](../../forge_next/graphify_enforcement.py).

Legend: **OK** | **stale** | **missing** | **fixed** (after this audit PR)

## Command surface (14 commands)

| Command | commands.json | README table | README workflow | integrations |
|---------|---------------|--------------|-----------------|--------------|
| sketch | OK | was missing → **fixed** | OK § Sketch | OK |
| develop | OK | OK | OK | OK |
| plan | OK | OK | OK | OK |
| evaluate | OK | OK | OK | OK |
| implement | OK | OK | OK | OK |
| code-review | OK | OK | OK | OK |
| test | OK | OK | OK | OK |
| diagnose | OK | OK | OK | OK |
| iterate | OK | was missing → **fixed** | OK | OK |
| ship | OK | was missing → **fixed** | was missing → **fixed** | OK |
| resume | OK | OK | OK | OK |
| status | OK | OK | OK | OK |
| doctor | OK | OK | — | OK |
| graphify | OK | OK | — | OK |

## Session model (PR #27)

| Topic | Code | README | AGENTS | skills |
|-------|------|--------|--------|--------|
| `sessions/{id}/session.json` | OK | was stale → **fixed** | was stale → **fixed** | was stale → **fixed** |
| Legacy flat `{skill}.json` | OK | **fixed** (compat note) | **fixed** | **fixed** |
| `index.json`, `_archive/` | OK | **fixed** | **fixed** | — |

## Graphify (ship-only banner, PR #21)

| File | Status |
|------|--------|
| `docs/graphify.md` | OK |
| `CLAUDE.md` | OK |
| `forge_next/graphify_policy.py` | OK |
| `README.md` | was stale (4 spots) → **fixed** |
| `integrations/README.md` | was stale → **fixed** |

## Diagnose (PRs #26, #29)

| Topic | README | AGENTS | skills/diagnose |
|-------|--------|--------|---------------|
| Feedback loop step-3 | OK | OK | **fixed** paths + symptom note |
| Symptom-level RCA gate | **fixed** | — | **fixed** |
| Sidecar path header | — | was stale → **fixed** | — |

## Runtime paths

| File | `.codex/forge/` canonical | Legacy `forge-codex` noted |
|------|---------------------------|----------------------------|
| `runtime_layout.py` | OK | OK |
| `skills/*/SKILL.md` | was stale → **fixed** |
| `AGENTS.md` | was stale → **fixed** |

## Packaging

| Artifact | Version | README example |
|----------|---------|----------------|
| `pyproject.toml` | 0.18.0 | was 0.14.16 → **fixed** |
| `plugin.json` | 0.18.0 | OK (aligned) |

## New docs from audit

| File | Purpose |
|------|---------|
| `docs/README.md` | Documentation hub |
| `docs/environment.md` | `FORGE_*` reference |
| `docs/sessions.md` | Session directory layout |

## Automation

| Test | Purpose |
|------|---------|
| `test_readme_commands.py` | commands.json ids in README |
| `test_docs_graphify_consistency.py` | No per-step GRAPHIFY claims |
| `test_skills_runtime_paths.py` | No bare `forge-codex` in skills |
