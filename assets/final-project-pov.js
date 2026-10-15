/* A local product walkthrough; no platform, model, or tool requests are sent. */
(function(){
 'use strict';
 const player=document.getElementById('pov-player');if(!player)return;
 const root=document.documentElement,scenes=[...player.querySelectorAll('[data-pov-scene]')],buttons=[...player.querySelectorAll('[data-pov-select]')],play=player.querySelector('[data-pov-play]'),prev=player.querySelector('[data-pov-prev]'),next=player.querySelector('[data-pov-next]'),reduce=matchMedia('(prefers-reduced-motion: reduce)');
 let index=0,playing=false,timer=null,animation=null,due=0,remaining=4200,allowMotion=false;
 const pair=(fa,en)=>{const f=document.createElement('span'),e=document.createElement('span');f.className='fa';e.className='en';f.textContent=fa;e.textContent=en;return[f,e]};
 function label(){const select=player.querySelector('#pov-stage-select');select.value=String(index);[...select.options].forEach(o=>o.textContent=o.dataset[root.lang==='en'?'en':'fa']);play.querySelector('[data-pov-play-label]').replaceChildren(...pair(playing?'توقف':'پخش تجربه',playing?'Pause':'Play walkthrough'));play.setAttribute('aria-pressed',String(playing));prev.disabled=index===0;next.disabled=index===scenes.length-1;const ratio=document.createElement('bdi');ratio.dir='ltr';ratio.textContent=(index+1)+' / '+scenes.length;player.querySelector('[data-pov-counter]').replaceChildren(...pair('گام ','Step '),ratio)}
 function render(motion){animation?.cancel();animation=null;scenes.forEach((s,i)=>s.hidden=i!==index);buttons.forEach((b,i)=>b.setAttribute('aria-pressed',String(i===index)));player.dataset.povStep=String(index);remaining=4200;label();if(motion&&!reduce.matches){animation=scenes[index].animate([{opacity:.35},{opacity:1}],{duration:220,easing:getComputedStyle(root).getPropertyValue('--ease').trim(),fill:'both'})}}
 function pause(){if(playing)remaining=Math.max(0,due-performance.now());playing=false;clearTimeout(timer);timer=null;if(animation?.playState==='running')animation.pause();label()}
 function schedule(ms){clearTimeout(timer);due=performance.now()+ms;timer=setTimeout(()=>{if(!playing)return;if(index===scenes.length-1){pause();return}index++;render(allowMotion);schedule(4200)},ms)}
 function go(i,motion){pause();index=Math.max(0,Math.min(scenes.length-1,i));render(motion)}
 play.addEventListener('click',e=>{if(playing){pause();return}allowMotion=e.detail!==0&&!reduce.matches;if(index===scenes.length-1){index=0;render(allowMotion)}else if(animation?.playState==='paused'&&allowMotion){animation.play()}document.dispatchEvent(new Event('pov-play'));playing=true;label();schedule(remaining)});
 prev.addEventListener('click',e=>go(index-1,e.detail!==0));next.addEventListener('click',e=>go(index+1,e.detail!==0));player.querySelector('[data-pov-reset]').addEventListener('click',()=>go(0,false));buttons.forEach((b,i)=>b.addEventListener('click',e=>go(i,e.detail!==0)));
 player.querySelector('#pov-stage-select').addEventListener('change',e=>go(Number(e.target.value),false));
 document.addEventListener('visibilitychange',()=>{if(document.hidden)pause()});document.addEventListener('platform-flow-play',pause);addEventListener('hashchange',()=>{if(location.hash!=='#outcome')pause()});reduce.addEventListener('change',()=>{pause();render(false)});new MutationObserver(label).observe(root,{attributes:true,attributeFilter:['lang']});
 player.querySelector('.pov-step-nav').hidden=false;player.querySelector('.pov-mobile-nav').hidden=false;player.querySelector('.pov-toolbar').hidden=false;render(false);
})();
