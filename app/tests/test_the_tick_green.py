"""The tick green reads as small text on its own pale tint.

Spenser, 2026-09-18, from 0.7.6.3: the tick green goes a shade darker, enough
to read as small text on its pale background. The done pill in the widget's
bar is 11.5px words in `--tick` on a 7 per cent tint of `--tick`, laid on the
bar's sunk paper. The floor for small text is 4.5 to 1, and sitting on the
floor is not passing it, so this asks for a little more.

One token, so every use follows it: the tint and the edge are mixed from
`--tick` rather than written out, which is how the old tint came to be a
copy of a colour that no longer exists.
"""
import re
from pathlib import Path

CSS = (Path(__file__).resolve().parents[1] / "web" / "src" / "brand.css").read_text()
BARE = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)


def token(name: str) -> str:
    return re.search(r"--%s:\s*(#[0-9A-Fa-f]{6})" % name, BARE).group(1)


def rgb(hex_: str):
    return tuple(int(hex_[i:i + 2], 16) for i in (1, 3, 5))


def luminance(c):
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def tint_strength() -> float:
    body = re.search(r"\.pill\.done\s*\{([^}]*)\}", BARE).group(1)
    m = re.search(r"background:\s*color-mix\(in srgb,\s*var\(--tick\)\s*([\d.]+)%", body)
    assert m, "the done pill's tint is not mixed from --tick"
    return float(m.group(1)) / 100


def test_the_tick_green_reads_on_its_tint():
    tick = rgb(token("tick"))
    sunk = rgb(token("paper-sunk"))
    a = tint_strength()
    under = tuple(round(a * t + (1 - a) * s) for t, s in zip(tick, sunk))
    got = contrast(tick, under)
    assert got >= 4.6, "the tick green is %.2f to 1 on its tint" % got


def test_the_done_pill_follows_the_one_token():
    body = re.search(r"\.pill\.done\s*\{([^}]*)\}", BARE).group(1)
    assert "color: var(--tick)" in body
    assert re.search(r"border:[^;]*color-mix\(in srgb,\s*var\(--tick\)", body)


def test_no_copy_of_the_old_green_is_left():
    assert "58, 143, 82" not in BARE and "3A8F52" not in BARE.upper()
