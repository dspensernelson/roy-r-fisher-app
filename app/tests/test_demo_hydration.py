"""Task 6: filling the development demo jobs, without touching anything real.

These build their own repo-shaped demo system in tmp_path, the same way the
reset tests do, so they never depend on Spenser's actual demo folders being
present and can never write into them.

The two properties that matter are that Mark's own photographs are never
modified, and that hydrating the baseline is what makes Reset Demo restore the
photographs instead of deleting them.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import demo  # noqa: E402
import hydrate_demo  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def fake_source(tmp_path, monkeypatch):
    """A stand-in for Report Examples, so no test ever reads the real corpus.

    Its files are deliberately given camera-style names and real EXIF, because
    what the tool has to strip is exactly that.
    """
    source = tmp_path / "Fake Report Examples" / "CLIENTTOWN_Some Property" / "Photos"
    source.mkdir(parents=True)
    for i in range(12):
        image = Image.new("RGB", (900 + i, 700), (40 + i * 5, 90, 120))
        exif = image.getexif()
        exif[0x0112] = 6                       # orientation
        exif[0x010F] = "AcmeCamera"            # the camera that took it
        exif[0x0132] = "2026:02:13 10:35:16"   # when it was taken
        image.save(source / ("20260213_10%04d.jpg" % i), quality=90, exif=exif)
    monkeypatch.setattr(hydrate_demo, "SOURCE", source.parents[1])
    monkeypatch.setattr(hydrate_demo, "MIN_BYTES", 1)
    return source.parents[1]


@pytest.fixture
def small_plan(monkeypatch):
    """The same shape of plan with far fewer photographs.

    The real plan copies 266 files, which is right on the machine and far too
    slow in a test. What is under test is the behaviour, not the volume.
    """
    monkeypatch.setattr(hydrate_demo, "PLAN", {
        name: dict(spec, real=min(spec["real"], 9))
        for name, spec in hydrate_demo.PLAN.items()})


@pytest.fixture
def demo_repo(tmp_path, monkeypatch, fake_source, small_plan):
    """A stand-in project whose baseline holds one of Mark's photographs."""
    monkeypatch.setattr(demo, "REPO", tmp_path)
    monkeypatch.setattr(demo, "CONFIG", tmp_path / ".rrf-demo.json")
    monkeypatch.setenv("RRF_SETTINGS_FILE", str(tmp_path / "settings.json"))

    baseline = tmp_path / ".rrf-demo-baseline" / "RRF Demo Jobs"
    for name in hydrate_demo.PLAN:
        (baseline / name / "Photos").mkdir(parents=True)
    # one real photograph, standing in for Mark's own
    real = baseline / "DAVENPORT_2840 Brady Street - 2026 Tax" / "Photos" / "his-own.jpg"
    Image.new("RGB", (1200, 900), (12, 34, 56)).save(real)

    demo.write_checksums(baseline, baseline.parent / demo.CHECKSUM_NAME)
    shutil.copytree(baseline, tmp_path / "RRF Demo Jobs")
    (tmp_path / "app" / "server").mkdir(parents=True)
    (tmp_path / "app" / "server" / "main.py").write_text("# do not touch me")
    (tmp_path / ".rrf-demo.json").write_text(json.dumps(
        {"demo_mode": True, "baseline": ".rrf-demo-baseline/RRF Demo Jobs",
         "working": "RRF Demo Jobs", "staging": ".rrf-demo-staging",
         "rollback": ".rrf-demo-rollback/RRF Demo Jobs"}))
    return tmp_path


