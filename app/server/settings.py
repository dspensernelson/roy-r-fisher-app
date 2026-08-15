"""Where Mark's Anthropic key lives, and how the app reads and changes it.

The key sits in a small file in his home folder, never inside the project, so
git can never see it. The launcher already reads that file on startup; this
module is the same file's other door, the one with a screen in front of it.

Three rules this module exists to keep:

- The key is never returned to the browser, never logged, never put in a job.
  Callers get a yes or no and the last four characters, nothing more.
- Saving takes effect in the running process, so nothing has to be restarted.
- The file may hold other lines a human put there. Rewriting the key leaves
  every other line exactly as it was.
"""
import os
from pathlib import Path

KEY_NAME = "ANTHROPIC_API_KEY"


class BadKey(Exception):
    """The service rejected the key. Distinct from being unable to reach it."""


def key_file() -> Path:
    """Home folder on both Mac and Windows. RRF_KEY_FILE overrides, for tests."""
    override = os.environ.get("RRF_KEY_FILE")
    return Path(override) if override else Path.home() / ".rrf-app.env"


def _lines() -> list:
    path = key_file()
    if not path.is_file():
        return []
    return path.read_text(errors="ignore").splitlines()


def _write(lines: list) -> None:
    path = key_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(line for line in lines if line.strip()) + "\n")
    try:
        path.chmod(0o600)
    except (OSError, NotImplementedError):
        # Windows has no POSIX mode bits. The file still sits in the user's
        # own profile folder, which is the protection that matters there.
        pass


def _unquote(value: str) -> str:
    """Strip one matching pair of surrounding quotes.

    The file was written to be read by a shell, so a value may be quoted.
    Python has to understand the same file the shell used to.
    """
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def stored_key() -> str:
    """The key in the file, or empty. Never raises on a malformed file.

    A line may carry a leading `export`, may be indented, and may be quoted,
    because a human or an older launcher may have written it. Anything that
    is not a well-formed ANTHROPIC_API_KEY line is ignored rather than
    guessed at.
    """
    for line in _lines():
        text = line.strip()
        if text.startswith("export "):
            text = text[len("export "):].lstrip()
        name, sep, value = text.partition("=")
        if sep and name.strip() == KEY_NAME:
            found = _unquote(value)
            if found:
                return found
    return ""


def active_key() -> str:
    """The key this program will actually use, or empty if there is none.

    One place, so every part of the app agrees. An environment variable wins,
    which is what lets a test or a developer override without touching the
    file. Below that, the file. Below that, nothing, and captions turn
    themselves off and say so.

    The launcher used to inject this by sourcing the file with the shell.
    Python reads it here instead, so starting the app any way at all gives
    the same answer, and so Mark's Windows machine needs no shell.
    """
    return os.environ.get(KEY_NAME, "").strip() or stored_key()


def status() -> dict:
    """What the screen is allowed to know: whether a key is set, and its last
    four characters so Mark can tell one key from another."""
    key = active_key()
    return {"key_set": bool(key), "ends_with": key[-4:] if len(key) >= 4 else ""}


def check_key(key: str) -> None:
    """Ask the service whether this key works.

    Raises BadKey when it is refused, and lets any other error through so the
    caller can tell 'wrong key' apart from 'no internet right now'.
    """
    import anthropic

    try:
        anthropic.Anthropic(api_key=key).models.list(limit=1)
    except anthropic.AuthenticationError as exc:
        raise BadKey("that key was not accepted") from exc
    except anthropic.PermissionDeniedError as exc:
        raise BadKey("that key does not have access") from exc


def save_key(key: str) -> None:
    kept = [line for line in _lines() if not line.startswith(f"{KEY_NAME}=")]
    _write(kept + [f"{KEY_NAME}={key}"])
    os.environ[KEY_NAME] = key          # live, so nothing needs restarting


def remove_key() -> None:
    _write([line for line in _lines() if not line.startswith(f"{KEY_NAME}=")])
    os.environ.pop(KEY_NAME, None)
