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

**It is written to the app's own cache folder, never into a job folder.**

Standard library only, like everything else that runs before uvicorn is
imported. It has to work in a package whose wheels are the thing that went
missing.
"""
import os
import tempfile
from pathlib import Path

# How long the page waits before it stops saying "starting" and starts saying
# something went wrong. Longer than the longest good start measured, and short
# enough that nobody sits in front of a lie. The app's own start timeout is 30
# seconds after the server is told to run; this covers the package check too.
GIVE_UP_SECONDS = 150

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


def page(port: int, version: str) -> str:
    """The page itself. One file, no network, no fonts, no images."""
    url = "http://127.0.0.1:%d/" % int(port)
    # Tokens rather than per-cent formatting. This page is mostly CSS, and CSS
    # is full of per-cent signs: 38%, 100vh, and every keyframe stop. The same
    # trap the rollback batch file carries a comment about.
    return TEMPLATE.replace("{{MARK}}", MARK) \
                   .replace("{{VERSION}}", version or "") \
                   .replace("{{URL}}", url) \
                   .replace("{{SECONDS}}", str(GIVE_UP_SECONDS))


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
  <p class="say">Starting version {{VERSION}}. This takes a few seconds.</p>
  <div class="bar"><span></span></div>
  <div class="late">
    <p><strong>It has not started.</strong></p>
    <p>Close this tab and double-click the Roy R. Fisher icon on your Desktop
       again. If it happens twice, send Spenser this whole window.</p>
  </div>
</div>
<script>
(function () {
  var url = "{{URL}}";
  var stop = Date.now() + {{SECONDS}} * 1000;
  function look() {
    if (Date.now() > stop) { document.body.className = "is-late"; return; }
    // no-cors, because this page is a file on disk and the app is a server.
    // The answer is opaque and that is fine: reaching it at all is the news.
    fetch(url, { mode: "no-cors", cache: "no-store" })
      .then(function () { window.location.replace(url); })
      .catch(function () { setTimeout(look, 500); });
  }
  look();
})();
</script>
</body></html>
"""


def write(port: int, version: str, where: Path = None) -> Path:
    """Put the page on disk and return its path. Raises if it cannot."""
    folder = Path(where) if where else splash_dir()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "starting.html"
    temp = path.with_name("starting.%d.writing" % os.getpid())
    temp.write_text(page(port, version), encoding="utf-8")
    os.replace(str(temp), str(path))
    return path


def show(port: int, version: str, opener=None) -> bool:
    """Write it and open it. True if the browser was given something to show.

    Never raises. A splash screen is a courtesy; failing to draw one must never
    be a reason the app does not start. When this returns False the caller
    opens the app the old way, once the server answers.
    """
    if opener is None:
        import webbrowser
        opener = webbrowser.open
    try:
        path = write(port, version)
        return bool(opener(path.as_uri()))
    except Exception:
        return False
