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
def demo_repo(tmp_path, monkeypatch):
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


def photo_count(job: Path) -> int:
    return len([p for p in (job / "Photos").iterdir()
                if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".heic")])


def test_it_covers_every_scenario_that_was_asked_for(demo_repo):
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)

    counts = {name: photo_count(baseline / name) for name in hydrate_demo.PLAN}
    assert 60 in counts.values(), "no job holds exactly the sixty-photo maximum"
    assert 61 in counts.values(), "no job holds sixty-one, so the refusal cannot be seen"
    # An ordinary job of about a dozen. Not exactly twelve here, because on
    # the real machine that job already holds two of Mark's own photographs
    # and the plan tops it up; this fixture starts it empty.
    assert any(8 <= n <= 14 for n in counts.values()), "no ordinary-sized job"
    assert all(n > 0 for n in counts.values()), "a demo job was left empty"


def test_every_job_ends_up_with_enough_to_feel_real(demo_repo):
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)
    for name, spec in hydrate_demo.PLAN.items():
        if spec["add"] == 0:
            # Deliberately left as it is: on the real machine this one already
            # holds Mark's own twelve, and the tool never adds to it.
            continue
        assert photo_count(baseline / name) >= 8, name


def test_shapes_formats_and_orientation_are_all_present(demo_repo):
    baseline = demo_repo / ".rrf-demo-baseline" / "RRF Demo Jobs"
    hydrate_demo.hydrate(baseline)

    shapes, suffixes, rotated, small = set(), set(), 0, 0
    for photo in baseline.rglob("Photos/*"):
        if photo.suffix.lower() not in (".jpg", ".jpeg", ".png", ".heic"):
            continue
        suffixes.add(photo.suffix.lower())
        with Image.open(photo) as image:
            width, height = image.size
            shapes.add("landscape" if width > height else
                       "portrait" if height > width else "square")
            if image.getexif().get(0x0112) in (5, 6, 7, 8):
                rotated += 1
            if max(width, height) < 800:
                small += 1

    assert {"landscape", "portrait", "square"} <= shapes, shapes
    assert {".jpg", ".png"} <= suffixes, suffixes
    assert rotated > 0, "no rotated EXIF anywhere, so orientation cannot be seen"
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

    sixty = "BETTENDORF_1830 E Kimberly Road - 2026 Tax"
    assert photo_count(working / sixty) == 0, "the working copy starts empty"

    demo.reset()

    assert photo_count(working / sixty) == 60
    assert photo_count(baseline / sixty) == 60


def test_the_tool_reads_no_protected_directory():
    """Generated from nothing, so nothing client-derived can travel in."""
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
    for forbidden in ("Report Examples", "locker", "archive"):
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
