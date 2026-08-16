"""What Mark says a file is, remembered outside his folders.

A classification is something the app knows, not something in his job, so
it lives in the app's own file in his home folder. These tests pin that,
and pin the three things the app may say about a classified file: the
source is present, it changed, or it is gone.

Synthetic folders here prove these mechanics and nothing else.
"""
import json
import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import classify  # noqa: E402
from main import create_app  # noqa: E402


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_CLASSIFY_FILE", str(tmp_path / "marks-answers.json"))
    return tmp_path / "marks-answers.json"


def make_job(tmp_path, name="JOB1") -> Path:
    job = tmp_path / name
    (job / "Maps").mkdir(parents=True)
    (job / "Maps" / "plat.pdf").write_bytes(b"a plat")
    return job


def test_the_nine_approved_labels_and_nothing_else(store):
    assert classify.LABELS == (
        "Engagement letter",
        "Deed",
        "Assessor or tax record",
        "Subject photograph",
        "Plat map",
        "Neighborhood map",
        "Aerial photo",
        "Comparable sale document",
        "Valuation workbook",
    )


def test_a_label_outside_the_list_is_refused(store, tmp_path):
    job = make_job(tmp_path)
    with pytest.raises(ValueError):
        classify.set_label(job, "Maps/plat.pdf", "Building sketch")
    with pytest.raises(ValueError):
        classify.set_label(job, "Maps/plat.pdf", "whatever Mark typed")
    assert classify.for_job(job) == {}


def test_a_file_that_is_not_there_cannot_be_classified(store, tmp_path):
    job = make_job(tmp_path)
    with pytest.raises(LookupError):
        classify.set_label(job, "Maps/imaginary.pdf", "Plat map")


