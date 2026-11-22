#!/usr/bin/env python3
"""Inline SVG figures for the glossary, generated from a small declared spec.

Every figure is plain SVG with no external files, no fonts to fetch and no colour
literals: the classes in assets/glossary.css resolve the site's own tokens, so light
and dark themes work and the page stays file:// safe.

A spec is a dict with "kind" plus that kind's fields. Text comes in fa/en pairs and
is emitted twice inside one <text> node; the site's two i18n rules hide one of them.

    {"kind":"split", "cap_fa":"...", "cap_en":"...",
     "from":{"fa":"...","en":"..."},
     "to":[{"fa":"...","en":"..."}, ...]}

validate() is the contract: build_glossary.py refuses to write a page whose figures
break it, and content authors run check_figures.py before handing work back.
"""
from html import escape

W = 680                     # every viewBox is this wide; CSS scales it down
MAX_LABEL = 26              # characters, both languages, per label
MAX_CAP = 150

KINDS = ('split', 'compare', 'pipeline', 'ladder', 'timeline', 'grid', 'ring',
         'quorum', 'bars')

FA_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


# ─────────────────────────────── primitives ────────────────────────────────

def _q(v):
    return escape(str(v), quote=True)


def _bi(node, sep=''):
    """The one place that decides how a bilingual string becomes markup."""
    if isinstance(node, dict):
        fa, en = node.get('fa', ''), node.get('en', '')
    else:
        fa = en = node
    return ('<tspan class="fa" direction="rtl">%s</tspan>'
            '<tspan class="en">%s</tspan>' % (escape(str(fa)), escape(str(en))))


def text(x, y, node, cls='fig-t', size=13, anchor='middle', weight=None, extra=''):
    style = ' style="font-size:%spx%s"' % (size, ';font-weight:%s' % weight if weight else '')
    return ('<text class="%s" x="%.1f" y="%.1f" text-anchor="%s"%s%s>%s</text>'
            % (cls, x, y, anchor, style, extra, _bi(node)))


def box(x, y, w, h, cls='fig-box', rx=12):
    return ('<rect class="%s" x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%d"/>'
            % (cls, x, y, w, h, rx))


def text_ltr(x, y, value, cls='fig-t', size=13, anchor='middle', weight=None):
    style = ' style="font-size:%spx%s"' % (size, ';font-weight:%s' % weight if weight else '')
    return ('<text class="%s" x="%.1f" y="%.1f" text-anchor="%s" direction="ltr"%s>%s</text>'
            % (cls, x, y, anchor, style, escape(str(value))))


def label_box(x, y, w, h, node, cls='fig-box', size=13, weight='700'):
    """A rounded box with its label centred; y is the box top."""
    return (box(x, y, w, h, cls) +
            text(x + w / 2, y + h / 2 + size * 0.36, node, 'fig-t', size, weight=weight))


def arrow(x1, y1, x2, y2, cls='fig-arrow', head='fig-head'):
    return ('<path class="%s" d="M%.1f %.1f L%.1f %.1f" marker-end="url(#%s)"/>'
            % (cls, x1, y1, x2, y2, head))


def line(x1, y1, x2, y2, cls='fig-line', extra=''):
    return ('<path class="%s" d="M%.1f %.1f L%.1f %.1f"%s/>' % (cls, x1, y1, x2, y2, extra))


def fit(node, budget=MAX_LABEL):
    """Label length in characters, counting the wider of the two languages."""
    if isinstance(node, dict):
        return max(len(str(node.get('fa', ''))), len(str(node.get('en', ''))))
    return len(str(node))


def size_for(node, base=13, hard=26, floor=10.5):
    n = fit(node)
    if n <= 14:
        return base
    if n >= hard:
        return floor
    return round(base - (base - floor) * (n - 14) / (hard - 14), 1)


def legend(cap_fa, cap_en, y, x=20):
    return ''


# ────────────────────────────────── kinds ──────────────────────────────────

