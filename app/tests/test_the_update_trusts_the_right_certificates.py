"""The update check trusts the certificates the package carries.

Found on Spenser's Windows virtual machine, 2026-09-02, the first time anyone
pressed the update button on Windows at all. `latest.json` was live, public,
and loaded fine in the VM's own browser. The app said "You are on the newest
version" anyway.

The reason, from the VM's own traceback:

    ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]
    certificate verify failed: unable to get local issuer certificate

The embedded Python that ships inside the package has no usable set of root
certificates on Windows. A browser on the same machine has its own and is
unaffected, which is why the address worked when typed in by hand and failed
from inside the app.

`fetch_text` and `fetch_to_file` swallow every network failure on purpose, so
this reported as "nothing is being offered", which is the same answer as a
healthy check finding nothing. It was silent by construction.

The package already carries `certifi`, whose whole job is to be that set of
certificates. Nothing pointed at it.

**Why no existing test caught this.** `conftest.FakeBucket` serves plain HTTP
on loopback. No test in this repository has ever opened a TLS connection, so
the entire certificate path was unexercised on every platform.
"""
import ssl
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app" / "server"))
import updates  # noqa: E402


def test_the_app_carries_its_own_certificates_and_they_are_on_disk():
    import certifi
    bundle = Path(certifi.where())
    assert bundle.is_file(), "certifi's bundle is what the fix relies on"
    assert bundle.read_bytes().startswith(b"\n#")  or bundle.stat().st_size > 100_000


def test_the_context_is_built_from_that_bundle():
    context = updates.ssl_context()
    assert context is not None
    import certifi
    loaded = context.cert_store_stats()
    assert loaded["x509_ca"] > 0, "no certificate authorities were loaded"


def test_verification_stays_on():
    """The wrong fix for this defect is to stop checking certificates. This
    fails if anyone ever reaches for `_create_unverified_context`."""
    context = updates.ssl_context()
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True


def test_reading_the_pointer_file_passes_the_context(monkeypatch):
    seen = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, _n=None):
            return b'{"version": "9.9.9", "zip": "x.zip", "size": 1}'

    def fake_urlopen(url, timeout=None, context=None):
        seen["context"] = context
        return FakeResponse()

    monkeypatch.setattr(updates.urllib.request, "urlopen", fake_urlopen)
    updates.fetch_text("https://example.invalid/latest.json", 4096)
    assert seen["context"] is not None, "the check went out trusting nothing"
    assert seen["context"].verify_mode == ssl.CERT_REQUIRED


def test_downloading_the_package_passes_the_context(monkeypatch, tmp_path):
    seen = {}

    class FakeResponse:
        def __init__(self):
            self.given = False

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, _n=None):
            if self.given:
                return b""
            self.given = True
            return b"abc"

    def fake_urlopen(url, timeout=None, context=None):
        seen["context"] = context
        return FakeResponse()

    monkeypatch.setattr(updates.urllib.request, "urlopen", fake_urlopen)
    updates.fetch_to_file("https://example.invalid/x.zip", tmp_path / "x.zip", 3)
    assert seen["context"] is not None, "the download went out trusting nothing"
    assert seen["context"].verify_mode == ssl.CERT_REQUIRED


def test_a_missing_bundle_does_not_take_the_app_down(monkeypatch):
    """Nothing in this module may raise at a caller, including this. If the
    certificates cannot be found, the check fails the way every other network
    failure already does: quietly, with nothing offered."""
    def no_certifi(*_a, **_k):
        raise ImportError("certifi is not here")
    monkeypatch.setattr(updates, "_bundle_path", no_certifi)
    context = updates.ssl_context()
    assert context is None            # falls back to the default behaviour


def test_the_fetch_still_answers_when_there_are_no_certificates(monkeypatch):
    def no_certifi(*_a, **_k):
        raise ImportError("certifi is not here")
    monkeypatch.setattr(updates, "_bundle_path", no_certifi)
    # Unreachable host, so this exercises the real failure path end to end.
    assert updates.fetch_text("https://127.0.0.1:1/latest.json", 4096) == ""
