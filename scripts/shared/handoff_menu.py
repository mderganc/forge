"""Skill handoff menu resolution and formatting."""

from __future__ import annotations

import json
from typing import Any

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
        ux_results = state.custom.get("ux_results") or {}
        if int(ux_results.get("failed", 0) or 0) > 0 and "diagnose" not in alts:
            alts.insert(0, "diagnose")
        mode = state.custom.get("mode", "run")
        mode_cmds = {
            "run": "test --mode run",
            "flows": "test --mode flows",
            "ux": "test --mode ux",
        }
        # Drop the current mode from alternatives; ensure the other modes appear.
        current_cmd = mode_cmds.get(mode, "test --mode run")
        alts = [a for a in alts if a != current_cmd]
        for other, cmd in mode_cmds.items():
            if other == mode:
                continue
            if cmd not in alts and f"test --mode {other}" not in alts:
                # Prefer replacing a stale same-family entry when present
                alts.append(cmd)
        # Historical swap: flows session should offer run (not another flows)
        if mode == "flows" and "test --mode flows" in alts:
            alts = [a if a != "test --mode flows" else "test --mode run" for a in alts]
        return default_cmd, alts

    if skill_name == "ux-review" and state is not None:
        findings = state.custom.get("findings") or []
        high = [
            f
            for f in findings
            if isinstance(f, dict)
            and str(f.get("severity", "")).lower() in ("blocker", "critical", "high")
        ]
        if high:
            alts = [a for a in alternatives if a != "diagnose"]
            return "diagnose", alts

    return default_cmd, list(alternatives)


def _handoff_option_rows(
    *,
    default_cmd: str | None,
    alternatives: list[str],
) -> list[tuple[str, str, bool]]:
    """Return ``(chain_cmd, description, is_default)`` rows for menu + multiselect."""
    from scripts.shared.skill_chain import COMMAND_DESCRIPTIONS

    rows: list[tuple[str, str, bool]] = []
    if default_cmd:
        rows.append(
            (default_cmd, COMMAND_DESCRIPTIONS.get(default_cmd, ""), True),
        )
    for alt_cmd in alternatives:
        rows.append((alt_cmd, COMMAND_DESCRIPTIONS.get(alt_cmd, ""), False))
    return rows


def chain_command_slug(chain_cmd: str) -> str:
    """Stable AskQuestion id (no spaces)."""
    tokens = [t.lstrip("-").replace("_", "-") for t in chain_cmd.strip().split()]
    return "-".join(tokens)


def build_handoff_multiselect_payload(
    skill_name: str,
    *,
    default_cmd: str | None,
    alternatives: list[str],
    state_path: object | None = None,
) -> dict[str, Any]:
    """Machine-readable handoff for agent AskQuestion (``allow_multiple: true``)."""
    from scripts.shared.workflow_tokens import chain_command_to_agent_invocation

    options: list[dict[str, str]] = []
    default_ids: list[str] = []

    for chain_cmd, desc, is_default in _handoff_option_rows(
        default_cmd=default_cmd,
        alternatives=alternatives,
    ):
        inv = chain_command_to_agent_invocation(chain_cmd)
        label = inv if not desc else f"{inv} — {desc}"
        if is_default:
            label += " (default)"
            default_ids.append(chain_command_slug(chain_cmd))
        options.append(
            {
                "id": chain_command_slug(chain_cmd),
                "chain_cmd": chain_cmd,
                "label": label,
            }
        )

    options.append({"id": "stop", "label": "(stop) — exit the workflow here"})

    payload: dict[str, Any] = {
        "type": "forge_handoff_multiselect",
        "skill": skill_name,
        "allow_multiple": True,
        "title": f"Next after {skill_name}",
        "prompt": "Which Forge workflow(s) should run next? (multiselect)",
        "options": options,
        "default_option_ids": default_ids,
        "shortcuts": {
            "default": 'Reply "yes" or "1" for the default only.',
            "stop": 'Reply "stop" to exit without running another skill.',
        },
    }
    if state_path:
        payload["state_file"] = str(state_path)
    return payload


def format_handoff_multiselect_block(
    skill_name: str,
    *,
    default_cmd: str | None,
    alternatives: list[str],
    state_path: object | None = None,
) -> str:
    payload = build_handoff_multiselect_payload(
        skill_name,
        default_cmd=default_cmd,
        alternatives=alternatives,
        state_path=state_path,
    )
    body = json.dumps(payload, indent=2, ensure_ascii=True)
    return (
        "**Agent (Cursor / Claude):** Present the block below with **AskQuestion** "
        "(`allow_multiple: true`). Use the option labels verbatim (`/forge:…` or `$forge:…`).\n\n"
        f"```handoff-multiselect\n{body}\n```"
    )


def format_handoff_menu_lines(
    skill_name: str,
    *,
    default_cmd: str | None,
    alternatives: list[str],
    state_path: object | None = None,
) -> list[str]:
    from scripts.shared.workflow_tokens import (
        chain_command_to_agent_invocation,
        workflow_invocation_prefix,
    )

    prefix = workflow_invocation_prefix()
    lines = [
        "",
        f"WORKFLOW HANDOFF — {skill_name} complete",
        "=" * (len(skill_name) + 22),
        "",
        format_handoff_multiselect_block(
            skill_name,
            default_cmd=default_cmd or None,
            alternatives=alternatives,
            state_path=state_path,
        ),
        "",
        f"**Text fallback** (same options; prefix `{prefix}`):",
        "",
    ]

    option_num = 1
    rows = _handoff_option_rows(default_cmd=default_cmd or None, alternatives=alternatives)

    if default_cmd:
        inv = chain_command_to_agent_invocation(default_cmd)
        desc = rows[0][1] if rows else ""
        desc_text = f" — {desc}" if desc else ""
        lines.append('Reply **"yes"** or **"1"** for the default, or pick numbers:')
        lines.append(f"  {option_num}. `{inv}`{desc_text} **(default)**")
        option_num += 1
        for chain_cmd, desc, _ in rows[1:]:
            inv = chain_command_to_agent_invocation(chain_cmd)
            desc_text = f" — {desc}" if desc else ""
            lines.append(f"  {option_num}. `{inv}`{desc_text}")
            option_num += 1
    else:
        lines.append("**(none — workflow terminates here)**")
        for chain_cmd, desc, _ in rows:
            inv = chain_command_to_agent_invocation(chain_cmd)
            desc_text = f" — {desc}" if desc else ""
            lines.append(f"  {option_num}. `{inv}`{desc_text}")
            option_num += 1

    lines.extend(
        [
            f"  {option_num}. `(stop)` — exit the workflow here",
            "",
            f"Resume any time: `forge takeover` or `{chain_command_to_agent_invocation('takeover')}`",
        ]
    )
    if state_path:
        lines.append(f"**State file:** `{state_path}`")
    return lines
