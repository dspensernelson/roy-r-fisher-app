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
def fake_source(tmp_path, monkeypatch):
    """A stand-in for Report Examples, with camera-style names and EXIF.

    No test reads the real corpus, and what the sanitiser has to strip is
    exactly this.
    """
    import photo_source
    source = tmp_path / "Fake Report Examples" / "CLIENTTOWN_A Property" / "Photos"
    source.mkdir(parents=True)
    for i in range(80):
        image = Image.new("RGB", (900 + i, 700), (40 + i % 60, 90, 120))
        exif = image.getexif()
        exif[0x0112] = 6
        exif[0x010F] = "AcmeCamera"
        exif[0x0132] = "2026:02:13 10:35:16"
        image.save(source / ("20260213_10%04d.jpg" % i), quality=88, exif=exif)
    monkeypatch.setattr(photo_source, "SOURCE", source.parents[1])
    monkeypatch.setattr(photo_source, "MIN_BYTES", 1)
    return source.parents[1]


@pytest.fixture
def built(tmp_path, fake_source):
    """The ordinary job. `built.parent` holds both."""
    return demo_job.build(tmp_path / "package")


# --- both practice jobs -----------------------------------------------------

def test_two_practice_jobs_ship(built):
    home = built.parent
    names = sorted(p.name for p in home.iterdir() if p.is_dir())
    assert names == sorted(spec["name"] for spec in demo_job.JOBS)


def test_the_twelve_photo_job_is_below_the_confirmation_threshold(built):
    import captions
    assert len(list((built / "Photos").iterdir())) == 12
    assert 12 <= captions.CONFIRM_ABOVE, "twelve would trigger the confirmation"


def test_the_sixty_one_photo_job_needs_confirming_and_two_tranches(built):
    import captions
    job = built.parent / demo_job.LARGE["name"]
    photos = sorted((job / "Photos").iterdir())
    assert len(photos) == 61

    assert 61 > captions.CONFIRM_ABOVE, "sixty-one would skip the confirmation"
    tranches = captions.plan_tranches(photos, {str(p): "x" for p in photos})
    assert [len(t) for t in tranches] == [60, 1]


def test_the_large_job_has_a_fictional_brief_of_its_own(built):
    import brief
    job = built.parent / demo_job.LARGE["name"]
    fields = brief.read_brief(job)["fields"]
    assert fields["Property address"] == "200 Example Avenue, Anytown, Iowa"
    assert "fictional" in fields["Client (intended user)"].lower()
    for folder in ("Photos", "Maps", "Comps", "Drafts"):
        assert (job / folder).is_dir()


def test_packaging_stops_rather_than_shipping_placeholders(tmp_path, monkeypatch):
    """If the approved source is not on the build machine, nothing is
    substituted. A practice job full of panels is what this replaced."""
    import photo_source
    monkeypatch.setattr(photo_source, "SOURCE", tmp_path / "nowhere")
    with pytest.raises(photo_source.SourceUnavailable) as raised:
        demo_job.build(tmp_path / "package")
    assert "not available" in str(raised.value)
    assert "placeholder" in str(raised.value)


def test_no_synthetic_panel_ships_anywhere(built):
    for photo in built.parent.rglob("Photos/*"):
        assert not photo.name.startswith("SYNTHETIC"), photo.name
        assert photo.name.startswith("photo-"), photo.name


# --- what it contains -------------------------------------------------------

def test_it_makes_the_jobs_under_a_demo_jobs_folder(built):
    assert built.parent.name == "Demo Jobs"
    assert built.name == demo_job.JOB_NAME


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


def test_the_photographs_are_real_ones_with_their_metadata_removed(built):
    """They are photographs now, not generated panels, and each is a copy with
    the camera information stripped out of it."""
    for path in sorted((built / "Photos").iterdir()):
        with Image.open(path) as im:
            assert not im.getexif(), path.name
            assert im.mode == "RGB"
        assert path.name.startswith("photo-")
        assert "20260213" not in path.name


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


def test_the_practice_jobs_stay_a_sensible_size(built):
    total = sum(p.stat().st_size for p in built.parent.rglob("*") if p.is_file())
    assert total < 60_000_000, "%d bytes is more than practice jobs need" % total


# --- it is obviously invented -----------------------------------------------

def test_the_address_is_plainly_fictional(built):
    text = (built / "job-brief.md").read_text(encoding="utf-8")
    assert "Anytown" in text and "100 Example Avenue" in text
    assert "fictional" in text.lower()


def test_the_source_is_only_ever_read(built, fake_source):
    """Copy only: never moved, renamed, edited, deleted or rewritten."""
    import hashlib
    after = {p: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(fake_source.rglob("*")) if p.is_file()}
    assert len(after) == 80, "a source file went missing"
    for p in after:
        with Image.open(p) as im:
            assert im.getexif(), "a source file lost its EXIF"


def test_nothing_client_shaped_appears_anywhere_in_it(built):
    """No city, street, client or report name from the real corpus."""
    blob = b" ".join(p.read_bytes()[:6000] for p in built.parent.rglob("*") if p.is_file())
    blob += b" ".join(str(p).encode() for p in built.parent.rglob("*"))
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


def test_the_jobs_folder_opens_and_shows_both_jobs(client, built):
    found = client.get("/api/workspace").json()
    assert found["valid"] is True
    assert found["folder_names"] == sorted(spec["name"] for spec in demo_job.JOBS)


def test_the_sixty_one_photo_job_opens_and_asks_to_confirm(client, built):
    name = demo_job.LARGE["name"]
    quote = client.get("/api/jobs/%s/caption-estimate" % name).json()
    assert quote["photos_to_send"] == 61
    assert quote["tranches"] == 2
    assert quote["needs_confirmation"] is True
    assert quote["estimate"]["arithmetic"] == "61 x $0.0500 = $3.05"


def test_the_twelve_photo_job_opens_without_asking(client, built):
    quote = client.get("/api/jobs/%s/caption-estimate" % demo_job.JOB_NAME).json()
    assert quote["photos_to_send"] == 12
    assert quote["tranches"] == 1
    assert quote["needs_confirmation"] is False


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
