"""The report is the photographs Mark picked, and nothing else.

His office keeps every shoot twice and names the folders differently every
job, so the app asks him once which folder holds the report photographs and
remembers the answer. Anything else in the job can still be pulled in one at a
time by classifying it a subject photograph on the job screen.

Two rules run through every test here.

Nothing he has typed is destroyed. A caption on a photograph that is currently
outside the chosen folder stays on disk, and comes back with the photograph if
he classifies it in. The choice is a view of his photographs, never a deletion.

Nothing falls back silently. If the folder he chose is gone, because the office
renamed it, the app says so and asks again. It never quietly picks a different
folder and builds a report out of photographs he did not choose.
"""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import classify  # noqa: E402
import jobfacts  # noqa: E402
import jobs  # noqa: E402
import photos  # noqa: E402

SUBJECT = "Subject photograph"


def a_photo(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (120, 90), (60, 110, 160)).save(path)
    return path


def a_job(tmp_path: Path, *relative_paths: str) -> Path:
    job = tmp_path / "DAVENPORT_1 Test Street"
    (job / "Photos").mkdir(parents=True, exist_ok=True)
    for rel in relative_paths:
        a_photo(job / "Photos" / rel)
    return job


def maquoketa(tmp_path: Path) -> Path:
    """The real shape: one loose aerial, sixteen raw, sixteen prepared."""
    paths = ["AERIAL.png"]
    paths += ["Raw pics_X/IMG_%04d.jpeg" % n for n in range(559, 575)]
    paths += ["Report Photos_X/%d IMG_%04d.jpeg" % (n - 558, n)
              for n in range(559, 575)]
    return a_job(tmp_path, *paths)


def files(job: Path):
    return [e["file"] for e in photos.load_manifest(job)["photos"]]


def fingerprint(folder: Path) -> dict:
    found = {}
    for path in sorted(Path(folder).rglob("*")):
        if path.is_file():
            found[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return found


# --- nothing changes for a job that has one place for photographs ---------
def test_photographs_loose_in_photos_are_all_the_report(tmp_path):
    """Five of the eleven real jobs, and every job the app makes itself. No
    question is ever asked and nothing behaves differently."""
    job = a_job(tmp_path, "a.jpg", "b.jpg", "c.jpg")
    assert sorted(files(job)) == ["a.jpg", "b.jpg", "c.jpg"]


def test_one_subfolder_and_nothing_else_is_all_the_report(tmp_path):
    job = a_job(tmp_path, "Raw pics_X/a.jpeg", "Raw pics_X/b.jpeg")
    assert sorted(files(job)) == ["a.jpeg", "b.jpeg"]


def test_with_no_answer_recorded_nothing_is_taken_away(tmp_path):
    """Until he answers, the app behaves exactly as it did. The screen asks
    the question; the manifest does not start hiding photographs on its own."""
    job = maquoketa(tmp_path)
    assert len(files(job)) == 33


# --- the answer decides ---------------------------------------------------
def test_his_answer_decides_what_is_in_the_report(tmp_path):
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    picked = files(job)
    assert len(picked) == 16
    assert all(name.endswith(".jpeg") for name in picked)
    assert "AERIAL.png" not in picked


def test_he_can_choose_the_top_of_photos(tmp_path):
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "")
    assert files(job) == ["AERIAL.png"]


def test_choosing_the_other_folder_gives_the_other_set(tmp_path):
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Raw pics_X")
    picked = files(job)
    assert len(picked) == 16
    assert all(name.startswith("IMG_") for name in picked)


def test_the_answer_can_be_changed(tmp_path):
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Raw pics_X")
    jobfacts.save_photo_folder(job, "Report Photos_X")
    assert all(f[0].isdigit() for f in files(job))


def test_a_nested_answer_works(tmp_path):
    """Mason City: the chosen folder is two levels down and its sibling holds
    the ones he threw out."""
    job = a_job(tmp_path,
                "Raw pics_W/All report photos used/good.jpeg",
                "Raw pics_W/Do Not Use/bad.jpeg")
    jobfacts.save_photo_folder(job, "Raw pics_W/All report photos used")
    assert files(job) == ["good.jpeg"]


# --- the folder he chose is gone ------------------------------------------
def test_a_chosen_folder_that_is_gone_is_reported_not_replaced(tmp_path):
    """The office renames the folder. The app must say so, never quietly build
    a report out of photographs he did not choose."""
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    (job / "Photos" / "Report Photos_X").rename(job / "Photos" / "Final Photos")
    manifest = photos.load_manifest(job)
    assert manifest["photo_folder_missing"] is True
    assert manifest["photos"] == []


def test_a_present_chosen_folder_is_not_reported_missing(tmp_path):
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    assert photos.load_manifest(job)["photo_folder_missing"] is False


