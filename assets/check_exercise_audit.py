#!/usr/bin/env python3
"""Check the static exercise audit coverage, labels and local links."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from collections import Counter
import json
ROOT=Path(__file__).resolve().parent.parent
class Page(HTMLParser):
 def __init__(self,path):
  super().__init__();self.ids=[];self.links=[];self.reviews=[];self.items=[];self.feed(path.read_text())
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.append(a['id'])
  if a.get('data-reviewed-exercise'):self.reviews.append(a['data-reviewed-exercise'])
  if 'audit-item' in a.get('class','').split():self.items.append(a)
  if tag in {'a','link','img','script','iframe'}:
   self.links.extend(a[k] for k in ['href','src'] if k in a)
files=[ROOT/'exercise-audit.html',ROOT/'index.html',*ROOT.glob('ch*/index.html')]
parsed={p.resolve():Page(p) for p in files}
data=json.loads((ROOT/'assets/exercise-audit.json').read_text());es=data['exercises']
assert len(es)==47 and len({(e['chapter'],e['number']) for e in es})==47
assert Counter(e['priority'] for e in es)=={'core':23,'role':21,'extra':3}
assert Counter(e['level'] for e in es)=={'foundation':4,'senior':27,'staff':16}
audit=parsed[ROOT/'exercise-audit.html'];assert len(audit.items)==47
corrected=[e for e in es if e['decision']=='correct']
assert len(corrected)==16
for e in corrected:
 assert e['resolution']['status']=='resolved'
 assert e['resolution']['fa'] and e['resolution']['en']
 solution=json.loads((ROOT/f"assets/solutions/ch{e['chapter']}/ex{e['number']}.json").read_text())
 for language in ('fa','en'):
  assert solution[f'lab_{language}']==e[f'lab_{language}'], f"Lab drift: ch{e['chapter']}/ex{e['number']}"
  assert f'data-correction="ch{e["chapter"]}-ex{e["number"]}"' in (ROOT/'exercise-audit.html').read_text()
# Regression guards for the original misleading lab instructions.
unsafe=['/ap.l/', 'why can\'t this oracle be sharded?', 'the w + r &gt; n condition breaks in practice',
        'accepting only writes with a greater token', 'two machines (or two containers)',
        'without pressuring the database', 'atomic request append with an ID']
for e in corrected:
 for phrase in unsafe:
  assert phrase not in e['lab_en'], f"Unsafe premise: ch{e['chapter']}/ex{e['number']}: {phrase}"
assert '۱۶ مورد اصلاح فرض فنی یا رفع ابهام لازم دارند' not in (ROOT/'exercise-audit.html').read_text()
for e in es:
 chapter=parsed[(ROOT/e['folder']/'index.html').resolve()]
 assert f'exercise-{e["number"]}' in chapter.ids
 assert f'ch{e["chapter"]}-ex{e["number"]}' in audit.ids
 assert e['prompt'] and e['prompt_en'] and e['reason'] and e['reason_en'] and e['followup'] and e['followup_en']
 assert len(e['signals'])==len(e['signals_en'])==3
 assert len(chapter.reviews)==sum(x['chapter']==e['chapter'] for x in es)
for path,page in list(parsed.items()):
 assert len(page.ids)==len(set(page.ids)),f'Duplicate IDs: {path}'
 for link in page.links:
  url=urlsplit(link)
  if url.scheme or url.netloc:continue
  dest=(path.parent/unquote(url.path)).resolve() if url.path else path
  assert dest.exists(),f'Missing file: {path} → {link}'
  if url.fragment and dest.suffix=='.html':
   if dest not in parsed:parsed[dest]=Page(dest)
   assert unquote(url.fragment) in parsed[dest].ids,f'Missing anchor: {path} → {link}'
assert (ROOT/'exercise-audit.html').read_text().count('aria-current="page"')==1
print('PASS: 47 bilingual briefs, levels/priorities, 14 chapters, unique IDs and local links')
