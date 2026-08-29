"""Learning that a newer version exists, and refusing to learn nonsense.

Every one of these asserts the same promise from a different angle: whatever
the bucket does, the app carries on. Mark is remote, he will not debug
anything, and an update check that can take the app down is worse than no
update check at all.

A real HTTP server on a loopback port stands in for the bucket. That is a
narrow mechanic, which is what synthetic fixtures are allowed to prove: it
tests the reading, the validating, and the refusing, and it claims nothing
about Cloudflare or about Mark's network.
"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))

import packaging  # noqa: E402
import updates  # noqa: E402


class Bucket:
    """A stand-in bucket. Serves whatever it is told to, including nonsense."""

    def __init__(self):
        self.files = {}
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                from urllib.parse import unquote
                name = unquote(self.path.lstrip("/"))
                body = outer.files.get(name)
                if body is None:
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        # A short poll interval, because the default is half a second and
        # shutdown waits for it. Thirty-eight tests each paying that is nineteen
        # seconds added to a suite that runs in twenty-seven.
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01},
            daemon=True)
        self.thread.start()

    @property
    def url(self):
        return "http://127.0.0.1:%d" % self.server.server_address[1]

    def put(self, name, body):
        self.files[name] = body if isinstance(body, bytes) else body.encode("utf-8")

    def put_latest(self, **fields):
        self.put(updates.LATEST_NAME, json.dumps(fields))

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def bucket(monkeypatch):
    made = Bucket()
    monkeypatch.setenv("RRF_UPDATE_BUCKET", made.url)
    updates.forget()
    yield made
    made.close()
    updates.forget()


@pytest.fixture
def installed(tmp_path):
    """A folder shaped like an installed package: it has a VERSION and it has
    no app/tests, which is what tells a package from a checkout."""
    root = tmp_path / "program"
    root.mkdir()
    (root / "VERSION").write_text("0.5.3\n", encoding="utf-8")
    return root


GOOD = {"version": "0.5.4", "zip": "Roy R. Fisher v0.5.4.zip", "size": 55939858}


# --- the ordinary case -----------------------------------------------------
def test_a_newer_version_is_offered(bucket, installed):
    bucket.put_latest(**GOOD)
    assert updates.available(installed) == GOOD


def test_the_running_version_is_not_an_update(bucket, installed):
    bucket.put_latest(version="0.5.3", zip="Roy R. Fisher v0.5.3.zip", size=100)
    assert updates.available(installed) == {}


def test_an_older_version_is_not_an_update(bucket, installed):
    bucket.put_latest(version="0.5.2", zip="Roy R. Fisher v0.5.2.zip", size=100)
    assert updates.available(installed) == {}


def test_ten_is_newer_than_nine_here_too(bucket, installed):
    (installed / "VERSION").write_text("0.9.0\n", encoding="utf-8")
    bucket.put_latest(version="0.10.0", zip="Roy R. Fisher v0.10.0.zip", size=100)
    assert updates.available(installed)["version"] == "0.10.0"


# --- a bucket that says nothing usable -------------------------------------
def test_an_empty_bucket_offers_nothing(bucket, installed):
    assert updates.available(installed) == {}


def test_a_bucket_that_is_not_there_offers_nothing(monkeypatch, installed):
    """Nothing listening at all. This is Mark with no internet, and it must
    look exactly like the bucket being empty."""
    monkeypatch.setenv("RRF_UPDATE_BUCKET", "http://127.0.0.1:9")
    assert updates.available(installed) == {}


def test_a_timeout_offers_nothing(monkeypatch, bucket, installed):
    import socket

    def slow(*_args, **_kwargs):
        raise socket.timeout("too slow")

    monkeypatch.setattr(updates.urllib.request, "urlopen", slow)
    assert updates.available(installed) == {}


def test_html_instead_of_json_offers_nothing(bucket, installed):
    bucket.put(updates.LATEST_NAME, "<html><body>404 not found</body></html>")
    assert updates.available(installed) == {}


def test_a_body_larger_than_a_pointer_file_offers_nothing(bucket, installed):
    """A pointer file is a few hundred bytes. Anything bigger is not one, and
    reading an unbounded body on the startup path is how a slow morning
    becomes a hung app."""
    padded = dict(GOOD)
    padded["padding"] = "x" * (updates.MAX_LATEST_BYTES + 100)
    bucket.put(updates.LATEST_NAME, json.dumps(padded))
    assert updates.available(installed) == {}


# --- a bucket that says something wrong ------------------------------------
@pytest.mark.parametrize("version", ["", "   ", "latest", "v0.5.4", None, 4, True])
def test_an_unusable_version_offers_nothing(bucket, installed, version):
    bucket.put_latest(version=version, zip="a.zip", size=100)
    assert updates.available(installed) == {}


@pytest.mark.parametrize("name", [
    "../evil.zip",
    "..\\evil.zip",
    "/etc/passwd.zip",
    "http://elsewhere.example/evil.zip",
    "sub/folder.zip",
    "evil.zip?x=1",
    "evil.zip#f",
    ".hidden.zip",
    "not-a-package.txt",
    "",
    None,
    17,
])
def test_a_filename_that_could_point_elsewhere_offers_nothing(bucket, installed, name):
    """The value is joined onto a URL. A name carrying a slash would point
    somewhere other than the bucket entirely."""
    bucket.put_latest(version="0.5.4", zip=name, size=100)
    assert updates.available(installed) == {}


@pytest.mark.parametrize("size", [0, -1, "55939858", None, True,
                                  updates.MAX_PACKAGE_BYTES + 1])
def test_an_implausible_size_offers_nothing(bucket, installed, size):
    bucket.put_latest(version="0.5.4", zip="a.zip", size=size)
    assert updates.available(installed) == {}


def test_a_missing_field_offers_nothing(bucket, installed):
    bucket.put_latest(version="0.5.4")
    assert updates.available(installed) == {}
    bucket.put_latest(zip="a.zip", size=100)
    assert updates.available(installed) == {}


def test_json_that_is_not_an_object_offers_nothing(bucket, installed):
    for body in ("[]", '"0.5.4"', "null", "17"):
        bucket.put(updates.LATEST_NAME, body)
        assert updates.available(installed) == {}


# --- the development checkout ----------------------------------------------
def test_a_checkout_is_never_offered_an_update(bucket, tmp_path):
    """Updating means installing a Windows package over a Windows install, and
    a checkout is neither. Decided by the same marker the launcher trusts."""
    root = tmp_path / "repo"
    (root / "app" / "tests").mkdir(parents=True)
    (root / "VERSION").write_text("0.5.3\n", encoding="utf-8")
    assert packaging.is_checkout(root)
    bucket.put_latest(**GOOD)
    assert updates.available(root) == {}


# --- what the last look saw -------------------------------------------------
def test_nothing_is_known_before_the_first_look():
    updates.forget()
    assert updates.known() == {}
    assert not updates.looked()


def test_a_look_remembers_what_it_found(bucket, installed):
    bucket.put_latest(**GOOD)
    assert updates.look(installed) == GOOD
    assert updates.known() == GOOD
    assert updates.looked()


def test_a_look_that_found_nothing_still_counts_as_having_looked(bucket, installed):
    """"We have not looked yet" and "we looked and there is nothing" are
    different sentences to Mark, so the app has to be able to tell them
    apart."""
    assert updates.look(installed) == {}
    assert updates.known() == {}
    assert updates.looked()


def test_a_look_never_raises_however_badly_it_goes(monkeypatch, installed):
    """A bucket that is down must not be able to take the app down with it."""
    def explode(*_args, **_kwargs):
        raise RuntimeError("the bucket fell over")

    monkeypatch.setattr(updates, "available", explode)
    updates.forget()
    assert updates.look(installed) == {}
    assert updates.looked()