def test_an_unanswered_job_is_not_reported_missing(tmp_path):
    job = maquoketa(tmp_path)
    manifest = photos.load_manifest(job)
    assert manifest["photo_folder_missing"] is False
    assert manifest["photo_folder"] is None


# --- the straggler, classified in from the left ---------------------------
def _classify(job: Path, rel: str, label: str = SUBJECT):
    classify.set_label(job, rel, label)


def test_a_classified_photograph_joins_the_report(tmp_path):
    """The one that never got copied across. He finds it on the left, says it
    is a subject photograph, and it appears on the right."""
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    _classify(job, "Photos/Raw pics_X/IMG_0559.jpeg")
    picked = files(job)
    assert len(picked) == 17
    assert "IMG_0559.jpeg" in picked


def test_removing_the_classification_takes_it_off_the_report(tmp_path):
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    _classify(job, "Photos/Raw pics_X/IMG_0559.jpeg")
    classify.remove_label(job, "Photos/Raw pics_X/IMG_0559.jpeg")
    assert len(files(job)) == 16


def test_another_label_does_not_put_a_file_in_the_report(tmp_path):
    """Only Subject photograph moves anything across. A plat map does not."""
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    _classify(job, "Photos/Raw pics_X/IMG_0559.jpeg", "Plat map")
    assert len(files(job)) == 16


def test_a_classified_photograph_appears_only_once(tmp_path):
    """Classifying one that is already in the chosen folder is not an error
    and does not double it."""
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    _classify(job, "Photos/Report Photos_X/1 IMG_0559.jpeg")
    assert len(files(job)) == 16


def test_a_classified_photograph_reaches_a_job_with_no_answer(tmp_path):
    """With no answer recorded everything is in already, so this changes
    nothing and must not crash or duplicate."""
    job = maquoketa(tmp_path)
    _classify(job, "Photos/Raw pics_X/IMG_0559.jpeg")
    assert len(files(job)) == 33


# --- his typing is never destroyed ----------------------------------------
def test_a_caption_outside_the_chosen_folder_survives_on_disk(tmp_path):
    job = maquoketa(tmp_path)
    manifest = photos.load_manifest(job)
    for entry in manifest["photos"]:
        if entry["file"] == "IMG_0559.jpeg":
            entry["caption"] = "West elevation from Generac Drive"
    photos.save_manifest(job, manifest)

    jobfacts.save_photo_folder(job, "Report Photos_X")
    assert "IMG_0559.jpeg" not in files(job)

    on_disk = json.loads(photos.manifest_path(job).read_text())
    kept = [e for e in on_disk["photos"] if e["file"] == "IMG_0559.jpeg"]
    assert kept and kept[0]["caption"] == "West elevation from Generac Drive"


def test_a_caption_comes_back_with_the_photograph(tmp_path):
    job = maquoketa(tmp_path)
    manifest = photos.load_manifest(job)
    for entry in manifest["photos"]:
        if entry["file"] == "IMG_0559.jpeg":
            entry["caption"] = "West elevation"
    photos.save_manifest(job, manifest)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    _classify(job, "Photos/Raw pics_X/IMG_0559.jpeg")

    back = [e for e in photos.load_manifest(job)["photos"]
            if e["file"] == "IMG_0559.jpeg"]
    assert back and back[0]["caption"] == "West elevation"


def test_saving_the_report_set_does_not_drop_the_rest(tmp_path):
    """The screen only ever holds the report photographs, so what it sends
    back is only those. The file must keep everything else."""
    job = maquoketa(tmp_path)
    manifest = photos.load_manifest(job)
    for entry in manifest["photos"]:
        if entry["file"] == "IMG_0559.jpeg":
            entry["caption"] = "West elevation"
    photos.save_manifest(job, manifest)

    jobfacts.save_photo_folder(job, "Report Photos_X")
    shown = photos.load_manifest(job)
    assert len(shown["photos"]) == 16
    photos.save_manifest(job, shown)

    on_disk = json.loads(photos.manifest_path(job).read_text())
    names = {e["file"] for e in on_disk["photos"]}
    assert len(names) == 33
    kept = [e for e in on_disk["photos"] if e["file"] == "IMG_0559.jpeg"]
    assert kept[0]["caption"] == "West elevation"


# --- cut, review and build all act on the chosen set ----------------------
def test_review_progress_counts_only_the_report(tmp_path):
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    manifest = photos.load_manifest(job)
    assert photos.review_progress(manifest)["included"] == 16


def test_cutting_still_works_inside_the_chosen_set(tmp_path):
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    photos.save_manifest(job, photos.load_manifest(job))
    photos._set_cut(job, "1 IMG_0559.jpeg", True)
    manifest = photos.load_manifest(job)
    assert len(photos.included(manifest)) == 15
    assert len(manifest["photos"]) == 16


