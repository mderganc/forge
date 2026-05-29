"""Graphify contract text injected into Forge skill step output.

When a repo has a Graphify index, workflow steps print a mandatory reminder
before agents grep/glob/search raw files.

Disable entirely: ``FORGE_SKIP_GRAPHIFY=1`` or ``forge graphify off``.
Defer during implement waves: ``forge graphify defer-waves`` or
``forge implement --defer-graphify-waves`` on step 1.
"""

from __future__ import annotations

import os
from pathlib import Path

from forge_next.graphify_enforcement import (
    graphify_deferred_note,
    graphify_fully_disabled,
    should_show_graphify_banner,
)

# Skills that primarily explore or map the codebase (stronger wording).
INVESTIGATION_SKILLS = frozenset({"develop", "diagnose", "plan", "test", "evaluate"})

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
    investigate = slug in INVESTIGATION_SKILLS
    lead = (
        "This phase explores or maps the codebase — **Graphify is mandatory** "
        "before search tools or bulk source reads."
        if investigate
        else "This repo has a Graphify knowledge graph — follow it before raw search."
    )

    lines = [
        bar,
        "GRAPHIFY — codebase map (required before raw search)",
        bar,
        "",
        lead,
        "",
        "**Before** grep, glob, ripgrep, semantic/codebase search, or reading source "
        "files for architecture or cross-module questions:",
        "",
        "1. Read **`graphify-out/GRAPH_REPORT.md`** (god nodes + communities).",
        "2. If **`graphify-out/wiki/index.md`** exists, navigate the wiki instead of raw files.",
        "3. For “how does X relate to Y”, prefer **`graphify query`**, **`graphify path`**, "
        "or **`graphify explain`** over scanning the tree.",
        "",
        "**After** you edit tracked code in this session, run **`graphify update .`** "
        "(AST-only, no API cost).",
        "",
    ]

    excerpt = graph_report_excerpt(root)
    if excerpt:
        lines.extend(["**Snapshot (read the full report for navigation):**", "", excerpt, ""])

    lines.append(
        f"_Step {step} of `{slug}` — disable: `FORGE_SKIP_GRAPHIFY=1` or `forge graphify off`; "
        "defer implement waves: `forge graphify defer-waves`._"
    )
    lines.append("")
    return "\n".join(lines)
