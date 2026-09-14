"""One web page the Windows virtual machine can use to fetch builds and send
files back.

**Why this exists.** Everything in this app that matters runs on Windows, and
nothing here is a Windows machine. So a build has to get to the virtual machine,
and its output has to get back. Shared folders between a Mac and a virtual
machine are fiddly and break on a reboot. A web page is not.

Two halves, both on one page.

- **Down.** Every file in the serve folder is a link. Click it in Edge.
- **Up.** A box that takes a file and writes it to the landing folder on the
  Mac, where it can be read and looked at.

Nothing here is clever and nothing here is secure. It is a development tool on
one machine, it is not in the package Mark gets, and it should not be left
running when it is not wanted.

**It binds to the virtual machine's own network address, not to everything.**
That address only exists between this Mac and the virtual machines on it, so
nothing on the house network or anywhere else can reach this page. Binding to
every address would have been one character shorter and would have published a
file-upload box to the local network.

**It is threaded on purpose.** The plain server handles one connection at a
time, and Edge holds a connection open after a download. That wedged it
completely on 2026-09-04: the page stopped answering while the process looked
perfectly healthy.

Run it:

    python3 tools/to_and_from_the_vm.py

Standard library only.
"""
import argparse
import http.server
import sys
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import quote

REPO = Path(__file__).resolve().parents[1]

# Where builds are picked up from and where the virtual machine's files land.
# Both sit under build/, which is not in the repository, so nothing a test
# machine sends back is ever committed by accident.
SERVE = REPO / "build" / "packages"
LANDING = REPO / "build" / "from-the-vm"

# The address of the Mac as the virtual machine sees it. See the note at the
# top about why this is not 0.0.0.0.
HOST = "192.168.64.1"
PORT = 8088

TOP = """<!doctype html><meta charset=utf-8>
<title>Roy R. Fisher: to and from the Mac</title>
<style>body{font:16px system-ui;margin:60px auto;max-width:640px;padding:0 16px}
h1{font-size:22px}h2{font-size:17px;margin-top:36px}input{font:inherit}
a{display:block;padding:6px 0}
button{font:inherit;padding:10px 18px;margin-top:16px}
.drop{border:2px dashed #999;padding:40px;text-align:center;border-radius:8px}
.none{color:#666}</style>
<h1>Roy R. Fisher: to and from the Mac</h1>
<h2>Download to this PC</h2>
"""

BOTTOM = """<h2>Send a file back to the Mac</h2>
<form method=post enctype=multipart/form-data action=/upload>
  <div class=drop>
    <p>Choose the file, or drag it onto this box.</p>
    <input type=file name=f multiple>
  </div>
  <button type=submit>Send it</button>
</form>
"""


def page(serve: Path) -> bytes:
    """Built on every request, so a package made a moment ago is listed.

    Deliberately not built once at start up. The whole point is to build
    something, refresh, and take it, and a page that listed what was there when
    the server started would be wrong exactly when it was wanted.
    """
    links = []
    for one in sorted(serve.glob("*")):
        if one.is_file():
            links.append("<a href='/%s'>%s  (%.1f MB)</a>"
                         % (quote(one.name), one.name,
                            one.stat().st_size / (1024.0 * 1024.0)))
    listed = "".join(links) or "<p class=none>Nothing is built yet.</p>"
    return (TOP + listed + BOTTOM).encode("utf-8")


def _files_in(body: bytes, content_type: str):
    """The uploaded files, as (name, bytes).

    Parsed with the email module rather than `cgi`. `cgi` does this in one
    line and was removed from Python in 3.13, so a tool written against it
    stops working the day this Mac's Python is upgraded. A multipart form and
    a multipart email are the same format, which is why this works.
    """
    headers = (b"MIME-Version: 1.0\r\nContent-Type: "
               + content_type.encode("utf-8", "replace") + b"\r\n\r\n")
    message = BytesParser().parsebytes(headers + body)
    if not message.is_multipart():
        return []
    found = []
    for part in message.get_payload():
        name = part.get_filename()
        if not name:
            continue
        # Only the last part of the name. A browser can send a path, and a
        # path could climb out of the landing folder.
        found.append((Path(name).name, part.get_payload(decode=True) or b""))
    return found


class Page(http.server.SimpleHTTPRequestHandler):

    serve = SERVE
    landing = LANDING

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.serve), **kwargs)

    def _send(self, body: bytes, kind="text/html; charset=utf-8") -> None:
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(page(self.serve))
            return
        # Everything else is a file in the serve folder, handled by the parent.
        return super().do_GET()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        body = self.rfile.read(length) if length else b""
        got = []
        try:
            for name, blob in _files_in(body, self.headers.get("Content-Type", "")):
                self.landing.mkdir(parents=True, exist_ok=True)
                (self.landing / name).write_bytes(blob)
                got.append("%s  (%.1f KB)" % (name, len(blob) / 1024.0))
                print("received %s" % name, flush=True)
        except Exception as exc:
            # A failed upload says so on the page. The person doing this is
            # standing at another computer and cannot see this window.
            print("upload failed: %s" % exc, flush=True)
            self._send(("<!doctype html><meta charset=utf-8><h1>That did not "
                        "work</h1><p>%s</p><p><a href='/'>Back</a></p>"
                        % exc).encode("utf-8"))
            return
        self._send(
            ("<!doctype html><meta charset=utf-8>"
             "<style>body{font:16px system-ui;margin:60px auto;max-width:640px}"
             "</style><h1>Got it</h1><p>%s</p><p><a href='/'>Send another</a></p>"
             % ("<br>".join(got) or "Nothing was chosen.")).encode("utf-8"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--serve", default=str(SERVE),
                        help="folder whose files the virtual machine can download")
    parser.add_argument("--landing", default=str(LANDING),
                        help="folder that files sent back are written into")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    chosen = parser.parse_args(argv)

    Page.serve = Path(chosen.serve)
    Page.landing = Path(chosen.landing)
    Page.serve.mkdir(parents=True, exist_ok=True)
    Page.landing.mkdir(parents=True, exist_ok=True)

    server = http.server.ThreadingHTTPServer((chosen.host, chosen.port), Page)
    server.daemon_threads = True
    print("Serving   %s" % Page.serve)
    print("Landing   %s" % Page.landing)
    print()
    print("Open this on the virtual machine:")
    print("    http://%s:%d/" % (chosen.host, chosen.port))
    print()
    print("Control-C stops it.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
        print("Stopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
