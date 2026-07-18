"""Problem specification sidecar (adaptive framing + optional KT/Cynefin/change)."""

from __future__ import annotations

from pathlib import Path

from scripts.diagnose.diagnose_framing import FRAMING_ENTRIES, FRAMING_TO_CATALOG
from scripts.diagnose.diagnose_registers import load_sidecar

FILENAME = ".diagnose-problem-spec.json"
_IS_ISNOT_DIMS = ("WHAT", "WHERE", "WHEN", "EXTENT")
_CYNEFIN_DOMAINS = frozenset({"Clear", "Complicated", "Complex", "Chaotic"})


def register_path(state_dir: Path) -> Path:
    return state_dir / FILENAME


def load_register(path: Path) -> dict | None:
    return load_sidecar(path)


def summarize(data: dict | None) -> str:
    if not data:
        return "(No problem spec sidecar loaded)"
    entry = data.get("framing_entry") or "?"
    domain = data.get("cynefin_domain") or "—"
    n_activated = len(data.get("activated_techniques") or data.get("routing_preferred") or [])
    return (
        f"Framing: **{entry}**; Cynefin: **{domain}**; "
        f"activated/routed techniques: **{n_activated}**"
    )


def _needs_change_analysis(data: dict) -> bool:
    entry = data.get("framing_entry")
    if entry == "kepner_tregoe":
        return True
    profile = data.get("incident_profile") or data.get("severity") or []
    tokens = profile if isinstance(profile, list) else [profile]
    joined = " ".join(str(t).lower() for t in tokens)
    return any(
        kw in joined
        for kw in (
            "regression",
            "sudden",
            "worked_before",
            "deploy",
            "highlight_regression",
        )
    )


def _validate_framing_entry(data: dict, entry: str | None) -> list[str]:
    issues: list[str] = []
    if not entry or str(entry).strip() not in FRAMING_ENTRIES:
        issues.append(
            "Problem spec missing 'framing_entry' — one of: "
            + ", ".join(sorted(FRAMING_ENTRIES))
            + "."
        )
        return issues

    entry_s = str(entry).strip()
    if entry_s == "kepner_tregoe":
        issues.extend(_validate_is_isnot(data))
    elif entry_s == "cynefin":
        issues.extend(_validate_cynefin(data))
    elif entry_s == "first_principles":
        fp = data.get("first_principles_snapshot")
        if not isinstance(fp, dict) or not fp.get("invariants"):
            issues.append(
                "framing_entry 'first_principles' needs 'first_principles_snapshot.invariants' "
                "(or complete `.diagnose-first-principles.json` before step 4)."
            )
    elif entry_s == "evidence_snapshot":
        obs = data.get("observations")
        if not isinstance(obs, list) or len(obs) < 1:
            issues.append(
                "framing_entry 'evidence_snapshot' needs non-empty 'observations' "
                "(timestamp, source, fact)."
            )
    elif entry_s == "mece_sketch":
        sketch = data.get("mece_sketch")
        nodes = sketch.get("nodes") if isinstance(sketch, dict) else None
        if not isinstance(nodes, list) or len(nodes) < 2:
            issues.append(
                "framing_entry 'mece_sketch' needs 'mece_sketch.nodes' with at least 2 nodes "
                "(or `.diagnose-mece-tree.json` before step 4)."
            )
    return issues


def validate(
    data: dict | None,
    *,
    path: Path | None = None,
    strict: bool = False,
) -> tuple[bool, list[str]]:
    from scripts.diagnose.register_validation import (
        finish_validation,
        missing_sidecar_issue,
        require_non_empty_str,
    )

    issues: list[str] = []
    label = str(path) if path else FILENAME

    if data is None:
        msg = f"No problem spec at {label}. Create `.diagnose-problem-spec.json` in Phase 1."
        if strict:
            issues.append(msg)
            return False, issues
        issues.append(msg)
        return False, issues

    require_non_empty_str(
        data,
        "problem_statement",
        issues,
        message=(
            "Problem spec missing non-empty 'problem_statement' (one-paragraph symptom/impact)."
        ),
    )

    entry = data.get("framing_entry")
    issues.extend(_validate_framing_entry(data, str(entry).strip() if entry else None))

    if _needs_change_analysis(data):
        lkg = data.get("last_known_good")
        if not lkg or not str(lkg).strip():
            issues.append("Change analysis missing 'last_known_good'.")
        if not data.get("change_window") and not data.get("candidate_changes"):
            issues.append(
                "Change analysis needs 'change_window' and/or non-empty 'candidate_changes'."
            )

    routing = data.get("routing_preferred")
    if routing is not None and not isinstance(routing, list):
        issues.append("'routing_preferred' must be an array of technique names.")

    activated = data.get("activated_techniques")
    if activated is not None and not isinstance(activated, list):
        issues.append("'activated_techniques' must be an array of catalog technique names.")

    if strict and entry in FRAMING_ENTRIES:
        mapped = FRAMING_TO_CATALOG.get(str(entry).strip())
        if mapped:
            combined = set(routing or []) | set(activated or [])
            if mapped not in combined and "5 Whys" not in combined:
                issues.append(
                    f"Include framing technique {mapped!r} in 'activated_techniques' "
                    "or 'routing_preferred'."
                )

    return finish_validation(issues)


def _validate_is_isnot(data: dict) -> list[str]:
    issues: list[str] = []
    matrix = data.get("is_isnot") or data.get("is_is_not")
    if not isinstance(matrix, dict):
        issues.append("Problem spec missing 'is_isnot' object with WHAT/WHERE/WHEN/EXTENT.")
        return issues
    for dim in _IS_ISNOT_DIMS:
        row = matrix.get(dim) or matrix.get(dim.lower())
        if not isinstance(row, dict):
            issues.append(f"IS/IS-NOT missing dimension {dim}.")
            continue
        for field in ("is", "is_not", "distinction"):
            val = row.get(field) or row.get(field.replace("_", ""))
            if not val or not str(val).strip():
                issues.append(f"IS/IS-NOT {dim}: missing non-empty '{field}'.")
    return issues


def _validate_cynefin(data: dict) -> list[str]:
    issues: list[str] = []
    domain = data.get("cynefin_domain")
    if not domain or not str(domain).strip():
        issues.append("Problem spec missing 'cynefin_domain' (Clear/Complicated/Complex/Chaotic).")
    elif str(domain).strip() not in _CYNEFIN_DOMAINS:
        issues.append(f"Invalid cynefin_domain: {domain!r}.")
    note = data.get("cynefin_strategy_note") or data.get("strategy_note")
    if not note or not str(note).strip():
        issues.append(
            "Cynefin framing needs 'cynefin_strategy_note' (how domain shapes investigation)."
        )
    return issues
