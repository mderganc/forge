"""Append-only Studio feedback log in Forge runtime memory (agent context)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

STUDIO_LOG_FILENAME = "studio-log.md"


def studio_log_path(repo_root: Path) -> Path:
    from scripts.shared.orchestrator import runtime_memory_dir

    return runtime_memory_dir(repo_root) / STUDIO_LOG_FILENAME


def _ts_label(ts: int | None) -> str:
    if ts is None:
        return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(ts))


def format_event_markdown(event: dict[str, Any]) -> str:
    """One markdown block for a single Studio event."""
    gate = event.get("gate") or "(no gate)"
    ts = event.get("ts")
    lines = [f"#### {_ts_label(ts if isinstance(ts, int) else None)} — `{gate}`", ""]
    etype = str(event.get("type", "event"))

    if etype == "click":
        lines.append(
            f"- **Selection:** {event.get('label') or event.get('choice') or '?'} "
            f"(`{event.get('choice', '')}`)"
        )
    elif etype == "submit":
        choices = event.get("choices") or []
        lines.append(f"- **Multi-select:** {', '.join(str(c) for c in choices)}")
    elif etype == "probe-response":
        lines.append(f"- **Probe `{event.get('probe_id', '')}`:** {event.get('text', '')}")
        if event.get("prompt"):
            lines.append(f"  - _Question:_ {event['prompt']}")
    elif etype == "probes-submit":
        lines.append("- **Probe answers (batch):**")
        for item in event.get("responses") or []:
            if not isinstance(item, dict):
                continue
            pid = item.get("probe_id", "q")
            text = item.get("text", "")
            lines.append(f"  - **`{pid}`:** {text}")
            if item.get("prompt"):
                lines.append(f"    - _Question:_ {item['prompt']}")
    elif etype == "feedback":
        lines.append(f"- **Freeform feedback:** {event.get('text', '')}")
    elif etype == "done":
        lines.append("- **Done reviewing** this screen.")
    elif etype == "approve":
        lines.append(
            f"- **Approved (locked):** `{event.get('gate', '')}` → `{event.get('html_path', '')}`"
        )
    elif etype == "unlock":
        lines.append(f"- **Unlocked:** `{event.get('gate', '')}` (editing allowed again)")
    else:
        lines.append(f"- **{etype}:** {event.get('label') or event.get('text') or event}")

    lines.append("")
    return "\n".join(lines)


def ensure_studio_log_header(repo_root: Path, *, session_id: str, workflow: str) -> Path:
    path = studio_log_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.is_file():
        path.write_text(
            "# Studio session log\n\n"
            "> Auto-appended from Forge Studio browser gates. "
            "Agents must read this file (or `{{STUDIO_LOG}}` in orchestrator output) "
            "before continuing visual gates. Summarize into `project.md` when the gate closes.\n\n",
            encoding="utf-8",
        )
    header = (
        f"\n## Session `{session_id}` ({workflow})\n\n"
        f"Started: {_ts_label(None)}\n\n"
    )
    with path.open("a", encoding="utf-8") as fh:
        fh.write(header)
    return path


def append_studio_log(repo_root: Path, event: dict[str, Any]) -> None:
    path = studio_log_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(format_event_markdown(event))


def read_studio_log(repo_root: Path | None = None) -> str:
    from scripts.shared.orchestrator import read_memory_file, runtime_memory_dir

    if repo_root is not None:
        path = studio_log_path(repo_root)
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return ""
    return read_memory_file(STUDIO_LOG_FILENAME)


def studio_log_context_block(repo_root: Path | None = None) -> str:
    text = read_studio_log(repo_root).strip()
    if not text:
        return "(No Studio interactions logged yet — see `templates/studio.md`.)"
    return text
