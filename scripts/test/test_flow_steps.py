"""Flow-mode step helpers (extracted from test_flows)."""

from __future__ import annotations

from pathlib import Path

from scripts.shared.orchestrator import SkillState, save_state


def record_flow_gate_failures(
    step: int,
    state: SkillState,
    sp: Path,
) -> list[str]:
    from scripts.test.test_flow_gates import check_authoring_gate, check_scaffold_gate

    if step == 4:
        gate_failures = check_scaffold_gate(state)
        if gate_failures:
            state.custom.setdefault("scaffold_attempts", 0)
            state.custom["scaffold_attempts"] += 1
            state.custom["scaffold_gate_failures"] = gate_failures
            save_state(state, sp)
        return gate_failures
    if step == 5:
        gate_failures = check_authoring_gate(state)
        if gate_failures:
            state.custom.setdefault("authoring_attempts", 0)
            state.custom["authoring_attempts"] += 1
            state.custom["authoring_gate_failures"] = gate_failures
            save_state(state, sp)
        return gate_failures
    return []


def ingest_flow_sidecars(step: int, state: SkillState, sp: Path) -> None:
    from scripts.test._sidecar import ingest_recommendation_sidecar, ingest_scope_sidecar

    state_dir = sp.parent
    side = state_dir / "sidecars"
    ingest_dir = side if side.is_dir() else state_dir

    if step == 3 and not state.custom.get("flow_type"):
        for candidate in (ingest_dir, state_dir, sp.parent):
            path = candidate / ".test-recommendation-step2.json"
            if path.is_file():
                rec = ingest_recommendation_sidecar(candidate)
                state.custom["flow_type"] = rec.get("chosen")
                state.custom["recommendation"] = rec
                save_state(state, sp)
                return
        ingest_recommendation_sidecar(ingest_dir)

    if step == 4:
        scope = ingest_scope_sidecar(ingest_dir)
        if scope:
            state.custom["flow_scope"] = scope
            save_state(state, sp)
