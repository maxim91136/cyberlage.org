"""Eigene Seite je Bericht: /bericht/2026-10/ (Deutsch) und /en/bericht/2026-10/ (Englisch), dazu je eine Übersicht.

Die Seiten sind fertiges HTML ohne Skript, damit Suchmaschinen und Link-Vorschauen sie ohne Rendern lesen.
Alle Zahlen kommen aus site/data/berichte.json (gerechnet in modell.berichte), hier wird nichts gerechnet.
"""
import html
import json
from datetime import date, timedelta

BASIS = "https://cyberlage.org"
MON_EN = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
T = {
    "de": {"pfad": "/bericht/", "start": "/", "h_alle": "Berichte: Dreier-Pegel je Monat, Quartal und Jahr",
           "intro": "Der Dreier-Pegel für jeden abgeschlossenen Monat, jedes Quartal und Jahr: Mittel, Höchst- und Tiefststand, Stufenwechsel und die Bausteine.",
           "monat": "Monate", "quartal": "Quartale", "jahr": "Jahre", "titel": "Cyber-Bedrohungslage %s: Dreier-Pegel %s (%s) · Cyberlage", "h1": "Dreier-Pegel %s",
           "mittel": "Mittel", "hoch": "Höchststand", "tief": "Tiefststand", "wechsel": "Stufenwechsel", "tage": "Tage", "je_stufe": "Tage je Stufe", "bausteine": "Bausteine",
           "th": ("Baustein", "Mittel", "Tage ≥ 1", "Δ"), "vor": {"monat": "Vormonat", "quartal": "Vorquartal", "jahr": "Vorjahr"}, "zum": " zum ",
           "leg": "Mittel: Messwert im Verhältnis zur Schwelle, 1 = Schwelle erreicht, wie im Pegel höchstens 2. Tage ≥ 1: Anteil der Tage an oder über der Schwelle. Δ: Veränderung des Mittels zum %s.",
           "logbuch": "Logbuch im Zeitraum", "rueck": "zurückgerechnet aus den Archivdaten, ohne die Gruppe Externe Einschätzungen",
           "live": "ab %s gespeicherter Tagesstand aller Bausteine, davor zurückgerechnet", "frueher": "← %s", "spaeter": "%s →", "alle": "Alle Berichte",
           "heute": "Dreier-Pegel heute", "regeln": "Regeln", "andere": "English", "fuss": "Ein privates Projekt von Dreier Labs, keine amtliche Stelle. Feste Sätze nach Regeln, keine Vorhersage."},
    "en": {"pfad": "/en/bericht/", "start": "/en/", "h_alle": "Reports: Dreier Gauge per month, quarter and year",
           "intro": "The Dreier Gauge for every completed month, quarter and year: average, high and low, level changes and the components.",
           "monat": "Months", "quartal": "Quarters", "jahr": "Years", "titel": "Cyber threat level %s: Dreier Gauge %s (%s) · Cyberlage", "h1": "Dreier Gauge %s",
           "mittel": "Average", "hoch": "High", "tief": "Low", "wechsel": "Level changes", "tage": "days", "je_stufe": "Days per level", "bausteine": "Components",
           "th": ("Component", "Average", "Days ≥ 1", "Δ"), "vor": {"monat": "previous month", "quartal": "previous quarter", "jahr": "previous year"}, "zum": " vs. ",
           "leg": "Average: reading relative to its threshold, 1 = threshold reached, capped at 2 as in the gauge. Days ≥ 1: share of days at or above the threshold. Δ: change of the average vs. the %s.",
           "logbuch": "Logbook in this period", "rueck": "back-calculated from the archive data, without the group external assessments",
           "live": "from %s stored daily value of all components, back-calculated before", "frueher": "← %s", "spaeter": "%s →", "alle": "All reports",
           "heute": "Dreier Gauge today", "regeln": "Rules", "andere": "Deutsch", "fuss": "A private project by Dreier Labs, not an official body. Fixed sentences by rule, no forecast."},
}


def _e(t):
    return html.escape(str(t))


def _zahl(v, n, sp):
    s = "%.*f" % (n, v)
    return s.replace(".", ",") if sp == "de" else s


def _vz(v, n, sp):
    if v is None:
        return "–"
    return ("+" if v > 0 else "−" if v < 0 else "±") + _zahl(abs(v), n, sp)


def _datum(iso, sp, kurz=False):
    j, m, t = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
    if sp == "de":
        return "%d.%d." % (t, m) if kurz else "%02d.%02d.%d" % (t, m, j)
    return "%d %s" % (t, MON_EN[m - 1]) if kurz else "%d %s %d" % (t, MON_EN[m - 1], j)


