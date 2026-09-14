"""She presses one button and the log reaches Spenser. What that costs, proved.

The goal the owner approved on 2026-09-14: she presses one button and the last
two days of log reach his email. She never picks a file, finds a folder, or
attaches anything.

Two things are proved here. The screen can show her exactly what would leave
her computer before it leaves, and the old folder-window behaviour is gone
rather than sitting beside the new one. A second way to do the same thing is
what caused the original fault: a control that revealed one of two files.
"""
import datetime
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from main import create_app  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
WEB = REPO / "app" / "web" / "src"


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def log_path(tmp_path, monkeypatch):
    path = tmp_path / ".rrf-app.log"
    monkeypatch.setenv("RRF_LOG_FILE", str(path))
    return path


def stamp(when) -> str:
    return when.isoformat(timespec="seconds")


def recent_line(message, minutes_ago=5) -> str:
    when = datetime.datetime.now() - datetime.timedelta(minutes=minutes_ago)
    return "%s %s\n" % (stamp(when), message)


# --- seeing it before sending it --------------------------------------------
def test_recent_answers_with_the_text_that_would_be_sent(client, log_path):
    log_path.write_text(recent_line("something worth reading"))
    response = client.get("/api/log/recent")

    assert response.status_code == 200
    body = response.json()
    assert "something worth reading" in body["text"]
    assert body["lines"] >= 1
    assert body["empty"] is False


def test_recent_reads_both_halves_which_is_the_whole_point(client, log_path):
    rotated = log_path.with_name(log_path.name + ".1")
    rotated.write_text(recent_line("the fault, in the rotated half", 180))
    log_path.write_text(recent_line("after the rotation", 5))

    body = client.get("/api/log/recent").json()
    assert "the fault, in the rotated half" in body["text"]
    assert "after the rotation" in body["text"]


def test_recent_names_the_running_version(client, log_path):
    import packaging
    log_path.write_text(recent_line("anything at all"))
    body = client.get("/api/log/recent").json()
    assert packaging.version_of(REPO) in body["text"]


def test_recent_on_a_machine_with_no_log_is_not_an_error(client, log_path):
    response = client.get("/api/log/recent")
    assert response.status_code == 200
    assert response.json()["empty"] is True


# --- the old way is gone ----------------------------------------------------
def test_the_folder_window_route_is_gone(client, log_path):
    """It does not stay beside the new view. A second way to do this is what
    caused the fault: one control that revealed one of two files."""
    log_path.write_text(recent_line("anything at all"))
    assert client.post("/api/log/show").status_code in (404, 405)


def test_the_route_is_not_registered_at_all():
    """Not merely refused. The old path is off the app's route table, so it
    cannot come back by somebody re-registering half of it."""
    paths = {getattr(route, "path", "") for route in create_app().routes}
    assert "/api/log/show" not in paths
    assert "/api/log/recent" in paths


def test_nothing_in_the_screens_still_calls_the_folder_window_route():
    api_js = (WEB / "api.js").read_text(encoding="utf-8")
    assert "showTheLog" not in api_js
    assert '"/api/log/show"' not in api_js
    for path in sorted((WEB / "screens").glob("*.jsx")):
        assert "showTheLog" not in path.read_text(encoding="utf-8"), path


def test_the_settings_screen_offers_the_new_words_and_not_the_old(client):
    source = (WEB / "screens" / "Settings.jsx").read_text(encoding="utf-8")
    assert "Show what will be sent" in source
    assert "Show the log" not in source
