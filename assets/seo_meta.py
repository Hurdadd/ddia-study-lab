#!/usr/bin/env python3
"""Build-time SEO: per-page meta and JSON-LD for public/, plus sitemap.xml.

Single source of truth for the pages that have no hand-written head (chapters,
solutions, capstone, exercise audit). index.html keeps its own head.
"""
from html import escape
from pathlib import Path
import json,re

BASE='https://ddia-study-lab.vercel.app'
OG=BASE+'/assets/og-image.png'
AUTHOR={'@type':'Person','name':'Hurdad Ashouri','url':'https://ashouri.dev','sameAs':['https://github.com/Hurdadd']}
BOOK={'@type':'Book','name':'Designing Data-Intensive Applications','author':[{'@type':'Person','name':'Martin Kleppmann'},{'@type':'Person','name':'Chris Riccomini'}]}

# chapter number -> (English topics, Persian topics); keep in step with each chapter's h2 headings
CH={
 1:('operational vs analytical systems, system of record vs derived data, cloud vs self-hosting, distributed vs single-machine','سیستم عملیاتی و تحلیلی، منبع حقیقت و داده مشتق، ابر و میزبانی شخصی، توزیع‌شده و تک‌ماشین'),
 2:('performance and percentiles, reliability and fault tolerance, scalability, maintainability','توصیف کارایی، قابلیت اطمینان و تحمل خطا، مقیاس‌پذیری، نگهداری‌پذیری'),
 3:('relational vs document model, graph models, event sourcing and CQRS, DataFrames and arrays','مدل رابطه‌ای و سندی، مدل گراف، Event Sourcing و CQRS، دیتافریم و آرایه'),
 4:('log-structured storage, B-trees vs LSM-trees, in-memory databases, columnar storage, vector indexes','ذخیره‌سازی لاگ‌محور، B-tree و LSM-tree، پایگاه داده درون‌حافظه، ذخیره‌سازی ستونی، ایندکس برداری'),
 5:('encoding formats, schema compatibility, gradual upgrades, dataflow through databases, REST and message passing','فرمت‌های کدگذاری، سازگاری طرح‌واره، ارتقای تدریجی، جریان داده'),
 6:('single-leader replication, replication lag, multi-leader write conflicts, leaderless replication','تکثیر تک‌رهبر، تأخیر تکثیر، تعارض نوشتن در چندرهبر، تکثیر بدون‌رهبر'),
 7:('sharding schemes, hot keys and rebalancing, request routing, secondary indexes','روش‌های تقسیم داده، کلید داغ و بازتوازن، مسیریابی درخواست، ایندکس ثانویه'),
 8:('ACID, weak isolation levels, lost update and write skew, serializability, two-phase commit','معنای ACID، سطوح ایزولاسیون ضعیف، write skew، سریال‌پذیری، commit دوفازی (2PC)'),
 9:('partial failure, unreliable networks and clocks, process pauses, leases and fencing','خرابی جزئی، شبکه و ساعت ناقابل‌اعتماد، توقف پردازه، lease و fencing'),
 10:('linearizability, logical clocks, consensus, coordination services','خطی‌پذیری، ساعت منطقی، اجماع، سرویس‌های هماهنگی'),
 11:('batch processing, Unix tools, distributed filesystems, processing models','پردازش دسته‌ای، ابزارهای یونیکس، سیستم فایل توزیع‌شده، مدل‌های پردازش'),
 12:('log-based brokers, redelivery and ordering, change data capture, exactly-once processing','بروکر لاگ‌محور، ترتیب و ارسال مجدد، CDC، پردازش exactly-once'),
 13:('data integration, batch and stream together, unbundling the database, correctness','یکپارچه‌سازی داده، ترکیب دسته‌ای و جریانی، تفکیک پایگاه داده، درستی'),
 14:('engineer responsibility, bias, feedback loops, privacy, consent','مسئولیت مهندس، سوگیری، حلقهٔ بازخورد، حریم خصوصی، رضایت'),
}
PAGES={
 'final-project/index.html':dict(
  title='Make Your Own AI Platform — DDIA Capstone Workshop',
  en='Design an AI platform step by step from DDIA ideas: requirements, estimates, 15 ADRs, an animated request flow and recovery targets.',
  fa='کارگاه طراحی پلتفرم هوش مصنوعی با ایده‌های DDIA: نیازمندی، برآورد، ADR، جریان درخواست انیمیشنی و اهداف بازیابی.'),
 'exercise-audit.html':dict(
  title='DDIA Exercise Audit: Interview Prep & Senior/Staff Path',
  en='Reviewed DDIA exercises for system-design interviews, leveled by priority, with a 2026 assessment and a Senior/Staff study path.',
  fa='ممیزی تمرین‌های DDIA برای مصاحبهٔ طراحی سیستم: تمرین‌ها به ترتیب اولویت و مسیر مطالعهٔ سنیور و استف.'),
}

def attr(s,name):
    m=re.search(r'\b'+name+r'="([^"]*)"',s)
    return m.group(1) if m else ''

