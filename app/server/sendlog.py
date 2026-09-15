"""Putting the log on the wire. One POST, and no way to aim it at anybody.

**What the owner decided, on 2026-09-14.** She presses one button and the last
two days of the log reach his email. She never picks a file, finds a folder, or
attaches anything. The recipient is fixed inside the receiving service and is
never sent by the app, so nothing here, and nothing anybody adds here later,
can turn this into a way to mail a stranger.

**Nothing secret is in this file, and nothing secret may ever be put in it.**
The package is public: anyone can download it, so anything inside it is public
knowledge. The service is what holds the mail key and the salt, as Worker
secrets set in the Cloudflare dashboard. The app carries no credential at all,
which is why the service has to count sends for itself rather than trust a
caller who could be anybody.

**Nothing here ever raises at its caller.** Same rule as `updates.py`, for the
same reason: the person pressing this button already has a problem, and an
error thrown out of the thing that was meant to report the problem is the worst
possible answer. Every failure comes back as a sentence she can act on, and
every sentence names the way through: the text is already on her screen, she
can copy it, and she can paste it into an email. There must be no dead end.

**The certificate context and the name we go by are pointed at, not copied.**
Both live in `updates.py`, both were found the hard way on 2026-09-02, and this
project has a recorded, repeating defect where a value is copied instead of
pointed at and the copy quietly stops agreeing. A second `ssl.create_default_context`
here would be that defect a sixth time.

Standard library only, like `updates.py` and `packaging.py` beside it.
"""
import os
import urllib.error
import urllib.request

import applog
import logwindow
import updates

# Where the log goes. Empty until the Cloudflare Worker in
# `tools/worker/send-the-log.js` is deployed and its address is pasted in here.
# Empty is a state this module reports honestly rather than dressing up as a
# network fault: an address nobody set is not the internet being off.
#
# It is the Worker's base address with no path. `PATH` is added below, the same
# shape `updates.bucket_url` and `updates.file_url` already use, so the one
# route the service accepts is written once.
ENDPOINT = ""

# The only route the Worker accepts. The test in `test_the_worker.py` reads the
# Worker source and checks it agrees with this.
PATH = "/send"

# The ceiling the Worker refuses at without reading the body. Two megabytes.
# `logwindow` already caps a send at one, so reaching this means something is
# wrong rather than something is large, and it is checked here so an absurd
# body is refused before the network is touched at all.
MAX_SEND_BYTES = 2 * 1024 * 1024

# What the service checks before it accepts anything, so a stray POST from
# somewhere else is refused rather than stored. Pointed at `logwindow` rather
# than typed again.
MARKER = logwindow.FIRST_LINE

SEND_TIMEOUT = 30.0

# Shown to her, never sent. It is in the fallback sentences so a failure always
# ends somewhere she can go, and it is in no request this module makes: a test
# asserts it is absent from the body and the headers.
SPENSER_EMAIL = "d.spensernelson@gmail.com"

# The way through, in one place, because it is the end of every refusal here
# and four copies of it would become four different sentences.
THE_WAY_THROUGH = (
    "You can still get it to him yourself: press Show what will be sent, "
    "press Copy, and paste it into an email to %s." % SPENSER_EMAIL)

SENT = "Sent. Spenser has the last two days of the log. You can carry on."

NOTHING_TO_SEND = (
    "Nothing has been written yet, so there is no log to send. "
    "If a screen is misbehaving, use it once and then press this again.")

CANNOT_REACH = (
    "The log could not be sent. The internet may be off, or the service may "
    "be down. Try again in a minute.\n" + THE_WAY_THROUGH)

TOO_OFTEN = (
    "One log already arrived from this computer in the last hour, so this one "
    "was not sent.\n" + THE_WAY_THROUGH)

NO_ADDRESS = (
    "This copy of the app has not been given an address to send to yet, so "
    "nothing was sent and nothing is wrong with your computer.\n"
    + THE_WAY_THROUGH)

TOO_BIG = (
    "The log is too large to send in one piece, so nothing was sent.\n"
    + THE_WAY_THROUGH)


def endpoint() -> str:
    """The Worker's base address. RRF_LOG_ENDPOINT overrides, for tests, the
    same way RRF_UPDATE_BUCKET already does for the bucket."""
    return (os.environ.get("RRF_LOG_ENDPOINT") or ENDPOINT).strip().rstrip("/")


def send_url() -> str:
    """The one address a log is ever posted to, or empty when none is set."""
    base = endpoint()
    return (base + PATH) if base else ""


def _refused(message: str, reason: str, **fields) -> dict:
    applog.note("log send refused", reason=reason, **fields)
    return {"sent": False, "message": message, "reason": reason}


def send(text: str) -> dict:
    """Post the log. Returns whether it went and the sentence to put on screen.

    Never raises, whatever happens. `reason` is a short word for the log and
    for a test, never for the screen: the screen shows `message`, which is the
    same sentence wherever it appears.

    `redact` is applied here as well as in `logwindow`, deliberately. A line
    already on her disk was written by whatever version of `applog` was
    running that day, and this is the last place that can still catch a key
    in one of them.
    """
    try:
        body = applog.redact(text or "")
        if not body.strip():
            return _refused(NOTHING_TO_SEND, "empty")

        encoded = body.encode("utf-8")
        if len(encoded) > MAX_SEND_BYTES:
            return _refused(TOO_BIG, "too big", bytes=len(encoded))

        url = send_url()
        if not url:
            return _refused(NO_ADDRESS, "no address")

        request = urllib.request.Request(
            url, data=encoded, method="POST",
            headers={"User-Agent": updates.USER_AGENT,
                     "Content-Type": "text/plain; charset=utf-8"})
        try:
            with urllib.request.urlopen(request, timeout=SEND_TIMEOUT,
                                        context=updates.ssl_context()) as answer:
                # Read and discard. The service answers a few bytes; reading
                # them is what finishes the request cleanly.
                answer.read(1024)
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                return _refused(TOO_OFTEN, "too often")
            return _refused(CANNOT_REACH, "refused", status=exc.code)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            return _refused(CANNOT_REACH, "unreachable", error=str(exc))

        applog.note("log sent", bytes=len(encoded))
        return {"sent": True, "message": SENT, "reason": ""}
    except Exception as exc:                          # never at the caller
        return _refused(CANNOT_REACH, "failed", error=str(exc))


def send_the_recent_log(version="") -> dict:
    """Read the last two days and post them. What the button ends up calling.

    One function so the screen cannot send something other than what
    `/api/log/recent` showed: both go through `logwindow.recent`.
    """
    found = logwindow.recent(version=version)
    if found["empty"]:
        return {"sent": False, "message": NOTHING_TO_SEND, "reason": "empty"}
    answer = send(found["text"])
    answer["lines"] = found["lines"]
    return answer
