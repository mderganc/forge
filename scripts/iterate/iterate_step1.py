"""Iterate step-1 initialization helpers."""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts.shared.orchestrator import SkillState


def apply_natural_language_args(
    args: argparse.Namespace,
    *,
    goal: str,
    target_raw: str,
    max_loops: int | None,
) -> tuple[str, str, int | None, str]:
    extra = (getattr(args, "text", None) or getattr(args, "natural_text", None) or "")
    nl_conf = "high"
    if isinstance(extra, str) and extra.strip():
        from scripts.iterate.iterate import parse_natural_iterate

        ng, nt, nl, nl_conf = parse_natural_iterate(extra)
        if not goal and ng:
            goal = ng
        if not target_raw and nt:
            target_raw = nt
        if max_loops is None and nl is not None:
            max_loops = nl
    return goal, target_raw, max_loops, nl_conf


def needs_clarification(
    *,
    goal: str,
    spec_confidence: str | None,
    extra: object,
    nl_conf: str,
) -> bool:
    if not goal:
        return True
    if spec_confidence == "low":
        return True
    if isinstance(extra, str) and extra.strip() and nl_conf in ("medium", "low"):
        return True
    return False


def build_step1_body(
    *,
    goal: str,
    target_raw: str,
    max_loops: int,
    gate_subdir: str,
    clarification: bool,
    nl_conf: str,
    extra: object,
) -> list[str]:
    body_parts = [
        "## Iterate — session initialized",
        "",
        f"**Goal:** {goal or '(not set — provide goal via flags or natural language)'}",
        f"**Target:** {target_raw or '(not set)'}",
        f"**Max outer loops:** {max_loops}",
        "",
        "### Gate directory",
        f"Create JSON gate files under `{gate_subdir}/` in Forge runtime memory (next to handoffs).",
        "",
        "### Next",
        "Run the **diagnose** workflow through completion. Then write gate file `diagnose.json`:",
        "```json",
        '{"status":"pass","open_findings_total":0,"open_findings_critical":0,"evidence_refs":[]}',
        "```",
        "",
        "Continue iterate at **step 2**.",
    ]
    if clarification:
        body_parts.extend([
            "",
            "### Clarification needed",
            "Confirm measurable target (name, threshold) and verification harness.",
        ])
        if isinstance(extra, str) and extra.strip() and nl_conf in ("medium", "low"):
            body_parts.append(
                f"Natural-language parsing confidence is **{nl_conf}** — confirm goal, target, "
                "and max loops explicitly or restate using `--goal`, `--target`, and `--max-loops`."
            )
    return body_parts


def populate_step1_state(
    state: SkillState,
    args: argparse.Namespace,
    *,
    goal: str,
    target_raw: str,
    max_loops: int,
    nl_conf: str,
    clarification: bool,
) -> None:
    state.custom["goal"] = goal
    state.custom["target_raw"] = target_raw
    state.custom["max_loops"] = int(max_loops)
    state.custom["nl_parse_confidence"] = nl_conf
    if getattr(args, "metric_command", None):
        state.custom["metric_command"] = str(args.metric_command)
    if getattr(args, "harness", None):
        state.custom["harness_hint"] = str(args.harness)
    from scripts.iterate.iterate import parse_target_spec, target_spec_to_dict

    spec, _conf = parse_target_spec(target_raw)
    state.custom["target_spec"] = target_spec_to_dict(spec)
    state.custom["clarification_needed"] = clarification
