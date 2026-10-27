#!/usr/bin/env python3
"""Idempotently embed the chapter experiments after their teaching sections.

Only generated marker regions and asset includes are replaced; original chapter
teaching text, frozen diagrams, solutions and exercises remain intact.
"""
import json
import re
from pathlib import Path
from html import escape
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parent.parent
# chapter: model, teaching section, English title, Persian title
LABS = {
    1: ('outbox', 's2', 'The order exists. Where is its event?', 'سفارش ثبت شد؛ رویدادش کجاست؟'),
    2: ('queue', 's2', 'A burst meets a fixed service rate', 'برخورد موج درخواست با ظرفیت محدود'),
    3: ('models', 's1', 'Rename once, or update every copy?', 'یک تغییر نام یا اصلاح همهٔ کپی‌ها؟'),
    4: ('wal', 's2', 'What survives a crash?', 'بعد از خرابی چه چیزی می‌ماند؟'),
    5: ('schema', 's3', 'An old service edits a new record', 'سرویس قدیمی یک رکورد جدید را ویرایش می‌کند'),
    6: ('replication', 's3', 'Read your own profile update', 'ویرایش پروفایلت را بخوان'),
    7: ('hotkey', 's3', 'One popular key, three shards', 'یک کلید محبوب، سه shard'),
    8: ('seat', 's3', 'Two buyers, one last seat', 'دو خریدار و آخرین صندلی'),
    9: ('retry', 's2', 'Timeout does not mean rollback', 'timeout به معنی rollback نیست'),
    10: ('quorum', 's3', 'A leader needs a majority', 'رهبر به اکثریت نیاز دارد'),
    11: ('batch', 's3', 'Retry a task without duplicating output', 'بازتلاش task بدون خروجی تکراری'),
    12: ('consumer', 's2', 'Crash between the effect and acknowledgement', 'خرابی بین اثر و تأیید پیام'),
    13: ('rebuild', 's1', 'Rebuild a projection from its source', 'بازسازی نما از مرجع داده'),
    14: ('privacy', 's6', 'Can a restore resurrect deleted data?', 'آیا restore دادهٔ حذف‌شده را برمی‌گرداند؟'),
}
# Additional labs: chapter -> [(model, teaching section, English title, Persian title)]
EXTRA = {
    1: [('olap', 's1', 'A heavy report meets checkout', 'گزارش سنگین در برابر پرداخت'),
            ('rpc', 's4', 'A call that can disappear', 'فراخوانی که می‌تواند گم شود')],
    2: [('fanout', 's1', 'One post, many followers', 'یک پست، چند دنبال‌کننده'),
            ('tail', 's2', 'The average hides the slow user', 'میانگین کاربر کند را پنهان می‌کند')],
    3: [('eventlog', 's3', 'Fix a wrong fee after the fact', 'اصلاح کارمزد اشتباه بعد از وقوع'),
            ('hops', 's2', 'Friends of friends of friends', 'دوستِ دوستِ دوست')],
    4: [('scan', 's1', 'Find the latest value of a key', 'پیدا کردن آخرین مقدار یک کلید'),
            ('btree', 's3', 'A page split meets a crash', 'شکستن صفحه و خرابی')],
    5: [('rolling', 's2', 'Add a field during a rolling upgrade', 'افزودن فیلد در حین rolling upgrade'),
            ('rename', 's3', 'Rename a field with old readers still running', 'تغییر نام فیلد وقتی خوانندهٔ قدیمی هنوز کار می‌کند')],
    7: [('rebalance', 's3', 'Add a fourth node', 'افزودن گره چهارم'),
            ('secondary', 's5', 'Search by color across shards', 'جست‌وجو بر اساس رنگ در بین شاردها')],
    8: [('dirty', 's2', 'Read a transfer that never happened', 'خواندن انتقالی که هرگز رخ نداد'),
            ('twopc', 's5', 'The coordinator dies after prepare', 'هماهنگ‌کننده بعد از prepare می‌میرد')],
    9: [('fencing', 's4', 'A paused client wakes up with an old lock', 'کلاینت متوقف‌شده با قفل قدیمی بیدار می‌شود'),
            ('timeout', 's1', 'Slow or dead?', 'کند است یا مرده؟')],
    10: [('lamport', 's2', 'Which write came later?', 'کدام نوشتن بعدتر بود؟'),
            ('ephemeral', 's4', 'The lock holder disappears', 'دارندهٔ قفل ناپدید می‌شود')],
    11: [('combiner', 's4', 'Shrink the shuffle', 'کوچک‌کردن shuffle'),
            ('rerun', 's1', 'Rerun a job whose input moved', 'اجرای دوبارهٔ کاری که ورودی‌اش تغییر کرد')],
    12: [('logbroker', 's3', 'A new consumer joins late', 'مصرف‌کنندهٔ جدید دیر می‌رسد'),
            ('ordering', 's2', 'Create then delete, seen backwards', 'ساخت و بعد حذف، معکوس دیده می‌شود')],
    13: [('unique', 's5', 'Two people claim the same username', 'دو نفر یک نام کاربری را می‌گیرند'),
            ('reconcile', 's2', 'A late event after the window closed', 'رویداد دیررسیده بعد از بسته‌شدن پنجره')],
    14: [('feedback', 's4', 'Patrols follow the data they create', 'گشت‌ها دادهٔ خودشان را می‌سازند'),
            ('proxy', 's3', 'No protected attribute, still biased', 'بدون ویژگی حفاظت‌شده هم سوگیری هست')],
    6: [
        ('failover', 's2', 'The leader dies after acknowledging a write', 'رهبر بعد از تأیید نوشتن می‌میرد'),
        ('monotonic', 's3', 'Two reads, time goes backwards', 'دو خواندن و بازگشت زمان به عقب'),
        ('leaderless', 's5', 'Do the write and read quorums overlap?', 'آیا quorum نوشتن و خواندن هم‌پوشانی دارند؟'),
    ],
}


