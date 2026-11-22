#!/usr/bin/env python3
"""Generate the glossary page and its hover data from assets/glossary.json.

assets/glossary.json is the single source of truth. This script validates it and
writes two artefacts into the repository:

  glossary/index.html        the bilingual term page (analogy first, technical second)
  assets/glossary-data.js    window.DDIA_GLOSSARY, loaded by assets/glossary.js so a
                             chapter can preview a term without any fetch (file:// safe)

Run: python3 assets/build_glossary.py [--check]
--check writes nothing and fails when the committed artefacts are out of date.
"""
from html import escape
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'assets' / 'glossary.json'
PAGE = ROOT / 'glossary' / 'index.html'
JS = ROOT / 'assets' / 'glossary-data.js'
BASE = 'https://ddia-study-lab.vercel.app'

REQUIRED = ('id','term','chapter','chapter_ref','one_liner_fa','one_liner_en',
            'everyday_fa','everyday_en','technical_fa','technical_en')
ALIAS_OK = re.compile(r'^[A-Za-z][A-Za-z0-9 .+\-/]*[A-Za-z0-9]$')

def scene_dirs():
    """chapter number -> directory name, e.g. 7 -> 'ch7-sharding'."""
    out = {}
    for p in sorted(ROOT.glob('ch*')):
        m = re.match(r'ch(\d+)-', p.name)
        if m and p.is_dir():
            out[int(m.group(1))] = p.name
    return out

def first_section(term, chapter_ref):
    """Anchor of the first chapter section that mentions the term, or '' for the page top.

    Best effort by design: the chapters are authored HTML, so this recomputes on every
    build instead of freezing an offset that would rot as the prose changes.
    """
    path = ROOT / chapter_ref / 'index.html'
    if not path.exists():
        return ''
    text = path.read_text(encoding='utf-8')
    at = text.lower().find(term.lower())
    if at < 0:
        return ''
    anchor = ''
    for m in re.finditer(r'<section id="([^"]+)"', text):
        if m.start() > at:
            break
        anchor = m.group(1)
    return '#' + anchor if anchor else ''

def fail(msg):
    print('FAIL: ' + msg)
    sys.exit(1)

def validate(doc, chapters):
    terms = doc.get('terms')
    if not isinstance(terms, list) or not terms:
        fail('glossary.json needs a non-empty "terms" list')
    seen_id, seen_alias, problems = set(), {}, []
    for i, t in enumerate(terms):
        label = t.get('id') or '#%d' % i
        for key in REQUIRED:
            if not str(t.get(key, '')).strip():
                problems.append('%s: missing "%s"' % (label, key))
        tid = t.get('id', '')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', tid):
            problems.append('%s: id must be lowercase-with-dashes' % label)
        if tid in seen_id:
            problems.append('%s: duplicate id' % label)
        seen_id.add(tid)
        ch = t.get('chapter')
        if ch not in chapters:
            problems.append('%s: chapter %r has no ch* directory' % (label, ch))
        if t.get('chapter_ref') and t['chapter_ref'] not in chapters.values():
            problems.append('%s: chapter_ref %r is not a chapter directory' % (label, t['chapter_ref']))
        aliases = t.get('aliases') or [t.get('term', '')]
        for a in aliases:
            if not ALIAS_OK.match(a or ''):
                problems.append('%s: alias %r must start and end with a letter/digit' % (label, a))
            key = (a or '').lower()
            if key in seen_alias:
                problems.append('%s: alias %r already used by "%s"' % (label, a, seen_alias[key]))
            seen_alias[key] = tid
    for t in terms:
        for rel in t.get('related') or []:
            if rel not in seen_id:
                problems.append('%s: related "%s" is not a term id' % (t.get('id'), rel))
    if problems:
        for p in problems:
            print('  - ' + p)
        fail('%d glossary problem(s)' % len(problems))
    return terms

def bi(fa, en, sep=''):
    """Bilingual text: the site shows exactly one of these two spans."""
    return ('<span class="fa">%s</span><span class="en">%s</span>'
            % (escape(fa), escape(en)))

def q(s):
    return escape(str(s), quote=True)

