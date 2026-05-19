"""Studio variables injected into Forge orchestrator prompts."""

from __future__ import annotations

from pathlib import Path

from forge_next.studio import approved as studio_approved
from forge_next.studio import log as studio_log


def orchestrator_studio_variables(repo_root: Path | None = None) -> dict[str, str]:
    return {
        "STUDIO_LOG": studio_log.studio_log_context_block(repo_root),
        "STUDIO_APPROVED": studio_approved.approved_context_block(repo_root),
    }
