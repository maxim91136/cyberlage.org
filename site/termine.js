/* Patch-Termine, Kalender-Export (.ics) und Terminliste. Aus app.js ausgelagert; nutzt die Helfer aus window.CL. */
(function () {
  "use strict";
  window.CL = window.CL || {};
  var $ = function () { return window.CL.$.apply(null, arguments); };
  var pick = function () { return window.CL.pick.apply(null, arguments); };
  var el = function () { return window.CL.el.apply(null, arguments); };
  var link = function () { return window.CL.link.apply(null, arguments); };
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
      add(z, { n: "Fortinet", l: "https://www.fortiguard.com/psirt", art: "fortinet" });
      add(z, { n: "Ivanti", l: "https://www.ivanti.com/blog/topics/security-advisory", art: "ivanti" });
      add(z, { n: "Citrix", l: "https://support.citrix.com/securitybulletins", art: "citrix" });
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
  window.CL.termine = termine;
  window.CL.inTagen = inTagen;
  window.CL.zeigeTermine = zeigeTermine;
})();
