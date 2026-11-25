#!/usr/bin/env python3
"""Report fa/en length drift per content block.

Reads content/chXX/content.json (not the rendered page), so grouped layouts
cannot confuse pairing. Exits 0; this is a report, the build gate is
build_chapter.py --check.
"""
import json
import os
import re
import sys
import html


def words(s: str) -> int:
    if not s:
        return 0
    return len(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def main(chapter: str) -> int:
    root = os.path.join("content", chapter)
    data = json.load(open(os.path.join(root, "content.json"), encoding="utf-8"))["blocks"]
    rows = []
    for pid, rec in data.items():
        wf, we = words(rec.get("fa")), words(rec.get("en"))
        if not wf or not we:
            rows.append((999, pid, rec.get("section"), wf, we))
            continue
        rows.append((max(wf / we, we / wf), pid, rec.get("section"), wf, we))
    rows.sort(reverse=True)
    flagged = [r for r in rows if r[0] > 1.6]
    print(f"{chapter}: {len(data)} blocks, {len(flagged)} with drift > 1.6x")
    for ratio, pid, sec, wf, we in flagged[:20]:
        print(f"  {pid} {sec}  fa={wf} en={we}  x{ratio:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "ch12"))
