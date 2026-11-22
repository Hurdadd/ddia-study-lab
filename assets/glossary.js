/* DDIA Study — inline glossary.
   Marks the first few mentions of each technical term in a chapter with a dotted
   underline, previews a one-line definition on hover/focus, and links the term to
   its full entry (everyday analogy, then the technical account) on the glossary page.
   file:// safe: no fetch, no modules, no dependencies. Data comes from glossary-data.js. */
(function () {
  "use strict";

  var G = window.DDIA_GLOSSARY;
  if (!G || !G.terms) return;

  var docEl = document.documentElement;
  var terms = G.terms;
  var order = G.order || Object.keys(terms);

  function lang() { return docEl.getAttribute("lang") === "fa" ? "fa" : "en"; }
  function pick(obj, field) { return obj[field + "_" + lang()] || obj[field + "_en"] || ""; }

  /* ---- where the glossary page lives, resolved from this script's own URL ---- */
  var self = document.currentScript ||
    document.querySelector('script[src$="glossary.js"]') ||
    document.querySelector('script[src*="glossary.js"]');
  var GLOSSARY_URL = "glossary/index.html";
  if (self && self.src) {
    try { GLOSSARY_URL = new URL("../glossary/index.html", self.src).href; } catch (e) {}
  }
  function entryUrl(id) {
    return GLOSSARY_URL.split("#")[0] + "#" + id;
  }

  /* ---------------------------------------------------------------- marking */

  var SKIP_TAGS = /^(CODE|PRE|A|SCRIPT|STYLE|NOSCRIPT|TEXTAREA|BUTTON|SELECT|OPTION|INPUT|SVG|PATH|KBD|SAMP|VAR|H1|MARK|TIME)$/;
  /* compact metadata rows list raw keywords; turning each into a link reads as noise */
  var SKIP_CLASS = /(^| )(term|term-pop|concept-lab|diagram|exercise-labels|meta-row|crumb|doc-nav|chmeta)( |$)/;
  var MAX_PER_TERM = G.maxPerTerm > 0 ? G.maxPerTerm : 2;

  var aliasToId = {};
  var entries = [];
  order.forEach(function (id) {
    var t = terms[id];
    if (!t) return;
    var list = (t.aliases && t.aliases.length) ? t.aliases : [t.term];
    list.forEach(function (a) {
      var low = String(a).toLowerCase();
      if (aliasToId[low]) return;              /* first term wins a shared alias */
      aliasToId[low] = id;
      entries.push({ id: id, alias: a });
    });
  });
  if (!entries.length) return;

  /* longest alias first so "consistent hashing" beats "hashing" */
  entries.sort(function (a, b) { return b.alias.length - a.alias.length; });
  function esc(s) { return s.replace(/[-/\\^$*+?.()|[\]{}]/g, "\\$&"); }
  var rx;
  try {
    rx = new RegExp("\\b(" + entries.map(function (e) { return esc(e.alias); }).join("|") + ")\\b", "gi");
  } catch (e) { return; }

  /* Which language a text node belongs to. The site renders both languages in the
     same DOM and hides one with CSS, so each language needs its own marking budget —
     otherwise the Persian copy could consume every mark before English is reached. */
  function langOf(node, stopAt) {
    for (var el = node.parentNode; el && el.nodeType === 1; el = el.parentNode) {
      var c = el.className;
      if (typeof c === "string" && c) {
        if (/(^| )fa( |$)/.test(c)) return "fa";
        if (/(^| )en( |$)/.test(c)) return "en";
      }
      if (el === stopAt) break;
    }
    return "-";
  }

  function skipped(node, stopAt) {
    for (var el = node.parentNode; el && el.nodeType === 1; el = el.parentNode) {
      if (el.hasAttribute && el.hasAttribute("data-no-glossary")) return true;
      if (SKIP_TAGS.test(el.tagName)) return true;
      if (el.className && typeof el.className === "string" && SKIP_CLASS.test(el.className)) return true;
      if (el === stopAt) return false;
    }
    return false;
  }

  function makeTerm(id, text) {
    var a = document.createElement("a");
    a.className = "term";
    a.href = entryUrl(id);
    a.setAttribute("data-term", id);
    a.textContent = text;
    return a;
  }

  function wrap(node, found) {
    var text = node.nodeValue, frag = document.createDocumentFragment(), pos = 0;
    found.sort(function (a, b) { return a.start - b.start; });
    found.forEach(function (m) {
      if (m.start < pos) return;
      if (m.start > pos) frag.appendChild(document.createTextNode(text.slice(pos, m.start)));
      frag.appendChild(makeTerm(m.id, text.slice(m.start, m.end)));
      pos = m.end;
    });
    if (pos === 0) return;
    if (pos < text.length) frag.appendChild(document.createTextNode(text.slice(pos)));
    node.parentNode.replaceChild(frag, node);
  }

  function mark() {
    var root = document.querySelector("main") || document.body;
    var scopes = [];
    var lede = document.querySelector(".doc-hero") || document.querySelector(".hero");
    if (lede) scopes.push(lede);
    Array.prototype.forEach.call(root.querySelectorAll("section"), function (s) {
      if (!lede || !lede.contains(s)) scopes.push(s);
    });
    if (!scopes.length) scopes = [root];
    var used = {};

    Array.prototype.forEach.call(scopes, function (scope) {
      var inScope = {};
      var walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT, null);
      var jobs = [], node, m;

      while ((node = walker.nextNode())) {
        var value = node.nodeValue;
        if (!value || value.length < 3) continue;
        if (skipped(node, scope)) continue;
        var tag = langOf(node, scope);
        rx.lastIndex = 0;
        var found = [];
        while ((m = rx.exec(value))) {
          var id = aliasToId[m[1].toLowerCase()];
          if (!id) continue;
          var key = tag + "|" + id;
          if (inScope[key] || (used[key] || 0) >= MAX_PER_TERM) continue;
          inScope[key] = true;
          used[key] = (used[key] || 0) + 1;
          found.push({ id: id, start: m.index, end: m.index + m[0].length });
          if (found.length >= 4) break;   /* a sentence that lists five terms reads as confetti */
        }
        if (found.length) jobs.push({ node: node, found: found });
      }
      jobs.forEach(function (job) { wrap(job.node, job.found); });
    });
  }

  /* --------------------------------------------------------------- popover */

  var pop = null, current = null, raf = 0;

  function ensurePop() {
    if (pop) return pop;
    pop = document.createElement("div");
    pop.className = "term-pop";
    pop.setAttribute("role", "tooltip");
    pop.setAttribute("id", "ddia-term-pop");
    document.body.appendChild(pop);
    return pop;
  }

  function place(el) {
    if (!pop) return;
    var r = el.getBoundingClientRect();
    var pw = pop.offsetWidth, ph = pop.offsetHeight;
    var vw = docEl.clientWidth, vh = docEl.clientHeight, gap = 10, edge = 10;

    var below = r.bottom + gap;
    var above = r.top - ph - gap;
    var top = (below + ph + edge <= vh || above < edge) ? below : above;
    if (top + ph > vh - edge) top = Math.max(edge, vh - ph - edge);

    var left = r.left + r.width / 2 - pw / 2;
    if (left < edge) left = edge;
    if (left + pw > vw - edge) left = vw - pw - edge;

    pop.style.top = Math.round(top) + "px";
    pop.style.left = Math.round(left) + "px";
  }

  function show(el) {
    var id = el.getAttribute("data-term");
    var t = id && terms[id];
    if (!t) return;
    var p = ensurePop();
    var fa = lang() === "fa";
    p.innerHTML = "";

    var label = document.createElement("b");
    label.textContent = pick(t, "term") || t.term;
    var body = document.createElement("p");
    body.textContent = pick(t, "one_liner");
    var more = document.createElement("p");
    more.className = "more";
    more.innerHTML = '<i aria-hidden="true">&rarr;</i>' +
      (fa ? "<span>مثال روزمره + توضیح فنی</span>" : "<span>Everyday example + technical detail</span>");

    p.appendChild(label);
    if (body.textContent) p.appendChild(body);
    p.appendChild(more);

    current = el;
    el.setAttribute("aria-describedby", "ddia-term-pop");
    p.classList.add("is-on");
    place(el);
  }

  function hide() {
    if (pop) pop.classList.remove("is-on");
    if (current) current.removeAttribute("aria-describedby");
    current = null;
  }

  function track() {
    if (!current) return;
    if (!document.body.contains(current)) { hide(); return; }
    place(current);
    raf = window.requestAnimationFrame(track);
  }

  function startTracking() { if (!raf) raf = window.requestAnimationFrame(track); }
  function stopTracking() { if (raf) window.cancelAnimationFrame(raf); raf = 0; }

  document.addEventListener("pointerover", function (e) {
    var el = e.target.closest && e.target.closest(".term");
    if (!el || el === current) return;
    show(el); startTracking();
  });
  document.addEventListener("pointerout", function (e) {
    var el = e.target.closest && e.target.closest(".term");
    if (!el) return;
    if (e.relatedTarget && el.contains(e.relatedTarget)) return;
    hide(); stopTracking();
  });
  document.addEventListener("focusin", function (e) {
    var el = e.target.closest && e.target.closest(".term");
    if (el) { show(el); startTracking(); }
  });
  document.addEventListener("focusout", function (e) {
    if (e.target.closest && e.target.closest(".term")) { hide(); stopTracking(); }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && current) hide();
  });
  window.addEventListener("scroll", hide, { passive: true });
  window.addEventListener("resize", hide);
  document.addEventListener("click", function (e) {
    if (e.target.closest && e.target.closest("[data-lang-toggle]")) hide();
  });

  /* ---------------------------------------------------- glossary page tools */

  function pageTools() {
    var grid = document.getElementById("gl-grid");
    if (!grid) return;
    var input = document.getElementById("gl-search");
    var chips = Array.prototype.slice.call(document.querySelectorAll("[data-gl-chapter]"));
    var cards = Array.prototype.slice.call(grid.querySelectorAll(".gl-card"));
    var count = document.getElementById("gl-count");
    var empty = document.getElementById("gl-empty");
    var activeChapter = "all";

    /* Searchable text is read from the card itself, minus the labels, so the page
       carries no duplicated index and both languages stay searchable. */
    function haystack(card) {
      var clone = card.cloneNode(true);
      var drop = clone.querySelectorAll("h3, .gl-related, .gl-chapter");
      for (var i = 0; i < drop.length; i++) drop[i].parentNode.removeChild(drop[i]);
      return clone.textContent.toLowerCase().replace(/\s+/g, " ");
    }
    cards.forEach(function (card) { card._hay = haystack(card); });

    function apply() {
      var q = (input && input.value || "").trim().toLowerCase();
      var shown = 0;
      cards.forEach(function (card) {
        var hay = card._hay || "";
        var ch = card.getAttribute("data-chapter");
        var ok = (activeChapter === "all" || ch === activeChapter) && (!q || hay.indexOf(q) !== -1);
        card.hidden = !ok;
        if (ok) shown++;
      });
      if (count) count.textContent = shown + " / " + cards.length;
      if (empty) empty.hidden = shown > 0;
    }
    if (input) {
      input.addEventListener("input", apply);
      input.addEventListener("keydown", function (e) {
        if (e.key === "Escape") { input.value = ""; apply(); }
      });
      /* the placeholder follows the language toggle instead of carrying both languages */
      function syncPlaceholder() {
        if (input.dataset.phFa) {
          input.placeholder = lang() === "fa" ? input.dataset.phFa : input.dataset.phEn;
        }
      }
      syncPlaceholder();
      if (window.MutationObserver) {
        new MutationObserver(syncPlaceholder)
          .observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
      }
    }
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        activeChapter = chip.getAttribute("data-gl-chapter");
        chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
        apply();
      });
    });
    apply();
  }

  /* A direct load with #term jumps before the long page has settled, which lands the
     card under the sticky filter bar. Re-run the scroll once layout is final. */
  function focusHash() {
    var id = location.hash ? decodeURIComponent(location.hash.slice(1)) : "";
    if (!id) return;
    var el = document.getElementById(id);
    if (el && el.classList.contains("gl-card")) {
      window.requestAnimationFrame(function () { el.scrollIntoView({ block: "start" }); });
    }
  }

  function boot() { mark(); pageTools(); focusHash(); }

  if (document.readyState === "complete") focusHash();
  else window.addEventListener("load", focusHash);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
