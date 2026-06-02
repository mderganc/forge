"""Row-level validation for the diagnose technique coverage matrix."""

from __future__ import annotations

VALID_STATUSES = frozenset({"applied", "skipped", "deferred"})


def build_technique_index(
    techniques: list,
) -> tuple[dict[str, dict], list[str]]:
    """Parse techniques array into name -> row map; return row-level issues."""
    issues: list[str] = []
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
    return by_name, issues


def validate_catalog_names(
    by_name: dict[str, dict],
    expected: list[str],
    *,
    required_names: list[str] | None = None,
) -> list[str]:
    """Ensure matrix rows use catalog names; require subset when adaptive."""
    issues: list[str] = []
    catalog = set(expected)
    extra = [n for n in by_name if n not in catalog]
    if extra:
        issues.append(f"Unknown technique names (use catalog exactly): {', '.join(extra)}.")

    if required_names is not None:
        missing = [n for n in required_names if n not in by_name]
        if missing:
            issues.append(
                f"Coverage matrix missing activated techniques: {', '.join(missing)}."
            )
    else:
        missing = [n for n in expected if n not in by_name]
        if missing:
            issues.append(f"Coverage matrix missing techniques: {', '.join(missing)}.")
    return issues


def validate_row_statuses(
    by_name: dict[str, dict],
    expected: list[str],
    *,
    routed: set[str],
    routed_only: bool,
    names_to_check: list[str] | None = None,
) -> list[str]:
    """Validate per-technique status, evidence, rationale, and defer triggers."""
    issues: list[str] = []
    check = names_to_check if names_to_check is not None else expected
    for name in check:
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
        elif status == "deferred":
            trigger = row.get("trigger")
            if not trigger or not str(trigger).strip():
                issues.append(f"{name}: status 'deferred' requires non-empty trigger.")

        if routed_only and name in routed:
            if status == "skipped" and (
                not row.get("rationale") or not str(row.get("rationale")).strip()
            ):
                issues.append(
                    f"{name} was in routing_preferred but is skipped without rationale."
                )
    return issues
