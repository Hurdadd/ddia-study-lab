#!/usr/bin/env python3
"""Generate the glossary from assets/glossary.json.

assets/glossary.json is the single source of truth. Only one page would be several
megabytes, so the glossary is published as:

  glossary/index.html        the index: every term, grouped by chapter, one line each
  glossary/ch<N>/index.html  the full entry for each term of that chapter
  assets/glossary-data.js    window.DDIA_GLOSSARY, the hover previews; every page that
                             marks a term loads it, so it carries no prose beyond the
                             one-line definition (file:// safe, no fetch)

Run: python3 assets/build_glossary.py [--check] [--preview]
--check writes nothing and fails when a committed page is out of date.
--preview builds what exists so far and drops links to terms not written yet.
"""
from html import escape
from pathlib import Path
import json, re, sys

import figures

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'assets' / 'glossary.json'
GLOSS = ROOT / 'glossary'
JS = ROOT / 'assets' / 'glossary-data.js'
BASE = 'https://ddia-study-lab.vercel.app'

REQUIRED = ('id', 'term', 'chapter', 'chapter_ref', 'one_liner_fa', 'one_liner_en',
            'daily_fa', 'daily_en', 'everyday_fa', 'everyday_en',
            'technical_fa', 'technical_en')
ALIAS_OK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .+\-/&@%'’]*[A-Za-z0-9)]$")
ID_OK = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

# depth floor per tier, in words of the Persian text (the language the site leads with)
FLOOR = {'A': {'daily': 22, 'everyday': 50, 'technical': 105, 'pitfall': 16, 'sections': 1},
         'B': {'daily': 16, 'everyday': 30, 'technical': 65, 'pitfall': 10, 'sections': 0}}


# ───────────────────────────────── naming ─────────────────────────────────────

def scene_dirs():
    """chapter number -> directory name, e.g. 7 -> 'ch7-sharding'."""
    out = {}
    for p in sorted(ROOT.glob('ch*')):
        m = re.match(r'ch(\d+)-', p.name)
        if m and p.is_dir():
            out[int(m.group(1))] = p.name
    return out


def strip_tags(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()


def chapter_titles(chapters):
    """chapter number -> {'fa','en'} taken from the chapter's own <h1>."""
    out = {}
    for num, ref in chapters.items():
        path = ROOT / ref / 'index.html'
        title = {'fa': 'فصل %s' % to_fa(num), 'en': 'Chapter %d' % num}
        if path.exists():
            text = path.read_text(encoding='utf-8')
            m = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.S)
            if m:
                fa = re.search(r'<span class="fa">(.*?)</span>', m.group(1), re.S)
                en = re.search(r'<span class="en">(.*?)</span>', m.group(1), re.S)
                if fa:
                    title['fa'] = strip_tags(fa.group(1))
                if en:
                    title['en'] = strip_tags(en.group(1))
        out[num] = title
    return out


def first_section(term, chapter_ref):
    """Anchor of the first chapter section that mentions the term, or '' for the page top."""
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


def warn(msg):
    print('  ! ' + msg)


# ───────────────────────────────── validation ─────────────────────────────────

def words(s):
    return len(str(s).split())


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
        if not ID_OK.match(tid):
            problems.append('%s: id must be lowercase-with-dashes' % label)
        if tid in seen_id:
            problems.append('%s: duplicate id' % label)
        seen_id.add(tid)
        ch = t.get('chapter')
        if ch not in chapters:
            problems.append('%s: chapter %r has no ch* directory' % (label, ch))
        if t.get('chapter_ref') and t['chapter_ref'] not in chapters.values():
            problems.append('%s: chapter_ref %r is not a chapter directory'
                            % (label, t['chapter_ref']))
        for c in t.get('chapters') or []:
            if c not in chapters:
                problems.append('%s: chapters entry %r has no ch* directory' % (label, c))
        aliases = t.get('aliases') or [t.get('term', '')]
        for a in aliases:
            if not ALIAS_OK.match(a or ''):
                problems.append('%s: alias %r must start and end with a letter/digit' % (label, a))
            key = (a or '').lower()
            if key in seen_alias:
                problems.append('%s: alias %r already used by "%s"' % (label, a, seen_alias[key]))
            seen_alias[key] = tid
        if t.get('figure'):
            for e in figures.validate(t['figure']):
                problems.append('%s: %s' % (label, e))
        problems.extend(validate_blocks(t, label))
    for t in terms:
        for rel in t.get('related') or []:
            if rel not in seen_id:
                problems.append('%s: related "%s" is not a term id' % (t.get('id'), rel))
    if problems:
        for p in problems:
            print('  - ' + p)
        fail('%d glossary problem(s)' % len(problems))
    return terms


