"""An empty folder can be chosen, but only as a deliberate answer.

The first version of this check refused every empty folder, which made a real
thing impossible: pointing the app at a brand new jobs folder before the first
job exists. That was recorded as a conflict rather than decided, and this is
the decision. Approved 2026-08-22.

The shape matters. It is a second, differently-worded button, not the same
press repeated, so it can never be reached by clicking through a refusal. And
it is offered only where it is true: the top of the disk, the home folder and a
single job folder stay refused however deliberate he is, because none of them
becomes a jobs folder by being insisted upon.
"""
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import jobs as jobs_module  # noqa: E402
import workspace  # noqa: E402
from main import create_app  # noqa: E402

WEB = Path(__file__).resolve().parents[1] / "web" / "src"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_SETTINGS_FILE", str(tmp_path / "settings.json"))
    monkeypatch.delenv("RRF_JOBS_HOME", raising=False)
    return TestClient(create_app(), raise_server_exceptions=False)


def make_job(parent: Path, name: str) -> Path:
    job = parent / name
    for folder in jobs_module.MARK_FOLDERS:
        (job / folder).mkdir(parents=True)
    return job


def choose(client, path, accept_empty=False):
    answer = client.put("/api/workspace",
                        json={"path": str(path), "accept_empty": accept_empty})
    return answer.status_code, answer.json().get("detail", "")


# --- the empty folder, refused then accepted ------------------------------
def test_an_empty_folder_is_refused_by_the_ordinary_press(client, tmp_path):
    fresh = tmp_path / "RRF Jobs"
    fresh.mkdir()
    code, detail = choose(client, fresh)
    assert code == 400
    assert "nothing in this folder yet" in detail.lower()
    assert "new jobs folder" in detail.lower(), "the refusal names the way forward"


def test_the_deliberate_press_accepts_it(client, tmp_path):
    fresh = tmp_path / "RRF Jobs"
    fresh.mkdir()
    code, _ = choose(client, fresh, accept_empty=True)
    assert code == 200
    assert client.get("/api/workspace").json()["path"] == str(fresh)


def test_an_empty_folder_gives_an_empty_jobs_list_not_an_error(client, tmp_path):
    fresh = tmp_path / "RRF Jobs"
    fresh.mkdir()
    choose(client, fresh, accept_empty=True)
    assert client.get("/api/jobs").json() == []
    assert client.get("/api/workspace/folders").json()["folders"] == []


def test_a_job_made_afterwards_appears(client, tmp_path):
    """The whole point of allowing it: the first job can now be made."""
    fresh = tmp_path / "RRF Jobs"
    fresh.mkdir()
    choose(client, fresh, accept_empty=True)
    client.post("/api/jobs", json={"name": "DAVENPORT_1 Main Street - 2026"})
    assert [j["name"] for j in client.get("/api/jobs").json()] == \
        ["DAVENPORT_1 Main Street - 2026"]


# --- the three that stay refused however deliberate ------------------------
def test_the_filesystem_root_is_refused_even_deliberately(client):
    code, detail = choose(client, Path("/"), accept_empty=True)
    assert code == 400
    assert "top of the disk" in detail.lower()


def test_the_home_folder_is_refused_even_deliberately(client):
    code, detail = choose(client, Path.home(), accept_empty=True)
    assert code == 400
    assert "home folder" in detail.lower()


def test_a_single_job_folder_is_refused_even_deliberately(client, tmp_path):
    job = make_job(tmp_path, "ANYTOWN_100 Example Avenue - 2026")
    code, detail = choose(client, job, accept_empty=True)
    assert code == 400
    assert "one job" in detail.lower()


def test_an_empty_job_folder_is_still_a_job_not_a_new_jobs_folder(client, tmp_path):
    """Named in the house style with nothing in it yet."""
    job = tmp_path / "DAVENPORT_100 Brady Street - 2026"
    job.mkdir()
    code, detail = choose(client, job, accept_empty=True)
    assert code == 400
    assert "one job" in detail.lower()


def test_a_folder_of_other_things_is_still_refused(client, tmp_path):
    """Not empty and holding no jobs. The deliberate press does not apply."""
    place = tmp_path / "Downloads"
    (place / "invoices").mkdir(parents=True)
    code, detail = choose(client, place, accept_empty=True)
    assert code == 400
    assert "no jobs were found" in detail.lower()


def test_nothing_is_saved_by_any_refusal(client, tmp_path):
    place = tmp_path / "Downloads"
    (place / "invoices").mkdir(parents=True)
    choose(client, place, accept_empty=True)
    assert client.get("/api/workspace").json()["chosen"] is False


# --- what the screen is told ----------------------------------------------
def test_the_screen_is_told_which_folder_it_is_looking_at(client, tmp_path):
    fresh = tmp_path / "RRF Jobs"
    fresh.mkdir()
    body = client.get("/api/browse", params={"path": str(fresh)}).json()
    assert body["is_root"] is False and body["is_home"] is False
    assert body["is_job"] is False and body["folders"] == []

    root = client.get("/api/browse", params={"path": "/"}).json()
    assert root["is_root"] is True

    home = client.get("/api/browse", params={"path": str(Path.home())}).json()
    assert home["is_home"] is True

    job = make_job(tmp_path, "ANYTOWN_200 Example Avenue - 2026")
    inside = client.get("/api/browse", params={"path": str(job)}).json()
    assert inside["is_job"] is True


def test_the_second_button_is_its_own_press_with_its_own_words():
    screen = (WEB / "screens" / "ChooseFolder.jsx").read_text()
    assert "Use as new jobs folder" in screen
    assert "use(true)" in screen and "use(false)" in screen


def test_the_second_button_is_not_offered_where_it_could_never_work():
    screen = (WEB / "screens" / "ChooseFolder.jsx").read_text()
    assert "loc.is_root || loc.is_home || loc.is_job" in screen
    assert "!neverAllowed" in screen
