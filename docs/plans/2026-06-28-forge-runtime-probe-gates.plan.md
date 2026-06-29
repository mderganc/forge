---
name: Forge runtime adaptation and probe gates
overview: "Self-adjusting repo-local .forge runtime, loud structural probes, and user gates on any non-OK probe outcome."
todos:
  - id: w0-forge-runtime-root
    content: "W0 — .forge runtime_root; migrate before create_session; dual-root takeover; tests+docs"
    status: completed
  - id: w1-runtime-adaptation
    content: "W1 — runtime_adaptation.py; writable alias for session/state writes; FORGE_ADAPT line"
    status: completed
  - id: w2-probe-banners-gate
    content: "W2 — probe status sidecar; loud banner; structural_probes_gate.py; pause + multiselect; block next step"
    status: completed
  - id: w3-probe-timeouts
    content: "W3 — probe timeouts; ship deferred pass; CI override CLI flags"
    status: completed
  - id: w4-integration-paths
    content: "W4 — update Codex/Cursor/Claude skills + docs to .forge/ paths; bundle templates"
    status: completed
isProject: false
---

# Forge runtime adaptation and structural probe gates

Design: [docs/forge/specs/2026-06-28-forge-runtime-probe-gates-design.md](../forge/specs/2026-06-28-forge-runtime-probe-gates-design.md)

## Problem

Codex sessions hit: (1) writes to read-only mount alias while cwd was writable alias, (2) structural scans hung with no output, (3) agents improvised sidecars after SIGINT, (4) evaluate loops burned tokens. Users should not configure `FORGE_REPO` or skip flags.

## Solution (three rules)

1. **Everything under `.forge/`** in the repo — sessions, sidecars, adaptation profile, graphify prefs.
2. **Forge adapts paths** — writable alias chosen automatically; fail loud if impossible.
3. **Probes are loud and gated** — non-`OK` status prints banner + `STRUCTURAL PROBES GATE`; workflow pauses until user picks retry / override / defer-to-ship / stop.

## Tasks

### W0 — `.forge` runtime root

- Change `runtime_root()` to return `repo_root / ".forge"` only.
- **Migrate before create_session** on step 1: copy `.codex/forge/{sessions,memory,state}` → `.forge/`; audit in `.forge/state/migration.json`.
- `takeover` / `status` index both roots until migration archive complete.
- Update docs (`sessions.md`, `environment.md`, AGENTS.md) and rewrite `test_shared_orchestrator.py` expectations.

### W1 — Runtime adaptation layer

- New `scripts/shared/runtime_adaptation.py`: probe aliases, write `.forge/adaptation.json`.
- `create_session`, `resolve_step1_state_path`, structural probe writes use `writable_repo_root()`.
- Remove bare `.resolve()` that re-canonicalizes to read-only spelling after writable pick.

### W2 — Loud probes + user gate

- `inject_structural_probes_section`: always append banner; `status` in sidecar.
- New `scripts/shared/structural_probes_gate.py`:
  - `format_probe_gate_body()`, `validate_probe_gate()`, multiselect JSON.
  - Gate sidecar `.structural-probes-gate.json`.
- Wire into evaluate, code-review, implement wave review steps that run probes.
- `format_step_output(..., require_confirmation=True)` when gate pending.
- Refactor `code_review/structural_probes_gate.py` to use shared module.
- Non-interactive: exit 1 on pending gate.

### W3 — Probe timeouts + CI

- Cap inventory/git subprocess timeouts.
- `forge ship --step 1` runs deferred full pass.
- CLI override flags for CI: `--allow-structural-probes-incomplete` (existing) + gate bypass reason fields.

### W4 — Integration paths (was W5)

- `install_codex_skills` bundles referenced templates.
- Update Cursor/Claude/Codex skills, AGENTS.md, README, `docs/sessions.md` to `.forge/`.

### Deferred: intent router

- “Loop until clean” → bounded takeover — separate follow-up after W0–W2 land.

## Acceptance

- No Forge runtime writes outside `<repo>/.forge/`.
- Every probe step prints `STRUCTURAL PROBES — {STATUS}`.
- Non-OK probe → user must choose before next step runs.
- `forge doctor` / `forge status` show probe gate state when pending.
