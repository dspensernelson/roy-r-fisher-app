import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
from main import create_app  # noqa: E402
import settings  # noqa: E402

FAKE = "sk-ant-test-000000000000000000000000000000000WXYZ"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_KEY_FILE", str(tmp_path / "key.env"))
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path / "jobs"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return TestClient(create_app())


def test_starts_with_no_key_and_says_so(client):
    body = client.get("/api/settings").json()
    assert body["key_set"] is False
    assert body["ends_with"] == ""


def test_saving_a_key_turns_the_features_on_without_a_restart(client):
    with patch.object(settings, "check_key", lambda k: None):
        r = client.put("/api/settings/key", json={"key": FAKE})
    assert r.status_code == 200
    # Set in this running process too, so nothing has to be restarted.
    assert os.environ["ANTHROPIC_API_KEY"] == FAKE
    body = client.get("/api/settings").json()
    assert body["key_set"] is True


def test_no_route_ever_hands_the_key_back(client):
    with patch.object(settings, "check_key", lambda k: None):
        put = client.put("/api/settings/key", json={"key": FAKE}).text
    got = client.get("/api/settings").text
    for text in (put, got):
        assert FAKE not in text
        assert "000000" not in text          # not even a chunk of it
    assert client.get("/api/settings").json()["ends_with"] == "WXYZ"   # last four only


def test_the_key_lands_in_a_file_only_the_owner_can_read(client, tmp_path):
    with patch.object(settings, "check_key", lambda k: None):
        client.put("/api/settings/key", json={"key": FAKE})
    written = tmp_path / "key.env"
    assert written.is_file()
    assert f"ANTHROPIC_API_KEY={FAKE}" in written.read_text()
    if os.name != "nt":                       # Windows has no POSIX mode bits
        assert oct(written.stat().st_mode & 0o777) == "0o600"


def test_the_key_file_lives_outside_the_project(monkeypatch):
    """It must never sit anywhere git could pick it up."""
    monkeypatch.delenv("RRF_KEY_FILE", raising=False)
    where = settings.key_file()
    assert where.parent == Path.home()
    repo = Path(__file__).resolve().parents[2]
    assert repo not in where.parents


def test_a_key_the_service_rejects_is_not_saved(client, tmp_path):
    def refuse(key):
        raise settings.BadKey("that key was not accepted")

    with patch.object(settings, "check_key", refuse):
        r = client.put("/api/settings/key", json={"key": "sk-ant-wrong"})
    assert r.status_code == 400
    assert not (tmp_path / "key.env").exists()
    assert "ANTHROPIC_API_KEY" not in os.environ


def test_a_service_that_cannot_be_reached_still_saves_but_says_so(client):
    def offline(key):
        raise OSError("no network")

    with patch.object(settings, "check_key", offline):
        body = client.put("/api/settings/key", json={"key": FAKE}).json()
    assert body["key_set"] is True
    assert body["checked"] is False
    assert "could not" in body["message"].lower()


def test_a_blank_key_is_refused(client):
    assert client.put("/api/settings/key", json={"key": "   "}).status_code == 400


def test_removing_the_key_clears_the_file_and_this_process(client, tmp_path):
    with patch.object(settings, "check_key", lambda k: None):
        client.put("/api/settings/key", json={"key": FAKE})
    assert client.delete("/api/settings/key").status_code == 200
    assert os.environ.get("ANTHROPIC_API_KEY", "") == ""
    assert client.get("/api/settings").json()["key_set"] is False
    text = (tmp_path / "key.env").read_text() if (tmp_path / "key.env").exists() else ""
    assert FAKE not in text


def test_other_settings_in_the_file_survive_a_key_change(client, tmp_path):
    """The file is shared with the launcher and may hold other lines. Rewriting
    the key must not wipe something a human put there by hand."""
    (tmp_path / "key.env").write_text("RRF_JOBS_HOME=/somewhere/else\nANTHROPIC_API_KEY=old\n")
    with patch.object(settings, "check_key", lambda k: None):
        client.put("/api/settings/key", json={"key": FAKE})
    text = (tmp_path / "key.env").read_text()
    assert "RRF_JOBS_HOME=/somewhere/else" in text
    assert "old" not in text


def test_save_key_replaces_an_export_form_line(tmp_path, monkeypatch):
    key_file = tmp_path / "key.env"
    key_file.write_text("export ANTHROPIC_API_KEY=OLDKEY\n")
    monkeypatch.setenv("RRF_KEY_FILE", str(key_file))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    settings.save_key("NEWKEY")
    # Simulate the next start: the live env var save_key sets is gone.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert settings.stored_key() == "NEWKEY"
    assert "OLDKEY" not in key_file.read_text()


def test_remove_key_removes_an_export_form_line(tmp_path, monkeypatch):
    key_file = tmp_path / "key.env"
    key_file.write_text("export ANTHROPIC_API_KEY=OLDKEY\nOTHER=keep me\n")
    monkeypatch.setenv("RRF_KEY_FILE", str(key_file))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    settings.remove_key()
    assert settings.stored_key() == ""
    assert "OTHER=keep me" in key_file.read_text()
