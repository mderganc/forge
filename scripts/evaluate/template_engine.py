"""Prompt template loading and variable substitution.

Templates are markdown files in the prompts/ directory. Variables use
{{VARIABLE_NAME}} syntax and are replaced by render_template().
"""

from __future__ import annotations

import os
import re
import sysconfig
from importlib import resources
from pathlib import Path
from typing import Iterable, Protocol, runtime_checkable

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"

# Probes used to detect a complete Forge checkout prompts/ tree (not a stub dir).
_CHECKOUT_SENTINELS = (
    "plan/context.md",
    "review/team_dispatch.md",
    "develop/startup.md",
    "diagnose/technique_catalog.md",
)

# Every orchestrator phase template (without .md). Kept in sync with workflow scripts.
WORKFLOW_PROMPT_TEMPLATES: tuple[str, ...] = (
    # evaluate — pre
    "pre/feasibility",
    "pre/completeness",
    "pre/codebase_alignment",
    "pre/risk_dependencies",
    # evaluate — post
    "post/completeness_audit",
    "post/correctness",
    "post/code_quality",
    "post/performance",
    "post/operational_readiness",
    # evaluate — review
    "review/team_dispatch",
    "review/findings_aggregation",
    "review/remediation",
    # evaluate — shared
    "shared/plan_parsing",
    "shared/discussion",
    "report",
    # plan
    "plan/context",
    "plan/architecture",
    "plan/creation",
    "plan/review_loop",
    "plan/approval",
    "plan/documentation",
    "plan/handoff",
    # develop
    "develop/startup",
    "develop/scope",
    "develop/investigation",
    "develop/investigation_review",
    "develop/solution",
    "develop/approval",
    "develop/handoff",
    "develop/spec_gate",
    # implement
    "implement/plan_detect",
    "implement/branch_setup",
    "implement/wave_dispatch",
    "implement/wave_review",
    "implement/wave_complete",
    "implement/integration_check",
    "implement/documentation",
    "implement/handoff",
    # diagnose
    "diagnose/define",
    "diagnose/evidence",
    "diagnose/decompose",
    "diagnose/analyze",
    "diagnose/solutions",
    "diagnose/quick_fix",
    "diagnose/report",
    # code-review
    "code-review/target_detection",
    "code-review/mode_selection",
    "code-review/diff_analysis",
    "code-review/security_scan",
    "code-review/architecture_check",
    "code-review/deep_dive",
    "code-review/discussion",
    "code-review/report",
    # test — run mode
    "test/context",
    "test/discovery",
    "test/execution",
    "test/failure_analysis",
    "test/coverage_gaps",
    "test/report",
    # test — flows mode
    "test/flow_context",
    "test/flow_recommendation",
    "test/flow_scope",
    "test/flow_scaffold",
    "test/flow_author",
    "test/flow_execute",
    "test/flow_report",
)


@runtime_checkable
class _ResourceLike(Protocol):
    def joinpath(self, *descendants: str): ...
    def read_text(self, encoding: str = "utf-8") -> str: ...
    def is_file(self) -> bool: ...


def packaged_prompts_root() -> _ResourceLike:
    """Packaged prompts shipped inside the forge-next wheel."""
    return resources.files("forge_next.assets").joinpath("prompts")


def _purelib_root() -> Path | None:
    try:
        return Path(sysconfig.get_path("purelib")).resolve()
    except Exception:
        return None


def _is_under_purelib(path: Path) -> bool:
    pure = _purelib_root()
    if pure is None:
        return False
    try:
        path.resolve().relative_to(pure)
        return True
    except ValueError:
        return False


def _checkout_prompts_complete(root: Path) -> bool:
    return all((root / rel).is_file() for rel in _CHECKOUT_SENTINELS)


