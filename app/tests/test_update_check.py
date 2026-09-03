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
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))

import packaging  # noqa: E402
import updates  # noqa: E402


def put_latest(fake_bucket, **fields):
    fake_bucket.put(updates.LATEST_NAME, json.dumps(fields))


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
def test_a_newer_version_is_offered(fake_bucket, installed):
    put_latest(fake_bucket, **GOOD)
    assert updates.available(installed) == GOOD


def test_the_running_version_is_not_an_update(fake_bucket, installed):
    put_latest(fake_bucket, version="0.5.3", zip="Roy R. Fisher v0.5.3.zip", size=100)
    assert updates.available(installed) == {}


def test_an_older_version_is_not_an_update(fake_bucket, installed):
    put_latest(fake_bucket, version="0.5.2", zip="Roy R. Fisher v0.5.2.zip", size=100)
    assert updates.available(installed) == {}


def test_ten_is_newer_than_nine_here_too(fake_bucket, installed):
    (installed / "VERSION").write_text("0.9.0\n", encoding="utf-8")
    put_latest(fake_bucket, version="0.10.0", zip="Roy R. Fisher v0.10.0.zip", size=100)
    assert updates.available(installed)["version"] == "0.10.0"


# --- a bucket that says nothing usable -------------------------------------
def test_an_empty_bucket_offers_nothing(fake_bucket, installed):
    assert updates.available(installed) == {}


def test_a_bucket_that_is_not_there_offers_nothing(monkeypatch, installed):
    """Nothing listening at all. This is Mark with no internet, and it must
    look exactly like the bucket being empty."""
    monkeypatch.setenv("RRF_UPDATE_BUCKET", "http://127.0.0.1:9")
    assert updates.available(installed) == {}


def test_a_timeout_offers_nothing(monkeypatch, fake_bucket, installed):
    import socket

    def slow(*_args, **_kwargs):
        raise socket.timeout("too slow")

    monkeypatch.setattr(updates.urllib.request, "urlopen", slow)
    assert updates.available(installed) == {}


def test_html_instead_of_json_offers_nothing(fake_bucket, installed):
    fake_bucket.put(updates.LATEST_NAME, "<html><body>404 not found</body></html>")
    assert updates.available(installed) == {}


def test_a_body_larger_than_a_pointer_file_offers_nothing(fake_bucket, installed):
    """A pointer file is a few hundred bytes. Anything bigger is not one, and
    reading an unbounded body on the startup path is how a slow morning
    becomes a hung app."""
    padded = dict(GOOD)
    padded["padding"] = "x" * (updates.MAX_LATEST_BYTES + 100)
    fake_bucket.put(updates.LATEST_NAME, json.dumps(padded))
    assert updates.available(installed) == {}


# --- a bucket that says something wrong ------------------------------------
@pytest.mark.parametrize("version", ["", "   ", "latest", "v0.5.4", None, 4, True])
def test_an_unusable_version_offers_nothing(fake_bucket, installed, version):
    put_latest(fake_bucket, version=version, zip="a.zip", size=100)
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
def test_a_filename_that_could_point_elsewhere_offers_nothing(fake_bucket, installed, name):
    """The value is joined onto a URL. A name carrying a slash would point
    somewhere other than the bucket entirely."""
    put_latest(fake_bucket, version="0.5.4", zip=name, size=100)
    assert updates.available(installed) == {}


@pytest.mark.parametrize("size", [0, -1, "55939858", None, True,
                                  updates.MAX_PACKAGE_BYTES + 1])
def test_an_implausible_size_offers_nothing(fake_bucket, installed, size):
    put_latest(fake_bucket, version="0.5.4", zip="a.zip", size=size)
    assert updates.available(installed) == {}


def test_a_missing_field_offers_nothing(fake_bucket, installed):
    put_latest(fake_bucket, version="0.5.4")
    assert updates.available(installed) == {}
    put_latest(fake_bucket, zip="a.zip", size=100)
    assert updates.available(installed) == {}


def test_json_that_is_not_an_object_offers_nothing(fake_bucket, installed):
    for body in ("[]", '"0.5.4"', "null", "17"):
        fake_bucket.put(updates.LATEST_NAME, body)
        assert updates.available(installed) == {}


# --- the development checkout ----------------------------------------------
def test_a_checkout_is_never_offered_an_update(fake_bucket, tmp_path):
    """Updating means installing a Windows package over a Windows install, and
    a checkout is neither. Decided by the same marker the launcher trusts."""
    root = tmp_path / "repo"
    (root / "app" / "tests").mkdir(parents=True)
    (root / "VERSION").write_text("0.5.3\n", encoding="utf-8")
    assert packaging.is_checkout(root)
    put_latest(fake_bucket, **GOOD)
    assert updates.available(root) == {}


# --- what the last look saw -------------------------------------------------
def test_nothing_is_known_before_the_first_look():
    updates.forget()
    assert updates.known() == {}
    assert not updates.looked()


def test_a_look_remembers_what_it_found(fake_bucket, installed):
    put_latest(fake_bucket, **GOOD)
    assert updates.look(installed) == GOOD
    assert updates.known() == GOOD
    assert updates.looked()


def test_a_look_that_found_nothing_still_counts_as_having_looked(fake_bucket, installed):
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


# --- what the update path may and may not touch -----------------------------
def test_nothing_in_the_update_path_reads_a_key_or_a_setting():
    """Never move, print, or copy a key. Nothing here has any reason to read
    one, and this is the test that it stays that way when somebody adds a
    feature to this file later."""
    for name in ("updates.py",):
        source = (APP / "server" / name).read_text()
        assert "import settings" not in source
        assert "import captions" not in source
        assert "sk-ant" not in source
    child = (APP / "update_apply.py").read_text()
    assert "import settings" not in child


def test_it_only_ever_fetches_and_never_sends(fake_bucket, installed):
    """The app asks the bucket for files. It never posts anything anywhere, so
    nothing about Mark, his jobs, or his machine leaves this computer.

    Asserted by watching every request the module makes rather than by reading
    the source, because a `data=` argument added later would still be a GET in
    the source and a POST on the wire.
    """
    seen = []
    real = updates.urllib.request.urlopen

    def watch(url, *args, **kwargs):
        seen.append(url)
        return real(url, *args, **kwargs)

    updates.urllib.request.urlopen = watch
    try:
        put_latest(fake_bucket, **GOOD)
        updates.available(installed)
    finally:
        updates.urllib.request.urlopen = real

    assert seen, "it did not ask the bucket anything"
    for asked in seen:
        # Checked on the property that actually matters rather than on the
        # type. A Request object is not itself a problem: the app builds one
        # to carry its own name, because Cloudflare refuses the default
        # Python-urllib name with a 403 (measured 2026-09-02). What must never
        # appear is a body or a method other than GET.
        if isinstance(asked, str):
            url, body, method = asked, None, "GET"
        else:
            url, body, method = asked.full_url, asked.data, asked.get_method()
        assert body is None, "the update path attached a body to a request"
        assert method == "GET", "the update path used %s, not GET" % method
        assert url.startswith(fake_bucket.url)