def validate_blocks(t, label):
    """Shape and depth floor of the optional blocks."""
    problems = []
    tier = t.get('tier', 'B')
    floor = FLOOR.get(tier, FLOOR['B'])

    need = {'daily_fa': 'daily', 'everyday_fa': 'everyday',
            'technical_fa': 'technical', 'pitfall_fa': 'pitfall'}
    for key, name in need.items():
        if name not in floor:
            continue
        have = words(t.get(key, ''))
        if have < floor[name]:
            problems.append('%s: %s_fa has %d words, tier %s needs %d'
                            % (label, name, have, tier, floor[name]))

    secs = t.get('sections') or []
    if not isinstance(secs, list):
        problems.append('%s: sections must be a list' % label)
    else:
        if len(secs) < floor['sections']:
            problems.append('%s: tier %s needs at least %d section(s), has %d'
                            % (label, tier, floor['sections'], len(secs)))
        if len(secs) > 4:
            problems.append('%s: at most 4 sections' % label)
        for i, s in enumerate(secs):
            if not isinstance(s, dict):
                problems.append('%s: sections[%d] must be an object' % (label, i))
                continue
            for k in ('h_fa', 'h_en', 'p_fa', 'p_en'):
                if not str(s.get(k, '')).strip():
                    problems.append('%s: sections[%d] missing %r' % (label, i, k))
            if words(s.get('p_fa', '')) < 40:
                problems.append('%s: sections[%d].p_fa has %d words, needs 40'
                                % (label, i, words(s.get('p_fa', ''))))

    nums = t.get('numbers') or []
    if not isinstance(nums, list) or len(nums) > 4:
        problems.append('%s: numbers must be a list of at most 4' % label)
    else:
        for i, n in enumerate(nums):
            if not isinstance(n, dict):
                problems.append('%s: numbers[%d] must be an object' % (label, i))
                continue
            for k in ('v', 'k_fa', 'k_en'):
                if not str(n.get(k, '')).strip():
                    problems.append('%s: numbers[%d] missing %r' % (label, i, k))
            if len(str(n.get('v', ''))) > 22:
                problems.append('%s: numbers[%d].v is too long' % (label, i))

    vs = t.get('vs')
    if vs is not None:
        if not isinstance(vs, dict):
            problems.append('%s: vs must be an object' % label)
        else:
            cols = vs.get('cols')
            if not isinstance(cols, list) or not 2 <= len(cols) <= 3:
                problems.append('%s: vs.cols must be 2..3 column headers' % label)
            else:
                for i, c in enumerate(cols):
                    if not (isinstance(c, dict) and c.get('h_fa') and c.get('h_en')):
                        problems.append('%s: vs.cols[%d] needs h_fa and h_en' % (label, i))
            rows = vs.get('rows')
            if not isinstance(rows, list) or not 1 <= len(rows) <= 5:
                problems.append('%s: vs.rows must be 1..5 rows' % label)
            else:
                for i, r in enumerate(rows):
                    if not isinstance(r, dict):
                        problems.append('%s: vs.rows[%d] must be an object' % (label, i))
                        continue
                    lab = r.get('label') or {}
                    if not (lab.get('fa') and lab.get('en')):
                        problems.append('%s: vs.rows[%d].label needs fa and en' % (label, i))
                    cells = r.get('cells')
                    if not isinstance(cells, list) or (isinstance(cols, list) and len(cells) != len(cols)):
                        problems.append('%s: vs.rows[%d].cells must match vs.cols' % (label, i))
                        continue
                    for j, c in enumerate(cells):
                        if not (isinstance(c, dict) and c.get('fa') and c.get('en')):
                            problems.append('%s: vs.rows[%d].cells[%d] needs fa and en'
                                            % (label, i, j))
                        elif max(len(c['fa']), len(c['en'])) > 70:
                            problems.append('%s: vs.rows[%d].cells[%d] is too long'
                                            % (label, i, j))

    if tier == 'A' and not t.get('figure'):
        problems.append('%s: tier A needs a figure' % label)
    return problems


# ────────────────────────────────── markup ───────────────────────────────────

