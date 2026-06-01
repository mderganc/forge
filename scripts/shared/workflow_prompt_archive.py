"""Persist rendered workflow step prompts beside skill state for reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SIDECAR_NAME = ".workflow-step-prompts.json"


def sidecar_path(state_dir: Path | None) -> Path | None:
    if state_dir is None:
        return None
    return Path(state_dir) / SIDECAR_NAME


def load_archive(state_dir: Path | None) -> dict[str, Any]:
    path = sidecar_path(state_dir)
    if path is None or not path.is_file():
        return {"skill": "", "steps": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"skill": "", "steps": []}
    if not isinstance(data, dict):
        return {"skill": "", "steps": []}
    data.setdefault("steps", [])
    return data


def save_archive(state_dir: Path, data: dict[str, Any]) -> Path:
    path = sidecar_path(state_dir)
    assert path is not None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")
    return path


def record_step_prompt(
    state_dir: Path | None,
    *,
    skill: str,
    step: int,
    phase_name: str,
    body: str,
    template_name: str = "",
) -> Path | None:
    """Append or replace the prompt body for a workflow step."""
    if state_dir is None:
        return None
    archive = load_archive(state_dir)
    archive["skill"] = skill
    archive["updated_at"] = datetime.now(timezone.utc).isoformat()
    steps: list[dict[str, Any]] = [
        s for s in archive.get("steps", [])
        if not (isinstance(s, dict) and s.get("step") == step)
    ]
    steps.append({
        "step": int(step),
        "phase_name": phase_name,
        "template_name": template_name,
        "body": body.strip(),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })
    steps.sort(key=lambda s: int(s.get("step", 0)))
    archive["steps"] = steps
    return save_archive(state_dir, archive)


def format_workflow_prompts_markdown(
    state_dir: Path | None,
    *,
    style: str = "brief",
) -> str:
    """Markdown appendix of recorded step prompts for test/code-review reports."""
    archive = load_archive(state_dir)
    steps = archive.get("steps") or []
    if not steps:
        return "_Workflow prompts: not recorded (no `.workflow-step-prompts.json` sidecar)._\n"

    skill = archive.get("skill") or "workflow"
    lines = [
        "## Workflow prompts (orchestrator-rendered)",
        "",
        f"**Skill:** `{skill}`",
        f"**Sidecar:** `{sidecar_path(state_dir)}`",
        "",
    ]

    if style == "brief":
        lines.append("| Step | Phase | Template |")
        lines.append("|------|-------|----------|")
        for s in steps:
            if not isinstance(s, dict):
                continue
            tpl = s.get("template_name") or "—"
            lines.append(
                f"| {s.get('step', '?')} | {s.get('phase_name', '?')} | `{tpl}` |"
            )
        lines.append("")
        lines.append("_Full prompt bodies are in the sidecar JSON `steps[].body`._")
        return "\n".join(lines) + "\n"

    for s in steps:
        if not isinstance(s, dict):
            continue
        step_n = s.get("step", "?")
        phase = s.get("phase_name", "Phase")
        tpl = s.get("template_name") or ""
        header = f"### Step {step_n} — {phase}"
        if tpl:
            header += f" (`{tpl}`)"
        lines.extend(["", header, "", s.get("body") or "_(empty)_", ""])
    return "\n".join(lines).strip() + "\n"
