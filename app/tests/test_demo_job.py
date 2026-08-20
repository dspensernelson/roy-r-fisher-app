"""The practice job that ships inside the package.

It exists so Mark has something to open the moment the app starts, instead of a
folder picker pointing at nothing. Everything in it is invented, and these
tests are mostly about proving that: no client material, no real address, no
metadata, and twelve images that say what they are on their face.

The last few drive the app against the generated job, because a demo that
cannot be opened is not a demo.
"""
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import demo_job  # noqa: E402
import jobs as jobs_module  # noqa: E402
import brief  # noqa: E402
from main import create_app  # noqa: E402


@pytest.fixture
def built(tmp_path):
    return demo_job.build(tmp_path)


# --- what it contains -------------------------------------------------------

def test_it_makes_one_job_under_a_demo_jobs_folder(built, tmp_path):
    assert built.parent.name == "Demo Jobs"
    assert built.name == demo_job.JOB_NAME
    assert [p.name for p in built.parent.iterdir() if p.is_dir()] == [demo_job.JOB_NAME]


def test_it_has_marks_own_standard_folders(built):
    for folder in jobs_module.MARK_FOLDERS:
        assert (built / folder).is_dir(), folder


def test_the_brief_is_readable_by_the_app(built):
    found = brief.read_brief(built)
    fields = found["fields"]
    assert fields["Property address"] == "100 Example Avenue, Anytown, Iowa"
    assert fields["Engagement type"] == "Full appraisal"
    assert fields["Property type"] == "Retail"


def test_there_are_exactly_twelve_photos(built):
    photos = sorted(p for p in (built / "Photos").iterdir() if p.is_file())
    assert len(photos) == 12


def test_the_photos_vary_in_size_and_orientation(built):
    shapes = []
    for path in sorted((built / "Photos").iterdir()):
        with Image.open(path) as im:
            shapes.append(im.size)
    assert len({s for s in shapes}) == 12                    # all different
    assert any(w > h for w, h in shapes), "no landscape"
    assert any(h > w for w, h in shapes), "no portrait"
    assert any(w == h for w, h in shapes), "no square"


def test_every_photo_opens_and_is_a_real_image(built):
    for path in sorted((built / "Photos").iterdir()):
        with Image.open(path) as im:
            im.verify()


def test_no_photo_carries_exif_or_a_location(built):
    """They never had any. Nothing here opens a camera file, so there is no
    metadata to inherit and none to strip."""
    for path in sorted((built / "Photos").iterdir()):
        with Image.open(path) as im:
            exif = im.getexif()
        assert not exif, path.name
        assert 0x8825 not in exif, "%s carries GPS" % path.name


def test_no_heic_is_shipped(built):
    """A HEIC placed straight into a Photos folder still fails Build today,
    per Section 1b, and that is not fixed until Task 4. Shipping one would
    hand Spenser a demo with a broken button in it."""
    names = [p.name.lower() for p in (built / "Photos").iterdir()]
    assert not [n for n in names if n.endswith((".heic", ".heif"))]


def test_the_whole_job_stays_small(built):
    total = sum(p.stat().st_size for p in built.rglob("*") if p.is_file())
    assert total < 1_500_000, "%d bytes is more than a practice job needs" % total


# --- it is obviously invented -----------------------------------------------

def test_the_address_is_plainly_fictional(built):
    text = (built / "job-brief.md").read_text(encoding="utf-8")
    assert "Anytown" in text and "100 Example Avenue" in text
    assert "fictional" in text.lower()


def test_every_photo_says_on_its_face_that_it_is_not_real(built):
    """Checked as pixels, not as a filename. The words are drawn into the
    image, so a photo separated from its folder still declares itself."""
    for path in sorted((built / "Photos").iterdir()):
        with Image.open(path) as im:
            colours = {c for _, c in im.convert("RGB").getcolors(maxcolors=1 << 20)}
        # a flat panel plus drawn text: never a photograph's colour spread
        assert len(colours) < 400, path.name


def test_nothing_client_shaped_appears_anywhere_in_it(built):
    """No city, street, client or report name from the real corpus."""
    blob = b" ".join(p.read_bytes() for p in built.rglob("*") if p.is_file())
    blob += b" ".join(str(p).encode() for p in built.rglob("*"))
    for forbidden in (b"Bettendorf", b"Davenport", b"Mason City", b"Walmart",
                      b"Kinze", b"Marquette", b"Burlington", b"Brady Street",
                      b"Forest", b"sk-ant"):
        assert forbidden not in blob, forbidden


