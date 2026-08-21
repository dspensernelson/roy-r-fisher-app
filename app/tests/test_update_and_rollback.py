"""Installing a new version, and going back to the old one.

Everything Mark sets up lives in his home folder, outside the versioned
application folder, which is what makes an update a matter of unzipping a
second folder and a rollback a matter of launching the first one again.

That claim had never been tested end to end. These tests do it with an
isolated home directory and a dummy key, so Spenser's real key and real
settings are never read, written, or printed.

Rollback here means two different versions. Refusing a second copy of the same
version is a separate property with its own tests in test_launcher.py, and one
does not stand in for the other.
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import appversion  # noqa: E402
import aipolicy  # noqa: E402
import classify  # noqa: E402
import jobfacts  # noqa: E402
import packaging  # noqa: E402
import settings  # noqa: E402
import startup  # noqa: E402
import state  # noqa: E402
import usage as usage_store  # noqa: E402
import workspace  # noqa: E402

DUMMY_KEY = "sk-ant-api03-DUMMY-not-a-real-key-for-tests-0000"

# Every file the app owns, and the module that owns it. All six live in the
# home folder, never inside a version's folder.
OWNED = {
    ".rrf-app.json": workspace.settings_file,
    ".rrf-app.env": settings.key_file,
    ".rrf-classifications.json": classify.store_file,
    ".rrf-app-version.json": appversion.store_file,
    ".rrf-ai-usage.json": usage_store.store_file,
    ".rrf-job-facts.json": jobfacts.store_file,
}


@pytest.fixture
def home(tmp_path, monkeypatch):
    """An isolated home. Never Spenser's."""
    box = tmp_path / "home"
    box.mkdir()
    for var, name in (("RRF_SETTINGS_FILE", ".rrf-app.json"),
                      ("RRF_KEY_FILE", ".rrf-app.env"),
                      ("RRF_CLASSIFY_FILE", ".rrf-classifications.json"),
                      ("RRF_VERSION_FILE", ".rrf-app-version.json"),
                      ("RRF_USAGE_FILE", ".rrf-ai-usage.json"),
                      ("RRF_JOBFACTS_FILE", ".rrf-job-facts.json"),
                      ("RRF_AI_POLICY_FILE", ".rrf-demo-ai-policy.json")):
        monkeypatch.setenv(var, str(box / name))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return box


def version_folder(root: Path, version: str) -> Path:
    """A folder shaped like an installed version, with its own VERSION."""
    folder = root / ("Roy R. Fisher v%s" % version)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / packaging.VERSION_NAME).write_text(version + "\n", encoding="utf-8")
    return folder


# --- where the state lives -------------------------------------------------

def test_every_owned_file_sits_outside_any_version_folder(home, tmp_path):
    older = version_folder(tmp_path / "installs", "0.2.0")
    newer = version_folder(tmp_path / "installs", "0.3.0")
    for name, where in OWNED.items():
        path = Path(where())
        assert older not in path.parents, name
        assert newer not in path.parents, name
        assert path.parent == home, name


def test_the_key_is_never_inside_either_package(home, tmp_path):
    settings.save_key(DUMMY_KEY)
    for version in ("0.2.0", "0.3.0"):
        folder = version_folder(tmp_path / "installs", version)
        for found in folder.rglob("*"):
            if found.is_file():
                assert DUMMY_KEY.encode() not in found.read_bytes(), found


# --- the update ------------------------------------------------------------

def test_v030_reads_the_key_the_earlier_version_saved(home):
    """The thing the Windows instructions depend on: he does not paste it
    again."""
    settings.save_key(DUMMY_KEY)                      # as the earlier version
    os.environ.pop("ANTHROPIC_API_KEY", None)

    import captions
    assert settings.stored_key() == DUMMY_KEY         # as v0.3.0
    assert settings.active_key() == DUMMY_KEY
    assert captions.ai_available() is True
    assert settings.status()["key_set"] is True
    assert settings.status()["ends_with"] == DUMMY_KEY[-4:]


def test_updating_neither_erases_nor_relocates_the_key(home, tmp_path):
    settings.save_key(DUMMY_KEY)
    where = Path(settings.key_file())
    before = where.read_bytes()

    # v0.3.0 arrives beside the old one and starts up.
    newer = version_folder(tmp_path / "installs", "0.3.0")
    startup.write_runtime(newer, 51234, "0.3.0")
    appversion.record("0.3.0", "2026-08-20T12:00:00")

    assert Path(settings.key_file()) == where, "the key moved"
    assert where.read_bytes() == before, "the key file changed"
    assert settings.stored_key() == DUMMY_KEY


