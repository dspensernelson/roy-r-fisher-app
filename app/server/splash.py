"""The page that says the app is starting, so a click never looks like nothing.

Double-clicking the icon used to do nothing visible for several seconds. The
package check hashes every file in the package, then uvicorn is imported and
the server has to answer, and only then does the browser open. All of that used
to happen behind a black console window that said "Starting Roy R. Fisher". The
window went on 2026-09-03, and the only proof the click had landed went with it.
Spenser, 2026-09-04: *"Can we make a loading screen?"*

This is that screen. It is a plain file on disk, opened in the browser before
the slow work starts, and it replaces itself with the app the moment the app
answers.

It is a courtesy and nothing rests on it. A page loaded from a file on disk may
be barred by the browser from asking a server on the same computer anything,
which is what Edge did on Mark's machine on 2026-09-14, and from inside the
page that is indistinguishable from the app being dead. So the app opens itself
in its own tab as soon as it answers, whatever this page manages, and this page
never claims the app failed.

**It is written to the app's own cache folder, never into a job folder.**

Standard library only, like everything else that runs before uvicorn is
imported. It has to work in a package whose wheels are the thing that went
missing.
"""
import os
import tempfile
from pathlib import Path

import startup            # standard library only, same as this module

# How long the page waits before it stops saying "starting" and starts
# pointing somewhere else.
#
# It was 150 seconds, on the reasoning that the wait had to cover the slowest
# possible good start. That reasoning fell on 2026-09-14: on Mark's Windows
# machine this page could not reach the app at all, so the wait was not a wait
# for a slow start, it was two and a half minutes of a sweeping bar leading to
# a sentence that was false. The app opens itself in its own tab the moment it
# answers now, so this page no longer has to carry anybody anywhere, and being
# early costs nothing.
#
# 20 seconds: shorter than the 30 the app itself waits for its own server, so
# in the bad case nobody is left staring, and long enough that a normal start,
# which is a few seconds, hands over first and this is never seen. It keeps
# looking after it says this, so a genuinely slow start is still carried over.
GIVE_UP_SECONDS = 20

# How often it asks, before and after it has given up. It slows down once it
# has said its piece, because a tab somebody forgot to close should not sit
# there asking twice a second all afternoon.
LOOK_EVERY_MS = 500
LOOK_EVERY_LATE_MS = 2000

# The mark, traced from the firm's logo files. Written out rather than read from
# a file, because this page has to render before anything is served and a
# missing asset would leave a broken image where the firm's mark should be.
MARK = ('<svg width="30" height="80" viewBox="0 0 80 215" role="img" aria-label="Roy R. Fisher">'
        '<polygon fill="#231F20" points="21,55 21,195 1,195 1,77"></polygon>'
        '<polygon fill="#8C0C04" points="54,2 54,214 26,214 26,26"></polygon>'
        '<polygon fill="#231F20" points="59,55 79,76 79,195 59,195"></polygon>'
        '</svg>')


def splash_dir() -> Path:
    """Beside the app's other working files, never inside a job.

    Falls back to the machine's temp folder, because a splash screen that
    cannot be written must never be a reason the app does not start.
    """
    try:
        import thumbcache
        return thumbcache.cache_root()
    except Exception:
        return Path(tempfile.gettempdir())


