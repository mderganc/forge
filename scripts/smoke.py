#!/usr/bin/env python3
"""End-to-end smoke test for every forge-codex orchestrator.

Runs each script with cwd=REPO_ROOT (where state is written by default),
cleaning up state files between skills via ``takeover --cleanup --all-stale --force``.

Verifies for each orchestrator:
  - --help works (clean import)
  - Over-cap step exits 0 with friendly "nothing left to do" message
  - Step 1 succeeds and writes session state (``.forge/sessions/{id}/session.json``)
  - Second step 1 allocates another parallel session (no clobber abort)
  - ``--cleanup --all-stale --force`` clears active sessions
  - Flows mode: walks all 7 steps with override sidecar and executes flows
  - test --mode ux redirects to forge ux-review
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.diagnose.technique_coverage import catalog_technique_names  # noqa: E402

SCRIPTS = {
    "plan": REPO / "scripts/plan/plan.py",
    "develop": REPO / "scripts/develop/develop.py",
    "implement": REPO / "scripts/implement/implement.py",
    "code-review": REPO / "scripts/code_review/code_review.py",
    "test": REPO / "scripts/test/test.py",
    "diagnose": REPO / "scripts/diagnose/orchestrate.py",
    "evaluate": REPO / "scripts/evaluate/evaluate.py",
}

MAX_STEPS = {
    "plan": 7,
    "develop": 8,
    "implement": 8,
    "code-review": 6,
    "test": 6,
    "diagnose": 7,
    "evaluate": 7,  # pre mode default
}

# Skills where step 1 always allocates a new session directory (parallel-first).
PARALLEL_SESSION_SKILLS = {"plan", "code-review", "test", "diagnose"}

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
TAKEOVER_CLEANUP = REPO / "scripts/takeover/takeover.py"
SMOKE_TMP = Path(tempfile.gettempdir()) / "forge-smoke"
SMOKE_EVAL_DIR = REPO / ".forge" / "smoke-eval"


def _smoke_env() -> dict[str, str]:
    env = os.environ.copy()
    env["FORGE_SKIP_SESSION_OPTIN"] = "1"
    env["FORGE_SKIP_GRAPHIFY"] = "1"
    env["FORGE_SKIP_GRAPHIFY_SESSION_REFRESH"] = "1"
    env["FORGE_SKIP_AUTO_CLOSE"] = "1"
    return env


def run(args, cwd=REPO):
    return subprocess.run(
        [sys.executable] + args,
        cwd=cwd,
        env=_smoke_env(),
        capture_output=True,
        text=True,
        timeout=120,
        encoding="utf-8",
        errors="replace",
    )


def _expected_skill_name(name: str) -> str:
    return "design" if name == "develop" else name


def _find_skill_state_path(skill_name: str) -> Path | None:
    from scripts.shared.skill_aliases import skills_match
    from scripts.shared.session_store import iter_session_json_paths

    expected = _expected_skill_name(skill_name)
    matches: list[Path] = []
    for path in iter_session_json_paths(REPO, include_archive=False):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if skills_match(str(data.get("skill_name", "")), expected):
            matches.append(path)
    if matches:
        return max(matches, key=lambda p: p.stat().st_mtime)

    legacy_paths = [
        REPO / ".codex/forge-codex/state" / f"{skill_name}.json",
        REPO / ".codex/forge/state" / f"{skill_name}.json",
        REPO / ".forge/state" / f"{expected}.json",
        REPO / f".forge-{skill_name}-state.json",
    ]
    return next((p for p in legacy_paths if p.exists()), None)


def _count_active_sessions(skill_name: str) -> int:
    from scripts.shared.session_store import list_active_sessions
    from scripts.shared.skill_aliases import skills_match

    expected = _expected_skill_name(skill_name)
    return sum(
        1 for s in list_active_sessions(REPO) if skills_match(s.skill, expected)
    )


def _state_sidecar_dir(state_path: Path) -> Path:
    if state_path.name == "session.json":
        return state_path.parent
    return state_path.parent


def _diagnose_sidecar_dir(state_path: Path) -> Path:
    base = _state_sidecar_dir(state_path)
    sidecars = base / "sidecars"
    sidecars.mkdir(parents=True, exist_ok=True)
    return sidecars


def cleanup_repo():
    """Wipe active Forge sessions and stray evaluate/test sidecars in REPO."""
    run([str(TAKEOVER_CLEANUP), "--cleanup", "--all-stale", "--force", "--step", "1"])
    if SMOKE_EVAL_DIR.exists():
        import shutil

        shutil.rmtree(SMOKE_EVAL_DIR, ignore_errors=True)
    for pattern in (
        ".evaluate-state.json",
        ".evaluate-findings-step*.json",
        ".test-recommendation-step*.json",
    ):
        for f in REPO.rglob(pattern):
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


def _find_diagnose_state() -> Path | None:
    return _find_skill_state_path("diagnose")


_FISHBONE = [
    "CODE",
    "CONFIG",
    "DATA",
    "INFRASTRUCTURE",
    "DEPENDENCIES",
    "ENVIRONMENT",
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


def _write_smoke_problem_spec(state_dir: Path, *, hypothesis: bool = False) -> None:
    from scripts.diagnose.diagnose_framing import CORE_TECHNIQUES

    activated = set(CORE_TECHNIQUES)
    if hypothesis:
        activated.add("Fishbone / Ishikawa")
    payload = {
        "framing_entry": "evidence_snapshot",
        "problem_statement": "Smoke gate validation incident",
        "activated_techniques": sorted(activated),
    }
    (state_dir / ".diagnose-problem-spec.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


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
                {
                    "id": 1,
                    "name": "5 Whys",
                    "status": "skipped",
                    "rationale": "incomplete smoke",
                },
                {
                    "id": 2,
                    "name": "Fishbone / Ishikawa",
                    "status": "skipped",
                    "rationale": "incomplete smoke",
                },
            ],
        }
    (state_dir / ".diagnose-technique-coverage.json").write_text(
        json.dumps(data), encoding="utf-8"
    )


def smoke_skill(name, script):
    print(f"\n=== {name} ===")
    cleanup_repo()
    fails = [0]

    if not script.is_file():
        print(f"  {FAIL} script missing: {script}")
        return fails[0] + 1

    r = run([str(script), "--help"])
    assert_eq(r.returncode, 0, "--help works", fails)

    over = MAX_STEPS[name] + 1
    extra = ["--mode", "pre"] if name == "evaluate" else []
    r = run([str(script), "--step", str(over)] + extra)
    assert_eq(r.returncode, 0, f"--step {over} exits 0", fails)
    assert_contains(
        r.stderr + r.stdout,
        "nothing left to do",
        "over-cap friendly message",
        fails,
    )

    if name != "evaluate":
        r = run([str(script), "--step", "1"])
        assert_eq(r.returncode, 0, "step 1 ran", fails)

        state_path = _find_skill_state_path(name)
        if state_path is None:
            print(f"  {FAIL} no state file written by step 1")
            fails[0] += 1
        else:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            expected_skill = _expected_skill_name(name)
            assert_eq(state.get("skill_name"), expected_skill, "state.skill_name", fails)
            assert_eq(state.get("failure_count"), 0, "state.failure_count == 0", fails)
            progressed = int(state.get("last_completed_step") or 0) >= 1 or int(
                state.get("current_step") or 0
            ) >= 1
            if progressed:
                print(f"  {PASS} state progressed past step 1")
            else:
                print(f"  {FAIL} state not progressed past step 1")
                fails[0] += 1

        if name in PARALLEL_SESSION_SKILLS:
            before = _count_active_sessions(name)
            r = run([str(script), "--step", "1"])
            assert_eq(r.returncode, 0, "second step 1 allocates session", fails)
            after = _count_active_sessions(name)
            if after <= before:
                print(
                    f"  {FAIL} parallel session count: expected > {before}, got {after}"
                )
                fails[0] += 1
            else:
                print(f"  {PASS} parallel session count increased")

    if name != "evaluate":
        r = run(
            [str(TAKEOVER_CLEANUP), "--cleanup", "--all-stale", "--force", "--step", "1"]
        )
        assert_eq(r.returncode, 0, "cleanup succeeded", fails)
        assert_eq(
            _count_active_sessions(name),
            0,
            f"no active {name} sessions after cleanup",
            fails,
        )

    return fails[0]


def smoke_evaluate():
    print(f"\n=== evaluate (end-to-end findings sidecar) ===")
    cleanup_repo()
    fails = [0]

    plan = SMOKE_EVAL_DIR / "plan.md"
    plan.parent.mkdir(parents=True, exist_ok=True)
    plan.write_text("# Test Plan\n\n## Architecture Overview\nA stub.\n", encoding="utf-8")

    r = run(
        [
            str(SCRIPTS["evaluate"]),
            "--step",
            "1",
            "--mode",
            "pre",
            "--plan",
            str(plan),
        ]
    )
    assert_eq(r.returncode, 0, "evaluate step 1 ran", fails)

    state_path = plan.parent / ".evaluate-state.json"
    assert_eq(state_path.exists(), True, "state file at plan dir", fails)

    if not state_path.exists():
        return fails[0]

    sidecar = plan.parent / ".evaluate-findings-step2.json"
    sidecar.write_text(
        json.dumps(
            [
                {
                    "phase": "feasibility",
                    "severity": "critical",
                    "title": "Test F1",
                    "detail": "stub",
                }
            ]
        ),
        encoding="utf-8",
    )

    r = run([str(SCRIPTS["evaluate"]), "--step", "3", "--state", str(state_path)])
    assert_eq(r.returncode, 0, "evaluate step 3 ran", fails)
    assert_eq(sidecar.exists(), False, "sidecar deleted after ingestion", fails)

    state = json.loads(state_path.read_text(encoding="utf-8"))
    findings = state.get("findings", [])
    assert_eq(len(findings), 1, "1 finding ingested", fails)
    if findings:
        assert_eq(findings[0]["title"], "Test F1", "finding title preserved", fails)
    assert_eq(state.get("failure_count"), 0, "evaluate.failure_count present", fails)

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

    state_dir = _diagnose_sidecar_dir(state_path)
    _write_smoke_problem_spec(state_dir, hypothesis=True)
    _write_smoke_hypothesis_register(state_dir, eliminated=False)
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

    state_dir = _diagnose_sidecar_dir(state_path)
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

    state_dir = _diagnose_sidecar_dir(state_path)
    # Omit coverage sidecar — adaptive step-7 closure gate should fail closed.

    r = run([str(SCRIPTS["diagnose"]), "--step", "7", "--state", str(state_path)])
    assert_eq(r.returncode, 0, "diagnose step 7 ran", fails)
    out = r.stdout + r.stderr
    assert_contains(out, "DIAGNOSE ARTIFACT GATE", "gate block present", fails)
    assert_contains(out.lower(), "technique coverage", "coverage section in gate", fails)
    assert_contains(out, "5 Whys", "mentions five whys in closure gate", fails)

    cleanup_repo()
    return fails[0]


def smoke_test_flows_mode():
    """Smoke: --mode flows walks through 7 steps with override sidecar."""
    print(f"\n=== test (flows mode smoke test) ===")
    cleanup_repo()
    fails = [0]

    r = run(
        [
            str(SCRIPTS["test"]),
            "--mode",
            "flows",
            "--flow-type",
            "scenario",
            "--step",
            "1",
        ]
    )
    assert_eq(r.returncode, 0, "flows step 1 ran", fails)

    state_path = _find_skill_state_path("test")
    if state_path:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert_eq(state.get("custom", {}).get("mode"), "flows", "flows mode set in state", fails)
        assert_eq(state.get("max_step"), 7, "max_step=7 in flows mode", fails)

    for step in range(2, 8):
        r = run([str(SCRIPTS["test"]), "--mode", "flows", "--step", str(step)])
        if r.returncode not in (0, 1):
            print(f"  {FAIL} step {step} returned unexpected code {r.returncode}")
            fails[0] += 1

    cleanup_repo()
    return fails[0]


def smoke_test_ux_mode_redirect():
    """Smoke: --mode ux exits 2 and points at forge ux-review."""
    print(f"\n=== test (ux mode redirect smoke) ===")
    cleanup_repo()
    fails = [0]

    r = run([str(SCRIPTS["test"]), "--mode", "ux", "--step", "1"])
    assert_eq(r.returncode, 2, "ux mode exits 2", fails)
    out = (r.stdout or "") + (r.stderr or "")
    assert_contains(out, "ux-review", "redirect mentions ux-review", fails)

    cleanup_repo()
    return fails[0]


def main():
    total = 0
    for name in ("plan", "develop", "implement", "code-review", "test", "diagnose"):
        total += smoke_skill(name, SCRIPTS[name])
    total += smoke_evaluate()
    total += smoke_diagnose_hypothesis_gate()
    total += smoke_diagnose_five_whys_gate()
    total += smoke_diagnose_coverage_gate()
    total += smoke_test_flows_mode()
    total += smoke_test_ux_mode_redirect()
    cleanup_repo()

    print(f"\n{'=' * 60}")
    if total == 0:
        print(f"{PASS} all smoke tests passed")
        return 0
    print(f"{FAIL} {total} failures")
    return 1


if __name__ == "__main__":
    sys.exit(main())
