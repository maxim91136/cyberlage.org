(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var txt = function () { return window.I18N.t.apply(null, arguments); };
  var pick = function (de, en) { return window.I18N.pick(de, en); };
  var zahl = function (n) { return typeof n === "number" ? n.toLocaleString(window.I18N.locale) : txt("keine"); };
  var datum = function (iso) {
    if (!iso) return txt("keine");
    var d = new Date(iso);
    if (isNaN(d)) return txt("keine");
    var t = d.toLocaleDateString(window.I18N.locale, { timeZone: "UTC", day: "2-digit", month: "2-digit", year: "numeric" });
    // Mit Uhrzeit nur, wenn die Quelle eine liefert (ISO mit "T"); Tageswerte bleiben Datum
    return /T\d\d:\d\d/.test(String(iso)) ? t + ", " + d.toLocaleTimeString(window.I18N.locale, { timeZone: "UTC", hour: "2-digit", minute: "2-digit", hour12: false }) + " UTC" : t;
  };
  var el = function (tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  };

  var knopf = $("totop");
  if (knopf) {
    var weich = !(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    knopf.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: weich ? "smooth" : "auto" }); });
    var navLinks = Array.prototype.slice.call(document.querySelectorAll(".navin > a[data-sec], .navin summary[data-sec]"));
    var abschnitte = navLinks.map(function (a) { return document.getElementById(a.getAttribute("data-sec")); });
    var ticks = false;
    var pruefen = function () {
      ticks = false;
      knopf.classList.toggle("on", window.scrollY > window.innerHeight * 1.2);
      var aktiv = -1, grenze = window.scrollY + 120;
      abschnitte.forEach(function (sec, i) { if (sec && sec.offsetTop <= grenze) aktiv = i; });
      navLinks.forEach(function (a, i) { if (i === aktiv) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current"); a.classList.toggle("aktiv", i === aktiv); });
    };
    window.addEventListener("scroll", function () { if (!ticks) { ticks = true; requestAnimationFrame(pruefen); } }, { passive: true });
    window.addEventListener("load", pruefen);
  }

  fetch("data/lage.json", { cache: "no-cache" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(render)
    .catch(function (err) { if (window.console) console.error(err);
      $("stand").textContent = txt("keine");
      $("stufe-wert").textContent = txt("keine");
      $("stufe-text").textContent = txt("laden_fehler");
    });

  function render(d) {
    var kq0 = (d.quellen || []).filter(function (q) { return q.id === "cisa-kev"; })[0] || {};
    $("stand").textContent = datum(kq0.abgerufen_am || d.stand);
    var fz = $("fazit"), f = d.fazit;
    if (fz && f) {
      fz.textContent = "";
      var fk = el("b", "mono", pick("Fazit", "Conclusion")); fz.appendChild(fk);
      if (f.status === "vorlaeufig") fz.appendChild(el("span", "mono dim", pick(" · vorläufig", " · provisional")));
      fz.appendChild(el("p", "ft", pick(f.text, f.text_en)));
      fz.appendChild(el("p", "fh", pick("Für Verteidiger: ", "For defenders: ") + pick(f.hinweis, f.hinweis_en)));
      fz.appendChild(el("p", "mono dim fine", pick("Feste Sätze nach Regeln, keine Vorhersage. Stufen des Radar-Scores geprüft am ", "Fixed sentences by rule, no forecast. Radar score levels checked on ") + datum(f.stand) + "."));
      fz.hidden = false; var fv = $("fazit-verk"); if (fv) fv.hidden = false;
    }
    var kqz = $("kern-quelle"); if (kqz) kqz.textContent = pick("Quelle aller Zahlen in diesem Kasten: CISA-KEV-Katalog, abgerufen ", "Source of all figures in this box: CISA KEV catalog, retrieved ") + datum(kq0.abgerufen_am || d.stand) + pick(" (Katalog veröffentlicht ", " (catalog published ") + datum(kq0.veroeffentlicht_am) + ")";

    var hatStufe = d.stufe !== null && d.stufe !== undefined;
    var name = hatStufe ? txt(String(d.stufe)) : null;
    $("stufe-wert").textContent = hatStufe ? name : "null";
    window.DP = hatStufe ? name + (d.pegel && typeof d.pegel.wert === "number" ? " " + d.pegel.wert : "") : "";
    if (hatStufe) $("lage-box").classList.add("st-" + d.stufe);
    $("stufe-text").textContent = hatStufe ? "" : txt("keine_bew");
    $("stufe-text").hidden = hatStufe;
    $("stufe-begr").textContent = pick(d.stufe_begruendung, d.stufe_begruendung_en) || "";

    var k = d.kev || {};
    $("k7").textContent = zahl(k.neu_7_tage);
    $("k30").textContent = zahl(k.neu_30_tage);
    $("kall").textContent = zahl(k.gesamt);
    $("kr").textContent = zahl(k.ransomware_bekannt_30_tage);

    var kq = (d.quellen || []).filter(function (q) { return q.id === "cisa-kev"; })[0] || {};
    $("kev-quelle").textContent = txt("kev_quelle", datum(kq.veroeffentlicht_am), datum(kq.abgerufen_am), pick(kq.lizenz, kq.lizenz_en) || txt("keine"));

    var ql = $("quellenliste");
    (d.quellen || []).forEach(function (q) {
      var r = el("div", "row");
      var n = el("strong"); 
      if (/^https:\/\//.test(q.link || "")) { var a = el("a", "", pick(q.name, q.name_en)); a.href = q.link; a.rel = "noopener"; n.appendChild(a); } else { n.textContent = pick(q.name, q.name_en); }
      r.appendChild(n);
      r.appendChild(el("span", "", txt("verarbeitet", pick(q.lizenz, q.lizenz_en), q.abgerufen_am ? datum(q.abgerufen_am) : "")));
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
      tr.appendChild(e.ransomware_bekannt ? el("td", "rw", txt("bekannt")) : el("td", "dim", txt("nicht_bekannt")));
      tr._text = (e.hersteller + " " + e.produkt + " " + e.cve).toLowerCase();
      body.appendChild(tr);
      return tr;
    });
    function filtern() {
      var q = $("filter").value.trim().toLowerCase(), n = 0;
      zeilen.forEach(function (tr) { var ok = !q || tr._text.indexOf(q) !== -1; tr.hidden = !ok; if (ok) n++; });
      $("treffer").textContent = txt("treffer", n, zeilen.length);
    }
    $("filter").addEventListener("input", filtern);
    filtern();

    var sw = d.schwellen || {};
    if (typeof sw.erhoeht_ab === "number" && typeof sw.hoch_ab === "number" && typeof sw.ransomware_aufschlag_ab === "number") {
      $("rechnung").innerHTML = txt("rechnung", d.fenster_tage || 30, sw.erhoeht_ab, sw.hoch_ab, sw.ransomware_aufschlag_ab, sw.basis_monate || 12, sw.median);
    } else {
      $("rechnung").textContent = txt("keine");
    }
    zeichneVerlauf(d.verlauf || [], d.schwellen || {});
    zeichneScoreVerlauf(((((d.radar || {}).konsens) || {}).score) || null);
    var tl = d.telegram && d.telegram.link;
    if (/^https:\/\/t\.me\//.test(tl || "")) { $("telegram-link").href = tl; $("telegram").hidden = false; }
    d_stand = d.stand; d_skala = d.radar_skala || null;
    zeigeBsi(d.cert_bund);
    zeigeEu(d.eu_kev);
    zeigeAusblick(d.ausblick);
    zeigeRadar(d.radar, d);
    zeigeKern(d);
    zeigeKonsens(d.radar);

    var h = $("hinweise");
    var hw = window.I18N.lang === "en" && d.hinweise_en ? d.hinweise_en : (d.hinweise || []);
    h.textContent = "";
    hw.forEach(function (t) { h.appendChild(el("li", "", t)); });
  }

  function waehleTab(name) {
    ["kev", "bsi", "eu", "ausblick"].forEach(function (n) {
      var t = $("t-" + n), an = n === name;
      t.setAttribute("aria-selected", an ? "true" : "false"); t.tabIndex = an ? 0 : -1;
      $("p-" + n).hidden = !an;
    });
  }
  function bedienung() {
    Array.prototype.forEach.call(document.querySelectorAll(".tabs button"), function (b) {
      b.addEventListener("click", function () { waehleTab(b.getAttribute("data-tab")); });
      b.addEventListener("keydown", function (e) {
        var ids = ["kev", "bsi", "eu", "ausblick"], i = ids.indexOf(b.getAttribute("data-tab"));
        if (e.key === "ArrowRight") i = (i + 1) % ids.length; else if (e.key === "ArrowLeft") i = (i + ids.length - 1) % ids.length; else return;
        waehleTab(ids[i]); $("t-" + ids[i]).focus(); e.preventDefault();
      });
    });
    var menues = Array.prototype.slice.call(document.querySelectorAll(".dd"));
    menues.forEach(function (m) {
      m.addEventListener("toggle", function () { if (m.open) menues.forEach(function (o) { if (o !== m) o.open = false; }); });
    });
    document.addEventListener("click", function (e) { menues.forEach(function (m) { if (!m.contains(e.target)) m.open = false; }); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") menues.forEach(function (m) { m.open = false; }); });
    Array.prototype.forEach.call(document.querySelectorAll(".dd-box a, a[data-offen]"), function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        var tab = a.getAttribute("data-tab"), offen = a.getAttribute("data-offen"), ziel = document.querySelector(a.getAttribute("href"));
        if (tab) waehleTab(tab);
        if (offen) { var d = $(offen); if (d) d.open = true; ziel = d || ziel; }
        menues.forEach(function (m) { m.open = false; });
        if (ziel) ziel.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
      });
    });
  }
  bedienung();

  function zeichneVerlauf(v, sw) {
    var svg = $("verlauf"), NS = "http://www.w3.org/2000/svg";
    if (!v.length) { $("verlauf-legende").textContent = txt("keine"); return; }
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
      t.appendChild(document.createElementNS(NS, "title")).textContent = txt("v_tip", datum(p.stand), p.neu, p.stufe ? txt(p.stufe) : "");
    });
    [["erhoeht_ab", "erhöht ab", "#e3b341"], ["hoch_ab", "hoch ab", "#ff8a7a"]].forEach(function (c) {
      if (typeof sw[c[0]] !== "number") return;
      mk("line", { x1: L, x2: B - R + 2, y1: y(sw[c[0]]), y2: y(sw[c[0]]), stroke: c[2], "stroke-dasharray": "5 4" });
      mk("text", { x: B - R + 6, y: y(sw[c[0]]) + 4, "text-anchor": "start", fill: c[2], "font-size": 11, "font-family": "ui-monospace,monospace" }, txt(c[0] === "hoch_ab" ? "hoch" : "erhoeht") + " " + sw[c[0]]);
    });
    [0, Math.floor(v.length / 2), v.length - 1].forEach(function (i) {
      mk("text", { x: L + i * w + w / 2, y: H - 8, "text-anchor": i === 0 ? "start" : (i === v.length - 1 ? "end" : "middle"), fill: "#8a99a6", "font-size": 11, "font-family": "ui-monospace,monospace" }, datum(v[i].stand));
    });
    var zahlen = v.map(function (p) { return p.neu; });
    var s = $("verlauf-titel");
    s.textContent = txt("v_titel", datum(v[0].stand), datum(v[v.length - 1].stand), Math.min.apply(null, zahlen), Math.max.apply(null, zahlen), zahlen[zahlen.length - 1]);
    $("verlauf-legende").textContent = txt("v_leg", sw.basis_monate || 12);
  }

  function zeichneScoreVerlauf(sc) {
    var svg = $("rs-chart"), leg = $("rs-legende"), NS = "http://www.w3.org/2000/svg";
    if (!svg) return;
    svg.textContent = "";
    var v = sc && sc.reihe || [];
    if (!v.length) { leg.textContent = txt("keine"); return; }
    var B = Math.max(300, Math.round(svg.getBoundingClientRect().width)) || 1000, H = B < 600 ? 170 : 200, L = 30, R = 16, T = 12, U = 28;
    svg.setAttribute("viewBox", "0 0 " + B + " " + H);
    var mk = function (tag, a, t) { var e = document.createElementNS(NS, tag); for (var k in a) e.setAttribute(k, a[k]); if (t !== undefined) e.textContent = t; svg.appendChild(e); return e; };
    var y = function (n) { return T + (H - T - U) * (1 - n / 100); };
    var x = function (i) { return v.length < 2 ? (L + B - R) / 2 : L + i * (B - L - R) / (v.length - 1); };
    [0, 50, 100].forEach(function (n) {
      mk("line", { x1: L, x2: B - R, y1: y(n), y2: y(n), stroke: n === 50 ? "#263340" : "#1d262e", "stroke-dasharray": n === 50 ? "4 4" : "0" });
      mk("text", { x: L - 6, y: y(n) + 4, "text-anchor": "end", fill: "#8a99a6", "font-size": 11, "font-family": "ui-monospace,monospace" }, String(n));
    });
    if (v.length > 1) mk("polyline", { points: v.map(function (p, i) { return x(i) + "," + y(p.wert); }).join(" "), fill: "none", stroke: "#6fe0a0", "stroke-width": 2 });
    v.forEach(function (p, i) {
      var c = mk("circle", { cx: x(i), cy: y(p.wert), r: v.length > 60 ? 1.5 : 3, fill: "#6fe0a0" });
      c.appendChild(document.createElementNS(NS, "title")).textContent = datum(p.stand) + ": " + p.wert + " (" + p.signale + "/" + p.von + ")";
    });
    [0, v.length - 1].forEach(function (i, k) {
      if (k && v.length < 2) return;
      mk("text", { x: x(i), y: H - 8, "text-anchor": i === 0 ? "start" : "end", fill: "#8a99a6", "font-size": 11, "font-family": "ui-monospace,monospace" }, datum(v[i].stand));
    });
    var t = document.createElementNS(NS, "title"); t.textContent = pick("Verlauf des Radar-Scores, zuletzt " + v[v.length - 1].wert + " von 100.", "Radar score over time, latest " + v[v.length - 1].wert + " of 100."); svg.insertBefore(t, svg.firstChild);
    leg.textContent = pick("Eine Messung pro Tag, seit " + datum(sc.live_seit || v[0].stand) + ". ", "One reading per day, since " + datum(sc.live_seit || v[0].stand) + ". ") +
      (v.length < 7 ? pick("Die Linie wächst mit jedem Tag; erst nach einigen Wochen sagt sie etwas aus. ", "The line grows each day; it only means something after a few weeks. ") : "") +
      pick("Experiment: Mittelwert der Ausschläge aller verfügbaren Signale, nicht objektiv und nicht Teil des Dreier-Pegels.", "Experiment: mean of the readings of all available signals, not objective and not part of the Dreier Gauge.");
  }

  function liste(boxId, zeilen, max) {
    var box = $(boxId); box.textContent = "";
    var rest = null;
    zeilen.forEach(function (z, i) {
      if (i === max) { rest = el("details", "mehr"); rest.appendChild(el("summary", "", txt("alle", zeilen.length))); box.appendChild(rest); }
      (rest || box).appendChild(z);
    });
  }
  function link(url, text) {
    if (/^https:\/\//.test(url || "")) { var a = el("a", "", text); a.href = url; a.rel = "noopener"; return a; }
    return el("span", "", text);
  }
  function luecke(q, stand) {
    if (!q.daten_seit || !stand) return "";
    var von = new Date(stand + "T00:00:00Z"); von.setUTCDate(von.getUTCDate() - q.fenster_tage);
    return new Date(q.daten_seit + "T00:00:00Z") > von ? txt("luecke", datum(q.daten_seit)) : "";
  }
  var d_stand = null, d_skala = null;
  function zeigeBsi(b) {
    if (!b) { $("bsi-info").textContent = txt("keine"); $("bsi-liste").textContent = txt("keine"); return; }
    $("bsi-info").textContent = txt("bsi_info", b.fenster_tage, b.kritisch_30_tage, b.hoch_30_tage, b.kritisch_7_tage, b.hoch_7_tage, datum(b.abgerufen_am)) + luecke(b, d_stand);
    liste("bsi-liste", (b.liste || []).map(function (e) {
      var r = el("div", "row zeile");
      r.appendChild(el("span", "mono dim", datum(e.datum)));
      r.appendChild(el("span", "mono " + (e.schwere === "kritisch" ? "rw" : ""), (window.I18N.t("schwere") || {})[e.schwere] || e.schwere));
      var t = el("span", "titel"); t.appendChild(link(e.link, e.titel)); r.appendChild(t);
      return r;
    }), 8);
  }
  function zeigeEu(u) {
    if (!u) { $("eu-info").textContent = txt("keine"); $("eu-liste").textContent = txt("keine"); return; }
    $("eu-info").textContent = txt("eu_info", u.neu_30_tage, u.fenster_tage, datum(u.abgerufen_am)) + luecke(u, d_stand);
    liste("eu-liste", (u.liste || []).map(function (e) {
      var r = el("div", "row zeile");
      r.appendChild(el("span", "mono dim", datum(e.ausgenutzt_seit)));
      r.appendChild(el("span", "mono", (e.hersteller || []).join(", ") || "–"));
      var t = el("span", "titel"); t.appendChild(link(e.link, (e.cve && e.cve[0]) || e.id)); r.appendChild(t);
      return r;
    }), 8);
  }

  (function () {
    var b = $("rss-kopieren"); if (!b) return;
    b.addEventListener("click", function () {
      var u = b.getAttribute("data-feed"), t = $("rss-btn"), ok = function () { t.textContent = pick("Kopiert – jetzt im Reader einfügen", "Copied – now paste it into your reader"); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(u).then(ok, function () { window.location.href = "feed.xml"; });
      else window.location.href = "feed.xml";
    });
  })();

  function zeichneScope(sig) {
    var svg = $("rd-scope"); if (!svg) return;
    var NS = "http://www.w3.org/2000/svg", C = 200, R = 128, MAX = 2;
    var sv = function (tag, at, par) { var n = document.createElementNS(NS, tag); for (var k in at) n.setAttribute(k, at[k]); (par || svg).appendChild(n); return n; };
    svg.textContent = "";
    var t = sv("title", { id: "rd-scope-t" }); t.textContent = pick("Radar der Signale: je weiter außen, desto stärker der Ausschlag", "Signal radar: the further out, the stronger the reading");
    var defs = sv("defs", {}), g = sv("radialGradient", { id: "rd-sw", cx: "0", cy: "0", r: "1" }, defs);
    sv("stop", { offset: "0", "stop-color": "#3ddc84", "stop-opacity": "0" }, g); sv("stop", { offset: "1", "stop-color": "#3ddc84", "stop-opacity": ".28" }, g);
    [0.5, 1, 1.5, 2].forEach(function (f) { sv("circle", { cx: C, cy: C, r: R * f / MAX, "class": f === 1 ? "sc-ring sc-schw" : "sc-ring" }); });
    var n = sig.length, pos = function (i, f) { var w = -Math.PI / 2 + i * 2 * Math.PI / n; return [C + Math.cos(w) * R * f / MAX, C + Math.sin(w) * R * f / MAX, w]; };
    sig.forEach(function (s, i) { var p = pos(i, MAX); sv("line", { x1: C, y1: C, x2: p[0], y2: p[1], "class": "sc-ax" }); });
    var sw = sv("g", { "class": "sc-sweep" });
    sv("path", { d: "M" + C + " " + C + " L" + C + " " + (C - R) + " A" + R + " " + R + " 0 0 0 " + (C - R * Math.sin(Math.PI / 4)) + " " + (C - R * Math.cos(Math.PI / 4)) + " Z", fill: "url(#rd-sw)" }, sw);
    sv("line", { x1: C, y1: C, x2: C, y2: C - R, "class": "sc-arm" }, sw);
    var pts = [];
    sig.forEach(function (s, i) { if (typeof s.ausschlag === "number") { var p = pos(i, Math.min(s.ausschlag, MAX)); pts.push(p[0].toFixed(1) + "," + p[1].toFixed(1)); } });
    if (pts.length > 2) sv("polygon", { points: pts.join(" "), "class": "sc-poly" });
    sig.forEach(function (s, i) {
      var l = pos(i, MAX + 0.34), nm = pick(s.name, s.name_en).split(" (")[0], dp = s.name_en === "Dreier Gauge"; if (dp && window.DP) nm += " · " + window.DP;
      var tx = sv("text", { x: l[0], y: l[1], "class": "sc-lab" + (dp ? " dp" : ""), "text-anchor": Math.abs(Math.cos(l[2])) < 0.3 ? "middle" : (Math.cos(l[2]) > 0 ? "start" : "end"), "dominant-baseline": "middle" });
      tx.textContent = nm;
      if (typeof s.ausschlag === "number") {
        var p = pos(i, Math.min(s.ausschlag, MAX));
        if (dp) sv("circle", { cx: p[0], cy: p[1], r: 13, "class": "sc-dpring" });
        sv("circle", { cx: p[0], cy: p[1], r: dp ? 8 : 6, "class": "sc-blip " + (s.erhoeht ? "an" : "aus") + (s.art === "eigen" ? " eigen" : "") });
      } else {
        var q = pos(i, 0.25); sv("circle", { cx: q[0], cy: q[1], r: 5, "class": "sc-blip kn" });
      }
    });
    var sl = sv("text", { x: C - R / 2 - 5, y: C - 5, "class": "sc-tx", "text-anchor": "end" }); sl.textContent = pick("Schwelle", "threshold");
  }

  function zeigeKonsens(r) {
    var k = r && r.konsens, z = $("konsens-zeile"), box = $("rd-signale"); box.textContent = "";
    if (!k || !k.bewertet) { $("rd-kon").textContent = txt("keine"); return; }
    var satz = pick(k.erhoeht + " von " + k.bewertet + " externen Signalen zeigen erhöht.", k.erhoeht + " of " + k.bewertet + " external signals show elevated.");
    $("rd-kon").textContent = satz + " " + pick("Stand ", "As of ") + datum(r.abgerufen_am) + ".";
    z.textContent = ""; z.appendChild(el("b", "", k.erhoeht + "/" + k.bewertet)); z.appendChild(document.createTextNode(pick(" externe Signale zeigen ebenfalls erhöht", " external signals also show elevated"))); z.appendChild(el("span", "zr", " · " + pick("Stand ", "as of ") + datum(r.abgerufen_am))); z.hidden = false;
    var sc = k.score, sb = $("rd-score"); sb.textContent = "";
    var ampel = (sc.stufe && sc.stufe.ampel) || "", rb = $("radar"), fzb = $("fazit");
    ["ruhig", "unauffaellig", "angespannt", "hoch", "ausserordentlich"].forEach(function (a) { [sb, rb, fzb].forEach(function (n) { if (n) n.classList.remove("ra-" + a); }); });
    if (ampel) [sb, rb, fzb].forEach(function (n) { if (n) n.classList.add("ra-" + ampel); });
    if (sc) {
      var gr = el("div", "sw mono", String(sc.wert)); gr.appendChild(el("small", "", " / 100")); if (sc.stufe) gr.appendChild(el("small", "sst", " · " + pick(sc.stufe.name, sc.stufe.name_en))); sb.appendChild(gr);
      var tx = el("div", "st");
      tx.appendChild(el("b", "mono", pick("Radar-Score · Experiment", "Radar score · experiment")));
      tx.appendChild(el("span", "", pick(
        "Gleich gewichteter Mittelwert der Ausschläge von " + sc.signale + " von " + sc.von + " Signalen. 50 heißt: die Regelschwellen sind im Schnitt erreicht, 100: im Schnitt doppelt so weit. Die Zeiträume der Signale sind verschieden, Messungen und Einschätzungen gemischt. Kein objektives Maß, es fließt nicht in den Dreier-Pegel ein. Tagesstand wird ab " + datum(sc.live_seit) + " gespeichert.",
        "Equally weighted mean of the readings of " + sc.signale + " of " + sc.von + " signals. 50 means the rule thresholds are reached on average, 100 twice as far. The signals cover different periods, measurements and assessments are mixed. Not an objective measure, it does not feed into the Dreier Gauge. The daily value is stored from " + datum(sc.live_seit) + ".")));
      tx.appendChild(el("span", "mono dim", pick("Stand: ", "as of: ") + datum(r.abgerufen_am)));
      sb.appendChild(tx); sb.hidden = false;
      var sk = $("rd-skala"), kal = d_skala;
      if (sk && kal && kal.stufen) {
        sk.textContent = "";
        var bar = el("div", "ska"); var von = 0;
        kal.stufen.forEach(function (x) {
          var bis = Math.min(x.bis, 100), seg = el("span", "sg ra-" + x.ampel); seg.style.width = (bis - von) + "%";
          seg.title = pick(x.name, x.name_en) + " (" + von + "–" + (bis === 100 ? 100 : bis - 1) + ")"; bar.appendChild(seg); von = bis;
        });
        var mk = el("i", "mk"); mk.style.left = Math.max(0, Math.min(100, sc.wert)) + "%"; bar.appendChild(mk);
        var zt = el("div", "skz mono"); [0, 30, 50, 64, 80, 100].forEach(function (n) { var t = el("span", "", String(n)); t.style.left = n + "%"; zt.appendChild(t); });
        sk.appendChild(bar); sk.appendChild(zt);
        sk.appendChild(el("p", "mono dim fine", pick("Stufen: ruhig, unauffällig, angespannt, hoch, außergewöhnlich. Grenzen vorläufig, am Dreier-Pegel ausgerichtet.", "Levels: calm, unremarkable, tense, high, exceptional. Limits provisional, aligned with the Dreier Gauge.")));
        sk.hidden = false;
      }
    }
    zeichneScope(k.signale || []);
    (k.signale || []).forEach(function (s) {
      var b = el("div", "sg"), st = s.erhoeht === true ? ["●", "an"] : (s.erhoeht === false ? ["○", "aus"] : ["–", "kn"]);
      b.appendChild(el("span", "p mono " + st[1], st[0]));
      b.appendChild(el("span", "n", pick(s.name, s.name_en) + (s.art === "eigen" ? pick(" (eigen)", " (own)") : "") + " · " + (s.erhoeht === true ? pick("erhöht", "elevated") : (s.erhoeht === false ? pick("normal", "normal") : pick("noch keine Aussage", "no rating yet")))));
      b.appendChild(el("span", "g", typeof s.ausschlag === "number" ? pick("Ausschlag ", "reading ") + s.ausschlag.toLocaleString(window.I18N.locale, { minimumFractionDigits: 1, maximumFractionDigits: 2 }) + pick("-fache der Schwelle", "x the threshold") : pick("noch kein Messwert", "no reading yet")));
      box.appendChild(b);
    });
  }

  function zeigeKern(d) {
    var r = d.radar && d.radar.zeit_bis_kev, j = r && r.jetzt, v = r && r.vor_12_monaten;
    var proz = function (x) { return typeof x === "number" ? Math.round(x * 100) + " %" : "–"; };
    var tg = function (x) { return typeof x === "number" ? x.toLocaleString(window.I18N.locale, { maximumFractionDigits: 1 }) : "–"; };
    var sw = d.schwellen || {}, box = $("kern"); box.textContent = "";
    var karte = function (wert, einheit, label, unter, ziel) {
      var a = el(ziel ? "a" : "div", "kk"); if (ziel) a.href = ziel;
      var w = el("div", "w mono", wert); if (einheit) w.appendChild(el("small", "", einheit)); a.appendChild(w);
      a.appendChild(el("div", "l", label)); if (unter) a.appendChild(el("div", "u", unter)); box.appendChild(a);
    };
    var pd = $("pegel-def");
    if (pd) pd.textContent = pick("Der Dreier-Pegel misst die Menge: wie viele ausgenutzte Schwachstellen in den letzten 30 Tagen neu in den KEV-Katalog kamen", "The Dreier Gauge measures the amount: how many exploited vulnerabilities were newly added to the KEV catalog in the last 30 days") +
      (typeof sw.hoch_ab === "number" ? pick(". Erhöht ab ", ". Elevated from ") + sw.erhoeht_ab + pick(", hoch ab ", ", high from ") + sw.hoch_ab + "." : ".");
    var ok = j && v && j.n_frisch >= 10 && v.n_frisch >= 10 && typeof j.median_frisch === "number" && typeof v.median_frisch === "number";
    if (ok) {
      karte(tg(j.median_frisch), pick(" Tage", " days"), pick("Median bis zur KEV-Aufnahme", "median time to KEV listing"), pick("vor 12 Monaten: ", "12 months ago: ") + tg(v.median_frisch), "#radar");
      karte(proz(j.anteil_30), "", pick("binnen 30 Tagen im KEV", "listed within 30 days"), pick("vor 12 Monaten: ", "12 months ago: ") + proz(v.anteil_30), "#radar");
      var q = v.median_frisch / Math.max(j.median_frisch, 0.5), s = $("schlagzeile"), n = (Math.round(q * 10) / 10).toLocaleString(window.I18N.locale);
      s.textContent = q >= 1.5 ? pick("Lücken kommen rund " + n + "-mal schneller in den KEV als vor einem Jahr.", "Vulnerabilities reach KEV about " + n + " times faster than a year ago.")
        : (q <= 0.67 ? pick("Lücken kommen langsamer in den KEV als vor einem Jahr.", "Vulnerabilities reach KEV more slowly than a year ago.")
        : pick("Lücken kommen ungefähr so schnell in den KEV wie vor einem Jahr.", "Vulnerabilities reach KEV about as fast as a year ago."));
      s.hidden = false; $("tempo-box").hidden = false;
    }
  }

  function zeigeRadar(r, d) {
    var proz = function (x) { return typeof x === "number" ? Math.round(x * 100) + " %" : "–"; };
    var tage = function (x) { return typeof x === "number" ? x.toLocaleString(window.I18N.locale, { maximumFractionDigits: 1 }) : "–"; };
    if (!r) { ["rd-zahlen", "rd-treffer", "rd-eu", "rd-k-score", "rd-gruende"].forEach(function (id) { $(id).textContent = txt("keine"); }); return; }
    var z = r.zeit_bis_kev || {};
    var zahlenBox = $("rd-zahlen"); zahlenBox.textContent = "";
    [["jetzt", pick("letzte 90 Tage", "last 90 days"), true], ["vor_12_monaten", pick("vor 12 Monaten", "12 months ago")], ["vor_24_monaten", pick("vor 24 Monaten", "24 months ago")]].forEach(function (k) {
      var f = z[k[0]]; if (!f) return;
      var b = el("div", "rd-z mono" + (k[2] ? " neu" : ""));
      b.appendChild(el("div", "l", k[1]));
      b.appendChild(el("div", "w", proz(f.anteil_30)));
      b.appendChild(el("div", "u", pick("binnen 30 Tagen · Median ", "within 30 days · median ") + tage(f.median_frisch) + pick(" Tage", " days")));
      zahlenBox.appendChild(b);
    });
    zeichneRadar(z.verlauf || []);
    $("rd-zeit-fine").textContent = pick(
      "Gemessen wird die Zeit zwischen Veröffentlichung einer CVE (CVE-Liste) und ihrer Aufnahme in den CISA-KEV. Der Median zählt nur frische Lücken (höchstens " + (z.frisch_tage || 365) + " Tage alt bei Aufnahme). Das ist die Aufnahme, nicht der erste Angriff, und Eigenmessung aus CC0- und CVE-Daten.",
      "We measure the time between a CVE being published (CVE list) and its addition to CISA KEV. The median counts only fresh vulnerabilities (at most " + (z.frisch_tage || 365) + " days old at addition). This is the listing, not the first attack. Own analysis of CC0 and CVE data.");
    var t = r.trefferquote || {};
    $("rd-treffer").textContent = typeof t.quote_reif === "number"
      ? pick(proz(t.quote_reif) + " der " + t.reif + " Prognosen (EPSS ab " + Math.round((t.schwelle || 0.1) * 100) + " %), die älter als " + t.reif_nach_tagen + " Tage sind, standen später im KEV. Insgesamt geprüft seit " + datum(t.seit) + ": " + t.prognosen + ", eingetreten: " + t.eingetreten + ".",
             proz(t.quote_reif) + " of the " + t.reif + " forecasts (EPSS from " + Math.round((t.schwelle || 0.1) * 100) + " %) older than " + t.reif_nach_tagen + " days were later listed in KEV. Checked since " + datum(t.seit) + ": " + t.prognosen + ", occurred: " + t.eingetreten + ".")
      : pick("Wir speichern jede Prognose des Ausblicks (EPSS ab " + Math.round((t.schwelle || 0.1) * 100) + " %) und prüfen später, ob die Lücke im KEV landet. Bisher gespeichert: " + (t.prognosen || 0) + ", davon eingetreten: " + (t.eingetreten || 0) + ". Die erste Quote erscheint " + (t.reif_nach_tagen || 30) + " Tage nach dem ersten gespeicherten Wert, vorher wäre sie nicht belastbar.",
             "We store every forecast of the outlook (EPSS from " + Math.round((t.schwelle || 0.1) * 100) + " %) and check later whether the vulnerability lands in KEV. Stored so far: " + (t.prognosen || 0) + ", occurred: " + (t.eingetreten || 0) + ". The first rate appears " + (t.reif_nach_tagen || 30) + " days after the first stored value; earlier it would not be reliable.");
    var e = r.europa;
    $("rd-eu").textContent = !e ? txt("keine") : pick(
      e.auch_im_cisa + " von " + e.eu_eintraege + " Einträgen im EU-KEV stehen auch im CISA-KEV, " + e.nur_eu + " nur in der EU. Bei " + e.eu_datum_frueher + " nennt die EU ein früheres Ausnutzungsdatum als die Aufnahme bei der CISA (Median-Abstand " + tage(e.median_abstand_tage) + " Tage). Der EU-Katalog bildet den US-Katalog also fast vollständig ab.",
      e.auch_im_cisa + " of " + e.eu_eintraege + " entries in EU-KEV are also in CISA KEV, " + e.nur_eu + " only in the EU. For " + e.eu_datum_frueher + " the EU names an earlier exploitation date than the CISA listing (median gap " + tage(e.median_abstand_tage) + " days). The EU catalogue thus mirrors the US catalogue almost completely.");
    ["rd-k-score", "rd-k-ktx"].forEach(function (id) { $(id).textContent = ""; });
    var sigO = {}; ((r.konsens && r.konsens.signale) || []).forEach(function (x) { sigO[x.name_en] = x; });
    var kachel = function (o) {
      var sg = o.sig ? sigO[o.sig] : null;
      var b = el("div", "kc " + (o.gr === "ktx" ? "ktx" : "") + (sg && sg.erhoeht === true ? " an" : (sg && sg.erhoeht === false ? " aus" : "")));
      var kopf = el("div", "kc-k mono"); kopf.appendChild(o.url ? link(o.url, o.name) : document.createTextNode(o.name));
      var nat = o.nat === "eins" ? pick("Einschätzung", "Assessment") : (o.nat === "ktx" ? pick("Kontext", "Context") : pick("Messung", "Measurement"));
      kopf.appendChild(el("span", "kc-a", nat + (o.quelle === "eigen" ? pick(" · eigen", " · own") : (o.quelle === "extern" ? pick(" · extern", " · external") : ""))));
      b.appendChild(kopf);
      var w = el("div", "kc-w mono", o.wert); if (o.einheit) w.appendChild(el("small", "", o.einheit)); b.appendChild(w);
      b.appendChild(el("div", "kc-m", o.misst));
      if (sg) b.appendChild(el("div", "kc-r", pick("Regel: ", "rule: ") + pick(sg.grund, sg.grund_en) + " · " + pick("Zeitraum: ", "period: ") + pick(sg.zeitraum, sg.zeitraum_en)));
      b.appendChild(el("div", "kc-s mono", o.stand));
      $(o.gr === "ktx" ? "rd-k-ktx" : "rd-k-score").appendChild(b);
    };
    var tg = pick("Stand ", "as of ");
    var jz = z.jetzt || {}, v12 = z.vor_12_monaten || {};
    if (typeof jz.median_frisch === "number") kachel({ gr: "score", nat: "mess", quelle: "eigen", sig: "Speed to KEV", name: pick("Tempo bis KEV", "Speed to KEV"), wert: tage(jz.median_frisch), einheit: pick(" Tage Median", " days median"), misst: pick("Veröffentlichung bis KEV-Aufnahme, vor 12 Monaten: ", "publication to KEV listing, 12 months ago: ") + tage(v12.median_frisch) + pick(" Tage", " days"), stand: pick("Quelle CISA KEV · abgerufen ", "source CISA KEV · retrieved ") + datum(((d.quellen || []).filter(function (x) { return x.id === "cisa-kev"; })[0] || {}).abgerufen_am || d.stand) });
    (r.einschaetzungen || []).forEach(function (q) {
      var pfeil = q.richtung === "steigend" ? " ↑" : (q.richtung === "fallend" ? " ↓" : ""), idx = q.wert && q.basis;
      if (!idx) return; // Lagebericht-Urteil steht schon bei den Gründen
      kachel({ gr: idx ? "score" : "ktx", nat: "eins", quelle: "extern", sig: idx ? "BSI Cyber Index" : null, name: q.name, url: q.link, wert: idx ? String(Math.round(q.wert / q.basis * 100)) : pick(q.urteil, q.urteil_en) + pfeil, einheit: idx ? pick(" % von 2024", " % of 2024") : "", misst: pick(q.misst, q.misst_en), stand: pick("Bericht vom ", "report of ") + datum(q.stand) + pick(" · von Hand geprüft ", " · checked by hand ") + datum(q.geprueft_am) + pick(" · jährlich", " · yearly") + (q.vorher ? pick(" · Vorjahr: ", " · year before: ") + pick(q.vorher, q.vorher_en) : "") });
    });
    if (r.sans) {
      var sn = { green: ["ruhig (grün)", "calm (green)"], yellow: ["erhöht (gelb)", "raised (yellow)"], orange: ["hoch (orange)", "high (orange)"], red: ["kritisch (rot)", "critical (red)"] }[r.sans.status] || ["–", "–"];
      kachel({ gr: "score", nat: "eins", quelle: "extern", sig: "SANS Infocon", name: "SANS Infocon", url: "https://isc.sans.edu/", wert: pick(sn[0], sn[1]), misst: pick("Scans und Ausbrüche im Netz", "scans and outbreaks across the internet"), stand: tg + datum(r.sans.abgerufen_am) + " · live" });
    }
    if (r.feodo) kachel({ gr: "score", nat: "mess", quelle: "extern", sig: "Botnet servers (Feodo)", name: pick("Botnetz-Server (Feodo)", "Botnet servers (Feodo)"), url: "https://feodotracker.abuse.ch/", wert: zahl(r.feodo.online), einheit: pick(" aktiv", " active"), misst: pick("aktive Steuerserver, abuse.ch", "active command servers, abuse.ch"), stand: pick("täglich · ", "daily · ") + ((r.konsens && r.konsens.messtage_feodo) || 0) + pick(" Messtage · abgerufen ", " days of data · fetched ") + datum(r.abgerufen_am) });
    if (typeof t.prognosen === "number") kachel({ gr: "ktx", nat: "mess", quelle: "eigen", name: pick("Trefferquote Ausblick", "Outlook hit rate"), wert: typeof t.quote_reif === "number" ? proz(t.quote_reif) : "–", misst: pick("Prognosen: ", "forecasts: ") + t.prognosen + pick(", eingetreten: ", ", occurred: ") + t.eingetreten, stand: (typeof t.quote_reif === "number" ? "" : pick("erste Quote nach 30 Tagen · ", "first rate after 30 days · ")) + pick("eigener Abgleich EPSS gegen KEV · Stand ", "own comparison EPSS vs KEV · as of ") + datum(r.abgerufen_am) });
    if (e) kachel({ gr: "ktx", nat: "mess", quelle: "eigen", name: "EU-KEV", wert: e.auch_im_cisa + "/" + e.eu_eintraege, misst: pick("EU-Einträge, die auch im CISA-KEV stehen", "EU entries also in CISA KEV"), stand: pick("eigener Abgleich EUVD (ENISA) gegen CISA-KEV · abgerufen ", "own comparison EUVD (ENISA) vs CISA KEV · retrieved ") + datum((d.eu_kev || {}).abgerufen_am || r.abgerufen_am) });
    if (r.ncsc) kachel({ gr: "ktx", nat: "mess", quelle: "extern", name: "NCSC-NL", url: "https://advisories.ncsc.nl/", wert: zahl(r.ncsc.advisories_30), einheit: pick(" Advisories", " advisories"), misst: zahl(r.ncsc.hoch_hoch_30) + pick(" davon mit Kans und Schade hoch", " rated likelihood and damage high"), stand: pick("30 Tage · ", "30 days · ") + tg + datum(r.abgerufen_am) });
    (d.sektor || []).forEach(function (x) {
      kachel({ gr: "ktx", nat: "ktx", quelle: "extern", name: "ENISA", url: /^https:\/\//.test(x.link || "") ? x.link : null, wert: x.wert.toLocaleString(window.I18N.locale, { maximumFractionDigits: 1 }), einheit: " %", misst: pick("der Ereignisse " + x.berichtsjahr + " betrafen die öffentliche Verwaltung (EU)", "of events in " + x.berichtsjahr + " affected public administration (EU)"), stand: "Threat Landscape 2026, S. " + x.seite + " · " + x.lizenz });
    });
    var ul = $("rd-gruende"); ul.textContent = "";
    (r.gruende || []).forEach(function (g) {
      var li = el("li", "", pick(g.aussage, g.aussage_en) + " ");
      li.appendChild(link(g.link, "[" + g.quelle + "]"));
      var pe = ((r.pruefung || {}).eintraege || []).filter(function (e) { return e.id === g.id; })[0];
      var st = el("span", "pr mono" + (pe && (pe.faellig || pe.link_tot) ? " warn" : ""),
        " " + pick("geprüft ", "checked ") + datum(g.geprueft_am) + (pe && pe.faellig ? pick(" · Prüfung fällig", " · check due") : "") + (pe && pe.link_tot ? pick(" · Link prüfen", " · check link") : ""));
      li.appendChild(st); ul.appendChild(li);
    });
    var pt = $("pruef-tabelle"), pr = r.pruefung;
    if (pt && pr) {
      pt.textContent = "";
      var kopf = el("tr", ""); [pick("Angabe", "Entry"), pick("geprüft", "checked"), pick("fällig am", "due"), pick("Quelle", "source")].forEach(function (h) { kopf.appendChild(el("th", "", h)); });
      pt.appendChild(el("thead", "")).appendChild(kopf);
      var tb = el("tbody", ""); pt.appendChild(tb);
      pr.eintraege.forEach(function (e) {
        var tr = el("tr", ""); tb.appendChild(tr);
        tr.appendChild(el("td", "", e.name)); tr.appendChild(el("td", "mono", datum(e.geprueft_am)));
        tr.appendChild(el("td", "mono" + (e.faellig ? " warn" : ""), datum(e.faellig_am) + (e.faellig ? pick(" · fällig", " · due") : "")));
        var td = el("td", "mono" + (e.link_tot ? " warn" : ""), e.link_tot ? pick("nicht erreichbar", "unreachable") : (e.erreichbar ? pick("erreichbar", "reachable") : pick("Fehlschlag, wird wiederholt", "failed, will retry")));
        tr.appendChild(td);
      });
    }
    var pz = $("rd-pruef");
    if (pz) pz.textContent = pr ? pick("Prüfstand: ", "Check status: ") + (pr.offen.length ? pr.offen.length + pick(" Angaben brauchen eine Prüfung.", " items need a check.") : pick("alle Angaben innerhalb der Frist, alle Quellen erreichbar", "all items within their deadline, all sources reachable")) + " (" + datum(pr.stand) + ")" : "";
  }

  function zeichneRadar(v) {
    var svg = $("rd-chart"), NS = "http://www.w3.org/2000/svg";
    svg.textContent = "";
    var ti = document.createElementNS(NS, "title"); ti.id = "rd-chart-titel"; svg.appendChild(ti);
    if (!v.length) return;
    var B = Math.max(300, Math.round(svg.getBoundingClientRect().width)) || 1000, H = B < 600 ? 170 : 200, L = 36, R = 8, T = 10, U = 26;
    svg.setAttribute("viewBox", "0 0 " + B + " " + H);
    var mk = function (tag, a, tx) { var e = document.createElementNS(NS, tag); for (var k in a) e.setAttribute(k, a[k]); if (tx !== undefined) e.textContent = tx; svg.appendChild(e); return e; };
    var y = function (p) { return T + (H - T - U) * (1 - p); }, w = (B - L - R) / v.length;
    [0, 0.5, 1].forEach(function (p) {
      mk("line", { x1: L, x2: B - R, y1: y(p), y2: y(p), stroke: "#1d262e" });
      mk("text", { x: L - 6, y: y(p) + 4, "text-anchor": "end", fill: "#8a99a6", "font-size": 11, "font-family": "ui-monospace,monospace" }, Math.round(p * 100) + " %");
    });
    v.forEach(function (p, i) {
      var t = mk("rect", { x: L + i * w + 1, y: y(p.anteil_30), width: Math.max(w - 2, 1), height: y(0) - y(p.anteil_30), fill: i === v.length - 1 ? "#ff8a7a" : "#3fae7a" });
      t.appendChild(document.createElementNS(NS, "title")).textContent = p.monat + ": " + Math.round(p.anteil_30 * 100) + " % (" + p.n + ")";
    });
    [0, Math.floor(v.length / 2), v.length - 1].forEach(function (i) {
      mk("text", { x: L + i * w + w / 2, y: H - 8, "text-anchor": i === 0 ? "start" : (i === v.length - 1 ? "end" : "middle"), fill: "#8a99a6", "font-size": 11, "font-family": "ui-monospace,monospace" }, v[i].monat);
    });
    $("rd-chart-titel").textContent = pick("Anteil der KEV-Aufnahmen binnen 30 Tagen nach Veröffentlichung, je Monat, " + v[0].monat + " bis " + v[v.length - 1].monat + ", zuletzt " + Math.round(v[v.length - 1].anteil_30 * 100) + " %",
      "Share of KEV additions within 30 days of publication, per month, " + v[0].monat + " to " + v[v.length - 1].monat + ", latest " + Math.round(v[v.length - 1].anteil_30 * 100) + " %");
  }

  function zeigeAusblick(u) {
    if (!u) { $("ab-info").textContent = txt("keine"); $("ab-liste").textContent = txt("keine"); return; }
    var prozent = function (x) { return (x * 100).toLocaleString(window.I18N.locale, { maximumFractionDigits: 1 }) + " %"; };
    $("ab-info").textContent = txt("ab_info", u.fenster_tage, zahl(u.geprueft), zahl(u.hoch_wahrscheinlich), Math.round((u.schwelle_hoch || 0.1) * 100), datum(u.abgerufen_am));
    liste("ab-liste", (u.liste || []).map(function (e) {
      var r = el("div", "row zeile");
      r.appendChild(el("span", "mono dim", datum(e.veroeffentlicht)));
      r.appendChild(el("span", "mono " + (e.epss >= (u.schwelle_hoch || 0.1) ? "rw" : ""), txt("ab_zeile", prozent(e.epss))));
      r.appendChild(el("span", "mono dim", typeof e.cvss === "number" ? "CVSS " + e.cvss.toLocaleString(window.I18N.locale, { minimumFractionDigits: 1 }) : "CVSS –"));
      var t = el("span", "titel"); t.appendChild(link(e.link, e.cve)); r.appendChild(t);
      return r;
    }), 10);
  }
})();
