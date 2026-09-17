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
  and nothing else. This file must never add a word. The two it does put on
  the page, `Done` and `done`, are the name of the section it generates and
  the count on the line that pulls a heading's own done items up, and both
  words are written in `docs/NOW.md` where the arrangement is explained.

**`Done` is generated, and that is the point.** There is no `Done` heading in
`docs/NOW.md`. Every item stays under the heading it belongs to, ticked or
not, and this file gathers the ticked ones into a section at the end. A person
had to remember to move an item when they ticked it and nobody is reminded of
that rule, and the file is the only place that knows where a done item came
from. Generating it means neither fact can be forgotten or lost. Spenser asked
for it on 2026-09-16.

A ticked item is on the page twice: once under its own heading, out of view,
and once in `Done`. The line at the end of each heading swaps which of the two
you can see, so nothing is open in two places at once.

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
# slightly wrong beats the page being absent. The star is not counted: it is
# laid out beside the words, not inside them.
LONG_ITEM = 96

# What separates an item from the north-star line it serves. A middle dot,
# because it appears in no item and a person editing `docs/NOW.md` can see it.
MARK = " · "

# Said out loud rather than left blank, so an item nobody has thought about
# cannot be mistaken for one that was thought about and serves no star.
NO_STAR = "No star"

# The five, in the order they appear in the first section of `docs/NOW.md`.
STARS = ["Star %d" % n for n in range(1, 6)]

# The section this file makes. It is not a heading in `docs/NOW.md` and a test
# checks that it never becomes one again.
DONE = "Done"

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
span.t{font-size:15.5px;flex:1}
.star{flex:none;align-self:flex-start;margin-top:3px;font-size:10.5px;font-weight:700;
  letter-spacing:.06em;text-transform:uppercase;white-space:nowrap;color:var(--brand);
  border:1px solid var(--brand);border-radius:2px;padding:1px 5px;opacity:.85}
.star.none{color:var(--line);border-color:var(--line);opacity:1}
input:checked~.star{color:var(--line);border-color:var(--line)}
.row.away{display:none}
.pull{display:flex;align-items:baseline;cursor:pointer;-webkit-user-select:none;user-select:none;
  padding:13px 0 3px;font-size:11px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--muted);font-weight:700;border-top:1px solid var(--line)}
