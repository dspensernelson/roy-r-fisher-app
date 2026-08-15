"""Walking folders, and choosing which of them are active.

Real folders in a temporary directory throughout. The 500-folder fixture is
here because nine demo folders prove nothing about the screen the appraiser will
actually meet.
"""
import json
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import browse  # noqa: E402
import workspace  # noqa: E402
from main import create_app  # noqa: E402


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_SETTINGS_FILE", str(tmp_path / "settings.json"))
    monkeypatch.delenv("RRF_JOBS_HOME", raising=False)
    jobs = tmp_path / "jobs"
    jobs.mkdir()
    return jobs


@pytest.fixture
def client(home):
    return TestClient(create_app())


# ------------------------------------------------------------- browsing ----
def test_it_lists_folders_and_never_files(tmp_path):
    (tmp_path / "A folder").mkdir()
    (tmp_path / "B folder").mkdir()
    (tmp_path / "a-document.docx").write_text("not somewhere to go")
    answer = browse.listing(str(tmp_path))
    assert [f["name"] for f in answer["folders"]] == ["A folder", "B folder"]
    assert answer["readable"] is True


def test_hidden_folders_are_left_out(tmp_path):
    (tmp_path / "Real").mkdir()
    (tmp_path / ".hidden").mkdir()
    assert [f["name"] for f in browse.listing(str(tmp_path))["folders"]] == ["Real"]


def test_an_empty_folder_is_readable_and_empty(tmp_path):
    inner = tmp_path / "empty"
    inner.mkdir()
    answer = browse.listing(str(inner))
    assert answer["readable"] is True
    assert answer["folders"] == []


def test_a_folder_it_cannot_open_says_so_rather_than_looking_empty(tmp_path):
    shut = tmp_path / "shut"
    shut.mkdir()
    shut.chmod(0o000)
    try:
        answer = browse.listing(str(shut))
        assert answer["readable"] is False
        assert answer["folders"] == []
        assert "will not let" in answer["message"]
    finally:
        shut.chmod(0o755)


