# Remaining Tier B + test-failure remediation plan

**Status:** planned (2026-07-18)  
**Baseline:** `pyscn check . --skip-clones -c .pyscn.toml` passes; targeted friction/pyscn-wave tests pass; full suite **`tests/`** reports **26 failed, 569 passed** when `build/` is excluded from collection.

This plan closes the last Tier B hygiene item and groups the 26 failing tests into fix waves with concrete file targets.

---

## Part 1 — Remaining Tier B

### Current state

W1–W4 (see [`docs/pyscn-quality-disposition.md`](pyscn-quality-disposition.md)) landed the major splits. At **`max_complexity = 15`** the repo is clean.

At the stricter **Tier B target (≤ 12)** one function remains:

| Function | File | Complexity | Notes |
|----------|------|------------|-------|
| `resolve_test_handoff` | `scripts/shared/handoff_resolvers.py` | **13** | Green/red default swap + flows/run alt swap + ux-review append |

All other original Tier B targets (`resolve_handoff_commands`, `step_for_phase`, diagnose validators) are split and pass at 15.

### Proposed refactor (no behavior change)

Split `resolve_test_handoff` into three helpers:

```text
_apply_test_results_handoff(default, alts, test_results) -> (default, alts)
  # failed > 0 → diagnose default, ship alt; else ship default, diagnose alt

_swap_test_mode_alts(alts, mode) -> alts
  # flows ↔ run swap; strip test --mode ux

_ensure_ux_review_alt(alts) -> alts
```

`resolve_test_handoff` becomes a 4-line dispatcher (~complexity 4).

**Verification:** `pyscn check scripts/shared/handoff_resolvers.py --skip-clones -c .pyscn.toml` with a temporary `max_complexity = 12` override, plus existing handoff tests in `tests/test_regressions.py` (`test_test_skill_handoff_*`).

### Doc follow-up

Update the Tier B table in `docs/pyscn-quality-disposition.md` to mark W1–W2 items **done** and list only `resolve_test_handoff` as the optional ≤12 follow-up.

---

## Part 2 — Test failures (26)

### Root-cause summary

| Category | Count | Primary cause |
|----------|------:|---------------|
| **Hermeticity / env** | **11** | Host env sets `FORGE_SKIP_*=1` (auto-close, session opt-in, graphify, eight agents); tests expect features **on** |
| **Legacy runtime paths** | **9** | Fixtures still seed `.codex/forge*/state` or `.codex/forge/sessions`; runtime now prefers `.forge/sessions/{id}/session.json` |
| **Assertion / asset drift** | **4** | `resume-context` schema v2; plan `approval.md` wording; packaged prompt mirror lag |
| **Structural gate contract** | **2** | Step 4 gate not exercised without `structural_enabled: true` + session path under `.forge/` |

> **Note:** Several failures are **not product bugs** — they fail because the developer shell exports automation skip flags. Fix once in `tests/conftest.py` rather than per-test patches.

### Wave 0 — Test harness hermeticity (fixes ~11 tests, ~30 min)

**Add `tests/conftest.py` autouse fixture** that `monkeypatch.delenv`s (or sets to empty) before each test:

- `FORGE_SKIP_AUTO_CLOSE`
- `FORGE_SKIP_SESSION_OPTIN`
- `FORGE_SKIP_GRAPHIFY`
- `FORGE_SKIP_GRAPHIFY_SESSION_REFRESH`
- `FORGE_SKIP_STRUCTURAL_EIGHT_AGENTS`

Individual tests that *intentionally* assert skip behavior (e.g. `test_forge_session_opt_in_banner_step1_only` second half) should `setenv` inside the test body — pattern already used elsewhere.

**Also add to `pytest.ini`:**

```ini
norecursedirs = tests/fixtures build dist .git graphify-out
```

Prevents stale `build/lib/` from shadowing imports and collecting orphan `scripts/test/test_*.py` modules (22 collection errors on full `pytest` today).

