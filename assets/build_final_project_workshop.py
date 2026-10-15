"""Render the capstone design workshop in the study site's visual language."""
import json

def icon(name):
    paths = {
        'next': '<path d="m9 5 7 7-7 7"/>',
        'chevron': '<path d="m6 9 6 6 6-6"/>',
        'plus': '<path d="M12 5v14M5 12h14"/>',
        'download': '<path d="M12 3v12m-5-5 5 5 5-5M5 17v4h14v-4"/>',
        'reset': '<path d="M4 10a8 8 0 1 1 1 7M4 4v6h6"/>',
        'play': '<path class="play-shape" d="m8 4 12 8-12 8Z"/><path class="pause-shape" d="M8 4v16M16 4v16"/>',
    }
    return '<svg class="ui-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+paths[name]+'</svg>'

STAGES = [['مسئله و کاربر',
  'Problem and user',
  'تأییدشده: کاربر اصلی توسعه\u200cدهنده است. می\u200cخواهد یک app را ثبت کند، ورودی بدهد و نتیجه و trace بگیرد. هنوز '
  'از این جمله نتیجه نمی\u200cگیریم که Kafka یا GPU لازم است.',
  'Confirmed: the primary user is a developer registering an app, submitting input, and receiving a result/trace. This '
  'does not yet imply Kafka or GPUs.',
  'یک user story با ورودی، خروجی و معیار موفقیت بنویسیم؛ «agent همه\u200cکاره» معیار قابل\u200cآزمون نیست.',
  'Write a user story with input, output, and success criteria; an all-purpose agent is not a testable requirement.'],
 ['مرز نسخهٔ اول',
  'First-version boundary',
  'پیشنهاد ADR-002: یک مسیر کوچک از ثبت app تا اجرای یک مدل و ابزار خواندنی. پنج قابلیت مقصد پروژه\u200cاند؛ '
  'هیچ\u200cکدام با دیدن نمودار پیاده\u200cسازی\u200cشده محسوب نمی\u200cشود.',
  'ADR-002 proposes one small app-to-model-and-read-only-tool path. Five capabilities are the destination, not '
  'implemented services.',
  'چه چیزی را در demo اول واقعاً می\u200cتوانیم اجرا و خراب کنیم؟ همین scope باید قبل از انتخاب ابزار روشن شود.',
  'What can the first demo actually run and deliberately break? Establish that scope before choosing tools.'],
 ['نیازهای رفتاری',
  'Functional needs',
  'ثبت app، هویت توسعه\u200cدهنده، پذیرش run، فراخوانی مدل/ابزار، نتیجه و مشاهدهٔ وضعیت. برای هرکدام یک acceptance '
  'example می\u200cنویسیم.',
  'Register apps, identify developers, admit runs, call models/tools, return results, expose state. Write an '
  'acceptance example for each.',
  'نیاز: «retry پاسخ گم\u200cشده run جدید نسازد». راه\u200cحل پیشنهادیِ بعدی: idempotency key و قید یکتا. نیاز را با '
  'ابزار یکی نکنیم.',
  'Need: retrying a lost response must not create another run. Later solution candidate: idempotency key and '
  'uniqueness. Separate needs from mechanisms.'],
 ['بار و تخمین',
  'Workload and estimates',
  'دفتر E01–E12 فرض\u200cها را ثبت می\u200cکند. میانگین روزانه، burst کوتاه و سناریوی یک میلیون سند سه workload '
  'متفاوت\u200cاند. تا اندازه\u200cگیری نکرده\u200cایم، عددها تخمین\u200cاند.',
  'E01–E12 record assumptions. Daily pilot average, short bursts, and a million-document scale scenario are different '
  'workloads. Unmeasured values remain estimates.',
  'حجم، token، حافظه و هزینه را با فرمول حساب کنیم؛ اگر جواب با بودجه نمی\u200cخواند scope یا معماری را عوض کنیم.',
  'Calculate volume, tokens, memory, and cost; adjust scope/architecture when results exceed the budget.'],
 ['کیفیت و خط قرمزها',
  'Quality and invariants',
  'اول مشخص کنیم admission، اولین token یا پایان run مهم است. سپس SLI، بار، پنجره، denominator، هدف و روش آزمون را '
  'تعریف کنیم.',
  'Choose between admission, useful first token, and final completion. Define SLI, load, window, denominator, target, '
  'and validation.',
  'ADR-003 سه ثانیه را فرضِ TTFT می\u200cگیرد؛ این عدد نه از DDIA آمده و نه هنوز از تجربهٔ کاربر اندازه\u200cگیری شده '
  'است.',
  'ADR-003 treats three seconds as a TTFT hypothesis; it is neither a DDIA mandate nor a measured user requirement.'],
 ['گزینه\u200cها و ADR',
  'Alternatives and ADRs',
  'برای هر انتخابِ مهم مسئله، گزینه\u200cها، دلیل، اثر منفی، فرض، آزمون و شرط بازنگری ثبت می\u200cشود. وضعیت Proposed '
  'با Accepted فرق دارد.',
  'Record context, alternatives, rationale, downside, assumptions, validation, and revisit triggers for major choices. '
  'Proposed and Accepted differ.',
  'فعلاً فقط انتخاب مخاطب پذیرفته شده است؛ ADRهای فنی پیشنهادی\u200cاند و با آزمایش یا گفت\u200cوگو تغییر '
  'می\u200cکنند.',
  'Only the audience choice is accepted; technical ADRs remain proposals subject to discussion and testing.'],
 ['رسم فلو، سپس ساخت',
  'Draw the flow, then implement',
  'بعد از این گام\u200cها، بلوک\u200cها و مرزِ داده را رسم می\u200cکنیم. انیمیشن پایین فقط یک درخواستِ فرضی را روی طرح '
  'پیشنهادی دنبال می\u200cکند.',
  'Only then draw components and data boundaries. The animation below follows a hypothetical request through a '
  'proposed design.',
  'پس از پذیرش scope و ADRهای لازم، اولین slice را می\u200cسازیم، crash را تزریق می\u200cکنیم و نتایج واقعی را جای '
  'فرض\u200cها می\u200cگذاریم.',
  'After accepting scope and required ADRs, build the first slice, inject crashes, and replace assumptions with '
  'measured results.']]