def chapter_label(n, chapters):
    return bi('فصل %s' % to_fa(n), 'Chapter %d' % n)

FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')
def to_fa(n):
    return str(n).translate(FA_DIGITS)

def build_data(terms, chapters):
    order = [t['id'] for t in terms]
    out = {}
    for t in terms:
        out[t['id']] = {
            'term': t['term'],
            'term_fa': t.get('term_fa', ''),
            'aliases': t.get('aliases') or [t['term']],
            'one_liner_fa': t['one_liner_fa'],
            'one_liner_en': t['one_liner_en'],
            'chapter': t['chapter'],
            'chapter_ref': t['chapter_ref'],
            'section': t.get('section', ''),
        }
    payload = {'maxPerTerm': 3, 'chapters': {str(k): v for k, v in sorted(chapters.items())},
               'order': order, 'terms': out}
    body = json.dumps(payload, ensure_ascii=False, indent=0, separators=(',', ':'))
    return ('/* Generated by assets/build_glossary.py from assets/glossary.json.\n'
            '   Do not edit by hand; run the builder instead. */\n'
            'window.DDIA_GLOSSARY = ' + body + ';\n')

def head(title_en, title_fa, desc):
    return (
'<!DOCTYPE html>\n'
'<html lang="en" dir="ltr" data-hue="lilac" data-title-fa="%s" data-title-en="%s">\n'
'<head>\n'
'<meta charset="utf-8">\n'
'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
'<title>%s</title>\n'
'<meta name="description" content="%s">\n'
'<link rel="canonical" href="%s/glossary/">\n'
'<meta property="og:type" content="article"><meta property="og:site_name" content="DDIA Study Lab">\n'
'<meta property="og:title" content="%s"><meta property="og:description" content="%s">\n'
'<meta property="og:url" content="%s/glossary/"><meta property="og:image" content="%s/assets/og-image.png">\n'
'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">\n'
'<meta property="og:locale" content="en_US"><meta property="og:locale:alternate" content="fa_IR">\n'
'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="%s">\n'
'<meta name="twitter:description" content="%s"><meta name="twitter:image" content="%s/assets/og-image.png">\n'
'<link rel="preconnect" href="https://fonts.googleapis.com">\n'
'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
'<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&family=Vazirmatn:wght@300;400;500;700;900&display=swap" rel="stylesheet">\n'
'<link rel="stylesheet" href="../assets/ddia.css">\n'
'<link rel="stylesheet" href="../assets/glossary.css">\n'
'</head>\n' % (q(title_fa), q(title_en), escape(title_en), q(desc),
               BASE, q(title_en), q(desc), BASE, BASE, q(title_en), q(desc), BASE))