def bi(fa, en, sep=''):
    """Bilingual text: the site shows exactly one of these two spans."""
    return ('<span class="fa">%s</span><span class="en">%s</span>'
            % (escape(str(fa)), escape(str(en))))


def q(s):
    return escape(str(s), quote=True)


FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def to_fa(n):
    return str(n).translate(FA_DIGITS)


def chapter_label(n):
    return bi('فصل %s' % to_fa(n), 'Chapter %d' % n)


def block(cls, title_fa, title_en, body_fa, body_en):
    return ('      <div class="gl-block %s">\n'
            '        <h3><span class="dot" aria-hidden="true"></span>%s</h3>\n'
            '        <p>%s</p>\n'
            '      </div>\n'
            % (cls, bi(title_fa, title_en), bi(body_fa, body_en)))


BY_ID = {}


def card(t, idx):
    """One full entry, rendered on its chapter's page."""
    out = []
    chapter = t['chapter']
    anchor = t.get('section') or first_section((t.get('aliases') or [t['term']])[0],
                                               t['chapter_ref'])
    href = '../../%s/index.html%s' % (t['chapter_ref'], anchor)
    tier = t.get('tier', 'B')

    out.append('    <article class="gl-card" id="%s" data-chapter="%d" data-tier="%s">\n'
               % (q(t['id']), chapter, tier))
    out.append('      <div class="gl-head">\n')
    out.append('        <h2>%s</h2>\n' % escape(t['term']))
    if t.get('term_fa'):
        out.append('        <span class="gl-alias">%s</span>\n' % escape(t['term_fa']))
    out.append('        <a class="gl-chapter" href="%s">%s &middot; %s</a>\n'
               % (q(href), chapter_label(chapter), bi('دیدن در متن', 'see in context')))
    extra = [c for c in (t.get('chapters') or []) if c != chapter]
    if extra:
        links = ' '.join('<a href="../ch%d/index.html#%s">%s</a>'
                         % (c, q(t['id']), bi('فصل %s' % to_fa(c), 'ch %d' % c))
                         for c in extra)
        out.append('        <span class="gl-alsoseen">%s %s</span>\n'
                   % (bi('همچنین', 'also in'), links))
    out.append('      </div>\n')
    if t.get('hook_fa') or t.get('hook_en'):
        out.append('      <p class="gl-hook">%s</p>\n' % bi(t.get('hook_fa', ''),
                                                          t.get('hook_en', '')))

    out.append('      <div class="gl-block daily">\n'
               '        <h3><span class="dot" aria-hidden="true"></span>%s</h3>\n'
               '        <p>%s</p>\n'
               '      </div>\n'
               % (bi('مثال روزمره، بدون اصطلاح', 'The everyday one, no jargon'),
                  bi(t['daily_fa'], t['daily_en'])))

    out.append(block('everyday', 'تشبیه و تصویر ذهنی', 'The analogy',
                     t['everyday_fa'], t['everyday_en']))

    if t.get('figure'):
        out.append('      ' + figures.render(t['figure'], 'f%d' % idx) + '\n')

    out.append('      <div class="gl-block tech">\n'
               '        <h3><span class="dot" aria-hidden="true"></span>%s</h3>\n'
               '        <p>%s</p>\n'
               '      </div>\n'
               % (bi('و بعدش، فنی', 'And now, technically'),
                  bi(t['technical_fa'], t['technical_en'])))

    nums = t.get('numbers') or []
    if nums:
        out.append('      <div class="gl-stats">\n')
        for n in nums:
            out.append('        <div class="stat"><span class="v">%s</span>'
                       '<span class="k">%s</span></div>\n'
                       % (escape(str(n['v'])), bi(n['k_fa'], n['k_en'])))
        out.append('      </div>\n')

    secs = t.get('sections') or []
    if secs:
        out.append('      <div class="gl-deep">\n')
        for s in secs:
            out.append('        <div class="deep-item">\n'
                       '          <h4>%s</h4>\n'
                       '          <p>%s</p>\n'
                       '        </div>\n'
                       % (bi(s['h_fa'], s['h_en']), bi(s['p_fa'], s['p_en'])))
        out.append('      </div>\n')

    vs = t.get('vs')
    if vs:
        out.append('      <div class="gl-vs">\n')
        out.append('        <h4>%s</h4>\n' % bi(vs.get('h_fa', ''), vs.get('h_en', '')))
        out.append('        <table>\n          <thead><tr><th scope="col"></th>')
        for c in vs['cols']:
            out.append('<th scope="col">%s</th>' % bi(c['h_fa'], c['h_en']))
        out.append('</tr></thead>\n          <tbody>\n')
        for r in vs['rows']:
            out.append('            <tr><th scope="row">%s</th>'
                       % bi(r['label']['fa'], r['label']['en']))
            for c in r['cells']:
                out.append('<td>%s</td>' % bi(c['fa'], c['en']))
            out.append('</tr>\n')
        out.append('          </tbody>\n        </table>\n      </div>\n')

    if t.get('pitfall_fa') or t.get('pitfall_en'):
        out.append(block('pitfall', 'تلهٔ رایج', 'The usual trap',
                         t.get('pitfall_fa', ''), t.get('pitfall_en', '')))

    rel = [r for r in (t.get('related') or []) if r in BY_ID]
    if rel:
        out.append('      <div class="gl-related"><span class="lbl">%s</span>\n'
                   % bi('مرتبط', 'Related'))
        for r in rel:
            other = BY_ID[r]
            out.append('        <a href="../ch%d/index.html#%s">%s</a>\n'
                       % (other['chapter'], q(r), escape(other['term'])))
        out.append('      </div>\n')

    out.append('    </article>\n\n')
    return ''.join(out)


