import io
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
from main import create_app  # noqa: E402


def jpg_bytes(color):
    buf = io.BytesIO()
    Image.new("RGB", (320, 240), color).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def client(tmp_path, monkeypatch):
    home = tmp_path / "jobs"
    (home / "JOB1" / "Photos").mkdir(parents=True)
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    return TestClient(create_app()), home / "JOB1"


def test_upload_copies_and_manifests(client):
    c, job = client
    r = c.post("/api/jobs/JOB1/photos", files=[
        ("files", ("a.jpg", jpg_bytes((200, 10, 10)), "image/jpeg")),
        ("files", ("b.jpg", jpg_bytes((10, 200, 10)), "image/jpeg")),
    ])
    assert r.status_code == 200
    assert (job / "Photos" / "a.jpg").exists() and (job / "Photos" / "b.jpg").exists()
    manifest = c.get("/api/jobs/JOB1/manifest").json()
    assert [p["file"] for p in manifest["photos"]] == ["a.jpg", "b.jpg"]
    assert all(p["caption"] == "" for p in manifest["photos"])


def test_upload_never_overwrites_existing_photo(client):
    c, job = client
    (job / "Photos" / "a.jpg").write_bytes(jpg_bytes((1, 2, 3)))
    original = (job / "Photos" / "a.jpg").read_bytes()
    c.post("/api/jobs/JOB1/photos", files=[("files", ("a.jpg", jpg_bytes((9, 9, 9)), "image/jpeg"))])
    assert (job / "Photos" / "a.jpg").read_bytes() == original      # untouched
    stored = {p.name for p in (job / "Photos").glob("a*.jpg")}
    assert len(stored) == 2                                          # uploaded copy got a new name


def test_manifest_roundtrip_and_thumb(client):
    c, job = client
    c.post("/api/jobs/JOB1/photos", files=[("files", ("a.jpg", jpg_bytes((5, 5, 5)), "image/jpeg"))])
    m = c.get("/api/jobs/JOB1/manifest").json()
    m["photos"][0]["caption"] = "View of front entrance"
    assert c.put("/api/jobs/JOB1/manifest", json=m).status_code == 200
    assert c.get("/api/jobs/JOB1/manifest").json()["photos"][0]["caption"] == "View of front entrance"
    t = c.get("/api/jobs/JOB1/thumb/a.jpg")
    assert t.status_code == 200 and t.headers["content-type"] == "image/jpeg"


def test_manifest_defaults_report_year_to_current_year(client):
    c, job = client
    import datetime
    m = c.get("/api/jobs/JOB1/manifest").json()
    assert m["report_year"] == datetime.date.today().year
    assert m["job"] == "JOB1"
    assert m["photos"] == []


# --- Path-safety / traversal tests -----------------------------------------
# Both the job name (URL segment) and the thumbnail `file` param are
# untrusted input that must be confined to the job's own Photos folder.
# These attack both with traversal, absolute paths, and backslash forms.

def test_upload_rejects_traversal_job_name(client):
    c, job = client
    r = c.post("/api/jobs/..%2F..%2Fevil/photos", files=[
        ("files", ("a.jpg", jpg_bytes((1, 1, 1)), "image/jpeg")),
    ])
    assert r.status_code in (400, 404)
    # nothing escaped the jobs home
    assert not (job.parent.parent / "evil").exists()


def test_manifest_get_rejects_traversal_job_name(client):
    c, job = client
    assert c.get("/api/jobs/..%2F..%2Fevil/manifest").status_code in (400, 404)
    assert c.get("/api/jobs/..\\evil/manifest").status_code in (400, 404)


def test_manifest_put_rejects_traversal_job_name(client):
    c, job = client
    body = {"job": "evil", "context": "", "report_year": 2026, "photos": []}
    assert c.put("/api/jobs/..%2F..%2Fevil/manifest", json=body).status_code in (400, 404)
    assert not (job.parent.parent / "evil").exists()


def test_thumb_rejects_traversal_job_name(client):
    c, job = client
    assert c.get("/api/jobs/..%2F..%2Fevil/thumb/a.jpg").status_code in (400, 404)


def test_thumb_rejects_traversal_in_file_param(client):
    c, job = client
    c.post("/api/jobs/JOB1/photos", files=[("files", ("a.jpg", jpg_bytes((3, 3, 3)), "image/jpeg"))])

    # Plant a "secret" file one level above the job's Photos dir to confirm
    # a traversal attempt can't reach it.
    secret = job / "secret.txt"
    secret.write_text("do not serve me")

    for traversal in ("..%2Fsecret.txt", "..\\secret.txt", "%2Fetc%2Fpasswd"):
        r = c.get(f"/api/jobs/JOB1/thumb/{traversal}")
        assert r.status_code in (400, 404), f"traversal {traversal!r} should not succeed"

    # And an absolute path passed as the file segment must not escape either.
    r = c.get("/api/jobs/JOB1/thumb/" + str(secret).replace("/", "%2F"))
    assert r.status_code in (400, 404)


