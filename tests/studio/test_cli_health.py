import json
import subprocess
import sys
from pathlib import Path

from forge_next.studio.cli_commands import _resolve_foreground


class _Args:
    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_json_implies_background() -> None:
    args = _Args(json=True, foreground=False, background=False)
    assert _resolve_foreground(args) is False


def test_explicit_foreground_wins() -> None:
    args = _Args(json=True, foreground=True, background=False)
    assert _resolve_foreground(args) is True


def test_studio_start_json_reaches_api(tmp_path: Path) -> None:
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
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[2]),
        timeout=20,
    )
    assert proc.returncode == 0, proc.stderr
    lines = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip().startswith("{")]
    assert lines
    data = json.loads(lines[-1])
    assert data["type"] == "server-started"
    status = subprocess.run(
        [
            sys.executable,
            "-m",
            "forge_next.cli",
            "studio",
            "status",
            "--repo",
            str(repo),
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[2]),
        timeout=10,
    )
    assert status.returncode == 0
    st = json.loads(status.stdout.strip())
    assert st.get("server_ready") is True
    subprocess.run(
        [
            sys.executable,
            "-m",
            "forge_next.cli",
            "studio",
            "stop",
            "--repo",
            str(repo),
            "--json",
        ],
        check=False,
        timeout=10,
    )
