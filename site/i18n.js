(function () {
  "use strict";
  var L = "de";
  try { var g = localStorage.getItem("lang"); if (g === "de" || g === "en") L = g; else L = (navigator.language || "de").slice(0, 2) === "de" ? "de" : "en"; }
  catch (e) { L = (navigator.language || "de").slice(0, 2) === "de" ? "de" : "en"; }

  // Englische Texte für Elemente mit data-t (Deutsch steht im HTML). Nur eigene, feste Texte.
  var EN = {
    skip: "Skip to content",
    n_termine: "/dates", t_h: "## dates: patch calendar", t_intro: "The next patch dates of the big vendors, calculated from their published rules. So you know in advance when to plan maintenance windows and time.",
    t_quelle: "Rules: Microsoft, Adobe and SAP usually publish on the second Tuesday of the month (Microsoft usually at 18:00 UTC). Oracle: Critical Patch Update on the third Tuesday of January, April, July and October, in the other months a Critical Security Patch Update on the third Tuesday; Oracle announces each date on the Thursday before. Out-of-band updates cannot be predicted and appear in the ticker. Dates without guarantee, the vendor's page is authoritative.",
    g_lage: "SITUATION", g_handeln: "ACT",
    tl_h: "## part 1 · situation", tl_intro: "How tense is the global cyber situation? The Dreier Gauge measures it as one score from several components, the signals and the history back it up.", sw_h: "## part 2 · act: flaws & patches", sw_intro: "Which flaws to close first, and with which patch. Only flaws with an available patch are ranked; attacked flaws without a patch are listed separately below.", s_patches: "Patches", s_termine: "Patch calendar", s_kev: "Exploited (KEV)", s_neu: "New flaws", s_lage: "Components & radar", s_sig: "Signals", s_rueck: "History",
    sw_1: "reported", sw_1t: "new flaws, warnings, forecast", sw_2: "attacked", sw_2t: "proven exploited (KEV)", sw_3: "patch", sw_3t: "what first, with which update",
    beta: "",
    n_rueck: "/history", n_neu: "/new", n_radar: "/radar", n_signale: "/signals", n_abo: "/subscribe",
    tab_ausblick: "Forecast",
    tab_kev: "KEV catalog", i_quellen: "Sources", i_begriffe: "Terms", i_methode: "Method", i_hinweise: "Notes",
    h_lbl: 'as of <span id="stand">…</span> · experiment',
    h_titel: "A cyber threat seismograph.<br>Worldwide, rule-based, openly sourced.",
    h_lead: "Worldwide, across all vendors: the Dreier Gauge combines several components under open rules into one score from 0 to 100: eight components in three groups: exploitation (KEV count, pace to KEV, EU KEV, Microsoft), warnings (CERT-Bund, NCSC-NL) and external assessments (BSI Cyber Index, SANS Infocon). Like a seismograph it shows the situation, it predicts nothing. An open experiment by Dreier Labs, the level limits are provisional. No statement about any one country or sector. A tool for defense: for blue teams, SOCs and everyone who protects their systems.",
    tg_btn: "Subscribe to the Telegram channel",
    rss_btn: "Copy the RSS feed address",
    rss_txt: "paste it into your feed reader (Feedly, Inoreader, NetNewsWire), no account needed.", rss_roh: "raw file",
    tg_txt: "one daily report; instant messages only for a level change or a ransomware alert.",
    h_lage: "Current situation",
    l_wie: "how the dreier gauge is calculated",
    l_stufe: "dreier gauge · worldwide", l_lade: "Loading data",
    l_7: "new · 7 days", l_30: "new · 30 days", l_ges: "catalog total",
    l_kev: "<strong>KEV</strong> stands for <em>Known Exploited Vulnerabilities</em>: a list by the US cybersecurity agency <strong>CISA</strong> of flaws that are proven to be exploited by attackers. The KEV count is one component of the gauge.",
    r_h: "## history", i_faq: "faq", l_verk2: "The conclusion drawn from it", l_tempo: "For comparison: the pace", l_tempo2: "· own signal in the radar, not part of the gauge", n_patches: "/patches", p_h: "## patches: what first, with what", p_intro: "What vendors patched recently, with figures and a rating by fixed rules. We do not manage patches and do not rate severity ourselves: severity and exploitation come from the vendors.", n_intro: "What became known in the last days: exploited vulnerabilities (CISA KEV, EU KEV), warnings of the BSI (CERT-Bund) and a forecast for new flaws. Each tab names its source, period and date.", l_faq: "▸ New here? Questions and answers (FAQ)",
    f1q: "What is the Dreier Gauge?", f1a: "Our own score, not a standard or norm. It combines several components into one number from 0 to 100 and derives a level from it: calm, unremarkable, tense, high or exceptional. 50 means the rule thresholds of the components are reached on average. It measures activity and signals, not the number of attacks, and predicts nothing.",
    l_umbau: "⚠ Work in progress: the Dreier Gauge is being reworked. Components and value may still change.",
    rd_einzel: "Individual values and group structure",
    k_bau: "## components", k_wie: "## how the gauge arises", k_ms: "Microsoft patch day", k_edge: "Edge and Chrome", k_hs: "Linux distributions and vendors", s_wie: "How the gauge arises",
    k_zuerst: "This week first",
    f1cq: "Why is it called the “Dreier” gauge?", f1ca: "The name comes from Dreier Labs, the project behind Cyberlage, and has nothing to do with the number of levels: the gauge has five levels (calm, unremarkable, tense, high, exceptional).",
    f1bq: "What is it made of?", f1ba: "From eight components in three groups. Exploitation: KEV count (new in the CISA catalog, 30 days), pace to KEV (how fast new flaws are exploited), EU KEV (newly reported as exploited) and Microsoft (exploited flaws in the latest patch day). Warnings: CERT-Bund (new critical and high advisories, 30 days) and NCSC-NL (new advisories, 30 days). External assessments: BSI Cyber Index and SANS Infocon. Each component is measured against its own threshold, the top quarter of its history. Averaged within each group first, then across groups. 50 means the thresholds are reached on average.",
    f2q: "Where does the data come from?", f2a: "From public sources, fetched daily: CISA KEV, CVE list, EU KEV (ENISA), Microsoft MSRC, CERT-Bund, NCSC-NL, BSI Cyber Index and SANS ISC. All eight feed the score. Every value names its source and date.",
    f3q: "What are KEV and CISA?", f3a: "CISA is the US cybersecurity agency. KEV (Known Exploited Vulnerabilities) is its catalog of vulnerabilities with proven exploitation in the wild. Being listed means exploited in practice, not just theoretically dangerous (unlike a CVSS severity or an EPSS probability). Limitation: it is the US view, and only what CISA adds counts.",
    f4q: "What are the thresholds, and who sets them?", f4a: "There are no official or standardised thresholds. We set them ourselves from the distribution of the 30-day count over 36 months: the 75th percentile (25 entries) gives “elevated”, the 90th (32) gives “high”. If at least 5 of the entries are used in ransomware campaigns, the level goes up by one. “High” therefore means: unusually many new entries compared with the last three years. The values are fixed, documented in config/regeln.json and re-checked by hand. Every change is visible in the repo history; objections are welcome as an issue on GitHub.",
    f5q: "Does “high” mean I am being attacked?", f5a: "No. The level applies in general, not to a sector or an organisation, and it predicts nothing. Whether a flaw affects you depends on your own inventory. That is what the list of newly added entries under “new” is for.",
    f6q: "What is the weakness of this method?", f6a: "The scale is relative and follows the sources: if CISA becomes more active overall, the KEV count hits its marks more often without the situation changing in an absolute sense. Hence the long 36-month basis and the manual re-check. Also, the score only counts what is reported, not what is exploited undetected.",
    f7q: "How reliable is the score?", f7a: "It is an experiment: the components cover different periods and mix measurements with assessments, the weights are equal and not yet justified. The level limits (30, 50, 64, 80) are provisional and aligned with the KEV count over the last 36 months. The daily value of the full gauge has been stored since 25 November 2026, the history before that is back-calculated from archive data; after about 90 days we derive the limits anew from its own distribution. Until then it is an overall impression, not an objective measure.",
    f8q: "What do the forecast and EPSS mean?", f8a: "The forecast shows vulnerabilities not yet in the KEV that EPSS (FIRST) rates as likely to be exploited soon. It does not influence the level. The site checks it itself: the hit rate appears once enough forecasts are 30 days old.",
    r_pegel: "KEV count over time", h_blau: "BLUE TEAM", h_motto: "For everyone who defends systems, from the admin to the security team.", i_pruef: "check calendar", i_pruef_t: "Hand-maintained entries (reasons, assessments by others such as the BSI report) can go stale, so each carries a check date. On every run a script checks whether the link is reachable (a link counts as dead only when every attempt fails for 24 hours) and whether the deadline has passed: 330 days for annual entries, 90 days for reasons, 183 days for the Dreier Gauge thresholds. If something is due it is marked yellow and an issue opens automatically in the project. The script checks only deadline and reachability, not content: the check date is set by a person who has read the source. Rules in RULES.md.", r_rscore: "Dreier Gauge over time · 3 years", n_h: "## new",
    rd_h: "## radar", rd_intro: "Our own measurements from open data, next to the assessments of other bodies. None of it feeds into the level.",
    rd_kon_h: "Components of the Dreier Gauge", rd_kon_n: "Each component follows a fixed rule (RULES.md). The dashed ring is the threshold: the further out a point lies, the stronger the reading. The gauge above is the mean of these.",
    rd_zeit_h: "How fast is a vulnerability reported as exploited?", rd_tr_h: "Hit rate of the forecast", rd_eu_h: "EU-KEV and CISA KEV",
    rd_sig_h: "## signals", rd_sig_intro: "Each component once, with value, threshold, rule and period. Measurements are counts from open raw data, assessments are judgements by other bodies.", rd_g_score: "In the Dreier Gauge: the eight components with their threshold", rd_g_ktx: "For orientation only: no threshold, not in the score", l_verk: "Built from these components", rd_det: "Explanations: hit rate and EU comparison", rd_vgl_n: "The sources measure different things. When several point the same way, that is a stronger signal than one alone.",
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
        "<p><strong>So entsteht der Dreier-Pegel:</strong> ein Score von 0 bis 100 aus acht Bausteinen in drei Gruppen: Ausnutzung (KEV-Menge, Tempo bis KEV, EU-KEV, Microsoft), Warnungen (CERT-Bund, NCSC-NL) und externe Einschätzungen (BSI Cyber Index, SANS Infocon). Jeder Baustein wird an seiner Schwelle gemessen (oberes Viertel seiner Historie), dann wird je Gruppe und über die Gruppen gemittelt. 50 heißt: die Regelschwellen sind im Schnitt erreicht, 100: im Schnitt doppelt so weit. Stufen: unter 30 ruhig, 30 bis 49 unauffällig, 50 bis 63 angespannt, 64 bis 79 hoch, ab 80 außergewöhnlich (vorläufig).</p><p><strong>Baustein KEV-Menge:</strong> gezählt wird, wie viele Schwachstellen in den letzten " + f + " Tagen neu in den CISA-KEV-Katalog aufgenommen wurden, weltweit und über alle Hersteller.</p>",
        "<ul><li><strong>niedrig:</strong> weniger als " + e + " neue Einträge</li><li><strong>erhöht:</strong> " + e + " bis " + (h - 1) + "</li><li><strong>hoch:</strong> " + h + " oder mehr</li></ul>",
        "<p><strong>Aufschlag:</strong> Sind unter den neuen Einträgen mindestens " + r + " mit bekannter Ransomware-Nutzung, steigt die Stufe um eine Ebene.</p>",
        "<p><strong>Woher die Schwellen kommen:</strong> aus den letzten " + m + " Monaten des Katalogs (das Anlaufjahr 2022 zählt nicht mit). " + e + " ist das 75. Perzentil, " + h + " das 90. Perzentil der 30-Tage-Zählung (Median " + med + "). Erhöht heißt also: mehr Neuzugänge als in drei von vier üblichen Zeiträumen.</p>",
        "<p class='dim'>Nicht Teil des Pegels: die Prognose (EPSS) und die ENISA-Zahlen. Sie dienen nur zur Einordnung. Der Pegel misst Aktivität in Katalogen und Warndiensten, keine Zahl von Angriffen. Alle Regeln: <a href='https://github.com/maxim91136/cyberlage.org/blob/main/RULES.md'>RULES.md</a>.</p>"].join(""); },
      en: function (f, e, h, r, m, med) { return [
        "<p><strong>How the Dreier Gauge arises:</strong> a score from 0 to 100 from eight components in three groups: exploitation (KEV count, pace to KEV, EU KEV, Microsoft), warnings (CERT-Bund, NCSC-NL) and external assessments (BSI Cyber Index, SANS Infocon). Each component is measured against its threshold (top quarter of its history), then averaged per group and across groups. 50 means the rule thresholds are reached on average, 100 twice as far. Levels: below 30 calm, 30 to 49 unremarkable, 50 to 63 tense, 64 to 79 high, from 80 exceptional (provisional).</p><p><strong>Component KEV count:</strong> counted is how many vulnerabilities were newly added to the CISA KEV catalog in the last " + f + " days, worldwide and across all vendors.</p>",
        "<ul><li><strong>low:</strong> fewer than " + e + " new entries</li><li><strong>elevated:</strong> " + e + " to " + (h - 1) + "</li><li><strong>high:</strong> " + h + " or more</li></ul>",
        "<p><strong>Surcharge:</strong> if at least " + r + " of the new entries have known ransomware use, the level goes up by one step.</p>",
        "<p><strong>Where the thresholds come from:</strong> the last " + m + " months of the catalog (the 2022 start-up year is excluded). " + e + " is the 75th percentile and " + h + " the 90th percentile of the 30-day count (median " + med + "). Elevated therefore means more additions than in three out of four typical periods.</p>",
        "<p class='dim'>Not part of the gauge: the forecast (EPSS) and the ENISA figures. They are for context only. The gauge measures activity in catalogs and warning services, not a number of attacks. Full rules: <a href='https://github.com/maxim91136/cyberlage.org/blob/main/RULES.md'>RULES.md</a>.</p>"].join(""); } },
    ab_info: { de: function (f, g, h, sw, a) { return "Die Prognose blickt auf neue Schwachstellen (CVE) der letzten " + f + " Tage, die noch nicht im KEV stehen: " + g + " geprüft, " + h + " davon mit mindestens " + sw + " % geschätzter Wahrscheinlichkeit, in den nächsten 30 Tagen ausgenutzt zu werden. Die Schätzung stammt von EPSS (FIRST), nicht von uns. Die zehn höchsten stehen hier. Stand: " + a + "."; },
               en: function (f, g, h, sw, a) { return "The forecast looks at new vulnerabilities (CVE) of the last " + f + " days that are not yet in the KEV: " + g + " checked, " + h + " of them with at least " + sw + " % estimated probability of being exploited in the next 30 days. The estimate comes from EPSS (FIRST), not from us. The ten highest are listed here. As of: " + a + "."; } },
    ab_zeile: { de: function (p) { return p + " Wahrscheinlichkeit"; }, en: function (p) { return p + " probability"; } },
    keine: { de: "keine Daten", en: "no data" },
    niedrig: { de: "niedrig", en: "low" }, ruhig: { de: "ruhig", en: "calm" }, unauffaellig: { de: "unauffällig", en: "unremarkable" }, angespannt: { de: "angespannt", en: "tense" }, ausserordentlich: { de: "außergewöhnlich", en: "exceptional" }, erhoeht: { de: "erhöht", en: "elevated" }, hoch: { de: "hoch", en: "high" },
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
    v_leg: { de: function (m) { return "Zeitraum: letzte " + m + " Monate, die Basis der Schwellen. Balken: grün unter erhöht-Schwelle, gelb erhöht, rot hoch. Wochenstände, rückwirkend mit den heutigen Schwellen gemessen. Die KEV-Menge wird täglich fortgeschrieben (data/pegel.json), ab heute als live gespeicherter Wert. Quelle: CISA KEV (CC0 1.0), eigene Auswertung."; },
             en: function (m) { return "Period: last " + m + " months, the basis of the thresholds. Bars: green below the elevated threshold, yellow elevated, red high. Weekly values, measured retroactively with today’s thresholds. The KEV count is recorded daily (data/pegel.json), from today as a live stored value. Source: CISA KEV (CC0 1.0), own analysis."; } }
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
    var tt = { "index": "Cyberlage · Dreier Gauge for the cyber threat", "hinweise": "Notes and privacy – Cyberlage" };
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
(function () {
  // Alle Links nach außen und auf Rohdateien öffnen in einem neuen Tab, die Seite selbst bleibt stehen
  document.addEventListener("click", function (e) {
    var l = e.target.closest && e.target.closest("a[href]"); if (!l) return;
    var h = l.getAttribute("href") || "";
    if ((/^https?:\/\//i.test(h) && l.hostname !== location.hostname) || /\.(json|xml|csv|ics)(\?|$)/i.test(h)) { l.target = "_blank"; l.rel = "noopener"; }
  }, true);
})();