def _kopf(sp, titel, beschreibung, pfad_de, pfad_en, extra=""):
    eigen = pfad_en if sp == "en" else pfad_de
    return ('<!doctype html>\n<html lang="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="dark">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n<link rel="canonical" href="%s%s">\n'
            '<link rel="alternate" hreflang="de" href="%s%s">\n<link rel="alternate" hreflang="en" href="%s%s">\n<link rel="alternate" hreflang="x-default" href="%s%s">\n'
            '<meta property="og:title" content="%s">\n<meta property="og:description" content="%s">\n<meta property="og:url" content="%s%s">\n<meta property="og:type" content="article">\n'
            '<meta property="og:image" content="%s/og.png">\n<meta name="twitter:card" content="summary_large_image">\n'
            '<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
            '<meta name="theme-color" content="#06090b">\n<link rel="stylesheet" href="/style.css">%s</head>\n'
            '<body class="bs"><header class="kopf"><div class="wrap marke"><a class="brand" href="%s"><img src="/favicon.svg" width="30" height="30" alt=""><span>cyberlage<span class="dim">.org</span></span></a></div>'
            '<div class="wrap bs-zurueck"><a class="mono" href="%s">%s</a></div></header>\n'
            % (sp, _e(titel), _e(beschreibung), BASIS, eigen, BASIS, pfad_de, BASIS, pfad_en, BASIS, pfad_de, _e(titel), _e(beschreibung), BASIS, eigen, BASIS, extra, T[sp]["start"], T[sp]["start"], "← Dreier Gauge" if sp == "en" else "← Dreier-Pegel"))


def _fuss(sp, andere_pfad):
    t = T[sp]
    return ('<p class="bs-nav mono"><a href="%s">%s</a> · <a href="%s">%s</a> · <a href="/RULES.md">%s</a> · <a href="%s" hreflang="%s">%s</a></p>\n'
            '<p class="mono dim fine">%s</p>\n</main></body></html>\n'
            % (t["pfad"], t["alle"], t["start"], t["heute"], t["regeln"], andere_pfad, "de" if sp == "en" else "en", t["andere"], t["fuss"]))


def seite(b, sp, daten, davor=None, danach=None):
    """Eine Berichtsseite als HTML. b: Bericht aus berichte.json; davor/danach: Nachbarn gleicher Art oder None."""
    t, en = T[sp], sp == "en"
    name = b["titel_en"] if en else b["titel"]
    stufe = b["stufe"]["name_en"] if en else b["stufe"]["name"]
    satz = b["satz_en"] if en else b["satz"]
    vor = t["vor"][b["art"]]
    ld = {"@context": "https://schema.org", "@type": "Report", "headline": t["h1"] % name, "description": satz, "inLanguage": sp,
          "datePublished": (date.fromisoformat(b["bis"]) + timedelta(days=1)).isoformat(), "dateModified": daten.get("stand"),
          "temporalCoverage": "%s/%s" % (b["von"], b["bis"]), "url": BASIS + t["pfad"] + b["id"] + "/",
          "publisher": {"@type": "Organization", "name": "Dreier Labs", "url": "https://dreierlabs.com/"}, "isPartOf": {"@type": "WebSite", "name": "Cyberlage", "url": BASIS + t["start"]}}
    extra = '\n<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>"
    z = [_kopf(sp, t["titel"] % (name, _zahl(b["mittel"], 1, sp), stufe), satz, "/bericht/%s/" % b["id"], "/en/bericht/%s/" % b["id"], extra)]
    z.append('<main class="wrap bs-main"><article class="br ra-%s">\n<div class="br-k"><h1>%s</h1><span class="br-st mono">%s · %s</span></div>\n<p class="br-satz">%s</p>\n'
             % (_e(b["stufe"]["ampel"]), _e(t["h1"] % name), _e(stufe), _zahl(b["mittel"], 1, sp), _e(satz)))
    kz = ((t["mittel"], _zahl(b["mittel"], 1, sp), "" if b["delta"] is None else _vz(b["delta"], 1, sp) + t["zum"] + vor),
          (t["hoch"], str(b["hoch"]["wert"]), _datum(b["hoch"]["datum"], sp, True)), (t["tief"], str(b["tief"]["wert"]), _datum(b["tief"]["datum"], sp, True)),
          (t["wechsel"], str(b["wechsel"]), "%d %s" % (b["tage"], t["tage"])))
    z.append('<div class="br-kzs">' + "".join('<div class="br-kz"><span class="mono dim">%s</span><strong class="mono">%s</strong>%s</div>'
                                              % (_e(a), _e(w), '<span class="dim">%s</span>' % _e(x) if x else "") for a, w, x in kz) + "</div>\n")
    z.append('<p class="lbl mono">%s</p>\n<div class="br-band">%s</div>\n<p class="br-leg mono dim">%s</p>\n' % (
        _e(t["je_stufe"]),
        "".join('<span class="sg ra-%s" style="width:%.3f%%"></span>' % (_e(s["ampel"]), 100.0 * s["tage"] / b["tage"]) for s in b["je_stufe"]),
        "".join('<span class="br-li"><i class="sg ra-%s"></i>%s %d</span>' % (_e(s["ampel"]), _e(s["name_en"] if en else s["name"]), s["tage"]) for s in b["je_stufe"])))
    if b["bausteine"]:
        z.append('<p class="lbl mono">%s</p>\n<div class="br-tab"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>\n<p class="br-leg2 dim">%s</p>\n' % (
            _e(t["bausteine"]), "".join("<th>%s</th>" % _e(x) for x in t["th"]),
            "".join('<tr><td>%s</td><td class="mono%s">%s</td><td class="mono">%d %%</td><td class="mono dim">%s</td></tr>'
                    % (_e(c["name_en"] if en else c["name"]), " rw" if c["mittel"] >= 1 else "", _zahl(c["mittel"], 2, sp), c["ueber"], _vz(c["delta"], 2, sp)) for c in b["bausteine"]),
            _e(t["leg"] % vor)))
    if b["logbuch"]:
        z.append('<p class="lbl mono">%s</p>\n<ul class="br-lb">%s</ul>\n' % (_e(t["logbuch"]), "".join(
            '<li><time class="mono dim" datetime="%s">%s</time> %s</li>' % (_e(x["datum"]), _datum(x["datum"], sp), _e(x["titel_en"] if en else x["titel"])) for x in b["logbuch"])))
    grund = t["rueck"] if b["bis"] < daten.get("live_seit", "9999") else t["live"] % _datum(daten["live_seit"], sp)
    z.append('<p class="br-fuss mono dim">%s – %s · %s</p>\n</article>\n' % (_datum(b["von"], sp), _datum(b["bis"], sp), _e(grund)))
    nachbarn = []
    if davor:
        nachbarn.append('<a rel="prev" href="%s%s/">%s</a>' % (t["pfad"], davor["id"], _e(t["frueher"] % (davor["titel_en"] if en else davor["titel"]))))
    if danach:
        nachbarn.append('<a rel="next" href="%s%s/">%s</a>' % (t["pfad"], danach["id"], _e(t["spaeter"] % (danach["titel_en"] if en else danach["titel"]))))
    if nachbarn:
        z.append('<p class="bs-nb mono">%s</p>\n' % "".join(nachbarn))
    z.append(_fuss(sp, ("/bericht/" if en else "/en/bericht/") + b["id"] + "/"))
    return "".join(z)


