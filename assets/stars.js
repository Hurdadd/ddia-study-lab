/* Star counter — same-origin refresh, no third-party request.
   The number is baked in by assets/build_stars.py so the page is correct with
   JavaScript off and on a first paint; this only re-reads the local JSON so a
   stale deployment still shows today's count. If the read fails, the baked
   number stays. */
(function () {
  'use strict';
  var slots = document.querySelectorAll('[data-star-count]');
  if (!slots.length) return;

  function compact(n) {
    return n >= 1000 ? (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k' : String(n);
  }

  function paint(stars) {
    for (var i = 0; i < slots.length; i++) slots[i].textContent = compact(stars);
    var links = document.querySelectorAll('a .star-pill');
    for (var j = 0; j < links.length; j++) {
      var link = links[j].closest('a');
      if (link) link.title = stars + ' stars on GitHub · star this repository';
    }
  }

  if (!window.fetch) return;
  fetch('assets/stars.json', { cache: 'no-cache' })
    .then(function (response) { return response.ok ? response.json() : null; })
    .then(function (data) {
      if (data && typeof data.stars === 'number') paint(data.stars);
    })
    .catch(function () { /* keep the baked number */ });
})();
