#!/usr/bin/env python3
"""Real-world E2E validation for diagnose hypothesis gates (subprocess + state files)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ORCH = REPO / "scripts" / "diagnose" / "orchestrate.py"
RESUME = REPO / "scripts" / "shared" / "resume.py"
FORGE = "forge"

FISHBONE = [
    "CODE", "CONFIG", "DATA", "INFRASTRUCTURE", "DEPENDENCIES", "ENVIRONMENT",
]

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"


def run(args: list[str], cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=45,
        encoding="utf-8",
        errors="replace",
    )


def cleanup() -> None:
    run([sys.executable, str(RESUME), "--cleanup", "--all-stale", "--force"])


def ok(cond: bool, msg: str, fails: list[int]) -> None:
    if cond:
        print(f"  {PASS} {msg}")
    else:
        print(f"  {FAIL} {msg}")
        fails[0] += 1


def find_state() -> Path | None:
    for p in (
        REPO / ".codex/forge/state/diagnose.json",
        REPO / ".codex/forge-codex/state/diagnose.json",
        REPO / ".forge/state/diagnose.json",
    ):
        if p.exists():
            return p
    return None


def write_register(state_dir: Path, count: int, *, confirmed: bool = False) -> None:
    hyps = []
    for i in range(count):
        cat = FISHBONE[i % len(FISHBONE)]
        status = "confirmed" if confirmed and i == 0 else "ruled_out" if confirmed else "open"
        hyps.append({
            "id": f"H{i + 1:02d}",
            "statement": f"E2E candidate {i + 1}: defect trace in {cat} layer zeta{i + 1}",
            "category": cat,
            "invariant_violated": "invariant",
            "predictions": ["observable"],
            "falsification_test": "test",
            "status": status,
            "evidence": "",
            "ruled_out_reason": "ruled out in validation" if status == "ruled_out" else "",
        })
    (state_dir / ".diagnose-hypotheses.json").write_text(
        json.dumps({"min_required": 10, "hypotheses": hyps}),
        encoding="utf-8",
    )


def load_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def advance_through_step3(state_path: Path, *, from_step: int = 2) -> None:
    """Complete steps through 3 so step 4 gate runs against real state."""
    for step in range(from_step, 4):
        r = run([sys.executable, str(ORCH), "--step", str(step), "--state", str(state_path)])
        if r.returncode != 0:
            raise RuntimeError(f"step {step} failed: {r.stderr or r.stdout}")


def scenario_gate_blocks_completion(fails: list[int]) -> None:
    print("\n=== E2E: gate failure does not mark step 4 complete (W1) ===")
    cleanup()
    r = run([sys.executable, str(ORCH), "--step", "1"])
    ok(r.returncode == 0, "diagnose step 1", fails)
    state_path = find_state()
    if state_path is None:
        ok(False, "diagnose state file exists", fails)
        return

    advance_through_step3(state_path)
    s3 = load_state(state_path)
    last3 = s3.get("last_completed_step", 0)
    ok(last3 >= 3, f"after step 3 last_completed_step >= 3 (got {last3})", fails)

    write_register(state_path.parent, 7)
    r4 = run([sys.executable, str(ORCH), "--step", "4", "--state", str(state_path)])
    out = r4.stdout + r4.stderr
    ok(r4.returncode == 0, "step 4 orchestrator exits 0", fails)
    ok("HYPOTHESIS REGISTER GATE" in out, "gate block in output", fails)
    ok("step 3" in out, "retry step 3 in output", fails)
    ok("Should I continue" in out or "wait for approval" in out.lower(), "confirmation required", fails)

    s4 = load_state(state_path)
    ok(s4.get("current_step") == 4, "current_step is 4 (re-entrant)", fails)
    ok(
        s4.get("last_completed_step", 0) < 4,
        f"last_completed_step < 4 after failed gate (got {s4.get('last_completed_step')})",
        fails,
    )
    ok(s4.get("custom", {}).get("hypothesis_regen_attempts") == 1, "regen attempt incremented", fails)

    # resume.py must NOT advance to step 5
    rr = run([sys.executable, str(RESUME)])
    resume_out = rr.stdout + rr.stderr
    ok("--step 4" in resume_out or "step 4" in resume_out.lower(), "resume targets step 4 retry", fails)
    ok("--step 5" not in resume_out, "resume does not suggest step 5 yet", fails)


def scenario_valid_register_passes(fails: list[int]) -> None:
    print("\n=== E2E: valid register passes step 4 ===")
    cleanup()
    run([sys.executable, str(ORCH), "--step", "1"])
    state_path = find_state()
    if state_path is None:
        ok(False, "state exists", fails)
        return
    advance_through_step3(state_path)
    write_register(state_path.parent, 10)
    r4 = run([sys.executable, str(ORCH), "--step", "4", "--state", str(state_path)])
    out = r4.stdout + r4.stderr
    ok(r4.returncode == 0, "step 4 exits 0", fails)
    ok("HYPOTHESIS REGISTER GATE" not in out, "no gate block", fails)
    s4 = load_state(state_path)
    ok(s4.get("last_completed_step") == 4, "step 4 marked complete", fails)


def scenario_elimination_gate(fails: list[int]) -> None:
    print("\n=== E2E: elimination gate at step 5 ===")
    cleanup()
    run([sys.executable, str(ORCH), "--step", "1"])
    state_path = find_state()
    if state_path is None:
        ok(False, "state exists", fails)
        return
    advance_through_step3(state_path)
    write_register(state_path.parent, 10, confirmed=False)
    run([sys.executable, str(ORCH), "--step", "4", "--state", str(state_path)])

    r5 = run([sys.executable, str(ORCH), "--step", "5", "--state", str(state_path)])
    out = r5.stdout + r5.stderr
    ok(r5.returncode == 0, "step 5 exits 0", fails)
    ok("HYPOTHESIS REGISTER GATE" in out or "elimination" in out.lower() or "confirmed" in out.lower(),
       "elimination gate messaging", fails)
    s5 = load_state(state_path)
    ok(s5.get("last_completed_step", 0) < 5, "step 5 not completed on gate fail", fails)

    write_register(state_path.parent, 10, confirmed=True)
    r5b = run([sys.executable, str(ORCH), "--step", "5", "--state", str(state_path)])
    ok(r5b.returncode == 0, "step 5 pass exits 0", fails)
    ok("HYPOTHESIS REGISTER GATE" not in (r5b.stdout + r5b.stderr), "no gate on pass", fails)
    s5b = load_state(state_path)
    ok(s5b.get("last_completed_step") == 5, "step 5 marked complete on pass", fails)


def scenario_override_bypass(fails: list[int]) -> None:
    print("\n=== E2E: override bypasses gate + stderr audit ===")
    cleanup()
    run([sys.executable, str(ORCH), "--step", "1"])
    state_path = find_state()
    if state_path is None:
        ok(False, "state exists", fails)
        return
    s = load_state(state_path)
    s.setdefault("custom", {})["hypothesis_override_reason"] = "E2E user approved minimum"
    state_path.write_text(json.dumps(s), encoding="utf-8")
    write_register(state_path.parent, 3)
    r4 = run([sys.executable, str(ORCH), "--step", "4", "--state", str(state_path)])
    out = r4.stdout + r4.stderr
    ok(r4.returncode == 0, "step 4 with override", fails)
    ok("HYPOTHESIS REGISTER GATE" not in out, "no gate with override", fails)
    ok("hypothesis gate bypassed" in r4.stderr.lower(), "stderr audit for register bypass", fails)
    s4 = load_state(state_path)
    ok(s4.get("last_completed_step") == 4, "step 4 completes under override", fails)


def scenario_forge_cli(fails: list[int]) -> None:
    print("\n=== E2E: forge diagnose CLI (global entry) ===")
    cleanup()
    r = run(["forge", "diagnose", "--step", "1"])
    ok(r.returncode == 0, "forge diagnose --step 1", fails)
    ok("Define" in r.stdout or "Classify" in r.stdout or "diagnose" in r.stdout.lower(),
       "diagnose prompt rendered", fails)


def main() -> int:
    fails = [0]
    cleanup()
    print("Diagnose hypothesis gate — real-world E2E")
    print("=" * 60)
    scenario_gate_blocks_completion(fails)
    scenario_valid_register_passes(fails)
    scenario_elimination_gate(fails)
    scenario_override_bypass(fails)
    scenario_forge_cli(fails)
    cleanup()
    print("\n" + "=" * 60)
    if fails[0] == 0:
        print(f"{PASS} all E2E scenarios passed")
        return 0
    print(f"{FAIL} {fails[0]} scenario failure(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
