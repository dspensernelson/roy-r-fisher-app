"""photo-manifest.json is hand-editable by design, so a broken one is an
expected condition. The answer is a 400 that names the file, never a 500."""
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import photos  # noqa: E402


def _job_with_manifest_text(tmp_path, text):
    (tmp_path / "Photos").mkdir()
    (tmp_path / "Photos" / "photo-manifest.json").write_text(text)
    return tmp_path


def test_garbage_manifest_is_a_400_not_a_crash(tmp_path):
    job = _job_with_manifest_text(tmp_path, "{not json")
    with pytest.raises(HTTPException) as err:
        photos.load_manifest(job)
    assert err.value.status_code == 400
    assert "photo-manifest.json" in err.value.detail


def test_list_shaped_manifest_is_a_400_not_a_crash(tmp_path):
    job = _job_with_manifest_text(tmp_path, "[1, 2, 3]")
    with pytest.raises(HTTPException) as err:
        photos.load_manifest(job)
    assert err.value.status_code == 400
    assert "photo-manifest.json" in err.value.detail
