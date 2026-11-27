/* Sortierbare, filterbare Tabellen. Aus app.js ausgelagert; läuft nach app.js (baut beim Laden sofort aus). */
(function () {
  "use strict";
  window.CL = window.CL || {};
  var pick = function () { return window.CL.pick.apply(null, arguments); };
  var el = function () { return window.CL.el.apply(null, arguments); };
  /* Jede Tabelle: Klick auf den Spaltenkopf sortiert (Zahlen, Datum, Text), ab sechs Zeilen kommt ein Filterfeld dazu. Läuft nur im Browser. */
  function zellWert(td) {
    if (td && td.dataset && td.dataset.sort !== undefined) { var ds = parseFloat(td.dataset.sort); return isNaN(ds) ? null : ds; }  // fester Sortierwert (Datum, Tage)
    var t = (td ? td.textContent : "").trim();
    if (!t || t === "–" || t === "-") return null;
    var m = t.match(/^(\d{1,2})[./](\d{1,2})[./](\d{4})(?:,?\s+(\d{1,2}):(\d{2}))?/);
    if (m) return Date.UTC(+m[3], +m[2] - 1, +m[1], +(m[4] || 0), +(m[5] || 0));
    var z = t.replace(/\s|%|×|x$/g, "");
    if (/^[+-]?[\d.,]+$/.test(z)) {
      z = window.I18N.lang === "en" ? z.replace(/,/g, "") : z.replace(/\./g, "").replace(",", ".");
      var n = parseFloat(z); if (!isNaN(n)) return n;
    }
    return t.toLowerCase();
  }
  function tabelleAusbauen(t) {
    if (t.dataset.tw || !t.tHead || !t.tBodies[0]) return;
    t.dataset.tw = "1";
    var tb = t.tBodies[0], kopf = Array.prototype.slice.call(t.tHead.rows[t.tHead.rows.length - 1].cells);
    if (kopf.some(function (th) { return th.colSpan > 1; })) return;
    kopf.forEach(function (th, i) {
      th.classList.add("th-s"); th.tabIndex = 0; th.setAttribute("role", "columnheader"); th.title = pick("Zum Sortieren klicken", "Click to sort");
      function sortiere() {
        var auf = th.getAttribute("aria-sort") !== "ascending";
        kopf.forEach(function (x) { x.removeAttribute("aria-sort"); }); th.setAttribute("aria-sort", auf ? "ascending" : "descending");
        var rows = Array.prototype.slice.call(tb.rows).map(function (r, n) { return { r: r, n: n, w: r.cells.length === kopf.length ? zellWert(r.cells[i]) : null }; });
        rows.sort(function (a, b) {
          if (a.w === null || b.w === null) return a.w === b.w ? a.n - b.n : (a.w === null ? 1 : -1);   // leere Werte immer ans Ende
          var c = typeof a.w === "number" && typeof b.w === "number" ? a.w - b.w : String(a.w).localeCompare(String(b.w), window.I18N.locale, { numeric: true });
          return (auf ? c : -c) || a.n - b.n;
        });
        rows.forEach(function (x) { tb.appendChild(x.r); });
      }
      th.addEventListener("click", sortiere);
      th.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); sortiere(); } });
    });
    if (t.closest("#neu") || t.closest("#p-hv") || t.closest("#p-hs")) t.classList.add("tw-k");  // Karten auf dem Handy, ohne Spaltenfilter
    if (t.classList.contains("tw-sp") || t.classList.contains("tw-k")) {  // Handy: jede Zeile wird zur Karte, dafür bekommt jede Zelle ihren Spaltennamen
      Array.prototype.forEach.call(tb.rows, function (r) { Array.prototype.forEach.call(r.cells, function (c, i) { if (kopf[i] && c.colSpan < 2) c.setAttribute("data-l", kopf[i].textContent); if (/^[–-]$/.test(c.textContent.trim())) c.classList.add("tw-leer"); }); });
    }
    if (t.classList.contains("tw-sp")) {  // Spaltenfilter: eine Eingabe je Spalte unter dem Kopf, alle zusammen (UND)
      var fr = el("tr", "tw-fr"), felder = [];
      function filtere() {
        Array.prototype.forEach.call(tb.rows, function (r) {
          r.hidden = !felder.every(function (f, i) { var w = f.value.toLowerCase().trim(); return !w || (r.cells[i] && r.cells[i].textContent.toLowerCase().indexOf(w) >= 0); });
        });
      }
      kopf.forEach(function (th) {
        var c = el("td", ""), f = el("input", "filter mono tw-cf"); f.type = "search"; f.autocomplete = "off"; f.placeholder = pick("filtern", "filter");
        f.setAttribute("aria-label", pick("Spalte filtern: ", "Filter column: ") + th.textContent); f.addEventListener("input", filtere); felder.push(f); c.appendChild(f); fr.appendChild(c);
      });
      t.tHead.appendChild(fr);
    } else if (tb.rows.length >= 6 && !t.closest("#neu") && !t.closest(".br-tab")) {
      var f = el("input", "filter mono tw-f"); f.type = "search"; f.autocomplete = "off"; f.placeholder = pick("Tabelle filtern …", "Filter table …"); f.setAttribute("aria-label", pick("Tabelle filtern", "Filter table"));
      f.addEventListener("input", function () {
        var w = f.value.toLowerCase().split(/\s+/).filter(Boolean);
        Array.prototype.forEach.call(tb.rows, function (r) { var x = r.textContent.toLowerCase(); r.hidden = !w.every(function (k) { return x.indexOf(k) >= 0; }); });
      });
      var wrap = t.parentNode.classList && t.parentNode.classList.contains("tabelle") ? t.parentNode : t;
      wrap.parentNode.insertBefore(f, wrap);
    }
  }
  function tabellenAusbauen() { Array.prototype.forEach.call(document.querySelectorAll("main table"), tabelleAusbauen); }
  (function () {
    var warte = null, ziel = document.querySelector("main");
    tabellenAusbauen();
    if (ziel && window.MutationObserver) new MutationObserver(function () { clearTimeout(warte); warte = setTimeout(tabellenAusbauen, 150); }).observe(ziel, { childList: true, subtree: true });
  })();

  window.CL.tabellenAusbauen = tabellenAusbauen;
})();
