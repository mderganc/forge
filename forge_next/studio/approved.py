"""Lock approved Studio HTML screens as immutable workflow references."""

from __future__ import annotations

import json
import re
import stat
import time
from pathlib import Path
from typing import Any

from forge_next.studio import server as studio_server

MANIFEST_VERSION = 1
MANIFEST_NAME = "manifest.json"
INDEX_FILENAME = "studio-approved-index.md"
GATE_ATTR_RE = re.compile(r"""data-studio-gate=["']([^"']+)["']""", re.IGNORECASE)


def approved_dir(repo_root: Path) -> Path:
    from scripts.shared.orchestrator import runtime_root

    root = runtime_root(repo_root) / "studio" / "approved"
    root.mkdir(parents=True, exist_ok=True)
    return root


def manifest_path(repo_root: Path) -> Path:
    return approved_dir(repo_root) / MANIFEST_NAME


def index_path(repo_root: Path) -> Path:
    from scripts.shared.orchestrator import runtime_memory_dir

    return runtime_memory_dir(repo_root) / INDEX_FILENAME


def infer_gate_from_html(html: str) -> str | None:
    match = GATE_ATTR_RE.search(html)
    return match.group(1) if match else None


def load_manifest(repo_root: Path) -> dict[str, Any]:
    path = manifest_path(repo_root)
    if not path.is_file():
        return {"v": MANIFEST_VERSION, "screens": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"v": MANIFEST_VERSION, "screens": []}
    if not isinstance(data, dict):
        return {"v": MANIFEST_VERSION, "screens": []}
    screens = data.get("screens")
    if not isinstance(screens, list):
        data["screens"] = []
    return data


def save_manifest(repo_root: Path, data: dict[str, Any]) -> None:
    path = manifest_path(repo_root)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def is_gate_locked(repo_root: Path, gate: str) -> bool:
    manifest = load_manifest(repo_root)
    for row in manifest.get("screens", []):
        if isinstance(row, dict) and row.get("gate") == gate:
            return True
    return False


def locked_gates(repo_root: Path) -> list[str]:
    manifest = load_manifest(repo_root)
    out: list[str] = []
    for row in manifest.get("screens", []):
        if isinstance(row, dict) and row.get("gate"):
            out.append(str(row["gate"]))
    return out


def locked_html_path(repo_root: Path, gate: str) -> Path:
    safe = re.sub(r"[^\w.-]+", "_", gate).strip("_") or "screen"
    return approved_dir(repo_root) / f"{safe}.html"


def _mark_readonly(path: Path) -> None:
    """Best-effort read-only bit so agents treat approved HTML as immutable."""
    try:
        mode = path.stat().st_mode
        path.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    except OSError:
        pass


def _clear_readonly(path: Path) -> None:
    """Restore write permission before replace or unlock (Windows needs this)."""
    try:
        mode = path.stat().st_mode
        path.chmod(mode | stat.S_IWUSR)
    except OSError:
        pass


def _write_index(repo_root: Path, manifest: dict[str, Any]) -> Path:
    idx = index_path(repo_root)
    idx.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Approved Studio screens (locked reference)",
        "",
        "> **Do not edit** files under `.codex/forge/studio/approved/`. "
        "These are the UI snapshots the user approved. "
        "Use them when planning, implementing, and reviewing — not the live session `content/` copies.",
        "",
    ]
    screens = manifest.get("screens") or []
    if not screens:
        lines.append("(No approved screens yet.)")
        lines.append("")
    else:
        for row in screens:
            if not isinstance(row, dict):
                continue
            gate = row.get("gate", "?")
            rel = row.get("html_path", "")
            at = row.get("approved_at", "")
            src = row.get("source_file", "")
            lines.append(f"## `{gate}`")
            lines.append("")
            lines.append(f"- **Approved:** {at}")
            lines.append(f"- **Locked HTML:** `{rel}`")
            if src:
                lines.append(f"- **Source screen:** `{src}`")
            if row.get("session_id"):
                lines.append(f"- **Session:** `{row['session_id']}`")
            lines.append("")
            lines.append("Open the HTML file for layout, options, and copy the user signed off on.")
            lines.append("")
    idx.write_text("\n".join(lines), encoding="utf-8")
    return idx


