/* DDIA Study — site behaviour: language + theme toggles, scroll reveal, TOC spy.
   file:// safe: no fetch, no modules, no dependencies. Defaults: EN, light. */
(function(){
  "use strict";
  var root = document.documentElement;
  var LANG_KEY = "ddia-lang", THEME_KEY = "ddia-theme";

  function titleFor(lang){
    return lang === "en" ? root.getAttribute("data-title-en") : root.getAttribute("data-title-fa");
  }
  function applyLang(lang){
    root.setAttribute("lang", lang);
    root.setAttribute("dir", lang === "en" ? "ltr" : "rtl");
    var t = titleFor(lang);
    if(t) document.title = t;
    document.querySelectorAll("[data-theme-toggle]").forEach(function(btn){
      btn.setAttribute("aria-label", lang === "en" ? "Toggle dark mode" : "تغییر حالت روشن و تیره");
    });
    try{ localStorage.setItem(LANG_KEY, lang); }catch(e){}
  }
  function applyTheme(theme){
    if(theme === "dark") root.setAttribute("data-theme", "dark");
    else root.removeAttribute("data-theme");
    try{ localStorage.setItem(THEME_KEY, theme); }catch(e){}
  }
  function init(){
    var savedLang = null, savedTheme = null;
    try{ savedLang = localStorage.getItem(LANG_KEY); savedTheme = localStorage.getItem(THEME_KEY); }catch(e){}
    var browserFa = false;
    try{
      var langs = navigator.languages || [navigator.language || ""];
      browserFa = langs.some(function(l){ return /^fa(-|$)/i.test(l); });
    }catch(e){}
    var lang = savedLang === "fa" ? "fa" : savedLang === "en" ? "en" :
      (root.getAttribute("data-default-lang") === "fa" || browserFa ? "fa" : "en");
    applyLang(lang);
    applyTheme(savedTheme === "dark" ? "dark" : "light");
    document.querySelectorAll("[data-lang-toggle]").forEach(function(btn){
      btn.addEventListener("click", function(){
        applyLang(root.getAttribute("lang") === "en" ? "fa" : "en");
      });
    });
    document.querySelectorAll("[data-theme-toggle]").forEach(function(btn){
      btn.addEventListener("click", function(){
        applyTheme(root.getAttribute("data-theme") === "dark" ? "light" : "dark");
      });
    });
  }

  /* entrance: blocks rise once as they enter the viewport */
  function reveal(){
    var els = document.querySelectorAll(".reveal");
    if(!els.length) return;
    if(!("IntersectionObserver" in window) || !window.matchMedia ||
       window.matchMedia("(prefers-reduced-motion: reduce)").matches){
      els.forEach(function(el){ el.classList.add("in"); });
      return;
    }
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        if(en.isIntersecting){ en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, {threshold:.08});
    els.forEach(function(el){ io.observe(el); });
  }

  /* TOC spy: marks the section currently on screen */
  function spy(){
    var toc = document.querySelector(".toc");
    if(!toc || !("IntersectionObserver" in window)) return;
    var links = Array.prototype.slice.call(toc.querySelectorAll('a[href^="#"]'));
    if(!links.length) return;
    var map = {};
    links.forEach(function(a){ map[a.getAttribute("href").slice(1)] = a; });
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(en){
        if(en.isIntersecting){
          links.forEach(function(a){ a.classList.remove("active"); });
          var a = map[en.target.id];
          if(a) a.classList.add("active");
        }
      });
    }, {rootMargin:"-30% 0px -60% 0px"});
    Object.keys(map).forEach(function(id){
      var s = document.getElementById(id);
      if(s) io.observe(s);
    });
  }

  /* Mobile: keep the table of contents from pushing the chapter below the fold. */
  function mobileToc(){
    var toc = document.querySelector(".toc");
    if(!toc || !window.matchMedia) return;
    if(!toc.id) toc.id = "chapter-toc";
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "toc-toggle";
    btn.setAttribute("aria-controls", toc.id);
    btn.setAttribute("aria-expanded", "false");
    btn.innerHTML = '<span class="fa">فهرست مطالب این فصل</span><span class="en">Chapter contents</span><span class="toc-chevron" aria-hidden="true">▾</span>';
    toc.parentNode.insertBefore(btn, toc);
    var mq = window.matchMedia("(max-width: 980px)");
    function sync(){
      var collapsed = mq.matches && btn.getAttribute("aria-expanded") !== "true";
      toc.classList.toggle("is-collapsed", collapsed);
    }
    btn.addEventListener("click", function(){
      var open = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", open ? "false" : "true");
      sync();
    });
    if(mq.addEventListener) mq.addEventListener("change", sync);
    else if(mq.addListener) mq.addListener(sync);
    sync();
  }

  document.addEventListener("DOMContentLoaded", function(){ init(); reveal(); spy(); mobileToc(); });
})();

/* Original study-site authorship; book and third-party rights remain separate. */
(function(){if(document.body.classList.contains('platform-page'))return;var script=document.querySelector('script[src$="assets/site.js"]');if(!script)return;var base=new URL('../',script.src),p=document.createElement('p');p.className='author-credit';var a=document.createElement('a');a.href=new URL('AUTHORS.md',base).href;a.textContent='hurdad ashouri';p.append('Written by ',a,' · AGPL-3.0-only');document.body.append(p)})();