def test_thumb_missing_file_is_404_not_500(client):
    c, job = client
    assert c.get("/api/jobs/JOB1/thumb/does-not-exist.jpg").status_code == 404


# --- Fix round 1: reviewer-found gaps ---------------------------------------

def test_thumb_symlink_escape_is_blocked(client, tmp_path):
    """`Path(...).name` only confines the STRING passed as `file`. It does
    nothing if that name, once joined to Photos/, resolves through a
    symlink to a file outside the job entirely. Plant exactly that: a
    symlink at Photos/link.jpg pointing at a file elsewhere on disk, and
    confirm the endpoint refuses to serve it rather than following the
    link.
    """
    c, job = client
    outside = tmp_path / "outside_secret.jpg"
    outside.write_bytes(jpg_bytes((123, 45, 67)))

    link = job / "Photos" / "link.jpg"
    link.symlink_to(outside)

    r = c.get("/api/jobs/JOB1/thumb/link.jpg")
    assert r.status_code == 404
    # no thumbnail should have been derived from the outside file either
    assert not (job / "Photos" / ".rrf-thumbs" / "link.jpg.jpg").exists()


def test_manifest_put_rejects_file_entry_that_escapes_photos_dir(client):
    """The manifest is written verbatim and later consumed by
    photo_pages.build_photo_docx, which does `photos_dir / entry["file"]`
    with no safety check of its own. A manifest entry with a traversal
    filename must be rejected at the PUT boundary, and the rejected write
    must not touch the manifest already on disk.
    """
    c, job = client
    baseline = c.get("/api/jobs/JOB1/manifest").json()
    malicious = {
        "job": "JOB1", "context": "", "report_year": 2026,
        "photos": [{"file": "../../../etc/passwd", "caption": "leak"}],
    }
    r = c.put("/api/jobs/JOB1/manifest", json=malicious)
    assert r.status_code == 400
    assert c.get("/api/jobs/JOB1/manifest").json() == baseline


def test_manifest_put_rejects_file_entry_with_subdirectory(client):
    """A 'file' containing a subdirectory segment (no '..' needed) is still
    not a bare filename per the manifest contract, and must be rejected
    even though 'sub/evil.jpg' happens to resolve inside Photos/ here.
    """
    c, job = client
    baseline = c.get("/api/jobs/JOB1/manifest").json()
    body = {
        "job": "JOB1", "context": "", "report_year": 2026,
        "photos": [{"file": "sub/evil.jpg", "caption": "x"}],
    }
    r = c.put("/api/jobs/JOB1/manifest", json=body)
    assert r.status_code == 400
    assert c.get("/api/jobs/JOB1/manifest").json() == baseline


def test_upload_does_not_write_through_dangling_symlink(client, tmp_path):
    """A pre-planted DANGLING symlink (target doesn't exist) sitting at the
    exact filename an upload will target must not let the write follow the
    link. `Path.exists()` alone returns False for a dangling symlink, so a
    naive "is this name free" check would treat the symlink's name as
    unoccupied and write straight through it to wherever the link points --
    this is the write-side counterpart of the read-side symlink escape
    fixed in thumb() in fix round 1.
    """
    c, job = client
    outside_target = tmp_path / "outside_target.jpg"  # deliberately never created
    link = job / "Photos" / "a.jpg"
    link.symlink_to(outside_target)  # a.jpg is a dangling symlink right now

    payload = jpg_bytes((77, 88, 99))
    r = c.post("/api/jobs/JOB1/photos", files=[("files", ("a.jpg", payload, "image/jpeg"))])
    assert r.status_code == 200

    # (a) / (c): the symlink's outside target was never created by the write
    assert not outside_target.exists()

    # the planted symlink itself is untouched -- still a dangling symlink,
    # never resolved through and never overwritten
    assert link.is_symlink()
    assert not link.exists()

    # (b) the uploaded bytes landed on a real regular file inside Photos/,
    # under a name the upload got redirected to (not "a.jpg", since that
    # name was occupied by the symlink)
    manifest = c.get("/api/jobs/JOB1/manifest").json()
    stored_names = [p["file"] for p in manifest["photos"]]
    assert len(stored_names) == 1
    stored_name = stored_names[0]
    assert stored_name != "a.jpg"
    stored_path = job / "Photos" / stored_name
    assert stored_path.is_file() and not stored_path.is_symlink()
    assert stored_path.read_bytes() == payload


