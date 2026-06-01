"""Causal linkage helpers for five-whys layer validation."""

from __future__ import annotations

import re

from scripts.diagnose.hypothesis_register import _jaccard, _word_set

_LINKAGE_JACCARD = 0.12

_SYMPTOM_ONLY = re.compile(
    r"^(the\s+)?(api|server|service|request|test|build|deploy)?\s*"
    r"(failed|crashed|errored|timed?\s*out|broken|down|unavailable)",
    re.I,
)
VAGUE_ROOT = re.compile(
    r"\b(human error|miscommunication|lack of communication|didn't test|"
    r"insufficient testing|complexity|bad luck|unknown reason)\b",
    re.I,
)


def layer_linkage_ok(because: str, why_question: str) -> bool:
    b_set = _word_set(because)
    q_set = _word_set(why_question)
    if not b_set:
        return False
    if not why_question.strip().lower().startswith("why"):
        return False
    return _jaccard(b_set, q_set) >= _LINKAGE_JACCARD


def is_symptom_only(text: str) -> bool:
    t = text.strip()
    if _SYMPTOM_ONLY.search(t) and len(t.split()) < 12:
        return True
    return False
