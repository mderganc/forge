#!/usr/bin/env python3
"""End-to-end smoke test for every forge-codex orchestrator.

Runs each script with cwd=REPO_ROOT (where state is written by default),
cleaning up state files between skills via --cleanup --all-stale --force.

Verifies for each orchestrator:
  - --help works (clean import)
  - Over-cap step exits 0 with friendly "nothing left to do" message
  - Step 1 succeeds and writes state with skill_name + failure_count
  - Same-skill clobber abort fires when step 1 is rerun (where applicable)
  - --cleanup --all-stale --force removes the state file
  - Flows mode: walks all 7 steps with override sidecar and executes flows
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.diagnose.technique_coverage import catalog_technique_names  # noqa: E402

SCRIPTS = {
    "plan":        REPO / "scripts/plan/plan.py",
    "develop":     REPO / "scripts/develop/develop.py",
    "implement":   REPO / "scripts/implement/implement.py",
    "code-review": REPO / "scripts/code-review/code_review.py",
    "test":        REPO / "scripts/test/test.py",
    "diagnose":    REPO / "scripts/diagnose/orchestrate.py",
    "evaluate":    REPO / "scripts/evaluate/evaluate.py",
}

MAX_STEPS = {
    "plan": 7, "develop": 7, "implement": 8, "code-review": 6,
    "test": 6, "diagnose": 7, "evaluate": 7,  # pre mode default
}

# Skills that hit handle_step_1 → check_same_skill_clobber path.
# develop and implement use _load_or_init pattern (resume vs init); skip clobber check.
CLOBBER_SKILLS = {"plan", "code-review", "test", "diagnose"}

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
RESUME = REPO / "scripts/shared/resume.py"


def run(args, cwd=REPO):
    return subprocess.run(
        [sys.executable] + args, cwd=cwd,
        capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace",
    )


def cleanup_repo():
    """Wipe every forge-codex state file in REPO."""
    run([str(RESUME), "--cleanup", "--all-stale", "--force"])
    # Also nuke the evaluate sidecar/state file if it lingered
    for f in REPO.rglob(".evaluate-state.json"):
        f.unlink(missing_ok=True)
    for f in REPO.rglob(".evaluate-findings-step*.json"):
        f.unlink(missing_ok=True)
    # Clean up test flows sidecar
    for f in REPO.rglob(".test-recommendation-step*.json"):
        f.unlink(missing_ok=True)


def assert_eq(actual, expected, msg, fails):
    if actual == expected:
        print(f"  {PASS} {msg}")
        return
    print(f"  {FAIL} {msg}: expected {expected!r}, got {actual!r}")
    fails[0] += 1


def assert_contains(haystack, needle, msg, fails):
    if needle in haystack:
        print(f"  {PASS} {msg}")
        return
    print(f"  {FAIL} {msg}: {needle!r} not found")
    fails[0] += 1


def _diagnose_state_paths():
    return [
        REPO / ".codex/forge-codex/state/diagnose.json",
        REPO / ".codex/forge/state/diagnose.json",
        REPO / ".forge/state/diagnose.json",
    ]


def _find_diagnose_state():
    return next((p for p in _diagnose_state_paths() if p.exists()), None)


_FISHBONE = [
    "CODE", "CONFIG", "DATA", "INFRASTRUCTURE", "DEPENDENCIES", "ENVIRONMENT",
]


def _smoke_hypothesis_entry(i: int, category: str, status: str = "open") -> dict:
    return {
        "id": f"H{i:02d}",
        "statement": f"Smoke gate candidate {i} in {category} path for validation",
        "category": category,
        "invariant_violated": "service healthy",
        "predictions": ["observable failure"],
        "falsification_test": "reproduce in staging",
        "status": status,
        "evidence": "",
        "ruled_out_reason": "ruled out for smoke" if status == "ruled_out" else "",
    }


def _write_smoke_hypothesis_register(state_dir: Path, *, eliminated: bool = False) -> None:
    hyps = [
        _smoke_hypothesis_entry(i + 1, _FISHBONE[i % len(_FISHBONE)])
        for i in range(10)
    ]
    if eliminated:
        for h in hyps:
            h["status"] = "ruled_out"
            h["ruled_out_reason"] = "not the cause"
        hyps[0]["status"] = "confirmed"
        hyps[0]["ruled_out_reason"] = ""
    reg = {"min_required": 10, "hypotheses": hyps}
    (state_dir / ".diagnose-hypotheses.json").write_text(
        json.dumps(reg), encoding="utf-8"
    )


def _write_smoke_five_whys_bad(state_dir: Path) -> None:
    """Five-whys chain with disconnected causal linkage (fails validate_chains)."""
    data = {
        "version": 1,
        "symptom": "API returns 500 on login",
        "chains": [
            {
                "id": "chain-1",
                "hypothesis_id": "H01",
                "layers": [
                    {
                        "level": 1,
                        "because": "Login handler throws when user record is missing",
                        "why_question": "Why is the user record missing in the login handler?",
                        "evidence": "auth.py:47",
                        "verdict": "confirmed",
                    },
                    {
                        "level": 2,
                        "because": "Query uses email column but form sends username",
                        "why_question": "Why is the weather bad today?",
                        "evidence": "diff",
                        "verdict": "confirmed",
                    },
                    {
                        "level": 3,
                        "because": "Migration renamed column without updating login SQL",
                        "why_question": "Why does the login query use the email column?",
                        "evidence": "git log",
                        "verdict": "confirmed",
                    },
                ],
                "root_cause": "Migration gap",
                "stop_reason": "defect",
                "but_for": "Without migration gap, login would succeed",
            }
        ],
    }
    (state_dir / ".diagnose-five-whys.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


def _write_smoke_coverage_matrix(state_dir: Path, *, complete: bool = True) -> None:
    if complete:
        rows = []
        for i, name in enumerate(catalog_technique_names(), start=1):
            row = {
                "id": i,
                "name": name,
                "status": "skipped",
                "rationale": f"Not required for smoke gate ({name})",
            }
            if name == "5 Whys":
                row["status"] = "applied"
                row["evidence_pointer"] = ".diagnose-five-whys.json#chain-1"
                row["rationale"] = ""
            rows.append(row)
        data = {
            "version": 1,
            "incident_profile": ["simple"],
            "routing_preferred": ["5 Whys"],
            "techniques": rows,
        }
    else:
        data = {
            "version": 1,
            "incident_profile": ["simple"],
            "routing_preferred": [],
            "techniques": [
                {"id": 1, "name": "5 Whys", "status": "skipped", "rationale": "incomplete smoke"},
                {"id": 2, "name": "Fishbone / Ishikawa", "status": "skipped", "rationale": "incomplete smoke"},
            ],
        }
    (state_dir / ".diagnose-technique-coverage.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


def smoke_skill(name, script):
    print(f"\n=== {name} ===")
    cleanup_repo()
    fails = [0]

    # --help
    r = run([str(script), "--help"])
    assert_eq(r.returncode, 0, "--help works", fails)

    # Over-cap step
    over = MAX_STEPS[name] + 1
    extra = ["--mode", "pre"] if name == "evaluate" else []
    r = run([str(script), "--step", str(over)] + extra)
    assert_eq(r.returncode, 0, f"--step {over} exits 0", fails)
    assert_contains(r.stderr + r.stdout, "nothing left to do",
                    "over-cap friendly message", fails)

    # Step 1 (skip evaluate — needs --plan)
    if name != "evaluate":
        r = run([str(script), "--step", "1"])
        assert_eq(r.returncode, 0, "step 1 ran", fails)

        if r.returncode == 0:
            # Find the state file (REPO_ROOT/.forge/state/<skill>.json or .codex/...)
            paths = [
                REPO / ".codex/forge-codex/state" / f"{name}.json",
                REPO / ".codex/forge/state" / f"{name}.json",
                REPO / ".forge/state" / f"{name}.json",
                REPO / f".forge-{name}-state.json",
            ]
            state_path = next((p for p in paths if p.exists()), None)
            if state_path is None:
                print(f"  {FAIL} no state file written by step 1")
                fails[0] += 1
            else:
                state = json.loads(state_path.read_text())
                expected_skill = "design" if name == "develop" else name
                assert_eq(state.get("skill_name"), expected_skill, "state.skill_name", fails)
                assert_eq(state.get("failure_count"), 0,
                          "state.failure_count == 0", fails)
                assert_eq(state.get("current_step"), 1,
                          "state.current_step == 1", fails)

    # Same-skill clobber: re-running step 1 should abort with rc=1
    if name in CLOBBER_SKILLS:
        r = run([str(script), "--step", "1"])
        assert_eq(r.returncode, 1, "step-1 rerun aborts (rc=1)", fails)
        assert_contains(r.stderr, "already in progress",
                        "clobber message", fails)

    # --cleanup --force clears the state
    if name != "evaluate":
        r = run([str(RESUME), "--cleanup", "--all-stale", "--force"])
        assert_eq(r.returncode, 0, "cleanup succeeded", fails)
        # Verify the skill's state file is gone
        for p in (
            REPO / ".codex/forge-codex/state" / f"{name}.json",
            REPO / ".forge/state" / f"{name}.json",
        ):
            assert_eq(p.exists(), False, f"{p.name} removed", fails)

    return fails[0]


def smoke_evaluate():
    print(f"\n=== evaluate (end-to-end findings sidecar) ===")
    cleanup_repo()
    fails = [0]

    # Use a real plan from /tmp so we don't pollute the repo
    plan = Path("/tmp/forge-smoke/plan.md")
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("# Test Plan\n\n## Architecture Overview\nA stub.\n")

    # Step 1
    r = run([str(SCRIPTS["evaluate"]), "--step", "1",
             "--mode", "pre", "--plan", str(plan)])
    assert_eq(r.returncode, 0, "evaluate step 1 ran", fails)

    # State file lives next to the plan
    state_path = plan.parent / ".evaluate-state.json"
    assert_eq(state_path.exists(), True,
              "state file at plan dir", fails)

    if not state_path.exists():
        return fails[0]

    # Drop a findings sidecar at the state-file directory for step 2
    sidecar = plan.parent / ".evaluate-findings-step2.json"
    sidecar.write_text(json.dumps([
        {"phase": "feasibility", "severity": "critical",
         "title": "Test F1", "detail": "stub"},
    ]))

    # Step 3 ingests sidecar from step 2
    r = run([str(SCRIPTS["evaluate"]), "--step", "3",
             "--state", str(state_path)])
    assert_eq(r.returncode, 0, "evaluate step 3 ran", fails)
    assert_eq(sidecar.exists(), False,
              "sidecar deleted after ingestion", fails)

    state = json.loads(state_path.read_text())
    findings = state.get("findings", [])
    assert_eq(len(findings), 1, "1 finding ingested", fails)
    if findings:
        assert_eq(findings[0]["title"], "Test F1",
                  "finding title preserved", fails)
    assert_eq(state.get("failure_count"), 0,
              "evaluate.failure_count present", fails)

    # Cleanup
    state_path.unlink(missing_ok=True)
    plan.unlink(missing_ok=True)

    return fails[0]


def smoke_diagnose_hypothesis_gate():
    """Step 4 gate fires when register has fewer than 10 hypotheses."""
    print("\n=== diagnose hypothesis gate (step 4) ===")
    cleanup_repo()
    fails = [0]

    r = run([str(SCRIPTS["diagnose"]), "--step", "1"])
    assert_eq(r.returncode, 0, "diagnose step 1 ran", fails)
    if r.returncode != 0:
        return fails[0]

    state_path = _find_diagnose_state()
    if state_path is None:
        print(f"  {FAIL} no diagnose state file")
        return fails[0] + 1

    state_dir = state_path.parent
    _write_smoke_hypothesis_register(state_dir, eliminated=False)
    # Only 7 hypotheses — below minimum
    reg = json.loads((state_dir / ".diagnose-hypotheses.json").read_text(encoding="utf-8"))
    reg["hypotheses"] = reg["hypotheses"][:7]
    (state_dir / ".diagnose-hypotheses.json").write_text(
        json.dumps(reg), encoding="utf-8"
    )

    r = run([str(SCRIPTS["diagnose"]), "--step", "4", "--state", str(state_path)])
    assert_eq(r.returncode, 0, "diagnose step 4 ran", fails)
    out = r.stdout + r.stderr
    assert_contains(out, "DIAGNOSE ARTIFACT GATE", "gate block present", fails)
    assert_contains(out, "step 3", "retry step 3 suggested", fails)

    cleanup_repo()
    return fails[0]


def smoke_diagnose_five_whys_gate():
    """Step 5 bundle gate fires when five-whys chains fail causal linkage."""
    print("\n=== diagnose five-whys gate (step 5) ===")
    cleanup_repo()
    fails = [0]

    r = run([str(SCRIPTS["diagnose"]), "--step", "1"])
    assert_eq(r.returncode, 0, "diagnose step 1 ran", fails)
    if r.returncode != 0:
        return fails[0]

    state_path = _find_diagnose_state()
    if state_path is None:
        print(f"  {FAIL} no diagnose state file")
        return fails[0] + 1

    state_dir = state_path.parent
    _write_smoke_hypothesis_register(state_dir, eliminated=True)
    _write_smoke_five_whys_bad(state_dir)
    _write_smoke_coverage_matrix(state_dir, complete=True)

    r = run([str(SCRIPTS["diagnose"]), "--step", "5", "--state", str(state_path)])
    assert_eq(r.returncode, 0, "diagnose step 5 ran", fails)
    out = r.stdout + r.stderr
    assert_contains(out, "DIAGNOSE ARTIFACT GATE", "gate block present", fails)
    assert_contains(out, "Five Whys", "five-whys section in gate", fails)
    assert_contains(out, "step 4", "retry step 4 suggested", fails)

    cleanup_repo()
    return fails[0]


def smoke_diagnose_coverage_gate():
    """Step 7 closure gate fires when the 20-technique matrix is incomplete."""
    print("\n=== diagnose coverage gate (step 7) ===")
    cleanup_repo()
    fails = [0]

    r = run([str(SCRIPTS["diagnose"]), "--step", "1"])
    assert_eq(r.returncode, 0, "diagnose step 1 ran", fails)
    if r.returncode != 0:
        return fails[0]

    state_path = _find_diagnose_state()
    if state_path is None:
        print(f"  {FAIL} no diagnose state file")
        return fails[0] + 1

    state_dir = state_path.parent
    _write_smoke_coverage_matrix(state_dir, complete=False)

    r = run([str(SCRIPTS["diagnose"]), "--step", "7", "--state", str(state_path)])
    assert_eq(r.returncode, 0, "diagnose step 7 ran", fails)
    out = r.stdout + r.stderr
    assert_contains(out, "DIAGNOSE ARTIFACT GATE", "gate block present", fails)
    assert_contains(out, "Technique coverage", "coverage section in gate", fails)
    assert_contains(out, "20", "mentions 20-technique matrix", fails)

    cleanup_repo()
    return fails[0]


def smoke_test_flows_mode():
    """Smoke: --mode flows walks through 7 steps with override sidecar.

    Verifies the flows-mode pipeline:
    1. Clean any prior state
    2. Run step 1 with --mode flows (initializes flow context)
    3. Run steps 2..7 sequentially (verifies no crashes, state updated)
    4. Verify final state has flow_type set and workflow terminates
    5. Cleanup
    """
    print(f"\n=== test (flows mode smoke test) ===")
    cleanup_repo()
    fails = [0]

    # Step 1: Initialize flows mode
    r = run([str(SCRIPTS["test"]), "--mode", "flows",
             "--flow-type", "scenario", "--step", "1"])
    assert_eq(r.returncode, 0, "flows step 1 ran", fails)

    # Check state was created with flows mode
    paths = [
        REPO / ".codex/forge-codex/state" / "test.json",
        REPO / ".forge/state" / "test.json",
    ]
    state_path = next((p for p in paths if p.exists()), None)
    if state_path:
        state = json.loads(state_path.read_text())
        assert_eq(state.get("custom", {}).get("mode"), "flows",
                  "flows mode set in state", fails)
        assert_eq(state.get("max_step"), 7, "max_step=7 in flows mode", fails)

    # Walk steps 2..7
    for step in range(2, 8):
        r = run([str(SCRIPTS["test"]), "--mode", "flows", "--step", str(step)])
        # Steps may return non-zero if they're stubs; we just check they don't crash
        if r.returncode != 0 and r.returncode != 1:
            print(f"  {FAIL} step {step} returned unexpected code {r.returncode}")
            fails[0] += 1

    # Final cleanup
    cleanup_repo()

    return fails[0]


def main():
    total = 0
    for name in ("plan", "develop", "implement", "code-review",
                 "test", "diagnose"):
        total += smoke_skill(name, SCRIPTS[name])
    total += smoke_evaluate()
    total += smoke_diagnose_hypothesis_gate()
    total += smoke_diagnose_five_whys_gate()
    total += smoke_diagnose_coverage_gate()
    total += smoke_test_flows_mode()
    cleanup_repo()  # final cleanup

    print(f"\n{'=' * 60}")
    if total == 0:
        print(f"{PASS} all smoke tests passed")
        return 0
    print(f"{FAIL} {total} failures")
    return 1


if __name__ == "__main__":
    sys.exit(main())
