"""No test, and no suite run, may write into Spenser's own home folder.

`conftest.never_touch_the_real_home` redirects every app-owned file into a
temporary folder. It works only while the list is complete, and its own comment
says so: "one forgotten line here would put every one of them in the same
position".

That happened. Thumbnails moved out of Mark's Photos folder into app-owned
storage on 2026-08-22, the new override was not added to that list, and every
suite run left a fresh folder of thumbnails in the real home directory, one per
pytest temporary folder, accumulating for ever.

This test is the thing that would have caught it: it asks each module where it
would write right now, and fails if the answer is the real home folder.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))

import aipolicy  # noqa: E402
import appversion  # noqa: E402
import classify  # noqa: E402
import jobfacts  # noqa: E402
import settings  # noqa: E402
import thumbcache  # noqa: E402
import usage  # noqa: E402
import workspace  # noqa: E402

# Every module that owns a file or folder in the home directory, and the
# function that answers where it is. Adding one to the app means adding it
# here, and the test then insists conftest redirects it.
OWNED = [
    ("settings key", settings.key_file),
    ("workspace settings", workspace.settings_file),
    ("classifications", classify.store_file),
    ("last-good version", appversion.store_file),
    ("AI usage history", usage.store_file),
    ("demo AI policy", aipolicy.policy_file),
    ("job facts", jobfacts.store_file),
    ("thumbnail cache", thumbcache.cache_root),
]


def test_every_app_owned_path_is_redirected_during_tests():
    home = Path.home().resolve()
    escaping = []
    for name, where in OWNED:
        target = Path(where()).resolve()
        if target == home or home in target.parents:
            escaping.append("%s -> %s" % (name, target))
    assert not escaping, (
        "these would be written into the real home folder during a test run:\n  "
        + "\n  ".join(escaping))


def test_the_thumbnail_cache_is_one_of_them():
    """The specific gap that let this happen, named so it cannot reopen."""
    assert any(name == "thumbnail cache" for name, _ in OWNED)
    conftest = (Path(__file__).resolve().parent / "conftest.py").read_text()
    assert "RRF_CACHE_DIR" in conftest
