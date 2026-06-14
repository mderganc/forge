"""Five Whys chain validation (linkage, layers, closure)."""

from __future__ import annotations

import re

from scripts.diagnose.text_similarity import jaccard, word_set

_LINKAGE_JACCARD = 0.12
_SYMPTOM_OVERLAP_THRESHOLD = 0.65

_SYMPTOM_ONLY = re.compile(
    r"^(the\s+)?(api|server|service|request|test|build|deploy)?\s*"
    r"(failed|crashed|errored|timed?\s*out|broken|down|unavailable)",
    re.I,
)
_SYMPTOM_PHRASES = re.compile(
    r"\b("
    r"returned?\s+\d{3}|"
    r"throws?\s+(an?\s+)?exception|"
    r"exception\s+(was\s+)?thrown|"
    r"test\s+(failed|fails|failure)|"
    r"build\s+failed|"
    r"deployment\s+failed|"
    r"timed?\s*out|"
    r"memory\s+leak|"
    r"null\s+pointer|"
    r"segfault|"
    r"crashed|"
    r"500\s+error|"
    r"404\s+not\s+found|"
    r"error\s+message|"
    r"stack\s+trace|"
    r"users?\s+(are\s+)?(unhappy|blocked|unable)|"
    r"performance\s+(degraded|issue|problem)|"
    r"latency\s+(spike|increase|issue)"
    r")\b",
    re.I,
)
_ACTIONABLE_ANCHOR = re.compile(
    r"file:|\.py:\d+|\.js:\d+|\.ts:\d+|\.tsx:\d+|migration\s+\d|"
    r"config\.|:\d+\b|checklist|procedure|\.env|settings\.|"
    r"unit\s+test\s+for|integration\s+test|missing\s+\w+|"
    r"omitted|without\s+updating|wrong\s+(column|field|query|config)",
    re.I,
)
VAGUE_ROOT = re.compile(
    r"\b(human error|miscommunication|lack of communication|didn't test|"
    r"insufficient testing|complexity|bad luck|unknown reason)\b",
    re.I,
)


def layer_linkage_ok(because: str, why_question: str) -> bool:
    b_set = word_set(because)
    q_set = word_set(why_question)
    if not b_set:
        return False
    if not why_question.strip().lower().startswith("why"):
        return False
    return jaccard(b_set, q_set) >= _LINKAGE_JACCARD


def is_symptom_only(text: str) -> bool:
    t = text.strip()
    if _SYMPTOM_ONLY.search(t) and len(t.split()) < 12:
        return True
    return False


def is_symptom_level(text: str) -> bool:
    """True when text describes observable failure, not an underlying mechanism."""
    t = text.strip()
    if not t:
        return False
    if is_symptom_only(t):
        return True
    if _SYMPTOM_PHRASES.search(t) and not _ACTIONABLE_ANCHOR.search(t):
        return True
    return False


def restates_symptom(candidate: str, symptom: str) -> bool:
    """True when candidate mostly repeats the reported symptom."""
    if not symptom or not candidate:
        return False
    return jaccard(word_set(candidate), word_set(symptom)) >= _SYMPTOM_OVERLAP_THRESHOLD


def validate_root_cause_quality(
    root_cause: str,
    *,
    symptom: str = "",
    chain_id: str = "",
) -> list[str]:
    """Return issues when a proposed root cause is still symptom-level."""
    issues: list[str] = []
    prefix = f"Chain {chain_id}: " if chain_id else ""
    root = root_cause.strip()
    if not root:
        return issues

    if is_symptom_level(root):
        issues.append(
            f"{prefix}root_cause looks like a symptom "
            f"({root!r}) — drill deeper to a changeable mechanism "
            "(code defect, config key, migration gap, missing test, process step)."
        )
    elif symptom and restates_symptom(root, symptom):
        issues.append(
            f"{prefix}root_cause restates the symptom — it must explain *why* "
            f"({root!r} vs symptom {symptom!r})."
        )

    return issues


def validate_chain_layers(chain: dict, cid: str) -> list[str]:
    issues: list[str] = []
    layers = chain.get("layers")
    if not isinstance(layers, list) or len(layers) < 1:
        issues.append(f"Chain {cid}: missing 'layers' array.")
        return issues

    prev_because = ""
    for layer in layers:
        if not isinstance(layer, dict):
            issues.append(f"Chain {cid}: invalid layer entry.")
            continue
        level = layer.get("level")
        because = str(layer.get("because", "")).strip()
        why_q = str(layer.get("why_question", "")).strip()
        evidence = str(layer.get("evidence", "")).strip()
        if not because:
            issues.append(f"Chain {cid} layer {level}: missing 'because'.")
        elif is_symptom_only(because):
            issues.append(
                f"Chain {cid} layer {level}: 'because' looks like a symptom, not a mechanism."
            )
        if not why_q:
            issues.append(f"Chain {cid} layer {level}: missing 'why_question'.")
        elif prev_because and not layer_linkage_ok(prev_because, why_q):
            issues.append(
                f"Chain {cid} layer {level}: why_question does not reference "
                f"previous because (causal link broken)."
            )
        if not evidence:
            issues.append(f"Chain {cid} layer {level}: missing 'evidence'.")
        prev_because = because

    return issues


def validate_chain_closure(
    chain: dict,
    cid: str,
    *,
    min_layers: int,
    symptom: str = "",
) -> list[str]:
    issues: list[str] = []
    layers = chain.get("layers")
    if not isinstance(layers, list):
        return issues

    n_layers = len(layers)
    root = str(chain.get("root_cause", "")).strip()
    but_for = str(chain.get("but_for", "")).strip()

    if n_layers < min_layers:
        issues.append(
            f"Chain {cid}: {n_layers} layer(s); minimum is {min_layers} unless you "
            "extend the chain to an actionable root cause."
        )

    if not root:
        issues.append(f"Chain {cid}: missing 'root_cause'.")
    elif VAGUE_ROOT.search(root) and not re.search(
        r"file:|migration|config|test|checklist|:\d+", root
    ):
        issues.append(
            f"Chain {cid}: root_cause is too vague — tie to a changeable artifact."
        )
    if not but_for:
        issues.append(f"Chain {cid}: missing 'but_for' counterfactual.")

    if root:
        issues.extend(
            validate_root_cause_quality(root, symptom=symptom, chain_id=str(cid))
        )

    return issues


def validate_confirmed_hypothesis_link(
    *,
    require_confirmed_link: bool,
    confirmed_ids: set[str] | None,
    has_confirmed_link: bool,
) -> list[str]:
    if require_confirmed_link and confirmed_ids and not has_confirmed_link:
        return [
            "At least one chain must link hypothesis_id to a confirmed register entry "
            f"(confirmed: {sorted(confirmed_ids)})."
        ]
    return []
