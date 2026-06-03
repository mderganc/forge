"""Root-cause closure and chain-level policy for five-whys."""

from __future__ import annotations

import re

from scripts.diagnose.five_whys_linkage import VAGUE_ROOT, validate_root_cause_quality


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