def lock_current_screen(
    repo_root: Path,
    session_dir: Path,
    *,
    gate: str | None = None,
    screen_path: Path | None = None,
    replace: bool = False,
) -> dict[str, Any]:
    """Copy a session screen into approved storage and update manifest + index."""
    content_dir = session_dir / "content"
    source = screen_path or studio_server.get_newest_screen(content_dir)
    if source is None or not source.is_file():
        raise FileNotFoundError("No HTML screen in session content/ to approve.")

    raw = source.read_text(encoding="utf-8")
    resolved_gate = (gate or infer_gate_from_html(raw) or source.stem).strip()
    if not resolved_gate:
        raise ValueError("Could not determine gate id; pass --gate.")

    if is_gate_locked(repo_root, resolved_gate) and not replace:
        raise FileExistsError(
            f"Gate `{resolved_gate}` is already approved. "
            "Use `forge studio approve --replace` to supersede."
        )

    dest = locked_html_path(repo_root, resolved_gate)
    if dest.is_file():
        _clear_readonly(dest)
    dest.write_text(raw, encoding="utf-8")
    _mark_readonly(dest)

    try:
        rel_html = dest.relative_to(repo_root.resolve())
        rel_str = str(rel_html).replace("\\", "/")
    except ValueError:
        rel_str = str(dest)

    meta = {
        "gate": resolved_gate,
        "html_path": rel_str,
        "approved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_id": session_dir.name,
        "source_file": source.name,
    }

    manifest = load_manifest(repo_root)
    screens = [r for r in manifest.get("screens", []) if r.get("gate") != resolved_gate]
    screens.append(meta)
    manifest["screens"] = screens
    save_manifest(repo_root, manifest)
    _write_index(repo_root, manifest)

    return meta


def unlock_gate(repo_root: Path, gate: str) -> dict[str, Any]:
    """Remove a locked gate so drafts and push are allowed again."""
    resolved = gate.strip()
    if not resolved:
        raise ValueError("Gate id is required.")
    if not is_gate_locked(repo_root, resolved):
        raise FileNotFoundError(f"Gate `{resolved}` is not locked.")

    manifest = load_manifest(repo_root)
    former_path = ""
    for row in manifest.get("screens", []):
        if isinstance(row, dict) and row.get("gate") == resolved:
            former_path = str(row.get("html_path", ""))
            break

    dest = locked_html_path(repo_root, resolved)
    if dest.is_file():
        _clear_readonly(dest)
        dest.unlink()

    manifest["screens"] = [
        r for r in manifest.get("screens", []) if not (isinstance(r, dict) and r.get("gate") == resolved)
    ]
    save_manifest(repo_root, manifest)
    _write_index(repo_root, manifest)

    return {
        "gate": resolved,
        "unlocked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "former_html_path": former_path,
    }


def read_approved_index(repo_root: Path | None = None) -> str:
    from scripts.shared.orchestrator import read_memory_file

    if repo_root is not None:
        path = index_path(repo_root)
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return ""
    return read_memory_file(INDEX_FILENAME)


def approved_context_block(repo_root: Path | None = None) -> str:
    text = read_approved_index(repo_root).strip()
    if not text:
        return "(No approved Studio screens yet — user must click **Approve screen** on the gate.)"
    return text


def check_push_allowed(repo_root: Path, html_path: Path) -> str | None:
    """Return error message if push would overwrite a locked gate screen."""
    try:
        raw = html_path.read_text(encoding="utf-8")
    except OSError:
        return None
    gate = infer_gate_from_html(raw)
    if gate and is_gate_locked(repo_root, gate):
        return (
            f"Gate `{gate}` is already approved and locked. "
            "Push a new gate id or use a draft filename until the user re-approves."
        )
    return None