# --- Manifest/folder reconciliation -----------------------------------------
# The appraiser's real workflow: camera photos land straight in the job's
# Photos folder, never through this app's own upload. A manifest that only
# ever reflects what upload wrote would show "0 photos" for a folder that
# plainly has some sitting in it (this is exactly the bug the job card vs.
# Photos screen mismatch surfaced). These prove load_manifest reconciles
# against the folder, never reshuffles a human's existing order/captions,
# and never writes back to disk on a plain GET.

def test_manifest_reconciles_photos_dropped_directly_into_folder(client):
    c, job = client
    (job / "Photos" / "b.jpg").write_bytes(jpg_bytes((1, 1, 1)))
    (job / "Photos" / "a.jpg").write_bytes(jpg_bytes((2, 2, 2)))
    manifest_file = job / "Photos" / "photo-manifest.json"
    assert not manifest_file.exists()

    m = c.get("/api/jobs/JOB1/manifest").json()
    assert [p["file"] for p in m["photos"]] == ["a.jpg", "b.jpg"]  # no EXIF -> filename order
    assert all(p["caption"] == "" for p in m["photos"])

    # a GET must never write the manifest to disk
    assert not manifest_file.exists()


def test_manifest_keeps_existing_entries_and_appends_new_file_from_disk(client):
    c, job = client
    r = c.post("/api/jobs/JOB1/photos", files=[
        ("files", ("a.jpg", jpg_bytes((10, 10, 10)), "image/jpeg")),
        ("files", ("b.jpg", jpg_bytes((20, 20, 20)), "image/jpeg")),
    ])
    assert r.status_code == 200

    # a human reorders these and writes real captions
    m = c.get("/api/jobs/JOB1/manifest").json()
    m["photos"] = [
        {"file": "b.jpg", "caption": "Rear yard"},
        {"file": "a.jpg", "caption": "Front entrance"},
    ]
    assert c.put("/api/jobs/JOB1/manifest", json=m).status_code == 200

    # a third photo lands in the folder outside the app entirely
    (job / "Photos" / "c.jpg").write_bytes(jpg_bytes((30, 30, 30)))

    m2 = c.get("/api/jobs/JOB1/manifest").json()
    assert m2["photos"][0] == {"file": "b.jpg", "caption": "Rear yard"}
    assert m2["photos"][1] == {"file": "a.jpg", "caption": "Front entrance"}
    assert m2["photos"][2]["file"] == "c.jpg"
    assert m2["photos"][2]["caption"] == ""

    # the GET reconciled the response only -- the file on disk still has
    # just the two entries the human actually saved
    on_disk = json.loads((job / "Photos" / "photo-manifest.json").read_text())
    assert [p["file"] for p in on_disk["photos"]] == ["b.jpg", "a.jpg"]


def test_manifest_drops_entries_for_files_deleted_from_disk(client):
    c, job = client
    r = c.post("/api/jobs/JOB1/photos", files=[
        ("files", ("a.jpg", jpg_bytes((5, 5, 5)), "image/jpeg")),
        ("files", ("b.jpg", jpg_bytes((6, 6, 6)), "image/jpeg")),
    ])
    assert r.status_code == 200
    (job / "Photos" / "a.jpg").unlink()

    m = c.get("/api/jobs/JOB1/manifest").json()
    assert [p["file"] for p in m["photos"]] == ["b.jpg"]

    # again, the GET must not have rewritten the manifest on disk
    on_disk = json.loads((job / "Photos" / "photo-manifest.json").read_text())
    assert [p["file"] for p in on_disk["photos"]] == ["a.jpg", "b.jpg"]


def test_manifest_rejects_absolute_path_job_name(client):
    """Coverage gap called out in review: the file-param traversal tests
    above cover '../', absolute paths, and backslash forms, but the job
    NAME was never attacked with an absolute path specifically.

    Both forms below are blocked, but by different layers, and the
    assertions say so explicitly rather than lumping them together:

    - A POSIX-style absolute path ('/etc/passwd') contains '/'. Starlette
      decodes %2F before route matching, so the decoded value no longer
      matches the single-segment {name} pattern at all -- this 404s at the
      ROUTER, before our handler runs. The generic {"detail": "Not Found"}
      body (not our own message) is the proof.
    - A Windows-style absolute path ('C:\\evil') has no forward slash, so it
      passes through as one literal path segment and DOES reach our
      handler, where jobs.resolve_job's '\\ in name' check rejects it. Our
      own {"detail": "Job not found."} body is the proof this one actually
      exercised the confinement code, not just routing.
    """
    c, job = client

    r_posix = c.get("/api/jobs/%2Fetc%2Fpasswd/manifest")
    assert r_posix.status_code == 404
    assert r_posix.json()["detail"] == "Not Found"  # router-level, generic

    r_windows = c.get("/api/jobs/C:\\evil/manifest")
    assert r_windows.status_code == 404
    assert r_windows.json()["detail"] == "Job not found."  # our handler ran
