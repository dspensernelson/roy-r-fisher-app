"""She presses one button and the log reaches Spenser. What that costs, proved.

The goal the owner approved on 2026-09-14: she presses one button and the last
two days of log reach his email. She never picks a file, finds a folder, or
attaches anything.

Two things are proved here. The screen can show her exactly what would leave
her computer before it leaves, and the old folder-window behaviour is gone
rather than sitting beside the new one. A second way to do the same thing is
what caused the original fault: a control that revealed one of two files.
"""
import datetime
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

from main import create_app  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
WEB = REPO / "app" / "web" / "src"


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def log_path(tmp_path, monkeypatch):
    path = tmp_path / ".rrf-app.log"
    monkeypatch.setenv("RRF_LOG_FILE", str(path))
    return path


def stamp(when) -> str:
    return when.isoformat(timespec="seconds")


def recent_line(message, minutes_ago=5) -> str:
    when = datetime.datetime.now() - datetime.timedelta(minutes=minutes_ago)
    return "%s %s\n" % (stamp(when), message)


# --- seeing it before sending it --------------------------------------------
def test_recent_answers_with_the_text_that_would_be_sent(client, log_path):
    log_path.write_text(recent_line("something worth reading"))
    response = client.get("/api/log/recent")

    assert response.status_code == 200
    body = response.json()
    assert "something worth reading" in body["text"]
    assert body["lines"] >= 1
    assert body["empty"] is False


def test_recent_reads_both_halves_which_is_the_whole_point(client, log_path):
    rotated = log_path.with_name(log_path.name + ".1")
    rotated.write_text(recent_line("the fault, in the rotated half", 180))
    log_path.write_text(recent_line("after the rotation", 5))

    body = client.get("/api/log/recent").json()
    assert "the fault, in the rotated half" in body["text"]
    assert "after the rotation" in body["text"]


def test_recent_names_the_running_version(client, log_path):
    import packaging
    log_path.write_text(recent_line("anything at all"))
    body = client.get("/api/log/recent").json()
    assert packaging.version_of(REPO) in body["text"]


def test_recent_on_a_machine_with_no_log_is_not_an_error(client, log_path):
    response = client.get("/api/log/recent")
    assert response.status_code == 200
    assert response.json()["empty"] is True


# --- the old way is gone ----------------------------------------------------
def test_the_folder_window_route_is_gone(client, log_path):
    """It does not stay beside the new view. A second way to do this is what
    caused the fault: one control that revealed one of two files."""
    log_path.write_text(recent_line("anything at all"))
    assert client.post("/api/log/show").status_code in (404, 405)


def test_the_route_is_not_registered_at_all():
    """Not merely refused. The old path is off the app's route table, so it
    cannot come back by somebody re-registering half of it."""
    paths = {getattr(route, "path", "") for route in create_app().routes}
    assert "/api/log/show" not in paths
    assert "/api/log/recent" in paths


def test_nothing_in_the_screens_still_calls_the_folder_window_route():
    api_js = (WEB / "api.js").read_text(encoding="utf-8")
    assert "showTheLog" not in api_js
    assert '"/api/log/show"' not in api_js
    for path in sorted((WEB / "screens").glob("*.jsx")):
        assert "showTheLog" not in path.read_text(encoding="utf-8"), path


def test_the_settings_screen_offers_the_new_words_and_not_the_old(client):
    source = (WEB / "screens" / "Settings.jsx").read_text(encoding="utf-8")
    assert "Show what will be sent" in source
    assert "Show the log" not in source


# --- the sender -------------------------------------------------------------
class FakeService:
    """A real HTTP server on a loopback port that accepts a POST.

    It proves a narrow mechanic: what this app puts on the wire, and what it
    does with each answer it gets back. It claims nothing about Cloudflare,
    about Workers, about R2, or about her office network.
    """

    def __init__(self, status=200):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer
        self.status = status
        self.seen = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                outer.seen.append({"path": self.path,
                                   "headers": dict(self.headers),
                                   "body": self.rfile.read(length)})
                self.send_response(outer.status)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *_args):
                pass

        class Quiet(HTTPServer):
            def handle_error(self, *_args):
                pass

        self.server = Quiet(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01},
            daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return "http://127.0.0.1:%d" % self.server.server_address[1]

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def service(monkeypatch):
    made = FakeService()
    monkeypatch.setenv("RRF_LOG_ENDPOINT", made.url)
    yield made
    made.close()


@pytest.fixture
def refusing_service(monkeypatch):
    made = FakeService(status=429)
    monkeypatch.setenv("RRF_LOG_ENDPOINT", made.url)
    yield made
    made.close()


def test_the_body_on_the_wire_is_exactly_what_the_screen_showed(service, log_path):
    """`Show what will be sent` has to be literally true. If the preview and
    the body could differ, the screen would be making a promise about
    something it had not seen."""
    import logwindow
    import sendlog

    log_path.write_text(recent_line("something worth reading"))
    shown = logwindow.recent(version="0.7.0")["text"]
    answer = sendlog.send(shown)

    assert answer["sent"] is True
    assert service.seen[-1]["body"].decode("utf-8") == shown


