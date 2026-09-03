"""The app says who it is, because the bucket refuses anything that does not.

Measured 2026-09-02, on Spenser's Windows virtual machine and then on his Mac.
Once the certificate fault was fixed, the connection completed and Cloudflare
answered:

    urllib.error.HTTPError: HTTP Error 403: Forbidden

Not a network fault and not a certificate fault. Cloudflare refuses the name
`urllib.request` gives itself, `Python-urllib/3.x`, as bot traffic. Measured
against the real bucket the same day: the default name is refused, and any
other name is served.

**This was never a Windows problem.** It failed the same way on the Mac and
would have failed on any machine. Between this and the certificate fault, the
update check had never once succeeded anywhere, and both were invisible for
the same reason: `fetch_text` swallows every failure and answers "", which
reads as "nothing is being offered".

`conftest.FakeBucket` cannot catch this on its own, because it answers
anything. So the test that matters is the one below that reads the header the
app actually sent.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import updates  # noqa: E402


def test_the_app_does_not_call_itself_python():
    """The exact string Cloudflare refused. If this ever comes back, the
    update check silently stops working everywhere and nothing else says so."""
    assert "Python-urllib" not in updates.USER_AGENT
    assert updates.USER_AGENT.strip() != ""


def test_reading_the_pointer_file_says_who_we_are(fake_bucket):
    fake_bucket.put("latest.json",
                    '{"version": "9.9.9", "zip": "x.zip", "size": 1}')
    body = updates.fetch_text(updates.file_url("latest.json"), 4096)

    assert '"version": "9.9.9"' in body
    assert fake_bucket.seen, "no request reached the bucket at all"
    sent = fake_bucket.seen[-1].get("User-Agent", "")
    assert sent == updates.USER_AGENT
    assert "Python-urllib" not in sent


def test_downloading_the_package_says_who_we_are(fake_bucket, tmp_path):
    fake_bucket.put("thing.zip", b"abcdefgh")
    updates.fetch_to_file(updates.file_url("thing.zip"),
                          tmp_path / "thing.zip", 8)

    assert (tmp_path / "thing.zip").read_bytes() == b"abcdefgh"
    sent = fake_bucket.seen[-1].get("User-Agent", "")
    assert sent == updates.USER_AGENT
    assert "Python-urllib" not in sent


def test_a_refusal_is_still_swallowed(monkeypatch):
    """Saying who we are does not change the rule that nothing here raises.
    A bucket that refuses us anyway must still leave the app running."""
    import urllib.error

    def refused(*_a, **_k):
        raise urllib.error.HTTPError("u", 403, "Forbidden", {}, None)

    monkeypatch.setattr(updates.urllib.request, "urlopen", refused)
    assert updates.fetch_text("https://example.invalid/latest.json", 4096) == ""


def test_the_whole_check_still_answers_nothing_when_refused(monkeypatch, tmp_path):
    import urllib.error

    def refused(*_a, **_k):
        raise urllib.error.HTTPError("u", 403, "Forbidden", {}, None)

    monkeypatch.setattr(updates.urllib.request, "urlopen", refused)
    (tmp_path / "VERSION").write_text("0.1.0")
    assert updates.look(tmp_path) == {}


# --- the check says what it saw ---------------------------------------------
# Both faults above reported as "nothing is being offered", which is what a
# healthy check finding nothing reports. On screen those stay the same, which
# is right for Mark. In the log they must not, which is what these prove.

def _log_text(tmp_path, monkeypatch):
    path = tmp_path / ".rrf-app.log"
    monkeypatch.setenv("RRF_LOG_FILE", str(path))
    return path


def test_a_refused_bucket_is_written_down(fake_bucket, tmp_path, monkeypatch):
    log = _log_text(tmp_path, monkeypatch)
    (tmp_path / "VERSION").write_text("0.1.0")
    updates.look(tmp_path)               # bucket serves no latest.json
    assert "update check reached nothing" in log.read_text()


def test_a_newer_version_is_written_down(fake_bucket, tmp_path, monkeypatch):
    log = _log_text(tmp_path, monkeypatch)
    (tmp_path / "VERSION").write_text("0.1.0")
    fake_bucket.put("latest.json",
                    '{"version": "9.9.9", "zip": "x.zip", "size": 1}')
    updates.look(tmp_path)
    text = log.read_text()
    assert "update check found a newer version" in text
    assert "offered=9.9.9" in text


def test_nothing_newer_is_written_down(fake_bucket, tmp_path, monkeypatch):
    log = _log_text(tmp_path, monkeypatch)
    (tmp_path / "VERSION").write_text("9.9.9")
    fake_bucket.put("latest.json",
                    '{"version": "0.1.0", "zip": "x.zip", "size": 1}')
    updates.look(tmp_path)
    assert "update check found nothing newer" in log.read_text()


def test_the_bucket_is_asked_once_per_check(fake_bucket, tmp_path, monkeypatch):
    """Writing down what it saw must not cost a second round trip. Her
    machine reads this over a network."""
    _log_text(tmp_path, monkeypatch)
    (tmp_path / "VERSION").write_text("0.1.0")
    fake_bucket.put("latest.json",
                    '{"version": "9.9.9", "zip": "x.zip", "size": 1}')
    fake_bucket.seen.clear()
    updates.look(tmp_path)
    assert len(fake_bucket.seen) == 1, "the check asked the bucket twice"