.pull::after{content:"+";margin-left:auto;font-size:15px;letter-spacing:0;color:var(--line)}
.pull.on::after{content:"\\2013"}
.pull:hover{color:var(--brand)}
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
    var k=x.getAttribute('data-k');
    if(held[k]!==undefined)x.checked=held[k];
    x.addEventListener('change',function(){
      save(k,x.checked);
      document.querySelectorAll('[data-k="'+k+'"]').forEach(function(y){y.checked=x.checked;});
      tally();
    });
  });
  document.querySelectorAll('details').forEach(function(d){
    if(held[d.id]!==undefined)d.open=held[d.id];
    d.addEventListener('toggle',function(){save(d.id,d.open);});
  });
  document.querySelectorAll('.pull').forEach(function(p){
    p.addEventListener('click',function(){
      var at=p.getAttribute('data-for'),up=!p.classList.contains('on');
      p.classList.toggle('on',up);
      document.querySelectorAll('.row[data-home="'+at+'"]').forEach(function(r){
        r.classList.toggle('away',!up);});
      document.querySelectorAll('.row[data-from="'+at+'"]').forEach(function(r){
        r.classList.toggle('away',up);});
      tally();
    });
  });
  function tally(){
    document.querySelectorAll('details').forEach(function(d){
      var seen=0,n=0;
      d.querySelectorAll('.row').forEach(function(r){
        if(r.classList.contains('away'))return;
        var x=r.querySelector('input');
        if(!x)return;
        seen++;if(x.checked)n++;});
      var c=d.querySelector('.count');
      if(c)c.textContent=seen?(n+' of '+seen):'';
    });
  }
  tally();
}());
</script>
"""


def read(path=SOURCE):
    """Sections in file order: [(heading, [(done, text, star), ...]), ...].

    Anything that is not a heading and not a checkbox line is dropped. That is
    on purpose: `docs/NOW.md` carries a note at the top explaining the rules to
    whoever edits it next, and that note is for the editor, not for him.

    An item may end ` %s Star 3`, naming which of the five north-star lines it
    serves, or ` %s %s` where it serves none. He asked on 2026-09-16 for the
    star to be put into everything, and the honest half of that is the items
    where the answer is nothing: the star is about the app behaving like an
    app, and most of the backlog does not touch it.
    """ % (MARK, MARK, NO_STAR)
    sections = []
    for line in io.open(path, encoding="utf-8").read().splitlines():
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif line.startswith("- [") and sections:
            done = line.startswith("- [x]")
            text, _, star = line[6:].strip().partition(MARK)
            sections[-1][1].append((done, text.strip(), star.strip()))
    return sections


def complain(sections, out=sys.stderr):
    """Say what is wrong without refusing to build. Returns the complaints."""
    said = []
    seen = {}
    for at, (heading, items) in enumerate(sections):
        if not items:
            said.append("%s has no items" % heading)
        if heading == DONE:
            said.append("%s is generated, it is not a heading in the file" % DONE)
        states = [d for d, _, _ in items]
        if states != sorted(states):
            said.append("a done item sits above an open one under %s" % heading)
        for _, text, star in items:
            if len(text) > LONG_ITEM:
                said.append("%d characters, will wrap: %s" % (len(text), text))
            if re.search(r"\b[A-Z]\d+\b", text):
                said.append("has a code in it, he does not read codes: %s" % text)
            if at and not star:
                said.append("no star said either way: %s" % text)
            if star and star != NO_STAR and star not in STARS:
                said.append("%s is not one of the five: %s" % (star, text))
            # Crossover. He asked for it by name on 2026-09-16, and the same
            # work under two headings is how an item gets done twice or argued
            # about twice. Compared on the words that carry meaning.
            key = frozenset(w for w in re.findall(r"[a-z]{4,}", text.lower())
                            if w not in ("that", "this", "with", "from", "must",
                                         "have", "they", "them", "then", "than",
                                         "what", "when", "into", "does", "every"))
            for before, where in seen.items():
                if key and len(key & before) >= max(3, len(key) * 2 // 3):
                    said.append("crossover with %s: %s" % (where, text))
            seen[key] = heading
    for one in said:
        out.write("  ! %s\n" % one)
    return said


def build(sections):
    """The page. The last section is made here, not read from the file.

    A ticked item is written twice: once under its own heading, out of view,
    and once in the generated section at the end. The line at the end of the
    heading swaps which of the two is shown, so the same item is never open in
    two places at once. Both copies carry the same key, so ticking either one
    ticks the other and the page holds one answer rather than two.
    """
    n = 0
    blocks = []
    finished = []
    for at, (heading, items) in enumerate(sections):
        rows = []
        mine = 0
        for done, text, star in items:
            n += 1
            chip = ""
            if star:
                chip = '<span class="star%s">%s</span>' % (
                    " none" if star == NO_STAR else "", html.escape(star))
            body = ('<input type="checkbox" data-k="c%d"%s>'
                    '<span class="t">%s</span>%s'
                    % (n, " checked" if done else "", html.escape(text), chip))
            if not done:
                rows.append('<label class="row">%s</label>' % body)
                continue
            mine += 1
            rows.append('<label class="row away" data-home="%d">%s</label>' % (at, body))
            finished.append('<label class="row" data-from="%d">%s</label>' % (at, body))
        if mine:
            # A line, not a button, saying how many of the finished items at
            # the end of the page belong to this heading. Clicking it brings
            # them up here, still ticked, and clicking it again sends them back.
            rows.append('<div class="pull" data-for="%d">%d done</div>' % (at, mine))
        blocks.append(
            '<details id="s%d"%s><summary>%s<span class="count"></span></summary>%s</details>'
            % (at, " open" if at < ALWAYS_OPEN else "",
               html.escape(heading), "".join(rows)))
    if finished:
        blocks.append(
            '<details id="sdone"><summary>%s<span class="count"></span></summary>%s</details>'
            % (html.escape(DONE), "".join(finished)))
    return PAGE % "".join(blocks)


def main(argv):
    where = pathlib.Path(argv[1]) if len(argv) > 1 else HERE / "build" / "now.html"
    sections = read()
    complain(sections)
    where.parent.mkdir(parents=True, exist_ok=True)
    io.open(where, "w", encoding="utf-8").write(build(sections))
    total = sum(len(i) for _, i in sections)
    done = sum(1 for _, i in sections for d, _, _ in i if d)
    # What the star actually covers. Printed every build because it is the
    # number that says whether the five sentences describe the project or only
    # the part of it he has been fighting.
    served = sum(1 for _, i in sections for _, _, s in i if s in STARS)
    print(json.dumps({"page": str(where), "sections": len(sections),
                      "items": total, "done": done,
                      "serving a star": served}, indent=2))


if __name__ == "__main__":
    main(sys.argv)
