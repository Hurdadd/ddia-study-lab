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
  'تأییدشده: کاربر اصلی توسعه\u200cدهنده است. می\u200cخواهد یک app را ثبت کند، ورودی بدهد و نتیجه و trace بگیرد. از '
  'همین یک جمله هنوز نمی\u200cشود گفت Kafka یا GPU لازم است.',
  'Confirmed: the primary user is a developer. They want to register an app, feed it input, and get a result and a trace back. One sentence like that '
  'doesn\'t yet tell us we need Kafka or a GPU.',
  'یک user story با ورودی، خروجی و معیار موفقیت بنویسیم؛ «agent همه\u200cکاره» معیار قابل\u200cآزمون نیست — این دام معروفه.',
  'We write one user story with input, output, and a success criterion. An “all-purpose agent” is not a testable requirement — that\'s the classic trap.'],
 ['مرز نسخهٔ اول',
  'First-version boundary',
  'پیشنهاد ADR-002 اینه: یک مسیر کوچک از ثبت app تا اجرای یک مدل و یک ابزار خواندنی. پنج قابلیت، مقصد پروژه\u200cاند؛ '
  'هیچ\u200cکدام با دیدن نمودار پیاده\u200cسازی\u200cشده حساب نمی\u200cشود.',
  'ADR-002 proposes one small path: from registering an app to running one model and one read-only tool. The five capabilities are the destination; none of them counts as implemented '
  'just because you saw a diagram.',
  'فرض کن می\u200cخواهی شروع کنی: در demo اول واقعاً چه چیزی را می\u200cتوانیم اجرا کنیم و عمداً خرابش کنیم؟ این scope باید قبل از انتخاب ابزار روشن شود — وگرنه ابزار را اشتباهی انتخاب می\u200cکنیم.',
  'Picture yourself starting: in the first demo, what can we actually run and deliberately break? That scope has to be clear before picking tools, otherwise you pick the wrong ones.'],
 ['نیازهای رفتاری',
  'Functional needs',
  'ثبت app، شناخت توسعه\u200cدهنده، پذیرش run، فراخوانی مدل/ابزار، برگرداندن نتیجه و دیدن وضعیت. برای هرکدام یک acceptance '
  'example می\u200cنویسیم.',
  'Register the app, know who the developer is, admit the run, call the model or tool, return the result, expose the state. For each of '
  'those we write one acceptance example.',
  'نیاز اینه: «retry پاسخ گم\u200cشده نباید run جدید بسازد». راه\u200cحل پیشنهادیِ بعدی: idempotency key و قید یکتا. نیاز را با ابزار '
  'یکی نکنیم — حساب کن.',
  'The need is this: “a retry after a lost response must not create a new run.” The candidate solution comes later: an idempotency key plus a uniqueness '
  'constraint. Don\'t mix the need up with the tool — count on it.'],
 ['بار و تخمین',
  'Workload and estimates',
  'دفتر E01–E12 فرض\u200cها را ثبت می\u200cکند. میانگین روزانه، burst کوتاه و سناریوی یک میلیون سند، سه workload '
  'متفاوت\u200cاند. تا اندازه\u200cگیری نکرده\u200cایم، همهٔ عددها تخمین\u200cاند.',
  'The E01–E12 workbook holds the assumptions. The daily average, the short burst, and the million-document scenario are three different workloads. '
  'Until we\'ve measured, every number stays an estimate.',
  'حجم، token، حافظه و هزینه را با فرمول حساب می\u200cکنیم؛ اگر جواب با بودجه نخواند، scope یا معماری را عوض می\u200cکنیم. اول عدد، بعد تصمیم.',
  'We do the volume, token, memory, and cost math with a formula; if the answer doesn\'t fit the budget, we change scope or architecture. Number first, decision second.'],
 ['کیفیت و خط قرمزها',
  'Quality and invariants',
  'اول مشخص کنیم کدام یک مهم است: admission، اولین token، یا پایان run. بعد SLI، بار، پنجره، denominator، هدف و روش آزمون را '
  'تعریف می‌کنیم.',
  'First we pick which one matters: admission, the first token, or the end of the run. Then we define the SLI, the load, the window, the denominator, the target, '
  'and how we\'ll test it.',
  'ADR-003 سه ثانیه را فرضِ TTFT می\u200cگیرد. این عدد نه از DDIA آمده، نه از تجربهٔ کاربر اندازه\u200cگیری شده — پس فرض است، نه استاندارد. یادت '
  'باشه.',
  'ADR-003 takes three seconds as a TTFT hypothesis. That number comes neither from DDIA nor from measured user experience, so it\'s an assumption, not a standard. Remember that.'],
 ['گزینه\u200cها و ADR',
  'Alternatives and ADRs',
  'برای هر انتخابِ مهم مسئله این\u200cها را ثبت می\u200cکنیم: گزینه\u200cها، دلیل، اثر منفی، فرض، آزمون و شرط بازنگری. یادت باشه، Proposed '
  'با Accepted فرق دارد.',
  'For every important choice we record the alternatives, the rationale, the downside, the assumptions, the validation, and the revisit trigger. Keep this in mind: Proposed '
  'and Accepted are not the same thing.',
  'فعلاً فقط انتخاب مخاطب پذیرفته شده است. ADRهای فنی پیشنهادی\u200cاند و با آزمایش یا گفت\u200cوگو عوض می\u200cشوند — پس روی همین\u200cها نگهشان '
  'داریم.',
  'So far only the audience choice is accepted. The technical ADRs are proposals, and they change with testing or discussion, so we hold them loosely.'],
 ['رسم فلو، سپس ساخت',
  'Draw the flow, then implement',
  'بعد از این گام\u200cها، بلوک\u200cها و مرزِ داده را رسم می\u200cکنیم. انیمیشن پایین فقط یک درخواستِ فرضی را روی طرح پیشنهادی دنبال می\u200cکند — پس '
  'با آن شواهد واقعی حساب نکن.',
  'After those stages we draw the components and the data boundaries. The animation below follows a hypothetical request through the proposed design, so don\'t count '
  'it as real evidence.',
  'پس از پذیرش scope و ADRهای لازم، اولین slice را می\u200cسازیم، crash تزریق می\u200cکنیم و نتیجهٔ واقعی را جای فرض\u200cها می\u200cگذاریم. فرض باید بمیرد تا '
  'نتیجه بیاید — حساب کن.',
  'Once scope and the required ADRs are accepted, we build the first slice, inject crashes, and put real results where the assumptions were. The assumption has to die before the result '
  'can arrive — count on it.']]