def _split(s):
    to = s['to']
    n = len(to)
    h = 196
    top_w = min(360, 120 + fit(s['from']) * 8.4)
    out = [box((W - top_w) / 2, 8, top_w, 44),
           text(W / 2, 36, s['from'], 'fig-t', min(13, size_for(s['from'])))]

    gap = 16
    cw = (W - 40 - gap * (n - 1)) / n
    bus_y = 84
    out.append(arrow(W / 2, 52, W / 2, bus_y))
    xs = [20 + i * (cw + gap) + cw / 2 for i in range(n)]
    if n > 1:
        out.append(line(xs[0], bus_y, xs[-1], bus_y, 'fig-line'))
    for i, item in enumerate(to):
        out.append(arrow(xs[i], bus_y, xs[i], 108))
        out.append(box(20 + i * (cw + gap), 108, cw, 48))
        out.append(text(xs[i], 137, item, 'fig-t', size_for(item, 13, 26, 10.5)))
    if s.get('down_fa') or s.get('down_en'):
        out.append(text(W / 2, 178, {'fa': s.get('down_fa', ''), 'en': s.get('down_en', '')},
                        'fig-t-muted', 11.5))
    return h, out


def _compare(s):
    lines = max(len(s['left'].get('lines') or []), len(s['right'].get('lines') or []), 1)
    h = 78 + lines * 30
    out = []
    pw = (W - 40 - 22) / 2
    for i, side in enumerate(('left', 'right')):
        p = s[side]
        x = 20 + i * (pw + 22)
        out.append(box(x, 6, pw, h - 12, 'fig-box'))
        out.append(box(x, 6, pw, 40, 'fig-fill', rx=12))
        out.append(text(x + pw / 2, 31, {'fa': p.get('h_fa', ''), 'en': p.get('h_en', '')},
                        'fig-t', size_for(p.get('h_en', ''), 13, 24, 10.5), weight='800'))
        for j, ln in enumerate(p.get('lines') or []):
            out.append(text(x + pw / 2, 66 + j * 30, ln,
                            'fig-t', size_for(ln, 12, 44, 10), anchor='middle'))
    return h, out


def _pipeline(s):
    items = s['items']
    n = len(items)
    h = 150
    gap = 22
    bw = (W - 40 - gap * (n - 1)) / n
    out = []
    for i, it in enumerate(items):
        x = 20 + i * (bw + gap)
        out.append(box(x, 34, bw, 62, 'fig-box'))
        out.append(text(x + bw / 2, 62, it, 'fig-t', size_for(it, 13, 26, 10.5), weight='700'))
        sub = {'fa': it.get('sub_fa', ''), 'en': it.get('sub_en', '')} if isinstance(it, dict) else None
        if sub and (sub['fa'] or sub['en']):
            out.append(text(x + bw / 2, 82, sub, 'fig-t-muted', 10.5))
        if i:
            out.append(arrow(x - gap + 3, 65, x - 3, 65))
    return h, out


def _ladder(s):
    items = s['items']
    n = len(items)
    h = 16 + n * 54
    out = []
    for i, it in enumerate(items):
        y = 8 + i * 54
        out.append(box(60, y, W - 120, 46, 'fig-box'))
        out.append(text(W / 2, y + 28, it, 'fig-t', size_for(it, 13, 40, 10.5), weight='700'))
    return h, out


def _timeline(s):
    items = s['items']
    n = len(items)
    h = 176
    y0 = 96
    xs = [60 + (W - 120) * (i / max(n - 1, 1)) for i in range(n)]
    out = [line(40, y0, W - 40, y0, 'fig-line')]
    for i, it in enumerate(items):
        out.append('<circle class="fig-dot" cx="%.1f" cy="%.1f" r="7"/>' % (xs[i], y0))
        out.append(text(xs[i], y0 - 26, it, 'fig-t', size_for(it, 12.5, 20, 10.5), weight='700'))
        note = {'fa': it.get('note_fa', ''), 'en': it.get('note_en', '')} if isinstance(it, dict) else None
        if note and (note['fa'] or note['en']):
            out.append(text(xs[i], y0 + 34, note, 'fig-t-muted', 11))
    return h, out


def _grid(s):
    cols, rows = s['cols'], s['rows']
    nc, nr = len(cols), len(rows)
    h = 34 + nr * 52 + 8
    x0, y0 = 122, 34
    cw = (W - x0 - 24) / nc
    out = []
    for c, col in enumerate(cols):
        out.append(text(x0 + c * cw + cw / 2, 24, col, 'fig-t', size_for(col, 11.5, 18, 9.8),
                        weight='800'))
    hot = {(int(r), int(c)) for r, c in (s.get('hot') or [])}
    for r, row in enumerate(rows):
        y = y0 + r * 52
        out.append(text(x0 / 2 - 6, y + 30, row, 'fig-t', size_for(row, 11.5, 18, 9.8)))
        for c in range(nc):
            cls = 'fig-box fig-fill' if (r, c) in hot else 'fig-box'
            out.append(box(x0 + c * cw + 4, y + 6, cw - 8, 38, cls, rx=9))
    if s.get('hl_fa') or s.get('hl_en'):
        out.append(text(W / 2, h - 2, {'fa': s.get('hl_fa', ''), 'en': s.get('hl_en', '')},
                        'fig-t-muted', 11))
    return h, out


