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

**The north star is five headings, since 2026-09-17.** Spenser asked for the
starred items to be pulled together, because they are the important ones. Each
of his five sentences is a heading, the first five in `docs/NOW.md`, and an
item naming `Star N` sits under the Nth. The suffix stays in the file, because
it is how an item finds its heading. The page no longer draws it beside the
words: the heading above already says it, and a badge repeating that on every
row is ten words where three will do. `complain` says when an item sits under
the wrong star.

**Notes, asked for on 2026-09-16.** Every row carries a small control at its
end, where the star used to be drawn. A note is keyed on the item's own words,
not on where the item sits, so it follows the item when the list is reordered
or the item moves to another heading. See `note_key`. He clicks it, types a note about that item, and it is read
back out of the store with a tool call, so he never copies anything. The note
goes to the artifact's own database when the page is published and to the
browser when it is opened as a file, which is what he does on his Mac. It is
never both at once, and the box says which. The control is furniture: it adds
nothing to an item's words, its star, its tick or its heading. The only two
lines it ever says are `KEPT_HERE` and `NOT_KEPT` below, and they are the one
exception to "nothing is invented here".

**What it adds that the old inline version did not:** a count on every heading,
so the shape of the work is visible without reading it, and headings that fold.
The first six are open when the page loads: the five stars, and what needs his
decision. The rest fold away.

