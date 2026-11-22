#!/usr/bin/env python3
"""Check the inline glossary end to end.

1. assets/glossary.json validates and the committed artefacts are in step.
2. Every term has a card on the generated page and a row in the hover data.
3. Every page that mentions a term loads the stylesheet and the scripts.

Run: python3 assets/check_glossary.py
"""
from pathlib import Path
import json, re, subprocess, sys

ROOT = Path(__file__).resolve().parent.parent
TERMS = ROOT / 'assets' / 'glossary.json'
PAGE = ROOT / 'glossary' / 'index.html'
JS = ROOT / 'assets' / 'glossary-data.js'

problems = []

# 1. generator agreement
proc = subprocess.run([sys.executable, str(ROOT / 'assets' / 'build_glossary.py'), '--check'],
                      capture_output=True, text=True)
if proc.returncode != 0:
    problems.append('build_glossary.py --check failed: ' + (proc.stdout + proc.stderr).strip()[:400])

doc = json.loads(TERMS.read_text(encoding='utf-8'))
terms = doc['terms']
ids = [t['id'] for t in terms]

# 2. page and data coverage
page = PAGE.read_text(encoding='utf-8')
data = JS.read_text(encoding='utf-8')
for tid in ids:
    if 'id="%s"' % tid not in page:
        problems.append('page is missing card #%s' % tid)
    if '"%s":{' % tid not in data:
        problems.append('hover data is missing #%s' % tid)
for need in ('glossary.css', 'glossary-data.js', 'glossary.js'):
    if need not in page:
        problems.append('page does not load %s' % need)

# every href the page links to must resolve inside the repo
for href in re.findall(r'href="(\.\./[^"#?]+)"', page):
    target = (PAGE.parent / href).resolve()
    if not target.exists():
        problems.append('broken link on the glossary page: %s' % href)

# 3. pages that use the glossary must load its assets, in the right relative form
wired = 0
for path in sorted(ROOT.glob('ch*/index.html')):
    s = path.read_text(encoding='utf-8')
    if '../assets/glossary.css' not in s or '../assets/glossary.js' not in s:
        problems.append('%s does not load the glossary assets' % path.relative_to(ROOT))
    else:
        wired += 1
root = (ROOT / 'index.html').read_text(encoding='utf-8')
if 'assets/glossary.js' not in root:
    problems.append('index.html does not load the glossary assets')

# 4. the data file must not claim terms the page does not have
declared = set(re.findall(r'"([a-z0-9-]+)":\{"term"', data))
for tid in sorted(declared - set(ids)):
    problems.append('hover data declares an unknown term: %s' % tid)

if problems:
    for p in problems:
        print('FAIL: ' + p)
    sys.exit(1)

print('PASS: %d terms across %d chapters; %d chapter pages wired; page, hover data and JSON in step'
      % (len(terms), len({t['chapter'] for t in terms}), wired))
