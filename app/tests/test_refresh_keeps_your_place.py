"""A browser refresh should not throw away where he was.

The audit found that reloading the page always returned to Jobs, from whatever
screen he was on. Every screen in this app lives at "/" and the view is state,
so there is nothing in the address for the browser to come back to.

This is the small version, and it is deliberately not routing. Giving each
screen a real address is a larger change than this pass was asked for; it is
written up instead. What is here remembers the last job screen for this tab
only, and refuses to restore one that is not still an active job.
"""
import re
from pathlib import Path

APP = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text()


def test_the_place_is_remembered_whenever_it_changes():
    assert "useEffect(() => { remember(view); }, [view]);" in APP


def test_it_is_this_tab_only():
    """sessionStorage, not localStorage: a new window is a new session."""
    assert "sessionStorage.setItem" in APP
    assert "sessionStorage.getItem" in APP
    assert "localStorage" not in APP


def test_only_screens_that_belong_to_a_job_come_back():
    """A setup step restored out of context would be worse than Jobs."""
    block = APP[APP.index("function lastPlace()"):]
    block = block[:block.index("\n}")]
    assert '["job", "photos", "sections"].includes(found.screen)' in block
    assert "found.job" in block


def test_a_job_that_is_no_longer_active_is_not_restored():
    block = APP[APP.index("const back ="):]
    block = block[:block.index("getDemo()")]
    assert "listJobs()" in block
    assert "live.some((one) => one.name === back.job)" in block


def test_a_damaged_or_unavailable_store_falls_back_to_jobs():
    """Private browsing, a full disk, or nonsense in the key."""
    for name in ("function remember(view)", "function lastPlace()"):
        block = APP[APP.index(name):]
        block = block[:block.index("\n}")]
        assert "try {" in block and "catch" in block


def test_nothing_is_restored_before_the_workspace_is_valid():
    block = APP[APP.index("const back ="):]
    block = block[:block.index("\n")]
    assert "saved && saved.valid" in block


def test_this_did_not_quietly_become_routing():
    """No history API, no router, no addresses. That is a separate decision."""
    assert "pushState" not in APP
    assert "window.location" not in APP
    assert not re.search(r"react-router", APP)
