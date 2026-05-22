"""Technique coverage matrix sidecar for diagnose (20 catalog techniques)."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.diagnose.diagnose_registers import load_sidecar
from scripts.evaluate.template_engine import read_prompt_file

COVERAGE_FILENAME = ".diagnose-technique-coverage.json"
CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "diagnose" / "technique_catalog.md"

VALID_STATUSES = frozenset({"applied", "skipped", "deferred"})

# catalog L16 — mandatory when severity is high
HIGH_SEVERITY_MANDATORY = frozenset({
    "Kepner-Tregoe Problem Analysis",
    "Barrier Analysis",
    "FMEA",
    "Fault Tree Analysis",
})

# At least one of these pairs satisfies FMEA-or-FTA rule
_FMEA_FTA_GROUP = frozenset({"FMEA", "Fault Tree Analysis"})


def coverage_path(state_dir: Path) -> Path:
    return state_dir / COVERAGE_FILENAME


def load_catalog_technique_names(catalog_path: Path | None = None) -> list[str]:
    """Parse exact technique names from technique_catalog.md table."""
    if catalog_path is None:
        label = "diagnose/technique_catalog.md"
        text = read_prompt_file(label)
    else:
        label = str(catalog_path)
        text = catalog_path.read_text(encoding="utf-8")
    by_id: dict[int, str] = {}
    for line in text.splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|", line.strip())
        if m:
            num = int(m.group(1))
            if 1 <= num <= 20:
                by_id[num] = m.group(2).strip()
    names = [by_id[i] for i in range(1, 21) if i in by_id]
    if len(names) != 20:
        raise ValueError(
            f"Expected 20 techniques in {label}, parsed {len(names)}: {names}"
        )
    return names


_CATALOG_NAMES: list[str] | None = None


def catalog_technique_names() -> list[str]:
    global _CATALOG_NAMES
    if _CATALOG_NAMES is None:
        _CATALOG_NAMES = load_catalog_technique_names()
    return list(_CATALOG_NAMES)


def summarize_coverage(data: dict | None) -> str:
    if not data or not isinstance(data.get("techniques"), list):
        return "(No technique coverage matrix loaded)"
    counts: dict[str, int] = {}
    for row in data["techniques"]:
        if isinstance(row, dict):
            st = str(row.get("status", "?"))
            counts[st] = counts.get(st, 0) + 1
    parts = [f"{k}: {v}" for k, v in sorted(counts.items())]
    return "**20** techniques — " + ", ".join(parts) if parts else "**20** techniques"


_HIGH_SEVERITY_PROFILE_TOKENS = frozenset({
    "high_severity",
    "high",
    "critical",
    "severe",
    "safety",
    "compliance",
    "high_consequence",
    "high_severity_incident",
})


def _profile_token_is_high_severity(token: str) -> bool:
    norm = str(token).lower().strip().replace("-", "_")
    if norm in _HIGH_SEVERITY_PROFILE_TOKENS:
        return True
    return norm.startswith("high_severity")


def _is_high_severity(data: dict | None) -> bool:
    if not data:
        return False
    if data.get("high_severity") is True:
        return True
    profile = data.get("incident_profile") or data.get("severity")
    if isinstance(profile, str):
        return _profile_token_is_high_severity(profile)
    if isinstance(profile, list):
        return any(_profile_token_is_high_severity(p) for p in profile)
    sev = data.get("severity")
    if isinstance(sev, str):
        return _profile_token_is_high_severity(sev)
    return False


def validate_coverage(
    data: dict | None,
    *,
    path: Path | None = None,
    routed_only: bool = False,
    allow_override_skips: bool = True,
) -> tuple[bool, list[str], list[str]]:
    """
    Validate coverage matrix.

    Returns (ok, issues, non_overridable_issues).
    """
    issues: list[str] = []
    non_overridable: list[str] = []
    label = str(path) if path else COVERAGE_FILENAME
    expected = catalog_technique_names()

    if data is None:
        issues.append(
            f"No technique coverage file at {label}. "
            "Create `.diagnose-technique-coverage.json` with all 20 catalog techniques."
        )
        return False, issues, non_overridable

    techniques = data.get("techniques")
    if not isinstance(techniques, list):
        issues.append(f"Coverage at {label} must contain a 'techniques' array.")
        return False, issues, non_overridable

    by_name: dict[str, dict] = {}
    for idx, row in enumerate(techniques):
        if not isinstance(row, dict):
            issues.append(f"Technique row {idx + 1} is not an object.")
            continue
        name = row.get("name")
        if not name or not str(name).strip():
            issues.append(f"Technique row {idx + 1} missing 'name'.")
            continue
        name_s = str(name).strip()
        if name_s in by_name:
            issues.append(f"Duplicate technique name: {name_s!r}.")
        else:
            by_name[name_s] = row

    missing = [n for n in expected if n not in by_name]
    extra = [n for n in by_name if n not in expected]
    if missing:
        issues.append(f"Coverage matrix missing techniques: {', '.join(missing)}.")
    if extra:
        issues.append(f"Unknown technique names (use catalog exactly): {', '.join(extra)}.")

    routed = set(data.get("routing_preferred") or [])
    high_sev = _is_high_severity(data)

    for name in expected:
        row = by_name.get(name)
        if not row:
            continue
        status = str(row.get("status", "")).strip().lower()
        if status not in VALID_STATUSES:
            issues.append(f"{name}: invalid status {row.get('status')!r}.")
            continue
        if status == "applied":
            ptr = row.get("evidence_pointer")
            if not ptr or not str(ptr).strip():
                issues.append(f"{name}: status 'applied' requires non-empty evidence_pointer.")
        elif status == "skipped":
            rationale = row.get("rationale")
            if not rationale or not str(rationale).strip():
                issues.append(f"{name}: status 'skipped' requires non-empty rationale.")
            if (
                high_sev
                and name in HIGH_SEVERITY_MANDATORY
                and name not in _FMEA_FTA_GROUP
                and not allow_override_skips
            ):
                non_overridable.append(
                    f"{name} cannot be 'skipped' on high-severity incidents (catalog mandatory set)."
                )
        elif status == "deferred":
            trigger = row.get("trigger")
            if not trigger or not str(trigger).strip():
                issues.append(f"{name}: status 'deferred' requires non-empty trigger.")

        if routed_only and name in routed:
            if status == "skipped" and (not row.get("rationale") or not str(row.get("rationale")).strip()):
                issues.append(
                    f"{name} was in routing_preferred but is skipped without rationale."
                )

    if high_sev and not allow_override_skips:
        applied_names = {
            n for n, r in by_name.items() if str(r.get("status")) == "applied"
        }
        for mandatory in HIGH_SEVERITY_MANDATORY:
            if mandatory in _FMEA_FTA_GROUP:
                continue
            row = by_name.get(mandatory)
            if mandatory not in applied_names:
                if row and str(row.get("status")) == "skipped":
                    non_overridable.append(
                        f"High-severity: '{mandatory}' cannot be skipped."
                    )
                else:
                    non_overridable.append(
                        f"High-severity: '{mandatory}' must be applied with evidence."
                    )
        if not (applied_names & _FMEA_FTA_GROUP):
            non_overridable.append(
                "High-severity: at least one of FMEA or Fault Tree Analysis must be applied."
            )

    ok = len(issues) == 0 and len(non_overridable) == 0
    return ok, issues, non_overridable
