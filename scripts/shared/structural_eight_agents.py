"""Civil Learning eight parallel structural subagents — dispatch text for Pass B."""

from __future__ import annotations

import os
from pathlib import Path

from scripts.shared.orchestrator import _detect_repo_root

# Verbatim from Civil Learning, "The Prompt That Actually Fixes Your AI-Generated Code" (Apr 2026).
CIVIL_LEARNING_MASTER_PROMPT = (
    "I want to clean up my codebase and improve code quality. This is a complex task, "
    "so we'll need 8 subagents. Make a sub agent for each of the following:"
    "1. Deduplicate and consolidate all code, and implement DRY where it reduces complexity"
    "2. Find all type definitions and consolidate any that should be shared"
    "3. Use tools like knip to find all unused code and remove, ensuring that it's actually "
    "not referenced anywhere"
    "4. Untangle any circular dependencies, using tools like madge"
    "5. Remove any weak types, for example 'unknown' and 'any' (and the equivalent in other "
    "languages), research what the types should be, research in the codebase and related "
    "packages to make sure that the replacements are strong types and there are no type issues"
    "6. Remove all try catch and equivalent defensive programming if it doesn't serve a "
    "specific role of handling unknown or unsanitized input or otherwise has a reason to be "
    "there, with clear error handling and no error hiding or fallback patterns"
    "7. Find any deprecated, legacy or fallback code, remove, and make sure all code paths "
    "are clean, concise and as singular as possible"
    "8. Find any AI slop, stubs, larp, unnecessary comments and remove. Any comments that "
    "describe in-motion work, replacements of previous work with new work, or otherwise are "
    "not helpful should be either removed or replaced with helpful comments for a new user "
    "trying to understand the codebase-- but if you do edit, be concise"
    "I want each to do detailed research on their task, write a critical assessment of the "
    "current code and recommendations, and then implement all high confidence recommendations."
)

EIGHT_AGENTS: list[dict[str, str]] = [
    {
        "id": "S1",
        "name": "DRY / deduplication",
        "mission": (
            "Deduplicate and consolidate all code, and implement DRY where it reduces complexity"
        ),
        "tools": "pyscn clones; graphify query for duplicates",
    },
    {
        "id": "S2",
        "name": "Shared types",
        "mission": (
            "Find all type definitions and consolidate any that should be shared"
        ),
        "tools": "mypy, tsc, graphify cross-file types",
    },
    {
        "id": "S3",
        "name": "Dead code",
        "mission": (
            "Use tools like knip to find all unused code and remove, ensuring that it's "
            "actually not referenced anywhere"
        ),
        "tools": "knip; pyscn deadcode; skylos dead code",
    },
    {
        "id": "S4",
        "name": "Circular dependencies",
        "mission": "Untangle any circular dependencies, using tools like madge",
        "tools": "madge --circular",
    },
    {
        "id": "S5",
        "name": "Weak types",
        "mission": (
            "Remove any weak types, for example 'unknown' and 'any' (and the equivalent in "
            "other languages), research what the types should be, research in the codebase "
            "and related packages to make sure that the replacements are strong types and "
            "there are no type issues"
        ),
        "tools": "mypy, tsc --noEmit",
    },
    {
        "id": "S6",
        "name": "Error handling",
        "mission": (
            "Remove all try catch and equivalent defensive programming if it doesn't serve a "
            "specific role of handling unknown or unsanitized input or otherwise has a reason "
            "to be there, with clear error handling and no error hiding or fallback patterns"
        ),
        "tools": "manual trace; bandit where relevant",
    },
    {
        "id": "S7",
        "name": "Legacy / fallback paths",
        "mission": (
            "Find any deprecated, legacy or fallback code, remove, and make sure all code "
            "paths are clean, concise and as singular as possible"
        ),
        "tools": "pyscn CFG dead code; Investigator-style traces",
    },
    {
        "id": "S8",
        "name": "AI slop",
        "mission": (
            "Find any AI slop, stubs, larp, unnecessary comments and remove. Any comments "
            "that describe in-motion work, replacements of previous work with new work, or "
            "otherwise are not helpful should be either removed or replaced with helpful "
            "comments for a new user trying to understand the codebase-- but if you do edit, "
            "be concise"
        ),
        "tools": "manual; pyscn noise",
    },
]

SIDECAR_NAME = ".structural-eight-agents.json"
QUICK_MODE_AGENT_IDS = ("S3", "S4", "S8")


