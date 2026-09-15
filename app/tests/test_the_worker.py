"""The service that receives a log, read as a file and held to the app's facts.

Nothing here deploys anything, reaches Cloudflare, or proves the Worker runs.
It cannot: a Worker runs on Cloudflare's runtime and there is none on this
machine. What it can prove, and what has actually bitten this project, is that
the two halves agree. The recorded, repeating defect here is a value copied
instead of pointed at, and a Worker is the one place a copy is unavoidable: it
is a different language and cannot import a Python constant.

So the copy is allowed and it is checked. If the path, the size ceiling or the
first line of a log ever changes on one side, this fails on the other.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import applog        # noqa: E402
import logwindow     # noqa: E402
import sendlog       # noqa: E402

REPO = Path(__file__).resolve().parents[2]
WORKER = REPO / "tools" / "worker" / "send-the-log.js"


def source() -> str:
    return WORKER.read_text(encoding="utf-8")


def constant(name: str) -> str:
    """A `const NAME = "value"` or `const NAME = 12345` out of the Worker."""
    found = re.search(r'const\s+%s\s*=\s*("([^"]*)"|[0-9_ *]+);' % name, source())
    assert found, "the Worker has no constant called %s" % name
    return (found.group(2) if found.group(2) is not None else found.group(1)).strip()


def number(name: str) -> int:
    """An arithmetic constant, worked out rather than read as a digit string,
    so `2 * 1024 * 1024` can be written as the arithmetic it is."""
    text = constant(name)
    assert re.fullmatch(r"[0-9_ *]+", text), text
    total = 1
    for part in text.split("*"):
        total *= int(part.strip().replace("_", ""))
    return total


def test_the_worker_is_one_file_that_can_be_pasted_into_the_dashboard():
    assert WORKER.is_file()
    assert source().lstrip().startswith("/**")
    assert "export default" in source()


def test_its_path_agrees_with_the_app():
    assert constant("PATH") == sendlog.PATH


def test_its_size_ceiling_agrees_with_the_app():
    assert number("MAX_BYTES") == sendlog.MAX_SEND_BYTES


def test_what_it_believes_a_log_looks_like_agrees_with_what_the_app_writes():
    marker = constant("MARKER")
    assert marker
    assert logwindow.FIRST_LINE.startswith(marker)
    assert sendlog.MARKER.startswith(marker)


def test_it_refuses_every_method_and_path_but_the_one():
    text = source()
    assert '"POST"' in text
    assert "405" in text                     # the wrong method
    assert "404" in text                     # the wrong path


def test_it_refuses_an_oversized_body_without_reading_it():
    """Content-Length is read before the body is. A service that reads two
    megabytes to decide it did not want them is a service anybody can make
    expensive."""
    text = source()
    at_length = text.index("content-length")
    at_body = text.index("await request.text()")
    assert at_length < at_body
    assert "413" in text


def test_it_counts_both_ways_at_the_numbers_the_owner_approved():
    assert number("A_DAY") == 50             # globally
    assert number("AN_HOUR") == 5            # per visitor
    assert "429" in source()


def test_no_address_is_ever_stored_only_a_salted_hash_of_one():
    text = source()
    # The address is hashed with a secret salt before it becomes a counter
    # name, so the counters hold nothing that identifies a person.
    assert "SHA-256" in text
    # The one function that reads the address salts it and digests it, and
    # nothing else in the file reads the header at all.
    naming = text.split("async function visitorName")[1].split("\n}")[0]
    assert "cf-connecting-ip" in naming
    assert "env.ADDRESS_SALT" in naming
    assert 'crypto.subtle.digest("SHA-256"' in naming
    assert text.lower().count("cf-connecting-ip") == 1

    # And the per visitor counter is named by that function's answer, never by
    # the address.
    key = [line for line in text.splitlines() if "hourKey" in line and "=" in line][0]
    assert "visitorName" in key


def test_it_stores_before_it_emails():
    """Storage is the record and email is the notice. A failed email must not
    lose the log, which is only true if the log is already in the bucket."""
    text = source()
    assert text.index("LOGS.put") < text.index("api.resend.com")


def test_the_bucket_is_the_private_one_the_owner_named():
    assert constant("BUCKET_NAME") == "rrf-app-logs"
    assert "private" in source().lower()


def test_the_recipient_is_fixed_inside_the_worker():
    """The owner's decision. The app never sends a recipient, so nobody can
    turn this into a way to mail a stranger."""
    assert "d.spensernelson@gmail.com" in source()


def test_no_key_salt_or_password_is_written_into_this_file():
    """It lives in the repository, and the repository is not where a
    credential goes. Checked with `applog.redact`, the rule this project
    already trusts to recognise one, rather than a second list of words that
    would drift away from it."""
    text = source()
    assert applog.redact(text) == text
    assert "re_" not in text                 # Resend's own key prefix
    assert "sk-ant-" not in text


def test_both_secrets_are_read_off_the_environment_and_never_written_down():
    text = source()
    for name in ("RESEND_KEY", "ADDRESS_SALT"):
        uses = [found.start() for found in re.finditer(name, text)]
        assert uses, name
        # Every place the name appears in code is `env.NAME`. Anywhere else it
        # appears is prose in the header comment, which is where the dashboard
        # instructions live.
        for at in uses:
            line = text[text.rfind("\n", 0, at) + 1:text.find("\n", at)]
            assert "env.%s" % name in line or line.lstrip().startswith("*"), line


def test_the_worker_never_ships_inside_the_package():
    """`tools/` is not copied into the package. Said out loud here because the
    Worker is the half that holds credentials at run time, and the package is
    public: anyone can download it, so anything inside it is public."""
    script = (REPO / "tools" / "package_windows.py").read_text(encoding="utf-8")
    copy_app = script.split("def copy_app")[1].split("\ndef ")[0]
    assert "tools" not in copy_app
