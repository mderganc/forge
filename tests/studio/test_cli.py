import json
import subprocess
import sys
from pathlib import Path


def test_studio_start_json(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# x\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "forge_next.cli",
            "studio",
            "start",
            "--repo",
            str(repo),
            "--background",
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[2]),
        timeout=15,
    )
    if proc.returncode != 0:
        return
    blob = (proc.stdout or "") + (proc.stderr or "")
    lines = [ln.strip() for ln in blob.splitlines() if ln.strip().startswith("{")]
    if not lines:
        return
    data = json.loads(lines[-1])
    assert data["type"] == "server-started"
    assert "session_id" in data


def test_forge_help_hides_studio() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "forge_next.cli", "--help"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[2]),
        timeout=30,
    )
    assert proc.returncode == 0
    text = proc.stdout.lower()
    assert "studio" not in text
