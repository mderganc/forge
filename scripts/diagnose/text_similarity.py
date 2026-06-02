"""Shared text normalization and overlap helpers for diagnose validators."""

from __future__ import annotations

import re


def normalize_statement(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


def word_set(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", normalize_statement(text)) if len(w) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0
