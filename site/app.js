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
    $("stufe-text").textContent = hatStufe ? "" : "Keine Bewertung";
    $("stufe-text").hidden = hatStufe;
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

    zeichneVerlauf(d.verlauf || [], d.schwellen || {});

    var h = $("hinweise");
    (d.hinweise || []).forEach(function (t) { h.appendChild(el("li", "", t)); });
  }

  function zeichneVerlauf(v, sw) {
    var svg = $("verlauf"), NS = "http://www.w3.org/2000/svg";
    if (!v.length) { $("verlauf-legende").textContent = "keine Daten"; return; }
    var B = Math.max(300, Math.round(svg.getBoundingClientRect().width)) || 1000, H = B < 600 ? 190 : 220, L = 30, R = 74, T = 14, U = 28;
    svg.setAttribute("viewBox", "0 0 " + B + " " + H);
    var max = Math.max.apply(null, v.map(function (p) { return p.neu; }).concat([sw.hoch_ab || 0])) + 4;
    var y = function (n) { return T + (H - T - U) * (1 - n / max); };
    var w = (B - L - R) / v.length;
    var farbe = { niedrig: "#6fe0a0", erhoeht: "#e3b341", hoch: "#ff8a7a" };
    var mk = function (tag, a, txt) {
      var e = document.createElementNS(NS, tag);
      for (var k in a) e.setAttribute(k, a[k]);
      if (txt !== undefined) e.textContent = txt;
      svg.appendChild(e); return e;
    };
    [0, Math.round(max / 2), max].forEach(function (n) {
      mk("line", { x1: L, x2: B - R, y1: y(n), y2: y(n), stroke: "#1d262e" });
      mk("text", { x: L - 6, y: y(n) + 4, "text-anchor": "end", fill: "#8a99a6", "font-size": 11, "font-family": "ui-monospace,monospace" }, String(n));
    });
    v.forEach(function (p, i) {
      var t = mk("rect", { x: L + i * w + 1, y: y(p.neu), width: Math.max(w - 2, 1), height: y(0) - y(p.neu), fill: farbe[p.stufe] || "#8a99a6" });
      t.appendChild(document.createElementNS(NS, "title")).textContent = datum(p.stand) + ": " + p.neu + " neu in 30 Tagen" + (p.stufe ? ", Stufe " + p.stufe : "");
    });
    [["erhoeht_ab", "erhöht ab", "#e3b341"], ["hoch_ab", "hoch ab", "#ff8a7a"]].forEach(function (c) {
      if (typeof sw[c[0]] !== "number") return;
      mk("line", { x1: L, x2: B - R + 2, y1: y(sw[c[0]]), y2: y(sw[c[0]]), stroke: c[2], "stroke-dasharray": "5 4" });
      mk("text", { x: B - R + 6, y: y(sw[c[0]]) + 4, "text-anchor": "start", fill: c[2], "font-size": 11, "font-family": "ui-monospace,monospace" }, c[1].replace(" ab", "") + " " + sw[c[0]]);
    });
    [0, Math.floor(v.length / 2), v.length - 1].forEach(function (i) {
      mk("text", { x: L + i * w + w / 2, y: H - 8, "text-anchor": i === 0 ? "start" : (i === v.length - 1 ? "end" : "middle"), fill: "#8a99a6", "font-size": 11, "font-family": "ui-monospace,monospace" }, datum(v[i].stand));
    });
    var zahlen = v.map(function (p) { return p.neu; });
    var s = $("verlauf-titel");
    s.textContent = "Neu aufgenommene Schwachstellen pro 30 Tage, " + datum(v[0].stand) + " bis " + datum(v[v.length - 1].stand) +
      ": niedrigster Wert " + Math.min.apply(null, zahlen) + ", höchster " + Math.max.apply(null, zahlen) + ", zuletzt " + zahlen[zahlen.length - 1] + ".";
    $("verlauf-legende").textContent = "Balken: grün unter erhöht-Schwelle, gelb erhöht, rot hoch. Wochenstände, auch rückwirkend mit den heutigen Schwellen gemessen. Quelle: CISA KEV (CC0 1.0), eigene Auswertung.";
  }
})();
