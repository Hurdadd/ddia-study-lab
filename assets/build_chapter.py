#!/usr/bin/env python3
"""Render a chapter page from content/chXX/template.html + content.json.

Placeholders have the form {{fa:b001}} / {{en:b001}}. Each block must exist in
every required language; the build fails otherwise (use --allow-missing to see
what is missing without writing output).

Extra languages (vi, zh, ...) are appended after the English block for the same
id, so adding a translation never touches the template.

Usage: python3 assets/build_chapter.py ch12 [--check] [--allow-missing]
"""
import json
import os
import re
import sys

LANGS = ("fa", "en")
EXTRA = ("vi", "zh")


def main(chapter: str, check: bool, allow_missing: bool) -> int:
    root = os.path.join("content", chapter)
    template = open(os.path.join(root, "template.html"), encoding="utf-8").read()
    data = json.load(open(os.path.join(root, "content.json"), encoding="utf-8"))["blocks"]

    missing = [(pid, lang) for pid, rec in data.items()
               for lang in LANGS if not rec.get(lang)]
    if missing:
        print("missing translations:")
        for pid, lang in missing:
            print("  -", pid, lang)
        if not allow_missing:
            return 1

    def render(match: "re.Match") -> str:
        lang, pid = match.group(1), match.group(2)
        rec = data.get(pid)
        if not rec:
            raise SystemExit(f"unknown block {pid}")
        html = rec.get(lang)
        if not html:
            return ""
        out = html
        if lang == "en":
            for post in rec.get("post") or []:
                out += ('\n<div %s><div class="fa">%s</div><div class="en">%s</div></div>'
                        % (post["attrs"], post["fa_inner"], post.get("en_inner") or ""))
            for extra in EXTRA:
                block = rec.get(extra)
                if block:
                    out += "\n" + block
        return out

    rendered = re.sub(r"\{\{(fa|en):(b\d+)\}\}", render, template)
    if check:
        print(f"{chapter}: {len(data)} blocks, template ok")
        return 0
    meta = json.load(open(os.path.join(root, "meta.json"), encoding="utf-8"))
    out_path = meta["output"]
    open(out_path, "w", encoding="utf-8").write(rendered)
    print(f"wrote {out_path} ({len(rendered)} bytes)")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    chapter = args[0] if args else "ch12"
    sys.exit(main(chapter, "--check" in flags, "--allow-missing" in flags))
