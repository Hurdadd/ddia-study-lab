#!/usr/bin/env python3
"""Bake the GitHub star count into the site, the README badge and the star chart.

The study site is a static export with no backend, so nothing here runs on a
visitor's request: the count is fetched once when the page is built, written to
``assets/stars.json``, drawn into ``assets/badges/stars.svg`` and stamped into
every ``[data-star-count]`` slot. The same read also collects each stargazer's
``starred_at`` timestamp, which draws ``assets/star-history.svg`` for the README
(see ``star_history.py``). In the browser ``assets/stars.js`` re-reads the JSON
from the same origin, which keeps the number fresh between deployments without a
third-party request or an API token in the page.

The count and the chart share one source: when the stargazer list is available
the number is that list's length, so the badge, the pill and the chart cannot
disagree. ``stargazers_count`` only fills in when the list itself is unavailable.

Usage:
  python3 assets/build_stars.py             # fetch, then write JSON, badge, chart, pages
  python3 assets/build_stars.py --offline   # reuse the cached JSON and redraw
  python3 assets/build_stars.py --check     # validate the cache, do not write
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import star_history  # noqa: E402  (sibling module, resolved from this file)

DATA = ROOT / 'assets' / 'stars.json'
BADGE = ROOT / 'assets' / 'badges' / 'stars.svg'
PAGES = (ROOT / 'index.html', ROOT / 'exercise-audit.html')
DEFAULT_REPO = 'Hurdadd/ddia-study-lab'
STALE_AFTER = timedelta(days=14)

LABEL = 'STARS'
LABEL_BG = '#302828'
VALUE_BG = '#b07d00'  # star gold, distinct from the amber status badge

# Verdana bold at Shields' 10px for-the-badge size, with their 1.2px tracking.
# Close enough to Shields' own measurement to sit beside the vendored badges.
GLYPHS = {
    '0': 7.3, '1': 7.3, '2': 7.3, '3': 7.3, '4': 7.3, '5': 7.3, '6': 7.3, '7': 7.3,
    '8': 7.3, '9': 7.3, 'A': 7.5, 'B': 7.6, 'C': 7.6, 'D': 8.2, 'E': 7.0, 'F': 6.5,
    'G': 8.4, 'H': 8.4, 'I': 4.5, 'J': 5.6, 'K': 7.6, 'L': 6.4, 'M': 9.6, 'N': 8.3,
    'O': 8.6, 'P': 7.5, 'Q': 8.6, 'R': 7.9, 'S': 7.4, 'T': 6.9, 'U': 8.1, 'V': 7.6,
    'W': 11.1, 'X': 7.6, 'Y': 7.3, 'Z': 7.0, ' ': 4.0, '-': 5.0, '.': 4.0, '|': 4.0,
}
TRACKING = 1.2
PADDING = 10.0  # per side, matching the other for-the-badge SVGs


def format_count(stars: int) -> str:
    """Shields-style compact value: 987, then 1.2k."""
    if stars < 1000:
        return str(stars)
    return f'{stars / 1000:.1f}k'.replace('.0k', 'k')


def text_width(text: str) -> float:
    return sum(GLYPHS.get(ch, 8.2) for ch in text.upper()) + TRACKING * len(text)


def render_badge(stars: int, repo: str) -> str:
    value = format_count(stars)
    label_w = round(text_width(LABEL) + PADDING * 2, 2)
    value_w = round(text_width(value) + PADDING * 2, 2)
    total = round(label_w + value_w, 2)
    aria = f'{LABEL}: {value}'
    label_text = round((label_w - PADDING * 2) * 10)
    value_text = round((value_w - PADDING * 2) * 10)
    label_x = round(label_w * 10 / 2, 1)
    value_x = round((label_w + value_w / 2) * 10, 1)
    return (
        f'<!-- Rendered by assets/build_stars.py for {repo}: '
        f'run it again to refresh the number. No runtime request is made. -->\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="28" role="img" '
        f'aria-label="{aria}"><title>{aria}</title><g shape-rendering="crispEdges">'
        f'<rect width="{label_w}" height="28" fill="{LABEL_BG}"/>'
        f'<rect x="{label_w}" width="{value_w}" height="28" fill="{VALUE_BG}"/></g>'
        f'<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" '
        f'text-rendering="geometricPrecision" font-size="100">'
        f'<text transform="scale(.1)" x="{label_x}" y="175" textLength="{label_text}">{LABEL}</text>'
        f'<text transform="scale(.1)" x="{value_x}" y="175" textLength="{value_text}" '
        f'font-weight="bold">{value}</text></g></svg>\n'
    )


def fetch_gh(repo: str) -> dict:
    out = subprocess.run(
        ['gh', 'api', f'repos/{repo}', '--jq',
         '{stars:.stargazers_count,forks:.forks_count,url:.html_url}'],
        capture_output=True, text=True, check=True, timeout=30,
    ).stdout
    return json.loads(out)


def fetch_api(repo: str) -> dict:
    request = urllib.request.Request(
        f'https://api.github.com/repos/{repo}',
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'ddia-study-lab-build'},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = json.loads(response.read().decode('utf-8'))
    return {
        'stars': body['stargazers_count'],
        'forks': body['forks_count'],
        'url': body['html_url'],
    }


def read_cached() -> dict:
    if not DATA.exists():
        raise SystemExit(f'{DATA.relative_to(ROOT)} is missing; run without --offline first')
    return json.loads(DATA.read_text(encoding='utf-8'))


def collect(repo: str, offline: bool) -> dict:
    if offline:
        return {**read_cached(), 'repo': repo, 'source': 'cache'}
    try:
        live = fetch_gh(repo)
        source = 'gh'
    except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError) as error:
        print(f'gh api failed ({error.__class__.__name__}); trying the public API', file=sys.stderr)
        try:
            live, source = fetch_api(repo), 'api'
        except urllib.error.URLError as fallback_error:
            raise SystemExit(f'Could not read {repo}: {error}; {fallback_error}') from fallback_error
    live['stars'] = int(live['stars'])
    live['forks'] = int(live['forks'])
    return {
        'repo': repo,
        'url': live.get('url', f'https://github.com/{repo}'),
        'stars': live['stars'],
        'forks': live['forks'],
        'source': source,
        'updated': datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
    }


def write_data(record: dict) -> None:
    # Same rule as the chart: keep the file byte-identical when nothing moved, so a
    # scheduled run only commits a real change.
    if DATA.exists():
        try:
            old = json.loads(DATA.read_text(encoding='utf-8'))
            if all(old.get(key) == record.get(key) for key in ('repo', 'stars', 'forks')):
                return
        except json.JSONDecodeError:
            pass
    DATA.write_text(json.dumps(record, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def write_badge(record: dict) -> None:
    BADGE.parent.mkdir(parents=True, exist_ok=True)
    BADGE.write_text(render_badge(record['stars'], record['repo']), encoding='utf-8')



def refresh_history(repo: str, offline: bool) -> list[str]:
    """Collect stargazer timestamps and redraw the README chart."""
    if offline:
        dates = star_history.read_history()
    else:
        try:
            dates = star_history.fetch_stars(repo)
        except Exception as error:  # network, auth or rate limit: keep what we have
            print(f'stargazer list unavailable ({error.__class__.__name__}); '
                  'keeping the cached chart', file=sys.stderr)
            dates = star_history.read_history()
        if dates:
            star_history.write_history(dates, repo)
    if dates:
        star_history.write_chart(dates, repo)
    return dates


def patch_pages(stars: int) -> list[str]:
    slot = re.compile(r'(<span[^>]*\bdata-star-count\b[^>]*>)([^<]*)(</span>)')
    touched = []
    for page in PAGES:
        if not page.exists():
            continue
        html = page.read_text(encoding='utf-8')
        updated, count = slot.subn(lambda m: f'{m.group(1)}{stars}{m.group(3)}', html)
        if count and updated != html:
            page.write_text(updated, encoding='utf-8')
        touched.append(f'{page.relative_to(ROOT).as_posix()} ({count})')
    return touched


def check() -> int:
    try:
        record = read_cached()
    except (SystemExit, json.JSONDecodeError) as error:
        print(f'FAIL stars.json is not readable: {error}', file=sys.stderr)
        return 1
    problems = []
    if not isinstance(record.get('stars'), int):
        problems.append('stars is not an integer')
    if BADGE.exists():
        badge = BADGE.read_text(encoding='utf-8')
        expected = format_count(record['stars'])
        if f'>{expected}</text>' not in badge:
            problems.append(f'badge value is not {expected}; rerun build_stars.py')
    else:
        problems.append('assets/badges/stars.svg is missing')
    updated = record.get('updated')
    try:
        stamp = datetime.fromisoformat(updated.replace('Z', '+00:00'))
        age = datetime.now(timezone.utc) - stamp
        if age > STALE_AFTER:
            problems.append(f'count is {age.days} days old; refresh it')
    except (AttributeError, ValueError):
        problems.append('updated is not an ISO timestamp')
    dates = star_history.read_history()
    if dates and len(dates) != record.get('stars'):
        problems.append(f'the chart has {len(dates)} stars but the badge has {record.get("stars")}')
    if dates and not star_history.CHART.exists():
        problems.append('assets/star-history.svg is missing; rerun build_stars.py')
    elif dates:
        chart = star_history.CHART.read_text(encoding='utf-8')
        if f'>{record["stars"]}</text>' not in chart:
            problems.append(f'the chart does not print {record["stars"]}')
    for page in PAGES:
        if page.exists() and 'data-star-count' not in page.read_text(encoding='utf-8'):
            problems.append(f'{page.name} lost its star slot')
    if problems:
        for problem in problems:
            print(f'FAIL {problem}', file=sys.stderr)
        return 1
    print(f'OK {record["repo"]}: {record["stars"]} stars ({record.get("source")}, {updated})')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default=None, help=f'default {DEFAULT_REPO}')
    parser.add_argument('--offline', action='store_true', help='reuse the cached count')
    parser.add_argument('--check', action='store_true', help='validate, write nothing')
    parser.add_argument('--print', dest='print_only', action='store_true', help='print the count only')
    args = parser.parse_args()

    if args.check:
        return check()

    repo = args.repo or (read_cached().get('repo') if DATA.exists() else None) or DEFAULT_REPO
    record = collect(repo, args.offline)
    if args.print_only:
        print(record['stars'])
        return 0
    dates = refresh_history(repo, args.offline)
    if dates:
        record['stars'] = len(dates)
    # A zero usually means the fetch was rate-limited or misrouted; never ship it.
    if record['stars'] <= 0 and DATA.exists():
        cached = read_cached()
        print(f'Kept the cached count ({cached.get("stars")}) because the live read returned 0', file=sys.stderr)
        record = {**cached, 'repo': repo}
    write_data(record)
    write_badge(record)
    pages = patch_pages(record['stars'])
    print(f'{record["repo"]}: {record["stars"]} stars, {record["forks"]} forks '
          f'({record["source"]}, {record["updated"]})')
    print('wrote assets/stars.json, assets/badges/stars.svg, assets/star-history.svg; '
          'slots ' + ', '.join(pages))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