FORMULAS = [[['token روزانه', 'Daily tokens'],
  ['E01×E02×(input+output)=۱٫۶M token/day.', 'E01×E02×(input+output)=1.6M tokens/day.'],
  ['retry، context طولانی و reasoning اضافه جدا اندازه\u200cگیری می\u200cشوند.',
   'Measure retries, longer context, and extra reasoning separately.']],
 [['هزینهٔ پایلوت', 'Pilot cost'],
  ['۱٫۲M input×$1/M + ۰٫۴M output×$4/M = $2.80/day؛ $84 در ۳۰روز.',
   '1.2M input×$1/M + 0.4M output×$4/M = $2.80/day; $84/30 days.'],
  ['E09 قیمت فرضی است؛ infra، embedding، retry و مالیات داخل این عدد نیستند.',
   'E09 is hypothetical; excludes infrastructure, embeddings, retries, and taxes.']],
 [['burst در inference', 'Inference burst'],
  ['۲۰ run/min×۸×۲۰۰۰ = ۵۳۳۳ token/s میانگینِ بازه؛ حدود $33.60/hour اگر یک ساعت ادامه یابد.',
   '20 runs/min×8×2000 = 5333 tokens/s over the interval; about $33.60/hour if sustained.'],
  ['E10 فقط ۵ دقیقه است؛ با هزینهٔ پایلوت جمع یا جایگزین نشود.',
   'E10 lasts five minutes; do not confuse it with pilot daily spend.']],
 [['حافظهٔ vector', 'Vector memory'],
  ['۱M×۴×۱۵۳۶×۴byte = 24.576 GB خام؛ دو نسل با factor1.5 ≈73.728 GB.',
   '1M×4×1536×4 bytes = 24.576GB raw; two generations at factor 1.5 ≈73.728GB.'],
  ['E04–E06؛ text، metadata، WAL و replica جدا؛ GB ده\u200cدهی است.',
   'E04–E06; excludes text, metadata, WAL, and replicas; decimal GB.']],
 [['log نگهداری\u200cشده', 'Retained log'],
  ['۵×۲۰۰۰×۸۶۴۰۰×۷×۳×۱٫۵ = 27.216 GB.', '5×2000×86400×7×3×1.5 = 27.216GB.'],
  ['E07–E08؛ compression نادیده گرفته شده و telemetry خارج این حساب است.',
   'E07–E08; compression ignored; telemetry excluded.']],
 [['seed و catch-up', 'Seed and catch-up'],
  ['۱M/۱۰۰=۱۰۰۰۰s؛ backlog=۵۰۰۰۰؛ با μ=۳۰ و λ=۵، catch-up=۲۰۰۰s.',
   '1M/100=10000s; backlog=50000; at μ=30 and λ=5, catch-up=2000s.'],
  ['اگر μ≤λ باشد catch-up تمام نمی\u200cشود؛ snapshot باثبات و WAL کافی جدا لازم\u200cاند.',
   'Catch-up cannot finish if μ≤λ; stable snapshots and sufficient WAL are separate requirements.']],
 [['هم\u200cزمانی', 'Concurrency'],
  ['با نرخ ۲۰/۶۰ run/s و میانگین زمان ۳۰s، Little: L=λW≈۱۰ run.',
   'At 20/60 runs/s and mean duration 30s, Little’s law gives L=λW≈10 runs.'],
  ['۳۰s فرضِ میانگین است، نه p95 یا حداکثر؛ رابطه برای بازهٔ تقریباً پایدار است.',
   '30s is an assumed mean, not p95/max; the relation assumes an approximately stable interval.']],
 [['حافظهٔ GPU', 'GPU memory'],
  ['۷B×۲byte ≈13.04GiB وزن؛ KV فرضی =2×32×8×128×2×4096×4byte =2GiB.',
   '7B×2 bytes ≈13.04GiB weights; hypothetical KV =2×32×8×128×2×4096×4 bytes =2GiB.'],
  ['layers=32، KV heads=8، head dim=128، batch=4؛ activation، workspace و fragmentation جدا. fit روی ۲۴GiB هنوز اثبات '
   'نشده.',
   '32 layers, 8 KV heads, head dim128, batch4; activations/workspace/fragmentation excluded. A 24GiB fit is '
   'unproven.']]]


