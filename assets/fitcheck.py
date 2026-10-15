#!/usr/bin/env python3
"""Fit-check for hand-built Tiimo-style SVG diagram pages (ddia-study).

Usage:
    python3 assets/fitcheck.py <one or more diagrams/*.html>

What it checks (FAIL = exit 1, must fix; WARN = advisory):
  FAIL  exactly one <svg> root with a parseable viewBox="0 0 W H"
  FAIL  svg root must scale: width="100%" (or no width attr), no fixed px width
  FAIL  every <text> must sit inside the viewBox (no clipped labels)
  FAIL  no two <text> bounding boxes may overlap (estimated w = len*size*0.6)
  FAIL  file:// safety: no remote <image> / remote resources (Google Fonts
        <link> is allowed but raises a WARN for offline use)
  WARN  page background should be a Tiimo cream (#f7f2e8 / #fffdf7 family)
  WARN  <text> smaller than 13px is likely illegible on phones
  WARN  missing <title> (accessibility)
  INFO  prints the suggested iframe height for the chapter embed:
        default 640px; taller diagrams get an explicit height.

Stdlib only. Geometry estimation is conservative on purpose.
"""
import re, sys
from html.parser import HTMLParser
from math import ceil

CREAMS = {"#f7f2e8", "#fffdf7", "#faf5ea", "#fbf6ec", "#f6f1e5"}
PHONE_MIN_PX = 13


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.svgs = []
        self.texts = []          # (x, y, size, anchor, string)
        self._cur = None
        self.title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "svg":
            self.svgs.append(a)
        elif tag == "text":
            try:
                x = float(a.get("x", "0").split()[0])
                y = float(a.get("y", "0").split()[0])
            except ValueError:
                x, y = 0.0, 0.0
            size = 16.0
            if "font-size" in a:
                m = re.match(r"([\d.]+)", a["font-size"])
                if m:
                    size = float(m.group(1))
            self._cur = [x, y, size, a.get("text-anchor", "start"), ""]
        elif tag == "title":
            self.title = True

    def handle_data(self, data):
        if self._cur is not None:
            self._cur[4] += data.strip() + " "

    def handle_endtag(self, tag):
        if tag == "text" and self._cur is not None:
            self.texts.append(tuple(self._cur))
            self._cur = None


def check(path):
    fails, warns, infos = [], [], []
    src = open(path, encoding="utf-8").read()

    c = Collector()
    try:
        c.feed(src)
    except Exception as e:  # noqa: BLE001
        return [f"unparseable HTML: {e}"], [], []

    if len(c.svgs) != 1:
        fails.append(f"expected exactly 1 <svg> root, found {len(c.svgs)}")
        return fails, warns, infos
    root = c.svgs[0]
    # NOTE: HTMLParser lowercases attribute names, so viewBox arrives as viewbox
    vb = re.match(r"\s*0\s+0\s+([\d.]+)\s+([\d.]+)\s*$", root.get("viewbox", root.get("viewBox", "")))
    if not vb:
        fails.append("svg root needs viewBox='0 0 W H'")
        return fails, warns, infos
    W, H = float(vb.group(1)), float(vb.group(2))
    if W <= 0 or H <= 0:
        fails.append("viewBox dimensions must be positive")

    w = (root.get("width") or "").strip()
    if w and w != "100%":
        fails.append(f"svg width must be 100% (fluid), got '{w}'")

    # file:// safety: remote images are fatal; font links only warn
    if re.search(r"<image[^>]+href\s*=\s*['\"]https?://", src):
        fails.append("remote <image> breaks file:// usage — download the asset")
    if re.search(r"https?://", src) and "fonts.googleapis" in src:
        warns.append("Google Fonts <link> needs network (offline falls back to system fonts)")
    elif re.search(r"https?://(?!fonts\.g)", src):
        warns.append("remote URL found — confirm the page works from file://")

    if not re.search(r"#[0-9a-fA-F]{6}", src) or not (CREAMS & set(re.findall(r"#[0-9a-fA-F]{6}", src))):
        warns.append("no Tiimo cream background detected (expect #f7f2e8 family)")

    if not c.title:
        warns.append("missing <title> (screen-reader accessibility)")

    for x, y, size, anchor, s in c.texts:
        s = s.strip()
        if not s:
            continue
        est_w = len(s) * size * 0.6
        x0 = {"start": x, "middle": x - est_w / 2, "end": x - est_w}.get(anchor, x)
        if x0 < -1 or x0 + est_w > W + 1 or y - size > H + 1 or y < -1:
            fails.append(f"text outside viewBox: '{s[:40]}' at ({x:g},{y:g})")
        if size < PHONE_MIN_PX:
            warns.append(f"tiny text ({size:g}px): '{s[:40]}' — may be illegible on phones")

    boxes = []
    for x, y, size, anchor, s in c.texts:
        s = s.strip()
        if not s:
            continue
        est_w = len(s) * size * 0.6
        x0 = {"start": x, "middle": x - est_w / 2, "end": x - est_w}.get(anchor, x)
        boxes.append((x0, y - size * 0.9, est_w, size * 1.1, s))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            ax, ay, aw, ah, sa = boxes[i]
            bx, by, bw, bh, sb = boxes[j]
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                fails.append(f"text overlap: '{sa[:30]}' x '{sb[:30]}'")

    ratio = H / W
    if ratio <= 0.62:
        infos.append("suggested iframe height: 640px (default)")
    else:
        h = min(1400, int(ceil(1050 * ratio / 10) * 10))
        infos.append(f"suggested iframe height: {h}px (tall diagram — set style= on the iframe)")
    return fails, warns, infos


def main(paths):
    bad = False
    for p in paths:
        fails, warns, infos = check(p)
        print(f"== {p}")
        for f in fails:
            print("  FAIL", f)
        for w in warns:
            print("  warn", w)
        for i in infos:
            print("  info", i)
        if not fails and not warns:
            print("  OK")
        bad = bad or bool(fails)
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