def bi(en, fa):
    return f'<span class="en">{escape(en)}</span><span class="fa">{escape(fa)}</span>'


class Locations(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.lines = [0]
        self.lines.extend(m.end() for m in re.finditer('\n', source))
        self.sections = []
        self.ends = {}
        self.exercises = []
        self.articles = []
        self.feed(source)

    def position(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'section':
            self.sections.append(attrs.get('id'))
        if tag == 'article':
            ident = attrs.get('id') if 'exercise-block' in attrs.get('class', '').split() else None
            self.articles.append(ident)

    def handle_endtag(self, tag):
        if tag == 'section' and self.sections:
            ident = self.sections.pop()
            if ident:
                self.ends[ident] = self.position() + len('</section>')
        if tag == 'article' and self.articles:
            ident = self.articles.pop()
            if ident:
                self.exercises.append((ident, self.position()))


def clean(source):
    for name in ('concept-lab', 'concept-lab-toc', 'exercise-studio'):
        source = re.sub(rf'\n?<!-- {name}:start -->.*?<!-- {name}:end -->\n?', '', source, flags=re.S)
    return source


def build():
    audit = json.loads((ROOT / 'assets/exercise-audit.json').read_text())
    reviewed = {(entry['chapter'], entry['number']) for entry in audit['exercises']}
    counts = {'labs': 0, 'exercise_links': 0, 'reviewed_links': 0}
    for chapter, main in LABS.items():
        paths = list(ROOT.glob(f'ch{chapter}-*/index.html'))
        if len(paths) != 1:
            raise RuntimeError(f'Expected one chapter {chapter}: {paths}')
        path = paths[0]
        source = clean(path.read_text())
        locations = Locations(source)
        by_anchor = {}
        toc = ''
        for model, anchor, title_en, title_fa in [main, *EXTRA.get(chapter, [])]:
            if anchor not in locations.ends:
                raise RuntimeError(f'Missing teaching anchor {path}:{anchor}')
            by_anchor[anchor] = by_anchor.get(anchor, '') + f'''\n<!-- concept-lab:start -->
<section class="concept-lab" id="try-{model}" data-lab="{model}" data-chapter="{chapter}">
<h3>{bi(title_en, title_fa)}</h3>
<p>{bi('Try the concept here: choose an action, inspect the state, then advance one event at a time.', 'همین‌جا مفهوم را امتحان کن؛ یک کار انتخاب کن، وضعیت را ببین و رویدادها را قدم‌به‌قدم جلو ببر.')}</p>
<noscript><p>{bi('Enable JavaScript to run this local experiment.', 'برای اجرای این آزمایش محلی جاوااسکریپت را فعال کن.')}</p></noscript>
</section>
<!-- concept-lab:end -->\n'''
            toc += f'\n<!-- concept-lab-toc:start -->\n<a href="#try-{model}">{bi("Try it: "+title_en,"امتحان کن: "+title_fa)}</a>\n<!-- concept-lab-toc:end -->\n'
            counts['labs'] += 1
        insertions = [(locations.ends[a], html) for a, html in by_anchor.items()]
        for ident, position in locations.exercises:
            number_match = re.fullmatch(r'exercise-(\d+)', ident)
            number = int(number_match[1]) if number_match else None
            is_reviewed = (chapter, number) in reviewed
            query = f'exercise=ch{chapter}-ex{number}' if is_reviewed else f'chapter={chapter}'
            label = bi('Open this exercise in the studio', 'این تمرین را در استودیو باز کن') if is_reviewed else bi('Explore this chapter in the studio', 'این فصل را در استودیو آزمایش کن')
            insertions.append((position, f'\n<!-- exercise-studio:start -->\n<a class="exercise-studio-link" href="../studio/index.html?{query}">{label}<span aria-hidden="true"> →</span></a>\n<!-- exercise-studio:end -->\n'))
            counts['exercise_links'] += 1
            counts['reviewed_links'] += is_reviewed
        toc_start = source.find('<nav class="toc">')
        if toc_start >= 0:
            toc_end = source.index('</nav>', toc_start)
            insertions.append((toc_end, toc))
        for offset, content in sorted(insertions, reverse=True):
            source = source[:offset] + content + source[offset:]
        if '../assets/concept-labs.css' not in source:
            source = source.replace('</head>', '<link rel="stylesheet" href="../assets/concept-labs.css">\n</head>')
        if '../assets/concept-labs.js' not in source:
            source = source.replace('</body>', '<script src="../assets/concept-labs.js" defer></script>\n</body>')
        path.write_text(source)
    print(json.dumps(counts))


if __name__ == '__main__':
    build()