def test_a_file_is_not_somewhere_to_go(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("x")
    answer = browse.listing(str(f))
    assert answer["readable"] is False
    assert answer["message"] == "That is not a folder."


def test_breadcrumbs_walk_back_up(tmp_path):
    deep = tmp_path / "one" / "two" / "three"
    deep.mkdir(parents=True)
    answer = browse.listing(str(deep))
    labels = [c["label"] for c in answer["breadcrumbs"]]
    assert labels[-3:] == ["one", "two", "three"]
    assert answer["parent"] == str(deep.parent)


def test_no_path_starts_where_he_lives():
    assert browse.listing("")["path"] == str(Path.home())


def test_a_symlink_reports_where_it_actually_goes(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    (real / "inside").mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    answer = browse.listing(str(link))
    assert answer["path"] == str(real.resolve())
    assert [f["name"] for f in answer["folders"]] == ["inside"]


def test_the_drive_list_is_asked_for_by_name(monkeypatch):
    monkeypatch.setattr(browse, "on_windows", lambda: True)
    monkeypatch.setattr(browse, "drives", lambda: ["C:\\", "D:\\"])
    answer = browse.listing(browse.DRIVES)
    assert answer["is_drive_list"] is True
    assert [f["name"] for f in answer["folders"]] == ["C:\\", "D:\\"]


def test_one_bad_drive_does_not_break_the_list(monkeypatch):
    """A card reader with nothing in it must not take the screen down."""
    real = {"C:\\"}

    class Fake:
        def __init__(self, p):
            self.p = p

        def is_dir(self):
            if self.p == "E:\\":
                raise OSError("device not ready")
            return self.p in real

    monkeypatch.setattr(browse, "Path", Fake)
    assert browse.drives() == ["C:\\"]


def test_going_up_from_a_drive_root_reaches_the_drive_list(monkeypatch, tmp_path):
    monkeypatch.setattr(browse, "on_windows", lambda: True)
    root = Path(tmp_path.anchor)
    assert browse.listing(str(root))["parent"] == browse.DRIVES


# --------------------------------------------------------- active jobs -----
def test_nothing_is_active_on_first_setup(client, home):
    for name in ["A job", "B job"]:
        (home / name).mkdir()
    client.put("/api/workspace", json={"path": str(home)})
    listed = client.get("/api/workspace/folders").json()
    assert listed["folders"] == ["A job", "B job"]
    assert listed["active"] == []
    assert client.get("/api/jobs").json() == []


def test_only_the_chosen_ones_show_on_the_jobs_screen(client, home):
    for name in ["A job", "B job", "C job"]:
        (home / name).mkdir()
    client.put("/api/workspace", json={"path": str(home)})
    client.put("/api/workspace/folders", json={"active": ["A job", "C job"]})
    assert [j["name"] for j in client.get("/api/jobs").json()] == ["A job", "C job"]


def test_a_selection_survives_a_restart(client, home):
    (home / "A job").mkdir()
    client.put("/api/workspace", json={"path": str(home)})
    client.put("/api/workspace/folders", json={"active": ["A job"]})

    fresh = TestClient(create_app())
    assert fresh.get("/api/workspace/folders").json()["active"] == ["A job"]
    assert [j["name"] for j in fresh.get("/api/jobs").json()] == ["A job"]


def test_unselecting_works(client, home):
    for name in ["A job", "B job"]:
        (home / name).mkdir()
    client.put("/api/workspace", json={"path": str(home)})
    client.put("/api/workspace/folders", json={"active": ["A job", "B job"]})
    client.put("/api/workspace/folders", json={"active": ["B job"]})
    assert [j["name"] for j in client.get("/api/jobs").json()] == ["B job"]


def test_a_newly_discovered_folder_starts_not_active(client, home):
    (home / "A job").mkdir()
    client.put("/api/workspace", json={"path": str(home)})
    client.put("/api/workspace/folders", json={"active": ["A job"]})

    (home / "Arrived later").mkdir()
    listed = client.get("/api/workspace/folders").json()
    assert "Arrived later" in listed["folders"]
    assert listed["active"] == ["A job"]
    assert [j["name"] for j in client.get("/api/jobs").json()] == ["A job"]


def test_a_folder_renamed_outside_the_app_is_reported_by_name(client, home):
    (home / "A job").mkdir()
    client.put("/api/workspace", json={"path": str(home)})
    client.put("/api/workspace/folders", json={"active": ["A job"]})

    (home / "A job").rename(home / "A job renamed")
    listed = client.get("/api/workspace/folders").json()
    assert listed["missing"] == ["A job"]
    assert "A job renamed" in listed["folders"]
    assert "A job renamed" not in listed["active"]      # never guessed at


def test_zero_active_is_allowed(client, home):
    (home / "A job").mkdir()
    client.put("/api/workspace", json={"path": str(home)})
    r = client.put("/api/workspace/folders", json={"active": []})
    assert r.status_code == 200
    assert client.get("/api/jobs").json() == []


def test_a_job_made_in_the_app_starts_active(client, home):
    client.put("/api/workspace", json={"path": str(home)})
    client.post("/api/jobs", json={"name": "DAVENPORT_1 Main - 2026"})
    assert [j["name"] for j in client.get("/api/jobs").json()] == ["DAVENPORT_1 Main - 2026"]


def test_making_a_job_not_active_never_touches_the_folder(client, home):
    job = home / "A job"
    (job / "Photos").mkdir(parents=True)
    (job / "Photos" / "a.jpg").write_bytes(b"a photo")
    client.put("/api/workspace", json={"path": str(home)})
    client.put("/api/workspace/folders", json={"active": ["A job"]})

    client.put("/api/workspace/folders", json={"active": []})

    assert job.is_dir()
    assert (job / "Photos" / "a.jpg").read_bytes() == b"a photo"


def test_two_parent_folders_keep_separate_selections(client, home, tmp_path):
    (home / "A job").mkdir()
    other = tmp_path / "other jobs"
    (other / "Z job").mkdir(parents=True)

    client.put("/api/workspace", json={"path": str(home)})
    client.put("/api/workspace/folders", json={"active": ["A job"]})
    client.put("/api/workspace", json={"path": str(other)})
    client.put("/api/workspace/folders", json={"active": ["Z job"]})

    client.put("/api/workspace", json={"path": str(home)})
    assert client.get("/api/workspace/folders").json()["active"] == ["A job"]


def test_no_folder_name_is_ever_parsed_or_rewritten(client, home):
    odd = "DAVENPORT_2840 Brady Street - 2026 Tax"
    (home / odd).mkdir()
    client.put("/api/workspace", json={"path": str(home)})
    client.put("/api/workspace/folders", json={"active": [odd]})
    assert client.get("/api/workspace/folders").json()["folders"] == [odd]
    assert [j["name"] for j in client.get("/api/jobs").json()] == [odd]
    assert json.loads(Path(workspace.settings_file()).read_text(
        encoding="utf-8"))["workspaces"][str(home.resolve())]["active"] == [odd]


# ------------------------------------------------- a burdened jobs folder ---
@pytest.fixture
def burdened(home):
    for i in range(500):
        (home / ("JOB %03d_%d Some Street - 2026" % (i, 100 + i))).mkdir()
    for i in range(20):
        (home / ("loose-%d.docx" % i)).write_text("not a job")
    return home


def test_five_hundred_folders_all_arrive_by_exact_name(client, burdened, capsys):
    client.put("/api/workspace", json={"path": str(burdened)})

    start = time.perf_counter()
    r = client.get("/api/workspace/folders")
    elapsed_ms = (time.perf_counter() - start) * 1000
    size = len(r.content)

    body = r.json()
    assert len(body["folders"]) == 500
    assert body["folders"][0] == "JOB 000_100 Some Street - 2026"
    assert body["folders"][-1] == "JOB 499_599 Some Street - 2026"
    assert body["active"] == []
    assert not any(name.endswith(".docx") for name in body["folders"])

    with capsys.disabled():
        print("\n  MEASURED, 500 folders: %.1f ms, %d bytes (%.1f KB)"
              % (elapsed_ms, size, size / 1024))


def test_selecting_some_of_five_hundred_saves_exactly_those(client, burdened):
    client.put("/api/workspace", json={"path": str(burdened)})
    chosen = ["JOB 007_107 Some Street - 2026", "JOB 300_400 Some Street - 2026"]
    client.put("/api/workspace/folders", json={"active": chosen})

    assert sorted(client.get("/api/workspace/folders").json()["active"]) == sorted(chosen)
    assert sorted(j["name"] for j in client.get("/api/jobs").json()) == sorted(chosen)


def test_reopening_manage_restores_the_saved_selections(client, burdened):
    client.put("/api/workspace", json={"path": str(burdened)})
    chosen = ["JOB 042_142 Some Street - 2026"]
    client.put("/api/workspace/folders", json={"active": chosen})

    fresh = TestClient(create_app())
    body = fresh.get("/api/workspace/folders").json()
    assert body["active"] == chosen
    assert len(body["folders"]) == 500


def test_an_exact_name_can_be_found_among_five_hundred(client, burdened):
    """Search filters the loaded names, so this is the data it filters."""
    body = client.put("/api/workspace", json={"path": str(burdened)}).json()
    assert body["folder_count"] == 500
    names = client.get("/api/workspace/folders").json()["folders"]
    hits = [n for n in names if "JOB 123" in n]
    assert hits == ["JOB 123_223 Some Street - 2026"]


# ------------------------------------------------- select all and clear all --
def test_select_all_is_every_folder_and_not_one_loose_file(client, burdened):
    """What Select all selects is exactly this list, which the screen already
    holds. Twenty loose .docx files sit beside them and none is offered."""
    client.put("/api/workspace", json={"path": str(burdened)})
    folders = client.get("/api/workspace/folders").json()["folders"]
    assert len(folders) == 500
    assert not any(name.endswith(".docx") for name in folders)

    client.put("/api/workspace/folders", json={"active": folders})
    saved = client.get("/api/workspace/folders").json()["active"]
    assert len(saved) == 500
    assert sorted(saved) == sorted(folders)
    assert len(client.get("/api/jobs").json()) == 500


def test_one_can_still_be_unselected_after_selecting_all(client, burdened):
    client.put("/api/workspace", json={"path": str(burdened)})
    folders = client.get("/api/workspace/folders").json()["folders"]
    dropped = "JOB 250_350 Some Street - 2026"

    client.put("/api/workspace/folders", json={"active": folders})
    client.put("/api/workspace/folders",
               json={"active": [n for n in folders if n != dropped]})

    saved = client.get("/api/workspace/folders").json()["active"]
    assert len(saved) == 499
    assert dropped not in saved
    assert dropped in client.get("/api/workspace/folders").json()["folders"]


def test_clear_all_saves_as_none_active(client, burdened):
    client.put("/api/workspace", json={"path": str(burdened)})
    folders = client.get("/api/workspace/folders").json()["folders"]
    client.put("/api/workspace/folders", json={"active": folders})
    assert len(client.get("/api/jobs").json()) == 500

    client.put("/api/workspace/folders", json={"active": []})
    assert client.get("/api/workspace/folders").json()["active"] == []
    assert client.get("/api/jobs").json() == []


def test_nothing_is_saved_until_it_is_sent(client, burdened):
    """The bulk controls change the screen only. Until Use these active jobs
    is pressed the app has been told nothing, so what is stored is unchanged."""
    client.put("/api/workspace", json={"path": str(burdened)})
    client.put("/api/workspace/folders", json={"active": ["JOB 001_101 Some Street - 2026"]})

    # reading the list, however many times, never changes what is saved
    for _ in range(3):
        client.get("/api/workspace/folders")
    assert client.get("/api/workspace/folders").json()["active"] == [
        "JOB 001_101 Some Street - 2026"]


def test_saving_and_reopening_restores_the_selection_exactly(client, burdened):
    client.put("/api/workspace", json={"path": str(burdened)})
    folders = client.get("/api/workspace/folders").json()["folders"]
    client.put("/api/workspace/folders", json={"active": folders})

    reopened = TestClient(create_app()).get("/api/workspace/folders").json()
    assert sorted(reopened["active"]) == sorted(folders)
    assert len(reopened["folders"]) == 500
    assert reopened["missing"] == []


def test_no_folder_is_touched_by_any_of_it(client, burdened):
    before = sorted(p.name for p in burdened.iterdir())
    client.put("/api/workspace", json={"path": str(burdened)})
    folders = client.get("/api/workspace/folders").json()["folders"]
    client.put("/api/workspace/folders", json={"active": folders})
    client.put("/api/workspace/folders", json={"active": []})
    assert sorted(p.name for p in burdened.iterdir()) == before


# The three things above happen in the browser, before anything is sent. There
# is no JavaScript test runner here, so these read the screen's own source.
# They prove the wiring, not the pixels: how it looks is checked by eye.
SCREEN = Path(__file__).resolve().parents[1] / "web" / "src" / "screens" / "ActiveJobs.jsx"


def test_select_all_ignores_the_search_filter():
    """`shown` is the filtered list. Select all must not use it, or a button
    reading 'Select all 500 jobs' would select the three being searched."""
    source = SCREEN.read_text()
    line = next(l for l in source.splitlines() if "const selectAll" in l)
    assert "data.folders" in line
    assert "shown" not in line


def test_neither_bulk_control_saves_anything():
    source = SCREEN.read_text()
    for name in ("const selectAll", "const clearAll"):
        line = next(l for l in source.splitlines() if name in l)
        assert "putWorkspaceFolders" not in line
        assert "setChosen" in line


def test_the_bulk_controls_go_dim_when_they_would_do_nothing():
    source = SCREEN.read_text()
    assert "disabled={chosen.size === data.folders.length" in source
    assert "disabled={chosen.size === 0}" in source
