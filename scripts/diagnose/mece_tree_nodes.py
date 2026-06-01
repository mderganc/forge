"""MECE tree node structure validation."""

from __future__ import annotations

from scripts.diagnose.hypothesis_register import FISHBONE_CATEGORIES


def validate_nodes_presence(
    data: dict | None,
    *,
    label: str,
    min_nodes: int,
) -> tuple[bool, list[str], list | None]:
    """Return (ok, issues, nodes) after presence and minimum-count checks."""
    issues: list[str] = []
    if data is None:
        issues.append(
            f"No MECE tree at {label}. Create `.diagnose-mece-tree.json` in Phase 3."
        )
        return False, issues, None

    nodes = data.get("nodes")
    if not isinstance(nodes, list) or len(nodes) < min_nodes:
        issues.append(
            f"MECE tree needs at least {min_nodes} nodes in 'nodes' array."
        )
        return False, issues, None

    return True, issues, nodes


def validate_node_entries(nodes: list) -> tuple[list[str], list[dict], set[str], dict[str | None, list[dict]]]:
    """Validate each node; return issues, node_list, ids, and siblings-by-parent map."""
    issues: list[str] = []
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

    return issues, node_list, ids, by_parent
