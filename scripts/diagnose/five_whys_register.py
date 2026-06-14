"""Five Whys chain sidecar for diagnose."""

from __future__ import annotations

from pathlib import Path

from scripts.diagnose.diagnose_registers import load_sidecar
from scripts.diagnose.five_whys_validate import (
    validate_chain_closure,
    validate_chain_layers,
    validate_confirmed_hypothesis_link,
)

FILENAME = ".diagnose-five-whys.json"
MIN_LAYERS_DEFAULT = 3

_VALID_STOP = frozenset({
    "actionable_process_gap",
    "defect",
    "config",
    "data",
    "dependency",
    "infrastructure",
    "design",
})

__all__ = [
    "FILENAME",
    "MIN_LAYERS_DEFAULT",
    "VALID_STOP",
    "load_register",
    "register_path",
    "summarize_chains",
    "validate_chains",
]


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

    symptom_text = str(symptom or "").strip()
    has_confirmed_link = False
    for cidx, chain in enumerate(chains):
        if not isinstance(chain, dict):
            issues.append(f"Chain {cidx + 1} is not an object.")
            continue
        cid = chain.get("id") or f"chain-{cidx + 1}"
        hid = chain.get("hypothesis_id")
        if hid and confirmed_ids and str(hid) in confirmed_ids:
            has_confirmed_link = True

        issues.extend(validate_chain_layers(chain, str(cid)))
        issues.extend(
            validate_chain_closure(
                chain, str(cid), min_layers=min_layers, symptom=symptom_text
            )
        )

    issues.extend(
        validate_confirmed_hypothesis_link(
            require_confirmed_link=require_confirmed_link,
            confirmed_ids=confirmed_ids,
            has_confirmed_link=has_confirmed_link,
        )
    )

    return len(issues) == 0, issues