def _ring(s):
    import math
    nodes = s['nodes']
    n = len(nodes)
    h = 292
    cx, cy, r = W / 2, h / 2 - 4, 92
    out = ['<circle class="fig-ring" cx="%.1f" cy="%.1f" r="%.1f"/>' % (cx, cy, r)]
    if s.get('center_fa') or s.get('center_en'):
        out.append(text(cx, cy + 4, {'fa': s.get('center_fa', ''), 'en': s.get('center_en', '')},
                        'fig-t-muted', 11.5))
    for i, nd in enumerate(nodes):
        a = -math.pi / 2 + 2 * math.pi * i / n
        px, py = cx + r * math.cos(a), cy + r * math.sin(a)
        lx, ly = cx + (r + 40) * math.cos(a), cy + (r + 40) * math.sin(a)
        out.append('<circle class="fig-dot" cx="%.1f" cy="%.1f" r="8"/>' % (px, py))
        anchor = 'middle'
        if math.cos(a) > 0.35:
            anchor = 'start'
        elif math.cos(a) < -0.35:
            anchor = 'end'
        out.append(text(lx, ly + 4, nd, 'fig-t', size_for(nd, 12.5, 22, 10.5), anchor=anchor))
    return h, out


def _quorum(s):
    nodes = s['nodes']
    n = len(nodes)
    h = 190
    y = 104
    span = W - 120
    xs = [60 + span * (i / max(n - 1, 1)) for i in range(n)]

    def bracket(idxs, yy, cls, label, tick_up):
        if not idxs:
            return ''
        lo, hi = min(idxs), max(idxs)
        seg = ['<path class="%s" d="M%.1f %.1f L%.1f %.1f"/>' % (cls, xs[lo], yy, xs[hi], yy)]
        for i in idxs:
            seg.append('<path class="%s" d="M%.1f %.1f L%.1f %.1f"/>'
                       % (cls, xs[i], yy, xs[i], yy + (-9 if tick_up else 9)))
        seg.append(text((xs[lo] + xs[hi]) / 2, yy - 8, label, 'fig-t-muted', 11))
        return ''.join(seg)

    out = []
    wr, rd = s.get('write') or {}, s.get('read') or {}
    out.append(bracket(wr.get('index') or [], 58, 'fig-line-strong',
                       {'fa': wr.get('label_fa', ''), 'en': wr.get('label_en', '')}, False))
    out.append(bracket(rd.get('index') or [], 152, 'fig-line',
                       {'fa': rd.get('label_fa', ''), 'en': rd.get('label_en', '')}, True))
    for i, nd in enumerate(nodes):
        hot = i in (wr.get('index') or [])
        out.append('<circle class="%s" cx="%.1f" cy="%.1f" r="23"/>'
                   % ('fig-node fig-fill' if hot else 'fig-node', xs[i], y))
        out.append(text(xs[i], y + 5, nd, 'fig-t', size_for(nd, 12, 12, 10), weight='800'))
    return h, out


def _bars(s):
    items = s['items']
    n = len(items)
    h = 208
    base = 158
    bw = min(54, (W - 60) / n - 26)
    gap = min(64, ((W - 40) - bw * n) / max(n - 1, 1))
    left = (W - (bw * n + gap * (n - 1))) / 2
    top = 40
    peak = max((it.get('p', 50) for it in items), default=100)
    out = []
    for i, it in enumerate(items):
        x = left + i * (bw + gap)
        p = max(4, min(100, float(it.get('p', 50))))
        bh = (p / 100.0) * (base - top)
        cls = 'fig-box fig-fill' if p == peak else 'fig-box'
        out.append(box(x, base - bh, bw, bh, cls, rx=8))
        out.append(text_ltr(x + bw / 2, base - bh - 10, it.get('v', ''),
                            'fig-t', 11.5, weight='800'))
        out.append(text(x + bw / 2, base + 22, it, 'fig-t', size_for(it, 11.5, 20, 9.5),
                        weight='700'))
    out.append(line(left - 12, base, left + bw * n + gap * (n - 1) + 12, base, 'fig-line'))
    return h, out


