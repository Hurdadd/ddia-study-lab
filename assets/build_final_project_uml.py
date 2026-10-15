from pathlib import Path
from html import escape
out=Path(__file__).resolve().parent.parent/'final-project/diagrams'
def text(x,y,s,size=14,anchor='start',weight=400):return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{escape(s)}</text>'
def box(x,y,w,h,name,lines,fill='#d3c3f2',stereo=None):
 s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="#71685e"/>'
 if stereo:s+=text(x+w/2,y+26,stereo,13,'middle')
 title_y=y+48 if stereo else y+34
 s+=text(x+w/2,title_y,name,18,'middle',800)
 s+=f'<line x1="{x}" y1="{title_y+15}" x2="{x+w}" y2="{title_y+15}" stroke="#71685e"/>'
 for i,line in enumerate(lines):s+=text(x+16,title_y+44+i*26,line)
 return s

def arrow(x1,y1,x2,y2,label,tx,ty,dashed=False):
 return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#302828" stroke-width="1.7" marker-end="url(#arr)"'+(' stroke-dasharray="6 4"' if dashed else '')+'/>'+text(tx,ty,label,13,'middle')
def finish(slug,title,W,H,svg):
 head='''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'''+escape(title)+'''</title><style>body{margin:0;background:#f7f2e8;color:#302828;font-family:system-ui,sans-serif}.stage{max-width:1240px;margin:auto;padding:12px}svg{width:100%;height:auto;display:block}text{fill:#302828;font-family:system-ui,sans-serif}</style></head><body><div class="stage">'''
 defs='<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 1L9 5L0 9" fill="none" stroke="#302828" stroke-width="1.5"/></marker></defs>'
 (out/f'{slug}.html').write_text(head+f'<svg width="100%" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(title)}"><title>{escape(title)}</title>'+defs+svg+'</svg></div></body></html>')
s=text(590,48,'Tenant isolation lives in the data model',28,'middle',800)+text(590,82,'UML associations: tenant-scoped keys, pinned versions, durable execution',16,'middle')
s+=box(40,130,300,150,'Tenant',['tenant_id: UUID [PK]','policy_epoch: long','quota_policy_id: UUID'],'#c3ceff')
s+=box(440,130,300,150,'Application',['tenant_id + app_id [PK]','active_release_id: UUID','definition_version: long'],'#c3ceff')
s+=box(840,130,300,150,'Run',['tenant_id + run_id [PK]','release_id: UUID [FK]','owner_epoch + status'],'#d3c3f2')
s+=box(40,390,300,175,'DocumentRevision',['tenant + source + entity','revision: long [PK part]','acl_revision: long','deleted + content_hash'],'#bfe6c9')
s+=box(440,390,300,175,'Release',['tenant_id + release_id [PK]','app_id: UUID [FK]','manifest_hash: string','immutable: true'],'#ffe08a')
s+=box(840,390,300,175,'Step',['tenant + run + step [PK]','intent_hash: string','attempt + owner_epoch','result_ref: URI?'],'#d3c3f2')
s+=box(40,690,300,175,'Evidence',['tenant + evidence_id [PK]','source_revision: string?','tool_call_id: UUID? [FK]','interval + artifact_hash'],'#bfe6c9')
s+=box(440,690,300,175,'ToolCall',['tenant + operation_key [PK]','run_id + step_id [FK]','input_hash + state','external_status_ref: URI?'],'#ffcfb8')
s+=box(840,690,300,175,'RunEvent',['tenant + run + seq [PK]','step_id: UUID? [FK]','event_type: string','event_version: long'],'#d3c3f2')
s+=arrow(340,205,440,205,'1 / 0..*',390,188)
s+=arrow(740,205,840,205,'1 / 0..*',790,188)
s+=arrow(190,280,190,390,'1 / 0..*',240,342)
s+=arrow(590,280,590,390,'1 / 1..*',640,342)
s+=arrow(990,280,990,390,'1 / 0..*',1040,342)
s+=arrow(190,565,190,690,'0..1 / 0..*',252,636)
s+=arrow(990,565,990,690,'1 / 0..*',1042,636)
s+='<path d="M840 480H790V650H590V690" fill="none" stroke="#302828" stroke-width="1.7" marker-end="url(#arr)"/>'+text(720,635,'Step 1 / ToolCall 0..*',13,'middle')
s+=arrow(440,778,340,778,'1 / 0..*',390,673)
s+=text(590,910,'Every foreign key includes tenant_id. Evidence may also refer to queried telemetry.',14,'middle')
finish('data-model','UML data model: tenant isolation and durable records',1180,940,s)
s=text(620,48,'Applications depend on platform contracts',28,'middle',800)+text(620,83,'UML dependency arrows point toward the required interface',16,'middle')
s+=box(40,140,340,200,'IncidentInvestigator',['start(input): RunHandle','hypothesize(evidence): Intent','report(results): Report'],'#ffcfb8','«application»')
s+=box(450,140,340,200,'RuntimePort',['submit(app, key): RunHandle','resume(run, epoch): Step','cancel(run): Outcome'],'#d3c3f2','«interface»')
s+=box(860,140,340,200,'ModelPort',['generate(request): Response','stream(request): TokenStream','usage(attempt): Usage'],'#c3ceff','«interface»')
s+=box(40,450,340,200,'EvaluationRunner',['run(dataset, release): Trial','score(trial): ScoreSet','compare(baseline): Gate'],'#ffe08a','«component»')
s+=box(450,450,340,200,'ToolPort',['validate(intent): Decision','execute(scoped): Evidence','reconcile(key): Outcome'],'#ffcfb8','«interface»')
s+=box(860,450,340,200,'ContextPort',['search(scope): Evidence[]','getRevision(id): Revision','authorize(ref): Decision'],'#bfe6c9','«interface»')
s+=arrow(380,240,450,240,'uses',415,222,True)
s+=arrow(790,240,860,240,'uses',825,222,True)
s+=arrow(620,340,620,450,'uses',656,400,True)
s+=arrow(790,550,860,550,'uses',825,532,True)
s+='<path d="M210 450V391H525V340" fill="none" stroke="#302828" stroke-dasharray="6 4" marker-end="url(#arr)"/>'+text(355,379,'runs the same application contract',13,'middle')
s+=text(620,703,'Adapters implement the ports; the application does not hold provider credentials.',14,'middle')
finish('component-uml','Component UML: reusable AI platform interfaces',1240,735,s)
print('Authored two UML SVG pages')
