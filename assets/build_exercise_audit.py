#!/usr/bin/env python3
"""Build the static, bilingual audit and reviewed exercise briefs. Stdlib only."""
from pathlib import Path
from html.parser import HTMLParser
from html import escape, unescape
import json,re,collections
ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'assets/exercise-audit.json'
D=json.loads(DATA.read_text()); ITEMS=D['exercises']
SOURCES={
'crdt':('Preguiça, Baquero, Shapiro · CRDTs · 2018','https://arxiv.org/abs/1805.06358'),
'privacy':('European Commission · GDPR principles','https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/principles-gdpr_en'),
'legal-basis':('European Commission · lawful grounds for processing','https://commission.europa.eu/law/law-topic/data-protection/information-business-and-organisations/legal-grounds-processing-data_en'),
'lamport':('Lamport · Time, Clocks, and Ordering · 1978','https://lamport.azurewebsites.net/pubs/time-clocks.pdf'),
'clocks':('Linux · time namespaces and realtime','https://man7.org/linux/man-pages/man7/time_namespaces.7.html'),
'fencing':('Kleppmann · distributed locking and fencing','https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html'),
'amazon':('Amazon · SDE III interview preparation','https://www.amazon.jobs/content/en/how-we-hire/sde-iii-interview-prep'),
'atlassian':('Atlassian · engineering interview handbook','https://www.atlassian.com/company/careers/resources/interviewing/engineering'),
'principal':('Atlassian · Principal Fullstack interview guide (©2023)','https://www.atlassian.com/dam/jcr%3A413849ac-e926-4841-b7a4-fbbfb7fb1d89/Document%20Talent%20Acquisition_Guide_P60%20Fullstack%20Engineer%20Guide.pdf?cdnVersion=1380'),
'microsoft':('Microsoft · technical interviewing','https://careers.microsoft.com/v2/global/en/hiring-tips/technical-interviewing'),
'anthropic':('Anthropic · AI-resistant technical evaluations · 2026-01-21','https://www.anthropic.com/engineering/AI-resistant-technical-evaluations'),
'openai':('OpenAI · interview guide','https://openai.com/interview-guide/'),
'slo':('Google SRE · implementing SLOs','https://sre.google/workbook/implementing-slos/'),
'idempotency':('AWS · safe retries with idempotent APIs','https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/'),
'retry':('AWS · timeouts, backoff and jitter','https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/'),
'mysql':('MySQL 8.4 · locking reads (SKIP LOCKED, gap locks)','https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html'),
'seatgeek':('SeatGeek · transactional outbox pattern','https://chairnerd.seatgeek.com/transactional-outbox-pattern'),
'postgres':('PostgreSQL 18 · transaction isolation','https://www.postgresql.org/docs/18/transaction-iso.html'),
'pg-lock':('PostgreSQL 18 · SELECT locking clauses','https://www.postgresql.org/docs/18/sql-select.html'),
'pg-range':('PostgreSQL 18 · ranges and exclusion constraints','https://www.postgresql.org/docs/18/rangetypes.html'),
'protobuf':('Protobuf · proto3 language guide','https://protobuf.dev/programming-guides/proto3/'),
'avro':('Avro 1.12 · schema resolution','https://avro.apache.org/docs/1.12.0/specification/'),
'kafka':('Kafka 4.1 · design and delivery semantics','https://kafka.apache.org/41/design/design/'),
'outbox':('Debezium · outbox event router','https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html'),
'cdc':('Debezium · PostgreSQL snapshot and streaming','https://debezium.io/documentation/reference/stable/connectors/postgresql.html'),
'jepsen':('Jepsen · consistency models','https://jepsen.io/consistency/models'),
'abd':('Attiya, Bar-Noy, Dolev · atomic registers · 1995','https://groups.csail.mit.edu/tds/papers/Attiya/JACM95.pdf'),
'vector':('Pinecone · production checklist','https://docs.pinecone.io/guides/operations/moving-to-production'),
'consent':('EDPB · consent guidelines 05/2020','https://www.edpb.europa.eu/documents/guideline/guidelines-052020-on-consent-under-regulation-2016679_en')
}
LEVEL={'foundation':('L1 · پایه','L1 · Foundations'),'senior':('L2 · Senior','L2 · Senior'),'staff':('L3 · Staff / Principal','L3 · Staff / Principal')}
PRIORITY={'core':('اولویت اصلی','Core priority'),'role':('وابسته به نقش','Role-specific'),'extra':('مکمل','Supplementary')}
DECISION={'keep':('حفظ','Keep'),'refocus':('نسخهٔ مصاحبه‌ای آماده','Interview brief ready'),'correct':('اصلاح‌شده','Corrected'),'optional':('اختیاری برای این مسیر','Optional for this track')}
def twin(fa,en): return f'<span class="fa">{fa}</span><span class="en">{en}</span>'
def links(keys):return ' · '.join(f'<a href="{escape(SOURCES[k][1],quote=True)}" target="_blank" rel="noopener">{escape(SOURCES[k][0])}</a>' for k in keys)
def badges(e):return '<div class="exercise-labels">'+''.join(f'<span class="exercise-label {kind}-{value}">{twin(*mapping[value])}</span>' for kind,value,mapping in [('level',e['level'],LEVEL),('priority',e['priority'],PRIORITY)])+f'<span class="exercise-label">{twin(str(e["minutes"])+" دقیقه بحث",str(e["minutes"])+" min discussion")}</span></div>'
def rubric(e):return '<h4>'+twin('معیار پاسخ خوب','What a good answer demonstrates')+'</h4><ul>'+''.join('<li>'+twin(escape(a),escape(b))+'</li>' for a,b in zip(e['signals'],e['signals_en']))+'</ul>'
class Node:
 def __init__(self,tag='',attrs=None,start=0,opening=0,parent=None):self.tag=tag;self.attrs=dict(attrs or []);self.start=start;self.opening=opening;self.end=opening;self.closing=opening;self.parent=parent;self.children=[]
 def walk(self):
  yield self
  for c in self.children:yield from c.walk()
