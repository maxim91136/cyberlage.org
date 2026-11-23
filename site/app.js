(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var zahl = function (n) { return typeof n === "number" ? n.toLocaleString("de-DE") : "keine Daten"; };
  var datum = function (iso) {
    if (!iso) return "keine Daten";
    var d = new Date(iso);
    return isNaN(d) ? "keine Daten" : d.toLocaleDateString("de-DE", { timeZone: "UTC", day: "2-digit", month: "2-digit", year: "numeric" });
  };
  var el = function (tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  };

  fetch("data/lage.json", { cache: "no-cache" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(render)
    .catch(function () {
      $("stand").textContent = "keine Daten";
      $("stufe-wert").textContent = "keine Daten";
      $("stufe-text").textContent = "Die Daten konnten nicht geladen werden.";
    });

  function render(d) {
    $("stand").textContent = datum(d.stand);

    var hatStufe = d.stufe !== null && d.stufe !== undefined;
    var NAMEN = { niedrig: "niedrig", erhoeht: "erhöht", hoch: "hoch" };
    var name = hatStufe ? (NAMEN[d.stufe] || String(d.stufe)) : null;
    $("stufe-wert").textContent = hatStufe ? name : "null";
    $("stufe-text").textContent = hatStufe ? "Stufe: " + name : "Keine Bewertung";
    $("stufe-begr").textContent = d.stufe_begruendung || "";

    var k = d.kev || {};
    $("k7").textContent = zahl(k.neu_7_tage);
    $("k30").textContent = zahl(k.neu_30_tage);
    $("kall").textContent = zahl(k.gesamt);
    $("kr").textContent = zahl(k.ransomware_bekannt_30_tage);

    var kq = (d.quellen || []).filter(function (q) { return q.id === "cisa-kev"; })[0] || {};
    $("kev-quelle").textContent = "quelle: CISA KEV · veröffentlicht " + datum(kq.veroeffentlicht_am) +
      " · abgerufen " + datum(kq.abgerufen_am) + " · lizenz " + (kq.lizenz || "keine Daten") + " · geltungsbereich: weltweit";

    var s = $("sektor");
    (d.sektor || []).forEach(function (z) {
      var box = el("div", "panel sektor");
      box.appendChild(el("div", "zahl mono", String(z.wert).replace(".", ",") + " %"));
      var t = el("div", "txt");
      t.appendChild(el("div", "", "der erfassten Ereignisse " + z.berichtsjahr + " betrafen die öffentliche Verwaltung."));
      var m = el("div", "mono dim fine");
      m.appendChild(document.createTextNode("geltungsbereich: " + z.geltungsbereich + (z.geltungsbereich === "EU" ? ", nicht Deutschland" : "") +
        " · " + z.quelle + ", Seite " + z.seite + " · " + z.lizenz + " · "));
      if (/^https:\/\//.test(z.link || "")) {
        var a = el("a", "", "Quelle");
        a.href = z.link; a.rel = "noopener"; m.appendChild(a);
      }
      t.appendChild(m); box.appendChild(t); s.appendChild(box);
    });

    var ql = $("quellenliste");
    (d.quellen || []).forEach(function (q) {
      var r = el("div", "row");
      var n = el("strong"); 
      if (/^https:\/\//.test(q.link || "")) { var a = el("a", "", q.name); a.href = q.link; a.rel = "noopener"; n.appendChild(a); } else { n.textContent = q.name; }
      r.appendChild(n);
      r.appendChild(el("span", "", "verarbeitet · " + q.lizenz + (q.abgerufen_am ? " · abgerufen " + datum(q.abgerufen_am) : "")));
      ql.appendChild(r);
    });

    var liste = d.neu || [];
    $("fenster").textContent = String(d.fenster_tage || 30);
    var body = $("neu-liste");
    var zeilen = liste.map(function (e) {
      var tr = el("tr");
      tr.appendChild(el("td", "mono", datum(e.hinzugefuegt)));
      tr.appendChild(el("td", "", e.hersteller));
      tr.appendChild(el("td", "", e.produkt));
      var c = el("td", "mono");
      if (/^https:\/\/nvd\.nist\.gov\//.test(e.link || "")) { var a = el("a", "", e.cve); a.href = e.link; a.rel = "noopener"; c.appendChild(a); } else { c.textContent = e.cve; }
      tr.appendChild(c);
      tr.appendChild(el("td", "mono", datum(e.frist)));
      tr.appendChild(e.ransomware_bekannt ? el("td", "rw", "bekannt") : el("td", "dim", "nicht bekannt"));
      tr._text = (e.hersteller + " " + e.produkt + " " + e.cve).toLowerCase();
      body.appendChild(tr);
      return tr;
    });
    function filtern() {
      var q = $("filter").value.trim().toLowerCase(), n = 0;
      zeilen.forEach(function (tr) { var ok = !q || tr._text.indexOf(q) !== -1; tr.hidden = !ok; if (ok) n++; });
      $("treffer").textContent = n + " von " + zeilen.length + " Einträgen";
    }
    $("filter").addEventListener("input", filtern);
    filtern();

    var h = $("hinweise");
    (d.hinweise || []).forEach(function (t) { h.appendChild(el("li", "", t)); });
  }
})();
