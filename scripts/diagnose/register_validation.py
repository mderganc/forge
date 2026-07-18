"""Shared non-fatal validation helpers for diagnose register sidecars."""

from __future__ import annotations

from typing import Any, Callable


def missing_sidecar_issue(label: str, create_hint: str) -> tuple[bool, list[str]]:
    return False, [
        f"No sidecar at {label}. {create_hint}",
    ]


def require_version(
    data: dict,
    issues: list[str],
    *,
    expected: int = 1,
) -> None:
    version = data.get("version")
    if version is not None and version != expected:
        issues.append(f"'version' must be {expected} when present.")


def require_non_empty_str(
    data: dict,
    field: str,
    issues: list[str],
    *,
    message: str | None = None,
) -> bool:
    value = data.get(field)
    if value and str(value).strip():
        return True
    issues.append(message or f"'{field}' must be a non-empty string.")
    return False


def require_bool_field(
    data: dict,
    field: str,
    issues: list[str],
    *,
    message: str | None = None,
) -> bool:
    value = data.get(field)
    if value is True or value is False:
        return True
    issues.append(message or f"'{field}' must be true or false.")
    return False


def require_list_min(
    data: dict,
    field: str,
    min_len: int,
    issues: list[str],
    *,
    item_check: Callable[[Any, int], str | None] | None = None,
) -> bool:
    value = data.get(field)
    if not isinstance(value, list) or len(value) < min_len:
        issues.append(
            f"'{field}' must be a list with at least {min_len} item(s)."
        )
        return False
    if item_check:
        for i, item in enumerate(value):
            msg = item_check(item, i)
            if msg:
                issues.append(msg)
    return True


def require_enum(
    data: dict,
    field: str,
    allowed: frozenset[str],
    issues: list[str],
    *,
    message: str | None = None,
) -> str | None:
    raw = data.get(field)
    if not raw or str(raw).strip() not in allowed:
        issues.append(
            message
            or f"'{field}' required — one of: {', '.join(sorted(allowed))}."
        )
        return None
    return str(raw).strip()


def finish_validation(issues: list[str]) -> tuple[bool, list[str]]:
    return len(issues) == 0, issues
