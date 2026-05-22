"""MECE issue tree sidecar for diagnose."""

from __future__ import annotations

from pathlib import Path

from scripts.diagnose.diagnose_registers import load_sidecar
from scripts.diagnose.hypothesis_register import FISHBONE_CATEGORIES

FILENAME = ".diagnose-mece-tree.json"


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
    issues: list[str] = []
    label = str(path) if path else FILENAME

    if data is None:
        issues.append(
            f"No MECE tree at {label}. Create `.diagnose-mece-tree.json` in Phase 3."
        )
        return False, issues

    nodes = data.get("nodes")
    if not isinstance(nodes, list) or len(nodes) < min_nodes:
        issues.append(
            f"MECE tree needs at least {min_nodes} nodes in 'nodes' array."
        )
        return False, issues

    ids: set[str] = set()
    by_parent: dict[str | None, list[dict]] = {}
    node_list: list[dict] = []

    for idx, node in enumerate(nodes):
        if not isinstance(node, dict):
            issues.append(f"MECE node {idx + 1} is not an object.")
            continue
        node_list.append(node)
        nid = node.get("id")
        if not nid or not str(nid).strip():
            issues.append(f"MECE node {idx + 1} missing 'id'.")
            continue
        nid_s = str(nid)
        if nid_s in ids:
            issues.append(f"Duplicate MECE node id: {nid_s!r}.")
        ids.add(nid_s)

        label_n = node.get("label") or node.get("statement")
        if not label_n or not str(label_n).strip():
            issues.append(f"MECE node {nid_s} missing label/statement.")

        cat = node.get("category")
        if cat:
            cat_u = str(cat).strip().upper()
            if cat_u not in FISHBONE_CATEGORIES:
                issues.append(f"MECE node {nid_s} invalid category {cat!r}.")

        parent = node.get("parent_id")
        parent_key = str(parent) if parent is not None else None
        by_parent.setdefault(parent_key, []).append(node)

    for node in node_list:
        pid = node.get("parent_id")
        if pid is not None and str(pid) not in ids:
            issues.append(
                f"MECE node {node.get('id')}: parent_id {pid!r} not found."
            )

    # Sibling overlap: same parent, same category, no mutual_exclusion_note
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

    return len(issues) == 0, issues
