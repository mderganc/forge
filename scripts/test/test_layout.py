"""Test layout detection: framework, entry-point, DB, roles, orchestrator pattern.

Pure-Python helper for detecting project test infrastructure, used by flow_context.md.
No external deps beyond stdlib.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Framework = Literal["pytest", "unknown"]
EntryPoint = Literal["ui", "http", "cli", "module", "none"]
TestDB = Literal["testcontainers", "pytest-postgresql", "sqlite", "none"]
RolesSource = Literal["django-groups", "casbin", "cerbos", "yaml", "none"]


@dataclass(frozen=True)
class TestLayout:
    """Detected test infrastructure for a project."""

    framework: Framework
    framework_confidence: float  # 0.0..1.0
    scenarios_dir: Path | None
    features_dir: Path | None
    cassettes_dir: Path | None
    scenario_index_md: Path | None
    entry_point: EntryPoint
    entry_point_confidence: float
    test_db: TestDB
    roles: list[str]  # discovered role names
    roles_source: RolesSource
    has_orchestrator_pattern: bool  # for workflow-dryrun fitness gating


def detect_test_layout(repo_root: Path) -> TestLayout:
    """Detect test infrastructure in a repository.

    Args:
        repo_root: Path to project root

    Returns:
        TestLayout with detected signals and confidence scores.
        No I/O on error; returns best-effort values.
    """
    repo_root = Path(repo_root).resolve()

    # Framework detection (pytest-only v1)
    framework, framework_confidence = _detect_framework(repo_root)

    # Scenario/feature/cassette directories
    scenarios_dir = _find_dir(repo_root, ["tests/scenarios", "tests/integration", "e2e"])
    features_dir = _find_dir(repo_root, ["tests/features", "features"])
    cassettes_dir = _find_dir(repo_root, ["tests/cassettes", "tests/fixtures/vcr"])
    scenario_index_md = (
        (scenarios_dir / "README.md")
        if scenarios_dir and (scenarios_dir / "README.md").exists()
        else None
    )

    # Entry-point detection
    entry_point, entry_point_confidence = _detect_entry_point(repo_root)

    # Test-DB detection
    test_db = _detect_test_db(repo_root)

    # Roles detection
    roles, roles_source = _detect_roles(repo_root)

    # Orchestrator pattern detection
    has_orchestrator_pattern = _detect_orchestrator_pattern(repo_root)

    return TestLayout(
        framework=framework,
        framework_confidence=framework_confidence,
        scenarios_dir=scenarios_dir,
        features_dir=features_dir,
        cassettes_dir=cassettes_dir,
        scenario_index_md=scenario_index_md,
        entry_point=entry_point,
        entry_point_confidence=entry_point_confidence,
        test_db=test_db,
        roles=roles,
        roles_source=roles_source,
        has_orchestrator_pattern=has_orchestrator_pattern,
    )


# ---------------------------------------------------------------------------
# Framework detection (pytest-only v1, F7)
# ---------------------------------------------------------------------------


def _detect_framework(repo_root: Path) -> tuple[Framework, float]:
    """Detect test framework with confidence score.

    Priority ladder:
    - [tool.pytest.ini_options] in pyproject.toml → 1.0
    - pytest.ini, conftest.py at root, or pytest in requirements → 0.9
    - Any tests/ dir with test_*.py → 0.7
    - Otherwise → "unknown", 0.3
    """
    repo_root = Path(repo_root).resolve()

    # Check for [tool.pytest.ini_options] in pyproject.toml
    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(errors="ignore")
        if "[tool.pytest.ini_options]" in content or "[tool.pytest" in content:
            return "pytest", 1.0

    # Check for pytest.ini
    if (repo_root / "pytest.ini").exists():
        return "pytest", 0.9

    # Check for conftest.py at root
    if (repo_root / "conftest.py").exists():
        return "pytest", 0.9

    # Check requirements for pytest
    for req_file in ["requirements.txt", "requirements-dev.txt", "requirements-test.txt"]:
        req_path = repo_root / req_file
        if req_path.exists():
            content = req_path.read_text(errors="ignore")
            if "pytest" in content:
                return "pytest", 0.9

    # Check for tests/ dir with test_*.py files
    tests_dir = repo_root / "tests"
    if tests_dir.is_dir():
        test_files = list(tests_dir.glob("test_*.py"))
        if test_files:
            return "pytest", 0.7

    return "unknown", 0.3


# ---------------------------------------------------------------------------
# Entry-point detection (F1)
# ---------------------------------------------------------------------------


def _detect_entry_point(repo_root: Path) -> tuple[EntryPoint, float]:
    """Detect highest-fidelity test entry point with confidence.

    Priority order (return first match):
    - Playwright config (playwright.config.py / playwright.config.js) → "ui", 1.0
    - Selenium imports anywhere → "ui", 0.7
    - FastAPI/Flask app declaration → "http", 1.0
    - Django ROOT_URLCONF → "http", 0.9
    - setup.py with console_scripts → "cli", 1.0
    - pyproject.toml [project.scripts] → "cli", 1.0
    - __main__.py at any package root → "cli", 0.7
    - Otherwise → "none", 1.0
    """
    repo_root = Path(repo_root).resolve()

    # Playwright config
    if (repo_root / "playwright.config.py").exists() or (
        repo_root / "playwright.config.js"
    ).exists():
        return "ui", 1.0

    # Selenium imports
    if _grep_py_files(repo_root, r"(?:import selenium|from selenium)"):
        return "ui", 0.7

    # FastAPI/Flask app declaration
    if _grep_py_files(repo_root, r'app\s*=\s*(?:FastAPI|Flask)\('):
        return "http", 1.0

    # Django ROOT_URLCONF
    if _grep_py_files(repo_root, r"ROOT_URLCONF"):
        return "http", 0.9

    # setup.py with console_scripts
    setup_py = repo_root / "setup.py"
    if setup_py.exists():
        content = setup_py.read_text(errors="ignore")
        if "console_scripts" in content or "entry_points" in content:
            return "cli", 1.0

    # pyproject.toml [project.scripts]
    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(errors="ignore")
        if "[project.scripts]" in content:
            return "cli", 1.0

    # __main__.py at any package root
    for main_py in repo_root.rglob("__main__.py"):
        # Exclude test dirs and hidden dirs
        if not any(p.name.startswith(".") or p.name == "tests" for p in main_py.parents):
            return "cli", 0.7

    return "none", 1.0


# ---------------------------------------------------------------------------
# Test-DB detection (F3)
# ---------------------------------------------------------------------------


def _detect_test_db(repo_root: Path) -> TestDB:
    """Detect test database infrastructure.

    Probe pyproject.toml, requirements*.txt, Pipfile, setup.cfg for:
    - testcontainers → "testcontainers"
    - pytest-postgresql / pytest-mysql → "pytest-postgresql"
    - :memory: or sqlite in conftest/fixtures → "sqlite"
    - Otherwise → "none"
    """
    repo_root = Path(repo_root).resolve()

    # Probe requirements files
    req_files = [
        repo_root / "pyproject.toml",
        repo_root / "requirements.txt",
        repo_root / "requirements-dev.txt",
        repo_root / "requirements-test.txt",
        repo_root / "Pipfile",
        repo_root / "setup.cfg",
    ]

    req_content = ""
    for rf in req_files:
        if rf.exists():
            req_content += rf.read_text(errors="ignore") + "\n"

    if "testcontainers" in req_content:
        return "testcontainers"

    if "pytest-postgresql" in req_content or "pytest-mysql" in req_content:
        return "pytest-postgresql"

    # Check for sqlite in conftest or fixtures
    conftest = repo_root / "conftest.py"
    if conftest.exists():
        conftest_content = conftest.read_text(errors="ignore")
        if ":memory:" in conftest_content or "sqlite" in conftest_content:
            return "sqlite"

    # Check for :memory: or sqlite3 usage in tests/conftest.py
    tests_conftest = repo_root / "tests" / "conftest.py"
    if tests_conftest.exists():
        content = tests_conftest.read_text(errors="ignore")
        if ":memory:" in content or "sqlite3" in content:
            return "sqlite"

    # Check for :memory: or sqlite3 usage in app code
    if _grep_py_files(repo_root, r'":memory:"|sqlite3\.connect'):
        return "sqlite"

    return "none"


# ---------------------------------------------------------------------------
# Roles detection (F2)
# ---------------------------------------------------------------------------


def _detect_roles(repo_root: Path) -> tuple[list[str], RolesSource]:
    """Detect role definitions from RBAC config.

    Probe in order (return on first match):
    - Django: */settings.py with AUTH_USER_MODEL + Group definitions
    - Casbin: casbin.conf / policy.csv
    - Cerbos: cerbos/policies/*.yaml
    - YAML: roles.yaml / permissions.yaml at project root
    - Otherwise → [], "none"

    For roles.yaml, use minimal YAML-like parser: extract role names from
    top-level mapping (lines like "role_name:" at column 0).
    """
    repo_root = Path(repo_root).resolve()

    # Django groups
    if _django_roles_exist(repo_root):
        roles = _parse_django_groups(repo_root)
        if roles:
            return roles, "django-groups"

    # Casbin
    casbin_roles = _parse_casbin(repo_root)
    if casbin_roles:
        return casbin_roles, "casbin"

    # Cerbos
    cerbos_roles = _parse_cerbos(repo_root)
    if cerbos_roles:
        return cerbos_roles, "cerbos"

    # YAML
    yaml_roles = _parse_yaml_roles(repo_root)
    if yaml_roles:
        return yaml_roles, "yaml"

    return [], "none"


def _django_roles_exist(repo_root: Path) -> bool:
    """Check if Django settings.py with Group definitions exists."""
    for settings in repo_root.rglob("settings.py"):
        content = settings.read_text(errors="ignore")
        if "AUTH_USER_MODEL" in content and "Group" in content:
            return True
    return False


def _parse_django_groups(repo_root: Path) -> list[str]:
    """Extract role names from Django Group.objects.create() calls.

    Basic regex: Group.objects.create(name=['"](.*?)['"])
    """
    roles = set()
    for py_file in repo_root.rglob("*.py"):
        content = py_file.read_text(errors="ignore")
        matches = re.findall(r'Group\.objects\.create\(name=["\']([^"\']+)["\']', content)
        roles.update(matches)
    return sorted(roles)


def _parse_casbin(repo_root: Path) -> list[str]:
    """Extract subjects from Casbin policy.csv."""
    roles = set()
    policy_csv = repo_root / "policy.csv"
    if policy_csv.exists():
        content = policy_csv.read_text(errors="ignore")
        # Simple parse: each line is subject,object,action
        for line in content.split("\n"):
            if line.strip() and not line.startswith("#"):
                parts = line.split(",")
                if len(parts) >= 1:
                    subject = parts[0].strip()
                    if subject and subject not in ("p", "p2"):
                        roles.add(subject)
    return sorted(roles)


def _parse_cerbos(repo_root: Path) -> list[str]:
    """Extract principal roles from cerbos/policies/*.yaml."""
    roles = set()
    cerbos_dir = repo_root / "cerbos" / "policies"
    if cerbos_dir.is_dir():
        for yaml_file in cerbos_dir.glob("*.yaml"):
            content = yaml_file.read_text(errors="ignore")
            # Extract principals: field or role names
            matches = re.findall(r"principal[:\s]+([a-z_]+)", content, re.IGNORECASE)
            roles.update(matches)
    return sorted(roles)


def _parse_yaml_roles(repo_root: Path) -> list[str]:
    """Extract role names from roles.yaml or permissions.yaml at project root.

    Minimal YAML parser: lines like "role_name:" at column 0, indented lines are
    children. Return top-level keys under 'roles:' block.
    """
    for fname in ["roles.yaml", "roles.yml", "permissions.yaml", "permissions.yml"]:
        path = repo_root / fname
        if path.exists():
            content = path.read_text(errors="ignore")
            roles = _extract_yaml_roles(content)
            if roles:
                return roles

    # Also check app/ subdirectories
    for path in repo_root.rglob("roles.yaml"):
        content = path.read_text(errors="ignore")
        roles = _extract_yaml_roles(content)
        if roles:
            return roles

    return []


def _extract_yaml_roles(yaml_content: str) -> list[str]:
    """Extract role names from YAML content.

    Heuristic: find 'roles:' block, then extract top-level keys in that block
    (lines starting with non-whitespace at the same indent level as children).
    """
    lines = yaml_content.split("\n")
    roles = []
    in_roles_block = False
    base_indent = None

    for line in lines:
        stripped = line.lstrip()

        # Check if we hit the roles: block
        if stripped.startswith("roles:") and not in_roles_block:
            in_roles_block = True
            base_indent = None
            continue

        # If not in roles block, skip
        if not in_roles_block:
            continue

        # Empty or comment line
        if not stripped or stripped.startswith("#"):
            continue

        # Calculate indent
        indent = len(line) - len(stripped)

        # If we haven't set base indent, use first content line's indent + 2
        if base_indent is None:
            base_indent = indent

        # If indent is back at base or less, we're done with roles block
        if indent < base_indent:
            in_roles_block = False
            break

        # If indent equals base, it's a role name
        if indent == base_indent:
            # Extract name (before : or whitespace)
            role_name = stripped.split(":")[0].strip()
            if role_name and not role_name.startswith("#"):
                roles.append(role_name)

    return roles


# ---------------------------------------------------------------------------
# Orchestrator pattern detection
# ---------------------------------------------------------------------------


def _detect_orchestrator_pattern(repo_root: Path) -> bool:
    """Detect orchestrator pattern for workflow-dryrun fitness gating.

    True if any of:
    - Celery task definitions
    - RQ task definitions
    - transitions / state machine library imports
    - scripts/<name>/<name>.py pattern (forge-codex style)
    - Airflow / Prefect / Dagster pipeline DAG
    """
    repo_root = Path(repo_root).resolve()

    # Celery tasks
    if _grep_py_files(repo_root, r"@celery\.task|@app\.task|from celery"):
        return True

    # RQ
    if _grep_py_files(repo_root, r"from rq|import rq"):
        return True

    # State machine libraries
    if _grep_py_files(repo_root, r"from transitions|import transitions"):
        return True
    if _grep_py_files(repo_root, r"from state_machine|import state_machine"):
        return True

    # Forge-codex style: scripts/<skill>/<skill>.py pattern
    scripts_dir = repo_root / "scripts"
    if scripts_dir.is_dir():
        for subdir in scripts_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("."):
                candidate = subdir / f"{subdir.name}.py"
                if candidate.exists():
                    return True

    # Airflow / Prefect / Dagster
    if _grep_py_files(
        repo_root, r"from airflow|import airflow|from prefect|import prefect|from dagster|import dagster"
    ):
        return True

    return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_dir(repo_root: Path, candidates: list[str]) -> Path | None:
    """Find first existing directory from candidates list."""
    for cand in candidates:
        path = repo_root / cand
        if path.is_dir():
            return path
    return None


def _grep_py_files(repo_root: Path, pattern: str) -> bool:
    """Search all .py files for regex pattern."""
    regex = re.compile(pattern)
    try:
        for py_file in repo_root.rglob("*.py"):
            # Skip hidden/test dirs for performance
            if any(p.name.startswith(".") for p in py_file.parents):
                continue
            try:
                content = py_file.read_text(errors="ignore")
                if regex.search(content):
                    return True
            except (OSError, RuntimeError):
                # File too large, permissions, etc.
                continue
    except (OSError, RuntimeError):
        # Directory iteration failed
        pass
    return False