def test_the_generator_reads_no_protected_directory():
    """Generated from nothing. It cannot copy what it never opens.

    Docstrings are excluded before matching. The module's own docstring says
    it copies nothing from those places, so scanning the raw text would find
    the sentence promising the opposite of what it was looking for.
    """
    import ast

    tree = ast.parse(Path(demo_job.__file__).read_text(encoding="utf-8"))

    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            found = ast.get_docstring(node, clean=False)
            if found is not None:
                docstrings.add(found)

    strings = [n.value for n in ast.walk(tree)
               if isinstance(n, ast.Constant) and isinstance(n.value, str)
               and n.value not in docstrings]

    for forbidden in ("Report Examples", "locker", "RRF Demo Jobs",
                      ".rrf-demo-baseline"):
        assert not [s for s in strings if forbidden in s], forbidden


def test_it_does_not_bring_back_the_development_demo_system():
    source = Path(demo_job.__file__).read_text(encoding="utf-8")
    import ast
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    assert "demo" not in names
    assert "aipolicy" not in names
    assert "captions" not in names
    assert "anthropic" not in names


# --- the app can actually use it --------------------------------------------

@pytest.fixture
def client(built, monkeypatch):
    monkeypatch.setenv("RRF_JOBS_HOME", str(built.parent))
    return TestClient(create_app())


def test_the_jobs_folder_opens_and_shows_the_one_job(client, built):
    found = client.get("/api/workspace").json()
    assert found["valid"] is True
    assert found["folder_names"] == [demo_job.JOB_NAME]


def test_all_twelve_photos_reach_the_subject_photographs_screen(client):
    manifest = client.get("/api/jobs/%s/manifest" % demo_job.JOB_NAME).json()
    assert len(manifest["photos"]) == 12
    assert all(p["caption"] == "" for p in manifest["photos"])


def test_the_photo_document_builds_from_the_shipped_dataset(client, built):
    """The workflow this demo exists for, run end to end with hand-typed
    captions and no AI of any kind."""
    from docx import Document

    manifest = client.get("/api/jobs/%s/manifest" % demo_job.JOB_NAME).json()
    for i, photo in enumerate(manifest["photos"], start=1):
        photo["caption"] = "View of demo subject %02d" % i
    assert client.put("/api/jobs/%s/manifest" % demo_job.JOB_NAME,
                      json=manifest).status_code == 200

    # Build is gated on review now, which is the approved behaviour.
    blocked = client.post("/api/jobs/%s/build" % demo_job.JOB_NAME)
    assert blocked.status_code == 400
    assert "reviewed" in blocked.json()["detail"]

    for photo in manifest["photos"]:
        assert client.post("/api/jobs/%s/photos/%s/reviewed"
                           % (demo_job.JOB_NAME, photo["file"])).status_code == 200

    created = client.post("/api/jobs/%s/build" % demo_job.JOB_NAME)
    assert created.status_code == 200, created.json()
    # named from the brief, never from the folder
    assert created.json()["created"] == "Anytown_100 Example Avenue Photos (Complete).docx"

    out = built / "Photos" / created.json()["created"]
    assert out.is_file()
    document = Document(str(out))
    images = [r for r in document.part.rels.values() if "image" in r.reltype]
    assert len(images) == 12


def test_using_the_demo_never_touches_an_original_photograph(client, built):
    before = {p.name: p.read_bytes() for p in (built / "Photos").iterdir()}
    manifest = client.get("/api/jobs/%s/manifest" % demo_job.JOB_NAME).json()
    for photo in manifest["photos"]:
        photo["caption"] = "a caption"
    client.put("/api/jobs/%s/manifest" % demo_job.JOB_NAME, json=manifest)
    for photo in manifest["photos"]:
        client.post("/api/jobs/%s/photos/%s/reviewed"
                    % (demo_job.JOB_NAME, photo["file"]))
    client.post("/api/jobs/%s/build" % demo_job.JOB_NAME)

    for name, body in before.items():
        assert (built / "Photos" / name).read_bytes() == body, name
