'use strict';
const assert = require('node:assert/strict');
const D = require('./studio-data.js'), E = require('./studio-engine.js');
for (const p of D.problems) {
  if (p.chapter) {
    assert.ok(p.lesson.steps.length, `${p.id}: authored reasoning`);
    assert.ok(p.lesson.diagrams.length, `${p.id}: authored figures`);
    for (const figure of p.lesson.diagrams) if (figure.editableGraph) {
      const validation = E.validateGraph(figure.editableGraph);
      assert.ok(validation.valid, `${p.id} ${figure.href}: ${validation.errors}`);
      assert.equal(E.simulate(figure.editableGraph).valid, false);
    }
  }
  const result = E.evaluate(p.reference, p, { qps: 1000 });
  assert.equal(result.total, 100, `${p.id}: reference coverage must be complete`);
  assert.equal(result.mode, 'exercise-coverage');
  assert.ok(result.manualReview.length, `${p.id}: reasoning needs a separate review`);
  assert.equal(E.evaluate({ nodes: [], edges: [] }, p).total, 0);
  if (p.reference.edges.length) {
    assert.ok(E.evaluate({ ...p.reference, edges: [] }, p).total < 100, `${p.id}: missing arrows must matter`);
  }
}
console.log('All 84 references cover their exercise rubric; empty and disconnected answers lose coverage.');
const asyncGraph = { nodes: [
  { id: 'client', type: 'client', config: {} },
  { id: 'app', type: 'app-server', capacity: 2000, config: {} },
  { id: 'worker', type: 'worker', capacity: 0, config: {} },
], edges: [
  { id: 'request', source: 'client', target: 'app', protocol: 'HTTP', label: 'Submit' },
  { id: 'async', source: 'app', target: 'worker', kind: 'background', protocol: 'Async' },
] };
let run = E.simulate(asyncGraph, { qps: 1000, failureNode: 'worker' });
assert.equal(run.throughput, 1000, 'Out-of-band failures cannot break synchronous throughput');
assert.equal(run.nodes.find(n => n.id === 'worker').active, false);
assert.ok(run.warnings.some(w => w.includes('have not been simulated')));
asyncGraph.edges[1].kind = 'request';
run = E.simulate(asyncGraph, { qps: 1000, failureNode: 'worker' });
assert.equal(run.throughput, 0, 'A failed request dependency must break throughput');
assert.equal(E.validateGraph({ ...asyncGraph, edges: [{ ...asyncGraph.edges[0], kind: 'bogus' }] }).valid, false);
const label = E.validateGraph(asyncGraph).graph.edges[0].label;
assert.equal(label, 'Submit', 'Transport and operation labels must survive normalization');
console.log('Background failures, request failures, edge labels and flow validation passed.');
