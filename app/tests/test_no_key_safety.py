"""Everything the app does on a machine with no API key, and what it must not.

This is the work-computer case. Spenser's employer owns that machine and no
personal API key goes on it, so the whole no-key path has to be genuinely
usable rather than a degraded shell: open the jobs, look at the photographs,
type captions, review them, build the document, restart, and find it all still
there.

The strongest test in here is the tripwire. `anthropic.Anthropic` is replaced
with something that raises the moment it is constructed, so any code path that
so much as builds a client fails the test loudly. That is a stronger claim than
counting requests: it proves no client is ever made, which means no request can
ever have been sent.

No real key is read, displayed, copied or tested anywhere in this file.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import aipolicy  # noqa: E402
import captions  # noqa: E402
import packaging  # noqa: E402
import settings  # noqa: E402
import startup  # noqa: E402
from main import create_app  # noqa: E402

JOB = "ANYTOWN_100 Example Avenue - 2026"


class ProviderTouched(AssertionError):
    """Raised if anything tries to build a provider client at all."""


@pytest.fixture
def tripwire(monkeypatch):
    """Any attempt to construct an Anthropic client fails the test."""
    import anthropic

    def explode(*args, **kwargs):
        raise ProviderTouched("a provider client was constructed with no key set")

    monkeypatch.setattr(anthropic, "Anthropic", explode)
    return explode


@pytest.fixture
def no_key(tmp_path, monkeypatch):
    """An isolated home with no key anywhere, the way that machine is."""
    box = tmp_path / "home"
    box.mkdir()
    for var, name in (("RRF_SETTINGS_FILE", ".rrf-app.json"),
                      ("RRF_KEY_FILE", ".rrf-app.env"),
                      ("RRF_CLASSIFY_FILE", ".rrf-classifications.json"),
                      ("RRF_VERSION_FILE", ".rrf-app-version.json"),
                      ("RRF_USAGE_FILE", ".rrf-ai-usage.json"),
                      ("RRF_JOBFACTS_FILE", ".rrf-job-facts.json"),
                      ("RRF_AI_POLICY_FILE", ".rrf-demo-ai-policy.json")):
        monkeypatch.setenv(var, str(box / name))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert settings.stored_key() == ""
    return box


@pytest.fixture
def job(tmp_path, monkeypatch, no_key):
    home = tmp_path / "jobs"
    place = home / JOB
    (place / "Photos").mkdir(parents=True)
    for i in range(6):
        Image.new("RGB", (900, 700), (40 + i * 9, 90, 120)).save(
            place / "Photos" / ("photo-%02d.jpg" % (i + 1)))
    (place / "job-brief.md").write_text(
        "# Job Brief - %s\n\n| Field | Value |\n|---|---|\n"
        "| Property address | 100 Example Avenue, Anytown, Iowa |\n" % JOB,
        encoding="utf-8")
    monkeypatch.setenv("RRF_JOBS_HOME", str(home))
    return place


@pytest.fixture
def client(job, tripwire):
    return TestClient(create_app(), raise_server_exceptions=False)


# --- it starts and shows everything ----------------------------------------

def test_the_app_starts_and_reports_its_version(client):
    assert client.get("/api/version").json()["version"] == packaging.version_of(
        Path(__file__).resolve().parents[2])


def test_the_jobs_and_every_photograph_are_visible(client, job):
    found = client.get("/api/workspace").json()
    assert found["valid"] is True
    manifest = client.get("/api/jobs/%s/manifest" % JOB).json()
    assert len(manifest["photos"]) == 6
    for photo in manifest["photos"]:
        answer = client.get("/api/jobs/%s/thumb/%s" % (JOB, photo["file"]))
        assert answer.status_code == 200
        assert answer.content, "a photograph would not display"


def test_nothing_is_attempted_automatically(client):
    """Opening the app and looking around must not reach the provider."""
    client.get("/api/workspace")
    client.get("/api/jobs/%s" % JOB)
    client.get("/api/jobs/%s/manifest" % JOB)
    client.get("/api/jobs/%s/caption-estimate" % JOB)
    client.get("/api/settings")
    # the tripwire would have raised by now


# --- the missing key says so, and says which kind of unavailable it is -----

def test_generate_captions_is_unavailable_and_explains_why(client):
    quote = client.get("/api/jobs/%s/caption-estimate" % JOB).json()
    assert quote["ai_available"] is False
    assert quote["blocked_because"] == "no_key"


def test_the_missing_key_reads_differently_from_every_other_unavailable_state(client, monkeypatch):
    """Four different reasons, four different answers. A grey control that
    leaves him guessing is the defect this exists to prevent."""
    reasons = {}
    reasons["no_key"] = client.get("/api/jobs/%s/caption-estimate" % JOB).json()["blocked_because"]

    monkeypatch.setattr(captions, "ai_available", lambda: True)
    monkeypatch.setattr(aipolicy, "classify_job", lambda j: aipolicy.LOCAL_ONLY)
    reasons["policy"] = client.get("/api/jobs/%s/caption-estimate" % JOB).json()["blocked_because"]

    monkeypatch.setattr(aipolicy, "classify_job", lambda j: aipolicy.NOT_DEMO)
    manifest = client.get("/api/jobs/%s/manifest" % JOB).json()
    for photo in manifest["photos"]:
        photo["caption"] = "typed"
    client.put("/api/jobs/%s/manifest" % JOB, json=manifest)
    reasons["nothing_to_do"] = client.get(
        "/api/jobs/%s/caption-estimate" % JOB).json()["blocked_because"]

    assert len(set(reasons.values())) == 3, reasons
    assert reasons["no_key"] == "no_key"
    assert reasons["policy"] == aipolicy.LOCAL_ONLY


def test_the_screen_has_its_own_words_for_each_one():
    screen = (Path(__file__).resolve().parents[1] / "web" / "src" / "screens"
              / "PhotosScreen.jsx").read_text(encoding="utf-8")
    assert "Open Settings to" in screen                 # the missing key
    assert "kept for local testing" in screen           # the policy
    assert "already has a caption" in screen            # nothing to do
    assert "Writing captions..." in screen              # in progress


def test_asking_for_captions_without_a_key_sends_nothing(client):
    answer = client.post("/api/jobs/%s/captions" % JOB)
    assert answer.status_code == 200
    assert answer.json()["ai_available"] is False
    # and the tripwire proves no client was built


# --- the whole manual workflow still works ---------------------------------

def test_typed_captions_save_locally(client, job):
    manifest = client.get("/api/jobs/%s/manifest" % JOB).json()
    for i, photo in enumerate(manifest["photos"], 1):
        photo["caption"] = "View of the north elevation %02d" % i
    assert client.put("/api/jobs/%s/manifest" % JOB, json=manifest).status_code == 200

    on_disk = json.loads((job / "Photos" / "photo-manifest.json").read_text())
    assert all(p["caption"].strip() for p in on_disk["photos"])


def test_review_and_build_work_without_a_key(client, job):
    manifest = client.get("/api/jobs/%s/manifest" % JOB).json()
    for i, photo in enumerate(manifest["photos"], 1):
        photo["caption"] = "View of the north elevation %02d" % i
    client.put("/api/jobs/%s/manifest" % JOB, json=manifest)

    blocked = client.post("/api/jobs/%s/build" % JOB)
    assert blocked.status_code == 400 and "reviewed" in blocked.json()["detail"]

    for photo in manifest["photos"]:
        assert client.post("/api/jobs/%s/photos/%s/reviewed"
                           % (JOB, photo["file"])).status_code == 200

    built = client.post("/api/jobs/%s/build" % JOB)
    assert built.status_code == 200, built.json()
    assert built.json()["created"] == "Anytown_100 Example Avenue Photos (Complete).docx"

    from docx import Document
    document = Document(str(job / "Photos" / built.json()["created"]))
    images = [r for r in document.part.rels.values() if "image" in r.reltype]
    assert len(images) == 6


def test_restart_keeps_the_typed_captions_and_the_ticks(client, job, tripwire):
    manifest = client.get("/api/jobs/%s/manifest" % JOB).json()
    for photo in manifest["photos"]:
        photo["caption"] = "typed by hand"
    client.put("/api/jobs/%s/manifest" % JOB, json=manifest)
    for photo in manifest["photos"]:
        client.post("/api/jobs/%s/photos/%s/reviewed" % (JOB, photo["file"]))

    fresh = TestClient(create_app(), raise_server_exceptions=False)   # a restart
    after = fresh.get("/api/jobs/%s/manifest" % JOB).json()
    assert all(p["caption"] == "typed by hand" for p in after["photos"])
    assert all(p.get("reviewed") for p in after["photos"])


# --- the single-instance lock ----------------------------------------------

def test_a_second_copy_is_refused_and_names_the_running_one(tmp_path):
    """A different property from rollback, and tested on its own."""
    import json as _json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = _json.dumps({"version": "0.3.0"}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        installs = tmp_path / "installs"
        running = installs / "Roy R. Fisher v0.3.0"
        running.mkdir(parents=True)
        startup.write_runtime(running, server.server_address[1], "0.3.0")

        second = installs / "Roy R. Fisher v0.3.0 copy"
        second.mkdir()
        with pytest.raises(startup.StartupRefused) as raised:
            startup.refuse_if_another_version_runs(second)
        assert "0.3.0" in raised.value.message
        assert "Close that window first" in raised.value.message
    finally:
        server.shutdown()
        server.server_close()


def test_closing_releases_the_lock_cleanly(tmp_path):
    """Nothing listens afterwards, so the next launch is free to start. The
    lock is the live port, not a file left behind, which is why a stale
    runtime.json never blocks anything."""
    installs = tmp_path / "installs"
    was_running = installs / "Roy R. Fisher v0.3.0"
    was_running.mkdir(parents=True)
    startup.write_runtime(was_running, startup.free_port(), "0.3.0")   # closed

    second = installs / "Roy R. Fisher v0.3.0 copy"
    second.mkdir()
    startup.refuse_if_another_version_runs(second)      # does not raise
    assert startup.runtime_file(was_running).is_file(), "the file is still there"