def build_page(terms, chapters):
    title_en = 'DDIA Glossary: %d terms, everyday analogy first' % len(terms)
    title_fa = 'واژه‌نامهٔ DDIA: %s واژه با مثال روزمره و توضیح فنی' % to_fa(len(terms))
    desc = ('Every jargon term in the DDIA study guide, explained twice: a plain everyday '
            'analogy first, then the technical account. · واژه‌های تخصصی DDIA با مثال روزمره و بعد توضیح فنی.')

    parts = [head(title_en, title_fa, desc)]
    parts.append('''<body>

<header class="topbar">
  <a class="wordmark" href="../index.html">DDIA<em>&middot;</em><span class="fa">واژه‌ها</span><span class="en">TERMS</span></a>
  <nav class="topnav">
    <a href="../index.html"><span class="fa">نقشه راه</span><span class="en">Roadmap</span></a>
    <a href="../ch7-sharding/index.html"><span class="fa">فصل ۷</span><span class="en">Chapter 7</span></a>
    <a href="../final-project/index.html"><span class="fa">پروژهٔ نهایی</span><span class="en">Final project</span></a>
    <a href="index.html" aria-current="page"><span class="fa">واژه‌ها</span><span class="en">Terms</span></a>
  </nav>
  <button class="langbtn" data-lang-toggle><span class="fa">EN</span><span class="en">فارسی</span></button>
  <button class="iconbtn" data-theme-toggle aria-label="theme">
    <svg class="icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
    <svg class="icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
  </button>
</header>

<section class="doc-hero">
  <div class="blobs" aria-hidden="true"><i class="b1"></i><i class="b2"></i><i class="b3"></i></div>
  <p class="crumb"><a href="../index.html">''' + bi('نقشه راه', 'Roadmap') + '''</a>/ ''' + bi('واژه‌نامه', 'Glossary') + '''</p>
  <h1><span class="fa">هر واژه، دو بار</span><span class="en">Each term, twice</span></h1>
  <p class="lede">
    ''' + bi(
      'واژه‌های تخصصی این راهنما را اینجا جمع کرده‌ام. برای هر کدام اول یک مثال روزمره می‌خوانی، بعد همان چیز را دقیق و فنی توضیح می‌دهم، و آخرش تله‌ای را می‌گویم که بیشتر آدم‌ها در آن گیر می‌کنند. در فصل‌ها، واژه‌های خط‌چین‌دار همین‌جا وصل می‌شوند.',
      'Every jargon word in this guide lives here. Each entry starts with an everyday analogy, then explains the same idea precisely, and closes with the trap most people fall into. In the chapters, dotted words link straight back to these entries.') + '''
  </p>
  <p class="meta-row">
    <b>''' + str(len(terms)) + '''</b> ''' + bi('واژه', 'terms') + '''
    <span class="dot">&middot;</span> <b>14</b> ''' + bi('فصل', 'chapters') + '''
    <span class="dot">&middot;</span> ''' + bi('فارسی و انگلیسی', 'Persian & English') + '''
  </p>
</section>

<main class="gl-main">
''')

    parts.append('''  <div class="gl-tools" role="group" aria-label="Filter glossary">
    <input class="gl-search" id="gl-search" type="search" autocomplete="off"
           placeholder="Search terms…" data-ph-en="Search terms…" data-ph-fa="جست‌وجو در واژه‌ها…"
           aria-label="Search glossary terms">
''')
    parts.append('    <div class="gl-chips" role="group" aria-label="Filter by chapter">\n')
    parts.append('      <button class="gl-chip" data-gl-chapter="all" aria-pressed="true">'
                 + bi('همه', 'All') + '</button>\n')
    for ch in sorted({t['chapter'] for t in terms}):
        parts.append('      <button class="gl-chip" data-gl-chapter="%d" aria-pressed="false">%s</button>\n'
                     % (ch, bi(to_fa(ch), str(ch))))
    parts.append('    </div>\n')
    parts.append('    <span class="gl-count" id="gl-count" aria-live="polite">%d / %d</span>\n' % (len(terms), len(terms)))
    parts.append('  </div>\n\n  <div class="gl-grid" id="gl-grid" data-no-glossary>\n')

    by_id = {t['id']: t for t in terms}
    anchor = {t['id']: (t.get('section') or first_section((t.get('aliases') or [t['term']])[0], t['chapter_ref']))
              for t in terms}
    for t in terms:
        href = '../%s/index.html%s' % (t['chapter_ref'], anchor[t['id']])

        parts.append('    <article class="gl-card" id="%s" data-chapter="%d">\n'
                     % (q(t['id']), t['chapter']))
        parts.append('      <div class="gl-head">\n')
        parts.append('        <h2>%s</h2>\n' % escape(t['term']))
        if t.get('term_fa'):
            parts.append('        <span class="gl-alias">%s</span>\n' % escape(t['term_fa']))
        parts.append('        <a class="gl-chapter" href="%s">%s &middot; %s</a>\n'
                     % (q(href), chapter_label(t['chapter'], chapters), bi('دیدن در متن', 'see in context')))
        parts.append('      </div>\n')
        if t.get('hook_fa') or t.get('hook_en'):
            parts.append('      <p class="gl-hook">%s</p>\n'
                         % bi(t.get('hook_fa', ''), t.get('hook_en', '')))
        parts.append('      <div class="gl-block everyday">\n        <h3><span class="dot" aria-hidden="true"></span>%s</h3>\n        <p>%s</p>\n      </div>\n'
                     % (bi('مثال روزمره', 'Everyday example'), bi(t['everyday_fa'], t['everyday_en'])))
        parts.append('      <div class="gl-block tech">\n        <h3><span class="dot" aria-hidden="true"></span>%s</h3>\n        <p>%s</p>\n      </div>\n'
                     % (bi('و بعدش، فنی', 'And now, technically'), bi(t['technical_fa'], t['technical_en'])))
        if t.get('pitfall_fa') or t.get('pitfall_en'):
            parts.append('      <div class="gl-block pitfall">\n        <h3><span class="dot" aria-hidden="true"></span>%s</h3>\n        <p>%s</p>\n      </div>\n'
                         % (bi('تلهٔ رایج', 'The usual trap'), bi(t.get('pitfall_fa', ''), t.get('pitfall_en', ''))))
        rel = [r for r in (t.get('related') or []) if r in by_id]
        if rel:
            parts.append('      <div class="gl-related"><span class="lbl">%s</span>\n' % bi('مرتبط', 'Related'))
            for r in rel:
                parts.append('        <a href="#%s">%s</a>\n' % (q(r), escape(by_id[r]['term'])))
            parts.append('      </div>\n')
        parts.append('    </article>\n\n')

    parts.append('  </div>\n')
    parts.append('  <p class="gl-empty" id="gl-empty" hidden>' +
                 bi('واژه‌ای با این جست‌وجو پیدا نشد. کلمهٔ دیگری امتحان کن.',
                    'No term matched that search. Try another word.') + '</p>\n')
    parts.append('</main>\n\n')

    parts.append('''<footer class="footer">
  <div class="giant">DDIA<em>&middot;</em>GL</div>
  <p class="small">
    ''' + bi('بر پایه «Designing Data-Intensive Applications، ویرایش ۲» · توضیح‌ها به فارسی و انگلیسی',
             'Based on “Designing Data-Intensive Applications, 2nd Edition” · explanations in Persian and English') + '''
  </p>
</footer>

<script src="../assets/site.js"></script>
<script src="../assets/glossary-data.js"></script>
<script src="../assets/glossary.js" defer></script>
</body>
</html>
''')

    ld = {'@context': 'https://schema.org', '@type': 'DefinedTermSet',
          'name': 'DDIA Study Lab glossary',
          'url': BASE + '/glossary/',
          'inLanguage': ['en', 'fa'],
          'definedTerm': [{'@type': 'DefinedTerm', 'name': t['term'], 'url': BASE + '/glossary/#' + t['id'],
                           'description': t['one_liner_en']} for t in terms]}
    # JSON-LD is injected into <head> after the title, matching seo_meta's placement
    page = ''.join(parts)
    tag = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>\n'
    page = page.replace('</head>', tag + '</head>', 1)
    return page

