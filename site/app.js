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

  function oeffne() {
    var id = (location.hash || "").slice(1), sec = id && document.getElementById(id), d = sec && sec.querySelector("details.sek");
    if (d) d.open = true;
  }
  window.addEventListener("hashchange", oeffne);
  document.addEventListener("click", function (e) {
    var l = e.target.closest && e.target.closest("a[href^='#']"); if (!l) return;
    var sec = document.getElementById(l.getAttribute("href").slice(1)), d = sec && sec.querySelector("details.sek"); if (d) d.open = true;
  });
  window.addEventListener("load", oeffne);
  // Ohne Ziel im Link immer oben starten: sonst stellt der Browser eine alte Scrollposition wieder her, die nach dem Nachladen der Daten woanders (z. B. beim Fazit) liegt.
  if (!location.hash) {
    try { history.scrollRestoration = "manual"; } catch (e) { /* ältere Browser */ }
    var oben = function () { if (!location.hash) window.scrollTo({ top: 0, left: 0, behavior: "instant" }); };
    oben(); window.addEventListener("load", oben); window.addEventListener("pageshow", oben);
  }

  var knopf = $("totop");
  if (knopf) {
    var weich = !(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    knopf.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: weich ? "smooth" : "auto" }); });
    var navLinks = Array.prototype.slice.call(document.querySelectorAll(".navin a[data-sec], .navin summary[data-sec]"));
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
      fz.appendChild(el("p", "mono dim fine", pick("Feste Sätze nach Regeln, keine Vorhersage. Stufen des Dreier-Pegels geprüft am ", "Fixed sentences by rule, no forecast. Dreier Gauge levels checked on ") + datum(f.stand) + "."));
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
    var kk = $("kev-kopf"); if (kk) kk.textContent = pick("Quelle: CISA KEV-Katalog (US-Behörde) · Katalog veröffentlicht ", "Source: CISA KEV catalog (US agency) · catalog published ") + datum(kq.veroeffentlicht_am) + pick(" · abgerufen ", " · retrieved ") + datum(kq.abgerufen_am);
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
      var fd = Date.parse(e.frist), tg = (fd - Date.now()) / 86400000;
      tr.appendChild(el("td", "mono" + (isNaN(fd) ? "" : (tg < 0 ? " fr-over" : (tg < 7 ? " fr-bald" : ""))), datum(e.frist)));
      tr.appendChild(e.ransomware_bekannt ? el("td", "rw", txt("bekannt")) : (function () { var c = el("td", "dim", "–"); c.title = txt("nicht_bekannt"); return c; })());
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
    zeichneScoreVerlauf(d.pegel || null);
    var tl = d.telegram && d.telegram.link;
    if (/^https:\/\/t\.me\//.test(tl || "")) { $("telegram-link").href = tl; $("telegram").hidden = false; }
    d_stand = d.stand; d_skala = d.radar_skala || null;
    zeigeBsi(d.cert_bund);
    zeigeEu(d.eu_kev);
    zeigeAusblick(d.ausblick);
    zeigeRadar(d.radar, d);
    zeigeKonsens(d.radar);
    zeigeTicker(d);
    zeigeTermine();
    zeigeZuerst(d.patches && d.patches.prioritaet);
    zeigeMicrosoft(d.patches && d.patches.microsoft);
    zeigeHersteller(d.patches && d.patches.hersteller);

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
    var B = Math.max(300, Math.round(svg.getBoundingClientRect().width)) || 1000, H = B < 600 ? 190 : 230, L = 30, R = 16, T = 12, U = 28;
    svg.setAttribute("viewBox", "0 0 " + B + " " + H);
    var mk = function (tag, a, t) { var e = document.createElementNS(NS, tag); for (var k in a) e.setAttribute(k, a[k]); if (t !== undefined) e.textContent = t; svg.appendChild(e); return e; };
    var y = function (n) { return T + (H - T - U) * (1 - n / 100); };
    var x = function (i) { return v.length < 2 ? (L + B - R) / 2 : L + i * (B - L - R) / (v.length - 1); };
    var mono = { "font-size": 11, "font-family": "ui-monospace,monospace", fill: "#8a99a6" };
    [0, 50, 100].forEach(function (n) {
      mk("line", { x1: L, x2: B - R, y1: y(n), y2: y(n), stroke: n === 50 ? "#263340" : "#1d262e", "stroke-dasharray": n === 50 ? "4 4" : "0" });
      mk("text", Object.assign({ x: L - 6, y: y(n) + 4, "text-anchor": "end" }, mono), String(n));
    });
    [30, 64, 80].forEach(function (n) { mk("line", { x1: L, x2: B - R, y1: y(n), y2: y(n), stroke: "#1d262e", "stroke-dasharray": "2 4" }); });
    // Linie 1: alle Bausteine mit Archiv, rückgerechnet
    mk("polyline", { points: v.map(function (p, i) { return x(i) + "," + y(p.ausnutzung); }).join(" "), fill: "none", stroke: "#5a8f74", "stroke-width": 1.6 });
    // Linie 2: voller Dreier-Pegel, erst ab dem Live-Start
    var live = []; v.forEach(function (p, i) { if (typeof p.wert === "number") live.push(i); });
    if (live.length) {
      var i0 = live[0];
      mk("line", { x1: x(i0), x2: x(i0), y1: T, y2: H - U, stroke: "#6fe0a0", "stroke-dasharray": "3 3", "stroke-opacity": .5 });
      if (live.length > 1) mk("polyline", { points: live.map(function (i) { return x(i) + "," + y(v[i].wert); }).join(" "), fill: "none", stroke: "#6fe0a0", "stroke-width": 2.6 });
      live.forEach(function (i) {
        var c = mk("circle", { cx: x(i), cy: y(v[i].wert), r: 3.2, fill: "#6fe0a0" });
        c.appendChild(document.createElementNS(NS, "title")).textContent = datum(v[i].stand) + ": " + v[i].wert + " (" + v[i].signale + "/" + sc.von_bausteine + pick(" Bausteine", " components") + ")";
      });
      mk("text", Object.assign({ x: x(i0) - 6, y: T + 10, "text-anchor": "end" }, mono, { fill: "#6fe0a0" }), pick("ab hier alle Bausteine", "all components from here"));
      var il = live[live.length - 1], lw = v[il].wert, la = v[il].ausnutzung, oben = la >= lw;
      var bg = { stroke: "#0d1117", "stroke-width": 4, "paint-order": "stroke" };
      mk("text", Object.assign({ x: x(il) - 9, y: y(lw) + (oben ? 16 : -8), "text-anchor": "end" }, mono, bg, { fill: "#6fe0a0", "font-weight": 600 }), lw + pick(" · voller Pegel", " · full gauge"));
      mk("text", Object.assign({ x: x(il) - 9, y: y(la) + (oben ? -10 : 18), "text-anchor": "end" }, mono, bg, { fill: "#8fbfa6" }), la + pick(" · ohne BSI/SANS", " · without BSI/SANS"));
    }
    var pk = v.length > 120 ? [0, Math.floor(v.length / 3), Math.floor(2 * v.length / 3)] : [0];
    pk.forEach(function (i) { mk("text", Object.assign({ x: x(i), y: H - 8, "text-anchor": "start" }, mono), datum(v[i].stand)); });
    mk("text", Object.assign({ x: x(v.length - 1), y: H - 8, "text-anchor": "end" }, mono), datum(v[v.length - 1].stand));
    var t = document.createElementNS(NS, "title"); t.textContent = pick("Verlauf des Dreier-Pegels, zuletzt " + (typeof sc.wert === "number" ? sc.wert : "–") + " von 100.", "Dreier Gauge over time, latest " + (typeof sc.wert === "number" ? sc.wert : "–") + " of 100."); svg.insertBefore(t, svg.firstChild);
    var ak = v[v.length - 1].ausnutzung;
    var n0 = v[0].n, n1 = v[v.length - 1].n;
    leg.textContent = pick("Dunkle Linie: Pegel aus allen Bausteinen mit Archiv, aus echten Meldungen rückgerechnet (anfangs " + n0 + ", zuletzt " + n1 + " Bausteine, je nachdem wie weit jede Quelle zurückreicht); die heutigen Schwellen werden rückwirkend angewendet, zuletzt " + ak + ". Helle Linie: voller Dreier-Pegel einschließlich der externen Einschätzungen (BSI, SANS), die kein Archiv haben, live gespeichert seit " + datum(sc.live_seit) + ". Nichts ist geschätzt.",
      "Dark line: gauge from all components with an archive, back-calculated from real advisories (" + n0 + " components at first, " + n1 + " latest, depending on how far each source goes back); today's thresholds are applied retroactively, latest " + ak + ". Bright line: full Dreier Gauge including the external assessments (BSI, SANS), which have no archive, stored live since " + datum(sc.live_seit) + ". Nothing is estimated.");
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

  // ---------- Patches ----------
  function monatName(id) {
    var m = /^(\d{4})-(\w{3})$/.exec(id || ""), M = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], i = m ? M.indexOf(m[2]) : -1;
    return i < 0 ? (id || "") : new Date(Date.UTC(+m[1], i, 1)).toLocaleDateString(window.I18N.locale, { timeZone: "UTC", month: "long", year: "numeric" });
  }
  function kpi(wert, label, klasse) {
    var k = el("div", "pk" + (klasse ? " " + klasse : "")); k.appendChild(el("b", "mono", String(wert))); k.appendChild(el("span", "", label)); return k;
  }
  function zeichneMonate(host, monate) {
    var NS = "http://www.w3.org/2000/svg", B = 600, H = 130, L = 8, U = 26, T = 14, mx = Math.max.apply(null, monate.map(function (m) { return m.cves; })) || 1;
    var svg = document.createElementNS(NS, "svg"); svg.setAttribute("viewBox", "0 0 " + B + " " + H); svg.setAttribute("class", "p-chart"); svg.setAttribute("role", "img");
    var t = document.createElementNS(NS, "title"); t.textContent = pick("CVEs je Patch Day, ohne Chromium und Azure Linux", "CVEs per patch day, excluding Chromium and Azure Linux"); svg.appendChild(t);
    var w = (B - 2 * L) / monate.length;
    monate.forEach(function (m, i) {
      var h = (H - U - T) * m.cves / mx, x = L + i * w + w * 0.15, y = H - U - h;
      var r = document.createElementNS(NS, "rect"); r.setAttribute("x", x); r.setAttribute("y", y); r.setAttribute("width", w * 0.7); r.setAttribute("height", Math.max(h, 1));
      r.setAttribute("fill", m.ausgenutzt > 0 ? "#e3b341" : "#3a6b52"); svg.appendChild(r);
      var tt = document.createElementNS(NS, "title"); tt.textContent = monatName(m.id) + ": " + m.cves + " CVEs, " + m.ausgenutzt + pick(" ausgenutzt", " exploited"); r.appendChild(tt);
      [["" + m.cves, y - 3, "#dfe6ec"], [m.id.slice(5) + (i === 0 || m.id.slice(5) === "Jan" ? " '" + m.id.slice(2, 4) : ""), H - 8, "#8a99a6"]].forEach(function (tx) {
        var te = document.createElementNS(NS, "text"); te.setAttribute("x", x + w * 0.35); te.setAttribute("y", tx[1]); te.setAttribute("text-anchor", "middle");
        te.setAttribute("fill", tx[2]); te.setAttribute("font-size", 10); te.setAttribute("font-family", "ui-monospace,monospace"); te.textContent = tx[0]; svg.appendChild(te);
      });
    });
    host.appendChild(svg);
  }
  function fixTeile(fixe) {
    var t = [];
    (fixe || []).forEach(function (f) {
      if (f.kb) t.push("KB" + f.kb + (f.fuer ? " (" + f.fuer + ")" : ""));
      else if (f.build) t.push(pick("Version ", "version ") + f.build + (f.produkt || f.fuer ? " (" + (f.produkt || f.fuer) + ")" : ""));
      else if (f.text && f.text.toLowerCase() !== "release notes") t.push(f.text + (f.fuer ? " (" + f.fuer + ")" : ""));
    });
    return t;
  }
  var TAG_MS = 86400000;
  function nteDienstag(jahr, monat, n) {
    var d = new Date(Date.UTC(jahr, monat, 1)), erst = (2 - d.getUTCDay() + 7) % 7;
    return new Date(Date.UTC(jahr, monat, 1 + erst + 7 * (n - 1)));
  }
  function termine(heute, anzahl) {
    var t0 = Date.UTC(heute.getUTCFullYear(), heute.getUTCMonth(), heute.getUTCDate()), grp = {};
    function add(dt, ev) { var k = dt.getTime(); if (k < t0) return; (grp[k] = grp[k] || { zeit: k, ev: [] }).ev.push(ev); }
    for (var i = 0; i < 7; i++) {
      var y = heute.getUTCFullYear() + Math.floor((heute.getUTCMonth() + i) / 12), m = (heute.getUTCMonth() + i) % 12;
      var z = nteDienstag(y, m, 2), o = nteDienstag(y, m, 3);
      add(z, { n: "Microsoft Patch Day", l: "https://msrc.microsoft.com/update-guide/", art: "ms" });
      add(z, { n: "Adobe", l: "https://helpx.adobe.com/security.html", art: "adobe" });
      add(z, { n: "SAP Security Patch Day", l: "https://support.sap.com/en/my-support/knowledge-base/security-notes-news.html", art: "sap" });
      add(o, { n: [0, 3, 6, 9].indexOf(m) >= 0 ? "Oracle Critical Patch Update (CPU)" : "Oracle Critical Security Patch Update", l: "https://www.oracle.com/security-alerts/", art: "oracle" });
    }
    return Object.keys(grp).map(function (k) { return grp[k]; }).sort(function (x, y) { return x.zeit - y.zeit; }).slice(0, anzahl).map(function (g) {
      g.tage = Math.round((g.zeit - t0) / TAG_MS); return g;
    });
  }
  function inTagen(n) { return n === 0 ? pick("heute", "today") : (n === 1 ? pick("morgen", "tomorrow") : pick("in " + n + " Tagen", "in " + n + " days")); }
  function icsText(s) { return String(s).replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\n/g, "\\n"); }
  function icsDatum(ms) { var d = new Date(ms); return d.getUTCFullYear() + ("0" + (d.getUTCMonth() + 1)).slice(-2) + ("0" + d.getUTCDate()).slice(-2); }
  function icsDatei(termine) {
    var stempel = new Date().toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z", z = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//cyberlage.org//Patch-Kalender//DE", "CALSCALE:GREGORIAN"];
    termine.forEach(function (t) {
      z.push("BEGIN:VEVENT", "UID:" + t.uid + "@cyberlage.org", "DTSTAMP:" + stempel, "DTSTART;VALUE=DATE:" + icsDatum(t.zeit), "DTEND;VALUE=DATE:" + icsDatum(t.zeit + TAG_MS));
      if (t.regel) z.push("RRULE:" + t.regel);
      z.push("SUMMARY:" + icsText(t.titel), "DESCRIPTION:" + icsText(t.text), "URL:" + t.url, "TRANSP:TRANSPARENT", "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + icsText(t.titel), "TRIGGER:-PT15H", "END:VALARM", "END:VEVENT");
    });
    z.push("END:VCALENDAR");
    return z.map(function (l) { var o = [], r = l; while (r.length > 70) { o.push(r.slice(0, 70)); r = " " + r.slice(70); } o.push(r); return o.join("\r\n"); }).join("\r\n") + "\r\n";
  }
  function icsLaden(name, text) {
    var bl = new Blob([text], { type: "text/calendar;charset=utf-8" }), u = URL.createObjectURL(bl), l = document.createElement("a");
    l.href = u; l.download = name; document.body.appendChild(l); l.click(); document.body.removeChild(l); setTimeout(function () { URL.revokeObjectURL(u); }, 3000);
  }
  function zeigeTermine() {
    var host = $("t-liste"); if (!host) return;
    host.textContent = "";
    var hinweis = pick("Erinnerung am Vortag um 9 Uhr (Standard des Kalenders). Termin nach den Regeln des Herstellers, ohne Gewähr.", "Reminder the day before at 9:00 (calendar default). Date from the vendor's rules, without guarantee.");
    termine(new Date(), 6).forEach(function (g) {
      var row = el("div", "t-row" + (g.tage <= 1 ? " t-nah" : ""));
      row.appendChild(el("span", "mono t-d", new Date(g.zeit).toLocaleDateString(window.I18N.locale, { timeZone: "UTC", weekday: "short", day: "2-digit", month: "2-digit", year: "numeric" })));
      row.appendChild(el("span", "mono t-c", inTagen(g.tage)));
      var w = el("span", "t-n");
      g.ev.forEach(function (e, i) { if (i) w.appendChild(document.createTextNode(" · ")); w.appendChild(link(e.l, e.n)); });
      row.appendChild(w);
      var b = el("button", "mono t-k", pick("+ Kalender", "+ calendar")); b.type = "button"; b.setAttribute("aria-label", pick("Termin in den Kalender eintragen", "Add this date to your calendar"));
      b.addEventListener("click", function () {
        var namen = g.ev.map(function (e) { return e.n; }).join(", ");
        icsLaden("patch-termin-" + icsDatum(g.zeit) + ".ics", icsDatei([{ uid: "pt-" + icsDatum(g.zeit), zeit: g.zeit, titel: namen, text: hinweis + " cyberlage.org/#termine", url: g.ev[0].l }]));
      });
      row.appendChild(b); host.appendChild(row);
    });
    var alle = el("button", "mono t-alle", pick("Alle vier Hersteller als wiederkehrende Einträge (.ics)", "All four vendors as recurring entries (.ics)")); alle.type = "button";
    alle.addEventListener("click", function () {
      var n = termine(new Date(), 40), liste = [];
      [["ms", "FREQ=MONTHLY;BYDAY=2TU", "Microsoft Patch Day"], ["adobe", "FREQ=MONTHLY;BYDAY=2TU", "Adobe Patch Day"], ["sap", "FREQ=MONTHLY;BYDAY=2TU", "SAP Security Patch Day"],
       ["oracle", "FREQ=MONTHLY;BYDAY=3TU", "Oracle Patch-Termin (CPU im Jan, Apr, Jul, Okt, sonst Critical Security Patch Update)"]].forEach(function (d) {
        var g = n.filter(function (x) { return x.ev.some(function (e) { return e.art === d[0]; }); })[0]; if (!g) return;
        var e = g.ev.filter(function (e) { return e.art === d[0]; })[0];
        liste.push({ uid: "serie-" + d[0], zeit: g.zeit, regel: d[1], titel: d[2], text: hinweis + " cyberlage.org/#termine", url: e.l });
      });
      icsLaden("patch-kalender.ics", icsDatei(liste));
    });
    host.appendChild(alle);
  }
  function zeigeTicker(d) {
    var bar = $("ticker"), b = $("tk-b"); if (!bar || !b) return;
    var items = [], heute = new Date(), t0 = Date.UTC(heute.getUTCFullYear(), heute.getUTCMonth(), heute.getUTCDate());
    var TAG = 86400000;
    function add(text, link, art) { items.push({ t: text, l: link, a: art || "" }); }
    termine(heute, 3).forEach(function (g) {
      if (g.tage > 7) return;
      var namen = g.ev.map(function (e) { return e.n; }).join(", ");
      add((g.tage <= 1 ? inTagen(g.tage).toUpperCase() : inTagen(g.tage).charAt(0).toUpperCase() + inTagen(g.tage).slice(1)) + ": " + namen, "#termine", g.tage <= 1 ? "warn" : "");
    });
    var ms = d.patches && d.patches.microsoft && d.patches.microsoft.monate, mon = ms ? Object.keys(ms).map(function (k) { return ms[k]; }) : [], m = mon[mon.length - 1];
    if (m) {
      var alt = (t0 - Date.parse(String(m.erste_veroeffentlichung).slice(0, 10))) / TAG;
      if (alt >= 0 && alt <= 10) add(pick("Microsoft Patch Day " + monatName(m.id) + ": ", "Microsoft Patch Day " + monatName(m.id) + ": ") + zahl(m.cves) + " CVEs, " + zahl(m.ausgenutzt) + pick(" ausgenutzt", " exploited") + (m.bewertung ? " · " + pick(m.bewertung.dringlichkeit, { dringend: "urgent", zeitnah: "prompt", normal: "normal" }[m.bewertung.dringlichkeit]) : ""), "#patches", m.ausgenutzt > 0 ? "warn" : "");
      (m.nachtraege || []).forEach(function (x) { var a2 = (t0 - Date.parse(String(x.am).slice(0, 10))) / TAG; if (a2 >= 0 && a2 <= 7) add(pick("Out-of-Band-Update (Microsoft) ", "Out-of-band update (Microsoft) ") + datum(x.am) + ": " + x.neue_cves + pick(" neue Lücken", " new flaws") + (x.ausgenutzt_neu ? ", " + x.ausgenutzt_neu + pick(" ausgenutzt", " exploited") : ""), "#patches", x.ausgenutzt_neu ? "alarm" : "warn"); });
    }
    var pr = d.patches && d.patches.prioritaet && d.patches.prioritaet.liste && d.patches.prioritaet.liste[0];
    if (pr) add(pick("Diese Woche zuerst: ", "This week first: ") + (pr.cves && pr.cves[0] ? pr.cves[0] + " – " : "") + pr.titel.slice(0, 70) + " (" + pr.quelle + ")", "#p-zuerst");
    var k = d.kev || {};
    if (typeof k.neu_7_tage === "number") add(pick("CISA-KEV: ", "CISA KEV: ") + zahl(k.neu_7_tage) + pick(" neue ausgenutzte Lücken in 7 Tagen, ", " new exploited flaws in 7 days, ") + zahl(k.neu_30_tage) + pick(" in 30 Tagen", " in 30 days") + (k.ransomware_bekannt_30_tage ? " · " + zahl(k.ransomware_bekannt_30_tage) + pick(" mit Ransomware-Nutzung", " with ransomware use") : ""), "#lage", k.ransomware_bekannt_30_tage ? "warn" : "");
    if (window.DP) add("Dreier-Pegel: " + window.DP, "#lage");
    if (!items.length) { bar.hidden = true; return; }
    var reduziert = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function bau(kopie) {
      var w = el("div", "tk-s"); if (kopie) w.setAttribute("aria-hidden", "true");
      items.forEach(function (x) { var a = el("a", "tk-i " + x.a); a.href = x.l; a.textContent = x.t; if (kopie) a.tabIndex = -1; w.appendChild(a); w.appendChild(el("span", "tk-t", " \u2591 ")); });
      return w;
    }
    b.textContent = ""; b.appendChild(bau(false));
    if (!reduziert) {
      b.appendChild(bau(true));
      var laenge = items.reduce(function (s, x) { return s + x.t.length; }, 0);
      b.style.animationDuration = Math.max(30, Math.round(laenge * 0.33)) + "s";
    } else b.classList.add("still");
    bar.hidden = false;
    var pb = $("tk-p");
    if (pb && !pb.getAttribute("data-an")) { pb.setAttribute("data-an", "1"); pb.addEventListener("click", function () { var an = bar.classList.toggle("halt"); pb.setAttribute("aria-pressed", an ? "true" : "false"); pb.textContent = an ? "\u25B6" : "\u275A\u275A"; }); }
  }
  function zeigeZuerst(pr) {
    var box = $("p-zuerst"); if (!box) return;
    if (!pr) { box.hidden = true; return; }
    box.textContent = "";
    box.appendChild(el("h3", "mono rd-t", pick("Diese Woche zuerst", "This week first")));
    if (!pr.liste.length) {
      box.appendChild(el("p", "", pick("Aktuell nichts, was nach unseren Regeln vorgezogen werden muss: keine Lücke aus den Patches der letzten Wochen steht im CISA-KEV, wird vom Hersteller als ausgenutzt gemeldet oder hat eine hohe Ausnutzungswahrscheinlichkeit. Der normale Patchzyklus genügt.", "Currently nothing that needs to be moved up by our rules: no flaw from the recent patches is in the CISA KEV, reported as exploited by the vendor or has a high likelihood of exploitation. The normal patch cycle is enough.")));
    } else {
      var ol = el("ol", "p-rang"), olRest = el("ol", "p-rang"); olRest.start = 6;
      pr.liste.forEach(function (k, idx) {
        var li = el("li", "p-r" + k.stufe);
        var kopf = el("div", "p-rk");
        kopf.appendChild(el("span", "mono p-q", k.quelle));
        kopf.appendChild(link(k.link, k.cves && k.cves.length ? k.cves.slice(0, 3).join(", ") + (k.cves.length > 3 ? " …" : "") : k.titel));
        kopf.appendChild(el("span", "mono dim", " · " + datum(k.datum)));
        li.appendChild(kopf);
        li.appendChild(el("div", "p-t", k.titel));
        var det = el("details", "p-det"); det.appendChild(el("summary", "mono", pick("Warum Platz " + k.rang + "? Details", "Why rank " + k.rang + "? Details")));
        if (k.betrifft && k.betrifft !== k.quelle) det.appendChild(el("div", "p-w", pick("Betrifft: ", "Affects: ") + k.betrifft));
        det.appendChild(el("div", "p-w", pick("Warum zuerst: ", "Why first: ") + pick(k.grund, k.grund_en)));
        var bw = [];
        (k.cvss || []).forEach(function (c) { bw.push("CVSS " + String(c.score).replace(".", pick(",", ".")) + ((k.cves || []).length > 1 || k.cvss.length > 1 ? " (" + c.cve + ")" : "")); });
        if (typeof k.epss === "number") bw.push("EPSS " + Math.round(k.epss * 100) + " %");
        li.appendChild(el("div", "p-w mono", pick("Bewertung: ", "Scores: ") + (bw.length ? bw.join(" · ") : pick("CVSS noch nicht verfügbar", "CVSS not available yet")) + (k.cves && k.cves.length > 3 ? " …" : "")));
        det.appendChild(el("div", "p-w mono dim fine", pick("Rang " + k.rang + ": Stufe " + k.stufe + " von 4 (", "Rank " + k.rang + ": level " + k.stufe + " of 4 (") + pick(k.stufe_name, k.stufe_name_en) + pick("). Innerhalb der Stufe zählt EPSS, dann CVSS.", "). Within a level EPSS counts, then CVSS.")));
        var fx = el("div", "p-fix"); fx.appendChild(el("b", "mono", pick("Lösung: ", "Fix: ")));
        var teile = [];
        teile = fixTeile(k.fixe);
        fx.appendChild(document.createTextNode(teile.length ? teile.join(", ") : pick(k.patch_text, k.patch_text_en)));
        if (k.patch_link && /^https:\/\//.test(k.patch_link)) { fx.appendChild(document.createTextNode(" · ")); fx.appendChild(link(k.patch_link, /OfficeSecurityReleases/.test(k.patch_link) ? pick("Office-Release-Notes", "Office release notes") : pick("Fix-Seite", "fix page"))); }
        li.appendChild(fx);
        if (k.monat) det.appendChild(el("div", "p-w mono dim", pick("Enthalten im Microsoft Patch Day ", "Included in the Microsoft Patch Day ") + monatName(k.monat) + pick(" (Sammelupdate des Monats; Nachträge sind Out-of-Band-Updates)", " (the month's cumulative update; later additions are out-of-band updates)")));
        li.appendChild(det);
        li.setAttribute("data-i", idx); li.setAttribute("data-k", pzKey(k));
        var lb = el("label", "p-ok mono"), cb = document.createElement("input"); cb.type = "checkbox"; cb.setAttribute("data-k", pzKey(k));
        lb.appendChild(cb); lb.appendChild(document.createTextNode(" " + pick("erledigt", "done"))); kopf.appendChild(lb);
        li.setAttribute("data-t", li.textContent.toLowerCase());
        (idx < 5 ? ol : olRest).appendChild(li);
      });
      box.appendChild(ol);
      if (olRest.children.length) {
        var dt = el("details", "p-mehr"); dt.appendChild(el("summary", "mono", pick("Weitere ", "Another ") + olRest.children.length + pick(" Einträge dieser Woche", " entries this week"))); dt.appendChild(olRest); box.appendChild(dt);
      }
    }
    var op = el("div", "p-op"); op.appendChild(el("h4", "mono rd-t", pick("Angegriffen, aber noch kein Patch", "Attacked, but no patch yet")));
    op.appendChild(el("p", "mono dim fine", pick("Lücken, für die der Hersteller selbst nur eine Umgehung oder Abmilderung meldet. Hier hilft kein Update, sondern die Gegenmaßnahme im Hinweis. Belegen können wir das nur dort, wo der Hersteller es angibt (derzeit Microsoft). Der CISA-KEV nennt keinen Patch-Stand, und viele Lücken ohne öffentlichen Patch bleiben deshalb unsichtbar.", "Flaws for which the vendor itself lists only a workaround or mitigation. No update helps here, the countermeasure in the notice does. We can only show this where the vendor states it (currently Microsoft). The CISA KEV gives no patch status, so many flaws without a public patch remain invisible here.")));
    var opl = (pr.ohne_patch || []).map(function (k) { return { cve: k.cves[0], wer: k.quelle, was: k.titel, datum: k.datum, aktion: pick("Microsoft nennt nur Umgehung oder Abmilderung.", "Microsoft lists only a workaround or mitigation."), link: k.link }; })
      ;
    if (!opl.length) op.appendChild(el("p", "", pick("Aktuell meldet Microsoft keine ausgenutzte oder kritische Lücke ohne Patch.", "Currently Microsoft reports no exploited or critical flaw without a patch.")));
    else {
      var ul = el("ul", "p-rang");
      opl.forEach(function (k) {
        var li = el("li", "p-r1 p-ohne"), kopf = el("div", "p-rk");
        kopf.appendChild(el("span", "mono p-q", k.wer)); kopf.appendChild(link(k.link, k.cve)); kopf.appendChild(el("span", "mono dim", " · " + datum(k.datum)));
        li.appendChild(kopf); li.appendChild(el("div", "p-t", k.was));
        if (k.aktion) li.appendChild(el("div", "p-w mono dim fine", k.aktion));
        li.setAttribute("data-t", li.textContent.toLowerCase()); ul.appendChild(li);
      });
      op.appendChild(ul);
    }
    box.appendChild(op);
    box.appendChild(el("p", "mono dim fine", pick("Reihenfolge nach festen Regeln: 1. im CISA-KEV, 2. vom Hersteller als ausgenutzt gemeldet, 3. EPSS ab 10 %, 4. vom Hersteller als kritisch eingestuft. Berücksichtigt: Microsoft Patch Day der letzten 30 Tage, Linux-Meldungen und Cisco der letzten 14 Tage (Linux nur mit KEV-Bezug). Stand ", "Order by fixed rules: 1. in the CISA KEV, 2. reported as exploited by the vendor, 3. EPSS from 10%, 4. rated critical by the vendor. Considered: Microsoft patch day of the last 30 days, Linux advisories and Cisco of the last 14 days (Linux only with a KEV link). As of ") + datum(pr.stand) + pick(". Das ist keine Vorhersage und ersetzt keine Prüfung in Ihrem eigenen System.", ". This is no forecast and does not replace a check in your own system.")));
    box.hidden = false;
    werkzeuge(pr);
  }
  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { } }
  function pzKey(k) { return ((k.cves && k.cves[0]) || k.titel) + "|" + k.quelle; }
  function pzLoesung(k) { var t = fixTeile(k.fixe); return t.length ? t.join(", ") : (pick(k.patch_text, k.patch_text_en) || ""); }
  function pzScore(k) { return (k.cvss || []).map(function (c) { return c.score; }).join("/"); }
  function werkzeuge(pr) {
    var host = $("p-werk"); if (!host) return;
    if (!pr || !pr.liste || !pr.liste.length) { host.hidden = true; return; }
    host.hidden = false; host.textContent = "";
    var erledigt = {}; try { erledigt = JSON.parse(lsGet("cl_erledigt") || "{}") || {}; } catch (e) { erledigt = {}; }
    host.appendChild(el("label", "lbl", pick("Betrifft mich? Produkte oder Hersteller, durch Komma getrennt", "Affects me? Products or vendors, separated by commas"))).setAttribute("for", "p-filter");
    var inp = el("input", "filter mono"); inp.id = "p-filter"; inp.type = "search"; inp.autocomplete = "off"; inp.placeholder = pick("z. B. windows 11, outlook, ubuntu, cisco", "e.g. windows 11, outlook, ubuntu, cisco"); inp.value = lsGet("cl_filter") || "";
    host.appendChild(inp);
    var info = el("p", "mono dim fine"); info.setAttribute("aria-live", "polite"); host.appendChild(info);
    var bt = el("div", "p-btns mono"); host.appendChild(bt);
    host.appendChild(el("p", "mono dim fine", pick("Filter und Haken bleiben nur in diesem Browser gespeichert, nichts wird übertragen.", "Filter and ticks are stored only in this browser, nothing is sent.")));
    function lis() { return Array.prototype.slice.call(document.querySelectorAll("#p-zuerst li[data-t]")); }
    function sichtbar() { return lis().filter(function (li) { return !li.hidden && li.hasAttribute("data-i"); }).map(function (li) { return pr.liste[+li.getAttribute("data-i")]; }); }
    function anwenden() {
      var ts = inp.value.toLowerCase().split(",").map(function (x) { return x.trim(); }).filter(Boolean), alle = lis(), n = 0, erl = 0, rest = false;
      alle.forEach(function (li) {
        var treffer = !ts.length || ts.some(function (t) { return li.getAttribute("data-t").indexOf(t) >= 0; });
        li.hidden = !treffer; if (treffer) n++;
        var cb = li.querySelector("input[type=checkbox]");
        if (cb) { var an = !!erledigt[cb.getAttribute("data-k")]; cb.checked = an; li.classList.toggle("p-done", an); if (treffer && an) erl++; }
        if (treffer && ts.length && li.closest(".p-mehr")) rest = true;
      });
      var dt = document.querySelector("#p-zuerst .p-mehr"); if (dt && rest) dt.open = true;
      info.textContent = (ts.length ? pick("Treffer: ", "Matches: ") + n + pick(" von ", " of ") + alle.length + " · " : "") + erl + pick(" erledigt", " done");
      lsSet("cl_filter", inp.value);
    }
    inp.addEventListener("input", anwenden);
    document.getElementById("p-zuerst").addEventListener("change", function (e) {
      var cb = e.target; if (!cb || cb.type !== "checkbox") return;
      var key = cb.getAttribute("data-k"); if (cb.checked) erledigt[key] = new Date().toISOString().slice(0, 10); else delete erledigt[key];
      lsSet("cl_erledigt", JSON.stringify(erledigt)); anwenden();
    });
    function knopf(text, fn) { var b = el("button", "mono", text); b.type = "button"; b.addEventListener("click", function () { var alt = b.textContent; var r = fn(); if (r) { b.textContent = r; setTimeout(function () { b.textContent = alt; }, 1600); } }); bt.appendChild(b); }
    function kopieren(t) {
      if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(t); return; }
      var ta = document.createElement("textarea"); ta.value = t; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); } catch (e) { } document.body.removeChild(ta);
    }
    function laden(name, text, typ) {
      var bl = new Blob([text], { type: typ }), u = URL.createObjectURL(bl), l = document.createElement("a"); l.href = u; l.download = name; document.body.appendChild(l); l.click(); document.body.removeChild(l); setTimeout(function () { URL.revokeObjectURL(u); }, 3000);
    }
    var heute = new Date().toISOString().slice(0, 10);
    knopf(pick("Kurzfassung kopieren", "Copy summary"), function () {
      var z = ["Patch-Lage " + heute + " · cyberlage.org", pick("Diese Woche zuerst:", "This week first:")];
      sichtbar().slice(0, 5).forEach(function (k, i) { z.push((i + 1) + ". " + ((k.cves && k.cves[0]) || "") + " – " + k.titel + " (" + k.quelle + ")" + (pzScore(k) ? " · CVSS " + pzScore(k) : "") + " · " + pick("Lösung: ", "Fix: ") + pzLoesung(k)); });
      z.push("https://cyberlage.org/#patches"); kopieren(z.join("\n")); return pick("kopiert ✓", "copied ✓");
    });
    knopf("CSV", function () {
      var sep = window.I18N.locale.indexOf("de") === 0 ? ";" : ",";
      function q(x) { return '"' + String(x == null ? "" : x).replace(/"/g, '""') + '"'; }
      var zl = [["Rang", "Quelle", "CVE", "Titel", "Betrifft", "CVSS", "EPSS", "Stufe", "Loesung", "Link", "Erledigt"].map(q).join(sep)];
      sichtbar().forEach(function (k) { zl.push([k.rang, k.quelle, (k.cves || []).join(" "), k.titel, k.betrifft, pzScore(k), typeof k.epss === "number" ? Math.round(k.epss * 100) + "%" : "", k.stufe_name, pzLoesung(k), k.link, erledigt[pzKey(k)] || ""].map(q).join(sep)); });
      laden("cyberlage-patches-" + heute + ".csv", "\ufeff" + zl.join("\r\n"), "text/csv;charset=utf-8");
    });
    knopf("Markdown", function () {
      var z = ["# Patch-Lage " + heute + " (cyberlage.org)", ""];
      sichtbar().forEach(function (k) { z.push("- [" + (erledigt[pzKey(k)] ? "x" : " ") + "] **" + ((k.cves && k.cves[0]) || k.titel) + "** " + k.titel + " (" + k.quelle + ")" + (pzScore(k) ? ", CVSS " + pzScore(k) : "") + " – " + pick("Lösung: ", "Fix: ") + pzLoesung(k) + " – " + k.link); });
      laden("cyberlage-patches-" + heute + ".md", z.join("\n") + "\n", "text/markdown;charset=utf-8");
    });
    knopf(pick("Drucken", "Print"), function () { window.print(); });
    knopf(pick("Haken zurücksetzen", "Reset ticks"), function () { erledigt = {}; lsSet("cl_erledigt", "{}"); anwenden(); return pick("zurückgesetzt", "reset"); });
    anwenden();
  }
  function zeigeEdge(m) {
    var box = $("p-edge"); if (!box) return;
    var c = m.chromium || { anzahl: m.davon_chromium_ausgenommen };
    if (!c.anzahl) { box.hidden = true; return; }
    box.textContent = "";
    box.appendChild(el("h3", "mono rd-t", pick("Edge und Chrome (Chromium)", "Edge and Chrome (Chromium)")));
    box.appendChild(el("p", "", pick(zahl(c.anzahl) + " Chromium-Lücken im " + monatName(m.id) + ". Sie kommen laufend mit den Browser-Updates, nicht nur am Patch Day, und stehen deshalb nicht in der Zahl oben.", zahl(c.anzahl) + " Chromium flaws in " + monatName(m.id) + ". They arrive continuously with browser updates, not only on patch day, and are therefore not in the figure above.")));
    if (c.edge || c.chrome) {
      var fx = el("div", "p-fix"); fx.appendChild(el("b", "mono", pick("Lösung: ", "Fix: ")));
      fx.appendChild(document.createTextNode((c.edge ? pick("Edge mindestens Version ", "Edge at least version ") + c.edge : "") + (c.edge && c.chrome ? " · " : "") + (c.chrome ? pick("Chrome mindestens Version ", "Chrome at least version ") + c.chrome : "") + pick(", Browser danach neu starten.", ", then restart the browser.")));
      box.appendChild(fx);
    }
    if (c.kev && c.kev.length) {
      var ex = el("p", "mono fine", pick("Davon als ausgenutzt gemeldet: ", "Reported as exploited: "));
      c.kev.forEach(function (x, i) { if (i) ex.appendChild(document.createTextNode(", ")); ex.appendChild(link("https://msrc.microsoft.com/update-guide/vulnerability/" + x.cve, x.cve)); });
      box.appendChild(ex);
    } else if (c.edge || c.chrome) box.appendChild(el("p", "mono dim fine", pick("Keine davon als ausgenutzt gemeldet.", "None of them reported as exploited.")));
    var q = el("p", "mono dim fine", pick("Quellen: Microsoft (Edge-Fixversion je CVE), Titel der Chromium-Meldungen (Chrome-Version). Mehr: ", "Sources: Microsoft (Edge fix version per CVE), titles of the Chromium notices (Chrome version). More: "));
    q.appendChild(link("https://learn.microsoft.com/deployedge/microsoft-edge-relnotes-security", pick("Edge-Sicherheitsupdates", "Edge security updates"))); q.appendChild(document.createTextNode(" · ")); q.appendChild(link("https://chromereleases.googleblog.com/", "Chrome Releases"));
    box.appendChild(q); box.hidden = false;
  }
  function zeigeMicrosoft(ms) {
    var box = $("p-ms"); if (!box) return;
    var monate = ms && ms.monate ? Object.keys(ms.monate).map(function (k) { return ms.monate[k]; }) : [];
    if (!monate.length) { box.hidden = true; return; }
    monate.sort(function (a, c) { return String(a.erste_veroeffentlichung).localeCompare(String(c.erste_veroeffentlichung)); });
    var m = monate[monate.length - 1], b = m.bewertung || {};
    box.textContent = "";
    var kopf = el("h3", "mono rd-t", pick("Microsoft Patch Day · ", "Microsoft patch day · ") + monatName(m.id)); box.appendChild(kopf);
    var sub = el("p", "mono dim fine", pick("veröffentlicht ", "released ") + datum(String(m.erste_veroeffentlichung).slice(0, 10)) + pick(" · Stand der Daten ", " · data as of ") + datum(m.aktuell) + pick(" · abgerufen ", " · retrieved ") + datum(ms.meta && ms.meta.abgerufen_am) + pick(" · Quelle: ", " · source: "));
    sub.appendChild(link((ms.meta && ms.meta.quelle_url) || "https://msrc.microsoft.com/update-guide", "Microsoft Security Response Center")); box.appendChild(sub);
    var dr = { dringend: ["pr-rot", pick("dringend", "urgent")], zeitnah: ["pr-gelb", pick("zeitnah", "prompt")], normal: ["pr-gruen", pick("normal", "normal")] }[b.dringlichkeit] || ["", ""];
    var bw = el("div", "p-bew"); bw.appendChild(el("span", "p-badge " + dr[0], dr[1]));
    bw.appendChild(el("span", "", pick(b.groesse, b.groesse_en) + (b.verhaeltnis_median ? " · " + pick("das ", "") + b.verhaeltnis_median.toLocaleString(window.I18N.locale) + pick("-Fache des Medians der Vormonate (", "x the median of earlier months (") + zahl(b.median_vormonate) + ")" : "")));
    box.appendChild(bw);
    var g = el("div", "p-kpis");
    g.appendChild(kpi(zahl(m.cves), "CVEs")); g.appendChild(kpi(zahl(m.schwere.Critical), pick("kritisch", "critical")));
    g.appendChild(kpi(zahl(m.ausgenutzt), pick("ausgenutzt", "exploited"), m.ausgenutzt > 0 ? "warn" : ""));
    g.appendChild(kpi(zahl(m.oeffentlich_bekannt), pick("öffentlich bekannt", "publicly disclosed")));
    g.appendChild(kpi(zahl(m.im_kev), pick("davon im KEV", "of them in KEV"), m.im_kev > 0 ? "warn" : ""));
    box.appendChild(g);
    var emp = el("p", "p-emp"); emp.appendChild(el("b", "mono p-emp-k", pick("Empfehlung", "Recommendation"))); emp.appendChild(document.createTextNode(pick(b.empfehlung, b.empfehlung_en))); box.appendChild(emp);
    if (b.aktionen && b.aktionen.length) {
      var al = el("ol", "p-akt");
      b.aktionen.forEach(function (x) {
        var li = el("li", ""); li.appendChild(link("https://msrc.microsoft.com/update-guide/vulnerability/" + x.cve, x.cve));
        li.appendChild(document.createTextNode(" · " + x.titel + (x.betrifft ? " · " + pick("betrifft ", "affects ") + x.betrifft : "")));
        var ft = fixTeile(x.fixe);
        var d = el("div", "p-fix"); d.appendChild(el("b", "mono", pick("Lösung: ", "Fix: ")));
        d.appendChild(document.createTextNode(ft.length ? ft.join(", ") : (x.patch === "nein" ? pick("noch kein Patch, nur Umgehung oder Abmilderung (Microsoft-Seite)", "no patch yet, only a workaround or mitigation (Microsoft page)") : pick("Details auf der Microsoft-Seite", "details on the Microsoft page"))));
        if (ft.some(function (z) { return /Version|version/.test(z); })) { d.appendChild(document.createTextNode(" · ")); d.appendChild(link("https://aka.ms/OfficeSecurityReleases", pick("Office-Release-Notes", "Office release notes"))); }
        li.appendChild(d); al.appendChild(li);
      });
      box.appendChild(al);
    }
    if (m.ausgenutzt_cves && m.ausgenutzt_cves.length) {
      var ex = el("p", "mono fine", pick("Ausgenutzt: ", "Exploited: "));
      m.ausgenutzt_cves.forEach(function (c, i) { if (i) ex.appendChild(document.createTextNode(", ")); ex.appendChild(link("https://msrc.microsoft.com/update-guide/vulnerability/" + c, c)); });
      box.appendChild(ex);
    }
    if (m.nachtraege && m.nachtraege.length) {
      var n = el("p", "mono fine", pick("Nachträge (Out-of-Band): ", "Later additions (out of band): ") + m.nachtraege.map(function (x) { return datum(x.am) + ": " + x.neue_cves + pick(" neue Lücken", " new flaws") + (x.ausgenutzt_neu ? " (" + x.ausgenutzt_neu + pick(" ausgenutzt", " exploited") + ")" : ""); }).join("; "));
      box.appendChild(n);
    }
    var det = el("details", "p-det"); det.appendChild(el("summary", "mono", pick("Zahlen, Produkte und Verlauf", "Figures, products and history")));
    var kv = el("div", "p-cols");
    var fam = el("div", ""); fam.appendChild(el("h4", "mono", pick("Betroffene Produkte (Anzahl CVEs)", "Affected products (CVE count)")));
    Object.keys(m.familien || {}).slice(0, 6).forEach(function (k) { fam.appendChild(el("div", "p-z mono", k + ": " + m.familien[k])); });
    var au = el("div", ""); au.appendChild(el("h4", "mono", pick("Art der Auswirkung", "Impact type")));
    Object.keys(m.auswirkung || {}).slice(0, 6).forEach(function (k) { au.appendChild(el("div", "p-z mono", k + ": " + m.auswirkung[k])); });
    kv.appendChild(fam); kv.appendChild(au); det.appendChild(kv);
    det.appendChild(el("p", "mono dim fine", pick("Nicht mitgezählt: ", "Not counted: ") + zahl(m.davon_azure_linux_ausgenommen) + pick(" Paketlücken von Azure Linux (Linux-Pakete in Microsofts Cloud-Distribution, kein Windows und kein Office) und die Chromium-Lücken für Edge, siehe Block unten. Schweregrad, Ausnutzung und Bekanntheit stammen von Microsoft.", " package flaws of Azure Linux (Linux packages in Microsoft's cloud distribution, not Windows or Office) and the Chromium flaws for Edge, see the block below. Severity, exploitation and disclosure come from Microsoft.")));
    zeigeEdge(m);
    zeichneMonate(det, monate);
    det.appendChild(el("p", "mono dim fine", pick("CVEs je Patch Day, letzte ", "CVEs per patch day, last ") + monate.length + pick(" Monate. Gelb: mindestens eine ausgenutzte Lücke.", " months. Yellow: at least one exploited flaw.")));
    box.appendChild(det);
    box.hidden = false;
  }
  function zeigeHersteller(hs) {
    var box = $("p-hs"); if (!box) return;
    var qs = hs && hs.quellen ? Object.keys(hs.quellen).map(function (k) { return hs.quellen[k]; }) : [];
    if (!qs.length) { box.hidden = true; return; }
    box.textContent = "";
    box.appendChild(el("h3", "mono rd-t", pick("Linux-Distributionen und Hersteller", "Linux distributions and vendors")));
    var tw = el("div", "tabelle"); tw.setAttribute("role", "region"); tw.tabIndex = 0;
    var t = el("table", ""); var th = el("tr", "");
    [pick("Quelle", "Source"), pick("neu 7 Tage", "new 7 days"), pick("neu 30 Tage", "new 30 days"), pick("davon kritisch", "of them critical"), pick("CVEs 30 Tage", "CVEs 30 days"), pick("Stand", "as of")].forEach(function (h) { th.appendChild(el("th", "", h)); });
    t.appendChild(el("thead", "")).appendChild(th);
    var tb = el("tbody", ""); t.appendChild(tb);
    qs.forEach(function (q) {
      var tr = el("tr", ""); tb.appendChild(tr);
      var c0 = el("td", ""); c0.appendChild(link(q.url, q.name)); tr.appendChild(c0);
      if (q.status !== "ok" || typeof q.neu_30 !== "number") {
        var c = el("td", "mono dim", pick("keine Daten (Quelle nicht erreichbar)", "no data (source unreachable)")); c.colSpan = 5; tr.appendChild(c); return;
      }
      [zahl(q.neu_7), zahl(q.neu_30), q.schwere_bekannt ? zahl(q.kritisch_30) : "–", zahl(q.cves_30), datum(q.abgerufen_am)].forEach(function (x) { tr.appendChild(el("td", "mono", x)); });
    });
    tw.appendChild(t); box.appendChild(tw);
    qs.forEach(function (q) {
      if (!q.letzte || !q.letzte.length) return;
      var d = el("details", "rd-det"); d.appendChild(el("summary", "mono", q.name + pick(": letzte Meldungen", ": latest advisories")));
      var ul = el("ul", "p-liste");
      q.letzte.slice(0, 6).forEach(function (x) {
        var li = el("li", ""); li.appendChild(el("span", "mono dim", datum(x.datum) + " ")); li.appendChild(link(x.link, x.titel + (x.schwere ? " (" + x.schwere + ")" : ""))); ul.appendChild(li);
      });
      d.appendChild(ul); box.appendChild(d);
    });
    var ad = el("p", "mono dim fine", pick("Adobe: keine maschinenlesbare Quelle ohne Konto, daher nur Verweis auf die ", "Adobe: no machine-readable source without an account, so a link only to the "));
    ad.appendChild(link("https://www.adobe.com/trust/security/bulletins-and-advisories.html", pick("Adobe-Sicherheitshinweise", "Adobe security bulletins")));
    ad.appendChild(document.createTextNode(pick(" (Patch Day: zweiter Dienstag, siehe Patch-Kalender). SAP-Hinweise erreichen Sie nur mit SAP-for-Me-Konto, hier steht die Nummer.", " (patch day: second Tuesday, see patch calendar). SAP notes need an SAP for Me account, only the number is shown here.")));
    box.appendChild(ad);
    box.appendChild(el("p", "mono dim fine", pick("Nur Zählung und Verweise auf die Meldungen der Hersteller, keine Texte. Schweregrade stammen von den Herstellern und fehlen, wo sie nicht geliefert werden (zum Beispiel bei Ubuntu und Debian).", "Counts and links to the vendors' advisories only, no texts. Severity comes from the vendors and is missing where they do not provide it (for example Ubuntu and Debian).")));
    box.hidden = false;
  }

  function zeigeBalken(sc, box) {
    var bs = [];
    sc.modell_gruppen.forEach(function (g) { g.bausteine.forEach(function (b) { if (typeof b.ausschlag === "number") bs.push(b); }); });
    if (!bs.length) return;
    var NS = "http://www.w3.org/2000/svg", W = 540, bo = sc.beobachtung || [], H = 36 + (bs.length + bo.length) * 34, X0 = 150, X1 = 500, max = 2;
    var svg = document.createElementNS(NS, "svg"); svg.setAttribute("viewBox", "0 0 " + W + " " + H); svg.setAttribute("width", "100%"); svg.setAttribute("role", "img");
    var mk = function (tag, a, t) { var e = document.createElementNS(NS, tag); for (var k in a) e.setAttribute(k, a[k]); if (t !== undefined) e.textContent = t; svg.appendChild(e); return e; };
    var mono = { "font-family": "ui-monospace,Menlo,Consolas,monospace", "font-size": "11", fill: "#9aa7b4" };
    var xs = function (v) { return X0 + (Math.min(v, max) / max) * (X1 - X0); };
    mk("title", {}, pick("Bausteine als Balken, Schwelle bei 1,0", "Components as bars, threshold at 1.0"));
    bs.forEach(function (b, i) {
      var y = 20 + i * 34, over = b.ausschlag >= 1;
      mk("text", Object.assign({ x: X0 - 8, y: y + 14, "text-anchor": "end" }, mono), pick(b.name, b.name_en));
      mk("rect", { x: X0, y: y, width: X1 - X0, height: 20, fill: "#1a222b" });
      mk("rect", { x: X0, y: y, width: xs(b.ausschlag) - X0, height: 20, fill: over ? "#e3b341" : "#4fa57a" });
      mk("text", Object.assign({ x: Math.min(xs(b.ausschlag) + 6, X1 - 30), y: y + 14 }, mono, { fill: "#e6edf3" }), b.ausschlag.toLocaleString(window.I18N.locale, { minimumFractionDigits: 1, maximumFractionDigits: 2 }));
    });
    bo.forEach(function (b, i) {
      var y = 20 + (bs.length + i) * 34, n = pick(b.name, b.name_en).split(":")[0];
      mk("text", Object.assign({ x: X0 - 8, y: y + 14, "text-anchor": "end" }, mono, { fill: "#6b7785" }), n);
      mk("rect", { x: X0, y: y, width: X1 - X0, height: 20, fill: "none", stroke: "#2a343f", "stroke-dasharray": "3 3" });
      mk("text", Object.assign({ x: X0 + 8, y: y + 14 }, mono, { fill: "#6b7785" }), pick("Beobachtung · Rohwert ", "observation · raw value ") + (b.wert === null || b.wert === undefined ? "–" : zahl(b.wert)) + pick(" · noch ohne Schwelle", " · no threshold yet"));
    });
    mk("line", { x1: xs(1), x2: xs(1), y1: 10, y2: 20 + bs.length * 34 - 8, stroke: "#e6edf3", "stroke-width": "1.5", "stroke-dasharray": "4 3" });
    mk("text", Object.assign({ x: xs(1), y: H - 4, "text-anchor": "middle" }, mono), pick("Schwelle 1,0", "threshold 1.0"));
    box.appendChild(el("h4", "mono rd-t", pick("Bausteine im Vergleich", "Components compared")));
    box.appendChild(svg);
    box.appendChild(el("p", "mono dim fine", bo.length ? pick(bs.length + " Bausteine zählen im Pegel, " + bo.length + " weitere werden beobachtet und zählen erst mit eigener Schwelle.", bs.length + " components count in the gauge, " + bo.length + " more are observed and count only once they have a threshold.") : pick("Alle " + bs.length + " Bausteine zählen im Pegel. Gelb: an oder über der Schwelle.", "All " + bs.length + " components count in the gauge. Yellow: at or above threshold.")));
  }

  function zeigeModell(sc) {
    var box = $("rd-modell"); if (!box) return; box.textContent = "";
    if (!sc || !sc.modell_gruppen) return;
    zeigeBalken(sc, box);
    box.appendChild(el("h4", "mono rd-t", pick("Aufbau · Modell ", "Structure · model ") + (sc.modell || "")));
    var ul = el("ul", "p-liste");
    sc.modell_gruppen.forEach(function (g) {
      if (!g.bausteine.length) return;
      var li = el("li", ""); li.appendChild(el("b", "mono", pick(g.name, g.name_en) + ": "));
      li.appendChild(document.createTextNode(g.bausteine.map(function (b) { return pick(b.name, b.name_en) + (typeof b.ausschlag === "number" ? " " + b.ausschlag.toLocaleString(window.I18N.locale, { maximumFractionDigits: 2 }) : " –"); }).join(" · ")));
      ul.appendChild(li);
    });
    box.appendChild(ul);
    box.appendChild(el("p", "mono dim fine", pick("Je Gruppe wird gemittelt, dann über die Gruppen. So wiegt ein Thema nicht doppelt, nur weil mehrere Bausteine dazu messen.", "Averaged within each group, then across groups, so one topic does not weigh double just because several components measure it.")));
    if (sc.beobachtung && sc.beobachtung.length) {
      var d = el("details", "rd-det"); d.appendChild(el("summary", "mono", pick("In Beobachtung (zählt noch nicht): " + sc.beobachtung.length, "Under observation (does not count yet): " + sc.beobachtung.length)));
      var u2 = el("ul", "p-liste");
      sc.beobachtung.forEach(function (b) {
        u2.appendChild(el("li", "", pick(b.name, b.name_en) + ": " + (b.wert === null || b.wert === undefined ? "–" : zahl(b.wert)) + " · " + pick("Historie: ", "history: ") + b.historie));
      });
      d.appendChild(u2);
      d.appendChild(el("p", "mono dim fine", pick("Diese Bausteine werden täglich gespeichert. Nach etwa 90 Tagen entscheiden wir, ob sie mit eigener Schwelle in das Modell aufgenommen werden (neue Version, Verlauf wird rückwirkend neu gerechnet, soweit Historie da ist).", "These components are stored daily. After about 90 days we decide whether to add them with their own threshold to the model (new version, history recomputed where data exists).")));
      box.appendChild(d);
    }
  }

  function zeigeKonsens(r) {
    var k = r && r.konsens, box = $("rd-signale"); box.textContent = "";
    if (!k || !k.bewertet) { $("rd-kon").textContent = txt("keine"); return; }
    var satz = pick(k.erhoeht + " von " + k.bewertet + (k.bewertet === 1 ? " externem Signal liegt" : " externen Signalen liegen") + " an oder über der Schwelle.", k.erhoeht + " of " + k.bewertet + " external " + (k.bewertet === 1 ? "signal is" : "signals are") + " at or above the threshold.");
    $("rd-kon").textContent = satz + " " + pick("Stand ", "As of ") + datum(r.abgerufen_am) + ".";
    var sc = k.score, sb = $("rd-score"); sb.textContent = "";
    var ampel = (sc.stufe && sc.stufe.ampel) || "", rb = $("radar"), fzb = $("fazit");
    ["ruhig", "unauffaellig", "angespannt", "hoch", "ausserordentlich"].forEach(function (a) { [sb, rb, fzb].forEach(function (n) { if (n) n.classList.remove("ra-" + a); }); });
    if (ampel) [sb, rb, fzb].forEach(function (n) { if (n) n.classList.add("ra-" + ampel); });
    if (sc) {
      var gr = el("div", "sw mono", String(sc.wert)); gr.appendChild(el("small", "", " / 100")); sb.appendChild(gr);
      var tx = el("div", "st");
      tx.appendChild(el("b", "mono", pick("Dreier-Pegel · Gesamtscore", "Dreier Gauge · overall score")));
      tx.appendChild(el("span", "", pick(
        "Aus " + sc.signale + " von " + sc.von + " Bausteinen, je Gruppe gemittelt. 50 heißt: die Regelschwellen sind im Schnitt erreicht, 100: im Schnitt doppelt so weit. Kein objektives Maß, die Grenzen sind vorläufig.",
        "From " + sc.signale + " of " + sc.von + " components, averaged per group. 50 means the rule thresholds are reached on average, 100 twice as far. Not an objective measure, the limits are provisional.")));
      tx.appendChild(el("span", "mono dim", pick("Stand: ", "as of: ") + datum(r.abgerufen_am)));
      sb.appendChild(tx); sb.hidden = false;
      var sbg = $("stufe-begr"); if (sbg) sbg.hidden = true;
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
        sk.appendChild(el("p", "mono dim fine", pick("Stufen: ruhig, unauffällig, angespannt, hoch, außergewöhnlich. Grenzen vorläufig.", "Levels: calm, unremarkable, tense, high, exceptional. Limits provisional.")));
        sk.hidden = false;
      }
    }
    zeigeModell(k.score);
    zeichneScope(k.signale || []);
    (k.signale || []).forEach(function (s) {
      var b = el("div", "sg"), st = s.erhoeht === true ? ["●", "an"] : (s.erhoeht === false ? ["○", "aus"] : ["–", "kn"]);
      b.appendChild(el("span", "p mono " + st[1], st[0]));
      b.appendChild(el("span", "n", pick(s.name, s.name_en) + (s.art === "eigen" ? pick(" (eigen)", " (own)") : "") + " · " + (s.erhoeht === true ? pick("an oder über der Schwelle", "at or above threshold") : (s.erhoeht === false ? pick("unter der Schwelle", "below threshold") : pick("noch keine Aussage", "no rating yet")))));
b.appendChild(el("span", "g", typeof s.ausschlag === "number" ? pick("Messwert: das ", "reading: ") + s.ausschlag.toLocaleString(window.I18N.locale, { minimumFractionDigits: 1, maximumFractionDigits: 2 }) + pick("-Fache der Schwelle", "x the threshold") : pick("noch kein Messwert", "no reading yet")));
      box.appendChild(b);
    });
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
      : pick("Wir speichern jede Prognose (EPSS ab " + Math.round((t.schwelle || 0.1) * 100) + " %) und prüfen später, ob die Lücke im KEV landet. Bisher gespeichert: " + (t.prognosen || 0) + ", davon eingetreten: " + (t.eingetreten || 0) + ". Die erste Quote erscheint " + (t.reif_nach_tagen || 30) + " Tage nach dem ersten gespeicherten Wert, vorher wäre sie nicht belastbar.",
             "We store every forecast (EPSS from " + Math.round((t.schwelle || 0.1) * 100) + " %) and check later whether the vulnerability lands in KEV. Stored so far: " + (t.prognosen || 0) + ", occurred: " + (t.eingetreten || 0) + ". The first rate appears " + (t.reif_nach_tagen || 30) + " days after the first stored value; earlier it would not be reliable.");
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
    ((r.konsens && r.konsens.signale) || []).forEach(function (x) {
      if (!x.baustein || typeof x.wert !== "number") return;
      kachel({ gr: "score", nat: "mess", quelle: "extern", sig: x.name_en, name: x.name, wert: zahl(x.wert), einheit: pick(" · Schwelle ", " · threshold ") + zahl(x.schwelle), misst: pick(x.misst, x.misst_en) + (x.daten_seit ? pick(", Archiv seit ", ", archive since ") + datum(x.daten_seit) : ""), stand: tg + datum(r.abgerufen_am) });
    });
    var jz = z.jetzt || {}, v12 = z.vor_12_monaten || {};
    if (typeof jz.median_frisch === "number") kachel({ gr: "score", nat: "mess", quelle: "eigen", sig: "Dreier Pace", name: pick("Dreier-Tempo", "Dreier Pace"), wert: tage(jz.median_frisch), einheit: pick(" Tage Median", " days median"), misst: pick("Veröffentlichung bis KEV-Aufnahme, vor 12 Monaten: ", "publication to KEV listing, 12 months ago: ") + tage(v12.median_frisch) + pick(" Tage", " days"), stand: pick("Quelle CISA KEV · abgerufen ", "source CISA KEV · retrieved ") + datum(((d.quellen || []).filter(function (x) { return x.id === "cisa-kev"; })[0] || {}).abgerufen_am || d.stand) });
    (r.einschaetzungen || []).forEach(function (q) {
      var pfeil = q.richtung === "steigend" ? " ↑" : (q.richtung === "fallend" ? " ↓" : ""), idx = q.wert && q.basis;
      if (!idx) return; // Lagebericht-Urteil steht schon bei den Gründen
      kachel({ gr: idx ? "score" : "ktx", nat: "eins", quelle: "extern", sig: idx ? "BSI Cyber Index" : null, name: q.name, url: q.link, wert: idx ? String(Math.round(q.wert / q.basis * 100)) : pick(q.urteil, q.urteil_en) + pfeil, einheit: idx ? pick(" % von 2024", " % of 2024") : "", misst: pick(q.misst, q.misst_en), stand: pick("Bericht vom ", "report of ") + datum(q.stand) + pick(" · von Hand geprüft ", " · checked by hand ") + datum(q.geprueft_am) + pick(" · jährlich", " · yearly") + (q.vorher ? pick(" · Vorjahr: ", " · year before: ") + pick(q.vorher, q.vorher_en) : "") });
    });
    if (r.sans) {
      var sn = { green: ["ruhig (grün)", "calm (green)"], yellow: ["erhöht (gelb)", "raised (yellow)"], orange: ["hoch (orange)", "high (orange)"], red: ["kritisch (rot)", "critical (red)"] }[r.sans.status] || ["–", "–"];
      kachel({ gr: "score", nat: "eins", quelle: "extern", sig: "SANS Infocon", name: "SANS Infocon", url: "https://isc.sans.edu/", wert: pick(sn[0], sn[1]), misst: pick("Scans und Ausbrüche im Netz", "scans and outbreaks across the internet"), stand: tg + datum(r.sans.abgerufen_am) + " · live" });
    }
    if (typeof t.prognosen === "number") kachel({ gr: "ktx", nat: "mess", quelle: "eigen", name: pick("Trefferquote Prognose", "Forecast hit rate"), wert: typeof t.quote_reif === "number" ? proz(t.quote_reif) : "–", misst: pick("Prognosen: ", "forecasts: ") + t.prognosen + pick(", eingetreten: ", ", occurred: ") + t.eingetreten, stand: (typeof t.quote_reif === "number" ? "" : pick("erste Quote nach 30 Tagen · ", "first rate after 30 days · ")) + pick("eigener Abgleich EPSS gegen KEV · Stand ", "own comparison EPSS vs KEV · as of ") + datum(r.abgerufen_am) });
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
      var t = el("span", "titel"); t.appendChild(link(e.link, e.cve));
      if (e.produkt) t.appendChild(el("span", "mono dim", " · " + e.produkt));
      if (e.beschreibung) t.appendChild(el("div", "ab-b dim", e.beschreibung));
      r.appendChild(t);
      return r;
    }), 10);
  }
})();
