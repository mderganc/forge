"""MECE issue tree sidecar for diagnose."""

from __future__ import annotations

from pathlib import Path

from scripts.diagnose.diagnose_registers import load_sidecar
from scripts.diagnose.mece_tree_nodes import validate_node_entries, validate_nodes_presence
from scripts.diagnose.mece_tree_siblings import validate_sibling_categories

FILENAME = ".diagnose-mece-tree.json"

__all__ = [
    "FILENAME",
    "load_register",
    "register_path",
    "summarize",
    "validate",
]


def register_path(state_dir: Path) -> Path:
    return state_dir / FILENAME


def load_register(path: Path) -> dict | None:
    return load_sidecar(path)


def summarize(data: dict | None) -> str:
    if not data or not isinstance(data.get("nodes"), list):
        return "(No MECE tree sidecar loaded)"
    nodes = data["nodes"]
    return f"**{len(nodes)}** MECE nodes"


def validate(
    data: dict | None,
    *,
    path: Path | None = None,
    min_nodes: int = 3,
) -> tuple[bool, list[str]]:
    label = str(path) if path else FILENAME
    ok, issues, nodes = validate_nodes_presence(data, label=label, min_nodes=min_nodes)
    if not ok or nodes is None:
        return False, issues

    node_issues, _node_list, _ids, by_parent = validate_node_entries(nodes)
    issues.extend(node_issues)
    issues.extend(validate_sibling_categories(by_parent))

    return len(issues) == 0, issues
