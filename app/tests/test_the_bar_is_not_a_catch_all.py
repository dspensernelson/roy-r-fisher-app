"""The widget's bottom bar holds four things, and a fifth needs a trade.

Spenser, 2026-09-18: *"We need to be careful with this box because I think
it's becoming a catch-all."* The rule is in HOW-WE-WORK.md: nothing new goes
into the bar unless something comes out or goes elsewhere.

This test is the reminder. It lists what the bar draws today. Adding a thing
to the bar fails it, on purpose, and the fix is not to add the thing here:
it is to take something out of the bar, or put the new thing somewhere else,
and then update the list in HOW-WE-WORK.md and here together.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCREEN = ROOT / "app" / "web" / "src" / "screens" / "PhotosScreen.jsx"
RULES = ROOT / "HOW-WE-WORK.md"

# What the bar holds on 2026-09-18, by the class each is drawn with.
TODAY = {"pill", "clear", "bar-back", "money"}


def the_bar() -> str:
    src = SCREEN.read_text()
    start = src.index('<div className="barline">')
    depth, i = 0, start
    for m in re.finditer(r"<(/?)div\b[^>]*?(/?)>", src[start:]):
        if m.group(2):
            continue
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return src[start:start + m.end()]
    raise AssertionError("the bar's closing tag was not found")


def test_the_bar_holds_what_the_rule_lists_and_nothing_more():
    bar = re.sub(r"\{/\*.*?\*/\}", "", the_bar(), flags=re.S)
    found = set()
    for cls in re.findall(r'className=\{?[`"]([^`"]+)[`"]', bar):
        first = re.sub(r"\$\{.*", "", cls).split()
        if first and first[0] != "barline":
            found.add(first[0])
    assert found == TODAY, (
        "the bar now holds %s. Spenser, 2026-09-18: nothing new goes into the "
        "bar unless something comes out or goes elsewhere. See HOW-WE-WORK.md."
        % sorted(found))


def test_the_rule_is_written_down_with_the_list():
    text = RULES.read_text()
    assert "catch-all" in text
    for words in ("reviewed", "Clear captions", "Restore cleared captions", "money"):
        assert words in text, words
