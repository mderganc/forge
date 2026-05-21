from pathlib import Path

from forge_next.studio import events as studio_events


def test_append_and_read_events(tmp_path: Path) -> None:
    state = tmp_path / "state"
    studio_events.append_event(state, {"type": "click", "gate": "gate1_hmw", "choice": "a"})
    evs, cur = studio_events.read_events_since_cursor(state)
    assert len(evs) == 1
    assert evs[0]["choice"] == "a"
    evs2, _ = studio_events.read_events_since_cursor(state)
    assert evs2 == []
    studio_events.set_cursor(state, 0)
    evs3, _ = studio_events.read_events_since_cursor(state)
    assert len(evs3) == 1


def test_clear_events(tmp_path: Path) -> None:
    state = tmp_path / "state"
    studio_events.append_event(state, {"type": "click", "choice": "x"})
    studio_events.clear_events(state)
    assert studio_events.read_events_since_cursor(state)[0] == []