def test_it_posts_to_the_one_path_the_service_accepts(service):
    import sendlog
    sendlog.send(sendlog.MARKER + " sample\n2026-09-14T09:30:00 a line")
    assert service.seen[-1]["path"] == sendlog.PATH


def test_it_says_who_it_is_because_cloudflare_refuses_python(service):
    """Measured 2026-09-02 against the real bucket: Cloudflare answers 403 to
    `Python-urllib/3.x`. The same wall stands in front of a Worker."""
    import sendlog
    import updates

    sendlog.send(sendlog.MARKER + " sample\n2026-09-14T09:30:00 a line")
    sent = service.seen[-1]["headers"].get("User-Agent", "")
    assert "Python-urllib" not in sent
    assert sent == updates.USER_AGENT


def test_it_never_puts_a_recipient_on_the_wire(service):
    """The owner's decision: the recipient is fixed inside the service and
    never sent by the app, so nobody can turn this into a way to mail a
    stranger."""
    import sendlog

    sendlog.send(sendlog.MARKER + " sample\n2026-09-14T09:30:00 a line")
    request = service.seen[-1]
    whole = (request["body"] + repr(request["headers"]).encode("utf-8")).lower()
    assert b"d.spensernelson" not in whole
    assert b"@gmail" not in whole
    assert b"to=" not in whole


def test_a_key_written_before_the_redaction_rule_existed_still_cannot_leave(service):
    """Redaction is applied again on the way out, not trusted from the write.

    A line already on her disk was written by a version of `applog` whose
    rules were whatever they were that day. This is the last place that can
    still catch one.
    """
    import sendlog

    sendlog.send("2026-09-14T09:30:00 key=sk-ant-abcdef1234567890abcdef1234567890")
    body = service.seen[-1]["body"].decode("utf-8")
    assert "sk-ant-" not in body
    assert "[removed]" in body


def test_an_unreachable_service_comes_back_as_a_sentence_and_never_raises(monkeypatch):
    import sendlog
    monkeypatch.setenv("RRF_LOG_ENDPOINT", "http://127.0.0.1:1")
    answer = sendlog.send(sendlog.MARKER + " sample")
    assert answer["sent"] is False
    assert "internet" in answer["message"].lower()
    assert "Show what will be sent" in answer["message"]


def test_one_already_sent_this_hour_gets_its_own_sentence(refusing_service):
    import sendlog
    answer = sendlog.send(sendlog.MARKER + " sample")
    assert answer["sent"] is False
    assert "hour" in answer["message"].lower()
    assert "Show what will be sent" in answer["message"]


def test_an_address_that_was_never_set_says_so_rather_than_blaming_the_internet(monkeypatch):
    """Never state a fact the app cannot observe. An unset address is not a
    network fault and must not be reported as one."""
    import sendlog
    monkeypatch.setenv("RRF_LOG_ENDPOINT", "")
    monkeypatch.setattr(sendlog, "ENDPOINT", "")
    answer = sendlog.send(sendlog.MARKER + " sample")
    assert answer["sent"] is False
    assert "internet" not in answer["message"].lower()
    assert sendlog.SPENSER_EMAIL in answer["message"]


def test_too_much_text_is_refused_before_the_network_is_touched(service):
    import sendlog
    # Ordinary log text rather than one long run of characters. A long run is
    # key shaped, redaction shrinks it to nothing, and the test would then be
    # measuring the wrong thing. The size checked is the size that would go on
    # the wire, after redaction, which is the only size that matters.
    one = "2026-09-14T09:30:00 a line of the sort the app actually writes\n"
    answer = sendlog.send(one * ((sendlog.MAX_SEND_BYTES // len(one)) + 200))
    assert answer["sent"] is False
    assert service.seen == []


def test_nothing_at_all_is_never_posted(service):
    import sendlog
    assert sendlog.send("")["sent"] is False
    assert service.seen == []


def test_no_password_key_or_token_lives_in_the_sender():
    """The package is public. Anything inside it is public knowledge.

    Checked with `applog.redact`, the rule this project already trusts to
    recognise a credential, rather than a second list of words that would
    drift away from it. If redaction finds nothing to remove in the source,
    the source carries nothing key shaped.
    """
    import applog

    source = (REPO / "app" / "server" / "sendlog.py").read_text(encoding="utf-8")
    assert applog.redact(source) == source
    assert "sk-ant-" not in source
    # Resend's own key prefix, the one credential this feature involves. It
    # belongs in the Cloudflare dashboard and nowhere in this repository.
    assert "re_" not in source


def test_the_update_path_only_ever_fetches_and_never_sends(fake_bucket, tmp_path):
    """The update bucket is read from and never written to. Adding a sender
    to this app must not quietly give the updater one."""
    import updates

    fake_bucket.put("latest.json",
                    '{"version": "9.9.9", "zip": "x.zip", "size": 8}')
    fake_bucket.put("x.zip", b"abcdefgh")
    (tmp_path / "VERSION").write_text("0.1.0")
    updates.look(tmp_path)
    updates.fetch_to_file(updates.file_url("x.zip"), tmp_path / "x.zip", 8)

    assert fake_bucket.methods, "no request reached the bucket at all"
    assert set(fake_bucket.methods) == {"GET"}