class DOM(HTMLParser):
 def __init__(self,s):
  super().__init__(convert_charrefs=False);self.s=s;self.lines=[0]+[m.end() for m in re.finditer('\n',s)];self.root=Node();self.stack=[self.root];self.feed(s)
 def pos(self):l,c=self.getpos();return self.lines[l-1]+c
 def handle_starttag(self,t,a):
  p=self.pos();n=Node(t,a,p,p+len(self.get_starttag_text()),self.stack[-1]);self.stack[-1].children.append(n)
  if t not in {'meta','link','br','hr','img','input','source','wbr'}:self.stack.append(n)
 def handle_startendtag(self,t,a):pass
 def handle_endtag(self,t):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==t:
    self.stack[i].closing=self.pos();self.stack[i].end=self.s.index('>',self.pos())+1;self.stack=self.stack[:i];break
 def inner(self,n):return self.s[n.opening:n.closing]
 def text(self,n):return unescape(re.sub('<[^>]*>','',self.inner(n))).strip()
def inside(n,p):return n.start>=p.start and n.end<=p.end
CHAPTERS={}
# Initialize missing lab wording on first build; reviewed data is authoritative thereafter.
for chapter in range(1,15):
 path=next(ROOT.glob(f'ch{chapter}-*/index.html'));s=path.read_text();dom=DOM(s);section=[n for n in dom.root.walk() if n.tag=='section' and n.attrs.get('id')][-1]
 es=[e for e in ITEMS if e['chapter']==chapter]; CHAPTERS[chapter]=path
 hue=re.search(r'data-hue="([^"]+)"',s).group(1)
 if all('lab_fa' in e for e in es):
  for e in es:e['folder']=path.parent.name;e['hue']=hue
  continue
 if chapter==13:
  ols=[n for n in section.walk() if n.tag=='ol']; assert len(ols)>=2
  fa_li=[n for n in ols[0].children if n.tag=='li'];en_li=[n for n in ols[1].children if n.tag=='li']; assert len(fa_li)==len(en_li)==4
  for e,f,a in zip(es,fa_li,en_li):
   if 'lab_fa' not in e:
    e['lab_fa']=dom.inner(f).strip();e['lab_en']=dom.inner(a).strip();e['title_fa']=dom.text(next(n for n in f.walk() if n.tag=='b')).rstrip(':');e['title_en']=dom.text(next(n for n in a.walk() if n.tag=='b')).rstrip(':')
   e['folder']=path.parent.name;e['hue']=hue
 else:
  titles=[n for n in section.walk() if n.tag=='span' and n.attrs.get('class')=='fa' and re.match(r'تمرین [۱-۹]',dom.text(n))]
  assert len(titles)==len(es),(chapter,len(titles))
  for e,n in zip(es,titles):
   container=n
   while container.parent and not (container.tag=='details' or container.attrs.get('class') in {'callout','cardmini'}):container=container.parent
   if 'lab_fa' not in e:
    f=next(x for x in container.walk() if x.tag=='div' and x.attrs.get('class')=='fa');a=next(x for x in container.walk() if x.tag=='div' and x.attrs.get('class')=='en')
    e['lab_fa']=dom.inner(f).strip();e['lab_en']=dom.inner(a).strip();e['title_fa']=dom.text(n);e['title_en']=dom.text(next(x for x in n.parent.walk() if x.tag=='span' and x.attrs.get('class')=='en'))
   e['folder']=path.parent.name;e['hue']=hue
