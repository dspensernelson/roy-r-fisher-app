"""A folder has to hold jobs before it can be confirmed as the jobs folder.

The audit walked the opening screen and found `Use this folder` live at every
level, including the drive root and inside a single job. Three different wrong
turns, each one click from an app with nothing in it and no explanation, in the
first ninety seconds with Spenser on the call.

The rule: the app decides by looking, never by where the user is standing. A
folder is one of his jobs when its name is in the firm's house style, or when
it carries at least two of Mark's own eight folders. Two rather than one
because `Documents` on a Mac often contains something called `Photos`, and one
signal would make the home folder look like it held a job.

The two-step setup itself is unchanged and deliberate: choose the folder, then
say which jobs are live. Nothing is auto-activated.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import jobs  # noqa: E402
import workspace  # noqa: E402
from main import create_app  # noqa: E402

WEB = Path(__file__).resolve().parents[1] / "web" / "src"


def make_job(parent: Path, name: str) -> Path:
    """A job the way the app itself creates one: Mark's eight folders."""
    job = parent / name
    for folder in jobs.MARK_FOLDERS:
        (job / folder).mkdir(parents=True)
    return job


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_SETTINGS_FILE", str(tmp_path / "settings.json"))
    return TestClient(create_app(), raise_server_exceptions=False)


def choose(client, path) -> "tuple[int, str]":
    answer = client.put("/api/workspace", json={"path": str(path)})
    return answer.status_code, answer.json().get("detail", "")


# --- what counts as a job -------------------------------------------------
def test_a_folder_of_marks_own_folders_is_a_job(tmp_path):
    assert workspace.looks_like_job(make_job(tmp_path, "somewhere"))


def test_the_house_name_alone_is_enough(tmp_path):
    """A job made outside the app, before any folder exists inside it."""
    empty = tmp_path / "DAVENPORT_2840 Brady Street - 2026 Tax"
    empty.mkdir()
    assert workspace.looks_like_job(empty)


def test_one_lookalike_folder_is_not_a_job(tmp_path):
    """`Documents` holding a `Photos` folder must not read as a job."""
    documents = tmp_path / "Documents"
    (documents / "Photos").mkdir(parents=True)
    assert not workspace.looks_like_job(documents)


def test_the_mac_library_folder_is_not_a_job(tmp_path):
    """Found by looking at the real screen, not by thinking about it.

    `~/Library` on a Mac holds both `Maps` and `Photos`. With the threshold at
    two it was reported as a job, so the home folder said `1 job found` and
    offered to be confirmed as the jobs folder.
    """
    library = tmp_path / "Library"
    (library / "Maps").mkdir(parents=True)
    (library / "Photos").mkdir()
    (library / "Caches").mkdir()
    assert not workspace.looks_like_job(library)


def test_a_half_built_job_is_still_recognised_by_its_name(tmp_path):
    """Raising the threshold must not cost a real job made by hand."""
    job = tmp_path / "DAVENPORT_100 Brady Street - 2026"
    (job / "Photos").mkdir(parents=True)
    assert workspace.looks_like_job(job)


def test_an_ordinary_folder_is_not_a_job(tmp_path):
    plain = tmp_path / "Downloads"
    plain.mkdir()
    assert not workspace.looks_like_job(plain)


# --- the four ways of choosing the wrong folder ---------------------------
def test_an_empty_folder_is_refused(client, tmp_path):
    empty = tmp_path / "nothing"
    empty.mkdir()
    code, detail = choose(client, empty)
    assert code == 400
    assert "no folders in here" in detail.lower()
    assert "go up a level" in detail.lower()


def test_a_folder_with_no_jobs_is_refused(client, tmp_path):
    home = tmp_path / "home"
    (home / "Desktop").mkdir(parents=True)
    (home / "Downloads").mkdir()
    code, detail = choose(client, home)
    assert code == 400
    assert "no jobs were found" in detail.lower()


