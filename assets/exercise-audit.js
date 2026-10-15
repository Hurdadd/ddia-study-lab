/* Static filtering; no network or modules, safe from file://. */
(function(){
  'use strict';
  var level=document.getElementById('audit-level');
  if(!level)return;
  var priority=document.getElementById('audit-priority'),search=document.getElementById('audit-search');
  var items=Array.from(document.querySelectorAll('.audit-item'));
  function normalize(text){return text.toLocaleLowerCase().replace(/ي/g,'ی').replace(/ك/g,'ک').replace(/[\u200c\u200d]/g,' ');}
  function filter(){
    var query=normalize(search.value.trim()),count=0;
    items.forEach(function(item){
      var match=(!level.value||item.dataset.level===level.value)&&(!priority.value||item.dataset.priority===priority.value)&&(!query||normalize(item.dataset.search).includes(query));
      item.hidden=!match;if(match)count++;
    });
    document.querySelectorAll('.audit-chapter').forEach(function(section){section.hidden=!Array.from(section.querySelectorAll('.audit-item')).some(function(item){return !item.hidden;});});
    document.getElementById('audit-count').textContent=count+' / '+items.length;
    document.getElementById('audit-empty').hidden=count!==0;
  }
  [level,priority,search].forEach(function(el){el.addEventListener('input',filter);});
  document.getElementById('audit-reset').addEventListener('click',function(){level.value='';priority.value='';search.value='';filter();search.focus();});
  function target(){
    var item=document.getElementById(location.hash.slice(1));
    if(item&&item.classList.contains('audit-item')){
      level.value='';priority.value='';search.value='';filter();
      var details=item.querySelector('details');if(details)details.open=true;
      item.scrollIntoView();
    }
  }
  window.addEventListener('hashchange',target);filter();target();
})();