# ─────────────────────────────────── pages ────────────────────────────────────

def head(title_en, title_fa, desc, canonical, extra_css=''):
    return (
'<!DOCTYPE html>\n'
'<html lang="en" dir="ltr" data-hue="lilac" data-title-fa="%s" data-title-en="%s">\n'
'<head>\n'
'<meta charset="utf-8">\n'
'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
'<title>%s</title>\n'
'<meta name="description" content="%s">\n'
'<link rel="canonical" href="%s%s">\n'
'<meta property="og:type" content="article"><meta property="og:site_name" content="DDIA Study Lab">\n'
'<meta property="og:title" content="%s"><meta property="og:description" content="%s">\n'
'<meta property="og:url" content="%s%s"><meta property="og:image" content="%s/assets/og-image.png">\n'
'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">\n'
'<meta property="og:locale" content="en_US"><meta property="og:locale:alternate" content="fa_IR">\n'
'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="%s">\n'
'<meta name="twitter:description" content="%s"><meta name="twitter:image" content="%s/assets/og-image.png">\n'
'<link rel="preconnect" href="https://fonts.googleapis.com">\n'
'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
'<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&family=Vazirmatn:wght@300;400;500;700;900&display=swap" rel="stylesheet">\n'
'<link rel="stylesheet" href="%sassets/ddia.css">\n'
'<link rel="stylesheet" href="%sassets/glossary.css">\n'
'</head>\n' % (q(title_fa), q(title_en), escape(title_en), q(desc),
               BASE, canonical, q(title_en), q(desc), BASE, canonical, BASE,
               q(title_en), q(desc), BASE, extra_css, extra_css))


def topbar(up, active):
    here = ' aria-current="page"' if active == 'glossary' else ''
    return '''<header class="topbar">
  <a class="wordmark" href="%sindex.html">DDIA<em>&middot;</em><span class="fa">واژه‌ها</span><span class="en">TERMS</span></a>
  <nav class="topnav">
    <a href="%sindex.html"><span class="fa">نقشه راه</span><span class="en">Roadmap</span></a>
    <a href="%sch7-sharding/index.html"><span class="fa">فصل ۷</span><span class="en">Chapter 7</span></a>
    <a href="%sfinal-project/index.html"><span class="fa">پروژهٔ نهایی</span><span class="en">Final project</span></a>
    <a href="%sglossary/index.html"%s><span class="fa">واژه‌ها</span><span class="en">Terms</span></a>
  </nav>
  <button class="langbtn" data-lang-toggle><span class="fa">EN</span><span class="en">فارسی</span></button>
  <button class="iconbtn" data-theme-toggle aria-label="theme">
    <svg class="icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
    <svg class="icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
  </button>
</header>

''' % (up, up, up, up, up, here)


def scripts(up):
    return '''
<script src="%sassets/site.js"></script>
<script src="%sassets/glossary-data.js"></script>
<script src="%sassets/glossary.js" defer></script>
</body>
</html>
''' % (up, up, up)


