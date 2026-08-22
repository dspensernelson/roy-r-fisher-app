"""The startup screen tells the truth about which failure happened.

Two failures reach the same place and they mean opposite things. A damaged
settings file is on disk and the server is fine; an unreachable server is the
other way round. Before Task 2.1 both showed "Could not reach the app's
server. Close this tab and start the app again.", which for the damaged file
was wrong twice over: it named the wrong cause, and it sent Mark round a
restart loop that cannot fix a file.

What this file proves and what it does not. The API half is proved properly,
by calling the route. The screen half is read from its own source, because
there is no JavaScript test runner in this project, which is the same thing
test_caption_toggle_structure.py does and says. So these pin the branch and
the two sentences; they do not render React. How it actually looks is checked
by eye on the real app, and was.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import state  # noqa: E402
import workspace  # noqa: E402
from main import create_app  # noqa: E402

WEB = Path(__file__).resolve().parents[1] / "web" / "src"
APP_JSX = WEB / "App.jsx"
API_JS = WEB / "api.js"

CANNOT_REACH = ("Could not reach the app's server. "
                "Close this tab and start the app again.")
DAMAGED = "{not json at all"


@pytest.fixture
def client():
    return TestClient(create_app(), raise_server_exceptions=False)


# --- the API half, proved by calling it -------------------------------------

def test_damaged_state_answers_409_with_the_flag_and_the_sentence(client):
    Path(workspace.settings_file()).write_text(DAMAGED, encoding="utf-8")
    response = client.get("/api/workspace")

    assert response.status_code == 409
    assert response.json() == {"detail": state.RECOVERABLE_MESSAGE,
                               "state_unreadable": True}


def test_the_answer_carries_no_internals(client):
    Path(workspace.settings_file()).write_text(DAMAGED, encoding="utf-8")
    body = client.get("/api/workspace").text

    assert "Traceback" not in body
    assert str(workspace.settings_file()) not in body
    assert DAMAGED not in body
    for parser_word in ("Expecting", "line 1 column", "JSONDecode", "json"):
        assert parser_word not in body


def test_a_healthy_workspace_is_unaffected(client):
    workspace.save_folder(str(Path(workspace.settings_file()).parent))
    response = client.get("/api/workspace")
    assert response.status_code == 200
    assert "state_unreadable" not in response.json()


def test_reading_the_damaged_file_never_changes_it(client):
    path = Path(workspace.settings_file())
    path.write_text(DAMAGED, encoding="utf-8")
    before = path.read_bytes()

    client.get("/api/workspace")
    client.get("/api/workspace")

    assert path.read_bytes() == before
    assert path.is_file()
    assert not list(path.parent.glob("*.writing"))


def test_no_repair_route_was_added(client):
    """Task 2.1 explains the problem. It does not fix the file, and there is
    no button that would."""
    paths = {r.path for r in create_app().routes}
    for invented in ("/api/state/repair", "/api/settings/repair",
                     "/api/state/reset", "/api/workspace/repair"):
        assert invented not in paths


# --- the screen half, read from its own source ------------------------------

@pytest.fixture
def app_source() -> str:
    return APP_JSX.read_text(encoding="utf-8")


@pytest.fixture
def api_source() -> str:
    return API_JS.read_text(encoding="utf-8")


def test_the_helper_attaches_status_and_the_flag_and_nothing_else(api_source):
    assert "err.status = res.status;" in api_source
    assert "err.stateUnreadable = body.state_unreadable === true;" in api_source
    # The whole body must not be carried through, or a future caller could put
    # server internals on a screen without meaning to.
    assert "err.body" not in api_source
    assert "Object.assign(err" not in api_source


def test_the_helper_still_gives_existing_callers_their_message(api_source):
    """Every other screen reads e.message. That behaviour is unchanged."""
    assert "new Error(body.detail || res.statusText)" in api_source


def test_the_screen_shows_the_server_sentence_only_for_the_flagged_409(app_source):
    branch = app_source[app_source.index("getWorkspace().then("):]
    branch = branch[:branch.index("getDemo()")]

    assert "e.status === 409" in branch
    assert "e.stateUnreadable" in branch
    assert "e.message" in branch
    assert "CANNOT_REACH" in branch


def test_the_generic_message_is_unchanged_and_is_the_fallback(app_source):
    assert 'const CANNOT_REACH = "%s";' % CANNOT_REACH in app_source
    branch = app_source[app_source.index("getWorkspace().then("):]
    branch = branch[:branch.index("getDemo()")]
    # the flagged case first, the generic message as the else
    assert branch.index("e.stateUnreadable") < branch.index("CANNOT_REACH")


def test_the_screen_does_not_show_every_server_message(app_source):
    """The defect this must not become: a rule that prints whatever the
    backend said onto the startup screen."""
    branch = app_source[app_source.index("getWorkspace().then("):]
    branch = branch[:branch.index("getDemo()")]
    assert ".catch((e) => setWsError(e.message))" not in branch
    assert "setWsError(e.message)" not in branch.replace(
        "e.stateUnreadable && e.message ? e.message : CANNOT_REACH", "")


def test_the_approved_sentence_is_not_copied_into_javascript(app_source, api_source):
    """It lives in state.RECOVERABLE_MESSAGE and is shown from the response.
    A second copy here is exactly how a value drifts and then quietly lies."""
    for source in (app_source, api_source):
        assert "could not be read" not in source
        assert "Contact Spenser" not in source


def test_the_loading_state_still_behaves_as_before(app_source):
    assert 'if (!ws) return (<>{masthead}<div className="frame"><p className="sub">Loading...</p></div></>);' \
        in app_source
    # the error branch still comes first, so a failure is never shown as loading
    assert app_source.index("if (wsError) return") < app_source.index("if (!ws) return")


def test_the_error_still_renders_inside_the_masthead_frame(app_source):
    assert 'if (wsError) return (<>{masthead}<div className="frame"><div className="error">{wsError}</div></div></>);' \
        in app_source


def test_no_other_screen_changed():
    """The correction is the startup path only. Nothing else learned to parse
    responses on its own."""
    for name in ("Settings.jsx", "JobHome.jsx", "SectionPicker.jsx",
                 "JobsPortal.jsx", "PhotosScreen.jsx", "ChooseFolder.jsx",
                 "ActiveJobs.jsx", "NewJob.jsx"):
        text = (WEB / "screens" / name).read_text(encoding="utf-8")
        assert "stateUnreadable" not in text, name
        assert "state_unreadable" not in text, name


def test_no_new_screen_modal_or_recovery_button_was_added(app_source):
    for invented in ("repairState", "Repair", "Delete settings",
                     "Start over", "recoveryModal"):
        assert invented not in app_source


# --- isolation ---------------------------------------------------------------

def test_these_tests_never_touch_the_real_home():
    """The autouse fixture in conftest points all six state paths at a
    temporary box. If that ever regresses, this says so here rather than in
    Spenser's home folder."""
    box = Path(workspace.settings_file()).parent
    assert box != Path.home()
    assert "pytest" in str(box) or "tmp" in str(box).lower()
