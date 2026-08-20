"""Where the caption key comes from, and who is allowed to see it.

The launcher used to source the key file with the shell and hand the key to
Python through the environment. That meant starting the app any other way
gave a different answer about whether captions worked, and it put a shell in
the product path on a Windows machine. Python reads the file itself now.

Nothing here ever asserts on the key's value beyond what the code must
return, and no test reads Spenser's real file: conftest points RRF_KEY_FILE
at a temporary one for every test in the suite.
"""
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import captions  # noqa: E402
import settings  # noqa: E402
from main import create_app  # noqa: E402

FROM_FILE = "sk-ant-file-0000000000000000000000000000"
FROM_ENV = "sk-ant-env-00000000000000000000000000000"


@pytest.fixture
def key_file(tmp_path, monkeypatch):
    path = tmp_path / "key.env"
    monkeypatch.setenv("RRF_KEY_FILE", str(path))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    return path


# ------------------------------------------------------------ precedence ---
def test_an_existing_environment_variable_wins(key_file, monkeypatch):
    key_file.write_text("ANTHROPIC_API_KEY=%s\n" % FROM_FILE)
    monkeypatch.setenv("ANTHROPIC_API_KEY", FROM_ENV)
    assert settings.active_key() == FROM_ENV


def test_the_file_is_used_when_there_is_no_environment_variable(key_file):
    key_file.write_text("ANTHROPIC_API_KEY=%s\n" % FROM_FILE)
    assert settings.active_key() == FROM_FILE
    assert captions.ai_available() is True


def test_an_empty_environment_variable_falls_through_to_the_file(key_file, monkeypatch):
    key_file.write_text("ANTHROPIC_API_KEY=%s\n" % FROM_FILE)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "   ")
    assert settings.active_key() == FROM_FILE


# --------------------------------------------------------- the file shape --
@pytest.mark.parametrize("line", [
    'ANTHROPIC_API_KEY=%s',
    'ANTHROPIC_API_KEY="%s"',
    "ANTHROPIC_API_KEY='%s'",
    'export ANTHROPIC_API_KEY=%s',
    'export ANTHROPIC_API_KEY="%s"',
    '  ANTHROPIC_API_KEY=%s  ',
])
def test_the_shapes_a_human_or_an_older_launcher_may_have_written(key_file, line):
    key_file.write_text((line % FROM_FILE) + "\n")
    assert settings.active_key() == FROM_FILE


def test_other_lines_in_the_file_are_left_alone(key_file):
    key_file.write_text("SOMETHING_ELSE=keep me\nANTHROPIC_API_KEY=%s\n# a note\n" % FROM_FILE)
    assert settings.active_key() == FROM_FILE
    assert "SOMETHING_ELSE=keep me" in key_file.read_text()


def test_only_the_one_name_is_read(key_file):
    key_file.write_text("OPENAI_API_KEY=sk-not-ours\nANTHROPIC_API_KEY_OLD=sk-nope\n")
    assert settings.active_key() == ""


# ------------------------------------------------------------- no key -----
def test_a_missing_file_means_captions_are_off_and_nothing_crashes(key_file):
    assert not key_file.exists()
    assert settings.active_key() == ""
    assert captions.ai_available() is False
    assert settings.status() == {"key_set": False, "ends_with": ""}


@pytest.mark.parametrize("body", [
    "", "\n\n", "ANTHROPIC_API_KEY=\n", 'ANTHROPIC_API_KEY=""\n',
    "ANTHROPIC_API_KEY\n", "just some text\n", "=nothing\n",
])
def test_an_empty_or_malformed_entry_means_captions_are_off(key_file, body):
    key_file.write_text(body)
    assert settings.active_key() == ""
    assert captions.ai_available() is False


def test_an_unreadable_file_does_not_crash(key_file):
    key_file.write_bytes(b"\xff\xfe\x00 not text at all")
    settings.active_key()          # would raise if it were not tolerant


# ------------------------------------------------------------ isolation ---
def test_rrf_key_file_keeps_tests_away_from_the_real_home(key_file):
    """conftest points this at a temporary file for every test, so a suite run
    can neither read nor write Spenser's own key."""
    assert str(settings.key_file()) == str(key_file)
    assert Path.home() / ".rrf-app.env" != settings.key_file()


def test_saving_and_removing_stay_inside_the_temporary_file(key_file):
    settings.save_key(FROM_FILE)
    assert key_file.is_file()
    assert settings.active_key() == FROM_FILE
    settings.remove_key()
    assert settings.active_key() == ""


