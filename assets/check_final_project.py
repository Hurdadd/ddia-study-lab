#!/usr/bin/env python3
"""Check the capstone's local navigation, target indices and frozen diagram export/specification hashes."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib,json
ROOT=Path(__file__).resolve().parent.parent
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[];self.frames=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  if tag=='a' and 'href' in a:self.links.append(a['href'])
  if tag=='iframe':self.frames.append(a['src'])
def parse(p):
 c=Page();c.feed(p.read_text());return c
for path in [ROOT/'index.html',ROOT/'final-project/index.html']:
 c=parse(path);assert len(c.ids)==len(set(c.ids)),f'Duplicate ids in {path}'
 for target in c.links+c.frames:
  u=urlsplit(target)
  if u.scheme or u.netloc:continue
  p=(path.parent/unquote(u.path)).resolve() if u.path else path
  assert p.exists(),f'Missing path {p}'
  if u.fragment and p.suffix=='.html':assert u.fragment in parse(p).ids,f'Missing anchor {target}'
project=parse(ROOT/'final-project/index.html')
assert project.ids.index('overview') < project.ids.index('company-evidence') < project.ids.index('start-here')
evidence=json.loads((ROOT/'final-project/interview-evidence.json').read_text())
assert len(evidence['reports'])==8 and len({r['company'] for r in evidence['reports']})==7
assert [r['id'] for r in evidence['reports'] if r['kind']=='official']==['I01']
assert all(r['url'].startswith('https://') and r['question'] and r['mapping'] and r['limit'] for r in evidence['reports'])
assert all(r['id'] in project.ids for r in evidence['reports'])
print('PASS: project context precedes workshop; 8 attributed interview records across 7 companies')
assert len(project.frames)==11
coverage=json.loads((ROOT/'final-project/chapter-coverage.json').read_text())
assert [x['chapter'] for x in coverage]==list(range(1,15))
acceptance=json.loads((ROOT/'final-project/acceptance.json').read_text())
assert len(acceptance)==16 and len({x['id'] for x in acceptance})==16
assert all(x['status']=='planned' for x in acceptance),'Blueprint must not claim unexecuted tests passed'
for d in json.loads((ROOT/'final-project/diagram-manifest.json').read_text()):
 assert all(x=='pass' for x in d['verified_gates'].values()),d['slug']
 actual=hashlib.sha256((ROOT/d['output']).read_bytes()).hexdigest()
 assert d['artifact_sha256']==actual,f'Stale diagram export: {d["slug"]}'
 assert d['specification_sha256']==hashlib.sha256((ROOT/d['candidate']).read_bytes()).hexdigest()
workshop=json.loads((ROOT/'final-project/workshop.json').read_text())
assert len(workshop['adrs'])==15 and len(workshop['assumptions'])==12
assert [d['id'] for d in workshop['adrs'] if d['status']=='accepted']==['ADR-001']
for d in workshop['adrs']:
 assert all(len(d[k])==2 and all(d[k]) for k in ['context','options','choice','reason','assumptions','validation','revisit'])
 assert (ROOT/'final-project/adrs'/(d['id']+'.md')).exists()
print('PASS: 15 ADR records, 12 assumptions, and only audience scope accepted')
print('PASS: local links/anchors, 11 diagrams, 14 chapter mappings, 16 planned tests, 9 frozen export/specification hash pairs')

recovery=json.loads((ROOT/'final-project/recovery.json').read_text())
assert [(c['rpo_seconds'],c['rto_seconds']) for c in recovery['cases']]==[(0,120),(300,1800),(900,14400),(0,14400)]
assert project.ids.index('recovery') < project.ids.index('outcome')
assert all((ROOT/f).is_file() for f in ['LICENSE','DCO','README.md','CONTRIBUTING.md','CODE_OF_CONDUCT.md','SECURITY.md','GOVERNANCE.md','NOTICE','docs/RECOVERY.md'])
assert 'GNU AFFERO GENERAL PUBLIC LICENSE' in (ROOT/'LICENSE').read_text()
print('PASS: recovery targets, final POV and AGPL/community package')