def page_info(rel,s):
    """(title, description, url, jsonld nodes) for a page, or None when it needs no injection."""
    url=BASE+'/'+rel.removesuffix('index.html')
    m=re.match(r'ch(\d+)-[^/]+/(index|solutions)\.html$',rel)
    crumbs=[('DDIA Study Lab',BASE+'/')]
    if m:
        n,kind=int(m[1]),m[2]
        topic=attr(s,'data-title-en').split(': ',1)[-1].split(' · ')[0]
        en,fa=CH[n]
        if kind=='index':
            title=attr(s,'data-title-en')
            desc=f'DDIA chapter {n} study guide: {en}. Interactive diagrams, interview pack and exercises. · خلاصهٔ فصل {n} کتاب DDIA به فارسی: {fa}.'
        else:
            title=f'DDIA Chapter {n} Solutions: {topic}'
            desc=f'Worked solutions and reasoning for the DDIA chapter {n} exercises ({topic}). · حل تمرین‌های فصل {n} کتاب DDIA با دلیل و توضیح.'
        crumbs.append((f'DDIA Chapter {n}: {topic}',BASE+f'/{rel.split("/")[0]}/'))
        if kind=='solutions': crumbs.append(('Solutions',url))
        node={'@type':'LearningResource','name':title,'description':desc,'url':url,'inLanguage':['en','fa'],'isAccessibleForFree':True,
              'learningResourceType':'study guide' if kind=='index' else 'worked solutions','about':BOOK,'author':AUTHOR,
              'isPartOf':{'@type':'Course','name':'DDIA Study Lab','url':BASE+'/'}}
    elif rel in PAGES:
        p=PAGES[rel];title=p['title'];desc=p['en']+' · '+p['fa']
        crumbs.append((title,url))
        node={'@type':'LearningResource','name':title,'description':desc,'url':url,'inLanguage':['en','fa'],'isAccessibleForFree':True,
              'about':BOOK,'author':AUTHOR,'isPartOf':{'@type':'Course','name':'DDIA Study Lab','url':BASE+'/'}}
    else: return None
    crumb={'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':i+1,'name':n,'item':u} for i,(n,u) in enumerate(crumbs)]}
    return title,desc,url,[node,crumb]

def inject(rel,s):
    """Insert SEO tags after </title>; pages that already declare a canonical are left alone."""
    if 'rel="canonical"' in s: return s
    info=page_info(rel,s)
    if not info: return s
    title,desc,url,nodes=info
    s=re.sub(r'<meta name="description"[^>]*>','',s)
    # the language toggle rewrites document.title from these attributes, so keep them in step
    s=re.sub(r'<title>.*?</title>','<title>'+escape(title)+'</title>',s,count=1,flags=re.S)
    s=re.sub(r'data-title-en="[^"]*"','data-title-en="'+escape(title)+'"',s,count=1)
    e=lambda v:escape(v,quote=True)
    tags=(f'<meta name="description" content="{e(desc)}"><link rel="canonical" href="{url}">'
     f'<meta property="og:type" content="article"><meta property="og:site_name" content="DDIA Study Lab">'
     f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
     f'<meta property="og:url" content="{url}"><meta property="og:image" content="{OG}">'
     f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
     f'<meta property="og:locale" content="en_US"><meta property="og:locale:alternate" content="fa_IR">'
     f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(title)}">'
     f'<meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{OG}">'
     '<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':nodes},ensure_ascii=False)+'</script>')
    out=s.replace('</title>','</title>'+tags,1)
    assert out!=s,rel
    return out

def sitemap(out):
    rels=['index.html']+[str(p.relative_to(out)) for p in sorted(out.glob('ch[0-9]*/index.html'),key=lambda p:int(re.match(r'ch(\d+)',p.parent.name)[1]))]
    rels+=[str(p.relative_to(out)) for p in sorted(out.glob('ch[0-9]*/solutions.html'),key=lambda p:int(re.match(r'ch(\d+)',p.parent.name)[1]))]
    rels+=['final-project/index.html','exercise-audit.html']
    urls=''.join(f'<url><loc>{BASE}/{r.removesuffix("index.html")}</loc></url>' for r in rels if (out/r).exists())
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+urls+'</urlset>\n'

def apply(out):
    for p in out.rglob('*.html'):
        rel=str(p.relative_to(out));s=p.read_text();t=inject(rel,s)
        if t!=s: p.write_text(t)
    (out/'sitemap.xml').write_text(sitemap(out))

if __name__=='__main__':
    # self-check: every chapter is covered and a second pass changes nothing
    import tempfile
    root=Path(__file__).resolve().parent.parent;tmp=Path(tempfile.mkdtemp())
    for r in [*root.glob('ch[0-9]*/*.html'),root/'exercise-audit.html',root/'final-project/index.html']:
        d=tmp/r.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);d.write_text(r.read_text())
    apply(tmp);first={p:p.read_text() for p in tmp.rglob('*.html')}
    apply(tmp);assert all(p.read_text()==s for p,s in first.items()),'not idempotent'
    assert sum('application/ld+json' in s for s in first.values())==30,'expected 14 chapters + 14 solutions + 2 pages'
    print('seo_meta ok;',sitemap(tmp).count('<url>'),'urls')
