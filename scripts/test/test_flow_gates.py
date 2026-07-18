"""Flow-mode gate checks (scaffold + authoring)."""

from __future__ import annotations

from scripts.shared.orchestrator import SkillState


def check_scaffold_gate(state: SkillState) -> list[str]:
    flow_files = state.custom.get("flow_files", [])
    missing = []

    if not flow_files:
        missing.append("flow_files list is empty — scaffold not created")
        return missing

    if not any("data-packs" in f for f in flow_files):
        missing.append("data-pack directories (clean/, messy/, edge-cases/, duplicates/) missing")

    if not any("conftest.py" in f or "steps" in f for f in flow_files):
        missing.append("role-parameterization harness file (conftest.py or steps/) missing")

    if not any("test_" in f and ".py" in f for f in flow_files):
        missing.append("primary test file missing or entry-point invocation not found")

    return missing


def check_authoring_gate(state: SkillState) -> list[str]:
    flow_scope = state.custom.get("flow_scope", {})
    authoring_results = state.custom.get("authoring_results", {})
    missing = []

    if not flow_scope.get("failure_paths", []):
        missing.append("no failure-path assertions (criterion 7) — at least 1 required")

    outcome_surfaces = authoring_results.get("outcome_surfaces", [])
    if len(outcome_surfaces) < 2:
        missing.append(
            f"outcome validation touches only {len(outcome_surfaces)} surface(s) "
            "(criterion 5) — at least 2 required"
        )

    external_mocks = authoring_results.get("external_mocks", [])
    allowed_externals = flow_scope.get("external_services_to_mock", [])
    for mock in external_mocks:
        if mock not in allowed_externals:
            missing.append(f"mock '{mock}' not in allowed externals (criterion 6)")

    return missing
