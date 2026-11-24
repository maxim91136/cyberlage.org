(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var txt = function () { return window.I18N.t.apply(null, arguments); };
  var pick = function (de, en) { return window.I18N.pick(de, en); };
  var zahl = function (n) { return typeof n === "number" ? n.toLocaleString(window.I18N.locale) : txt("keine"); };
  var datum = function (iso) {
    if (!iso) return txt("keine");
    var d = new Date(iso);
    return isNaN(d) ? txt("keine") : d.toLocaleDateString(window.I18N.locale, { timeZone: "UTC", day: "2-digit", month: "2-digit", year: "numeric" });
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
    $("stand").textContent = datum(d.stand);

    var hatStufe = d.stufe !== null && d.stufe !== undefined;
    var name = hatStufe ? txt(String(d.stufe)) : null;
    $("stufe-wert").textContent = hatStufe ? name : "null";
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

    var s = $("sektor");
    (d.sektor || []).forEach(function (z) {
      var box = el("div", "panel sektor");
      box.appendChild(el("div", "zahl mono", String(z.wert).replace(".", ",") + " %"));
      var t = el("div", "txt");
      t.appendChild(el("div", "", txt("sektor_txt", z.berichtsjahr)));
      var m = el("div", "mono dim fine");
      m.appendChild(document.createTextNode(txt("sektor_meta", z.geltungsbereich, z.geltungsbereich === "EU", z.quelle, z.seite, z.lizenz)));
      if (/^https:\/\//.test(z.link || "")) {
        var a = el("a", "", txt("quelle"));
        a.href = z.link; a.rel = "noopener"; m.appendChild(a);
      }
      t.appendChild(m); box.appendChild(t); s.appendChild(box);
    });

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
    var tl = d.telegram && d.telegram.link;
    if (/^https:\/\/t\.me\//.test(tl || "")) { $("telegram-link").href = tl; $("telegram").hidden = false; }
    d_stand = d.stand;
    zeigeBsi(d.cert_bund);
    zeigeEu(d.eu_kev);
    zeigeAusblick(d.ausblick);
    zeigeRadar(d.radar, d);

    var h = $("hinweise");
    var hw = window.I18N.lang === "en" && d.hinweise_en ? d.hinweise_en : (d.hinweise || []);
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
    Array.prototype.forEach.call(document.querySelectorAll(".dd-box a"), function (a) {
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
  var d_stand = null;
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

  function zeigeRadar(r, d) {
    var proz = function (x) { return typeof x === "number" ? Math.round(x * 100) + " %" : "–"; };
    var tage = function (x) { return typeof x === "number" ? x.toLocaleString(window.I18N.locale, { maximumFractionDigits: 1 }) : "–"; };
    if (!r) { ["rd-zahlen", "rd-treffer", "rd-eu", "rd-vergleich", "rd-gruende"].forEach(function (id) { $(id).textContent = txt("keine"); }); return; }
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
    var vg = $("rd-vergleich"); vg.textContent = "";
    var zeile = function (name, url, urteil, misst, stand) {
      var b = el("div", "vg");
      var n = el("div", "n"); n.appendChild(url ? link(url, name) : document.createTextNode(name)); b.appendChild(n);
      b.appendChild(el("div", "mono", urteil)); b.appendChild(el("div", "m", misst)); b.appendChild(el("div", "s", stand)); vg.appendChild(b);
    };
    zeile("Cyberlage", null, (d.stufe ? txt(d.stufe) : txt("keine")), pick("zählt neu ausgenutzte Lücken im CISA-KEV (30 Tage)", "counts newly exploited vulnerabilities in CISA KEV (30 days)"), pick("Stand ", "as of ") + datum(d.stand) + pick(" · täglich", " · daily"));
    (r.einschaetzungen || []).forEach(function (q) {
      var pfeil = q.richtung === "steigend" ? " ↑" : (q.richtung === "fallend" ? " ↓" : "");
      zeile(q.name, q.link, pick(q.urteil, q.urteil_en) + pfeil, pick(q.misst, q.misst_en),
        pick("Stand ", "as of ") + datum(q.stand) + pick(" · jährlich", " · yearly") + (q.vorher ? pick(" · Vorjahr: ", " · year before: ") + pick(q.vorher, q.vorher_en) : ""));
    });
    if (r.sans) {
      var sn = { green: ["ruhig (grün)", "calm (green)"], yellow: ["erhöht (gelb)", "raised (yellow)"], orange: ["hoch (orange)", "high (orange)"], red: ["kritisch (rot)", "critical (red)"] }[r.sans.status];
      zeile("SANS Internet Storm Center", "https://isc.sans.edu/", pick(sn[0], sn[1]), pick("beobachtet Scans und Ausbrüche im Netz, ein anderer Blickwinkel", "watches scans and outbreaks across the internet, a different angle"), pick("Stand ", "as of ") + datum(r.sans.abgerufen_am) + pick(" · live", " · live"));
    }
    var ul = $("rd-gruende"); ul.textContent = "";
    (r.gruende || []).forEach(function (g) {
      var li = el("li", "", pick(g.aussage, g.aussage_en) + " ");
      li.appendChild(link(g.link, "[" + g.quelle + "]")); ul.appendChild(li);
    });
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