def main():
    check = '--check' in sys.argv
    if not DATA.exists():
        fail('missing %s' % DATA.relative_to(ROOT))
    try:
        doc = json.loads(DATA.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        fail('glossary.json is not valid JSON: %s' % exc)
    chapters = scene_dirs()
    terms = validate(doc, chapters)
    terms.sort(key=lambda t: (t['chapter'], t['term'].lower()))

    page = build_page(terms, chapters)
    data = build_data(terms, chapters)

    if check:
        stale = []
        if not PAGE.exists() or PAGE.read_text(encoding='utf-8') != page:
            stale.append(str(PAGE.relative_to(ROOT)))
        if not JS.exists() or JS.read_text(encoding='utf-8') != data:
            stale.append(str(JS.relative_to(ROOT)))
        if stale:
            fail('out of date, run python3 assets/build_glossary.py: ' + ', '.join(stale))
        print('ok: %d terms, page and data in step' % len(terms))
        return

    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(page, encoding='utf-8')
    JS.write_text(data, encoding='utf-8')
    print('wrote %s (%d terms, %d KB)' % (PAGE.relative_to(ROOT), len(terms), len(page) // 1024))
    print('wrote %s (%d KB)' % (JS.relative_to(ROOT), len(data) // 1024))

if __name__ == '__main__':
    main()
