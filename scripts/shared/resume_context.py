"""Continuity snapshot and Graphify status helpers for `forge takeover`.

Persists a single `resume-context.json` under the runtime state directory on
every skill state save, and reads optional `graphify-status.json` written by
the Graphify refresh hook.
"""

from __future__ import annotations

import json
import re
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Lazy imports from orchestrator are avoided at top level where possible;
# callers pass search_dir/repo_root explicitly using orchestrator helpers.

RESUME_CONTEXT_SCHEMA_VERSION = 2
RESUME_CONTEXT_SCHEMA_VERSION_V1 = 1
RESUME_CONTEXT_WRITER_VERSION = "forge-next:2"
RESUME_CONTEXT_FILENAME = "resume-context.json"
GRAPHIFY_STATUS_FILENAME = "graphify-status.json"

# Default staleness: 24 hours since last successful graph refresh
GRAPHIFY_STALE_HOURS_DEFAULT = 24

REQUIRED_SNAPSHOT_KEYS_V1 = frozenset(
    {"schema_version", "skill", "current_step", "last_completed_step", "max_step", "state_path", "updated_at"}
)
REQUIRED_SNAPSHOT_KEYS = frozenset({"schema_version", "focus", "sessions", "updated_at"})


def resume_context_path(search_dir: Path | None = None) -> Path:
    from scripts.shared.orchestrator import runtime_state_dir

    return runtime_state_dir(search_dir) / RESUME_CONTEXT_FILENAME


def graphify_status_path(search_dir: Path | None = None) -> Path:
    from scripts.shared.orchestrator import runtime_state_dir

    return runtime_state_dir(search_dir) / GRAPHIFY_STATUS_FILENAME


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _infer_invocation_status_skill(state: Any) -> str:
    """Map SkillState fields to success | retry | in_progress."""
    fc = int(getattr(state, "failure_count", 0) or 0)
    cur = int(getattr(state, "current_step", 0) or 0)
    last = int(getattr(state, "last_completed_step", 0) or 0)
    max_step = int(getattr(state, "max_step", 6) or 6)
    if fc > 0:
        return "retry"
    if cur > 0 and last == cur and cur < max_step:
        return "success"
    if cur >= max_step and last >= max_step:
        return "success"
    return "in_progress"


def _latest_handoff_info(search_dir: Path | None) -> tuple[str | None, str | None]:
    """Return (relative_path, skill_name) for newest handoff-*.md by mtime."""
    from scripts.shared.orchestrator import legacy_memory_dir, runtime_memory_dir

    best: tuple[float, Path, str] | None = None
    repo = Path(search_dir) if search_dir else None
    if repo is None:
        from scripts.shared.orchestrator import _detect_repo_root

        repo = _detect_repo_root()

    for mem in (runtime_memory_dir(search_dir), legacy_memory_dir(search_dir)):
        if not mem.is_dir():
            continue
        for p in mem.glob("handoff-*.md"):
            try:
                mtime = p.stat().st_mtime
            except OSError:
                continue
            m = re.match(r"^handoff-(.+)\.md$", p.name)
            skill = m.group(1) if m else None
            if best is None or mtime > best[0]:
                best = (mtime, p, skill or "")
    if not best:
        return None, None
    _, path, skill = best
    try:
        rel = path.resolve().relative_to(repo.resolve())
        return str(rel).replace("\\", "/"), skill or None
    except ValueError:
        return str(path), skill or None


def _current_step_path(search_dir: Path | None) -> str | None:
    from scripts.shared.orchestrator import legacy_memory_dir, runtime_memory_dir

    repo = Path(search_dir) if search_dir else None
    if repo is None:
        from scripts.shared.orchestrator import _detect_repo_root

        repo = _detect_repo_root()
    for mem in (runtime_memory_dir(search_dir), legacy_memory_dir(search_dir)):
        p = mem / "current-step.md"
        if p.is_file():
            try:
                return str(p.resolve().relative_to(repo.resolve())).replace("\\", "/")
            except ValueError:
                return str(p)
    return None


def _open_findings_count(state: Any) -> int:
    try:
        return len([f for f in getattr(state, "findings", []) or [] if f.get("status") != "dismissed"])
    except Exception:
        return 0