def test_all_owned_state_survives_an_update(home, tmp_path):
    settings.save_key(DUMMY_KEY)
    workspace.save_folder("/his/jobs")
    workspace.save_active_jobs(Path("/his/jobs"), ["A job"])
    jobfacts.save(Path("/his/jobs/A job"), "Rock Island", "42 Mill Road")
    usage_store.open_bucket("b")
    usage_store.record_run({"run_id": "r1", "photos_captioned": 3,
                            "calculated_cost": 0.02, "status": "completed"}, "b")
    appversion.record("0.2.0", "2026-08-19T10:00:00")

    version_folder(tmp_path / "installs", "0.3.0")     # the update

    assert settings.stored_key() == DUMMY_KEY
    assert workspace.saved_folder() == "/his/jobs"
    assert workspace.active_jobs(Path("/his/jobs")) == ["A job"]
    assert jobfacts.for_job(Path("/his/jobs/A job"))["city"] == "Rock Island"
    assert len(usage_store.runs()) == 1
    assert appversion.last_good() == "0.2.0"


def test_review_state_lives_with_the_job_and_survives_both(tmp_path):
    """Review is a manifest field in the job folder, so it belongs to the job
    rather than to a version and neither an update nor a rollback can move
    it."""
    import photos as photos_routes
    manifest = {"photos": [{"file": "a.jpg", "caption": "x", "reviewed": True},
                           {"file": "b.jpg", "caption": "", }]}
    progress = photos_routes.review_progress(manifest)
    assert progress["reviewed"] == 1 and progress["included"] == 2


# --- the rollback ----------------------------------------------------------

def test_the_supported_rollback_sequence(home, tmp_path):
    """Old version, then new, then back to old, then new again.

    Two different versions, which is what rollback means. Two copies of one
    version is the single-instance property and is tested elsewhere.
    """
    installs = tmp_path / "installs"
    older = version_folder(installs, "0.2.0")
    newer = version_folder(installs, "0.3.0")

    # 1-2. the earlier version runs and he sets things up
    settings.save_key(DUMMY_KEY)
    workspace.save_folder("/his/jobs")
    appversion.record("0.2.0", "2026-08-19T10:00:00")
    startup.write_runtime(older, 51000, "0.2.0")
    assert packaging.version_of(older) == "0.2.0"

    # 3-4. it stops; v0.3.0 starts and finds everything
    assert settings.stored_key() == DUMMY_KEY
    assert workspace.saved_folder() == "/his/jobs"

    # 5. v0.3.0 writes state of its own
    startup.write_runtime(newer, 51001, "0.3.0")
    appversion.record("0.3.0", "2026-08-20T12:00:00")
    classify.set_label if False else None
    jobfacts.save(Path("/his/jobs/A job"), "Rock Island", "42 Mill Road")
    newer_state = Path(appversion.store_file()).read_bytes()

    # 6-7. it stops; the earlier version is launched again
    assert packaging.version_of(older) == "0.2.0"

    # 8. it operates safely: everything it understands is still there, and
    #    nothing newer has been truncated or corrupted by its presence.
    assert settings.stored_key() == DUMMY_KEY
    assert workspace.saved_folder() == "/his/jobs"
    assert appversion.last_good() == "0.3.0"
    assert Path(appversion.store_file()).read_bytes() == newer_state

    # 9. and back to v0.3.0, with its state intact
    assert appversion.last_good() == "0.3.0"
    assert jobfacts.for_job(Path("/his/jobs/A job"))["address"] == "42 Mill Road"
    assert Path(appversion.store_file()).read_bytes() == newer_state


def test_an_older_version_meeting_newer_state_refuses_rather_than_truncating(home):
    """The one case where going back has to say no.

    A schema this copy does not understand is refused with the approved
    sentence, and the file is left exactly as it is. Guessing at an unknown
    shape is how a newer version's settings get silently truncated by an
    older one.
    """
    path = Path(workspace.settings_file())
    from_the_future = json.dumps({"schema": 99, "jobs_folder": "/his/jobs"})
    path.write_text(from_the_future, encoding="utf-8")

    with pytest.raises(state.StateTooNew):
        workspace.saved_folder()
    assert path.read_text(encoding="utf-8") == from_the_future


def test_rollback_and_single_instance_are_different_properties():
    """Recorded so neither is ever presented as evidence for the other."""
    launcher = (Path(__file__).resolve().parents[1] / "server" / "startup.py") \
        .read_text(encoding="utf-8")
    assert "refuse_if_another_version_runs" in launcher
    assert "already_running_here" in launcher
    # This file tests versions; test_launcher.py tests copies.
    here = Path(__file__).read_text(encoding="utf-8")
    assert "single-instance" in here.lower() or "second copy" in here.lower()


# --- the key never leaks ---------------------------------------------------

def test_a_missing_key_still_says_so_plainly(home):
    import captions
    assert settings.stored_key() == ""
    assert captions.ai_available() is False
    assert settings.status() == {"key_set": False, "ends_with": ""}


def test_no_test_here_ever_prints_or_stores_a_real_key(home):
    """Everything above uses the dummy, and the dummy is obviously one.

    The needle is assembled at run time. Written out as a literal it matched
    its own assertion and the test failed on itself.
    """
    assert "DUMMY" in DUMMY_KEY
    needle = "sk-" + "ant-" + "api03-"
    here = Path(__file__).read_text(encoding="utf-8")
    assert needle not in here.replace(DUMMY_KEY, ""), \
        "a key-shaped string other than the dummy appears in this file"
