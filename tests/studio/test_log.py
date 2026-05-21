from pathlib import Path

from forge_next.studio import log as studio_log


def test_format_probe_batch() -> None:
    md = studio_log.format_event_markdown(
        {
            "ts": 1779210040,
            "type": "probes-submit",
            "gate": "gate1_hmw",
            "responses": [
                {
                    "probe_id": "visual_controls",
                    "prompt": "Color ok?",
                    "text": "Yes, use radios",
                }
            ],
        }
    )
    assert "visual_controls" in md
    assert "Yes, use radios" in md
    assert "gate1_hmw" in md


def test_append_studio_log(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    studio_log.ensure_studio_log_header(repo, session_id="sess-1", workflow="develop")
    studio_log.append_studio_log(
        repo,
        {"ts": 1, "type": "click", "gate": "g1", "choice": "a", "label": "A"},
    )
    text = studio_log.read_studio_log(repo)
    assert "sess-1" in text
    assert "**Selection:** A" in text
