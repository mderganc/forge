"""Deviations tracking for forge takeover."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def empty_deviations() -> dict[str, list[Any]]:
    return {
        "inferences": [],
        "retries": [],
        "blockers": [],
        "assumptions": [],
    }


def record_inference(dev: dict[str, Any], field: str, chosen: str, reason: str) -> None:
    dev.setdefault("inferences", []).append(
        {"field": field, "chosen": chosen, "reason": reason}
    )


def record_retry(dev: dict[str, Any], skill: str, step: int, count: int) -> None:
    dev.setdefault("retries", []).append({"skill": skill, "step": step, "count": count})


def record_blocker(dev: dict[str, Any], message: str) -> None:
    dev.setdefault("blockers", []).append({"message": message})


def record_assumption(dev: dict[str, Any], text: str) -> None:
    dev.setdefault("assumptions", []).append(text)


def write_deviations(path: Path, dev: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dev, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_summary(path: Path, dev: dict[str, Any], *, outcome: str, goal: str) -> None:
    lines = [
        "# Takeover run summary",
        "",
        f"- **Outcome:** {outcome}",
        f"- **Goal:** {goal}",
        "",
        "## Inferences",
    ]
    for inf in dev.get("inferences", []):
        lines.append(f"- **{inf.get('field')}:** {inf.get('chosen')} — {inf.get('reason')}")
    lines.extend(["", "## Blockers"])
    for b in dev.get("blockers", []):
        lines.append(f"- {b.get('message')}")
    lines.extend(["", "## Assumptions"])
    for a in dev.get("assumptions", []):
        lines.append(f"- {a}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