**Tests fixed by Wave 0 alone:**

| Test | Env var |
|------|---------|
| `test_auto_close_removes_plan_when_handoff_exists` | `FORGE_SKIP_AUTO_CLOSE` |
| `test_auto_close_upstream_plan_when_starting_implement` | same |
| `test_auto_close_step1_abandoned` | same |
| `test_auto_close_abandoned_mid_pipeline_code_review_when_starting_design` | same |
| `test_auto_close_stale_pipeline_session_when_starting_design` | same |
| `test_forge_session_opt_in_banner_step1_only` | `FORGE_SKIP_SESSION_OPTIN` |
| `test_format_step_output_includes_session_opt_in_on_step1_only` | same |
| `test_evaluate_format_output_includes_opt_in_only_on_step_1` | same |
| `test_forge_graphify_banner_ship_only_for_workflow_steps` | `FORGE_SKIP_GRAPHIFY` (ship banner half) |
| `test_graphify_refresh_background_spawns_detached` | `FORGE_SKIP_GRAPHIFY` |
| `test_session_start_spawns_background_refresh_by_default` | `FORGE_SKIP_GRAPHIFY` / session refresh skip |
| `test_pre_tool_use_grep_emits_context` | `FORGE_SKIP_GRAPHIFY` |
| `test_should_dispatch_eight_agents_matrix` | `FORGE_SKIP_STRUCTURAL_EIGHT_AGENTS` |

### Wave A — Session-layout fixtures (fixes ~9 tests, ~1–2 h)

**Create `tests/helpers/session_fixtures.py`:**

```python
def write_session_state(tmp_path, skill, *, step=1, custom=None, session_id="abc") -> Path:
    """Write .forge/sessions/{id}/session.json and return path."""

def write_completed_flat_state(tmp_path, skill, ...) -> Path:
    """Write .forge/state/{skill}.json for cleanup eligibility tests."""
```

**Migrate callers:**

| File | Tests | Change |
|------|-------|--------|
| `tests/test_regressions.py` | `test_resume_cleanup_*` (3) | `.codex/forge-codex/state` → `.forge/state/` (or session archive eligible state) |
| `tests/test_takeover.py` | `test_cleanup_dry_run_no_delete` | `.codex/forge/state` → `.forge/state/plan.json` with `completed_at` / max_step complete |
| `tests/test_structural_probes_gate.py` | `test_code_review_step4_blocked_without_sidecar` | `.codex/forge/sessions/abc` → `.forge/sessions/abc`; set `st.custom["structural_enabled"] = True` |
| `tests/test_structural_probes_runner.py` | step3 smoke tests (3) | same path + `structural_enabled`; mock inject only when gate path is valid |

**Optional production hardening (if we want legacy cleanup in real repos):** extend `_iter_skill_state_paths` to glob `runtime_root_candidates()` legacy `state/` dirs (`.codex/forge/state`, `.codex/forge-codex/state`). Not required if tests move to canonical layout — prefer test migration first.

### Wave B — Structural probe contract (fixes ~2–4 tests, ~45 min)

Failures occur because step 3 probe injection and step 4 gate only run when structural mode is on.

**Test changes:**

1. Set `state.custom["structural_enabled"] = True` (and `structural` CLI flag if subprocess tests).
2. Use session paths under `.forge/sessions/`.
3. For `test_code_review_step3_mentions_sidecar` — either call with structural on so real injection runs, or keep monkeypatch but assert on the mocked banner strings only after fixing path resolution (state file must load).

**Product check:** confirm `handle_step_n(4)` calls `validate_structural_probes_gate` when `structural_enabled` — no code change expected if flag was the only gap.

### Wave C — Schema / assertion updates (fixes 1 test, ~15 min)

| Test | Fix |
|------|-----|
| `test_save_state_writes_resume_context_snapshot` | Assert `schema_version >= 1` or `== 2`; optionally assert `sessions` array and `focus` field exist (v2 contract) |

