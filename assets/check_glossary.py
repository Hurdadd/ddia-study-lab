#!/usr/bin/env python3
"""Check the glossary end to end.

1. assets/glossary.json validates and every committed page matches the builder.
2. Every term has a full card on its chapter page and a row in the hover data.
3. The index lists every term exactly once and every link resolves.
4. Every figure has a caption and its own marker definition.
5. Every chapter page that marks terms loads the glossary stylesheet and scripts.
6. Every internal link with a #fragment on every glossary page lands on a real
   element, and each generated "also in" link goes to the chapter's own page.

Run: python3 assets/check_glossary.py
"""
from pathlib import Path
import json, re, subprocess, sys

ROOT = Path(__file__).resolve().parent.parent
TERMS = ROOT / 'assets' / 'glossary.json'
INDEX = ROOT / 'glossary' / 'index.html'
JS = ROOT / 'assets' / 'glossary-data.js'

PREVIEW = '--preview' in sys.argv
problems = []

# 1. generator agreement
proc = subprocess.run([sys.executable, str(ROOT / 'assets' / 'build_glossary.py'), '--check']
                      + (['--preview'] if PREVIEW else []),
                      capture_output=True, text=True)
if proc.returncode != 0:
    problems.append('build_glossary.py --check failed: ' + (proc.stdout + proc.stderr).strip()[:800])

doc = json.loads(TERMS.read_text(encoding='utf-8'))
terms = doc['terms']
ids = [t['id'] for t in terms]

index_page = INDEX.read_text(encoding='utf-8')
data = JS.read_text(encoding='utf-8')

pages = {}
for t in terms:
    path = INDEX.parent / ('ch%d' % t['chapter']) / 'index.html'
    if not path.exists():
        problems.append('missing chapter page %s' % path.relative_to(ROOT))
        pages[t['chapter']] = ''
    else:
        pages[t['chapter']] = path.read_text(encoding='utf-8')

# 2. a full card per term, on the right page
for t in terms:
    tid = t['id']
    body = pages.get(t['chapter'], '')
    if 'id="%s"' % tid not in body:
        problems.append('page for chapter %d is missing card #%s' % (t['chapter'], tid))
        continue
    card = re.search(r'<article class="gl-card" id="%s".*?</article>' % re.escape(tid), body, re.S)
    if not card:
        continue
    html = card.group(0)
    for need, label in (('<div class="gl-block daily">', 'everyday example'),
                        ('<div class="gl-block tech">', 'technical block')):
        if need not in html:
            problems.append('#%s has no %s' % (tid, label))
    has_fig = '<figure class="gl-fig"' in html
    if t.get('figure') and not has_fig:
        problems.append('#%s declares a figure but renders none' % tid)
    if not t.get('figure') and has_fig:
        problems.append('#%s renders a figure it does not declare' % tid)
    if '"%s":{' % tid not in data:
        problems.append('hover data is missing #%s' % tid)

# 3. the index lists every term once, and its links point at a real page and anchor
rows = re.findall(r'<a class="gl-row" href="ch(\d+)/index\.html#([a-z0-9-]+)"', index_page)
seen = {}
for ch, tid in rows:
    if tid in seen:
        problems.append('index lists #%s twice' % tid)
    seen[tid] = int(ch)
for t in terms:
    if t['id'] not in seen:
        problems.append('index does not list #%s' % t['id'])
    elif seen[t['id']] != t['chapter']:
        problems.append('#%s is listed under chapter %d but lives in %d'
                        % (t['id'], seen[t['id']], t['chapter']))
for ch, tid in rows:
    body = pages.get(int(ch))
    if body is not None and 'id="%s"' % tid not in body:
        problems.append('index link #%s does not resolve on chapter page %s' % (tid, ch))

# 4. figures: captions and per-figure markers
total_fig = 0
for ch, body in pages.items():
    for need in ('glossary.css', 'glossary-data.js', 'glossary.js'):
        if '../assets/%s' % need not in body:
            problems.append('chapter page %d does not load %s' % (ch, need))
    used = set(re.findall(r'marker-end="url\(#(f\d+)\)"', body))
    defined = set(re.findall(r'<marker id="(f\d+)"', body))
    for m in sorted(used - defined):
        problems.append('chapter %d uses marker #%s but never defines it' % (ch, m))
    figs = len(re.findall(r'<figure class="gl-fig"', body))
    total_fig += figs
    if figs != len(re.findall(r'<figcaption>', body)):
        problems.append('chapter %d: %d figures but %d captions'
                        % (ch, figs, len(re.findall(r'<figcaption>', body))))
declared_fig = sum(1 for t in terms if t.get('figure'))
if total_fig != declared_fig:
    problems.append('%d figures rendered for %d declared' % (total_fig, declared_fig))

# 5. links out of the glossary pages resolve inside the repo
check_paths = [(INDEX, index_page)]
for ch in pages:
    check_paths.append((INDEX.parent / ('ch%d' % ch) / 'index.html', pages[ch]))
