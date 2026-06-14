"""Hypothesis register sidecar for the diagnose skill.

Non-fatal validation (returns issues, never sys.exit). Mirrors path helpers
from scripts/test/_sidecar.py.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.diagnose.five_whys_validate import is_symptom_level, restates_symptom
from scripts.diagnose.text_similarity import jaccard, normalize_statement, word_set

REGISTER_FILENAME = ".diagnose-hypotheses.json"

FISHBONE_CATEGORIES = frozenset({
    "CODE",
    "CONFIG",
    "DATA",
    "INFRASTRUCTURE",
    "DEPENDENCIES",
    "ENVIRONMENT",
})

VALID_STATUSES = frozenset({
    "open",
    "ruled_out",
    "plausible",
    "confirmed",
    "deferred",
})

# Word-overlap threshold for near-duplicate statements (Jaccard on word sets).
_DUPLICATE_JACCARD_THRESHOLD = 0.85

_MIN_FISHBONE_CATEGORIES = 4


def register_path(state_dir: Path) -> Path:
    """Return path to the hypothesis register beside diagnose state.json."""
    return state_dir / REGISTER_FILENAME


def load_register(path: Path) -> dict | None:
    """Load register JSON. Returns None if missing or unparseable."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _find_near_duplicates(statements: list[str]) -> list[str]:
    """Return human-readable pairs that exceed duplicate threshold."""
    issues: list[str] = []
    normalized = [normalize_statement(s) for s in statements]
    for i in range(len(statements)):
        for j in range(i + 1, len(statements)):
            if normalized[i] == normalized[j]:
                issues.append(
                    f"Hypotheses {i + 1} and {j + 1} have identical statements after normalization."
                )
                continue
            ja = jaccard(word_set(statements[i]), word_set(statements[j]))
            if ja >= _DUPLICATE_JACCARD_THRESHOLD:
                issues.append(
                    f"Hypotheses {i + 1} and {j + 1} are near-duplicates "
                    f"(word overlap {ja:.0%} >= {_DUPLICATE_JACCARD_THRESHOLD:.0%})."
                )
    return issues


def validate_register(
    data: dict | None,
    *,
    min_required: int = 10,
    path: Path | None = None,
) -> tuple[bool, list[str]]:
    """Validate register structure and breadth. Non-fatal."""
    issues: list[str] = []
    label = str(path) if path else REGISTER_FILENAME

    if data is None:
        issues.append(
            f"No hypothesis register found at {label}. "
            "Run **Phase 3** to create `.diagnose-hypotheses.json` (or resume from step 3)."
        )
        return False, issues

    hypotheses = data.get("hypotheses")
    if not isinstance(hypotheses, list):
        issues.append(f"Register at {label} must contain a 'hypotheses' array.")
        return False, issues

    if len(hypotheses) < min_required:
        issues.append(
            f"Register has {len(hypotheses)} hypotheses; minimum is {min_required}. "
            "Add distinct, falsifiable root-cause candidates across fishbone categories."
        )

    seen_ids: set[str] = set()
    categories: set[str] = set()
    statements: list[str] = []

    for idx, h in enumerate(hypotheses):
        if not isinstance(h, dict):
            issues.append(f"Hypothesis entry {idx + 1} is not an object.")
            continue
        hid = h.get("id")
        if not hid or not str(hid).strip():
            issues.append(f"Hypothesis entry {idx + 1} missing non-empty 'id'.")
        elif str(hid) in seen_ids:
            issues.append(f"Duplicate hypothesis id: {hid!r}.")
        else:
            seen_ids.add(str(hid))

        statement = h.get("statement")
        if not statement or not str(statement).strip():
            issues.append(f"Hypothesis {hid or idx + 1} missing non-empty 'statement'.")
        else:
            statements.append(str(statement))

        cat = h.get("category")
        if cat:
            cat_upper = str(cat).strip().upper()
            if cat_upper not in FISHBONE_CATEGORIES:
                issues.append(
                    f"Hypothesis {hid or idx + 1} has invalid category {cat!r} "
                    f"(expected one of {sorted(FISHBONE_CATEGORIES)})."
                )
            else:
                categories.add(cat_upper)

        status = h.get("status", "open")
        if str(status) not in VALID_STATUSES:
            issues.append(
                f"Hypothesis {hid or idx + 1} has invalid status {status!r}."
            )

    if len(categories) < _MIN_FISHBONE_CATEGORIES:
        issues.append(
            f"Register spans {len(categories)} fishbone categories; "
            f"need at least {_MIN_FISHBONE_CATEGORIES} distinct among "
            f"{sorted(FISHBONE_CATEGORIES)}."
        )

    issues.extend(_find_near_duplicates(statements))

    return len(issues) == 0, issues


