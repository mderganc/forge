"""Hypothesis register validation helpers."""

from __future__ import annotations

from scripts.diagnose.five_whys_validate import is_symptom_level, restates_symptom
from scripts.diagnose.hypothesis_register import FISHBONE_CATEGORIES, VALID_STATUSES


def validate_hypothesis_entry(
    h: dict,
    idx: int,
    issues: list[str],
    *,
    categories: set[str],
    seen_ids: set[str],
    statements: list[str],
) -> None:
    hid = h.get("id")
    if not hid or not str(hid).strip():
        issues.append(f"Hypothesis entry {idx + 1} missing non-empty 'id'.")
    elif str(hid) in seen_ids:
        issues.append(f"Duplicate hypothesis id: {hid!r}.")
    else:
        seen_ids.add(str(hid))

    statement = h.get("statement")
    if not statement or not str(statement).strip():
        issues.append(f"Hypothesis {hid or idx + 1} missing non-empty 'statement'.")
    else:
        statements.append(str(statement))

    cat = h.get("category")
    if cat:
        cat_upper = str(cat).strip().upper()
        if cat_upper not in FISHBONE_CATEGORIES:
            issues.append(
                f"Hypothesis {hid or idx + 1} has invalid category {cat!r} "
                f"(expected one of {sorted(FISHBONE_CATEGORIES)})."
            )
        else:
            categories.add(cat_upper)

    status = h.get("status", "open")
    if str(status) not in VALID_STATUSES:
        issues.append(f"Hypothesis {hid or idx + 1} has invalid status {status!r}.")


def validate_confirmed_and_ruled_out(
    h: dict,
    issues: list[str],
    *,
    symptom: str,
) -> None:
    if str(h.get("status")) == "confirmed":
        statement = str(h.get("statement", "")).strip()
        hid = h.get("id", "?")
        if statement and is_symptom_level(statement):
            issues.append(
                f"Hypothesis {hid} is confirmed but its statement is symptom-level "
                f"({statement!r}) — confirm a changeable mechanism, not the failure mode."
            )
        elif statement and symptom and restates_symptom(statement, symptom):
            issues.append(
                f"Hypothesis {hid} is confirmed but restates the symptom "
                f"({statement!r}) — state the underlying cause."
            )

    if str(h.get("status")) == "ruled_out":
        reason = h.get("ruled_out_reason")
        if not reason or not str(reason).strip():
            issues.append(
                f"Hypothesis {h.get('id', '?')} is ruled_out but missing 'ruled_out_reason'."
            )
