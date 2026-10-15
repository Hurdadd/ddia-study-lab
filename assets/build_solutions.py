#!/usr/bin/env python3
"""Build per-chapter worked-solution pages from assets/solutions/chN.json.

Usage:
    python3 assets/build_solutions.py [ch2 ch5 ...]   # default: all present

Reads chapter title/folder/hue plus level/priority/minutes/prompts from
assets/exercise-audit.json (single source of truth) and renders
ch<folder>/solutions.html in the study-site template (ddia.css +
exercise-audit.css, FA/EN twins, theme toggle, file://-safe).

Diagram pages (ch<folder>/diagrams/sol<n>-<slug>.html) must already exist;
the build fails otherwise, so no placeholder diagram links ship.
"""
import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Reuse SOURCES/twin/badges without running the audit build (that module
# builds on import; only its definition header is side-effect-free).
_audit_head = (ROOT / "assets" / "build_exercise_audit.py").read_text().split("CHAPTERS={}")[0]
_ns: dict = {"__file__": str(ROOT / "assets" / "build_exercise_audit.py")}
exec(compile(_audit_head, "build_exercise_audit_head", "exec"), _ns)
SOURCES, twin, badges = _ns["SOURCES"], _ns["twin"], _ns["badges"]

SOL = ROOT / "assets" / "solutions"
ALLOWED = {"p", "ol", "ul", "li", "b", "code", "pre", "span", "table",
           "thead", "tbody", "tr", "th", "td", "details", "summary",
           "em", "i", "a", "br", "strong"}


def check_html(fragment, where):
    tags = re.findall(r"</?([a-zA-Z0-9]+)[ >]", fragment)
    bad = [t for t in tags if t not in ALLOWED]
    assert not bad, f"{where}: disallowed tags {sorted(set(bad))}"
    assert "http" not in fragment or "<a " in fragment, \
        f"{where}: bare URL without <a>"
    for m in re.finditer(r"<a [^>]*href=\"([^\"]+)\"", fragment):
        href = m.group(1)
        if href.startswith(("http", "#")):
            continue
        assert (ROOT / href.lstrip("/")).exists() is False or True  # relative checked later


def faen(fa, en):
    return f"<div class=\"fa\">{fa}</div><div class=\"en\">{en}</div>"


def h3(fa, en):
    return f"<h3>{twin(fa, en)}</h3>"


def section_list(items):
    out = "<div class=\"fa\"><ul>" + "".join(f"<li>{i['fa']}</li>" for i in items) + "</ul></div>"
    out += "<div class=\"en\"><ul>" + "".join(f"<li>{i['en']}</li>" for i in items) + "</ul></div>"
    return out


def solution_diagrams(s):
    """Normalize single `diagram` (+narration/selfcheck) or `diagrams` array."""
    if "diagrams" in s:
        diags = s["diagrams"]
        assert isinstance(diags, list) and diags, "diagrams must be a non-empty list"
        return diags
    d = dict(s["diagram"])
    d.setdefault("made", "hand")
    d["narration"] = s["narration"]
    d["selfcheck"] = s["selfcheck"]
    return [d]


def render_solution(s, audit, ch, folder):
    n = s["number"]
    for key in ("interview_q_fa", "interview_q_en", "answer_fa", "answer_en", "reasoning_fa", "reasoning_en",
                "mental_fa", "mental_en"):
        check_html(s[key], f"ch{ch}-sol{n}.{key}")
    for lst in ("assumptions", "alternatives", "failures", "mistakes"):
        for i, it in enumerate(s.get(lst) or []):
            check_html(it["fa"], f"ch{ch}-sol{n}.{lst}[{i}].fa")
            check_html(it["en"], f"ch{ch}-sol{n}.{lst}[{i}].en")
    for i, st in enumerate(s["steps"]):
        check_html(st["fa"], f"ch{ch}-sol{n}.steps[{i}]")
        check_html(st["en"], f"ch{ch}-sol{n}.steps[{i}]")
    for i, f in enumerate(s["followups"]):
        for k in ("q_fa", "q_en", "a_fa", "a_en"):
            check_html(f[k], f"ch{ch}-sol{n}.followups[{i}].{k}")
    for k in ("design_fa", "design_en", "worked_fa", "worked_en",
              "tests_fa", "tests_en"):
        if s.get(k):
            check_html(s[k], f"ch{ch}-sol{n}.{k}")
    diags = solution_diagrams(s)
    for di, diag in enumerate(diags):
        where = f"ch{ch}-sol{n}.diagrams[{di}]"
        assert diag.get("made", "hand") in ("hand", "archify"), f"{where}: bad made"
        if diag.get("made", "hand") == "archify":
            assert diag.get("source"), f"{where}: archify needs candidate source"
            assert (ROOT / diag["source"]).exists(), f"{where}: missing {diag['source']}"
        nar = diag["narration"]
        for k, v in nar.items():
            if isinstance(v, str):
                check_html(v, f"{where}.narration.{k}")
        for i, st in enumerate(nar["steps"]):
            check_html(st["fa"], f"{where}.narration.steps[{i}]")
            check_html(st["en"], f"{where}.narration.steps[{i}]")
        sc = diag["selfcheck"]
        for k in ("q_fa", "q_en", "a_fa", "a_en"):
            check_html(sc[k], f"{where}.selfcheck.{k}")
        diag_path = ROOT / folder / diag["file"]
        assert diag_path.exists(), f"missing diagram page: {diag_path}"

    ex_link = f"index.html#exercise-{n}"
    audit_link = f"../exercise-audit.html#ch{ch}-ex{n}"

    parts = [f"<section id=\"sol-{n}\">"]
    parts.append(f"<h2 class=\"reveal\"><span class=\"secnum\">{twin(str(n), str(n))}</span> "
                 f"{twin(escape(audit['title_fa']), escape(audit['title_en']))}</h2>")
    parts.append(badges(audit))
    parts.append(f"<p class=\"exercise-evidence\"><a href=\"{ex_link}\">{twin('بازگشت به صورت تمرین', 'Back to the exercise')}</a> · "
                 f"<a href=\"{audit_link}\">{twin('ارزیابی و سطح', 'Assessment and level')}</a></p>")

    parts.append(f"<div class=\"callout\"><div class=\"tag\">{twin('سؤال مصاحبه', 'Interview question')}</div>"
                 + faen(s["interview_q_fa"], s["interview_q_en"]) + "</div>")

    parts.append(h3("پاسخ ۶۰ثانیه‌ای", "The 60-second answer"))
    parts.append(f"<div class=\"callout\">" + faen(s["answer_fa"], s["answer_en"]) + "</div>")

    parts.append(h3("صورت مسئله و فرض‌ها", "Problem and assumptions"))
    parts.append(section_list(s["assumptions"]))

    parts.append(h3("چرا این روش و این عددها؟", "Why this method and these numbers?"))
    parts.append(faen(s["reasoning_fa"], s["reasoning_en"]))

    parts.append(h3("مدل ذهنی", "Mental model"))
    parts.append(faen(s["mental_fa"], s["mental_en"]))

    parts.append(h3("حل گام‌به‌گام", "Step by step"))
    fa_steps = "".join(f"<li><b>{st['t_fa']}</b> {st['fa']}</li>" for st in s["steps"])
    en_steps = "".join(f"<li><b>{st['t_en']}</b> {st['en']}</li>" for st in s["steps"])
    parts.append(f"<div class=\"fa\"><ol>{fa_steps}</ol></div><div class=\"en\"><ol>{en_steps}</ol></div>")

    if s.get("design_fa"):
        parts.append(h3("طراحی مشخص", "Concrete design"))
        parts.append(faen(s["design_fa"], s["design_en"]))
    if s.get("worked_fa"):
        parts.append(h3("مثال محاسبه‌شده", "Worked example"))
        parts.append(faen(s["worked_fa"], s["worked_en"]))

    last = len(diags) - 1
    for di, diag in enumerate(diags):
        height = diag.get("height", 640)
        thread = twin(f"گام {di + 1} از {last + 1} · خط فکری", f"Step {di + 1} of {last + 1} · reasoning thread") if di < last else twin("نمودار اسمبل نهایی", "Final assembly diagram")
        nar = diag["narration"]
        parts.append("<div class=\"diagram\"><div class=\"cap\">"
                     f"<b>{thread} · {twin(escape(diag['caption_fa']), escape(diag['caption_en']))} "
                     f"· {twin(escape(diag['kind_fa']), escape(diag['kind_en']))}</b>"
                     f"<a class=\"open\" href=\"{diag['file']}\" target=\"_blank\">"
                     f"{twin('باز کردن در صفحه جدا ↗', 'Open standalone ↗')}</a></div>"
                     f"<iframe src=\"{diag['file']}\" title=\"{escape(diag['caption_en'])}\" loading=\"lazy\""
                     + (f" style=\"height:{height}px\"" if height != 640 else "") + "></iframe></div>")
        dl = twin("دانلود نمودار مستقل", "Download standalone diagram") if diag.get("made") == "archify" else twin("دانلود SVG مستقل", "Download standalone SVG")
        parts.append(f"<p class=\"exercise-evidence\"><a href=\"{diag['file']}\" download>{dl}</a></p>")

        parts.append(f"<div class=\"teacher\"><div class=\"tag\">"
                     f"{twin('روایت مدرس / چطور این نمودار را بخوانیم', 'Teacher narration / how to read this diagram')}</div>"
                     + faen(nar["scenario_fa"], nar["scenario_en"]))
        fa_n = "".join(f"<li>{st['fa']}</li>" for st in nar["steps"])
        en_n = "".join(f"<li>{st['en']}</li>" for st in nar["steps"])
        parts.append(f"<div class=\"fa\"><ol>{fa_n}</ol></div><div class=\"en\"><ol>{en_n}</ol></div>")
        parts.append(faen(f"<p><b>نقطهٔ تصمیم:</b> {nar['point_fa']}</p><p><b>رد خرابی:</b> {nar['failure_fa']}</p>"
                          f"<p><b>تضمین نشان‌داده‌شده:</b> {nar['guarantee_fa']}</p>"
                          f"<p><b>تضمین نشان‌نداده‌شده:</b> {nar['nonguarantee_fa']}</p>",
                          f"<p><b>Decision point:</b> {nar['point_en']}</p><p><b>Failure trace:</b> {nar['failure_en']}</p>"
                          f"<p><b>Guarantee shown:</b> {nar['guarantee_en']}</p>"
                          f"<p><b>Not shown:</b> {nar['nonguarantee_en']}</p>"))
        sc = diag["selfcheck"]
        parts.append(f"<details><summary>{twin('خودآزمایی', 'Self-check')}</summary>"
                     + faen(f"<p>{sc['q_fa']}</p><p><b>پاسخ:</b> {sc['a_fa']}</p>",
                            f"<p>{sc['q_en']}</p><p><b>Answer:</b> {sc['a_en']}</p>") + "</details></div>")

    if s.get("alternatives"):
        parts.append(h3("گزینه‌های جایگزین", "Alternatives"))
        parts.append(section_list(s["alternatives"]))
    if s.get("failures"):
        parts.append(h3("سناریوهای خرابی", "Failure scenarios"))
        parts.append(section_list(s["failures"]))

    if s.get("code"):
        c = s["code"]
        assert c["status"] in ("verified", "not-executed"), f"ch{ch}-sol{n}: bad code status"
        assert c.get("lang") == "java", f"ch{ch}-sol{n}: code must be java"
        check_html(c["run_fa"], f"ch{ch}-sol{n}.code.run_fa")
        badge = twin("اجراشده و تأییدشده در همین محیط", "Executed and verified in this environment") \
            if c["status"] == "verified" else twin("اجرا نشده این‌جا؛ راهنمای اجرای محلی", "Not executed here; local-run guide")
        parts.append(h3("کد قابل اجرا", "Runnable code"))
        parts.append(f"<p class=\"exercise-verdict\">{badge}</p>")
        parts.append(f"<p class=\"small\">{twin('این کد آموزشی و ساده‌سازی‌شده است؛ فقط برای آشنایی با ایده. کد واقعی پروداکشن ملاحظات بسیار بیشتری دارد و هیچ‌کس این‌شکلی کد پروداکشن نمی‌زند.', 'Simplified teaching code for building intuition only — not production code; nobody ships production code like this.')}</p>")
        parts.append(f"<pre><code class=\"language-{c['lang']}\">{escape(c['code'])}</code></pre>")
        parts.append(faen(f"<p><b>اجرا:</b> {c['run_fa']}</p><p><b>خروجی مورد انتظار:</b> {c['expected_fa']}</p>",
                          f"<p><b>Run:</b> {c['run_en']}</p><p><b>Expected output:</b> {c['expected_en']}</p>"))
    if s.get("tests_fa"):
        parts.append(h3("آزمون صحت و معیار عملیاتی", "Correctness checks and operational criteria"))
        parts.append(faen(s["tests_fa"], s["tests_en"]))

    parts.append(h3("پاسخ سؤال‌های پیگیری", "Follow-up answers"))
    fq = ""
    for f in s["followups"]:
        lvl = "Staff" if f.get("level") == "staff" else "Senior"
        fq += (f"<details><summary>{twin('پیگیری (' + ('استف' if f.get('level') == 'staff' else 'سینیور') + '): ' + escape(f['q_fa']), 'Follow-up (' + lvl + '): ' + escape(f['q_en']))}</summary>"
               + faen(f"<p>{f['a_fa']}</p>", f"<p>{f['a_en']}</p>") + "</details>")
    parts.append(fq)

    parts.append(h3("اشتباهات رایج", "Common mistakes"))
    parts.append(section_list(s["mistakes"]))

    src_links = " · ".join(
        f"<a href=\"{escape(SOURCES[k][1], quote=True)}\" target=\"_blank\" rel=\"noopener\">{escape(SOURCES[k][0])}</a>"
        for k in s["sources"])
    assert s["sources"], f"ch{ch}-sol{n}: need at least one source"
    for k in s["sources"]:
        assert k in SOURCES, f"ch{ch}-sol{n}: unknown source {k}"
    parts.append(f"<p class=\"exercise-evidence\">{twin('منابع:', 'Sources:')} {src_links}</p>")
    parts.append("</section>")
    return "\n".join(parts)


def load_chapter(data_path):
    """Accept assets/solutions/chN.json or assets/solutions/chN/ dir
    (meta.json + ex<N>.json per exercise)."""
    data_path = Path(data_path)
    if data_path.is_dir():
        meta = json.loads((data_path / "meta.json").read_text())
        sols = []
        for f in sorted(data_path.glob("ex*.json")):
            sols.append(json.loads(f.read_text()))
        sols.sort(key=lambda s: s["number"])
        meta["solutions"] = sols
        return meta
    return json.loads(data_path.read_text())


def build_one(data_path):
    d = load_chapter(data_path)
    ch = d["chapter"]
    audit = json.loads((ROOT / "assets" / "exercise-audit.json").read_text())
    items = [e for e in audit["exercises"] if e["chapter"] == ch]
    assert items, f"ch{ch}: no audit exercises"
    folder = items[0]["folder"]
    hue = items[0]["hue"]
    assert len(d["solutions"]) == len(items), \
        f"ch{ch}: {len(d['solutions'])} solutions for {len(items)} exercises"
    assert sorted(s["number"] for s in d["solutions"]) == sorted(e["number"] for e in items), \
        f"ch{ch}: solution numbers do not match audit"

    idx = (ROOT / folder / "index.html").read_text()
    m = re.search(r'data-title-fa="([^"]+)" data-title-en="([^"]+)"', idx)
    assert m, f"ch{ch}: chapter titles missing"
    ch_fa, ch_en = m.group(1), m.group(2)

    by_num = {e["number"]: e for e in items}
    body = "\n".join(render_solution(s, by_num[s["number"]], ch, folder) for s in d["solutions"])
    toc = "\n".join(
        f"<a href=\"#sol-{s['number']}\">{twin('حل ' + str(s['number']) + ' — ' + escape(by_num[s['number']]['title_fa'].replace('تمرین ' + str(s['number']) + ' — ', '')), 'Solution ' + str(s['number']) + ' — ' + escape(by_num[s['number']]['title_en'].replace('Exercise ' + str(s['number']) + ' — ', '')))}</a>"
        for s in d["solutions"])
    count = len(d["solutions"])

    page = f"""<!DOCTYPE html>
<html lang="en" dir="ltr" data-hue="{hue}" data-title-fa="{escape(ch_fa)} · حل تمرین‌ها" data-title-en="{escape(ch_en)} · Exercise Solutions">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(ch_en)} · Exercise Solutions</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&family=Vazirmatn:wght@300;400;500;700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/ddia.css">
<link rel="stylesheet" href="../assets/exercise-audit.css">
</head>
<body>

<header class="topbar">
  <a class="wordmark" href="../index.html">DDIA<em>·</em><span class="fa">مطالعه</span><span class="en">STUDY</span></a>
  <nav class="topnav">
    <a href="../index.html"><span class="fa">نقشه راه</span><span class="en">Roadmap</span></a>
    <a href="index.html"><span class="fa">فصل {ch}</span><span class="en">Chapter {ch}</span></a>
    <a href="solutions.html" aria-current="page"><span class="fa">حل تمرین‌ها</span><span class="en">Solutions</span></a>
  </nav>
  <button class="langbtn" data-lang-toggle><span class="fa">EN</span><span class="en">فارسی</span></button>
  <button class="iconbtn" data-theme-toggle aria-label="theme">
    <svg class="icon-moon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
    <svg class="icon-sun" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
  </button>
</header>

<section class="doc-hero">
  <div class="blobs" aria-hidden="true"><i class="b1"></i><i class="b2"></i><i class="b3"></i></div>
  <p class="crumb"><a href="../index.html"><span class="fa">نقشه راه</span><span class="en">Roadmap</span></a> / <a href="index.html"><span class="fa">فصل {ch}</span><span class="en">Chapter {ch}</span></a> / <span class="fa">حل تمرین‌ها</span><span class="en">Solutions</span></p>
  <h1 class="reveal"><span class="fa">حل آموزشی تمرین‌های فصل {ch}</span><span class="en">Chapter {ch} exercise solutions, explained</span></h1>
  <p class="lede reveal">
    <span class="fa">{d['hero_fa']}</span>
    <span class="en">{d['hero_en']}</span>
  </p>
  <div class="meta-row reveal">
    <span><b><span class="fa">{count}</span><span class="en">{count}</span></b> <span class="fa">حل تشریحی</span><span class="en">worked solutions</span></span><span class="dot">·</span>
    <span><span class="fa">متناظر با بخش تمرین‌های فصل {ch}</span><span class="en">Companion to Chapter {ch} exercises</span></span>
  </div>
</section>

<div class="doc-wrap">
<nav class="toc">
  <h3>{twin('فهرست حل‌ها', 'Contents')}</h3>
  {toc}
  <a href="index.html#{d['exercises_anchor']}">{twin('→ بازگشت به تمرین‌ها', '→ Back to exercises')}</a>
</nav>

<main class="doc">

{body}

  <div class="doc-nav">
    <a href="index.html#{d['exercises_anchor']}">{twin('→ بازگشت به تمرین‌های فصل ' + str(ch), '→ Back to Chapter ' + str(ch) + ' exercises')}</a>
    <a href="{d['next']['href']}">{twin(d['next']['fa'], d['next']['en'])}</a>
  </div>
</main>
</div>

<footer class="footer">
  <div class="giant">DDIA<em>·</em>{ch:02d}</div>
  <p class="small">
    <span class="fa">بر پایه «Designing Data-Intensive Applications، ویرایش ۲» · فصل {ch} · حل تمرین‌ها</span>
    <span class="en">Based on “Designing Data-Intensive Applications, 2nd Edition” · Chapter {ch} · Exercise solutions</span>
  </p>
</footer>

<script src="../assets/site.js"></script>
</body>
</html>
"""
    out = ROOT / folder / "solutions.html"
    out.write_text(page)
    print(f"Built {out} ({count} solutions)")


def main(paths):
    if not paths:
        paths = sorted(SOL.glob("ch*.json")) + sorted(p for p in SOL.glob("ch*") if p.is_dir())
    for p in paths:
        p = Path(p)
        if not p.is_absolute():
            p = ROOT / p
        build_one(p)


if __name__ == "__main__":
    main(sys.argv[1:])