RENDER = {'split': _split, 'compare': _compare, 'pipeline': _pipeline, 'ladder': _ladder,
          'timeline': _timeline, 'grid': _grid, 'ring': _ring, 'quorum': _quorum, 'bars': _bars}


# ───────────────────────────────── validation ──────────────────────────────

def _need(node, key, where, errs, cap=None):
    v = node.get(key)
    if v is None or (isinstance(v, str) and not v.strip()):
        errs.append('%s: missing %r' % (where, key))
        return None
    if not isinstance(v, str):
        errs.append('%s: %r must be a string' % (where, key))
        return None
    if cap and len(v) > cap:
        errs.append('%s: %r is %d chars (max %d)' % (where, key, len(v), cap))
    return v


def _pair(node, where, errs, cap=MAX_LABEL):
    """A bilingual label: {'fa':..,'en':..} with both sides non-empty and short."""
    if not isinstance(node, dict):
        errs.append('%s: must be an object with fa/en' % where)
        return
    for k in ('fa', 'en'):
        if not str(node.get(k, '')).strip():
            errs.append('%s: missing %r' % (where, k))
        elif cap and len(str(node[k])) > cap:
            errs.append('%s.%s is %d chars (max %d): %r'
                        % (where, k, len(node[k]), cap, node[k]))
        elif re_line_break(node[k]):
            errs.append('%s.%s must be a single line' % (where, k))


def re_line_break(v):
    return '\n' in str(v) or '\r' in str(v)