def _session_entry_from_state(state: Any, state_path: Path) -> dict[str, Any]:
    from scripts.shared.session_store import session_id_from_state_path

    sid = getattr(state, "session_id", None) or session_id_from_state_path(state_path) or ""
    return {
        "session_id": sid,
        "skill": getattr(state, "skill_name", "unknown"),
        "state_path": str(Path(state_path).resolve()),
        "current_step": int(getattr(state, "current_step", 0) or 0),
        "last_completed_step": int(getattr(state, "last_completed_step", 0) or 0),
        "max_step": int(getattr(state, "max_step", 6) or 6),
        "label": getattr(state, "label", None) or "",
        "updated_at": _utc_now_iso(),
        "invocation_status": _infer_invocation_status_skill(state),
        "open_findings_count": _open_findings_count(state),
    }


def _migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    """Wrap a v1 single-skill blob as a v2 index."""
    entry = {
        "session_id": "",
        "skill": data.get("skill", "unknown"),
        "state_path": data.get("state_path", ""),
        "current_step": data.get("current_step", 0),
        "last_completed_step": data.get("last_completed_step", 0),
        "max_step": data.get("max_step", 6),
        "label": "",
        "updated_at": data.get("updated_at") or _utc_now_iso(),
        "invocation_status": data.get("invocation_status"),
        "open_findings_count": data.get("open_findings_count", 0),
    }
    # Best-effort session id from path
    try:
        from scripts.shared.session_store import session_id_from_state_path

        entry["session_id"] = session_id_from_state_path(Path(str(entry["state_path"]))) or ""
    except Exception:
        pass
    for key in ("evaluate_plan_path", "evaluate_plan_name", "evaluate_mode"):
        if key in data:
            entry[key] = data[key]
    focus = entry["session_id"] or "legacy"
    return {
        "schema_version": RESUME_CONTEXT_SCHEMA_VERSION,
        "writer_version": RESUME_CONTEXT_WRITER_VERSION,
        "focus": focus,
        "updated_at": data.get("updated_at") or _utc_now_iso(),
        "sessions": [entry],
        # Keep top-level mirrors for older readers during transition
        "skill": entry["skill"],
        "current_step": entry["current_step"],
        "last_completed_step": entry["last_completed_step"],
        "max_step": entry["max_step"],
        "state_path": entry["state_path"],
        "invocation_status": entry.get("invocation_status"),
        "memory_latest_handoff_path": data.get("memory_latest_handoff_path"),
        "memory_latest_handoff_skill": data.get("memory_latest_handoff_skill"),
        "memory_current_step_path": data.get("memory_current_step_path"),
        "open_findings_count": entry.get("open_findings_count", 0),
    }


def write_skill_resume_snapshot(state: Any, state_path: Path, *, search_dir: Path | None = None) -> None:
    """Write continuity snapshot (v2 index + focus) after a SkillState save. Never raises."""
    try:
        from scripts.shared.orchestrator import runtime_state_dir

        state_dir = runtime_state_dir(search_dir)
        state_dir.mkdir(parents=True, exist_ok=True)
        out = state_dir / RESUME_CONTEXT_FILENAME
        handoff_rel, handoff_skill = _latest_handoff_info(search_dir)
        entry = _session_entry_from_state(state, state_path)
        focus = entry["session_id"] or "unknown"

        existing, _ = load_resume_snapshot(search_dir)
        sessions: list[dict[str, Any]] = []
        if existing and isinstance(existing.get("sessions"), list):
            sessions = [s for s in existing["sessions"] if isinstance(s, dict)]
        # Upsert by session_id or state_path
        key = entry["session_id"] or entry["state_path"]
        replaced = False
        new_sessions: list[dict[str, Any]] = []
        for s in sessions:
            sk = s.get("session_id") or s.get("state_path")
            if sk and sk == key:
                new_sessions.append(entry)
                replaced = True
            else:
                new_sessions.append(s)
        if not replaced:
            new_sessions.append(entry)

        payload: dict[str, Any] = {
            "schema_version": RESUME_CONTEXT_SCHEMA_VERSION,
            "writer_version": RESUME_CONTEXT_WRITER_VERSION,
            "snapshot_id": uuid.uuid4().hex,
            "focus": focus,
            "updated_at": _utc_now_iso(),
            "sessions": new_sessions,
            # Top-level mirrors = focus session (backward compatible)
            "skill": entry["skill"],
            "current_step": entry["current_step"],
            "last_completed_step": entry["last_completed_step"],
            "max_step": entry["max_step"],
            "invocation_status": entry.get("invocation_status"),
            "state_path": entry["state_path"],
            "started_at": getattr(state, "started_at", None),
            "last_error_summary": None,
            "memory_current_step_path": _current_step_path(search_dir),
            "memory_latest_handoff_path": handoff_rel,
            "memory_latest_handoff_skill": handoff_skill,
            "open_findings_count": entry.get("open_findings_count", 0),
        }
        _atomic_write_json(out, payload)
    except Exception:
        return


