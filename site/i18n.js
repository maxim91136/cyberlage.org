(function () {
  "use strict";
  var L = "de";
  try { var g = localStorage.getItem("lang"); if (g === "de" || g === "en") L = g; else L = (navigator.language || "de").slice(0, 2) === "de" ? "de" : "en"; }
  catch (e) { L = (navigator.language || "de").slice(0, 2) === "de" ? "de" : "en"; }

  // Englische Texte für Elemente mit data-t (Deutsch steht im HTML). Nur eigene, feste Texte.
  var EN = {
    skip: "Skip to content",
    beta: "<b>BETA</b> · more coming soon",
    n_rueck: "/history", n_neu: "/new",
    tab_kev: "KEV catalog", i_quellen: "Sources", i_begriffe: "Terms", i_methode: "Method", i_hinweise: "Notes",
    h_lbl: 'as of <span id="stand">…</span> · situation picture from open sources',
    h_titel: "The global cyber situation, rule-based and openly sourced.",
    h_lead: "Worldwide, across all vendors: we count the vulnerabilities that bodies such as CISA report as exploited and combine them into one level using open rules. No statement about any one country or sector. For everyone who defends.",
    tg_btn: "Subscribe to the Telegram channel",
    tg_txt: " new entries, critical warnings and level changes as soon as they appear.",
    h_lage: "Current situation",
    l_wie: "how the level is calculated",
    l_stufe: "lage.level · worldwide", l_lade: "Loading data",
    l_7: "new · 7 days", l_30: "new · 30 days", l_ges: "catalog total",
    l_kev: "<strong>KEV</strong> stands for <em>Known Exploited Vulnerabilities</em>: a list by the US cybersecurity agency <strong>CISA</strong> of flaws that are proven to be exploited by attackers. The level shows how many are newly added.",
    r_h: "## history", n_h: "## new",
    n_sub: 'Exploited vulnerabilities of the last <span id="fenster">30</span> days, newest first. The filter runs only in your browser.',
    n_filter: "Filter by vendor, product or CVE", n_ph: "e.g. microsoft, fortinet, CVE-2026",
    th1: "Added", th2: "Vendor", th3: "Product", th5: "Due date (CISA)",
    n_q1: "Source: CISA KEV (CC0 1.0). The due date applies to US federal agencies and is only a guide. Links lead to the NIST CVE page (NVD). No attack details.",
    n_q2: "Source: CERT-Bund, the computer emergency team of the <strong>BSI</strong> (German Federal Office for Information Security), via wid.cert-bund.de. Only title, severity, date and link are reused; the texts are at the BSI. No indication of any cooperation with the BSI.",
    n_q3: "Source: EU Vulnerability Database (EUVD) of <strong>ENISA</strong>, the EU Agency for Cybersecurity. The licence is not explicitly clarified, so only ID, CVE, vendor and link are shown.",
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
    f_links: '<a href="https://dreierlabs.com/impressum.html">legal notice</a> · <a href="hinweise.html">notes &amp; privacy</a>',
    top: "Back to top",
    // hinweise.html
    hw_titel: "Notes and privacy",
    hw_anbieter: 'This site is operated by Dreier Labs. The full legal notice is at <a href="https://dreierlabs.com/impressum.html">dreierlabs.com/impressum.html</a>.',
    hw_h1: "## notes", hw_h2: "## privacy",
    hw_l1: "Cyberlage is a private project of Dreier Labs and not an official body. There is no connection to the BSI or any other authority.",
    hw_l2: "The content is an analysis of openly licensed sources and no substitute for warnings from the BSI or a CERT. No guarantee of accuracy or completeness.",
    hw_l3: "The operators of linked sites are responsible for them.",
    hw_ds: 'This site sets no cookies and embeds no tracking or third-party services. When you visit, the hosting provider (Cloudflare) processes technically necessary connection data. More: <a href="https://dreierlabs.com/datenschutz.html">privacy policy of Dreier Labs</a>.',
    hw_zurueck: "Back to the start page"
  };

  // Dynamische Texte (Funktionen oder Strings je Sprache)
  var S = {
    rechnung: { de: function (f, e, h, r, m, med) { return [
        "<p><strong>Gezählt wird:</strong> wie viele Schwachstellen in den letzten " + f + " Tagen neu in den CISA-KEV-Katalog aufgenommen wurden, weltweit und über alle Hersteller.</p>",
        "<ul><li><strong>niedrig:</strong> weniger als " + e + " neue Einträge</li><li><strong>erhöht:</strong> " + e + " bis " + (h - 1) + "</li><li><strong>hoch:</strong> " + h + " oder mehr</li></ul>",
        "<p><strong>Aufschlag:</strong> Sind unter den neuen Einträgen mindestens " + r + " mit bekannter Ransomware-Nutzung, steigt die Stufe um eine Ebene.</p>",
        "<p><strong>Woher die Schwellen kommen:</strong> aus den letzten " + m + " Monaten des Katalogs (das Anlaufjahr 2022 zählt nicht mit). " + e + " ist das 75. Perzentil, " + h + " das 90. Perzentil der 30-Tage-Zählung (Median " + med + "). Erhöht heißt also: mehr Neuzugänge als in drei von vier üblichen Zeiträumen.</p>",
        "<p class='dim'>Nicht Teil der Stufe: CERT-Bund, EU-KEV und die ENISA-Zahlen. Sie dienen nur zur Einordnung. Die Stufe misst Aktivität im Katalog, keine Zahl von Angriffen. Alle Regeln: <a href='https://github.com/maxim91136/cyberlage.org/blob/main/RULES.md'>RULES.md</a>.</p>"].join(""); },
      en: function (f, e, h, r, m, med) { return [
        "<p><strong>What is counted:</strong> how many vulnerabilities were newly added to the CISA KEV catalog in the last " + f + " days, worldwide and across all vendors.</p>",
        "<ul><li><strong>low:</strong> fewer than " + e + " new entries</li><li><strong>elevated:</strong> " + e + " to " + (h - 1) + "</li><li><strong>high:</strong> " + h + " or more</li></ul>",
        "<p><strong>Surcharge:</strong> if at least " + r + " of the new entries have known ransomware use, the level goes up by one step.</p>",
        "<p><strong>Where the thresholds come from:</strong> the last " + m + " months of the catalog (the 2022 start-up year is excluded). " + e + " is the 75th percentile and " + h + " the 90th percentile of the 30-day count (median " + med + "). Elevated therefore means more additions than in three out of four typical periods.</p>",
        "<p class='dim'>Not part of the level: CERT-Bund, EU-KEV and the ENISA figures. They are for context only. The level measures activity in the catalog, not a number of attacks. Full rules: <a href='https://github.com/maxim91136/cyberlage.org/blob/main/RULES.md'>RULES.md</a>.</p>"].join(""); } },
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
    v_leg: { de: "Balken: grün unter erhöht-Schwelle, gelb erhöht, rot hoch. Wochenstände, auch rückwirkend mit den heutigen Schwellen gemessen. Quelle: CISA KEV (CC0 1.0), eigene Auswertung.",
             en: "Bars: green below the elevated threshold, yellow elevated, red high. Weekly values, also measured retroactively with today’s thresholds. Source: CISA KEV (CC0 1.0), own analysis." }
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
