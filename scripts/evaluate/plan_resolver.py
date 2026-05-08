"""Plan resolution — find a plan file by path or keyword search.

Supports three modes:
1. Exact file path — validated and returned directly.
2. Keyword search — scores all .md files under docs/ by filename and title match.
3. No argument — lists recent .md files by modification time.
"""

from __future__ import annotations

import re
from pathlib import Path


def extract_title(path: Path) -> str:
    """Extract title from YAML frontmatter, or fall back to filename stem."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return path.stem

    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            frontmatter = text[3:end]
            for line in frontmatter.splitlines():
                if line.strip().startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip("'\"")
                    if title:
                        return title
    return path.stem


def score_file(path: Path, keywords: list[str], title: str) -> int:
    """Score a file against search keywords. Higher = better match."""
    score = 0
    name_lower = path.stem.lower()
    title_lower = title.lower()

    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in name_lower:
            score += 2
        if kw_lower in title_lower:
            score += 1
    return score


_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", ".env", ".tox", ".mypy_cache"}


def _find_md_files(search_root: Path) -> list[Path]:
    """Find all .md files under search_root, sorted by mtime descending.

    Skips hidden directories and common noise directories.
    Handles broken symlinks and permission errors gracefully.
    """
    mtime_cache: dict[Path, float] = {}
    for p in search_root.rglob("*.md"):
        # Skip files inside ignored directories
        if any(part in _SKIP_DIRS or part.startswith(".") for part in p.relative_to(search_root).parts[:-1]):
            continue
        try:
            mtime_cache[p] = p.stat().st_mtime
        except OSError:
            continue
    files = list(mtime_cache.keys())
    files.sort(key=lambda p: mtime_cache[p], reverse=True)
    return files


def resolve_plan(
    query: str,
    search_root: Path,
    *,
    return_matches: bool = False,
    max_results: int = 5,
) -> Path | list[Path]:
    """Resolve a plan query to a file path.

    Args:
        query: File path or space-separated keywords.
        search_root: Root directory to search for .md files.
        return_matches: If True, return list of matches instead of single path.
        max_results: Max matches to return in keyword mode.

    Returns:
        Single Path (return_matches=False) or list[Path] (return_matches=True).

    Raises:
        FileNotFoundError: If exact path doesn't exist or no keyword matches found.
    """
    query = query.strip()

    candidate = Path(query)
    if candidate.suffix == ".md" and candidate.exists():
        return [candidate] if return_matches else candidate

    relative = search_root / query
    if relative.suffix == ".md" and relative.exists():
        return [relative] if return_matches else relative

    if "/" in query and query.endswith(".md"):
        raise FileNotFoundError(f"Plan file not found: {query}")

    keywords = query.split()
    if not keywords:
        files = _find_md_files(search_root)[:max_results]
        if not files:
            raise FileNotFoundError(f"No .md files found under {search_root}")
        return files if return_matches else files[0]

    md_files = _find_md_files(search_root)
    scored: list[tuple[int, Path]] = []
    for f in md_files:
        title = extract_title(f)
        s = score_file(f, keywords, title)
        if s > 0:
            scored.append((s, f))

    scored.sort(key=lambda x: (-x[0], x[1].name))

    if not scored:
        raise FileNotFoundError(f"No plans matching keywords: {' '.join(keywords)}")

    matches = [path for _, path in scored[:max_results]]
    return matches if return_matches else matches[0]