def build_workshop(root, twin, p, table, ul, call):
    data = json.loads((root/'final-project/workshop.json').read_text())

    def heading(number, fa, en):
        return '<h2 class="workshop-heading"><span class="secnum" aria-hidden="true">'+number+'</span>'+twin(fa,en)+'</h2>'

    def disclosure(fa, en, content, cls='workbook-reference'):
        return f'<details class="{cls}"><summary>'+twin(fa,en)+icon('plus')+'</summary><div class="disclosure-body">'+content+'</div></details>'

    def action(href, fa, en):
        return f'<a class="workshop-link" href="{href}">'+twin(fa,en)+icon('next')+'</a>'

    examples = [
        [('توسعه‌دهنده، app و ورودی','Developer, app, input'),('یک run قابل‌پیگیری','One traceable run'),('نتیجه و trace قابل‌مشاهده','An inspectable result and trace')],
        [('یک مدل و یک ابزار خواندنی','One model and one read-only tool'),('یک مسیر کوچکِ سرتاسری','One small end-to-end slice'),('demo قابل‌اجرا و آزمونِ crash','A runnable demo and a crash test')],
        [('پاسخِ پذیرش گم می‌شود','The admission response is lost'),('retry همان run را برگرداند','A retry returns the same run'),('شناسهٔ run قبل و بعد برابر است','The run ID stays the same')],
        [('<bdi dir="ltr">100 runs × 8 calls × 2000 tokens</bdi>','100 runs × 8 calls × 2000 tokens'),('۱٫۶ میلیون token در روز، فرضی','1.6M daily tokens, hypothetical'),('مقایسهٔ حساب با بودجه و بار واقعی','Compare with budget and actual load')],
        [('برنامهٔ تعاملی؛ اولین token مفید','An interactive app; useful first token'),('۳ ثانیه، هدفِ پیشنهادی','Three seconds, a proposed target'),('تست کاربر + اندازه‌گیری سرتاسری','User tests + end-to-end measurement')],
        [('نیاز، گزینه‌ها و محدودیت','A need, alternatives, constraints'),('یک ADR با وضعیت Proposed','An ADR marked Proposed'),('آزمونِ انتخاب و شرطِ بازنگری','A validation test and revisit trigger')],
        [('scope و تصمیم‌های لازم پذیرفته شوند','Accept scope and required decisions'),('رسم مرزها، سپس اولین slice','Draw boundaries, then build a slice'),('تزریق crash و ثبت نتیجهٔ واقعی','Inject crashes and record real results')],
    ]
    nav = '<div class="workshop-step-nav" hidden aria-label="Workshop stages">'
    options = ''
    articles = ''
    roles = [('ورودی / نیاز','Input / need'),('تصمیم / فرض','Decision / assumption'),('شاهدِ لازم','Evidence needed')]
    for i,(fa,en,body_fa,body_en,question_fa,question_en) in enumerate(STAGES):
        nav += f'<button type="button" data-workshop-select="{i}" aria-pressed="{str(i==0).lower()}"><span class="lesson-number" aria-hidden="true">{i+1:02}</span><span>'+twin(fa,en)+'</span>'+icon('next')+'</button>'
        options += f'<option value="{i}">{i+1} / 7 · '+fa+'</option>'
        worked = '<dl class="lesson-example">'+''.join('<div><dt>'+twin(*role)+'</dt><dd>'+twin(*example)+'</dd></div>' for role,example in zip(roles,examples[i]))+'</dl>'
        articles += f'<article class="workshop-step" data-workshop-step="{i}"><h3>'+twin(fa,en)+'</h3>'+p(body_fa,body_en)+'<div class="workshop-question"><h4>'+twin('کاری که در این گام انجام می‌دهیم','The task for this stage')+'</h4>'+p(question_fa,question_en)+'</div>'+worked+'</article>'
    nav += '</div>'
    mobile = '<div class="workshop-mobile-nav" hidden><label for="workshop-stage-select">'+twin('انتخاب گام از هفت گام طراحی','Choose one of seven design stages')+'</label><div class="stage-select-wrap"><select id="workshop-stage-select">'+options+'</select>'+icon('chevron')+'</div></div>'
    controls = '<div class="lesson-controls" hidden><button type="button" data-workshop-prev class="quiet-button">'+icon('next')+twin('گام قبل','Previous stage')+'</button><span data-workshop-count></span><button type="button" data-workshop-next class="quiet-button">'+twin('گام بعد','Next stage')+icon('next')+'</button></div>'
    start = '<section id="start-here" class="workshop-section">'+heading('01','اول مسئله را بفهمیم','Understand the problem first')+p('از نیاز توسعه‌دهنده شروع می‌کنیم؛ بعد عدد می‌گذاریم، گزینه‌ها را می‌سنجیم و معماری را رسم می‌کنیم. این هفت گام مسیر طراحی‌اند، نه گزارشِ پیشرفتِ ساخت.','Start from the developer’s needs, estimate demand, weigh alternatives, then draw the architecture. These seven stages guide the design; they do not report implementation progress.')+'<p class="workshop-status">'+twin('در مرحلهٔ تعریف نیازها هستیم. مخاطب تأیید شده؛ معماری پیشنهادی است و سرویس‌های پلتفرم هنوز ساخته نشده‌اند.','Requirements stage. Audience confirmed; architecture proposed; platform services not yet implemented.')+'</p><div class="workshop-layout">'+nav+mobile+'<div class="workshop-current">'+articles+controls+'</div></div><div class="workshop-links">'+action('#estimates','فرض‌ها را حساب کنیم','Calculate the assumptions')+action('#decisions','دلیل تصمیم‌ها را بخوانیم','Read the decisions')+action('#architecture','مسیر درخواست را ببینیم','Follow a request')+'</div></section>'

    inputs = [
        ('runs','run در روز','Runs per day',100,'E01'),
        ('calls','call مدل در هر run','Model calls per run',8,'E02'),
        ('input','توکن ورودی در هر call','Input tokens per call',1500,'E03'),
        ('output','توکن خروجی در هر call','Output tokens per call',500,'E03'),
        ('documents','تعداد سند','Document count',1000000,'E04'),
        ('seed','سند در ثانیه برای seed','Seed documents per second',100,'E04'),
    ]
    def fields(items):
        return ''.join(f'<label for="estimate-input-{key}"><span class="estimate-field-label">'+twin(fa,en)+f'<bdi class="assumption-id">{assumption}</bdi></span><input id="estimate-input-{key}" name="{key}" type="number" value="{value}" min="1" max="1000000000" step="1" required inputmode="numeric"></label>' for key,fa,en,value,assumption in items)

    output_data = {
        'cost':('هزینهٔ روزانهٔ نمونه','Example daily cost','$2.80','E01–E03 · E09'),
        'tokens':('توکن روزانه','Daily tokens','1,600,000','E01–E03'),
        'month':('هزینهٔ نمونه در ۳۰ روز','Example cost over 30 days','$84.00','E09'),
        'vectors':('فقط بایت خامِ بردارها','Raw vector bytes only','24.576 GB','E04–E06'),
        'generations':('دو نسلِ بردار با overhead فرضی','Two generations, assumed overhead','73.728 GB','E05–E06'),
        'snapshot':('زمان seed','Seed duration','2.778 h','E04'),
        'backlog':('تغییرهای جمع‌شده حین seed','Changes accumulated during seed','50,000','E04 · E07'),
        'catchup':('زمان catch-up','Catch-up duration','33.333 min','E04 · E07'),
    }
    def outputs(keys):
        return '<dl class="estimate-results">'+''.join('<div class="result-'+key+'"><dt>'+twin(*output_data[key][:2])+f'</dt><dd><output id="estimate-{key}">'+output_data[key][2]+'</output></dd><span class="result-assumptions" dir="ltr">'+output_data[key][3]+'</span></div>' for key in keys)+'</dl>'

    pilot = '<div class="estimate-scenario pilot-scenario"><div class="scenario-title"><h3>'+twin('پایلوتِ روزانه','The daily pilot')+'</h3><span>'+twin('بارِ inference','Inference demand')+'</span></div><div class="scenario-workspace"><fieldset><legend class="sr-only">'+twin('فرض‌های پایلوت روزانه','Daily pilot assumptions')+'</legend>'+fields(inputs[:4])+'</fieldset><div class="scenario-answer">'+outputs(['cost','tokens','month'])+'<p class="design-question">'+twin('پرسش طراحی: با این مصرف، بودجهٔ مدل و سقف هر run چقدر باشد؟','Design question: what model budget and per-run limit does this imply?')+'</p></div></div><p class="estimate-caveat">'+twin('E09: نرخ‌های فرضی <bdi dir="ltr">$1/M</bdi> ورودی و <bdi dir="ltr">$4/M</bdi> خروجی؛ زیرساخت، embedding، retry و مالیات جدا هستند.','E09: hypothetical rates of $1/M input and $4/M output. Infrastructure, embeddings, retries, and taxes are separate.')+'</p></div>'
    scale = '<div class="estimate-scenario scale-scenario"><div class="scenario-title"><h3>'+twin('وقتی داده بزرگ می‌شود','When the data grows')+'</h3><span>'+twin('سناریوی مقیاس','Scale scenario')+'</span></div><div class="scenario-workspace"><fieldset><legend class="sr-only">'+twin('فرض‌های مقیاس داده','Data scale assumptions')+'</legend>'+fields(inputs[4:])+'<p class="estimate-caveat">'+twin('ثابت‌های این سناریو: ۴ chunk در سند، ۱۵۳۶ بعد، float32، پنج تغییر در ثانیه و پردازش ۳۰ تغییر در ثانیه.','Scenario constants: 4 chunks per document, 1536 dimensions, float32, 5 changes/s, and processing at 30 changes/s.')+'</p></fieldset><div class="scenario-answer">'+outputs(['vectors','generations','snapshot','backlog','catchup'])+'<p class="design-question">'+twin('پرسش طراحی: آیا حافظه، retention و سرعت پردازش برای رسیدن به دادهٔ زنده کافی‌اند؟','Design question: are memory, retention, and processing speed sufficient to catch up?')+'</p></div></div></div>'
    form = '<form id="estimate-form">'+pilot+scale+'<div class="estimate-submit"><button type="submit" class="langbtn">'+twin('محاسبهٔ دوباره','Recalculate')+icon('reset')+'</button><p>'+twin('ورودی‌ها را تغییر بده؛ خروجی‌ها محاسبه می‌شوند، benchmark اجرا نمی‌شود.','Edit the inputs to recalculate. This is arithmetic, not a benchmark.')+'</p></div></form><p id="estimate-error" role="alert" hidden></p>'
    equations = [
        ('مصرف روزانه','Daily usage','100 × 8 × (1500 + 500) = 1,600,000 tokens/day','E01 × E02 × E03','retry و context طولانی‌تر جدا هستند.','Retries and longer contexts are separate.'),
        ('هزینهٔ مدل','Model cost','1.2M × $1/M + 0.4M × $4/M = $2.80/day','E01–E03 · E09','نرخ‌ها نمونه‌اند؛ قیمتِ یک provider نیستند.','Illustrative rates, not a provider’s prices.'),
        ('حافظهٔ خامِ بردارها','Raw vector memory','1,000,000 × 4 × 1536 × 4 B = 24.576 GB','E04–E06','متن، metadata، WAL و replica جدا هستند؛ GB ده‌دهی است.','Excludes text, metadata, WAL, and replicas; decimal GB.'),
        ('رسیدن به جریان زنده','Catching up','50,000 ÷ (30 − 5) = 2,000 s ≈ 33.33 min','E04 · E07','باید سرعت پردازش از ورود تغییرها بیشتر باشد.','Processing must be faster than incoming changes.'),
    ]
    derivations = '<div class="worked-equations">'+''.join('<div class="worked-equation"><h4>'+twin(fa,en)+f'<bdi class="assumption-id">{ids}</bdi></h4><p class="equation" dir="ltr">{eq}</p><p class="equation-limit">'+twin(cfa,cen)+'</p></div>' for fa,en,eq,ids,cfa,cen in equations)+'</div>'
    formula_table = table([('خروجی','Output'),('فرمول و عددِ سناریو','Formula and scenario result'),('فرض و محدودیت','Assumption and limit')],[[row[0], ('<bdi dir="ltr">'+row[1][1]+'</bdi>', '<bdi dir="ltr">'+row[1][1]+'</bdi>'), row[2]] for row in FORMULAS])
    assumptions = table([('شناسه','ID'),('فرض','Assumption'),('عدم‌قطعیت','Uncertainty')],[[(d['id'],d['id']),tuple(d['value']),tuple(d['uncertainty'])] for d in data['assumptions']])
    estimates = '<section id="estimates" class="workshop-section">'+heading('02','هر عدد، یک فرض و یک حساب','Every number needs an assumption')+p('دو سناریوی جدا را بررسی می‌کنیم: مصرفِ یک پایلوت کوچک و حجمِ یک مجموعه‌دادهٔ بزرگ. اعداد فرضی‌اند؛ شناسهٔ کنار هر ورودی، راهِ رسیدن به فرض و محدودیت آن است.','Explore two separate scenarios: a small pilot’s usage and a large dataset’s size. Values are hypothetical; assumption IDs connect each input to its source and limits.')+form+'<h3 class="derivation-title">'+twin('این جواب‌ها از کجا می‌آیند؟','Where do these answers come from?')+'</h3>'+derivations+disclosure('همهٔ فرمول‌ها و محدودیت‌ها','All formulas and limitations',formula_table)+disclosure('دفتر ۱۲ فرضِ قابل‌بازنگری','The 12 revisitable assumptions',assumptions)+'</section>'

    # A visibly allocated budget explains the proposal; it is not measured evidence.
    allocations = [(100,'لبه','Edge'), (300,'پذیرش / صف','Admission / queue'), (250,'بازیابی context','Context'), (1900,'provider مدل','Model provider'), (450,'انتقال / حاشیهٔ ظرفیت','Transport / headroom')]
    budget_legend = '<dl class="budget-legend" id="budget-legend">'+''.join(f'<div><dt><i class="budget-key budget-part-{i}" aria-hidden="true"></i>'+twin(fa,en)+f'</dt><dd dir="ltr">{ms} ms</dd></div>' for i,(ms,fa,en) in enumerate(allocations))+'</dl>'
    slo = '<div class="slo-example"><div class="slo-question"><h3>'+twin('چرا سه ثانیه؟','Why three seconds?')+'</h3><p>'+twin('یک فرض برای تجربهٔ تعاملی؛ هنوز نیازِ اثبات‌شده نیست.','A hypothesis for the interactive experience, still unproven.')+'</p><a class="workshop-link" href="#ADR-003">'+twin('استدلال و آزمون در ADR-003','Rationale and validation in ADR-003')+icon('next')+'</a></div><div class="slo-budget"><p class="budget-equation" dir="ltr">100 + 300 + 250 + 1900 + 450 = <strong>3000 ms</strong></p><div class="budget-bar" role="img" aria-label="E11 · TTFT budget" aria-describedby="budget-legend budget-note">'+''.join(f'<i style="flex:{n}" class="budget-part-{i}"></i>' for i,n in enumerate([100,300,250,1900,450]))+'</div>'+budget_legend+'<p id="budget-note">'+twin('E11؛ بودجهٔ تخصیصی و اندازه‌گیری‌نشدهٔ مسیر؛ جمعِ p95 اجزا نیست. هدف مربوط به اولین token مفید است، نه پایانِ agent.','E11: allocated, unmeasured path budget, not the sum of component p95s. The target concerns the useful first token, not agent completion.')+'</p></div></div>'
    decisions = '<section id="decisions" class="workshop-section">'+heading('03','تصمیمی که بشود از آن دفاع کرد','Decisions you can defend')+p('هر رکورد یک سؤال دارد: چه نیازی، کدام گزینه‌ها، چرا این انتخاب و با چه شاهدی؟ فقط انتخاب مخاطب پذیرفته شده؛ تصمیم‌های فنی را باید با نیاز، عدد و آزمون بررسی کنیم.','Each record asks: which need, which alternatives, why this choice, and what evidence? Only the audience choice is accepted. Technical decisions still need requirements, estimates, and validation.')+slo+'<div class="decision-register"><div class="register-heading"><h3>'+twin('دفتر تصمیم‌های معماری','Architecture decision register')+'</h3><p>'+twin('۱ پذیرفته‌شده · ۱۴ پیشنهادی','1 accepted · 14 proposed')+'</p></div>'
    def adr_copy(pair):
        return [pair[0].replace('≤۳۰۰۰ms', '<bdi dir="ltr">≤3000 ms</bdi>').replace('۱۰۰+۳۰۰+۲۵۰+۱۹۰۰+۴۵۰=۳۰۰۰ms', '<bdi dir="ltr">100 + 300 + 250 + 1900 + 450 = 3000 ms</bdi>'), pair[1]]

    field_names = [('context','مسئله','Context'),('options','گزینه‌های روی میز','Alternatives'),('choice','پیشنهاد فعلی','Current proposal'),('reason','دلیل انتخاب و هزینه‌اش','Rationale and trade-off'),('assumptions','فرض‌های پشت تصمیم','Underlying assumptions'),('validation','شاهدی که لازم داریم','Evidence we need'),('revisit','چه وقت تغییرش بدهیم؟','When to revisit')]
    for d in data['adrs']:
        status = twin('پذیرفته‌شده' if d['status']=='accepted' else 'پیشنهادی','Accepted' if d['status']=='accepted' else 'Proposed')
        decisions += f'<details class="adr-record" id="{d["id"]}" data-status="{d["status"]}"><summary><bdi class="adr-id">{d["id"]}</bdi><span class="adr-title">'+twin(*d['title'])+'<span class="adr-preview">'+twin(*adr_copy(d['choice']))+'</span></span><span class="adr-status">'+status+'</span>'+icon('plus')+'</summary><div class="adr-body">'
        for key,fa,en in field_names:
            decisions += f'<div class="adr-field adr-{key}"><h4>'+twin(fa,en)+'</h4>'+p(*adr_copy(d[key]))+'</div>'
        decisions += '<div class="adr-footer"><p>'+twin('فصل‌های مرتبط: ','Related chapters: ')+', '.join(f'<a href="#chapter-{n}">{n}</a>' for n in d['chapters'])+f'</p><a href="adrs/{d["id"]}.md" class="workshop-link">'+twin('فایل تصمیم‌نامه','Decision record file')+icon('download')+'</a></div></div></details>'
    decisions += '</div>'+disclosure('قرارداد کامل SLO و روش سنجش','The complete SLO contract and measurement method',p('مثال ADR-003: صورتِ کسر، درخواست موفق با اولین token مفید در حداکثر ۳ ثانیه؛ مخرج، همهٔ درخواست‌های تعاملی واجد شرایط، شامل deadline و خطای provider؛ پنجره ۷ روز؛ هدف پیشنهادی ۹۵٪؛ بارِ آزمون E03 و E10. admission و پایانِ agent معیارهای جدا می‌خواهند. پیامِ loading، token مفید نیست.','ADR-003: numerator = successful useful-first-token responses within 3 seconds; denominator = all eligible interactive requests, including deadlines/provider errors; window = 7 days; proposed target = 95%; test workload = E03 and E10. Admission and completion require separate metrics. Loading messages do not count as useful tokens.')+p('جمعِ بودجه‌ها، p95 سرتاسری را اثبات نمی‌کند. اگر احتمال عبور هر یک از پنج جزء از بودجه‌اش حداکثر ۱٪ باشد، union bound عبور هر جزء را حداکثر ۵٪ کران می‌دهد؛ این شرایط باید در همان بار اندازه‌گیری شوند. خطاها نیز از همان بودجهٔ ۵٪ مصرف می‌کنند؛ پس این کرانِ latency اثباتِ SLO نیست.','Adding allocations does not prove end-to-end p95. If each of five components exceeds its allocation with probability at most 1%, a union bound limits any violation to 5%; these conditions need same-workload measurements. Errors consume that same 5% budget, so this latency bound does not prove the SLO.')+'<p><a href="https://sre.google/workbook/implementing-slos/" target="_blank" rel="noopener">Google SRE · Implementing SLOs</a> · <a href="https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html" target="_blank" rel="noopener">AWS · ADR process</a></p>')+'</section>'

    flow = '<section id="architecture" class="workshop-section">'+heading('04','یک درخواست را دنبال کنیم','Follow one request')+p('هر بلوک باید پاسخی به یک نیاز باشد. این مسیرِ دوازده‌گامی، طرح پیشنهادی را توضیح می‌دهد؛ درخواست واقعی به مدل، پایگاه داده یا ابزار نمی‌فرستد.','Every component must answer a need. This twelve-step path explains the proposed design; it sends no real requests to a model, database, or tool.')+'<div class="flow-player" id="flow-player"><div class="flow-stage"><svg id="platform-flow-svg" viewBox="0 0 900 580" role="img" aria-labelledby="flow-svg-title flow-svg-desc"><title id="flow-svg-title">Proposed AI platform request flow</title><desc id="flow-svg-desc">Developer, API, durable run store, runtime, model gateway, provider, tool gateway and data. An illustrative simulation.</desc></svg></div><div class="flow-caption" aria-live="polite"><span class="flow-position" data-flow-counter></span><p class="flow-route" dir="ltr" data-flow-route></p><h3 data-flow-title></h3><p data-flow-explanation></p><a class="workshop-link" data-flow-adr href="#ADR-001">ADR-001</a></div><div class="flow-toolbar"><button type="button" data-flow-play class="langbtn" aria-pressed="false">'+icon('play')+'<span data-flow-play-label>'+twin('پخش فلو','Play flow')+'</span></button><div class="flow-manual"><button type="button" data-flow-prev class="quiet-button">'+icon('next')+twin('گام قبل','Previous')+'</button><button type="button" data-flow-next class="quiet-button">'+twin('گام بعد','Next')+icon('next')+'</button><button type="button" data-flow-reset class="quiet-button">'+icon('reset')+twin('از ابتدا','Restart')+'</button></div></div></div><p class="flow-note">'+twin('پخش با انتخاب تو شروع می‌شود. نشانِ متحرک محل گام را توضیح می‌دهد؛ زمان حرکت، تأخیر واقعی نیست. در حالت کاهش حرکت، گام‌ها ثابت عوض می‌شوند.','Playback starts on request. The marker explains the current step; travel time is not actual latency. Reduced-motion mode uses static step changes.')+'</p><noscript><p>'+twin('برای پخش JavaScript لازم است؛ متن و نمودارهای مرجع قابل‌خواندن‌اند.','JavaScript enables playback; text and reference diagrams remain readable.')+'</p></noscript></section>'
    return start+estimates+decisions+flow