def test_the_built_document_holds_only_the_chosen_photographs(tmp_path):
    """The engine reads the manifest file off disk, so the answer has to reach
    the document and not only the screen."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
    from docx import Document
    from photo_pages import build_photo_docx

    shipped = Path(__file__).resolve().parents[1] / "templates" / "Photo.docx"
    job = maquoketa(tmp_path)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    manifest = photos.load_manifest(job)
    for entry in manifest["photos"]:
        entry["caption"] = "A caption"
    photos.save_manifest(job, manifest)

    out = build_photo_docx(photos.manifest_path(job), shipped,
                           entries=photos.included(photos.load_manifest(job)))
    assert len(Document(str(out)).inline_shapes) == 16


def test_the_engine_still_reads_the_file_when_it_is_given_nothing(tmp_path):
    """The command line entry point passes no entries and must not change."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
    from docx import Document
    from photo_pages import build_photo_docx

    shipped = Path(__file__).resolve().parents[1] / "templates" / "Photo.docx"
    job = a_job(tmp_path, "a.jpg", "b.jpg")
    manifest = photos.load_manifest(job)
    for entry in manifest["photos"]:
        entry["caption"] = "A caption"
    photos.save_manifest(job, manifest)
    out = build_photo_docx(photos.manifest_path(job), shipped)
    assert len(Document(str(out)).inline_shapes) == 2


# --- nothing of Mark's is written -----------------------------------------
def test_choosing_and_reading_writes_nothing_into_his_folders(tmp_path):
    job = maquoketa(tmp_path)
    before = fingerprint(job)
    jobfacts.save_photo_folder(job, "Report Photos_X")
    photos.load_manifest(job)
    photos.photo_groups(job)
    _classify(job, "Photos/Raw pics_X/IMG_0559.jpeg")
    photos.load_manifest(job)
    assert fingerprint(job) == before


# --- the routes -----------------------------------------------------------
def _client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import main
    monkeypatch.setenv("RRF_JOBS_HOME", str(tmp_path))
    return TestClient(main.create_app())


def test_the_route_asks_when_there_is_more_than_one_place(tmp_path, monkeypatch):
    maquoketa(tmp_path)
    client = _client(tmp_path, monkeypatch)
    body = client.get("/api/jobs/DAVENPORT_1 Test Street/photo-groups").json()
    assert body["needs_choice"] is True
    assert [g["count"] for g in body["groups"]] == [16, 16, 1]


def test_the_route_never_asks_when_there_is_one_place(tmp_path, monkeypatch):
    a_job(tmp_path, "a.jpg", "b.jpg")
    client = _client(tmp_path, monkeypatch)
    body = client.get("/api/jobs/DAVENPORT_1 Test Street/photo-groups").json()
    assert body["needs_choice"] is False


def test_the_route_stops_asking_once_he_has_answered(tmp_path, monkeypatch):
    maquoketa(tmp_path)
    client = _client(tmp_path, monkeypatch)
    url = "/api/jobs/DAVENPORT_1 Test Street/photo-group"
    assert client.put(url, json={"folder": "Report Photos_X"}).status_code == 200
    body = client.get("/api/jobs/DAVENPORT_1 Test Street/photo-groups").json()
    assert body["needs_choice"] is False
    assert body["chosen"] == "Report Photos_X"


def test_a_folder_with_no_photographs_in_it_is_refused(tmp_path, monkeypatch):
    """No answer may be recorded for a place the app has not just looked at."""
    maquoketa(tmp_path)
    client = _client(tmp_path, monkeypatch)
    url = "/api/jobs/DAVENPORT_1 Test Street/photo-group"
    assert client.put(url, json={"folder": "Somewhere Else"}).status_code == 400
    assert client.put(url, json={"folder": "../.."}).status_code == 400


def test_the_route_reports_a_folder_that_has_gone(tmp_path, monkeypatch):
    job = maquoketa(tmp_path)
    client = _client(tmp_path, monkeypatch)
    client.put("/api/jobs/DAVENPORT_1 Test Street/photo-group",
               json={"folder": "Report Photos_X"})
    (job / "Photos" / "Report Photos_X").rename(job / "Photos" / "Final Photos")
    body = client.get("/api/jobs/DAVENPORT_1 Test Street/photo-groups").json()
    assert body["chosen_missing"] is True


def test_the_manifest_route_returns_only_the_chosen_photographs(tmp_path, monkeypatch):
    maquoketa(tmp_path)
    client = _client(tmp_path, monkeypatch)
    client.put("/api/jobs/DAVENPORT_1 Test Street/photo-group",
               json={"folder": "Report Photos_X"})
    body = client.get("/api/jobs/DAVENPORT_1 Test Street/manifest").json()
    assert len(body["photos"]) == 16