# ------------------------------------------------- the key stays server-side
def test_no_api_response_carries_the_key(key_file):
    key_file.write_text("ANTHROPIC_API_KEY=%s\n" % FROM_FILE)
    client = TestClient(create_app())
    for url in ["/api/settings", "/api/caption-styles", "/api/demo", "/api/workspace"]:
        body = client.get(url).text
        assert FROM_FILE not in body, url
        assert "sk-ant" not in body, url


def test_the_screen_is_told_availability_and_nothing_more(key_file):
    key_file.write_text("ANTHROPIC_API_KEY=%s\n" % FROM_FILE)
    body = TestClient(create_app()).get("/api/caption-styles").json()
    assert body["ai_available"] is True
    assert "key" not in json.dumps(body).lower().replace("key\":", "")

    key_file.unlink()
    off = TestClient(create_app()).get("/api/caption-styles").json()
    assert off["ai_available"] is False


def test_settings_never_returns_more_than_the_last_four(key_file):
    key_file.write_text("ANTHROPIC_API_KEY=%s\n" % FROM_FILE)
    body = TestClient(create_app()).get("/api/settings").json()
    assert body["key_set"] is True
    assert body["ends_with"] == FROM_FILE[-4:]
    assert len(body["ends_with"]) == 4


# ----------------------------------------------- the launcher is out of it --
LAUNCHER = Path(__file__).resolve().parents[2] / "Start Roy R. Fisher.command"


def test_the_launcher_no_longer_touches_the_key():
    text = LAUNCHER.read_text()
    assert "ANTHROPIC_API_KEY" not in text
    assert ".rrf-app.env" not in text
    assert "set -a" not in text, "the launcher must not source anything"


def test_the_launcher_only_starts_the_app():
    text = LAUNCHER.read_text()
    assert "python3 app/run_app.py" in text


# ------------------------------------------------ the control looks off ----
SCREEN = Path(__file__).resolve().parents[1] / "web" / "src" / "screens" / "PhotosScreen.jsx"
CSS = Path(__file__).resolve().parents[1] / "web" / "src" / "brand.css"


def _element(source: str, label: str) -> str:
    """The <button ...> element whose visible text is `label`.

    Found by walking back from the label to its own opening tag, rather than
    by slicing a fixed number of characters before the first time the words
    appear. The fixed window broke once a comment above a different button
    mentioned this one by name, which made the test read the wrong element and
    fail for a reason that had nothing to do with the behaviour it guards.
    """
    at = source.index(">%s<" % label) if ">%s<" % label in source else source.rindex(label)
    start = source.rindex("<button", 0, at)
    return source[start:at]


def test_generating_captions_is_genuinely_disabled_when_there_is_no_key():
    """Only this control. Build photo pages has nothing to do with the key
    and must not be switched off by it.

    The control was renamed from Suggest captions to Generate captions on
    2026-08-20, to match the wording of the spend confirmation.
    """
    source = SCREEN.read_text()

    # It is disabled through canGenerate, which is false whenever the server
    # gives a reason: no key, a local-only job, or nothing left to caption.
    assert "disabled={!!busy || !canGenerate}" in source, \
        "the control must be disabled, not merely styled"
    assert 'blockedBecause === "no_key"' in source, \
        "a missing key must be one of the named reasons"
    assert "const canGenerate = inPhotos.length > 0 && !blockedBecause" in source

    build = _element(source, "Build photo pages")
    assert "aiOn" not in build, "building a report does not need a key"
    assert "canGenerate" not in build, "building a report does not need the key either"


def test_a_grey_generate_button_always_says_why():
    """The defect this closes: Spenser met a grey button, read it as the app
    being broken, and went looking for his API key. The key was fine; a
    fixture had put 61 photos in that job and the old ceiling refused it."""
    source = SCREEN.read_text()
    for reason in ("no_key", "local_only", "nothing_to_do"):
        assert 'blockedBecause === "%s"' % reason in source, reason


def test_the_unavailable_control_does_not_look_like_a_live_button():
    source = SCREEN.read_text()
    assert 'is-off' in source
    css = CSS.read_text()
    block = css[css.index(".button.is-off"):]
    block = block[:block.index("}")]
    assert "background: #EDEAE3" in block, "grey, not the live blue"
    assert "var(--ink-muted)" in block


def test_the_screen_says_captions_can_still_be_typed():
    source = SCREEN.read_text()
    assert "type every caption in yourself" in source
    assert "no key is set up on this computer" in source
