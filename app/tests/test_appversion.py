"""The last version that actually started, stored and nothing more.

Task 2 owns the file. Task 3 owns the twenty-second rule, the version endpoint,
and the launcher, so the last test here is a boundary: it checks that none of
that arrived early.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import appversion  # noqa: E402
import state  # noqa: E402
import workspace  # noqa: E402


def test_it_round_trips_with_the_current_schema():
    appversion.record("0.1.0", "2026-08-19T10:00:00")
    assert appversion.last_good() == "0.1.0"
    assert appversion.qualified_at() == "2026-08-19T10:00:00"
    data = json.loads(Path(appversion.store_file()).read_text(encoding="utf-8"))
    assert data["schema"] == state.CURRENT_SCHEMA


def test_a_later_version_replaces_the_record():
    appversion.record("0.1.0", "2026-08-19T10:00:00")
    appversion.record("0.2.0", "2026-08-20T09:30:00")
    assert appversion.last_good() == "0.2.0"


def test_the_previous_record_survives_a_failed_write(monkeypatch):
    appversion.record("0.1.0", "2026-08-19T10:00:00")

    def boom(*a, **k):
        raise OSError("disk went away")

    monkeypatch.setattr(state.os, "replace", boom)
    with pytest.raises(OSError):
        appversion.record("0.2.0", "2026-08-20T09:30:00")
    assert appversion.last_good() == "0.1.0"


def test_nothing_qualifies_without_a_version_or_a_time():
    for version, when in (("", "2026-08-19"), ("0.1.0", ""), ("  ", " ")):
        with pytest.raises(ValueError):
            appversion.record(version, when)
    assert appversion.last_good() == ""


def test_it_lives_in_its_own_file_not_in_the_settings():
    """Deliberately separate. The settings file is written every time Mark
    picks a folder or edits his active jobs, so it is the one most likely to
    be caught half-written by the very crash this record exists to survive."""
    appversion.record("0.1.0", "2026-08-19T10:00:00")
    assert Path(appversion.store_file()).name == ".rrf-app-version.json"
    assert Path(appversion.store_file()) != Path(workspace.settings_file())
    settings_text = Path(workspace.settings_file()).read_text(encoding="utf-8") \
        if Path(workspace.settings_file()).is_file() else ""
    assert "0.1.0" not in settings_text


def test_task_three_behaviour_has_not_arrived_early():
    """Storage only. No timer, no endpoint, no launcher, no rollback.

    Reads the parsed module rather than its text, because the text includes a
    docstring that names the very things this checks are absent.
    """
    import ast

    tree = ast.parse(Path(appversion.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert imported == {"os", "pathlib", "state"}, imported

    called = {n.func.attr for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for forbidden in ("Timer", "sleep", "run", "bind", "listen", "open_new"):
        assert forbidden not in called, forbidden

    defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert defined == {"store_file", "read", "last_good", "qualified_at", "record"}
