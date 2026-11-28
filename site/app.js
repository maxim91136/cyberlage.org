(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var txt = function () { return window.I18N.t.apply(null, arguments); };
  var pick = function (de, en) { var r = window.I18N.pick(de, en); return typeof dx === "function" ? dx(r) : r; };
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

  /* Gemeinsame Helfer für die ausgelagerten Teile (termine.js, radar.js, tabellen.js); sie lesen sie erst beim Aufruf. */
  window.CL = Object.assign(window.CL || {}, { "$": $, txt: txt, pick: pick, zahl: zahl, datum: datum, el: el, link: link, liste: liste,
    zeichneScope: zeichneScope, zeigeModell: zeigeModell, skala: function () { return d_skala; } });
  var TAG_MS = 86400000;
  var termine = window.CL.termine, inTagen = window.CL.inTagen, zeigeTermine = window.CL.zeigeTermine;
  var zeigeKonsens = window.CL.zeigeKonsens, zeigeRadar = window.CL.zeigeRadar, zeichneRadar = window.CL.zeichneRadar, zeigeAusblick = window.CL.zeigeAusblick;

  /* Immer nur ein Teil und innerhalb eines Teils nur ein Abschnitt offen: so bleibt die Seite kurz und man verliert nicht den Faden. */
  function exklusiv(d) {
    if (!d || !d.open || !d.classList) return;
    var gruppe = [];
    if (d.classList.contains("teil")) gruppe = Array.prototype.slice.call(document.querySelectorAll("main > details.teil"));
    else if (d.classList.contains("sek") && d.parentElement && d.parentElement.tagName === "SECTION") {
      var t = d.closest("details.teil"); if (t) gruppe = Array.prototype.slice.call(t.querySelectorAll(":scope > section > details.sek"));
    }
    gruppe.forEach(function (x) { if (x !== d) x.open = false; });
  }
  function aufklappen(el0) {
    if (!el0) return;
    for (var n = el0; n; n = n.parentElement) if (n.tagName === "DETAILS") { n.open = true; exklusiv(n); }
    var d = el0.querySelector && el0.querySelector(":scope > details.sek"); if (d) { d.open = true; exklusiv(d); }
  }
  var geklickt = null;
  document.addEventListener("click", function (e) { var sm = e.target.closest && e.target.closest("summary"); geklickt = sm && sm.parentElement && sm.parentElement.tagName === "DETAILS" ? sm.parentElement : null; }, true);
  /* Sprung zum Ziel; lädt der Inhalt erst danach nach, wird einmal nachgesprungen, falls das Ziel noch zu weit unten steht. */
  function springe(z) {
    z.scrollIntoView(); ohneZiel();
    [200, 450, 900].forEach(function (ms) { setTimeout(function () { var r = z.getBoundingClientRect(); if (r.top > 150 && r.height > 0) z.scrollIntoView(); }, ms); });
  }
  function ohneZiel() { try { history.replaceState(null, "", location.pathname + location.search); } catch (e) { /* ältere Browser */ } }
  function oeffne() {
    var id = (location.hash || "").slice(1), z = id && document.getElementById(id); if (!z) return;
    aufklappen(z); setTimeout(function () { springe(z); }, 60);
  }
  var vorDruck = [];
  window.addEventListener("beforeprint", function () { vorDruck = Array.prototype.filter.call(document.querySelectorAll("details"), function (d) { return !d.open; }); vorDruck.forEach(function (d) { d.open = true; }); });
  window.addEventListener("afterprint", function () { vorDruck.forEach(function (d) { d.open = false; }); vorDruck = []; });
  window.addEventListener("hashchange", oeffne);
  document.addEventListener("click", function (e) {
    var l = e.target.closest && e.target.closest("a[href^='#']"); if (!l) return;
    var ziel = document.getElementById(l.getAttribute("href").slice(1)); aufklappen(ziel);
    var off = l.getAttribute("data-offen"), od = off && document.getElementById(off);
    if (od) { aufklappen(od); od.open = true; setTimeout(function () { od.scrollIntoView(); ohneZiel(); }, 60); return; }
    if (l.closest && l.closest(".dd-box")) return;
    if (ziel && ziel.scrollIntoView) setTimeout(function () { springe(ziel); }, 60);
  });
  // Klappen: jeder Besuch beginnt zugeklappt; beim Öffnen die Grafiken in der richtigen Breite neu zeichnen
  try { localStorage.removeItem("klappen"); } catch (e) { /* egal */ }
  document.addEventListener("toggle", function (e) {
    var d = e.target; if (!d || d.tagName !== "DETAILS") return;
    if (d.open && geklickt === d) {  // vom Besucher geöffnet: Geschwister zuklappen und die Überschrift nach oben holen
      geklickt = null; exklusiv(d);
      var sm = d.querySelector(":scope > summary"); if (sm && (d.classList.contains("teil") || d.classList.contains("sek")) && sm.scrollIntoView) setTimeout(function () { sm.scrollIntoView({ block: "start" }); }, 30);
    }
    if (d.open && window.neuZeichnen) window.neuZeichnen();
  }, true);
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
    var ticks = false, letzterAktiv = -2, knopfAn = null;
    var pruefen = function () {
      ticks = false;
      var an = window.scrollY > window.innerHeight * 1.2;
      if (an !== knopfAn) { knopfAn = an; knopf.classList.toggle("on", an); }
      var aktiv = -1, grenze = window.scrollY + 120;
      abschnitte.forEach(function (sec, i) { if (!sec || sec.offsetParent === null) return; var r = sec.getBoundingClientRect(); if (r.top <= 120 && r.bottom > 120) aktiv = i; });
      if (aktiv < 0) [["teil1", "lage"], ["teil2", "patches"], ["teilb", "logbuch"], ["teil3", "info"]].forEach(function (p) {
        var t = document.getElementById(p[0]); if (!t) return; var r = t.getBoundingClientRect();
        if (r.top <= 120 && r.bottom > 120) navLinks.forEach(function (l, i) { if (l.getAttribute("data-sec") === p[1]) aktiv = i; });
      });
      if (aktiv === letzterAktiv) return;  // nur bei Wechsel in die Leiste schreiben: ein Schreibzugriff je Scroll-Bild lässt unter dem Glas der Leiste (iOS) alles neu zeichnen
      letzterAktiv = aktiv;
      navLinks.forEach(function (a, i) { if (i === aktiv) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current"); a.classList.toggle("aktiv", i === aktiv); });
    };
    window.addEventListener("scroll", function () { if (!ticks) { ticks = true; requestAnimationFrame(pruefen); } }, { passive: true });
    window.addEventListener("load", pruefen);
  }

  fetch("/data/lage.json", { cache: "no-cache" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(render)
    .catch(function (err) { if (window.console) console.error(err);
      $("stand").textContent = txt("keine");
      $("stufe-wert").textContent = txt("keine");
      $("stufe-text").textContent = txt("laden_fehler");
    });

  function render(d) {
    var kq0 = (d.quellen || []).filter(function (q) { return q.id === "cisa-kev"; })[0] || {};
    $("stand").textContent = datum((d.radar && d.radar.abgerufen_am) || kq0.abgerufen_am || d.stand);
    window.__pegel = d.pegel || null;
    zeigeLogbuch(d.logbuch || []);
    var fz = $("fazit"), f = d.fazit;
    if (fz && f) {
      fz.textContent = "";
      var fk = el("b", "mono", pick("Fazit", "Conclusion")); fz.appendChild(fk);
      if (f.treiber && f.stufe_satz) {
        // Sichtbar nur das Wichtigste: Lage in einem Satz und der erste Satz der Empfehlung. Der Rest steht unter „Mehr zum Fazit“.
        var hinw = pick(f.hinweis, f.hinweis_en) || "", cut = hinw.search(/[.!?]\s+[A-ZÄÖÜ]/), kurz = cut > 0 ? hinw.slice(0, cut + 1) : hinw, rest = cut > 0 ? hinw.slice(cut + 1).trim() : "";
        var dl = el("dl", "fz-dl");
        [[pick("Lage", "Situation"), pick(f.stufe_satz, f.stufe_satz_en), ""], [pick("Empfehlung", "Advice"), kurz, "fh"]].forEach(function (z) {
          dl.appendChild(el("dt", "mono", z[0])); dl.appendChild(el("dd", z[2], z[1]));
        });
        fz.appendChild(dl);
        var mehr = el("details", "fz-mehr"); mehr.appendChild(el("summary", "mono", pick("Mehr zum Fazit", "More on the conclusion")));
        var dl2 = el("dl", "fz-dl");
        dl2.appendChild(el("dt", "mono", pick("Treiber", "Drivers"))); dl2.appendChild(el("dd", "", pick(f.treiber, f.treiber_en)));
        if (rest) { dl2.appendChild(el("dt", "mono", pick("Dazu", "Also"))); dl2.appendChild(el("dd", "", rest)); }
        var tp = d.tempo || {}, zj = ((d.radar || {}).zeit_bis_kev || {}).jetzt || {};
        if (typeof tp.wert === "number") {
          dl2.appendChild(el("dt", "mono", pick("Tempo bis KEV", "Pace to KEV")));
          var dz = el("dd", "fz-zeit"), tg = tp.wert.toLocaleString(window.I18N.locale, { maximumFractionDigits: 1 });
          dz.appendChild(document.createTextNode(pick("Neue Lücken stehen im Median ", "New flaws are on the KEV list a median ")));
          dz.appendChild(el("strong", "mono", tg + " " + (tp.wert === 1 ? pick("Tag", "day") : pick("Tage", "days"))));
          dz.appendChild(document.createTextNode(pick(" nach ihrer Veröffentlichung auf der KEV-Liste", " after publication")
            + (typeof zj.anteil_30 === "number" ? ", " + Math.round(zj.anteil_30 * 100) + pick(" % innerhalb von 30 Tagen", "% within 30 days") : "")
            + (tp.fenster_tage ? pick(" (Aufnahmen der letzten " + tp.fenster_tage + " Tage)", " (additions of the last " + tp.fenster_tage + " days)") : "") + ". "));
          var zl = el("a", "", pick("Verlauf", "History")); zl.href = "#rueckblick"; zl.setAttribute("data-offen", "k-r-tempo"); dz.appendChild(zl);
          dl2.appendChild(dz);
        }
        var top = ((((d.patches || {}).prioritaet || {}).liste) || []).slice(0, 3);
        if (top.length) {
          dl2.appendChild(el("dt", "mono", pick("Zuerst patchen", "Patch first")));
          var dd = el("dd", "fz-top");
          top.forEach(function (p, i) {
            if (i) dd.appendChild(document.createTextNode(" · "));
            var nm = String(p.titel || "").replace(/^[A-Z]+-[\d:-]+:\s*/, "").split(",")[0].replace(/^.*\//, "").replace(/\s+(security update|vulnerabilit(y|ies)|update)$/i, "").trim();
            if (nm.length > 34) nm = nm.slice(0, 34).replace(/\s+\S*$/, "") + "…";
            var mk = { 1: "KEV", 2: pick("ausgenutzt", "exploited"), 3: "EPSS", 4: pick("kritisch", "critical") }[p.stufe] || "";
            var lk = el("a", "", (p.cves && p.cves[0] ? p.cves[0] : nm) + (p.cves && p.cves[0] && nm ? " (" + nm + ")" : "")); lk.href = "#patches"; lk.title = pick(p.grund, p.grund_en) || ""; dd.appendChild(lk);
            if (mk) { dd.appendChild(document.createTextNode(" ")); dd.appendChild(el("span", "fz-mk mono", mk)); }
          });
          dl2.appendChild(dd);
        }
        mehr.appendChild(dl2);
        var bg = el("p", "mono dim fine", pick("KEV: Liste nachweislich ausgenutzter Lücken der US-Behörde CISA · CERT-Bund: Warndienst des BSI · „2,6-fach“: Messwert im Verhältnis zur Schwelle des Bausteins (1,0 = Schwelle erreicht) · ", "KEV: list of flaws proven to be exploited, kept by the US agency CISA · CERT-Bund: warning service of the BSI · “2.6x”: measured value relative to the component’s threshold (1.0 = threshold reached) · "));
        var bl = el("a", "", pick("alle Begriffe", "all terms")); bl.href = "#info"; bl.setAttribute("data-offen", "i-begriffe"); bg.appendChild(bl); mehr.appendChild(bg);
        mehr.appendChild(el("p", "mono dim fine", pick("Feste Sätze nach Regeln, keine Vorhersage. Stufen des Dreier-Pegels geprüft am ", "Fixed sentences by rule, no forecast. Dreier Gauge levels checked on ") + datum(f.stand) + (f.status === "vorlaeufig" ? pick(", Stufengrenzen noch vorläufig.", ", level limits still provisional.") : ".")));
        fz.appendChild(mehr);
      } else {
        fz.appendChild(el("p", "ft", pick(f.text, f.text_en)));
        fz.appendChild(el("p", "fh", pick("Für Verteidiger: ", "For defenders: ") + pick(f.hinweis, f.hinweis_en)));
      }
      fz.hidden = false; var fv = $("fazit-verk"); if (fv) fv.hidden = false;
    }
    var kqz = $("kern-quelle"); if (kqz) kqz.textContent = pick("Quelle aller Zahlen in diesem Kasten: CISA-KEV-Katalog, abgerufen ", "Source of all figures in this box: CISA KEV catalog, retrieved ") + datum(kq0.abgerufen_am || d.stand) + pick(" (Katalog veröffentlicht ", " (catalog published ") + datum(kq0.veroeffentlicht_am) + ")";

    var hatStufe = d.stufe !== null && d.stufe !== undefined;
    var name = hatStufe ? txt(String(d.stufe)) : null;
    $("stufe-wert").textContent = hatStufe ? name : "null";
    if (hatStufe && d.pegel && typeof d.pegel.wert === "number") document.title = name.toUpperCase() + " " + d.pegel.wert + pick(" · Cyberlage: Cyber-Bedrohungslage heute", " · Cyberlage: cyber threat level today");
    Array.prototype.forEach.call(document.querySelectorAll(".fuss-siegel"), function (fsg) {  // Web-Audit und Code-Audit im Fuß
      fsg.href = pick("/audit/", "/en/audit/") + (fsg.id === "fuss-siegel-code" ? "#code-audit" : ""); fsg.querySelector("span").textContent = pick(fsg.getAttribute("data-de"), fsg.getAttribute("data-en"));
    });
    var na = $("n-audit"); if (na) na.href = pick("/audit/", "/en/audit/");
    var nl = $("n-links"); if (nl) nl.href = pick("/links/", "/en/links/");
    var hk = $("hero-kurz");
    if (hk && d.pegel && typeof d.pegel.wert === "number" && d.kev) {
      hk.textContent = pick("Gesamtscore " + d.pegel.wert + " von 100 aus " + d.pegel.signale + " von " + d.pegel.von + " Bausteinen. Neu im CISA-Katalog ausgenutzter Schwachstellen: " + d.kev.neu_7_tage + " in 7 Tagen, " + d.kev.neu_30_tage + " in 30 Tagen.",
        "Score " + d.pegel.wert + " out of 100, from " + d.pegel.signale + " of " + d.pegel.von + " components. Newly added to the CISA catalogue of exploited vulnerabilities: " + d.kev.neu_7_tage + " in 7 days, " + d.kev.neu_30_tage + " in 30 days.");
    }
    var ls = document.querySelector('[data-t="l_stufe"]');
    if (ls && d.pegel && d.pegel.modell) ls.textContent = pick("dreier-pegel " + d.pegel.modell + " · von dreier labs · weltweit", "dreier gauge " + d.pegel.modell + " · by dreier labs · worldwide");
    var rv = document.querySelector('[data-t="r_rscore"]');
    if (rv && d.pegel && d.pegel.modell) rv.textContent = pick("Dreier-Pegel " + d.pegel.modell + " im Verlauf · 3 Jahre", "Dreier Gauge " + d.pegel.modell + " over time · 3 years");
    window.DP = hatStufe ? name + (d.pegel && typeof d.pegel.wert === "number" ? " " + d.pegel.wert : "") : "";
    if (hatStufe) $("lage-box").classList.add("st-" + d.stufe);
    $("stufe-text").textContent = hatStufe ? "" : txt("keine_bew");
    $("stufe-text").hidden = hatStufe;
    $("stufe-begr").textContent = pick(d.stufe_begruendung, d.stufe_begruendung_en) || "";
    /* Was die Stufe in einem Satz heißt (Orientierung für Neulinge, siehe RULES.md „Einstieg“) */
    var sinn = $("stufe-sinn"), SINN = {
      ruhig: ["Weniger Aktivität als üblich.", "Less activity than usual."],
      unauffaellig: ["Aktivität im üblichen Rahmen.", "Activity within the usual range."],
      angespannt: ["Etwas mehr Aktivität als üblich.", "Somewhat more activity than usual."],
      hoch: ["Deutlich mehr Aktivität als üblich.", "Clearly more activity than usual."],
      ausserordentlich: ["Außergewöhnlich viel Aktivität.", "Exceptionally high activity."]
    };
    if (sinn) {
      var sz = hatStufe && SINN[d.stufe]; sinn.hidden = !sz;
      if (sz) {
        sinn.textContent = pick(sz[0] + " Das beschreibt die Lage weltweit, keine Warnung für dich persönlich. ", sz[1] + " This describes the global situation, not a warning for you personally. ");
        var sa = document.createElement("a"); sa.href = "#info"; sa.setAttribute("data-offen", "i-faq"); sa.textContent = pick("Was heißt das? ▸", "What does this mean? ▸"); sinn.appendChild(sa);
      }
    }

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
      var kp = body.parentNode.tHead && body.parentNode.tHead.rows[0];
      if (kp) Array.prototype.forEach.call(tr.cells, function (z, i) { if (kp.cells[i]) z.setAttribute("data-l", kp.cells[i].textContent); });
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
      $("rechnung").innerHTML = txt("rechnung", d.fenster_tage || 30, sw.erhoeht_ab, sw.hoch_ab, sw.ransomware_aufschlag_ab, Number(sw.basis_monate) || 12, Number(sw.median));
    } else {
      $("rechnung").textContent = txt("keine");
    }
    zeichneVerlauf(d.verlauf || [], d.schwellen || {});
    zeichneScoreVerlauf(d.pegel || null);
    window.neuZeichnen = function () { zeichneVerlauf(d.verlauf || [], d.schwellen || {}); zeichneScoreVerlauf(d.pegel || null); var zz = (d.radar || {}).zeit_bis_kev || {}; if (zz.verlauf) zeichneRadar(zz.verlauf); };
    var tl = d.telegram && d.telegram.link;
    if (/^https:\/\/t\.me\//.test(tl || "")) { $("telegram-link").href = tl; $("telegram").hidden = false; }
    d_stand = d.stand; d_skala = d.radar_skala || null;
    zeigeBsi(d.cert_bund);
    zeigeEu(d.eu_kev);
    zeigeAusblick(d.ausblick);
    zeigeRadar(d.radar, d);
    zeigeKonsens(d.radar);
    d_life = d.patches && d.patches.lifecycle || null; life_d = d_life;
    zeigeTicker(d);
    zeigeBoard(d);
    zeigeSchnell(d);
    zeigeTermine();
    zeigeZuerst(d.patches && d.patches.prioritaet);
    zeigeBereiche(d);
    d_prio = d.patches && d.patches.prioritaet || null;
    zeigePatchLevel(d.patches && d.patches.microsoft, d_life);
    zeigeLebenszyklen(d_life);
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
        if (offen) { var d = $(offen); if (d) { aufklappen(d); d.open = true; } ziel = d || ziel; }
        menues.forEach(function (m) { m.open = false; });
        if (ziel) ziel.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
      });
    });
  }
  bedienung();

  var DX = [[/Office und SharePoint/g, "Office and SharePoint"], [/Entwicklung und Server/g, "Development and servers"], [/Cloud und Dienste/g, "Cloud and services"],
    [/Windows \(andere\)/g, "Windows (other)"], [/\bSonstige\b/g, "Other"], [/ und weitere\b/g, " and more"], [/\bkritisch\b/g, "critical"], [/\bmittel\b/g, "medium"], [/\bniedrig\b/g, "low"], [/\bhoch\b/g, "high"], [/\bunbekannt\b/g, "unknown"]];
  function dx(t) { if (window.I18N.lang !== "en" || typeof t !== "string") return t; DX.forEach(function (r) { t = t.replace(r[0], r[1]); }); return t; }

  function monatKurz(id) {
    var M = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], i = M.indexOf((id || "").slice(5));
    return i < 0 ? (id || "").slice(5) : new Date(Date.UTC(2000, i, 1)).toLocaleDateString(window.I18N.locale, { timeZone: "UTC", month: "short" }).replace(".", "");
  }

  function zeichneVerlauf(v, sw) {
    var svg = $("verlauf"), NS = "http://www.w3.org/2000/svg";
    Array.prototype.slice.call(svg.childNodes).forEach(function (n) { if (n.nodeName !== "title") svg.removeChild(n); });
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
      mk("text", { x: L - 6, y: y(n) + 4, "text-anchor": "end", fill: "#8a99a6", "font-size": 12, "font-family": "ui-monospace,monospace" }, String(n));
    });
    v.forEach(function (p, i) {
      var t = mk("rect", { x: L + i * w + 1, y: y(p.neu), width: Math.max(w - 2, 1), height: y(0) - y(p.neu), fill: farbe[p.stufe] || "#8a99a6" });
      t.appendChild(document.createElementNS(NS, "title")).textContent = txt("v_tip", datum(p.stand), p.neu, p.stufe ? txt(p.stufe) : "");
    });
    [["erhoeht_ab", "erhöht ab", "#e3b341"], ["hoch_ab", "hoch ab", "#ff8a7a"]].forEach(function (c) {
      if (typeof sw[c[0]] !== "number") return;
      mk("line", { x1: L, x2: B - R + 2, y1: y(sw[c[0]]), y2: y(sw[c[0]]), stroke: c[2], "stroke-dasharray": "5 4" });
      mk("text", { x: B - R + 6, y: y(sw[c[0]]) + 4, "text-anchor": "start", fill: c[2], "font-size": 12, "font-family": "ui-monospace,monospace" }, txt(c[0] === "hoch_ab" ? "hoch" : "erhoeht") + " " + sw[c[0]]);
    });
    [0, Math.floor(v.length / 2), v.length - 1].forEach(function (i) {
      mk("text", { x: L + i * w + w / 2, y: H - 8, "text-anchor": i === 0 ? "start" : (i === v.length - 1 ? "end" : "middle"), fill: "#8a99a6", "font-size": 12, "font-family": "ui-monospace,monospace" }, datum(v[i].stand));
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
    if (!v.length && sc && sc.reihe_k) {
      var rk = sc.reihe_k, t0 = Date.parse(rk.start + "T00:00:00Z");
      v = rk.a.map(function (a, i) { var st = new Date(t0 + i * 86400000).toISOString().slice(0, 10), lv = rk.live[st]; return { stand: st, ausnutzung: a, n: rk.n[i], wert: lv ? lv[0] : null, signale: lv ? lv[1] : null }; });
    }
    if (!v.length) { leg.textContent = txt("keine"); return; }
    var B = Math.max(300, Math.round(svg.getBoundingClientRect().width)) || 1000, H = B < 600 ? 190 : 230, L = 30, R = B < 600 ? 16 : 118, T = 12, U = 28;
    svg.setAttribute("viewBox", "0 0 " + B + " " + H);
    var mk = function (tag, a, t) { var e = document.createElementNS(NS, tag); for (var k in a) e.setAttribute(k, a[k]); if (t !== undefined) e.textContent = t; svg.appendChild(e); return e; };
    var y = function (n) { return T + (H - T - U) * (1 - n / 100); };
    var x = function (i) { return v.length < 2 ? (L + B - R) / 2 : L + i * (B - L - R) / (v.length - 1); };
    var mono = { "font-size": 12, "font-family": "ui-monospace,monospace", fill: "#8a99a6" };
    var stf = d_skala && d_skala.stufen && d_skala.stufen.length > 1 ? d_skala.stufen : null;
    var grenzen = stf ? stf.slice(0, -1).map(function (z) { return z.bis; }) : [35, 50, 64, 80];
    [0, 100].forEach(function (n) { mk("line", { x1: L, x2: B - R, y1: y(n), y2: y(n), stroke: "#1d262e" }); });
    [0].concat(grenzen, [100]).forEach(function (n) { mk("text", Object.assign({ x: L - 6, y: y(n) + 4, "text-anchor": "end" }, mono), String(n)); });
    grenzen.forEach(function (n) { mk("line", { x1: L, x2: B - R, y1: y(n), y2: y(n), stroke: n === 50 ? "#263340" : "#1d262e", "stroke-dasharray": n === 50 ? "4 4" : "2 4" }); });
    // Namen der Stufen am rechten Rand, nur wo Platz ist (Desktop); am Handy stehen die Grenzzahlen links
    if (stf && R > 60) {
      var unten = 0;
      stf.forEach(function (z) {
        var oben = Math.min(z.bis, 100);
        mk("text", Object.assign({ x: B - R + 8, y: y((unten + oben) / 2) + 4, "text-anchor": "start" }, mono, { "font-size": 11 }), pick(z.name, z.name_en || z.name));
        unten = oben;
      });
    }
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
      var il = live[live.length - 1], lw = v[il].wert, la = v[il].ausnutzung;
      var kopf = mk("text", Object.assign({ x: B - R - 8, y: T + 10, "text-anchor": "end" }, mono, { stroke: "#0d1117", "stroke-width": 4, "paint-order": "stroke" }));
      var t1 = document.createElementNS(NS, "tspan"); t1.setAttribute("fill", "#6fe0a0"); t1.setAttribute("font-weight", "600"); t1.textContent = "● " + pick("heute ", "today ") + lw; kopf.appendChild(t1);
      var t2 = document.createElementNS(NS, "tspan"); t2.setAttribute("fill", "#8fbfa6"); t2.textContent = pick("  ·  Linie ", "  ·  line ") + la; kopf.appendChild(t2);
    }
    // Zeitachse: echte Kalenderdaten (1. Januar mit Jahreszahl, 1. Juli als Strich), nicht Drittel der Datenpunkte
    var letzt = v.length - 1, endX = x(letzt);
    for (var yr = +v[0].stand.slice(0, 4); yr <= +v[letzt].stand.slice(0, 4); yr++) {
      [["01-01", true], ["07-01", false]].forEach(function (m) {
        var tag = yr + "-" + m[0], k = -1;
        for (var q = 0; q < v.length; q++) { if (v[q].stand >= tag) { k = q; break; } }
        if (k < 0 || v[k].stand.slice(0, 7) !== tag.slice(0, 7) || k === letzt) return;
        mk("line", { x1: x(k), x2: x(k), y1: H - U, y2: H - U + 5, stroke: "#3a4650" });
        if (m[1] && endX - x(k) > (R > 60 ? 96 : 60)) mk("text", Object.assign({ x: x(k), y: H - 8, "text-anchor": x(k) < L + 20 ? "start" : "middle" }, mono), String(yr));
      });
    }
    mk("text", Object.assign({ x: endX, y: H - 8, "text-anchor": "end" }, mono), R > 60 ? datum(v[letzt].stand) : pick("heute", "today"));
    svg.setAttribute("role", "img"); svg.setAttribute("aria-label", pick("Verlauf des Dreier-Pegels, zuletzt " + (typeof sc.wert === "number" ? sc.wert : "–") + " von 100.", "Dreier Gauge over time, latest " + (typeof sc.wert === "number" ? sc.wert : "–") + " of 100."));
    var ak = v[v.length - 1].ausnutzung;
    // Der Text über den heutigen Pegel richtet sich nach der Zahl der gespeicherten Tage: erst ein Punkt, dann ein kurzes Stück, später eine Linie
    var tage = live.length, hz = typeof lw === "number" ? lw : "–", abw = typeof lw === "number" && lw !== ak, seit = datum(sc.live_seit);
    var heute_de = tage <= 1 ? "Der Punkt am Ende ist der Pegel von heute (" + hz + "). Die Daten dafür sind ganz neu: mit jedem Tag kommt ein Punkt dazu, bis daraus eine Linie wird."
      : tage < 30 ? "Das helle Stück am Ende ist der Pegel von heute (" + hz + "), gespeichert seit dem " + seit + " (" + tage + " Tage). Mit jedem Tag wird es länger."
      : "Die helle Linie am Ende ist der Pegel von heute (" + hz + "), gespeichert seit dem " + seit + ".";
    var heute_en = tage <= 1 ? "The dot at the end is today's gauge (" + hz + "). The data for it is brand new: one dot is added every day until it becomes a line."
      : tage < 30 ? "The bright stretch at the end is today's gauge (" + hz + "), stored since " + seit + " (" + tage + " days). It grows longer every day."
      : "The bright line at the end is today's gauge (" + hz + "), stored since " + seit + ".";
    leg.textContent = pick("Die Linie zeigt, wie der Pegel in den letzten 3 Jahren gewesen wäre, nach den heutigen Regeln aus echten Meldungen berechnet. " + heute_de + (abw ? " Der heutige Pegel weicht von der Linie (" + ak + ") ab, weil er auch die Einschätzungen von BSI und SANS enthält; die gibt es nur für heute." : ""),
      "The line shows what the gauge would have been over the last 3 years, calculated from real advisories using today's rules. " + heute_en + (abw ? " Today's gauge differs from the line (" + ak + ") because it also includes the assessments of BSI and SANS, which exist only for today." : ""));
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
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(u).then(ok, function () { window.location.href = "/feed.xml"; });
      else window.location.href = "/feed.xml";
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
    var sl = sv("text", { x: C - (R / 2 + 6) * 0.383, y: C - (R / 2 + 6) * 0.924, "class": "sc-tx", "text-anchor": "end" }); sl.textContent = pick("Schwelle", "threshold");
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
      [["" + m.cves, y - 3, "#dfe6ec"], [monatKurz(m.id) + (i === 0 || m.id.slice(5) === "Jan" ? " '" + m.id.slice(2, 4) : ""), H - 8, "#8a99a6"]].forEach(function (tx) {
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
      else if (f.build) t.push(pick("Version ", "version ") + f.build + (f.produkt || f.fuer ? " (" + dx(f.produkt || f.fuer) + ")" : ""));
      else if (f.text && f.text.toLowerCase() !== "release notes") t.push(f.text + (f.fuer ? " (" + f.fuer + ")" : ""));
    });
    return t;
  }
  /* Board im Kopf: feststehende Tafel mit den nächsten wichtigen Terminen (kein Lauftext). Quelle der Zeilen: Patch-Kalender (termine) und Support-Ende (data/patches/lifecycle). */
  function lifeName(slug, z) {
    var c = String(z.zyklus || ""), m;
    if (slug === "windows") {
      var wz = winZyklus(c);
      if (!wz) return "Windows " + c;
      return "Windows " + wz.v + " " + wz.r.toUpperCase() + (wz.ed ? " (" + wz.ed + ")" : "");
    }
    if (slug !== "windows-server") return ((life_d && life_d.produkte && life_d.produkte[slug] && life_d.produkte[slug].name) || slug) + " " + c;
    return "Windows Server " + c.replace(/-r2$/i, " R2").replace(/^(\d+h\d)/i, function (x) { return x.toUpperCase(); });
  }
  function lifeEreignisse(life, t0, tage) {
    var out = [];
    Object.keys((life && life.produkte) || {}).forEach(function (slug) {
      (life.produkte[slug].zyklen || []).forEach(function (z) {
        if (life.produkte[slug].gruppe !== "os") return;  // Board: nur Betriebssysteme, den Rest zeigt /lebenszyklen
        if (slug === "windows" && (!winZyklus(z.zyklus) || winZyklus(z.zyklus).ed === null)) return;  // Enterprise/Education, Pro, LTSC; IoT bleibt außen vor
        [["eol", pick("Support-Ende ", "End of support ")], ["erweitert", pick("Ende erweiterter Support ", "End of extended support ")]].forEach(function (f) {
          var dt = z[f[0]]; if (!dt) return;
          var zeit = Date.parse(dt + "T00:00:00Z"), n = Math.round((zeit - t0) / TAG_MS);
          if (n >= 0 && n <= tage) out.push({ zeit: zeit, tage: n, n: f[1] + lifeName(slug, z), l: "#lebenszyklen" });
        });
      });
    });
    return out;
  }
  function zeigeBoard(d) {
    var box = $("board"), ul = $("bd-l"); if (!box || !ul) return;
    var heute = new Date(), t0 = Date.UTC(heute.getUTCFullYear(), heute.getUTCMonth(), heute.getUTCDate()), zeilen = [];
    var g = termine(heute, 12).filter(function (x) { return x.ev.some(function (e) { return e.art === "ms"; }); })[0];
    if (g) {
      var rest = g.ev.length - 1;
      zeilen.push({ zeit: g.zeit, tage: g.tage, n: "Microsoft Patch Day" + (rest > 0 ? " +" + rest + pick(" Hersteller", " vendors") : ""), l: "#termine" });
    }
    var gesehen = {};
    lifeEreignisse(d.patches && d.patches.lifecycle, t0, 120).sort(function (a, b) { return a.zeit - b.zeit; }).forEach(function (e) {
      var k = e.n + e.zeit; if (gesehen[k] || zeilen.length >= 5) return; gesehen[k] = 1; zeilen.push(e);
    });
    zeilen.sort(function (a, b) { return a.zeit - b.zeit; });
    ul.textContent = "";
    zeilen.forEach(function (e) {
      var li = el("li", "bd-r" + (e.tage <= 2 ? " bd-nah" : ""));
      var dz = new Date(e.zeit), lo = window.I18N.locale;
      var bl = el("span", "bd-bl", ""); bl.setAttribute("aria-hidden", "true");
      bl.appendChild(el("span", "mono bd-mo", dz.toLocaleDateString(lo, { timeZone: "UTC", month: "short" }).replace(".", "")));
      bl.appendChild(el("strong", "bd-tg", String(dz.getUTCDate())));
      li.appendChild(bl);
      var sr = el("span", "sr", dz.toLocaleDateString(lo, { timeZone: "UTC", weekday: "short", day: "2-digit", month: "2-digit", year: "numeric" }) + ", "); li.appendChild(sr);
      var cc = el("span", "mono bd-c", inTagen(e.tage));
      var w = el("span", "bd-n"), la = link(e.l, e.n); if (la.tagName !== "A") { la = el("a", "", e.n); la.href = e.l; } w.appendChild(la); var tx = el("span", "bd-x"); tx.appendChild(cc); tx.appendChild(w); li.appendChild(tx); ul.appendChild(li);
    });
    $("bd-h").textContent = pick("ANSTEHEND", "UPCOMING");
    box.setAttribute("aria-label", pick("Anstehende wichtige Termine", "Upcoming important dates"));
    var m = $("bd-m"); if (m) m.textContent = pick("alle Termine", "all dates");
    box.hidden = !zeilen.length;
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
    if (window.DP) add(pick("Dreier-Pegel: ", "Dreier Gauge: ") + window.DP, "#lage");
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
  /* Ausgenutzte Lücken der letzten 30 Tage, nach Bereich (config/bereiche.json). Die Auswahl bleibt nur im Browser. */
  function zeigeBereiche(d) {
    var box = $("p-bereich"); if (!box) return;
    var bl = d.bereiche && d.bereiche.liste, neu = d.neu || [];
    if (!bl || !bl.length) { box.hidden = true; return; }
    box.hidden = false; box.textContent = "";
    box.appendChild(el("h3", "mono rd-t", pick("Was betreue ich?", "What do I look after?")));
    box.appendChild(el("p", "dim", pick("Bereich wählen: Die Seite zeigt die Hersteller dieses Bereichs mit Zahlen und Patch-Tag und darunter, was dort gerade angegriffen wird. Gezeigt werden Lücken, die in den letzten " + (d.fenster_tage || 30) + " Tagen als nachweislich angegriffen in den CISA-KEV kamen, zugeordnet nach Hersteller und Produkt.",
      "Pick an area: the site shows that area's vendors with figures and patch day and, below, what is being attacked there. Shown are flaws added to the CISA KEV as proven attacked in the last " + (d.fenster_tage || 30) + " days, assigned by vendor and product.")));
    var wahl = lsGet("cl_bereich"); if (wahl !== "alle" && !bl.some(function (b) { return b.id === wahl; })) wahl = "alle";
    var bname = {}; bl.forEach(function (b) { bname[b.id] = pick(b.name, b.name_en); });
    var prl = (((d.patches || {}).prioritaet || {}).liste) || [], prn = {}; prl.forEach(function (p) { prn[p.bereich] = (prn[p.bereich] || 0) + 1; });
    /* Zwei Zahlen je Knopf: Einträge in „Diese Woche zuerst patchen“ und neu im KEV (30 Tage) */
    function knopfText(k, name, patch, kev) {
      k.textContent = ""; k.appendChild(document.createTextNode(name + " "));
      var z = el("span", "b-z"); z.appendChild(el("b", patch ? "rw" : "", String(patch))); z.appendChild(document.createTextNode(" · " + kev)); k.appendChild(z);
      k.setAttribute("aria-label", name + pick(": " + patch + " zuerst patchen, " + kev + " neu angegriffen", ": " + patch + " to patch first, " + kev + " newly attacked"));
    }
    var bt = el("div", "p-btns mono b-btns"); bt.setAttribute("role", "group"); bt.setAttribute("aria-label", pick("Bereich", "Area")); box.appendChild(bt);
    var leg = el("p", "mono dim fine b-leg"); leg.appendChild(document.createTextNode(pick("Zahlen je Bereich: ", "Figures per area: "))); leg.appendChild(el("b", "rw", pick("zuerst patchen", "patch first"))); leg.appendChild(document.createTextNode(pick(" · neu angegriffen (CISA-KEV, 30 Tage)", " · newly attacked (CISA KEV, 30 days)"))); box.appendChild(leg);
    var info = el("p", "mono dim fine"), ul = el("ul", "b-liste"); box.appendChild(info);
    var zbox = el("div", "b-zu"); box.appendChild(zbox);
    box.appendChild(el("h4", "mono b-h4", pick("Gerade angegriffen (CISA-KEV, 30 Tage)", "Under attack now (CISA KEV, 30 days)"))); box.appendChild(ul);
    box.appendChild(el("p", "mono dim fine", pick("Reine Zuordnung nach Namen, feste Regeln in RULES.md. Was bei dir im Einsatz ist, weiß die Seite nicht: eigenes Inventar prüfen. Frist = Frist der CISA für US-Behörden, als Anhalt. Die Auswahl bleibt nur in diesem Browser.",
      "Assignment by name only, fixed rules in RULES.md. The site does not know what you run: check your own inventory. Deadline = CISA deadline for US agencies, as a guide. Your choice stays in this browser only.")));
    var hq = ((d.patches || {}).hersteller || {}).quellen || {}, hbox = el("div", "b-hs"); box.insertBefore(hbox, zbox.nextSibling);
    /* Hersteller je Bereich: q = Quelle mit Zahlen, t = Patch-Tag nach Regel des Herstellers, a = Sprung zu einem Abschnitt, ohne = noch keine offene Quelle angebunden */
    var KAT = {
      netzwerk: [{ n: "Cisco", q: "cisco" }, { n: "Fortinet", q: "fortinet", t: "fortinet" }, { n: "Palo Alto Networks", q: "paloalto" }, { n: "Ivanti", q: "ivanti", t: "ivanti" }],
      fernwartung: [{ n: "Ivanti", q: "ivanti", t: "ivanti" }, { n: "ConnectWise", ohne: 1 }, { n: "SolarWinds", ohne: 1 }],
      arbeitsplatz: [{ n: "Browser: Chrome, Edge, Firefox, Opera, Safari", n_en: "Browsers: Chrome, Edge, Firefox, Opera, Safari", a: "k-edge" }, { n: "Mozilla (Firefox, Thunderbird)", q: "mozilla" }, { n: "Adobe", t: "adobe", l: "https://helpx.adobe.com/security.html" }, { n: "Apple", q: "apple" }],
      virtualisierung: [{ n: "Citrix (Cloud Software Group)", t: "citrix", l: "https://support.citrix.com/securitybulletins" }, { n: "Terminalserver und Remote-Desktop (Microsoft)", n_en: "Terminal servers and Remote Desktop (Microsoft)", t: "ms", a: "k-ms" }, { n: "VMware (Broadcom)", ohne: 1 }],
      windows: [{ n: "Microsoft Patch Day", t: "ms", a: "k-ms" }],
      zusammenarbeit: [{ n: "Microsoft (Exchange, SharePoint, Teams)", t: "ms", a: "k-ms" }, { n: "Atlassian", ohne: 1 }, { n: "Zimbra", ohne: 1 }],
      anwendungen: [{ n: "SAP", q: "sap", t: "sap" }, { n: "Oracle", t: "oracle", l: "https://www.oracle.com/security-alerts/" }],
      linux: [{ n: "Ubuntu", q: "ubuntu" }, { n: "Debian", q: "debian" }, { n: "Red Hat", q: "redhat" }, { n: "SUSE", q: "suse" }, { n: "AlmaLinux", q: "alma" }, { n: "Rocky Linux", q: "rocky" }, { n: "Amazon Linux", q: "amazon" }]
    };
    function naechster(art) {
      var g = termine(new Date(), 14).filter(function (x) { return x.ev.some(function (e) { return e.art === art; }); })[0];
      return g ? new Date(g.zeit).toLocaleDateString(window.I18N.locale, { timeZone: "UTC", weekday: "short", day: "2-digit", month: "2-digit" }) + " (" + inTagen(g.tage) + ")" : "";
    }
    function zeigeHersteller() {
      hbox.textContent = "";
      var liste = KAT[wahl];
      if (wahl === "alle") { hbox.appendChild(el("p", "dim fine", pick("Hersteller mit Zahlen und Patch-Tag erscheinen, sobald ein Bereich gewählt ist.", "Vendors with figures and patch day appear once an area is picked."))); return; }
      if (!liste) {
        if (wahl !== "sonstige") { hbox.appendChild(el("h4", "mono", pick("Hersteller in diesem Bereich", "Vendors in this area"))); hbox.appendChild(el("p", "dim fine", pick("Für diesen Bereich ist noch keine Hersteller-Quelle angebunden. Maßgeblich ist die Liste der angegriffenen Lücken darunter.", "No vendor source is connected for this area yet. The list of attacked flaws below is what counts."))); }
        return;
      }
      hbox.appendChild(el("h4", "mono", pick("Hersteller in diesem Bereich", "Vendors in this area")));
      var gr = el("div", "b-kacheln"); hbox.appendChild(gr);
      liste.forEach(function (h) {
        var k = el("div", "b-k"), q = h.q ? hq[h.q] : null, name = pick(h.n, h.n_en || h.n), kopf = el("div", "b-kn mono");
        if (h.a) { var an = el("a", "", name); an.href = "#" + h.a; an.addEventListener("click", function () { var z = $(h.a); if (z) z.open = true; }); kopf.appendChild(an); }
        else if (q && q.url) kopf.appendChild(link(q.url, name));
        else if (h.l) kopf.appendChild(link(h.l, name));
        else kopf.appendChild(document.createTextNode(name));
        k.appendChild(kopf);
        if (h.q) {
          if (!q) k.appendChild(el("div", "dim fine", pick("Zahlen folgen mit dem nächsten Abruf", "figures follow with the next fetch")));
          else if (q.status !== "ok" || typeof q.neu_30 !== "number") k.appendChild(el("div", "dim fine", pick("keine Daten (Quelle nicht erreichbar)", "no data (source unreachable)")));
          else {
            k.appendChild(el("div", "b-kz mono", pick(q.neu_30 + " Meldungen in 30 Tagen, " + q.neu_7 + " in 7", q.neu_30 + " advisories in 30 days, " + q.neu_7 + " in 7")));
            var zus = []; if (q.schwere_bekannt && q.kritisch_30) zus.push(pick(q.kritisch_30 + " kritisch", q.kritisch_30 + " critical")); if (q.im_kev_30) zus.push(pick(q.im_kev_30 + " mit Lücke im KEV", q.im_kev_30 + " with a KEV flaw"));
            if (zus.length) k.appendChild(el("div", "b-kz mono rw", zus.join(" · ")));
            var n1 = (q.letzte || [])[0];
            if (n1) { var dv = el("div", "dim fine"); dv.appendChild(document.createTextNode(pick("zuletzt ", "latest ") + datum(n1.datum) + ": ")); dv.appendChild(link(n1.link, dx(String(n1.titel).slice(0, 70)))); k.appendChild(dv); }
          }
        }
        if (h.t) { var nt = naechster(h.t); if (nt) k.appendChild(el("div", "b-kz mono", pick("nächster Patch-Tag: ", "next patch day: ") + nt)); }
        if (h.t && !h.q && !h.a) k.appendChild(el("div", "dim fine", pick("Nur der Termin: Der Hersteller bietet keine offene Quelle, die sich ohne Konto abrufen lässt.", "Date only: the vendor offers no open source that can be fetched without an account.")));
        if (h.a && !h.t) k.appendChild(el("div", "dim fine", pick("Versionen und Lücken im Abschnitt weiter unten", "versions and flaws in the section further down")));
        if (h.a && h.t) k.appendChild(el("div", "dim fine", pick("Zahlen und Bewertung im Abschnitt weiter unten", "figures and rating in the section further down")));
        if (h.ohne) k.appendChild(el("div", "dim fine", pick("Noch keine offene Quelle angebunden. Angegriffenes steht trotzdem in der Liste darunter.", "No open source connected yet. Attacked flaws still appear in the list below.")));
        gr.appendChild(k);
      });
    }
    function zeigeZuerstBereich() {
      zbox.textContent = "";
      var mein = wahl === "alle" ? prl : prl.filter(function (p) { return p.bereich === wahl; });
      zbox.appendChild(el("h4", "mono b-h4", pick("Diese Woche zuerst patchen", "Patch first this week")));
      if (!mein.length) { zbox.appendChild(el("p", "dim fine", pick("Für diesen Bereich steht diese Woche nichts in der Rangliste. Die Rangliste nimmt nur Meldungen aus angebundenen Quellen auf.", "Nothing for this area in this week's ranking. The ranking only includes advisories from connected sources."))); return; }
      var ol = el("ol", "b-liste b-ol"); zbox.appendChild(ol);
      mein.slice(0, 5).forEach(function (p) {
        var li = el("li", ""); li.appendChild(link(p.link, p.cves && p.cves.length ? p.cves[0] : dx(p.titel)));
        var mk = { 1: "KEV", 2: pick("ausgenutzt", "exploited"), 3: "EPSS", 4: pick("kritisch", "critical") }[p.stufe];
        if (mk) { li.appendChild(document.createTextNode(" ")); li.appendChild(el("span", "fz-mk mono", mk)); }
        li.appendChild(document.createTextNode(" · " + dx(String(p.titel || "").replace(/^[A-Z]+-[\d:-]+:\s*/, "").slice(0, 90))));
        li.appendChild(el("span", "mono dim", " · " + p.quelle + " · " + datum(p.datum) + (wahl === "alle" && bname[p.bereich] ? " · " + bname[p.bereich] : "")));
        ol.appendChild(li);
      });
      if (mein.length > 5) zbox.appendChild(el("p", "mono dim fine", pick("und " + (mein.length - 5) + " weitere in der Liste „Diese Woche zuerst“ darunter", "and " + (mein.length - 5) + " more in the list “This week first” below")));
    }
    function zeige() {
      zeigeZuerstBereich();
      zeigeHersteller();
      Array.prototype.forEach.call(bt.children, function (b) { b.setAttribute("aria-pressed", String(b.dataset.b === wahl)); });
      var b = wahl === "alle" ? { name: "Alle Bereiche", name_en: "All areas", fuer: "die Rangliste über alles, ohne Filter", fuer_en: "the ranking across everything, unfiltered", anzahl: bl.reduce(function (n, x) { return n + x.anzahl; }, 0), anzahl_7: bl.reduce(function (n, x) { return n + (x.anzahl_7 || 0); }, 0) }
        : bl.filter(function (x) { return x.id === wahl; })[0], mein = wahl === "alle" ? neu.filter(function (e) { return e.bereich; }) : neu.filter(function (e) { return e.bereich === wahl; });
      info.textContent = (pick(b.fuer, b.fuer_en) ? pick(b.name, b.name_en) + ": " + pick(b.fuer, b.fuer_en) + ". " : "") + pick((wahl === "alle" ? prl.length : prn[wahl] || 0) + " in der Rangliste „zuerst patchen“. " + b.anzahl + " neu angegriffen in " + (d.fenster_tage || 30) + " Tagen, davon " + b.anzahl_7 + " in den letzten 7.", (wahl === "alle" ? prl.length : prn[wahl] || 0) + " in the “patch first” ranking. " + b.anzahl + " newly attacked in " + (d.fenster_tage || 30) + " days, " + b.anzahl_7 + " of them in the last 7.");
      ul.textContent = "";
      var alt = box.querySelector(".b-mehr"); if (alt) alt.parentNode.removeChild(alt);
      if (!mein.length) { ul.appendChild(el("li", "dim", pick("In diesem Bereich kam in den letzten " + (d.fenster_tage || 30) + " Tagen nichts neu als angegriffen in den Katalog. Das heißt nicht, dass es nichts zu patchen gibt.", "Nothing in this area was newly listed as attacked in the last " + (d.fenster_tage || 30) + " days. That does not mean there is nothing to patch."))); return; }
      mein.forEach(function (e) {
        var li = el("li", ""); li.appendChild(el("span", "mono dim", datum(e.hinzugefuegt) + " ")); li.appendChild(link(e.link, e.cve));
        li.appendChild(document.createTextNode(" · " + e.hersteller + " " + e.produkt));
        if (wahl === "alle" && bname[e.bereich]) li.appendChild(el("span", "mono dim", " · " + bname[e.bereich]));
        if (e.ransomware_bekannt) { li.appendChild(document.createTextNode(" ")); li.appendChild(el("span", "fz-mk mono rw", "Ransomware")); }
        li.appendChild(el("span", "mono dim", " · " + pick("Frist ", "deadline ") + datum(e.frist)));
        ul.appendChild(li);
      });
      /* Ohne Filter ist die Liste lang: die ersten zehn zeigen, der Rest per Knopf */
      if (wahl === "alle" && mein.length > 10) {
        Array.prototype.forEach.call(ul.children, function (li, i) { li.hidden = i >= 10; });
        var mb = el("button", "mono b-mehr", pick("alle " + mein.length + " zeigen", "show all " + mein.length)); mb.type = "button";
        mb.addEventListener("click", function () { Array.prototype.forEach.call(ul.children, function (li) { li.hidden = false; }); mb.parentNode.removeChild(mb); });
        ul.parentNode.insertBefore(mb, ul.nextSibling);
      }
    }
    (function () {
      var k = el("button", ""); knopfText(k, pick("Alle", "All"), prl.length, bl.reduce(function (n, x) { return n + x.anzahl; }, 0)); k.type = "button"; k.dataset.b = "alle";
      k.addEventListener("click", function () { wahl = "alle"; lsSet("cl_bereich", wahl); zeige(); }); bt.appendChild(k);
    })();
    bl.forEach(function (b) {
      var k = el("button", ""); knopfText(k, pick(b.name, b.name_en), prn[b.id] || 0, b.anzahl); k.type = "button"; k.dataset.b = b.id;
      k.addEventListener("click", function () { wahl = b.id; lsSet("cl_bereich", wahl); zeige(); }); bt.appendChild(k);
    });
    zeige();
  }

  function zeigeZuerst(pr) {
    var box = $("p-zuerst"); if (!box) return;
    if (!pr) { box.hidden = true; return; }
    box.textContent = "";
    box.appendChild(el("h3", "mono rd-t", pick("Diese Woche zuerst", "This week first")));
    box.appendChild(el("p", "mono dim fine", pick("KEV: nachweislich ausgenutzt (CISA) · EPSS: Wahrscheinlichkeit einer Ausnutzung in 30 Tagen · CVSS: Schwere von 0 bis 10", "KEV: proven to be exploited (CISA) · EPSS: probability of exploitation within 30 days · CVSS: severity from 0 to 10")));
    if (!pr.liste.length) {
      box.appendChild(el("p", "", pick("Aktuell nichts, was nach unseren Regeln vorgezogen werden muss: keine Lücke aus den Patches der letzten Wochen steht im CISA-KEV, wird vom Hersteller als ausgenutzt gemeldet oder hat eine hohe Ausnutzungswahrscheinlichkeit. Der normale Patchzyklus genügt.", "Currently nothing that needs to be moved up by our rules: no flaw from the recent patches is in the CISA KEV, reported as exploited by the vendor or has a high likelihood of exploitation. The normal patch cycle is enough.")));
    } else {
      var ol = el("ol", "p-rang"), olRest = el("ol", "p-rang"); olRest.start = 6;
      pr.liste.forEach(function (k, idx) {
        var li = el("li", "p-r" + k.stufe);
        var kopf = el("div", "p-rk");
        kopf.appendChild(el("span", "mono p-q", k.quelle));
        kopf.appendChild(link(k.link, k.cves && k.cves.length ? k.cves.slice(0, 3).join(", ") + (k.cves.length > 3 ? " …" : "") : k.titel));
        kopf.appendChild(el("span", "mono dim p-dt", datum(k.datum)));
        li.appendChild(kopf);
        li.appendChild(el("div", "p-t", dx(k.titel)));
        var det = el("details", "p-det"); det.appendChild(el("summary", "mono", pick("Warum Platz " + k.rang + "? Details", "Why rank " + k.rang + "? Details")));
        if (k.betrifft && k.betrifft !== k.quelle) det.appendChild(el("div", "p-w", pick("Betrifft: ", "Affects: ") + dx(k.betrifft)));
        det.appendChild(el("div", "p-w", pick("Warum zuerst: ", "Why first: ") + pick(k.grund, k.grund_en)));
        var bw = [];
        (k.cvss || []).forEach(function (c) { bw.push("CVSS " + String(c.score).replace(".", pick(",", ".")) + ((k.cves || []).length > 1 || k.cvss.length > 1 ? " (" + c.cve + ")" : "")); });
        if (typeof k.epss === "number") bw.push("EPSS\u00a0" + (k.epss >= 0.995 && k.epss < 1 ? ">\u00a099" : Math.round(k.epss * 100)) + "\u00a0%");
        var bwz = el("div", "p-w mono", pick("Bewertung: ", "Scores: ") + (bw.length ? bw.join(" · ") : pick("CVSS noch nicht verfügbar", "CVSS not available yet")) + (k.cves && k.cves.length > 3 ? " …" : ""));
        bwz.title = pick("CVSS: Schwere einer Lücke von 0 bis 10, vergeben vom Hersteller oder der NVD. EPSS: geschätzte Wahrscheinlichkeit, dass die Lücke in den nächsten 30 Tagen ausgenutzt wird (FIRST). KEV: Liste nachweislich ausgenutzter Lücken (CISA).", "CVSS: severity of a flaw from 0 to 10, assigned by the vendor or the NVD. EPSS: estimated probability that the flaw is exploited within the next 30 days (FIRST). KEV: list of flaws proven to be exploited (CISA).");
        li.appendChild(bwz);
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
    host.appendChild(el("label", "lbl", pick("Nur meine Produkte anzeigen", "Show only my products"))).setAttribute("for", "p-filter");
    var inp = el("input", "filter mono"); inp.id = "p-filter"; inp.type = "search"; inp.autocomplete = "off"; inp.placeholder = pick("z. B. windows 11, outlook, ubuntu, cisco", "e.g. windows 11, outlook, ubuntu, cisco"); inp.value = lsGet("cl_filter") || "";
    host.appendChild(inp);
    host.appendChild(el("p", "dim fine", pick("Produkte oder Hersteller eintippen, getrennt durch Komma, zum Beispiel windows 11, cisco. Die Liste darunter zeigt dann nur Passendes. Mit dem Kästchen vor einem Eintrag hakst du Erledigtes ab. Die sichtbare Liste kannst du kopieren oder exportieren.", "Type products or vendors, separated by commas, for example windows 11, cisco. The list below then shows only matches. Use the box in front of an entry to tick off what is done. You can copy or export the visible list.")));
    var info = el("p", "mono dim fine"); info.setAttribute("aria-live", "polite"); host.appendChild(info);
    var bt = el("div", "p-btns mono"); host.appendChild(bt);
    host.appendChild(el("p", "mono dim fine", pick("Dein Filter und deine Haken werden nur in diesem Browser gespeichert, nichts wird gesendet.", "Your filter and ticks are stored only in this browser, nothing is sent.")));
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
      info.textContent = (ts.length ? pick("Treffer: ", "Matches: ") + n + pick(" von ", " of ") + alle.length : alle.length + pick(" Einträge", " entries")) + " · " + erl + pick(" erledigt", " done");
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
      /* Zellen, die mit = + - @ oder einem Steuerzeichen beginnen, liest Excel als Formel: Hochkomma davor macht Text daraus */
      function q(x) { var t = String(x == null ? "" : x); if (/^[=+\-@\t\r]/.test(t)) t = "'" + t; return '"' + t.replace(/"/g, '""') + '"'; }
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
    box.appendChild(el("h3", "mono rd-t", pick("Chrome und Edge (Chromium)", "Chrome and Edge (Chromium)")));
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
    box.appendChild(el("p", "mono dim fine", pick("Die Chrome-Version in der Lösung ist die höchste Mindestversion aus den Meldungen dieses Monats, nicht die neueste Ausgabe. Die neuesten Versionen stehen darunter.", "The Chrome version in the fix is the highest minimum version from this month's notices, not the newest release. The newest versions are listed below.")));
    var q = el("p", "mono dim fine", pick("Quellen: Microsoft (Edge-Fixversion je CVE), Titel der Chromium-Meldungen (Chrome-Version). Mehr: ", "Sources: Microsoft (Edge fix version per CVE), titles of the Chromium notices (Chrome version). More: "));
    q.appendChild(link("https://learn.microsoft.com/deployedge/microsoft-edge-relnotes-security", pick("Edge-Sicherheitsupdates", "Edge security updates"))); q.appendChild(document.createTextNode(" · ")); q.appendChild(link("https://chromereleases.googleblog.com/", "Chrome Releases"));
    box.appendChild(q); box.hidden = false;
  }
  var d_life = null, d_prio = null, life_d = null;
  /* endoflife-Zyklus "11-25h2-e" zerlegen. ed: Anzeigename der Edition; null = nicht anzeigen (Home, IoT und anderes). */
  function winZyklus(c) {
    var m = /^(\d+)-([a-z0-9]+)(?:-(.+))?$/.exec(c || "");
    if (!m) return null;
    var ed = { "": "", w: "Pro", e: "Enterprise/Education", "e-lts": "LTSC" }[m[3] || ""];
    return { v: m[1], r: m[2], ed: ed === undefined ? null : ed };
  }
  /* Support-Zeilen je System. Windows 10/11: Enterprise/Education und Pro (alles, was Volumenaktivierung kann); Home steht nicht drin. */
  function supportTeile(life, key) {
    var zy = [], t = (life && life.produkte) || {}, m;
    if (/^Windows (10|11) /.test(key) && t.windows) {
      m = /^Windows (\d+) (\w+)$/.exec(key);
      if (m) zy = t.windows.zyklen.filter(function (z) { var c = winZyklus(z.zyklus); return c && c.v === m[1] && c.r === m[2].toLowerCase() && c.ed !== null; });
    } else if (/^Windows Server /.test(key) && t["windows-server"]) {
      var want = key.replace("Windows Server ", "").toLowerCase().replace(" r2", "-r2");
      zy = t["windows-server"].zyklen.filter(function (z) { return z.zyklus === want; });
    }
    return zy.map(function (z) {
      return { ed: (winZyklus(z.zyklus) || {}).ed || "", ende: z.eol, erw: z.erweitert && z.erweitert > z.eol ? z.erweitert : "" };
    }).sort(function (a, b) { return a.ende < b.ende ? 1 : -1; });
  }
  function supportText(life, key, heute, kurz) {
    return supportTeile(life, key).map(function (x) {
      var aus = x.ende < heute, pre = kurz ? (aus ? pick("beendet ", "ended ") : "") : (aus ? pick("Support beendet ", "Support ended ") : pick("Support bis ", "Support until "));
      return pre + datum(x.ende) + (x.ed ? " (" + x.ed + ")" : "") + (x.erw ? pick(" · ESU bis ", " · ESU until ") + datum(x.erw) : "");
    }).join(" · ");
  }
  /* Lebenszyklen: Support-Ende je Produkt und Version (data/patches/lifecycle.json, Quelle endoflife.date). Farbe nach Restzeit, Schwellen in RULES.md. */
  function lzKlasse(tage, erwTage) {
    if (tage === null) return "lz-ok";
    if (tage < 0) return erwTage !== null && erwTage >= 0 ? "lz-esu" : "lz-aus";
    return tage <= 182 ? "lz-6" : (tage <= 365 ? "lz-12" : "lz-ok");
  }
  function lzName(slug, p, z) {
    if (slug === "windows" || slug === "windows-server") return lifeName(slug, z).replace(/^Windows Server /, "").replace(/^Windows /, "");
    return z.zyklus + (z.name ? " · " + z.name : "") + (z.lts && slug !== "firefox" ? " LTS" : "");
  }
  function zeigeLebenszyklen(life) {
    var host = $("lz-liste"), qu = $("lz-quelle"); if (!host) return;
    host.textContent = "";
    var prod = (life && life.produkte) || {}, slugs = Object.keys(prod);
    if (!slugs.length) { host.appendChild(el("p", "dim", pick("Keine Lebenszyklus-Daten verfügbar.", "No lifecycle data available."))); return; }
    var heute = new Date(), t0 = Date.UTC(heute.getUTCFullYear(), heute.getUTCMonth(), heute.getUTCDate());
    function tage(dt) { return dt ? Math.round((Date.parse(dt + "T00:00:00Z") - t0) / TAG_MS) : null; }
    var gr = [["os", pick("Betriebssysteme", "Operating systems")], ["netz", pick("Netzwerk und Sicherheit", "Network and security")], ["browser", pick("Browser", "Browsers")], ["virt", pick("Virtualisierung und Terminalserver", "Virtualisation and terminal servers")]];
    gr.forEach(function (g) {
      var liste = slugs.filter(function (s) { return prod[s].gruppe === g[0]; }); if (!liste.length) return;
      host.appendChild(el("h3", "mono lz-g", g[1]));
      liste.forEach(function (slug) {
        var p = prod[slug], zy = (p.zyklen || []).filter(function (z) { return slug !== "windows" || (winZyklus(z.zyklus) && winZyklus(z.zyklus).ed !== null); });
        zy = zy.map(function (z) { return { z: z, t: tage(z.eol), e: tage(z.erweitert) }; });
        var kommend = zy.filter(function (x) { return x.t !== null && x.t >= 0; }).sort(function (a, b) { return a.t - b.t; });
        var rest = zy.filter(function (x) { return x.t === null || x.t < 0; }).sort(function (a, b) { return (b.t === null ? 1e9 : b.t) - (a.t === null ? 1e9 : a.t); });
        var d = el("details", "sek sub lz-p"), sm = el("summary", "");
        var h = el("h4", "mono", p.name); sm.appendChild(h);
        sm.appendChild(el("span", "mono dim lz-n", kommend.length ? pick("nächstes Ende ", "next end ") + datum(kommend[0].z.eol) + " (" + inTagen(kommend[0].t) + ")" : pick("kein Ende in Sicht", "no end in sight")));
        d.appendChild(sm);
        var sc = el("div", "p-pl-s"), tab = el("table", "mono p-pl-t tw-sp lz-t"), kp = el("thead", ""), tb = el("tbody", ""), th = el("tr", "");
        [pick("Version", "Version"), pick("Support-Ende", "End of support"), pick("Erweitert (ESU, ESM)", "Extended (ESU, ESM)"), pick("Restzeit", "Time left")].forEach(function (c) { th.appendChild(el("th", "", c)); });
        kp.appendChild(th); tab.appendChild(kp); tab.appendChild(tb);
        kommend.concat(rest).forEach(function (x) {
          var r = el("tr", lzKlasse(x.t, x.e));
          r.appendChild(el("td", "", lzName(slug, p, x.z)));
          var c2 = el("td", "", x.z.eol ? datum(x.z.eol) : pick("noch kein Datum genannt", "no date given yet")); c2.dataset.sort = x.z.eol ? String(Date.parse(x.z.eol + "T00:00:00Z")) : ""; r.appendChild(c2);
          var c3 = el("td", "", x.z.erweitert ? datum(x.z.erweitert) : "–"); c3.dataset.sort = x.z.erweitert ? String(Date.parse(x.z.erweitert + "T00:00:00Z")) : ""; r.appendChild(c3);
          var c4 = el("td", "lz-r", x.t === null ? pick("offen", "open") : (x.t < 0 ? (x.e !== null && x.e >= 0 ? pick("beendet, ESU läuft", "ended, ESU running") : pick("beendet", "ended")) : inTagen(x.t))); c4.dataset.sort = x.t === null ? "" : String(x.t); r.appendChild(c4);
          tb.appendChild(r);
        });
        sc.appendChild(tab); d.appendChild(sc); host.appendChild(d);
      });
    });
    if (qu) {
      qu.textContent = "";
      qu.appendChild(document.createTextNode(pick("Quelle: ", "Source: "))); qu.appendChild(link("https://endoflife.date", "endoflife.date"));
      qu.appendChild(document.createTextNode(life.meta ? pick(" (Herstellerangaben, Stand ", " (vendor data, as of ") + datum(String(life.meta.abgerufen_am).slice(0, 10)) + ")" : ""));
      var ohne = life.meta && life.meta.ohne_quelle;
      if (ohne && ohne.length) qu.appendChild(document.createTextNode(pick(" · Keine Quelle für: ", " · No source for: ") + ohne.join(", ") + pick(" (nichts geschätzt).", " (nothing estimated).")));
    }
  }
  /* Schnellzugriff oben in „Handeln“: je Kachel eine Zahl und ein Sprung. Nur Anzeige vorhandener Daten. */
  function zeigeSchnell(d) {
    var box = $("sw-schnell"); if (!box) return;
    var P = d.patches || {}, heute = new Date(), t0 = Date.UTC(heute.getUTCFullYear(), heute.getUTCMonth(), heute.getUTCDate()), k = [];
    function kachel(href, titel, info) { k.push({ href: href, t: titel, i: info }); }
    var mon = P.microsoft && P.microsoft.monate ? Object.keys(P.microsoft.monate).map(function (x) { return P.microsoft.monate[x]; }) : [];
    mon.sort(function (a, c) { return String(a.erste_veroeffentlichung).localeCompare(String(c.erste_veroeffentlichung)); });
    var m = mon[mon.length - 1];
    if (m && m.systeme && Object.keys(m.systeme).length) kachel("#p-pl", pick("Windows-Patch-Level", "Windows patch level"), Object.keys(m.systeme).length + pick(" Systeme · Update vom ", " systems · update of ") + datum(String(m.erste_veroeffentlichung).slice(0, 10)));
    var pr = P.prioritaet && P.prioritaet.liste;
    if (pr && pr.length) kachel("#k-zuerst", pick("Diese Woche zuerst", "This week first"), pr.length + pick(" Einträge", " entries"));
    var nx = termine(heute, 12).filter(function (x) { return x.ev.some(function (e) { return e.art === "ms"; }); })[0];
    if (nx) kachel("#k-ms", pick("Microsoft Patch Day", "Microsoft patch day"), inTagen(nx.tage) + " · " + new Date(nx.zeit).toLocaleDateString(window.I18N.locale, { timeZone: "UTC", day: "2-digit", month: "2-digit" }));
    var le = lifeEreignisse(P.lifecycle, t0, 365).sort(function (a, b) { return a.zeit - b.zeit; })[0];
    if (le) kachel("#lebenszyklen", pick("Lebenszyklen", "Lifecycles"), pick("nächstes Ende ", "next end ") + inTagen(le.tage));
    kachel("#termine", pick("Termine", "Dates"), pick("Patch-Kalender", "patch calendar"));
    box.textContent = "";
    k.forEach(function (x) { var a = el("a", "sw-k"); a.href = x.href; a.appendChild(el("b", "mono", x.t)); a.appendChild(el("span", "mono dim", x.i)); box.appendChild(a); });
    box.hidden = !k.length;
  }
  /* Patch-Level-Tabelle: eigener Kasten oben im Patch-Bereich, ohne Aufklappen sichtbar. */
  function zeigePatchLevel(ms, life) {
    var box = $("p-pl"); if (!box) return;
    var mon = ms && ms.monate ? Object.keys(ms.monate).map(function (k) { return ms.monate[k]; }) : [];
    mon.sort(function (a, c) { return String(a.erste_veroeffentlichung).localeCompare(String(c.erste_veroeffentlichung)); });
    var m = mon[mon.length - 1], s = m && m.systeme;
    if (!s || !Object.keys(s).length) { box.hidden = true; return; }
    box.textContent = ""; box.hidden = false;
    var heute = new Date().toISOString().slice(0, 10), wrap = box;
    var dtm = datum(String(m.erste_veroeffentlichung).slice(0, 10));
    var sm = el("summary", ""); sm.appendChild(el("h3", "mono", pick("Windows-Patch-Level: aktuelle Builds · Update vom " + dtm, "Windows patch level: current builds · update of " + dtm))); wrap.appendChild(sm);
    wrap.appendChild(el("p", "mono fine", pick("Nur Windows (Client und Server). So muss ein Rechner mindestens aktualisiert sein, um alle Lücken vom Patch Day " + monatName(m.id) + " zu schließen. Die Build-Nummer steht in winver bzw. ver.", "Windows only (client and server). This is the minimum a machine needs to close all flaws of the " + monatName(m.id) + " patch day. The build number is shown by winver or ver.")));
    var sc = el("div", "p-pl-s"), tab = el("table", "mono p-pl-t tw-sp"), kp = el("thead", ""), tb = el("tbody", ""), th = el("tr", "");
    [pick("System", "System"), pick("Aktuelle Build", "Current build"), "KB", pick("Ende Enterprise/Server", "End Enterprise/Server"), pick("Ende Pro", "End Pro"), "Ende LTSC", pick("ESU bis", "ESU until")].forEach(function (h) { th.appendChild(el("th", "", h)); });
    kp.appendChild(th); tab.appendChild(kp); tab.appendChild(tb);
    ["Windows 11", "Windows 10", "Windows Server"].forEach(function (gr) {
      Object.keys(s).filter(function (k) { return k.indexOf(gr + " ") === 0 && s[k].build; }).forEach(function (k) {
        var x = s[k], r = el("tr", "");
        r.appendChild(el("td", "", k)); r.appendChild(el("td", "", x.build));
        var td = el("td", ""); if (x.kb) { var a = link("https://support.microsoft.com/help/" + x.kb, "KB" + x.kb); td.appendChild(a); } r.appendChild(td);
        var tl = supportTeile(life, k), ent = tl.filter(function (e) { return e.ed === "Enterprise/Education" || e.ed === ""; })[0], pro = tl.filter(function (e) { return e.ed === "Pro"; })[0], lts = tl.filter(function (e) { return e.ed === "LTSC"; })[0];
        var esu = tl.map(function (e) { return e.erw; }).filter(Boolean).sort().pop();
        [ent && ent.ende, pro && pro.ende, lts && lts.ende, esu].forEach(function (dt, ci) {
          var c = el("td", dt && ci < 3 && dt < heute ? "lz-end" : "", dt ? datum(dt) : "–"); c.dataset.sort = dt ? String(Date.parse(dt + "T00:00:00Z")) : ""; r.appendChild(c);
        });
        tb.appendChild(r);
      });
    });
    sc.appendChild(tab); wrap.appendChild(sc);
    wrap.appendChild(el("p", "mono dim fine", pick("Build und KB gelten für alle Editionen; Home ist nicht aufgeführt. Stand des Patch Day (zweiter Dienstag); optionale Vorschau-Updates zwischendurch haben eine höhere Build. Ein Client mit niedrigerer Build hat den Patch nicht. Rot: Support schon beendet. Alle Support-Enden und Quellen unter /lebenszyklen.", "Build and KB apply to all editions; Home is not listed. Patch-day level (second Tuesday); optional preview updates in between have a higher build. A client with a lower build is missing the patch. Red: support already ended. All support dates and sources under /lifecycles.")));
    var qq = el("p", "mono dim fine", pick("Quellen: ", "Sources: ")); qq.appendChild(link("https://msrc.microsoft.com/update-guide", "Microsoft Security Response Center")); qq.appendChild(document.createTextNode(" · ")); qq.appendChild(link("https://endoflife.date", "endoflife.date") ); qq.appendChild(document.createTextNode(life && life.meta ? pick(" (Stand ", " (as of ") + datum(String(life.meta.abgerufen_am).slice(0, 10)) + ")" : "")); wrap.appendChild(qq);
  }
  function zeigeSysteme(box, m, vorm, life) {
    var s = m.systeme; if (!s || !Object.keys(s).length) return;
    var heute = new Date().toISOString().slice(0, 10), wrap = el("div", "p-sys");
    wrap.appendChild(el("h4", "mono rd-t", pick("Stand je System · " + monatName(m.id), "Status by system · " + monatName(m.id))));
    ["Windows 11", "Windows 10", "Windows Server"].forEach(function (gr) {
      var keys = Object.keys(s).filter(function (k) { return k.indexOf(gr + " ") === 0; });
      if (!keys.length) return;
      wrap.appendChild(el("div", "mono p-sg", gr));
      keys.forEach(function (k) {
        var x = s[k], v = vorm && vorm.systeme && vorm.systeme[k], r = el("div", "p-sr");
        var kopf = el("div", "p-sk"); kopf.appendChild(el("b", "mono p-sv", k.slice(gr.length + 1)));
        if (x.kb) { var a = link("https://support.microsoft.com/help/" + x.kb, "KB" + x.kb); a.className = "mono"; kopf.appendChild(a); }
        if (x.build) kopf.appendChild(el("span", "mono dim", "Build " + x.build));
        if (!x.kb && !x.build) kopf.appendChild(el("span", "mono dim", pick("kein Fix mit Build und KB in diesem Monat", "no fix with build and KB this month")));
        r.appendChild(kopf);
        r.appendChild(el("div", "mono fine p-ss", zahl(x.cves) + " CVEs · " + zahl(x.kritisch) + pick(" kritisch", " critical") + " · " + zahl(x.ausgenutzt) + pick(" ausgenutzt", " exploited") + (v ? " · " + pick("Vormonat ", "previous month ") + zahl(v.cves) : "")));
        var st = supportText(life, k, heute);
        if (st) r.appendChild(el("div", "mono fine dim p-ss", st));
        wrap.appendChild(r);
      });
    });
    var q = el("p", "mono dim fine", pick("Quellen: KB und Build je Version aus dem Patch-Day-Dokument des Microsoft Security Response Center (häufigste Angabe), Support-Ende von ", "Sources: KB and build per version from the Microsoft Security Response Center patch-day document (most common entry), end of support from "));
    q.appendChild(link("https://endoflife.date", "endoflife.date")); q.appendChild(document.createTextNode(life && life.meta ? pick(" (Stand ", " (as of ") + datum(String(life.meta.abgerufen_am).slice(0, 10)) + ")" : pick(" (aktuell nicht abrufbar)", " (currently unavailable)")));
    wrap.appendChild(q); box.appendChild(wrap);
  }
  function zeigeMsPrio(box, pr) {
    var k = ((pr && pr.liste) || []).filter(function (c) { return c.quelle === "Microsoft" && /Windows/.test(c.betrifft || ""); });
    if (!k.length) return;
    function sorte(c) { var b = c.betrifft || ""; return /Windows Server/.test(b) ? "server" : (/Windows 1[01]/.test(b) ? "client" : ""); }
    var wrap = el("div", "p-prio");
    wrap.appendChild(el("h4", "mono rd-t", pick("Zuerst patchen · Microsoft Windows", "Patch first · Microsoft Windows")));
    [["server", pick("Server", "Servers")], ["client", pick("Arbeitsplätze (Windows 10/11)", "Workstations (Windows 10/11)")]].forEach(function (gr) {
      var li = k.filter(function (c) { return sorte(c) === gr[0]; });
      wrap.appendChild(el("div", "mono p-sg", gr[1] + " · " + li.length));
      if (!li.length) { wrap.appendChild(el("p", "mono dim fine", pick("Nichts in der Prioritätsliste.", "Nothing in the priority list."))); return; }
      var ol = el("ol", "p-akt");
      li.slice(0, 3).forEach(function (c) {
        var it = el("li", ""); it.appendChild(link(c.link, c.cves && c.cves[0] ? c.cves[0] : c.titel));
        it.appendChild(document.createTextNode(" · " + dx(c.titel) + " · " + pick(c.grund, c.grund_en || c.grund)));
        ol.appendChild(it);
      });
      wrap.appendChild(ol);
      if (li.length > 3) wrap.appendChild(el("p", "mono dim fine", pick("+ " + (li.length - 3) + " weitere in „Diese Woche zuerst patchen“.", "+ " + (li.length - 3) + " more in “Patch this week first”.")));
    });
    box.appendChild(wrap);
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
    var bw = el("div", "p-bew"); bw.appendChild(el("span", "p-badge " + dr[0], dr[1] + (b.dringlichkeit === "dringend" && m.ausgenutzt ? pick(" · " + m.ausgenutzt + " bereits ausgenutzt", " · " + m.ausgenutzt + " already exploited") : "")));
    bw.appendChild(el("span", "", pick(b.groesse, b.groesse_en) + (b.verhaeltnis_median ? " · " + (window.I18N.lang === "en" ? "" : "das ") + b.verhaeltnis_median.toLocaleString(window.I18N.locale) + pick("-Fache des Medians der Vormonate (", "x the median of earlier months (") + zahl(b.median_vormonate) + ")" : "")));
    box.appendChild(bw);
    var g = el("div", "p-kpis");
    g.appendChild(kpi(zahl(m.cves), "CVEs")); g.appendChild(kpi(zahl(m.schwere.Critical), pick("kritisch", "critical")));
    g.appendChild(kpi(zahl(m.ausgenutzt), pick("ausgenutzt", "exploited"), m.ausgenutzt > 0 ? "warn" : ""));
    g.appendChild(kpi(zahl(m.oeffentlich_bekannt), pick("öffentlich bekannt", "publicly disclosed")));
    g.appendChild(kpi(zahl(m.im_kev), pick("davon im KEV", "of them in KEV"), m.im_kev > 0 ? "warn" : ""));
    box.appendChild(g);
    var nx = termine(new Date(), 12).filter(function (x) { return x.ev.some(function (e) { return e.art === "ms"; }); })[0];
    if (nx) box.appendChild(el("p", "mono p-nx", pick("Nächster Patch Day: ", "Next patch day: ") + new Date(nx.zeit).toLocaleDateString(window.I18N.locale, { timeZone: "UTC", weekday: "short", day: "2-digit", month: "2-digit", year: "numeric" }) + " · " + inTagen(nx.tage) + pick(" (Microsoft veröffentlicht die Inhalte erst an diesem Tag)", " (Microsoft publishes the contents only on that day)")));
    zeigeSysteme(box, m, monate[monate.length - 2], d_life);
    zeigeMsPrio(box, d_prio);
    var emp = el("p", "p-emp"); emp.appendChild(el("b", "mono p-emp-k", pick("Empfehlung", "Recommendation"))); emp.appendChild(document.createTextNode(pick(b.empfehlung, b.empfehlung_en))); box.appendChild(emp);
    if (b.aktionen && b.aktionen.length) {
      var al = el("ol", "p-akt");
      b.aktionen.forEach(function (x) {
        var li = el("li", ""); li.appendChild(link("https://msrc.microsoft.com/update-guide/vulnerability/" + x.cve, x.cve));
        li.appendChild(document.createTextNode(" · " + dx(x.titel) + (x.betrifft ? " · " + pick("betrifft ", "affects ") + dx(x.betrifft) : "")));
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
    Object.keys(m.familien || {}).slice(0, 6).forEach(function (k) { fam.appendChild(el("div", "p-z mono", dx(k) + ": " + m.familien[k])); });
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
  /* Weitere Browser neben Chromium: nur Firmenversionen (Firefox ESR); wo keine offene Quelle angebunden ist, steht „keine Daten“ */
  function zeigeBrowser(hs) {
    var box = $("p-browser"); if (!box) return;
    var qs = hs && hs.quellen ? hs.quellen : {}, chr = qs.chrome && qs.chrome.kanaele ? qs.chrome.kanaele : {}, saf = qs.apple && qs.apple.safari ? qs.apple.safari : null, moz = qs.mozilla && qs.mozilla.letzte ? qs.mozilla.letzte : [], app = qs.apple && qs.apple.letzte ? qs.apple.letzte : [];
    box.textContent = "";
    box.appendChild(el("h3", "mono rd-t", pick("Neueste Version je Browser", "Newest version per browser")));
    function zeile(name, fn) { var p = el("p", "", ""); p.appendChild(el("b", "mono", name + ": ")); fn(p); box.appendChild(p); }
    function kanal(name, k, zusatz) {
      zeile(name, function (p) {
        if (!k) { p.appendChild(document.createTextNode(pick("keine Daten (Chrome-Releases-Blog nicht abrufbar). ", "no data (Chrome Releases blog not reachable). "))); return; }
        p.appendChild(link(k.link, k.version)); p.appendChild(document.createTextNode(" (" + datum(k.datum) + ")" + zusatz));
      });
    }
    kanal(pick("Chrome Stable", "Chrome Stable"), chr.Stable, pick(". Windows, Mac und Linux; Chromium-Lücken siehe oben.", ". Windows, Mac and Linux; Chromium flaws see above."));
    kanal(pick("Chrome Extended Stable (Firmen)", "Chrome Extended Stable (organisations)"), chr["Extended Stable"], pick(". Nur verwaltetes Chrome auf Windows und Mac, per Richtlinie. Laut Google dieselben Sicherheitsfixes wie Stable, wo technisch möglich, aber mit älterem Versionsstand.", ". Managed Chrome on Windows and Mac only, enabled by policy. According to Google the same security fixes as Stable where technically possible, but on an older version."));
    zeile(pick("Firefox ESR (Mozilla)", "Firefox ESR (Mozilla)"), function (p) {
      var linien = {}, reihe = [];
      moz.forEach(function (x) { var m = /Firefox ESR (\d+)(\.\d+)*/.exec(x.titel || ""); if (!m || linien[m[1]]) return; linien[m[1]] = 1; reihe.push({ v: /Firefox ESR (\d+(?:\.\d+)*)/.exec(x.titel)[1], x: x }); });
      if (!reihe.length) { p.appendChild(document.createTextNode(pick("keine Daten.", "no data."))); return; }
      p.appendChild(document.createTextNode(pick("Die ESR-Ausgabe ist für Organisationen gedacht. Aktueller Stand laut Mozilla: ", "The ESR edition is meant for organisations. Current level according to Mozilla: ")));
      reihe.forEach(function (r, i) { if (i) p.appendChild(document.createTextNode(", ")); p.appendChild(link(r.x.link, "ESR " + r.v)); p.appendChild(document.createTextNode(" (" + datum(r.x.datum) + ")")); });
      p.appendChild(document.createTextNode(pick(". In der jeweiligen ESR-Linie sollte mindestens diese Version laufen.", ". Each ESR line should run at least this version.")));
    });
    zeile("Opera", function (p) {
      p.appendChild(document.createTextNode(pick("Baut auf Chromium, die Chromium-Lücken oben gelten dort ebenfalls. Opera liefert die Fixes mit eigenen Versionsnummern. Keine offene Quelle angebunden: keine Daten. ", "Built on Chromium, so the Chromium flaws above apply there too. Opera ships the fixes with its own version numbers. No open source connected: no data. ")));
      p.appendChild(link("https://blogs.opera.com/desktop/", pick("Opera-Versionshinweise", "Opera release notes")));
    });
    zeile(pick("Safari (Apple)", "Safari (Apple)"), function (p) {
      if (saf) { p.appendChild(link(saf.link, saf.titel)); p.appendChild(document.createTextNode(" (" + datum(saf.datum) + pick("). Kommt mit Apples System-Updates.", "). Comes with Apple's system updates."))); return; }
      p.appendChild(document.createTextNode(pick("Kommt mit Apples System-Updates. In der Apple-Liste, die wir abrufen, steht kein Safari-Eintrag: keine Daten. ", "Comes with Apple's system updates. The Apple list we fetch holds no Safari entry: no data. ")));
      p.appendChild(link("https://support.apple.com/en-us/100100", pick("Apple Security Releases", "Apple Security Releases")));
    });
    box.appendChild(el("p", "mono dim fine", pick("Quellen: Chrome-Releases-Blog (Google), Mozilla Security Advisories, Apple Security Releases, Opera. Nichts ist geschätzt.", "Sources: Chrome Releases blog (Google), Mozilla Security Advisories, Apple Security Releases, Opera. Nothing is estimated.")));
    box.hidden = false;
  }
  function zeigeHersteller(hs) {
    zeigeBrowser(hs);
    var alle = hs && hs.quellen ? Object.keys(hs.quellen).map(function (k) { return hs.quellen[k]; }) : [];
    herstellerTabelle($("p-hv"), alle.filter(function (q) { return q.typ === "hersteller" && q.id !== "chrome"; }), pick("Hersteller: Netzwerk, Anwendungen, Browser, Apple", "Vendors: network, applications, browsers, Apple"), true);
    herstellerTabelle($("p-hs"), alle.filter(function (q) { return q.typ !== "hersteller"; }), pick("Linux-Distributionen", "Linux distributions"), false);
  }
  function herstellerTabelle(box, qs, titel, mitAdobe) {
    if (!box) return;
    if (!qs.length) { box.hidden = true; return; }
    box.textContent = "";
    box.appendChild(el("h3", "mono rd-t", titel));
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
    box.appendChild(el("p", "mono dim fine", pick("Meldungen und CVEs zählen Verschiedenes: Eine Meldung kann mehrere CVEs schließen, mehrere Meldungen können dieselbe CVE betreffen, und manche nennen keine. Die Hersteller schneiden ihre Meldungen unterschiedlich zu, die Zahlen sind deshalb nicht direkt vergleichbar.", "Advisories and CVEs count different things: one advisory can fix several CVEs, several advisories can cover the same CVE, and some name none. Vendors slice their advisories differently, so the numbers are not directly comparable.")));
    qs.forEach(function (q) {
      if (!q.letzte || !q.letzte.length) return;
      var d = el("details", "rd-det"); d.appendChild(el("summary", "mono", q.name + pick(": letzte Meldungen", ": latest advisories")));
      var ul = el("ul", "p-liste");
      q.letzte.slice(0, 6).forEach(function (x) {
        var li = el("li", ""); li.appendChild(el("span", "mono dim", datum(x.datum) + " ")); li.appendChild(link(x.link, dx(x.titel) + (x.schwere ? " (" + dx(x.schwere) + ")" : ""))); ul.appendChild(li);
      });
      d.appendChild(ul); box.appendChild(d);
    });
    var ad = el("p", "mono dim fine", pick("Adobe: keine maschinenlesbare Quelle ohne Konto, daher nur Verweis auf die ", "Adobe: no machine-readable source without an account, so a link only to the "));
    ad.appendChild(link("https://www.adobe.com/trust/security/bulletins-and-advisories.html", pick("Adobe-Sicherheitshinweise", "Adobe security bulletins")));
    ad.appendChild(document.createTextNode(pick(" (Patch Day: zweiter Dienstag, siehe Patch-Kalender). SAP-Hinweise erreichst du nur mit SAP-for-Me-Konto, hier steht die Nummer.", " (patch day: second Tuesday, see patch calendar). SAP notes need an SAP for Me account, only the number is shown here.")));
    if (mitAdobe) box.appendChild(ad);
    box.appendChild(el("p", "mono dim fine", pick("Nur Zählung und Verweise auf die Meldungen der Hersteller, keine Texte. Schweregrade stammen von den Herstellern und fehlen, wo sie nicht geliefert werden (zum Beispiel bei Ubuntu und Debian).", "Counts and links to the vendors' advisories only, no texts. Severity comes from the vendors and is missing where they do not provide it (for example Ubuntu and Debian).")));
    box.hidden = false;
  }

  // Berichte je Monat, Quartal und Jahr: werden erst geladen, wenn der Abschnitt aufgeht
  (function () {
    var sek = $("k-berichte"), box = $("br-box"), wahl = $("br-wahl"), tabs = $("br-art"); if (!sek || !box || !wahl || !tabs) return;
    var daten = null, art = "monat", laedt = false;
    var z1 = function (v, n) { return v.toLocaleString(window.I18N.locale, { minimumFractionDigits: n, maximumFractionDigits: n }); };
    var kurz = function (iso) { return new Date(iso).toLocaleDateString(window.I18N.locale, { timeZone: "UTC", day: "numeric", month: "short" }); };
    var mitVz = function (v, n) { return v === null || v === undefined ? "–" : (v > 0 ? "+" : v < 0 ? "−" : "±") + z1(Math.abs(v), n); };
    function kopiere(t, b) {
      var fertig = function () { var alt = b.textContent; b.textContent = pick("Kopiert", "Copied"); setTimeout(function () { b.textContent = alt; }, 1600); };
      if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(t).then(fertig, function () { }); return; }
      var ta = document.createElement("textarea"); ta.value = t; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); fertig(); } catch (e) { } document.body.removeChild(ta);
    }
    function kennzahl(name, wert, zusatz) { var k = el("div", "br-kz"); k.appendChild(el("span", "mono dim", name)); k.appendChild(el("strong", "mono", wert)); if (zusatz) k.appendChild(el("span", "dim", zusatz)); return k; }
    function zeige(b) {
      box.textContent = ""; if (!b) { box.appendChild(el("p", "dim", pick("Für diesen Zeitraum gibt es noch keinen abgeschlossenen Bericht.", "There is no completed report for this period yet."))); return; }
      var a = el("article", "br ra-" + b.stufe.ampel), kopf = el("div", "br-k");
      kopf.appendChild(el("h3", "", pick(b.titel, b.titel_en)));
      kopf.appendChild(el("span", "br-st mono", pick(b.stufe.name, b.stufe.name_en) + " · " + z1(b.mittel, 1)));
      a.appendChild(kopf);
      a.appendChild(el("p", "br-satz", pick(b.satz, b.satz_en)));
      var kn = el("div", "br-kn"), k1 = el("button", "mono", pick("Text kopieren", "Copy text")), k2 = el("button", "mono", pick("Link kopieren", "Copy link"));
      var link = location.origin + pick("/bericht/", "/en/bericht/") + b.id + "/";
      k1.type = k2.type = "button";
      k1.addEventListener("click", function () { kopiere(pick(b.satz, b.satz_en) + "\n\n" + link, k1); });
      k2.addEventListener("click", function () { kopiere(link, k2); });
      var k3 = el("a", "mono br-eig", pick("Eigene Seite", "Own page")); k3.href = pick("/bericht/", "/en/bericht/") + b.id + "/";
      kn.appendChild(k1); kn.appendChild(k2); kn.appendChild(k3); a.appendChild(kn);
      var vor = { monat: pick("Vormonat", "previous month"), quartal: pick("Vorquartal", "previous quarter"), jahr: pick("Vorjahr", "previous year") }[b.art];
      var kz = el("div", "br-kzs");
      kz.appendChild(kennzahl(pick("Mittel", "Average"), z1(b.mittel, 1), b.delta === null ? "" : mitVz(b.delta, 1) + pick(" zum ", " vs. ") + vor));
      kz.appendChild(kennzahl(pick("Höchststand", "High"), String(b.hoch.wert), kurz(b.hoch.datum)));
      kz.appendChild(kennzahl(pick("Tiefststand", "Low"), String(b.tief.wert), kurz(b.tief.datum)));
      kz.appendChild(kennzahl(pick("Stufenwechsel", "Level changes"), String(b.wechsel), b.tage + pick(" Tage", " days")));
      a.appendChild(kz);
      a.appendChild(el("p", "lbl mono", pick("Tage je Stufe", "Days per level")));
      var band = el("div", "br-band"), leg = el("p", "br-leg mono dim");
      b.je_stufe.forEach(function (s, i) {
        var seg = el("span", "sg ra-" + s.ampel); seg.style.width = (100 * s.tage / b.tage) + "%"; seg.title = pick(s.name, s.name_en) + ": " + s.tage; band.appendChild(seg);
        var l = el("span", "br-li"); var p = el("i", "sg ra-" + s.ampel); l.appendChild(p); l.appendChild(document.createTextNode(pick(s.name, s.name_en) + " " + s.tage)); leg.appendChild(l);
      });
      a.appendChild(band); a.appendChild(leg);
      if (b.bausteine.length) {
        a.appendChild(el("p", "lbl mono", pick("Bausteine", "Components")));
        var tw = el("div", "br-tab"), t = el("table"), th = el("thead"), tr = el("tr"), tb = el("tbody");
        [pick("Baustein", "Component"), pick("Mittel", "Average"), pick("Tage ≥ 1", "Days ≥ 1"), "Δ"].forEach(function (x) { tr.appendChild(el("th", "", x)); });
        th.appendChild(tr); t.appendChild(th);
        b.bausteine.forEach(function (c) {
          var r = el("tr"); r.appendChild(el("td", "", pick(c.name, c.name_en)));
          r.appendChild(el("td", "mono" + (c.mittel >= 1 ? " rw" : ""), z1(c.mittel, 2)));
          r.appendChild(el("td", "mono", c.ueber + " %")); r.appendChild(el("td", "mono dim", mitVz(c.delta, 2))); tb.appendChild(r);
        });
        t.appendChild(tb); tw.appendChild(t); a.appendChild(tw);
        a.appendChild(el("p", "br-leg2 dim", pick("Mittel: Messwert im Verhältnis zur Schwelle, 1 = Schwelle erreicht, wie im Pegel höchstens 2. Tage ≥ 1: Anteil der Tage an oder über der Schwelle. Δ: Veränderung des Mittels zum ", "Average: reading relative to its threshold, 1 = threshold reached, capped at 2 as in the gauge. Days ≥ 1: share of days at or above the threshold. Δ: change of the average vs. the ") + vor + "."));
      }
      if (b.logbuch.length) {
        a.appendChild(el("p", "lbl mono", pick("Logbuch im Zeitraum", "Logbook in this period")));
        var ul = el("ul", "br-lb"); b.logbuch.forEach(function (e) { var li = el("li"); li.appendChild(el("time", "mono dim", datum(e.datum) + " ")); li.appendChild(document.createTextNode(pick(e.titel, e.titel_en))); ul.appendChild(li); });
        a.appendChild(ul);
      }
      a.appendChild(el("p", "br-fuss mono dim", datum(b.von) + " – " + datum(b.bis) + " · " + (b.bis < daten.live_seit
        ? pick("zurückgerechnet aus den Archivdaten, ohne die Gruppe Externe Einschätzungen", "back-calculated from the archive data, without the group external assessments")
        : pick("ab " + datum(daten.live_seit) + " gespeicherter Tagesstand aller Bausteine, davor zurückgerechnet", "from " + datum(daten.live_seit) + " stored daily value of all components, back-calculated before"))));
      box.appendChild(a);
    }
    function fuelle(id) {
      var liste = daten.berichte.filter(function (b) { return b.art === art; });
      wahl.textContent = ""; liste.forEach(function (b) { var o = el("option", "", pick(b.titel, b.titel_en)); o.value = b.id; wahl.appendChild(o); });
      if (id) wahl.value = id;
      zeige(liste.filter(function (b) { return b.id === wahl.value; })[0] || liste[0]);
    }
    function setzeArt(a2, id) {
      art = a2; Array.prototype.forEach.call(tabs.querySelectorAll("button"), function (b) { var an = b.getAttribute("data-art") === art; b.setAttribute("aria-selected", an ? "true" : "false"); b.tabIndex = an ? 0 : -1; });
      if (daten) fuelle(id);
    }
    function lade(id) {
      if (daten || laedt) return; laedt = true; box.textContent = ""; box.appendChild(el("p", "dim", pick("Lädt …", "Loading …")));
      fetch("/data/berichte.json", { cache: "no-cache" }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (d) {
        daten = d;
        var bi = document.querySelector('[data-t="br_intro"]');
        if (bi && d.modell && !bi.getAttribute("data-mv")) { bi.textContent = bi.textContent + " " + pick("Modell Version ", "Model version ") + d.modell + "."; bi.setAttribute("data-mv", "1"); }
        var ziel = id && d.berichte.filter(function (b) { return b.id === id; })[0];
        if (ziel) setzeArt(ziel.art, ziel.id); else fuelle();
      }).catch(function () { laedt = false; box.textContent = ""; box.appendChild(el("p", "dim", pick("Die Berichte ließen sich nicht laden.", "The reports could not be loaded."))); });
    }
    tabs.addEventListener("click", function (e) { var b = e.target.closest ? e.target.closest("button[data-art]") : null; if (b) setzeArt(b.getAttribute("data-art")); });
    wahl.addEventListener("change", function () { fuelle(wahl.value); });
    sek.addEventListener("toggle", function () { if (sek.open) lade(); });
    var m = /[?&]bericht=([0-9]{4}(?:-(?:Q[1-4]|[01][0-9]))?)(?:&|$)/.exec(location.search);
    if (m) { aufklappen(sek); sek.open = true; lade(m[1]); setTimeout(function () { sek.scrollIntoView(); }, 300); }
  })();

  function zeigeLogbuch(liste) {
    var box = $("lb-liste"), sek = $("logbuch"); if (!box) return; box.textContent = "";
    if (sek) sek.hidden = !liste.length;
    var art = { erkenntnis: pick("Erkenntnis", "Finding"), ereignis: pick("Ereignis", "Event"), modell: pick("Modell", "Model") };
    liste.forEach(function (e) {
      var a = el("article", "lb lb-" + e.art), kopf = el("div", "lb-k mono");
      kopf.appendChild(el("time", "", datum(e.datum))); kopf.appendChild(el("span", "lb-art", art[e.art] || e.art));
      a.appendChild(kopf);
      a.appendChild(el("h3", "lb-t", pick(e.titel, e.titel_en)));
      a.appendChild(el("p", "", pick(e.text, e.text_en)));
      var bl = pick(e.belege, e.belege_en) || [];
      if (bl.length) { var ul = el("ul", "lb-b mono dim"); bl.forEach(function (b) { ul.appendChild(el("li", "", b)); }); a.appendChild(ul); }
      box.appendChild(a);
    });
  }

  function zeigeBalken(sc, box) {
    var bs = [];
    sc.modell_gruppen.forEach(function (g) { g.bausteine.forEach(function (b) { if (typeof b.ausschlag === "number") bs.push(b); }); });
    if (!bs.length) return;
    var NS = "http://www.w3.org/2000/svg", W = 540, bo = sc.beobachtung || [], H = 36 + (bs.length + bo.length) * 34, X0 = 150, X1 = 500, max = 2;
    var svg = document.createElementNS(NS, "svg"); svg.setAttribute("viewBox", "0 0 " + W + " " + H); svg.setAttribute("width", "100%"); svg.setAttribute("role", "img"); svg.setAttribute("class", "rd-balken");
    var mk = function (tag, a, t) { var e = document.createElementNS(NS, tag); for (var k in a) e.setAttribute(k, a[k]); if (t !== undefined) e.textContent = t; svg.appendChild(e); return e; };
    var mono = { "font-family": "ui-monospace,Menlo,Consolas,monospace", "font-size": "12", fill: "#9aa7b4" };
    var xs = function (v) { return X0 + (Math.min(v, max) / max) * (X1 - X0); };
    mk("title", {}, pick("Bausteine als Balken, Schwelle bei 1,0", "Components as bars, threshold at 1.0"));
    bs.forEach(function (b, i) {
      var y = 20 + i * 34, over = b.ausschlag >= 1;
      mk("text", Object.assign({ x: X0 - 8, y: y + 14, "text-anchor": "end" }, mono), pick(b.name, b.name_en));
      mk("rect", { x: X0, y: y, width: X1 - X0, height: 20, fill: "#1a222b" });
      mk("rect", { x: X0, y: y, width: xs(b.ausschlag) - X0, height: 20, fill: over ? "#e3b341" : "#4fa57a" });
      mk("text", Object.assign({ x: b.ausschlag > 1.8 ? X1 - 6 : xs(b.ausschlag) + 6, y: y + 14 }, mono, b.ausschlag > 1.8 ? { fill: "#0d1117", "font-weight": 700, "text-anchor": "end" } : { fill: "#e6edf3" }), b.ausschlag.toLocaleString(window.I18N.locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
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
    box.appendChild(el("p", "mono dim fine", bo.length ? pick(bs.length + " Bausteine zählen im Pegel, " + bo.length + " weitere werden beobachtet und zählen erst mit eigener Schwelle.", bs.length + " components count in the gauge, " + bo.length + " more are observed and count only once they have a threshold.") : pick("Alle " + bs.length + " Bausteine zählen im Pegel. Gelb: an oder über der Schwelle. Für den Pegel zählt jeder Ausschlag höchstens mit 2,0.", "All " + bs.length + " components count in the gauge. Yellow: at or above threshold. For the gauge each reading counts at most 2.0.")));
  }

  function zeigeModell(sc) {
    var box = $("rd-modell"); if (!box) return; box.textContent = "";
    if (!sc || !sc.modell_gruppen) return;
    var bb = $("rd-balken") || box; if (bb !== box) bb.textContent = "";
    zeigeBalken(sc, bb);
    // Ein kompakter Block statt zweier Listen: je Gruppe eine Zeile mit Gruppenwert und Leitfrage, darunter die Bausteine als Marken
    var fmt = function (v) { return v.toLocaleString(window.I18N.locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); };
    var gw = {}; (sc.gruppen || []).forEach(function (x) { gw[x.id] = x.ausschlag; });
    var tab = el("div", "gr-tab");
    sc.modell_gruppen.forEach(function (g) {
      if (!g.bausteine.length) return;
      var z = el("div", "gr-z"), kopf = el("div", "gr-k mono");
      kopf.appendChild(el("b", "", pick(g.name, g.name_en)));
      if (typeof gw[g.id] === "number") kopf.appendChild(el("span", "gr-w" + (gw[g.id] >= 1 ? " an" : ""), fmt(gw[g.id])));
      z.appendChild(kopf);
      if (g.frage) z.appendChild(el("div", "dim gr-frage", pick(g.frage, g.frage_en)));
      var marken = el("div", "gr-m mono");
      g.bausteine.forEach(function (b) {
        var hat = typeof b.ausschlag === "number";
        marken.appendChild(el("span", "gr-b" + (hat ? (b.ausschlag >= 1 ? " an" : " aus") : ""), pick(b.name, b.name_en) + " " + (hat ? fmt(b.ausschlag) : "–")));
      });
      z.appendChild(marken); tab.appendChild(z);
    });
    box.appendChild(tab);
    var pg = window.__pegel;
    if (pg && pg.modell) {
      var mv = el("details", "rd-det rd-ver");
      mv.appendChild(el("summary", "mono", pick("Modell Version ", "Model version ") + pg.modell + (pg.modell_pruefsumme ? " · " + pick("Prüfsumme ", "checksum ") + pg.modell_pruefsumme : "")));
      var ml = el("ul", "p-liste");
      (pg.modell_aenderungen || []).slice().reverse().forEach(function (x) { ml.appendChild(el("li", "mono fine", x.version + " (" + x.datum + "): " + pick(x.text, x.text_en))); });
      mv.appendChild(ml);
      mv.appendChild(el("p", "mono dim fine", pick("Jede Änderung an Bausteinen, Schwellen oder Stufen bekommt eine neue Version und einen Eintrag hier und im Logbuch. Frühere Werte werden dabei mit dem neuen Modell neu gerechnet; die seit dem Start gespeicherten Tageswerte bleiben unverändert.", "Every change to components, thresholds or levels gets a new version and an entry here and in the logbook. Earlier values are then recomputed with the new model; the daily values stored since launch stay unchanged.")));
      box.appendChild(mv);
    }
    box.appendChild(el("p", "mono dim fine", pick("Zahl = Messwert im Verhältnis zur Schwelle, 1,00 heißt Schwelle erreicht (gelb: an oder über der Schwelle). Erst wird je Gruppe gemittelt, dann über die Gruppen; jeder Baustein zählt höchstens mit 2,00.", "Number = reading relative to the threshold, 1.00 means threshold reached (yellow: at or above). Averaged within each group first, then across groups; each component counts at most 2.00.")));
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

  /* Externe Links öffnen in einem neuen Tab, damit die Lage offen bleibt. */
  document.addEventListener("click", function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
    if (a && /^https?:$/.test(a.protocol) && a.host !== location.host && !a.target) { a.target = "_blank"; a.rel = "noopener"; }
  }, true);

  // Handy-Menü: Knopf „Menü“ klappt alle Punkte untereinander auf (bis 899 px per CSS)
  (function () {
    var le = document.querySelector(".leiste"), ni = le && le.querySelector(".navin"); if (!ni) return;
    var b = document.createElement("button"); b.type = "button"; b.className = "menue-knopf mono"; b.id = "menue-knopf";
    b.setAttribute("aria-expanded", "false"); b.setAttribute("aria-controls", "menue-panel");
    var t = document.createElement("span"); b.appendChild(document.createTextNode("☰ ")); b.appendChild(t);
    ni.insertBefore(b, ni.firstChild);
    var nl = ni.querySelector(".nav-links"); if (nl) nl.id = "menue-panel";
    function setz(o) { le.classList.toggle("menue-offen", o); b.setAttribute("aria-expanded", o ? "true" : "false"); t.textContent = o ? pick("Schließen", "Close") : pick("Menü", "Menu"); }
    setz(false);
    b.addEventListener("click", function () { setz(!le.classList.contains("menue-offen")); });
    le.addEventListener("click", function (ev) { var a = ev.target.closest && ev.target.closest(".nav-links a"); if (a) setz(false); });
    document.addEventListener("keydown", function (ev) { if (ev.key === "Escape") setz(false); });
  })();
})();