def _scripts_prompts_eligible() -> bool:
    """Whether scripts/../prompts should be searched before packaged assets."""
    if not PROMPTS_DIR.is_dir():
        return False
    if _checkout_prompts_complete(PROMPTS_DIR):
        return True
    # Ignore empty/stub site-packages/prompts created beside installed scripts.
    if _is_under_purelib(PROMPTS_DIR):
        return False
    # Editable/incomplete checkout: still try repo prompts, then packaged fallback.
    return True


def default_prompts_root() -> Path | _ResourceLike:
    """Resolve the preferred prompts root (first candidate for load_template).

    Resolution order:
    1) FORGE_CODEX_PROMPTS_DIR env var (developer override)
    2) Repo-local `prompts/` relative to this file (editable checkout)
    3) Packaged assets at `forge_next.assets/prompts` (pipx install)

    load_template() searches every eligible root; packaged assets are always
    included so pip installs work when checkout prompts/ is missing files.
    """
    override = os.environ.get("FORGE_CODEX_PROMPTS_DIR")
    if override:
        return Path(override).expanduser().resolve()

    if _scripts_prompts_eligible():
        return PROMPTS_DIR

    return packaged_prompts_root()


def _prompt_roots(prompts_dir: Path | _ResourceLike | None) -> list[Path | _ResourceLike]:
    """Ordered roots to search when loading a template."""
    if prompts_dir is not None:
        return [prompts_dir, packaged_prompts_root()]

    roots: list[Path | _ResourceLike] = []
    override = os.environ.get("FORGE_CODEX_PROMPTS_DIR")
    if override:
        roots.append(Path(override).expanduser().resolve())
    if _scripts_prompts_eligible():
        roots.append(PROMPTS_DIR)
    roots.append(packaged_prompts_root())
    return roots


def _join(root: Path | _ResourceLike, rel: str) -> Path | _ResourceLike:
    if isinstance(root, Path):
        return root / rel
    return root.joinpath(rel)


def _exists(path: Path | _ResourceLike) -> bool:
    if isinstance(path, Path):
        return path.is_file()
    return path.is_file()


def load_template(name: str, prompts_dir: Path | _ResourceLike | None = None) -> str:
    """Load a prompt template by relative name (without .md extension).

    Args:
        name: Relative path like "shared/plan_parsing" or "pre/feasibility"
        prompts_dir: Root prompts directory. If omitted, auto-resolves via
            default_prompts_root() and always falls back to packaged assets.

    Returns:
        Template content as string.

    Raises:
        FileNotFoundError: If template file doesn't exist in any root.
    """
    rel = f"{name}.md"
    tried: list[str] = []
    for root in _prompt_roots(prompts_dir):
        path = _join(root, rel)
        tried.append(str(path))
        if not _exists(path):
            continue
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Some working copies on Windows may contain legacy cp1252 bytes.
            # Fall back so workflows still run; packaged assets are UTF-8.
            return path.read_text(encoding="cp1252")

    raise FileNotFoundError(
        f"Template not found: {rel} (searched: {', '.join(tried)})"
    )


def read_prompt_file(relative: str, *, prompts_dir: Path | _ResourceLike | None = None) -> str:
    """Load a prompt file by repo-relative path (with or without .md suffix)."""
    rel = relative.replace("\\", "/").strip("/")
    if rel.endswith(".md"):
        rel = rel[:-3]
    return load_template(rel, prompts_dir=prompts_dir)


def validate_workflow_prompts(
    names: Iterable[str] | None = None,
    *,
    prompts_dir: Path | _ResourceLike | None = None,
) -> list[str]:
    """Return template names that cannot be loaded from any prompt root."""
    missing: list[str] = []
    for name in names or WORKFLOW_PROMPT_TEMPLATES:
        try:
            load_template(name, prompts_dir=prompts_dir)
        except FileNotFoundError:
            missing.append(name)
    return missing


def render_template(template: str, variables: dict[str, str]) -> str:
    """Replace {{VARIABLE_NAME}} placeholders with values.

    Variables not present in the dict are left as-is (not an error).
    """
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        return variables.get(key, match.group(0))

    return re.sub(r"\{\{(\w+)\}\}", replacer, template)
