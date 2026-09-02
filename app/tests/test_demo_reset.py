"""The demo reset, and everything it must refuse.

Every test builds its own repo-shaped temporary tree and points the demo
module at it, so nothing here can reach the real project, the real demo
folders, or the archival copy in ~/Documents.
"""
import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import demo  # noqa: E402
import workspace  # noqa: E402


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A stand-in project with a baseline, a working copy and a settings file."""
    monkeypatch.setattr(demo, "REPO", tmp_path)
    monkeypatch.setattr(demo, "CONFIG", tmp_path / ".rrf-demo.json")
    monkeypatch.setenv("RRF_SETTINGS_FILE", str(tmp_path / "settings.json"))

    baseline = tmp_path / ".rrf-demo-baseline" / "RRF Demo Jobs"
    (baseline / "A job" / "Photos").mkdir(parents=True)
    (baseline / "A job" / "Photos" / "a.jpg").write_bytes(b"a photo")
    (baseline / "A job" / "Photos" / "photo-manifest.json").write_text(json.dumps(
        {"job": "A job", "context": "", "report_year": 2026, "caption_style": "view",
         "photos": [{"file": "a.jpg", "caption": ""}]}, indent=2))
    (baseline / "A job" / "job-brief.md").write_text("# Job Brief - A job\n")
    (baseline / "B job").mkdir()
    (baseline / "B job" / "notes.txt").write_text("a source document")
    demo.write_checksums(baseline, baseline.parent / demo.CHECKSUM_NAME)

    working = tmp_path / "TEST JOBS"
    shutil.copytree(baseline, working)

    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "server").mkdir()
    (tmp_path / "app" / "server" / "main.py").write_text("# do not touch me")
    return tmp_path


def write_config(repo: Path, **overrides):
    body = {"demo_mode": True, "baseline": ".rrf-demo-baseline/RRF Demo Jobs",
            "working": "TEST JOBS", "staging": ".rrf-demo-staging",
            "rollback": ".rrf-demo-rollback/RRF Demo Jobs"}
    body.update(overrides)
    (repo / ".rrf-demo.json").write_text(json.dumps(body))


def dirty_it(repo: Path):
    """Make the working copy look like a test run just happened in it."""
    w = repo / "TEST JOBS"
    m = w / "A job" / "Photos" / "photo-manifest.json"
    data = json.loads(m.read_text())
    data["photos"][0]["caption"] = "View east from Brady Street"
    m.write_text(json.dumps(data, indent=2))
    (w / "A job" / "Photos" / "Photo (RRF App).docx").write_bytes(b"a built document")
    (w / "A job" / "Photos" / ".rrf-thumbs").mkdir()
    (w / "A job" / "Photos" / ".rrf-thumbs" / "a.jpg.jpg").write_bytes(b"a thumbnail")
    (w / "A job" / "Photos" / "dropped-in.jpg").write_bytes(b"added mid-test")
    (w / "C job added mid-test").mkdir()


# ------------------------------------------------------- the guard refuses --
def test_no_configuration_means_no_demo_mode(repo):
    assert demo.enabled() is False
    assert demo.status() == {"demo_mode": False}


def test_demo_mode_must_be_explicitly_true(repo):
    write_config(repo, demo_mode=False)
    assert demo.enabled() is False
    write_config(repo, demo_mode="yes")
    assert demo.enabled() is False


@pytest.mark.parametrize("role,bad", [
    ("working", "app"),
    ("working", "app/server"),
    ("working", "."),
    ("working", ".rrf-demo-baseline/RRF Demo Jobs"),
    ("baseline", "TEST JOBS"),
    ("staging", "app"),
    ("rollback", "TEST JOBS"),
])
def test_an_inside_the_repo_but_wrong_path_is_refused(repo, role, bad):
    """Being in the project is not enough. It must be the exact place."""
    write_config(repo, **{role: bad})
    assert demo.enabled() is False
    with pytest.raises(demo.DemoError):
        demo.reset()


def test_configuring_app_as_the_working_folder_does_not_touch_app(repo):
    guarded = repo / "app" / "server" / "main.py"
    before = guarded.read_bytes()
    write_config(repo, working="app")
    assert demo.enabled() is False
    with pytest.raises(demo.DemoError):
        demo.reset()
    assert guarded.read_bytes() == before
    assert (repo / "app" / "server").is_dir()


def test_an_absolute_path_is_refused(repo, tmp_path):
    write_config(repo, working=str(tmp_path / "TEST JOBS"))
    assert demo.enabled() is False


def test_a_symlink_pointing_at_the_approved_place_is_refused(repo):
    """Resolving both sides would make these look identical. They are not."""
    link = repo / "sneaky"
    link.symlink_to(repo / "TEST JOBS")
    write_config(repo, working="sneaky")
    assert demo.enabled() is False


def test_paths_must_be_distinct(repo):
    write_config(repo, staging="TEST JOBS")
    assert demo.enabled() is False


def test_a_missing_checksum_file_means_no_demo_mode(repo):
    write_config(repo)
    (repo / ".rrf-demo-baseline" / demo.CHECKSUM_NAME).unlink()
    assert demo.enabled() is False


def test_a_tampered_baseline_is_refused_and_nothing_moves(repo):
    write_config(repo)
    (repo / ".rrf-demo-baseline" / "RRF Demo Jobs" / "B job" / "notes.txt").write_text("changed")
    dirty_it(repo)
    before = demo.fingerprint(repo / "TEST JOBS")
    with pytest.raises(demo.DemoError) as caught:
        demo.reset()
    assert "baseline does not match" in caught.value.message
    assert demo.fingerprint(repo / "TEST JOBS") == before
    assert caught.value.report["working_in_place"] is True


def test_a_leftover_rollback_blocks_a_new_reset(repo):
    write_config(repo)
    (repo / ".rrf-demo-rollback" / "RRF Demo Jobs").mkdir(parents=True)
    with pytest.raises(demo.DemoError) as caught:
        demo.reset()
    assert "earlier failed reset" in caught.value.message


# ----------------------------------------------------------- it does work ---
def test_a_reset_puts_the_working_copy_back_exactly(repo):
    write_config(repo)
    dirty_it(repo)
    assert demo.fingerprint(repo / "TEST JOBS") != demo.fingerprint(
        repo / ".rrf-demo-baseline" / "RRF Demo Jobs")

    report = demo.reset()

    assert demo.fingerprint(repo / "TEST JOBS") == demo.fingerprint(
        repo / ".rrf-demo-baseline" / "RRF Demo Jobs")
    assert report["files"] == 4


def test_everything_a_test_run_left_behind_is_gone(repo):
    write_config(repo)
    dirty_it(repo)
    demo.reset()
    w = repo / "TEST JOBS"

    manifest = json.loads((w / "A job" / "Photos" / "photo-manifest.json").read_text())
    assert all(not p["caption"] for p in manifest["photos"])
    assert not list(w.rglob("Photo (RRF App)*.docx"))
    assert not list(w.rglob(".rrf-thumbs"))
    assert not (w / "A job" / "Photos" / "dropped-in.jpg").exists()
    assert not (w / "C job added mid-test").exists()
    # and the real material is back
    assert (w / "A job" / "Photos" / "a.jpg").read_bytes() == b"a photo"
    assert (w / "B job" / "notes.txt").read_text() == "a source document"


def test_a_successful_reset_leaves_no_backups_at_all(repo):
    write_config(repo)
    for _ in range(3):
        dirty_it(repo)
        demo.reset()
    assert not (repo / ".rrf-demo-rollback").exists()
    assert not (repo / ".rrf-demo-staging").exists()
    leftovers = [p.name for p in repo.iterdir() if p.name.startswith(".rrf-demo")]
    assert sorted(leftovers) == [".rrf-demo-baseline", ".rrf-demo.json"]


def test_the_restored_folder_can_be_written_to(repo):
    """The baseline is read-only. Its copy must not inherit that."""
    for p in (repo / ".rrf-demo-baseline").rglob("*"):
        p.chmod(0o444 if p.is_file() else 0o555)
    write_config(repo)
    demo.reset()
    m = repo / "TEST JOBS" / "A job" / "Photos" / "photo-manifest.json"
    m.write_text(m.read_text())          # would raise if it came back read-only
    (repo / "TEST JOBS" / "A job" / "Photos" / "new.jpg").write_bytes(b"x")


def test_it_clears_the_two_settings_and_removes_an_empty_file(repo):
    write_config(repo)
    workspace.save_folder(str(repo / "TEST JOBS"))
    workspace.save_active_jobs(repo / "TEST JOBS", ["A job"])
    assert Path(workspace.settings_file()).is_file()

    demo.reset()

    assert workspace.saved_folder() == ""
    assert workspace.active_jobs(repo / "TEST JOBS") == []
    assert not Path(workspace.settings_file()).exists()


def test_other_settings_survive_and_the_file_stays(repo):
    write_config(repo)
    Path(workspace.settings_file()).write_text(json.dumps(
        {"jobs_folder": str(repo / "TEST JOBS"), "something_else": "keep me"}),
        encoding="utf-8")
    demo.reset()
    left = json.loads(Path(workspace.settings_file()).read_text(encoding="utf-8"))
    # The schema stamp Task 2 added is bookkeeping, not one of his settings.
    # What this test is for is unchanged: the reset takes the demo's own keys
    # and leaves every other setting exactly where it was.
    assert {k: v for k, v in left.items() if k != "schema"} == {"something_else": "keep me"}
    assert left["schema"] == 1


def test_it_never_opens_the_key_file(repo, tmp_path, monkeypatch):
    key = tmp_path / "key.env"
    key.write_text("ANTHROPIC_API_KEY=sk-ant-not-a-real-key\n")
    monkeypatch.setenv("RRF_KEY_FILE", str(key))
    write_config(repo)
    before = key.read_bytes()
    demo.reset()
    assert key.read_bytes() == before


def test_the_baseline_is_untouched_by_a_reset(repo):
    write_config(repo)
    before = demo.fingerprint(repo / ".rrf-demo-baseline" / "RRF Demo Jobs")
    dirty_it(repo)
    demo.reset()
    assert demo.fingerprint(repo / ".rrf-demo-baseline" / "RRF Demo Jobs") == before


def test_it_restores_the_baseline_inclusion_state(repo):
    """Photos cut during a test run come back included, because inclusion
    lives in the manifest and the manifest comes from the baseline."""
    write_config(repo)
    m = repo / "TEST JOBS" / "A job" / "Photos" / "photo-manifest.json"
    data = json.loads(m.read_text())
    data["photos"][0]["cut"] = True
    m.write_text(json.dumps(data, indent=2))
    assert json.loads(m.read_text())["photos"][0]["cut"] is True

    demo.reset()

    after = json.loads(m.read_text())
    assert all("cut" not in e for e in after["photos"])


def test_two_runs_start_from_the_same_place(repo):
    write_config(repo)
    dirty_it(repo)
    demo.reset()
    first = demo.fingerprint(repo / "TEST JOBS")
    dirty_it(repo)
    demo.reset()
    assert demo.fingerprint(repo / "TEST JOBS") == first