def validate(spec):
    """Return a list of human-readable problems; empty means the spec is renderable."""
    errs = []
    if not isinstance(spec, dict):
        return ['figure must be an object']
    kind = spec.get('kind')
    if kind not in RENDER:
        return ['figure.kind %r is not one of %s' % (kind, ', '.join(KINDS))]
    for k, cap in (('cap_fa', MAX_CAP), ('cap_en', MAX_CAP)):
        _need(spec, k, 'figure', errs, cap)

    if kind == 'split':
        _pair(spec.get('from'), 'split.from', errs)
        to = spec.get('to')
        if not isinstance(to, list) or not 2 <= len(to) <= 4:
            errs.append('split.to must be a list of 2..4 labels')
        else:
            for i, it in enumerate(to):
                _pair(it, 'split.to[%d]' % i, errs)
    elif kind == 'compare':
        for side in ('left', 'right'):
            p = spec.get(side)
            if not isinstance(p, dict):
                errs.append('compare.%s must be an object' % side)
                continue
            _pair({'fa': p.get('h_fa'), 'en': p.get('h_en')}, 'compare.%s.head' % side, errs, 24)
            lines = p.get('lines')
            if not isinstance(lines, list) or not 1 <= len(lines) <= 3:
                errs.append('compare.%s.lines must be a list of 1..3 items' % side)
            else:
                for i, ln in enumerate(lines):
                    _pair(ln, 'compare.%s.lines[%d]' % (side, i), errs, 40)
    elif kind == 'pipeline':
        items = spec.get('items')
        if not isinstance(items, list) or not 3 <= len(items) <= 5:
            errs.append('pipeline.items must be a list of 3..5 stages')
        else:
            for i, it in enumerate(items):
                _pair(it, 'pipeline.items[%d]' % i, errs)
                if isinstance(it, dict) and (it.get('sub_fa') or it.get('sub_en')):
                    _pair({'fa': it.get('sub_fa', ''), 'en': it.get('sub_en', '')},
                          'pipeline.items[%d].sub' % i, errs, 20)
    elif kind == 'ladder':
        items = spec.get('items')
        if not isinstance(items, list) or not 3 <= len(items) <= 5:
            errs.append('ladder.items must be a list of 3..5 layers')
        else:
            for i, it in enumerate(items):
                _pair(it, 'ladder.items[%d]' % i, errs, 40)
    elif kind == 'timeline':
        items = spec.get('items')
        if not isinstance(items, list) or not 2 <= len(items) <= 4:
            errs.append('timeline.items must be a list of 2..4 moments')
        else:
            for i, it in enumerate(items):
                _pair(it, 'timeline.items[%d]' % i, errs, 20)
                if isinstance(it, dict) and (it.get('note_fa') or it.get('note_en')):
                    _pair({'fa': it.get('note_fa', ''), 'en': it.get('note_en', '')},
                          'timeline.items[%d].note' % i, errs, 22)
    elif kind == 'grid':
        cols, rows = spec.get('cols'), spec.get('rows')
        if not isinstance(cols, list) or not 2 <= len(cols) <= 4:
            errs.append('grid.cols must be a list of 2..4 labels')
        else:
            for i, c in enumerate(cols):
                _pair(c, 'grid.cols[%d]' % i, errs, 18)
        if not isinstance(rows, list) or not 2 <= len(rows) <= 4:
            errs.append('grid.rows must be a list of 2..4 labels')
        else:
            for i, r in enumerate(rows):
                _pair(r, 'grid.rows[%d]' % i, errs, 18)
        hot = spec.get('hot') or []
        if not isinstance(hot, list):
            errs.append('grid.hot must be a list of [row, col] pairs')
        else:
            for h in hot:
                if (not isinstance(h, list) or len(h) != 2 or
                        not all(isinstance(v, int) for v in h)):
                    errs.append('grid.hot entries must be [row, col] integers')
                elif isinstance(cols, list) and isinstance(rows, list) and (
                        not 0 <= h[0] < len(rows) or not 0 <= h[1] < len(cols)):
                    errs.append('grid.hot %r is outside the grid' % (h,))
    elif kind == 'ring':
        nodes = spec.get('nodes')
        if not isinstance(nodes, list) or not 3 <= len(nodes) <= 8:
            errs.append('ring.nodes must be a list of 3..8 labels')
        else:
            for i, nd in enumerate(nodes):
                _pair(nd, 'ring.nodes[%d]' % i, errs, 22)
        if spec.get('center_fa') or spec.get('center_en'):
            _pair({'fa': spec.get('center_fa', ''), 'en': spec.get('center_en', '')},
                  'ring.center', errs, 18)
    elif kind == 'quorum':
        nodes = spec.get('nodes')
        if not isinstance(nodes, list) or not 3 <= len(nodes) <= 5:
            errs.append('quorum.nodes must be a list of 3..5 labels')
            n = 3
        else:
            n = len(nodes)
            for i, nd in enumerate(nodes):
                _pair(nd, 'quorum.nodes[%d]' % i, errs, 12)
        for side in ('write', 'read'):
            p = spec.get(side)
            if not isinstance(p, dict):
                errs.append('quorum.%s must be an object' % side)
                continue
            _pair({'fa': p.get('label_fa', ''), 'en': p.get('label_en', '')},
                  'quorum.%s.label' % side, errs, 24)
            idx = p.get('index')
            if not isinstance(idx, list) or not idx:
                errs.append('quorum.%s.index must be a non-empty list' % side)
            else:
                for v in idx:
                    if not isinstance(v, int) or not 0 <= v < n:
                        errs.append('quorum.%s.index %r is out of range' % (side, v))
    elif kind == 'bars':
        items = spec.get('items')
        if not isinstance(items, list) or not 3 <= len(items) <= 6:
            errs.append('bars.items must be a list of 3..6 bars')
        else:
            for i, it in enumerate(items):
                _pair(it, 'bars.items[%d]' % i, errs, 20)
                if not isinstance(it, dict):
                    continue
                if not str(it.get('v', '')).strip():
                    errs.append('bars.items[%d].v is required' % i)
                try:
                    float(it.get('p'))
                except (TypeError, ValueError):
                    errs.append('bars.items[%d].p must be a number 0..100' % i)
    return errs


# ───────────────────────────────── rendering ───────────────────────────────

def render(spec, uid, lang_pairs=True):
    """Full <figure> markup: caption, the svg, and a per-figure marker definition."""
    h, parts = RENDER[spec['kind']](spec)
    head = ('<svg class="fig-svg" viewBox="0 0 %d %d" role="img" preserveAspectRatio="xMidYMid meet" '
            'aria-label="%s">' % (W, int(h), _q(str(spec.get('cap_en', '')))))
    defs = ('<defs><marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto-start-reverse"><path class="fig-head" d="M0 0 L10 5 L0 10 z"/>'
            '</marker></defs>' % uid)
    parts = [p.replace('#fig-head', '#' + uid) for p in parts]
    cap = ('<figcaption>%s</figcaption>'
           % _bi({'fa': spec.get('cap_fa', ''), 'en': spec.get('cap_en', '')}))
    return ('<figure class="gl-fig" data-fig="%s">%s%s%s</svg>%s</figure>'
            % (spec['kind'], head, defs, ''.join(parts), cap))
