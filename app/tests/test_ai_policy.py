"""Which demo photographs may leave this machine, and why naming cannot decide it.

Everything here builds its own repo-shaped temporary tree, the same way the
demo reset tests do, so nothing can reach the real project or the real demo
folders.

The rule being pinned is default-deny with a derived root: permission needs
live demo validation, the job sitting under that validated root, and its exact
name on the allowlist. Anything less is a refusal, and a refusal can be reached
from a remembered root while permission can never be.
"""
import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import aipolicy  # noqa: E402
import demo  # noqa: E402
import state  # noqa: E402


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A stand-in project with a valid baseline and working demo folder."""
    monkeypatch.setattr(demo, "REPO", tmp_path)
    monkeypatch.setattr(demo, "CONFIG", tmp_path / ".rrf-demo.json")
    monkeypatch.setenv("RRF_SETTINGS_FILE", str(tmp_path / "settings.json"))

    baseline = tmp_path / ".rrf-demo-baseline" / "RRF Demo Jobs"
    for name in ("A job", "B job"):
        (baseline / name / "Photos").mkdir(parents=True)
        (baseline / name / "Photos" / "a.jpg").write_bytes(b"a photo")
    demo.write_checksums(baseline, baseline.parent / demo.CHECKSUM_NAME)
    shutil.copytree(baseline, tmp_path / "RRF Demo Jobs")

    (tmp_path / "app" / "server").mkdir(parents=True)
    (tmp_path / "app" / "server" / "main.py").write_text("# do not touch me")
    return tmp_path


def write_config(repo: Path, **overrides):
    body = {"demo_mode": True, "baseline": ".rrf-demo-baseline/RRF Demo Jobs",
            "working": "RRF Demo Jobs", "staging": ".rrf-demo-staging",
            "rollback": ".rrf-demo-rollback/RRF Demo Jobs"}
    body.update(overrides)
    (repo / ".rrf-demo.json").write_text(json.dumps(body))


def job(repo: Path, name: str) -> Path:
    return repo / "RRF Demo Jobs" / name


# --- the root is derived, never supplied ------------------------------------

def test_a_valid_configuration_derives_the_exact_approved_root(repo):
    write_config(repo)
    assert aipolicy.validated_demo_root() == (repo / "RRF Demo Jobs").resolve()


def test_there_is_no_way_to_supply_a_root_by_hand(repo):
    """The enforcement that matters. If any function took a path, a screen, a
    test helper, or a future caller could name a folder and have it trusted."""
    import ast, inspect

    tree = ast.parse(Path(aipolicy.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and "root" in node.name:
            args = [a.arg for a in node.args.args]
            assert args == [], "%s takes %s" % (node.name, args)

    assert inspect.signature(aipolicy.remember_root).parameters == {}
    assert inspect.signature(aipolicy.validated_demo_root).parameters == {}


def test_an_invalid_configuration_yields_local_only(repo):
    """No config file at all: no demo mode, so nothing can be AI safe."""
    assert demo.enabled() is False
    assert aipolicy.validated_demo_root() is None
    assert aipolicy.may_send_to_ai(job(repo, "A job")) is False


@pytest.mark.parametrize("broken", [
    {"demo_mode": False},
    {"working": "somewhere else"},
    {"working": "/absolute/RRF Demo Jobs"},
    {"baseline": "RRF Demo Jobs"},
])
def test_every_broken_configuration_refuses(repo, broken):
    write_config(repo, **broken)
    aipolicy.mark_ai_safe  # the allowlist route is closed too
    assert aipolicy.validated_demo_root() is None
    assert aipolicy.may_send_to_ai(job(repo, "A job")) is False


def test_an_unvalidated_root_cannot_be_marked_ai_safe(repo):
    write_config(repo, demo_mode=False)
    with pytest.raises(ValueError):
        aipolicy.mark_ai_safe("A job")


# --- default deny -----------------------------------------------------------

def test_every_job_under_the_root_starts_local_only(repo):
    write_config(repo)
    for name in ("A job", "B job"):
        assert aipolicy.classify_job(job(repo, name)) == aipolicy.LOCAL_ONLY
        assert aipolicy.may_send_to_ai(job(repo, name)) is False


def test_only_an_allowlisted_job_becomes_ai_safe(repo):
    write_config(repo)
    aipolicy.mark_ai_safe("A job")
    assert aipolicy.classify_job(job(repo, "A job")) == aipolicy.AI_SAFE
    assert aipolicy.may_send_to_ai(job(repo, "A job")) is True
    assert aipolicy.may_send_to_ai(job(repo, "B job")) is False


def test_a_renamed_job_falls_back_to_local_only(repo):
    write_config(repo)
    aipolicy.mark_ai_safe("A job")
    (repo / "RRF Demo Jobs" / "A job").rename(repo / "RRF Demo Jobs" / "A job renamed")
    assert aipolicy.may_send_to_ai(job(repo, "A job renamed")) is False
    assert aipolicy.classify_job(job(repo, "A job renamed")) == aipolicy.LOCAL_ONLY


def test_a_new_job_is_local_only(repo):
    write_config(repo)
    aipolicy.mark_ai_safe("A job")
    (repo / "RRF Demo Jobs" / "C job added later").mkdir()
    assert aipolicy.may_send_to_ai(job(repo, "C job added later")) is False


def test_a_moved_job_is_no_longer_ai_safe(repo):
    write_config(repo)
    aipolicy.mark_ai_safe("A job")
    moved = repo / "somewhere else" / "A job"
    moved.parent.mkdir()
    shutil.move(str(repo / "RRF Demo Jobs" / "A job"), str(moved))
    assert aipolicy.may_send_to_ai(moved) is False


def test_an_unrecognised_name_under_the_root_is_local_only(repo):
    write_config(repo)
    aipolicy.mark_ai_safe("A job")
    assert aipolicy.may_send_to_ai(job(repo, "Not a job we know")) is False


# --- production jobs are untouched -----------------------------------------

def test_a_production_job_outside_the_root_is_unaffected(repo, tmp_path):
    write_config(repo)
    aipolicy.mark_ai_safe("A job")
    real = tmp_path / "Marks Jobs" / "BETTENDORF_5675 Forest - 2026"
    real.mkdir(parents=True)
    assert aipolicy.classify_job(real) == aipolicy.NOT_DEMO
    assert aipolicy.may_send_to_ai(real) is False


# --- Reset Demo -------------------------------------------------------------

def test_reset_demo_does_not_erase_or_weaken_the_policy(repo):
    write_config(repo)
    aipolicy.mark_ai_safe("A job")
    before = Path(aipolicy.policy_file()).read_bytes()

    demo.reset()

    assert Path(aipolicy.policy_file()).read_bytes() == before
    assert aipolicy.allowlist() == ["A job"]
    assert aipolicy.may_send_to_ai(job(repo, "B job")) is False


def test_a_remembered_root_can_restrict_but_never_permit(repo):
    """Demo validation failing must not turn a demo job into a production one
    and quietly stop restricting it."""
    write_config(repo)
    aipolicy.mark_ai_safe("A job")
    assert aipolicy.may_send_to_ai(job(repo, "A job")) is True

    (repo / ".rrf-demo.json").unlink()          # validation now fails
    assert aipolicy.classify_job(job(repo, "A job")) == aipolicy.LOCAL_ONLY
    assert aipolicy.may_send_to_ai(job(repo, "A job")) is False


# --- privacy ----------------------------------------------------------------

def test_the_policy_file_holds_no_client_content(repo, tmp_path):
    write_config(repo)
    aipolicy.mark_ai_safe("A job")
    real = tmp_path / "Marks Jobs" / "BETTENDORF_5675 Forest - 2026"
    real.mkdir(parents=True)
    aipolicy.classify_job(real)

    raw = Path(aipolicy.policy_file()).read_bytes()
    for forbidden in (b"BETTENDORF", b"5675 Forest", b"Bettendorf", b"sk-ant",
                      b".jpg", b"View of", b"caption"):
        assert forbidden not in raw, forbidden

    data = json.loads(raw.decode("utf-8"))
    assert set(data) == {"schema", "demo_root", "ai_safe_jobs"}


def test_the_policy_carries_the_current_schema(repo):
    write_config(repo)
    aipolicy.mark_ai_safe("A job")
    data = json.loads(Path(aipolicy.policy_file()).read_text(encoding="utf-8"))
    assert data["schema"] == state.CURRENT_SCHEMA


# --- the Task 4 boundary ----------------------------------------------------

def test_task_two_introduces_no_client_and_no_request():
    """This module decides. It must not send, and it must not be able to."""
    import ast

    tree = ast.parse(Path(aipolicy.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported == {"os", "pathlib", "demo", "state"}, imported
    for forbidden in ("anthropic", "httpx", "requests", "urllib", "captions"):
        assert forbidden not in imported


def test_the_caption_route_is_not_guarded_yet_and_task_four_must_do_it():
    """A deliberate record, not an oversight. Task 2 builds the policy and
    Task 4 wires it in, so until that lands nothing consults this and no
    report may describe the caption route as guarded. When Task 4 lands, this
    test is the one that should fail and be rewritten."""
    main_source = (Path(__file__).resolve().parents[1] / "server" / "main.py") \
        .read_text(encoding="utf-8")
    assert "aipolicy" not in main_source

    # And the thing Task 4 has to call is already here, ready, named, and
    # asks permission rather than asking for a refusal.
    assert aipolicy.may_send_to_ai.__doc__
    assert callable(aipolicy.may_send_to_ai)
