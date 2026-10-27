/* Focused model checks: node assets/check_studio_engine.cjs */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const data = require('./studio-data.js');
const engine = require('./studio-engine.js');
const node = (id, type, capacity = 10000, extra = {}) => ({ id, type, x: 0, y: 0, replicas: 1, capacity, config: {}, ...extra });
const graph = (nodes, pairs) => ({ nodes, edges: pairs.map(([source, target], i) => ({ id: `e${i}`, source, target, protocol: 'RPC' })) });
const stat = (run, id) => run.nodes.find(n => n.id === id);
const close = (actual, expected) => assert.ok(Math.abs(actual - expected) <= .02, `${actual} != ${expected}`);

assert.equal(data.components.length, 38);
assert.equal(new Set(data.components.map(c => c.id)).size, 38);
assert.equal(data.problems.length, 84);
assert.equal(data.problems.filter(p => p.chapter > 0).length, 49);
assert.equal(data.problems.filter(p => p.chapter === 0).length, 35);
assert.equal(data.tradeoffs.length, 14);
const audited = JSON.parse(fs.readFileSync(path.join(__dirname, 'exercise-audit.json'), 'utf8')).exercises;
for (const ex of audited) {
  const problem = data.problems.find(p => p.id === `ch${ex.chapter}-ex${ex.number}`);
  assert.ok(problem);
  assert.equal(problem.promptFa, ex.prompt);
  assert.equal(problem.promptEn, ex.prompt_en);
  assert.deepEqual(problem.signalsEn, ex.signals_en);
  assert.ok(fs.existsSync(path.join(__dirname, '../', problem.folder, 'solutions.html')));
}
for (const p of data.problems) {
  assert.ok(p.titleFa && p.titleEn && p.promptFa && p.promptEn);
  assert.ok(engine.validateGraph(p.starter).valid, `${p.id} starter`);
  assert.ok(engine.validateGraph(p.reference).valid, `${p.id} reference`);
  assert.ok(engine.simulate(p.reference).valid, `${p.id} simulation`);
}

// Fan-out duplicates dependency work; load balancers instead split requests.
const nodes = [node('c', 'client'), node('a', 'app-server'), node('b', 'sql-db'), node('d', 'sql-db')];
let g = graph(nodes, [['c', 'a'], ['a', 'b'], ['a', 'd']]);
let run = engine.simulate(g, { qps: 800 });
assert.equal(stat(run, 'b').incomingQPS, 800);
assert.equal(stat(run, 'd').incomingQPS, 800);
assert.equal(run.throughput, 800);
g.nodes[1].type = 'load-balancer';
run = engine.simulate(g, { qps: 800 });
assert.equal(stat(run, 'b').incomingQPS, 400);
assert.equal(stat(run, 'd').incomingQPS, 400);
assert.equal(run.throughput, 800);

// Fan-in is accumulated before the shared dependency is evaluated.
g = graph([node('c', 'client'), node('lb', 'load-balancer'), node('a', 'app-server'), node('b', 'app-server'), node('db', 'sql-db', 600)], [['c', 'lb'], ['lb', 'a'], ['lb', 'b'], ['a', 'db'], ['b', 'db']]);
run = engine.simulate(g, { qps: 800 });
assert.equal(stat(run, 'db').incomingQPS, 800);
assert.equal(run.throughput, 600);
assert.equal(stat(run, 'db').status, 'overloaded');

// Capacity zero remains zero; downstream cannot report successful throughput.
g = graph([node('c', 'client'), node('db', 'sql-db', 0)], [['c', 'db']]);
run = engine.simulate(g, { qps: 100 });
assert.equal(stat(run, 'db').capacity, 0);
assert.equal(run.throughput, 0);
assert.equal(run.latencyMs, null);
assert.equal(stat(run, 'db').utilization, null);
run = engine.simulate(g, { qps: 0 });
assert.equal(run.throughput, 0);
assert.equal(stat(run, 'db').incomingQPS, 0);

// Failure injection does not invent automatic failover on a balancer.
g = graph([node('c', 'client'), node('lb', 'load-balancer'), node('a', 'app-server'), node('b', 'app-server')], [['c', 'lb'], ['lb', 'a'], ['lb', 'b']]);
run = engine.simulate(g, { qps: 1000, failureNode: 'a' });
assert.equal(stat(run, 'a').status, 'failed');
assert.equal(run.throughput, 500);
assert.ok(run.warnings.some(w => w.includes('rerouting')));

