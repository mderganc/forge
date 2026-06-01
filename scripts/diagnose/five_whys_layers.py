"""Per-layer validation for five-whys chains."""

from __future__ import annotations

from scripts.diagnose.five_whys_linkage import is_symptom_only, layer_linkage_ok


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
