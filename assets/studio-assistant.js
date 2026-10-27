/* Capacity arithmetic and reviewable assistant edits; no model call on page load. */
(function () {
  'use strict';
  const api = window.DDIAStudio, engine = window.DDIAStudioEngine, data = window.DDIAStudioData;
  if (!api || !engine || !data) return;
  const $ = s => document.querySelector(s), fa = () => document.documentElement.lang === 'fa';
  const t = (en, persian) => fa() ? persian : en;
  const n = v => Number(v).toLocaleString(fa() ? 'fa-IR' : 'en-US', {maximumFractionDigits: 2});
  const element = (tag, text, attrs = {}) => { const el = document.createElement(tag); if (text !== null) el.textContent = text; Object.entries(attrs).forEach(([k,v]) => el.setAttribute(k,v)); return el; };
  function bilingual(el, en, persian) { el.append(element('span', persian, {class:'fa'}), element('span', en, {class:'en'})); return el; }
  function addPanel(name, en, persian) {
    let panel = $('#panel-'+name);
    if (!panel) {
      panel = element('div', null, {id:'panel-'+name,class:'workbench-panel',role:'tabpanel',hidden:''});
      (name==='assistant' ? $('#assistant-drawer') : $('.workbench')).append(panel);
    }
    if(name==='capacity'&&!document.querySelector('[data-panel="capacity"]')) {
      const tab=bilingual(element('button',null,{role:'tab','aria-selected':'false','data-panel':name}),en,persian);
      const before=document.querySelector('[data-panel="tradeoffs"]');
      if(before)before.before(tab);else $('.workbench-tabs').append(tab);
      tab.addEventListener('click',()=>api.setPanel(name));
    }
    return panel;
  }
  let capacity = {dau:100000000, requests:20, writes:20, size:5, peak:3, retention:365};
  try { const v = JSON.parse(localStorage.getItem('ddia-studio-capacity-v2')); if(v && typeof v === 'object') for(const k of Object.keys(capacity)) if(Number.isFinite(v[k]) && v[k]>=0) capacity[k]=v[k]; } catch (_) {}
  const capacityPanel = addPanel('capacity', 'Capacity planning', 'برآورد ظرفیت');
  capacityPanel.append(bilingual(element('h2',null),'Capacity estimation','برآورد ظرفیت'));
  const form = element('form',null,{class:'capacity-inputs',id:'capacity-form'}), inputs = {};
  const fields = [
    ['dau','Daily active users','کاربر فعال روزانه',1e9,1],
    ['requests','Average requests / user / day','میانگین درخواست هر کاربر در روز',100000,1],
    ['writes','Writes (%)','نوشتن (%)',100,1],
    ['size','Average data per request (KB)','حجم میانگین هر درخواست (KB)',100000,1],
  ];
  for(const [key,en,persian,max,step] of fields) {
    const label=bilingual(element('label',null),en,persian), input=element('input',null,{id:'capacity-'+key,type:'number',min:key==='peak'?'1':'0',max:String(max),step:String(step),required:''});
    input.value=capacity[key];inputs[key]=input;label.append(input);
    const presets={dau:[1000000,10000000,100000000,1000000000],requests:[5,20,50,100],writes:[10,20,50,80],size:[1,5,50,500]};
    const row=element('div',null,{class:'capacity-presets'});
    for(const value of presets[key]) {
      const display=key==='dau'?(value>=1e9?'1B':value/1e6+'M'):key==='writes'?value+'%':key==='size'?value+' KB':String(value);
      const button=element('button',display,{type:'button'});button.addEventListener('click',()=>{input.value=value;renderCapacity();});row.append(button);
    }
    label.append(row);form.append(label);
  }
  capacityPanel.append(form);
  const results=element('div',null,{id:'capacity-results',class:'capacity-results','aria-live':'polite'});
  capacityPanel.append(results);
  let peakQPS=0;
  function renderCapacity() {
    results.replaceChildren();
    const valid=form.checkValidity();
    if(!valid) {results.textContent=t('Enter valid, non-negative assumptions.','فرض‌ها را با عدد معتبر و نامنفی وارد کن.');return;}
    for(const k of Object.keys(inputs)) capacity[k]=Number(inputs[k].value);
    try {localStorage.setItem('ddia-studio-capacity-v2',JSON.stringify(capacity));}catch(_){}
    const daily=capacity.dau*capacity.requests, qps=daily/86400, bytes=capacity.size*1024, storage=daily*(capacity.writes/100)*bytes;
    peakQPS=qps*capacity.peak;
    const list=[
      [t('Requests / day','درخواست در روز'),n(daily),'DAU × requests/user/day'],
      [t('Average QPS','QPS میانگین'),n(qps),'requests/day ÷ 86,400'],
      [t('Peak QPS','QPS اوج'),n(peakQPS),'average QPS × peak multiplier'],
      [t('Storage / day','ذخیره‌سازی در روز'),n(storage/1e12)+' TB','requests/day × write ratio × KB × 1,024 ÷ 10¹²'],
      [t('Storage / year','ذخیره‌سازی در سال'),n(storage*365/1e12)+' TB','bytes/day × 365 ÷ 10¹²'],
      [t('Peak bandwidth','پهنای باند اوج'),n(peakQPS*bytes*8/1e9)+' Gbit/s','peak QPS × bytes/request × 8 ÷ 10⁹'],
    ];
    for(const [label,value,formula] of list) {const item=element('div',null),term=element('h3',label),out=element('output',value,{dir:'auto'}),eq=element('code',formula,{dir:'ltr'});item.append(term,out,eq);results.append(item);}
    results.append(element('p',t('Reference formulas use a 3× peak, 365-day storage and 1 KB = 1,024 bytes. Replicas, indexes, metadata and compression are excluded.','فرمول مرجع: اوج ۳ برابر، ذخیرهٔ ۳۶۵ روز و هر KB برابر ۱۰۲۴ بایت است. replica، ایندکس، فراداده و فشرده‌سازی حساب نمی‌شوند.'),{class:'capacity-boundary'}));
  }
  form.addEventListener('input',renderCapacity);form.addEventListener('submit',e=>e.preventDefault());
  renderCapacity();

  new MutationObserver(()=>renderCapacity()).observe(document.documentElement,{attributes:true,attributeFilter:['lang']});
})();