// Cache misses include writes: 80% reads x 75% hit => 40% reach the DB.
g = graph([node('c', 'client'), node('cache', 'cache'), node('db', 'sql-db')], [['c', 'cache'], ['cache', 'db']]);
run = engine.simulate(g, { qps: 1000, readRatio: .8, cacheHitRate: .75 });
assert.equal(stat(run, 'db').incomingQPS, 400);
assert.equal(run.throughput, 1000);
run = engine.simulate(g, { qps: 1000, readRatio: .8, cacheHitRate: .75, failureNode: 'db' });
assert.equal(run.throughput, 600);
run = engine.simulate(g, { qps: 1000, readRatio: 0, cacheHitRate: 1 });
assert.equal(stat(run, 'db').incomingQPS, 1000);
run = engine.simulate(g, { qps: 1000, readRatio: 1, cacheHitRate: 1 });
assert.equal(stat(run, 'db').incomingQPS, 0);
assert.equal(run.latencyMs, 1); // cache latency comes from the component catalog

// A cache without an origin cannot invent a response for misses or writes.
g = graph([node('c', 'client'), node('cache', 'cache')], [['c', 'cache']]);
run = engine.simulate(g, { qps: 1000, readRatio: .8, cacheHitRate: .75 });
assert.equal(run.throughput, 600);
assert.ok(run.warnings.some(w => w.includes('no connected origin')));

// The queue reports growth separately from its intake capacity.
g = graph([node('c', 'client'), node('q', 'queue', 5000), node('worker', 'worker', 600)], [['c', 'q'], ['q', 'worker']]);
run = engine.simulate(g, { qps: 1000 });
assert.equal(stat(run, 'q').queueBacklogQPS, 400);
assert.equal(run.throughput, 600);
assert.ok(run.warnings.some(w => w.includes('backlog')));

// A cycle fails closed; partial topological calculations must never look valid.
g = graph([node('a', 'app-server'), node('b', 'sql-db')], [['a', 'b'], ['b', 'a']]);
run = engine.simulate(g);
assert.equal(run.valid, false);
assert.equal(run.throughput, null);
assert.equal(run.latencyMs, null);
assert.ok(run.warnings.some(w => /cyclic/i.test(w)));

// Root selection ignores unconnected objects when a client entry exists.
g = graph([node('c', 'client'), node('app', 'app-server'), node('db', 'sql-db'), node('unused', 'sql-db')], [['c', 'app'], ['app', 'db']]);
run = engine.simulate(g, { qps: 1000 });
assert.equal(stat(run, 'unused').incomingQPS, 0);
assert.equal(stat(run, 'unused').active, false);
assert.equal(run.throughput, 1000);

// Invalid imports are rejected before a caller can put their data on a canvas.
for (const bad of [
  null, [], { nodes: [], edges: 'wrong' },
  graph([node('c', 'not-a-component')], []),
  graph([node('c', 'client', -1)], []),
  graph([node('c', 'client', 10, { replicas: 0 })], []),
  graph([node('c', 'client', 10, { latency: Infinity })], []),
  graph([node('c', 'client'), node('c', 'cache')], []),
  graph([node('c', 'client')], [['c', 'missing']]),
  graph([node('c', 'client')], [['c', 'c']]),
  graph([node('c', 'client', 10, { config: { notes: { html: '<script>' } } })], []),
  JSON.parse('{"nodes":[],"edges":[],"__proto__":{"polluted":true}}'),
  JSON.parse('{"nodes":[{"id":"c","type":"client","config":{"constructor":"bad"}}],"edges":[]}'),
]) {
  assert.equal(engine.validateGraph(bad).valid, false, JSON.stringify(bad));
  assert.equal(engine.simulate(bad).valid, false);
}
assert.equal({}.polluted, undefined);

// Adding disconnected components never improves this structural score.
g = graph([node('c', 'client'), node('app', 'app-server', 2000), node('db', 'sql-db', 2000)], [['c', 'app'], ['app', 'db']]);
let score = engine.evaluate(g, data.problems[0], { qps: 1000 });
assert.equal(score.categories.length, 5);
assert.equal(score.categories.reduce((sum, c) => sum + c.score, 0), score.total);
assert.ok(score.limitations.some(s => s.includes('not proof')));
const before = score.total;
g.nodes.push(node('extra', 'cache'));
assert.ok(engine.evaluate(g, {}, { qps: 1000 }).total <= before);
assert.ok(engine.coach('failure', g).startsWith('Local rule-based coach'));
assert.ok(engine.coach('خرابی', g, {}, { lang: 'fa' }).includes('محلی'));
console.log('Studio model checks passed: 84 exercises, 38 components, propagation, cache, failures, queues, cycles, imports and rubric.');
