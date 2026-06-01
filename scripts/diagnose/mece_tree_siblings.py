"""MECE sibling mutual-exclusion checks."""

from __future__ import annotations


def validate_sibling_categories(by_parent: dict[str | None, list[dict]]) -> list[str]:
    """Flag same-parent siblings sharing a category without mutual_exclusion_note."""
    issues: list[str] = []
    for parent_key, siblings in by_parent.items():
        if len(siblings) < 2:
            continue
        cats: dict[str, list] = {}
        for s in siblings:
            c = str(s.get("category", "")).strip().upper()
            if c:
                cats.setdefault(c, []).append(s)
        for cat, group in cats.items():
            if len(group) > 1:
                without_note = [
                    s for s in group
                    if not str(s.get("mutual_exclusion_note", "")).strip()
                ]
                if len(without_note) > 1:
                    issues.append(
                        f"MECE siblings under parent {parent_key!r} share category {cat} "
                        "without mutual_exclusion_note — branches may overlap."
                    )
    return issues