def uebersicht(berichte, sp):
    t, en = T[sp], sp == "en"
    z = [_kopf(sp, t["h_alle"] + " · Cyberlage", t["intro"], "/bericht/", "/en/bericht/"),
         '<main class="wrap bs-main"><h1>%s</h1>\n<p class="dim">%s</p>\n' % (_e(t["h_alle"]), _e(t["intro"]))]
    for art in ("jahr", "quartal", "monat"):
        liste = [b for b in berichte if b["art"] == art]
        if not liste:
            continue
        z.append('<h2 class="mono">%s</h2>\n<ul class="bs-liste">%s</ul>\n' % (_e(t[art]), "".join(
            '<li class="ra-%s"><a href="%s%s/">%s</a><span class="mono">%s · %s</span></li>'
            % (_e(b["stufe"]["ampel"]), t["pfad"], b["id"], _e(b["titel_en"] if en else b["titel"]), _zahl(b["mittel"], 1, sp), _e(b["stufe"]["name_en"] if en else b["stufe"]["name"])) for b in liste)))
    z.append(_fuss(sp, "/bericht/" if en else "/en/bericht/"))
    return "".join(z)


def schreibe(site, daten):
    """Schreibt alle Berichtsseiten unter site/bericht/ und site/en/bericht/. Gibt [(pfad_de, pfad_en, lastmod oder None)] für die Sitemap zurück."""
    berichte = daten.get("berichte") or []
    if not berichte:
        return []
    out = [("/bericht/", "/en/bericht/", daten.get("stand"))]
    for sp in ("de", "en"):
        ziel = site / T[sp]["pfad"].strip("/")
        ziel.mkdir(parents=True, exist_ok=True)
        (ziel / "index.html").write_text(uebersicht(berichte, sp), encoding="utf-8")
        for art in ("monat", "quartal", "jahr"):
            reihe = sorted([b for b in berichte if b["art"] == art], key=lambda b: b["bis"])
            for i, b in enumerate(reihe):
                (ziel / b["id"]).mkdir(exist_ok=True)
                (ziel / b["id"] / "index.html").write_text(seite(b, sp, daten, reihe[i - 1] if i else None, reihe[i + 1] if i + 1 < len(reihe) else None), encoding="utf-8")
    for b in sorted(berichte, key=lambda b: b["bis"], reverse=True):
        out.append(("/bericht/%s/" % b["id"], "/en/bericht/%s/" % b["id"], None))  # ohne lastmod: die Seiten werden bei jedem Lauf neu gerechnet
    return out
