(function () {
  "use strict";
  var L = "de";
  try { var g = localStorage.getItem("lang"); if (g === "de" || g === "en") L = g; else L = (navigator.language || "de").slice(0, 2) === "de" ? "de" : "en"; }
  catch (e) { L = (navigator.language || "de").slice(0, 2) === "de" ? "de" : "en"; }

  // Englische Texte für Elemente mit data-t (Deutsch steht im HTML). Nur eigene, feste Texte.
  var EN = {
    skip: "Skip to content",
    n_schwach: "/flaws", sw_h: "## flaws & patches", sw_intro: "The second part of the page follows the path of a flaw: it is reported, it is attacked, and there is (or is not yet) a patch. Everything above measures the situation, here is what you can actually do.",
    sw_1: "reported", sw_1t: "new flaws, warnings, forecast", sw_2: "attacked", sw_2t: "proven exploited (KEV)", sw_3: "patched?", sw_3t: "which patch, what first",
    beta: "",
    n_rueck: "/history", n_neu: "/new", n_radar: "/radar", n_signale: "/signals", n_abo: "/subscribe",
    tab_ausblick: "Forecast",
    tab_kev: "KEV catalog", i_quellen: "Sources", i_begriffe: "Terms", i_methode: "Method", i_hinweise: "Notes",
    h_lbl: 'as of <span id="stand">…</span> · experiment',
    h_titel: "A cyber threat seismograph.<br>Worldwide, rule-based, openly sourced.",
    h_lead: "Worldwide, across all vendors: we count the vulnerabilities that bodies such as CISA report as exploited and combine them into one level using open rules. Like a seismograph, the Dreier Gauge and the radar show the readings, they predict nothing. The whole thing is an open experiment by Dreier Labs: the level follows fixed rules, the radar score is an attempt. No statement about any one country or sector. A tool for defense: for blue teams, SOCs and everyone who protects their systems.",
    tg_btn: "Subscribe to the Telegram channel",
    rss_btn: "Copy the RSS feed address",
    rss_txt: "paste it into your feed reader (Feedly, Inoreader, NetNewsWire), no account needed.", rss_roh: "raw file",
    tg_txt: "one daily report; instant messages only for a level change or a ransomware alert.",
    h_lage: "Current situation",
    l_wie: "how the level is calculated",
    l_stufe: "dreier gauge · worldwide", l_lade: "Loading data",
    l_7: "new · 7 days", l_30: "new · 30 days", l_ges: "catalog total",
    l_kev: "<strong>KEV</strong> stands for <em>Known Exploited Vulnerabilities</em>: a list by the US cybersecurity agency <strong>CISA</strong> of flaws that are proven to be exploited by attackers. The level shows how many are newly added.",
    r_h: "## history", i_faq: "faq", l_verk2: "Combined from gauge and radar", l_tempo: "For comparison: the pace", l_tempo2: "· own signal in the radar, not part of the gauge", n_patches: "/patches", p_h: "## patches", p_intro: "What vendors patched recently, with figures and a rating by fixed rules. We do not manage patches and do not rate severity ourselves: severity and exploitation come from the vendors.", n_intro: "What became known in the last days: exploited vulnerabilities (CISA KEV, EU KEV), warnings of the BSI (CERT-Bund) and a forecast for new flaws. Each tab names its source, period and date.", l_faq: "▸ New here? Questions and answers (FAQ)",
    f1q: "What is the Dreier Gauge?", f1a: "Our own score, not a standard or norm. It counts how many vulnerabilities were newly added to the CISA KEV catalog in the last 30 days (the gauge reading) and derives a level from it: low, elevated or high. It measures activity in the catalog, not the number of attacks.",
    f1bq: "What is the Dreier Pace?", f1ba: "Our second signal next to the amount: it measures speed. We take the flaws added to the KEV in the last 90 days and form the median of the days from their publication to the listing. The smaller the number, the faster flaws are reported as exploited. The levels come from 36 months of data: elevated from the fastest quarter (up to 5 days), high from the fastest tenth (up to 3 days). Amount and pace come from the same source but are different axes, which is why they are shown separately side by side.",
    f2q: "Where does the data come from?", f2a: "The gauge is built solely from CISA's public KEV catalog, fetched daily. Other sources (BSI, SANS, abuse.ch, NCSC-NL, ENISA, EU KEV) run alongside in the radar and do not feed the gauge. Every value names its source and date.",
    f3q: "What are KEV and CISA?", f3a: "CISA is the US cybersecurity agency. KEV (Known Exploited Vulnerabilities) is its catalog of vulnerabilities with proven exploitation in the wild. Being listed means exploited in practice, not just theoretically dangerous (unlike a CVSS severity or an EPSS probability). Limitation: it is the US view, and only what CISA adds counts.",
    f4q: "What are the thresholds, and who sets them?", f4a: "There are no official or standardised thresholds. We set them ourselves from the distribution of the 30-day count over 36 months: the 75th percentile (25 entries) gives “elevated”, the 90th (32) gives “high”. If at least 5 of the entries are used in ransomware campaigns, the level goes up by one. “High” therefore means: unusually many new entries compared with the last three years. The values are fixed, documented in config/regeln.json and re-checked by hand. Every change is visible in the repo history; objections are welcome as an issue on GitHub.",
    f5q: "Does “high” mean I am being attacked?", f5a: "No. The level applies in general, not to a sector or an organisation, and it predicts nothing. Whether a flaw affects you depends on your own inventory. That is what the list of newly added entries under “new” is for.",
    f6q: "What is the weakness of this method?", f6a: "The scale is relative and follows the catalog: if CISA becomes more active overall, the count hits the marks more often without the situation changing in an absolute sense. Hence the long 36-month basis and the manual re-check. Also, the gauge only counts what enters the KEV, not what is exploited unnoticed.",
    f7q: "What is the radar score?", f7a: "An experiment. It is the mean of the readings of all available signals (Dreier Gauge, speed to KEV, BSI Cyber Index, SANS, Feodo), each against its own rule threshold. It is not objective, not part of the Dreier Gauge, and only means something after several weeks of history. Its levels (calm, unremarkable, tense, high, exceptional) are provisional and aligned with the Dreier Gauge; after about 90 days we will re-derive them from its own distribution.",
    f8q: "What do the forecast and EPSS mean?", f8a: "The forecast shows vulnerabilities not yet in the KEV that EPSS (FIRST) rates as likely to be exploited soon. It does not influence the level. The site checks it itself: the hit rate appears once enough forecasts are 30 days old.",
    r_pegel: "Dreier Gauge over time", h_blau: "BLUE TEAM", h_motto: "For everyone who defends.", i_pruef: "check calendar", i_pruef_t: "Hand-maintained entries (reasons, assessments by others such as the BSI report) can go stale, so each carries a check date. On every run a script checks whether the link is reachable (a link counts as dead only when every attempt fails for 24 hours) and whether the deadline has passed: 330 days for annual entries, 90 days for reasons, 183 days for the Dreier Gauge thresholds. If something is due it is marked yellow and an issue opens automatically in the project. The script checks only deadline and reachability, not content: the check date is set by a person who has read the source. Rules in RULES.md.", r_rscore: "Radar score over time · experiment", n_h: "## new",
    rd_h: "## radar", rd_intro: "Our own measurements from open data, next to the assessments of other bodies. None of it feeds into the level.",
    rd_kon_h: "Radar score", rd_kon_n: "Each signal follows a fixed rule (RULES.md). Only external sources count as confirmation. The dashed ring is the rule threshold, the further out a point lies, the stronger the reading. Only the radar score above forms a mean.",
    rd_zeit_h: "How fast is a vulnerability reported as exploited?", rd_tr_h: "Hit rate of the forecast", rd_eu_h: "EU-KEV and CISA KEV",
    rd_sig_h: "## signals", rd_sig_intro: "Each signal once, with value, rule and period. Measurements are counts from open raw data, assessments are judgements by other bodies.", rd_g_score: "In the radar score: signals with a rule threshold", rd_g_ktx: "For orientation only: no threshold, not in the score", l_verk: "Axis “Dreier Gauge” in the radar", rd_det: "Explanations: hit rate and EU comparison", rd_vgl_n: "The sources measure different things. When several point the same way, that is a stronger signal than one alone.",
    rd_warum_h: "Documented reasons for the pace", rd_warum_n: "This is the long-term background, not today's level. Maintained by hand, each with a source and check date. We do not measure geopolitical tension.",
    n_sub: 'Exploited vulnerabilities of the last <span id="fenster">30</span> days, newest first. The filter runs only in your browser.',
    n_filter: "Filter by vendor, product or CVE", n_ph: "e.g. microsoft, fortinet, CVE-2026",
    th1: "Added", th2: "Vendor", th3: "Product", th5: "Due date (CISA)",
    n_q1: "Source: CISA KEV (CC0 1.0). The due date applies to US federal agencies and is only a guide. Links lead to the NIST CVE page (NVD). No attack details.",
    n_q2: "Source: CERT-Bund, the computer emergency team of the <strong>BSI</strong> (German Federal Office for Information Security), via wid.cert-bund.de. Only title, severity, date and link are reused; the texts are at the BSI. No indication of any cooperation with the BSI.",
    n_q3: "Source: EU Vulnerability Database (EUVD) of <strong>ENISA</strong>, the EU Agency for Cybersecurity. The licence is not explicitly clarified, so only ID, CVE, vendor and link are shown.",
    n_q4: 'Forecast, not part of the level: the probability comes from <strong>EPSS</strong> (Exploit Prediction Scoring System, FIRST) and estimates whether a new flaw will be exploited in the next 30 days. An estimate, not a finding. Listed are new CVEs of the last days that are not yet in the KEV. See EPSS at <a href="https://www.first.org/epss">first.org/epss</a>. Publication date and CVSS score from the NVD. This product uses data from the NVD API but is not endorsed or certified by the NVD.',
    i_qtxt: "From CERT-Bund (BSI) we show only title, severity, date and link, always with the source. The texts are at the BSI.",
    i_dl: "<dt>CISA</dt><dd>Cybersecurity and Infrastructure Security Agency, the US cybersecurity agency. Maintains the KEV list.</dd>" +
      "<dt>KEV</dt><dd>Known Exploited Vulnerabilities: flaws that are proven to be exploited in attacks.</dd>" +
      "<dt>CVE</dt><dd>The worldwide standard identifier of a vulnerability, for example CVE-2026-12345.</dd>" +
      "<dt>BSI / CERT-Bund</dt><dd>The German Federal Office for Information Security and its computer emergency team. They warn about vulnerabilities in Germany.</dd>" +
      "<dt>ENISA / EUVD</dt><dd>The EU Agency for Cybersecurity and its vulnerability database (European Union Vulnerability Database).</dd>" +
      "<dt>NVD</dt><dd>National Vulnerability Database of the US institute NIST, the place to find details on a CVE.</dd>" +
      "<dt>Ransomware</dt><dd>Malware that encrypts data to extort a ransom.</dd>",
    i_grid: '<div class="panel pad"><strong>Published data only</strong><p class="dim">We do not know what is in use where, and we do not claim to.</p></div>' +
      '<div class="panel pad"><strong>No data instead of guesses</strong><p class="dim">If a sourced value is missing, it says “no data”.</p></div>' +
      '<div class="panel pad"><strong>Open rules</strong><p class="dim">Window, thresholds and derivation are in <a href="https://github.com/maxim91136/cyberlage.org/blob/main/RULES.md">RULES.md</a>.</p></div>',
    f_fuss: 'A project by <a href="https://dreierlabs.com">Dreier Labs</a>. Private project, not an official body, no connection to the BSI or any authority. No warranty.',
    f_links: '<a href="impressum.html">legal notice</a> · <a href="hinweise.html">notes &amp; privacy</a>',
    top: "Back to top",
    // hinweise.html
    hw_titel: "Notes and privacy",
    hw_anbieter: 'This site is operated by Dreier Labs. The full legal notice is at <a href="https://dreierlabs.com/impressum.html">dreierlabs.com/impressum.html</a>.',
    hw_h1: "## notes", hw_h2: "## privacy",
    hw_l1: "Cyberlage is a private project of Dreier Labs and not an official body. There is no connection to the BSI or any other authority.",
    hw_l2: "The content is an analysis of openly licensed sources and no substitute for warnings from the BSI or a CERT. No guarantee of accuracy or completeness.",
    hw_l3: "The operators of linked sites are responsible for them.",
    hw_ds: 'This site sets no cookies and embeds no tracking or third-party services. When you visit, the hosting provider (Cloudflare) processes technically necessary connection data. Your browser’s local storage holds only your language choice and the alert mode setting; neither is transmitted. More: <a href="https://dreierlabs.com/datenschutz.html">privacy policy of Dreier Labs</a>.',
    hw_zurueck: "Back to the start page"
  };

  // Dynamische Texte (Funktionen oder Strings je Sprache)
  var S = {
    rechnung: { de: function (f, e, h, r, m, med) { return [
        "<p><strong>Gezählt wird:</strong> wie viele Schwachstellen in den letzten " + f + " Tagen neu in den CISA-KEV-Katalog aufgenommen wurden, weltweit und über alle Hersteller.</p>",
        "<ul><li><strong>niedrig:</strong> weniger als " + e + " neue Einträge</li><li><strong>erhöht:</strong> " + e + " bis " + (h - 1) + "</li><li><strong>hoch:</strong> " + h + " oder mehr</li></ul>",
        "<p><strong>Aufschlag:</strong> Sind unter den neuen Einträgen mindestens " + r + " mit bekannter Ransomware-Nutzung, steigt die Stufe um eine Ebene.</p>",
        "<p><strong>Woher die Schwellen kommen:</strong> aus den letzten " + m + " Monaten des Katalogs (das Anlaufjahr 2022 zählt nicht mit). " + e + " ist das 75. Perzentil, " + h + " das 90. Perzentil der 30-Tage-Zählung (Median " + med + "). Erhöht heißt also: mehr Neuzugänge als in drei von vier üblichen Zeiträumen.</p>",
        "<p class='dim'>Nicht Teil der Stufe: CERT-Bund, EU-KEV, die Prognose (EPSS) und die ENISA-Zahlen. Sie dienen nur zur Einordnung. Die Stufe misst Aktivität im Katalog, keine Zahl von Angriffen. Alle Regeln: <a href='https://github.com/maxim91136/cyberlage.org/blob/main/RULES.md'>RULES.md</a>.</p>"].join(""); },
      en: function (f, e, h, r, m, med) { return [
        "<p><strong>What is counted:</strong> how many vulnerabilities were newly added to the CISA KEV catalog in the last " + f + " days, worldwide and across all vendors.</p>",
        "<ul><li><strong>low:</strong> fewer than " + e + " new entries</li><li><strong>elevated:</strong> " + e + " to " + (h - 1) + "</li><li><strong>high:</strong> " + h + " or more</li></ul>",
        "<p><strong>Surcharge:</strong> if at least " + r + " of the new entries have known ransomware use, the level goes up by one step.</p>",
        "<p><strong>Where the thresholds come from:</strong> the last " + m + " months of the catalog (the 2022 start-up year is excluded). " + e + " is the 75th percentile and " + h + " the 90th percentile of the 30-day count (median " + med + "). Elevated therefore means more additions than in three out of four typical periods.</p>",
        "<p class='dim'>Not part of the level: CERT-Bund, EU-KEV, the forecast (EPSS) and the ENISA figures. They are for context only. The level measures activity in the catalog, not a number of attacks. Full rules: <a href='https://github.com/maxim91136/cyberlage.org/blob/main/RULES.md'>RULES.md</a>.</p>"].join(""); } },
    ab_info: { de: function (f, g, h, sw, a) { return "Die Prognose blickt auf neue Schwachstellen (CVE) der letzten " + f + " Tage, die noch nicht im KEV stehen: " + g + " geprüft, " + h + " davon mit mindestens " + sw + " % geschätzter Wahrscheinlichkeit, in den nächsten 30 Tagen ausgenutzt zu werden. Die Schätzung stammt von EPSS (FIRST), nicht von uns. Die zehn höchsten stehen hier. Stand: " + a + "."; },
               en: function (f, g, h, sw, a) { return "The forecast looks at new vulnerabilities (CVE) of the last " + f + " days that are not yet in the KEV: " + g + " checked, " + h + " of them with at least " + sw + " % estimated probability of being exploited in the next 30 days. The estimate comes from EPSS (FIRST), not from us. The ten highest are listed here. As of: " + a + "."; } },
    ab_zeile: { de: function (p) { return p + " Wahrscheinlichkeit"; }, en: function (p) { return p + " probability"; } },
    keine: { de: "keine Daten", en: "no data" },
    niedrig: { de: "niedrig", en: "low" }, erhoeht: { de: "erhöht", en: "elevated" }, hoch: { de: "hoch", en: "high" },
    erhoeht_lbl: { de: "erhöht", en: "elevated" },
    keine_bew: { de: "Keine Bewertung", en: "No rating" },
    laden_fehler: { de: "Die Daten konnten nicht geladen werden.", en: "The data could not be loaded." },
    kev_quelle: { de: function (v, a, l) { return "quelle: CISA KEV · veröffentlicht " + v + " · abgerufen " + a + " · lizenz " + l + " · geltungsbereich: weltweit"; },
                  en: function (v, a, l) { return "source: CISA KEV · published " + v + " · retrieved " + a + " · licence " + l + " · scope: worldwide"; } },
    sektor_txt: { de: function (j) { return "der erfassten Ereignisse " + j + " betrafen die öffentliche Verwaltung. Zur Einordnung, nicht Teil der Stufe."; },
                  en: function (j) { return "of the recorded events in " + j + " affected public administration. For context, not part of the level."; } },
    sektor_meta: { de: function (g, eu, q, seite, lz) { return "geltungsbereich: " + g + (eu ? ", nicht Deutschland" : "") + " · " + q + ", Seite " + seite + " · " + lz + " · "; },
                   en: function (g, eu, q, seite, lz) { return "scope: " + g + (eu ? ", not Germany" : "") + " · " + q + ", page " + seite + " · " + lz + " · "; } },
    quelle: { de: "Quelle", en: "Source" },
    verarbeitet: { de: function (lz, a) { return "verarbeitet · " + lz + (a ? " · abgerufen " + a : ""); },
                   en: function (lz, a) { return "processed · " + lz + (a ? " · retrieved " + a : ""); } },
    bekannt: { de: "bekannt", en: "known" }, nicht_bekannt: { de: "nicht bekannt", en: "not known" },
    treffer: { de: function (n, m) { return n + " von " + m + " Einträgen"; }, en: function (n, m) { return n + " of " + m + " entries"; } },
    alle: { de: function (n) { return "Alle " + n + " anzeigen"; }, en: function (n) { return "Show all " + n; } },
    luecke: { de: function (d) { return " Achtung: Wir sammeln erst seit dem " + d + ", die Zahlen decken noch nicht das ganze Fenster ab."; },
              en: function (d) { return " Note: we have only been collecting since " + d + ", so the figures do not yet cover the whole window."; } },
    bsi_info: { de: function (t, k, h, k7, h7, a) { return "Letzte " + t + " Tage: " + k + " kritisch, " + h + " hoch (davon 7 Tage: " + k7 + " kritisch, " + h7 + " hoch). Abgerufen " + a + "."; },
                en: function (t, k, h, k7, h7, a) { return "Last " + t + " days: " + k + " critical, " + h + " high (of which 7 days: " + k7 + " critical, " + h7 + " high). Retrieved " + a + "."; } },
    schwere: { de: { kritisch: "kritisch", hoch: "hoch" }, en: { kritisch: "critical", hoch: "high" } },
    eu_info: { de: function (n, t, a) { return n + " neu als ausgenutzt gemeldet in den letzten " + t + " Tagen. Abgerufen " + a + "."; },
               en: function (n, t, a) { return n + " newly reported as exploited in the last " + t + " days. Retrieved " + a + "."; } },
    v_titel: { de: function (a, b, mn, mx, z) { return "Neu aufgenommene Schwachstellen pro 30 Tage, " + a + " bis " + b + ": niedrigster Wert " + mn + ", höchster " + mx + ", zuletzt " + z + "."; },
               en: function (a, b, mn, mx, z) { return "Newly added vulnerabilities per 30 days, " + a + " to " + b + ": lowest " + mn + ", highest " + mx + ", latest " + z + "."; } },
    v_tip: { de: function (d, n, st) { return d + ": " + n + " neu in 30 Tagen" + (st ? ", Stufe " + st : ""); },
             en: function (d, n, st) { return d + ": " + n + " new in 30 days" + (st ? ", level " + st : ""); } },
    v_leg: { de: function (m) { return "Zeitraum: letzte " + m + " Monate, die Basis der Schwellen. Balken: grün unter erhöht-Schwelle, gelb erhöht, rot hoch. Wochenstände, rückwirkend mit den heutigen Schwellen gemessen. Der Pegelstand wird täglich fortgeschrieben (data/pegel.json), ab heute als live gespeicherter Wert. Quelle: CISA KEV (CC0 1.0), eigene Auswertung."; },
             en: function (m) { return "Period: last " + m + " months, the basis of the thresholds. Bars: green below the elevated threshold, yellow elevated, red high. Weekly values, measured retroactively with today’s thresholds. The gauge reading is recorded daily (data/pegel.json), from today as a live stored value. Source: CISA KEV (CC0 1.0), own analysis."; } }
  };

  var api = {
    lang: L,
    t: function (k) {
      var e = S[k]; if (!e) return k;
      var v = e[L]; var args = Array.prototype.slice.call(arguments, 1);
      return typeof v === "function" ? v.apply(null, args) : v;
    },
    locale: L === "de" ? "de-DE" : "en-GB",
    pick: function (de, en) { return L === "en" && en ? en : de; }
  };
  window.I18N = api;

  document.documentElement.lang = L;
  if (L === "en") {
    Array.prototype.forEach.call(document.querySelectorAll("[data-t]"), function (n) {
      var v = EN[n.getAttribute("data-t")]; if (v !== undefined) n.innerHTML = v;
    });
    Array.prototype.forEach.call(document.querySelectorAll("[data-t-ph]"), function (n) {
      var v = EN[n.getAttribute("data-t-ph")]; if (v !== undefined) n.setAttribute("placeholder", v);
    });
    var tt = { "index": "Cyberlage – situation picture from open sources", "hinweise": "Notes and privacy – Cyberlage" };
    document.title = /hinweise/.test(location.pathname) ? tt.hinweise : tt.index;
    var md = document.querySelector('meta[name="description"]');
    if (md) md.setAttribute("content", "The cyber situation, derived by rules from exploited vulnerabilities. Open sources, open rules. A project by Dreier Labs.");
  }
  var b = document.getElementById("sprache");
  if (b) {
    b.textContent = L === "de" ? "EN" : "DE";
    b.addEventListener("click", function () {
      try { localStorage.setItem("lang", L === "de" ? "en" : "de"); } catch (e) { }
      location.reload();
    });
  }
})();