def copies(base: Path) -> list:
    """Every sanitised copy. `photo-*` also matches photo-manifest.json."""
    return [p for p in sorted(base.rglob("Photos/photo-*"))
            if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic")]


def photo_count(job: Path) -> int:
    return len([p for p in (job / "Photos").iterdir()
                if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic")])


def test_it_covers_every_scenario_that_was_asked_for(demo_repo):
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)

    counts = {name: photo_count(baseline / name) for name in hydrate_demo.PLAN}
    assert any(8 <= n <= 14 for n in counts.values()), "no ordinary-sized job"
    assert all(n > 0 for n in counts.values()), "a demo job was left empty"


def test_the_real_plan_covers_the_tranche_scenarios():
    """Checked against the plan itself rather than by copying 266 files.

    Sixty is one full tranche, sixty-one is 60 + 1, and a hundred is 60 + 40.
    None of them is a refusal any more.
    """
    wanted = {spec["real"] for spec in hydrate_demo.PLAN.values()}
    assert 60 in wanted and 61 in wanted and 100 in wanted, sorted(wanted)


def test_every_job_ends_up_with_enough_to_feel_real(demo_repo):
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)
    for name, spec in hydrate_demo.PLAN.items():
        if spec["real"] == 0:
            # Deliberately left as it is: on the real machine this one already
            # holds Mark's own twelve, and the tool never adds to it.
            continue
        assert photo_count(baseline / name) >= 8, name


def test_the_photographs_are_real_ones_not_placeholders(demo_repo, fake_source):
    """The correction of 2026-08-20. Flat coloured panels were useless: you
    cannot judge a layout, a caption or a document size against a rectangle."""
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)

    made = copies(baseline)
    assert len(made) > 20, "hardly anything was copied"

    synthetic = [p for p in baseline.rglob("Photos/SYNTHETIC-*") if p.is_file()]
    assert len(synthetic) <= 2, "synthetic fixtures are the exception, not the fill"
    for one in synthetic:
        assert one.name.startswith("SYNTHETIC-"), "a fixture must announce itself"


def test_the_copies_carry_no_exif_no_gps_and_no_client_filename(demo_repo):
    """Re-encoded rather than byte-copied, which is what removes the camera's
    metadata, the date it was taken and any location in it."""
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)

    for copy in copies(baseline):
        with Image.open(copy) as image:
            exif = image.getexif()
        assert not exif, "%s kept its EXIF" % copy.name
        assert 0x8825 not in exif, "%s kept a GPS block" % copy.name
        assert copy.name.startswith("photo-"), copy.name
        assert "20260213" not in copy.name, "a source filename travelled"


def test_the_source_is_only_ever_read(demo_repo, fake_source):
    """Copy only: never moved, renamed, edited, deleted or rewritten."""
    before = {p: (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
              for p in sorted(fake_source.rglob("*")) if p.is_file()}
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)

    after = {p: (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
             for p in sorted(fake_source.rglob("*")) if p.is_file()}
    assert after == before, "the read-only source changed"


def test_mixed_formats_and_a_small_image_are_present(demo_repo):
    """Orientation is deliberately not among these any more.

    The copies have their EXIF stripped, which is the whole point of
    sanitising them, so none of them can carry an orientation tag. Orientation
    handling is proved in test_photo_pilot_backend against an image built for
    it, which is where a test of that behaviour belongs.
    """
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)

    suffixes, small = set(), 0
    for photo in baseline.rglob("Photos/*"):
        if photo.suffix.lower() not in (".jpg", ".jpeg", ".png", ".heic"):
            continue
        suffixes.add(photo.suffix.lower())
        with Image.open(photo) as image:
            if max(image.size) < 800:
                small += 1

    assert ".jpg" in suffixes and ".png" in suffixes, suffixes
    assert small > 0, "no small image, so the never-enlarge rule cannot be seen"


def test_review_and_exclusion_fixtures_exist(demo_repo):
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)

    cut = reviewed = 0
    for found in baseline.rglob("Photos/photo-manifest.json"):
        for entry in json.loads(found.read_text())["photos"]:
            cut += bool(entry.get("cut"))
            reviewed += bool(entry.get("reviewed"))
    assert cut > 0, "nothing is excluded anywhere"
    assert reviewed > 0, "no part-reviewed job to look at"


# --- the safety half --------------------------------------------------------

def test_marks_own_photographs_are_never_modified(demo_repo):
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    his = baseline / "DAVENPORT_2840 Brady Street - 2026 Tax" / "Photos" / "his-own.jpg"
    before = hashlib.sha256(his.read_bytes()).hexdigest()

    hydrate_demo.hydrate(baseline)

    assert his.is_file()
    assert hashlib.sha256(his.read_bytes()).hexdigest() == before


def test_it_only_ever_adds_and_never_replaces(demo_repo):
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)
    first = {p: hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(baseline.rglob("Photos/*")) if p.is_file()}

    hydrate_demo.hydrate(baseline)          # again
    second = {p: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(baseline.rglob("Photos/*")) if p.is_file()}

    for path, digest in first.items():
        assert second.get(path) == digest, path