def write_evaluate_resume_snapshot(
    *,
    plan_path: str,
    plan_name: str,
    mode: str | None,
    current_step: int,
    last_completed_step: int,
    max_step: int,
    state_path: Path,
    failure_count: int,
    search_dir: Path | None = None,
) -> None:
    """Write continuity snapshot for evaluate sessions (v2 index upsert)."""
    try:
        from types import SimpleNamespace

        shim = SimpleNamespace(
            skill_name="evaluate",
            session_id=None,
            current_step=current_step,
            last_completed_step=last_completed_step,
            max_step=max_step,
            failure_count=failure_count,
            label=plan_name,
            started_at=None,
            findings=[],
        )
        write_skill_resume_snapshot(shim, state_path, search_dir=search_dir)
        data, _ = load_resume_snapshot(search_dir)
        if not data:
            return
        resolved = str(Path(state_path).resolve())
        for s in data.get("sessions") or []:
            if str(s.get("state_path", "")) == resolved:
                s["evaluate_plan_path"] = plan_path
                s["evaluate_plan_name"] = plan_name
                s["evaluate_mode"] = mode
                break
        data["evaluate_plan_path"] = plan_path
        data["evaluate_plan_name"] = plan_name
        data["evaluate_mode"] = mode
        from scripts.shared.orchestrator import runtime_state_dir

        _atomic_write_json(runtime_state_dir(search_dir) / RESUME_CONTEXT_FILENAME, data)
    except Exception:
        return


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        import os

        os.close(fd)
        Path(tmp).write_text(content, encoding="utf-8")
        Path(tmp).replace(path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def load_resume_snapshot(search_dir: Path | None = None) -> tuple[dict[str, Any] | None, str | None]:
    """Load and validate resume-context.json. Returns (data, warn_message).

    Accepts schema v1 (migrated in-memory to v2) and v2.
    """
    path = resume_context_path(search_dir)
    if not path.is_file():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None, "resume-context.json exists but is not valid JSON; ignoring snapshot."
    ver = data.get("schema_version")
    if ver == RESUME_CONTEXT_SCHEMA_VERSION_V1:
        missing = REQUIRED_SNAPSHOT_KEYS_V1 - set(data.keys())
        if missing:
            return None, f"resume-context.json missing fields {sorted(missing)}; ignoring snapshot."
        return _migrate_v1_to_v2(data), None
    if ver != RESUME_CONTEXT_SCHEMA_VERSION:
        return None, f"resume-context.json schema_version {ver!r} is unsupported; ignoring snapshot."
    missing = REQUIRED_SNAPSHOT_KEYS - set(data.keys())
    if missing:
        return None, f"resume-context.json missing fields {sorted(missing)}; ignoring snapshot."
    if not isinstance(data.get("sessions"), list):
        return None, "resume-context.json `sessions` must be an array; ignoring snapshot."
    return data, None


def _first_non_empty_lines(text: str, max_lines: int = 12, max_chars: int = 1200) -> str:
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    out = "\n".join(lines[:max_lines])
    if len(out) > max_chars:
        return out[: max_chars - 3] + "..."
    return out


def _strip_yaml_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) >= 3:
        return parts[2].lstrip()
    return text


def summarize_memory_for_resume(search_dir: Path | None = None) -> str:
    """Short operational summary: synthesis rollup first, then current-step, then handoffs."""
    from scripts.shared.memory_synthesis import SYNTHESIS_FILENAME
    from scripts.shared.orchestrator import legacy_memory_dir, read_memory_file, runtime_memory_dir
    from scripts.shared.resume_memory_summary import (
        summary_from_newest_handoff,
        summary_from_synthesis,
    )

    for mem in (runtime_memory_dir(search_dir), legacy_memory_dir(search_dir)):
        text = summary_from_synthesis(mem)
        if text:
            return text

    cur = read_memory_file("current-step.md")
    if cur.strip():
        return _first_non_empty_lines(cur)

    for mem in (runtime_memory_dir(search_dir), legacy_memory_dir(search_dir)):
        text = summary_from_newest_handoff(mem)
        if text:
            return text
    _ = SYNTHESIS_FILENAME
    return ""


def find_graph_report_paths(repo_root: Path) -> list[Path]:
    """Candidate GRAPH_REPORT.md locations for codebase context."""
    candidates = [
        repo_root / "graphify-out" / "GRAPH_REPORT.md",
        repo_root / "GRAPH_REPORT.md",
    ]
    from scripts.shared.orchestrator import runtime_root

    rt = runtime_root(repo_root)
    candidates.append(rt / "graphify" / "GRAPH_REPORT.md")
    return [p for p in candidates if p.is_file()]


