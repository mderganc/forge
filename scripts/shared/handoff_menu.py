"""Skill handoff menu resolution and formatting."""

from __future__ import annotations

from scripts.shared.skill_state import SkillState


def resolve_handoff_commands(
    skill_name: str,
    state: SkillState | None,
    *,
    default_cmd: str,
    alternatives: list[str],
) -> tuple[str, list[str]]:
    """Apply skill-specific overrides to default and alternative next commands."""
    if skill_name == "diagnose" and state is not None:
        fc = str(state.custom.get("fix_complexity", "unknown")).lower()
        base_alts = list(alternatives)
        if fc == "large":
            return "design", [c for c in base_alts if c not in ("design", "develop")]
        if fc == "complex":
            return "plan", [c for c in base_alts if c != "plan"]

    if skill_name == "test" and state is not None:
        alts = list(alternatives)
        test_results = state.custom.get("test_results", {})
        if test_results.get("failed", 0) > 0 and "diagnose" not in alts:
            alts.insert(0, "diagnose")
        mode = state.custom.get("mode", "run")
        if mode == "flows" and "test --mode flows" in alts:
            idx = alts.index("test --mode flows")
            alts[idx] = "test --mode run"
        elif mode == "run" and "test --mode run" in alts:
            idx = alts.index("test --mode run")
            alts[idx] = "test --mode flows"
        return default_cmd, alts

    return default_cmd, list(alternatives)


def format_handoff_menu_lines(
    skill_name: str,
    *,
    default_cmd: str,
    alternatives: list[str],
    state_path: object | None = None,
) -> list[str]:
    from scripts.shared.skill_chain import COMMAND_DESCRIPTIONS
    from scripts.shared.workflow_tokens import chain_command_to_agent_invocation

    lines = ["", f"WORKFLOW HANDOFF — {skill_name} complete", ""]
    option_num = 1

    if default_cmd:
        desc = COMMAND_DESCRIPTIONS.get(default_cmd, "")
        desc_text = f" ({desc})" if desc else ""
        inv = chain_command_to_agent_invocation(default_cmd)
        lines.append('**Default (reply "yes" or "1"):**')
        lines.append(f"1. `{inv}`{desc_text}")
        option_num = 2
    else:
        lines.append("**(none — workflow terminates here)**")

    if alternatives:
        lines.append("")
        lines.append("**Alternatives:**")
        for alt_cmd in alternatives:
            desc = COMMAND_DESCRIPTIONS.get(alt_cmd, "")
            desc_text = f" ({desc})" if desc else ""
            lines.append(f"{option_num}. `{chain_command_to_agent_invocation(alt_cmd)}`{desc_text}")
            option_num += 1

    lines.append("")
    lines.append("**To stop without transitioning:**")
    lines.append("Reply 'stop' (stop) and the workflow will end here.")
    if state_path:
        lines.append("")
        lines.append(f"**State file:** `{state_path}`")
    return lines
