"""Five Whys chain sidecar for diagnose."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.diagnose.diagnose_registers import load_sidecar
from scripts.diagnose.hypothesis_register import _jaccard, _word_set

FILENAME = ".diagnose-five-whys.json"
MIN_LAYERS_DEFAULT = 3
_LINKAGE_JACCARD = 0.12

_SYMPTOM_ONLY = re.compile(
    r"^(the\s+)?(api|server|service|request|test|build|deploy)?\s*"
    r"(failed|crashed|errored|timed?\s*out|broken|down|unavailable)",
    re.I,
)
_VAGUE_ROOT = re.compile(
    r"\b(human error|miscommunication|lack of communication|didn't test|"
    r"insufficient testing|complexity|bad luck|unknown reason)\b",
    re.I,
)
_VALID_STOP = frozenset({
    "actionable_process_gap",
    "defect",
    "config",
    "data",
    "dependency",
    "infrastructure",
    "design",
})


def register_path(state_dir: Path) -> Path:
    return state_dir / FILENAME


def load_register(path: Path) -> dict | None:
    return load_sidecar(path)


def summarize_chains(data: dict | None) -> str:
    if not data or not isinstance(data.get("chains"), list):
        return "(No five-whys chains loaded)"
    chains = data["chains"]
    n = len(chains)
    complete = sum(
        1 for c in chains
        if isinstance(c, dict) and c.get("root_cause") and str(c.get("root_cause")).strip()
    )
    return f"**{n}** chain(s) — **{complete}** with documented root cause"


def _layer_linkage_ok(because: str, why_question: str) -> bool:
    b_set = _word_set(because)
    q_set = _word_set(why_question)
    if not b_set:
        return False
    if not why_question.strip().lower().startswith("why"):
        return False
    return _jaccard(b_set, q_set) >= _LINKAGE_JACCARD


def _is_symptom_only(text: str) -> bool:
    t = text.strip()
    if _SYMPTOM_ONLY.search(t) and len(t.split()) < 12:
        return True
    return False


def validate_chains(
    data: dict | None,
    *,
    path: Path | None = None,
    min_layers: int = MIN_LAYERS_DEFAULT,
    require_confirmed_link: bool = False,
    confirmed_ids: set[str] | None = None,
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    label = str(path) if path else FILENAME

    if data is None:
        issues.append(
            f"No five-whys file at {label}. "
            "Create `.diagnose-five-whys.json` (draft in Phase 3, finalize in Phase 4)."
        )
        return False, issues

    symptom = data.get("symptom")
    if not symptom or not str(symptom).strip():
        issues.append("Five-whys sidecar missing non-empty 'symptom'.")

    chains = data.get("chains")
    if not isinstance(chains, list) or len(chains) < 1:
        issues.append("At least one five-whys chain is required in 'chains'.")
        return False, issues

    has_confirmed_link = False
    for cidx, chain in enumerate(chains):
        if not isinstance(chain, dict):
            issues.append(f"Chain {cidx + 1} is not an object.")
            continue
        cid = chain.get("id") or f"chain-{cidx + 1}"
        hid = chain.get("hypothesis_id")
        if hid and confirmed_ids and str(hid) in confirmed_ids:
            has_confirmed_link = True

        layers = chain.get("layers")
        if not isinstance(layers, list) or len(layers) < 1:
            issues.append(f"Chain {cid}: missing 'layers' array.")
            continue

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
            elif _is_symptom_only(because):
                issues.append(
                    f"Chain {cid} layer {level}: 'because' looks like a symptom, not a mechanism."
                )
            if not why_q:
                issues.append(f"Chain {cid} layer {level}: missing 'why_question'.")
            elif prev_because and not _layer_linkage_ok(prev_because, why_q):
                issues.append(
                    f"Chain {cid} layer {level}: why_question does not reference "
                    f"previous because (causal link broken)."
                )
            if not evidence:
                issues.append(f"Chain {cid} layer {level}: missing 'evidence'.")
            prev_because = because

        n_layers = len(layers)
        stop_reason = str(chain.get("stop_reason", "")).strip().lower()
        root = str(chain.get("root_cause", "")).strip()
        but_for = str(chain.get("but_for", "")).strip()

        if n_layers < min_layers:
            issues.append(
                f"Chain {cid}: {n_layers} layer(s); minimum is {min_layers} unless you "
                "extend the chain to an actionable root cause."
            )

        if not root:
            issues.append(f"Chain {cid}: missing 'root_cause'.")
        elif _VAGUE_ROOT.search(root) and not re.search(r"file:|migration|config|test|checklist|:\d+", root):
            issues.append(
                f"Chain {cid}: root_cause is too vague — tie to a changeable artifact."
            )
        if not but_for:
            issues.append(f"Chain {cid}: missing 'but_for' counterfactual.")

    if require_confirmed_link and confirmed_ids and not has_confirmed_link:
        issues.append(
            "At least one chain must link hypothesis_id to a confirmed register entry "
            f"(confirmed: {sorted(confirmed_ids)})."
        )

    return len(issues) == 0, issues
