"""Resume memory summary helpers (extracted from resume_context)."""

from __future__ import annotations

from pathlib import Path


def _strip_yaml_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[2].lstrip()
    return text


def summary_from_synthesis(mem_dir: Path, *, max_lines: int = 24, max_chars: int = 2000) -> str:
    from scripts.shared.memory_synthesis import SYNTHESIS_FILENAME
    from scripts.shared.resume_context import _first_non_empty_lines

    syn = mem_dir / SYNTHESIS_FILENAME
    try:
        if syn.is_file():
            raw = syn.read_text(encoding="utf-8", errors="replace")
            body = _strip_yaml_frontmatter(raw).strip()
            if body:
                return _first_non_empty_lines(body, max_lines=max_lines, max_chars=max_chars)
    except OSError:
        pass
    return ""


def summary_from_newest_handoff(mem_dir: Path) -> str:
    from scripts.shared.resume_context import _first_non_empty_lines

    best: tuple[float, str] | None = None
    if not mem_dir.is_dir():
        return ""
    for p in mem_dir.glob("handoff-*.md"):
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        if best is None or mtime > best[0]:
            try:
                best = (mtime, p.read_text(encoding="utf-8"))
            except OSError:
                continue
    if best and best[1].strip():
        return _first_non_empty_lines(best[1])
    return ""
