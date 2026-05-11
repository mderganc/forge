"""Rewrite `forge-memory-synthesis.md` as an explicit merge of existing memory files.

Called after skill state saves so `forge resume` and humans have a single
curated rollup under `memory/` without replacing hand-written `current-step.md`
or handoffs.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SYNTHESIS_FILENAME = "forge-memory-synthesis.md"
MAX_PROJECT_CHARS = 14_000
MAX_HANDOFF_CHARS = 3_000
MAX_HANDOFF_FILES = 5
MAX_CURRENT_STEP_CHARS = 8_000


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _truncate(s: str, limit: int) -> str:
    s = s.strip()
    if len(s) <= limit:
        return s
    return s[: limit - 20] + "\n\n…(truncated)…"


def _read_if(path: Path, limit: int) -> str:
    try:
        if path.is_file():
            return _truncate(path.read_text(encoding="utf-8", errors="replace"), limit)
    except OSError:
        pass
    return ""


def _memory_candidates(search_dir: Path | None) -> list[Path]:
    from scripts.shared.orchestrator import legacy_memory_dir, runtime_memory_dir

    out: list[Path] = []
    for base in (runtime_memory_dir(search_dir), legacy_memory_dir(search_dir)):
        if base.is_dir():
            out.append(base)
    # de-dupe same resolved path
    seen: set[Path] = set()
    uniq: list[Path] = []
    for p in out:
        try:
            r = p.resolve()
        except OSError:
            r = p
        if r not in seen:
            seen.add(r)
            uniq.append(p)
    return uniq


def _collect_handoff_excerpts(search_dir: Path | None) -> list[tuple[str, str]]:
    """Return list of (label, excerpt) newest first."""
    rows: list[tuple[float, str, str]] = []
    for mem in _memory_candidates(search_dir):
        for p in mem.glob("handoff-*.md"):
            m = re.match(r"^handoff-(.+)\.md$", p.name, re.I)
            skill = m.group(1) if m else p.stem
            try:
                mtime = p.stat().st_mtime
            except OSError:
                continue
            body = _read_if(p, MAX_HANDOFF_CHARS)
            if body:
                rows.append((mtime, f"handoff-{skill}", body))
    rows.sort(key=lambda t: t[0], reverse=True)
    return [(label, body) for _, label, body in rows[:MAX_HANDOFF_FILES]]


def _first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.is_file():
            return p
    return None


def write_memory_synthesis(
    *,
    skill_name: str,
    current_step: int,
    last_completed_step: int,
    max_step: int,
    state_path: Path,
    search_dir: Path | None = None,
    footer_md: str | None = None,
) -> None:
    """Build `memory/forge-memory-synthesis.md` from project + current-step + handoffs."""
    try:
        from scripts.shared.orchestrator import runtime_memory_dir

        mem_dir = runtime_memory_dir(search_dir)
        mem_dir.mkdir(parents=True, exist_ok=True)
        out_path = mem_dir / SYNTHESIS_FILENAME

        parts: list[str] = []
        project_chunks: list[str] = []
        current_chunks: list[str] = []
        for mem in _memory_candidates(search_dir):
            proj = mem / "project.md"
            t = _read_if(proj, MAX_PROJECT_CHARS)
            if t:
                project_chunks.append(f"### From `{proj.name}` @ `{mem}`\n\n{t}")
            curp = mem / "current-step.md"
            t2 = _read_if(curp, MAX_CURRENT_STEP_CHARS)
            if t2:
                current_chunks.append(f"### From `{curp.name}` @ `{mem}`\n\n{t2}")

        project_block = "\n\n".join(project_chunks) if project_chunks else "_No `project.md` content found._"
        current_block = "\n\n".join(current_chunks) if current_chunks else "_No `current-step.md` content found._"

        handoffs = _collect_handoff_excerpts(search_dir)
        if handoffs:
            ho_lines = []
            for label, body in handoffs:
                ho_lines.append(f"### {label}\n\n{body}")
            handoff_block = "\n\n".join(ho_lines)
        else:
            handoff_block = "_No `handoff-*.md` files with content._"

        lines = [
            "---",
            f"forge_synthesis_skill: {skill_name}",
            f"forge_synthesis_step: {current_step}",
            f"forge_synthesis_updated: {_utc_stamp()}",
            "---",
            "",
            "# Forge memory synthesis",
            "",
            "This file is **auto-generated** when workflow state is saved. It rolls up",
            "existing memory files so resume and new chats can open **one** narrative",
            "summary without replacing `current-step.md` or handoffs.",
            "",
            "## Active workflow (from last state save)",
            "",
            f"- **Skill:** `{skill_name}`",
            f"- **Step:** {current_step} / {max_step} (last completed: {last_completed_step})",
            f"- **State file:** `{state_path}`",
            "",
            "## Rolled up: project context",
            "",
            project_block,
            "",
            "## Rolled up: current-step notes",
            "",
            current_block,
            "",
            "## Rolled up: recent handoffs (newest first)",
            "",
            handoff_block,
            "",
        ]
        if footer_md:
            lines.extend(["", footer_md.strip(), ""])
        out_path.write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        return


def write_memory_synthesis_from_skill_state(state: Any, state_path: Path, search_dir: Path | None = None) -> None:
    write_memory_synthesis(
        skill_name=getattr(state, "skill_name", "unknown"),
        current_step=int(getattr(state, "current_step", 0) or 0),
        last_completed_step=int(getattr(state, "last_completed_step", 0) or 0),
        max_step=int(getattr(state, "max_step", 6) or 6),
        state_path=state_path,
        search_dir=search_dir,
    )


def write_memory_synthesis_evaluate(
    *,
    plan_name: str,
    mode: str | None,
    current_step: int,
    last_completed_step: int,
    max_step: int,
    state_path: Path,
    search_dir: Path | None = None,
) -> None:
    footer = (
        "## Evaluate session\n\n"
        f"- **Plan:** `{plan_name}`\n"
        f"- **Mode:** `{mode or 'pre'}`\n"
    )
    write_memory_synthesis(
        skill_name="evaluate",
        current_step=current_step,
        last_completed_step=last_completed_step,
        max_step=max_step,
        state_path=state_path,
        search_dir=search_dir,
        footer_md=footer,
    )
