"""Problem specification sidecar (IS/IS-NOT, Cynefin, change analysis)."""

from __future__ import annotations

from pathlib import Path

from scripts.diagnose.diagnose_registers import load_sidecar

FILENAME = ".diagnose-problem-spec.json"
_IS_ISNOT_DIMS = ("WHAT", "WHERE", "WHEN", "EXTENT")


def register_path(state_dir: Path) -> Path:
    return state_dir / FILENAME


def load_register(path: Path) -> dict | None:
    return load_sidecar(path)


def summarize(data: dict | None) -> str:
    if not data:
        return "(No problem spec sidecar loaded)"
    domain = data.get("cynefin_domain") or "?"
    return f"Cynefin: **{domain}**; change window documented: {bool(data.get('change_window'))}"


def validate(
    data: dict | None,
    *,
    path: Path | None = None,
    strict: bool = False,
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    label = str(path) if path else FILENAME

    if data is None:
        msg = (
            f"No problem spec at {label}. "
            "Create `.diagnose-problem-spec.json` in Phase 1."
        )
        if strict:
            issues.append(msg)
            return False, issues
        issues.append(msg)
        return False, issues

    matrix = data.get("is_isnot") or data.get("is_is_not")
    if not isinstance(matrix, dict):
        issues.append("Problem spec missing 'is_isnot' object with WHAT/WHERE/WHEN/EXTENT.")
    else:
        for dim in _IS_ISNOT_DIMS:
            row = matrix.get(dim) or matrix.get(dim.lower())
            if not isinstance(row, dict):
                issues.append(f"IS/IS-NOT missing dimension {dim}.")
                continue
            for field in ("is", "is_not", "distinction"):
                val = row.get(field) or row.get(field.replace("_", ""))
                if not val or not str(val).strip():
                    issues.append(
                        f"IS/IS-NOT {dim}: missing non-empty '{field}'."
                    )

    if not data.get("cynefin_domain") or not str(data.get("cynefin_domain")).strip():
        issues.append("Problem spec missing 'cynefin_domain' (Clear/Complicated/Complex/Chaotic).")

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

    return len(issues) == 0, issues
