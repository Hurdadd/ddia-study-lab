/* Sizes each chapter-exercise reference so it carries the default 1000 QPS, then writes reference_sizing.json
   (node id -> replicas) for build_studio_data.py. Run after editing exercise_references.py and rebuilding once. */
const vm=require('vm'),fs=require('fs');const w={};w.window=w;
vm.runInNewContext(fs.readFileSync(__dirname+'/studio-data.js','utf8'),w);vm.runInNewContext(fs.readFileSync(__dirname+'/studio-engine.js','utf8'),w);
const {problems}=w.DDIAStudioData,E=w.DDIAStudioEngine,out={};
for(const p of problems.filter(x=>x.chapter)){
  const g=p.reference;
  for(let i=0;i<40;i++){
    const r=E.simulate(g,{qps:1000});
    if(r.valid===false)throw new Error(p.id+' invalid '+JSON.stringify(r.errors||r.warnings)+' i='+i+' '+JSON.stringify(g.nodes.map(n=>n.replicas)));
    const worst=r.nodes.filter(n=>n.active&&n.utilization>0.8).sort((a,b)=>b.utilization-a.utilization)[0];
    if(!worst)break;
    const node=g.nodes.find(n=>n.id===worst.id);if(node.replicas>=12)break;node.replicas++;
  }
  out[p.id]=Object.fromEntries(g.nodes.map(n=>[n.id,n.replicas]));
}
fs.writeFileSync(__dirname+'/reference_sizing.json',JSON.stringify(out,null,1));
console.log('sized',Object.keys(out).length);