def page(port: int, version: str, saying: str = None, patience: int = None) -> str:
    """The page itself. One file, no network, no fonts, no images.

    `saying` is the one line it shows. It defaults to the ordinary start, and
    is given something else when the app has to stop a copy that is already
    running before it can start, because that is a different several seconds
    and the screen should not describe it wrongly.

    `patience` is how long it waits before it stops saying "starting" and
    points at the other tab. It is longer when a copy is being stopped first,
    since that wait is legitimate and pointing him at another tab in the middle
    of it would point him at the copy being closed.
    """
    url = "http://127.0.0.1:%d/" % int(port)
    # Two addresses, and the difference is the point. The page asks on the
    # first, which is the route whose only caller is this page, so the app
    # hearing it knows the page is not blocked and does not open a tab of its
    # own. Then the page goes to the second, which is the app.
    ask = url.rstrip("/") + startup.LOADING_PAGE_PATH
    saying = saying or ("Starting version %s. This takes a few seconds."
                        % (version or ""))
    # Tokens rather than per-cent formatting. This page is mostly CSS, and CSS
    # is full of per-cent signs: 38%, 100vh, and every keyframe stop. The same
    # trap the rollback batch file carries a comment about.
    return TEMPLATE.replace("{{MARK}}", MARK) \
                   .replace("{{SAY}}", saying) \
                   .replace("{{ASK}}", ask) \
                   .replace("{{URL}}", url) \
                   .replace("{{SECONDS}}", str(int(patience or GIVE_UP_SECONDS))) \
                   .replace("{{EVERY}}", str(LOOK_EVERY_MS)) \
                   .replace("{{LATE}}", str(LOOK_EVERY_LATE_MS))


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Starting Roy R. Fisher</title>
<style>
  :root { color-scheme: light; }
  body {
    margin: 0; min-height: 100vh; background: #FAF8F4; color: #231F20;
    font: 16px/1.55 "Segoe UI", -apple-system, "Helvetica Neue", Helvetica, Arial, sans-serif;
    display: grid; place-items: center;
  }
  .band { position: fixed; top: 0; left: 0; right: 0; height: 3px; background: #8C0C04; }
  .box { text-align: center; padding: 24px; }
  .mark { display: block; margin: 0 auto 18px; }
  h1 {
    font-family: Georgia, "Times New Roman", serif; font-size: 21px; font-weight: 600;
    letter-spacing: 0.22em; margin: 0 0 4px;
  }
  .tag { font-size: 11.5px; font-style: italic; color: #6E6E73; margin: 0 0 26px; }
  .say { font-size: 15px; margin: 0 0 14px; }
  .bar { width: 190px; height: 4px; background: #E3E0D8; border-radius: 2px;
         overflow: hidden; margin: 0 auto; }
  .bar span { display: block; width: 38%; height: 100%; background: #8C0C04;
              border-radius: 2px; animation: sweep 1.15s ease-in-out infinite; }
  @keyframes sweep { 0% { transform: translateX(-110%); } 100% { transform: translateX(370%); } }
  @media (prefers-reduced-motion: reduce) { .bar span { animation: none; width: 100%; } }
  .late { display: none; max-width: 46ch; margin: 0 auto; color: #231F20; }
  body.is-late .bar, body.is-late .say { display: none; }
  body.is-late .late { display: block; }
</style></head>
<body>
<div class="band"></div>
<div class="box">
  {{MARK}}
  <h1>ROY R. FISHER</h1>
  <p class="tag">&ldquo;The Established Commercial Valuation Experts&rdquo;</p>
  <p class="say">{{SAY}}</p>
  <div class="bar"><span></span></div>
  <div class="late">
    <p><strong>Roy R. Fisher has probably opened in another tab.</strong></p>
    <p>This window could not reach it, which on some computers is just how the
       browser is set up. Look along the top of your browser for the other tab
       and carry on there. You can close this one.</p>
    <p>If there is no other tab, double-click the Roy R. Fisher icon on your
       Desktop again. If that does not work either, send Spenser this whole
       window.</p>
  </div>
</div>
<script>
(function () {
  var app = "{{URL}}";
  var ask = "{{ASK}}";
  var stop = Date.now() + {{SECONDS}} * 1000;
  var wait = {{EVERY}};
  function look() {
    // Giving up changes what this says, not what it is doing. It keeps
    // asking, more slowly, so a start that was merely slow still lands here
    // rather than leaving the person to find the other tab by hand.
    if (Date.now() > stop) { document.body.className = "is-late"; wait = {{LATE}}; }
    // no-cors, because this page is a file on disk and the app is a server.
    // The answer is opaque and that is fine: reaching it at all is the news,
    // and it is the news at both ends. The app counts this request as the
    // proof that this page is not blocked, and so does not open a tab of its
    // own beside the one this page is about to become.
    fetch(ask, { mode: "no-cors", cache: "no-store" })
      .then(function () { window.location.replace(app); })
      .catch(function () { setTimeout(look, wait); });
  }
  look();
})();
</script>
</body></html>
"""


def write(port: int, version: str, where: Path = None, saying: str = None,
          patience: int = None) -> Path:
    """Put the page on disk and return its path. Raises if it cannot."""
    folder = Path(where) if where else splash_dir()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "starting.html"
    temp = path.with_name("starting.%d.writing" % os.getpid())
    temp.write_text(page(port, version, saying, patience), encoding="utf-8")
    os.replace(str(temp), str(path))
    return path


def show(port: int, version: str, opener=None, saying: str = None,
         patience: int = None) -> bool:
    """Write it and open it. True if the browser was given something to show.

    Never raises. A splash screen is a courtesy; failing to draw one must never
    be a reason the app does not start. When this returns False the caller
    opens the app the old way, once the server answers.
    """
    if opener is None:
        import webbrowser
        opener = webbrowser.open
    try:
        path = write(port, version, saying=saying, patience=patience)
        return bool(opener(path.as_uri()))
    except Exception:
        return False
