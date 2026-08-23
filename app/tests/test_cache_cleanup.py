"""The app tidies its own cache, and only its own cache.

Thumbnails moved out of Mark's job folders into app-owned storage, and nothing
ever removed them again, so the folder grew for every job and every re-crop and
never shrank. This sweeps it.

Two boundaries matter more than the sweeping does.

It only deletes things whose names are the shapes this module writes, inside
the cache root. A cache path pointed somewhere unexpected can then only ever be
a no-op, never a disaster.

It never touches a legacy `.rrf-thumbs` folder. Those sit inside Mark's own job
folders, and removing anything from one of his folders is a separate decision
that has not been made.
"""
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import thumbcache  # noqa: E402

DAY = 86400
NOW = 1_800_000_000.0


@pytest.fixture
def cache(tmp_path, monkeypatch):
    root = tmp_path / "cache"
    root.mkdir()
    monkeypatch.setenv("RRF_CACHE_DIR", str(root))
    return root


def entry(cache: Path, name: str, age_days: float, files=("photo-01-aabbccdd.jpg",)):
    """One cache folder, last used `age_days` ago."""
    folder = cache / name
    folder.mkdir()
    when = NOW - age_days * DAY
    for f in files:
        (folder / f).write_bytes(b"x" * 100)
        os.utime(folder / f, (when, when))
    return folder


HOT = "0123456789abcdef"
COLD = "fedcba9876543210"


# --- what it removes ------------------------------------------------------
def test_a_cache_folder_nobody_has_used_for_a_month_goes(cache):
    old = entry(cache, COLD, age_days=40)
    report = thumbcache.prune(now=NOW)
    assert not old.exists()
    assert report["removed"] == 1
    assert report["freed_bytes"] == 100


def test_a_cache_folder_still_in_use_stays(cache):
    fresh = entry(cache, HOT, age_days=2)
    report = thumbcache.prune(now=NOW)
    assert fresh.exists()
    assert report["removed"] == 0 and report["kept"] == 1


def test_the_newest_thumbnail_decides_for_the_whole_folder(cache):
    folder = entry(cache, HOT, age_days=40)
    recent = folder / "photo-02-11223344.jpg"
    recent.write_bytes(b"y")
    os.utime(recent, (NOW - DAY, NOW - DAY))
    thumbcache.prune(now=NOW)
    assert folder.exists(), "one photo still in use keeps the job's thumbnails"


# --- what it must never touch --------------------------------------------
def test_a_folder_that_is_not_ours_is_left_alone(cache):
    stranger = cache / "someone-elses-folder"
    stranger.mkdir()
    (stranger / "important.txt").write_bytes(b"not ours")
    os.utime(stranger / "important.txt", (NOW - 400 * DAY, NOW - 400 * DAY))
    thumbcache.prune(now=NOW)
    assert (stranger / "important.txt").exists()


def test_a_stray_file_among_our_thumbnails_saves_the_whole_folder(cache):
    folder = entry(cache, COLD, age_days=400)
    (folder / "notes.txt").write_bytes(b"put here by somebody")
    thumbcache.prune(now=NOW)
    assert folder.exists() and (folder / "notes.txt").exists()


def test_a_legacy_thumbs_folder_in_a_job_is_never_reached(tmp_path, cache):
    """It is inside one of Mark's jobs, which this never looks at."""
    job = tmp_path / "ANYTOWN_1 Main - 2026" / "Photos" / thumbcache.LEGACY_THUMB_DIR
    job.mkdir(parents=True)
    kept = job / "photo-01.jpg.jpg"
    kept.write_bytes(b"old")
    os.utime(kept, (NOW - 900 * DAY, NOW - 900 * DAY))
    entry(cache, COLD, age_days=400)
    thumbcache.prune(now=NOW)
    assert kept.exists(), "nothing is ever removed from one of his folders"


def test_a_symlinked_folder_is_not_followed(cache, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    victim = outside / "photo-01-aabbccdd.jpg"
    victim.write_bytes(b"not ours")
    os.utime(victim, (NOW - 400 * DAY, NOW - 400 * DAY))
    (cache / COLD).symlink_to(outside, target_is_directory=True)
    thumbcache.prune(now=NOW)
    assert victim.exists()


def test_a_missing_cache_is_not_an_error(tmp_path, monkeypatch):
    monkeypatch.setenv("RRF_CACHE_DIR", str(tmp_path / "never-made"))
    assert thumbcache.prune(now=NOW)["removed"] == 0


# --- how much work it may do ---------------------------------------------
def test_the_sweep_is_bounded(cache):
    for n in range(6):
        entry(cache, "%016x" % n, age_days=400)
    report = thumbcache.prune(budget=4, now=NOW)
    assert report["looked_at"] == 4
    assert report["removed"] == 4
    assert report["stopped_early"] is True
    assert len(list(cache.iterdir())) == 2, "the rest wait for the next start"


def test_a_second_sweep_finishes_what_the_first_left(cache):
    for n in range(6):
        entry(cache, "%016x" % n, age_days=400)
    thumbcache.prune(budget=4, now=NOW)
    thumbcache.prune(budget=4, now=NOW)
    assert list(cache.iterdir()) == []


# --- where it is wired in -------------------------------------------------
def test_it_runs_at_startup_and_never_delays_it():
    source = (Path(__file__).resolve().parents[1] / "run_app.py").read_text()
    assert "thumbcache.prune()" in source
    block = source[source.index("def tidy_cache():"):]
    block = block[:block.index("threading.Thread(target=tidy_cache")]
    assert "except Exception" in block, "tidying must never take the app down"
    assert "threading.Thread(target=tidy_cache, daemon=True).start()" in source
