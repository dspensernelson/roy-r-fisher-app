import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Mark's delivered reports and his own folder template. Private material: it
# is not in this repository and never will be, so every test that needs a
# piece of it says which piece and skips when it is not there.
#
# It moved next door on 2026-08-21, when the application repository was split
# out of the evidence vault, and this path did not follow it. The corpus was
# still on the machine and fifteen tests had been quietly skipping ever since,
# including the one that compares a built document against a delivered report.
# Both places are checked so the same suite works either side of that split and
# on a clone that has neither.
#
# Walking up came later, on 2026-09-02, and it is the same defect a third time.
# A git worktree sits deeper than the checkout, so the path beside it misses
# and 124 tests skipped on a machine with the corpus sitting right there. That
# is worse than a failure: a skip reads as "this machine does not have it" and
# a candidate looks proven when it was never run. `tools/photo_source.py` was
# fixed this way on 2026-08-28 and this module never got it.
#
# RRF_CORPUS overrides, the same way RRF_PHOTO_SOURCE already does. Read-only
# in every one of these places. Nothing here ever writes to the corpus.
def _find_corpus() -> Path:
    override = os.environ.get("RRF_CORPUS")
    if override:
        return Path(override)
    here = REPO_ROOT
    for _ in range(4):
        beside = here.parent / "RRF" / "Report Examples"
        if beside.is_dir():
            return beside
        inside = here / "Report Examples"
        if inside.is_dir():
            return inside
        here = here.parent
    return REPO_ROOT.parent / "RRF" / "Report Examples"


CORPUS = _find_corpus()
TEMPLATE_DOCX = CORPUS / "Templates and Other" / "Mark Folder Template" / "Photos" / "Photo.docx"
GOLDEN_PHOTOS = (CORPUS / "MASON CITY_Walmart_4151 4th St SW" / "Photos"
                 / "Raw pics_Walmart Mason City 4151 4th St SW" / "All report photos used")
GOLDEN_DELIVERED = (CORPUS / "MASON CITY_Walmart_4151 4th St SW" / "Photos"
                    / "PHOTOS_Mason City_ 4151_4th_St_SW_(Walmart).docx")


def _golden_ready() -> bool:
    """The Mason City photos and the delivered document the golden test
    compares against. Checked properly, because the photos live inside a
    Photos folder and .gitignore excludes those by design."""
    if not GOLDEN_DELIVERED.is_file() or not GOLDEN_PHOTOS.is_dir():
        return False
    return len(list(GOLDEN_PHOTOS.glob("*.jpeg"))) >= 12


# Checking the corpus ROOT was not enough and quietly cost a test run. The
# root is tracked, so on a fresh clone it exists while everything inside a
# Photos folder does not, and the guard passed while the test failed. Each
# guard now checks the exact file the tests behind it open.
has_template = pytest.mark.skipif(
    not TEMPLATE_DOCX.is_file(),
    reason="Mark's folder template is private and not in this repository",
)

has_golden_corpus = pytest.mark.skipif(
    not (TEMPLATE_DOCX.is_file() and _golden_ready()),
    reason="the Mason City delivered report and its photos are private and not in this repository",
)


@pytest.fixture(autouse=True)
def never_touch_the_real_home(tmp_path_factory, monkeypatch):
    """No test may write into Spenser's own home folder.

    Found the hard way. A job the app creates is now marked active, which
    writes the settings file, and tests that only overrode RRF_JOBS_HOME
    wrote into his real ~/.rrf-app.json instead. Forty entries pointing at
    pytest temporary folders ended up in it. A test that reaches outside its
    own tmp_path is a bug in the test, so this closes the door for all of
    them at once rather than one file at a time.
    """
    box = tmp_path_factory.mktemp("home")
    monkeypatch.setenv("RRF_SETTINGS_FILE", str(box / ".rrf-app.json"))
    monkeypatch.setenv("RRF_KEY_FILE", str(box / ".rrf-app.env"))
    # Every app-owned file, not only the two that already existed. The
    # classification store was missing from this list and only individual
    # tests overrode it, so any test that classified a file without setting
    # RRF_CLASSIFY_FILE itself wrote into his real home. Task 2 added three
    # more of these, and one forgotten line here would put every one of them
    # in the same position, so the list is kept complete rather than added to
    # a test at a time.
    monkeypatch.setenv("RRF_CLASSIFY_FILE", str(box / ".rrf-classifications.json"))
    monkeypatch.setenv("RRF_VERSION_FILE", str(box / ".rrf-app-version.json"))
    monkeypatch.setenv("RRF_USAGE_FILE", str(box / ".rrf-ai-usage.json"))
    monkeypatch.setenv("RRF_AI_POLICY_FILE", str(box / ".rrf-demo-ai-policy.json"))
    monkeypatch.setenv("RRF_JOBFACTS_FILE", str(box / ".rrf-job-facts.json"))
    # The app's own log, added 2026-09-02. The same reasoning as every entry
    # above it: a test that logs without this set would otherwise write into
    # Spenser's real ~/.rrf-app.log.
    monkeypatch.setenv("RRF_LOG_FILE", str(box / ".rrf-app.log"))
    # The thumbnail cache, added 2026-08-22 when thumbnails moved out of
    # Mark's Photos folder. Missing it did exactly what the comment above
    # predicts: every suite run left a fresh folder of thumbnails in the
    # real home directory, one per pytest tmp_path, accumulating for ever.
    monkeypatch.setenv("RRF_CACHE_DIR", str(box / ".rrf-app-cache"))
    # The update scratch folder, added 2026-08-28 with the in-app update
    # button. Same reason as every line above it: a test that downloads a
    # package without this would write 53 MB into his real home folder, once
    # per run, for ever.
    monkeypatch.setenv("RRF_DOWNLOAD_DIR", str(box / ".rrf-app-download"))


@pytest.fixture
def template_path() -> Path:
    return TEMPLATE_DOCX


# --- a stand-in for the update bucket ---------------------------------------
class FakeBucket:
    """A real HTTP server on a loopback port, serving whatever it is told to.

    Shared rather than copied into each test file, because two copies of a test
    double drift the same way two copies of anything else do.

    This proves a narrow mechanic: reading, validating, downloading and
    refusing. It claims nothing about Cloudflare, about R2, or about Mark's
    network, and it is not evidence that any of those work.
    """

    def __init__(self):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer
        self.files = {}
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                from urllib.parse import unquote
                body = outer.files.get(unquote(self.path.lstrip("/")))
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

        class Quiet(HTTPServer):
            # A cancelled or refused download closes the connection part way
            # through, which is the behaviour under test. socketserver prints a
            # traceback for it, which would make a passing suite look broken.
            def handle_error(self, *_args):
                pass

        self.server = Quiet(("127.0.0.1", 0), Handler)
        # A short poll interval, because the default is half a second and
        # shutdown waits for it. Sixty tests each paying that would add half a
        # minute to a suite that runs in under thirty seconds.
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01},
            daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return "http://127.0.0.1:%d" % self.server.server_address[1]

    def put(self, name, body) -> None:
        self.files[name] = body if isinstance(body, bytes) else body.encode("utf-8")

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def fake_bucket(monkeypatch):
    """A bucket the app will read from, already pointed at by the environment."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
    import updates

    made = FakeBucket()
    monkeypatch.setenv("RRF_UPDATE_BUCKET", made.url)
    updates.forget()
    updates.end_run()
    yield made
    made.close()
    updates.forget()
    updates.end_run()