### Wave D — Prompt asset sync (fixes 2–3 tests, ~30 min)

| Test | Fix |
|------|-----|
| `test_packaged_prompts_mirror_plan_phase[approval.md]` | Copy `prompts/plan/approval.md` → `forge_next/assets/prompts/plan/approval.md` (wording now says **Documentation Planning** step 6) |
| `test_all_repo_prompts_mirrored_in_packaged_assets` | Run existing sync script or `forge install` template copy step; ensure assets tree matches `prompts/` |
| `test_packaged_structural_prompts_match_repo[post/code_quality.md]` | Sync `prompts/post/code_quality.md` → packaged twin (evaluate post step 4 lens paragraph added) |

**Process:** add a one-liner to release checklist — any prompt edit under `prompts/` must touch `forge_next/assets/prompts/` in the same PR (or run `scripts/sync_prompt_assets.py` if one exists; otherwise mirror manually).

### Wave E — Evaluate eight-agent expectation (fixes 1 test, ~15 min)

`test_should_dispatch_eight_agents_matrix` expects `should_dispatch_eight_agents("evaluate", 1, mode="review")` → True.

After Wave 0 env fix, re-run. If still failing, align test with intentional product change in `structural_eight_agents.py` (evaluate post step 4 explicitly **does not** dispatch eight agents). Update matrix:

```python
assert sea.should_dispatch_eight_agents("evaluate", 1, mode="review")  # keep
assert not sea.should_dispatch_eight_agents("evaluate", 4, mode="post")  # already present
```

If `evaluate` + `mode="review"` was removed from dispatch table, update test to match docstring in `should_dispatch_eight_agents`.

### Wave F — Structural prompt integration smoke (fixes 1 test, ~30 min)

`test_code_review_step3_real_template_probe_gate` expects `STRUCTURAL PROBES — DEFERRED` when structural off.

**Options (pick one):**

1. **Test-only:** pass `structural_enabled=True` and assert on active probe banner instead of deferred banner.
2. **Product:** ensure deferred banner still renders when structural off at step 3 (regression in template injection).

Prefer (1) unless product intent is to always show deferred text at step 3.

---

## Execution order

```text
W0  conftest + pytest.ini          → unblocks 11 env-sensitive tests
W1  Tier B resolve_test_handoff    → optional hygiene (≤12)
A   session fixtures + path migrate → cleanup + structural integration
B   structural_enabled in tests    → gate + runner smokes
C   resume-context v2 assertion
D   prompt asset sync
E   eight-agent matrix alignment
F   deferred-banner smoke
```

**Gate command after each wave:**

```bash
python -m pytest tests/ --ignore=build -q
pyscn check . --skip-clones -c .pyscn.toml
```

**Done when:** 0 failures in `tests/`, pyscn clean at 15, optional Tier B pass at 12.

---

## Risk notes

| Risk | Mitigation |
|------|------------|
| Wave 0 masks real CI skip behavior | CI should set `FORGE_SKIP_*` in workflow env; tests override locally — document in `tests/conftest.py` header |
| Legacy `.codex/` repos lose cleanup | Consider `_iter_skill_state_paths` legacy glob in a follow-up if user reports matter |
| Prompt sync drifts again | Add `test_prompt_assets` to pre-commit or ship skill step 1 |

---

## Files touched (expected)

| Wave | Files |
|------|-------|
| W0 | `tests/conftest.py` (new), `pytest.ini` |
| W1 | `scripts/shared/handoff_resolvers.py`, `docs/pyscn-quality-disposition.md` |
| A | `tests/helpers/session_fixtures.py` (new), `tests/test_regressions.py`, `tests/test_takeover.py`, `tests/test_structural_probes_*.py` |
| B–F | Same test files + `forge_next/assets/prompts/**` |

No version bump required unless we ship prompt asset changes to PyPI users (then patch `pyproject.toml` + plugin version per AGENTS.md).
