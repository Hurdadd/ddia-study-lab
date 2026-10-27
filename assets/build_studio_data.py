#!/usr/bin/env python3
"""Generate the offline studio catalog from the maintained exercise audit."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import exercise_references
# Capacities and service times are teaching inputs, never provider benchmarks.
SPECS = [
    ('client', 'Client', 'کاربر', 'network', 1000000, 0, 'Entry point that generates the selected request rate.', 'نقطهٔ آغاز درخواست‌ها با نرخ انتخاب‌شده.'),
    ('dns', 'DNS', 'نام‌گستری', 'network', 100000, 2, 'Resolves a service name; drawn as a request dependency.', 'نام سرویس را پیدا می‌کند؛ اینجا یک وابستگی درخواست است.'),
    ('cdn', 'CDN', 'شبکهٔ تحویل محتوا', 'network', 80000, 3, 'Caches read responses near clients.', 'پاسخ خواندن را نزدیک کاربر نگه می‌دارد.'),
    ('load-balancer', 'Load balancer', 'توزیع‌کنندهٔ بار', 'network', 50000, 2, 'Splits requests equally across outgoing connections.', 'درخواست را به‌طور مساوی بین اتصال‌های خروجی تقسیم می‌کند.'),
    ('api-gateway', 'API gateway', 'درگاه API', 'network', 15000, 4, 'Routes requests and applies entry policies.', 'درخواست را هدایت و سیاست‌های ورود را اعمال می‌کند.'),
    ('rate-limiter', 'Rate limiter', 'محدودکنندهٔ نرخ', 'network', 5000, 1, 'Rejects excess load above its configured capacity.', 'بار بیشتر از ظرفیت تنظیم‌شده را رد می‌کند.'),
    ('app-server', 'Application server', 'سرور برنامه', 'compute', 2000, 15, 'Runs business logic and calls connected dependencies.', 'منطق برنامه را اجرا و وابستگی‌های متصل را فراخوانی می‌کند.'),
    ('worker', 'Stream processor / worker', 'پردازشگر جریان / کار', 'compute', 800, 25, 'Consumes work from a queue or stream.', 'کار را از صف یا جریان دریافت می‌کند.'),
    ('sql-db', 'SQL database', 'پایگاه دادهٔ رابطه‌ای', 'storage', 1000, 12, 'Stores relational records; transaction correctness needs separate analysis.', 'رکورد رابطه‌ای را نگه می‌دارد؛ صحت تراکنش تحلیل جدا می‌خواهد.'),
    ('nosql-db', 'Document database', 'پایگاه دادهٔ سندی', 'storage', 3000, 8, 'Stores documents or key-value records.', 'سند یا رکورد کلیدمقدار را نگه می‌دارد.'),
    ('cache', 'Cache', 'کش', 'storage', 12000, 2, 'Serves cacheable reads locally and forwards writes and misses.', 'خواندن‌های موفق را پاسخ می‌دهد و نوشتن و miss را عبور می‌دهد.'),
    ('object-storage', 'Object storage', 'ذخیره‌ساز شیء', 'storage', 4000, 35, 'Stores large immutable objects.', 'اشیای بزرگ و معمولاً تغییرناپذیر را نگه می‌دارد.'),
    ('file-storage', 'File storage', 'ذخیره‌ساز فایل', 'storage', 1500, 15, 'Provides a shared file dependency.', 'وابستگی فایل مشترک را نمایش می‌دهد.'),
    ('search', 'Search index', 'نمایهٔ جست‌وجو', 'storage', 2000, 20, 'Provides a derived search view.', 'نمای مشتق‌شدهٔ جست‌وجو را فراهم می‌کند.'),
    ('warehouse', 'Data warehouse', 'انبار داده', 'storage', 200, 100, 'Represents analytical query work.', 'کار پرس‌وجوی تحلیلی را نمایش می‌دهد.'),
    ('graph-db', 'Graph database', 'پایگاه دادهٔ گرافی', 'storage', 800, 18, 'Stores graph relationships.', 'رابطه‌های گراف را نگه می‌دارد.'),
    ('time-series-db', 'Time-series database', 'پایگاه دادهٔ سری زمانی', 'storage', 4000, 10, 'Stores timestamped measurements.', 'اندازه‌گیری زمان‌دار را نگه می‌دارد.'),
    ('vector-db', 'Vector index', 'نمایهٔ برداری', 'storage', 500, 30, 'Represents vector retrieval work.', 'کار بازیابی برداری را نمایش می‌دهد.'),
    ('queue', 'Message queue', 'صف پیام', 'messaging', 10000, 5, 'Buffers work; excess input is shown as backlog growth per second.', 'کار را بافر می‌کند؛ بار اضافی رشد backlog در ثانیه است.'),
    ('pubsub', 'Pub/sub', 'انتشار و اشتراک', 'messaging', 12000, 4, 'Publishes one copy to each connected subscriber.', 'یک نسخه به هر مشترک متصل می‌رساند.'),
    ('websocket', 'WebSocket service', 'سرویس وب‌سوکت', 'compute', 8000, 5, 'Represents persistent-message delivery.', 'تحویل پیام با اتصال ماندگار را نمایش می‌دهد.'),
    ('scheduler', 'Scheduler', 'زمان‌بند', 'compute', 1000, 10, 'Represents scheduled execution.', 'اجرای زمان‌بندی‌شده را نمایش می‌دهد.'),
    ('service-discovery', 'Service discovery', 'کشف سرویس', 'infra', 20000, 2, 'Represents a service registry dependency.', 'وابستگی رجیستری سرویس را نمایش می‌دهد.'),
    ('monitoring', 'Monitoring', 'پایش', 'infra', 10000, 3, 'Represents observability ingestion, not proof of availability.', 'دریافت دادهٔ پایش را نمایش می‌دهد و تضمین دسترس‌پذیری نیست.'),
    ('auth', 'Authentication', 'احراز هویت', 'compute', 3000, 10, 'Represents an identity-check dependency.', 'وابستگی بررسی هویت را نمایش می‌دهد.'),
    ('coordinator', 'Coordinator', 'هماهنگ‌کننده', 'infra', 1000, 10, 'Marks coordination; quorum and fencing are not simulated.', 'هماهنگی را مشخص می‌کند؛ quorum و fencing شبیه‌سازی نمی‌شوند.'),
    ('reverse-proxy', 'Reverse proxy', 'پراکسی معکوس', 'network', 20000, 2, 'Represents an upstream routing and connection boundary.', 'مرز مسیریابی و اتصال به بالادست را نمایش می‌دهد.'),
    ('origin-shield', 'Origin shield', 'محافظ مبدأ', 'network', 25000, 3, 'Caches upstream reads to reduce origin load.', 'خواندن بالادست را کش می‌کند تا بار مبدأ کمتر شود.'),
    ('notification-service', 'Notification service', 'سرویس اعلان', 'compute', 1200, 15, 'Dispatches user notification work.', 'کار اعلان کاربر را ارسال می‌کند.'),
    ('geospatial-index', 'Geospatial index', 'نمایهٔ مکانی', 'storage', 2000, 12, 'Represents location-index lookups.', 'جست‌وجوی نمایهٔ موقعیت را نمایش می‌دهد.'),
    ('service-mesh', 'Service mesh', 'شبکهٔ سرویس', 'infra', 20000, 2, 'Represents inter-service policy and routing.', 'سیاست و مسیریابی بین سرویس را نمایش می‌دهد.'),
    ('distributed-lock', 'Distributed lock', 'قفل توزیع‌شده', 'infra', 1000, 8, 'Marks lock coordination; lease safety and fencing need a stateful proof.', 'هماهنگی قفل را مشخص می‌کند؛ ایمنی lease و fencing اثبات وضعیت‌مند می‌خواهد.'),
    ('circuit-breaker', 'Circuit breaker', 'قطع‌کنندهٔ مدار', 'infra', 10000, 1, 'Marks a failure boundary; open/half-open transitions are not modeled.', 'مرز خرابی را مشخص می‌کند؛ گذار حالت باز و نیمه‌باز مدل نشده است.'),
    ('config-service', 'Configuration service', 'سرویس پیکربندی', 'infra', 6000, 5, 'Stores runtime configuration; rollout order is outside this model.', 'پیکربندی زمان اجرا را نگه می‌دارد؛ ترتیب انتشار بیرون این مدل است.'),
    ('id-generator', 'ID generator', 'مولد شناسه', 'infra', 10000, 2, 'Marks ID allocation; uniqueness and clock behavior require separate tests.', 'تخصیص شناسه را نمایش می‌دهد؛ یکتایی و رفتار ساعت آزمون جدا می‌خواهد.'),
    ('sharded-counter', 'Sharded counter', 'شمارندهٔ پارتیشن‌شده', 'infra', 8000, 5, 'Represents partitioned aggregation with an explicit merge contract.', 'تجمیع پارتیشن‌شده با قرارداد ادغام صریح را نمایش می‌دهد.'),
    ('custom', 'Custom component', 'جزء سفارشی', 'custom', 1000, 10, 'A named component with explicit capacity and service time.', 'جزء نام‌گذاری‌شده با ظرفیت و زمان خدمت صریح.'),
    ('note', 'Design note', 'یادداشت طراحی', 'custom', 0, 0, 'Records assumptions; cannot carry request edges.', 'فرض‌ها را ثبت می‌کند؛ در مسیر درخواست قرار نمی‌گیرد.'),
]
COLORS = {'network': '#60a5fa', 'compute': '#a78bfa', 'storage': '#34d399', 'messaging': '#fbbf24', 'infra': '#fb923c', 'custom': '#94a3b8'}
TRADEOFFS = {
    'network': ('Routing simplicity trades off against extra hops and shared entry points.', 'سادگی مسیریابی در برابر پرش اضافه و نقاط ورود مشترک.'),
    'compute': ('More execution units add capacity under ideal balancing, with operating cost and coordination overhead.', 'واحد اجرای بیشتر با توزیع ایده‌آل ظرفیت می‌دهد، اما هزینه و هماهنگی می‌خواهد.'),
    'storage': ('Access speed, freshness, durability and operational complexity must be chosen explicitly.', 'سرعت، تازگی، دوام و پیچیدگی عملیات باید صریح انتخاب شوند.'),
    'messaging': ('Buffering absorbs bursts but adds lag, retries and duplicate-handling work.', 'بافر نوسان بار را جذب می‌کند، اما lag، retry و مدیریت تکرار می‌خواهد.'),
    'infra': ('Shared infrastructure simplifies policy but creates dependencies needing failure plans.', 'زیرساخت مشترک سیاست را ساده می‌کند و برنامهٔ خرابی می‌خواهد.'),
    'custom': ('State what the abstraction omits before using its numbers to decide.', 'قبل از تصمیم با عددها، محدودیت مدل را بنویس.'),
}


def graph(types, labels=None, fanout=False):
    nodes = []
    for i, typ in enumerate(types):
        nodes.append({'id': f'n{i+1}', 'type': typ, 'label': (labels or {}).get(i, ''), 'x': 110 + (i % 4) * 240, 'y': 160 + (i // 4) * 180, 'replicas': 1, 'config': {}})
    pairs = [(i, i+1) for i in range(len(nodes)-1)]
    if fanout and len(nodes) >= 5:
        pairs = [(0, 1), (1, 2), (2, 3), (2, 4)]
    return {'nodes': nodes, 'edges': [{'id': f'e{i+1}', 'source': f'n{a+1}', 'target': f'n{b+1}', 'protocol': 'HTTPS' if a == 0 else 'RPC'} for i, (a, b) in enumerate(pairs)]}


# References are editable starting hypotheses, not model answers to correctness exercises.
TEMPLATES = {
    1: (['client', 'app-server', 'sql-db'], ['client', 'app-server', 'queue', 'search', 'warehouse'], True),
    2: (['client', 'app-server', 'sql-db'], ['client', 'load-balancer', 'app-server', 'cache', 'sql-db'], False),
    3: (['client', 'app-server', 'sql-db'], ['client', 'app-server', 'nosql-db'], False),
    4: (['client', 'app-server', 'sql-db'], ['client', 'app-server', 'cache', 'sql-db'], False),
    5: (['client', 'api-gateway', 'app-server'], ['client', 'api-gateway', 'app-server', 'queue', 'worker'], False),
    6: (['client', 'app-server', 'sql-db'], ['client', 'load-balancer', 'app-server', 'sql-db', 'sql-db'], True),
    7: (['client', 'app-server', 'time-series-db'], ['client', 'app-server', 'load-balancer', 'time-series-db', 'time-series-db'], True),
    8: (['client', 'app-server', 'sql-db'], ['client', 'app-server', 'sql-db', 'queue', 'worker'], False),
    9: (['client', 'app-server', 'custom'], ['client', 'app-server', 'rate-limiter', 'queue', 'worker'], False),
    10: (['client', 'app-server', 'coordinator'], ['client', 'app-server', 'coordinator', 'sql-db'], False),
    11: (['object-storage', 'worker', 'warehouse'], ['object-storage', 'queue', 'worker', 'object-storage', 'warehouse'], True),
    12: (['queue', 'worker', 'sql-db'], ['queue', 'worker', 'sql-db', 'search'], False),
    13: (['client', 'app-server', 'sql-db'], ['client', 'app-server', 'queue', 'sql-db', 'search'], True),
    14: (['client', 'app-server', 'sql-db'], ['client', 'auth', 'app-server', 'sql-db'], False),
}


# Original briefs covering the same public categories, not copied problem statements.
CLASSICS = [
    ('url-shortener', 'URL shortener', 'کوتاه‌کنندهٔ لینک', 'easy', 'stable aliases and collision recovery', 'نام مستعار پایدار و بازیابی برخورد کلید', ['cache', 'sql-db'], ['hashing', 'cache']),
    ('rate-limiter', 'Rate limiter', 'محدودکنندهٔ نرخ', 'easy', 'per-tenant budgets and burst admission', 'بودجهٔ هر مستأجر و پذیرش بار ناگهانی', ['rate-limiter', 'cache'], ['token bucket', 'fairness']),
    ('parking-lot', 'Parking allocation', 'تخصیص پارکینگ', 'easy', 'exclusive spot allocation and expired reservations', 'تخصیص انحصاری جا و انقضای رزرو', ['sql-db'], ['state machine', 'transactions']),
    ('notifications', 'Notification delivery', 'تحویل اعلان', 'medium', 'channel preferences, retries and duplicate suppression', 'ترجیح کانال، تلاش مجدد و حذف پیام تکراری', ['queue', 'worker', 'custom'], ['queue', 'idempotency']),
    ('typeahead', 'Typeahead search', 'پیشنهاد هنگام تایپ', 'medium', 'prefix lookup and safe index refresh', 'جست‌وجوی پیشوند و نوسازی امن نمایه', ['cache', 'search'], ['prefix', 'index']),
    ('instagram', 'Photo sharing', 'اشتراک عکس', 'medium', 'upload processing and privacy-aware feeds', 'پردازش بارگذاری و خوراک با رعایت حریم خصوصی', ['queue', 'worker', 'object-storage'], ['media', 'feed']),
    ('spotify', 'Music streaming', 'پخش موسیقی', 'medium', 'playlists, offline sync and audio delivery', 'فهرست پخش، همگام‌سازی آفلاین و تحویل صوت', ['cdn', 'object-storage'], ['streaming', 'offline']),
    ('distributed-cache', 'Distributed cache', 'کش توزیع‌شده', 'medium', 'key placement, eviction and hot-key pressure', 'جای کلید، بیرون‌اندازی و فشار کلید داغ', ['load-balancer', 'cache'], ['hashing', 'hot keys']),
    ('tinder', 'Proximity matching', 'تطبیق بر پایهٔ نزدیکی', 'medium', 'location freshness, mutual matches and ranking', 'تازگی موقعیت، تطبیق دوطرفه و رتبه‌بندی', ['nosql-db'], ['geo', 'ranking']),
    ('reddit', 'Discussion community', 'جامعهٔ گفت‌وگو', 'medium', 'thread trees, moderation and vote aggregation', 'درخت گفت‌وگو، نظارت و تجمیع رأی', ['cache', 'sql-db'], ['ranking', 'moderation']),
    ('yelp', 'Local reviews', 'نظر دربارهٔ کسب‌وکار محلی', 'medium', 'nearby search and trustworthy review aggregates', 'جست‌وجوی نزدیک و تجمیع قابل اعتماد نظرها', ['search', 'sql-db'], ['geo', 'aggregation']),
    ('twitter', 'News feed', 'خوراک خبر', 'hard', 'celebrity fan-out and chronological freshness', 'انتشار برای دنبال‌کنندگان زیاد و تازگی زمانی', ['queue', 'worker', 'cache'], ['fan-out', 'timeline']),
    ('chat', 'Chat delivery', 'تحویل پیام گفت‌وگو', 'hard', 'conversation ordering, reconnects and delivery receipts', 'ترتیب گفت‌وگو، اتصال مجدد و رسید تحویل', ['websocket', 'queue', 'nosql-db'], ['ordering', 'WebSocket']),
    ('web-crawler', 'Web crawler', 'خزندهٔ وب', 'medium', 'frontier scheduling, host politeness and deduplication', 'زمان‌بندی frontier، رعایت میزبان و حذف تکرار', ['queue', 'worker', 'object-storage'], ['frontier', 'dedup']),
    ('dropbox', 'File synchronization', 'همگام‌سازی فایل', 'hard', 'chunk transfer, concurrent edits and conflict recovery', 'انتقال قطعه، ویرایش هم‌زمان و بازیابی تعارض', ['object-storage', 'sql-db'], ['chunks', 'sync']),
    ('ecommerce', 'E-commerce checkout', 'پرداخت فروشگاه', 'hard', 'inventory holds and a partially failed checkout', 'نگه‌داشت موجودی و پرداخت نیمه‌کاره', ['sql-db', 'queue', 'worker'], ['saga', 'inventory']),
    ('slack', 'Team messaging', 'پیام‌رسان تیمی', 'hard', 'workspace isolation, channel history and search', 'جداسازی فضای کاری، تاریخچهٔ کانال و جست‌وجو', ['websocket', 'queue', 'search'], ['tenancy', 'search']),
    ('code-editor', 'Online code editor', 'ویرایشگر کد آنلاین', 'medium', 'isolated execution and concurrent workspace edits', 'اجرای جداشده و ویرایش هم‌زمان فضای کار', ['queue', 'worker', 'object-storage'], ['sandbox', 'collaboration']),
    ('cicd', 'CI/CD pipeline', 'خط لولهٔ CI/CD', 'medium', 'dependency scheduling, reproducible artifacts and rollback', 'زمان‌بندی وابستگی، خروجی بازتولیدپذیر و بازگشت', ['queue', 'worker', 'object-storage'], ['DAG', 'artifacts']),
    ('digital-wallet', 'Digital wallet', 'کیف پول دیجیتال', 'hard', 'balanced ledger entries and transfer reconciliation', 'توازن دفترکل و تطبیق انتقال', ['sql-db', 'queue'], ['ledger', 'reconciliation']),
    ('uber', 'Ride matching', 'تطبیق سفر', 'hard', 'driver positions, offer acceptance and rematching', 'موقعیت راننده، قبول پیشنهاد و تطبیق مجدد', ['cache', 'nosql-db'], ['geo', 'dispatch']),
    ('youtube', 'Video hosting', 'میزبانی ویدئو', 'hard', 'resumable uploads, transcoding and playback delivery', 'ادامهٔ بارگذاری، تبدیل ویدئو و تحویل پخش', ['queue', 'worker', 'object-storage', 'cdn'], ['transcoding', 'CDN']),
    ('payments', 'Payment processing', 'پردازش پرداخت', 'hard', 'idempotent charges and uncertain provider outcomes', 'برداشت idempotent و نتیجهٔ نامعلوم ارائه‌دهنده', ['sql-db', 'queue', 'custom'], ['idempotency', 'reconciliation']),
    ('ticket-booking', 'Ticket booking', 'رزرو بلیت', 'hard', 'seat exclusivity, fair waiting and expiring holds', 'انحصار صندلی، انتظار منصفانه و انقضای نگه‌داشت', ['queue', 'worker', 'sql-db'], ['locking', 'fairness']),
    ('google-docs', 'Collaborative documents', 'سند مشارکتی', 'hard', 'offline concurrent edits and convergence', 'ویرایش هم‌زمان آفلاین و همگرایی', ['websocket', 'queue', 'nosql-db'], ['CRDT', 'OT']),
    ('monitoring', 'Metrics and monitoring', 'معیارها و پایش', 'hard', 'high-cardinality ingestion and actionable alerting', 'دریافت دادهٔ پرکاردینال و هشدار قابل اقدام', ['queue', 'worker', 'time-series-db'], ['cardinality', 'alerts']),
    ('netflix', 'Subscription video', 'ویدئوی اشتراکی', 'hard', 'playback authorization, adaptive delivery and viewing progress', 'مجوز پخش، تحویل تطبیقی و پیشرفت تماشا', ['auth', 'cdn', 'object-storage'], ['streaming', 'authorization']),
    ('google-maps', 'Maps and routing', 'نقشه و مسیریابی', 'hard', 'tile caching, road updates and route recomputation', 'کش کاشی، به‌روزرسانی راه و محاسبهٔ مجدد مسیر', ['cdn', 'cache', 'graph-db'], ['routing', 'tiles']),
    ('zoom', 'Video conferencing', 'کنفرانس ویدئویی', 'hard', 'room placement, congestion and reconnect handling', 'جای‌گذاری اتاق، ازدحام و اتصال مجدد', ['websocket', 'app-server'], ['WebRTC', 'SFU']),
    ('food-delivery', 'Food delivery', 'تحویل غذا', 'hard', 'order lifecycle, courier assignment and cancellation races', 'چرخهٔ سفارش، تخصیص پیک و رقابت لغو', ['queue', 'worker', 'sql-db'], ['dispatch', 'state machine']),
    ('airbnb', 'Accommodation booking', 'رزرو اقامتگاه', 'hard', 'calendar availability, payment expiry and double-booking prevention', 'دسترس‌پذیری تقویم، انقضای پرداخت و جلوگیری از رزرو تکراری', ['search', 'sql-db'], ['calendar', 'transactions']),
    ('whatsapp', 'Private messaging', 'پیام‌رسان خصوصی', 'hard', 'multi-device delivery, encrypted payloads and key changes', 'تحویل چنددستگاهی، محتوای رمز‌شده و تغییر کلید', ['websocket', 'queue', 'nosql-db'], ['encryption', 'delivery']),
    ('google-search', 'Web search', 'جست‌وجوی وب', 'hard', 'incremental crawling, inverted indexes and query ranking', 'خزش افزایشی، نمایهٔ معکوس و رتبه‌بندی پرس‌وجو', ['queue', 'worker', 'search'], ['ranking', 'index']),
    ('tiktok', 'Short-video feed', 'خوراک ویدئوی کوتاه', 'hard', 'video ingestion, recommendation feedback and abuse controls', 'دریافت ویدئو، بازخورد پیشنهاد و کنترل سوءاستفاده', ['queue', 'worker', 'vector-db'], ['recommendation', 'media']),
    ('kafka', 'Durable event log', 'لاگ رویداد بادوام', 'hard', 'partition ordering, consumer offsets and replay after failure', 'ترتیب پارتیشن، offset مصرف‌کننده و بازپخش پس از خرابی', ['queue', 'worker', 'sql-db'], ['consumer groups', 'delivery semantics']),
]

COMPARISONS = [
    ('sql-nosql', 'SQL vs NoSQL', 'SQL یا NoSQL', 'Choose around invariants and access patterns; neither label alone specifies consistency or scale.', 'انتخاب را بر اساس invariant و الگوی دسترسی انجام بده؛ هیچ‌کدام به‌تنهایی سازگاری یا مقیاس را مشخص نمی‌کند.'),
    ('push-pull', 'Push vs pull fan-out', 'انتشار push یا pull', 'Push pays on writes and serves cheap reads; pull saves write work but assembles reads. Measure skew.', 'push هنگام نوشتن هزینه می‌دهد و خواندن را ارزان می‌کند؛ pull کار نوشتن را کم می‌کند و خواندن را می‌سازد. چولگی را اندازه بگیر.'),
    ('sync-async', 'Synchronous vs asynchronous', 'همگام یا ناهمگام', 'Waiting exposes dependency latency; buffering adds lag and requires retries, backpressure and idempotency.', 'انتظار تأخیر وابستگی را آشکار می‌کند؛ بافر lag می‌آورد و retry، backpressure و idempotency می‌خواهد.'),
    ('strong-eventual', 'Strong vs eventual consistency', 'سازگاری قوی یا نهایی', 'Name the actual guarantee and failure model. Eventual convergence does not promise a freshness bound.', 'تضمین دقیق و مدل خرابی را نام ببر. همگرایی نهایی کران تازگی را تضمین نمی‌کند.'),
    ('monolith-services', 'Monolith vs microservices', 'یکپارچه یا ریزسرویس', 'Separate deployability can justify services; network failures and distributed transactions add operating work.', 'استقرار مستقل می‌تواند سرویس را توجیه کند؛ خرابی شبکه و تراکنش توزیع‌شده کار عملیات را زیاد می‌کند.'),
    ('rest-grpc', 'REST vs gRPC', 'REST یا gRPC', 'Compare browser reach, schema evolution, streaming and tooling before transport overhead.', 'دسترسی مرورگر، تکامل schema، جریان و ابزارها را پیش از سربار انتقال مقایسه کن.'),
    ('cache-aside-through', 'Cache-aside vs write-through', 'کش کنارگذاشته یا نوشتن از مسیر کش', 'Cache-aside fills on demand; write-through pays write latency. Both need explicit invalidation and failure contracts.', 'cache-aside در تقاضا پر می‌شود؛ write-through تأخیر نوشتن می‌دهد. هر دو قرارداد ابطال و خرابی می‌خواهند.'),
    ('vertical-horizontal', 'Vertical vs horizontal scale', 'مقیاس عمودی یا افقی', 'A larger machine avoids coordination until its limits; more machines require partitioning or shared-state discipline.', 'ماشین بزرگ‌تر تا سقف ظرفیت هماهنگی را کم می‌کند؛ ماشین بیشتر پارتیشن‌بندی یا انضباط وضعیت مشترک می‌خواهد.'),
    ('polling-websocket', 'Polling vs WebSocket', 'polling یا وب‌سوکت', 'Polling simplifies reconnects but repeats requests; persistent sockets need connection ownership and backpressure.', 'polling اتصال مجدد را ساده می‌کند و درخواست تکرار می‌کند؛ اتصال ماندگار مالکیت و backpressure می‌خواهد.'),
    ('single-multi-leader', 'Single vs multi-leader', 'یک رهبر یا چند رهبر', 'One write authority simplifies conflict order; local multi-leader writes need a conflict and deletion policy.', 'یک مرجع نوشتن ترتیب تعارض را ساده می‌کند؛ چند رهبر محلی سیاست تعارض و حذف می‌خواهد.'),
    ('hash-range', 'Hash vs range partitioning', 'پارتیشن‌بندی hash یا range', 'Hash spreads many keys but hurts range scans; ranges preserve locality and can create hot partitions.', 'hash کلیدهای فراوان را پخش و پیمایش بازه را سخت می‌کند؛ range محلی‌بودن را حفظ می‌کند و ممکن است داغ شود.'),
    ('cdn-push-pull', 'CDN push vs pull', 'CDN با push یا pull', 'Pre-positioning spends bandwidth before demand; pull waits for first access and needs origin protection.', 'پیش‌جای‌گذاری پیش از تقاضا پهنای باند خرج می‌کند؛ pull منتظر اولین دسترسی می‌ماند و حفاظت origin می‌خواهد.'),
    ('bucket-window', 'Token bucket vs sliding window', 'سطل توکن یا پنجرهٔ لغزان', 'A token bucket explicitly permits bounded bursts; window counters approximate history with different memory costs.', 'سطل توکن burst محدود را صریح مجاز می‌کند؛ شمارندهٔ پنجره تاریخچه را با هزینهٔ حافظهٔ متفاوت تخمین می‌زند.'),
    ('delivery-semantics', 'At-least-once vs exactly-once effects', 'تحویل حداقل یک بار یا اثر دقیقاً یک بار', 'Retries may redeliver. Exactly-once effects need a defined boundary, durable deduplication and atomic state changes.', 'retry می‌تواند پیام را دوباره برساند. اثر دقیقاً یک بار مرز مشخص، حذف تکرار بادوام و تغییر وضعیت اتمی می‌خواهد.'),
]

# Static shipped-data facts, decoded without target execution from the captured SysDes
# bundle-10/11. Exact provenance: .local-backups/sysdes-reference/behavior-ledger.md.
ORIGINAL_DATA = {'components': [{'id': 'dns',
                 'label': 'DNS',
                 'category': 'networking',
                 'icon': 'Globe',
                 'maxQPS': 100000,
                 'latencyMs': 10,
                 'scalable': True,
                 'stateful': False,
                 'description': 'Domain Name System — resolves human-readable domain names (e.g., example.com) to IP '
                                'addresses. Every internet request starts with a DNS lookup, making it the first hop '
                                'in any system design. Services like AWS Route 53 and Google Cloud DNS also support '
                                'health-checked routing and geo-based load balancing.'},
                {'id': 'cdn',
                 'label': 'CDN',
                 'category': 'networking',
                 'icon': 'Cloudy',
                 'maxQPS': 500000,
                 'latencyMs': 15,
                 'scalable': True,
                 'stateful': False,
                 'description': 'Content Delivery Network — caches static assets (images, JS, CSS, videos) at edge '
                                'locations close to users, reducing latency from hundreds of milliseconds to low '
                                'double digits. Essential for any read-heavy or media-heavy system serving a global '
                                'audience. Examples include Amazon CloudFront, Google Cloud CDN, and Cloudflare.'},
                {'id': 'load-balancer',
                 'label': 'Load Balancer',
                 'category': 'networking',
                 'icon': 'Network',
                 'maxQPS': 1000000,
                 'latencyMs': 1,
                 'scalable': True,
                 'stateful': False,
                 'description': 'Distributes incoming traffic across multiple backend servers using algorithms like '
                                'round-robin, least-connections, or weighted routing. Prevents any single server from '
                                'becoming a bottleneck and enables zero-downtime deployments via rolling updates. AWS '
                                'ALB/NLB, Google Cloud Load Balancing, and HAProxy are common choices.'},
                {'id': 'api-gateway',
                 'label': 'API Gateway',
                 'category': 'networking',
                 'icon': 'Router',
                 'maxQPS': 50000,
                 'latencyMs': 10,
                 'scalable': True,
                 'stateful': False,
                 'description': 'Single entry point for all API requests — handles routing, authentication, rate '
                                'limiting, request transformation, and protocol translation. Use it when you have '
                                'multiple microservices behind a unified API surface. AWS API Gateway, Kong, and '
                                'Google Cloud Apigee are popular managed options.'},
                {'id': 'rate-limiter',
                 'label': 'Rate Limiter',
                 'category': 'networking',
                 'icon': 'ShieldAlert',
                 'maxQPS': 80000,
                 'latencyMs': 1,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Throttles requests per client, IP, or API key to protect downstream services from '
                                'abuse, DDoS attacks, and traffic spikes. Typically implemented using token bucket or '
                                'sliding window algorithms backed by Redis. Often built into API gateways like Kong or '
                                'AWS WAF, or implemented as a standalone service.'},
                {'id': 'app-server',
                 'label': 'App Server',
                 'category': 'compute',
                 'icon': 'Server',
                 'maxQPS': 5000,
                 'latencyMs': 20,
                 'scalable': True,
                 'stateful': False,
                 'description': 'Stateless application server that executes core business logic and serves API '
                                'requests. Designed to scale horizontally — spin up more instances behind a load '
                                'balancer to handle increased traffic. Runs on AWS EC2/ECS, Google Compute Engine, or '
                                'containerized in Kubernetes pods.'},
                {'id': 'auth-service',
                 'label': 'Auth Service',
                 'category': 'compute',
                 'icon': 'KeyRound',
                 'maxQPS': 10000,
                 'latencyMs': 15,
                 'scalable': True,
                 'stateful': False,
                 'description': 'Dedicated authentication and authorization service that handles user login, token '
                                'issuance (JWT/OAuth2), session management, and permission checks. Centralizing auth '
                                'prevents security logic from being scattered across microservices. Examples include '
                                'AWS Cognito, Auth0, Firebase Auth, and Google Cloud Identity Platform.'},
                {'id': 'sql-db',
                 'label': 'SQL Database',
                 'category': 'storage',
                 'icon': 'Database',
                 'maxQPS': 10000,
                 'latencyMs': 8,
                 'scalable': False,
                 'stateful': True,
                 'description': 'Relational database providing ACID transactions, strong consistency, and structured '
                                'schemas with SQL queries. Best for data with complex relationships, joins, and strict '
                                'integrity requirements (e.g., financial transactions, user accounts). Examples '
                                'include Amazon RDS (PostgreSQL/MySQL), Google Cloud SQL, and Amazon Aurora.'},
                {'id': 'nosql-db',
                 'label': 'NoSQL Database',
                 'category': 'storage',
                 'icon': 'HardDrive',
                 'maxQPS': 50000,
                 'latencyMs': 3,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Non-relational database optimized for flexible schemas, horizontal scaling, and '
                                'high-throughput workloads. Choose it when you need low-latency key-value lookups, '
                                'wide-column storage, or document-oriented data without complex joins. Amazon '
                                'DynamoDB, Google Cloud Bigtable, MongoDB Atlas, and Apache Cassandra are widely '
                                'used.'},
                {'id': 'cache',
                 'label': 'Cache / Redis',
                 'category': 'storage',
                 'icon': 'Zap',
                 'maxQPS': 100000,
                 'latencyMs': 1,
                 'scalable': True,
                 'stateful': True,
                 'description': 'In-memory data store delivering sub-millisecond read latency for frequently accessed '
                                'data, session storage, leaderboards, and real-time counters. Placing a cache between '
                                'your app servers and database can reduce DB load by 80-90% for read-heavy workloads. '
                                'Amazon ElastiCache (Redis/Memcached) and Google Cloud Memorystore are managed '
                                'options.'},
                {'id': 'object-storage',
                 'label': 'Object Storage',
                 'category': 'storage',
                 'icon': 'Archive',
                 'maxQPS': 25000,
                 'latencyMs': 75,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Highly durable blob/object storage for unstructured data like images, videos, '
                                'backups, and static website assets. Offers virtually unlimited capacity with '
                                '99.999999999% (11 nines) durability. Amazon S3, Google Cloud Storage, and Azure Blob '
                                'Storage are the industry standards, often paired with a CDN for fast delivery.'},
                {'id': 'search',
                 'label': 'Search / ES',
                 'category': 'storage',
                 'icon': 'Search',
                 'maxQPS': 20000,
                 'latencyMs': 10,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Full-text search engine that indexes and queries large volumes of text with features '
                                'like fuzzy matching, faceted search, and relevance scoring. Use it when users need to '
                                'search across product catalogs, logs, or content feeds. Elasticsearch (Amazon '
                                'OpenSearch), Apache Solr, and Google Cloud Search are common choices.'},
                {'id': 'message-queue',
                 'label': 'Message Queue',
                 'category': 'messaging',
                 'icon': 'MessageSquare',
                 'maxQPS': 100000,
                 'latencyMs': 5,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Asynchronous message broker that decouples producers from consumers, enabling '
                                'reliable background processing, event-driven architectures, and traffic spike '
                                'buffering. Critical for any workflow where synchronous processing would create '
                                'bottlenecks or coupling. Apache Kafka, Amazon SQS/SNS, Google Cloud Pub/Sub, and '
                                'RabbitMQ are widely adopted.'},
                {'id': 'service-mesh',
                 'label': 'Service Mesh',
                 'category': 'infrastructure',
                 'icon': 'GitBranch',
                 'maxQPS': 80000,
                 'latencyMs': 2,
                 'scalable': True,
                 'stateful': False,
                 'description': 'Transparent service-to-service communication layer that handles mutual TLS, retries, '
                                'circuit breaking, load balancing, and distributed tracing between microservices. Use '
                                'it when your microservice count grows beyond what manual configuration can manage. '
                                'Istio, Linkerd, and AWS App Mesh are leading implementations.'},
                {'id': 'monitoring',
                 'label': 'Monitoring',
                 'category': 'infrastructure',
                 'icon': 'Activity',
                 'maxQPS': 500000,
                 'latencyMs': 5,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Observability stack for metrics collection, centralized logging, distributed tracing, '
                                'and alerting. Every production system needs monitoring to detect outages, track SLOs, '
                                'and debug performance issues. Prometheus + Grafana, AWS CloudWatch, Google Cloud '
                                'Monitoring, Datadog, and the ELK stack are standard tools.'},
                {'id': 'websocket-server',
                 'label': 'WebSocket Server',
                 'category': 'compute',
                 'icon': 'Radio',
                 'maxQPS': 50000,
                 'latencyMs': 2,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Maintains persistent bidirectional connections for real-time communication. Essential '
                                'for chat apps, live notifications, collaborative editing, and gaming. Services like '
                                'Socket.io, AWS API Gateway WebSocket, and Pusher handle millions of concurrent '
                                'connections with connection-to-server mapping stored in Redis.'},
                {'id': 'task-scheduler',
                 'label': 'Task Scheduler',
                 'category': 'compute',
                 'icon': 'Clock',
                 'maxQPS': 10000,
                 'latencyMs': 50,
                 'scalable': True,
                 'stateful': False,
                 'description': 'Manages delayed, scheduled, and recurring background jobs with retry logic and '
                                'dead-letter queues. Critical for email campaigns, report generation, data pipelines, '
                                'and cleanup tasks. Celery, AWS Step Functions, Google Cloud Tasks, and Temporal are '
                                'common implementations.'},
                {'id': 'stream-processor',
                 'label': 'Stream Processor',
                 'category': 'compute',
                 'icon': 'Waves',
                 'maxQPS': 200000,
                 'latencyMs': 10,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Processes continuous data streams in real-time for analytics, event processing, and '
                                'ETL pipelines. Handles windowed aggregations, joins, and transformations on unbounded '
                                'data. Apache Kafka Streams, Apache Flink, Spark Streaming, and AWS Kinesis Data '
                                'Analytics are industry standards.'},
                {'id': 'notification-service',
                 'label': 'Notification Service',
                 'category': 'compute',
                 'icon': 'Bell',
                 'maxQPS': 50000,
                 'latencyMs': 100,
                 'scalable': True,
                 'stateful': False,
                 'description': 'Orchestrates multi-channel delivery of push notifications, emails, SMS, and in-app '
                                'messages with priority queuing, template rendering, and delivery tracking. Firebase '
                                'Cloud Messaging, AWS SNS/SES, Twilio, and OneSignal handle billions of notifications '
                                'daily with device token management.'},
                {'id': 'graph-db',
                 'label': 'Graph Database',
                 'category': 'storage',
                 'icon': 'Share2',
                 'maxQPS': 8000,
                 'latencyMs': 15,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Stores and queries highly connected data using nodes, edges, and properties — '
                                'optimized for relationship traversals like friend-of-friend queries, recommendation '
                                'engines, and fraud detection. Neo4j, Amazon Neptune, and JanusGraph significantly '
                                'outperform relational joins for multi-hop traversals.'},
                {'id': 'timeseries-db',
                 'label': 'Time-Series DB',
                 'category': 'storage',
                 'icon': 'TrendingUp',
                 'maxQPS': 100000,
                 'latencyMs': 3,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Optimized for ingesting and querying time-stamped data with built-in downsampling, '
                                'retention policies, and time-windowed aggregations. Essential for monitoring metrics, '
                                'IoT sensor data, and financial tick data. InfluxDB, TimescaleDB, Amazon Timestream, '
                                'and Prometheus TSDB are purpose-built for this workload.'},
                {'id': 'data-warehouse',
                 'label': 'Data Warehouse',
                 'category': 'storage',
                 'icon': 'Warehouse',
                 'maxQPS': 1000,
                 'latencyMs': 5000,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Columnar analytical database designed for complex queries across terabytes/petabytes '
                                'of historical data. Separates analytics from operational databases to prevent query '
                                'load from impacting production. Google BigQuery, Amazon Redshift, Snowflake, and '
                                'ClickHouse support SQL analytics at massive scale.'},
                {'id': 'service-discovery',
                 'label': 'Service Discovery',
                 'category': 'infrastructure',
                 'icon': 'Compass',
                 'maxQPS': 50000,
                 'latencyMs': 1,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Enables microservices to find and communicate with each other dynamically without '
                                'hardcoded addresses. Handles service registration, health checking, and DNS-based or '
                                'API-based lookups. HashiCorp Consul, Apache ZooKeeper, etcd, and AWS Cloud Map are '
                                'widely used for service mesh coordination.'},
                {'id': 'reverse-proxy',
                 'label': 'Reverse Proxy',
                 'category': 'networking',
                 'icon': 'Shield',
                 'maxQPS': 100000,
                 'latencyMs': 1,
                 'scalable': True,
                 'stateful': False,
                 'description': 'Sits between clients and backend servers to handle SSL termination, request routing, '
                                'caching, compression, and security filtering. Unlike a load balancer, it can also '
                                'serve cached content, rewrite URLs, and add security headers. Nginx, Envoy, '
                                'Cloudflare, and AWS CloudFront function as reverse proxies.'},
                {'id': 'distributed-lock',
                 'label': 'Distributed Lock',
                 'category': 'infrastructure',
                 'icon': 'Lock',
                 'maxQPS': 10000,
                 'latencyMs': 5,
                 'scalable': False,
                 'stateful': True,
                 'description': 'Provides mutual exclusion across distributed systems to prevent race conditions in '
                                'critical sections like inventory updates, leader election, and distributed '
                                'transactions. Redis Redlock, Apache ZooKeeper recipes, and etcd lease-based locks are '
                                'common implementations with trade-offs between safety and liveness.'},
                {'id': 'circuit-breaker',
                 'label': 'Circuit Breaker',
                 'category': 'infrastructure',
                 'icon': 'ShieldOff',
                 'maxQPS': 100000,
                 'latencyMs': 1,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Prevents cascading failures by monitoring downstream service health and '
                                'short-circuiting requests when failure rates exceed a threshold. Implements three '
                                'states: closed (normal), open (failing, reject immediately), and half-open (testing '
                                'recovery). Netflix Hystrix popularized the pattern; Resilience4j, Envoy, and Istio '
                                'provide modern implementations.'},
                {'id': 'file-store',
                 'label': 'File Store',
                 'category': 'storage',
                 'icon': 'FolderOpen',
                 'maxQPS': 10000,
                 'latencyMs': 10,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Network-attached file storage providing POSIX-compatible file system semantics for '
                                'shared access across multiple compute instances. Supports hierarchical directories, '
                                'file locking, and concurrent reads/writes. Amazon EFS, Google Cloud Filestore, and '
                                'Azure Files are managed options. Use when applications need a traditional file system '
                                'interface rather than object/blob APIs.'},
                {'id': 'origin-shield',
                 'label': 'Origin Shield',
                 'category': 'networking',
                 'icon': 'ShieldCheck',
                 'maxQPS': 200000,
                 'latencyMs': 5,
                 'scalable': True,
                 'stateful': False,
                 'description': 'An additional caching layer between CDN edge locations and the origin server that '
                                'reduces origin load by collapsing duplicate requests from multiple edge PoPs into a '
                                'single origin fetch. Reduces origin bandwidth by 50-90% for popular content. AWS '
                                'CloudFront Origin Shield, Cloudflare Tiered Cache, and Fastly Shield PoPs are '
                                'implementations.'},
                {'id': 'coordination-service',
                 'label': 'Coordination Service',
                 'category': 'infrastructure',
                 'icon': 'Users',
                 'maxQPS': 20000,
                 'latencyMs': 5,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Provides distributed coordination primitives: leader election, configuration '
                                'management, distributed barriers, and group membership. Built on consensus protocols '
                                '(Raft/ZAB) for strong consistency. Apache ZooKeeper, etcd, and Consul are the primary '
                                'implementations. Essential for distributed systems that need agreement on shared '
                                'state.'},
                {'id': 'custom',
                 'label': 'Custom Component',
                 'category': 'compute',
                 'icon': 'Box',
                 'maxQPS': 50000,
                 'latencyMs': 10,
                 'scalable': True,
                 'stateful': False,
                 'description': 'A generic component that can be renamed to represent any service, system, or '
                                'infrastructure not available in the predefined component library. Double-click the '
                                'node label on the canvas to rename it. Use this for specialized services like ML '
                                'inference engines, recommendation services, fraud detection, content moderation, or '
                                'any domain-specific component.'},
                {'id': 'id-generator',
                 'label': 'ID Generator',
                 'category': 'infrastructure',
                 'icon': 'Fingerprint',
                 'maxQPS': 500000,
                 'latencyMs': 1,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Generates globally unique, sortable IDs across distributed nodes using algorithms '
                                'like Twitter Snowflake, ULID, or UUID. Each node embeds a timestamp, machine ID, and '
                                'sequence number to guarantee uniqueness without centralized coordination. Essential '
                                'for database primary keys, URL shortening, event ordering, and sharding keys.'},
                {'id': 'sharded-counter',
                 'label': 'Sharded Counter',
                 'category': 'infrastructure',
                 'icon': 'Hash',
                 'maxQPS': 500000,
                 'latencyMs': 2,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Distributes a single logical counter across multiple shards to avoid hot-key '
                                'bottlenecks under massive concurrent writes. Reads aggregate across shards with '
                                'eventual consistency. Critical for like counts, view counters, follower counts, and '
                                'real-time voting at scale. Typically backed by Redis or purpose-built counter tables '
                                'with periodic reconciliation.'},
                {'id': 'pub-sub',
                 'label': 'Pub/Sub',
                 'category': 'messaging',
                 'icon': 'Megaphone',
                 'maxQPS': 200000,
                 'latencyMs': 5,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Topic-based publish/subscribe messaging where each message is broadcast to all '
                                'subscribers, unlike point-to-point queues where each message is consumed by one '
                                'consumer. Enables event-driven fan-out for feeds, analytics pipelines, CDC, and '
                                'cross-service event propagation. Google Cloud Pub/Sub, AWS SNS, and Apache Kafka '
                                'topics are canonical implementations.'},
                {'id': 'vector-db',
                 'label': 'Vector Database',
                 'category': 'storage',
                 'icon': 'Brain',
                 'maxQPS': 10000,
                 'latencyMs': 10,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Stores high-dimensional vector embeddings and performs approximate nearest-neighbor '
                                '(ANN) search for similarity matching. Powers recommendation engines, semantic search, '
                                'image search, and RAG-based AI systems. Pinecone, Weaviate, Milvus, Qdrant, and '
                                'pgvector are leading implementations using HNSW or IVF indexing algorithms.'},
                {'id': 'geospatial-index',
                 'label': 'Geospatial Index',
                 'category': 'storage',
                 'icon': 'MapPin',
                 'maxQPS': 50000,
                 'latencyMs': 5,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Indexes and queries location data using geohash, quadtree, R-tree, or H3 hexagonal '
                                'grids for efficient nearest-neighbor and radius searches. Essential for ride-sharing, '
                                'food delivery, local search, and any proximity-based system. PostGIS, Redis GEO '
                                '(GEOADD/GEOSEARCH), Elasticsearch geo_point, and Google S2 library are common '
                                'implementations.'},
                {'id': 'config-service',
                 'label': 'Config Service',
                 'category': 'infrastructure',
                 'icon': 'Settings',
                 'maxQPS': 50000,
                 'latencyMs': 2,
                 'scalable': True,
                 'stateful': True,
                 'description': 'Centralized dynamic configuration management for feature flags, A/B test parameters, '
                                'and runtime settings without redeployment. Supports versioning, rollback, targeted '
                                'rollouts by user segment, and real-time propagation to all service instances. AWS '
                                'AppConfig, LaunchDarkly, Unleash, and etcd-backed config stores are common '
                                'implementations.'}],
 'tradeoffs': [{'id': 'sql-vs-nosql',
                'title': 'SQL vs NoSQL',
                'optionA': {'name': 'SQL (Relational)',
                            'pros': ['ACID transactions',
                                     'Strong consistency',
                                     'Complex joins and queries',
                                     'Well-understood schema enforcement'],
                            'cons': ['Harder to scale horizontally',
                                     'Rigid schema — migrations can be painful',
                                     'Lower write throughput at extreme scale']},
                'optionB': {'name': 'NoSQL (Document/Key-Value)',
                            'pros': ['Horizontal scaling built-in',
                                     'Flexible schema',
                                     'High write throughput',
                                     'Low-latency key-value lookups'],
                            'cons': ['Limited join support',
                                     'Eventual consistency by default',
                                     'Data modeling requires denormalization']},
                'whenToChooseA': 'When you need complex queries, transactions, or strong consistency (payments, '
                                 'inventory, user accounts).',
                'whenToChooseB': 'When you need massive scale, flexible schema, or high write throughput (social '
                                 'feeds, IoT data, session stores).'},
               {'id': 'push-vs-pull',
                'title': 'Push vs Pull (Fan-out)',
                'optionA': {'name': 'Fan-out on Write (Push)',
                            'pros': ['Fast reads — timeline is pre-computed',
                                     'Simple read path',
                                     'Consistent user experience'],
                            'cons': ['High write amplification for popular users',
                                     'Wasted work if followers never read',
                                     'Slow writes for celebrity accounts']},
                'optionB': {'name': 'Fan-out on Read (Pull)',
                            'pros': ['No write amplification', 'Always fresh data', 'Simple write path'],
                            'cons': ['Slow reads — must aggregate at read time',
                                     'Higher read latency',
                                     'Complex read path with many DB queries']},
                'whenToChooseA': 'For most users with moderate follower counts where read latency matters most.',
                'whenToChooseB': 'For celebrity/high-follower accounts, or when write simplicity is more important '
                                 'than read speed.'},
               {'id': 'sync-vs-async',
                'title': 'Sync vs Async Communication',
                'optionA': {'name': 'Synchronous (Request-Response)',
                            'pros': ['Simple to reason about',
                                     'Immediate feedback',
                                     'Easy error handling',
                                     'Natural request-response pattern'],
                            'cons': ['Tight coupling between services',
                                     'Cascading failures',
                                     'Caller blocks until response']},
                'optionB': {'name': 'Asynchronous (Message Queue)',
                            'pros': ['Loose coupling',
                                     'Better fault tolerance',
                                     'Natural load leveling',
                                     'Retry and dead-letter support'],
                            'cons': ['Harder to debug',
                                     'Eventual consistency',
                                     'Message ordering challenges',
                                     'Additional infrastructure (broker)']},
                'whenToChooseA': 'When you need immediate responses and simple request-response flows (API gateway to '
                                 'service, user-facing reads).',
                'whenToChooseB': 'For fire-and-forget tasks, cross-service events, or when you need to decouple '
                                 'producers from consumers (notifications, analytics, order processing).'},
               {'id': 'strong-vs-eventual',
                'title': 'Strong vs Eventual Consistency',
                'optionA': {'name': 'Strong Consistency',
                            'pros': ['All reads see the latest write',
                                     'Simplifies application logic',
                                     'No stale data surprises'],
                            'cons': ['Higher latency (coordination overhead)',
                                     'Lower availability during partitions',
                                     'Harder to scale geographically']},
                'optionB': {'name': 'Eventual Consistency',
                            'pros': ['Higher availability',
                                     'Lower latency',
                                     'Better geographic distribution',
                                     'Higher throughput'],
                            'cons': ['Stale reads possible',
                                     'Complex conflict resolution',
                                     'Application must handle inconsistency']},
                'whenToChooseA': 'For financial transactions, inventory counts, or anywhere correctness is '
                                 'non-negotiable.',
                'whenToChooseB': 'For social feeds, analytics, caches, or anywhere slight staleness is acceptable for '
                                 'better performance.'},
               {'id': 'monolith-vs-microservices',
                'title': 'Monolith vs Microservices',
                'optionA': {'name': 'Monolith',
                            'pros': ['Simple deployment',
                                     'Easy local development',
                                     'No network overhead between modules',
                                     'Straightforward debugging'],
                            'cons': ['Harder to scale individual components',
                                     'Longer build/deploy cycles at scale',
                                     'Technology lock-in',
                                     'Team coupling']},
                'optionB': {'name': 'Microservices',
                            'pros': ['Independent scaling per service',
                                     'Independent deployments',
                                     'Technology flexibility per service',
                                     'Team autonomy'],
                            'cons': ['Distributed system complexity',
                                     'Network latency between services',
                                     'Operational overhead (monitoring, tracing)',
                                     'Data consistency challenges']},
                'whenToChooseA': 'For early-stage products, small teams, or when the domain is not yet well '
                                 'understood.',
                'whenToChooseB': 'For large organizations with clear domain boundaries, independent scaling needs, and '
                                 'dedicated platform teams.'},
               {'id': 'rest-vs-grpc',
                'title': 'REST vs gRPC',
                'optionA': {'name': 'REST (HTTP/JSON)',
                            'pros': ['Universal browser support',
                                     'Human-readable payloads',
                                     'Simple tooling (curl, Postman)',
                                     'Wide ecosystem'],
                            'cons': ['Larger payload size (JSON)',
                                     'No built-in streaming',
                                     'No strict schema enforcement',
                                     'HTTP/1.1 overhead']},
                'optionB': {'name': 'gRPC (Protocol Buffers)',
                            'pros': ['Binary protocol — smaller payloads',
                                     'Built-in bi-directional streaming',
                                     'Strong schema via .proto files',
                                     'HTTP/2 multiplexing'],
                            'cons': ['No native browser support (needs proxy)',
                                     'Binary payloads harder to debug',
                                     'Steeper learning curve',
                                     'Code generation required']},
                'whenToChooseA': 'For public APIs, browser clients, or when developer experience and debuggability '
                                 'matter most.',
                'whenToChooseB': 'For internal service-to-service communication where performance, streaming, and '
                                 'strict contracts matter.'},
               {'id': 'cache-aside-vs-write-through',
                'title': 'Cache-aside vs Write-through',
                'optionA': {'name': 'Cache-aside (Lazy Loading)',
                            'pros': ['Only caches data that is actually read',
                                     'Cache failure does not block writes',
                                     'Simple implementation'],
                            'cons': ['Cache miss penalty (extra DB read)',
                                     'Stale data until TTL expires',
                                     'Cold start problem']},
                'optionB': {'name': 'Write-through',
                            'pros': ['Cache is always up-to-date', 'No stale data', 'Consistent read performance'],
                            'cons': ['Write latency increases (write to cache + DB)',
                                     'Caches data that may never be read',
                                     'More complex write path']},
                'whenToChooseA': 'For read-heavy workloads where some staleness is acceptable and you want to minimize '
                                 'cache size.',
                'whenToChooseB': 'When data freshness is critical and the write volume is manageable.'},
               {'id': 'vertical-vs-horizontal',
                'title': 'Vertical vs Horizontal Scaling',
                'optionA': {'name': 'Vertical Scaling (Scale Up)',
                            'pros': ['No code changes needed',
                                     'No distributed system complexity',
                                     'Simple data consistency',
                                     'Lower operational overhead'],
                            'cons': ['Hardware limits (single machine ceiling)',
                                     'Single point of failure',
                                     'Expensive at high end',
                                     'Downtime during upgrades']},
                'optionB': {'name': 'Horizontal Scaling (Scale Out)',
                            'pros': ['Virtually unlimited capacity',
                                     'Better fault tolerance',
                                     'Cost-effective with commodity hardware',
                                     'Zero-downtime scaling'],
                            'cons': ['Distributed system complexity',
                                     'Data partitioning challenges',
                                     'Network overhead',
                                     'Consistency challenges']},
                'whenToChooseA': 'For early-stage systems, databases that are hard to shard, or when simplicity '
                                 'outweighs scale needs.',
                'whenToChooseB': 'When you need fault tolerance, unlimited growth, or when individual machines cannot '
                                 'handle the load.'},
               {'id': 'polling-vs-websocket',
                'title': 'Polling vs WebSocket',
                'optionA': {'name': 'Polling (Short/Long)',
                            'pros': ['Simple to implement',
                                     'Works through all proxies/firewalls',
                                     'Stateless — easy to load balance',
                                     'HTTP caching friendly'],
                            'cons': ['Wasted requests when no new data',
                                     'Higher latency (polling interval)',
                                     'More server load at scale']},
                'optionB': {'name': 'WebSocket',
                            'pros': ['Real-time bidirectional communication',
                                     'Low latency',
                                     'Efficient — no repeated handshakes',
                                     'Server can push updates instantly'],
                            'cons': ['Stateful connections — harder to load balance',
                                     'Connection management overhead',
                                     'Proxy/firewall compatibility issues',
                                     'Reconnection logic needed']},
                'whenToChooseA': 'For infrequent updates, simple dashboards, or when infrastructure does not support '
                                 'persistent connections.',
                'whenToChooseB': 'For chat, live feeds, collaborative editing, gaming, or any feature needing '
                                 'sub-second updates.'},
               {'id': 'single-vs-multi-leader',
                'title': 'Single Leader vs Multi-Leader Replication',
                'optionA': {'name': 'Single Leader',
                            'pros': ['No write conflicts', 'Simple consistency model', 'Easy to reason about ordering'],
                            'cons': ['Single point of failure for writes',
                                     'Write latency for remote clients',
                                     'Leader failover complexity']},
                'optionB': {'name': 'Multi-Leader',
                            'pros': ['Writes accepted at any datacenter',
                                     'Better write latency for geo-distributed users',
                                     'Tolerates datacenter outages'],
                            'cons': ['Write conflicts must be resolved',
                                     'Complex conflict resolution logic',
                                     'Harder to maintain consistency']},
                'whenToChooseA': 'When strong consistency is required and most users are in one region.',
                'whenToChooseB': 'For geo-distributed systems where write latency matters and you can handle conflict '
                                 'resolution (collaborative docs, multi-region apps).'},
               {'id': 'hash-vs-range-partitioning',
                'title': 'Hash Partitioning vs Range Partitioning',
                'optionA': {'name': 'Hash Partitioning',
                            'pros': ['Even data distribution',
                                     'No hotspots from sequential keys',
                                     'Simple partition assignment'],
                            'cons': ['Range queries require scatter-gather',
                                     'Rebalancing on cluster resize',
                                     'Loses data locality']},
                'optionB': {'name': 'Range Partitioning',
                            'pros': ['Efficient range queries',
                                     'Data locality for related keys',
                                     'Natural ordering preserved'],
                            'cons': ['Hotspots from sequential writes',
                                     'Uneven partition sizes',
                                     'Requires careful split-point selection']},
                'whenToChooseA': 'For key-value lookups where even distribution matters (user IDs, session tokens, URL '
                                 'shortener).',
                'whenToChooseB': 'When range scans are common (time-series data, alphabetical listings, log '
                                 'analysis).'},
               {'id': 'cdn-push-vs-pull',
                'title': 'CDN Push vs CDN Pull',
                'optionA': {'name': 'CDN Push (Origin Push)',
                            'pros': ['Content available immediately',
                                     'No first-request latency penalty',
                                     'Full control over what is cached'],
                            'cons': ['Storage costs for all pushed content',
                                     'Must manage cache invalidation',
                                     'Wasted space for unpopular content']},
                'optionB': {'name': 'CDN Pull (Origin Pull)',
                            'pros': ['Only popular content is cached',
                                     'Lower storage costs',
                                     'Automatic cache population'],
                            'cons': ['First request is slow (cache miss)',
                                     'Thundering herd on cache expiry',
                                     'Less control over cached content']},
                'whenToChooseA': 'For critical content that must always be fast (homepage assets, popular videos, app '
                                 'bundles).',
                'whenToChooseB': 'For long-tail content where most items are rarely accessed (user profile images, old '
                                 'blog posts).'},
               {'id': 'token-bucket-vs-sliding-window',
                'title': 'Rate Limiting: Token Bucket vs Sliding Window',
                'optionA': {'name': 'Token Bucket',
                            'pros': ['Allows controlled bursts',
                                     'Simple to implement',
                                     'Memory efficient (few counters)',
                                     'Smooth rate limiting'],
                            'cons': ['Burst traffic can spike',
                                     'Tuning bucket size and refill rate',
                                     'Less precise at boundaries']},
                'optionB': {'name': 'Sliding Window Log/Counter',
                            'pros': ['Precise rate limiting', 'No boundary spikes', 'Accurate per-window counting'],
                            'cons': ['Higher memory usage (log of timestamps)',
                                     'More complex implementation',
                                     'Sliding window counter trades precision for memory']},
                'whenToChooseA': 'When you want to allow short bursts while enforcing average rate (API gateways, '
                                 'general rate limiting).',
                'whenToChooseB': 'When strict per-window accuracy matters and you cannot tolerate boundary bursts '
                                 '(financial APIs, security-sensitive endpoints).'},
               {'id': 'at-least-once-vs-exactly-once',
                'title': 'Message Queue: At-least-once vs Exactly-once',
                'optionA': {'name': 'At-least-once Delivery',
                            'pros': ['Simpler to implement',
                                     'No message loss',
                                     'Higher throughput',
                                     'Most brokers support natively'],
                            'cons': ['Duplicate messages possible',
                                     'Consumer must be idempotent',
                                     'Application-level deduplication needed']},
                'optionB': {'name': 'Exactly-once Delivery',
                            'pros': ['No duplicates', 'Simplifies consumer logic', 'Correct by default'],
                            'cons': ['Significant performance overhead',
                                     'Requires transactional coordination',
                                     'Limited broker support (Kafka transactions)',
                                     'Higher latency']},
                'whenToChooseA': 'For most use cases — design idempotent consumers instead (notifications, analytics '
                                 'events, log processing).',
                'whenToChooseB': 'For financial transactions or state changes where duplicates cause real harm and you '
                                 'can afford the performance cost.'}],
 'problems': [{'id': 'url-shortener',
               'title': 'URL Shortener',
               'difficulty': 'Easy',
               'description': 'Design a URL shortening service like Bitly or TinyURL. Users submit long URLs and '
                              'receive short, unique aliases that redirect to the original destination. The system is '
                              'heavily read-biased — for every URL created, expect 100x more redirect lookups. '
                              'Real-world services like Bitly handle billions of redirects per month with sub-100ms '
                              'latency, making caching strategy the key design decision.',
               'requirements': {'readsPerSec': 100000,
                                'writesPerSec': 1000,
                                'storageGB': 500,
                                'latencyMs': 100,
                                'users': '100M DAU'},
               'constraints': ['Short URLs should be unique and non-predictable (base62 or base58 encoding)',
                               'Redirect latency < 100ms at p99 — users should not notice any delay',
                               'System should handle 100:1 read/write ratio',
                               'URLs should expire after a configurable TTL (default 5 years)',
                               'Analytics tracking for click counts, geographic distribution, and referrer data',
                               'Custom alias support — users can choose their own short URL slug',
                               'Rate limiting to prevent abuse (e.g., max 100 URLs/min per API key)'],
               'hints': [{'title': 'Start with the basics',
                          'content': 'Consider DNS → Load Balancer → App Server → Database as your starting flow.'},
                         {'title': 'Think about reads',
                          'content': 'Most requests are reads (redirects). A cache layer can dramatically reduce DB '
                                     'load.'},
                         {'title': 'Scaling writes',
                          'content': 'Use a NoSQL database or partition your SQL database by key hash for write '
                                     'scaling.'},
                         {'title': 'Advanced: Key generation',
                          'content': 'Pre-generate keys in a separate Key Generation Service (KGS) to avoid collision '
                                     'checks at write time. Store unused keys in a dedicated table and move them to a '
                                     "'used' table atomically."}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 100, 'y': 250},
                                               {'componentId': 'cdn', 'x': 300, 'y': 100},
                                               {'componentId': 'load-balancer', 'x': 300, 'y': 250},
                                               {'componentId': 'rate-limiter', 'x': 300, 'y': 400},
                                               {'componentId': 'app-server', 'x': 500, 'y': 250},
                                               {'componentId': 'cache', 'x': 500, 'y': 100},
                                               {'componentId': 'nosql-db', 'x': 700, 'y': 250},
                                               {'componentId': 'monitoring', 'x': 700, 'y': 100}],
                                     'edges': [{'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'dns', 'target': 'cdn'},
                                               {'source': 'load-balancer', 'target': 'rate-limiter'},
                                               {'source': 'rate-limiter', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Storage', 'Caching', 'Hashing']},
              {'id': 'twitter-feed',
               'title': 'Twitter / News Feed',
               'difficulty': 'Hard',
               'description': 'Design a social media feed like Twitter (X). Users can post tweets, follow others, and '
                              'see a personalized timeline ranked by relevance. The core challenge is fan-out: when a '
                              'celebrity with 50M followers posts a tweet, how do you deliver it to all their '
                              "followers' timelines without melting your infrastructure? Real systems like Twitter use "
                              'a hybrid approach — pre-computing timelines for most users while handling high-follower '
                              'accounts differently.',
               'requirements': {'readsPerSec': 100000,
                                'writesPerSec': 1000,
                                'storageGB': 500000,
                                'latencyMs': 200,
                                'users': '250M DAU'},
               'constraints': ['Timeline should be eventually consistent within 5 seconds of a new post',
                               'Support users with millions of followers (celebrities) without write amplification '
                               'storms',
                               'Feed should rank by relevance using signals like recency, engagement, and relationship '
                               'strength',
                               'Media uploads (images/videos up to 512MB) must be supported with async processing',
                               'Real-time notifications for mentions, likes, retweets, and DMs',
                               'Full-text search across all public tweets with sub-second response time',
                               'Graceful degradation — serve stale timelines rather than showing errors during peak '
                               'load'],
               'hints': [{'title': 'Fan-out strategy',
                          'content': 'Consider fan-out-on-write for normal users and fan-out-on-read for celebrities.'},
                         {'title': 'Caching the timeline',
                          'content': "Pre-compute and cache each user's timeline in Redis. Update on new posts."},
                         {'title': 'Media handling',
                          'content': 'Use object storage (S3) for media with a CDN for global delivery.'},
                         {'title': 'Advanced: Hybrid fan-out',
                          'content': 'Set a follower threshold (e.g., 10K). Below it, fan-out-on-write pushes to '
                                     "followers' cached timelines. Above it, fan-out-on-read merges celebrity tweets "
                                     'at read time. This gives you the best of both approaches.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 420},
                                               {'componentId': 'app-server', 'x': 500, 'y': 200},
                                               {'componentId': 'cache', 'x': 500, 'y': 50},
                                               {'componentId': 'message-queue', 'x': 500, 'y': 380},
                                               {'componentId': 'sql-db', 'x': 700, 'y': 200},
                                               {'componentId': 'nosql-db', 'x': 700, 'y': 380},
                                               {'componentId': 'object-storage', 'x': 350, 'y': 80},
                                               {'componentId': 'search', 'x': 700, 'y': 50},
                                               {'componentId': 'monitoring', 'x': 850, 'y': 200}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Fan-out', 'Cache', 'Timeline']},
              {'id': 'chat-system',
               'title': 'Chat System',
               'difficulty': 'Hard',
               'description': 'Design a real-time chat application like WhatsApp, Slack, or Discord. Support 1:1 '
                              'messaging, group chats with up to 1000 members, read receipts, typing indicators, and '
                              'online presence. Messages must be delivered reliably and in order, even when users '
                              'switch between devices. WhatsApp processes over 100 billion messages per day — the key '
                              'challenges are maintaining persistent connections at scale and guaranteeing '
                              'exactly-once delivery.',
               'requirements': {'readsPerSec': 50000,
                                'writesPerSec': 100000,
                                'storageGB': 50000,
                                'latencyMs': 50,
                                'users': '500M DAU'},
               'constraints': ['Messages delivered in under 50ms for online users via persistent WebSocket connections',
                               'Guaranteed message ordering within a conversation using sequence numbers',
                               'Offline message delivery when user comes back online (store-and-forward pattern)',
                               'Support group chats with up to 1000 members with efficient fan-out',
                               'End-to-end encryption for 1:1 chats (server should never see plaintext)',
                               'Read receipts and typing indicators with minimal overhead (no DB writes for ephemeral '
                               'events)',
                               'Multi-device sync — messages appear on all logged-in devices simultaneously'],
               'hints': [{'title': 'WebSocket connections',
                          'content': 'Use persistent WebSocket connections for real-time delivery. Need a connection '
                                     'gateway.'},
                         {'title': 'Message ordering',
                          'content': 'Use a message queue with per-conversation partitioning to guarantee ordering.'},
                         {'title': 'Presence system',
                          'content': 'Use Redis with TTL keys for online/offline status. Heartbeat every 30 seconds.'},
                         {'title': 'Advanced: Connection management',
                          'content': 'Use a dedicated WebSocket gateway layer that maintains millions of persistent '
                                     'connections. Store connection-to-server mappings in Redis so any app server can '
                                     "route a message to the correct gateway holding the recipient's connection."}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'websocket-server', 'x': 200, 'y': 100},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 100},
                                               {'componentId': 'app-server', 'x': 500, 'y': 180},
                                               {'componentId': 'cache', 'x': 500, 'y': 50},
                                               {'componentId': 'message-queue', 'x': 500, 'y': 350},
                                               {'componentId': 'nosql-db', 'x': 700, 'y': 250},
                                               {'componentId': 'monitoring', 'x': 700, 'y': 50},
                                               {'componentId': 'rate-limiter', 'x': 50, 'y': 100}],
                                     'edges': [{'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'rate-limiter'},
                                               {'source': 'load-balancer', 'target': 'websocket-server'},
                                               {'source': 'websocket-server', 'target': 'app-server'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['WebSocket', 'Messaging', 'Real-time']},
              {'id': 'ride-sharing',
               'title': 'Uber / Ride Sharing',
               'difficulty': 'Hard',
               'description': 'Design a ride-sharing platform like Uber or Lyft. Match riders with nearby drivers in '
                              'real-time, track live location updates, calculate accurate ETAs, and handle dynamic '
                              'surge pricing. The system must ingest millions of location updates per second from '
                              'active drivers while simultaneously running proximity queries to match riders. Uber '
                              'processes over 1 million location updates per second during peak hours, making '
                              'geospatial indexing and real-time stream processing the central design challenges.',
               'requirements': {'readsPerSec': 80000,
                                'writesPerSec': 300000,
                                'storageGB': 1000,
                                'latencyMs': 100,
                                'users': '50M DAU'},
               'constraints': ['Driver matching within 5 seconds using geospatial proximity search',
                               'Location updates every 4 seconds from all active drivers (~1M concurrent drivers)',
                               'ETA accuracy within 20% of actual using real-time traffic and historical data',
                               'Surge pricing computed in real-time per geo zone based on supply/demand ratios',
                               'Trip history and receipts stored permanently for regulatory compliance',
                               'Payment processing with idempotent charge guarantees (no double-charging)',
                               'Graceful handling of driver/rider disconnections mid-trip without data loss'],
               'hints': [{'title': 'Geo-spatial indexing',
                          'content': 'Use geohashing or a spatial index to efficiently find nearby drivers.'},
                         {'title': 'Location ingestion',
                          'content': 'High-frequency location updates need a message queue to buffer writes.'},
                         {'title': 'Matching service',
                          'content': 'A dedicated matching service queries the spatial index and assigns the optimal '
                                     'driver.'},
                         {'title': 'Advanced: Geohash sharding',
                          'content': 'Partition your driver location data by geohash prefix so each shard handles a '
                                     'geographic region. This lets proximity queries hit a single shard instead of '
                                     'scanning globally. Use Redis Geo commands (GEOADD/GEOSEARCH) for O(log N) '
                                     'nearest-neighbor lookups.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'rate-limiter', 'x': 350, 'y': 120},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 400},
                                               {'componentId': 'app-server', 'x': 500, 'y': 250},
                                               {'componentId': 'cache', 'x': 500, 'y': 120},
                                               {'componentId': 'message-queue', 'x': 500, 'y': 400},
                                               {'componentId': 'stream-processor', 'x': 650, 'y': 400},
                                               {'componentId': 'nosql-db', 'x': 700, 'y': 250},
                                               {'componentId': 'sql-db', 'x': 700, 'y': 120},
                                               {'componentId': 'monitoring', 'x': 850, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'rate-limiter'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'stream-processor'},
                                               {'source': 'stream-processor', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Geo-spatial', 'Real-time', 'Matching']},
              {'id': 'video-streaming',
               'title': 'YouTube / Video Streaming',
               'difficulty': 'Hard',
               'description': 'Design a video streaming platform like YouTube or Netflix. Support video upload, '
                              'transcoding into multiple formats and resolutions, globally distributed storage, and '
                              'adaptive bitrate streaming to millions of concurrent viewers. YouTube serves over 1 '
                              'billion hours of video daily — the key challenges are building an efficient '
                              'upload-transcode-serve pipeline, leveraging CDN edge caching for popular content, and '
                              'separating the fast metadata path from the slow video delivery path.',
               'requirements': {'readsPerSec': 200000,
                                'writesPerSec': 5000,
                                'storageGB': 1000000,
                                'latencyMs': 200,
                                'users': '2.7B MAU'},
               'constraints': ['Videos transcoded into multiple resolutions (360p, 720p, 1080p, 4K) and codecs (H.264, '
                               'VP9, AV1)',
                               'Adaptive bitrate streaming (HLS/DASH) adjusts quality based on real-time bandwidth',
                               'Global delivery with < 200ms video start time for 95th percentile of users',
                               'Support live streaming with < 5s glass-to-glass latency',
                               'Recommendations engine producing personalized feeds from billions of videos',
                               'Upload processing pipeline handles videos up to 256GB with resumable uploads',
                               'Copyright detection (Content ID) must scan uploaded content before it goes live'],
               'hints': [{'title': 'Upload pipeline',
                          'content': 'Upload to object storage, then use a message queue to trigger async transcoding '
                                     'workers.'},
                         {'title': 'CDN is critical',
                          'content': 'A CDN is essential for serving video content globally. Cache popular videos at '
                                     'the edge.'},
                         {'title': 'Metadata vs video',
                          'content': 'Separate video metadata (SQL/NoSQL) from video content (object storage + CDN).'},
                         {'title': 'Advanced: Tiered storage',
                          'content': 'Use hot/warm/cold storage tiers. Popular videos stay on CDN edge and fast object '
                                     'storage. Videos older than 30 days with low views move to cheaper '
                                     'infrequent-access storage (S3 IA / Glacier). This can cut storage costs by '
                                     '60-70% without affecting user experience.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 100},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 420},
                                               {'componentId': 'rate-limiter', 'x': 350, 'y': 100},
                                               {'componentId': 'app-server', 'x': 500, 'y': 250},
                                               {'componentId': 'cache', 'x': 500, 'y': 100},
                                               {'componentId': 'message-queue', 'x': 500, 'y': 400},
                                               {'componentId': 'stream-processor', 'x': 600, 'y': 400},
                                               {'componentId': 'object-storage', 'x': 700, 'y': 100},
                                               {'componentId': 'sql-db', 'x': 700, 'y': 250},
                                               {'componentId': 'search', 'x': 700, 'y': 400},
                                               {'componentId': 'monitoring', 'x': 850, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'rate-limiter'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'message-queue', 'target': 'stream-processor'},
                                               {'source': 'stream-processor', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Streaming', 'CDN', 'Transcoding']},
              {'id': 'rate-limiter',
               'title': 'Rate Limiter',
               'difficulty': 'Easy',
               'description': 'Design a distributed rate limiting service that throttles API requests per client, IP, '
                              'or API key. Real systems like Cloudflare and AWS WAF use token bucket or sliding window '
                              'algorithms backed by distributed counters in Redis. The key challenge is achieving '
                              'consistency across multiple rate limiter instances without adding significant latency '
                              'to the request path — Stripe processes hundreds of millions of API calls per day while '
                              'enforcing per-key rate limits with sub-millisecond overhead.',
               'requirements': {'readsPerSec': 50000,
                                'writesPerSec': 50000,
                                'storageGB': 10,
                                'latencyMs': 5,
                                'users': '50M DAU'},
               'constraints': ['Sub-millisecond decision latency — rate limiting must not become a bottleneck itself',
                               'Support multiple limiting algorithms: token bucket, sliding window log, sliding window '
                               'counter',
                               'Distributed counting across multiple instances using Redis with atomic operations '
                               '(INCR + EXPIRE)',
                               'Per-client, per-endpoint, and global rate limits with configurable thresholds',
                               'Graceful handling of Redis failures — fail open vs fail closed configurable per rule',
                               'Return standard HTTP 429 with Retry-After header and remaining quota in response '
                               'headers',
                               'Support burst allowance — allow short traffic spikes above the sustained rate limit'],
               'hints': [{'title': 'Start simple',
                          'content': 'Begin with an API Gateway fronting app servers. Rate limit checks happen before '
                                     'business logic.'},
                         {'title': 'Distributed counters',
                          'content': 'Use Redis with INCR + EXPIRE for atomic counter updates across all instances. '
                                     'Lua scripts ensure atomicity.'},
                         {'title': 'Sliding window',
                          'content': 'A sliding window counter using two fixed windows with weighted counts gives '
                                     'accuracy without the memory cost of a full log.'},
                         {'title': 'Advanced: Local + global',
                          'content': 'Use a two-tier approach: local in-memory counters for hot-path speed with '
                                     'periodic sync to Redis for global consistency. This reduces Redis round-trips by '
                                     '90% while keeping limits accurate within a small margin.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'rate-limiter', 'x': 350, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 500, 'y': 250},
                                               {'componentId': 'app-server', 'x': 650, 'y': 250},
                                               {'componentId': 'cache', 'x': 350, 'y': 100},
                                               {'componentId': 'monitoring', 'x': 650, 'y': 100}],
                                     'edges': [{'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'rate-limiter'},
                                               {'source': 'rate-limiter', 'target': 'api-gateway'},
                                               {'source': 'rate-limiter', 'target': 'cache'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Distributed', 'Algorithm', 'Redis']},
              {'id': 'notification-system',
               'title': 'Notification System',
               'difficulty': 'Medium',
               'description': 'Design a scalable notification service like Firebase Cloud Messaging or AWS SNS that '
                              'delivers push notifications, emails, and SMS to hundreds of millions of users. The '
                              'system must handle priority-based routing, template rendering, delivery tracking, and '
                              'retry logic across multiple channels. Firebase Cloud Messaging delivers over 1 trillion '
                              'push notifications per year — the key challenges are fan-out at scale, rate limiting '
                              'per channel, and maintaining delivery guarantees without overwhelming downstream '
                              'providers.',
               'requirements': {'readsPerSec': 50000,
                                'writesPerSec': 100000,
                                'storageGB': 2000,
                                'latencyMs': 500,
                                'users': '500M DAU'},
               'constraints': ['Support push (iOS/Android/Web), email, and SMS delivery channels with pluggable '
                               'providers',
                               'Priority queue system — critical alerts (security, payments) jump ahead of marketing '
                               'notifications',
                               'Template engine with variable substitution and localization (100+ languages)',
                               'At-least-once delivery with deduplication to prevent duplicate notifications to users',
                               'Per-user notification preferences and opt-out management across all channels',
                               'Delivery tracking with read receipts, bounce handling, and delivery status webhooks',
                               'Rate limiting per provider to avoid being throttled by APNS, FCM, email gateways, or '
                               'SMS providers'],
               'hints': [{'title': 'Event-driven architecture',
                          'content': 'Use a message queue to decouple notification producers from the delivery '
                                     'pipeline. Events trigger notification creation.'},
                         {'title': 'Priority queues',
                          'content': 'Use separate message queues or priority lanes for critical vs marketing '
                                     'notifications to prevent backlog delays.'},
                         {'title': 'Template and preferences',
                          'content': 'Store templates and user preferences in a cache layer for fast lookup during '
                                     'high-volume sends.'},
                         {'title': 'Advanced: Fan-out workers',
                          'content': 'Use a worker pool pattern: a dispatcher reads from the priority queue, resolves '
                                     'user preferences, renders templates, then fans out to channel-specific workers '
                                     '(push worker, email worker, SMS worker). Each worker handles retries and '
                                     'provider-specific rate limits independently.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'app-server', 'x': 500, 'y': 200},
                                               {'componentId': 'message-queue', 'x': 500, 'y': 380},
                                               {'componentId': 'cache', 'x': 500, 'y': 60},
                                               {'componentId': 'nosql-db', 'x': 700, 'y': 200},
                                               {'componentId': 'sql-db', 'x': 700, 'y': 380},
                                               {'componentId': 'monitoring', 'x': 850, 'y': 200},
                                               {'componentId': 'rate-limiter', 'x': 350, 'y': 100}],
                                     'edges': [{'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'},
                                               {'source': 'api-gateway', 'target': 'rate-limiter'}]},
               'tags': ['Push', 'Queue', 'Fanout']},
              {'id': 'typeahead-autocomplete',
               'title': 'Typeahead / Autocomplete',
               'difficulty': 'Medium',
               'description': "Design a search autocomplete system like Google's search suggestions or Algolia's "
                              'instant search. As users type each character, the system returns the top 5-10 matching '
                              'suggestions ranked by popularity, personalization, and recency within 100ms. Google '
                              'processes over 8.5 billion searches per day with autocomplete triggering on every '
                              'keystroke — the core challenges are building an efficient prefix-matching data '
                              'structure (trie) and keeping suggestions fresh as search trends change in real-time.',
               'requirements': {'readsPerSec': 200000,
                                'writesPerSec': 5000,
                                'storageGB': 100,
                                'latencyMs': 50,
                                'users': '17B queries/day'},
               'constraints': ['Response time under 50ms at p99 — suggestions must appear as the user types each '
                               'character',
                               'Top-K results ranked by query frequency, recency, and optional personalization signals',
                               'Support prefix matching and fuzzy matching (handle typos with edit distance ≤ 2)',
                               'Real-time trend updates — breaking news or viral topics should appear within minutes',
                               'Multi-language support with proper Unicode handling and transliteration',
                               'Filter offensive or inappropriate suggestions before returning results',
                               'Personalized suggestions based on user search history when available'],
               'hints': [{'title': 'Trie data structure',
                          'content': 'Use a trie (prefix tree) to efficiently store and query prefix matches. Each '
                                     'node stores the top-K suggestions for that prefix.'},
                         {'title': 'Caching is critical',
                          'content': 'Cache the most popular prefixes (1-3 characters) aggressively — they account for '
                                     'the majority of queries.'},
                         {'title': 'Offline aggregation',
                          'content': 'Use a message queue to collect search logs, then batch-process to update '
                                     'suggestion rankings periodically.'},
                         {'title': 'Advanced: Two-tier approach',
                          'content': 'Serve from an in-memory trie on the app servers for ultra-low latency, backed by '
                                     'a distributed cache (Redis) for longer prefixes. Use a background pipeline that '
                                     'aggregates search logs, computes new rankings, and rebuilds the trie every 15 '
                                     'minutes.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 100},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'app-server', 'x': 400, 'y': 250},
                                               {'componentId': 'cache', 'x': 400, 'y': 100},
                                               {'componentId': 'message-queue', 'x': 400, 'y': 400},
                                               {'componentId': 'nosql-db', 'x': 600, 'y': 250},
                                               {'componentId': 'search', 'x': 600, 'y': 100},
                                               {'componentId': 'monitoring', 'x': 800, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Trie', 'Search', 'Caching']},
              {'id': 'web-crawler',
               'title': 'Web Crawler',
               'difficulty': 'Medium',
               'description': 'Design a distributed web crawler like Googlebot that can crawl billions of web pages '
                              'efficiently. The crawler must manage a URL frontier, respect robots.txt politeness '
                              'policies, deduplicate content, and handle the enormous variety of web page structures. '
                              "Google's crawler discovers and indexes trillions of URLs and maintains an index of over "
                              '400 billion pages — the key design decisions involve URL prioritization, politeness '
                              '(not overwhelming any single domain), and distributed coordination to avoid redundant '
                              'crawls.',
               'requirements': {'readsPerSec': 10000,
                                'writesPerSec': 50000,
                                'storageGB': 50000,
                                'latencyMs': 1000,
                                'users': 'N/A (internal system)'},
               'constraints': ['Crawl rate of 1000+ pages per second across the entire cluster',
                               'Respect robots.txt and per-domain crawl delays — never overwhelm a single website',
                               'URL deduplication using content hashing (SimHash/MinHash) to detect near-duplicate '
                               'pages',
                               'URL frontier with priority queue — prioritize important/fresh pages over deep/stale '
                               'ones',
                               'Handle DNS resolution caching to avoid repeated lookups for the same domain',
                               'Graceful handling of spider traps (infinite URL generation, redirect loops, soft 404s)',
                               'Incremental re-crawling based on page change frequency (adaptive crawl scheduling)'],
               'hints': [{'title': 'URL frontier design',
                          'content': 'Use a message queue as your URL frontier with priority levels. Separate front '
                                     'queues (priority) from back queues (politeness/per-host).'},
                         {'title': 'Deduplication',
                          'content': 'Use a Bloom filter or content hash stored in a NoSQL database to quickly check '
                                     'if a URL or page content has been seen before.'},
                         {'title': 'Distributed workers',
                          'content': 'Multiple crawler workers pull URLs from the frontier, fetch pages, extract '
                                     'links, and push new URLs back. Partition by domain for politeness.'},
                         {'title': 'Advanced: DNS cache + politeness',
                          'content': 'Maintain a local DNS cache (TTL-based) on each crawler worker to reduce DNS '
                                     'overhead. Implement per-domain rate limiters in Redis — each worker checks the '
                                     "domain's last crawl timestamp before fetching. This prevents any single domain "
                                     'from being overwhelmed even with hundreds of workers.'}],
               'referenceSolution': {'nodes': [{'componentId': 'message-queue', 'x': 100, 'y': 250},
                                               {'componentId': 'app-server', 'x': 300, 'y': 250},
                                               {'componentId': 'cache', 'x': 300, 'y': 100},
                                               {'componentId': 'rate-limiter', 'x': 300, 'y': 400},
                                               {'componentId': 'nosql-db', 'x': 550, 'y': 250},
                                               {'componentId': 'object-storage', 'x': 550, 'y': 100},
                                               {'componentId': 'search', 'x': 550, 'y': 400},
                                               {'componentId': 'monitoring', 'x': 750, 'y': 250}],
                                     'edges': [{'source': 'message-queue', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'rate-limiter'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'object-storage'},
                                               {'source': 'nosql-db', 'target': 'search'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Distributed', 'Queue', 'Storage']},
              {'id': 'distributed-cache',
               'title': 'Distributed Cache',
               'difficulty': 'Medium',
               'description': 'Design a distributed in-memory caching system like Redis or Memcached. The system must '
                              'support key-value storage with sub-millisecond reads, consistent hashing for data '
                              'distribution, multiple eviction policies, and replication for fault tolerance. Redis '
                              'can serve hundreds of thousands to over 1 million requests per second per node on '
                              'optimized hardware — the key challenges are maintaining cache coherence across nodes, '
                              'handling hot keys that receive disproportionate traffic, and designing a partition '
                              'strategy that minimizes data movement during scaling events.',
               'requirements': {'readsPerSec': 500000,
                                'writesPerSec': 100000,
                                'storageGB': 500,
                                'latencyMs': 2,
                                'users': 'N/A (infrastructure)'},
               'constraints': ['Sub-millisecond read latency at p99 with support for 1M+ ops/sec per node',
                               'Consistent hashing with virtual nodes for even data distribution and minimal remapping '
                               'on scale events',
                               'Multiple eviction policies: LRU, LFU, TTL-based, and random eviction',
                               'Primary-replica replication with configurable consistency (async for speed, sync for '
                               'safety)',
                               'Hot key detection and mitigation — replicate hot keys across multiple nodes',
                               'Support for data structures beyond key-value: lists, sets, sorted sets, hash maps',
                               'Cluster health monitoring with automatic failover when a primary node goes down'],
               'hints': [{'title': 'Consistent hashing',
                          'content': 'Use consistent hashing with virtual nodes to map keys to cache servers. This '
                                     'minimizes key redistribution when adding/removing nodes.'},
                         {'title': 'Replication',
                          'content': 'Each primary node replicates to 1-2 replicas. On primary failure, promote a '
                                     'replica using leader election.'},
                         {'title': 'Eviction policies',
                          'content': 'Implement LRU using a doubly-linked list + hash map for O(1) eviction. Support '
                                     'configurable policies per cache namespace.'},
                         {'title': 'Advanced: Hot key handling',
                          'content': 'Detect hot keys by sampling access patterns. When a key exceeds a threshold '
                                     '(e.g., 1000 QPS), automatically replicate it to all nodes and route reads using '
                                     'client-side random selection. This distributes the load of '
                                     'celebrity-profile-style hot keys.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'app-server', 'x': 400, 'y': 250},
                                               {'componentId': 'cache', 'x': 600, 'y': 150},
                                               {'componentId': 'nosql-db', 'x': 600, 'y': 350},
                                               {'componentId': 'monitoring', 'x': 800, 'y': 250},
                                               {'componentId': 'service-mesh', 'x': 400, 'y': 100}],
                                     'edges': [{'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'service-mesh'},
                                               {'source': 'service-mesh', 'target': 'cache'},
                                               {'source': 'cache', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Hashing', 'Replication', 'Memory']},
              {'id': 'payment-system',
               'title': 'Payment System',
               'difficulty': 'Hard',
               'description': 'Design a payment processing platform like Stripe or PayPal. The system handles payment '
                              'authorization, capture, settlement, refunds, and ledger management with strict '
                              'financial consistency guarantees. Stripe processes nearly $2 trillion annually — the '
                              'core challenges are ensuring exactly-once payment execution through idempotency keys, '
                              'maintaining a double-entry accounting ledger, and handling the complex state machine of '
                              'payment lifecycles across multiple payment processors and methods.',
               'requirements': {'readsPerSec': 30000,
                                'writesPerSec': 10000,
                                'storageGB': 5000,
                                'latencyMs': 200,
                                'users': '10M merchants'},
               'constraints': ['Exactly-once payment execution using idempotency keys — no double-charges under any '
                               'failure scenario',
                               'Double-entry accounting ledger — every transaction creates balanced debit and credit '
                               'entries',
                               'Support multiple payment methods: credit cards, bank transfers, digital wallets, '
                               'crypto',
                               'PCI DSS compliance — card numbers must be tokenized and never stored in plaintext',
                               'Reconciliation system that matches internal records with bank settlement files daily',
                               'Dispute/chargeback handling workflow with evidence submission and deadline tracking',
                               "Multi-currency support with real-time exchange rates and proper rounding (banker's "
                               'rounding)'],
               'hints': [{'title': 'Idempotency is everything',
                          'content': 'Every payment API call must include an idempotency key. Store the key and result '
                                     'so retries return the same response without re-executing.'},
                         {'title': 'Payment state machine',
                          'content': 'Model payments as a state machine: created → authorized → captured → settled (or '
                                     'refunded). Store every state transition.'},
                         {'title': 'Ledger design',
                          'content': 'Use a SQL database with ACID transactions for the ledger. Every operation '
                                     'creates two rows: a debit and a credit that sum to zero.'},
                         {'title': 'Advanced: Saga pattern',
                          'content': 'Use the saga pattern for multi-step payments (authorize → fraud check → capture '
                                     '→ settle). Each step has a compensating action (e.g., void authorization). A '
                                     'message queue coordinates steps, and failed steps trigger compensating '
                                     'transactions in reverse order.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 100},
                                               {'componentId': 'rate-limiter', 'x': 350, 'y': 420},
                                               {'componentId': 'app-server', 'x': 500, 'y': 250},
                                               {'componentId': 'cache', 'x': 500, 'y': 100},
                                               {'componentId': 'distributed-lock', 'x': 500, 'y': 420},
                                               {'componentId': 'message-queue', 'x': 650, 'y': 420},
                                               {'componentId': 'sql-db', 'x': 700, 'y': 200},
                                               {'componentId': 'nosql-db', 'x': 700, 'y': 100},
                                               {'componentId': 'monitoring', 'x': 850, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'rate-limiter'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'distributed-lock'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['ACID', 'Idempotent', 'Ledger']},
              {'id': 'ticket-booking',
               'title': 'Ticket Booking (Ticketmaster)',
               'difficulty': 'Hard',
               'description': 'Design a ticket booking platform like Ticketmaster or BookMyShow for concerts, sports '
                              'events, and shows. The system must handle massive traffic spikes when popular events go '
                              "on sale (Taylor Swift's Eras Tour saw 14 million users hit the site simultaneously), "
                              'manage seat inventory with optimistic locking to prevent double-booking, and implement '
                              'a virtual waiting room queue. The central challenges are handling extreme concurrency '
                              'on hot inventory, seat hold/release lifecycle management, and preventing bots from '
                              'buying tickets.',
               'requirements': {'readsPerSec': 200000,
                                'writesPerSec': 50000,
                                'storageGB': 1000,
                                'latencyMs': 200,
                                'users': '100M DAU'},
               'constraints': ['No double-booking — optimistic locking or distributed locks must prevent two users '
                               'from booking the same seat',
                               'Virtual waiting room queue that activates when traffic exceeds system capacity '
                               '(fairness guarantee)',
                               'Seat hold with TTL — selected seats are reserved for 10 minutes during checkout, then '
                               'auto-released',
                               'Bot detection and mitigation using CAPTCHA, device fingerprinting, and behavioral '
                               'analysis',
                               'Support interactive seat maps with real-time availability updates via WebSocket/SSE',
                               'Payment timeout handling — if payment fails after seat selection, seats must be '
                               'released back to inventory',
                               'Surge pricing and dynamic pricing tiers based on demand signals and remaining '
                               'inventory'],
               'hints': [{'title': 'Virtual queue',
                          'content': 'When traffic spikes, put users in a Redis-backed FIFO queue. Release them in '
                                     'batches to the booking flow at a controlled rate.'},
                         {'title': 'Inventory locking',
                          'content': 'Use Redis distributed locks (SETNX with TTL) for seat holds. This prevents '
                                     'double-booking while allowing auto-release on timeout.'},
                         {'title': 'Event-driven updates',
                          'content': 'Use a message queue to broadcast seat availability changes to all connected '
                                     'clients in real-time.'},
                         {'title': 'Advanced: Two-phase booking',
                          'content': 'Phase 1: Optimistically reserve the seat in Redis (SETNX with 10-min TTL). Phase '
                                     '2: On payment success, persist to SQL database and remove the Redis hold. On '
                                     'payment failure or timeout, the Redis key auto-expires and the seat becomes '
                                     'available. This gives you both speed and durability.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'rate-limiter', 'x': 350, 'y': 100},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 420},
                                               {'componentId': 'websocket-server', 'x': 530, 'y': 420},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 100},
                                               {'componentId': 'distributed-lock', 'x': 720, 'y': 100},
                                               {'componentId': 'message-queue', 'x': 720, 'y': 420},
                                               {'componentId': 'sql-db', 'x': 720, 'y': 250},
                                               {'componentId': 'nosql-db', 'x': 880, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'rate-limiter'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'websocket-server'},
                                               {'source': 'websocket-server', 'target': 'app-server'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'distributed-lock'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Concurrency', 'Inventory', 'Booking']},
              {'id': 'collaborative-editor',
               'title': 'Google Docs / Collaborative Editor',
               'difficulty': 'Hard',
               'description': 'Design a real-time collaborative document editor like Google Docs or Notion where '
                              'multiple users can simultaneously edit the same document with changes appearing '
                              'instantly for all participants. Google Docs supports up to 100 concurrent editors on a '
                              'single document — the core challenges are conflict resolution when two users edit the '
                              'same paragraph simultaneously (using Operational Transformation or CRDTs), maintaining '
                              'cursor positions and selections across participants, and ensuring document state '
                              'eventually converges to the same result regardless of network delays.',
               'requirements': {'readsPerSec': 50000,
                                'writesPerSec': 30000,
                                'storageGB': 5000,
                                'latencyMs': 100,
                                'users': '100M DAU'},
               'constraints': ['Real-time collaboration with changes visible to all editors within 200ms',
                               'Conflict resolution using OT (Operational Transformation) or CRDTs for concurrent '
                               'edits',
                               "Cursor presence — show each collaborator's cursor position and selection in real-time",
                               'Full version history with point-in-time restore and diff between any two versions',
                               'Offline editing support with automatic merge when reconnecting',
                               'Rich text formatting, tables, images, and embedded content',
                               'Document-level and block-level permissions (view, comment, edit) with sharing '
                               'controls'],
               'hints': [{'title': 'WebSocket for real-time',
                          'content': 'Use persistent WebSocket connections for bidirectional real-time updates between '
                                     'clients and the collaboration server.'},
                         {'title': 'OT vs CRDT',
                          'content': 'OT transforms operations against concurrent edits (used by Google Docs). Figma '
                                     'uses a custom server-authoritative approach inspired by CRDTs. OT is simpler; '
                                     'CRDTs are more robust offline.'},
                         {'title': 'Version history',
                          'content': 'Store document snapshots periodically and individual operations between '
                                     'snapshots. Reconstruct any version by applying ops to the nearest snapshot.'},
                         {'title': 'Advanced: Collaboration server',
                          'content': 'Run a dedicated collaboration server per document that receives all client '
                                     'operations, transforms them against concurrent ops (OT), applies them to the '
                                     'authoritative document state, and broadcasts the transformed ops to all other '
                                     "clients. Use Redis Pub/Sub to coordinate when a document's collaboration server "
                                     'moves between instances.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 420},
                                               {'componentId': 'websocket-server', 'x': 530, 'y': 420},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'message-queue', 'x': 720, 'y': 420},
                                               {'componentId': 'sql-db', 'x': 720, 'y': 200},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 80},
                                               {'componentId': 'object-storage', 'x': 880, 'y': 200},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 370}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'websocket-server'},
                                               {'source': 'websocket-server', 'target': 'app-server'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['CRDT', 'WebSocket', 'Collaboration']},
              {'id': 'file-storage',
               'title': 'Dropbox / File Storage',
               'difficulty': 'Hard',
               'description': 'Design a cloud file storage and synchronization service like Dropbox or Google Drive. '
                              'Users upload files that sync across all their devices, with support for file '
                              'versioning, sharing, and conflict resolution. Dropbox syncs over 1.2 billion files '
                              'daily — the key engineering challenges are efficient delta sync (only uploading changed '
                              'blocks instead of entire files), deduplication across users to save storage, and '
                              'handling conflicts when the same file is edited on multiple devices while offline.',
               'requirements': {'readsPerSec': 50000,
                                'writesPerSec': 20000,
                                'storageGB': 1000000,
                                'latencyMs': 500,
                                'users': '700M registered users'},
               'constraints': ['Block-level chunking (4MB blocks) with content-addressable storage for deduplication',
                               'Delta sync — only upload changed blocks, not the entire file, reducing bandwidth by '
                               '80%+',
                               'File versioning with configurable retention (default 30 days) and point-in-time '
                               'restore',
                               'Conflict resolution for simultaneous edits — create conflict copies with user '
                               'resolution UI',
                               'Real-time sync notifications to all devices when a file changes on any device',
                               'Sharing with granular permissions (view, edit, comment) and shareable links with '
                               'expiration',
                               'Resumable uploads for large files — handle network interruptions without restarting'],
               'hints': [{'title': 'Block-level storage',
                          'content': 'Split files into fixed-size blocks, hash each block, and store blocks in object '
                                     'storage. The metadata DB maps files to ordered lists of block hashes.'},
                         {'title': 'Deduplication',
                          'content': "Use content-addressable storage — if a block hash already exists, don't store it "
                                     'again. This saves massive storage when users share similar files.'},
                         {'title': 'Sync protocol',
                          'content': 'When a file changes, compute the new block list, diff against the stored block '
                                     'list, and only upload new/changed blocks. Notify other devices via a message '
                                     'queue.'},
                         {'title': 'Advanced: Delta sync with rolling hash',
                          'content': 'Use rolling hash (Rabin fingerprint) to detect block boundaries in modified '
                                     'files. This enables variable-size chunking that minimizes the number of changed '
                                     'blocks even when content is inserted in the middle of a file. Combine with a '
                                     'message queue for real-time sync notifications to all connected devices.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 100},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 100},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'object-storage', 'x': 720, 'y': 100},
                                               {'componentId': 'sql-db', 'x': 720, 'y': 250},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Chunking', 'Sync', 'Dedup']},
              {'id': 'parking-lot',
               'title': 'Parking Lot System',
               'difficulty': 'Easy',
               'description': 'Design a smart parking lot management system that tracks vehicle entry/exit, manages '
                              'spot availability in real-time, handles reservations, and processes payments. Modern '
                              'smart parking systems like ParkMobile and SpotHero serve hundreds of millions of annual '
                              'transactions — the key challenges are maintaining accurate real-time availability '
                              'across multiple lots, handling concurrent reservation requests for the same spot, and '
                              'integrating with IoT sensors for automatic occupancy detection.',
               'requirements': {'readsPerSec': 5000,
                                'writesPerSec': 2000,
                                'storageGB': 100,
                                'latencyMs': 200,
                                'users': '10M DAU'},
               'constraints': ['Real-time spot availability updated within 2 seconds of vehicle entry/exit via IoT '
                               'sensors',
                               'Reservation system with time slots — prevent double-booking of the same spot at the '
                               'same time',
                               'Dynamic pricing based on demand, time of day, event proximity, and lot occupancy '
                               'percentage',
                               'Support multiple vehicle types: compact, regular, handicapped, EV charging, motorcycle',
                               'Automatic license plate recognition (LPR) for ticketless entry and exit',
                               'Payment processing with support for hourly, daily, and monthly passes',
                               'Multi-lot management dashboard with analytics (peak hours, revenue, utilization '
                               'trends)'],
               'hints': [{'title': 'Data model',
                          'content': 'Model parking lots with floors, zones, and individual spots. Each spot has a '
                                     'type, status, and optional reservation.'},
                         {'title': 'Real-time availability',
                          'content': 'Use Redis to cache current availability counts per lot/floor/type. Update on '
                                     'every entry/exit event for instant queries.'},
                         {'title': 'Reservation locking',
                          'content': 'Use optimistic locking in the database for reservations — check availability at '
                                     'commit time, not at selection time.'},
                         {'title': 'Advanced: Event-driven updates',
                          'content': 'IoT sensors publish entry/exit events to a message queue. A processor updates '
                                     'the cache (Redis) and database, and broadcasts availability changes to the '
                                     'mobile app via WebSocket for real-time map updates.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'app-server', 'x': 500, 'y': 250},
                                               {'componentId': 'cache', 'x': 500, 'y': 100},
                                               {'componentId': 'message-queue', 'x': 500, 'y': 400},
                                               {'componentId': 'sql-db', 'x': 700, 'y': 250},
                                               {'componentId': 'monitoring', 'x': 700, 'y': 100}],
                                     'edges': [{'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'message-queue', 'target': 'sql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['IoT', 'Real-time', 'Booking']},
              {'id': 'instagram',
               'title': 'Instagram / Photo Sharing',
               'difficulty': 'Medium',
               'description': 'Design a photo and short-video sharing platform like Instagram. Users upload photos '
                              'that are processed (resized, filtered, compressed), stored across a CDN, and displayed '
                              'in a personalized feed. Instagram serves over 3 billion monthly active users and '
                              'processes 100+ million photo uploads daily — the key challenges are building an '
                              'efficient media processing pipeline, generating a ranked feed from thousands of '
                              'candidate posts, and serving media globally with minimal latency using edge caching.',
               'requirements': {'readsPerSec': 150000,
                                'writesPerSec': 20000,
                                'storageGB': 500000,
                                'latencyMs': 200,
                                'users': '500M DAU'},
               'constraints': ['Photo upload processing pipeline: resize to multiple resolutions, apply optional '
                               'filters, strip EXIF data',
                               'Stories (24h ephemeral content) and Reels (short video) alongside permanent posts',
                               'Ranked feed using signals: relationship strength, post engagement, recency, content '
                               'type preferences',
                               'Image/video CDN with edge caching — serve media from the nearest POP to the user',
                               'Social graph storage for followers/following with efficient fan-out for feed '
                               'generation',
                               'Real-time engagement (likes, comments, shares) with optimistic UI updates',
                               'Content moderation pipeline — automated detection of policy-violating content before '
                               'publication'],
               'hints': [{'title': 'Media pipeline',
                          'content': 'Upload original to object storage, push a processing job to a message queue, '
                                     'workers generate thumbnails and resized versions, then update CDN.'},
                         {'title': 'Feed generation',
                          'content': 'Pre-compute feeds for most users (fan-out-on-write). For high-follower accounts, '
                                     'merge their posts at read time (fan-out-on-read).'},
                         {'title': 'CDN strategy',
                          'content': 'Serve all media through a CDN with aggressive caching. Use image-specific CDNs '
                                     '(like Cloudinary or Imgix) for on-the-fly resizing.'},
                         {'title': 'Advanced: Two-tier storage',
                          'content': 'Recent photos (< 30 days) stay on fast SSD-backed object storage with CDN '
                                     'caching. Older photos migrate to cheaper archival storage (S3 Infrequent '
                                     'Access). When an old photo is accessed, the CDN fetches from archival storage '
                                     'and caches it at the edge, hiding the higher latency from users.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 420},
                                               {'componentId': 'app-server', 'x': 530, 'y': 200},
                                               {'componentId': 'cache', 'x': 530, 'y': 60},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 380},
                                               {'componentId': 'object-storage', 'x': 720, 'y': 80},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 250},
                                               {'componentId': 'search', 'x': 720, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['CDN', 'Media', 'Feed']},
              {'id': 'music-streaming',
               'title': 'Spotify / Music Streaming',
               'difficulty': 'Medium',
               'description': 'Design a music streaming platform like Spotify that serves audio content to millions of '
                              'concurrent listeners, manages a catalog of 100M+ tracks, generates personalized '
                              'playlists, and supports offline downloads. Spotify streams billions of minutes of audio '
                              'daily — the key challenges are optimizing audio delivery with adaptive bitrate '
                              'streaming, building a recommendation engine from listening history, and managing music '
                              'licensing and royalty tracking for artists.',
               'requirements': {'readsPerSec': 100000,
                                'writesPerSec': 10000,
                                'storageGB': 500000,
                                'latencyMs': 200,
                                'users': '250M DAU'},
               'constraints': ['Adaptive bitrate audio streaming (96kbps, 160kbps, 320kbps) based on network '
                               'conditions',
                               'Gapless playback with audio pre-buffering — next track starts loading before current '
                               'track ends',
                               'Personalized recommendations: Discover Weekly, Release Radar, daily mixes using '
                               'collaborative filtering',
                               'Offline mode with encrypted local storage — downloaded tracks work without internet',
                               'Social features: collaborative playlists, friend activity, sharing to external '
                               'platforms',
                               'Real-time play count tracking and royalty calculation per stream for rights holders',
                               'Search across 100M+ tracks by title, artist, album, lyrics with fuzzy matching'],
               'hints': [{'title': 'Audio delivery',
                          'content': 'Store audio files in object storage at multiple bitrates. Use a CDN with edge '
                                     'caching for popular tracks — top 1% of tracks account for 80% of streams.'},
                         {'title': 'Recommendation engine',
                          'content': 'Combine collaborative filtering (users who liked X also liked Y) with '
                                     'content-based features (audio analysis, genre, mood). Process listening events '
                                     'through a message queue.'},
                         {'title': 'Catalog and search',
                          'content': 'Store the music catalog in a NoSQL database. Use Elasticsearch for full-text '
                                     'search across titles, artists, and lyrics.'},
                         {'title': 'Advanced: Pre-fetch pipeline',
                          'content': 'When a user is 30 seconds from the end of a track, predict the next track (based '
                                     'on queue, playlist, or auto-play) and start streaming it to the client. Cache '
                                     'frequently co-listened tracks on the same CDN edge node to reduce origin '
                                     'fetches.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 420},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'object-storage', 'x': 720, 'y': 80},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 250},
                                               {'componentId': 'search', 'x': 720, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Streaming', 'CDN', 'Recommendations']},
              {'id': 'ecommerce',
               'title': 'Amazon / E-Commerce',
               'difficulty': 'Hard',
               'description': 'Design a large-scale e-commerce platform like Amazon. The system handles product '
                              'catalog management with millions of SKUs, shopping cart persistence, inventory tracking '
                              'across warehouses, order processing, and personalized recommendations. Amazon processes '
                              'over 300 million active customer accounts and handles millions of orders per hour '
                              'during peak events like Prime Day — the central challenges are maintaining inventory '
                              'consistency across concurrent purchases, building a low-latency product search, and '
                              'orchestrating the complex order fulfillment pipeline.',
               'requirements': {'readsPerSec': 200000,
                                'writesPerSec': 50000,
                                'storageGB': 20000,
                                'latencyMs': 200,
                                'users': '300M active accounts'},
               'constraints': ['Product catalog with 100M+ SKUs, each with variants (size, color), pricing tiers, and '
                               'seller information',
                               'Real-time inventory tracking across multiple warehouses — prevent overselling on '
                               'concurrent purchases',
                               'Shopping cart persistence — carts survive browser closure, device switching, and user '
                               'sign-in/out',
                               'Order processing pipeline: payment → inventory reservation → warehouse assignment → '
                               'shipping → delivery tracking',
                               'Product search with filters (category, price, rating, availability) and typo tolerance',
                               'Personalized recommendations on homepage, product pages, and cart (frequently bought '
                               'together)',
                               'Flash sale / Prime Day handling — 100× normal traffic spikes with fair inventory '
                               'allocation'],
               'hints': [{'title': 'Microservice split',
                          'content': 'Separate services for catalog, cart, inventory, orders, payments, and search. '
                                     'Each scales independently based on its traffic pattern.'},
                         {'title': 'Inventory management',
                          'content': 'Use optimistic locking with version numbers for inventory updates. Reserve stock '
                                     'at checkout, deduct on payment confirmation, release on timeout.'},
                         {'title': 'Cart design',
                          'content': 'Store carts in a NoSQL database (DynamoDB) with the user ID as the key. Merge '
                                     'anonymous carts with user carts on sign-in.'},
                         {'title': 'Advanced: Event sourcing for orders',
                          'content': 'Model orders as a stream of events (created → paid → picked → packed → shipped → '
                                     'delivered). Each event is appended to a message queue. Consumers update '
                                     'projections (order status, inventory, analytics) independently. This gives you '
                                     'full auditability, replay capability, and decoupled services.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 100},
                                               {'componentId': 'rate-limiter', 'x': 350, 'y': 420},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 100},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'sql-db', 'x': 720, 'y': 200},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 350},
                                               {'componentId': 'search', 'x': 880, 'y': 200},
                                               {'componentId': 'object-storage', 'x': 880, 'y': 350},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 80}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'rate-limiter'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Catalog', 'Cart', 'Inventory']},
              {'id': 'team-messaging',
               'title': 'Slack / Team Messaging',
               'difficulty': 'Hard',
               'description': 'Design a workspace-based team messaging platform like Slack or Microsoft Teams. The '
                              'system supports organized channels, threaded conversations, direct messages, file '
                              'sharing, search across message history, and integrations with third-party services. '
                              'Slack handles tens of millions of daily active users across hundreds of thousands of '
                              'workspaces — the key challenges are maintaining message ordering and delivery '
                              'guarantees across channels, building a fast full-text search index over billions of '
                              'messages, and managing the complex permission model of workspaces, channels, and '
                              'threads.',
               'requirements': {'readsPerSec': 100000,
                                'writesPerSec': 30000,
                                'storageGB': 10000,
                                'latencyMs': 100,
                                'users': '100M DAU'},
               'constraints': ['Workspace isolation — data from one workspace must never leak to another (multi-tenant '
                               'security)',
                               'Channel types: public (discoverable), private (invite-only), DMs (1:1 and group)',
                               'Threaded conversations with reply counts, last-reply timestamps, and thread-follow '
                               'notifications',
                               'Real-time message delivery via WebSocket with offline message queuing for disconnected '
                               'clients',
                               'Full-text search across all messages in a workspace with filters (channel, user, date '
                               'range, has:file)',
                               'File sharing with preview generation (images, PDFs, code snippets) and per-file access '
                               'control',
                               'Integration framework for bots and external services (webhooks, slash commands, OAuth '
                               'apps)'],
               'hints': [{'title': 'Message storage',
                          'content': 'Store messages in a NoSQL database partitioned by workspace + channel. Use '
                                     'channel-level sequence numbers for ordering.'},
                         {'title': 'Real-time delivery',
                          'content': 'Maintain WebSocket connections per user. Use Redis Pub/Sub to route messages — '
                                     "subscribe each connection to the user's active channels."},
                         {'title': 'Search architecture',
                          'content': 'Index messages in Elasticsearch partitioned by workspace. Update the index '
                                     'asynchronously via a message queue to avoid slowing down message sends.'},
                         {'title': 'Advanced: Connection gateway',
                          'content': 'Deploy a dedicated WebSocket gateway layer that maintains persistent '
                                     'connections. App servers send messages to the gateway via an internal message '
                                     'bus. The gateway maps user IDs to connections. This separates the stateful '
                                     'connection layer from the stateless business logic, letting each scale '
                                     'independently.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 420},
                                               {'componentId': 'websocket-server', 'x': 530, 'y': 380},
                                               {'componentId': 'app-server', 'x': 530, 'y': 200},
                                               {'componentId': 'cache', 'x': 530, 'y': 60},
                                               {'componentId': 'message-queue', 'x': 720, 'y': 380},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 200},
                                               {'componentId': 'object-storage', 'x': 720, 'y': 60},
                                               {'componentId': 'search', 'x': 880, 'y': 380},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 200},
                                               {'componentId': 'rate-limiter', 'x': 200, 'y': 420}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'load-balancer', 'target': 'rate-limiter'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'websocket-server'},
                                               {'source': 'websocket-server', 'target': 'app-server'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'message-queue', 'target': 'search'},
                                               {'source': 'message-queue', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['WebSocket', 'Search', 'Workspace']},
              {'id': 'metrics-monitoring',
               'title': 'Metrics / Monitoring System',
               'difficulty': 'Hard',
               'description': 'Design a metrics collection and monitoring system like Datadog, Prometheus, or New '
                              'Relic. The system ingests millions of time-series data points per second from thousands '
                              'of servers, stores them efficiently with configurable retention, supports real-time '
                              'dashboarding, and triggers alerts based on complex threshold and anomaly detection '
                              'rules. Datadog ingests trillions of data points daily — the core challenges are '
                              'designing a storage engine optimized for time-series write patterns, supporting '
                              'flexible aggregation queries at sub-second speed, and building a reliable alerting '
                              'pipeline with low false-positive rates.',
               'requirements': {'readsPerSec': 100000,
                                'writesPerSec': 500000,
                                'storageGB': 50000,
                                'latencyMs': 100,
                                'users': 'N/A (infrastructure)'},
               'constraints': ['Ingest 500K+ metrics data points per second with sub-second write latency',
                               'Time-series storage with automatic downsampling: raw (7 days), 1-min avg (30 days), '
                               '1-hour avg (1 year)',
                               'Flexible query language for aggregation: avg, sum, percentiles, rate, group-by across '
                               'arbitrary tag dimensions',
                               'Real-time dashboard rendering with auto-refresh and support for custom visualization '
                               'widgets',
                               'Alerting engine with threshold, anomaly detection, and composite alert conditions',
                               'Alert routing with escalation policies, on-call schedules, and multi-channel delivery '
                               '(PagerDuty, Slack, email)',
                               'Tag-based metric organization with high-cardinality tag support (up to 10K unique '
                               'values per tag)'],
               'hints': [{'title': 'Write-optimized ingestion',
                          'content': 'Use a message queue to buffer incoming metrics. Batch writes to the time-series '
                                     'database for higher throughput.'},
                         {'title': 'Time-series storage',
                          'content': 'Use a specialized time-series database (or NoSQL with time-based partitioning). '
                                     'Compress adjacent data points using delta-of-delta encoding.'},
                         {'title': 'Alerting pipeline',
                          'content': 'Separate the alerting evaluation from ingestion. A dedicated service '
                                     'continuously evaluates alert rules against recent data and fires notifications.'},
                         {'title': 'Advanced: Downsampling pipeline',
                          'content': 'Run a background job that reads raw metrics older than 7 days, computes 1-minute '
                                     'aggregates (avg, min, max, count), writes them to a separate table, and deletes '
                                     'the raw data. Repeat at 30 days for 1-hour aggregates. This reduces storage by '
                                     '100x while keeping historical queries fast.'}],
               'referenceSolution': {'nodes': [{'componentId': 'load-balancer', 'x': 100, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 250, 'y': 250},
                                               {'componentId': 'app-server', 'x': 420, 'y': 200},
                                               {'componentId': 'message-queue', 'x': 420, 'y': 380},
                                               {'componentId': 'cache', 'x': 420, 'y': 60},
                                               {'componentId': 'timeseries-db', 'x': 620, 'y': 200},
                                               {'componentId': 'sql-db', 'x': 620, 'y': 380},
                                               {'componentId': 'search', 'x': 620, 'y': 60},
                                               {'componentId': 'monitoring', 'x': 820, 'y': 200},
                                               {'componentId': 'auth-service', 'x': 250, 'y': 100}],
                                     'edges': [{'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'timeseries-db'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['TimeSeries', 'Alerting', 'Aggregation']},
              {'id': 'netflix',
               'title': 'Netflix / Video Streaming Platform',
               'difficulty': 'Hard',
               'description': 'Design a video streaming platform like Netflix that serves personalized content to 325 '
                              'million subscribers across 190+ countries. Netflix accounts for over 15% of global '
                              'internet bandwidth during peak hours — the key challenges are building a content '
                              'recommendation engine that drives 80% of watch time, implementing adaptive bitrate '
                              'streaming (ABR) that adjusts quality frame-by-frame based on network conditions, and '
                              'leveraging a global CDN (Open Connect) with ISP-embedded appliances to serve 17,000+ '
                              'titles with sub-second start times.',
               'requirements': {'readsPerSec': 300000,
                                'writesPerSec': 5000,
                                'storageGB': 2000000,
                                'latencyMs': 100,
                                'users': '325M subscribers'},
               'constraints': ['Adaptive bitrate streaming (ABR) using per-shot encoding — each scene encoded at '
                               'optimal bitrate/resolution ladder',
                               'Content recommendation engine processing billions of implicit signals (watch time, '
                               'pauses, rewatches, abandons)',
                               'Global CDN with ISP-embedded Open Connect Appliances (OCAs) caching popular content at '
                               'the network edge',
                               'DRM enforcement (Widevine, FairPlay, PlayReady) with license server handling 100K+ '
                               'license requests/sec',
                               'Multi-profile support per account with isolated recommendation models and viewing '
                               'history',
                               'Content ingestion pipeline: ingest mezzanine file → encode 1200+ variants (resolution '
                               '× bitrate × codec) per title'],
               'hints': [{'title': 'Content delivery',
                          'content': 'Use a CDN with ISP-embedded edge appliances for popular titles. Pre-position '
                                     'content during off-peak hours based on predicted regional demand.'},
                         {'title': 'Recommendation engine',
                          'content': 'Combine collaborative filtering with deep learning models trained on viewing '
                                     'patterns. Stream user events through a message queue for real-time signal '
                                     'processing.'},
                         {'title': 'Encoding pipeline',
                          'content': 'Use per-title and per-shot encoding optimization. Process through a message '
                                     'queue that triggers parallel transcoding workers to generate the full '
                                     'resolution/bitrate ladder.'},
                         {'title': 'Advanced: Microservice architecture',
                          'content': 'Netflix uses 1000+ microservices. Separate the control plane (API, auth, '
                                     'recommendations, search) from the data plane (video streaming via CDN). The API '
                                     'gateway (Zuul) handles routing, auth, and rate limiting. Use a cache '
                                     '(EVCache/Memcached) aggressively — Netflix caches billions of data points to '
                                     'achieve sub-100ms API responses.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 420},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 250},
                                               {'componentId': 'object-storage', 'x': 720, 'y': 80},
                                               {'componentId': 'search', 'x': 720, 'y': 420},
                                               {'componentId': 'stream-processor', 'x': 880, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'message-queue', 'target': 'stream-processor'},
                                               {'source': 'message-queue', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Streaming', 'CDN', 'Recommendations', 'DRM']},
              {'id': 'tinder',
               'title': 'Tinder / Dating App',
               'difficulty': 'Medium',
               'description': 'Design a location-based dating application like Tinder that matches users based on '
                              'geographic proximity, preferences, and compatibility signals. Tinder processes over 2 '
                              'billion swipes per day with 75 million monthly active users — the key challenges are '
                              'building an efficient geospatial index for proximity matching, a recommendation engine '
                              'that surfaces relevant profiles while avoiding already-seen users, and handling the '
                              'high write throughput of swipe events with real-time match notifications when two users '
                              'swipe right on each other.',
               'requirements': {'readsPerSec': 100000,
                                'writesPerSec': 50000,
                                'storageGB': 100000,
                                'latencyMs': 200,
                                'users': '75M MAU'},
               'constraints': ['Geospatial proximity search using geohashing or R-tree index — find users within '
                               'configurable radius (1-160 km)',
                               'Recommendation engine that filters by preferences (age, gender, distance) and ranks by '
                               'compatibility score',
                               'Swipe deduplication — never show a user the same profile twice, even across sessions',
                               'Real-time match detection — when both users swipe right, notify both instantly via '
                               'push notification',
                               'Photo storage and serving with face detection validation and content moderation '
                               'pipeline',
                               'ELO-like scoring system that adapts profile visibility based on desirability signals'],
               'hints': [{'title': 'Geospatial indexing',
                          'content': 'Use geohashing to partition users by location. Store active user locations in '
                                     'Redis with GEOADD for O(log N) proximity queries within a radius.'},
                         {'title': 'Recommendation pipeline',
                          'content': 'Pre-compute a recommendation deck for each active user: filter by preferences, '
                                     'exclude already-swiped profiles, rank by compatibility score, and cache the top '
                                     '100 candidates.'},
                         {'title': 'Match detection',
                          'content': 'On each right-swipe, check if the target user has already right-swiped the '
                                     'current user. Store swipes in a NoSQL database keyed by (swiper, swipee) for '
                                     'O(1) lookup.'},
                         {'title': 'Advanced: Sharded recommendation',
                          'content': 'Partition the user base by geohash prefix so each recommendation shard handles a '
                                     'geographic region. Within each shard, maintain a bloom filter of seen profiles '
                                     'per user to avoid re-showing. Pre-compute recommendation decks during off-peak '
                                     'hours using a stream processor that scores all eligible matches.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 200},
                                               {'componentId': 'object-storage', 'x': 720, 'y': 80},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'stream-processor', 'x': 720, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'stream-processor'},
                                               {'source': 'stream-processor', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Geo-spatial', 'Matching', 'Recommendations', 'Real-time']},
              {'id': 'google-maps',
               'title': 'Google Maps / Navigation',
               'difficulty': 'Hard',
               'description': 'Design a mapping and navigation platform like Google Maps that serves map tiles, '
                              'computes optimal routes, provides real-time traffic updates, and estimates accurate '
                              'ETAs. Google Maps serves over 1 billion daily active users and processes 1 billion '
                              'kilometers of driving directions daily — the core challenges are serving pre-rendered '
                              'map tiles at multiple zoom levels from a multi-petabyte tile corpus, computing shortest '
                              'paths on a road graph with hundreds of millions of edges using hierarchical algorithms '
                              '(Contraction Hierarchies / A*), and ingesting real-time GPS probe data from millions of '
                              'devices to update traffic conditions every 30 seconds.',
               'requirements': {'readsPerSec': 500000,
                                'writesPerSec': 100000,
                                'storageGB': 5000000,
                                'latencyMs': 200,
                                'users': '1B DAU'},
               'constraints': ['Map tile serving at 20+ zoom levels — vector tiles for mobile, raster tiles for web, '
                               'pre-rendered and cached at CDN edge',
                               'Route computation using Contraction Hierarchies or A* on a graph with 500M+ road '
                               'segments in under 200ms',
                               'Real-time traffic layer updated every 30 seconds from GPS probe data aggregated across '
                               'millions of active drivers',
                               'ETA prediction combining historical patterns, live traffic, road type, and time-of-day '
                               'with < 20% error',
                               'Multi-modal routing: driving, walking, cycling, public transit with real-time schedule '
                               'integration',
                               'Geocoding and reverse geocoding with fuzzy address matching across 200+ countries and '
                               'scripts'],
               'hints': [{'title': 'Map tile serving',
                          'content': 'Pre-render tiles at each zoom level and store in object storage. Serve via CDN '
                                     'for instant loading. Use vector tiles on mobile to reduce bandwidth — the client '
                                     'renders them locally.'},
                         {'title': 'Route computation',
                          'content': 'Use Contraction Hierarchies (CH) to preprocess the road graph. CH reduces a '
                                     'cross-country route query from millions of edge relaxations to a few thousand, '
                                     'enabling sub-200ms responses.'},
                         {'title': 'Real-time traffic',
                          'content': 'Ingest GPS probes from active users into a stream processor. Aggregate speed per '
                                     'road segment over 30-second windows. Store in a time-series database and overlay '
                                     'on the pre-computed road graph.'},
                         {'title': 'Advanced: Partitioned graph serving',
                          'content': 'Partition the road graph geographically. Each partition server handles local '
                                     'routing. For cross-partition routes, use a two-level approach: a global overlay '
                                     'graph of inter-partition highways handles the macro route, then local servers '
                                     'compute the first-mile and last-mile segments. Cache popular origin-destination '
                                     'pairs for instant responses.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 200},
                                               {'componentId': 'object-storage', 'x': 720, 'y': 80},
                                               {'componentId': 'stream-processor', 'x': 530, 'y': 420},
                                               {'componentId': 'timeseries-db', 'x': 720, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'stream-processor'},
                                               {'source': 'stream-processor', 'target': 'timeseries-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Geo-spatial', 'Graph', 'Real-time', 'CDN']},
              {'id': 'zoom',
               'title': 'Zoom / Video Conferencing',
               'difficulty': 'Hard',
               'description': 'Design a real-time video conferencing platform like Zoom that supports meetings with up '
                              'to 1000 participants, screen sharing, recording, and breakout rooms. Zoom handles over '
                              '300 million daily meeting participants with end-to-end latency under 150ms — the core '
                              'challenges are building a Selective Forwarding Unit (SFU) architecture that routes '
                              'video streams without transcoding to minimize latency, managing bandwidth allocation '
                              'when dozens of participants have cameras enabled simultaneously, and providing reliable '
                              'recording with server-side mixing for cloud playback.',
               'requirements': {'readsPerSec': 50000,
                                'writesPerSec': 50000,
                                'storageGB': 500000,
                                'latencyMs': 50,
                                'users': '300M daily meeting participants'},
               'constraints': ['End-to-end glass-to-glass latency under 150ms for real-time audio/video using WebRTC '
                               'or custom UDP protocol',
                               'SFU (Selective Forwarding Unit) architecture — server forwards streams without '
                               'transcoding to minimize latency',
                               'Simulcast: each sender encodes 3 quality layers (low/medium/high), SFU selects '
                               'per-receiver based on bandwidth and layout',
                               'Screen sharing at 1080p/30fps alongside camera feeds with independent bandwidth '
                               'allocation',
                               'Cloud recording with server-side mixing — composite multiple video streams into a '
                               'single recording file',
                               'Breakout rooms, waiting rooms, and host controls with real-time state synchronization '
                               'across all participants'],
               'hints': [{'title': 'SFU over MCU',
                          'content': 'Use a Selective Forwarding Unit (SFU) instead of a Multipoint Control Unit '
                                     '(MCU). SFU forwards packets without decoding/re-encoding, reducing latency and '
                                     'server CPU cost by 10x compared to MCU.'},
                         {'title': 'Simulcast for bandwidth',
                          'content': 'Each sender publishes 3 quality layers (e.g., 180p, 360p, 720p). The SFU '
                                     'dynamically selects the appropriate layer for each receiver based on their '
                                     'available bandwidth and visible tile size.'},
                         {'title': 'Distributed media routing',
                          'content': 'Deploy SFU servers in multiple regions. For cross-region meetings, cascade SFU '
                                     "servers over dedicated backbone links rather than sending each participant's "
                                     'stream across regions independently.'},
                         {'title': 'Advanced: Geo-distributed SFU mesh',
                          'content': "For global meetings, deploy SFU nodes in each participant's nearest region. "
                                     "Connect SFU nodes via a server-to-server mesh over the provider's backbone "
                                     'network. Each SFU forwards only the active speaker and pinned streams across '
                                     'regions (not all participants), reducing cross-region bandwidth by 80%. Use SRTP '
                                     'for encryption and RTCP feedback for congestion control.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'websocket-server', 'x': 350, 'y': 420},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 200},
                                               {'componentId': 'object-storage', 'x': 720, 'y': 80},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'load-balancer', 'target': 'websocket-server'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'websocket-server', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['WebRTC', 'Real-time', 'Media', 'SFU']},
              {'id': 'food-delivery',
               'title': 'Doordash / Food Delivery',
               'difficulty': 'Hard',
               'description': 'Design a food delivery platform like DoorDash or Uber Eats that connects customers, '
                              'restaurants, and delivery drivers in real-time. DoorDash processes over 750 million '
                              'orders per quarter across 500,000+ merchant partners — the core challenges are building '
                              'a real-time dispatch system that optimally matches orders to drivers (considering '
                              'location, capacity, and estimated completion times), maintaining accurate ETAs that '
                              'update as conditions change, and handling the three-sided marketplace where restaurant '
                              'prep times, driver routes, and customer expectations must all be balanced '
                              'simultaneously.',
               'requirements': {'readsPerSec': 80000,
                                'writesPerSec': 40000,
                                'storageGB': 50000,
                                'latencyMs': 200,
                                'users': '46M MAU'},
               'constraints': ['Real-time order tracking with GPS updates every 5 seconds from active delivery drivers',
                               'Driver dispatch algorithm optimizing for delivery time, driver earnings, and order '
                               'batching (multi-pickup routes)',
                               'Restaurant inventory and prep-time estimation — dynamically adjust menu availability '
                               'based on kitchen capacity',
                               'ETA prediction combining restaurant prep time, driver travel time, and real-time '
                               'traffic conditions',
                               'Payment splitting: customer charge, restaurant payout (minus commission), driver '
                               'payout (base + tips + peak pay)',
                               'Surge pricing and delivery fee calculation based on real-time demand/supply ratio per '
                               'zone'],
               'hints': [{'title': 'Three-sided marketplace',
                          'content': 'Model the system as three user types: customers (ordering), restaurants '
                                     '(preparing), and drivers (delivering). Each has separate real-time state that '
                                     'must be coordinated.'},
                         {'title': 'Dispatch optimization',
                          'content': 'Use a centralized dispatch service that runs a matching algorithm every few '
                                     'seconds, considering driver proximity to restaurant, current orders in progress, '
                                     'and restaurant prep time estimates.'},
                         {'title': 'Real-time tracking',
                          'content': 'Ingest driver GPS updates into a stream processor. Update ETAs in real-time and '
                                     'push to customers via WebSocket or server-sent events.'},
                         {'title': 'Advanced: Order batching',
                          'content': 'DoorDash groups multiple orders from nearby restaurants heading to nearby '
                                     'destinations into a single driver route. The dispatch algorithm runs a '
                                     'traveling-salesman heuristic (nearest-neighbor with 2-opt improvement) to '
                                     'minimize total delivery time while keeping each individual order within its '
                                     'promised ETA window.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 300},
                                               {'componentId': 'sql-db', 'x': 720, 'y': 150},
                                               {'componentId': 'stream-processor', 'x': 720, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'message-queue', 'target': 'stream-processor'},
                                               {'source': 'stream-processor', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Geo-spatial', 'Real-time', 'Dispatch', 'Marketplace']},
              {'id': 'reddit',
               'title': 'Reddit / Social News',
               'difficulty': 'Medium',
               'description': 'Design a social news aggregation and discussion platform like Reddit. Users submit '
                              'posts to topic-based communities (subreddits), vote content up or down, and engage in '
                              'deeply nested comment threads. Reddit serves 97+ million daily active users across '
                              '100,000+ active communities — the key challenges are implementing a ranking algorithm '
                              '(hot, top, controversial, best) that surfaces quality content across communities of '
                              'vastly different sizes, efficiently storing and rendering deeply nested comment trees '
                              'with thousands of replies, and building a moderation system that scales across '
                              'volunteer moderators.',
               'requirements': {'readsPerSec': 200000,
                                'writesPerSec': 20000,
                                'storageGB': 200000,
                                'latencyMs': 200,
                                'users': '97M DAU'},
               'constraints': ['Multiple ranking algorithms: hot (time-decayed score), top (by time window), '
                               'controversial (balanced up/down), best (Wilson score)',
                               'Nested comment trees with efficient rendering — load top-level comments first, '
                               'lazy-load deep threads',
                               'Subreddit isolation — each community has its own rules, moderators, CSS themes, and '
                               'content policies',
                               'Vote counting with anti-manipulation: rate limiting, vote fuzzing, and bot detection',
                               'Cross-posting and content aggregation across subreddits with deduplication on /r/all',
                               'Full-text search across posts and comments with subreddit and time-range filters'],
               'hints': [{'title': 'Ranking algorithm',
                          'content': "Reddit's hot ranking uses: score = log10(max(|ups - downs|, 1)) + sign(ups - "
                                     'downs) * (post_time - epoch) / 45000. Pre-compute rankings and cache the sorted '
                                     'feeds for each subreddit.'},
                         {'title': 'Comment tree storage',
                          'content': 'Store comments in a NoSQL database with parent_id for tree structure. Use '
                                     "materialized path (e.g., 'root/parent/child') for efficient subtree queries. "
                                     'Cache top-level comments aggressively.'},
                         {'title': 'Vote processing',
                          'content': 'Process votes through a message queue to decouple the fast vote acknowledgment '
                                     'from the slower ranking recalculation. Use Redis to cache current vote counts '
                                     'per post.'},
                         {'title': 'Advanced: Hybrid feed computation',
                          'content': 'For small subreddits (< 10K subscribers), compute rankings on the fly from '
                                     'cached vote counts. For large subreddits (> 100K), pre-compute ranked feeds '
                                     'every 30 seconds using a background job. For /r/all, use a stream processor that '
                                     'merges top posts from all subreddits with normalized scoring to prevent large '
                                     'communities from dominating.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 200},
                                               {'componentId': 'sql-db', 'x': 720, 'y': 350},
                                               {'componentId': 'search', 'x': 880, 'y': 200},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 350}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Ranking', 'Comments', 'Voting', 'Community']},
              {'id': 'airbnb',
               'title': 'Airbnb / Booking Platform',
               'difficulty': 'Hard',
               'description': 'Design a property rental and booking platform like Airbnb that connects hosts with '
                              'guests for short-term stays. Airbnb has 7+ million active listings across 220 countries '
                              'with billions of monthly searches — the core challenges are building a search system '
                              'that handles complex multi-dimensional queries (location, dates, price, amenities, '
                              'guest count), implementing a booking and reservation system that prevents '
                              'double-booking across overlapping date ranges, and building a dynamic pricing algorithm '
                              'that helps hosts optimize revenue based on seasonality, local events, and comparable '
                              'listings.',
               'requirements': {'readsPerSec': 100000,
                                'writesPerSec': 10000,
                                'storageGB': 100000,
                                'latencyMs': 200,
                                'users': '50M DAU'},
               'constraints': ['Search with compound filters: location (geo-radius), date range availability, price '
                               'range, guest count, amenities, property type',
                               'Calendar-based availability management — hosts block dates, bookings reserve date '
                               'ranges, no double-booking allowed',
                               'Reservation system with hold-and-confirm pattern: temporarily hold dates during '
                               'checkout flow (15-min TTL)',
                               'Dynamic pricing suggestions using comparable listings, seasonality patterns, local '
                               'event calendars, and demand forecasts',
                               'Review system with bilateral reviews (host reviews guest, guest reviews host) revealed '
                               'simultaneously after both submit',
                               'Multi-currency pricing with real-time exchange rates, host payout in local currency, '
                               'guest charges in their currency'],
               'hints': [{'title': 'Search architecture',
                          'content': 'Use Elasticsearch with geo_point for location search, date range queries for '
                                     'availability, and filters for amenities/price. Pre-compute availability '
                                     'calendars as bitmaps for fast date-range intersection.'},
                         {'title': 'Availability management',
                          'content': "Store each listing's availability as a calendar in a SQL database. Use row-level "
                                     'locking or optimistic concurrency to prevent double-booking when two guests try '
                                     'to book overlapping dates.'},
                         {'title': 'Booking flow',
                          'content': 'Phase 1: Hold the dates in a distributed lock (Redis SETNX with 15-min TTL). '
                                     'Phase 2: Process payment. Phase 3: Confirm booking in SQL and release the lock. '
                                     'On timeout, dates auto-release.'},
                         {'title': 'Advanced: Search relevance',
                          'content': "Airbnb's search ranking combines 100+ features: price competitiveness, host "
                                     'response rate, listing quality score, guest-listing compatibility, and '
                                     'conversion probability. Use a two-stage ranking pipeline: a fast candidate '
                                     'retrieval phase (Elasticsearch with geo + date filters) followed by a '
                                     'machine-learned re-ranking model (gradient boosted trees) that scores the top '
                                     '1000 candidates.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'sql-db', 'x': 720, 'y': 150},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 300},
                                               {'componentId': 'search', 'x': 880, 'y': 150},
                                               {'componentId': 'object-storage', 'x': 880, 'y': 300},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 420}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Search', 'Booking', 'Geo-spatial', 'Marketplace']},
              {'id': 'whatsapp',
               'title': 'WhatsApp / Messaging',
               'difficulty': 'Hard',
               'description': 'Design an end-to-end encrypted messaging platform like WhatsApp that handles 100+ '
                              'billion messages per day across 3 billion monthly active users. The server never sees '
                              'plaintext message content — the core challenges are implementing the Signal Protocol '
                              'for end-to-end encryption with perfect forward secrecy, reliably delivering messages to '
                              'offline users (store-and-forward), efficiently fanning out messages in group chats (up '
                              'to 1024 members), and synchronizing message state across multiple linked devices while '
                              'maintaining encryption guarantees.',
               'requirements': {'readsPerSec': 100000,
                                'writesPerSec': 1000000,
                                'storageGB': 500000,
                                'latencyMs': 50,
                                'users': '3B MAU'},
               'constraints': ['End-to-end encryption using Signal Protocol — server stores only ciphertext, key '
                               'exchange via X3DH (Extended Triple Diffie-Hellman)',
                               'Offline message delivery with store-and-forward — messages queued on server until '
                               'recipient reconnects, then delivered in order',
                               'Group messaging up to 1024 members with Sender Keys protocol for efficient group '
                               'encryption',
                               'Media sharing with encrypted upload — media encrypted client-side, uploaded to object '
                               'storage, decryption key sent in message',
                               'Multi-device support (WhatsApp Web/Desktop) with message sync using companion device '
                               'protocol',
                               'Read receipts, typing indicators, and online presence as ephemeral signals (no '
                               'persistent storage)'],
               'hints': [{'title': 'Connection management',
                          'content': 'Maintain persistent WebSocket connections from each client to a connection '
                                     'gateway. Store the mapping of user ID → gateway server in Redis for message '
                                     'routing.'},
                         {'title': 'Message delivery',
                          'content': "On send: encrypt client-side, send to server, server queues in recipient's inbox "
                                     '(NoSQL). When recipient is online, push immediately via their WebSocket '
                                     'connection. When offline, store and deliver on reconnect.'},
                         {'title': 'Group messaging',
                          'content': 'Use Sender Keys: the sender encrypts the message once with a shared group key, '
                                     'server fans out the ciphertext to all group members. This avoids N separate '
                                     'encryptions per message.'},
                         {'title': 'Advanced: Multi-device sync',
                          'content': "WhatsApp's multi-device architecture treats each device as a separate Signal "
                                     'Protocol client. When sending to a user with 4 linked devices, the sender '
                                     "encrypts the message 4 times (once per device's public key). Each device "
                                     'maintains its own ratchet state. The server stores per-device message queues and '
                                     'delivers independently. This eliminates the need for a primary device to be '
                                     'online.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'websocket-server', 'x': 200, 'y': 100},
                                               {'componentId': 'app-server', 'x': 400, 'y': 250},
                                               {'componentId': 'cache', 'x': 400, 'y': 100},
                                               {'componentId': 'message-queue', 'x': 400, 'y': 400},
                                               {'componentId': 'nosql-db', 'x': 600, 'y': 250},
                                               {'componentId': 'object-storage', 'x': 600, 'y': 100},
                                               {'componentId': 'monitoring', 'x': 800, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'websocket-server'},
                                               {'source': 'websocket-server', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Encryption', 'WebSocket', 'Messaging', 'Real-time']},
              {'id': 'search-engine',
               'title': 'Google Search / Search Engine',
               'difficulty': 'Hard',
               'description': 'Design a web search engine like Google that crawls billions of web pages, builds an '
                              'inverted index, ranks results by relevance, and returns the top results in under 200ms. '
                              'Google processes over 8.5 billion searches per day across an index of hundreds of '
                              'billions of pages (hundreds of petabytes) — the core challenges are building and '
                              'maintaining a distributed inverted index that maps every word to the documents '
                              'containing it, implementing a ranking algorithm (PageRank + hundreds of signals) that '
                              'surfaces the most relevant results, and serving queries with sub-200ms latency by '
                              'scattering the query across thousands of index shards in parallel.',
               'requirements': {'readsPerSec': 500000,
                                'writesPerSec': 50000,
                                'storageGB': 10000000,
                                'latencyMs': 200,
                                'users': '8.5B queries/day'},
               'constraints': ['Distributed inverted index sharded across thousands of machines — each shard holds a '
                               'portion of the web',
                               'PageRank computation over a web graph of 100B+ nodes using iterative MapReduce '
                               '(converges in 40-50 iterations)',
                               'Query parsing with spell correction, synonym expansion, entity recognition, and intent '
                               'classification',
                               'Sub-200ms query latency by scatter-gather across index shards with aggressive timeouts '
                               '(drop slow shards)',
                               'Freshness: crawl and re-index high-priority pages (news sites) within minutes of '
                               'changes',
                               'Snippet generation — extract the most relevant text fragment from each result page to '
                               'display in results'],
               'hints': [{'title': 'Inverted index',
                          'content': 'Build an inverted index mapping each term to a sorted list of (docID, frequency, '
                                     'positions). Shard by document (each shard holds the full index for a subset of '
                                     'pages). At query time, scatter the query to all shards and merge results.'},
                         {'title': 'Ranking signals',
                          'content': 'Combine hundreds of signals: PageRank (link authority), BM25 (term relevance), '
                                     'freshness, page speed, mobile-friendliness, and user engagement metrics. Use a '
                                     'machine-learned model to weight signals.'},
                         {'title': 'Crawl and index pipeline',
                          'content': 'Web crawler discovers pages → message queue → parser extracts text and links → '
                                     'indexer updates inverted index → PageRank recomputes periodically on the link '
                                     'graph.'},
                         {'title': 'Advanced: Two-phase ranking',
                          'content': 'Phase 1 (retrieval): Use the inverted index to find candidate documents matching '
                                     'the query terms using BM25 scoring — returns top 1000 candidates per shard. '
                                     'Phase 2 (ranking): A machine-learned model re-ranks candidates using 200+ '
                                     'features (PageRank, click-through rate, query-document embedding similarity). '
                                     'This two-phase approach lets you apply expensive ranking only to promising '
                                     'candidates.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 150},
                                               {'componentId': 'search', 'x': 720, 'y': 300},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'object-storage', 'x': 880, 'y': 150},
                                               {'componentId': 'stream-processor', 'x': 720, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 300}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'stream-processor'},
                                               {'source': 'stream-processor', 'target': 'search'},
                                               {'source': 'app-server', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Search', 'Indexing', 'PageRank', 'Distributed']},
              {'id': 'location-service',
               'title': 'Yelp / Location-Based Service',
               'difficulty': 'Medium',
               'description': 'Design a location-based business discovery and review platform like Yelp or Google '
                              'Places. Users search for businesses by category and proximity, browse photos and '
                              'reviews, and contribute their own ratings. Yelp indexes over 330 million reviews for 7+ '
                              'million businesses — the core challenges are building an efficient geospatial index '
                              '(QuadTree or Geohash) that supports proximity search with category filters, aggregating '
                              'review scores in real-time as new reviews come in, and serving business detail pages '
                              'with rich media from a global CDN.',
               'requirements': {'readsPerSec': 100000,
                                'writesPerSec': 5000,
                                'storageGB': 50000,
                                'latencyMs': 200,
                                'users': '33M monthly unique visitors'},
               'constraints': ['Geospatial search using QuadTree or Geohash index — find businesses within radius '
                               'sorted by relevance and distance',
                               'Compound search: category + location + price range + rating + open-now with sub-200ms '
                               'response',
                               'Review aggregation with Bayesian average rating (accounts for review count, not just '
                               'mean score)',
                               'Photo storage with thumbnails, CDN serving, and user-uploaded content moderation',
                               'Business profile pages with hours, menu (for restaurants), and real-time busy-times '
                               'based on check-in data',
                               'Autocomplete for business names and categories with typo tolerance and location-biased '
                               'results'],
               'hints': [{'title': 'Geospatial indexing',
                          'content': 'Use a QuadTree to partition geographic space. Each leaf node contains businesses '
                                     'within that area. Proximity queries traverse the tree to find nearby leaves, '
                                     'then filter by radius. Alternatively, use Geohash with prefix matching.'},
                         {'title': 'Search with filters',
                          'content': 'Use Elasticsearch with geo_distance queries for proximity search. Add filters '
                                     'for category, price range, and open hours. Pre-compute popular searches per '
                                     'geohash cell for instant results.'},
                         {'title': 'Review aggregation',
                          'content': 'Cache aggregate ratings in Redis. On new review, update the running average '
                                     'atomically. Use Bayesian average to prevent businesses with few 5-star reviews '
                                     'from outranking those with hundreds of 4.5-star reviews.'},
                         {'title': 'Advanced: QuadTree sharding',
                          'content': 'Build a distributed QuadTree where each server owns a geographic partition. '
                                     'Dense areas (Manhattan) get finer-grained partitions than rural areas. A routing '
                                     "layer maps the user's search center to the relevant partition servers. For "
                                     'boundary queries (search radius spans multiple partitions), query adjacent '
                                     'partitions in parallel and merge results.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 200},
                                               {'componentId': 'search', 'x': 720, 'y': 350},
                                               {'componentId': 'object-storage', 'x': 880, 'y': 200},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 350}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Geo-spatial', 'Search', 'Reviews', 'QuadTree']},
              {'id': 'tiktok',
               'title': 'TikTok / Short Video',
               'difficulty': 'Hard',
               'description': 'Design a short-form video platform like TikTok that serves personalized video feeds to '
                              "over 1.5 billion monthly active users. TikTok's recommendation engine is its core "
                              'competitive advantage — it builds interest graphs from watch-time signals (not just '
                              'social graphs) to surface relevant content even for new users within minutes. The '
                              'platform processes billions of video views per day with a multi-petabyte content '
                              'library — the key challenges are building the For You Page (FYP) recommendation '
                              'algorithm, a high-throughput video transcoding pipeline that processes millions of '
                              'uploads daily, and a content moderation system that reviews content before publication.',
               'requirements': {'readsPerSec': 500000,
                                'writesPerSec': 50000,
                                'storageGB': 5000000,
                                'latencyMs': 100,
                                'users': '1.5B MAU'},
               'constraints': ['For You Page recommendation combining collaborative filtering, content embeddings, and '
                               'real-time engagement signals',
                               'Video transcoding pipeline: ingest → content moderation → transcode (multiple '
                               'resolutions/bitrates) → CDN distribution',
                               'Content moderation at upload time — automated detection of policy violations (nudity, '
                               'violence, misinformation) before publication',
                               'Creator economy features: live gifting, creator fund payouts, branded content '
                               'marketplace',
                               'Duet and Stitch features requiring frame-accurate video composition on server or '
                               'client',
                               'Global CDN with regional content regulations — different content availability per '
                               'country'],
               'hints': [{'title': 'Recommendation engine',
                          'content': "TikTok's FYP uses an interest graph built from watch-time signals (not social "
                                     'graph). Track: watch duration, replays, shares, comments, follows-from-video. '
                                     'Feed these signals into a real-time stream processor.'},
                         {'title': 'Video pipeline',
                          'content': 'Upload to object storage → push processing job to message queue → workers '
                                     'transcode to 360p/720p/1080p → push to CDN. Run content moderation in parallel '
                                     'with transcoding to minimize time-to-publish.'},
                         {'title': 'Feed serving',
                          'content': 'Pre-compute a ranked candidate pool per user. On each swipe, serve the next '
                                     'video from the pool. Refresh the pool every few minutes using the latest '
                                     'engagement signals.'},
                         {'title': 'Advanced: Two-tower recommendation',
                          'content': 'Use a two-tower neural network: one tower encodes user interests (watch history, '
                                     'engagement patterns), the other encodes video features (visual embeddings, '
                                     'audio, text, hashtags). Compute dot-product similarity to score candidates. '
                                     'Generate candidates from multiple sources: interest graph, trending, geographic, '
                                     'and following — then blend and re-rank using the two-tower model for the final '
                                     'feed.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 200},
                                               {'componentId': 'object-storage', 'x': 720, 'y': 80},
                                               {'componentId': 'search', 'x': 880, 'y': 80},
                                               {'componentId': 'stream-processor', 'x': 720, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'cdn', 'target': 'object-storage'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'search'},
                                               {'source': 'message-queue', 'target': 'stream-processor'},
                                               {'source': 'message-queue', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Recommendations', 'CDN', 'Streaming', 'ML']},
              {'id': 'message-queue-design',
               'title': 'Distributed Message Queue (Kafka)',
               'difficulty': 'Hard',
               'description': 'Design a distributed message queue system like Apache Kafka that provides durable, '
                              'ordered, and high-throughput message delivery between services. Kafka processes '
                              'trillions of messages per day at companies like LinkedIn, handling 1M+ messages/second '
                              'per broker — the core challenges are designing a partitioned commit log that supports '
                              'parallel consumption, implementing consumer group coordination with partition '
                              'rebalancing, achieving exactly-once semantics through idempotent producers and '
                              'transactional writes, and maintaining data durability through in-sync replica (ISR) '
                              'sets with configurable acknowledgment levels.',
               'requirements': {'readsPerSec': 1000000,
                                'writesPerSec': 1000000,
                                'storageGB': 500000,
                                'latencyMs': 5,
                                'users': 'N/A (infrastructure)'},
               'constraints': ['Partitioned commit log — messages within a partition are strictly ordered and assigned '
                               'monotonic offsets',
                               'Consumer groups with automatic partition assignment — each partition consumed by '
                               'exactly one consumer in the group',
                               'In-Sync Replica (ISR) set — configurable replication factor (typically 3) with '
                               'leader-based writes and follower replication',
                               'Exactly-once semantics via idempotent producers (sequence numbers per partition) and '
                               'transactional writes across partitions',
                               'Log compaction — retain only the latest value per key for changelog/snapshot topics',
                               'Configurable retention: time-based (7 days default) or size-based (per partition log '
                               'segment cleanup)'],
               'hints': [{'title': 'Partitioned log',
                          'content': 'Model each topic as N partitions. Each partition is an append-only log stored on '
                                     'disk. Producers hash the message key to determine the target partition. This '
                                     'enables parallel writes and ordered consumption per partition.'},
                         {'title': 'Replication for durability',
                          'content': 'Each partition has a leader and N-1 follower replicas. Producers write to the '
                                     'leader, followers pull and replicate. The ISR (In-Sync Replica) set tracks which '
                                     'followers are caught up. Configurable acks: 0 (fire-and-forget), 1 (leader '
                                     'only), all (all ISR replicas).'},
                         {'title': 'Consumer groups',
                          'content': 'A consumer group coordinator assigns partitions to consumers. When a consumer '
                                     'joins or leaves, trigger a rebalance. Store consumer offsets in an internal '
                                     '__consumer_offsets topic for durability.'},
                         {'title': 'Advanced: Zero-copy and page cache',
                          'content': 'Kafka achieves high throughput by leveraging the OS page cache for reads (no '
                                     'application-level cache needed) and zero-copy transfers (sendfile syscall) from '
                                     'disk to network socket. Sequential disk writes are faster than random memory '
                                     "access — Kafka's append-only log exploits this for 800MB/s+ write throughput per "
                                     'broker on commodity SSDs.'}],
               'referenceSolution': {'nodes': [{'componentId': 'load-balancer', 'x': 100, 'y': 250},
                                               {'componentId': 'app-server', 'x': 300, 'y': 250},
                                               {'componentId': 'nosql-db', 'x': 500, 'y': 150},
                                               {'componentId': 'monitoring', 'x': 500, 'y': 350},
                                               {'componentId': 'distributed-lock', 'x': 300, 'y': 100},
                                               {'componentId': 'service-discovery', 'x': 300, 'y': 400}],
                                     'edges': [{'source': 'load-balancer', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'distributed-lock'},
                                               {'source': 'app-server', 'target': 'service-discovery'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Queue', 'Distributed', 'Replication', 'Streaming']},
              {'id': 'digital-wallet',
               'title': 'Digital Wallet / UPI',
               'difficulty': 'Hard',
               'description': 'Design a digital wallet and P2P payment system like Google Pay, PayTM, or UPI (Unified '
                              "Payments Interface). India's UPI network processes over 16 billion transactions per "
                              'month across 600+ banks — the core challenges are maintaining strict financial '
                              'consistency with double-entry bookkeeping, achieving exactly-once transaction execution '
                              'through idempotency keys (critical when network timeouts cause retries), implementing '
                              'distributed locks for concurrent balance updates, and meeting regulatory requirements '
                              'for transaction audit trails, KYC compliance, and settlement reconciliation with '
                              'banking partners.',
               'requirements': {'readsPerSec': 50000,
                                'writesPerSec': 30000,
                                'storageGB': 10000,
                                'latencyMs': 200,
                                'users': '100M DAU'},
               'constraints': ['Exactly-once transaction execution using idempotency keys — retries must return the '
                               'same result without re-debiting',
                               'Double-entry bookkeeping — every transfer creates a debit on sender and credit on '
                               'receiver that sum to zero',
                               'Distributed locks for balance updates — prevent race conditions when concurrent '
                               'transactions hit the same wallet',
                               'KYC (Know Your Customer) compliance with tiered wallet limits based on verification '
                               'level',
                               'Transaction history with complete audit trail — every state transition logged for '
                               'regulatory reporting',
                               'Bank settlement reconciliation — daily batch settlement with partner banks, handling '
                               'discrepancies automatically'],
               'hints': [{'title': 'Idempotency first',
                          'content': 'Every transaction API call must include an idempotency key. Before executing, '
                                     'check if this key was already processed. Store the key and result atomically '
                                     'with the transaction in the same database transaction.'},
                         {'title': 'Balance management',
                          'content': 'Use a SQL database with SERIALIZABLE isolation for wallet balances. Use SELECT '
                                     'FOR UPDATE or distributed locks to prevent concurrent transactions from creating '
                                     'negative balances.'},
                         {'title': 'Transaction state machine',
                          'content': 'Model each transaction as: initiated → debited → credited → completed (or failed '
                                     '→ reversed). Use a message queue for reliable state transitions with '
                                     'compensating transactions on failure.'},
                         {'title': 'Advanced: Saga with compensation',
                          'content': "For P2P transfers: Step 1: Debit sender's wallet (with distributed lock). Step "
                                     "2: Credit receiver's wallet. If Step 2 fails, execute compensating action "
                                     '(re-credit sender). Use a message queue to orchestrate saga steps. Store the '
                                     'saga state so it can resume after any failure. This achieves eventual '
                                     'consistency while maintaining financial accuracy.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'auth-service', 'x': 350, 'y': 100},
                                               {'componentId': 'rate-limiter', 'x': 350, 'y': 420},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 100},
                                               {'componentId': 'distributed-lock', 'x': 530, 'y': 420},
                                               {'componentId': 'message-queue', 'x': 720, 'y': 420},
                                               {'componentId': 'sql-db', 'x': 720, 'y': 200},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 100},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'auth-service'},
                                               {'source': 'api-gateway', 'target': 'rate-limiter'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'distributed-lock'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'message-queue', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['ACID', 'Idempotent', 'Ledger', 'Payments']},
              {'id': 'code-editor',
               'title': 'Online Code Editor',
               'difficulty': 'Medium',
               'description': 'Design an online code editor and execution platform like Replit, CodeSandbox, or VS '
                              'Code for the Web. The system supports real-time collaborative editing, sandboxed code '
                              'execution in 50+ programming languages, and a virtual file system per project. Replit '
                              'serves 20+ million developers — the core challenges are implementing real-time '
                              'collaboration with conflict resolution (OT/CRDT) across multiple cursors, securely '
                              'sandboxing user code execution in isolated containers with resource limits (CPU, '
                              'memory, network), and providing Language Server Protocol (LSP) features (autocomplete, '
                              'go-to-definition, error diagnostics) with low latency.',
               'requirements': {'readsPerSec': 30000,
                                'writesPerSec': 20000,
                                'storageGB': 50000,
                                'latencyMs': 100,
                                'users': '10M DAU'},
               'constraints': ['Real-time collaborative editing using OT or CRDT with multi-cursor support and '
                               'conflict resolution',
                               'Sandboxed code execution in isolated containers (gVisor/Firecracker) with CPU, memory, '
                               'and network resource limits',
                               'Language Server Protocol (LSP) integration for autocomplete, diagnostics, '
                               'go-to-definition across 50+ languages',
                               'Virtual file system per project with version history and git integration',
                               'Terminal emulation with PTY (pseudo-terminal) forwarding over WebSocket',
                               'Instant project boot — sub-5-second cold start using pre-warmed container pools and '
                               'filesystem snapshots'],
               'hints': [{'title': 'Collaboration layer',
                          'content': 'Use a WebSocket server for real-time sync. Implement OT (Operational '
                                     'Transformation) or CRDT for conflict-free concurrent edits. Broadcast cursor '
                                     'positions and selections to all collaborators.'},
                         {'title': 'Sandboxed execution',
                          'content': 'Run user code in lightweight VMs (Firecracker) or sandboxed containers (gVisor). '
                                     'Pre-warm a pool of containers per language to minimize cold-start latency. '
                                     'Enforce strict resource limits and network isolation.'},
                         {'title': 'File system design',
                          'content': 'Use object storage for persistent project files with a NoSQL metadata database. '
                                     'Cache active project files in memory on the execution container for fast reads. '
                                     'Sync changes back to object storage on save.'},
                         {'title': 'Advanced: Snapshot and restore',
                          'content': 'Use filesystem snapshots (overlayfs) to create instant project forks. Pre-build '
                                     'base images for each language with common dependencies pre-installed. On project '
                                     "open, layer the user's files on top of the base image using an overlay "
                                     'filesystem — this gives sub-second project boot times instead of installing '
                                     'dependencies from scratch.'}],
               'referenceSolution': {'nodes': [{'componentId': 'dns', 'x': 50, 'y': 250},
                                               {'componentId': 'cdn', 'x': 200, 'y': 80},
                                               {'componentId': 'load-balancer', 'x': 200, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 350, 'y': 250},
                                               {'componentId': 'websocket-server', 'x': 350, 'y': 420},
                                               {'componentId': 'app-server', 'x': 530, 'y': 250},
                                               {'componentId': 'cache', 'x': 530, 'y': 80},
                                               {'componentId': 'message-queue', 'x': 530, 'y': 420},
                                               {'componentId': 'nosql-db', 'x': 720, 'y': 250},
                                               {'componentId': 'object-storage', 'x': 720, 'y': 80},
                                               {'componentId': 'monitoring', 'x': 880, 'y': 250}],
                                     'edges': [{'source': 'dns', 'target': 'cdn'},
                                               {'source': 'dns', 'target': 'load-balancer'},
                                               {'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'load-balancer', 'target': 'websocket-server'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'websocket-server', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'nosql-db'},
                                               {'source': 'app-server', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Collaboration', 'Sandbox', 'WebSocket', 'LSP']},
              {'id': 'cicd-pipeline',
               'title': 'CI/CD Pipeline',
               'difficulty': 'Medium',
               'description': 'Design a continuous integration and continuous deployment platform like GitHub Actions, '
                              'GitLab CI, or Jenkins. The system orchestrates build pipelines triggered by code '
                              'commits, runs tests in parallel across isolated environments, stores build artifacts, '
                              'and deploys to production using strategies like blue-green or canary. GitHub Actions '
                              'processes millions of workflow runs daily — the core challenges are efficiently '
                              'scheduling and executing build jobs across a fleet of heterogeneous runners, managing '
                              'artifact storage and caching for fast builds, and implementing reliable deployment '
                              'orchestration with automatic rollback on failure detection.',
               'requirements': {'readsPerSec': 20000,
                                'writesPerSec': 10000,
                                'storageGB': 200000,
                                'latencyMs': 500,
                                'users': '5M DAU'},
               'constraints': ['Pipeline orchestration: define workflows as DAGs (directed acyclic graphs) of jobs '
                               'with dependency edges',
                               'Parallel test execution across isolated runners — scale runner fleet dynamically based '
                               'on queue depth',
                               'Build caching: cache dependencies (node_modules, Maven repo) and Docker layers across '
                               'runs for 3-10x speedup',
                               'Artifact storage with retention policies — store build outputs, test reports, and '
                               'coverage data',
                               'Deployment strategies: blue-green (instant switch), canary (gradual rollout with '
                               'health checks), rolling update',
                               'Automatic rollback on deployment failure — detect health check failures and revert to '
                               'the previous known-good version'],
               'hints': [{'title': 'Job scheduling',
                          'content': 'Use a message queue with priority lanes for different job types. A scheduler '
                                     'service parses the workflow DAG, resolves dependencies, and enqueues jobs as '
                                     'their dependencies complete.'},
                         {'title': 'Runner management',
                          'content': 'Runners pull jobs from the queue, execute in isolated containers, and report '
                                     'results. Use auto-scaling (scale runners based on queue depth) with a minimum '
                                     'warm pool to avoid cold-start delays.'},
                         {'title': 'Build caching',
                          'content': 'Cache dependencies in object storage keyed by lock-file hash. On each build, '
                                     'check if a cache exists for the current dependency set. This can reduce build '
                                     'times by 3-10x for dependency-heavy projects.'},
                         {'title': 'Advanced: Canary deployments',
                          'content': 'Deploy the new version to 5% of traffic (canary). Monitor error rates, latency '
                                     'p99, and custom health metrics for 10 minutes. If metrics stay within '
                                     'thresholds, gradually increase to 25% → 50% → 100%. If any metric degrades, '
                                     'automatically roll back to the previous version and notify the team. Store '
                                     'deployment state in a SQL database for auditability.'}],
               'referenceSolution': {'nodes': [{'componentId': 'load-balancer', 'x': 100, 'y': 250},
                                               {'componentId': 'api-gateway', 'x': 250, 'y': 250},
                                               {'componentId': 'app-server', 'x': 420, 'y': 250},
                                               {'componentId': 'cache', 'x': 420, 'y': 80},
                                               {'componentId': 'message-queue', 'x': 420, 'y': 420},
                                               {'componentId': 'sql-db', 'x': 620, 'y': 250},
                                               {'componentId': 'object-storage', 'x': 620, 'y': 80},
                                               {'componentId': 'task-scheduler', 'x': 620, 'y': 420},
                                               {'componentId': 'monitoring', 'x': 820, 'y': 250}],
                                     'edges': [{'source': 'load-balancer', 'target': 'api-gateway'},
                                               {'source': 'api-gateway', 'target': 'app-server'},
                                               {'source': 'app-server', 'target': 'cache'},
                                               {'source': 'app-server', 'target': 'message-queue'},
                                               {'source': 'app-server', 'target': 'sql-db'},
                                               {'source': 'message-queue', 'target': 'task-scheduler'},
                                               {'source': 'task-scheduler', 'target': 'object-storage'},
                                               {'source': 'app-server', 'target': 'monitoring'}]},
               'tags': ['Pipeline', 'Deployment', 'Orchestration', 'Caching']}]}

COMPONENT_ALIASES = {
    'auth-service': 'auth', 'message-queue': 'queue', 'websocket-server': 'websocket',
    'task-scheduler': 'scheduler', 'stream-processor': 'worker', 'timeseries-db': 'time-series-db',
    'data-warehouse': 'warehouse', 'file-store': 'file-storage', 'coordination-service': 'coordinator',
    'pub-sub': 'pubsub',
}
PROBLEM_ALIASES = {
    'twitter-feed': 'twitter', 'chat-system': 'chat', 'ride-sharing': 'uber',
    'video-streaming': 'youtube', 'notification-system': 'notifications',
    'typeahead-autocomplete': 'typeahead', 'payment-system': 'payments',
    'collaborative-editor': 'google-docs', 'file-storage': 'dropbox',
    'music-streaming': 'spotify', 'team-messaging': 'slack', 'metrics-monitoring': 'monitoring',
    'search-engine': 'google-search', 'location-service': 'yelp', 'message-queue-design': 'kafka',
    'cicd-pipeline': 'cicd',
}

def source_reference(reference):
    nodes = []
    for i, n in enumerate(reference['nodes']):
        nodes.append({'id': f'n{i+1}', 'type': COMPONENT_ALIASES.get(n['componentId'], n['componentId']),
                      'label': '', 'x': n['x'], 'y': n['y'], 'replicas': 1, 'config': {}})
    # The shipped conversion selects the first node matching a component ID.
    first = {}
    for i, n in enumerate(reference['nodes']):
        first.setdefault(n['componentId'], f'n{i+1}')
    edges = [{'id': f'e{i+1}', 'source': first[e['source']], 'target': first[e['target']], 'protocol': 'http'}
             for i, e in enumerate(reference['edges']) if e['source'] in first and e['target'] in first]
    return {'nodes': nodes, 'edges': edges}

def build():
    components = []
    for ident, label, fa, category, qps, latency, description, description_fa in SPECS:
        t, tf = TRADEOFFS[category]
        components.append(dict(id=ident, label=label, labelFa=fa, category=category, maxQPS=qps, latencyMs=latency, color=COLORS[category], description=description, descriptionFa=description_fa, tradeoff=t, tradeoffFa=tf))
    source_components = {COMPONENT_ALIASES.get(c['id'], c['id']): c for c in ORIGINAL_DATA['components']}
    for component in components:
        source = source_components.get(component['id'])
        if source:
            component.update(sourceId=source['id'], sourceCategory=source['category'],
                             label=source['label'], maxQPS=source['maxQPS'], latencyMs=source['latencyMs'],
                             icon=source['icon'], scalable=source['scalable'], stateful=source['stateful'],
                             description=source['description'])
    problems = []
    for ex in json.loads((ROOT / 'assets/exercise-audit.json').read_text())['exercises']:
        starter_types, reference_types, fanout = TEMPLATES[ex['chapter']]
        ident = f"ch{ex['chapter']}-ex{ex['number']}"
        reference, note_en, note_fa = exercise_references.build(ident)
        problems.append({
            'id': f"ch{ex['chapter']}-ex{ex['number']}",
            'titleFa': ex['title_fa'], 'titleEn': ex['title_en'],
            'promptFa': ex['prompt'], 'promptEn': ex['prompt_en'],
            'signalsFa': ex['signals'], 'signalsEn': ex['signals_en'],
            'followupFa': ex.get('followup', ''), 'followupEn': ex.get('followup_en', ''),
            **{k: ex[k] for k in ('folder', 'chapter', 'number', 'level', 'priority', 'minutes')},
            'solutionHref': f"../{ex['folder']}/solutions.html#sol-{ex['number']}",
            'lessonHref': f"../{ex['folder']}/index.html",
            'starter': graph(starter_types), 'reference': reference,
            'referenceNoteFa': note_fa + ' این طرح قابل ویرایش است؛ استدلال کامل در لینک حل تمرین است.',
            'referenceNoteEn': note_en + ' This sketch is editable; the full reasoning is in the linked solution.',
        })
    authored = {entry[0]: entry for entry in CLASSICS}
    for source in ORIGINAL_DATA['problems']:
        ident = PROBLEM_ALIASES.get(source['id'], source['id'])
        fa = authored[ident]
        problems.append({
            'id': f'sys-{ident}', 'sourceId': source['id'],
            'titleFa': fa[2], 'titleEn': source['title'],
            'promptEn': source['description'],
            'promptFa': f'سرویس «{fa[2]}» را طراحی کن. {fa[5]} را صریح بررسی کن. بار و محدودیت‌های مرجع در پنل نیازمندی‌ها آمده‌اند. مسیر داده و پیام را رسم کن، طرح را اجرا و موازنه‌ها را ثبت کن.',
            'description': source['description'], 'difficulty': source['difficulty'],
            'requirements': source['requirements'], 'constraints': source['constraints'], 'hints': source['hints'],
            'signalsEn': [f'Explains {fa[4]}', 'States measurable workload and failure assumptions', 'Tests a change and records its cost and correctness limits'],
            'signalsFa': [f'{fa[5]} را توضیح می‌دهد', 'فرض بار و خرابی قابل اندازه‌گیری می‌نویسد', 'یک تغییر را آزمایش و هزینه و محدودیت صحتش را ثبت می‌کند'],
            'chapter': 0, 'number': 0, 'folder': None, 'level': source['difficulty'].lower(), 'priority': 'practice', 'minutes': 42,
            'tags': source['tags'], 'solutionHref': None, 'lessonHref': None,
            'starter': {'nodes': [], 'edges': []}, 'reference': source_reference(source['referenceSolution']),
            'referenceNoteFa': 'توپولوژی مرجع از نسخهٔ مشاهده‌شدهٔ SysDes است؛ رسم گراف تضمین صحت واقعی نیست.',
            'referenceNoteEn': 'Reference topology matches the captured SysDes design; the diagram is not a correctness guarantee.',
        })
    result = {'components': components, 'problems': problems, 'tradeoffs': [dict(id=source['id'], titleEn=source['title'], titleFa=tf, en=e, fa=f, textEn=e, textFa=f, source=source) for source, (i, t, tf, e, f) in zip(ORIGINAL_DATA['tradeoffs'], COMPARISONS)], 'componentAliases': COMPONENT_ALIASES}
    output = '/* Generated by assets/build_studio_data.py; all capacity values are illustrative. */\n(function(root){\n  const data = ' + json.dumps(result, ensure_ascii=False, separators=(',', ':')) + ';\n  root.DDIAStudioData = data;\n  if (typeof module === "object" && module.exports) module.exports = data;\n})(typeof globalThis !== "undefined" ? globalThis : window);\n'
    (ROOT / 'assets/studio-data.js').write_text(output)
    print(f"Studio catalog: {len(components)} components, {len(problems)} exercises")


if __name__ == '__main__':
    build()
