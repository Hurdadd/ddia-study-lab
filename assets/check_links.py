#!/usr/bin/env python3
"""Check internal file links and fragment anchors on the published pages.

Run: python3 assets/check_links.py
The public export is checked separately after build_site.py.
"""
import re, sys, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = [*ROOT.glob('ch*/**/*.html'), *ROOT.glob('glossary/**/*.html'),
         *ROOT.glob('studio/**/*.html'), *ROOT.glob('final-project/**/*.html'),
         ROOT / 'index.html', ROOT / 'exercise-audit.html']
PAGES = [p for p in PAGES if p.is_file() and 'public' not in p.parts]

_ids = {}
def ids(path):
    key = str(path)
    if key not in _ids:
        _ids[key] = set(re.findall(r'id="([^"]+)"', path.read_text(encoding='utf-8', errors='ignore')))
    return _ids[key]

broken, bad, total = [], [], 0
for page in PAGES:
    text = page.read_text(encoding='utf-8', errors='ignore')
    for value in re.findall(r'(?:href|src)="([^"]+)"', text):
        if not value or value.startswith(('http:', 'https:', 'mailto:', 'tel:', 'data:', 'javascript:', '//')):
            continue
        total += 1
        path, _, fragment = value.partition('#')
        path = urllib.parse.unquote(path.split('?')[0])
        target = page if not path else (page.parent / path).resolve()
        if path and target.is_dir():
            target = target / 'index.html'
        if path and not target.exists():
            broken.append((page.relative_to(ROOT), value))
            continue
        if fragment and target.suffix == '.html' and fragment not in ids(target):
            bad.append((page.relative_to(ROOT), value, target.relative_to(ROOT)))

for row in broken[:20]:
    print('BROKEN FILE', *row)
for row in bad[:20]:
    print('BROKEN ANCHOR', *row)
if broken or bad:
    print(f'FAIL: {len(broken)} broken files, {len(bad)} broken anchors in {len(PAGES)} pages')
    sys.exit(1)
print(f'PASS: {total} internal links in {len(PAGES)} pages; files and fragments resolve')
