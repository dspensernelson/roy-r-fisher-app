"""A damaged file says so once, and is never touched.

Two behaviours are pinned here and they are easy to confuse. A file that is not
there means "nothing saved yet", which is ordinary and answers with nothing. A
file that is there and cannot be read is not ordinary, and it refuses.

Before Task 2 both answered the same way, and that was the defect: a truncated
settings file read exactly like a brand new machine, so the app asked Mark to
choose his jobs folder again and never suggested anything had been lost.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import appversion  # noqa: E402
import classify  # noqa: E402
import settings  # noqa: E402
import state  # noqa: E402
import usage  # noqa: E402
import workspace  # noqa: E402
from main import create_app  # noqa: E402

DAMAGED = "{not json at all"


# --- legacy files keep working ----------------------------------------------

def test_a_schemaless_workspace_file_still_reads(tmp_path):
    """Written before versioning existed. Not damaged, just version 0."""
    path = Path(workspace.settings_file())
    path.write_text(json.dumps({"jobs_folder": "/his/jobs"}), encoding="utf-8")
    assert workspace.saved_folder() == "/his/jobs"
    assert state.schema_of(state.read_json(path)) == state.LEGACY_SCHEMA


def test_a_schemaless_classification_store_still_reads(tmp_path):
    path = Path(classify.store_file())
    job = tmp_path / "JOB1"
    job.mkdir()
    path.write_text(json.dumps(
        {"jobs": {str(job.resolve()): {"Maps/plat.pdf": {"label": "Plat map"}}}}),
        encoding="utf-8")
    assert classify.for_job(job)["Maps/plat.pdf"]["label"] == "Plat map"


def test_reading_a_legacy_file_does_not_rewrite_it(tmp_path):
    """Opening the app may not change a file on disk. The stamp arrives with
    the next real save, not with a read."""
    path = Path(workspace.settings_file())
    path.write_text(json.dumps({"jobs_folder": "/his/jobs"}), encoding="utf-8")
    before = path.read_bytes()
    workspace.saved_folder()
    workspace.jobs_home()
    workspace.status()
    assert path.read_bytes() == before


def test_the_next_save_writes_the_current_shape(tmp_path):
    path = Path(workspace.settings_file())
    path.write_text(json.dumps({"jobs_folder": "/old", "keep": "me"}), encoding="utf-8")
    workspace.save_folder("/new")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["schema"] == state.CURRENT_SCHEMA
    assert data["jobs_folder"] == "/new"
    assert data["keep"] == "me"          # nothing else was dropped


def test_existing_key_file_formats_still_read():
    """Text, not JSON, and deliberately tolerant. A shell wrote it once."""
    path = Path(settings.key_file())
    for body in ('export ANTHROPIC_API_KEY="sk-ant-quoted"\n',
                 "   ANTHROPIC_API_KEY=sk-ant-indented\n",
                 "# a note\nANTHROPIC_API_KEY='sk-ant-single'\n"):
        path.write_text(body, encoding="utf-8")
        assert settings.stored_key().startswith("sk-ant-")


# --- round trips ------------------------------------------------------------

def test_valid_state_round_trips():
    workspace.save_folder("/his/jobs")
    assert workspace.saved_folder() == "/his/jobs"
    appversion.record("0.1.0", "2026-08-19T10:00:00")
    assert appversion.last_good() == "0.1.0"


# --- refusals ---------------------------------------------------------------

@pytest.mark.parametrize("reader", [
    lambda: workspace.saved_folder(),
    lambda: classify.for_job(Path("/tmp/nope")),
    lambda: appversion.last_good(),
    lambda: usage.runs(),
])
def test_malformed_state_refuses_rather_than_reading_as_empty(reader, tmp_path):
    for path in (workspace.settings_file(), classify.store_file(),
                 appversion.store_file(), usage.store_file()):
        Path(path).write_text(DAMAGED, encoding="utf-8")
    with pytest.raises(state.StateUnreadable):
        reader()


def test_a_malformed_file_is_left_byte_for_byte(tmp_path):
    path = Path(workspace.settings_file())
    path.write_text(DAMAGED, encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(state.StateUnreadable):
        workspace.saved_folder()
    assert path.read_bytes() == before
    assert path.is_file()                        # not renamed away either
    assert not list(path.parent.glob("*.writing"))


def test_a_future_schema_is_refused_not_guessed_at():
    """An older version reading a newer file must not truncate it, which is
    what guessing at an unknown shape would do after a rollback."""
    path = Path(workspace.settings_file())
    path.write_text(json.dumps({"schema": 99, "jobs_folder": "/x"}), encoding="utf-8")
    with pytest.raises(state.StateTooNew):
        workspace.saved_folder()


def test_a_json_document_that_is_not_an_object_is_refused():
    path = Path(workspace.settings_file())
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(state.StateUnreadable):
        workspace.saved_folder()


def test_an_absent_file_is_not_an_error():
    """The one case that legitimately answers with nothing."""
    assert not Path(workspace.settings_file()).exists()
    assert workspace.saved_folder() == ""
    assert workspace.jobs_home() is None
    assert appversion.last_good() == ""


# --- what reaches the screen ------------------------------------------------

def test_the_route_answers_with_the_approved_sentence_and_no_detail():
    Path(workspace.settings_file()).write_text(DAMAGED, encoding="utf-8")
    client = TestClient(create_app(), raise_server_exceptions=False)
    response = client.get("/api/workspace")

    assert response.status_code == 409
    # state_unreadable was added in Task 2.1 so the startup screen can tell
    # this apart from a busy 409 without matching the sentence, which would
    # mean keeping a second copy of it in JavaScript.
    assert response.json() == {"detail": state.RECOVERABLE_MESSAGE,
                               "state_unreadable": True}

    body = response.text
    assert "Traceback" not in body
    assert "json" not in body.lower()
    assert str(workspace.settings_file()) not in body


def test_the_approved_sentence_is_the_wording_spenser_agreed():
    assert state.RECOVERABLE_MESSAGE == (
        "The app's saved settings could not be read. "
        "The file was not changed. Contact Spenser before continuing.")
