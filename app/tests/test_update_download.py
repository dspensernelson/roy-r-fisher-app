"""Fetching the package, and refusing to trust it until it has been checked.

The promise here is the one Spenser called non-negotiable: the app downloads a
zip and then runs code out of it, so the package is checked before anything
from it is executed. These tests cover the first of the two checks, the
published SHA-256 over the whole file.

What that check honestly does: it catches a damaged or incomplete download. An
interrupted transfer, a truncated file, a flipped byte. What it does not do,
and every one of these tests is written knowing it: without code signing it
does not prove who built the package. Anyone able to replace the zip in the
bucket can replace the checksum beside it. That is an accepted and named limit,
not an oversight.

Every failing case asserts the same two things afterwards: the download is gone
and nothing outside the scratch folder was touched.
"""
import hashlib
import json
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))

import updates  # noqa: E402

ZIP_NAME = "Roy R. Fisher v0.5.4.zip"
BODY = b"not really a zip, but it is bytes and it has a hash" * 200


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def serve_package(fake_bucket, body=BODY, digest=None):
    """Put a package, its sidecar, and a pointer file into the bucket."""
    fake_bucket.put(ZIP_NAME, body)
    fake_bucket.put(ZIP_NAME + ".sha256", "%s  %s\n" % (digest or sha(body), ZIP_NAME))
    fake_bucket.put(updates.LATEST_NAME, json.dumps(
        {"version": "0.5.4", "zip": ZIP_NAME, "size": len(body)}))


def fetch(size=None):
    """Download the package the bucket is serving into the scratch folder."""
    updates.clear_scratch()
    target = updates.download_dir() / ZIP_NAME
    updates.fetch_to_file(updates.file_url(ZIP_NAME), target,
                          len(BODY) if size is None else size)
    return target


# --- the ordinary case -----------------------------------------------------
def test_a_good_download_matches_its_published_checksum(fake_bucket):
    serve_package(fake_bucket)
    target = fetch()
    assert target.read_bytes() == BODY
    assert updates.verify_download(target, ZIP_NAME) == sha(BODY)


def test_the_scratch_folder_is_in_his_home_and_not_among_the_versions(monkeypatch):
    """install_windows reads every folder in the install home as a version and
    prunes the oldest. A scratch folder there would eventually be deleted as
    one."""
    monkeypatch.delenv("RRF_DOWNLOAD_DIR", raising=False)
    assert updates.download_dir() == Path.home() / updates.DOWNLOAD_DIR_NAME
    assert updates.DOWNLOAD_DIR_NAME.startswith(".")


def test_the_scratch_folder_is_cleared_at_the_start_of_an_attempt(fake_bucket):
    """At the start, not the end: the process that finishes an update runs out
    of this folder and cannot delete the ground it stands on."""
    updates.clear_scratch()
    (updates.download_dir() / "left over.txt").write_text("old", encoding="utf-8")
    updates.clear_scratch()
    assert list(updates.download_dir().iterdir()) == []


# --- the checksum ----------------------------------------------------------
def test_a_truncated_download_is_refused(fake_bucket):
    serve_package(fake_bucket)
    target = fetch()
    target.write_bytes(BODY[:-20])
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.verify_download(target, ZIP_NAME)
    assert "did not arrive intact" in refused.value.message


def test_one_flipped_byte_is_refused(fake_bucket):
    """Same length, different contents. Size alone would not notice this."""
    serve_package(fake_bucket)
    target = fetch()
    damaged = bytearray(BODY)
    damaged[17] ^= 0xFF
    target.write_bytes(bytes(damaged))
    with pytest.raises(updates.UpdateRefused):
        updates.verify_download(target, ZIP_NAME)


def test_a_missing_sidecar_is_refused_and_never_skipped(fake_bucket):
    """"We could not check it" and "it is fine" are the two answers this must
    never confuse."""
    fake_bucket.put(ZIP_NAME, BODY)
    target = fetch()
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.verify_download(target, ZIP_NAME)
    assert "could not be checked" in refused.value.message


@pytest.mark.parametrize("line", [
    "", "   ", "no hash here\n", "zzzz  file.zip\n",
    "abc123  file.zip\n",
    "30daa76043de030ca9e95a923fc35376228cd77b0790fafd1ac0c94f51cde15  f.zip\n",
])
def test_a_malformed_sidecar_is_refused(fake_bucket, line):
    fake_bucket.put(ZIP_NAME, BODY)
    fake_bucket.put(ZIP_NAME + ".sha256", line)
    target = fetch()
    with pytest.raises(updates.UpdateRefused):
        updates.verify_download(target, ZIP_NAME)


def test_the_sidecar_is_read_the_way_sha256sum_writes_it(fake_bucket):
    """Hash, two spaces, filename. Only the first field is read."""
    assert updates.read_sidecar(
        "%s  Roy R. Fisher v0.5.4.zip\n" % sha(BODY)) == sha(BODY)
    assert updates.read_sidecar("%s\n" % sha(BODY).upper()) == sha(BODY)


