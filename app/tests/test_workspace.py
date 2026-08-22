"""Where the jobs folder is remembered, and how it gets chosen.

Real temporary folders throughout, nothing stood in for. Choosing a folder
is done in the app's own page now, so there is no operating-system window
here for a test to be unable to click.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import workspace  # noqa: E402
from main import create_app  # noqa: E402

# Every character that has bitten a path in this project: spaces, quotes a
# shell would eat, a dollar sign, a backtick that a sourced file would run,
# an ampersand, an apostrophe, and a letter outside ASCII.
HOSTILE = 'RRF "Demo" $HOME `whoami` & O\u2019Brien Jobs \u00e9'


@pytest.fixture
def clean(tmp_path, monkeypatch):
    """A settings file of our own, and no override in the environment."""
    monkeypatch.setenv("RRF_SETTINGS_FILE", str(tmp_path / "settings.json"))
    monkeypatch.delenv("RRF_JOBS_HOME", raising=False)
    return tmp_path


@pytest.fixture
def client(clean):
    return TestClient(create_app())


def make_jobs_folder(root: Path, names, loose=()) -> Path:
    """A jobs folder holding real-looking jobs.

    Each child carries Mark's own eight folders, because a bare empty folder
    is no longer accepted as a job and a folder holding none of them is no
    longer accepted as the jobs folder.
    """
    import jobs as jobs_module
    folder = root / "jobs"
    folder.mkdir()
    for name in names:
        for inner in jobs_module.MARK_FOLDERS:
            (folder / name / inner).mkdir(parents=True)
    for name in loose:
        (folder / name).write_text("not a job")
    return folder


# --------------------------------------------------------- remembering it ---
def test_nothing_chosen_means_nothing_chosen(clean):
    assert workspace.jobs_home() is None
    status = workspace.status()
    assert status["chosen"] is False
    assert status["valid"] is False
    assert status["path"] == ""


def test_no_invented_default_folder(clean):
    """The old code answered Documents/RRF Jobs whether or not it existed."""
    assert workspace.saved_folder() == ""
    assert workspace.jobs_home() is None


def test_a_saved_folder_is_used(clean):
    folder = make_jobs_folder(clean, ["DAVENPORT_1 Main - 2026"])
    workspace.save_folder(str(folder))
    assert workspace.jobs_home() == folder


def test_env_override_beats_the_saved_folder(clean, monkeypatch):
    saved = make_jobs_folder(clean, [])
    workspace.save_folder(str(saved))
    other = clean / "other"
    other.mkdir()
    monkeypatch.setenv("RRF_JOBS_HOME", str(other))
    assert workspace.jobs_home() == other
    assert workspace.status()["source"] == "override"


def test_a_hostile_path_survives_being_saved_and_read_back(clean):
    folder = clean / HOSTILE
    folder.mkdir()
    workspace.save_folder(str(folder))
    assert workspace.saved_folder() == str(folder)
    assert workspace.jobs_home() == folder
    # and nothing in the file on disk was run, quoted away or re-encoded
    raw = Path(workspace.settings_file()).read_text(encoding="utf-8")
    assert json.loads(raw)["jobs_folder"] == str(folder)


def test_a_windows_shaped_path_survives(clean):
    windows = r"C:\Users\Mark\Documents\RRF Jobs\O'Brien & Co $x"
    workspace.save_folder(windows)
    assert workspace.saved_folder() == windows


def test_saving_the_folder_leaves_other_settings_alone(clean):
    path = Path(workspace.settings_file())
    path.write_text(json.dumps({"something_else": "keep me"}), encoding="utf-8")
    workspace.save_folder("/somewhere")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["something_else"] == "keep me"
    assert data["jobs_folder"] == "/somewhere"


def test_an_unreadable_settings_file_is_refused_and_left_alone(clean):
    """Changed in Task 2, deliberately. This used to assert that a damaged
    settings file read as no settings at all, which is the same answer a brand
    new machine gives. A truncated file therefore showed Mark the first-run
    screen and let him believe the app had forgotten his jobs folder. Now it
    refuses, says so once, and does not touch the file."""
    import state
    path = Path(workspace.settings_file())
    damaged = "{not json at all"
    path.write_text(damaged, encoding="utf-8")

    with pytest.raises(state.StateUnreadable):
        workspace.saved_folder()
    with pytest.raises(state.StateUnreadable):
        workspace.jobs_home()

    # Never repaired, renamed, or deleted.
    assert path.read_text(encoding="utf-8") == damaged


# ------------------------------------------------------- looking at it ------
def test_it_counts_only_immediate_child_folders(clean):
    folder = make_jobs_folder(clean, ["A job", "B job"], loose=["notes.txt", "sheet.xlsx"])
    (folder / "A job" / "Photos").mkdir(exist_ok=True)   # nested, must not count
    facts = workspace.describe(folder)
    assert facts["folder_count"] == 2
    assert facts["folder_names"] == ["A job", "B job"]
    assert facts["loose_file_count"] == 2


def test_it_reports_folder_names_exactly_as_they_are_on_disk(clean):
    names = ["DAVENPORT_2840 Brady Street - 2026 Tax", "MUSCATINE_910 Grandview Avenue ROW"]
    folder = make_jobs_folder(clean, names)
    assert workspace.describe(folder)["folder_names"] == sorted(names)


def test_hidden_entries_are_not_jobs(clean):
    folder = make_jobs_folder(clean, ["Real job"])
    (folder / ".hidden").mkdir()
    (folder / ".DS_Store").write_text("noise")
    facts = workspace.describe(folder)
    assert facts["folder_count"] == 1
    assert facts["loose_file_count"] == 0


def test_a_folder_with_no_folders_says_so(clean):
    folder = make_jobs_folder(clean, [], loose=["just-a-file.docx"])
    facts = workspace.describe(folder)
    assert facts["exists"] and facts["is_folder"]
    assert facts["folder_count"] == 0
    assert facts["folder_names"] == []


def test_a_folder_that_is_gone(clean):
    facts = workspace.describe(clean / "never-existed")
    assert facts["exists"] is False
    assert facts["folder_count"] == 0


def test_a_file_is_not_a_folder(clean):
    f = clean / "a-file.txt"
    f.write_text("x")
    facts = workspace.describe(f)
    assert facts["exists"] is True
    assert facts["is_folder"] is False


def test_a_saved_folder_that_was_deleted_is_chosen_but_not_valid(clean):
    import shutil
    folder = make_jobs_folder(clean, ["One"])
    workspace.save_folder(str(folder))
    shutil.rmtree(folder)
    status = workspace.status()
    assert status["chosen"] is True
    assert status["valid"] is False
    assert status["path"] == str(folder)


# ------------------------------------------------------------- saving it ----
def test_confirming_saves_it_and_the_app_uses_it_at_once(client, clean, monkeypatch):
    folder = make_jobs_folder(clean, ["DAVENPORT_7719 Northwest Boulevard - 2026"])
    r = client.put("/api/workspace", json={"path": str(folder)})
    assert r.status_code == 200
    assert r.json()["valid"] is True

    # no restart: once marked active, the same running app lists them
    client.put("/api/workspace/folders",
               json={"active": ["DAVENPORT_7719 Northwest Boulevard - 2026"]})
    listed = client.get("/api/jobs").json()
    assert [j["name"] for j in listed] == ["DAVENPORT_7719 Northwest Boulevard - 2026"]


def test_a_saved_choice_survives_a_restart(client, clean):
    folder = make_jobs_folder(clean, ["One", "Two"])
    client.put("/api/workspace", json={"path": str(folder)})

    client.put("/api/workspace/folders", json={"active": ["One", "Two"]})

    fresh = TestClient(create_app())          # a brand new app, as after a restart
    assert fresh.get("/api/workspace").json()["path"] == str(folder)
    assert len(fresh.get("/api/jobs").json()) == 2      # active choices survive too


def test_a_hostile_path_can_be_saved_and_used(client, clean):
    folder = clean / HOSTILE
    folder.mkdir()
    (folder / "MOLINE_3400 41st Avenue Drive - Rent Study").mkdir()
    assert client.put("/api/workspace", json={"path": str(folder)}).status_code == 200
    client.put("/api/workspace/folders",
               json={"active": ["MOLINE_3400 41st Avenue Drive - Rent Study"]})
    listed = client.get("/api/jobs").json()
    assert [j["name"] for j in listed] == ["MOLINE_3400 41st Avenue Drive - Rent Study"]


def test_confirming_a_folder_that_vanished_is_refused(client, clean):
    gone = clean / "gone"
    r = client.put("/api/workspace", json={"path": str(gone)})
    assert r.status_code == 400
    assert "not there any more" in r.json()["detail"]
    assert workspace.saved_folder() == ""


def test_confirming_a_file_is_refused(client, clean):
    f = clean / "a-file.txt"
    f.write_text("x")
    r = client.put("/api/workspace", json={"path": str(f)})
    assert r.status_code == 400
    assert workspace.saved_folder() == ""


def test_confirming_nothing_is_refused(client, clean):
    assert client.put("/api/workspace", json={"path": "   "}).status_code == 400


def test_an_empty_folder_is_refused_and_says_why(client, clean):
    """Approved 2026-08-22, and a reversal of what this file used to hold.

    It used to accept an empty folder on the grounds that he might be setting
    up before any job exists. The audit found the cost of that: `Use this
    folder` was live everywhere, so the drive root and his home folder were
    accepted in exactly the same silent way, and the first thing he met was an
    app with nothing in it and no explanation. Refusing names the mistake.

    The case this gives up is real and is recorded as a conflict for Spenser:
    a genuinely empty new jobs folder can no longer be chosen, so the app can
    no longer be pointed at one before the first job exists.
    """
    folder = make_jobs_folder(clean, [])
    r = client.put("/api/workspace", json={"path": str(folder)})
    assert r.status_code == 400
    assert "no folders in here" in r.json()["detail"].lower()
    assert client.get("/api/workspace").json()["chosen"] is False


# ------------------------------------------- before anything is chosen ------
def test_the_jobs_list_is_empty_rather_than_broken(client, clean):
    assert client.get("/api/jobs").json() == []


def test_making_a_job_with_nowhere_to_put_it_is_refused(client, clean):
    r = client.post("/api/jobs", json={"name": "DAVENPORT_1 Main - 2026"})
    assert r.status_code == 400
    assert "No jobs folder chosen" in r.json()["detail"]


def test_opening_a_job_with_nowhere_to_look_is_refused(client, clean):
    assert client.get("/api/jobs/anything").status_code == 400


def test_photo_routes_refuse_rather_than_crash(client, clean):
    assert client.get("/api/jobs/anything/manifest").status_code == 400
