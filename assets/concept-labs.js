/* Local, deterministic teaching models. No network, backend or measured timings. */
(function (root) {
  'use strict';
  const B = (en, fa) => ({en, fa});
  const A = (id, label, when, run) => ({id, label, when, run});
  const at = stage => s => s.stage === stage;
  const say = (s, en, fa, from, to) => { s.message = B(en, fa); s.move = [from || 0, to === undefined ? 1 : to]; };
  const models = {};
  function add(id, title, prompt, assumption, labels, initial, actions, view) {
    models[id] = {id, title, prompt, assumption, labels, initial: () => ({stage:0, ...initial(), message:prompt, move:null}), actions, view};
  }
  add('outbox', B('The order exists. Where is its event?', 'سفارش ثبت شد؛ رویدادش کجاست؟'),
    B('Choose how to publish an order, then crash the process between commit and delivery.', 'روش انتشار سفارش را انتخاب کن؛ بعد بین ثبت و تحویل، پردازش را متوقف کن.'),
    B('One database transaction can include the order and its outbox row. The relay retries and the view deduplicates by order ID.', 'یک تراکنش می‌تواند سفارش و ردیف outbox را با هم ثبت کند. relay بازتلاش می‌کند و نما با شناسهٔ سفارش تکرار را حذف می‌کند.'),
    [B('Order store', 'مرجع سفارش'),B('Publisher / outbox', 'ناشر / outbox'),B('Search view', 'نمای جست‌وجو')],
    () => ({policy:null, order:0, pending:false, alive:true, search:0}), [
      A('direct',B('Separate writes', 'دو نوشتن جدا'),at(0),s=>{s.policy='direct';s.stage=1;say(s,'Order and event use separate writes. Commit the order next.','سفارش و رویداد جدا نوشته می‌شوند. حالا سفارش را ثبت کن.');}),
      A('outbox',B('Transactional outbox', 'outbox تراکنشی'),at(0),s=>{s.policy='outbox';s.stage=1;say(s,'The order and pending event will commit atomically.','سفارش و رویداد در انتظار، اتمیک ثبت می‌شوند.');}),
      A('commit',B('Commit order', 'ثبت سفارش'),at(1),s=>{s.order=1;s.pending=s.policy==='outbox';s.stage=2;say(s,'Order #1 is durable. Delivery has not happened.','سفارش ۱ پایدار است؛ هنوز تحویل رخ نداده.',0,1);}),
      A('crash',B('Crash publisher', 'توقف ناشر'),at(2),s=>{s.alive=false;s.stage=3;say(s,'The process died in the commit/publish gap. Inspect what survived.','پردازش در فاصلهٔ ثبت و انتشار متوقف شد. ببین چه چیزی باقی مانده است.',1,1);}),
      A('recover',B('Restart and retry relay', 'راه‌اندازی و بازتلاش relay'),at(3),s=>{s.alive=true;if(s.pending){s.search=s.order;s.pending=false;}s.stage=4;say(s,s.search?'The durable outbox supplied the missing event; search now contains order #1.':'No event was stored. Restarting alone cannot discover this missing publication.',s.search?'outbox پایدار رویداد گم‌شده را رساند؛ جست‌وجو حالا سفارش ۱ را دارد.':'رویدادی ذخیره نشده؛ راه‌اندازی مجدد به‌تنهایی این انتشار گم‌شده را پیدا نمی‌کند.',1,2);})
    ],s=>[`order=${s.order}`,`mode=${s.policy||'?'}\npending=${s.pending}\nprocess=${s.alive?'up':'down'}`,`order=${s.search}`]);

  add('queue',B('A burst meets a fixed service rate', 'برخورد موج درخواست با ظرفیت محدود'),
    B('Six requests arrive together. Choose the worker count, then advance service ticks.', 'شش درخواست با هم می‌رسند. تعداد workerها را انتخاب کن و نوبت‌های پردازش را جلو ببر.'),
    B('Each worker completes one request per illustrative tick. FIFO, identical work, no networking or coordination cost.', 'در این مدل هر worker در هر نوبت یک درخواست انجام می‌دهد؛ FIFO و کار یکسان، بدون هزینهٔ شبکه یا هماهنگی.'),
    [B('Arrivals', 'ورودی'),B('FIFO queue', 'صف FIFO'),B('Workers / completed', 'workerها / تکمیل‌شده')],
    ()=>({workers:0, queue:0, done:0, tick:0}),[
      A('one',B('1 worker', '۱ worker'),at(0),s=>{s.workers=1;s.stage=1;say(s,'One completion per tick. Send the burst.','هر نوبت یک تکمیل؛ موج را بفرست.');}),
      A('three',B('3 workers', '۳ worker'),at(0),s=>{s.workers=3;s.stage=1;say(s,'Three completions per tick, with three times the worker allocation.','هر نوبت سه تکمیل با سه برابر تخصیص worker.');}),
      A('burst',B('Send 6 requests', 'ارسال ۶ درخواست'),at(1),s=>{s.queue=6;s.stage=2;say(s,'All six arrived before any service tick; the queue is visible.','هر شش درخواست قبل از پردازش رسیدند؛ صف را می‌بینی.',0,1);}),
      A('tick',B('Serve one tick', 'یک نوبت پردازش'),s=>s.stage===2&&s.queue>0,s=>{const done=Math.min(s.queue,s.workers);s.queue-=done;s.done+=done;s.tick++;if(!s.queue)s.stage=3;say(s,`${done} completed; ${s.queue} waiting. Tail completion needs ${Math.ceil(6/s.workers)} ticks in this model.`,`${done} تکمیل و ${s.queue} در انتظار؛ آخرین درخواست در این مدل به ${Math.ceil(6/s.workers)} نوبت نیاز دارد.`,1,2);})
    ],s=>['burst=6',`waiting=${s.queue}\ntick=${s.tick}`,`workers=${s.workers}\ncompleted=${s.done}`]);

  add('models',B('Rename once, or update every copy?', 'یک تغییر نام یا اصلاح همهٔ کپی‌ها؟'),
    B('An author name appears on two posts. Choose normalized references or embedded copies, then rename.', 'نام یک نویسنده در دو پست دیده می‌شود. ارجاع رابطه‌ای یا کپی سندی را انتخاب کن و نام را تغییر بده.'),
    B('The join reads the current author row. Embedded documents are separate writes; no automatic fan-out or transaction is assumed.', 'join ردیف فعلی نویسنده را می‌خواند؛ سندهای کپی‌شده جدا نوشته می‌شوند و fan-out یا تراکنش خودکار فرض نشده است.'),
    [B('Author row', 'ردیف نویسنده'),B('Post A', 'پست A'),B('Post B', 'پست B')],
    ()=>({mode:null,author:'Mina',a:'Mina',b:'Mina'}),[
      A('join',B('Reference author ID', 'ارجاع با شناسهٔ نویسنده'),at(0),s=>{s.mode='join';s.stage=1;say(s,'Both posts reference author #7.','هر دو پست به نویسندهٔ ۷ ارجاع دارند.');}),
      A('embed',B('Embed author name', 'کپی نام داخل سند'),at(0),s=>{s.mode='embed';s.stage=1;say(s,'Each post stores its own author-name copy.','هر پست کپی جداگانهٔ نام نویسنده را نگه می‌دارد.');}),
      A('rename',B('Rename to Sara', 'تغییر نام به سارا'),at(1),s=>{s.author='Sara';if(s.mode==='join'){s.a=s.b='Sara';}else{s.a='Sara';}s.stage=2;say(s,s.mode==='join'?'A join resolves both references to the updated row.':'The author and post A changed; post B still has the old copy.',s.mode==='join'?'join هر دو ارجاع را به ردیف به‌روز متصل می‌کند.':'نویسنده و پست A تغییر کردند؛ پست B هنوز کپی قدیمی را دارد.',0,1);}),
      A('read',B('Read post B', 'خواندن پست B'),at(2),s=>{s.stage=3;say(s,`Post B shows ${s.b}. ${s.mode==='join'?'One authoritative name, with a join at read time.':'Duplication requires explicit propagation; locality trades off update work.'}`,`پست B نام ${s.b} را نشان می‌دهد. ${s.mode==='join'?'یک نام مرجع با join هنگام خواندن.':'تکثیر داده به انتشار صریح تغییر نیاز دارد؛ دسترسی محلی هزینهٔ به‌روزرسانی دارد.'}`,0,2);}),
      A('repair',B('Propagate to post B', 'انتشار تغییر به پست B'),s=>s.stage===3&&s.mode==='embed',s=>{s.b=s.author;s.stage=4;say(s,'The second copy is repaired by an additional write.','کپی دوم با یک نوشتن اضافه اصلاح شد.',0,2);})
    ],s=>[`id=7\nname=${s.author}`,`${s.mode==='join'?'author_id=7 →':'name='}${s.a}`,`${s.mode==='join'?'author_id=7 →':'name='}${s.b}`]);

  add('wal',B('What survives a crash?', 'بعد از خرابی چه چیزی می‌ماند؟'),
    B('Write x=7 into memory, crash before flushing the table, and recover.', 'مقدار x=7 را در حافظه بنویس، قبل از flush جدول خرابی ایجاد کن و بازیابی کن.'),
    B('Acknowledged WAL records are fsynced to durable storage. A crash loses RAM; it does not corrupt the durable log or table.', 'رکورد WAL پیش از تأیید با fsync پایدار می‌شود؛ خرابی RAM را پاک می‌کند ولی لاگ و جدول پایدار را خراب نمی‌کند.'),
    [B('Memtable (RAM)', 'memtable در RAM'),B('Durable WAL', 'WAL پایدار'),B('SSTable (disk)', 'SSTable روی دیسک')],
    ()=>({walOn:false,mem:null,wal:null,disk:null,down:false}),[
      A('wal',B('Enable durable WAL', 'فعال‌کردن WAL پایدار'),at(0),s=>{s.walOn=true;s.stage=1;say(s,'A log record must become durable before acknowledgement.','رکورد لاگ پیش از تأیید باید پایدار شود.');}),
      A('ram',B('Acknowledge RAM only', 'تأیید فقط از RAM'),at(0),s=>{s.stage=1;say(s,'RAM-only acknowledgement can lose this write after a crash.','تأیید از RAM می‌تواند این نوشتن را پس از خرابی از دست بدهد.');}),
      A('write',B('Write x=7', 'نوشتن x=7'),at(1),s=>{s.mem=7;if(s.walOn)s.wal=7;s.stage=2;say(s,'Write acknowledged; the SSTable has not been flushed.','نوشتن تأیید شد؛ هنوز SSTable نوشته نشده است.',0,1);}),
      A('crash',B('Crash before flush', 'خرابی قبل از flush'),at(2),s=>{s.mem=null;s.down=true;s.stage=3;say(s,'Volatile memory vanished. Inspect the durable bytes.','حافظهٔ موقت از بین رفت؛ بایت‌های پایدار را بررسی کن.',0,0);}),
      A('recover',B('Replay WAL', 'بازپخش WAL'),at(3),s=>{s.down=false;s.mem=s.wal;s.stage=4;say(s,s.mem===7?'Replay restored x=7 from the durable WAL.':'There is no durable record to replay: the acknowledged write is lost.',s.mem===7?'بازپخش WAL پایدار مقدار x=7 را برگرداند.':'رکورد پایداری برای بازپخش نیست؛ نوشتن تأییدشده گم شد.',1,0);}),
      A('flush',B('Flush recovered table', 'flush جدول بازیابی‌شده'),at(4),s=>{s.disk=s.mem;s.stage=5;say(s,'The current memtable was flushed. Recovery cannot invent missing data.','memtable فعلی روی دیسک نوشته شد؛ بازیابی نمی‌تواند دادهٔ گم‌شده بسازد.',0,2);})
    ],s=>[`x=${s.mem??'∅'}\nprocess=${s.down?'down':'up'}`,`x=${s.wal??'∅'}\nenabled=${s.walOn}`,`x=${s.disk??'∅'}`]);

  add('schema',B('An old service edits a new record', 'سرویس قدیمی یک رکورد جدید را ویرایش می‌کند'),
    B('A v2 record contains a locale field unknown to v1. Pass it through an old reader and back to v2.', 'رکورد v2 فیلد locale دارد که v1 نمی‌شناسد. آن را از خوانندهٔ قدیمی عبور بده و به v2 برگردان.'),
    B('Tagged fields have stable identifiers. This is a read-modify-write round trip; unknown-field retention depends on the codec and application.', 'شناسهٔ فیلدها ثابت است. این چرخه خواندن، ویرایش و نوشتن است؛ حفظ فیلد ناشناخته به codec و برنامه بستگی دارد.'),
    [B('v2 writer', 'نویسنده v2'),B('v1 intermediary', 'واسط v1'),B('v2 reader', 'خواننده v2')],
    ()=>({keep:null,wire:{name:'Mina',locale:'fa'},old:null,result:null}),[
      A('preserve',B('Preserve unknown fields', 'حفظ فیلد ناشناخته'),at(0),s=>{s.keep=true;s.stage=1;say(s,'The old intermediary retains unknown tagged fields.','واسط قدیمی فیلدهای تگ‌دار ناشناخته را نگه می‌دارد.');}),
      A('drop',B('Rebuild known fields only', 'بازسازی فقط فیلدهای شناخته‌شده'),at(0),s=>{s.keep=false;s.stage=1;say(s,'Reconstructing only known fields may discard new information.','بازسازی فقط فیلدهای شناخته‌شده می‌تواند اطلاعات جدید را حذف کند.');}),
      A('decode',B('Decode with v1', 'decode با v1'),at(1),s=>{s.old=s.keep?{...s.wire}:{name:s.wire.name};s.stage=2;say(s,'v1 understands name, but not locale.','نسخهٔ v1 نام را می‌فهمد ولی locale را نمی‌شناسد.',0,1);}),
      A('edit',B('Edit name and re-encode', 'ویرایش نام و encode مجدد'),at(2),s=>{s.old.name='Sara';s.stage=3;say(s,'The old service changed name without understanding locale.','سرویس قدیمی نام را بدون درک locale تغییر داد.',1,1);}),
      A('read',B('Decode with v2', 'decode با v2'),at(3),s=>{s.result={...s.old};s.stage=4;say(s,s.result.locale?'The new reader recovered locale=fa; the unknown field survived.':'locale disappeared in the round trip. Parsing successfully did not preserve information.',s.result.locale?'خوانندهٔ جدید locale=fa را بازیابی کرد؛ فیلد ناشناخته حفظ شد.':'locale در چرخه حذف شد؛ موفقیت parse به معنی حفظ اطلاعات نیست.',1,2);})
    ],s=>[JSON.stringify(s.wire),s.old?JSON.stringify(s.old):'∅',s.result?JSON.stringify(s.result):'∅']);

  add('replication',B('Read your own profile update', 'ویرایش پروفایلت را بخوان'),
    B('Write a new profile value, hold replication, and choose where the read goes.', 'پروفایل را تغییر بده، تکثیر را عقب بینداز و مقصد خواندن را انتخاب کن.'),
    B('Single leader, one asynchronous follower, no failover. A leader read sees its committed write; a delayed follower can return the previous value.', 'یک رهبر و یک follower ناهمزمان، بدون failover؛ خواندن رهبر نوشتن ثبت‌شده را می‌بیند و follower عقب‌مانده ممکن است مقدار قبلی را برگرداند.'),
    [B('Client', 'کاربر'),B('Leader', 'رهبر'),B('Follower', 'پیرو')],
    ()=>({leader:0,follower:0,pending:false,read:null}),[
      A('write',B('Write profile v1', 'نوشتن پروفایل v1'),at(0),s=>{s.leader=1;s.pending=true;s.stage=1;say(s,'Leader committed v1. The replication message is still in flight.','رهبر v1 را ثبت کرد؛ پیام تکثیر هنوز در راه است.',0,1);}),
      A('hold',B('Hold replication message', 'تأخیر پیام تکثیر'),at(1),s=>{s.stage=2;say(s,'The write succeeded, while the follower remains at v0. Choose a read route.','نوشتن موفق است ولی پیرو هنوز v0 دارد؛ مسیر خواندن را انتخاب کن.',1,2);}),
      A('follower',B('Read follower', 'خواندن پیرو'),at(2),s=>{s.read=s.follower;s.stage=3;say(s,`Follower returned v${s.read}; the client observed stale data.`,`پیرو v${s.read} برگرداند؛ کاربر دادهٔ قدیمی دید.`,2,0);}),
      A('leader',B('Read leader', 'خواندن رهبر'),at(2),s=>{s.read=s.leader;s.stage=3;say(s,'Leader returned v1. Routing this session to the leader supplies read-your-writes in this model.','رهبر v1 برگرداند؛ مسیریابی این نشست به رهبر در این مدل خواندنِ نوشتنِ خود را تضمین می‌کند.',1,0);}),
      A('deliver',B('Deliver delayed message', 'تحویل پیام عقب‌افتاده'),at(3),s=>{s.follower=s.leader;s.pending=false;s.stage=4;say(s,'The follower caught up. A later read can be fresh even though the earlier read was stale.','پیرو همگام شد؛ خواندن بعدی می‌تواند تازه باشد حتی اگر قبلی قدیمی بود.',1,2);})
    ],s=>[`last read=${s.read===null?'∅':'v'+s.read}`,`profile=v${s.leader}`,`profile=v${s.follower}\nmessage=${s.pending?'pending':'none'}`]);

  add('failover',B('The leader dies after acknowledging a write', 'رهبر بعد از تأیید نوشتن می‌میرد'),
    B('Choose async or synchronous replication, acknowledge a write, kill the leader and promote the follower.', 'تکثیر ناهمزمان یا همزمان را انتخاب کن، نوشتن را تأیید کن، رهبر را بکش و follower را ارتقا بده.'),
    B('One leader and one follower, manual promotion, no third node. Synchronous means the follower stores the write before the client is acknowledged.', 'یک رهبر و یک follower، ارتقای دستی و بدون گره سوم؛ همزمان یعنی follower پیش از تأیید به کاربر نوشتن را ذخیره کرده است.'),
    [B('Old leader', 'رهبر قبلی'),B('Follower', 'پیرو'),B('Client', 'کاربر')],
    ()=>({sync:null,leader:0,follower:0,acked:false,down:false,promoted:false,lost:false}),[
      A('async',B('Asynchronous replication', 'تکثیر ناهمزمان'),at(0),s=>{s.sync=false;s.stage=1;say(s,'The leader acknowledges before the follower has the write.','رهبر پیش از رسیدن نوشتن به follower تأیید می‌دهد.');}),
      A('sync',B('Synchronous replication', 'تکثیر همزمان'),at(0),s=>{s.sync=true;s.stage=1;say(s,'The leader waits for the follower before acknowledging.','رهبر پیش از تأیید منتظر follower می‌ماند.');}),
      A('write',B('Write v1 and acknowledge', 'نوشتن v1 و تأیید'),at(1),s=>{s.leader=1;s.follower=s.sync?1:0;s.acked=true;s.stage=2;say(s,s.sync?'The client was acknowledged after both copies stored v1.':'The client was acknowledged. Only the leader has v1; the message is still in flight.',s.sync?'کاربر پس از ذخیرهٔ v1 روی هر دو کپی تأیید گرفت.':'کاربر تأیید گرفت ولی فقط رهبر v1 را دارد؛ پیام هنوز در راه است.',0,1);}),
      A('crash',B('Kill the leader', 'از کار انداختن رهبر'),at(2),s=>{s.down=true;s.stage=3;say(s,'The leader is gone. Its unreplicated bytes are unreachable.','رهبر از دسترس خارج شد؛ بایت‌های تکثیرنشده‌اش در دسترس نیستند.',0,0);}),
      A('promote',B('Promote the follower', 'ارتقای follower'),at(3),s=>{s.promoted=true;s.stage=4;say(s,`The new leader serves v${s.follower}. ${s.follower?'The acknowledged write is present.':'The acknowledged write is missing from the new leader.'}`,`رهبر جدید v${s.follower} را سرو می‌کند. ${s.follower?'نوشتن تأییدشده موجود است.':'نوشتن تأییدشده روی رهبر جدید نیست.'}`,1,2);}),
      A('rejoin',B('Old leader rejoins', 'بازگشت رهبر قبلی'),at(4),s=>{s.down=false;if(s.leader>s.follower){s.lost=true;s.leader=s.follower;}s.stage=5;say(s,s.lost?'The old leader must discard v1: an acknowledged write was lost in failover.':'The old leader rejoins as a follower; nothing was lost.',s.lost?'رهبر قبلی باید v1 را دور بریزد؛ نوشتن تأییدشده در failover گم شد.':'رهبر قبلی به‌عنوان follower برمی‌گردد؛ چیزی گم نشد.',1,0);})
    ],s=>[`v${s.leader}\n${s.down?'down':'up'}${s.lost?'\ndiscarded v1':''}`,`v${s.follower}\nrole=${s.promoted?'leader':'follower'}`,`ack=${s.acked}\nmode=${s.sync===null?'?':s.sync?'sync':'async'}`]);

  add('monotonic',B('Two reads, time goes backwards', 'دو خواندن و بازگشت زمان به عقب'),
    B('Choose how reads are routed, then read the same profile twice while one follower lags.', 'مسیریابی خواندن را انتخاب کن و وقتی یک follower عقب است، یک پروفایل را دو بار بخوان.'),
    B('Follower A has v1 and follower B is still at v0. The first read lands on A. Random routing may send the second read to B; sticky routing pins the session to A.', 'follower A مقدار v1 را دارد و B هنوز v0 دارد. خواندن اول به A می‌رسد؛ مسیریابی تصادفی ممکن است خواندن دوم را به B بفرستد و sticky نشست را به A می‌بندد.'),
    [B('Follower A', 'پیرو A'),B('Follower B', 'پیرو B'),B('Client observations', 'مشاهدات کاربر')],
    ()=>({mode:null,a:1,b:0,seen:[]}),[
      A('random',B('Random replica per read', 'هر خواندن به یک replica تصادفی'),at(0),s=>{s.mode='random';s.stage=1;say(s,'Each read may reach a different follower.','هر خواندن ممکن است به follower دیگری برسد.');}),
      A('sticky',B('Pin session to one replica', 'نشست به یک replica بسته شود'),at(0),s=>{s.mode='sticky';s.stage=1;say(s,'All reads in this session go to the same follower.','همهٔ خواندن‌های این نشست به یک follower می‌روند.');}),
      A('first',B('First read', 'خواندن اول'),at(1),s=>{s.seen=[s.a];s.stage=2;say(s,'Read 1 hit follower A and returned v1.','خواندن ۱ به A رسید و v1 برگرداند.',2,0);}),
      A('second',B('Second read', 'خواندن دوم'),at(2),s=>{const v=s.mode==='sticky'?s.a:s.b;s.seen.push(v);s.stage=3;say(s,v<s.seen[0]?'The client saw v1, then v0: its own timeline moved backwards.':'The client saw v1 twice; it never went back in time.',v<s.seen[0]?'کاربر اول v1 و بعد v0 دید؛ زمان از دید او به عقب رفت.':'کاربر دو بار v1 دید؛ زمان به عقب نرفت.',2,v<s.seen[0]?1:0);}),
      A('catchup',B('Follower B catches up', 'همگام‌شدن B'),at(3),s=>{s.b=1;s.stage=4;say(s,'B is current now, but the earlier observation order is unchanged.','B حالا به‌روز است ولی ترتیب مشاهده‌های قبلی تغییر نمی‌کند.',1,1);})
    ],s=>[`v${s.a}`,`v${s.b}`,`reads=[${s.seen.map(v=>'v'+v)}]\nrouting=${s.mode||'?'}`]);

  add('leaderless',B('Do the write and read quorums overlap?', 'آیا quorum نوشتن و خواندن هم‌پوشانی دارند؟'),
    B('Three replicas, one write. Choose how many acknowledgements the write and the read wait for.', 'سه replica و یک نوشتن؛ تعداد تأییدهایی را که نوشتن و خواندن صبر می‌کنند انتخاب کن.'),
    B('n=3. The write reaches replicas 1..w. The read contacts the last r replicas, the worst case. If w+r>n, at least one contacted replica has the write.', 'n=۳؛ نوشتن به replicaهای ۱ تا w می‌رسد و خواندن بدترین حالت، یعنی r replica آخر، را می‌پرسد. اگر w+r>n باشد دست‌کم یک replica پرسیده‌شده نوشتن را دارد.'),
    [B('Replica 1', 'replica ۱'),B('Replica 2', 'replica ۲'),B('Replica 3', 'replica ۳')],
    ()=>({w:0,r:0,vals:[0,0,0],result:null}),[
      A('w1',B('Write waits for 1 ack (w=1)', 'نوشتن با ۱ تأیید (w=1)'),at(0),s=>{s.w=1;s.stage=1;say(s,'The write succeeds once one replica stores it.','نوشتن با ذخیره روی یک replica موفق می‌شود.');}),
      A('w2',B('Write waits for 2 acks (w=2)', 'نوشتن با ۲ تأیید (w=2)'),at(0),s=>{s.w=2;s.stage=1;say(s,'The write succeeds once two replicas store it.','نوشتن با ذخیره روی دو replica موفق می‌شود.');}),
      A('r1',B('Read asks 1 replica (r=1)', 'خواندن از ۱ replica (r=1)'),at(1),s=>{s.r=1;s.stage=2;say(s,'The read returns the first answer it gets.','خواندن اولین پاسخ را برمی‌گرداند.');}),
      A('r2',B('Read asks 2 replicas (r=2)', 'خواندن از ۲ replica (r=2)'),at(1),s=>{s.r=2;s.stage=2;say(s,'The read compares two answers and keeps the newest.','خواندن دو پاسخ را مقایسه می‌کند و جدیدترین را نگه می‌دارد.');}),
      A('write',B('Write v1', 'نوشتن v1'),at(2),s=>{for(let i=0;i<s.w;i++)s.vals[i]=1;s.stage=3;say(s,`v1 is stored on ${s.w} replica(s). The rest have not seen it yet.`,`v1 روی ${s.w} replica ذخیره شد؛ بقیه هنوز آن را ندیده‌اند.`,0,1);}),
      A('read',B('Read (worst-case replicas)', 'خواندن (بدترین انتخاب replica)'),at(3),s=>{s.result=Math.max(...s.vals.slice(3-s.r));s.stage=4;say(s,s.result?`w+r=${s.w+s.r}>3: the read overlapped a replica holding v1.`:`w+r=${s.w+s.r}≤3: the read missed every replica holding v1 and returned stale v0.`,s.result?`w+r=${s.w+s.r}>۳؛ خواندن با replicaی که v1 دارد هم‌پوشانی داشت.`:`w+r=${s.w+s.r}≤۳؛ خواندن به هیچ replicaی که v1 دارد نرسید و v0 قدیمی را برگرداند.`,2,0);})
    ],s=>s.vals.map((v,i)=>`v${v}${s.stage===4&&i>=3-s.r?'\n← read asked':''}`));

  add('hotkey',B('One popular key, three shards', 'یک کلید محبوب، سه shard'),
    B('Eight increments target one key. Try adding an idle shard or splitting the counter into salted keys.', 'هشت افزایش برای یک کلید می‌رسد؛ افزودن shard بیکار یا تقسیم شمارنده به کلیدهای saltشده را امتحان کن.'),
    B('Each shard handles two increments per tick. Salted counter writes are spread evenly and require read-time aggregation; ordinary single-key writes are not.', 'هر shard در هر نوبت دو افزایش انجام می‌دهد؛ نوشتن شمارندهٔ saltشده یکنواخت پخش می‌شود و خواندن تجمیعی لازم دارد؛ کلید عادی چنین نیست.'),
    [B('Shard A', 'shard A'),B('Shard B', 'shard B'),B('Shard C', 'shard C')],
    ()=>({mode:null,queues:[0,0,0],done:[0,0,0],tick:0}),[
      A('add',B('Add an idle shard', 'افزودن shard بیکار'),at(0),s=>{s.mode='one-key';s.stage=1;say(s,'Hashing still routes one key to one owner; adding a shard alone does not split this key.','hash همچنان یک کلید را به یک مالک می‌فرستد؛ افزودن shard به‌تنهایی این کلید را تقسیم نمی‌کند.');}),
      A('salt',B('Salt a counter into 3 keys', 'تقسیم شمارنده به ۳ کلید'),at(0),s=>{s.mode='salt';s.stage=1;say(s,'This changes the data model: three sub-counters must be summed on reads.','مدل داده تغییر می‌کند؛ سه زیرشمارنده هنگام خواندن باید جمع شوند.');}),
      A('send',B('Send 8 increments', 'ارسال ۸ افزایش'),at(1),s=>{s.queues=s.mode==='salt'?[3,3,2]:[8,0,0];s.stage=2;say(s,'Inspect the per-shard queues before service.','پیش از پردازش صف هر shard را ببین.',0,2);}),
      A('tick',B('Serve one tick', 'یک نوبت پردازش'),s=>s.stage===2&&s.queues.some(Boolean),s=>{s.queues=s.queues.map((n,i)=>{const k=Math.min(2,n);s.done[i]+=k;return n-k;});s.tick++;if(!s.queues.some(Boolean))s.stage=3;say(s,`After ${s.tick} ticks: ${s.done.reduce((a,b)=>a+b,0)} increments completed. ${s.mode==='salt'?'Reads aggregate all sub-counters.':'Other shards cannot help this single key.'}`,`پس از ${s.tick} نوبت، ${s.done.reduce((a,b)=>a+b,0)} افزایش تکمیل شد؛ ${s.mode==='salt'?'خواندن همهٔ زیرشمارنده‌ها را جمع می‌کند.':'shardهای دیگر به این تک‌کلید کمک نمی‌کنند.'}`,0,2);})
    ],s=>s.queues.map((n,i)=>`waiting=${n}\ncompleted=${s.done[i]}`));

  add('seat',B('Two buyers, one last seat', 'دو خریدار و آخرین صندلی'),
    B('Both buyers read remaining=1. Choose an unconditional insert or an atomic guarded reservation.', 'هر دو خریدار remaining=1 می‌خوانند؛ درج بدون شرط یا رزرو اتمیک با شرط را انتخاب کن.'),
    B('The guarded transaction checks remaining > 0 and decrements it atomically. Blind inserts only check an earlier read; bookings are separate rows.', 'تراکنش محافظت‌شده remaining > 0 را بررسی و اتمیک کم می‌کند؛ درج ساده فقط به خواندن قبلی تکیه دارد و رزروها ردیف‌های جدا هستند.'),
    [B('Buyer A', 'خریدار A'),B('Reservation store', 'مرجع رزرو'),B('Buyer B', 'خریدار B')],
    ()=>({guard:false,a:null,b:null,remaining:1,bookings:[],aResult:null,bResult:null}),[
      A('blind',B('Check then insert', 'بررسی و سپس درج جدا'),at(0),s=>{s.stage=1;say(s,'The check is separate from the write; both clients can pass.','بررسی از نوشتن جداست؛ هر دو کاربر ممکن است عبور کنند.');}),
      A('guard',B('Atomic conditional reservation', 'رزرو اتمیک شرطی'),at(0),s=>{s.guard=true;s.stage=1;say(s,'The database will enforce the invariant at reservation time.','پایگاه داده شرط را هنگام رزرو اعمال می‌کند.');}),
      A('read',B('Both read remaining', 'خواندن موجودی توسط هر دو'),at(1),s=>{s.a=s.b=s.remaining;s.stage=2;say(s,'Both snapshots show one available seat. Reads alone reserve nothing.','هر دو snapshot یک صندلی آزاد می‌بینند؛ خواندن صندلی را رزرو نمی‌کند.',1,2);}),
      A('a',B('Reserve for A', 'رزرو برای A'),at(2),s=>{s.bookings.push('A');s.remaining=0;s.aResult='reserved';s.stage=3;say(s,'A reserved the last seat. B still holds the old observation.','A آخرین صندلی را رزرو کرد؛ B هنوز مشاهدهٔ قبلی را دارد.',0,1);}),
      A('b',B('Reserve for B', 'رزرو برای B'),at(3),s=>{if(s.guard){s.bResult='rejected';}else{s.bookings.push('B');s.bResult='reserved';}s.stage=4;say(s,s.guard?'The atomic condition sees zero remaining and rejects B; one booking survives.':'B trusted its old read and inserted another booking. Two bookings now claim one seat.',s.guard?'شرط اتمیک موجودی صفر را می‌بیند و B را رد می‌کند؛ یک رزرو باقی ماند.':'B به خواندن قبلی اعتماد کرد و رزرو دیگری نوشت؛ دو رزرو برای یک صندلی ثبت شد.',2,1);})
    ],s=>[`read=${s.a??'∅'}\nresult=${s.aResult||'∅'}`,`remaining=${s.remaining}\nbookings=[${s.bookings}]`,`read=${s.b??'∅'}\nresult=${s.bResult||'∅'}`]);

  add('retry',B('Timeout does not mean rollback', 'timeout به معنی rollback نیست'),
    B('Commit a payment, lose its reply, then choose the retry identity.', 'پرداخت را ثبت کن، پاسخ را گم کن و هویت بازتلاش را انتخاب کن.'),
    B('The durable payment store atomically deduplicates request IDs with the effect. Responses can be lost independently of commits.', 'مرجع پایدار پرداخت، شناسهٔ درخواست و اثر آن را اتمیک ثبت و تکرار را حذف می‌کند؛ پاسخ مستقل از commit ممکن است گم شود.'),
    [B('Client knowledge', 'دانش کاربر'),B('Network', 'شبکه'),B('Payment store', 'مرجع پرداخت')],
    ()=>({charges:0,ids:[],knowledge:'not sent',reply:'∅'}),[
      A('send',B('Send payment request #42', 'ارسال درخواست پرداخت ۴۲'),at(0),s=>{s.charges=1;s.ids=[42];s.knowledge='waiting';s.reply='success in flight';s.stage=1;say(s,'The server committed one payment; the success response is in flight.','سرور یک پرداخت ثبت کرد؛ پاسخ موفقیت هنوز در راه است.',0,2);}),
      A('drop',B('Lose response; timeout', 'گم‌کردن پاسخ و timeout'),at(1),s=>{s.knowledge='outcome unknown';s.reply='lost';s.stage=2;say(s,'The client cannot distinguish a lost request from a lost reply. The server state did not roll back.','کاربر نمی‌تواند درخواست گم‌شده را از پاسخ گم‌شده تشخیص دهد؛ وضعیت سرور rollback نشده است.',2,1);}),
      A('same',B('Retry with ID #42', 'بازتلاش با همان شناسهٔ ۴۲'),at(2),s=>{s.knowledge='success known';s.reply='cached result';s.stage=3;say(s,'The store found #42 and returned its original result without another charge.','مرجع شناسهٔ ۴۲ را یافت و نتیجهٔ قبلی را بدون پرداخت دوباره برگرداند.',2,0);}),
      A('new',B('Retry with new ID #43', 'بازتلاش با شناسهٔ جدید ۴۳'),at(2),s=>{s.charges++;s.ids.push(43);s.knowledge='success known';s.reply='new result';s.stage=3;say(s,'A new identity looks like a new payment: the customer was charged twice.','هویت جدید یک پرداخت جدید به نظر می‌رسد؛ مشتری دوبار پرداخت کرد.',0,2);})
    ],s=>[s.knowledge,s.reply,`charges=${s.charges}\nids=[${s.ids}]`]);

  add('quorum',B('A leader needs a majority', 'رهبر به اکثریت نیاز دارد'),
    B('Partition a three-voter group, then decide which side receives the write.', 'گروه سه‌رأی‌دهنده را تقسیم کن و مقصد نوشتن را انتخاب کن.'),
    B('A simplified leader-based crash-fault model: a commit needs 2/3 durable acknowledgements in the current term; no membership changes or Byzantine faults.', 'مدل سادهٔ رهبرمحور با خرابی توقف؛ commit به تأیید پایدار ۲ از ۳ عضو در term فعلی نیاز دارد؛ عضویت ثابت و بدون خطای بیزانسی.'),
    [B('Voter A / old leader', 'رأی‌دهنده A / رهبر قبلی'),B('Voter B', 'رأی‌دهنده B'),B('Voter C', 'رأی‌دهنده C')],
    ()=>({split:false,term:[1,1,1],logs:[0,0,0],committed:[false,false,false],target:null}),[
      A('partition',B('Partition A | B,C', 'تقسیم A | B,C'),at(0),s=>{s.split=true;s.stage=1;say(s,'A is isolated; B and C can communicate. A name or lease alone is not a majority.','A جداست؛ B و C به هم دسترسی دارند. نام رهبر یا lease به‌تنهایی اکثریت نیست.',0,1);}),
      A('minority',B('Write to old leader A', 'نوشتن به رهبر قبلی A'),at(1),s=>{s.logs[0]=1;s.target='A';s.stage=2;say(s,'A appended locally but has only 1/3 votes. No committed success can be returned.','A محلی append کرد ولی فقط ۱ از ۳ رأی دارد؛ موفقیت ثبت‌شده نمی‌تواند برگرداند.',0,0);}),
      A('majority',B('Elect B; write to B,C', 'انتخاب B و نوشتن در B,C'),at(1),s=>{s.term[1]=s.term[2]=2;s.logs[1]=s.logs[2]=1;s.committed[1]=s.committed[2]=true;s.target='BC';s.stage=2;say(s,'B wins term 2 with C. Two durable copies form a majority, so this entry commits.','B با C در term ۲ انتخاب شد؛ دو کپی پایدار اکثریت می‌سازند و entry ثبت می‌شود.',1,2);}),
      A('heal',B('Heal network', 'وصل‌کردن شبکه'),at(2),s=>{s.split=false;s.term=[2,2,2];if(s.target==='BC'){s.logs[0]=1;s.committed[0]=true;}else{s.logs[0]=0;}s.stage=3;say(s,s.target==='BC'?'A accepts the higher term and catches up with the committed majority.':'B and C elect a new-term leader; A discards the minority-only tentative entry, which never committed.',s.target==='BC'?'A term بالاتر را می‌پذیرد و با اکثریت ثبت‌شده همگام می‌شود.':'B و C رهبر term جدید را انتخاب می‌کنند؛ A ورودی موقتِ فقط اقلیت را که commit نشده بود حذف می‌کند.',1,0);})
    ],s=>s.logs.map((n,i)=>`entry=${n}\n${s.committed[i]?'committed':'uncommitted'}\nterm=${s.term[i]}${s.split&&i===0?' · isolated':''}`));

  add('batch',B('Retry a task without duplicating output', 'بازتلاش task بدون خروجی تکراری'),
    B('A task writes two output rows and crashes before completion acknowledgement. Choose its publication strategy.', 'task دو ردیف خروجی می‌نویسد و پیش از تأیید اتمام متوقف می‌شود؛ روش انتشار را انتخاب کن.'),
    B('Input is deterministic. The staged strategy atomically publishes one winning attempt manifest; direct append has no deduplication.', 'ورودی قطعی است؛ روش staging مانیفست یک تلاش برنده را اتمیک منتشر می‌کند؛ append مستقیم حذف تکرار ندارد.'),
    [B('Task attempt', 'تلاش task'),B('Attempt staging', 'فضای موقت تلاش'),B('Published output', 'خروجی منتشرشده')],
    ()=>({mode:null,attempt:1,temp:[],output:[],failed:false}),[
      A('append',B('Append directly', 'append مستقیم'),at(0),s=>{s.mode='append';s.stage=1;say(s,'Each attempt appends to shared visible output.','هر تلاش به خروجی قابل مشاهدهٔ مشترک اضافه می‌کند.');}),
      A('stage',B('Stage then atomic publish', 'staging و انتشار اتمیک'),at(0),s=>{s.mode='stage';s.stage=1;say(s,'Attempt-local output is invisible until publication.','خروجی هر تلاش تا انتشار دیده نمی‌شود.');}),
      A('run',B('Write first attempt', 'نوشتن تلاش اول'),at(1),s=>{if(s.mode==='stage')s.temp=['a','b'];else s.output.push('a','b');s.stage=2;say(s,'Attempt 1 produced rows a and b, before completion was acknowledged.','تلاش ۱ قبل از تأیید اتمام، ردیف‌های a و b را تولید کرد.',0,s.mode==='stage'?1:2);}),
      A('crash',B('Crash before acknowledgement', 'خرابی پیش از تأیید'),at(2),s=>{s.failed=true;s.stage=3;say(s,'The scheduler sees no completed task and will retry.','زمان‌بند task تکمیل‌شده نمی‌بیند و بازتلاش می‌کند.',0,0);}),
      A('retry',B('Run attempt 2 and publish', 'اجرای تلاش ۲ و انتشار'),at(3),s=>{s.attempt=2;s.failed=false;if(s.mode==='stage'){s.temp=['a','b'];s.output=[...s.temp];}else{s.output.push('a','b');}s.stage=4;say(s,s.mode==='stage'?'One winning attempt manifest exposes a,b once; the orphaned attempt can be cleaned.':'Direct append exposed a,b twice. Task retry alone does not make the sink exactly-once.',s.mode==='stage'?'مانیفست یک تلاش برنده a,b را یک بار نشان می‌دهد؛ تلاش رهاشده قابل پاک‌کردن است.':'append مستقیم a,b را دوبار نشان داد؛ بازتلاش task به‌تنهایی خروجی را exactly-once نمی‌کند.',1,2);})
    ],s=>[`attempt=${s.attempt}\nstate=${s.failed?'crashed':'running'}`,`rows=[${s.temp}]`,`rows=[${s.output}]`]);

  add('consumer',B('Crash between the effect and acknowledgement', 'خرابی بین اثر و تأیید پیام'),
    B('Apply event #9, crash before acknowledgement, and redeliver it.', 'رویداد ۹ را اعمال کن، پیش از ack خرابی ایجاد کن و دوباره تحویلش بده.'),
    B('At-least-once delivery. With deduplication, event ID and counter effect commit in one durable sink transaction; acknowledgements are separate.', 'تحویل at-least-once؛ در روش حذف تکرار، شناسهٔ رویداد و اثر شمارنده در یک تراکنش پایدار مقصد ثبت می‌شوند و ack جداست.'),
    [B('Broker', 'بروکر'),B('Consumer', 'مصرف‌کننده'),B('Durable sink', 'مقصد پایدار')],
    ()=>({dedup:false,delivered:0,count:0,seen:[],acked:false,down:false}),[
      A('plain',B('Apply every delivery', 'اعمال هر تحویل'),at(0),s=>{s.stage=1;say(s,'Every delivery increments the sink counter.','هر تحویل شمارندهٔ مقصد را زیاد می‌کند.');}),
      A('dedup',B('Atomic event-ID deduplication', 'حذف تکرار اتمیک با شناسه'),at(0),s=>{s.dedup=true;s.stage=1;say(s,'Effect and event ID will commit together in the sink.','اثر و شناسهٔ رویداد با هم در مقصد commit می‌شوند.');}),
      A('apply',B('Deliver #9 and commit effect', 'تحویل ۹ و ثبت اثر'),at(1),s=>{s.delivered=1;s.count=1;if(s.dedup)s.seen=[9];s.stage=2;say(s,'The effect committed. The broker has not received an acknowledgement.','اثر ثبت شد؛ بروکر هنوز ack دریافت نکرده است.',0,2);}),
      A('crash',B('Crash before ack', 'خرابی قبل از ack'),at(2),s=>{s.down=true;s.stage=3;say(s,'The broker still considers #9 unacknowledged. Sink state survives the consumer crash.','بروکر هنوز ۹ را تأییدنشده می‌داند؛ وضعیت مقصد از خرابی مصرف‌کننده جان سالم برد.',1,1);}),
      A('redeliver',B('Restart and redeliver #9', 'راه‌اندازی و تحویل دوبارهٔ ۹'),at(3),s=>{s.down=false;s.delivered++;if(!s.dedup)s.count++;s.acked=true;s.stage=4;say(s,s.dedup?'The durable seen-ID suppresses the second effect, then the consumer acknowledges.':'The redelivery increments again. Acknowledging later cannot undo the duplicate effect.',s.dedup?'شناسهٔ پایدار اثر دوم را حذف می‌کند؛ سپس مصرف‌کننده ack می‌دهد.':'تحویل دوباره یک افزایش دیگر ایجاد کرد؛ ack بعدی اثر تکراری را خنثی نمی‌کند.',0,2);})
    ],s=>[`deliveries=${s.delivered}\nacked=${s.acked}`,`process=${s.down?'down':'up'}`,`count=${s.count}\nseen=[${s.seen}]`]);

  add('rebuild',B('Rebuild a projection from its source', 'بازسازی نما از مرجع داده'),
    B('Two confirmed orders feed a derived total. Corrupt the projection, then choose a recovery source.', 'دو سفارش قطعی مجموع مشتق‌شده را تغذیه می‌کنند؛ نما را خراب کن و منبع بازیابی را انتخاب کن.'),
    B('The source log retains both committed events. Rebuild folds into a fresh projection and swaps it in; replaying into an existing counter would require deduplication.', 'لاگ مرجع هر دو رویداد ثبت‌شده را نگه می‌دارد؛ بازسازی در نمای تازه انجام و جایگزین می‌شود؛ replay در شمارندهٔ موجود به حذف تکرار نیاز دارد.'),
    [B('Authoritative events', 'رویدادهای مرجع'),B('Projection builder', 'سازندهٔ نما'),B('Derived total', 'مجموع مشتق‌شده')],
    ()=>({events:[10,20],total:30,source:null,replayed:0}),[
      A('corrupt',B('Lose derived state', 'از دست‌دادن نمای مشتق‌شده'),at(0),s=>{s.total=0;s.stage=1;say(s,'The projection is empty; authoritative events remain untouched.','نما خالی است؛ رویدادهای مرجع هنوز سالم‌اند.',2,2);}),
      A('source',B('Rebuild from source log', 'بازسازی از لاگ مرجع'),at(1),s=>{s.source='log';s.stage=2;say(s,'Create a new empty projection and read the authoritative events.','نمای خالی تازه بساز و رویدادهای مرجع را بخوان.',0,1);}),
      A('view',B('Copy the empty projection', 'کپی نمای خالی'),at(1),s=>{s.source='view';s.stage=3;say(s,'Copying a broken derivative cannot recover the missing facts. The source is still available.','کپی مشتق خراب حقایق گم‌شده را برنمی‌گرداند؛ مرجع هنوز موجود است.',2,1);}),
      A('event',B('Replay next source event', 'بازپخش رویداد بعدی مرجع'),s=>s.stage===2&&s.replayed<s.events.length,s=>{s.total+=s.events[s.replayed++];if(s.replayed===s.events.length)s.stage=3;say(s,`Folded ${s.replayed}/2 events; total=${s.total}. Rebuild is complete only after the retained source is consumed.`,`${s.replayed} از ۲ رویداد اعمال شد؛ total=${s.total}. بازسازی پس از مصرف کامل مرجع نگه‌داری‌شده تمام می‌شود.`,0,2);})
    ],s=>[`amounts=[${s.events}]`,`source=${s.source||'∅'}\nreplayed=${s.replayed}/2`,`total=${s.total}`]);

  add('privacy',B('Can a restore resurrect deleted data?', 'آیا restore دادهٔ حذف‌شده را برمی‌گرداند؟'),
    B('Revoke consent and delete a profile, then restore an older backup.', 'رضایت را پس بگیر و پروفایل را حذف کن؛ بعد backup قدیمی را برگردان.'),
    B('A local engineering model, not a legal compliance assessment. A durable deletion ledger survives this restore and is applied before restored data is served.', 'مدل مهندسی محلی است و ارزیابی انطباق قانونی نیست. دفتر حذف پایدار از این restore جان سالم می‌برد و پیش از سرویس‌دهی دادهٔ بازیابی‌شده اعمال می‌شود.'),
    [B('Consent / deletion ledger', 'رضایت / دفتر حذف'),B('Live profile', 'پروفایل فعال'),B('Old backup', 'backup قدیمی')],
    ()=>({guard:false,consent:true,tombstone:false,live:true,backup:true}),[
      A('naive',B('Restore without deletion ledger', 'restore بدون دفتر حذف'),at(0),s=>{s.stage=1;say(s,'An old backup can contain a profile that was deleted later.','backup قدیمی می‌تواند پروفایلی داشته باشد که بعداً حذف شده است.');}),
      A('guard',B('Retain and enforce deletion ledger', 'حفظ و اعمال دفتر حذف'),at(0),s=>{s.guard=true;s.stage=1;say(s,'Keep a durable deletion marker outside the restored snapshot.','نشانگر حذف پایدار را خارج از snapshot بازیابی‌شده نگه دار.');}),
      A('delete',B('Revoke consent and delete', 'پس‌گرفتن رضایت و حذف'),at(1),s=>{s.consent=false;s.live=false;s.tombstone=s.guard;s.stage=2;say(s,'Live profile deleted. The older backup still contains it.','پروفایل فعال حذف شد؛ backup قدیمی هنوز آن را دارد.',0,1);}),
      A('restore',B('Restore old backup', 'بازیابی backup قدیمی'),at(2),s=>{s.live=s.backup&&!s.tombstone;s.stage=3;say(s,s.live?'The restore resurrected the profile despite revoked consent. A deletion must propagate across restore paths.':'The restore consulted the retained deletion ledger before serving; the profile remains absent.',s.live?'restore با وجود لغو رضایت پروفایل را برگرداند؛ حذف باید مسیر بازیابی را هم پوشش دهد.':'restore پیش از سرویس‌دهی دفتر حذف را بررسی کرد؛ پروفایل همچنان حذف‌شده ماند.',2,1);})
    ],s=>[`consent=${s.consent}\ndeleted-ID=${s.tombstone}`,`profile=${s.live?'present':'absent'}`,`profile=${s.backup?'present':'absent'}\nsnapshot=before deletion`]);

  add('olap',B('A report meets checkout', 'گزارش سنگین در برابر پرداخت'),
    B('Decide where the heavy sales report runs, start it, then place an order.', 'تصمیم بگیر گزارش سنگین فروش کجا اجرا شود؛ آن را شروع کن و بعد یک سفارش ثبت کن.'),
    B('The report scans every order. On the primary it competes with checkout for the same resources; a warehouse copy isolates it but is as old as the last ETL run.', 'گزارش همهٔ سفارش‌ها را می‌خواند. روی primary با checkout سر منابع مشترک رقابت می‌کند؛ نسخهٔ warehouse جدا است ولی به اندازهٔ آخرین ETL قدیمی است.'),
    [B('Report location', 'محل گزارش'),B('Report job', 'کار گزارش'),B('Checkout', 'پرداخت')],
    ()=>({mode:null,reportOn:false,checkout:null,fresh:false}),[
      A('primary',B('Run on the primary database', 'اجرا روی دیتابیس اصلی'),at(0),s=>{s.mode='primary';s.stage=1;say(s,'The report will read the live OLTP tables.','گزارش جدول‌های زندهٔ OLTP را می‌خواند.');}),
      A('warehouse',B('Run on a warehouse copy', 'اجرا روی نسخهٔ warehouse'),at(0),s=>{s.mode='warehouse';s.stage=1;say(s,'The report will read last night copy.','گزارش نسخهٔ دیشب را می‌خواند.');}),
      A('report',B('Start the report', 'شروع گزارش'),at(1),s=>{s.reportOn=true;s.stage=2;say(s,'A full scan is running. Now a customer pays.','یک اسکن کامل در حال اجراست؛ حالا مشتری پرداخت می‌کند.',0,1);}),
      A('checkout',B('Place an order', 'ثبت سفارش'),at(2),s=>{s.checkout=s.mode==='primary'?'slow':'fast';s.stage=3;say(s,s.checkout==='slow'?'The order waited behind the scan: analytics hurt the user-facing path.':'The order was unaffected; the report used another machine.',s.checkout==='slow'?'سفارش پشت اسکن ماند؛ تحلیل مسیر کاربر را کند کرد.':'سفارش تحت تأثیر نبود؛ گزارش روی ماشین دیگری بود.',1,2);}),
      A('etl',B('Check how fresh the report is', 'تازگی گزارش را بسنج'),at(3),s=>{s.fresh=s.mode==='primary';s.stage=4;say(s,s.fresh?'The report saw live data, at the price shown in checkout.':'The report does not contain the order just placed until the next ETL load.',s.fresh?'گزارش داده زنده دید، با هزینه‌ای که در checkout دیدی.':'گزارش سفارش تازه را ندارد تا بارگذاری بعدی ETL.',1,0);})
    ],s=>[`mode=${s.mode||'?'}`,`report=${s.reportOn?'running':'idle'}\nfresh=${s.stage>=4?s.fresh:'?'}`,`checkout=${s.checkout||'∅'}`]);

  add('fanout',B('One post, many followers', 'یک پست، چند دنبال‌کننده'),
    B('Choose when the timeline is assembled, publish a post, open a timeline, then grow the audience.', 'انتخاب کن timeline کی ساخته شود؛ پست منتشر کن، timeline را باز کن و بعد مخاطب را زیاد کن.'),
    B('Fan-out on write copies the post into each follower timeline. Fan-out on read stores it once and merges at read time. Costs are counted in operations, not milliseconds.', 'fan-out هنگام نوشتن پست را در timeline هر دنبال‌کننده کپی می‌کند؛ fan-out هنگام خواندن یک بار ذخیره می‌کند و هنگام خواندن ادغام می‌کند. هزینه با تعداد عملیات شمرده می‌شود نه میلی‌ثانیه.'),
    [B('Followers', 'دنبال‌کننده‌ها'),B('Write path', 'مسیر نوشتن'),B('Read path', 'مسیر خواندن')],
    ()=>({mode:null,followers:3,writes:0,reads:0}),[
      A('onwrite',B('Fan out on write', 'fan-out هنگام نوشتن'),at(0),s=>{s.mode='write';s.stage=1;say(s,'Each post will be copied to every follower timeline.','هر پست در timeline همهٔ دنبال‌کننده‌ها کپی می‌شود.');}),
      A('onread',B('Merge on read', 'ادغام هنگام خواندن'),at(0),s=>{s.mode='read';s.stage=1;say(s,'A post is stored once; timelines are merged when opened.','پست یک بار ذخیره می‌شود و timeline هنگام باز شدن ادغام می‌شود.');}),
      A('post',B('Publish a post', 'انتشار پست'),at(1),s=>{s.writes=s.mode==='write'?s.followers:1;s.stage=2;say(s,`The post cost ${s.writes} write(s).`,`این پست ${s.writes} نوشتن هزینه داشت.`,0,1);}),
      A('open',B('Open one timeline', 'باز کردن یک timeline'),at(2),s=>{s.reads=s.mode==='write'?1:s.followers;s.stage=3;say(s,`Opening a timeline cost ${s.reads} lookup(s).`,`باز کردن timeline ${s.reads} lookup هزینه داشت.`,1,2);}),
      A('celebrity',B('Account grows to 1000 followers', 'حساب به ۱۰۰۰ دنبال‌کننده می‌رسد'),at(3),s=>{s.followers=1000;s.writes=s.mode==='write'?1000:1;s.reads=s.mode==='write'?1:1000;s.stage=4;say(s,s.mode==='write'?'One post now costs 1000 writes; reads stayed cheap.':'Writes stayed cheap; every timeline open now merges 1000 sources.',s.mode==='write'?'یک پست حالا ۱۰۰۰ نوشتن می‌خواهد؛ خواندن ارزان ماند.':'نوشتن ارزان ماند؛ هر بار باز کردن timeline ۱۰۰۰ منبع را ادغام می‌کند.',1,2);})
    ],s=>[`followers=${s.followers}`,`mode=${s.mode||'?'}\nper post=${s.writes} writes`,`per open=${s.reads} lookups`]);

  add('eventlog',B('Fix a wrong fee after the fact', 'اصلاح کارمزد اشتباه بعد از وقوع'),
    B('Store the account as a balance or as events, charge a fee by mistake, then correct the rule.', 'حساب را به‌صورت موجودی یا رویداد ذخیره کن، کارمزد را اشتباهی کم کن و بعد قاعده را اصلاح کن.'),
    B('Events are append-only facts and the balance is derived by replay. A stored balance keeps only the latest result.', 'رویدادها واقعیت‌های append-only هستند و موجودی با بازپخش به‌دست می‌آید. موجودی ذخیره‌شده فقط آخرین نتیجه را نگه می‌دارد.'),
    [B('Stored history', 'تاریخچهٔ ذخیره‌شده'),B('Current balance', 'موجودی فعلی'),B('After the fix', 'بعد از اصلاح')],
    ()=>({mode:null,events:[],balance:0,fixed:null}),[
      A('state',B('Store only the balance', 'فقط موجودی ذخیره شود'),at(0),s=>{s.mode='state';s.stage=1;say(s,'Each change overwrites the number.','هر تغییر عدد را بازنویسی می‌کند.');}),
      A('events',B('Store events', 'ذخیرهٔ رویدادها'),at(0),s=>{s.mode='events';s.stage=1;say(s,'Each change is appended as a fact.','هر تغییر به‌صورت یک واقعیت اضافه می‌شود.');}),
      A('ops',B('Deposit 100, then a buggy fee of 30', 'واریز ۱۰۰ و کارمزد اشتباه ۳۰'),at(1),s=>{s.balance=70;if(s.mode==='events')s.events=['deposit 100','fee 30 (bug)'];s.stage=2;say(s,'The balance is 70. The fee rule was wrong: it should have been 0.','موجودی ۷۰ است. قاعدهٔ کارمزد اشتباه بود و باید صفر می‌بود.',0,1);}),
      A('fix',B('Correct the rule and recompute', 'اصلاح قاعده و محاسبهٔ دوباره'),at(2),s=>{s.fixed=s.mode==='events'?100:'?';s.stage=3;say(s,s.mode==='events'?'Replaying the facts with the fixed rule gives 100.':'Only 70 remains. Without the history you cannot tell what the right value was.',s.mode==='events'?'بازپخش واقعیت‌ها با قاعدهٔ درست ۱۰۰ می‌دهد.':'فقط ۷۰ مانده است؛ بدون تاریخچه نمی‌دانی مقدار درست چه بوده.',1,2);})
    ],s=>[s.events.length?s.events.join('\n'):(s.mode==='state'?'no history':'∅'),`balance=${s.balance}`,`balance=${s.fixed===null?'∅':s.fixed}`]);

  add('scan',B('Find the latest value of a key', 'پیدا کردن آخرین مقدار یک کلید'),
    B('Append four writes to a log, then read key k with and without an index.', 'چهار نوشتن را به log اضافه کن و کلید k را با و بدون index بخوان.'),
    B('A log only appends, so a key may appear many times and the last entry wins. A hash index keeps the offset of the latest entry for each key.', 'log فقط اضافه می‌کند؛ پس یک کلید چند بار ظاهر می‌شود و آخرین رکورد برنده است. hash index آفست آخرین رکورد هر کلید را نگه می‌دارد.'),
    [B('Append-only log', 'log فقط‌افزودنی'),B('Hash index', 'hash index'),B('Lookup of k', 'جست‌وجوی k')],
    ()=>({indexed:null,log:[],index:null,reads:0,value:null}),[
      A('noindex',B('No index', 'بدون index'),at(0),s=>{s.indexed=false;s.stage=1;say(s,'Reads must scan the log.','خواندن باید log را اسکن کند.');}),
      A('hash',B('Keep a hash index', 'نگه‌داشتن hash index'),at(0),s=>{s.indexed=true;s.stage=1;say(s,'Every write also updates an in-memory key to offset map.','هر نوشتن نگاشت کلید به آفست را در حافظه هم به‌روز می‌کند.');}),
      A('write',B('Write k=1, k=2, j=9, k=3', 'نوشتن k=1، k=2، j=9، k=3'),at(1),s=>{s.log=['k=1','k=2','j=9','k=3'];if(s.indexed)s.index={k:3,j:2};s.stage=2;say(s,'The log holds four records; k appears three times.','log چهار رکورد دارد و k سه بار آمده است.',0,1);}),
      A('get',B('Get k', 'خواندن k'),at(2),s=>{s.reads=s.indexed?1:s.log.length;s.value=3;s.stage=3;say(s,`Found k=3 after reading ${s.reads} record(s). The newest entry wins either way.`,`k=3 پس از خواندن ${s.reads} رکورد پیدا شد؛ در هر دو حالت جدیدترین رکورد برنده است.`,1,2);})
    ],s=>[s.log.length?s.log.join('\n'):'∅',s.index?JSON.stringify(s.index):(s.indexed===false?'none':'∅'),`k=${s.value??'∅'}\nrecords read=${s.reads}`]);

  add('rolling',B('Add a field during a rolling upgrade', 'افزودن فیلد در حین rolling upgrade'),
    B('The new reader is deployed before old records are rewritten. Choose how the new field is declared.', 'خوانندهٔ جدید پیش از بازنویسی رکوردهای قدیمی deploy شده است. نحوهٔ تعریف فیلد جدید را انتخاب کن.'),
    B('Old stored records have no tier field. A required field makes the new reader reject them; an optional field with a default keeps them readable.', 'رکوردهای قدیمی فیلد tier ندارند. فیلد اجباری خوانندهٔ جدید را روی آن‌ها شکست می‌دهد؛ فیلد اختیاری با مقدار پیش‌فرض آن‌ها را خواندنی نگه می‌دارد.'),
    [B('Old record (v1)', 'رکورد قدیمی v1'),B('New schema (v2)', 'schema جدید v2'),B('Read result', 'نتیجهٔ خواندن')],
    ()=>({schema:null,result:null}),[
      A('required',B('tier is required', 'tier اجباری است'),at(0),s=>{s.schema='required';s.stage=1;say(s,'Readers must find tier in every record.','خواننده باید tier را در هر رکورد پیدا کند.');}),
      A('optional',B('tier is optional, default basic', 'tier اختیاری با پیش‌فرض basic'),at(0),s=>{s.schema='optional';s.stage=1;say(s,'A missing tier becomes basic.','نبود tier به basic تبدیل می‌شود.');}),
      A('read',B('Read the old record', 'خواندن رکورد قدیمی'),at(1),s=>{s.result=s.schema==='required'?'error: missing tier':'{id:1, tier:basic}';s.stage=2;say(s,s.schema==='required'?'Decoding failed: every old record is now unreadable until it is rewritten.':'Decoding worked: old data and new code coexist during the upgrade.',s.schema==='required'?'decode شکست خورد؛ همهٔ رکوردهای قدیمی تا بازنویسی خواندنی نیستند.':'decode موفق شد؛ داده قدیمی و کد جدید هنگام ارتقا کنار هم کار می‌کنند.',0,2);})
    ],s=>['{id:1}',`tier: ${s.schema||'?'}`,s.result||'∅']);

  add('rebalance',B('Add a fourth node', 'افزودن گره چهارم'),
    B('Twelve keys live on three nodes. Choose how keys map to nodes, then add a node.', 'دوازده کلید روی سه گره هستند. نحوهٔ نگاشت کلید به گره را انتخاب کن و گره جدید اضافه کن.'),
    B('Keys 0..11. Mod-N uses key mod node-count. Fixed partitions keep 12 partitions and move whole partitions to the new node.', 'کلیدهای ۰ تا ۱۱. روش mod-N از key mod تعداد گره استفاده می‌کند؛ پارتیشن ثابت ۱۲ پارتیشن نگه می‌دارد و پارتیشن‌های کامل را به گره جدید می‌دهد.'),
    [B('Before', 'قبل'),B('After', 'بعد'),B('Data moved', 'داده جابه‌جاشده')],
    ()=>({scheme:null,nodes:3,moved:0}),[
      A('mod',B('node = key mod N', 'گره = key mod N'),at(0),s=>{s.scheme='mod';s.stage=1;say(s,'The node count is part of every key location.','تعداد گره در محل هر کلید دخالت دارد.');}),
      A('fixed',B('Fixed partitions', 'پارتیشن ثابت'),at(0),s=>{s.scheme='fixed';s.stage=1;say(s,'Partitions are assigned to nodes; the key to partition map never changes.','پارتیشن‌ها به گره‌ها اختصاص دارند و نگاشت کلید به پارتیشن ثابت می‌ماند.');}),
      A('add',B('Add node 4', 'افزودن گره ۴'),at(1),s=>{let m=0;for(let k=0;k<12;k++)if(s.scheme==='mod'&&k%3!==k%4)m++;if(s.scheme==='fixed')m=3;s.nodes=4;s.moved=m;s.stage=2;say(s,`${m} of 12 keys moved.`,`${m} کلید از ۱۲ کلید جابه‌جا شد.`,0,2);})
    ],s=>[`scheme=${s.scheme||'?'}\nnodes=3\n4 keys each`,`nodes=${s.nodes}`,`moved=${s.moved}/12`]);

  add('dirty',B('Read a transfer that never happened', 'خواندن انتقالی که هرگز رخ نداد'),
    B('A transaction debits an account. Read it before it finishes, then roll it back.', 'یک تراکنش از حساب کم می‌کند. پیش از پایانش بخوان و بعد آن را rollback کن.'),
    B('The account starts at 100. Read uncommitted shows in-flight writes; read committed shows only committed values.', 'حساب با ۱۰۰ شروع می‌شود. read uncommitted نوشتن در حال انجام را نشان می‌دهد و read committed فقط مقدار ثبت‌شده را.'),
    [B('Committed value', 'مقدار ثبت‌شده'),B('Transaction T1', 'تراکنش T1'),B('Reader', 'خواننده')],
    ()=>({level:null,balance:100,temp:null,seen:null}),[
      A('ru',B('Read uncommitted', 'read uncommitted'),at(0),s=>{s.level='uncommitted';s.stage=1;say(s,'Readers may see uncommitted changes.','خواننده‌ها ممکن است تغییرهای ثبت‌نشده را ببینند.');}),
      A('rc',B('Read committed', 'read committed'),at(0),s=>{s.level='committed';s.stage=1;say(s,'Readers see only committed values.','خواننده‌ها فقط مقدار ثبت‌شده را می‌بینند.');}),
      A('debit',B('T1 debits 50, not committed', 'T1 مبلغ ۵۰ کم می‌کند، ثبت نشده'),at(1),s=>{s.temp=50;s.stage=2;say(s,'T1 wrote 50 but has not committed.','T1 مقدار ۵۰ را نوشت ولی ثبت نکرده است.',0,1);}),
      A('read',B('Read the account', 'خواندن حساب'),at(2),s=>{s.seen=s.level==='uncommitted'?s.temp:s.balance;s.stage=3;say(s,`The reader saw ${s.seen}.`,`خواننده ${s.seen} را دید.`,1,2);}),
      A('abort',B('Roll back T1', 'rollback تراکنش T1'),at(3),s=>{s.temp=null;s.stage=4;say(s,s.seen===50?'The reader acted on 50, a value that never existed: a dirty read.':'Nothing the reader saw was undone; the balance is still 100.',s.seen===50?'خواننده بر اساس ۵۰ تصمیم گرفت، مقداری که هرگز وجود نداشت: dirty read.':'چیزی که خواننده دید لغو نشد؛ موجودی هنوز ۱۰۰ است.',1,0);})
    ],s=>[`balance=${s.balance}`,`pending=${s.temp??'∅'}`,`read=${s.seen??'∅'}\nlevel=${s.level||'?'}`]);

  add('fencing',B('A paused client wakes up with an old lock', 'کلاینت متوقف‌شده با قفل قدیمی بیدار می‌شود'),
    B('Client A takes a lease, freezes, loses it to B, then wakes up and writes. Decide whether storage checks tokens.', 'کلاینت A لیز می‌گیرد، متوقف می‌شود، آن را به B می‌دهد و بعد بیدار می‌شود و می‌نویسد. تصمیم بگیر storage توکن را بررسی کند یا نه.'),
    B('Each lock grant carries a rising token. A client does not know its lease expired while paused. Storage with fencing rejects tokens lower than the highest it has seen.', 'هر قفل یک توکن افزایشی دارد. کلاینت متوقف نمی‌داند لیزش تمام شده است. storage با fencing توکن کمتر از بیشترین توکن دیده‌شده را رد می‌کند.'),
    [B('Lock service', 'سرویس قفل'),B('Client A', 'کلاینت A'),B('Storage', 'storage')],
    ()=>({fence:null,holder:'none',value:'init',max:0,rejected:false}),[
      A('plain',B('Storage ignores tokens', 'storage توکن را نادیده می‌گیرد'),at(0),s=>{s.fence=false;s.stage=1;say(s,'Any write is accepted.','هر نوشتن پذیرفته می‌شود.');}),
      A('fence',B('Storage checks tokens', 'storage توکن را بررسی می‌کند'),at(0),s=>{s.fence=true;s.stage=1;say(s,'Writes with a stale token are refused.','نوشتن با توکن قدیمی رد می‌شود.');}),
      A('lockA',B('A acquires the lock (token 33)', 'A قفل را می‌گیرد (توکن ۳۳)'),at(1),s=>{s.holder='A (33)';s.stage=2;say(s,'A believes it is the holder.','A باور دارد دارندهٔ قفل است.',0,1);}),
      A('pause',B('A freezes; B gets token 34 and writes', 'A متوقف می‌شود؛ B توکن ۳۴ می‌گیرد و می‌نویسد'),at(2),s=>{s.holder='B (34)';s.value='B';s.max=34;s.stage=3;say(s,'The lease expired while A was paused. B wrote with token 34.','لیز در توقف A تمام شد و B با توکن ۳۴ نوشت.',0,2);}),
      A('wake',B('A wakes up and writes with token 33', 'A بیدار می‌شود و با توکن ۳۳ می‌نویسد'),at(3),s=>{if(s.fence){s.rejected=true;}else{s.value='A';}s.stage=4;say(s,s.fence?'Storage rejected token 33: B data is safe.':'Storage accepted the stale write and overwrote B: corruption.',s.fence?'storage توکن ۳۳ را رد کرد و داده B سالم ماند.':'storage نوشتن قدیمی را پذیرفت و B را بازنویسی کرد: خرابی داده.',1,2);})
    ],s=>[`holder=${s.holder}`,s.stage>=4?(s.rejected?'write refused':'write sent'):(s.stage>=3?'frozen':'idle'),`value=${s.value}\nhighest token=${s.max}`]);

  add('lamport',B('Which write came later?', 'کدام نوشتن بعدتر بود؟'),
    B('Node B writes after receiving node A message, but its wall clock runs 5 seconds behind. Pick the ordering rule.', 'گره B بعد از دریافت پیام گره A می‌نویسد ولی ساعت دیواری‌اش ۵ ثانیه عقب است. قاعدهٔ ترتیب را انتخاب کن.'),
    B('Wall-clock timestamps compare unsynchronized clocks. A Lamport counter on B becomes max(own, received) plus one, so a causal successor always gets a larger number.', 'timestamp ساعت دیواری ساعت‌های همگام‌نشده را مقایسه می‌کند. شمارندهٔ Lamport در B برابر max(شمارندهٔ خودش، دریافتی) به‌علاوهٔ یک می‌شود؛ پس جانشین علّی همیشه عدد بزرگ‌تری دارد.'),
    [B('Write v1 on A', 'نوشتن v1 در A'),B('Write v2 on B', 'نوشتن v2 در B'),B('Winner', 'برنده')],
    ()=>({rule:null,a:null,b:null,winner:null}),[
      A('wall',B('Last write wins by wall clock', 'برنده با ساعت دیواری'),at(0),s=>{s.rule='wall';s.stage=1;say(s,'The larger timestamp wins.','timestamp بزرگ‌تر برنده است.');}),
      A('lamport',B('Order by Lamport counters', 'ترتیب با شمارندهٔ Lamport'),at(0),s=>{s.rule='lamport';s.stage=1;say(s,'The larger logical counter wins.','شمارندهٔ منطقی بزرگ‌تر برنده است.');}),
      A('a',B('A writes v1 and sends it to B', 'A مقدار v1 را می‌نویسد و برای B می‌فرستد'),at(1),s=>{s.a=s.rule==='wall'?100:1;s.stage=2;say(s,`v1 gets timestamp ${s.a}.`,`v1 timestamp ${s.a} می‌گیرد.`,0,1);}),
      A('b',B('B reads v1, then writes v2', 'B مقدار v1 را می‌بیند و v2 را می‌نویسد'),at(2),s=>{s.b=s.rule==='wall'?95:2;s.stage=3;say(s,`v2 gets timestamp ${s.b}, even though it happened after v1.`,`v2 با اینکه بعد از v1 رخ داد timestamp ${s.b} گرفت.`,1,1);}),
      A('merge',B('Resolve the conflict', 'حل تعارض'),at(3),s=>{s.winner=s.b>s.a?'v2':'v1';s.stage=4;say(s,s.winner==='v2'?'v2 wins: the causally later write survived.':'v1 wins: the causally later write v2 was silently discarded.',s.winner==='v2'?'v2 برنده شد؛ نوشتن بعدی از نظر علّی حفظ شد.':'v1 برنده شد؛ v2 که از نظر علّی بعدتر بود بی‌صدا دور ریخته شد.',2,0);})
    ],s=>[`v1 ts=${s.a??'∅'}`,`v2 ts=${s.b??'∅'}\nrule=${s.rule||'?'}`,`winner=${s.winner||'∅'}`]);

  add('combiner',B('Shrink the shuffle', 'کوچک‌کردن shuffle'),
    B('A mapper emits word counts. Choose whether it pre-aggregates locally before data crosses the network.', 'یک mapper شمارش کلمه‌ها را تولید می‌کند. انتخاب کن پیش از عبور از شبکه محلی جمع کند یا نه.'),
    B('One mapper sees a a a a b b. A combiner merges identical keys locally, which is safe because addition is associative.', 'یک mapper دنباله a a a a b b را می‌بیند. combiner کلیدهای یکسان را محلی جمع می‌کند و چون جمع شرکت‌پذیر است امن است.'),
    [B('Mapper output', 'خروجی mapper'),B('Shuffle', 'shuffle'),B('Reducer result', 'نتیجهٔ reducer')],
    ()=>({combine:null,emitted:0,sent:0,result:null}),[
      A('plain',B('No combiner', 'بدون combiner'),at(0),s=>{s.combine=false;s.stage=1;say(s,'Every pair goes to the reducer.','هر جفت به reducer می‌رود.');}),
      A('combine',B('Combine locally', 'جمع محلی'),at(0),s=>{s.combine=true;s.stage=1;say(s,'Equal keys are merged before sending.','کلیدهای برابر پیش از ارسال ادغام می‌شوند.');}),
      A('map',B('Run the mapper', 'اجرای mapper'),at(1),s=>{s.emitted=6;s.stage=2;say(s,'The mapper emitted six pairs.','mapper شش جفت تولید کرد.',0,1);}),
      A('shuffle',B('Shuffle to the reducer', 'shuffle به reducer'),at(2),s=>{s.sent=s.combine?2:6;s.stage=3;say(s,`${s.sent} pair(s) crossed the network.`,`${s.sent} جفت از شبکه عبور کرد.`,1,2);}),
      A('reduce',B('Reduce', 'reduce'),at(3),s=>{s.result='a=4, b=2';s.stage=4;say(s,'Same answer either way; the combiner only saved network traffic.','پاسخ در هر دو حالت یکی است؛ combiner فقط ترافیک شبکه را کم کرد.',2,2);})
    ],s=>[`pairs emitted=${s.emitted}`,`pairs sent=${s.sent}\ncombiner=${s.combine===null?'?':s.combine}`,s.result||'∅']);

  add('logbroker',B('A new consumer joins late', 'مصرف‌کنندهٔ جدید دیر می‌رسد'),
    B('Choose a queue or a log, publish three messages, let consumer 1 read them, then add consumer 2.', 'صف یا log را انتخاب کن، سه پیام منتشر کن، بگذار مصرف‌کنندهٔ ۱ آن‌ها را بخواند و بعد مصرف‌کنندهٔ ۲ را اضافه کن.'),
    B('A queue deletes a message once it is acknowledged. A log retains it and each consumer tracks its own offset.', 'صف پیام را بعد از ack حذف می‌کند. log پیام را نگه می‌دارد و هر مصرف‌کننده offset خودش را دارد.'),
    [B('Broker', 'broker'),B('Consumer 1', 'مصرف‌کنندهٔ ۱'),B('Consumer 2', 'مصرف‌کنندهٔ ۲')],
    ()=>({kind:null,msgs:[],c1:[],c2:[]}),[
      A('queue',B('Message queue', 'صف پیام'),at(0),s=>{s.kind='queue';s.stage=1;say(s,'Acknowledged messages are removed.','پیام‌های ack‌شده حذف می‌شوند.');}),
      A('log',B('Log-based broker', 'broker مبتنی بر log'),at(0),s=>{s.kind='log';s.stage=1;say(s,'Messages stay in the log until retention expires.','پیام‌ها تا پایان retention در log می‌مانند.');}),
      A('publish',B('Publish m1, m2, m3', 'انتشار m1، m2، m3'),at(1),s=>{s.msgs=['m1','m2','m3'];s.stage=2;say(s,'Three messages are stored.','سه پیام ذخیره شد.',0,1);}),
      A('consume',B('Consumer 1 reads and acknowledges', 'مصرف‌کنندهٔ ۱ می‌خواند و ack می‌کند'),at(2),s=>{s.c1=[...s.msgs];if(s.kind==='queue')s.msgs=[];s.stage=3;say(s,'Consumer 1 processed all three.','مصرف‌کنندهٔ ۱ هر سه را پردازش کرد.',0,1);}),
      A('join',B('Consumer 2 starts from the beginning', 'مصرف‌کنندهٔ ۲ از ابتدا شروع می‌کند'),at(3),s=>{s.c2=[...s.msgs];s.stage=4;say(s,s.c2.length?'Consumer 2 replayed the history from offset 0.':'Consumer 2 got nothing: the messages were deleted after the first ack.',s.c2.length?'مصرف‌کنندهٔ ۲ تاریخچه را از offset صفر بازپخش کرد.':'مصرف‌کنندهٔ ۲ چیزی نگرفت؛ پیام‌ها پس از ack اول حذف شده بودند.',0,2);})
    ],s=>[`${s.kind||'?'}: [${s.msgs}]`,`[${s.c1}]`,`[${s.c2}]`]);

  add('unique',B('Two people claim the same username', 'دو نفر یک نام کاربری را می‌گیرند'),
    B('Choose how requests are routed, send two claims for alice at once, then process them.', 'مسیر درخواست‌ها را انتخاب کن، دو درخواست همزمان برای alice بفرست و پردازششان کن.'),
    B('Independent services each check their own view and see alice as free. A log partitioned by username puts both claims in one order.', 'سرویس‌های مستقل هر کدام نمای خود را بررسی می‌کنند و alice را آزاد می‌بینند. log پارتیشن‌شده با username هر دو درخواست را در یک ترتیب واحد می‌گذارد.'),
    [B('Claim 1', 'درخواست ۱'),B('Claim 2', 'درخواست ۲'),B('Outcome', 'نتیجه')],
    ()=>({route:null,sent:false,results:[]}),[
      A('split',B('Each service checks its own copy', 'هر سرویس نمای خودش را بررسی می‌کند'),at(0),s=>{s.route='split';s.stage=1;say(s,'No shared order for the two claims.','برای دو درخواست ترتیب مشترکی نیست.');}),
      A('partition',B('Partition the log by username', 'پارتیشن‌بندی log با username'),at(0),s=>{s.route='partition';s.stage=1;say(s,'Both claims go to the same partition.','هر دو درخواست به یک پارتیشن می‌روند.');}),
      A('send',B('Send both claims', 'ارسال هر دو درخواست'),at(1),s=>{s.sent=true;s.stage=2;say(s,'Both claims are in flight.','هر دو درخواست در راه هستند.',0,1);}),
      A('process',B('Process', 'پردازش'),at(2),s=>{s.results=s.route==='split'?['accepted','accepted']:['accepted','rejected'];s.stage=3;say(s,s.route==='split'?'Both succeeded: the uniqueness rule broke.':'The second claim saw the first and was rejected.',s.route==='split'?'هر دو موفق شدند و یکتایی نقض شد.':'درخواست دوم اولی را دید و رد شد.',1,2);})
    ],s=>[s.sent?'claim alice':'∅',s.sent?'claim alice':'∅',s.results.length?s.results.join(' / '):'∅']);

  add('feedback',B('Patrols follow the data they create', 'گشت‌ها دادهٔ خودشان را می‌سازند'),
    B('Two districts have the same real crime. Choose the patrol policy and run two rounds.', 'دو منطقه جرم واقعی یکسان دارند. سیاست گشت را انتخاب کن و دو دور اجرا کن.'),
    B('Recorded incidents start at A=6, B=5, while real crime is equal. You only record what you patrol. The top policy patrols the higher count; the audit policy splits patrols.', 'رخدادهای ثبت‌شده با A=۶ و B=۵ شروع می‌شوند ولی جرم واقعی برابر است. فقط جایی را ثبت می‌کنی که گشت می‌زنی. سیاست top به منطقهٔ پرشمارتر می‌رود و audit گشت را تقسیم می‌کند.'),
    [B('Recorded incidents', 'رخدادهای ثبت‌شده'),B('Policy', 'سیاست'),B('Real crime', 'جرم واقعی')],
    ()=>({policy:null,rec:[6,5],round:0}),[
      A('top',B('Patrol the higher count', 'گشت در منطقهٔ پرشمارتر'),at(0),s=>{s.policy='top';s.stage=1;say(s,'All patrols go where the data is highest.','همهٔ گشت‌ها به جایی می‌روند که داده بیشتر است.');}),
      A('audit',B('Split patrols evenly', 'تقسیم برابر گشت'),at(0),s=>{s.policy='audit';s.stage=1;say(s,'Both districts get coverage.','هر دو منطقه پوشش می‌گیرند.');}),
      A('round',B('Run a round', 'اجرای یک دور'),s=>s.stage>=1&&s.stage<3,s=>{if(s.policy==='top'){s.rec[s.rec[0]>=s.rec[1]?0:1]+=5;}else{s.rec[0]+=3;s.rec[1]+=3;}s.round++;s.stage++;say(s,`Recorded A=${s.rec[0]}, B=${s.rec[1]}; real crime is still equal.`,`ثبت‌شده A=${s.rec[0]} و B=${s.rec[1]}؛ جرم واقعی هنوز برابر است.`,0,1);})
    ],s=>[`A=${s.rec[0]}  B=${s.rec[1]}`,`${s.policy||'?'}\nround=${s.round}`,'A=5  B=5']);


  add('rpc',B('A call that can disappear', 'فراخوانی که می‌تواند گم شود'),
    B('Call the same function in-process, then as a remote service, and let something fail.', 'یک تابع را یک بار داخل همان پردازش و یک بار از راه شبکه صدا بزن و بگذار چیزی خراب شود.'),
    B('An in-process call fails together with its caller. A network call can fail between the two machines, leaving the caller without knowing whether the work happened.', 'فراخوانی درون‌پردازشی همراه فراخواننده می‌شکند. فراخوانی شبکه‌ای بین دو ماشین می‌تواند خراب شود و فراخواننده نمی‌داند کار انجام شده یا نه.'),
    [B('Caller', 'فراخواننده'),B('Call path', 'مسیر فراخوانی'),B('Callee', 'فراخوانده')],
    ()=>({mode:null,outcome:null,done:false}),[
      A('local',B('In-process call', 'فراخوانی داخل پردازش'),at(0),s=>{s.mode='local';s.stage=1;say(s,'Caller and callee share one process.','فراخواننده و فراخوانده یک پردازش مشترک دارند.');}),
      A('remote',B('Remote call over the network', 'فراخوانی از راه شبکه'),at(0),s=>{s.mode='remote';s.stage=1;say(s,'Caller and callee run on different machines.','فراخواننده و فراخوانده روی دو ماشین جدا هستند.');}),
      A('call',B('Call charge(10)', 'صدا زدن charge(10)'),at(1),s=>{s.done=true;s.outcome='ok';s.stage=2;say(s,'The call succeeded.','فراخوانی موفق شد.',0,2);}),
      A('fail',B('Break something during the call', 'خراب‌کردن چیزی هنگام فراخوانی'),at(2),s=>{s.outcome=s.mode==='local'?'both crashed together':'timeout: did it run?';s.stage=3;say(s,s.mode==='local'?'Caller and callee died together, so there is no doubt about the state.':'The reply was lost. The work may or may not have happened: the caller cannot tell.',s.mode==='local'?'هر دو با هم مردند و در وضعیت ابهامی نیست.':'پاسخ گم شد. کار شاید انجام شده باشد و شاید نه؛ فراخواننده نمی‌داند.',1,0);})
    ],s=>['charge(10)',`path=${s.mode||'?'}`,`work=${s.done?'ran':'—'}\nresult=${s.outcome||'∅'}`]);

  add('tail',B('The average hides the slow user', 'میانگین کاربر کند را پنهان می‌کند'),
    B('Ten requests: nine take 100 ms and one takes 1000 ms. Pick the metric you alert on.', 'ده درخواست: نُه تا ۱۰۰ میلی‌ثانیه و یکی ۱۰۰۰ میلی‌ثانیه. معیار هشدار را انتخاب کن.'),
    B('Mean = 190 ms; the 99th percentile (nearest rank) = 1000 ms. The alert threshold is 500 ms.', 'میانگین ۱۹۰ میلی‌ثانیه و صدک ۹۹ (نزدیک‌ترین رتبه) ۱۰۰۰ میلی‌ثانیه است. آستانهٔ هشدار ۵۰۰ میلی‌ثانیه.'),
    [B('Requests', 'درخواست‌ها'),B('Metric', 'معیار'),B('Alert', 'هشدار')],
    ()=>({metric:null,value:null,alert:null}),[
      A('mean',B('Alert on the mean', 'هشدار روی میانگین'),at(0),s=>{s.metric='mean';s.stage=1;say(s,'We watch the average latency.','میانگین تأخیر را زیر نظر می‌گیریم.');}),
      A('p99',B('Alert on p99', 'هشدار روی p99'),at(0),s=>{s.metric='p99';s.stage=1;say(s,'We watch the slowest 1%.','کندترین ۱٪ را زیر نظر می‌گیریم.');}),
      A('measure',B('Measure the ten requests', 'اندازه‌گیری ده درخواست'),at(1),s=>{s.value=s.metric==='mean'?190:1000;s.stage=2;say(s,`The ${s.metric} is ${s.value} ms.`,`${s.metric} برابر ${s.value} میلی‌ثانیه است.`,0,1);}),
      A('alert',B('Check the 500 ms threshold', 'بررسی آستانهٔ ۵۰۰'),at(2),s=>{s.alert=s.value>500;s.stage=3;say(s,s.alert?'Alert fires: someone waited a full second.':'No alert, yet one user waited ten times longer than the rest.',s.alert?'هشدار فعال شد؛ یک نفر یک ثانیهٔ کامل منتظر ماند.':'هشداری نیست ولی یک کاربر ده برابر بقیه منتظر ماند.',1,2);})
    ],s=>['9 × 100 ms\n1 × 1000 ms',`${s.metric||'?'} = ${s.value??'∅'} ms`,`alert=${s.alert===null?'∅':s.alert}`]);

  add('hops',B('Friends of friends of friends', 'دوستِ دوستِ دوست'),
    B('Choose join tables or a graph model, then ask for connections two hops away and then any number of hops.', 'جدول join یا مدل گراف را انتخاب کن و بعد ارتباط دو گام دورتر و سپس هر تعداد گام را بپرس.'),
    B('A fixed hop count in SQL is a fixed number of joins. An unknown number of hops needs a recursive query; a graph engine has a native variable-length pattern.', 'تعداد گام ثابت در SQL تعداد ثابتی join است. تعداد گام نامعلوم به پرس‌وجوی بازگشتی نیاز دارد؛ موتور گراف الگوی طول متغیر دارد.'),
    [B('Question', 'پرسش'),B('Storage', 'ذخیره‌سازی'),B('Query shape', 'شکل پرس‌وجو')],
    ()=>({model:null,q:null,shape:null}),[
      A('tables',B('Relational join table', 'جدول رابطه‌ای'),at(0),s=>{s.model='tables';s.stage=1;say(s,'Friendships are rows in a join table.','دوستی‌ها ردیف‌های یک جدول join هستند.');}),
      A('graph',B('Graph model', 'مدل گراف'),at(0),s=>{s.model='graph';s.stage=1;say(s,'People are vertices and friendships are edges.','آدم‌ها رأس و دوستی‌ها یال هستند.');}),
      A('two',B('Exactly 2 hops away', 'دقیقاً ۲ گام دورتر'),at(1),s=>{s.q='2 hops';s.shape=s.model==='tables'?'2 self-joins':'(a)-[:FRIEND*2]->(b)';s.stage=2;say(s,'A fixed depth is easy in both.','عمق ثابت در هر دو آسان است.',0,2);}),
      A('any',B('Any number of hops', 'هر تعداد گام'),at(2),s=>{s.q='any hops';s.shape=s.model==='tables'?'WITH RECURSIVE …':'(a)-[:FRIEND*]->(b)';s.stage=3;say(s,s.model==='tables'?'The depth is unknown, so the query must be recursive: it can no longer be a fixed set of joins.':'The pattern simply states variable length.',s.model==='tables'?'عمق نامعلوم است، پس پرس‌وجو باید بازگشتی باشد و دیگر مجموعهٔ ثابتی از join نیست.':'الگو فقط طول متغیر را می‌گوید.',1,2);})
    ],s=>[s.q||'∅',`model=${s.model||'?'}`,s.shape||'∅']);

  add('btree',B('A page split meets a crash', 'شکستن صفحه و خرابی'),
    B('Insert key 25 into a full page, crash halfway through the split, and recover with or without a WAL.', 'کلید ۲۵ را در صفحهٔ پر وارد کن، وسط شکستن صفحه خرابی ایجاد کن و با WAL یا بدون آن بازیابی کن.'),
    B('The page holds 3 keys. A split writes two leaf pages and then updates the parent. Without a log, a crash between them leaves one page unreachable.', 'ظرفیت صفحه ۳ کلید است. split دو صفحهٔ برگ می‌نویسد و بعد والد را به‌روز می‌کند. بدون لاگ، خرابی بین این دو یک صفحه را غیرقابل‌دسترس می‌کند.'),
    [B('Leaf pages', 'صفحه‌های برگ'),B('Parent page', 'صفحهٔ والد'),B('Lookup of 25', 'جست‌وجوی ۲۵')],
    ()=>({wal:null,pages:['10 20 30'],parent:'—',down:false,found:null}),[
      A('wal',B('Write-ahead log on', 'WAL فعال'),at(0),s=>{s.wal=true;s.stage=1;say(s,'Intended page changes are logged first.','تغییر قصدشده ابتدا در لاگ می‌آید.');}),
      A('nowal',B('No log', 'بدون لاگ'),at(0),s=>{s.wal=false;s.stage=1;say(s,'Pages are overwritten in place.','صفحه‌ها در جا بازنویسی می‌شوند.');}),
      A('insert',B('Insert 25 (split the page)', 'وارد کردن ۲۵ (split)'),at(1),s=>{s.pages=['10 20','25 30'];s.stage=2;say(s,'Both leaves are written; the parent has not been updated yet.','هر دو برگ نوشته شد؛ والد هنوز به‌روز نشده است.',0,1);}),
      A('crash',B('Crash before the parent is updated', 'خرابی پیش از به‌روزرسانی والد'),at(2),s=>{s.down=true;s.stage=3;say(s,'The process stopped mid-split.','پردازش وسط split متوقف شد.',1,1);}),
      A('recover',B('Restart and look up 25', 'راه‌اندازی و جست‌وجوی ۲۵'),at(3),s=>{s.down=false;if(s.wal){s.parent='25 → page 2';s.found=true;}else{s.found=false;}s.stage=4;say(s,s.found?'The log was replayed, the parent now points to the new page and 25 is found.':'The parent never learned about the new page: key 25 is unreachable, the tree is corrupt.',s.found?'لاگ بازپخش شد، والد به صفحهٔ جدید اشاره می‌کند و ۲۵ پیدا می‌شود.':'والد از صفحهٔ جدید خبردار نشد؛ کلید ۲۵ در دسترس نیست و درخت خراب است.',1,2);})
    ],s=>[s.pages.join('\n'),`${s.parent}${s.down?'\nprocess=down':''}`,s.found===null?'∅':(s.found?'found':'NOT FOUND')]);

  add('rename',B('Rename a field with old readers still running', 'تغییر نام فیلد وقتی خوانندهٔ قدیمی هنوز کار می‌کند'),
    B('Choose how fields are identified on the wire, rename name to full_name, then read with an old service.', 'نحوهٔ شناسایی فیلدها روی سیم را انتخاب کن، name را به full_name تغییر بده و با سرویس قدیمی بخوان.'),
    B('By-name encodings carry the field name. Tag-based encodings carry a number, so the name in the schema can change without changing the bytes.', 'کدگذاری بر اساس نام، نام فیلد را حمل می‌کند. کدگذاری بر اساس tag عدد حمل می‌کند؛ پس نام در schema بدون تغییر بایت‌ها عوض می‌شود.'),
    [B('New writer', 'نویسندهٔ جدید'),B('On the wire', 'روی سیم'),B('Old reader result', 'نتیجهٔ خوانندهٔ قدیمی')],
    ()=>({fmt:null,wire:'name: Mina',read:null}),[
      A('byname',B('Fields identified by name', 'شناسایی با نام'),at(0),s=>{s.fmt='name';s.wire='name: Mina';s.stage=1;say(s,'Bytes contain the field name.','بایت‌ها نام فیلد را دارند.');}),
      A('bytag',B('Fields identified by tag number', 'شناسایی با شمارهٔ tag'),at(0),s=>{s.fmt='tag';s.wire='1: Mina';s.stage=1;say(s,'Bytes contain tag 1; the name lives only in the schema.','بایت‌ها tag شمارهٔ ۱ را دارند؛ نام فقط در schema است.');}),
      A('rename',B('Rename name → full_name', 'تغییر name به full_name'),at(1),s=>{s.wire=s.fmt==='name'?'full_name: Mina':'1: Mina';s.stage=2;say(s,s.fmt==='name'?'The wire now says full_name.':'The wire is unchanged: tag 1 still means the same field.',s.fmt==='name'?'روی سیم حالا full_name است.':'روی سیم تغییری نکرد؛ tag ۱ هنوز همان فیلد است.',0,1);}),
      A('old',B('Old service reads the record', 'سرویس قدیمی رکورد را می‌خواند'),at(2),s=>{s.read=s.fmt==='name'?'name = ∅ (missing)':'name = Mina';s.stage=3;say(s,s.fmt==='name'?'The old reader looks for name and finds nothing.':'The old reader still finds its field by number.',s.fmt==='name'?'خوانندهٔ قدیمی دنبال name می‌گردد و چیزی نمی‌یابد.':'خوانندهٔ قدیمی فیلدش را هنوز با شماره پیدا می‌کند.',1,2);})
    ],s=>[`format=${s.fmt||'?'}`,s.wire,s.read||'∅']);

  add('secondary',B('Search by color across shards', 'جست‌وجو بر اساس رنگ در بین شاردها'),
    B('Choose a local or a global secondary index, write a red item, then search for red items.', 'ایندکس ثانویهٔ محلی یا سراسری را انتخاب کن، یک آیتم قرمز بنویس و بعد قرمزها را جست‌وجو کن.'),
    B('Three shards. A local index covers only its own shard, so a search must ask every shard. A global index is partitioned by term and lives on another shard, so one search asks one place but each write touches two shards.', 'سه شارد. ایندکس محلی فقط شارد خودش را می‌پوشاند و جست‌وجو باید از همهٔ شاردها بپرسد. ایندکس سراسری بر اساس term پارتیشن شده و روی شارد دیگری است؛ جست‌وجو یک جا می‌پرسد ولی هر نوشتن دو شارد را درگیر می‌کند.'),
    [B('Shard 1', 'شارد ۱'),B('Shard 2', 'شارد ۲'),B('Shard 3', 'شارد ۳')],
    ()=>({kind:null,writes:0,asked:0}),[
      A('local',B('Local index per shard', 'ایندکس محلی هر شارد'),at(0),s=>{s.kind='local';s.stage=1;say(s,'Each shard indexes only its own rows.','هر شارد فقط ردیف‌های خودش را ایندکس می‌کند.');}),
      A('global',B('Global index by term', 'ایندکس سراسری بر اساس term'),at(0),s=>{s.kind='global';s.stage=1;say(s,'The term red is owned by shard 3.','term قرمز مال شارد ۳ است.');}),
      A('write',B('Write a red item on shard 1', 'نوشتن آیتم قرمز روی شارد ۱'),at(1),s=>{s.writes=s.kind==='local'?1:2;s.stage=2;say(s,`The write touched ${s.writes} shard(s).`,`این نوشتن ${s.writes} شارد را درگیر کرد.`,0,1);}),
      A('search',B('Search for red items', 'جست‌وجوی قرمزها'),at(2),s=>{s.asked=s.kind==='local'?3:1;s.stage=3;say(s,`The search contacted ${s.asked} shard(s)${s.kind==='local'?': one slow shard slows the whole search.':'.'}`,`جست‌وجو با ${s.asked} شارد تماس گرفت${s.kind==='local'?'؛ یک شارد کند کل جست‌وجو را کند می‌کند.':'.'}`,1,2);})
    ],s=>[`index=${s.kind||'?'}\nitem written here=${s.writes?'yes':'no'}`,`index entry=${s.kind==='global'&&s.writes?'no':'—'}`,`index owner=${s.kind==='global'?'yes: red':'—'}\nwrites=${s.writes}\nasked=${s.asked}`]);

  add('twopc',B('The coordinator dies after prepare', 'هماهنگ‌کننده بعد از prepare می‌میرد'),
    B('Both participants vote yes, then the coordinator crashes. Decide whether it logged its decision first.', 'هر دو شرکت‌کننده بله می‌گویند، بعد هماهنگ‌کننده خراب می‌شود. تصمیم بگیر ابتدا تصمیمش را ثبت کرده باشد یا نه.'),
    B('After voting yes a participant must wait for the coordinator: it cannot commit or abort alone. A durable decision log lets a restarted coordinator finish the job.', 'شرکت‌کننده بعد از رأی بله باید منتظر هماهنگ‌کننده بماند و تنها نمی‌تواند commit یا abort کند. لاگ پایدار تصمیم اجازه می‌دهد هماهنگ‌کنندهٔ راه‌اندازی‌شده کار را تمام کند.'),
    [B('Coordinator', 'هماهنگ‌کننده'),B('Participant A', 'شرکت‌کنندهٔ A'),B('Participant B', 'شرکت‌کنندهٔ B')],
    ()=>({durable:null,coord:'idle',a:'working',b:'working',locks:false}),[
      A('durable',B('Decision log is durable', 'لاگ تصمیم پایدار است'),at(0),s=>{s.durable=true;s.stage=1;say(s,'The decision will be written to disk before it is sent.','تصمیم پیش از ارسال روی دیسک نوشته می‌شود.');}),
      A('volatile',B('Decision only in memory', 'تصمیم فقط در حافظه'),at(0),s=>{s.durable=false;s.stage=1;say(s,'The decision lives only in RAM.','تصمیم فقط در RAM است.');}),
      A('prepare',B('Prepare: both vote yes', 'prepare: هر دو بله می‌گویند'),at(1),s=>{s.coord='decided commit';s.a=s.b='prepared';s.locks=true;s.stage=2;say(s,'Both hold locks and wait for the verdict.','هر دو قفل را نگه داشته و منتظر حکم‌اند.',0,1);}),
      A('crash',B('Coordinator crashes', 'خرابی هماهنگ‌کننده'),at(2),s=>{s.coord='down';s.stage=3;say(s,'The participants hear nothing. They are in doubt and keep their locks.','شرکت‌کننده‌ها خبری نمی‌شنوند؛ در ابهام‌اند و قفل‌ها را نگه می‌دارند.',0,0);}),
      A('restart',B('Restart the coordinator', 'راه‌اندازی هماهنگ‌کننده'),at(3),s=>{if(s.durable){s.coord='commit sent';s.a=s.b='committed';s.locks=false;}else{s.coord='decision lost';}s.stage=4;say(s,s.durable?'The log supplied the decision; both committed and released their locks.':'The decision is gone. The prepared participants stay blocked until an operator intervenes.',s.durable?'لاگ تصمیم را داد؛ هر دو commit و قفل‌ها آزاد شدند.':'تصمیم از بین رفته. شرکت‌کننده‌ها تا دخالت اپراتور مسدود می‌مانند.',0,2);})
    ],s=>[s.coord,`${s.a}\nlocks=${s.locks}`,`${s.b}\nlocks=${s.locks}`]);

  add('timeout',B('Slow or dead?', 'کند است یا مرده؟'),
    B('Pick a failure-detection timeout, let the node stall for 3 seconds, then let it really crash.', 'timeout تشخیص خرابی را انتخاب کن، بگذار گره ۳ ثانیه متوقف شود و بعد واقعاً خراب شود.'),
    B('The monitor cannot tell a stalled node from a dead one; it only sees silence. A short timeout reacts fast but misjudges stalls; a long one is accurate but slow.', 'پایشگر گرهٔ متوقف را از گرهٔ مرده تشخیص نمی‌دهد و فقط سکوت می‌بیند. timeout کوتاه سریع است ولی توقف را اشتباه می‌فهمد؛ بلند دقیق ولی کند است.'),
    [B('Monitor', 'پایشگر'),B('Node', 'گره'),B('Verdict', 'حکم')],
    ()=>({timeout:null,node:'up',verdict:'—',outage:0}),[
      A('short',B('Timeout 1 s', 'timeout یک ثانیه'),at(0),s=>{s.timeout=1;s.stage=1;say(s,'Silence for 1 second means dead.','یک ثانیه سکوت یعنی مرده.');}),
      A('long',B('Timeout 10 s', 'timeout ده ثانیه'),at(0),s=>{s.timeout=10;s.stage=1;say(s,'Silence for 10 seconds means dead.','ده ثانیه سکوت یعنی مرده.');}),
      A('stall',B('Node stalls for 3 s (GC pause)', 'گره ۳ ثانیه متوقف می‌شود'),at(1),s=>{s.node='stalled';s.verdict=s.timeout<3?'declared dead (wrongly)':'still alive';s.stage=2;say(s,s.timeout<3?'False alarm: failover starts for a node that was only paused, and it may wake up thinking it is the leader.':'The monitor waited out the pause; nothing happened.',s.timeout<3?'هشدار غلط: failover برای گرهی شروع می‌شود که فقط متوقف بود و ممکن است بیدار شود و خود را رهبر بداند.':'پایشگر توقف را تحمل کرد و اتفاقی نیفتاد.',1,0);}),
      A('crash',B('Node really crashes', 'گره واقعاً خراب می‌شود'),at(2),s=>{s.node='dead';s.outage=s.timeout;s.verdict='declared dead (correctly)';s.stage=3;say(s,`Detected after ${s.timeout} s: that is how long clients were failing.`,`پس از ${s.timeout} ثانیه تشخیص داده شد؛ مشتری‌ها به همین مدت خطا می‌دیدند.`,1,0);})
    ],s=>[`timeout=${s.timeout??'?'} s`,`node=${s.node}`,`${s.verdict}\nunnoticed outage=${s.outage} s`]);

  add('ephemeral',B('The lock holder disappears', 'دارندهٔ قفل ناپدید می‌شود'),
    B('Client A takes a lock and crashes. Choose whether the lock is tied to a session.', 'کلاینت A قفل را می‌گیرد و خراب می‌شود. انتخاب کن قفل به یک session وابسته باشد یا نه.'),
    B('An ephemeral lock disappears when its owner session times out. A plain key stays until someone deletes it.', 'قفل ephemeral وقتی session صاحبش timeout شود حذف می‌شود. کلید ساده می‌ماند تا کسی آن را حذف کند.'),
    [B('Lock service', 'سرویس قفل'),B('Client A', 'کلاینت A'),B('Client B', 'کلاینت B')],
    ()=>({kind:null,owner:'free',a:'idle',b:'idle',time:0}),[
      A('session',B('Ephemeral lock with a session', 'قفل ephemeral با session'),at(0),s=>{s.kind='session';s.stage=1;say(s,'The lock lives as long as the client session.','قفل تا زمانی که session کلاینت زنده است می‌ماند.');}),
      A('plain',B('Plain lock key', 'کلید ساده'),at(0),s=>{s.kind='plain';s.stage=1;say(s,'The lock stays until deleted.','قفل تا حذف‌شدن می‌ماند.');}),
      A('acquire',B('A acquires the lock', 'A قفل را می‌گیرد'),at(1),s=>{s.owner='A';s.a='holding';s.stage=2;say(s,'A is working inside the critical section.','A داخل بخش بحرانی کار می‌کند.',1,0);}),
      A('crash',B('A crashes; B tries to lock', 'A خراب می‌شود؛ B تلاش می‌کند'),at(2),s=>{s.a='dead';s.b='blocked';s.stage=3;say(s,'B is refused: the service still lists A as the owner.','B رد می‌شود؛ سرویس هنوز A را صاحب قفل می‌داند.',2,0);}),
      A('wait',B('30 seconds pass', '۳۰ ثانیه می‌گذرد'),at(3),s=>{s.time=30;if(s.kind==='session'){s.owner='B';s.b='holding';}s.stage=4;say(s,s.kind==='session'?'A session expired, its lock vanished and B took over.':'Nobody releases a plain key: B waits forever. The system is stuck.',s.kind==='session'?'session A منقضی شد، قفلش حذف شد و B آن را گرفت.':'هیچ‌کس کلید ساده را آزاد نمی‌کند؛ B تا ابد منتظر می‌ماند و سیستم گیر می‌کند.',0,2);})
    ],s=>[`owner=${s.owner}\ntime=${s.time} s`,s.a,s.b]);

  add('rerun',B('Rerun a job whose input moved', 'اجرای دوبارهٔ کاری که ورودی‌اش تغییر کرد'),
    B('A job crashes at the end of its first attempt. Meanwhile a new record arrives. Retry and compare.', 'یک کار در پایان تلاش اول خراب می‌شود. در همین حال رکورد تازه‌ای می‌رسد. دوباره اجرا کن و مقایسه کن.'),
    B('The first attempt counted 3 records. If the input is an immutable snapshot, a retry sees the same 3. If the file is edited in place, the retry may see 4.', 'تلاش اول ۳ رکورد را شمرد. اگر ورودی snapshot تغییرناپذیر باشد، تلاش دوباره همان ۳ را می‌بیند. اگر فایل در جا ویرایش شود، ممکن است ۴ ببیند.'),
    [B('Input', 'ورودی'),B('Attempts', 'تلاش‌ها'),B('Output', 'خروجی')],
    ()=>({kind:null,input:3,first:null,out:null}),[
      A('immutable',B('Immutable snapshot', 'snapshot تغییرناپذیر'),at(0),s=>{s.kind='immutable';s.stage=1;say(s,'The job reads a fixed snapshot of the input.','کار یک snapshot ثابت از ورودی را می‌خواند.');}),
      A('mutable',B('File edited in place', 'فایل در جا ویرایش می‌شود'),at(0),s=>{s.kind='mutable';s.stage=1;say(s,'The job reads whatever the file holds right now.','کار آنچه را فایل الان دارد می‌خواند.');}),
      A('run',B('Attempt 1 counts, then crashes', 'تلاش ۱ می‌شمارد و خراب می‌شود'),at(1),s=>{s.first=3;s.stage=2;say(s,'Attempt 1 counted 3 but crashed before publishing.','تلاش ۱ عدد ۳ را شمرد ولی پیش از انتشار خراب شد.',0,1);}),
      A('append',B('A new record is appended', 'رکورد تازه اضافه می‌شود'),at(2),s=>{if(s.kind==='mutable')s.input=4;s.stage=3;say(s,s.kind==='mutable'?'The file now holds 4 records.':'The new record goes to a new file; the snapshot is untouched.',s.kind==='mutable'?'فایل حالا ۴ رکورد دارد.':'رکورد جدید در فایل تازه می‌رود و snapshot دست‌نخورده است.',0,0);}),
      A('retry',B('Retry', 'اجرای دوباره'),at(3),s=>{s.out=s.input;s.stage=4;say(s,s.out===s.first?'The retry produced exactly what attempt 1 would have: reruns are safe.':'The retry says 4 while attempt 1 said 3: the result depends on when you ran it.',s.out===s.first?'اجرای دوباره دقیقاً همان نتیجهٔ تلاش ۱ را داد؛ بازاجرا امن است.':'اجرای دوباره ۴ می‌گوید ولی تلاش ۱ می‌گفت ۳؛ نتیجه به زمان اجرا بستگی دارد.',1,2);})
    ],s=>[`records=${s.input}\n${s.kind||'?'}`,`attempt 1 counted=${s.first??'∅'}`,`output=${s.out??'∅'}`]);

  add('ordering',B('Create then delete, seen backwards', 'ساخت و بعد حذف، معکوس دیده می‌شود'),
    B('Send create(u1) and delete(u1) and choose how events are assigned to partitions.', 'create(u1) و delete(u1) را بفرست و انتخاب کن رویدادها چگونه به پارتیشن‌ها بروند.'),
    B('A log keeps order only inside one partition. Round-robin spreads one entity over partitions; key-based routing keeps it in one.', 'log فقط داخل یک پارتیشن ترتیب را نگه می‌دارد. round-robin یک موجودیت را بین پارتیشن‌ها پخش می‌کند و مسیریابی با کلید آن را در یک پارتیشن نگه می‌دارد.'),
    [B('Producer', 'تولیدکننده'),B('Partitions', 'پارتیشن‌ها'),B('Consumer sees', 'مصرف‌کننده می‌بیند')],
    ()=>({mode:null,p0:[],p1:[],seen:[]}),[
      A('rr',B('Round-robin partitioning', 'پارتیشن‌بندی round-robin'),at(0),s=>{s.mode='rr';s.stage=1;say(s,'Each event goes to the next partition.','هر رویداد به پارتیشن بعدی می‌رود.');}),
      A('key',B('Partition by user key', 'پارتیشن‌بندی با کلید کاربر'),at(0),s=>{s.mode='key';s.stage=1;say(s,'All events of u1 go to the same partition.','همهٔ رویدادهای u1 به یک پارتیشن می‌روند.');}),
      A('send',B('Send create then delete', 'ارسال create و بعد delete'),at(1),s=>{s.p0=['create u1'];s.p1=s.mode==='rr'?['delete u1']:[];if(s.mode==='key')s.p0.push('delete u1');s.stage=2;say(s,'Both events are stored.','هر دو رویداد ذخیره شد.',0,1);}),
      A('read',B('Consumer reads; partition 1 is faster', 'مصرف‌کننده می‌خواند؛ پارتیشن ۱ سریع‌تر است'),at(2),s=>{s.seen=s.mode==='rr'?['delete u1','create u1']:['create u1','delete u1'];s.stage=3;say(s,s.mode==='rr'?'The consumer saw delete before create: the deleted user is resurrected downstream.':'The order is preserved: the user ends deleted.',s.mode==='rr'?'مصرف‌کننده delete را قبل از create دید؛ کاربر حذف‌شده پایین‌دست زنده می‌شود.':'ترتیب حفظ شد؛ کاربر در نهایت حذف است.',1,2);})
    ],s=>[`mode=${s.mode||'?'}`,`p0: ${s.p0.join(', ')||'∅'}\np1: ${s.p1.join(', ')||'∅'}`,s.seen.length?s.seen.join('\n→ '):'∅']);

  add('reconcile',B('A late event after the window closed', 'رویداد دیررسیده بعد از بسته‌شدن پنجره'),
    B('A stream counts 10 events live, then 2 late ones arrive. Choose whether a batch job corrects the count.', 'یک stream ده رویداد را زنده می‌شمارد و بعد ۲ رویداد دیررس می‌رسد. انتخاب کن یک batch آن را اصلاح کند یا نه.'),
    B('The stream closed its window and drops late events. A nightly batch recomputes from the full log and replaces the served value.', 'stream پنجره را بسته و رویداد دیررس را کنار می‌گذارد. batch شبانه از لاگ کامل دوباره حساب می‌کند و مقدار نمایش‌داده‌شده را عوض می‌کند.'),
    [B('Stream layer', 'لایهٔ stream'),B('Batch layer', 'لایهٔ batch'),B('Served total', 'مجموع نمایش‌داده‌شده')],
    ()=>({both:null,stream:0,late:0,batch:null}),[
      A('streamonly',B('Stream only', 'فقط stream'),at(0),s=>{s.both=false;s.stage=1;say(s,'The stream is the only computation.','stream تنها محاسبه است.');}),
      A('both',B('Stream plus nightly batch', 'stream و batch شبانه'),at(0),s=>{s.both=true;s.stage=1;say(s,'A batch job can recompute from the full log.','batch می‌تواند از لاگ کامل دوباره حساب کند.');}),
      A('live',B('10 events arrive live', 'ده رویداد زنده می‌رسد'),at(1),s=>{s.stream=10;s.stage=2;say(s,'The stream shows 10.','stream عدد ۱۰ را نشان می‌دهد.',0,2);}),
      A('late',B('2 late events arrive', 'دو رویداد دیررس می‌رسد'),at(2),s=>{s.late=2;s.stage=3;say(s,'The window already closed: the stream ignores them, though the log keeps them.','پنجره بسته شده؛ stream آن‌ها را نادیده می‌گیرد ولی لاگ نگهشان می‌دارد.',0,0);}),
      A('night',B('The night passes', 'شب می‌گذرد'),at(3),s=>{if(s.both)s.batch=s.stream+s.late;s.stage=4;say(s,s.both?'The batch recounted from the log: 12. The served value was corrected.':'Nothing recomputes: the dashboard stays at 10 although 12 events happened.',s.both?'batch از لاگ دوباره شمرد: ۱۲. مقدار نمایش‌داده‌شده اصلاح شد.':'چیزی دوباره حساب نمی‌شود؛ داشبورد روی ۱۰ می‌ماند با اینکه ۱۲ رویداد رخ داده.',1,2);})
    ],s=>[`counted=${s.stream}\nlate dropped=${s.late}`,s.batch===null?'∅':`recount=${s.batch}`,`served=${s.batch??s.stream}`]);

  add('proxy',B('No protected attribute, still biased', 'بدون ویژگی حفاظت‌شده هم سوگیری هست'),
    B('Remove the protected attribute from a lending model, train it, then try to measure fairness.', 'ویژگی حفاظت‌شده را از مدل وام حذف کن، مدل را آموزش بده و بعد انصاف را اندازه بگیر.'),
    B('Postcode correlates with group membership, so the model reconstructs it. Group labels kept only for auditing let you see the gap and correct for it.', 'کد پستی با عضویت گروه هم‌بسته است؛ پس مدل آن را بازسازی می‌کند. برچسب گروه که فقط برای ممیزی نگه داشته شود، فاصله را نشان می‌دهد و اصلاحش ممکن می‌کند.'),
    [B('Training data', 'داده آموزش'),B('Model', 'مدل'),B('Acceptance by group', 'پذیرش به تفکیک گروه')],
    ()=>({keep:null,model:null,rates:null,fixed:false}),[
      A('drop',B('Delete the group column everywhere', 'حذف ستون گروه از همه‌جا'),at(0),s=>{s.keep=false;s.stage=1;say(s,'No group labels exist anywhere.','هیچ‌جا برچسب گروه وجود ندارد.');}),
      A('audit',B('Remove it from the model, keep it for audit', 'حذف از مدل و نگه‌داری برای ممیزی'),at(0),s=>{s.keep=true;s.stage=1;say(s,'The model never sees it; the audit table does.','مدل آن را نمی‌بیند ولی جدول ممیزی دارد.');}),
      A('train',B('Train using postcode and income', 'آموزش با کد پستی و درآمد'),at(1),s=>{s.model='uses postcode';s.stage=2;say(s,'Postcode carries most of what the group column carried.','کد پستی بیشتر آنچه ستون گروه داشت را حمل می‌کند.',0,1);}),
      A('measure',B('Measure acceptance by group', 'اندازه‌گیری پذیرش هر گروه'),at(2),s=>{s.rates=s.keep?'A 70%  B 40%':'cannot split by group';s.stage=3;say(s,s.keep?'The audit table shows a 30-point gap.':'Without labels you can only see one overall number: the gap is invisible.',s.keep?'جدول ممیزی ۳۰ واحد فاصله نشان می‌دهد.':'بدون برچسب فقط یک عدد کلی می‌بینی و فاصله دیده نمی‌شود.',1,2);}),
      A('fix',B('Adjust thresholds per audit result', 'تنظیم آستانه‌ها با نتیجهٔ ممیزی'),s=>s.stage===3&&s.keep,s=>{s.fixed=true;s.rates='A 60%  B 55%';s.stage=4;say(s,'The gap shrank to 5 points, and you can show the evidence.','فاصله به ۵ واحد رسید و می‌توانی شواهدش را نشان دهی.',1,2);}),
      A('ship',B('Ship it', 'انتشار مدل'),s=>s.stage===3&&!s.keep,s=>{s.stage=4;say(s,'The model ships. The unfairness is real, just unmeasured.','مدل منتشر می‌شود؛ ناعدالتی واقعی است ولی اندازه‌گیری نشده.',1,2);})
    ],s=>[`group column=${s.keep===null?'?':s.keep?'audit only':'deleted'}`,s.model||'∅',s.rates||'∅']);

  const clone = s => JSON.parse(JSON.stringify(s));
  function transition(id, state, actionId) {
    const model=models[id], action=model.actions.find(a=>a.id===actionId);
    if(!action || !action.when(state)) throw new Error(`Unavailable action: ${id}/${actionId}`);
    const next=clone(state); action.run(next); return next;
  }
  if(typeof module!=='undefined'&&module.exports) module.exports={models,transition};
  if(typeof document==='undefined')return;
  const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const bi = text => `<span class="en">${escape(text.en)}</span><span class="fa">${escape(text.fa)}</span>`;
  const icon = name => `<svg viewBox="0 0 24 24" width="17" height="17" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${({step:'<path d="m6 5 9 7-9 7zM19 5v14"/>',back:'<path d="M9 5 2 12l7 7M2 12h14a5 5 0 0 0 0-10"/>',reset:'<path d="M3 3v6h6M3.5 9A9 9 0 1 1 3 15"/>',play:'<path d="m7 4 13 8-13 8z"/>',pause:'<path d="M8 4v16M16 4v16"/>'})[name]}</svg>`;
  function mount(el) {
    if(el.dataset.ready)return;
    const model=models[el.dataset.lab];if(!model)return;
    el.dataset.ready='true';
    let history=[{state:model.initial(),action:null}], cursor=0, timer=null, flowing=false;
    const titleId=`lab-title-${model.id}`;
    el.setAttribute('aria-labelledby',titleId);
    el.innerHTML=`<div class="concept-lab-head"><h3 id="${titleId}">${bi(model.title)}</h3><p>${bi(model.prompt)}</p></div><div class="lab-scene" role="group" aria-label="System state"><svg class="lab-links" aria-hidden="true"><defs><marker id="ah-${model.id}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1 1 9 5 1 9z" fill="currentColor"/></marker></defs></svg><div class="lab-nodes"></div><div class="lab-bubble" aria-hidden="true"></div></div><div class="lab-flow-note" aria-live="polite"></div><div class="lab-feedback" aria-live="polite" aria-atomic="true"></div><div class="lab-choices" role="group"></div><div class="lab-toolbar"><button type="button" data-lab-control="back">${icon('back')}${bi(B('Back one step','یک قدم عقب'))}</button><button type="button" data-lab-control="step">${icon('step')}${bi(B('Next step','گام بعد'))}</button><button type="button" data-lab-control="play">${icon('play')}${bi(B('Play steps','پخش مراحل'))}</button><button type="button" data-lab-control="flow">${icon('play')}${bi(B('Play whole flow','نمایش کل فلو'))}</button><button type="button" data-lab-control="reset">${icon('reset')}${bi(B('Reset','شروع دوباره'))}</button><span class="lab-position"></span></div><details class="lab-history"><summary>${bi(B('Event history','تاریخچهٔ رویدادها'))}</summary><ol></ol></details><details class="lab-assumptions"><summary>${bi(B('Teaching model and assumptions','مدل آموزشی و فرض‌ها'))}</summary><p>${bi(model.assumption)}</p><p>${bi(B('All state stays in this page. Values and ticks illustrate the stated rules; they are not infrastructure measurements.','تمام وضعیت در همین صفحه است؛ مقدارها و نوبت‌ها قواعد مدل را نشان می‌دهند و اندازه‌گیری زیرساخت نیستند.'))}</p></details><a class="lab-studio-link" href="../studio/index.html?chapter=${el.dataset.chapter}">${bi(B('Continue with chapter exercises in the studio','ادامه با تمرین‌های فصل در استودیو'))}<span aria-hidden="true"> →</span></a>`;
    const controls=Object.fromEntries([...el.querySelectorAll('[data-lab-control]')].map(b=>[b.dataset.labControl,b]));
    const state=()=>history[cursor].state;
    const available=()=>model.actions.filter(a=>a.when(state()));
    function stop(){if(timer){clearInterval(timer);timer=null;}flowing=false;el.querySelector('.lab-flow-note').innerHTML='';controls.play.innerHTML=icon('play')+bi(B('Play steps','پخش مراحل'));controls.flow.innerHTML=icon('play')+bi(B('Play whole flow','نمایش کل فلو'));}
    const BAD=/crash|kill|drop|pause|abort|delete|corrupt|partition|celebrity|burst|freeze/;
    function animate(move,action){
      const scene=el.querySelector('.lab-scene'),cards=[...scene.querySelectorAll('.lab-node')],bubble=scene.querySelector('.lab-bubble');
      if(!move||document.documentElement.dataset.motion==='off'||!bubble.animate)return;
      const bad=BAD.test(action.id),sr=scene.getBoundingClientRect();
      const at=i=>{const r=cards[i].getBoundingClientRect();return {x:r.left-sr.left+r.width/2,y:r.top-sr.top+r.height/2};};
      const flash=(i,cls)=>{cards[i].classList.remove(cls);void cards[i].offsetWidth;cards[i].classList.add(cls);};
      bubble.innerHTML=bi(action.label);bubble.classList.toggle('bad',bad);
      if(move[0]===move[1]){flash(move[1],bad?'shake':'pulse');return;}
      const a=at(move[0]),b=at(move[1]),key=Math.min(...move)+'-'+Math.max(...move),link=scene.querySelector(`.lab-link[data-key="${key}"]`);
      if(link){link.classList.add('active');setTimeout(()=>link.classList.remove('active'),1300);}
      flash(move[0],'send');
      const place=p=>`translate(${p.x}px,${p.y}px) translate(-50%,-50%)`;
      bubble.animate([{transform:place(a)+' scale(.6)',opacity:0},{opacity:1,offset:.18},{opacity:1,offset:.82},{transform:place(b)+' scale(1)',opacity:0}],{duration:1150,easing:'cubic-bezier(.45,0,.2,1)'}).onfinish=()=>flash(move[1],bad?'shake':'hit');
    }
    const ICON={client:'<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',queue:'<rect x="3" y="7" width="5" height="10" rx="1"/><rect x="10" y="7" width="5" height="10" rx="1"/><path d="M18 12h3m-1.5-1.5L21 12l-1.5 1.5"/>',log:'<path d="M5 4h14M5 9h14M5 14h9M5 19h6"/>',disk:'<ellipse cx="12" cy="6" rx="8" ry="3"/><path d="M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',search:'<circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/>',server:'<rect x="3" y="4" width="18" height="6" rx="1.5"/><rect x="3" y="14" width="18" height="6" rx="1.5"/><path d="M7 7h.01M7 17h.01"/>',clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',db:'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/>',doc:'<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>'};
    const pickIcon=label=>{const l=label.en.toLowerCase();return /client|reader|user|buyer|request|arrival|consumer|claim|observ/.test(l)?'client':/queue|broker|relay|outbox|shuffle|message|publisher|lock service/.test(l)?'queue':/log|wal|ledger|history|event|stored/.test(l)?'log':/disk|sstable|backup|storage|table|memtable/.test(l)?'disk':/search|view|index|report|read result/.test(l)?'search':/clock|time|lamport/.test(l)?'clock':/leader|follower|replica|node|server|shard|worker|service|mapper|reducer|checkout|job|patrol|policy/.test(l)?'server':/db|database|account|record|author|row|profile|order|balance|primary/.test(l)?'db':'doc';};
    const hue=[...model.id].reduce((h,c)=>(h*31+c.charCodeAt(0))%360,7);
    el.style.setProperty('--lab-h',hue);
    const LAYOUT={stack:'outbox wal schema eventlog scan rolling dirty combiner olap rpc tail btree rename reconcile',fan:'replication failover monotonic hotkey fencing secondary ordering timeout',tri:'leaderless quorum lamport privacy unique batch rebuild retry feedback twopc ephemeral rerun proxy hops'};
    const layout=Object.keys(LAYOUT).find(k=>LAYOUT[k].split(' ').includes(model.id))||'row';
    const LINKS={row:[[0,1],[1,2]],stack:[[0,1],[1,2]],fan:[[0,1],[0,2]],tri:[[0,1],[0,2],[1,2]]}[layout];
    function drawLinks(){
      const scene=el.querySelector('.lab-scene'),svg=scene.querySelector('.lab-links'),cards=[...scene.querySelectorAll('.lab-node')];if(cards.length<3)return;
      const sr=scene.getBoundingClientRect(),box=cards.map(c=>{const r=c.getBoundingClientRect();return {w:r.width,h:r.height,x:r.left-sr.left+r.width/2,y:r.top-sr.top+r.height/2};});
      const edge=(a,b)=>{const dx=b.x-a.x,dy=b.y-a.y,k=Math.min(dx?(a.w/2+6)/Math.abs(dx):1e9,dy?(a.h/2+6)/Math.abs(dy):1e9);return {x:a.x+dx*k,y:a.y+dy*k};};
      svg.setAttribute('viewBox',`0 0 ${sr.width} ${sr.height}`);svg.querySelectorAll('line').forEach(l=>l.remove());
      for(const [i,j] of LINKS){const p=edge(box[i],box[j]),q=edge(box[j],box[i]),line=document.createElementNS('http://www.w3.org/2000/svg','line');line.setAttribute('x1',p.x);line.setAttribute('y1',p.y);line.setAttribute('x2',q.x);line.setAttribute('y2',q.y);line.setAttribute('class','lab-link');line.dataset.key=i+'-'+j;line.setAttribute('marker-end',`url(#ah-${model.id})`);svg.append(line);}
    }
    if('ResizeObserver'in root)new ResizeObserver(()=>drawLinks()).observe(el);
    let shown=null;
    function render(animateStep){
      const s=state();const view=model.view(s),before=animateStep&&shown?shown:null;shown=view;
      el.querySelector('.lab-nodes').innerHTML=view.map((value,i)=>`<div class="lab-node${/\b(down|frozen|error)\b/.test(value)?' is-down':''}${before&&before[i]!==value?' changed':''}"><b><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${ICON[pickIcon(model.labels[i])]}</svg>${bi(model.labels[i])}</b><pre dir="ltr">${escape(value)}</pre></div>`).join('');
      el.querySelector('.lab-nodes').dataset.layout=layout;drawLinks();
      el.querySelector('.lab-feedback').innerHTML=bi(s.message);
      el.querySelector('.lab-choices').innerHTML=available().map(a=>`<button type="button" data-lab-action="${a.id}">${bi(a.label)}</button>`).join('')||`<p class="lab-done">${bi(B('Run complete. Step back to try another decision.','اجرا تمام شد؛ برای امتحان تصمیم دیگر یک قدم عقب برو.'))}</p>`;
      controls.back.disabled=cursor===0;controls.step.disabled=available().length!==1;controls.play.disabled=available().length!==1;
      el.querySelector('.lab-position').innerHTML=bi(B(`Step ${cursor}`,`گام ${cursor}`));
      el.querySelector('.lab-history ol').innerHTML=history.slice(0,cursor+1).map((h,i)=>`<li>${i?bi(model.actions.find(a=>a.id===h.action).label):bi(B('Prepared initial state','وضعیت اولیهٔ آماده'))} — ${bi(h.state.message)}</li>`).join('');
      if(animateStep&&history[cursor].action)animate(s.move,model.actions.find(a=>a.id===history[cursor].action));
      if(!available().length&&!flowing)stop();
    }
    function run(id){history=history.slice(0,cursor+1);history.push({state:transition(model.id,state(),id),action:id});cursor++;render(true);}
    function allPaths(){
      const leaves=[];(function dfs(st,path){if(leaves.length>=300)return;const av=model.actions.filter(a=>a.when(st));if(!av.length){leaves.push(path);return;}for(const a of av)dfs(transition(model.id,st,a.id),[...path,a.id]);})(model.initial(),[]);
      const firsts=new Set(),pick=[];for(const p of leaves)if(!firsts.has(p[0])){firsts.add(p[0]);pick.push(p);}
      for(const p of leaves){if(pick.length>=4)break;if(!pick.includes(p))pick.push(p);}return pick.slice(0,4);
    }
    function playFlow(){
      stop();const paths=allPaths();let pi=0,si=0;flowing=true;controls.flow.innerHTML=icon('pause')+bi(B('Pause','مکث'));
      const note=el.querySelector('.lab-flow-note'),begin=()=>{history=[{state:model.initial(),action:null}];cursor=0;render(false);const first=model.actions.find(a=>a.id===paths[pi][0]).label;note.innerHTML=bi(B(`Scenario ${pi+1} of ${paths.length}: `,`سناریو ${pi+1} از ${paths.length}: `))+bi(first);};
      begin();
      timer=setInterval(()=>{if(si<paths[pi].length){run(paths[pi][si++]);}else{pi++;if(pi>=paths.length){stop();return;}si=0;begin();}},1500);
    }
    function advance(){const actions=available();if(actions.length===1){run(actions[0].id);}else{stop();el.querySelector('.lab-choices button')?.focus();}}
    el.addEventListener('click',e=>{
      const action=e.target.closest('[data-lab-action]');if(action){stop();run(action.dataset.labAction);(el.querySelector('.lab-choices button')||controls.back).focus({preventScroll:true});return;}
      const button=e.target.closest('[data-lab-control]');if(!button)return;
      switch(button.dataset.labControl){
        case 'back':stop();if(cursor){cursor--;render(false);}break;
        case 'flow':if(flowing)stop();else playFlow();break;
        case 'reset':stop();history=[{state:model.initial(),action:null}];cursor=0;render(false);break;
        case 'step':stop();advance();break;
        case 'play':if(timer){stop();}else if(available().length===1){controls.play.innerHTML=icon('pause')+bi(B('Pause','مکث'));advance();if(available().length===1)timer=setInterval(advance,1200);}else{el.querySelector('.lab-choices button')?.focus();}break;
      }
    });
    // Stop timers off-screen or when the document is hidden; no autonomous background work.
    document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
    if('IntersectionObserver'in root){new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)stop();}).observe(el);}
    function localizeLabels(){const lang=document.documentElement.lang==='fa'?'fa':'en';el.querySelector('.lab-scene').setAttribute('aria-label',B('Current system state','وضعیت فعلی سیستم')[lang]);el.querySelector('.lab-choices').setAttribute('aria-label',B('Choose the next action','کار بعدی را انتخاب کن')[lang]);}
    localizeLabels();
    new MutationObserver(localizeLabels).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});
    render(false);
  }
  function init(){const labs=document.querySelectorAll('.concept-lab[data-lab]');if('IntersectionObserver'in root){const observer=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){mount(entry.target);observer.unobserve(entry.target);}}),{rootMargin:'400px'});labs.forEach(el=>observer.observe(el));}else labs.forEach(mount);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})(typeof window==='undefined'?globalThis:window);
