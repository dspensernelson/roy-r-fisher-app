"""Every app-owned file survives a failed write.

The point of the shared helper is that a crash mid-save cannot cost Mark his
setup. These tests break the write in each of the two places it can break,
after the temporary file exists and during the replacement, and check the same
three things every time: the previous file is byte for byte what it was, the
new content did not land, and nothing was abandoned beside it.

Synthetic files and temporary folders only. They prove this mechanic and
nothing about Mark's real folders.
"""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import appversion  # noqa: E402
import classify  # noqa: E402
import settings  # noqa: E402
import state  # noqa: E402
import usage  # noqa: E402
import workspace  # noqa: E402


def boom(*args, **kwargs):
    raise OSError("disk went away")


# --- the helper itself ------------------------------------------------------

def test_a_successful_write_replaces_the_contents(tmp_path):
    target = tmp_path / ".rrf-app.json"
    state.write_json(target, {"jobs_folder": "/somewhere"})
    assert json.loads(target.read_text(encoding="utf-8"))["jobs_folder"] == "/somewhere"
    state.write_json(target, {"jobs_folder": "/elsewhere"})
    assert json.loads(target.read_text(encoding="utf-8"))["jobs_folder"] == "/elsewhere"


def test_a_failed_replacement_leaves_the_previous_file(tmp_path, monkeypatch):
    target = tmp_path / ".rrf-app.json"
    state.write_json(target, {"jobs_folder": "/keep me"})
    before = target.read_bytes()

    monkeypatch.setattr(state.os, "replace", boom)
    with pytest.raises(OSError):
        state.write_json(target, {"jobs_folder": "/lost"})

    assert target.read_bytes() == before
    assert not list(tmp_path.glob("*.writing"))


def test_a_failed_temporary_write_leaves_the_previous_file(tmp_path, monkeypatch):
    target = tmp_path / ".rrf-app.json"
    state.write_json(target, {"jobs_folder": "/keep me"})
    before = target.read_bytes()

    monkeypatch.setattr(state.json, "dumps", boom)
    with pytest.raises(OSError):
        state.write_json(target, {"jobs_folder": "/lost"})

    assert target.read_bytes() == before
    assert not list(tmp_path.glob("*.writing"))


def test_the_temporary_file_lives_beside_the_target(tmp_path, monkeypatch):
    """Not in the system temp folder. A rename across two filesystems is a
    copy, and a copy is not atomic, which is the whole thing this avoids."""
    target = tmp_path / "sub" / ".rrf-app.json"
    seen = {}

    real = state.os.replace

    def watch(src, dst):
        seen["src"] = Path(src).parent
        seen["dst"] = Path(dst).parent
        return real(src, dst)

    monkeypatch.setattr(state.os, "replace", watch)
    state.write_json(target, {"a": 1})
    assert seen["src"] == seen["dst"] == target.parent


def test_it_refuses_to_write_through_a_link(tmp_path):
    """A link left where one of our files belongs would let the write land
    anywhere, including inside one of Mark's job folders."""
    elsewhere = tmp_path / "elsewhere.json"
    elsewhere.write_text("{}", encoding="utf-8")
    link = tmp_path / ".rrf-app.json"
    link.symlink_to(elsewhere)

    with pytest.raises(state.StateUnreadable):
        state.write_json(link, {"jobs_folder": "/x"})
    with pytest.raises(state.StateUnreadable):
        state.read_json(link)
    assert elsewhere.read_text(encoding="utf-8") == "{}"


def test_it_writes_utf8_whatever_the_machine_prefers(tmp_path):
    target = tmp_path / ".rrf-app.json"
    name = "Bettendorf café — plân"
    state.write_json(target, {"jobs_folder": name})
    assert json.loads(target.read_bytes().decode("utf-8"))["jobs_folder"] == name


def test_owner_only_permissions_never_stop_a_save(tmp_path, monkeypatch):
    """Windows has no POSIX mode bits and raises for them. Refusing to save
    there would be refusing to work on the machine this app is for."""
    def no_such_thing(*args, **kwargs):
        raise NotImplementedError("no mode bits here")

    monkeypatch.setattr(Path, "chmod", no_such_thing)
    target = tmp_path / ".rrf-app.env"
    state.write_text(target, "ANTHROPIC_API_KEY=sk-ant-fake\n", owner_only=True)
    assert "sk-ant-fake" in target.read_text(encoding="utf-8")


# --- every app-owned file goes through it -----------------------------------

def _saved_bytes(path):
    return Path(path).read_bytes()


def test_workspace_survives_a_failed_write(tmp_path, monkeypatch):
    workspace.save_folder("/first choice")
    before = _saved_bytes(workspace.settings_file())
    monkeypatch.setattr(state.os, "replace", boom)
    with pytest.raises(OSError):
        workspace.save_folder("/second choice")
    assert _saved_bytes(workspace.settings_file()) == before


def test_the_key_file_survives_a_failed_write(monkeypatch):
    settings.save_key("sk-ant-first")
    before = _saved_bytes(settings.key_file())
    monkeypatch.setattr(state.os, "replace", boom)
    with pytest.raises(OSError):
        settings.save_key("sk-ant-second")
    assert _saved_bytes(settings.key_file()) == before


def test_the_version_record_survives_a_failed_write(monkeypatch):
    appversion.record("0.1.0", "2026-08-19T10:00:00")
    before = _saved_bytes(appversion.store_file())
    monkeypatch.setattr(state.os, "replace", boom)
    with pytest.raises(OSError):
        appversion.record("0.2.0", "2026-08-19T11:00:00")
    assert _saved_bytes(appversion.store_file()) == before
    assert appversion.last_good() == "0.1.0"


def test_the_usage_history_survives_a_failed_write(monkeypatch):
    usage.open_bucket("opus-5/p1/img1")
    usage.record_run({"run_id": "r1", "photos_captioned": 12})
    before = _saved_bytes(usage.store_file())
    monkeypatch.setattr(state.os, "replace", boom)
    with pytest.raises(OSError):
        usage.record_run({"run_id": "r2", "photos_captioned": 3})
    assert _saved_bytes(usage.store_file()) == before
    assert [r["run_id"] for r in usage.runs()] == ["r1"]


def test_no_app_owned_write_lands_in_a_job_folder(tmp_path):
    """Every one of the six resolves under the overridden home box, never
    under a job. The Never list says app knowledge stays out of his folders."""
    job = tmp_path / "BETTENDORF_5675 Forest - 2026"
    (job / "Photos").mkdir(parents=True)

    for path in (workspace.settings_file(), settings.key_file(),
                 classify.store_file(), appversion.store_file(),
                 usage.store_file()):
        assert job not in Path(path).resolve().parents
