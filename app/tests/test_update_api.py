"""The routes behind the update button.

Only one of these changes anything, and Mark has to click for it. The rest
report. That split is the approved shape: not automatic, not silent, not on a
timer.

Two things every test here holds. Opening a screen never costs a request to the
internet, because the look happens once in the background at startup and again
only when he asks. And a run that fails leaves the app answering normally
afterwards, because a failed update that also breaks the app is the one outcome
that would strand him.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))

import main  # noqa: E402
import packaging  # noqa: E402
import updates  # noqa: E402


@pytest.fixture
def client(monkeypatch, tmp_path):
    updates.forget()
    updates.end_run()
    updates.forget_cleared()
    monkeypatch.setattr(main, "PROGRAM", tmp_path / "program")
    monkeypatch.setattr(main, "HOME", tmp_path)
    (tmp_path / "program").mkdir(parents=True)
    (tmp_path / "program" / "VERSION").write_text("0.5.3\n", encoding="utf-8")
    yield TestClient(main.create_app())
    updates.forget()
    updates.end_run()
    updates.forget_cleared()


OFFER = {"version": "0.5.4", "zip": "Roy R. Fisher v0.5.4.zip", "size": 55939858}


# --- reporting --------------------------------------------------------------
def test_it_reports_nothing_before_anything_has_looked(client):
    found = client.get("/api/update").json()
    assert found["available"] == ""
    assert found["looked"] is False
    assert found["run"]["running"] is False


def test_it_reports_an_offer_once_a_look_has_found_one(client):
    updates.remember(OFFER)
    found = client.get("/api/update").json()
    assert found["available"] == "0.5.4"
    assert found["size"] == 55939858
    assert found["looked"] is True


def test_reading_the_status_never_touches_the_network(client, monkeypatch):
    """Opening a screen must not cost a request to the internet. The look
    happens once at startup and again only when he asks."""
    def never(*_a, **_k):
        raise AssertionError("the status route went to the network")

    monkeypatch.setattr(updates.urllib.request, "urlopen", never)
    assert client.get("/api/update").status_code == 200
    assert client.get("/api/update/progress").status_code == 200


def test_check_now_looks_and_answers_either_way(client, fake_bucket):
    """The startup look is silent because he did not ask. This one answers,
    because he did."""
    answered = client.post("/api/update/check").json()
    assert answered["available"] == ""
    assert answered["looked"] is True

    fake_bucket.put(updates.LATEST_NAME, json.dumps(OFFER))
    answered = client.post("/api/update/check").json()
    assert answered["available"] == "0.5.4"


def test_a_checkout_is_never_offered_an_update(client, fake_bucket, monkeypatch):
    (main.PROGRAM / "app" / "tests").mkdir(parents=True)
    fake_bucket.put(updates.LATEST_NAME, json.dumps(OFFER))
    assert client.post("/api/update/check").json()["available"] == ""


# --- starting ---------------------------------------------------------------
def test_starting_without_an_offer_is_refused(client):
    answered = client.post("/api/update/start")
    assert answered.status_code == 400
    assert "no update" in answered.json()["detail"].lower()


def test_two_updates_cannot_run_at_once(client):
    updates.remember(OFFER)
    updates.begin_run("0.5.4", 100)
    answered = client.post("/api/update/start")
    assert answered.status_code == 409
    assert "already running" in answered.json()["detail"]


def test_an_update_cannot_start_while_the_demo_is_being_reset(client):
    import busy

    updates.remember(OFFER)
    with busy.resetting():
        answered = client.post("/api/update/start")
    assert answered.status_code == 409


def test_starting_answers_at_once_rather_than_after_the_download(client,
                                                                 monkeypatch):
    """The download takes minutes. The screen has a bar to draw in the
    meantime, and it cannot draw it while waiting for this to return."""
    import threading

    let_go = threading.Event()

    def slow(*_a, **_k):
        let_go.wait(5)
        raise updates.UpdateRefused("stopped")

    monkeypatch.setattr(updates, "prepare", slow)
    updates.remember(OFFER)
    answered = client.post("/api/update/start")
    assert answered.status_code == 200
    assert answered.json()["run"]["running"] is True
    let_go.set()


# --- failing ----------------------------------------------------------------
def _wait_for_the_run_to_end(timeout=5.0):
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not updates.run_state()["running"]:
            return updates.run_state()
        time.sleep(0.02)
    raise AssertionError("the run never ended")


def test_a_refused_update_leaves_its_sentence_and_the_app_working(client,
                                                                  monkeypatch):
    def refuse(*_a, **_k):
        raise updates.UpdateRefused("The update did not arrive intact.")

    monkeypatch.setattr(updates, "prepare", refuse)
    updates.remember(OFFER)
    client.post("/api/update/start")
    found = _wait_for_the_run_to_end()
    assert found["error"] == "The update did not arrive intact."
    assert client.get("/api/version").json()["version"] == "0.5.3"


def test_anything_unexpected_still_reads_as_a_sentence(client, monkeypatch):
    def explode(*_a, **_k):
        raise RuntimeError("nobody predicted this")

    monkeypatch.setattr(updates, "prepare", explode)
    updates.remember(OFFER)
    client.post("/api/update/start")
    found = _wait_for_the_run_to_end()
    assert "did not finish" in found["error"]
    assert "nobody predicted this" in found["error"]
    assert "this app still works" in found["error"]
    assert client.get("/api/update").status_code == 200


def test_a_failed_update_never_closes_the_app(client, monkeypatch):
    """The one outcome that would strand him."""
    closed = []
    monkeypatch.setattr(updates, "close_the_app",
                        lambda *a, **k: closed.append(True))
    monkeypatch.setattr(updates, "prepare",
                        lambda *a, **k: (_ for _ in ()).throw(
                            updates.UpdateRefused("no")))
    updates.remember(OFFER)
    client.post("/api/update/start")
    _wait_for_the_run_to_end()
    assert not closed


def test_nothing_is_handed_over_when_the_package_is_refused(client, monkeypatch):
    handed = []
    monkeypatch.setattr(updates, "hand_off", lambda *a, **k: handed.append(a))
    monkeypatch.setattr(updates, "prepare",
                        lambda *a, **k: (_ for _ in ()).throw(
                            updates.UpdateRefused("no")))
    updates.remember(OFFER)
    client.post("/api/update/start")
    _wait_for_the_run_to_end()
    assert not handed


# --- succeeding -------------------------------------------------------------
def test_a_good_run_hands_over_and_then_closes(client, monkeypatch, tmp_path):
    import threading

    order = []
    done = threading.Event()
    monkeypatch.setattr(main, "CLOSING_PAUSE", 0.01)
    monkeypatch.setattr(updates, "prepare", lambda *a, **k: tmp_path / "package")
    monkeypatch.setattr(updates, "hand_off", lambda p, **k: order.append("hand off"))
    monkeypatch.setattr(updates, "close_the_app",
                        lambda *a, **k: order.append("close") or done.set())
    updates.remember(OFFER)
    client.post("/api/update/start")

    assert done.wait(5), "the run never reached the close"
    assert order == ["hand off", "close"], "it closed before handing over"


def test_writes_in_flight_are_waited_for_before_it_closes(client, monkeypatch,
                                                          tmp_path):
    """Every app-owned file is written to a temporary file and moved into
    place, so an interrupted write cannot corrupt one. It can still lose one,
    and losing a caption run he just approved is a bad way to find out."""
    import threading

    waited = []
    done = threading.Event()
    monkeypatch.setattr(main, "CLOSING_PAUSE", 0.01)
    monkeypatch.setattr(main.busy, "wait_until_idle",
                        lambda *a, **k: waited.append(True) or True)
    monkeypatch.setattr(updates, "prepare", lambda *a, **k: tmp_path / "package")
    monkeypatch.setattr(updates, "hand_off", lambda p, **k: None)
    # Waited on before this test returns. A worker still running when
    # monkeypatch puts the real close_the_app back would exit the process, and
    # os._exit takes the test run with it without saying why.
    monkeypatch.setattr(updates, "close_the_app", lambda *a, **k: done.set())
    updates.remember(OFFER)
    client.post("/api/update/start")

    assert done.wait(5), "the run never reached the close"
    assert waited


# --- cancelling -------------------------------------------------------------
def test_cancel_asks_the_run_to_stop(client):
    updates.remember(OFFER)
    updates.begin_run("0.5.4", 100)
    answered = client.post("/api/update/cancel").json()
    assert answered["cancelling"] is True


# --- the startup look -------------------------------------------------------
def test_the_startup_look_is_silent_and_cannot_take_the_app_down():
    """Asserted on the source. No internet, a bucket that is down, and a slow
    morning must all look exactly like there being no update."""
    source = (APP / "run_app.py").read_text()
    assert "look_for_an_update" in source
    assert "daemon=True" in source
    start = source.index("def look_for_an_update")
    assert "except Exception:" in source[start:start + 600]
