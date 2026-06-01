"""Per-step gate resolution and body augmentation for diagnose orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from scripts.diagnose import diagnose_gates

if TYPE_CHECKING:
    from scripts.shared.orchestrator import SkillState


def resolve_step_gate(
    step: int,
    state: SkillState,
    state_path: Path,
) -> tuple[diagnose_gates.DiagnoseGateResult | None, str]:
    """Return gate result (steps 4–5, 7) and optional step-2 advisory warning."""
    if step == 2:
        ps_result = diagnose_gates.check_problem_spec_gate(state, state_path, step, strict=False)
        if not ps_result.passed and ps_result.gate_body:
            warning = (
                "\n\n---\n\n**Problem spec (advisory — fix before Phase 4):**\n"
                + ps_result.gate_body
            )
            return None, warning
        return None, ""

    if step == 4:
        gate_result = diagnose_gates.check_register_gate(state, state_path, step)
        if gate_result.passed:
            gate_result = diagnose_gates.check_quartet_gate(state, state_path, step)
        return gate_result, ""

    if step == 5:
        return diagnose_gates.check_step5_bundle_gate(state, state_path, step), ""

    if step == 7:
        return diagnose_gates.check_step7_closure_gate(state, state_path, step), ""

    return None, ""


def apply_gate_template_variables(
    variables: dict[str, str],
    gate_result: diagnose_gates.DiagnoseGateResult | None,
) -> None:
    if gate_result and not gate_result.passed:
        body = gate_result.gate_body
        variables["HYPOTHESIS_GATE"] = body
        variables["DIAGNOSE_ARTIFACT_GATE"] = body
        variables["FIVE_WHYS_GATE"] = body
        variables["TECHNIQUE_COVERAGE_GATE"] = body
        variables["QUARTET_GATE"] = body


def append_complexity_gate_notes(step: int, body: str, state: SkillState) -> str:
    fc = state.custom.get("fix_complexity", "unknown")
    if step == 6 and fc == "complex":
        body += (
            "\n\n---\n\n"
            "**COMPLEXITY GATE TRIGGERED (complex):** Fix is too broad for quick implementation here.\n"
            "Write handoff file and direct user to `plan` -> `implement`.\n"
            "Then skip to Phase 7 (Report).\n"
        )
    elif step == 6 and fc == "large":
        body += (
            "\n\n---\n\n"
            "**COMPLEXITY GATE TRIGGERED (large / systemic):** Solution space needs design work before planning.\n"
            "Write handoff file and direct user to **`develop`** (brainstorm / design) → then **`plan`** → `implement`.\n"
            "Then skip to Phase 7 (Report).\n"
        )
    return body


def complexity_run_summary(step: int, state: SkillState, default: str) -> str:
    if step != 6:
        return default
    fc = state.custom.get("fix_complexity")
    if fc == "complex":
        return "Complexity gate triggered; diagnose prepared handoff path for planning flow."
    if fc == "large":
        return "Large-complexity gate triggered; diagnose prepared handoff path for develop → plan."
    return default


def suggested_next_for_complexity(complexity: str) -> str:
    if complexity == "large":
        return "develop"
    if complexity == "complex":
        return "plan"
    return "(end of flow)"


def routing_label_for_complexity(complexity: str) -> str:
    if complexity == "large":
        return "develop → plan"
    if complexity == "complex":
        return "plan → implement"
    return "resolved / choose next skill from menu"
