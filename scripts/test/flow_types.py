"""Mock flow-type catalog — structured form for recommendation logic.

This module exports FLOW_TYPES, a catalog of the four supported mock-flow styles.
Provides per-type fitness signals, criteria scores, tooling defaults, and file-layout
templates for the recommendation step in `forge:test --mode flows`.

The companion prose documentation is at templates/mock-flow-types.md. The prose is
authoritative for human readers; this module is the structured form consulted by
recommendation and scaffolding logic.

Provenance: v1 tuned against forge-codex repo + tests/fixtures/mock-flows-target/

Glossary:
- Criteria 1–8: The eight quality gates defined in the plan. Each flow type is
  scored 0–10 per criterion.
- fit_signals/anti_signals: Heuristics for the recommendation algorithm. Key is a
  project-detected signal (e.g., "has_http_endpoint"); value is a weight applied
  when scoring this flow type.
- needs_orchestrator_pattern (F11): workflow-dryrun=True; others=False. Used to
  gate recommendation when the SUT has no orchestrator pattern.
- needs_test_db (F3): scenario/workflow-dryrun=True; http-replay=False. Used to
  deprioritize types when no test-DB infrastructure is detected.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FlowTypeMetadata:
    """Structured metadata for one flow type.

    All fields are frozen for immutability. Attributes:
    - name: Type name ("scenario" | "bdd" | "http-replay" | "workflow-dryrun").
    - tooling: List of tool/library names (e.g., ["pytest", "pytest-recording"]).
    - file_layout: Dict mapping layout keys to path templates. Must include "primary"
      (the main test file template).
    - fit_signals: Dict of signal_name -> weight (0.0–1.0). Higher = stronger fit.
    - anti_signals: Dict of signal_name -> weight. Higher magnitude = stronger mis-fit.
    - criteria_scores: Dict {criterion_number (1–8): score (0–10)}. Encodes how well
      this type meets each quality criterion.
    - needs_orchestrator_pattern: If True, recommendation requires an orchestrator
      pattern detected in the project (e.g., state machine, multi-step workflow).
    - needs_test_db: If True, recommendation requires test-DB infrastructure.
    - data_pack_dirs: List of standard subdirectories for test data packs:
      ["clean", "messy", "edge-cases", "duplicates"].
    """

    name: str
    tooling: list[str] = field(default_factory=list)
    file_layout: dict[str, str] = field(default_factory=dict)
    fit_signals: dict[str, float] = field(default_factory=dict)
    anti_signals: dict[str, float] = field(default_factory=dict)
    criteria_scores: dict[int, int] = field(default_factory=dict)
    needs_orchestrator_pattern: bool = False
    needs_test_db: bool = False
    data_pack_dirs: list[str] = field(default_factory=lambda: ["clean", "messy", "edge-cases", "duplicates"])


FLOW_TYPES: dict[str, FlowTypeMetadata] = {
    "scenario": FlowTypeMetadata(
        name="scenario",
        tooling=["pytest"],
        file_layout={
            "primary": "tests/scenarios/test_<scope>.py",
            "fixtures": "tests/scenarios/<scope>/fixtures/",
            "data_packs": "tests/scenarios/<scope>/fixtures/data-packs/",
        },
        fit_signals={
            "has_http_endpoint": 0.8,
            "has_cli_entry": 0.6,
            "has_test_db": 0.9,
            "framework_is_pytest": 0.7,
        },
        anti_signals={
            "no_entry_point": 0.5,
            "no_test_db": 0.4,
        },
        criteria_scores={
            1: 9,  # Realistic scenarios — well-suited, end-to-end flow
            2: 9,  # Representative test data — data packs directly supported
            3: 8,  # User roles/permissions — can parameterize via fixtures
            4: 10, # Full process execution — hits HTTP/CLI/module entry points
            5: 9,  # Outcome validation — multiple assertion surfaces (DB, response, logs)
            6: 8,  # Minimal mocking — can stub only externals when test DB exists
            7: 9,  # Failure/edge handling — easy to add failure-path variants
            8: 10, # Repeatable regression — deterministic with fixed test data
        },
        needs_orchestrator_pattern=False,
        needs_test_db=True,
    ),
    "bdd": FlowTypeMetadata(
        name="bdd",
        tooling=["pytest-bdd", "behave"],
        file_layout={
            "primary": "tests/features/test_<scope>.feature",
            "steps": "tests/features/steps/step_<scope>.py",
            "fixtures": "tests/features/<scope>/fixtures/",
            "data_packs": "tests/features/<scope>/fixtures/data-packs/",
        },
        fit_signals={
            "has_feature_files": 0.9,
            "team_prefers_gherkin": 0.7,
            "has_http_endpoint": 0.7,
            "has_test_db": 0.8,
        },
        anti_signals={
            "no_existing_features": 0.3,
            "no_test_db": 0.3,
        },
        criteria_scores={
            1: 10, # Realistic scenarios — Gherkin scenarios are inherently realistic
            2: 8,  # Representative test data — indirectly via step definitions
            3: 8,  # User roles/permissions — parameterized via scenario outlines
            4: 9,  # Full process execution — HTTP/CLI via steps
            5: 8,  # Outcome validation — step assertions, can touch multiple surfaces
            6: 7,  # Minimal mocking — can mock externals in step definitions
            7: 8,  # Failure/edge handling — natural via scenario variants
            8: 9,  # Repeatable regression — Gherkin + deterministic data
        },
        needs_orchestrator_pattern=False,
        needs_test_db=True,
    ),
    "http-replay": FlowTypeMetadata(
        name="http-replay",
        tooling=["pytest", "vcrpy", "pytest-recording"],
        file_layout={
            "primary": "tests/cassettes/test_<scope>.py",
            "cassettes": "tests/cassettes/data/<scope>/",
            "data_packs": "tests/cassettes/data/<scope>/data-packs/",
        },
        fit_signals={
            "has_http_endpoint": 1.0,
            "no_test_db": 0.8,
            "has_external_apis": 0.7,
            "framework_is_pytest": 0.8,
        },
        anti_signals={
            "no_http_endpoint": 0.6,
            "test_db_required": 0.2,  # HTTP-replay doesn't need DB state
        },
        criteria_scores={
            1: 7,  # Realistic scenarios — good for API-driven workflows, limited to HTTP
            2: 6,  # Representative test data — cassettes capture real payloads, less control
            3: 6,  # User roles/permissions — can replay different auth headers, but limited
            4: 10, # Full process execution — exact HTTP record/replay
            5: 7,  # Outcome validation — response payload, cassette metadata, limited DB
            6: 9,  # Minimal mocking — no mocking needed if cassettes are replayed
            7: 5,  # Failure/edge handling — replays must pre-exist; hard to add new failures
            8: 8,  # Repeatable regression — cassette replay is deterministic
        },
        needs_orchestrator_pattern=False,
        needs_test_db=False,
    ),
    "workflow-dryrun": FlowTypeMetadata(
        name="workflow-dryrun",
        tooling=["pytest"],
        file_layout={
            "primary": "tests/orchestration/test_<scope>_dryrun.py",
            "harness": "tests/orchestration/harness_<scope>.py",
            "data_packs": "tests/orchestration/<scope>/fixtures/data-packs/",
        },
        fit_signals={
            "has_orchestrator_pattern": 1.0,
            "has_state_machine": 0.9,
            "has_multi_step_workflow": 0.8,
            "has_test_db": 0.8,
        },
        anti_signals={
            "no_orchestrator": 1.0,
            "no_test_db": 0.4,
        },
        criteria_scores={
            1: 9,  # Realistic scenarios — end-to-end multi-step journeys
            2: 8,  # Representative test data — varies by step, data packs per role
            3: 8,  # User roles/permissions — parameterized across workflow steps
            4: 8,  # Full process execution — orchestrator harness, not direct calls
            5: 9,  # Outcome validation — state transitions, assertions per step
            6: 8,  # Minimal mocking — stub step workers, exercise core logic
            7: 9,  # Failure/edge handling — test retry paths, partial failures
            8: 10, # Repeatable regression — deterministic step orchestration
        },
        needs_orchestrator_pattern=True,
        needs_test_db=True,
    ),
}


def score_flow_types(layout) -> dict[str, float]:
    """Score each flow type against project layout.

    Given project-detected layout signals (from detect_test_layout), returns
    a dict mapping each flow type name to a numeric score (0.0–10.0).

    Scoring logic:
    1. If type requires orchestrator and project has none, score = 0.
    2. If type requires test-DB and project has none, apply penalty.
    3. Sum fit_signals and subtract anti_signals based on project signals.
    4. Return normalized score.

    Args:
        layout: TestLayout object from detect_test_layout with attributes:
            - has_orchestrator_pattern (bool)
            - test_db (str: "none", "sqlite", "testcontainers", "pytest-postgresql")
            - entry_point (str: "none", "cli", "http", "ui", "module")
            - roles (list[str]): discovered role names
            - framework (str): "pytest" or "unknown"

    Returns:
        Dict mapping each flow type to a score.
    """
    scores = {}

    # Extract attributes from layout (works with both dataclass and dict)
    has_orchestrator = getattr(layout, "has_orchestrator_pattern",
                               layout.get("has_orchestrator_pattern", False) if isinstance(layout, dict) else False)
    test_db = getattr(layout, "test_db",
                      layout.get("test_db", "none") if isinstance(layout, dict) else "none")
    has_test_db = test_db != "none"
    entry_point = getattr(layout, "entry_point",
                          layout.get("entry_point", "none") if isinstance(layout, dict) else "none")
    framework = getattr(layout, "framework",
                        layout.get("framework", "unknown") if isinstance(layout, dict) else "unknown")

    has_http_endpoint = entry_point == "http"
    has_cli_entry = entry_point == "cli"

    for flow_type_name, metadata in FLOW_TYPES.items():
        # Hard gate: if orchestrator required but not present, score is 0
        if metadata.needs_orchestrator_pattern and not has_orchestrator:
            scores[flow_type_name] = 0
            continue

        # Start with a base score of 5
        score = 5.0

        # Apply fit signals (positive)
        if "has_http_endpoint" in metadata.fit_signals and has_http_endpoint:
            score += metadata.fit_signals["has_http_endpoint"] * 2.0
        if "has_cli_entry" in metadata.fit_signals and has_cli_entry:
            score += metadata.fit_signals["has_cli_entry"] * 1.5
        if "has_test_db" in metadata.fit_signals and has_test_db:
            score += metadata.fit_signals["has_test_db"] * 2.0
        if "framework_is_pytest" in metadata.fit_signals and framework == "pytest":
            score += metadata.fit_signals["framework_is_pytest"] * 1.0
        if "has_orchestrator_pattern" in metadata.fit_signals and has_orchestrator:
            score += metadata.fit_signals["has_orchestrator_pattern"] * 2.0

        # Apply anti-signals (negative)
        if "no_entry_point" in metadata.anti_signals and entry_point == "none":
            score -= metadata.anti_signals["no_entry_point"] * 1.5
        if "no_test_db" in metadata.anti_signals and not has_test_db:
            score -= metadata.anti_signals["no_test_db"] * 1.5
        if "no_http_endpoint" in metadata.anti_signals and not has_http_endpoint:
            score -= metadata.anti_signals["no_http_endpoint"] * 1.0
        if "no_orchestrator" in metadata.anti_signals and not has_orchestrator:
            score -= metadata.anti_signals["no_orchestrator"] * 3.0

        # Clamp to [0, 10]
        score = max(0.0, min(10.0, score))
        scores[flow_type_name] = score

    return scores
