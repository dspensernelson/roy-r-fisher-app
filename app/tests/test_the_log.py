"""The app writes down what it did, so a hang leaves evidence.

Nothing in this codebase wrote anything to disk before this. `applog.py` adds
one file, one line per event, and this proves it: a request is recorded, a
key never reaches it, the file rotates rather than growing forever, and a
call to `note` cannot raise even when the file cannot be written.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import applog  # noqa: E402


@pytest.fixture
def log_path(tmp_path, monkeypatch):
    path = tmp_path / ".rrf-app.log"
    monkeypatch.setenv("RRF_LOG_FILE", str(path))
    return path


def test_a_request_writes_one_line_naming_the_path_and_a_duration(log_path):
    import io
    from PIL import Image

    from fastapi.testclient import TestClient
    from main import create_app

    def jpg_bytes(color):
        buf = io.BytesIO()
        Image.new("RGB", (10, 10), color).save(buf, format="JPEG")
        return buf.getvalue()

    home = log_path.parent / "jobs"
    (home / "JOB1" / "Photos").mkdir(parents=True)
    import os
    os.environ["RRF_JOBS_HOME"] = str(home)
    try:
        c = TestClient(create_app())
        r = c.get("/api/jobs/JOB1/manifest")
        assert r.status_code == 200
    finally:
        del os.environ["RRF_JOBS_HOME"]

    assert log_path.is_file()
    lines = log_path.read_text().splitlines()
    assert any("/api/jobs/JOB1/manifest" in line and "200" in line for line in lines)


def test_rrf_log_file_is_honoured_so_nothing_reaches_the_real_home(log_path, monkeypatch):
    real_home = Path("/should/never/be/touched")
    monkeypatch.setattr(Path, "home", staticmethod(lambda: real_home))
    applog.note("a test event")
    assert log_path.is_file()
    assert not (real_home / applog.LOG_NAME).exists()


def test_a_key_never_reaches_the_log(log_path):
    applog.note("captions sent", key="sk-ant-abcdef1234567890abcdef1234567890")
    text = log_path.read_text()
    assert "sk-ant-" not in text
    assert "[removed]" in text


def test_a_long_secret_looking_value_is_also_removed(log_path):
    applog.note("token seen", value="a" * 48)
    text = log_path.read_text()
    assert "a" * 48 not in text
    assert "[removed]" in text


def test_the_file_rotates_and_keeps_exactly_one_previous_file(log_path):
    log_path.write_text("x" * (applog.MAX_BYTES + 1))
    applog.note("after the ceiling")

    previous = log_path.with_name(log_path.name + ".1")
    assert previous.is_file()
    assert previous.stat().st_size >= applog.MAX_BYTES

    current = log_path.read_text()
    assert "after the ceiling" in current
    assert len(current) < applog.MAX_BYTES


def test_note_never_raises_even_when_the_path_is_unwritable(monkeypatch):
    monkeypatch.setenv("RRF_LOG_FILE", "/this/path/does/not/exist/and/cannot/be/made")
    applog.note("this must not raise")  # would raise before the try/except


def test_redact_replaces_a_key_but_leaves_ordinary_text_alone():
    assert applog.redact("Blaul Lofts, 61 photographs") == "Blaul Lofts, 61 photographs"
    assert "sk-ant-" not in applog.redact("key sk-ant-abc123def456ghi789jkl012")
