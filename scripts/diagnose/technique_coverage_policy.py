"""High-severity mandatory technique policy for diagnose coverage."""

from __future__ import annotations

# catalog L16 — mandatory when severity is high
HIGH_SEVERITY_MANDATORY = frozenset({
    "Kepner-Tregoe Problem Analysis",
    "Barrier Analysis",
    "FMEA",
    "Fault Tree Analysis",
})

_FMEA_FTA_GROUP = frozenset({"FMEA", "Fault Tree Analysis"})

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


def is_high_severity(data: dict | None) -> bool:
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


def validate_high_severity_policy(
    by_name: dict[str, dict],
    *,
    high_severity: bool,
    allow_override_skips: bool,
) -> list[str]:
    """Return non-overridable policy violations for high-severity incidents."""
    non_overridable: list[str] = []
    if not high_severity or allow_override_skips:
        return non_overridable

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
    return non_overridable


def mandatory_skip_violations(
    by_name: dict[str, dict],
    *,
    high_severity: bool,
    allow_override_skips: bool,
) -> list[str]:
    """Rows that cannot be skipped on high-severity incidents."""
    if not high_severity or allow_override_skips:
        return []
    violations: list[str] = []
    for name in HIGH_SEVERITY_MANDATORY:
        if name in _FMEA_FTA_GROUP:
            continue
        row = by_name.get(name)
        if row and str(row.get("status")) == "skipped":
            violations.append(
                f"{name} cannot be 'skipped' on high-severity incidents (catalog mandatory set)."
            )
    return violations
