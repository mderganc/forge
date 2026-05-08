from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    # Ensure consistent encoding on Windows.
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.run(
        argv,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_forge_launcher_can_run_against_foreign_repo(tmp_path: Path) -> None:
    """Smoke test: run `forge` launcher against a repo without vendored scripts."""
    foreign = tmp_path / "foreign-repo"
    foreign.mkdir(parents=True, exist_ok=True)

    # Minimal repo marker for repo-root detection.
    (foreign / "README.md").write_text("# Foreign Repo\n", encoding="utf-8")

    # Run `forge status` against it: should not crash and should print the repo path.
    cmd = [
        sys.executable,
        "-c",
        "from forge_codex.cli import main; main(['status','--repo',r'" + str(foreign) + "'])",
    ]
    res = _run(cmd, cwd=foreign)
    assert res.returncode == 0, res.stderr
    # Avoid Unicode punctuation in asserts; Windows console encodings vary.
    assert "forge" in res.stdout.lower()
    assert "status" in res.stdout.lower()

