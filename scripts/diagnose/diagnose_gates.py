"""Orchestrator gate checks for diagnose sidecars."""

from __future__ import annotations

from pathlib import Path

from scripts.diagnose.activated_techniques import (
    requires_first_principles,
    requires_hypothesis_register,
    requires_mece_tree,
    resolve_activated_techniques,
)
from scripts.diagnose.barriers_register import load_register as load_barriers
from scripts.diagnose.barriers_register import register_path as barriers_path
from scripts.diagnose.barriers_register import validate as validate_barriers
from scripts.diagnose.diagnose_registers import (
    DiagnoseGateResult,
    GateSection,
    has_override,
    merge_gate_results,
)
from scripts.diagnose.first_principles_register import load_register as load_fp
from scripts.diagnose.first_principles_register import register_path as fp_path
from scripts.diagnose.first_principles_register import validate as validate_fp
from scripts.diagnose.five_whys_register import load_register as load_five_whys
from scripts.diagnose.five_whys_register import register_path as five_whys_path
from scripts.diagnose.five_whys_register import validate_chains
from scripts.diagnose.hypothesis_register import (
    load_register as load_hypotheses,
    register_path as hypothesis_path,
    validate_elimination,
    validate_register,
)
from scripts.diagnose.mece_tree_register import load_register as load_mece
from scripts.diagnose.mece_tree_register import register_path as mece_path
from scripts.diagnose.mece_tree_register import validate as validate_mece
from scripts.diagnose.problem_spec_register import load_register as load_problem_spec
from scripts.diagnose.problem_spec_register import register_path as problem_spec_path
from scripts.diagnose.problem_spec_register import validate as validate_problem_spec
from scripts.diagnose.repro_loop_register import load_register as load_repro_loop
from scripts.diagnose.repro_loop_register import register_path as repro_loop_path
from scripts.diagnose.repro_loop_register import (
    requires_override_to_proceed,
    validate as validate_repro_loop,
)
from scripts.diagnose.technique_coverage import load_sidecar as load_coverage
from scripts.diagnose.technique_coverage import coverage_path
from scripts.diagnose.technique_coverage import validate_coverage
from scripts.shared.orchestrator import SkillState

PHASE_NAMES: dict[int, str] = {}


def _confirmed_hypothesis_ids(reg_data: dict | None) -> set[str]:
    if not reg_data or not isinstance(reg_data.get("hypotheses"), list):
        return set()
    return {
        str(h["id"])
        for h in reg_data["hypotheses"]
        if isinstance(h, dict) and str(h.get("status")) == "confirmed" and h.get("id")
    }


def _section(
    title: str,
    issues: list[str],
    state: SkillState,
    override_key: str,
) -> GateSection:
    return GateSection(
        title=title,
        issues=issues,
        override_key=override_key,
        bypassed=has_override(state.custom, override_key),
    )


def check_problem_spec_gate(
    state: SkillState,
    sp: Path,
    step: int,
    *,
    strict: bool = False,
) -> DiagnoseGateResult:
    """Step 2: light problem-spec validation."""
    if has_override(state.custom, "problem_spec_override_reason"):
        return DiagnoseGateResult(passed=True)

    sd = sp.parent
    data = load_problem_spec(problem_spec_path(sd))
    ok, issues = validate_problem_spec(data, path=problem_spec_path(sd), strict=strict)
    if ok:
        return DiagnoseGateResult(passed=True)

    attempts = int(state.custom.get("problem_spec_regen_attempts", 0))
    retry = 1 if attempts < 1 and strict else None
    if attempts < 1:
        state.custom["problem_spec_regen_attempts"] = attempts + 1

    sections = [_section("Problem specification", issues, state, "problem_spec_override_reason")]
    return merge_gate_results(
        sections,
        phase=PHASE_NAMES.get(step, f"Step {step}"),
        retry_step=retry,
        attempt=attempts,
        max_attempts=1,
        state_path=str(sp),
    )