def read_graphify_codebase_excerpt(repo_root: Path, max_chars: int = 1600) -> str:
    for p in find_graph_report_paths(repo_root):
        try:
            body = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        excerpt = _first_non_empty_lines(body, max_lines=20, max_chars=max_chars)
        if excerpt:
            return f"(from `{p.relative_to(repo_root)}`)\n{excerpt}"
    return ""


def read_graphify_status(search_dir: Path | None = None) -> dict[str, Any]:
    """Parse graphify-status.json with safe defaults."""
    path = graphify_status_path(search_dir)
    default: dict[str, Any] = {
        "status": "missing",
        "last_refresh": None,
        "error": None,
        "repo_head": None,
        "graphify_available": False,
    }
    if not path.is_file():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {**default, "status": "error", "error": "graphify-status.json is not valid JSON"}
    out = {**default, **{k: data.get(k, default[k]) for k in default}}
    # Recompute stale from last_refresh if status was fresh
    if out.get("status") == "fresh" and out.get("last_refresh"):
        try:
            from datetime import timedelta

            lr = datetime.fromisoformat(str(out["last_refresh"]).replace("Z", "+00:00"))
            if lr.tzinfo is None:
                lr = lr.replace(tzinfo=timezone.utc)
            age = datetime.now(timezone.utc) - lr
            if age > timedelta(hours=GRAPHIFY_STALE_HOURS_DEFAULT):
                out["status"] = "stale"
                out["stale_since_hours"] = round(age.total_seconds() / 3600.0, 1)
        except Exception:
            out["status"] = "stale"
    return out


def _resume_step_dict(d: dict[str, Any]) -> int:
    """Mirror resume._resume_step for dict-shaped sessions (no import cycle)."""
    current = int(d.get("current_step", 1) or 1)
    last_completed = int(d.get("last_completed_step", 0) or 0)
    max_step = int(d.get("max_step", 6) or 6)
    last_completed = min(last_completed, current)
    if current <= 0:
        return 1
    if current >= max_step and last_completed >= max_step:
        return max_step
    if last_completed == current and current < max_step:
        return current + 1
    return max(current, 1)


def snapshot_memory_conflict(
    session: dict,
    snap: dict[str, Any] | None,
) -> bool:
    """True when active JSON session disagrees with snapshot on skill or resume step."""
    if not snap:
        return False
    sk = snap.get("skill")
    if sk and sk != session.get("skill"):
        return True
    mem_step = _resume_step_dict(
        {
            "skill": snap.get("skill"),
            "current_step": snap.get("current_step"),
            "last_completed_step": snap.get("last_completed_step"),
            "max_step": snap.get("max_step", 6),
            "path": snap.get("state_path"),
        }
    )
    state_step = _resume_step_dict(session)
    if int(mem_step) != int(state_step):
        return True
    p_snap = snap.get("state_path")
    p_sess = str(session.get("path", ""))
    if p_snap and p_sess and Path(p_snap).resolve() != Path(p_sess).resolve():
        return True
    return False


def continuation_confidence(session: dict | None, snap: dict[str, Any] | None, memory_summary: str) -> str:
    if session and snap and not (session and snap and snapshot_memory_conflict(session, snap)):
        return "high"
    if snap and memory_summary:
        return "medium"
    if snap or memory_summary:
        return "medium"
    return "low"


def suggested_continuation_lines(
    *,
    session: dict | None,
    snap: dict[str, Any] | None,
    memory_summary: str,
    successor_skill: str | None,
) -> list[str]:
    """Two to three concrete next-step suggestions."""
    lines: list[str] = []
    if session:
        skill = session["skill"]
        lines.append(f"Resume `{skill}` from persisted JSON state (authoritative for step math).")
    elif snap:
        lines.append(
            f"Continue `{snap.get('skill')}` at step {_resume_step_dict({**snap, 'path': snap.get('state_path')})} "
            f"using state file `{snap.get('state_path')}` (from continuity snapshot)."
        )
    if memory_summary:
        lines.append("Re-read `memory/current-step.md` (or latest handoff) for narrative context before acting.")
    if successor_skill:
        lines.append(f"If the pipeline is idle, consider starting or continuing `{successor_skill}`.")
    if not lines:
        lines.append("Start a workflow with develop, plan, diagnose, or evaluate.")
    return lines[:3]
