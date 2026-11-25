/* Step-through controls for technical examples.
   Each .technical-example has setup/steps/result parts, duplicated per language.
   The control steps both language trees in lockstep, so it works in any language. */
(function () {
  var LABELS = {
    start: { fa: "قدم‌به‌قدم", en: "Step through" },
    next: { fa: "قدم بعدی", en: "Next step" },
    reset: { fa: "از نو", en: "Restart" }
  };

  function label(key) {
    var l = LABELS[key];
    return '<span class="fa">' + l.fa + '</span><span class="en">' + l.en + '</span>';
  }

  function partsOf(root, lang) {
    var wrap = root.querySelector(':scope > .' + lang);
    if (!wrap) return [];
    return Array.prototype.slice.call(wrap.querySelectorAll("[data-example-part]"));
  }

  document.querySelectorAll(".technical-example").forEach(function (ex) {
    var fa = partsOf(ex, "fa");
    var en = partsOf(ex, "en");
    var n = Math.max(fa.length, en.length);
    if (n < 2) return;

    var bar = document.createElement("div");
    bar.className = "step-controls";
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "step-btn";
    btn.innerHTML = label("start");
    bar.appendChild(btn);
    ex.appendChild(bar);

    var at = 0;
    var running = false;

    function setVisible(count) {
      [fa, en].forEach(function (list) {
        list.forEach(function (p, i) {
          p.classList.toggle("step-hidden", running && i >= count);
        });
      });
    }

    function paint() {
      if (!running) {
        btn.innerHTML = label("start");
        return;
      }
      btn.innerHTML = at >= n ? label("reset") : label("next");
    }

    btn.addEventListener("click", function () {
      if (!running) {
        running = true;
        at = 1;
      } else if (at >= n) {
        running = false;
        at = 0;
      } else {
        at += 1;
      }
      setVisible(at);
      paint();
    });
  });
})();