DATA.write_text(json.dumps(D,ensure_ascii=False,indent=2)+'\n')
# Current lab wording lives beside the prompt and its explicit resolution.
def lab(e):
 return '<div class="fa">'+e['lab_fa']+'</div><div class="en">'+e['lab_en']+'</div>'
def brief(e):
 return '<p>'+twin(escape(e['prompt']),escape(e['prompt_en']))+'</p>'+rubric(e)+'<p><b>'+twin('پیگیری مصاحبه:','Interview follow-up:')+'</b> '+twin(escape(e['followup']),escape(e['followup_en']))+'</p>'
def released(ch):
 d=ROOT/'assets'/'solutions'/f'ch{ch}'
 return (d/'released').exists()
def exercise(e):
 ident=f'exercise-{e["number"]}';target=f'../exercise-audit.html#ch{e["chapter"]}-ex{e["number"]}'
 sol=(ROOT/e['folder']/'solutions.html')
 sollink=(f' · <a href="solutions.html#sol-{e["number"]}">'+twin('حل آموزشی این تمرین','Worked solution')+'</a>') if (sol.exists() and released(e['chapter'])) else ''
 return f'''<article class="exercise-block" id="{ident}" data-reviewed-exercise="{e['number']}">
<h3>{twin(escape(e['title_fa']),escape(e['title_en']))}</h3>
{badges(e)}
<p class="exercise-verdict">{twin(escape(e['reason']),escape(e['reason_en']))}</p>
<details class="interview-brief" open><summary>{twin('نسخهٔ بازبینی‌شده برای مصاحبه','Reviewed interview brief')}</summary>{brief(e)}</details>
<details class="lab-brief"><summary>{twin('آزمایشگاه تکمیلی · زمان تقریبی '+e['lab'],'Extended hands-on laboratory · estimated '+e['lab_en_duration'])}</summary>{lab(e)}<p class="small">{twin('برای یادگیریِ عمیق است؛ انجام کاملش در زمان بحثِ مصاحبه انتظار نمی‌رود.','The full laboratory is optional depth work and is not expected within the discussion time.')}</p></details>
<p class="exercise-evidence"><a href="{target}">{twin('ارزیابی، سطح و شواهد این تمرین','Assessment, level and evidence')}</a>{sollink} · {links(e['sources'])}</p>
</article>'''
for chapter,path in CHAPTERS.items():
 s=path.read_text();dom=DOM(s);section=[n for n in dom.root.walk() if n.tag=='section' and n.attrs.get('id')][-1]
 es=[e for e in ITEMS if e['chapter']==chapter];body=dom.inner(section)
 if 'data-reviewed-exercise=' in body:
  nodes=[n for n in section.walk() if n.tag=='article' and 'data-reviewed-exercise' in n.attrs]
  edits=[(n.start,n.end,exercise(e)) for n,e in zip(nodes,es)];assert len(nodes)==len(es)
 elif chapter==13:
  ols=[n for n in section.walk() if n.tag=='ol'];fa=ols[0].parent;en=ols[1].parent
  edits=[(fa.start,en.end,'<div class="exercise-list">\n'+'\n'.join(map(exercise,es))+'\n</div>')]
 else:
  titles=[n for n in section.walk() if n.tag=='span' and n.attrs.get('class')=='fa' and re.match(r'تمرین [۱-۹]',dom.text(n))];edits=[]
  for n,e in zip(titles,es):
   c=n
   while c.parent and not (c.tag=='details' or c.attrs.get('class') in {'callout','cardmini'}):c=c.parent
   edits.append((c.start,c.end,exercise(e)))
 for start,end,new in sorted(edits,reverse=True):s=s[:start]+new+s[end:]
 s=s.replace('تمرین‌های عملی (بدون جواب آماده)','تمرین‌های مصاحبه و آزمایشگاه').replace('تمرین‌های عملی (بدونِ جوابِ آماده)','تمرین‌های مصاحبه و آزمایشگاه').replace('Hands-on exercises (no ready answers)','Interview exercises and hands-on labs')
 # The exercise section's original two-column cards were not suited to the reviewed text.
 start=s.rfind('<section id=');s=s[:start]+s[start:].replace('class="grid2"','class="exercise-list"')
 stylesheet='<link rel="stylesheet" href="../assets/exercise-audit.css">'
 if stylesheet not in s:s=s.replace('<link rel="stylesheet" href="../assets/ddia.css">','<link rel="stylesheet" href="../assets/ddia.css">\n'+stylesheet)
 section_link='<p class="exercise-section-note">'+twin('این تمرین‌ها برای مسیر Backend / Distributed Systems در ۱۴ اکتبر ۲۰۲۶ بازبینی شدند. سطح مربوط به نسخهٔ مصاحبه‌ای است؛ زمان آزمایشگاه جداست.','Reviewed on 14 October 2026 for Backend / Distributed Systems. Level refers to the interview brief; full-lab time is separate.')+' <a href="../exercise-audit.html">'+twin('روش ارزیابی و مسیر مطالعه','Method and study path')+'</a></p>'
 if 'class="exercise-section-note"' not in s:
  start=s.rfind('<section id=');h=s.index('</h2>',start)+5;s=s[:h]+'\n'+section_link+s[h:]
 path.write_text(s)