def footer(up):
    return '''<footer class="footer">
  <div class="giant">DDIA<em>&middot;</em>GL</div>
  <p class="small">
    ''' + bi('بر پایه «Designing Data-Intensive Applications، ویرایش ۲» · توضیح‌ها به فارسی و انگلیسی',
             'Based on “Designing Data-Intensive Applications, 2nd Edition” · explanations in Persian and English') + '''
  </p>
</footer>
'''


def build_index(terms, chapters, figures_n):
    title_en = 'DDIA Glossary: %d terms, each with a plain example and a diagram' % len(terms)
    title_fa = ('واژه‌نامهٔ DDIA: %s واژه، هر کدام با یک مثال روزمره و یک نمودار'
                % to_fa(len(terms)))
    desc = ('Every jargon term in this DDIA study guide: a jargon-free everyday example, an '
            'analogy, a generated diagram, the technical account and the usual trap. · '
            'همهٔ واژه‌های تخصصی DDIA با مثال روزمره، نمودار و توضیح فنی.')

    parts = [head(title_en, title_fa, desc, '/glossary/', '../')]
    parts.append('<body>\n\n')
    parts.append(topbar('../', 'glossary'))
    parts.append('''<section class="doc-hero">
  <div class="blobs" aria-hidden="true"><i class="b1"></i><i class="b2"></i><i class="b3"></i></div>
  <p class="crumb"><a href="../index.html">''' + bi('نقشه راه', 'Roadmap') + '''</a>/ ''' + bi('واژه‌نامه', 'Glossary') + '''</p>
  <h1><span class="fa">هر واژه، از زندگی روزمره تا کد</span><span class="en">Every term, from real life to real code</span></h1>
  <p class="lede">
    ''' + bi(
      'هر واژهٔ تخصصی این راهنما اینجاست، و هر کدام یک مسیر ثابت دارد: اول یک صحنهٔ ساده که همان روز در زندگی خودت دیده‌ای و اصلاً اصطلاح ندارد؛ بعد یک تشبیه که تصویر ذهنی می‌سازد؛ بعد یک نمودار؛ بعد همان چیز به زبان دقیق و فنی؛ و آخرش تله‌ای که بیشتر آدم‌ها در آن گیر می‌کنند. روی واژه‌های خط‌چین‌دار فصل‌ها بروی، می‌آیی همین‌جا. برای خواندنِ کاملِ یک واژه، روی خودش بزن.',
      'Every jargon word in this guide is here, and each one follows the same path: a plain scene from your own day with no jargon, an analogy that builds a mental picture, a diagram, the same thing stated precisely, and the trap most people fall into. Click a dotted word in a chapter and you land here. Click a term below for its full entry.') + '''
  </p>
  <p class="meta-row">
    <b>''' + bi(to_fa(len(terms)), str(len(terms))) + '''</b> ''' + bi('واژه', 'terms') + '''
    <span class="dot">&middot;</span> <b>''' + bi(to_fa(figures_n), str(figures_n)) + '''</b> ''' + bi('نمودار', 'diagrams') + '''
    <span class="dot">&middot;</span> <b>''' + bi(to_fa(len({t['chapter'] for t in terms})),
                                                    str(len({t['chapter'] for t in terms}))) + '''</b> ''' + bi('فصل', 'chapters') + '''
  </p>
</section>

<main class="gl-main">
''')

    parts.append('''  <div class="gl-tools" role="group" aria-label="Filter glossary">
    <input class="gl-search" id="gl-search" type="search" autocomplete="off"
           placeholder="Search terms…" data-ph-en="Search terms…" data-ph-fa="جست‌وجو در واژه‌ها…"
           aria-label="Search glossary terms">
    <span class="gl-count" id="gl-count" aria-live="polite">%d / %d</span>
  </div>

  <div class="gl-list" id="gl-list" data-no-glossary>
''' % (len(terms), len(terms)))

    by_ch = {}
    for t in terms:
        by_ch.setdefault(t['chapter'], []).append(t)
    for ch in sorted(by_ch):
        title = TITLES.get(ch, {'fa': 'فصل %s' % ch, 'en': 'Chapter %d' % ch})
        parts.append('    <section class="gl-chgroup" id="ch%d" data-chapter="%d">\n' % (ch, ch))
        parts.append('      <h2><span class="gl-num">%s</span>%s</h2>\n'
                     % (bi(to_fa(ch), str(ch)), bi(title['fa'], title['en'])))
        parts.append('      <ul>\n')
        for t in by_ch[ch]:
            parts.append('        <li><a class="gl-row" href="ch%d/index.html#%s" data-chapter="%d">'
                         '<span class="t">%s</span>'
                         '<span class="fa-name">%s</span>'
                         '<span class="one">%s</span></a></li>\n'
                         % (ch, q(t['id']), ch, escape(t['term']),
                            escape(t.get('term_fa') or ''),
                            bi(t['one_liner_fa'], t['one_liner_en'])))
        parts.append('      </ul>\n    </section>\n\n')
    parts.append('  </div>\n')
    parts.append('  <p class="gl-empty" id="gl-empty" hidden>' +
                 bi('واژه‌ای با این جست‌وجو پیدا نشد. کلمهٔ دیگری امتحان کن.',
                    'No term matched that search. Try another word.') + '</p>\n')
    parts.append('</main>\n\n')
    parts.append(footer('../'))
    parts.append(scripts('../'))

    ld = {'@context': 'https://schema.org', '@type': 'DefinedTermSet',
          'name': 'DDIA Study Lab glossary',
          'url': BASE + '/glossary/',
          'inLanguage': ['en', 'fa'],
          'definedTerm': [{'@type': 'DefinedTerm', 'name': t['term'],
                           'url': '%s/glossary/ch%d/#%s' % (BASE, t['chapter'], t['id']),
                           'description': t['one_liner_en']} for t in terms]}
    page = ''.join(parts)
    tag = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>\n'
    return page.replace('</head>', tag + '</head>', 1)


