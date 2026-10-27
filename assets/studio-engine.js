/* Offline teaching model. No provider benchmarks, tail latency or correctness guarantees. */
(function (root) {
  'use strict';
  const catalog = () => root.DDIAStudioData || (typeof require === 'function' ? require('./studio-data.js') : { components: [] });
  const componentMap = () => new Map(catalog().components.map(c => [c.id, c]));
  const finite = (value, fallback, max = 1e9) => Number.isFinite(Number(value)) ? Math.max(0, Math.min(max, Number(value))) : fallback;
  const plain = value => value !== null && typeof value === 'object' && !Array.isArray(value) && [Object.prototype, null].includes(Object.getPrototypeOf(value));
  const forbidden = new Set(['__proto__', 'constructor', 'prototype']);
  const text = value => typeof value === 'string' && value.length <= 4000;
  const id = value => typeof value === 'string' && /^[a-zA-Z0-9][a-zA-Z0-9_:-]{0,79}$/.test(value);
  const round = value => Math.round(value * 100) / 100;
  const tr = (opts, en, fa) => opts && opts.lang === 'fa' ? fa : en;

  function validateGraph(input) {
    const errors = [], warnings = [], comps = componentMap();
    if (!plain(input) || !Array.isArray(input.nodes) || !Array.isArray(input.edges)) return { valid: false, errors: ['Graph must contain nodes and edges arrays.'], warnings };
    if (input.nodes.length > 200 || input.edges.length > 600) return { valid: false, errors: ['Graph exceeds the limit of 200 nodes or 600 edges.'], warnings };
    const clean = { nodes: [], edges: [] }, nodeIds = new Set(), edgeIds = new Set();
    function safeKeys(obj) { return Object.keys(obj).every(key => !forbidden.has(key)); }
    if (!safeKeys(input)) errors.push('Unsafe graph property.');
    for (const node of input.nodes) {
      if (!plain(node) || !safeKeys(node) || !id(node.id) || nodeIds.has(node.id) || !comps.has(node.type)) { errors.push('Invalid, duplicate or unknown node.'); continue; }
      nodeIds.add(node.id);
      const def = comps.get(node.type), normalized = { id: node.id, type: node.type, label: node.label === undefined ? def.label : node.label, x: node.x === undefined ? 100 : node.x, y: node.y === undefined ? 100 : node.y, replicas: node.replicas === undefined ? 1 : node.replicas, config: {} };
      if (!text(normalized.label)) errors.push(`Invalid label on ${node.id}.`);
      for (const key of ['x', 'y']) if (!Number.isFinite(normalized[key]) || Math.abs(normalized[key]) > 100000) errors.push(`Invalid ${key} on ${node.id}.`);
      if (!Number.isInteger(normalized.replicas) || normalized.replicas < 1 || normalized.replicas > 1000) errors.push(`Replicas on ${node.id} must be an integer from 1 to 1000.`);
      for (const key of ['capacity', 'latency']) if (node[key] !== undefined) {
        if (!Number.isFinite(node[key]) || node[key] < 0 || node[key] > 1e9) errors.push(`Invalid ${key} on ${node.id}.`);
        normalized[key] = node[key];
      }
      if (node.config !== undefined) {
        if (!plain(node.config) || !safeKeys(node.config) || Object.keys(node.config).length > 40) errors.push(`Invalid config on ${node.id}.`);
        else for (const [key, value] of Object.entries(node.config)) {
          if (!/^[a-zA-Z][a-zA-Z0-9_]{0,59}$/.test(key) || !(text(value) || typeof value === 'boolean' || (typeof value === 'number' && Number.isFinite(value)) || value === null)) errors.push(`Config values on ${node.id} must be finite numbers, text or booleans.`);
          else normalized.config[key] = value;
        }
      }
      clean.nodes.push(normalized);
    }
    const byId = new Map(clean.nodes.map(n => [n.id, n]));
    const pairs = new Set();
    for (const edge of input.edges) {
      if (!plain(edge) || !safeKeys(edge) || !id(edge.id) || edgeIds.has(edge.id) || !nodeIds.has(edge.source) || !nodeIds.has(edge.target) || edge.source === edge.target) { errors.push('Invalid edge, missing endpoint, self-loop or duplicate edge id.'); continue; }
      const pair = `${edge.source}>${edge.target}`;
      if (pairs.has(pair)) { errors.push('Duplicate connection between the same nodes.'); continue; }
      pairs.add(pair); edgeIds.add(edge.id);
      if (byId.get(edge.source).type === 'note' || byId.get(edge.target).type === 'note') { errors.push('Design notes cannot carry request edges.'); continue; }
      const protocol = edge.protocol === undefined ? 'RPC' : edge.protocol;
      if (!text(protocol) || protocol.length > 80) { errors.push('Invalid edge protocol.'); continue; }
      clean.edges.push({ id: edge.id, source: edge.source, target: edge.target, protocol });
    }
    if (!clean.nodes.some(n => n.type !== 'note')) warnings.push('Add a traffic component to run the simulation.');
    const topology = sortGraph(clean);
    if (topology.cyclic) warnings.push('Cyclic traffic paths are unsupported. Remove a back edge; replication and retry loops need a stateful model.');
    return { valid: errors.length === 0, errors, warnings, graph: errors.length ? undefined : clean };
  }

  function sortGraph(graph) {
    const nodes = graph.nodes.filter(n => n.type !== 'note');
    const outgoing = new Map(nodes.map(n => [n.id, []]));
    const incoming = new Map(nodes.map(n => [n.id, []]));
    for (const edge of graph.edges) { outgoing.get(edge.source).push(edge); incoming.get(edge.target).push(edge); }
    const degree = new Map(nodes.map(n => [n.id, incoming.get(n.id).length]));
    const roots = nodes.filter(n => degree.get(n.id) === 0), queue = roots.slice(), sorted = [];
    for (let i = 0; i < queue.length; i++) {
      const node = queue[i]; sorted.push(node);
      for (const edge of outgoing.get(node.id)) { degree.set(edge.target, degree.get(edge.target) - 1); if (!degree.get(edge.target)) queue.push(nodes.find(n => n.id === edge.target)); }
    }
    return { nodes, outgoing, incoming, roots, sorted, cyclic: sorted.length !== nodes.length };
  }

  function simulate(input, opts = {}) {
    const validation = validateGraph(input);
    const assumptions = [
      tr(opts, 'Illustrative steady-state requests per second and service times; not benchmarks, p99 or an SLO prediction.', 'نرخ درخواست و زمان خدمت آموزشی‌اند؛ benchmark، p99 یا پیش‌بینی SLO نیستند.'),
      tr(opts, 'Load balancers split equally; other branches copy requests to every dependency. Cache and CDN forward all writes plus cache misses.', 'توزیع‌کننده بار را مساوی تقسیم می‌کند؛ شاخه‌های دیگر درخواست را به همهٔ وابستگی‌ها می‌فرستند. کش و CDN نوشتن‌ها و miss را عبور می‌دهند.'),
      tr(opts, 'Replica capacity scales ideally. No quorum, replication lag, transactional safety, retries or geographic latency is modeled.', 'ظرفیت نسخه‌ها ایده‌آل جمع می‌شود؛ quorum، lag، صحت تراکنش، retry و تأخیر جغرافیایی مدل نشده‌اند.'),
      tr(opts, 'Latency sums service time along the longest dependency path; asynchronous branches are shown as dependencies. Queue backlog is growth in requests per second.', 'تأخیر جمع زمان خدمت طولانی‌ترین مسیر وابستگی است؛ شاخهٔ ناهمگام هم وابستگی حساب می‌شود. backlog رشد درخواست در ثانیه است.'),
    ];
    const stopped = warnings => ({ valid: false, nodes: [], events: [], throughput: null, latencyMs: null, warnings, assumptions });
    if (!validation.valid) return stopped(validation.errors);
    const graph = validation.graph, topology = sortGraph(graph);
    if (topology.cyclic) return stopped(validation.warnings);
    if (!topology.nodes.length) return stopped(validation.warnings);
    const comps = componentMap(), warnings = validation.warnings.slice(), stats = new Map(), events = [];
    const totalQPS = finite(opts.qps, 1000), readRatio = finite(opts.readRatio, .8, 1), hit = finite(opts.cacheHitRate, .8, 1);
    const selectedRoot = opts.entryNode && topology.roots.find(n => n.id === opts.entryNode);
    const clients = topology.roots.filter(n => n.type === 'client');
    const trafficRoots = selectedRoot ? [selectedRoot] : clients.length ? clients : topology.roots;
    const active = new Set();
    function mark(nodeId) { if (active.has(nodeId)) return; active.add(nodeId); topology.outgoing.get(nodeId).forEach(e => mark(e.target)); }
    trafficRoots.forEach(n => mark(n.id));
    const inputQPS = new Map(topology.nodes.map(n => [n.id, 0]));
    trafficRoots.forEach(n => inputQPS.set(n.id, totalQPS / trafficRoots.length));
    for (const node of topology.sorted) {
      const def = comps.get(node.type), incomingQPS = inputQPS.get(node.id), failed = node.id === opts.failureNode;
      const capacity = failed ? 0 : (node.capacity === undefined ? def.maxQPS : node.capacity) * node.replicas;
      const accepted = Math.min(incomingQPS, capacity), outgoing = topology.outgoing.get(node.id);
      const cached = ['cache', 'cdn', 'origin-shield'].includes(node.type);
      const localHit = cached ? readRatio * finite(node.config.cacheHitRate, hit, 1) : 0;
      const forwardRatio = 1 - localHit;
      if (cached && outgoing.length === 0 && forwardRatio > 0 && incomingQPS > 0) warnings.push(tr(opts, `${node.label || def.label}: misses and writes have no connected origin.`, `${node.label || def.labelFa}: برای miss و نوشتن مبدأیی متصل نیست.`));
      const stat = { id: node.id, incomingQPS: round(incomingQPS), capacity: round(capacity), utilization: capacity > 0 ? round(incomingQPS / capacity) : incomingQPS > 0 ? null : 0, latencyMs: failed ? null : (node.latency === undefined ? def.latencyMs : node.latency), status: failed ? 'failed' : incomingQPS > capacity ? 'overloaded' : incomingQPS >= capacity * .8 && incomingQPS > 0 ? 'busy' : 'healthy', queueBacklogQPS: 0, droppedQPS: round(incomingQPS - accepted), active: active.has(node.id), accepted, localHit, successRatio: 1, pathLatency: 0 };
      if (['queue', 'event-stream'].includes(node.type)) {
        const downstreamCapacity = outgoing.length ? Math.min(...outgoing.map(e => { const target = graph.nodes.find(n => n.id === e.target); return target.id === opts.failureNode ? 0 : (target.capacity === undefined ? comps.get(target.type).maxQPS : target.capacity) * target.replicas; })) : 0;
        stat.queueBacklogQPS = round(Math.max(0, incomingQPS - Math.min(capacity, downstreamCapacity)));
        if (stat.queueBacklogQPS > 0) warnings.push(tr(opts, `${node.label || def.label}: backlog grows by about ${stat.queueBacklogQPS} requests/s; retention is not simulated.`, `${node.label || def.labelFa}: صف تقریباً ${stat.queueBacklogQPS} درخواست در ثانیه رشد می‌کند؛ retention مدل نشده است.`));
      }
      stats.set(node.id, stat);
      if (stat.status === 'overloaded') warnings.push(tr(opts, `${node.label || def.label}: ${round(incomingQPS)} requests/s exceeds capacity ${round(capacity)}.`, `${node.label || def.labelFa}: بار ${round(incomingQPS)} از ظرفیت ${round(capacity)} درخواست در ثانیه بیشتر است.`));
      if (failed && stat.active) warnings.push(tr(opts, `${node.label || def.label} is unavailable. No automatic rerouting or failover is assumed.`, `${node.label || def.labelFa} قطع است؛ تغییر مسیر یا failover خودکار فرض نشده است.`));
      for (const edge of outgoing) {
        const routed = accepted * forwardRatio / (node.type === 'load-balancer' ? outgoing.length : 1);
        inputQPS.set(edge.target, inputQPS.get(edge.target) + routed);
        events.push({ source: edge.source, target: edge.target, label: `${round(routed)} req/s · ${edge.protocol}`, qps: round(routed) });
      }
    }
    // shortcut: a steady-state DAG cannot establish timing-dependent correctness; use event labs for histories.
    for (const node of topology.sorted.slice().reverse()) {
      const stat = stats.get(node.id), children = topology.outgoing.get(node.id).map(e => stats.get(e.target));
      const acceptedRatio = stat.incomingQPS > 0 ? Math.min(1, stat.capacity / stat.incomingQPS) : stat.status === 'failed' ? 0 : 1;
      const dependencyRatio = children.length ? node.type === 'load-balancer' ? children.reduce((sum, c) => sum + c.successRatio, 0) / children.length : Math.min(...children.map(c => c.successRatio)) : ['cache', 'cdn', 'origin-shield'].includes(node.type) ? 0 : 1;
      stat.successRatio = acceptedRatio * (stat.localHit + (1 - stat.localHit) * dependencyRatio);
      stat.pathLatency = (stat.latencyMs || 0) + (children.length && stat.localHit < 1 ? Math.max(...children.map(c => c.pathLatency)) : 0);
    }
    const throughput = round(trafficRoots.reduce((sum, node) => sum + totalQPS / trafficRoots.length * stats.get(node.id).successRatio, 0));
    const latencyMs = throughput === 0 && totalQPS > 0 ? null : round(Math.max(...trafficRoots.map(n => stats.get(n.id).pathLatency)));
    if (topology.nodes.some(n => !active.has(n.id))) warnings.push(tr(opts, 'Disconnected components are excluded from traffic. Connect them to an entry point before drawing conclusions.', 'اجزای جدا از مسیر ورودی بار نمی‌گیرند؛ قبل از نتیجه‌گیری آن‌ها را متصل کن.'));
    if (!graph.edges.length) warnings.push(tr(opts, 'There are no dependencies. A successful client node alone does not represent a working application.', 'وابستگی‌ای متصل نیست؛ موفقیت یک گرهٔ کاربر به معنی کارکرد برنامه نیست.'));
    return { valid: true, nodes: Array.from(stats.values()).map(({ accepted, localHit, successRatio, pathLatency, ...publicStat }) => publicStat), throughput, latencyMs, warnings, events, assumptions };
  }

  function evaluate(input, problem = {}, opts = {}) {
    const validation = validateGraph(input), run = simulate(input, opts), fa = opts.lang === 'fa';
    const limitations = [tr(opts, 'Transparent structural practice rubric, not proof of availability, correctness or exercise completion.', 'معیار شفاف تمرین ساختاری است؛ اثبات دسترس‌پذیری، صحت یا اتمام تمرین نیست.'), tr(opts, 'Read the exercise signals and solution. Consistency, privacy, transactions and recovery require arguments or execution traces beyond this graph.', 'معیارهای تمرین و حل را بخوان؛ سازگاری، حریم خصوصی، تراکنش و بازیابی به استدلال یا تاریخچهٔ اجرا نیاز دارند.')];
    if (!validation.valid || !run.valid) return { total: 0, categories: ['Scalability', 'Availability', 'Latency', 'Cost', 'Trade-offs'].map(name => ({ name, score: 0, max: 20, feedback: run.warnings })), feedback: run.warnings, checks: [], limitations };
    const graph = validation.graph, topology = sortGraph(graph), comps = componentMap();
    const activeNodes = graph.nodes.filter(n => run.nodes.some(s => s.id === n.id && s.active));
    const activeStats = run.nodes.filter(n => n.active);
    const appPresent = activeNodes.some(n => comps.get(n.type).category === 'compute');
    const hasStore = activeNodes.some(n => comps.get(n.type).category === 'storage');
    const hasPath = graph.edges.length > 0 && (appPresent || hasStore);
    const qps = finite(opts.qps, 1000), capacityOK = hasPath && run.throughput >= qps * .99;
    const headroom = hasPath && activeStats.every(n => n.utilization !== null && n.utilization <= .8);
    const replicated = activeNodes.filter(n => !['client', 'note', 'region'].includes(n.type)).every(n => n.replicas >= 2);
    const failureTested = Boolean(opts.failureNode) && activeStats.some(n => n.id === opts.failureNode);
    const survives = failureTested && run.throughput >= qps * .99;
    const latencyBudget = finite(opts.latencyBudgetMs, 100);
    const latencyOK = hasPath && run.latencyMs !== null && run.latencyMs <= latencyBudget;
    const noOverload = hasPath && activeStats.every(n => n.status !== 'overloaded' && n.queueBacklogQPS === 0 && n.status !== 'failed');
    const noUnused = activeNodes.length === topology.nodes.length;
    const noWaste = hasPath && activeNodes.filter(n => !['client', 'note', 'region'].includes(n.type)).every(n => { const stat = activeStats.find(s => s.id === n.id); return stat.incomingQPS === 0 || stat.utilization >= .05; });
    const notes = graph.nodes.filter(n => n.type === 'note' || (typeof n.config.notes === 'string' && n.config.notes.trim().length >= 20));
    const rationale = notes.some(n => (n.type === 'note' ? n.label : n.config.notes).trim().length >= 20);
    const requirement = typeof opts.rationale === 'string' && opts.rationale.trim().length >= 40;
    const checks = [
      ['Scalability', capacityOK, 'Meets selected request rate', 'توان پاسخ به بار انتخابی'],
      ['Scalability', headroom, 'At least 20% ideal capacity headroom', 'حداقل ۲۰ درصد ظرفیت آزاد در مدل ایده‌آل'],
      ['Availability', hasPath && replicated, 'Every active dependency has replica capacity configured (failure domains unverified)', 'برای هر وابستگی فعال نسخه تنظیم شده؛ دامنهٔ خرابی بررسی نشده'],
      ['Availability', survives, 'Selected node outage retains target throughput without assumed rerouting', 'در قطع گرهٔ انتخابی بار هدف بدون فرض تغییر مسیر حفظ می‌شود'],
      ['Latency', latencyOK, `Illustrative service path fits ${latencyBudget} ms budget`, `زمان خدمت مسیر در بودجهٔ ${latencyBudget} میلی‌ثانیه است`],
      ['Latency', noOverload, 'No overloaded node or growing queue at selected load', 'در بار انتخابی گرهٔ اشباع یا صف رو به رشد وجود ندارد'],
      ['Cost', hasPath && noUnused, 'Every traffic component serves the selected entry flow', 'همهٔ اجزای ترافیک در مسیر ورودی انتخابی کاربرد دارند'],
      ['Cost', noWaste, 'No serving dependency below 5% illustrative capacity use', 'هیچ وابستگی پاسخ‌دهنده زیر ۵ درصد مصرف ظرفیت آموزشی نیست'],
      ['Trade-offs', rationale, 'A meaningful design note records assumptions', 'یادداشت طراحی معنادار فرض‌ها را ثبت می‌کند'],
      ['Trade-offs', requirement, 'Written rationale ties choices to exercise requirements', 'توضیح مکتوب انتخاب‌ها را به نیاز تمرین وصل می‌کند'],
    ].map(([category, passed, en, persian]) => ({ category, label: fa ? persian : en, passed, detail: passed ? tr(opts, 'Satisfied under the stated model assumptions.', 'با فرض‌های همین مدل برقرار است.') : tr(opts, 'Revise the design or explain why this criterion does not apply.', 'طرح را اصلاح کن یا توضیح بده چرا این معیار کاربرد ندارد.') }));
    const categoryNames = { Scalability: 'مقیاس‌پذیری', Availability: 'دسترس‌پذیری', Latency: 'تأخیر', Cost: 'هزینه', 'Trade-offs': 'موازنه‌ها' };
    const categories = Object.keys(categoryNames).map(key => { const own = checks.filter(c => c.category === key); return { name: fa ? categoryNames[key] : key, score: own.filter(c => c.passed).length * 10, max: 20, feedback: own.filter(c => !c.passed).map(c => c.label) }; });
    return { total: categories.reduce((sum, c) => sum + c.score, 0), categories, checks, feedback: checks.filter(c => !c.passed).map(c => c.label), limitations, signals: fa ? problem.signalsFa || [] : problem.signalsEn || [] };
  }

  function coach(question, graph, problem = {}, opts = {}) {
    const prefix = tr(opts, 'Local rule-based coach (no AI request). ', 'راهنمای محلی مبتنی بر قواعد (بدون درخواست هوش مصنوعی). ');
    const run = simulate(graph, opts);
    if (!run.valid) return prefix + run.warnings.join(' ');
    const q = String(question || '').toLowerCase();
    if (/reference|answer|solution|مرجع|پاسخ|حل/.test(q)) return prefix + tr(opts, 'Load the reference as an editable hypothesis, then open the worked solution. A similar-looking graph is not proof that the exercise is solved.', 'طرح مرجع را به‌عنوان فرضیهٔ قابل ویرایش باز کن و حل تشریحی را بخوان. شباهت گراف اثبات حل شدن تمرین نیست.');
    if (/fail|avail|replica|خراب|قطع|دسترس|نسخه/.test(q)) return prefix + tr(opts, 'Select an active dependency for failure injection and rerun. Compare delivered throughput, then document recovery, failure domains and routing. Increasing replicas alone only scales ideal capacity here.', 'یک وابستگی فعال را قطع و دوباره اجرا کن. توان پاسخ را مقایسه و بازیابی، دامنهٔ خرابی و مسیریابی را مستند کن. افزایش نسخه در این مدل فقط ظرفیت ایده‌آل را بالا می‌برد.');
    const saturated = run.nodes.find(n => n.status === 'overloaded' || n.queueBacklogQPS > 0);
    if (saturated) { const node = graph.nodes.find(n => n.id === saturated.id); return prefix + tr(opts, `${node.label || node.type} receives ${saturated.incomingQPS} req/s against ${saturated.capacity} capacity. Trace its incoming edges. Try one replica, cache-hit or load change at a time and compare. Queue backlog growth: ${saturated.queueBacklogQPS} req/s.`, `${node.label || node.type} بار ${saturated.incomingQPS} با ظرفیت ${saturated.capacity} درخواست در ثانیه دارد. مسیر ورودی را دنبال کن. هر بار فقط نسخه، hit کش یا بار را تغییر بده و مقایسه کن. رشد صف: ${saturated.queueBacklogQPS} درخواست در ثانیه.`); }
    if (/cache|latency|slow|کش|تأخیر|کند/.test(q)) return prefix + tr(opts, 'Follow the longest path and compare the selected load with one change. Cache misses equal reads × (1 − hit rate), while writes still reach storage. Then state the freshness and invalidation contract omitted by this model.', 'طولانی‌ترین مسیر را دنبال و فقط یک تغییر را در همان بار مقایسه کن. miss برابر خواندن ضربدر (۱ منهای hit) است و نوشتن همچنان به ذخیره‌ساز می‌رود. قرارداد تازگی و ابطال کش را که مدل ندارد بنویس.');
    const signals = opts.lang === 'fa' ? problem.signalsFa : problem.signalsEn;
    return prefix + tr(opts, `At ${finite(opts.qps, 1000)} req/s the illustrative throughput is ${run.throughput}. Pick one requirement, change one parameter, run a failure case and record the trade-off. ${signals && signals[0] ? 'Exercise focus: ' + signals[0] : ''}`, `در بار ${finite(opts.qps, 1000)} توان پاسخ آموزشی ${run.throughput} درخواست در ثانیه است. یک نیاز را انتخاب کن، یک پارامتر را تغییر بده، خرابی را امتحان و موازنه را ثبت کن. ${signals && signals[0] ? 'تمرکز تمرین: ' + signals[0] : ''}`);
  }


  // Captured SysDes arithmetic, intentionally separate from the extended teaching model.
  // Source provenance and known optimistic quirks: behavior-ledger.md B15–B18.
  function simulateReference(input, opts = {}) {
    const validation = validateGraph(input);
    const assumptions = [tr(opts, 'Reference mode reproduces the captured SysDes capacity heuristics, including its optimistic throughput and cycle handling. These are not benchmarks or measured p99 values.', 'حالت مرجع قواعد ظرفیت نسخهٔ مشاهده‌شدهٔ SysDes را با محدودیت‌های توان پاسخ و چرخه بازتولید می‌کند؛ benchmark یا p99 اندازه‌گیری‌شده نیست.'), tr(opts, 'Load balancers and API gateways split; every other component fans out. Cache hits, failures, async acknowledgments, queue growth and correctness are not modeled.', 'توزیع‌کنندهٔ بار و درگاه API تقسیم می‌کنند و بقیه بار را تکثیر می‌کنند. hit کش، خرابی، تأیید ناهمگام، رشد صف و صحت مدل نمی‌شوند.')];
    if (!validation.valid) return { valid: false, nodes: [], events: [], throughput: null, latencyMs: null, warnings: validation.errors, assumptions, model: 'source-reference' };
    const graph = validation.graph, topology = sortGraph(graph), comps = componentMap();
    const qps = finite(opts.qps ?? opts.requestsPerSec, 10000), arriving = new Map(), metrics = new Map(), warnings = [], events = [];
    const degree = new Map(topology.nodes.map(n => [n.id, topology.incoming.get(n.id).length]));
    topology.roots.forEach(n => arriving.set(n.id, qps / topology.roots.length));
    const processed = new Set();
    function measure(node) {
      const def = comps.get(node.type), incomingQPS = arriving.get(node.id) ?? 0;
      const capacity = (node.capacity === undefined ? def.maxQPS : node.capacity) * node.replicas;
      const utilization = capacity === 0 || capacity === Infinity ? 0 : incomingQPS / capacity;
      const baseLatency = node.latency === undefined ? def.latencyMs : node.latency;
      const latencyMs = utilization > .7 ? baseLatency * (1 + 3 * Math.max(0, utilization - .7)) : baseLatency;
      const status = utilization > .8 ? 'critical' : utilization > .5 ? 'warning' : 'healthy';
      const stat = { id: node.id, nodeId: node.id, incomingQPS, capacity, effectiveQPS: capacity, utilization: Math.min(utilization, 2), latencyMs, status, isBottleneck: utilization > .8, active: true, queueBacklogQPS: 0 };
      metrics.set(node.id, stat);
      return stat;
    }
    for (const node of topology.sorted) {
      processed.add(node.id);
      const stat = measure(node), targets = topology.outgoing.get(node.id);
      const forwarded = Math.min(stat.incomingQPS, stat.capacity);
      const split = ['load-balancer', 'api-gateway'].includes(node.type);
      for (const edge of targets) {
        const rate = split && targets.length > 0 ? forwarded / targets.length : forwarded;
        arriving.set(edge.target, (arriving.get(edge.target) ?? 0) + rate);
        events.push({ source: edge.source, target: edge.target, qps: rate, label: `${round(rate)} req/s · ${edge.protocol}` });
      }
    }
    const blocked = topology.nodes.filter(n => !processed.has(n.id) && degree.get(n.id) > 0);
    if (blocked.length) {
      warnings.push(`Cycle detected involving node(s): ${blocked.map(n => n.id).join(', ')}. Processing with accumulated QPS.`);
      blocked.forEach(measure);
    }
    for (const node of topology.nodes) if (!metrics.has(node.id)) {
      const def = comps.get(node.type);
      metrics.set(node.id, { id: node.id, nodeId: node.id, incomingQPS: 0, capacity: (node.capacity ?? def.maxQPS) * node.replicas, effectiveQPS: (node.capacity ?? def.maxQPS) * node.replicas, utilization: 0, latencyMs: node.latency ?? def.latencyMs, status: 'idle', isBottleneck: false, active: false, queueBacklogQPS: 0 });
    }
    const path = new Map();
    topology.roots.forEach(n => path.set(n.id, metrics.get(n.id)?.latencyMs ?? 0));
    for (const node of topology.sorted) for (const edge of topology.outgoing.get(node.id)) {
      const candidate = (path.get(node.id) ?? 0) + (metrics.get(edge.target)?.latencyMs ?? 0);
      if (candidate > (path.get(edge.target) ?? 0)) path.set(edge.target, candidate);
    }
    const bottlenecks = Array.from(metrics.values()).filter(n => n.isBottleneck);
    return { valid: true, nodes: Array.from(metrics.values()), nodeMetrics: metrics, throughput: topology.nodes.length === 0 ? 0 : bottlenecks.length ? Math.min(...bottlenecks.map(n => n.capacity)) : qps, latencyMs: Math.max(0, ...path.values()), totalLatencyMs: Math.max(0, ...path.values()), bottleneckNodes: bottlenecks.map(n => n.id), warnings, events, assumptions, timestamp: Date.now(), model: 'source-reference' };
  }

  function evaluateReference(input, problem = {}, opts = {}) {
    const validation = validateGraph(input);
    const limitations = [tr(opts, 'This reproduces the captured local presence/connectivity rubric. It does not inspect the selected problem, written rationale, measured performance or correctness.', 'این ارزیابی معیار محلی حضور و اتصال اجزای نسخهٔ مشاهده‌شده را بازتولید می‌کند؛ نیاز تمرین، توضیح مکتوب، عملکرد اندازه‌گیری‌شده و صحت را بررسی نمی‌کند.')];
    if (!validation.valid) return { total: 0, categories: [], feedback: validation.errors, checks: [], limitations, verdict: 'Invalid graph', summary: 'Validate the graph before evaluation.', model: 'source-reference' };
    const graph = validation.graph, comps = componentMap();
    const nodes = graph.nodes.filter(n => n.type !== 'note').map(n => { const def = comps.get(n.type); return { ...n, sourceId: def.sourceId || def.id, category: def.sourceCategory || def.category, scalable: def.scalable === undefined ? false : def.scalable }; });
    if (!nodes.length) return { total: 0, categories: [], feedback: [], checks: [], limitations, verdict: 'Empty Canvas', summary: 'Add components to the canvas to get a score.', model: 'source-reference' };
    const edges = graph.edges, ids = nodes.map(n => n.sourceId), has = id => ids.includes(id), find = id => nodes.find(n => n.id === id);
    const allChecks = [], categories = [];
    function category(name, tests) {
      let score = 0; const feedback = [], passed = [];
      for (const [condition, points, label, partial = 0] of tests) {
        const ok = Boolean(condition); score += ok ? points : partial;
        const detail = ok ? `Reference criterion met (+${points}).` : `Reference criterion not met${partial ? ` (+${partial} partial)` : ''}.`;
        allChecks.push({ category: name, label, passed: ok, detail });
        (ok ? passed : feedback).push(label);
      }
      categories.push({ name, category: name, score: Math.max(0, Math.min(score, 20)), max: 20, maxScore: 20, feedback, passed });
    }
    const compute = nodes.some(n => n.category === 'compute' && n.scalable);
    const dbReplica = nodes.some(n => ['nosql-db', 'sql-db'].includes(n.sourceId) && n.replicas > 1);
    const lbLinked = has('load-balancer') && compute && edges.some(e => find(e.source)?.sourceId === 'load-balancer' && (find(e.target)?.category === 'compute' || ['api-gateway', 'rate-limiter'].includes(find(e.target)?.sourceId)));
    category('Scalability', [
      [has('load-balancer'), 3, 'Load balancer'], [compute, 3, 'Scalable compute'], [has('cache'), 3, 'Cache'],
      [has('message-queue'), 3, 'Message queue'], [dbReplica, 3, 'SQL or NoSQL replicas > 1'],
      [has('cdn'), 3, 'CDN'], [lbLinked, 2, 'Load balancer connected to compute, API gateway or rate limiter'],
    ]);
    const entryFanout = nodes.some(n => ['load-balancer', 'api-gateway', 'cdn'].includes(n.sourceId) && edges.filter(e => e.source === n.id).length >= 2);
    const duplicate = ids.some((id, i) => ids.indexOf(id) !== i);
    const database = has('sql-db') || has('nosql-db'), cacheDB = has('cache') && database;
    category('Availability', [
      [nodes.filter(n => n.scalable || n.replicas > 1).length >= Math.floor(.7 * nodes.length), 3, '70% threshold of scalable or replicated components'],
      [nodes.some(n => n.category === 'storage' && n.replicas > 1), 3, 'Replicated storage'],
      [(entryFanout || duplicate) && nodes.length > 2, 3, 'Entry fan-out or duplicate component type'],
      [has('monitoring'), 3, 'Monitoring'], [has('rate-limiter') || has('api-gateway'), 3, 'Rate limiter or gateway'],
      [cacheDB, 3, 'Cache with SQL or NoSQL'], [has('message-queue'), 2, 'Message queue'],
    ]);
    const outgoing = new Map(nodes.map(n => [n.id, []]));
    edges.forEach(e => outgoing.get(e.source)?.push(e.target));
    const dbIds = new Set(nodes.filter(n => ['sql-db', 'nosql-db'].includes(n.sourceId)).map(n => n.id));
    const cacheBefore = nodes.filter(n => n.sourceId === 'cache').some(n => outgoing.get(n.id).some(id => dbIds.has(id) || (outgoing.get(id) || []).some(next => dbIds.has(next))));
    const topology = sortGraph(graph), depths = new Map(topology.roots.map(n => [n.id, 1]));
    // The original hop calculation updates blocked cycle-frontier nodes as edges are encountered.
    for (const n of topology.sorted) for (const e of topology.outgoing.get(n.id)) depths.set(e.target, Math.max(depths.get(e.target) || 0, (depths.get(n.id) ?? 1) + 1));
    const hops = Math.max(0, ...depths.values());
    category('Latency', [
      [has('cdn'), 3, 'CDN'], [cacheBefore, 3, 'Cache reaches SQL or NoSQL within two edges', has('cache') ? 1 : 0],
      [hops <= 4, 3, 'Request path at most four layers', hops <= 5 ? 2 : 0], [has('dns'), 1, 'DNS'],
      [has('message-queue'), 3, 'Message queue'], [has('load-balancer'), 2, 'Load balancer'],
      [has('cache') || has('nosql-db'), 5, 'Cache or NoSQL'],
    ]);
    const storageCount = nodes.filter(n => n.category === 'storage').length, connected = new Set(edges.flatMap(e => [e.source, e.target]));
    category('Cost Efficiency', [
      [nodes.length >= 3 && nodes.length <= 25, 3, 'Between 3 and 25 components', nodes.length < 3 || nodes.length <= 35 ? 1 : 0],
      [storageCount >= 1 && storageCount <= 5, 3, 'Between 1 and 5 storage components'], [cacheDB, 3, 'Cache with SQL or NoSQL'],
      [nodes.every(n => connected.has(n.id)), 3, 'Every component has at least one connection'], [has('cdn'), 3, 'CDN'],
      [has('message-queue'), 3, 'Message queue'], [!(has('api-gateway') && has('rate-limiter') && has('service-mesh')), 2, 'No simultaneous gateway, limiter and mesh'],
    ]);
    const persistence = new Set(ids.filter(id => ['sql-db', 'nosql-db', 'cache', 'timeseries-db', 'graph-db', 'search', 'object-storage'].includes(id)));
    const breadth = new Set(nodes.map(n => n.category)).size;
    category('Trade-offs', [
      [cacheDB, 3, 'Cache with SQL or NoSQL'], [persistence.size >= 2, 3, 'At least two recognized persistence types', persistence.size === 1 ? 1 : 0],
      [has('message-queue'), 3, 'Message queue'], [has('rate-limiter') || has('api-gateway'), 3, 'Rate limiter or gateway'],
      [breadth >= 4, 3, 'At least four component categories', breadth >= 3 ? 1 : 0],
      [has('auth-service') || has('api-gateway') && has('rate-limiter'), 3, 'Auth service or gateway with limiter'], [has('monitoring'), 2, 'Monitoring'],
    ]);
    const total = Math.max(0, Math.min(categories.reduce((sum, c) => sum + c.score, 0), 100));
    const verdict = total >= 86 ? 'Architect Level' : total >= 71 ? 'Excellent' : total >= 51 ? 'Good' : total >= 31 ? 'Decent' : 'Needs Work';
    const feedback = categories.flatMap(c => c.feedback);
    return { total, categories, verdict, feedback, checks: allChecks, limitations, summary: feedback.length ? `${feedback.length} suggestion${feedback.length > 1 ? 's' : ''} for improvement.` : 'Outstanding system design! All criteria met.', model: 'source-reference' };
  }

  const api = { simulate, evaluate, simulateReference, evaluateReference, coach, validateGraph };
  root.DDIAStudioEngine = api;
  if (typeof module === 'object' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : window);