Standard library only. It runs on the Mac, not on Windows, and it is not part
of the package.
"""
import hashlib
import html
import io
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
SOURCE = HERE / "docs" / "NOW.md"

# The headings open when the page loads: the five stars and What needs you.
# Everything else folds away, so the page stays the length of a checklist
# however long the list underneath grows. Two until 2026-09-17, when the one
# north star heading became five.
ALWAYS_OPEN = 6

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

# The five, in the order of the first five headings of `docs/NOW.md`. An item
# naming one of these belongs under the heading at that same position.
STARS = ["Star %d" % n for n in range(1, 6)]

# The section this file makes. It is not a heading in `docs/NOW.md` and a test
# checks that it never becomes one again.
DONE = "Done"

# The only two things the notes control ever says, and the one exception to
# "the page says nothing `docs/NOW.md` does not". They are furniture beside an
# item, never words inside one, and a test holds them to this list so a third
# cannot arrive quietly.
#
# Both had to be said. Published, a note goes to the artifact's own store and
# can be read back out of it. Opened as a file on his Mac, which is what he
# does, there is no store at all and the note stays in that browser. Saying so
# is the fifth north-star line: a note shown as kept when it is not is the app
# telling him something it does not know.
def note_key(text):
    """A note's own key: the item's exact words, not where the item sits.

    The tick's key counts down the page, so it moves the moment anything
    above it moves. A note keyed on that would follow the position and land
    on a stranger, and items move between headings several times a day.

    The words are what a note is about. They survive reordering, moving an
    item to another heading, ticking it, and changing the star it names,
    which is every one of the things that shifts around an item while the
    item stays the same thing. `docs/NOW.md` already forbids two items with
    the same words and a test holds that, so the words are a key.

    Rewording an item orphans its note. That is correct: better a note that
    is plainly about a line nobody can find than one silently attached to a
    different item. The note carries the item's whole line for that reason.

    The star is not part of it. It is written after the middle dot and is
    already stripped off by `read` before this sees the text.
    """
    return "n" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


KEPT_HERE = "This browser only"
NOT_KEPT = "Not saved"
FURNITURE = set(re.findall(r"[A-Za-z]{4,}", KEPT_HERE + " " + NOT_KEPT))

# The box he types a note into. One of them, moved under whichever row he
# opened, because a box per row is 127 boxes nobody asked for. Both lines
# start hidden: the page says nothing about the store until the store has
# answered.
BOX = ('<div class="box" id="box" hidden><textarea id="pad" rows="3"></textarea>'
       '<div class="foot"><span class="say bad" id="bad" hidden>%s</span>'
       '<span class="say" id="here" hidden>%s</span></div></div>'
       % (html.escape(NOT_KEPT), html.escape(KEPT_HERE)))

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
.count{font-size:11px;letter-spacing:.04em;color:var(--line);font-weight:700}
.north>summary{color:var(--brand)}
.row{display:flex;gap:12px;align-items:flex-start;padding:11px 0;border-top:1px solid var(--line);cursor:pointer}
summary+.row{border-top:0}
input{margin:3px 0 0;width:17px;height:17px;flex:none;accent-color:var(--brand);cursor:pointer}
input:checked+span{color:#9C9890;text-decoration:line-through}
span.t{font-size:15.5px;flex:1}
.row.away{display:none}
.pull{display:flex;align-items:baseline;cursor:pointer;-webkit-user-select:none;user-select:none;
  padding:13px 0 3px;font-size:11px;letter-spacing:.09em;text-transform:uppercase;
  color:var(--muted);font-weight:700;border-top:1px solid var(--line)}
.pull::after{content:"+";margin-left:auto;font-size:15px;letter-spacing:0;color:var(--line)}
.pull.on::after{content:"\\2013"}
.pull:hover{color:var(--brand)}
.note{flex:none;align-self:flex-start;margin-top:2px;padding:0 7px;border:0;background:none;
  font-family:inherit;font-size:14px;line-height:1.3;color:var(--line);cursor:pointer;
  -webkit-appearance:none}
.note:hover{color:var(--muted)}
.note.on{color:var(--brand)}
.box{margin:2px 0 14px 29px;border-left:2px solid var(--brand);padding-left:11px}
.box textarea{display:block;width:100%%;min-height:78px;resize:vertical;background:var(--sunk);
  color:var(--ink);border:1px solid var(--line);border-radius:3px;padding:8px 9px;
  font:15px/1.45 'Helvetica Neue',Helvetica,Arial,'Segoe UI',sans-serif}
.box textarea:focus{outline:none;border-color:var(--brand)}
.foot{display:flex;gap:12px;padding:5px 0 0;font-size:10.5px;letter-spacing:.07em;
  text-transform:uppercase;font-weight:700;color:var(--muted)}
.say{margin-left:auto}
.bad{color:var(--brand)}
[hidden]{display:none!important}
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
(function(){
  // The notes he leaves on an item. Spenser, 2026-09-16: "now there needs to
  // be a notes button to the left of the star. When i click it leave notes i
  // can hand to you". He hands nothing over: the note is read back out of the
  // store, so nothing is ever copied or pasted.
  //
  // Two stores and only ever one of them answering. Published, the artifact's
  // own database holds the notes. Opened as a file there is no database, so
  // the note is kept in this browser and the box says so. Never both at once:
  // one note with two homes is the fault this project keeps meeting.
  var box=document.getElementById('box'),pad=document.getElementById('pad'),
      here=document.getElementById('here'),bad=document.getElementById('bad');
  var mine={},store=null,asked=false,cur=null,was='',queue=Promise.resolve();
  function read(){try{return JSON.parse(localStorage.getItem('rrf-notes')||'{}');}
    catch(e){return {};}}
  function write(all){try{localStorage.setItem('rrf-notes',JSON.stringify(all));
    return true;}catch(e){return false;}}
  function mark(){document.querySelectorAll('.note').forEach(function(b){
    b.classList.toggle('on',!!mine[b.getAttribute('data-n')]);});}
  // Said only once the store has answered. Before that the page knows nothing
  // about where a note would go, so it claims nothing.
  function say(){here.hidden=!(asked&&!store);}
  var first=read();
  for(var key in first){if(first[key]&&first[key].text)mine[key]=first[key].text;}
  mark();
  // One write, when he has finished and the words have changed. A caption box
  // that wrote on every keystroke put one read across the office network per
  // letter Colleen typed, and that is a recorded fault.
  function keep(){
    if(!cur)return;
    var b=cur,k=b.getAttribute('data-n'),text=pad.value.trim();
    if(text===was)return;
    var before=mine[k],row=b.parentNode;
    was=text;
    if(text)mine[k]=text;else delete mine[k];
    mark();
    // The item's own line and where it sat go with the note. The key is the
    // words, so this is what finds an orphan when an item is reworded.
    var body={text:text,item:row.querySelector('.t').textContent,
      section:row.getAttribute('data-h'),star:row.getAttribute('data-s'),
      at:new Date().toISOString()};
    var lost=function(){
      if(before===undefined)delete mine[k];else mine[k]=before;
      was=before||'';mark();bad.hidden=false;};
    if(store){
      var ref=store.collection('notes').doc(k);
      queue=queue.then(function(){return text?ref.set(body):ref.delete();})
        .then(function(){bad.hidden=true;},lost);
      return;
    }
    var held=read();
    if(text)held[k]=body;else delete held[k];
    if(write(held))bad.hidden=true;else lost();
  }
  function shut(){if(!cur)return;keep();cur=null;box.hidden=true;}
  function show(b){
    if(cur===b){shut();return;}
    shut();
    cur=b;
    var row=b.parentNode;
    row.parentNode.insertBefore(box,row.nextSibling);
    was=mine[b.getAttribute('data-n')]||'';
    pad.value=was;bad.hidden=true;say();box.hidden=false;pad.focus();
    // The caret goes to the end of what is already there. Setting the
    // words leaves it at the start, so reopening a note put him in
    // front of his own sentence and Backspace did nothing.
    try{pad.setSelectionRange(was.length,was.length);}catch(e){}
  }
  document.querySelectorAll('.note').forEach(function(b){
    b.addEventListener('click',function(e){
      e.preventDefault();e.stopPropagation();show(b);});});
  pad.addEventListener('blur',keep);
  pad.addEventListener('keydown',function(e){if(e.key==='Escape')shut();});
  document.addEventListener('mousedown',function(e){
    if(!cur||box.contains(e.target))return;
    if(e.target.closest&&e.target.closest('.note'))return;
    shut();});
  window.addEventListener('pagehide',keep);
  // Asked for without the page waiting on it. It can take ten seconds and it
  // can answer after the page is built, so the page draws and the notes light
  // up when it answers.
  var got=null;
  try{if(window.claude&&window.claude.use)got=window.claude.use('db');}catch(e){}
  if(got&&got.then){got.then(function(db){
    asked=true;
    if(!db){say();return;}
    store=db;
    db.collection('notes').get().then(function(snap){
      var now={};
      snap.docs.forEach(function(d){var v=d.data()||{};if(v.text)now[d.id]=v.text;});
      mine=now;mark();say();},function(){say();});
  },function(){asked=true;say();});}else{asked=true;}
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
            if not star:
                said.append("no star said either way: %s" % text)
            if star and star != NO_STAR and star not in STARS:
                said.append("%s is not one of the five: %s" % (star, text))
            # The suffix is how an item finds its heading, so an item under
            # the wrong one is the file disagreeing with itself.
            if star in STARS and STARS.index(star) != at:
                said.append("%s belongs under heading %d, not %s: %s"
                            % (star, STARS.index(star) + 1, heading, text))
            if at < len(STARS) and star not in STARS:
                said.append("under a star heading without naming it: %s" % text)
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
            # The notes control, at the end of the row, where he asked for it
            # when the star was still drawn to its right. A glyph, not a word:
            # the page may not add one to an item, and a pencil beside the
            # words is understood without being explained. It is quiet until
            # the note exists, which is how he sees at a glance where he left
            # one. The star is not drawn: the heading above already says it.
            body = ('<input type="checkbox" data-k="c%d"%s>'
                    '<span class="t">%s</span>'
                    '<button type="button" class="note" data-n="%s">&#9998;&#xFE0E;</button>'
                    % (n, " checked" if done else "", html.escape(text),
                       note_key(text)))
            # A note says which heading and which star its item sat under, so
            # it still reads back as something rather than as a sentence about
            # nothing. The row is the only place that knows.
            where = ' data-h="%s" data-s="%s"' % (html.escape(heading),
                                                  html.escape(star))
            if not done:
                rows.append('<label class="row"%s>%s</label>' % (where, body))
                continue
            mine += 1
            rows.append('<label class="row away" data-home="%d"%s>%s</label>'
                        % (at, where, body))
            finished.append('<label class="row" data-from="%d"%s>%s</label>'
                            % (at, where, body))
        if mine:
            # A line, not a button, saying how many of the finished items at
            # the end of the page belong to this heading. Clicking it brings
            # them up here, still ticked, and clicking it again sends them back.
            rows.append('<div class="pull" data-for="%d">%d done</div>' % (at, mine))
        blocks.append(
            '<details id="s%d"%s%s><summary>%s<span class="count"></span></summary>%s</details>'
            % (at, ' class="north"' if at < len(STARS) else "",
               " open" if at < ALWAYS_OPEN else "",
               html.escape(heading), "".join(rows)))
    if finished:
        blocks.append(
            '<details id="sdone"><summary>%s<span class="count"></span></summary>%s</details>'
            % (html.escape(DONE), "".join(finished)))
    # One box for the whole page, moved under whichever row he opens.
    return PAGE % ("".join(blocks) + BOX)


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