def skip_structural_eight_agents() -> bool:
    v = os.environ.get("FORGE_SKIP_STRUCTURAL_EIGHT_AGENTS", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def structural_eight_agents_full_dispatch() -> bool:
    """When set, dispatch all eight Civil Learning subagents (not the default quick trio)."""
    v = os.environ.get("FORGE_STRUCTURAL_EIGHT_AGENTS_FULL", "").strip().lower()
    return v in ("1", "true", "yes", "on")


def should_dispatch_eight_agents(skill_name: str, step: int, mode: str | None = None) -> bool:
    """Whether to append the eight-subagent dispatch banner for this orchestrator step."""
    if skip_structural_eight_agents():
        return False
    slug = skill_name.strip().lower()
    if slug == "code-review" and step == 3:
        return True
    if slug == "evaluate" and step == 1 and mode == "review":
        return True
    # evaluate post step 4: structural probes only (eight agents duplicate code-review and stall agents)
    return False


def default_eight_agents_quick_mode(
    *,
    user_quick: bool = False,
    force_full: bool = False,
) -> bool:
    """Default to S3/S4/S8 unless full eight is requested.

    ``force_full`` (e.g. thorough code-review) or ``FORGE_STRUCTURAL_EIGHT_AGENTS_FULL=1``
    → full eight (return False). Otherwise return True for the quick trio.
    ``user_quick`` keeps the trio even when an env full-dispatch flag is absent.
    """
    if force_full or structural_eight_agents_full_dispatch():
        return False
    if user_quick:
        return True
    return True


def _template_path() -> Path | None:
    repo = _detect_repo_root()
    candidates = [
        repo / "templates" / "structural-quality-eight-agents.md",
        repo / "forge_next" / "assets" / "templates" / "structural-quality-eight-agents.md",
    ]
    for p in candidates:
        if p.is_file():
            return p
    return None


def load_eight_agents_template() -> str:
    path = _template_path()
    if path is not None:
        return path.read_text(encoding="utf-8")
    return _fallback_template_body()


def _fallback_template_body() -> str:
    return (
        "# Structural quality — eight parallel subagents\n\n"
        "See `scripts/shared/structural_eight_agents.py` for dispatch constants.\n"
    )


def agents_for_mode(*, quick_mode: bool) -> list[dict[str, str]]:
    if quick_mode:
        return [a for a in EIGHT_AGENTS if a["id"] in QUICK_MODE_AGENT_IDS]
    return list(EIGHT_AGENTS)


def format_eight_agents_dispatch_banner(*, quick_mode: bool = False) -> str:
    """Banner appended after structural probe planning/results on dispatch steps."""
    bar = ("=" * 60) if os.environ.get("FORGE_ASCII") == "1" else ("━" * 60)
    agents = agents_for_mode(quick_mode=quick_mode)
    lines = [
        bar,
        "STRUCTURAL QUALITY — eight parallel subagents (Civil Learning)",
        bar,
        "",
        "Use the **master prompt** below as the charter. Spawn **one subagent per row** "
        "in parallel (Codex: `spawn_agent`; Cursor: `Task`; Claude Code: subagents). "
        "Each subagent gets its numbered mission plus the shared closing instruction.",
        "",
        "> **Master prompt (source wording):**",
        ">",
        "> " + CIVIL_LEARNING_MASTER_PROMPT,
        "",
    ]
    lines.extend(
        [
            "",
            "### Forge guardrails (review / evaluate)",
            "",
            "- **Research → critical assessment → recommendations** for every agent (required).",
            "- **Implement** high-confidence fixes only when this workflow is allowed to edit "
            "(e.g. `forge:implement`, or the user asked for fix-in-place). On "
            "**code-review** and **evaluate**, default to **findings only** — no commits.",
            "- Read `.structural-probes.json` when present; cite probe IDs (`K*`, `M*`, `P*`, `Y*`).",
            f"- Write one JSON object per agent to **`{SIDECAR_NAME}`** beside session state "
            "(merge into a single file with an `agents` array).",
            "- **Close each subagent** as soon as it finishes (`close_agent` / Task completes). "
            "Do not leave all eight open across the next orchestrator step.",
            "- **Do not block the orchestrator step** on finishing every agent or probe — write the "
            "phase findings sidecar and run the next `forge … --step` when Pass B is time-boxed.",
            "",
            "### Parallel dispatch table",
            "",
            "| ID | Subagent | Mission (numbered item) | Tool hints |",
            "|----|----------|-------------------------|------------|",
        ]
    )
    for a in agents:
        lines.append(
            f"| **{a['id']}** | {a['name']} | {a['mission']} | {a['tools']} |"
        )
    lines.extend(
        [
            "",
            "### Per-subagent spawn prompt (copy for each `S#`)",
            "",
            "Replace `{ID}`, `{NAME}`, `{MISSION}` from the table. Append to every spawn:",
            "",
            "```text",
            "You are structural subagent {ID} — {NAME}.",
            "",
            "Mission (from Civil Learning): {MISSION}",
            "",
            "Do detailed research on your task, write a critical assessment of the current "
            "code and recommendations, and then implement all high confidence recommendations "
            "(findings-only if this session is review/evaluate without implement permission).",
            "",
            "Scope: {{TARGET}} and changed paths only unless architecture mode says full module.",
            "Read .structural-probes.json and templates/structural-quality-probes.md first.",
            "Output: append your entry to .structural-eight-agents.json under agents[].",
            "```",
            "",
            "Full playbook: `templates/structural-quality-eight-agents.md`.",
            "",
        ]
    )
    if quick_mode:
        lines.append(
            "_Default trio: dispatching S3, S4, S8 only (dead code, cycles, AI slop). "
            "Full eight: FORGE_STRUCTURAL_EIGHT_AGENTS_FULL=1._"
        )
        lines.append("")
    return "\n".join(lines)
