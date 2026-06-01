"""Technique coverage matrix sidecar for diagnose (20 catalog techniques)."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.diagnose.diagnose_registers import load_sidecar
from scripts.diagnose.technique_coverage_policy import (
    HIGH_SEVERITY_MANDATORY,
    is_high_severity,
    mandatory_skip_violations,
    validate_high_severity_policy,
)
from scripts.diagnose.technique_coverage_rows import (
    VALID_STATUSES,
    build_technique_index,
    validate_catalog_names,
    validate_row_statuses,
)
from scripts.evaluate.template_engine import read_prompt_file

COVERAGE_FILENAME = ".diagnose-technique-coverage.json"
CATALOG_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "diagnose" / "technique_catalog.md"

__all__ = [
    "COVERAGE_FILENAME",
    "CATALOG_PATH",
    "VALID_STATUSES",
    "HIGH_SEVERITY_MANDATORY",
    "coverage_path",
    "load_catalog_technique_names",
    "catalog_technique_names",
    "summarize_coverage",
    "validate_coverage",
    "load_sidecar",
]


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

    by_name, row_issues = build_technique_index(techniques)
    issues.extend(row_issues)
    issues.extend(validate_catalog_names(by_name, expected))

    routed = set(data.get("routing_preferred") or [])
    high_sev = is_high_severity(data)
    issues.extend(
        validate_row_statuses(
            by_name,
            expected,
            routed=routed,
            routed_only=routed_only,
        )
    )
    non_overridable.extend(
        mandatory_skip_violations(
            by_name,
            high_severity=high_sev,
            allow_override_skips=allow_override_skips,
        )
    )
    non_overridable.extend(
        validate_high_severity_policy(
            by_name,
            high_severity=high_sev,
            allow_override_skips=allow_override_skips,
        )
    )

    ok = len(issues) == 0 and len(non_overridable) == 0
    return ok, issues, non_overridable
