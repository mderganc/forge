"""Documentation completion gate for implement step 8 (handoff).

Reads `.implement-documentation-gate.json` beside the implement state file and
validates the plan file Documentation section has no skeleton markers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.shared.workflow_gate import (
    exit_if_gate_fails as _exit_if_gate_fails,
    gate_sidecar_path as _gate_sidecar_path,
    load_gate_json,
)

DOCUMENTATION_GATE_FILE = ".implement-documentation-gate.json"
DOCUMENTATION_MARKER_ID = "DOCUMENTATION"
SKELETON_PREFIX = "<!-- FORGE_SKELETON: "
SKELETON_SUFFIX = " -->"


def documentation_skeleton_marker(plan_path: Path) -> str:
    return f"{SKELETON_PREFIX}{DOCUMENTATION_MARKER_ID}{SKELETON_SUFFIX}"


def plan_documentation_section_complete(plan_path: Path | None) -> tuple[bool, str]:
    """True if plan has no Documentation skeleton marker."""
    if plan_path is None or not plan_path.is_file():
        return False, "Plan path missing or not a file — cannot verify Documentation section."
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError as e:
        return False, f"Cannot read plan file: {e}"
    marker = documentation_skeleton_marker(plan_path)
    if marker in text:
        return False, (
            "Plan file still contains unfilled Documentation skeleton marker. "
            f"Fill `## Documentation` in `{plan_path}`."
        )
    return True, ""


def gate_sidecar_path(state_path: Path) -> Path:
    return _gate_sidecar_path(state_path, DOCUMENTATION_GATE_FILE)


def _normalize_audience_level(raw: str) -> str:
    s = raw.strip().lower().replace("-", "_").replace(" ", "_")
    if s in ("architect/expert", "architect_expert", "expert", "architect"):
        return "architect_expert"
    if s in ("technical_operator", "operator", "technicaloperator"):
        return "technical_operator"
    if s == "user":
        return "user"
    return s


def _parse_applicable(raw: Any) -> bool | None:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if s in ("yes", "true", "1", "y"):
        return True
    if s in ("no", "false", "0", "n"):
        return False
    return None


def _audience_levels_ok(rows: list[Any]) -> tuple[bool, str]:
    required = {"architect_expert", "technical_operator", "user"}
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        al = _normalize_audience_level(str(row.get("audience_level", "")))
        if al not in required:
            continue
        seen.add(al)
        if "justification" not in row or not str(row.get("justification", "")).strip():
            return False, f"audience_matrix row needs non-empty justification for {al}"
        app = _parse_applicable(row.get("applicable"))
        if app is None:
            return False, f"audience_matrix row has invalid 'applicable' for {al}"
        if app:
            ev = str(row.get("delivery_evidence", "")).strip()
            if not ev:
                return (
                    False,
                    f"audience_matrix: when applicable=true for {al}, "
                    "non-empty delivery_evidence is required (what shipped).",
                )
    if seen != required:
        return False, (
            "audience_matrix must include architect_expert, technical_operator, "
            f"user (found {sorted(seen)})"
        )
    return True, ""


def _external_wiki_ok(rows: Any) -> tuple[bool, str]:
    if rows is None:
        return False, "external_wiki_checklist key missing (use [] if none)."
    if not isinstance(rows, list):
        return False, "external_wiki_checklist must be an array."
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            return False, f"external_wiki_checklist[{i}] must be an object."
        status = str(row.get("status", "")).strip().lower()
        ev = str(row.get("evidence_link", row.get("evidence", ""))).strip()
        na_status = status in ("na", "n/a", "not_applicable", "none", "skipped")
        if not na_status and not ev:
            return (
                False,
                f"external_wiki_checklist[{i}]: provide evidence_link or mark status N/A.",
            )
    return True, ""


def handoff_docs_summary(data: dict[str, Any] | None) -> dict[str, str]:
    """Extract human-readable lines for implement handoff context."""
    if not data:
        return {
            "Docs Completed": "(no gate file — see gate validation)",
            "External Wiki Evidence": "(none)",
        }
    lines: list[str] = []
    am = data.get("audience_matrix")
    if isinstance(am, list):
        for row in am:
            if not isinstance(row, dict):
                continue
            al = row.get("audience_level", "?")
            app = row.get("applicable", "")
            ev = row.get("delivery_evidence", "")
            lines.append(f"- {al} (applicable={app}): {ev or '(no evidence recorded)'}")
    wiki = data.get("external_wiki_checklist")
    wiki_txt = (
        json.dumps(wiki, indent=2)
        if isinstance(wiki, list) and wiki
        else "(none or N/A)"
    )
    return {
        "Docs Completed": "\n".join(lines) if lines else "(see gate JSON)",
        "External Wiki Evidence": wiki_txt,
    }


def validate_documentation_gate(
    state_path: Path,
    plan_path: Path | None,
    *,
    allow_incomplete: bool = False,
    override_reason: str = "",
    override_requested_by: str = "",
    override_follow_up: str = "",
    override_timestamp: str = "",
) -> tuple[bool, str]:
    """Return (ok, message). If not ok, message is human-readable for stderr."""

    if allow_incomplete:
        if not override_reason.strip():
            return (
                False,
                "ERROR: --allow-docs-incomplete requires a non-empty "
                "`--docs-override-reason`.",
            )
        if not override_follow_up.strip():
            return (
                False,
                "ERROR: --allow-docs-incomplete requires a non-empty "
                "`--docs-override-follow-up`.",
            )
        ts = override_timestamp or "(timestamp not set)"
        return True, (
            "Documentation gate OVERRIDDEN by user.\n"
            f"Reason: {override_reason.strip()}\n"
            f"Requested by: {override_requested_by or '(not set)'}\n"
            f"Follow-up: {override_follow_up.strip()}\n"
            f"Recorded at: {ts}"
        )

    ok_plan, plan_msg = plan_documentation_section_complete(plan_path)
    if not ok_plan:
        return False, plan_msg

    sidecar = gate_sidecar_path(state_path)
    data = load_gate_json(sidecar)

    if data is None:
        return (
            False,
            f"ERROR: Missing documentation gate file: {sidecar}\n"
            "Complete step 7 (documentation) and write the gate file — "
            "see prompts/implement/documentation.md.",
        )

    if not data.get("complete"):
        return False, "ERROR: documentation gate JSON has complete: false."

    am = data.get("audience_matrix")
    if not isinstance(am, list):
        return False, "ERROR: documentation gate JSON missing audience_matrix array."

    ok_am, am_msg = _audience_levels_ok(am)
    if not ok_am:
        return False, f"ERROR: audience_matrix invalid — {am_msg}"

    ok_w, w_msg = _external_wiki_ok(data.get("external_wiki_checklist"))
    if not ok_w:
        return False, f"ERROR: external wiki checklist — {w_msg}"

    return True, ""


def exit_if_gate_fails(ok: bool, msg: str) -> None:
    _exit_if_gate_fails(
        ok,
        msg,
        error_prefix="",
        echo_msg_on_success=True,
    )