def build_chapter(ch, items, chapters):
    title = TITLES.get(ch, {'fa': 'فصل %s' % ch, 'en': 'Chapter %d' % ch})
    title_en = 'DDIA Glossary, chapter %d: %s' % (ch, title['en'])
    title_fa = 'واژه‌نامهٔ DDIA، فصل %s: %s' % (to_fa(ch), title['fa'])
    desc = ('The %d terms of chapter %d, each with a jargon-free example, a diagram, the '
            'technical account and the usual trap. · %s واژهٔ فصل %s.'
            % (len(items), ch, to_fa(len(items)), to_fa(ch)))

    parts = [head(title_en, title_fa, desc, '/glossary/ch%d/' % ch, '../../')]
    parts.append('<body>\n\n')
    parts.append(topbar('../../', 'glossary'))
    parts.append('''<section class="doc-hero gl-chhero">
  <div class="blobs" aria-hidden="true"><i class="b1"></i><i class="b2"></i><i class="b3"></i></div>
  <p class="crumb"><a href="../../index.html">''' + bi('نقشه راه', 'Roadmap') + '''</a>/ <a href="../index.html">'''
    + bi('واژه‌نامه', 'Glossary') + '''</a>/ ''' + bi('فصل %s' % to_fa(ch), 'Chapter %d' % ch) + '''</p>
  <h1><span class="gl-num">''' + bi(to_fa(ch), str(ch)) + '''</span>''' + bi(title['fa'], title['en']) + '''</h1>
  <p class="lede">''' + bi('%s واژه از فصل %s — هر کدام با یک مثال روزمره، یک نمودار و تلهٔ رایج.'
                           % (to_fa(len(items)), to_fa(ch)),
                           '%d terms from chapter %d, each with an everyday example, a diagram and the usual trap.'
                           % (len(items), ch)) + '''</p>
</section>

<main class="gl-main">
''')

    parts.append('  <nav class="gl-chnav" aria-label="Glossary chapters">\n')
    if ch - 1 in CHAPTER_SET:
        parts.append('    <a class="prev" href="../ch%d/index.html">%s</a>\n'
                     % (ch - 1, bi('قبلی: فصل %s' % to_fa(ch - 1), '← chapter %d' % (ch - 1))))
    parts.append('    <a href="../index.html">%s</a>\n' % bi('همهٔ واژه‌ها', 'All terms'))
    if ch + 1 in CHAPTER_SET:
        parts.append('    <a class="next" href="../ch%d/index.html">%s</a>\n'
                     % (ch + 1, bi('بعدی: فصل %s' % to_fa(ch + 1), 'chapter %d →' % (ch + 1))))
    parts.append('  </nav>\n\n')

    parts.append('  <div class="gl-grid" id="gl-grid" data-no-glossary>\n')
    for i, t in enumerate(items):
        parts.append(card(t, ch * 100 + i))
    parts.append('  </div>\n')
    parts.append('</main>\n\n')
    parts.append(footer('../../'))
    parts.append(scripts('../../'))
    return ''.join(parts)


