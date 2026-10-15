#!/usr/bin/env python3
"""Reject internal notes, raw tool reports and private paths in publication files."""
from pathlib import Path
import json,re,subprocess,sys
ROOT=Path(__file__).resolve().parent.parent
DENY=re.compile(r"(?:^|/)(?:\.archify|\.impeccable|\.local-backups|\.stale-receipts|\.codex|\.agents|\.cursor)(?:/|$)|(?:^|/)(?:HANDOFF[^/]*|AGENTS|CLAUDE|PRODUCT|[^/]*(?:conversation|transcript|chat.history)[^/]*)\.(?:md|json)$|(?:^|/)final-project/research/|(?:^|/)docs/DEPLOYMENT\.md$|(?:^|/)assets/solutions/_schema\.md$|\.(?:browser-check|delivery|finalize|finalize-summary)\.json$",re.I)
PRIVATE_PATH=re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+/(?:Documents|Desktop|Downloads|\.codex|\.agents)/")
SECRET=re.compile(r"gh[pousr]_[A-Za-z0-9]{25,}|sk-[A-Za-z0-9]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
MARKERS=['<send_user_'+'message_question_reply>','<environment_'+'context>','You are '+'Codex','## Current '+'user request']
files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
if '--export' in sys.argv:
 files=[str(p.relative_to(ROOT)) for p in (ROOT/'public').rglob('*') if p.is_file()]
errors=[]
for name in filter(None,files):
 rel=name.removeprefix('public/')
 if DENY.search(rel):errors.append((rel,'internal publication path'))
 p=ROOT/name
 if not p.is_file():continue
 try:text=p.read_text()
 except UnicodeError:continue
 if PRIVATE_PATH.search(text):errors.append((rel,'machine-specific private path'))
 if SECRET.search(text):errors.append((rel,'credential-like value'))
 if any(marker in text for marker in MARKERS):errors.append((rel,'conversation/system-context marker'))
 if p.suffix=='.json':
  def transcript(v):
   if isinstance(v,dict):
    if v.get('role') in ('user','assistant','system') and 'content' in v:return True
    return any(transcript(x) for x in v.values())
   return isinstance(v,list) and any(transcript(x) for x in v)
  try:
   if transcript(json.loads(text)):errors.append((rel,'chat transcript structure'))
  except json.JSONDecodeError:pass
if errors:
 for name,reason in errors:print(f'FAIL: {name}: {reason}')
 sys.exit(1)
print(f'PASS: {len(list(filter(None,files)))} publication files; no internal notes, raw tool reports, private paths, transcript markers or credential patterns')