def check_repro_loop_gate(state: SkillState, sp: Path, step: int) -> DiagnoseGateResult:
    """Step 3: require feedback loop sidecar before 5 Whys."""
    if has_override(state.custom, "repro_loop_override_reason"):
        return DiagnoseGateResult(passed=True)

    sd = sp.parent
    reg_file = repro_loop_path(sd)
    data = load_repro_loop(reg_file)
    ok, issues = validate_repro_loop(data, path=reg_file)
    if ok and requires_override_to_proceed(data):
        ok = False
        issues = [
            "Sidecar documents cannot_build_loop — set state "
            "'repro_loop_override_reason' after user provides access/artifacts, "
            "or build a runnable loop and update the sidecar."
        ]

    if ok:
        return DiagnoseGateResult(passed=True)

    attempts = int(state.custom.get("repro_loop_regen_attempts", 0))
    retry = 2 if attempts < 1 else None
    if attempts < 1:
        state.custom["repro_loop_regen_attempts"] = attempts + 1

    sections = [_section("Feedback loop / reproduction", issues, state, "repro_loop_override_reason")]
    return merge_gate_results(
        sections,
        phase=PHASE_NAMES.get(step, f"Step {step}"),
        retry_step=retry,
        attempt=attempts,
        max_attempts=1,
        state_path=str(sp),
    )


def check_register_gate(state: SkillState, sp: Path, step: int) -> DiagnoseGateResult:
    sd = sp.parent
    activated = resolve_activated_techniques(sd, state.custom)
    if not requires_hypothesis_register(activated):
        return DiagnoseGateResult(passed=True)

    if has_override(state.custom, "hypothesis_override_reason"):
        return DiagnoseGateResult(passed=True)
    reg_file = hypothesis_path(sd)
    reg_data = load_hypotheses(reg_file)
    min_required = int(state.custom.get("hypothesis_min", 10))
    ok, issues = validate_register(reg_data, min_required=min_required, path=reg_file)
    if ok:
        return DiagnoseGateResult(passed=True)

    attempts = int(state.custom.get("hypothesis_regen_attempts", 0))
    retry = 3 if attempts < 1 else None
    if attempts < 1:
        state.custom["hypothesis_regen_attempts"] = attempts + 1

    sections = [_section("Hypothesis register", issues, state, "hypothesis_override_reason")]
    return merge_gate_results(
        sections,
        phase=PHASE_NAMES.get(step, f"Step {step}"),
        retry_step=retry,
        attempt=attempts,
        max_attempts=1,
        state_path=str(sp),
    )


def check_quartet_gate(state: SkillState, sp: Path, step: int) -> DiagnoseGateResult:
    """Optional first-principles + MECE when activated in problem spec."""
    sd = sp.parent
    activated = resolve_activated_techniques(sd, state.custom)
    if not requires_first_principles(activated) and not requires_mece_tree(activated):
        return DiagnoseGateResult(passed=True)

    if has_override(state.custom, "quartet_override_reason"):
        return DiagnoseGateResult(passed=True)

    active_sections: list[GateSection] = []

    if requires_first_principles(activated):
        fp_data = load_fp(fp_path(sd))
        ok, issues = validate_fp(fp_data, path=fp_path(sd))
        if not ok:
            active_sections.append(
                _section("First-principles", issues, state, "quartet_override_reason")
            )

    if requires_mece_tree(activated):
        mece_data = load_mece(mece_path(sd))
        ok2, issues2 = validate_mece(mece_data, path=mece_path(sd))
        if not ok2:
            active_sections.append(_section("MECE tree", issues2, state, "quartet_override_reason"))

    if not active_sections:
        return DiagnoseGateResult(passed=True)

    attempts = int(state.custom.get("quartet_regen_attempts", 0))
    retry = 3 if attempts < 1 else None
    if attempts < 1:
        state.custom["quartet_regen_attempts"] = attempts + 1

    return merge_gate_results(
        active_sections,
        phase=PHASE_NAMES.get(step, f"Step {step}"),
        retry_step=retry,
        attempt=attempts,
        max_attempts=1,
        state_path=str(sp),
    )


