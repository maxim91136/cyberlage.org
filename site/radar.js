/* Konsens-Radar, Radar-Grafik und Ausblick. Aus app.js ausgelagert; nutzt die Helfer aus window.CL. */
(function () {
  "use strict";
  window.CL = window.CL || {};
  var $ = function () { return window.CL.$.apply(null, arguments); };
  var pick = function () { return window.CL.pick.apply(null, arguments); };
  var el = function () { return window.CL.el.apply(null, arguments); };
  var txt = function () { return window.CL.txt.apply(null, arguments); };
  var zahl = function () { return window.CL.zahl.apply(null, arguments); };
  var datum = function () { return window.CL.datum.apply(null, arguments); };
  var link = function () { return window.CL.link.apply(null, arguments); };
  var liste = function () { return window.CL.liste.apply(null, arguments); };
  var zeichneScope = function () { return window.CL.zeichneScope.apply(null, arguments); };
  var zeigeModell = function () { return window.CL.zeigeModell.apply(null, arguments); };
  function zeigeKonsens(r) {
    var k = r && r.konsens, box = $("rd-signale"); box.textContent = "";
    if (!k || !k.bewertet) { $("rd-kon").textContent = txt("keine"); return; }
    var alleS = (k.signale || []).filter(function (x) { return typeof x.ausschlag === "number"; }), ueberS = alleS.filter(function (x) { return x.ausschlag >= 1; }).length;
    var satz = pick(ueberS + " von " + alleS.length + " Bausteinen liegen an oder über ihrer Schwelle.", ueberS + " of " + alleS.length + " components are at or above their threshold.");
    $("rd-kon").textContent = satz + " " + pick("Stand ", "As of ") + datum(r.abgerufen_am) + ".";
    if ($("rd-kurz")) $("rd-kurz").textContent = satz;
    var sc = k.score, sb = $("rd-score"); sb.textContent = "";
    var ampel = (sc.stufe && sc.stufe.ampel) || "", rb = $("radar"), fzb = $("fazit");
    ["ruhig", "unauffaellig", "angespannt", "hoch", "ausserordentlich"].forEach(function (a) { [sb, rb, fzb].forEach(function (n) { if (n) n.classList.remove("ra-" + a); }); });
    if (ampel) [sb, rb, fzb].forEach(function (n) { if (n) n.classList.add("ra-" + ampel); });
    if (sc) {
      var szl = $("stufe-zahl");
      if (szl) {
        szl.textContent = ""; szl.appendChild(document.createTextNode(String(sc.wert))); szl.appendChild(el("small", "", " / 100"));
        if (sc.signale < sc.von) szl.appendChild(el("small", "sz-n", pick("aus " + sc.signale + " von " + sc.von + " Bausteinen", "from " + sc.signale + " of " + sc.von + " components")));
        szl.setAttribute("aria-label", pick("Dreier-Pegel " + sc.wert + " von 100", "Dreier Gauge " + sc.wert + " out of 100")); szl.hidden = false;
      }
      var tx = el("div", "st");
      var st0 = (window.CL.skala() && window.CL.skala().stufen) || [], ix = -1; st0.forEach(function (x, i) { if (ix < 0 && sc.wert < x.bis) ix = i; });
      if (ix >= 0) {
        var teile = [];
        if (ix < st0.length - 1) teile.push(pick((st0[ix].bis - sc.wert) + (st0[ix].bis - sc.wert === 1 ? " Punkt" : " Punkte") + " bis „" + st0[ix + 1].name + "“", (st0[ix].bis - sc.wert) + (st0[ix].bis - sc.wert === 1 ? " point" : " points") + " to “" + st0[ix + 1].name_en + "”"));
        if (ix > 0) teile.push(pick((sc.wert - st0[ix - 1].bis + 1) + " über der Grenze zu „" + st0[ix - 1].name + "“", (sc.wert - st0[ix - 1].bis + 1) + " above the limit to “" + st0[ix - 1].name_en + "”"));
        var lv = ((window.__pegel || {}).reihe_k || {}).live || {}, tg = Object.keys(lv).sort(), gest = tg.length > 1 ? lv[tg[tg.length - 2]][0] : null;
        if (typeof gest === "number") teile.push(pick("am Vortag " + gest, "previous day " + gest));
        if (teile.length) tx.appendChild(el("span", "mono", pick("Abstand: ", "Margin: ") + teile.join(" · ")));
        var rk9 = (window.__pegel || {}).reihe_k, a9 = rk9 && rk9.a ? rk9.a.slice(-90) : [];
        if (a9.length > 20) {
          var NSs = "http://www.w3.org/2000/svg", Ws = 260, Hs = 46, mn = Math.min.apply(null, a9), mx = Math.max.apply(null, a9), sp = Math.max(mx - mn, 1);
          var sv = document.createElementNS(NSs, "svg"); sv.setAttribute("viewBox", "0 0 " + Ws + " " + Hs); sv.setAttribute("class", "spark"); sv.setAttribute("role", "img");
          var ti = document.createElementNS(NSs, "title"); ti.textContent = pick("Verlauf der letzten 90 Tage", "Course of the last 90 days"); sv.appendChild(ti);
          var pl = document.createElementNS(NSs, "polyline"); pl.setAttribute("fill", "none"); pl.setAttribute("stroke", "currentColor"); pl.setAttribute("stroke-width", "1.6");
          pl.setAttribute("points", a9.map(function (v, i) { return (i * (Ws - 4) / (a9.length - 1) + 2).toFixed(1) + "," + (Hs - 4 - (v - mn) / sp * (Hs - 8)).toFixed(1); }).join(" ")); sv.appendChild(pl);
          var w9 = el("div", "spark-w mono"); w9.appendChild(sv);
          w9.appendChild(el("span", "dim", pick("90 Tage: " + mn + " bis " + mx + " · ohne BSI und SANS zurückgerechnet", "90 days: " + mn + " to " + mx + " · back-calculated without BSI and SANS")));
          tx.appendChild(w9);
        }
      }
      sb.appendChild(tx); sb.hidden = !tx.children.length;
      var sbg = $("stufe-begr"); if (sbg) sbg.hidden = true;
      var sk = $("rd-skala"), kal = window.CL.skala();
      if (sk && kal && kal.stufen) {
        sk.textContent = "";
        var bar = el("div", "ska"); var von = 0;
        kal.stufen.forEach(function (x) {
          var bis = Math.min(x.bis, 100), seg = el("span", "sg ra-" + x.ampel); seg.style.width = (bis - von) + "%";
          seg.title = pick(x.name, x.name_en) + " (" + von + "–" + (bis === 100 ? 100 : bis - 1) + ")"; bar.appendChild(seg); von = bis;
        });
        var mk = el("i", "mk"), mz = el("b", "mkz mono", String(sc.wert)), zl1 = Math.max(0, Math.min(100, sc.wert)) + "%", zl2 = Math.max(2, Math.min(98, sc.wert)) + "%";
        var ruhe = window.__zeigerLief || (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
        bar.appendChild(mk); bar.appendChild(mz);
        if (ruhe) { mk.style.left = zl1; mz.style.left = zl2; }
        else {
          window.__zeigerLief = true; mk.style.left = "0%"; mz.style.left = "2%"; bar.classList.add("lauf");
          requestAnimationFrame(function () { requestAnimationFrame(function () { mk.style.left = zl1; mz.style.left = zl2; }); });
        }
        var zt = el("div", "skz mono"); [0].concat(kal.stufen.map(function (x) { return Math.min(x.bis, 100); })).forEach(function (n) { var t = el("span", "", String(n)); t.style.left = n + "%"; zt.appendChild(t); });
        var nm = el("div", "skn mono"), v0 = 0;
        kal.stufen.forEach(function (x) { var b2 = Math.min(x.bis, 100), t = el("span", x.ampel === ampel ? "akt" : "", pick(x.name, x.name_en)); t.style.width = (b2 - v0) + "%"; nm.appendChild(t); v0 = b2; });
        sk.appendChild(bar); sk.appendChild(zt); sk.appendChild(nm);
        sk.appendChild(el("p", "mono dim fine skt", pick("Stufen: ruhig, unauffällig, angespannt, hoch, außergewöhnlich. Grenzen vorläufig.", "Levels: calm, unremarkable, tense, high, exceptional. Limits provisional.")));
        sk.hidden = false;
      }
    }
    zeigeModell(k.score);
    zeichneScope(k.signale || []);
    (k.signale || []).forEach(function (s) {
      var b = el("div", "sg"), st = s.erhoeht === true ? ["●", "an"] : (s.erhoeht === false ? ["○", "aus"] : ["–", "kn"]);
      b.appendChild(el("span", "p mono " + st[1], st[0]));
      b.appendChild(el("span", "n", pick(s.name, s.name_en) + " · " + (s.erhoeht === true ? pick("an oder über der Schwelle", "at or above threshold") : (s.erhoeht === false ? pick("unter der Schwelle", "below threshold") : pick("noch keine Aussage", "no rating yet")))));
b.appendChild(el("span", "g", typeof s.ausschlag === "number" ? pick("Messwert: das ", "reading: ") + s.ausschlag.toLocaleString(window.I18N.locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + pick("-Fache der Schwelle", "x the threshold") : pick("noch kein Messwert", "no reading yet")));
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
      e.auch_im_cisa + " von " + e.eu_eintraege + " Einträgen im EU-KEV stehen auch im CISA-KEV, " + e.nur_eu + " nur in der EU. Bei " + e.eu_datum_frueher + " nennt die EU ein früheres Ausnutzungsdatum als die Aufnahme bei der CISA (Abstand im Median: " + tage(e.median_abstand_tage) + " Tage). Der EU-Katalog bildet den US-Katalog also fast vollständig ab.",
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
      if (o.sig) b.setAttribute("data-sig", o.sig);
      $(o.gr === "ktx" ? "rd-k-ktx" : "rd-k-score").appendChild(b);
    };
    var tg = pick("Stand ", "as of ");
    var kq = (d.kev || {})["neu_" + (d.fenster_tage || 30) + "_tage"], sw0 = d.schwellen || {};
    if (typeof kq === "number") kachel({ gr: "score", nat: "mess", quelle: "eigen", sig: "KEV count", name: pick("KEV-Menge", "KEV count"), wert: zahl(kq), einheit: pick(" · Schwelle ", " · threshold ") + zahl(sw0.erhoeht_ab), misst: pick("neu im CISA-KEV-Katalog in " + (d.fenster_tage || 30) + " Tagen, Archiv 36 Monate", "new in the CISA KEV catalog in " + (d.fenster_tage || 30) + " days, archive 36 months"), stand: tg + datum(d.stand) });
    var jz = z.jetzt || {}, v12 = z.vor_12_monaten || {};
    if (typeof jz.median_frisch === "number") kachel({ gr: "score", nat: "mess", quelle: "eigen", sig: "KEV pace", name: pick("Tempo bis KEV", "Pace to KEV"), wert: tage(jz.median_frisch), einheit: pick(" Tage Median", " days median"), misst: pick("Veröffentlichung bis KEV-Aufnahme, vor 12 Monaten: ", "publication to KEV listing, 12 months ago: ") + tage(v12.median_frisch) + pick(" Tage", " days"), stand: pick("Quelle CISA KEV · abgerufen ", "source CISA KEV · retrieved ") + datum(((d.quellen || []).filter(function (x) { return x.id === "cisa-kev"; })[0] || {}).abgerufen_am || d.stand) });
    ((r.konsens && r.konsens.signale) || []).slice().sort(function (x, y) { var o = ["eu_kev", "ms_ausgenutzt", "cert_bund", "ncsc_nl"]; return o.indexOf(x.baustein) - o.indexOf(y.baustein); }).forEach(function (x) {
      if (!x.baustein || typeof x.wert !== "number") return;
      kachel({ gr: "score", nat: "mess", quelle: "extern", sig: x.name_en, name: x.name, wert: zahl(x.wert), einheit: pick(" · Schwelle ", " · threshold ") + zahl(x.schwelle), misst: pick(x.misst, x.misst_en) + (x.daten_seit ? pick(", Archiv seit ", ", archive since ") + datum(x.daten_seit) : ""), stand: tg + datum(r.abgerufen_am) });
    });
    (r.einschaetzungen || []).forEach(function (q) {
      var pfeil = q.richtung === "steigend" ? " ↑" : (q.richtung === "fallend" ? " ↓" : ""), idx = q.wert && q.basis;
      if (!idx) return; // Lagebericht-Urteil steht schon bei den Gründen
      kachel({ gr: idx ? "score" : "ktx", nat: "eins", quelle: "extern", sig: idx ? "BSI Cyber Index" : null, name: q.name, url: q.link, wert: idx ? String(Math.round(q.wert / q.basis * 100)) : pick(q.urteil, q.urteil_en) + pfeil, einheit: idx ? pick(" % von 2024", " % of 2024") : "", misst: pick(q.misst, q.misst_en), stand: pick("Bericht vom ", "report of ") + datum(q.stand) + pick(" · von Hand geprüft ", " · checked by hand ") + datum(q.geprueft_am) + pick(" · jährlich", " · yearly") + (q.vorher ? pick(" · Vorjahr: ", " · year before: ") + pick(q.vorher, q.vorher_en) : "") });
    });
    if (r.sans) {
      var sn = { green: ["ruhig (grün)", "calm (green)"], yellow: ["erhöht (gelb)", "raised (yellow)"], orange: ["hoch (orange)", "high (orange)"], red: ["kritisch (rot)", "critical (red)"] }[r.sans.status] || ["–", "–"];
      kachel({ gr: "score", nat: "eins", quelle: "extern", sig: "SANS Infocon", name: "SANS Infocon", url: "https://isc.sans.edu/", wert: pick(sn[0], sn[1]), misst: pick("Scans und Ausbrüche im Netz", "scans and outbreaks across the internet"), stand: tg + datum(r.sans.abgerufen_am) + " · live" });
    }
    window.__ordneKacheln = function () {
      var gruppen = (((r.konsens || {}).score || {}).modell_gruppen) || [], ziel = $("rd-k-score"); if (!gruppen.length || !ziel) return;
      var kacheln = Array.prototype.slice.call(ziel.querySelectorAll(".kc")); if (!kacheln.length) return;
      ziel.className = "kc-gruppen"; ziel.textContent = "";
      gruppen.forEach(function (g) {
        var sigs = g.bausteine.map(function (x) { return x.signal; }), meine = kacheln.filter(function (k) { return sigs.indexOf(k.getAttribute("data-sig")) >= 0; });
        if (!meine.length) return;
        var w = el("div", "kc-gruppe");
        w.appendChild(el("h4", "mono kc-gh", pick(g.name, g.name_en)));
        if (g.frage) w.appendChild(el("p", "dim gr-frage", pick(g.frage, g.frage_en)));
        var grid = el("div", "rd-kacheln"); meine.sort(function (x, y) { return sigs.indexOf(x.getAttribute("data-sig")) - sigs.indexOf(y.getAttribute("data-sig")); }).forEach(function (k) { grid.appendChild(k); });
        w.appendChild(grid); ziel.appendChild(w);
      });
      var rest = kacheln.filter(function (k) { return !k.parentNode || k.parentNode === ziel; });
      if (rest.length) { var g2 = el("div", "rd-kacheln"); rest.forEach(function (k) { g2.appendChild(k); }); ziel.appendChild(g2); }
    };
    window.__ordneKacheln();
    if (typeof t.prognosen === "number") kachel({ gr: "ktx", nat: "mess", quelle: "eigen", name: pick("Trefferquote Prognose", "Forecast hit rate"), wert: typeof t.quote_reif === "number" ? proz(t.quote_reif) : "–", misst: pick("Prognosen: ", "forecasts: ") + t.prognosen + pick(", eingetreten: ", ", occurred: ") + t.eingetreten, stand: (typeof t.quote_reif === "number" ? "" : pick("erste Quote nach 30 Tagen · ", "first rate after 30 days · ")) + pick("eigener Abgleich EPSS gegen KEV · Stand ", "own comparison EPSS vs KEV · as of ") + datum(r.abgerufen_am) });
    if (e) kachel({ gr: "ktx", nat: "mess", quelle: "eigen", name: pick("EU-KEV und CISA-KEV: Überschneidung", "EU KEV and CISA KEV: overlap"), wert: e.auch_im_cisa + "/" + e.eu_eintraege, misst: pick("EU-Einträge, die auch im CISA-KEV stehen", "EU entries also in CISA KEV"), stand: pick("eigener Abgleich EUVD (ENISA) gegen CISA-KEV · abgerufen ", "own comparison EUVD (ENISA) vs CISA KEV · retrieved ") + datum((d.eu_kev || {}).abgerufen_am || r.abgerufen_am) });
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
    var B = Math.max(300, Math.round(svg.getBoundingClientRect().width)) || 1000, H = B < 600 ? 170 : 200, L = 48, R = 8, T = 10, U = 26;
    svg.setAttribute("viewBox", "0 0 " + B + " " + H);
    var mk = function (tag, a, tx) { var e = document.createElementNS(NS, tag); for (var k in a) e.setAttribute(k, a[k]); if (tx !== undefined) e.textContent = tx; svg.appendChild(e); return e; };
    var y = function (p) { return T + (H - T - U) * (1 - p); }, w = (B - L - R) / v.length;
    [0, 0.5, 1].forEach(function (p) {
      mk("line", { x1: L, x2: B - R, y1: y(p), y2: y(p), stroke: "#1d262e" });
      mk("text", { x: L - 6, y: y(p) + 4, "text-anchor": "end", fill: "#8a99a6", "font-size": 12, "font-family": "ui-monospace,monospace" }, Math.round(p * 100) + " %");
    });
    v.forEach(function (p, i) {
      var t = mk("rect", { x: L + i * w + 1, y: y(p.anteil_30), width: Math.max(w - 2, 1), height: y(0) - y(p.anteil_30), fill: i === v.length - 1 ? "#ff8a7a" : "#3fae7a" });
      t.appendChild(document.createElementNS(NS, "title")).textContent = p.monat + ": " + Math.round(p.anteil_30 * 100) + " % (" + p.n + ")";
    });
    [0, Math.floor(v.length / 2), v.length - 1].forEach(function (i) {
      mk("text", { x: L + i * w + w / 2, y: H - 8, "text-anchor": i === 0 ? "start" : (i === v.length - 1 ? "end" : "middle"), fill: "#8a99a6", "font-size": 12, "font-family": "ui-monospace,monospace" }, v[i].monat);
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
  window.CL.zeigeKonsens = zeigeKonsens;
  window.CL.zeigeRadar = zeigeRadar;
  window.CL.zeichneRadar = zeichneRadar;
  window.CL.zeigeAusblick = zeigeAusblick;
})();