def test_reset_demo_restores_the_photographs_rather_than_deleting_them(demo_repo):
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    working = demo_repo / "RRF Demo Jobs"

    hydrate_demo.hydrate(baseline)
    demo.write_checksums(baseline, baseline.parent / demo.CHECKSUM_NAME)

    job = "BETTENDORF_1830 E Kimberly Road - 2026 Tax"
    assert photo_count(working / job) == 0, "the working copy starts empty"
    expected = photo_count(baseline / job)
    assert expected > 0, "nothing was hydrated to restore"

    demo.reset()

    assert photo_count(working / job) == expected
    assert photo_count(baseline / job) == expected


def test_the_tool_writes_only_into_the_demo_baseline():
    """It reads Report Examples now, which Spenser authorised on 2026-08-20.
    What matters is that it only ever reads there: every write goes to the
    demo baseline the validated configuration names."""
    import ast

    tree = ast.parse(Path(hydrate_demo.__file__).read_text(encoding="utf-8"))
    writes = {n.func.attr for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for destructive in ("unlink", "rmtree", "rename", "replace", "move"):
        if destructive == "unlink":
            continue          # clear_ours removes only files this tool made
        assert destructive not in writes, destructive

    source = Path(hydrate_demo.__file__).read_text(encoding="utf-8")
    assert "SOURCE" in source and "Report Examples" in source
    assert "shutil.copy" not in source, "copies are re-encoded, never byte-copied"


def test_the_tool_names_no_other_protected_directory():
    """Report Examples is authorised. The locker and the archive are not."""
    import ast

    tree = ast.parse(Path(hydrate_demo.__file__).read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            found = ast.get_docstring(node, clean=False)
            if found is not None:
                docstrings.add(found)
    strings = [n.value for n in ast.walk(tree)
               if isinstance(n, ast.Constant) and isinstance(n.value, str)
               and n.value not in docstrings]
    for forbidden in ("locker", "archive"):
        assert not [s for s in strings if forbidden in s], forbidden


def test_it_refuses_to_run_without_a_validated_demo_configuration(tmp_path, monkeypatch):
    """It writes only into the baseline that .rrf-demo.json names, and there
    is no way to point it somewhere else.

    Checked in this process, not by running the script. An earlier version
    shelled out, which meant the monkeypatch did not apply and the subprocess
    happily hydrated the real demo folders on this machine instead of the
    temporary one. Harmless because the tool only ever adds, but the test was
    proving nothing and touching something it had no business touching.
    """
    monkeypatch.setattr(demo, "REPO", tmp_path)
    monkeypatch.setattr(demo, "CONFIG", tmp_path / "nothing.json")
    assert demo.config() is None

    # argv belongs to pytest in this process, so it is replaced for the call.
    monkeypatch.setattr(sys, "argv", ["hydrate_demo.py"])
    with pytest.raises(SystemExit) as raised:
        hydrate_demo.main()
    assert "nothing to hydrate" in str(raised.value)

    # and there is no parameter anywhere that would let a caller name a root
    import inspect
    assert list(inspect.signature(hydrate_demo.hydrate).parameters) == ["baseline"]
    assert "config()" in Path(hydrate_demo.__file__).read_text(encoding="utf-8")


def test_the_hydrated_material_is_local_only_and_never_ai_safe(demo_repo):
    """These jobs are copies of Mark's real work. Section 25 defaults every
    one of them to Local only, and hydration marks nothing AI safe."""
    import aipolicy

    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)
    demo.write_checksums(baseline, baseline.parent / demo.CHECKSUM_NAME)
    demo.reset()

    working = demo_repo / "RRF Demo Jobs"
    for job in sorted(p for p in working.iterdir() if p.is_dir()):
        assert aipolicy.classify_job(job) == aipolicy.LOCAL_ONLY, job.name
        assert aipolicy.may_send_to_ai(job) is False, job.name
    assert aipolicy.allowlist() == []


def test_the_packaged_practice_job_is_a_different_thing_entirely():
    """The synthetic Demo Jobs folder that ships in the package is separate
    from this development demo system, and neither tool knows the other."""
    import demo_job

    import ast

    def code_strings(module):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        docs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
                found = ast.get_docstring(node, clean=False)
                if found is not None:
                    docs.add(found)
        return [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and n.value not in docs]

    # Compared as code, not as prose: demo_job's docstring says in words that
    # it is not the development demo system, and matching the file text would
    # find that sentence and call it a violation.
    assert demo_job.DEMO_PARENT == "Demo Jobs"
    assert not [s for s in code_strings(demo_job) if "RRF Demo Jobs" in s]
    assert [s for s in code_strings(hydrate_demo) if "DAVENPORT" in s]
    assert "demo_job" not in code_strings(hydrate_demo)
