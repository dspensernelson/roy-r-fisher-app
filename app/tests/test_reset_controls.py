"""The two testing controls: start setup over, and clear this job's captions.

Both are judged by what they leave behind, so these run against real folders
and real manifest files on disk.
"""
import copy
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import workspace  # noqa: E402
from main import create_app  # noqa: E402

# Everything a real manifest has been seen to hold, including a key the app
# does not write itself: ai_available arrives by the browser handing back
# what the API answered with, and one was found sitting in a real manifest
# on disk. Clearing captions has to leave keys like that alone.
FULL_MANIFEST = {
    "job": "DAVENPORT_2840 Brady Street - 2026 Tax",
    "context": "2840 Brady Street, Davenport, Iowa · Retail",
    "report_year": 2026,
    "caption_style": "view",
    "ai_available": True,
    "photos": [
        {"file": "a.jpg", "caption": "View east from Brady Street"},
        {"file": "b.jpg", "caption": ""},
        {"file": "c.jpg", "caption": "Rear loading area"},
    ],
}


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


def make_job(home: Path, name: str, manifest=None) -> Path:
    """A real job folder on disk: real photo files, a real manifest file.

    Mark's own eight folders too, because the jobs folder can no longer be
    chosen unless it actually holds something the app recognises as a job.
    """
    import jobs as jobs_module
    manifest = FULL_MANIFEST if manifest is None else manifest
    job = home / name
    for folder in jobs_module.MARK_FOLDERS:
        (job / folder).mkdir(parents=True, exist_ok=True)
    for entry in manifest["photos"]:
        (job / "Photos" / entry["file"]).write_bytes(b"not really a photo")
    (job / "Photos" / "photo-manifest.json").write_text(json.dumps(manifest, indent=2))
    return job


# ------------------------------------------------------ start setup over ----
def test_it_forgets_only_the_jobs_folder(client, home):
    settings = Path(workspace.settings_file())
    settings.write_text(json.dumps({"jobs_folder": str(home),
                                    "something_else": "keep me"}), encoding="utf-8")

    r = client.delete("/api/workspace")
    assert r.status_code == 200
    assert r.json()["chosen"] is False
    assert r.json()["valid"] is False

    left = json.loads(settings.read_text(encoding="utf-8"))
    assert "jobs_folder" not in left
    assert left["something_else"] == "keep me"


def test_it_never_opens_the_key_file(client, home, tmp_path, monkeypatch):
    key_file = tmp_path / "key.env"
    key_file.write_text("ANTHROPIC_API_KEY=sk-ant-not-a-real-key\n")
    monkeypatch.setenv("RRF_KEY_FILE", str(key_file))
    before = key_file.read_text()

    client.put("/api/workspace", json={"path": str(home)})
    client.delete("/api/workspace")

    assert key_file.read_text() == before


def test_it_changes_nothing_on_disk(client, home):
    make_job(home, "DAVENPORT_1 Main - 2026")
    before = sorted(str(p.relative_to(home)) for p in home.rglob("*"))

    client.put("/api/workspace", json={"path": str(home)})
    client.delete("/api/workspace")

    assert sorted(str(p.relative_to(home)) for p in home.rglob("*")) == before


def test_the_same_folder_can_be_chosen_again(client, home):
    make_job(home, "DAVENPORT_1 Main - 2026")
    client.put("/api/workspace", json={"path": str(home)})
    client.delete("/api/workspace")
    assert client.get("/api/jobs").json() == []

    again = client.put("/api/workspace", json={"path": str(home)})
    assert again.status_code == 200
    client.put("/api/workspace/folders", json={"active": ["DAVENPORT_1 Main - 2026"]})
    assert [j["name"] for j in client.get("/api/jobs").json()] == ["DAVENPORT_1 Main - 2026"]


