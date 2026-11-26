"""Linkseite /links/ (Deutsch) und /en/links/ (Englisch): von uns ausgewählte, einzeln geprüfte Seiten zu Lage, Schwachstellen und Angriffsdaten.

Fertiges HTML ohne Skript aus data/links.json (von Hand gepflegt, je Eintrag mit Prüfdatum; der Prüfkalender in pruefen.py prüft die Erreichbarkeit).
Die Sammlung hat keinen Einfluss auf Pegel oder Regeln. Nichts davon ist bezahlt oder vermittelt."""
import html
import json
from datetime import date
from pathlib import Path

import berichtseiten as bs

BASIS = bs.BASIS
MON_EN = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

T = {
    "de": {"pfad": "/links/", "andere": "English", "start": "/", "titel": "Weitere Quellen: ausgewählte Lagebilder und Datenseiten · Cyberlage",
           "beschr": "Von Cyberlage ausgewählte und einzeln geprüfte Seiten zu Cyberlage, Schwachstellen und Angriffsdaten: Behörden, Kommunen, Sensoren, Ransomware.",
           "h1": "Weitere Quellen",
           "intro": ("Eine kleine Sammlung von Seiten, die wir selbst lesen und für nützlich halten. Jede Seite wurde einzeln geprüft: erreichbar, Betreiber erkennbar, Aktualität sichtbar.",
                     "Die Sammlung hat keinen Einfluss auf den Dreier-Pegel. Was dort einfließt, ist als „im Dreier-Pegel“ markiert. Die Links sind weder bezahlt noch vermittelt."),
           "pegel": "im Dreier-Pegel", "von": "Betreiber", "pflege": "Pflege", "geprueft": "geprüft am", "oeffnet": "öffnet in neuem Tab",
           "fuss_h": "Hinweise",
           "fuss": ("Von Hand gepflegte Listen können Lücken haben oder veralten. Wo eine Seite Vorfälle sammelt, heißt das nicht, dass jeder Vorfall erfasst ist.",
                    "Fehlt eine gute Seite? Vorschläge gern per Hinweis an uns. Aufgenommen wird nur, was wir geprüft haben."),
           "heute": "Dreier-Pegel heute", "audit": "Web-Audit", "regeln": "Regeln", "projekt": "Ein privates Projekt von Dreier Labs, keine amtliche Stelle. Feste Regeln, keine Vorhersage."},
    "en": {"pfad": "/en/links/", "andere": "Deutsch", "start": "/en/", "titel": "More sources: selected situation reports and data sites · Cyberlage",
           "beschr": "Sites selected and individually checked by Cyberlage on the cyber situation, vulnerabilities and attack data: agencies, municipalities, sensors, ransomware.",
           "h1": "More sources",
           "intro": ("A small collection of sites we read ourselves and find useful. Each one was checked individually: reachable, operator identifiable, freshness visible.",
                     "The collection has no influence on the Dreier Gauge. What does feed into it is marked “in the Dreier Gauge”. The links are neither paid nor brokered."),
           "pegel": "in the Dreier Gauge", "von": "Operator", "pflege": "Upkeep", "geprueft": "checked on", "oeffnet": "opens in a new tab",
           "fuss_h": "Notes",
           "fuss": ("Hand-kept lists can have gaps or go stale. Where a site collects incidents, that does not mean every incident is covered.",
                    "Missing a good site? Suggestions welcome via the contact notice. We only add what we have checked."),
           "heute": "Dreier Gauge today", "audit": "Web audit", "regeln": "Rules", "projekt": "A private project by Dreier Labs, not an official body. Fixed rules, no forecast."},
}


def _e(t):
    return html.escape(str(t), quote=True)


def _datum(iso, sp):
    j, m, t = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
    return "%02d.%02d.%d" % (t, m, j) if sp == "de" else "%d %s %d" % (t, MON_EN[m - 1], j)


def lies(wurzel):
    return json.loads((Path(wurzel) / "data" / "links.json").read_text(encoding="utf-8"))


def _pflege_en(p):
    return {"amtlich, jährlich": "official, annual", "amtlich, laufend": "official, ongoing", "von Hand, aus öffentlichen Berichten": "by hand, from public reports",
            "von Hand, offenes Wiki": "by hand, open wiki", "automatisch, Honeypots": "automatic, honeypots", "automatisch und Redaktion": "automatic and editorial",
            "automatisch, Sensoren und Partner": "automatic, sensors and partners", "automatisch, eigene Messungen": "automatic, own measurements",
            "automatisch, täglich": "automatic, daily", "automatisch, Leak-Seiten-Monitoring": "automatic, leak-site monitoring", "automatisch, Community": "automatic, community",
            "jährlich": "annual"}.get(p, p)


def seite(sp, daten):
    t = T[sp]
    andere = T["en" if sp == "de" else "de"]["pfad"]
    z = [bs._kopf(sp, t["titel"], t["beschr"], T["de"]["pfad"], T["en"]["pfad"]),
         '<main class="wrap bs-main"><h1>%s</h1>\n%s\n' % (_e(t["h1"]), "".join('<p class="dim ln-intro">%s</p>' % _e(p) for p in t["intro"]))]
    for g in daten["gruppen"]:
        eintraege = [x for x in daten["links"] if x["gruppe"] == g["id"]]
        if not eintraege:
            continue
        z.append('<h2 class="ln-h">%s</h2>\n<div class="ln-liste">\n' % _e(g[sp]))
        for x in eintraege:
            marke = '<span class="ln-pegel mono">%s</span>' % _e(t["pegel"]) if x["im_pegel"] else ""
            pflege = x["pflege"] if sp == "de" else _pflege_en(x["pflege"])
            z.append('<article class="ln-k"><h3><a href="%s" target="_blank" rel="noopener" title="%s">%s</a>%s</h3>'
                     '<p class="ln-text">%s</p><p class="ln-meta mono dim">%s: %s · %s: %s · %s %s</p></article>\n'
                     % (_e(x["url"]), _e(t["oeffnet"]), _e(x["name"]), marke, _e(x[sp]), _e(t["von"]), _e(x["betreiber"]), _e(t["pflege"]), _e(pflege), _e(t["geprueft"]), _e(_datum(x["geprueft_am"], sp))))
        z.append("</div>\n")
    z.append('<h2 class="ln-h">%s</h2>\n%s' % (_e(t["fuss_h"]), "".join('<p class="dim ln-intro">%s</p>' % _e(p) for p in t["fuss"])))
    z.append('<p class="bs-nav mono"><a href="%s">%s</a> · <a href="%s">%s</a> · <a href="/RULES.md">%s</a> · <a href="%s" hreflang="%s">%s</a></p>\n<p class="mono dim fine">%s</p>\n</main></body></html>\n'
             % (t["start"], _e(t["heute"]), "/audit/" if sp == "de" else "/en/audit/", _e(t["audit"]), _e(t["regeln"]), andere, "en" if sp == "de" else "de", _e(t["andere"]), _e(t["projekt"])))
    return "".join(z)


def schreibe(wurzel):
    """Schreibt site/links/index.html und site/en/links/index.html. Gibt [(pfad_de, pfad_en, lastmod)] für die Sitemap zurück."""
    wurzel = Path(wurzel)
    daten = lies(wurzel)
    for sp in ("de", "en"):
        ziel = wurzel / "site" / T[sp]["pfad"].strip("/")
        ziel.mkdir(parents=True, exist_ok=True)
        (ziel / "index.html").write_text(seite(sp, daten), encoding="utf-8")
    return [("/links/", "/en/links/", max(x["geprueft_am"] for x in daten["links"]))]