FORMULAS = [[['token روزانه', 'Daily tokens'],
  ['E01×E02×(input+output)=۱٫۶M token/day.', 'E01×E02×(input+output)=1.6M tokens/day.'],
  ['retry، context طولانی و reasoning اضافه جدا اندازه\u200cگیری می\u200cشوند — قاطی\u200cشان نکن.',
   'Measure retries, longer context, and extra reasoning separately, not lumped together.']],
 [['هزینهٔ پایلوت', 'Pilot cost'],
  ['۱٫۲M input×$1/M + ۰٫۴M output×$4/M = $2.80/day؛ $84 در ۳۰روز.',
   '1.2M input×$1/M + 0.4M output×$4/M = $2.80/day; $84/30 days.'],
  ['E09 قیمت فرضی است؛ infra، embedding، retry و مالیات داخل این عدد نمی‌آیند.',
   'E09 is hypothetical; infrastructure, embeddings, retries, and taxes stay outside that number.']],
 [['burst در inference', 'Inference burst'],
  ['۲۰ run/min×۸×۲۰۰۰ = ۵۳۳۳ token/s میانگینِ بازه؛ حدود $33.60/hour اگر یک ساعت ادامه یابد.',
   '20 runs/min×8×2000 = 5333 tokens/s over the interval; about $33.60/hour if sustained.'],
  ['E10 فقط ۵ دقیقه است؛ با هزینهٔ پایلوت جمع یا جایگزینش نکن.',
   'E10 lasts five minutes; don\'t add it to, or swap it for, the pilot\'s daily spend.']],
 [['حافظهٔ vector', 'Vector memory'],
  ['۱M×۴×۱۵۳۶×۴byte = 24.576 GB خام؛ دو نسل با factor1.5 ≈73.728 GB.',
   '1M×4×1536×4 bytes = 24.576GB raw; two generations at factor 1.5 ≈73.728GB.'],
  ['E04–E06؛ text، metadata، WAL و replica جدا حساب می\u200cشوند؛ GB ده\u200cدهی است.',
   'E04–E06; text, metadata, WAL, and replicas are extra, and the GB figure is decimal.']],
 [['log نگهداری\u200cشده', 'Retained log'],
  ['۵×۲۰۰۰×۸۶۴۰۰×۷×۳×۱٫۵ = 27.216 GB.', '5×2000×86400×7×3×1.5 = 27.216GB.'],
  ['E07–E08؛ compression را نادیده گرفتیم و telemetry خارج این حساب است.',
   'E07–E08; compression ignored, and telemetry is outside this account.']],
 [['seed و catch-up', 'Seed and catch-up'],
  ['۱M/۱۰۰=۱۰۰۰۰s؛ backlog=۵۰۰۰۰؛ با μ=۳۰ و λ=۵، catch-up=۲۰۰۰s.',
   '1M/100=10000s; backlog=50000; at μ=30 and λ=5, catch-up=2000s.'],
  ['اگر μ≤λ باشد catch-up تمام نمی\u200cشود؛ snapshot باثبات و WAL کافی جدا لازم داریم.',
   'Catch-up never finishes if μ≤λ; stable snapshots and enough WAL are separate requirements.']],
 [['هم\u200cزمانی', 'Concurrency'],
  ['با نرخ ۲۰/۶۰ run/s و میانگین زمان ۳۰s، Little: L=λW≈۱۰ run.',
   'At 20/60 runs/s and mean duration 30s, Little’s law gives L=λW≈10 runs.'],
  ['۳۰s فرضِ میانگین است، نه p95 یا حداکثر؛ این رابطه فقط برای بازهٔ تقریباً پایدار درست است.',
   '30s is an assumed mean, not p95 or max, and the relation only holds for a roughly stable interval.']],
 [['حافظهٔ GPU', 'GPU memory'],
  ['۷B×۲byte ≈13.04GiB وزن؛ KV فرضی =2×32×8×128×2×4096×4byte =2GiB.',
   '7B×2 bytes ≈13.04GiB weights; hypothetical KV =2×32×8×128×2×4096×4 bytes =2GiB.'],
  ['layers=32، KV heads=8، head dim=128، batch=4؛ activation، workspace و fragmentation جدا حساب می‌شوند. fit شدن روی ۲۴GiB هنوز اثبات '
   'نشده.',
   '32 layers, 8 KV heads, head dim128, batch4; activations, workspace, and fragmentation are extra. Fitting it in 24GiB is still '
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
        [('پاسخِ پذیرش گم می‌شود','The admission response is lost'),('retry همان run را برگرداند','A retry returns the same run'),('شناسهٔ run قبل و بعد یکیه','The run ID stays the same')],
        [('<bdi dir="ltr">100 runs × 8 calls × 2000 tokens</bdi>','100 runs × 8 calls × 2000 tokens'),('۱٫۶ میلیون token در روز، فرضی','1.6M daily tokens, hypothetical'),('مقایسهٔ حساب با بودجه و بار واقعی','Compare the numbers with the budget and the real load')],
        [('برنامهٔ تعاملی؛ اولین token مفید','An interactive app; the first useful token'),('۳ ثانیه، هدفِ پیشنهادی','Three seconds, a proposed target'),('تست کاربر + اندازه‌گیری سرتاسری','User tests + end-to-end measurement')],
        [('نیاز، گزینه‌ها و محدودیت','A need, alternatives, constraints'),('یک ADR با وضعیت Proposed','An ADR marked Proposed'),('آزمونِ انتخاب و شرطِ بازنگری','A validation test and revisit trigger')],
        [('scope و تصمیم‌های لازم پذیرفته بشن','The scope and the required decisions get accepted'),('رسم مرزها، سپس اولین slice','Draw boundaries, then build a slice'),('تزریق crash و ثبت نتیجهٔ واقعی','Inject crashes and record the real result')],
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
    start = '<section id="start-here" class="workshop-section">'+heading('01','اول مسئله را بفهمیم','Understand the problem first')+p('داستان از این قراره: از نیاز توسعه‌دهنده شروع می‌کنیم؛ بعد عدد می‌گذاریم، گزینه‌ها را می‌سنجیم و معماری را رسم می‌کنیم. این هفت گام، مسیر طراحی‌اند — نه گزارشِ پیشرفتِ ساخت.','Here\'s the plan: start from the developer\'s needs, then put numbers on it, weigh the alternatives, and draw the architecture. These seven stages are the design path, not a progress report on building.')+'<p class="workshop-status">'+twin('الان در مرحلهٔ تعریف نیازها هستیم. مخاطب تأیید شده، معماری پیشنهادی است و سرویس‌های پلتفرم هنوز ساخته نشده‌اند.','Right now we\'re at the requirements stage. The audience is confirmed, the architecture is a proposal, and the platform services aren\'t built yet.')+'</p><div class="workshop-layout">'+nav+mobile+'<div class="workshop-current">'+articles+controls+'</div></div><div class="workshop-links">'+action('#estimates','فرض‌ها را حساب کنیم','Calculate the assumptions')+action('#decisions','دلیل تصمیم‌ها را بخوانیم','Read the decisions')+action('#architecture','مسیر درخواست را ببینیم','Follow a request')+'</div></section>'

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

    pilot = '<div class="estimate-scenario pilot-scenario"><div class="scenario-title"><h3>'+twin('پایلوتِ روزانه','The daily pilot')+'</h3><span>'+twin('بارِ inference','Inference demand')+'</span></div><div class="scenario-workspace"><fieldset><legend class="sr-only">'+twin('فرض‌های پایلوت روزانه','Daily pilot assumptions')+'</legend>'+fields(inputs[:4])+'</fieldset><div class="scenario-answer">'+outputs(['cost','tokens','month'])+'<p class="design-question">'+twin('پرسش طراحی: با این مصرف، بودجهٔ مدل و سقف هر run چقدر باشه؟','Design question: with this usage, what model budget and per-run cap should we set?')+'</p></div></div><p class="estimate-caveat">'+twin('E09: نرخ‌های فرضی <bdi dir="ltr">$1/M</bdi> ورودی و <bdi dir="ltr">$4/M</bdi> خروجی. زیرساخت، embedding، retry و مالیات جدا حساب می‌شن.','E09: hypothetical rates of $1/M input and $4/M output. Infrastructure, embeddings, retries, and taxes are counted separately.')+'</p></div>'
    scale = '<div class="estimate-scenario scale-scenario"><div class="scenario-title"><h3>'+twin('وقتی داده بزرگ می‌شود','When the data grows')+'</h3><span>'+twin('سناریوی مقیاس','Scale scenario')+'</span></div><div class="scenario-workspace"><fieldset><legend class="sr-only">'+twin('فرض‌های مقیاس داده','Data scale assumptions')+'</legend>'+fields(inputs[4:])+'<p class="estimate-caveat">'+twin('ثابت‌های این سناریو: ۴ chunk در سند، ۱۵۳۶ بعد، float32، پنج تغییر در ثانیه و پردازش ۳۰ تغییر در ثانیه.','The constants behind this scenario: 4 chunks per document, 1536 dimensions, float32, 5 changes/s, and processing at 30 changes/s.')+'</p></fieldset><div class="scenario-answer">'+outputs(['vectors','generations','snapshot','backlog','catchup'])+'<p class="design-question">'+twin('پرسش طراحی: حافظه، retention و سرعت پردازش برای رسیدن به دادهٔ زنده کافی‌ان؟','Design question: do we have enough memory, retention, and processing speed to catch up with the live data?')+'</p></div></div></div>'
    form = '<form id="estimate-form">'+pilot+scale+'<div class="estimate-submit"><button type="submit" class="langbtn">'+twin('محاسبهٔ دوباره','Recalculate')+icon('reset')+'</button><p>'+twin('ورودی‌ها رو عوض کن؛ خروجی‌ها دوباره حساب می‌شن. این حسابه، نه benchmark.','Change the inputs and the outputs recompute. This is arithmetic, not a benchmark.')+'</p></div></form><p id="estimate-error" role="alert" hidden></p>'
    equations = [
        ('مصرف روزانه','Daily usage','100 × 8 × (1500 + 500) = 1,600,000 tokens/day','E01 × E02 × E03','retry و context طولانی‌تر جدا حساب می‌شن.','Retries and longer contexts are counted separately.'),
        ('هزینهٔ مدل','Model cost','1.2M × $1/M + 0.4M × $4/M = $2.80/day','E01–E03 · E09','این نرخ‌ها نمونه‌ان؛ قیمتِ یه provider نیستن.','These rates are illustrative, not any provider\'s prices.'),
        ('حافظهٔ خامِ بردارها','Raw vector memory','1,000,000 × 4 × 1536 × 4 B = 24.576 GB','E04–E06','متن، metadata، WAL و replica جدا حساب می‌شن؛ و GB ده‌دهیه.','Text, metadata, WAL, and replicas are extra, and the GB figure is decimal.'),
        ('رسیدن به جریان زنده','Catching up','50,000 ÷ (30 − 5) = 2,000 s ≈ 33.33 min','E04 · E07','سرعت پردازش باید از ورود تغییرها بیشتر باشه.','Processing has to be faster than the changes coming in.'),
    ]
    derivations = '<div class="worked-equations">'+''.join('<div class="worked-equation"><h4>'+twin(fa,en)+f'<bdi class="assumption-id">{ids}</bdi></h4><p class="equation" dir="ltr">{eq}</p><p class="equation-limit">'+twin(cfa,cen)+'</p></div>' for fa,en,eq,ids,cfa,cen in equations)+'</div>'
    formula_table = table([('خروجی','Output'),('فرمول و عددِ سناریو','Formula and scenario result'),('فرض و محدودیت','Assumption and limit')],[[row[0], ('<bdi dir="ltr">'+row[1][1]+'</bdi>', '<bdi dir="ltr">'+row[1][1]+'</bdi>'), row[2]] for row in FORMULAS])
    assumptions = table([('شناسه','ID'),('فرض','Assumption'),('عدم‌قطعیت','Uncertainty')],[[(d['id'],d['id']),tuple(d['value']),tuple(d['uncertainty'])] for d in data['assumptions']])
    estimates = '<section id="estimates" class="workshop-section">'+heading('02','هر عدد، یک فرض و یک حساب','Every number needs an assumption')+p('دو سناریوی جدا رو نگاه می‌کنیم: مصرفِ یه پایلوت کوچک و حجمِ یه مجموعه‌دادهٔ بزرگ. عددها فرضی‌ان؛ شناسهٔ کنار هر ورودی هم می‌گه فرض از کجا اومده و کجا می‌شکنه.','We look at two separate scenarios: what a small pilot consumes, and how big a large dataset gets. The numbers are hypothetical, and the ID next to each input tells you where the assumption came from and where it breaks.')+form+'<h3 class="derivation-title">'+twin('این جواب‌ها از کجا می‌آیند؟','Where do these answers come from?')+'</h3>'+derivations+disclosure('همهٔ فرمول‌ها و محدودیت‌ها','All formulas and limitations',formula_table)+disclosure('دفتر ۱۲ فرضِ قابل‌بازنگری','The 12 revisitable assumptions',assumptions)+'</section>'

    # A visibly allocated budget explains the proposal; it is not measured evidence.
    allocations = [(100,'لبه','Edge'), (300,'پذیرش / صف','Admission / queue'), (250,'بازیابی context','Context'), (1900,'provider مدل','Model provider'), (450,'انتقال / حاشیهٔ ظرفیت','Transport / headroom')]
    budget_legend = '<dl class="budget-legend" id="budget-legend">'+''.join(f'<div><dt><i class="budget-key budget-part-{i}" aria-hidden="true"></i>'+twin(fa,en)+f'</dt><dd dir="ltr">{ms} ms</dd></div>' for i,(ms,fa,en) in enumerate(allocations))+'</dl>'
    slo = '<div class="slo-example"><div class="slo-question"><h3>'+twin('چرا سه ثانیه؟','Why three seconds?')+'</h3><p>'+twin('یه فرض برای تجربهٔ تعاملی؛ هنوز نیازِ اثبات‌شده نیست.','A hypothesis for the interactive experience, not a proven need yet.')+'</p><a class="workshop-link" href="#ADR-003">'+twin('استدلال و آزمون در ADR-003','Rationale and validation in ADR-003')+icon('next')+'</a></div><div class="slo-budget"><p class="budget-equation" dir="ltr">100 + 300 + 250 + 1900 + 450 = <strong>3000 ms</strong></p><div class="budget-bar" role="img" aria-label="E11 · TTFT budget" aria-describedby="budget-legend budget-note">'+''.join(f'<i style="flex:{n}" class="budget-part-{i}"></i>' for i,n in enumerate([100,300,250,1900,450]))+'</div>'+budget_legend+'<p id="budget-note">'+twin('E11؛ بودجهٔ تخصیصی و اندازه‌گیری‌نشدهٔ مسیر؛ جمعِ p95 اجزا نیست. هدف مربوط به اولین token مفیده، نه پایانِ agent.','E11: an allocated, unmeasured budget for the path — not the sum of the component p95s. The target is about the first useful token, not the end of the agent.')+'</p></div></div>'
    decisions = '<section id="decisions" class="workshop-section">'+heading('03','تصمیمی که بشود از آن دفاع کرد','Decisions you can defend')+p('هر رکورد یه سؤال داره: چه نیازی، کدوم گزینه‌ها، چرا این انتخاب، و با چه شاهدی؟ فعلاً فقط انتخاب مخاطب پذیرفته شده؛ بقیهٔ تصمیم‌های فنی رو باید با نیاز، عدد و آزمون ببینی.','Every record asks a question: which need, which alternatives, why this choice, and on what evidence? Only the audience choice is accepted so far; the rest of the technical decisions still have to face requirements, numbers, and tests.')+slo+'<div class="decision-register"><div class="register-heading"><h3>'+twin('دفتر تصمیم‌های معماری','Architecture decision register')+'</h3><p>'+twin('۱ پذیرفته‌شده · ۱۴ پیشنهادی','1 accepted · 14 proposed')+'</p></div>'
    def adr_copy(pair):
        return [pair[0].replace('≤۳۰۰۰ms', '<bdi dir="ltr">≤3000 ms</bdi>').replace('۱۰۰+۳۰۰+۲۵۰+۱۹۰۰+۴۵۰=۳۰۰۰ms', '<bdi dir="ltr">100 + 300 + 250 + 1900 + 450 = 3000 ms</bdi>'), pair[1]]

    field_names = [('context','مسئله','Context'),('options','گزینه‌های روی میز','Alternatives'),('choice','پیشنهاد فعلی','Current proposal'),('reason','دلیل انتخاب و هزینه‌اش','Rationale and trade-off'),('assumptions','فرض‌های پشت تصمیم','Underlying assumptions'),('validation','شاهدی که لازم داریم','Evidence we need'),('revisit','چه وقت تغییرش بدهیم؟','When to revisit')]
    for d in data['adrs']:
        status = twin('پذیرفته‌شده' if d['status']=='accepted' else 'پیشنهادی','Accepted' if d['status']=='accepted' else 'Proposed')
        decisions += f'<details class="adr-record" id="{d["id"]}" data-status="{d["status"]}"><summary><bdi class="adr-id">{d["id"]}</bdi><span class="adr-title">'+twin(*d['title'])+'<span class="adr-preview">'+twin(*adr_copy(d['choice']))+'</span></span><span class="adr-status">'+status+'</span>'+icon('plus')+'</summary><div class="adr-body">'
        for key,fa,en in field_names:
            decisions += f'<div class="adr-field adr-{key}"><h4>'+twin(fa,en)+'</h4>'+p(*adr_copy(d[key]))+'</div>'
        decisions += '<div class="adr-footer"><p>'+twin('فصل‌های مرتبط: ','Related chapters: ')+', '.join(f'<a href="#chapter-{n}">{n}</a>' for n in d['chapters'])+f'</p><a href="adrs/{d["id"]}.md" class="workshop-link">'+twin('فایل تصمیم‌نامه','Decision record file')+icon('download')+'</a></div></div></details>'
    decisions += '</div>'+disclosure('قرارداد کامل SLO و روش سنجش','The complete SLO contract and measurement method',p('مثال ADR-003: صورتِ کسر، درخواست موفق با اولین token مفید در حداکثر ۳ ثانیه؛ مخرج، همهٔ درخواست‌های تعاملی واجد شرایط، شامل deadline و خطای provider؛ پنجره ۷ روز؛ هدف پیشنهادی ۹۵٪؛ بارِ آزمون E03 و E10. admission و پایانِ agent معیارهای جدا می‌خوان. پیامِ loading، token مفید نیست.','ADR-003 example: the numerator is a successful request with a useful first token inside 3 seconds; the denominator is every eligible interactive request, including deadline misses and provider errors; the window is 7 days; the proposed target is 95%; the test workload is E03 and E10. Admission and agent completion each need their own metric — and a loading message is not a useful token.')+p('جمعِ بودجه‌ها p95 سرتاسری رو اثبات نمی‌کنه. اگر احتمال عبور هر یک از پنج جزء از بودجه‌اش حداکثر ۱٪ باشه، union bound عبور هر جزء رو حداکثر ۵٪ کران می‌زنه — ولی این شرایط باید روی همون بار اندازه‌گیری بشن. خطاها هم از همون بودجهٔ ۵٪ می‌خورن؛ پس این کرانِ latency اثباتِ SLO نیست.','Adding up the budgets doesn\'t prove an end-to-end p95. If each of the five components has at most a 1% chance of blowing its allocation, a union bound caps any violation at 5% — but those conditions have to be measured on the same workload. Errors eat that same 5% budget too, so this latency bound is not a proof of the SLO.')+'<p><a href="https://sre.google/workbook/implementing-slos/" target="_blank" rel="noopener">Google SRE · Implementing SLOs</a> · <a href="https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html" target="_blank" rel="noopener">AWS · ADR process</a></p>')+'</section>'

    flow = '<section id="architecture" class="workshop-section">'+heading('04','یک درخواست را دنبال کنیم','Follow one request')+p('هر بلوک باید پاسخی به یک نیاز باشد. این مسیرِ دوازده‌گامی، طرح پیشنهادی را توضیح می‌دهد؛ درخواست واقعی به مدل، پایگاه داده یا ابزار نمی‌فرستد.','Every block has to answer some need. This twelve-step path walks the proposed design; it sends no real request to a model, a database, or a tool.')+'<div class="flow-player" id="flow-player"><div class="flow-stage"><svg id="platform-flow-svg" viewBox="0 0 900 580" role="img" aria-labelledby="flow-svg-title flow-svg-desc"><title id="flow-svg-title">Proposed AI platform request flow</title><desc id="flow-svg-desc">Developer, API, durable run store, runtime, model gateway, provider, tool gateway and data. An illustrative simulation.</desc></svg></div><div class="flow-caption" aria-live="polite"><span class="flow-position" data-flow-counter></span><p class="flow-route" dir="ltr" data-flow-route></p><h3 data-flow-title></h3><p data-flow-explanation></p><a class="workshop-link" data-flow-adr href="#ADR-001">ADR-001</a></div><div class="flow-toolbar"><button type="button" data-flow-play class="langbtn" aria-pressed="false">'+icon('play')+'<span data-flow-play-label>'+twin('پخش فلو','Play flow')+'</span></button><div class="flow-manual"><button type="button" data-flow-prev class="quiet-button">'+icon('next')+twin('گام قبل','Previous')+'</button><button type="button" data-flow-next class="quiet-button">'+twin('گام بعد','Next')+icon('next')+'</button><button type="button" data-flow-reset class="quiet-button">'+icon('reset')+twin('از ابتدا','Restart')+'</button></div></div></div><p class="flow-note">'+twin('پخش با انتخاب تو شروع می‌شه. نشانِ متحرک بهت می‌گه الان کجای مسیریم؛ زمان حرکت، تأخیر واقعی نیست. با حالت کاهش حرکت، گام‌ها ثابت عوض می‌شن.','Playback starts when you press it. The moving marker shows you where the request is; the travel time is not real latency. With reduced motion on, the steps just change.')+'</p><noscript><p>'+twin('برای پخش، JavaScript لازمه؛ متن و نمودارهای مرجع در هر حالتی خوانا می‌مونن.','JavaScript is needed for playback; the text and the reference diagrams stay readable either way.')+'</p></noscript></section>'
    return start+estimates+decisions+flow