def validate_elimination(
    data: dict | None,
    *,
    path: Path | None = None,
) -> tuple[bool, list[str]]:
    """Validate that elimination produced at least one confirmed root cause."""
    issues: list[str] = []
    label = str(path) if path else REGISTER_FILENAME

    if data is None:
        issues.append(
            f"No hypothesis register at {label} — complete Phase 4 elimination first."
        )
        return False, issues

    hypotheses = data.get("hypotheses")
    if not isinstance(hypotheses, list):
        issues.append(f"Register at {label} missing 'hypotheses' array.")
        return False, issues

    statuses = [
        str(h.get("status", "open"))
        for h in hypotheses
        if isinstance(h, dict)
    ]
    confirmed = sum(1 for s in statuses if s == "confirmed")
    plausible = sum(1 for s in statuses if s == "plausible")
    open_count = sum(1 for s in statuses if s == "open")

    if confirmed < 1:
        issues.append(
            "No hypothesis has status 'confirmed'. "
            "Finish falsification tests in Phase 4 before solution generation."
        )

    symptom = ""
    if isinstance(data.get("symptom"), str):
        symptom = data["symptom"].strip()

    for h in hypotheses:
        if not isinstance(h, dict):
            continue
        if str(h.get("status")) == "confirmed":
            statement = str(h.get("statement", "")).strip()
            hid = h.get("id", "?")
            if statement and is_symptom_level(statement):
                issues.append(
                    f"Hypothesis {hid} is confirmed but its statement is symptom-level "
                    f"({statement!r}) — confirm a changeable mechanism, not the failure mode."
                )
            elif statement and symptom and restates_symptom(statement, symptom):
                issues.append(
                    f"Hypothesis {hid} is confirmed but restates the symptom "
                    f"({statement!r}) — state the underlying cause."
                )

        if str(h.get("status")) == "ruled_out":
            reason = h.get("ruled_out_reason")
            if not reason or not str(reason).strip():
                issues.append(
                    f"Hypothesis {h.get('id', '?')} is ruled_out but missing 'ruled_out_reason'."
                )

    if plausible > 2 and open_count > 0:
        issues.append(
            f"Register has {plausible} plausible and {open_count} still open — "
            "resolve or rule out remaining hypotheses before Phase 5."
        )

    return len(issues) == 0, issues


def summarize_register(data: dict | None) -> str:
    """Human-readable status counts for template injection."""
    if not data or not isinstance(data.get("hypotheses"), list):
        return "(No hypothesis register loaded)"

    counts: dict[str, int] = {}
    for h in data["hypotheses"]:
        if isinstance(h, dict):
            st = str(h.get("status", "open"))
            counts[st] = counts.get(st, 0) + 1

    parts = [f"{k}: {v}" for k, v in sorted(counts.items())]
    total = len(data["hypotheses"])
    return f"**{total}** hypotheses — " + ", ".join(parts) if parts else f"**{total}** hypotheses"


def format_gate_block(
    issues: list[str],
    *,
    phase: str,
    retry_step: int | None = None,
    attempt: int = 0,
    max_attempts: int = 1,
    require_confirmation: bool = True,
    state_path: str | None = None,
) -> str:
    """Markdown gate block with optional continuation override."""
    bar = "━" * 60
    lines = [
        "",
        bar,
        "HYPOTHESIS REGISTER GATE",
        bar,
        "",
        f"**Phase:** {phase}",
        "",
        "The hypothesis register did not pass validation:",
        "",
    ]
    for issue in issues:
        lines.append(f"- {issue}")
    lines.append("")

    if retry_step is not None and attempt < max_attempts:
        lines.append(
            f"**Automatic retry ({attempt + 1} of {max_attempts}):** "
            f"Return to **step {retry_step}** and fix the register, then re-run this step."
        )
        lines.append("")
    elif attempt >= max_attempts:
        lines.append(
            "Retry budget exhausted. Fix the register, or ask the user to approve an override "
            "with a documented reason (`hypothesis_override_reason` in session state)."
        )
        lines.append("")

    lines.append(
        "**Pause here.** Present the issues above to the user and **wait for approval** "
        "before proceeding — same discipline as the autonomy gate in guided/interactive modes."
    )
    if require_confirmation:
        lines.append("")
        lines.append(
            "Reply **yes** when the register is ready, or **override:** `<reason>` to proceed "
            "under the minimum (record the reason in session state)."
        )

    if require_confirmation and state_path:
        lines.extend(["", f"Resume context: `{state_path}`"])

    return "\n".join(lines)