for path, body in check_paths:
    for href in re.findall(r'href="((?:\.\./)[^"#?]+)"', body):
        target = (path.parent / href).resolve()
        # a preview build has no page for a chapter whose terms are not written yet
        if PREVIEW and re.search(r'(?:^|/)ch\d+/index\.html$', href) and not target.exists():
            continue
        if not target.exists():
            problems.append('broken link on %s: %s' % (path.relative_to(ROOT), href))

# 6. every internal fragment link lands on a file that defines the id, and the
#    generated "also in" links point at the chapter folders (not the glossary page)
def fragment_target(path, href):
    """(file, fragment) for an internal href carrying a #fragment, else None."""
    if href.startswith(('http://', 'https://', '//', 'mailto:', 'javascript:',
                        'data:', 'tel:')) or '#' not in href:
        return None
    target, frag = href.split('#', 1)
    target = target.split('?', 1)[0]
    if not target:
        return path, frag
    if target.startswith('/'):
        return (ROOT / target.lstrip('/')).resolve(), frag
    return (path.parent / target).resolve(), frag


frag_links = 0
for path in sorted(INDEX.parent.rglob('*.html')):
    body = path.read_text(encoding='utf-8')
    for href in re.findall(r'href="([^"]+)"', body):
        got = fragment_target(path, href)
        if not got:
            continue
        frag_links += 1
        target, frag = got
        if not frag:
            problems.append('%s: link %s has an empty fragment'
                            % (path.relative_to(ROOT), href))
        elif not target.is_file():
            try:
                shown = target.relative_to(ROOT)
            except ValueError:
                shown = target
            problems.append('%s: link %s has no target file %s'
                            % (path.relative_to(ROOT), href, shown))
        elif 'id="%s"' % frag not in target.read_text(encoding='utf-8'):
            problems.append('%s: link %s points at #%s, which the target does not define'
                            % (path.relative_to(ROOT), href, frag))

# the "also in" badge must link to each extra chapter's own page, with a live anchor
chapter_dirs = {}
for p in sorted(ROOT.glob('ch*')):
    m = re.match(r'ch(\d+)-', p.name)
    if m and p.is_dir():
        chapter_dirs[int(m.group(1))] = p.name

also_links = 0
for t in terms:
    extras = [c for c in (t.get('chapters') or []) if c != t['chapter']]
    body = pages.get(t['chapter'], '')
    at = body.find('<article class="gl-card" id="%s"' % t['id'])
    if at < 0:
        continue
    end = body.find('</article>', at)
    card_html = body[at:end if end > at else len(body)]
    mark = card_html.find('<span class="gl-alsoseen">')
    span = card_html[mark:card_html.find('</div>', mark)] if mark >= 0 else ''
    links = re.findall(r'href="([^"]+)"', span)
    if len(links) != len(extras):
        problems.append('#%s has %d also-in link(s) for %d extra chapter(s)'
                        % (t['id'], len(links), len(extras)))
        continue
    for chapter, href in zip(extras, links):
        folder = chapter_dirs.get(chapter)
        if not folder:
            problems.append('#%s is also in chapter %d, which has no ch* folder'
                            % (t['id'], chapter))
            continue
        want = '../../%s/index.html' % folder
        if not href.startswith(want):
            problems.append('#%s also-in link %s does not point at %s'
                            % (t['id'], href, want))
            continue
        also_links += 1
        frag = href[len(want):]
        page = (ROOT / folder / 'index.html').read_text(encoding='utf-8')
        if frag and not (frag.startswith('#') and 'id="%s"' % frag[1:] in page):
            problems.append('#%s also-in link %s names no section on %s'
                            % (t['id'], href, folder))

# 7. the pages that mark terms must load the glossary, in the right relative form
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

# 8. the homepage advertises a count; it must be the real one
m = None if PREVIEW else re.search(r'<section class="gloss-band".*?</section>', root, re.S)
if not m and not PREVIEW:
    problems.append('index.html lost the glossary band')
elif m:
    fa = re.search(r'<span class="fa">([۰-۹]+) واژه', m.group(0))
    en = re.search(r'<span class="en">(\d+) terms', m.group(0))
    want = len(terms)
    if en and int(en.group(1)) != want:
        problems.append('homepage says %s terms, glossary has %d' % (en.group(1), want))
    if fa:
        fa_n = int(fa.group(1).translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')))
        if fa_n != want:
            problems.append('homepage says %d terms in Persian, glossary has %d' % (fa_n, want))

# 9. the data file must not claim terms that have no page
declared = set(re.findall(r'"([a-z0-9-]+)":\{"term"', data))
for tid in sorted(declared - set(ids)):
    problems.append('hover data declares an unknown term: %s' % tid)

if problems:
    for p in problems:
        print('FAIL: ' + p)
    sys.exit(1)

print('PASS: %d terms across %d chapter pages, %d figures; %d chapter pages wired; '
      '%d fragment links and %d also-in links resolve; '
      'index, pages, hover data and JSON in step'
      % (len(terms), len(pages), total_fig, wired, frag_links, also_links))