def test_a_classification_survives_a_restart(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    # Nothing cached: a fresh read of the file on disk, as the next start does.
    saved = classify.for_job(job)
    assert saved["Maps/plat.pdf"]["label"] == "Plat map"
    assert json.loads(store.read_text())["jobs"]


def test_the_record_lives_outside_the_job_folder(store, tmp_path):
    job = make_job(tmp_path)
    before = sorted(p.relative_to(job).as_posix() for p in job.rglob("*"))
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    after = sorted(p.relative_to(job).as_posix() for p in job.rglob("*"))
    assert before == after
    assert store.is_file()


def test_changing_a_label_replaces_it_rather_than_appending(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    classify.set_label(job, "Maps/plat.pdf", "Aerial photo")
    saved = classify.for_job(job)
    assert len(saved) == 1
    assert saved["Maps/plat.pdf"]["label"] == "Aerial photo"


def test_removing_one_record_leaves_the_others_alone(store, tmp_path):
    job = make_job(tmp_path)
    (job / "Maps" / "aerial.jpg").write_bytes(b"an aerial")
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    classify.set_label(job, "Maps/aerial.jpg", "Aerial photo")
    classify.remove_label(job, "Maps/plat.pdf")
    saved = classify.for_job(job)
    assert list(saved) == ["Maps/aerial.jpg"]


def test_two_jobs_keep_their_own_answers(store, tmp_path):
    one = make_job(tmp_path, "JOB1")
    two = make_job(tmp_path, "JOB2")
    classify.set_label(one, "Maps/plat.pdf", "Plat map")
    classify.set_label(two, "Maps/plat.pdf", "Aerial photo")
    assert classify.for_job(one)["Maps/plat.pdf"]["label"] == "Plat map"
    assert classify.for_job(two)["Maps/plat.pdf"]["label"] == "Aerial photo"
    classify.remove_label(one, "Maps/plat.pdf")
    assert classify.for_job(one) == {}
    assert classify.for_job(two)["Maps/plat.pdf"]["label"] == "Aerial photo"


def test_an_untouched_file_reads_present(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    assert classify.state_of(job, "Maps/plat.pdf") == "present"


def test_a_renamed_file_reads_missing_and_never_present(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    (job / "Maps" / "plat.pdf").rename(job / "Maps" / "plat final.pdf")
    assert classify.state_of(job, "Maps/plat.pdf") == "missing"
    # The record is kept, so Mark can still see it and clear it himself.
    assert classify.for_job(job)["Maps/plat.pdf"]["label"] == "Plat map"


def test_a_different_file_at_the_same_name_reads_changed(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    (job / "Maps" / "plat.pdf").write_bytes(b"a completely different document")
    assert classify.state_of(job, "Maps/plat.pdf") == "changed"


def test_a_record_can_be_removed_after_its_file_is_gone(store, tmp_path):
    job = make_job(tmp_path)
    classify.set_label(job, "Maps/plat.pdf", "Plat map")
    (job / "Maps" / "plat.pdf").unlink()
    classify.remove_label(job, "Maps/plat.pdf")
    assert classify.for_job(job) == {}


def test_a_failed_write_does_not_destroy_what_was_already_saved(store, tmp_path):
    job = make_job(tmp_path)
    (job / "Maps" / "aerial.jpg").write_bytes(b"an aerial")
    classify.set_label(job, "Maps/plat.pdf", "Plat map")

    def explode(*args, **kwargs):
        raise OSError("disk went away")

    # Its own context on purpose. Undoing the shared monkeypatch here would
    # also undo the fixture's RRF_CLASSIFY_FILE and point the next line at
    # the real store in the home folder.
    with pytest.MonkeyPatch.context() as broken:
        broken.setattr(classify.json, "dump", explode)
        with pytest.raises(OSError):
            classify.set_label(job, "Maps/aerial.jpg", "Aerial photo")

    saved = classify.for_job(job)
    assert saved["Maps/plat.pdf"]["label"] == "Plat map"
    assert "Maps/aerial.jpg" not in saved
    assert not list(store.parent.glob("*.writing"))


def test_an_unreadable_store_is_never_repaired_or_guessed_at(store, tmp_path):
    job = make_job(tmp_path)
    store.write_text("{ not json")
    assert classify.for_job(job) == {}


# --- The screen's side of it: the three routes ------------------------------

@pytest.fixture
def client(tmp_path, monkeypatch):
    """A real job under a real jobs home, with the store pointed somewhere
    safe. Returns the client and the job folder."""
    monkeypatch.setenv("RRF_CLASSIFY_FILE", str(tmp_path / "answers.json"))
    home = tmp_path / "home"
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    job = home / "JOB1"
    (job / "Maps").mkdir(parents=True)
    (job / "Photos").mkdir()
    (job / "Maps" / "plat.pdf").write_bytes(b"a plat")
    (job / "Site Visit").mkdir()
    (job / "Site Visit" / "notes.pdf").write_bytes(b"notes")
    (job / "Valuation.xlsm").write_bytes(b"PK")
    return TestClient(create_app()), job


def test_the_folders_route_shows_typical_other_and_loose_files(client):
    c, job = client
    body = c.get("/api/jobs/JOB1/folders").json()
    assert [r["folder"] for r in body["typical"]] == ["Maps", "Photos"]
    assert [r["folder"] for r in body["other"]] == ["Site Visit"]
    assert [f["name"] for f in body["root_files"]] == ["Valuation.xlsm"]
    assert body["missing_classifications"] == []


def test_an_unknown_job_is_a_404(client):
    c, _ = client
    assert c.get("/api/jobs/NOPE/folders").status_code == 404


def test_a_file_starts_unclassified_and_says_so(client):
    c, _ = client
    body = c.get("/api/jobs/JOB1/folders").json()
    maps = [r for r in body["typical"] if r["folder"] == "Maps"][0]
    assert maps["files"][0]["classification"] is None


def test_classifying_a_file_shows_beside_it_as_present(client):
    c, _ = client
    r = c.put("/api/jobs/JOB1/classification",
              json={"file": "Maps/plat.pdf", "label": "Plat map"})
    assert r.status_code == 200
    body = c.get("/api/jobs/JOB1/folders").json()
    maps = [x for x in body["typical"] if x["folder"] == "Maps"][0]
    assert maps["files"][0]["classification"] == {"label": "Plat map",
                                                  "state": "present"}


def test_a_loose_file_can_be_classified_too(client):
    c, _ = client
    r = c.put("/api/jobs/JOB1/classification",
              json={"file": "Valuation.xlsm", "label": "Valuation workbook"})
    assert r.status_code == 200
    body = c.get("/api/jobs/JOB1/folders").json()
    assert body["root_files"][0]["classification"]["label"] == "Valuation workbook"


def test_a_file_in_a_folder_the_app_did_not_expect_can_be_classified(client):
    c, _ = client
    r = c.put("/api/jobs/JOB1/classification",
              json={"file": "Site Visit/notes.pdf", "label": "Deed"})
    assert r.status_code == 200
    body = c.get("/api/jobs/JOB1/folders").json()
    other = body["other"][0]
    assert other["files"][0]["classification"]["label"] == "Deed"


def test_a_label_off_the_list_is_refused_by_the_route(client):
    c, _ = client
    r = c.put("/api/jobs/JOB1/classification",
              json={"file": "Maps/plat.pdf", "label": "Building sketch"})
    assert r.status_code == 400
    assert c.get("/api/jobs/JOB1/folders").json()["typical"][0]["files"][0][
        "classification"] is None


def test_a_file_the_app_has_not_observed_is_refused_by_the_route(client):
    c, _ = client
    r = c.put("/api/jobs/JOB1/classification",
              json={"file": "Maps/imaginary.pdf", "label": "Plat map"})
    assert r.status_code == 404


def test_changing_and_then_removing_a_classification(client):
    c, _ = client
    c.put("/api/jobs/JOB1/classification",
          json={"file": "Maps/plat.pdf", "label": "Plat map"})
    c.put("/api/jobs/JOB1/classification",
          json={"file": "Maps/plat.pdf", "label": "Neighborhood map"})
    maps = c.get("/api/jobs/JOB1/folders").json()["typical"][0]
    assert maps["files"][0]["classification"]["label"] == "Neighborhood map"

    r = c.request("DELETE", "/api/jobs/JOB1/classification",
                  json={"file": "Maps/plat.pdf"})
    assert r.status_code == 200
    maps = c.get("/api/jobs/JOB1/folders").json()["typical"][0]
    assert maps["files"][0]["classification"] is None


def test_a_changed_source_stops_reading_as_confirmed(client):
    c, job = client
    c.put("/api/jobs/JOB1/classification",
          json={"file": "Maps/plat.pdf", "label": "Plat map"})
    (job / "Maps" / "plat.pdf").write_bytes(b"a completely different document")
    maps = c.get("/api/jobs/JOB1/folders").json()["typical"][0]
    assert maps["files"][0]["classification"]["state"] == "changed"


def test_a_renamed_source_stays_visible_in_its_folder(client):
    """The record is never silently dropped just because the file moved."""
    c, job = client
    c.put("/api/jobs/JOB1/classification",
          json={"file": "Maps/plat.pdf", "label": "Plat map"})
    (job / "Maps" / "plat.pdf").rename(job / "Maps" / "plat final.pdf")
    maps = [r for r in c.get("/api/jobs/JOB1/folders").json()["typical"]
            if r["folder"] == "Maps"][0]
    gone = [f for f in maps["files"] if f["kind"] == "missing"]
    assert len(gone) == 1
    assert gone[0]["rel"] == "Maps/plat.pdf"
    assert gone[0]["classification"] == {"label": "Plat map", "state": "missing"}
    # The count is what was observed, so the vanished file is not counted.
    assert maps["count"] == 1


def test_a_record_whose_whole_folder_is_gone_is_still_reachable(client):
    c, job = client
    c.put("/api/jobs/JOB1/classification",
          json={"file": "Site Visit/notes.pdf", "label": "Deed"})
    shutil.rmtree(job / "Site Visit")
    body = c.get("/api/jobs/JOB1/folders").json()
    assert [r["folder"] for r in body["other"]] == []
    assert body["missing_classifications"] == [
        {"name": "notes.pdf", "rel": "Site Visit/notes.pdf", "within": "",
         "kind": "missing",
         "classification": {"label": "Deed", "state": "missing"}}]


def test_a_stale_record_can_be_cleared_after_its_file_is_gone(client):
    c, job = client
    c.put("/api/jobs/JOB1/classification",
          json={"file": "Site Visit/notes.pdf", "label": "Deed"})
    shutil.rmtree(job / "Site Visit")
    r = c.request("DELETE", "/api/jobs/JOB1/classification",
                  json={"file": "Site Visit/notes.pdf"})
    assert r.status_code == 200
    assert c.get("/api/jobs/JOB1/folders").json()["missing_classifications"] == []


def test_the_route_offers_the_nine_labels_and_no_others(client):
    c, _ = client
    assert c.get("/api/classifications").json()["labels"] == list(classify.LABELS)