def test_a_single_job_folder_is_refused_and_says_so(client, tmp_path):
    """Standing inside one job, the refusal names that exact mistake."""
    job = make_job(tmp_path, "ANYTOWN_100 Example Avenue - 2026")
    code, detail = choose(client, job)
    assert code == 400
    assert "one job" in detail.lower()
    assert "up one level" in detail.lower()


def test_the_drive_root_is_refused(client):
    code, detail = choose(client, Path("/"))
    assert code == 400
    assert detail


def test_nothing_is_saved_when_the_folder_is_refused(client, tmp_path):
    empty = tmp_path / "nothing"
    empty.mkdir()
    choose(client, empty)
    assert client.get("/api/workspace").json()["chosen"] is False


# --- the folder that does hold jobs ---------------------------------------
def test_a_real_jobs_folder_is_accepted(client, tmp_path):
    root = tmp_path / "RRF Jobs"
    make_job(root, "ANYTOWN_100 Example Avenue - 2026")
    make_job(root, "ANYTOWN_200 Example Avenue - 2026")
    code, _ = choose(client, root)
    assert code == 200
    assert client.get("/api/workspace").json()["path"] == str(root)


def test_the_screen_is_told_how_many_jobs_are_here(client, tmp_path):
    root = tmp_path / "RRF Jobs"
    make_job(root, "ANYTOWN_100 Example Avenue - 2026")
    make_job(root, "ANYTOWN_200 Example Avenue - 2026")
    (root / "Old paperwork").mkdir()
    body = client.get("/api/browse", params={"path": str(root)}).json()
    assert body["job_count"] == 2
    marked = {f["name"]: f["is_job"] for f in body["folders"]}
    assert marked["ANYTOWN_100 Example Avenue - 2026"] is True
    assert marked["Old paperwork"] is False


def test_the_count_is_zero_inside_a_single_job(client, tmp_path):
    job = make_job(tmp_path, "ANYTOWN_100 Example Avenue - 2026")
    body = client.get("/api/browse", params={"path": str(job)}).json()
    assert body["job_count"] == 0, "Mark's own folders are not themselves jobs"


# --- the screens ----------------------------------------------------------
def test_the_confirm_button_is_off_until_jobs_are_found():
    screen = (WEB / "screens" / "ChooseFolder.jsx").read_text()
    assert "const canUse = jobsHere > 0" in screen
    assert "disabled={!canUse || !!busy}" in screen
    assert "jobs found" in screen


def test_the_confirm_button_sits_with_the_result_not_at_the_far_edge():
    """It used to live in title-actions, at the opposite corner from the list."""
    screen = (WEB / "screens" / "ChooseFolder.jsx").read_text()
    block = screen[screen.index('className={`folder-result'):]
    block = block[:block.index("</div>", block.index("Use this folder"))]
    assert "folder-result-count" in block and "Use this folder" in block
    actions = screen[screen.index('<div className="title-row">'):screen.index("</div>")]
    assert "Use this folder" not in actions


def test_the_screen_says_whether_to_open_a_folder_or_stop_here():
    screen = (WEB / "screens" / "ChooseFolder.jsx").read_text()
    assert "Stop here and choose it." in screen
    assert "Open one of the folders below to keep looking." in screen


def test_folder_rows_are_named_for_a_screen_reader():
    screen = (WEB / "screens" / "ChooseFolder.jsx").read_text()
    assert "aria-label={f.is_job ?" in screen
    assert 'aria-label="Up one folder"' in screen
    # the icon is decoration and must not be read out as content
    assert 'className="picker-icon" aria-hidden="true"' in screen


def test_active_jobs_cannot_be_confirmed_with_nothing_picked():
    screen = (WEB / "screens" / "ActiveJobs.jsx").read_text()
    assert "disabled={!!busy || chosen.size === 0}" in screen
    assert "Pick at least one job" in screen


def test_active_jobs_still_starts_with_nothing_chosen_and_keeps_its_tools():
    screen = (WEB / "screens" / "ActiveJobs.jsx").read_text()
    assert "setChosen(new Set(r.active))" in screen, "the saved answer, not everything"
    assert "Select all" in screen and "Clear all" in screen
    assert 'type="search"' in screen, "search is preserved"
