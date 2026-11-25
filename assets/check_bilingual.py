#!/usr/bin/env python3
"""Bilingual parity check for one chapter page.

The page keeps parallel <div class="fa"> / <div class="en"> blocks. This script
compares the *prose* (technical-example boxes are excluded, because they are a
separate component), reports pairs whose length drifts apart, blocks that lost
their counterpart, and duplicated example ids.

Usage: python3 assets/check_bilingual.py ch12-stream-processing/index.html
Exit code 1 when something needs attention.
"""
import re
import sys
import html


def words(s: str) -> int:
    clean = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return len(clean.split())


def strip_examples(s: str) -> str:
    return re.sub(r'<div class="technical-example.*?</div>', " ", s, flags=re.S)


def main(path: str) -> int:
    src = open(path, encoding="utf-8").read()
    problems = []
    seq = [(m.start(), m.group(1)) for m in re.finditer(r'<div class="(fa|en)">', src)]
    pairs = 0
    for idx, (pos, lang) in enumerate(seq):
        if lang != "fa":
            continue
        nxt = seq[idx + 1] if idx + 1 < len(seq) else None
        if not nxt or nxt[1] != "en":
            problems.append(f"unpaired fa block at char {pos}")
            continue
        fa = strip_examples(src[pos:src.find("</div>", pos)])
        en = src[nxt[0]:src.find("</div>", nxt[0] + 10)]
        wf, we = words(fa), words(en)
        pairs += 1
        if not we or not wf:
            problems.append(f"empty pair at char {pos} (fa={wf}, en={we})")
            continue
        ratio = wf / we
        if ratio < 0.6 or ratio > 1.6:
            problems.append(f"prose drift fa={wf} en={we} (x{ratio:.2f}) at char {pos}")

    ids = re.findall(r'id="(example-ch12-\d+)"', src)
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        problems.append(f"duplicate example ids: {sorted(dupes)}")

    print(f"{path}: {pairs} pairs, {len(ids)} example ids, {len(problems)} issues")
    for p in problems:
        print("  -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "ch12-stream-processing/index.html"
    sys.exit(main(target))