def build_data(terms, chapters):
    out = {}
    for t in terms:
        out[t['id']] = {
            'term': t['term'],
            'term_fa': t.get('term_fa', ''),
            'aliases': t.get('aliases') or [t['term']],
            'one_liner_fa': t['one_liner_fa'],
            'one_liner_en': t['one_liner_en'],
            'chapter': t['chapter'],
            'page': 'ch%d/index.html' % t['chapter'],
            'section': t.get('section', ''),
        }
    payload = {'maxPerTerm': 2, 'root': 'glossary/',
               'chapters': {str(k): v for k, v in sorted(chapters.items())},
               'order': [t['id'] for t in terms], 'terms': out}
    body = json.dumps(payload, ensure_ascii=False, indent=0, separators=(',', ':'))
    return ('/* Generated by assets/build_glossary.py from assets/glossary.json.\n'
            '   Do not edit by hand; run the builder instead. */\n'
            'window.DDIA_GLOSSARY = ' + body + ';\n')


TITLES = {}
CHAPTER_SET = set()
TERMS = []


def main():
    check = '--check' in sys.argv
    preview = '--preview' in sys.argv
    if not DATA.exists():
        fail('missing %s' % DATA.relative_to(ROOT))
    try:
        doc = json.loads(DATA.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        fail('glossary.json is not valid JSON: %s' % exc)

    chapters = scene_dirs()
    if preview:
        ids = {t['id'] for t in doc['terms']}
        for t in doc['terms']:
            t['related'] = [r for r in (t.get('related') or []) if r in ids]
        print('preview build: %d terms' % len(ids))

    global TERMS, TITLES, CHAPTER_SET, BY_ID
    terms = validate(doc, chapters)
    TERMS = terms
    BY_ID = {t['id']: t for t in terms}
    TITLES = chapter_titles(chapters)
    CHAPTER_SET = set(chapters)
    terms.sort(key=lambda t: (t['chapter'], t['term'].lower()))

    by_ch = {}
    for t in terms:
        by_ch.setdefault(t['chapter'], []).append(t)

    pages = {GLOSS / 'index.html': build_index(terms, chapters,
                                               sum(1 for t in terms if t.get('figure')))}
    for ch, items in by_ch.items():
        pages[GLOSS / ('ch%d' % ch) / 'index.html'] = build_chapter(ch, items, chapters)
    data = build_data(terms, chapters)

    if check:
        stale = []
        for path, html in pages.items():
            if not path.exists() or path.read_text(encoding='utf-8') != html:
                stale.append(str(path.relative_to(ROOT)))
        if not JS.exists() or JS.read_text(encoding='utf-8') != data:
            stale.append(str(JS.relative_to(ROOT)))
        if stale:
            fail('out of date, run python3 assets/build_glossary.py: ' + ', '.join(stale))
        print('ok: %d terms on %d pages, data in step' % (len(terms), len(pages)))
        return

    total = 0
    for path, html in pages.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding='utf-8')
        total += len(html.encode())
    JS.write_text(data, encoding='utf-8')
    print('wrote %d glossary pages (%d terms, %d figures, %d KB total)'
          % (len(pages), len(terms), sum(1 for t in terms if t.get('figure')), total // 1024))
    print('wrote %s (%d KB)' % (JS.relative_to(ROOT), len(data.encode()) // 1024))

    # a stale chapter page left behind by an earlier chapter assignment would still
    # be reachable from a bookmark, so report it instead of leaving it to rot
    for d in sorted(GLOSS.glob('ch*')):
        m = re.match(r'ch(\d+)$', d.name)
        if m and int(m.group(1)) not in by_ch:
            warn('%s exists but no term points at it' % d.relative_to(ROOT))

    bad = []
    for t in terms:
        ref = t['chapter_ref']
        anchor = t.get('section') or first_section((t.get('aliases') or [t['term']])[0], ref)
        if not anchor:
            continue
        body = (ROOT / ref / 'index.html').read_text(encoding='utf-8')
        if 'id="%s"' % anchor[1:] not in body:
            bad.append('%s -> %s%s' % (t['id'], ref, anchor))
    if bad:
        warn('%d chapter anchors do not resolve (linked to page top instead):' % len(bad))
        for b in bad[:8]:
            warn('  ' + b)


if __name__ == '__main__':
    main()