def check_step5_bundle_gate(state: SkillState, sp: Path, step: int) -> DiagnoseGateResult:
    """Hypothesis elimination + five whys + routed technique coverage."""
    sd = sp.parent
    sections: list[GateSection] = []

    reg_file = hypothesis_path(sd)
    activated = resolve_activated_techniques(sd, state.custom)
    reg_data = load_hypotheses(reg_file)
    if requires_hypothesis_register(activated) and not has_override(
        state.custom, "hypothesis_override_reason"
    ):
        ok, issues = validate_elimination(reg_data, path=reg_file)
        if not ok:
            sections.append(_section("Hypothesis elimination", issues, state, "hypothesis_override_reason"))

    confirmed = _confirmed_hypothesis_ids(reg_data) if requires_hypothesis_register(activated) else set()
    if not has_override(state.custom, "five_whys_override_reason"):
        fw_data = load_five_whys(five_whys_path(sd))
        ok, issues = validate_chains(
            fw_data,
            path=five_whys_path(sd),
            require_confirmed_link=bool(confirmed),
            confirmed_ids=confirmed,
        )
        if not ok:
            sections.append(_section("Five Whys chains", issues, state, "five_whys_override_reason"))

    if not has_override(state.custom, "technique_coverage_override_reason"):
        cov_data = load_coverage(coverage_path(sd))
        ok, issues, _ = validate_coverage(
            cov_data,
            path=coverage_path(sd),
            routed_only=True,
            allow_override_skips=True,
            adaptive=True,
            activated=activated,
        )
        if not ok:
            sections.append(
                _section("Technique coverage (routed)", issues, state, "technique_coverage_override_reason")
            )

    if not sections:
        return DiagnoseGateResult(passed=True)

    attempts = int(state.custom.get("step5_bundle_attempts", 0))
    retry = 4 if attempts < 1 else None
    if attempts < 1:
        state.custom["step5_bundle_attempts"] = attempts + 1

    return merge_gate_results(
        sections,
        phase=PHASE_NAMES.get(step, f"Step {step}"),
        retry_step=retry,
        attempt=attempts,
        max_attempts=1,
        state_path=str(sp),
    )


def check_step7_closure_gate(state: SkillState, sp: Path, step: int) -> DiagnoseGateResult:
    """Activated techniques + five whys + optional sidecars."""
    sd = sp.parent
    activated = resolve_activated_techniques(sd, state.custom)
    sections: list[GateSection] = []
    non_overridable: list[str] = []

    reg_data = load_hypotheses(hypothesis_path(sd))
    confirmed = (
        _confirmed_hypothesis_ids(reg_data)
        if requires_hypothesis_register(activated)
        else set()
    )

    if not has_override(state.custom, "technique_coverage_override_reason"):
        cov_data = load_coverage(coverage_path(sd))
        ok, issues, policy = validate_coverage(
            cov_data,
            path=coverage_path(sd),
            routed_only=False,
            allow_override_skips=False,
            adaptive=True,
            activated=activated,
        )
        non_overridable.extend(policy)
        if not ok:
            sections.append(
                _section("Technique coverage (20 techniques)", issues, state, "technique_coverage_override_reason")
            )

    if not has_override(state.custom, "five_whys_override_reason"):
        fw_data = load_five_whys(five_whys_path(sd))
        ok, issues = validate_chains(
            fw_data,
            path=five_whys_path(sd),
            require_confirmed_link=True,
            confirmed_ids=confirmed,
        )
        if not ok:
            sections.append(_section("Five Whys chains", issues, state, "five_whys_override_reason"))

    if not has_override(state.custom, "quartet_override_reason"):
        if requires_first_principles(activated):
            fp_data = load_fp(fp_path(sd))
            ok, issues = validate_fp(fp_data, path=fp_path(sd))
            if not ok:
                sections.append(
                    _section("First-principles", issues, state, "quartet_override_reason")
                )

        if requires_mece_tree(activated):
            mece_data = load_mece(mece_path(sd))
            ok2, issues2 = validate_mece(mece_data, path=mece_path(sd))
            if not ok2:
                sections.append(_section("MECE tree", issues2, state, "quartet_override_reason"))

    cov_data = load_coverage(coverage_path(sd))
    high_barrier = False
    if cov_data:
        prof = cov_data.get("incident_profile") or []
        high_barrier = any(
            "safety" in str(p).lower() or "compliance" in str(p).lower() or "high" in str(p).lower()
            for p in (prof if isinstance(prof, list) else [prof])
        )
    if high_barrier and not has_override(state.custom, "barriers_override_reason"):
        b_data = load_barriers(barriers_path(sd))
        ok, issues = validate_barriers(b_data, path=barriers_path(sd), required=True)
        if not ok:
            sections.append(_section("Barrier analysis", issues, state, "barriers_override_reason"))

    if not sections and not non_overridable:
        return DiagnoseGateResult(passed=True)

    attempts = int(state.custom.get("step7_closure_attempts", 0))
    retry = 5 if attempts < 1 else 4
    if attempts < 1:
        state.custom["step7_closure_attempts"] = attempts + 1

    return merge_gate_results(
        sections,
        phase=PHASE_NAMES.get(step, f"Step {step}"),
        retry_step=retry,
        attempt=attempts,
        max_attempts=1,
        state_path=str(sp),
        non_overridable=non_overridable or None,
    )
