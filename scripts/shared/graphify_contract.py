"""Graphify contract text injected into Forge orchestrator step output.

Graphify **refresh and GRAPHIFY banners** run on **`forge ship --step 1`** (or
``$forge:ship``) at finalize time — not on develop/plan/implement/code-review/test/
diagnose/evaluate steps.

Disable entirely: ``FORGE_SKIP_GRAPHIFY=1`` or ``forge graphify off``.
"""

from __future__ import annotations

import os
from pathlib import Path

from forge_next.graphify_enforcement import (
    graphify_deferred_note,
    graphify_fully_disabled,
    should_show_graphify_banner,
)

_GRAPH_REPORT_CANDIDATES = (
    "graphify-out/GRAPH_REPORT.md",
    "GRAPH_REPORT.md",
)


def skip_forge_graphify_banner(repo_root: Path | None = None) -> bool:
    """Return True when Graphify is fully disabled (env or ``forge graphify off``)."""
    return graphify_fully_disabled((repo_root or Path.cwd()).resolve())


def graph_index_present(repo_root: Path) -> bool:
    """True when the repo appears to have a Graphify knowledge graph."""
    root = repo_root.resolve()
    if (root / "graphify-out" / "graph.json").is_file():
        return True
    for rel in _GRAPH_REPORT_CANDIDATES:
        if (root / rel).is_file():
            return True
    rt_graph = root / ".codex" / "forge" / "graphify" / "GRAPH_REPORT.md"
    if rt_graph.is_file():
        return True
    legacy = root / ".codex" / "forge-codex" / "graphify" / "GRAPH_REPORT.md"
    return legacy.is_file()


def _first_non_empty_lines(text: str, *, max_lines: int = 14, max_chars: int = 1100) -> str:
    lines: list[str] = []
    total = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if total + len(line) + 1 > max_chars:
            break
        lines.append(line)
        total += len(line) + 1
        if len(lines) >= max_lines:
            break
    return "\n".join(lines)


def graph_report_excerpt(repo_root: Path, *, max_chars: int = 1100) -> str:
    """Short excerpt from GRAPH_REPORT.md for step banners."""
    root = repo_root.resolve()
    for rel in _GRAPH_REPORT_CANDIDATES:
        p = root / rel
        if not p.is_file():
            continue
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        excerpt = _first_non_empty_lines(body, max_chars=max_chars)
        if excerpt:
            return f"(from `{rel}`)\n{excerpt}"
    return ""


def forge_graphify_banner(
    skill_name: str,
    step: int,
    repo_root: Path | None = None,
) -> str:
    """Return a Graphify reminder block for skill step output, or empty string."""
    root = (repo_root or Path.cwd()).resolve()
    if graphify_fully_disabled(root):
        return ""
    if not graph_index_present(root):
        return ""
    slug = skill_name.strip().lower()
    if not should_show_graphify_banner(slug, step, root):
        return graphify_deferred_note(slug, step, root)

    bar = ("=" * 60) if os.environ.get("FORGE_ASCII") == "1" else ("━" * 60)
    lines = [
        bar,
        "GRAPHIFY — refresh before you ship",
        bar,
        "",
        "You are on **`forge ship`** — update the knowledge graph **before** commit/PR/publish.",
        "",
        "1. The orchestrator already ran **`forge graphify refresh`** (foreground) for this step.",
        "2. Read **`graphify-out/GRAPH_REPORT.md`** if you need navigation context for the ship summary.",
        "3. If **`graphify-out/wiki/index.md`** exists, use it instead of bulk file reads.",
        "4. For cross-module questions in the PR body or review, prefer **`graphify query`**, "
        "**`graphify path`**, **`graphify explain`**.",
        "",
        "Other workflow skills (`develop`, `plan`, `implement`, `code-review`, `test`, "
        "`diagnose`, `evaluate`) **do not** print GRAPHIFY blocks — graphify runs here at ship time.",
        "",
    ]

    excerpt = graph_report_excerpt(root)
    if excerpt:
        lines.extend(["**Snapshot (read the full report for navigation):**", "", excerpt, ""])

    lines.append(
        f"_Step {step} of `{slug}` — disable: `FORGE_SKIP_GRAPHIFY=1` or `forge graphify off`._"
    )
    lines.append("")
    return "\n".join(lines)