# Shared header keeps language and theme behaviour exactly as in the study site.
home=(ROOT/'index.html').read_text();header=re.search(r'<header class="topbar">.*?</header>',home,re.S)[0]
header=header.replace('href="#chapters"','href="index.html#chapters"').replace('href="#how"','href="index.html#how"').replace('href="#final-project"','href="index.html#final-project"')
if 'href="exercise-audit.html"' in header:
 header=header.replace('href="exercise-audit.html"','href="exercise-audit.html" aria-current="page"')
else:
 header=header.replace('</nav>','<a href="exercise-audit.html" aria-current="page">'+twin('ممیزی تمرین‌ها','Exercise audit')+'</a></nav>')
chaplinks=''.join(f'<a href="#chapter-{c}">{twin("فصل "+str(c),"Chapter "+str(c))}</a>' for c in range(1,15))
counts=collections.Counter(e['priority'] for e in ITEMS)
svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 250" role="img" aria-labelledby="audit-title audit-desc"><title id="audit-title">Exercise priorities · Backend / Distributed Systems</title><desc id="audit-desc">Editorial assessment, not interview frequency: 25 core, 21 role-specific, 3 supplementary exercises. All 49 have reviewed interview briefs.</desc><rect width="800" height="250" rx="16" fill="#fffdf7"/>
<g font-family="Tahoma, sans-serif" fill="#302828" font-size="18"><text x="28" y="40">Study priority · 49 reviewed exercises</text>
<text x="28" y="89">Core</text><text x="28" y="148">Role-specific</text><text x="28" y="207">Supplementary</text></g>
<g><rect x="190" y="65" width="575" height="32" rx="8" fill="#bfe6c9"/><rect x="190" y="124" width="483" height="32" rx="8" fill="#c3ceff"/><rect x="190" y="183" width="69" height="32" rx="8" fill="#ffe08a"/></g>
<g font-family="Tahoma, sans-serif" fill="#302828" font-size="18" font-weight="700"><text x="777" y="88">25</text><text x="685" y="147">21</text><text x="272" y="206">3</text></g></svg>'''
(ROOT/'assets/solutions/exercise-priority.svg').write_text(svg)
intro=f'''<section class="doc-hero audit-hero"><h1>{twin('کدام تمرین ارزش وقتت را دارد؟','Which exercises deserve your time?')}</h1>
<p class="lede">{twin('۴۹ تمرین DDIA با صورت مصاحبه‌ای، آزمایشگاه تکمیلی و حل آموزشی؛ برای هر تمرین، فرض‌ها، معیار پاسخ و دلیل تصمیم‌ها را در پاسخ دنبال کن.','49 DDIA exercises with focused interview briefs, optional laboratories and worked solutions. Follow each answer for assumptions, evaluation criteria and the reasoning behind decisions.')}</p>
<p class="small">{twin('ممیزی اولیه: ۱۴ اکتبر ۲۰۲۶ · اصلاح فنی: ۱۵ اکتبر ۲۰۲۶ · Backend / Distributed Systems','Initial review: 14 October 2026 · Technical corrections: 15 October 2026 · Backend / Distributed Systems')}</p>
<a class="link-arrow" href="index.html">{twin('بازگشت به نقشهٔ فصل‌ها','Back to the chapter roadmap')}</a></section>'''
method='''<section id="method"><h2>'''+twin('راهنمای استفاده از تمرین‌ها','How to use the exercises')+'''</h2>
<p>'''+twin('ابتدا صورت مصاحبه‌ای را در زمان پیشنهادی حل کن و تصمیم‌هایت را با معیار پاسخ بسنج؛ سپس حل آموزشی و آزمایشگاه همان تمرین را بخوان. فرض‌ها و مرز تضمین هر مسئله در متن آن آمده‌اند و نکته‌های فنیِ اصلاح‌شده در بخش بعد به سؤال و پاسخ مربوط لینک دارند.','Solve the interview brief within its suggested time, evaluate your decisions against the criteria, then study the worked solution and optional lab. Each exercise states its assumptions and guarantee boundaries; the resolved technical points below link to the corresponding question and answer.')+'''</p>
<p>'''+twin('در راهنماهای رسمی Amazon و Atlassian، توضیح نیازها، انتخاب، تریدآف، مقیاس، هزینه و قابلیت اطمینان مبنای ارزیابی‌اند. راهنمای Microsoft نیز حل مسئله، تست و طراحی سیستم‌های توزیع‌شده را نام می‌برد. بنابراین برای هر تمرین، یک صورت‌سؤال با زمان محدود و نشانه‌های پاسخ خوب نوشته شده است. این نگاشت و برچسب‌ها استنباط آموزشی ما هستند.','Amazon and Atlassian emphasize requirements, design choices, trade-offs, scale, cost and reliability; Microsoft also names testing and distributed-system design. Each exercise therefore has a bounded discussion brief and answer criteria. This mapping and the labels are our editorial inference.')+'''</p>
<p class="exercise-evidence">'''+links(['amazon','atlassian','microsoft'])+'''</p>
<p>'''+twin('این‌ها بانک سؤال محرمانهٔ شرکت‌ها یا آمار فراوانی سؤال در ۲۰۲۶ نیستند. منابع رسمی در تاریخ بالا بررسی شده‌اند؛ تاریخ بررسی با تاریخ انتشار فرق دارد. مثلاً راهنمای Principal آتلسیان ©۲۰۲۳ است. مقالهٔ استخدام مهندسان عملکرد Anthropic در ۲۱ ژانویهٔ ۲۰۲۶ نشان می‌دهد آزمون‌های تخصصی در واکنش به AI تغییر کرده‌اند؛ این شاهدِ یک تیم است، نه الزام AI/RAG برای همهٔ مصاحبه‌های backend.','These sources are neither private question banks nor 2026 question-frequency statistics. Access date differs from publication date: the Principal guide is ©2023. Anthropic’s 21 January 2026 performance-hiring article documents changes in one specialist team responding to AI; it does not establish a universal AI/RAG requirement for backend interviews.')+'''</p>
<p class="exercise-evidence">'''+links(['principal','anthropic'])+'''</p>
<p>'''+twin('تمرکز این ممیزی Senior/Staff در Backend و سیستم‌های توزیع‌شده است. برای نقش Data، Storage، SRE، Payments یا ML، اولویت تمرین‌های تخصصی تغییر می‌کند. این مجموعه به‌تنهایی آمادگی coding/DSA، product architecture، project deep dive و رفتار/رهبری را پوشش نمی‌دهد.','The target is Senior/Staff backend and distributed systems. Data, storage, SRE, payments and ML roles change the specialist priorities. This set alone does not cover coding/DSA, product architecture, project deep dives or behavioral/leadership interviews.')+'''</p>
<p class="exercise-evidence">'''+links(['principal','openai'])+'''</p>
<figure class="audit-plot"><img src="assets/solutions/exercise-priority.svg" alt="23 core, 21 role-specific, 3 supplementary exercises"><figcaption>'''+twin('این نمودار اولویت آموزشی ما را نشان می‌دهد، نه احتمال طرح سؤال.','This chart shows our study priorities, not the probability of an interview question.')+''' <a href="assets/solutions/exercise-priority.svg" download>SVG</a></figcaption></figure>
</section>'''
levels='''<section id="levels"><h2>'''+twin('معنای برچسب‌ها','How to read the labels')+'''</h2>
<div class="audit-table"><table><thead><tr><th>'''+twin('سطح','Level')+'''</th><th>'''+twin('انتظار از نسخهٔ مصاحبه‌ای','Expected interview reasoning')+'''</th></tr></thead><tbody>
<tr><td>L1 · Foundations</td><td>'''+twin('محاسبه و فهم دقیق یک مفهوم؛ پیش‌نیاز پاسخ‌های لول بالا است.','Accurate calculations and one concept: prerequisites for advanced answers.')+'''</td></tr>
<tr><td>L2 · Senior</td><td>'''+twin('نیاز و invariant، طراحی قابل اجرا، trade-off، failure و معیار صحت/عملکرد.','Requirements, invariants, practical design, trade-offs, failures and measurable correctness/performance.')+'''</td></tr>
<tr><td>L3 · Staff / Principal</td><td>'''+twin('مرز تضمین‌ها، چند failure domain، migration/recovery، هزینه و اثر تصمیم بین اجزا یا تیم‌ها. حل این تمرین به‌تنهایی معادل احراز عنوان شغلی نیست.','Guarantee boundaries, multiple failure domains, migration/recovery, cost and cross-component/team consequences. Solving an exercise alone does not establish a job level.')+'''</td></tr>
</tbody></table></div>
<p>'''+twin('اولویت اصلی: ابتدا برای این مسیر بخوان. وابسته به نقش: در deep dive همان تخصص سرمایه‌گذاری کن. مکمل: برای آگاهی و بحث مرتبط، پس از هسته. زمان‌ها تخمین ما برای بحث‌اند؛ ساخت آزمایشگاه جدا و طولانی‌تر است.','Core: study first for this track. Role-specific: invest when aligned with the target specialty. Supplementary: deepen relevant discussion after the core. Times are our discussion estimates; full implementation labs are separate and longer.')+'''</p>
<h3>'''+twin('امتیاز دادن به پاسخ','Scoring a response')+'''</h3>
<p>'''+twin('برای هر کدام از پنج محورِ «روشن کردن مسئله و invariant»، «طراحی»، «trade-off و عدد»، «خرابی و recovery» و «آزمون و توضیح روشن» از صفر تا دو امتیاز بده: صفر=غایب/غلط، یک=ناقص، دو=دقیق و قابل دفاع. این rubric آموزشی است؛ حد قبولی شرکت‌ها را ادعا نمی‌کند. معیارهای اختصاصی زیر هر تمرین را هم بررسی کن.','Score five dimensions from 0–2: requirements/invariants, design, quantified trade-offs, failure/recovery, and testing/clear communication. Zero means absent or incorrect, one incomplete, two precise and defensible. This is a practice rubric, not a company hiring threshold; also check each exercise’s specific criteria.')+'''</p>
</section>'''
corrections='<section id="corrections"><h2>'+twin('نکته‌های فنیِ اعمال‌شده در تمرین‌ها','Technical clarifications applied to the exercises')+'</h2><ul>'
for e in ITEMS:
 if e['decision']!='correct':continue
 resolution=e['resolution'];assert resolution['status']=='resolved'
 c,n=e['chapter'],e['number']
 corrections+=f'<li data-correction="ch{c}-ex{n}"><a href="{e["folder"]}/index.html#exercise-{n}">'+twin('فصل '+str(c)+' · تمرین '+str(n),'Chapter '+str(c)+' · Exercise '+str(n))+'</a>: '+twin(escape(resolution['fa']),escape(resolution['en']))+f' · <a href="{e["folder"]}/solutions.html#sol-{n}">'+twin('دلیل و حل آموزشی','Reasoning and worked solution')+'</a></li>'
corrections+='</ul></section>'
path='<section id="path"><h2>'+twin('مسیر پیشنهادی مطالعه','Suggested study path')+'</h2><ol>'+''.join('<li>'+twin(f,a)+'</li>' for f,a in [
('فصل ۲: محاسبهٔ بار، SLO و failure domain؛ سپس فصل‌های ۱ و ۳: مرجع و مدل داده.','Chapter 2: capacity, SLOs and failure domains; then chapters 1 and 3: authority and data models.'),
('فصل ۸ و ۹: concurrency، idempotency، timeout و fencing؛ این‌ها را با history و invariant توضیح بده.','Chapters 8 and 9: concurrency, idempotency, timeouts and fencing; practice histories and invariants.'),
('فصل ۶ و ۷: freshness و hotspot؛ فصل ۵: rollout سازگار و workflow recovery.','Chapters 6 and 7: freshness and hotspots; chapter 5: compatible rollout and workflow recovery.'),
('فصل ۱۲ و ۱۳: offset/outbox، migration و reconciliation؛ بعد deep diveهای تخصصی فصل ۴، ۱۰ و ۱۱.','Chapters 12 and 13: offsets/outbox, migration and reconciliation; then specialist deep dives in chapters 4, 10 and 11.')])+'</ol><h3>'+twin('تمرین تکمیلی در دل همین مسئله‌ها','Operational follow-ups in the worked solutions')+'</h3><ul>'+''.join(f'<li><a href="{folder}/solutions.html#sol-{n}">'+twin(fa,en)+'</a></li>' for folder,n,fa,en in [('ch9-distributed-trouble',1,'rate limiting، overload و بودجهٔ retry','Rate limiting, overload and retry budgets'),('ch6-replication',1,'cache stampede، hot key و تازگی','Cache stampedes, hot keys and freshness'),('ch4-storage-retrieval',3,'مرز tenant در retrieval و cache','Tenant boundaries in retrieval and caches'),('ch2-nonfunctional',3,'backup restore و دلیل RPO/RTO','Backup restoration and RPO/RTO reasoning'),('ch13-streaming-philosophy',2,'migration، معیار cutover و rollback','Migration, cutover criteria and rollback'),('ch1-tradeoffs',2,'هزینه، رشد و انتخاب حداقل توزیع','Cost, growth and distribution choices')])+'</ul><p>'+twin('برای Staff/Principal، روایت پروژهٔ واقعی با شواهد impact و همکاری بین تیم‌ها را جدا تمرین کن. هر پاسخ اکنون بخش «چرا این روش و این عددها؟» دارد؛ عدد آموزشی نقطهٔ شروع تحلیل است و باید با دادهٔ محصول جایگزین شود.','For Staff/Principal, separately practice a real project narrative with evidence of impact and cross-team work. Every answer includes “Why this method and these numbers?”; teaching inputs start the analysis and must be replaced by product evidence.')+'</p></section>'
filters='''<div class="audit-filters" aria-label="Exercise filters"><label>'''+twin('سطح','Level')+'''<select id="audit-level"><option value="">All · همه</option>'''+''.join(f'<option value="{k}">{v[1]}</option>' for k,v in LEVEL.items())+'''</select></label><label>'''+twin('اولویت','Priority')+'''<select id="audit-priority"><option value="">All · همه</option>'''+''.join(f'<option value="{k}">{v[1]} · {v[0]}</option>' for k,v in PRIORITY.items())+'''</select></label><label class="audit-search-label">'''+twin('جست‌وجو در موضوع و ارزیابی','Search topics and assessments')+'''<input id="audit-search" type="search" placeholder="Kafka, رزرو, SLO…"></label><button id="audit-reset" type="button">'''+twin('پاک کردن فیلترها','Clear filters')+'''</button><p id="audit-count" role="status" aria-live="polite">49 / 49</p></div><p id="audit-empty" hidden>'''+twin('تمرینی با این فیلترها پیدا نشد. فیلترها را پاک کن.','No matching exercises. Clear the filters to see all exercises.')+'''</p>'''
chapters=''
for c,pathfile in CHAPTERS.items():
 es=[e for e in ITEMS if e['chapter']==c];chapters+=f'<section id="chapter-{c}" class="audit-chapter"><h2>'+twin('فصل '+str(c),'Chapter '+str(c))+f' <a class="audit-chapter-link" href="{pathfile.parent.name}/index.html">'+twin('متن فصل','Chapter text')+'</a>'
 if ((ROOT/es[0]['folder']/'solutions.html').exists() and released(c)):
  chapters+=f' <a class="audit-chapter-link" href="{es[0]["folder"]}/solutions.html">'+twin('حل تمرین‌ها','Exercise solutions')+'</a>'
 chapters+='</h2>'
 for e in es:
  ident=f'ch{c}-ex{e["number"]}';target=f'{e["folder"]}/index.html#exercise-{e["number"]}'
  search=escape(' '.join([e['title_fa'],e['title_en'],e['prompt'],e['prompt_en'],e['reason'],e['reason_en']]),quote=True)
  chapters+=f'<article id="{ident}" class="audit-item" data-level="{e["level"]}" data-priority="{e["priority"]}" data-search="{search}"><h3><a href="{target}">'+twin(escape(e['title_fa']),escape(e['title_en']))+'</a></h3>'+badges(e)+'<p class="audit-decision">'+twin(*DECISION[e['decision']])+'</p><p>'+twin(escape(e['reason']),escape(e['reason_en']))+'</p><details><summary>'+twin('صورت مصاحبه‌ای و معیار پاسخ','Interview brief and answer criteria')+'</summary>'+brief(e)+'</details><p class="exercise-evidence">'+twin('شواهد موضوع و معیار؛ سطح و اولویت ارزیابی ماست:','Topic/criteria evidence; levels and priorities are our assessment:')+' '+links(e['sources'])
  if ((ROOT/e['folder']/'solutions.html').exists() and released(e['chapter'])):
   chapters+=f' · <a href="{e["folder"]}/solutions.html#sol-{e["number"]}">'+twin('حل آموزشی این تمرین','Worked solution')+'</a>'
  chapters+='</p></article>'
 chapters+='</section>'
source_section='<section id="sources"><h2>'+twin('منابع و تاریخ‌ها','Sources and dates')+'</h2><p>'+twin('همه در ۱۴ اکتبر ۲۰۲۶ بررسی شده‌اند. منبع استخدام، معیار را پشتیبانی می‌کند؛ مستند فنی، ادعای فنی را. هیچ لینک استخدامی به معنی تأیید سؤال دقیق این مجموعه نیست. مطالب قدیمیِ بنیادی مثل ABD به‌صرف قدیمی بودن منسوخ نیستند.','All were checked on 14 October 2026. Hiring guides support evaluation criteria; technical documentation supports technical premises. No hiring link certifies the exact exercise as a real interview question. Foundational work such as ABD is not obsolete merely because it is old.')+'</p><ul>'+''.join(f'<li>{links([k])}</li>' for k in SOURCES)+'</ul></section>'
page='''<!DOCTYPE html><html lang="fa" dir="rtl" data-hue="mint" data-title-fa="DDIA · ممیزی تمرین‌ها برای مصاحبه" data-title-en="DDIA · Interview exercise audit"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DDIA · ممیزی تمرین‌ها برای مصاحبه</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;700;800;900&family=Vazirmatn:wght@300;400;500;700;900&display=swap" rel="stylesheet"><link rel="stylesheet" href="assets/ddia.css"><link rel="stylesheet" href="assets/exercise-audit.css"></head><body>'''+header+intro+'<div class="doc-wrap"><aside class="toc" aria-label="Audit contents"><p class="audit-toc-title">'+twin('فهرست ممیزی','Audit contents')+'</p>'+''.join('<a href="#'+id+'">'+twin(f,a)+'</a>' for id,f,a in [('method','راهنمای تمرین‌ها','Exercise guide'),('levels','معنای سطح‌ها','Level definitions'),('corrections','نکته‌های فنی','Technical clarifications'),('path','مسیر مطالعه','Study path')])+chaplinks+'<a href="#sources">'+twin('منابع','Sources')+'</a></aside><main class="doc audit-doc">'+method+levels+corrections+path+'<section id="exercises"><h2>'+twin('ارزیابی تک‌تک ۴۹ تمرین','All 49 exercise assessments')+'</h2>'+filters+'</section>'+chapters+source_section+'</main></div><footer class="footer"><p class="small">'+twin('DDIA Study · ممیزی آموزشی مبتنی بر منابع عمومی · اجرای محلی','DDIA Study · Educational audit based on public sources · Local only')+'</p></footer><script src="assets/site.js"></script><script src="assets/exercise-audit.js"></script></body></html>'
(ROOT/'exercise-audit.html').write_text(page)
assert len(ITEMS)==49 and len({(e['chapter'],e['number']) for e in ITEMS})==49
print('Built 49 reviewed briefs, 14 labelled chapters and one linked audit.')
import build_concept_labs
build_concept_labs.build()
