"""Shared markdown table helpers for plan wave parsing."""

from __future__ import annotations

import re


def split_table_row(line: str) -> list[str]:
    if "|" not in line:
        return []
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def normalize_header(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def is_separator_row(line: str) -> bool:
    if "|" not in line:
        return False
    for ch in line.strip():
        if ch not in "|\r\n\t -:":
            return False
    return "-" in line


def wave_cell_to_int(cell: str) -> int | None:
    cell = cell.strip()
    if not cell:
        return None
    m = re.search(r"(\d+)", cell)
    if not m:
        return None
    return int(m.group(1))
