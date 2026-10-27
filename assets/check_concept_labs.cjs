/* Semantic regression checks for the local chapter models (node, no DOM). */
'use strict';
const assert = require('node:assert/strict');
const {models, transition} = require('./concept-labs.js');
function run(id, actions) {
  let state=models[id].initial();
  for(const action of actions){
    const before=JSON.stringify(state);
    const next=transition(id,state,action);
    assert.equal(JSON.stringify(state),before,`${id}/${action} mutated history`);
    state=next;
  }
  return state;
}
assert.equal(Object.keys(models).length,43);
let s=run('outbox',['direct','commit','crash','recover']);assert.equal(s.order,1);assert.equal(s.search,0);
s=run('outbox',['outbox','commit','crash','recover']);assert.equal(s.search,1);assert.equal(s.pending,false);
s=run('queue',['one','burst','tick']);assert.equal(s.queue,5);assert.equal(s.done,1);
s=run('queue',['three','burst','tick','tick']);assert.equal(s.queue,0);assert.equal(s.tick,2);
s=run('models',['join','rename','read']);assert.equal(s.b,'Sara');
s=run('models',['embed','rename','read']);assert.equal(s.b,'Mina');s=transition('models',s,'repair');assert.equal(s.b,'Sara');
s=run('wal',['ram','write','crash','recover','flush']);assert.equal(s.mem,null);assert.equal(s.disk,null);
s=run('wal',['wal','write','crash','recover','flush']);assert.equal(s.mem,7);assert.equal(s.disk,7);
s=run('schema',['preserve','decode','edit','read']);assert.equal(s.result.locale,'fa');assert.equal(s.result.name,'Sara');
s=run('schema',['drop','decode','edit','read']);assert.equal(s.result.locale,undefined);
s=run('replication',['write','hold','follower']);assert.equal(s.read,0);assert.equal(s.leader,1);s=transition('replication',s,'deliver');assert.equal(s.follower,1);
s=run('replication',['write','hold','leader']);assert.equal(s.read,1);assert.equal(s.follower,0);
s=run('failover',['async','write','crash','promote']);assert.equal(s.follower,0);assert.equal(s.acked,true);s=transition('failover',s,'rejoin');assert.equal(s.lost,true);assert.equal(s.leader,0);
s=run('failover',['sync','write','crash','promote','rejoin']);assert.equal(s.follower,1);assert.equal(s.lost,false);
s=run('monotonic',['random','first','second']);assert.deepEqual(s.seen,[1,0]);
s=run('monotonic',['sticky','first','second','catchup']);assert.deepEqual(s.seen,[1,1]);assert.equal(s.b,1);
for(const [w,r,fresh] of [['w1','r1',0],['w1','r2',0],['w2','r1',0],['w2','r2',1]]){s=run('leaderless',[w,r,'write','read']);assert.equal(s.result,fresh,`${w}${r}`);}
s=run('hotkey',['add','send','tick']);assert.deepEqual(s.queues,[6,0,0]);
s=run('hotkey',['salt','send','tick','tick']);assert.equal(s.done.reduce((a,b)=>a+b,0),8);assert.equal(s.tick,2);
s=run('seat',['blind','read','a','b']);assert.equal(s.bookings.length,2);assert.equal(s.remaining,0);
s=run('seat',['guard','read','a','b']);assert.deepEqual(s.bookings,['A']);assert.equal(s.bResult,'rejected');
s=run('retry',['send','drop']);assert.equal(s.knowledge,'outcome unknown');assert.equal(s.charges,1);assert.equal(transition('retry',s,'same').charges,1);assert.equal(transition('retry',s,'new').charges,2);
s=run('quorum',['partition','minority']);assert.equal(s.committed.some(Boolean),false);s=transition('quorum',s,'heal');assert.deepEqual(s.logs,[0,0,0]);
s=run('quorum',['partition','majority']);assert.equal(s.committed.filter(Boolean).length,2);s=transition('quorum',s,'heal');assert.equal(s.committed.every(Boolean),true);
s=run('batch',['append','run','crash','retry']);assert.deepEqual(s.output,['a','b','a','b']);
s=run('batch',['stage','run','crash','retry']);assert.deepEqual(s.output,['a','b']);
s=run('consumer',['plain','apply','crash','redeliver']);assert.equal(s.count,2);assert.equal(s.acked,true);
s=run('consumer',['dedup','apply','crash','redeliver']);assert.equal(s.count,1);assert.deepEqual(s.seen,[9]);
s=run('rebuild',['corrupt','view']);assert.equal(s.total,0);
s=run('rebuild',['corrupt','source','event','event']);assert.equal(s.total,30);assert.equal(s.replayed,2);
s=run('privacy',['naive','delete','restore']);assert.equal(s.consent,false);assert.equal(s.live,true);
s=run('privacy',['guard','delete','restore']);assert.equal(s.live,false);assert.equal(s.backup,true);
s=run('olap',['primary','report','checkout']);assert.equal(s.checkout,'slow');
s=run('olap',['warehouse','report','checkout','etl']);assert.equal(s.checkout,'fast');assert.equal(s.fresh,false);
s=run('fanout',['onwrite','post','open']);assert.deepEqual([s.writes,s.reads],[3,1]);s=transition('fanout',s,'celebrity');assert.equal(s.writes,1000);
s=run('fanout',['onread','post','open']);assert.deepEqual([s.writes,s.reads],[1,3]);
s=run('eventlog',['events','ops','fix']);assert.equal(s.fixed,100);
s=run('eventlog',['state','ops','fix']);assert.equal(s.fixed,'?');
s=run('scan',['noindex','write','get']);assert.equal(s.reads,4);assert.equal(s.value,3);
s=run('scan',['hash','write','get']);assert.equal(s.reads,1);assert.equal(s.value,3);
s=run('rolling',['required','read']);assert.match(s.result,/error/);
s=run('rolling',['optional','read']);assert.match(s.result,/basic/);
s=run('rebalance',['mod','add']);assert.equal(s.moved,9);
s=run('rebalance',['fixed','add']);assert.equal(s.moved,3);
s=run('dirty',['ru','debit','read','abort']);assert.equal(s.seen,50);assert.equal(s.balance,100);
s=run('dirty',['rc','debit','read','abort']);assert.equal(s.seen,100);
s=run('fencing',['plain','lockA','pause','wake']);assert.equal(s.value,'A');
s=run('fencing',['fence','lockA','pause','wake']);assert.equal(s.value,'B');assert.equal(s.rejected,true);
s=run('lamport',['wall','a','b','merge']);assert.equal(s.winner,'v1');
s=run('lamport',['lamport','a','b','merge']);assert.equal(s.winner,'v2');
s=run('combiner',['plain','map','shuffle','reduce']);assert.equal(s.sent,6);
s=run('combiner',['combine','map','shuffle','reduce']);assert.equal(s.sent,2);assert.equal(s.result,'a=4, b=2');
s=run('logbroker',['queue','publish','consume','join']);assert.deepEqual(s.c2,[]);
s=run('logbroker',['log','publish','consume','join']);assert.deepEqual(s.c2,['m1','m2','m3']);
s=run('unique',['split','send','process']);assert.deepEqual(s.results,['accepted','accepted']);
s=run('unique',['partition','send','process']);assert.deepEqual(s.results,['accepted','rejected']);
s=run('feedback',['top','round','round']);assert.deepEqual(s.rec,[16,5]);
s=run('feedback',['audit','round','round']);assert.deepEqual(s.rec,[12,11]);
s=run('rpc',['local','call','fail']);assert.match(s.outcome,/together/);s=run('rpc',['remote','call','fail']);assert.match(s.outcome,/timeout/);
s=run('tail',['mean','measure','alert']);assert.equal(s.alert,false);s=run('tail',['p99','measure','alert']);assert.equal(s.alert,true);
s=run('hops',['tables','two','any']);assert.match(s.shape,/RECURSIVE/);s=run('hops',['graph','two','any']);assert.match(s.shape,/\*\]/);
s=run('btree',['nowal','insert','crash','recover']);assert.equal(s.found,false);s=run('btree',['wal','insert','crash','recover']);assert.equal(s.found,true);
s=run('rename',['byname','rename','old']);assert.match(s.read,/missing/);s=run('rename',['bytag','rename','old']);assert.match(s.read,/Mina/);
s=run('secondary',['local','write','search']);assert.deepEqual([s.writes,s.asked],[1,3]);s=run('secondary',['global','write','search']);assert.deepEqual([s.writes,s.asked],[2,1]);
s=run('twopc',['durable','prepare','crash','restart']);assert.equal(s.a,'committed');assert.equal(s.locks,false);s=run('twopc',['volatile','prepare','crash','restart']);assert.equal(s.a,'prepared');assert.equal(s.locks,true);
s=run('timeout',['short','stall']);assert.match(s.verdict,/wrongly/);s=run('timeout',['long','stall','crash']);assert.equal(s.outage,10);
s=run('ephemeral',['session','acquire','crash','wait']);assert.equal(s.owner,'B');s=run('ephemeral',['plain','acquire','crash','wait']);assert.equal(s.owner,'A');
s=run('rerun',['immutable','run','append','retry']);assert.equal(s.out,3);s=run('rerun',['mutable','run','append','retry']);assert.equal(s.out,4);
s=run('ordering',['rr','send','read']);assert.equal(s.seen[0],'delete u1');s=run('ordering',['key','send','read']);assert.equal(s.seen[0],'create u1');
s=run('reconcile',['streamonly','live','late','night']);assert.equal(s.batch,null);s=run('reconcile',['both','live','late','night']);assert.equal(s.batch,12);
s=run('proxy',['drop','train','measure']);assert.match(s.rates,/cannot/);s=run('proxy',['audit','train','measure','fix']);assert.equal(s.fixed,true);
// Exhaust every reachable branch, including terminal states and invalid actions.
let states=0, transitions=0;
for(const [id,model]of Object.entries(models)){
  const queue=[model.initial()],seen=new Set();
  while(queue.length){
    const state=queue.shift(), key=JSON.stringify(state);
    if(seen.has(key))continue;seen.add(key);states++;
    assert.equal(model.view(state).length,3);
    assert.ok(state.message.en&&state.message.fa);
    for(const action of model.actions){
      if(action.when(state)){queue.push(transition(id,state,action.id));transitions++;}
      else assert.throws(()=>transition(id,state,action.id),/Unavailable action/);
    }
  }
}
console.log(`Chapter labs passed: ${Object.keys(models).length} models, ${states} reachable states, ${transitions} valid transitions; unsafe/safe branches and history immutability verified.`);
