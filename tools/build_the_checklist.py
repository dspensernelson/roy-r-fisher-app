"""Turn `docs/NOW.md` into the page Spenser actually works from.

**Why this is a file and not three lines typed into a shell each time.** The
checklist is republished every session and it was being regenerated from
memory, which is how prose got onto it twice and how items got truncated from
wrapped lines. The rules for what the page may contain are written down here,
next to the code that enforces them, and `test_the_checklist.py` holds them.

**What the page is for.** He does not open markdown. This page is the only
place he sees the state of the project, so it has to be readable at a glance
on a phone and on a laptop, and it has to survive being scrolled by somebody
who is tired.

**The rules it enforces, all of which were learned the hard way:**

- Every item is one line. No paragraphs. A wrapped line is how an item lost
  its ending on 2026-09-15.
- No bug numbers and no codes. `B15` means nothing to him and he said so.
- Nothing is invented here. The text is whatever `docs/NOW.md` says, escaped
  and nothing else. This file must never add a word.

**What it adds that the old inline version did not:** a count on every heading,
so the shape of the work is visible without reading it, and headings that fold.
Folding is off for the first two sections, because the north star and the work
to get a version to the office are the two he opens the page to see.

Standard library only. It runs on the Mac, not on Windows, and it is not part
of the package.
"""
import html
import io
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
SOURCE = HERE / "docs" / "NOW.md"

# The two that are open when the page loads. Everything else folds away, so the
# page stays the length of a checklist however long the list underneath grows.
ALWAYS_OPEN = 2

# An item longer than this wraps on a narrow screen, and a wrapped item is how
# one lost its ending. This is a warning, not a refusal: refusing would mean
# this script could block a session from publishing, and the page being
# slightly wrong beats the page being absent.
LONG_ITEM = 96

PAGE = """<title>Roy R. Fisher: Checklist</title>
<style>
:root{--ground:#FAF8F4;--ink:#231F20;--muted:#6E6E73;--line:#E3E0D8;--brand:#8C0C04;--sunk:#F2EFE8}
*{box-sizing:border-box}html,body{margin:0}
body{background:var(--ground);color:var(--ink);font:16px/1.5 'Helvetica Neue',Helvetica,Arial,'Segoe UI',sans-serif;padding:0 0 70px}
.topline{height:4px;background:var(--brand)}
.wrap{max-width:660px;margin:0 auto;padding:0 22px}
details{border-top:1px solid var(--line)}
details:first-of-type{border-top:0}
summary{display:flex;align-items:baseline;gap:10px;list-style:none;cursor:pointer;
  padding:26px 0 8px;font-size:11.5px;letter-spacing:.11em;text-transform:uppercase;
  color:var(--muted);font-weight:700}
summary::-webkit-details-marker{display:none}
summary::after{content:"+";margin-left:auto;font-size:15px;letter-spacing:0;color:var(--line)}
details[open]>summary::after{content:"\\2013"}
details:first-of-type summary{color:var(--brand)}
.count{font-size:11px;letter-spacing:.04em;color:var(--line);font-weight:700}
.row{display:flex;gap:12px;align-items:flex-start;padding:11px 0;border-top:1px solid var(--line);cursor:pointer}
summary+.row{border-top:0}
input{margin:3px 0 0;width:17px;height:17px;flex:none;accent-color:var(--brand);cursor:pointer}
input:checked+span{color:#9C9890;text-decoration:line-through}
span.t{font-size:15.5px}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --ground:#1A1817;--ink:#F2EFE8;--muted:#9A948C;--line:#33302C;--brand:#E4675C;--sunk:#221F1D}}
:root[data-theme="dark"]{--ground:#1A1817;--ink:#F2EFE8;--muted:#9A948C;--line:#33302C;--brand:#E4675C;--sunk:#221F1D}
</style>
<div class="topline"></div>
<div class="wrap">%s</div>
<script>
(function(){
  var save=function(k,v){try{var s=JSON.parse(localStorage.getItem('rrf')||'{}');s[k]=v;
    localStorage.setItem('rrf',JSON.stringify(s));}catch(e){}};
  var held={};try{held=JSON.parse(localStorage.getItem('rrf')||'{}');}catch(e){}
  document.querySelectorAll('input').forEach(function(x){
    if(held[x.id]!==undefined)x.checked=held[x.id];
    x.addEventListener('change',function(){save(x.id,x.checked);tally();});
  });
  document.querySelectorAll('details').forEach(function(d){
    if(held[d.id]!==undefined)d.open=held[d.id];
    d.addEventListener('toggle',function(){save(d.id,d.open);});
  });
  function tally(){
    document.querySelectorAll('details').forEach(function(d){
      var b=d.querySelectorAll('input'),n=0;
      b.forEach(function(x){if(x.checked)n++;});
      var c=d.querySelector('.count');
      if(c)c.textContent=b.length?(n+' of '+b.length):'';
    });
  }
  tally();
}());
</script>
"""


def read(path=SOURCE):
    """Sections in file order: [(heading, [(done, text), ...]), ...].

    Anything that is not a heading and not a checkbox line is dropped. That is
    on purpose: `docs/NOW.md` carries a note at the top explaining the rules to
    whoever edits it next, and that note is for the editor, not for him.
    """
    sections = []
    for line in io.open(path, encoding="utf-8").read().splitlines():
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif line.startswith("- [") and sections:
            done = line.startswith("- [x]")
            sections[-1][1].append((done, line[6:].strip()))
    return sections


def complain(sections, out=sys.stderr):
    """Say what is wrong without refusing to build. Returns the complaints."""
    said = []
    for heading, items in sections:
        if not items:
            said.append("%s has no items" % heading)
        for _, text in items:
            if len(text) > LONG_ITEM:
                said.append("%d characters, will wrap: %s" % (len(text), text))
            if re.search(r"\b[A-Z]\d+\b", text):
                said.append("has a code in it, he does not read codes: %s" % text)
    for one in said:
        out.write("  ! %s\n" % one)
    return said


def build(sections):
    n = 0
    blocks = []
    for at, (heading, items) in enumerate(sections):
        rows = []
        for done, text in items:
            n += 1
            rows.append(
                '<label class="row"><input type="checkbox" id="c%d"%s>'
                '<span class="t">%s</span></label>'
                % (n, " checked" if done else "", html.escape(text)))
        blocks.append(
            '<details id="s%d"%s><summary>%s<span class="count"></span></summary>%s</details>'
            % (at, " open" if at < ALWAYS_OPEN else "",
               html.escape(heading), "".join(rows)))
    return PAGE % "".join(blocks)


def main(argv):
    where = pathlib.Path(argv[1]) if len(argv) > 1 else HERE / "build" / "now.html"
    sections = read()
    complain(sections)
    where.parent.mkdir(parents=True, exist_ok=True)
    io.open(where, "w", encoding="utf-8").write(build(sections))
    total = sum(len(i) for _, i in sections)
    done = sum(1 for _, i in sections for d, _ in i if d)
    print(json.dumps({"page": str(where), "sections": len(sections),
                      "items": total, "done": done}, indent=2))


if __name__ == "__main__":
    main(sys.argv)