# ------------------------------------------------------- clear captions -----
def test_only_the_captions_change(client, home):
    """The whole manifest before and after, with only caption values allowed
    to differ. This is the guard against ever fixing captions by deleting
    the manifest, which would take the order and the style with it."""
    job = make_job(home, "DAVENPORT_2840 Brady Street - 2026 Tax")
    client.put("/api/workspace", json={"path": str(home)})
    path = job / "Photos" / "photo-manifest.json"
    before = json.loads(path.read_text())

    r = client.post("/api/jobs/DAVENPORT_2840 Brady Street - 2026 Tax/captions/clear")
    assert r.status_code == 200
    assert r.json()["cleared"] == 2          # the blank one was not counted

    after = json.loads(path.read_text())

    # every caption is now empty
    assert all(entry["caption"] == "" for entry in after["photos"])

    # and with the captions masked out, the two are identical
    def masked(m):
        m = copy.deepcopy(m)
        for entry in m["photos"]:
            entry["caption"] = "<masked>"
        return m

    assert masked(after) == masked(before)


def test_the_file_order_and_every_other_key_survive(client, home):
    job = make_job(home, "A job")
    client.put("/api/workspace", json={"path": str(home)})
    client.post("/api/jobs/A job/captions/clear")
    after = json.loads((job / "Photos" / "photo-manifest.json").read_text())

    assert [e["file"] for e in after["photos"]] == ["a.jpg", "b.jpg", "c.jpg"]
    assert after["caption_style"] == "view"
    assert after["report_year"] == 2026
    assert after["context"] == FULL_MANIFEST["context"]
    assert after["job"] == FULL_MANIFEST["job"]
    assert after["ai_available"] is True     # a key the app never writes itself


def test_the_photos_themselves_are_untouched(client, home):
    job = make_job(home, "A job")
    client.put("/api/workspace", json={"path": str(home)})
    photos = job / "Photos"
    before = {p.name: p.read_bytes() for p in photos.iterdir() if p.suffix == ".jpg"}

    client.post("/api/jobs/A job/captions/clear")

    after = {p.name: p.read_bytes() for p in photos.iterdir() if p.suffix == ".jpg"}
    assert after == before


def test_a_built_word_file_is_left_alone(client, home):
    job = make_job(home, "A job")
    built = job / "Photos" / "Photo (RRF App).docx"
    built.write_bytes(b"a built document")
    client.put("/api/workspace", json={"path": str(home)})

    client.post("/api/jobs/A job/captions/clear")

    assert built.is_file()
    assert built.read_bytes() == b"a built document"


def test_no_other_job_is_affected(client, home):
    make_job(home, "A job")
    other = make_job(home, "B job")
    client.put("/api/workspace", json={"path": str(home)})
    before = (other / "Photos" / "photo-manifest.json").read_text()

    client.post("/api/jobs/A job/captions/clear")

    assert (other / "Photos" / "photo-manifest.json").read_text() == before


def test_it_is_refused_when_there_is_nothing_to_clear(client, home):
    blank = copy.deepcopy(FULL_MANIFEST)
    for entry in blank["photos"]:
        entry["caption"] = ""
    make_job(home, "A job", manifest=blank)
    client.put("/api/workspace", json={"path": str(home)})

    r = client.post("/api/jobs/A job/captions/clear")
    assert r.status_code == 400
    assert "no captions to clear" in r.json()["detail"]


def test_it_is_refused_when_there_is_no_manifest_at_all(client, home):
    job = home / "A job"
    (job / "Photos").mkdir(parents=True)
    client.put("/api/workspace", json={"path": str(home)})

    r = client.post("/api/jobs/A job/captions/clear")
    assert r.status_code == 400


def test_captions_can_be_written_again_afterwards(client, home, monkeypatch):
    """Suggest captions works on the blanks, which is what clearing leaves."""
    job = make_job(home, "A job")
    client.put("/api/workspace", json={"path": str(home)})
    client.post("/api/jobs/A job/captions/clear")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    import captions
    monkeypatch.setattr(captions, "draft_captions",
                        lambda context, paths, style=None: ({p.name: "fresh caption" for p in paths}, {"input": 100, "output": 20}))

    r = client.post("/api/jobs/A job/captions")
    assert r.status_code == 200
    assert [p["caption"] for p in r.json()["photos"]] == ["fresh caption"] * 3


def test_a_job_that_does_not_exist_is_refused(client, home):
    make_job(home, "A job")          # so the folder can be chosen at all
    client.put("/api/workspace", json={"path": str(home)})
    assert client.post("/api/jobs/nope/captions/clear").status_code == 404