# --- the network -----------------------------------------------------------
def test_a_bucket_that_is_not_there_refuses_plainly(monkeypatch, tmp_path):
    monkeypatch.setenv("RRF_UPDATE_BUCKET", "http://127.0.0.1:9")
    monkeypatch.setenv("RRF_DOWNLOAD_DIR", str(tmp_path / "scratch"))
    updates.clear_scratch()
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.fetch_to_file(updates.file_url(ZIP_NAME),
                              updates.download_dir() / ZIP_NAME, len(BODY))
    assert "could not be downloaded" in refused.value.message
    assert "Nothing has changed" in refused.value.message


def test_a_file_that_keeps_arriving_is_stopped(fake_bucket):
    """A body far larger than announced is not our package, and reading it to
    the end would be filling his disk on a stranger's say-so."""
    fake_bucket.put(ZIP_NAME, b"x" * (updates.CHUNK * 6))
    updates.clear_scratch()
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.fetch_to_file(updates.file_url(ZIP_NAME),
                              updates.download_dir() / ZIP_NAME, 100)
    assert "did not match the size" in refused.value.message


def test_progress_is_reported_while_it_downloads(fake_bucket):
    serve_package(fake_bucket)
    seen = []
    updates.clear_scratch()
    updates.fetch_to_file(updates.file_url(ZIP_NAME),
                          updates.download_dir() / ZIP_NAME, len(BODY),
                          on_progress=seen.append)
    assert seen and seen[-1] == len(BODY)
    assert seen == sorted(seen)


# --- cancelling ------------------------------------------------------------
def test_cancel_stops_the_download(fake_bucket):
    fake_bucket.put(ZIP_NAME, b"y" * (updates.CHUNK * 4))
    updates.clear_scratch()
    updates.request_cancel()
    try:
        with pytest.raises(updates.UpdateRefused) as refused:
            updates.fetch_to_file(updates.file_url(ZIP_NAME),
                                  updates.download_dir() / ZIP_NAME,
                                  updates.CHUNK * 4,
                                  cancelled=updates.cancelled)
        assert "was stopped" in refused.value.message
        assert "Nothing has changed" in refused.value.message
    finally:
        updates.end_run()
        updates._cancel.clear()


def test_a_cancel_does_not_survive_into_the_next_run():
    updates.request_cancel()
    assert updates.cancelled()
    updates.begin_run("0.5.4", 100)
    assert not updates.cancelled()
    updates.end_run()


# --- room on the disk ------------------------------------------------------
def test_three_copies_of_the_package_are_budgeted_for():
    """The zip, the tree it unpacks into, and the copy install_windows makes.
    Measured 2026-08-28: 53.3 MB unpacks to 116.8 MB."""
    zip_size = 55939858
    needed = updates.space_needed(zip_size)
    assert needed > zip_size * 5, "one copy budgeted where three are made"
    assert needed < zip_size * 8, "budgeting far more than three copies"


def test_too_little_room_refuses_before_the_network_is_touched(monkeypatch, tmp_path):
    monkeypatch.setenv("RRF_DOWNLOAD_DIR", str(tmp_path / "scratch"))

    class Tiny(object):
        free = 1000

    monkeypatch.setattr(updates.shutil, "disk_usage", lambda _p: Tiny)

    def never(*_a, **_k):
        raise AssertionError("the network was touched before the space check")

    monkeypatch.setattr(updates.urllib.request, "urlopen", never)
    with pytest.raises(updates.UpdateRefused) as refused:
        updates.check_space(55939858)
    assert "not enough room" in refused.value.message
    assert "nothing has changed" in refused.value.message.lower()


def test_enough_room_is_not_a_refusal(monkeypatch, tmp_path):
    monkeypatch.setenv("RRF_DOWNLOAD_DIR", str(tmp_path / "scratch"))

    class Plenty(object):
        free = 100 * 1024 * 1024 * 1024

    monkeypatch.setattr(updates.shutil, "disk_usage", lambda _p: Plenty)
    updates.check_space(55939858)


def test_a_disk_that_cannot_be_measured_is_not_treated_as_full(monkeypatch, tmp_path):
    """Refusing on an unreadable disk would stop an update that would have
    worked. A genuinely full disk fails on the write instead, plainly."""
    monkeypatch.setenv("RRF_DOWNLOAD_DIR", str(tmp_path / "scratch"))

    def unmeasurable(_p):
        raise OSError("no idea")

    monkeypatch.setattr(updates.shutil, "disk_usage", unmeasurable)
    updates.check_space(55939858)


# --- the progress light ----------------------------------------------------
def test_the_run_reports_where_it_has_got_to():
    updates.begin_run("0.5.4", 500)
    assert updates.running()
    updates.advance(120)
    updates.set_stage(updates.CHECKING)
    found = updates.run_state()
    assert found["stage"] == updates.CHECKING
    assert (found["done"], found["total"], found["version"]) == (120, 500, "0.5.4")
    updates.end_run()
    assert not updates.running()


def test_a_failure_leaves_its_sentence_on_the_screen():
    """A failure that cleared itself would leave him looking at a screen that
    had quietly gone back to normal."""
    updates.begin_run("0.5.4", 500)
    updates.fail_run("The update did not arrive intact.")
    found = updates.run_state()
    assert not found["running"]
    assert found["error"] == "The update did not arrive intact."
    updates.end_run()
