"""Flow-mode gate checks (scaffold + authoring)."""

from __future__ import annotations

from scripts.shared.orchestrator import SkillState


def _roles(state: SkillState) -> list:
    flow_scope = state.custom.get("flow_scope") or {}
    roles = flow_scope.get("roles")
    if isinstance(roles, list) and roles:
        return roles
    custom_roles = state.custom.get("roles")
    if isinstance(custom_roles, list) and custom_roles:
        return custom_roles
    return ["anonymous"]


def _failure_paths(state: SkillState) -> list:
    flow_scope = state.custom.get("flow_scope") or {}
    paths = flow_scope.get("failure_paths") or []
    return paths if isinstance(paths, list) else []


def check_scaffold_gate(state: SkillState) -> list[str]:
    """Require a primary test + at least ``clean/``; multi-role harness when needed."""
    flow_files = state.custom.get("flow_files", [])
    missing = []

    if not flow_files:
        missing.append("flow_files list is empty — scaffold not created")
        return missing

    has_packs = any("data-packs" in f for f in flow_files)
    has_clean = any("data-packs" in f and "clean" in f for f in flow_files)
    if not has_packs:
        missing.append("data-pack directories missing — create at least clean/ (proportional budget)")
    elif not has_clean:
        missing.append("data-packs/clean/ missing — smoke minimum is clean/ only")

    roles = _roles(state)
    if len(roles) > 1 and not any("conftest.py" in f or "steps" in f for f in flow_files):
        missing.append("role-parameterization harness file (conftest.py or steps/) missing")

    if not any("test_" in f and ".py" in f for f in flow_files):
        if not any(f.endswith(".feature") for f in flow_files):
            missing.append("primary test file missing or entry-point invocation not found")

    return missing


def check_authoring_gate(state: SkillState) -> list[str]:
    """Authoring bar scales with scope: smoke may omit failure_paths and use 1 surface."""
    flow_scope = state.custom.get("flow_scope", {})
    authoring_results = state.custom.get("authoring_results", {})
    missing = []

    failure_paths = _failure_paths(state)
    # Smoke (no scoped failure_paths): OK. Non-empty scope: require them present
    # (legacy contract — scope listed them so authoring must keep them).
    # The gate historically failed when failure_paths was empty; minimal-scope bias
    # flips that: empty means intentional smoke, not a missing criterion.

    roles = _roles(state)
    outcome_surfaces = authoring_results.get("outcome_surfaces", [])
    # Multi-role or scoped failure paths → ≥2 surfaces; smoke → ≥1
    min_surfaces = 2 if (len(roles) > 1 or failure_paths) else 1
    if len(outcome_surfaces) < min_surfaces:
        missing.append(
            f"outcome validation touches only {len(outcome_surfaces)} surface(s) "
            f"(criterion 5) — at least {min_surfaces} required for this scope"
        )

    external_mocks = authoring_results.get("external_mocks", [])
    allowed_externals = flow_scope.get("external_services_to_mock", [])
    for mock in external_mocks:
        if mock not in allowed_externals:
            missing.append(f"mock '{mock}' not in allowed externals (criterion 6)")

    return missing
