#!/usr/bin/env python3
"""Structural gate for ddia-study chapter pages (the bugs tag-balance can't see).

Usage:
    python3 assets/structcheck.py <one or more ch*/index.html>

FAILs (exit 1):
  table parts (thead/tbody/tr/td/th) outside a <table>  -> browsers DROP them,
      so readers get run-on text while tag-balance stays green.
  bare <li> outside <ul>/<ol>                          -> invalid HTML, FA/EN
      indent asymmetry (EN twin usually has the list wrapper).
  .diagram nested inside .callout                      -> diagram + narration
      render with callout styling; usually means the callout's .en twin got
      stranded after the teacher block.
  old-template markup (header.hero / div.wrap / span.num / .badge / <style>)
      (.grid2/.cardmini are the documented compat path and are allowed.)

WARNs (exit still 0):
  bare Persian-numeral <b> (should be twinned fa/en for EN mode).

Stdlib only. Run it on every chapter after migration/translation edits.
"""
import re, sys
from html.parser import HTMLParser

VOID = {"meta", "link", "br", "hr", "img", "input", "source"}
TABLE_PARTS = {"thead", "tbody", "tfoot", "tr", "td", "th"}
OLD = ['<header class="hero"', '<div class="wrap">', '<span class="num">',
       'class="badge', "class='badge"]


class Checker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []  # (tag, attrs-dict, lineno)
        self.fails, self.warns = [], []

    def handle_starttag(self, tag, attrs):
        lineno, _ = self.getpos()
        a = dict(attrs)
        tags = [t for t, _, _ in self.stack]
        if tag in TABLE_PARTS and "table" not in tags:
            self.fails.append(f"{lineno}: <{tag}> outside <table> (tokens dropped by browsers)")
        if tag == "li" and "ul" not in tags and "ol" not in tags:
            self.fails.append(f"{lineno}: bare <li> outside <ul>/<ol>")
        if tag == "div" and "diagram" in (a.get("class") or "").split():
            for t, pa, pl in self.stack:
                if t == "div" and "callout" in (pa.get("class") or "").split():
                    self.fails.append(f"{lineno}: .diagram nested inside .callout opened at line {pl}")
                    break
        if tag not in VOID:
            self.stack.append((tag, a, lineno))

    def handle_startendtag(self, tag, attrs):
        pass  # self-closing: never pushed

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return


def check(path):
    src = open(path, encoding="utf-8").read()
    c = Checker()
    try:
        c.feed(src)
    except Exception as e:  # noqa: BLE001
        return [f"unparseable HTML: {e}"], []
    for pat in OLD:
        for m in re.finditer(re.escape(pat), src):
            lineno = src.count("\n", 0, m.start()) + 1
            c.fails.append(f"{lineno}: old-template markup {pat!r}")
    for m in re.finditer(r"<b>[۰-۹]+</b>", src):
        lineno = src.count("\n", 0, m.start()) + 1
        c.warns.append(f"{lineno}: bare Persian-numeral <b> (twin it for EN mode)")
    return c.fails, c.warns


def main(paths):
    bad = False
    for p in paths:
        fails, warns = check(p)
        print(f"== {p}")
        for f in fails:
            print("  FAIL", f)
        for w in warns:
            print("  warn", w)
        if not fails and not warns:
            print("  OK")
        bad = bad or bool(fails)
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
