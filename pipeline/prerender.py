#!/usr/bin/env python3
"""Schreibt die wichtigsten Werte als echten Text in site/index.html (Bereich <noscript>),
damit auch Crawler und Filter ohne JavaScript Inhalt sehen. Nur Standardbibliothek."""
import html
from datetime import datetime, timezone
import json
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
NAME = {"niedrig": "niedrig", "erhoeht": "erhöht", "ruhig": "ruhig", "unauffaellig": "unauffällig", "angespannt": "angespannt", "hoch": "hoch", "ausserordentlich": "außergewöhnlich", None: "keine Bewertung"}


def kurzlage(lage):
    """Ein Satz für Maschinen und Vorschauen: Stufe, Score, Zahl der Bausteine."""
    pg = lage.get("pegel") or {}
    if not lage.get("stufe") or not isinstance(pg.get("wert"), int):
        return ""
    return "Dreier-Pegel am %s: %s, %d von 100 (aus %s von %s Bausteinen)." % (".".join(reversed(str(lage["stand"])[:10].split("-"))), NAME.get(lage["stufe"], lage["stufe"]), pg["wert"], pg.get("signale"), pg.get("von"))


def baustein(lage):
    e = lambda t: html.escape(str(t))
    k = lage["kev"]
    fz = lage.get("fazit") or {}
    sig = [x for x in ((lage.get("radar") or {}).get("konsens") or {}).get("signale", []) if isinstance(x.get("ausschlag"), (int, float))]
    zahl = lambda v: ("%.2f" % v).rstrip("0").rstrip(".").replace(".", ",")
    zeilen = [
        f'<p class="panel pad"><b>Die globale Cyberlage, Stand {e(lage["stand"])}, Dreier-Pegel: {e(NAME.get(lage.get("stufe"), "keine Bewertung"))}.</b> '
        f'{e(lage.get("stufe_begruendung") or "")} Neu im CISA-Katalog ausgenutzter Schwachstellen: {e(k["neu_7_tage"])} in 7 Tagen, {e(k["neu_30_tage"])} in 30 Tagen. '
        'Regelbasiert und offen belegt. Ein privates Projekt von Dreier Labs, keine amtliche Stelle.</p>',
    ]
    if fz.get("stufe_satz"):
        zeilen.append(f'<p class="panel pad"><b>Lage:</b> {e(fz["stufe_satz"])} <b>Treiber:</b> {e(fz.get("treiber") or "")} <b>Empfehlung:</b> {e(fz.get("hinweis") or "")}</p>')
    if sig:
        zeilen.append('<p class="panel pad"><b>Bausteine des Dreier-Pegels</b> (Messwert im Verhältnis zur Schwelle, 1,0 = Schwelle erreicht): '
                      + "; ".join("%s %s" % (e(x["name"]), zahl(x["ausschlag"])) for x in sig)
                      + '. Stufen: unter 35 ruhig, 35 bis 49 unauffällig, 50 bis 63 angespannt, 64 bis 79 hoch, ab 80 außergewöhnlich.</p>')
    zeilen.append('<p class="panel pad">Die Zahlen stehen als Rohdaten unter <a href="data/lage.json">data/lage.json</a>, die Regeln unter <a href="RULES.md">RULES.md</a>. Für die Ansicht mit Verlauf und Listen wird JavaScript benötigt.</p>')
    return "".join(zeilen)


def siegel_fuss(en=False):
    """Siegel mit Kurztext für den Fuß der Startseite aus data/audit/cyberlage.org.json; ohne Daten oder Score leer."""
    import auditseiten
    try:
        d = json.loads((WURZEL / "data" / "audit" / "cyberlage.org.json").read_text(encoding="utf-8"))
        regeln = json.loads((WURZEL / "audit" / "regeln.json").read_text(encoding="utf-8"))
        jetzt = datetime.now(timezone.utc)
        if d.get("score") is None:
            return ""
        de, e_ = auditseiten.fuss_text(d, regeln, "de", jetzt), auditseiten.fuss_text(d, regeln, "en", jetzt)
    except (OSError, ValueError, KeyError):
        return ""
    q = lambda t: html.escape(t, quote=True)
    web = ('<a class="fuss-siegel" id="fuss-siegel" href="%s" data-de="%s" data-en="%s"><img src="/audit/siegel/cyberlage.org.svg" width="72" height="72" alt="" loading="lazy">'
           '<span class="mono dim">%s</span></a>') % ("/en/audit/" if en else "/audit/", q(de), q(e_), q(e_ if en else de))
    return web + siegel_fuss_code(en)


def siegel_fuss_code(en=False):
    """Zweites Siegel im Fuß: das Dreier-Code-Siegel aus data/codeaudit/cyberlage.org.json; ohne Daten oder Score leer."""
    import auditseiten
    import codeauditseiten
    try:
        d = codeauditseiten.lies(WURZEL)
        regeln = codeauditseiten.regeln_lesen(WURZEL)
        if d is None or d.get("score") is None:
            return ""
        jetzt = datetime.now(timezone.utc)
        de, e_ = codeauditseiten.fuss_text(d, regeln, "de", jetzt), codeauditseiten.fuss_text(d, regeln, "en", jetzt)
    except (OSError, ValueError, KeyError):
        return ""
    q = lambda t: html.escape(t, quote=True)
    return ('<a class="fuss-siegel" id="fuss-siegel-code" href="%s#code-audit" data-de="%s" data-en="%s"><img src="/audit/siegel/%s.svg" width="72" height="72" alt="" loading="lazy">'
            '<span class="mono dim">%s</span></a>') % ("/en/audit/" if en else "/audit/", q(de), q(e_), auditseiten.html.escape(codeauditseiten.SVG_NAME), q(e_ if en else de))


def vorbelegen(s, lage):
    """Startwerte direkt ins HTML, damit vor dem Laden der Daten kein Platzhalter steht. JavaScript überschreibt sie danach."""
    e = lambda t: html.escape(str(t))
    k = lage["kev"]
    if lage.get("stufe"):
        s = re.sub(r'(<div class="stufe mono" id="stufe-wert">)[^<]*(</div>)', lambda m: m.group(1) + e(NAME[lage["stufe"]]) + m.group(2), s, count=1)
        s = re.sub(r'<div class="stufe-text" id="stufe-text"[^>]*>[^<]*</div>', '<div class="stufe-text" id="stufe-text" hidden></div>', s, count=1)
    for kennung, wert in (("k7", k.get("neu_7_tage")), ("k30", k.get("neu_30_tage")), ("kall", k.get("gesamt")), ("kr", k.get("ransomware_bekannt_30_tage"))):
        if isinstance(wert, int):
            s = re.sub(r'(<b id="%s">)[^<]*(</b>)' % kennung, lambda m: m.group(1) + f"{wert:,}".replace(",", ".") + m.group(2), s, count=1)  # noqa: B023 (Lambda läuft sofort in re.sub)
    kurz = kurzlage(lage)
    if kurz:
        fest = " Seismograph der Cyber-Bedrohungslage aus zehn offenen Bausteinen, regelbasiert und nachprüfbar. Ein Werkzeug für alle, die Systeme verteidigen. Ein Projekt von Dreier Labs."
        s = re.sub(r'(<meta name="description" content=")[^"]*(">)', lambda m: m.group(1) + e(kurz + fest) + m.group(2), s, count=1)
        s = re.sub(r'(<meta property="og:description" content=")[^"]*(">)', lambda m: m.group(1) + e(kurz + " Regelbasiert aus offenen Quellen.") + m.group(2), s, count=1)
        pg = lage["pegel"]
        s = re.sub(r'<a id="hero-pegel"[^>]*>[^<]*</a>', lambda m: '<a id="hero-pegel" class="hero-pegel mono st-%s" href="#lage">Dreier-Pegel heute: %s · %d / 100  · Details</a>' % (e(lage["stufe"]), e(NAME[lage["stufe"]].upper()), pg["wert"]), s, count=1)
    s = re.sub(r"<!--kt-start-->.*?<!--kt-end-->", lambda m: "<!--kt-start-->" + e(kurztext(lage)) + "<!--kt-end-->", s, count=1, flags=re.S)
    s = re.sub(r"<!--sg-start-->.*?<!--sg-end-->", lambda m: "<!--sg-start-->" + siegel_fuss() + "<!--sg-end-->", s, count=1, flags=re.S)
    li = "".join(f"<li>{e(t)}</li>" for t in lage.get("hinweise") or [])
    if li:
        s = re.sub(r'(<ul id="hinweise" class="hinw">).*?(</ul>)', lambda m: m.group(1) + li + m.group(2), s, count=1, flags=re.S)
    return s


BASIS = "https://cyberlage.org"


def kurztext(lage, en=False):
    """Sichtbarer Kurztext unter dem Pegel (derselbe Aufbau wie in app.js): Score, Zahl der Bausteine, neue KEV-Einträge."""
    pg, k = lage.get("pegel") or {}, lage.get("kev") or {}
    if not isinstance(pg.get("wert"), int):
        return ""
    if en:
        return "Score %d out of 100, from %s of %s components. Newly added to the CISA catalogue of exploited vulnerabilities: %s in 7 days, %s in 30 days." % (
            pg["wert"], pg.get("signale"), pg.get("von"), k.get("neu_7_tage"), k.get("neu_30_tage"))
    return "Gesamtscore %d von 100 aus %s von %s Bausteinen. Neu im CISA-Katalog ausgenutzter Schwachstellen: %s in 7 Tagen, %s in 30 Tagen." % (
        pg["wert"], pg.get("signale"), pg.get("von"), k.get("neu_7_tage"), k.get("neu_30_tage"))


def stufe_en(lage):
    """Englischer Name der Stufe aus der Skala in lage.json."""
    for x in (lage.get("radar_skala") or {}).get("stufen") or []:
        if x.get("ampel") == lage.get("stufe"):
            return x.get("name_en")
    return None


def titel(lage, en=False):
    """Seitentitel: Tagesstand vorn (im Reiter sichtbar), dahinter der feste Teil mit dem Suchbegriff. Derselbe Aufbau wie in app.js."""
    fest = "Cyberlage: cyber threat level today" if en else "Cyberlage: Cyber-Bedrohungslage heute"
    pg, name = lage.get("pegel") or {}, (stufe_en(lage) if en else NAME.get(lage.get("stufe")))
    return "%s %d · %s" % (name.upper(), pg["wert"], fest) if name and lage.get("stufe") and isinstance(pg.get("wert"), int) else fest


def kurzlage_en(lage):
    pg, name = lage.get("pegel") or {}, stufe_en(lage)
    if not name or not isinstance(pg.get("wert"), int):
        return ""
    return "Dreier Gauge on %s: %s, %d out of 100 (from %s of %s components)." % (str(lage["stand"])[:10], name, pg["wert"], pg.get("signale"), pg.get("von"))


def strukturierte_daten(lage, en=False):
    """JSON-LD: die Seite und der offene Datensatz dahinter. Nur Angaben, die auch auf der Seite stehen."""
    url = BASIS + ("/en/" if en else "/")
    wer = {"@type": "Organization", "name": "Dreier Labs", "url": "https://dreierlabs.com/"}
    daten = [{"@context": "https://schema.org", "@type": "WebSite", "name": "Cyberlage", "url": url, "inLanguage": "en" if en else "de", "publisher": wer},
             {"@context": "https://schema.org", "@type": "Dataset", "name": "Dreier Gauge: daily cyber threat level" if en else "Dreier-Pegel: Tagesstand der Cyber-Bedrohungslage",
              "description": ("Daily score from 0 to 100 for the cyber threat level, computed by fixed rules from ten open components (exploited vulnerabilities, advisories, attack activity, external assessments). Rules and sources are published."
                              if en else "Täglicher Score von 0 bis 100 für die Cyber-Bedrohungslage, nach festen Regeln aus zehn offenen Bausteinen berechnet (ausgenutzte Schwachstellen, Warnungen, Angriffsaktivität, externe Einschätzungen). Regeln und Quellen sind veröffentlicht."),
              "url": url, "creator": wer, "isAccessibleForFree": True, "license": BASIS + "/LICENSE", "dateModified": str(lage.get("stand"))[:10],
              "distribution": [{"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": BASIS + "/data/lage.json"},
                               {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": BASIS + "/data/berichte.json"}]}]
    return '<script type="application/ld+json">' + json.dumps(daten, ensure_ascii=False).replace("</", "<\\/") + "</script>"


def kopf(s, lage, en=False):
    """Titel und strukturierte Daten in den Kopf schreiben."""
    e = lambda t: html.escape(str(t))
    s = re.sub(r"<title>[^<]*</title>", lambda m: "<title>" + e(titel(lage, en)) + "</title>", s, count=1)
    return re.sub(r"<!--ld-start-->.*?<!--ld-end-->", lambda m: "<!--ld-start-->" + strukturierte_daten(lage, en) + "<!--ld-end-->", s, count=1, flags=re.S)


def englisch(s, lage):
    """Aus der fertigen deutschen Startseite die englische unter /en/: eigene Adresse, Sprache, Titel, Beschreibung und Kurztext.
    Die übrigen Texte tauscht i18n.js im Browser, die Daten kommen aus derselben lage.json."""
    e = lambda t: html.escape(str(t))
    k, kurz = lage["kev"], kurzlage_en(lage)
    fest = " Seismograph of the cyber threat level from ten open components, rule-based and verifiable. A tool for everyone who defends systems. A project by Dreier Labs."
    for muster, neu in (
            (r'<html lang="de">', '<html lang="en">'),
            (r'(<meta name="description" content=")[^"]*(">)', lambda m: m.group(1) + e((kurz or "") + fest).strip() + m.group(2)),
            (r'(<meta property="og:description" content=")[^"]*(">)', lambda m: m.group(1) + e(((kurz + " ") if kurz else "") + "Rule-based from open sources.") + m.group(2)),
            (r'(<meta property="og:title" content=")[^"]*(">)', lambda m: m.group(1) + "Seismograph of the cyber threat level. Worldwide, rule-based, openly sourced." + m.group(2)),
            (r'(<meta property="og:url" content=")[^"]*(">)', lambda m: m.group(1) + BASIS + "/en/" + m.group(2)),
            (r'(<link rel="canonical" href=")[^"]*(">)', lambda m: m.group(1) + BASIS + "/en/" + m.group(2))):
        s, n = re.subn(muster, neu, s, count=1)
        if n != 1:
            raise ValueError("englische Seite: Muster fehlt: " + muster[:40])
    s = s.replace('<a href="/audit/"', '<a href="/en/audit/"')  # Menüpunkt Audit zeigt auf die englische Seite
    s = s.replace('<a href="/links/"', '<a href="/en/links/"')  # Menüpunkt Links zeigt auf die englische Seite
    s = re.sub(r"<!--sg-start-->.*?<!--sg-end-->", lambda m: "<!--sg-start-->" + siegel_fuss(True) + "<!--sg-end-->", s, count=1, flags=re.S)
    name = stufe_en(lage)
    if name and isinstance((lage.get("pegel") or {}).get("wert"), int):
        s = re.sub(r'(<a id="hero-pegel"[^>]*>)[^<]*(</a>)', lambda m: m.group(1) + "Dreier Gauge today: %s · %d / 100  · Details" % (e(name.upper()), lage["pegel"]["wert"]) + m.group(2), s, count=1)
        s = re.sub(r'(<div class="stufe mono" id="stufe-wert">)[^<]*(</div>)', lambda m: m.group(1) + e(name) + m.group(2), s, count=1)
    s = re.sub(r"<!--kt-start-->.*?<!--kt-end-->", lambda m: "<!--kt-start-->" + e(kurztext(lage, True)) + "<!--kt-end-->", s, count=1, flags=re.S)
    text = ('<p class="panel pad"><b>The global cyber situation, as of %s. %s</b> Newly added to the CISA catalogue of exploited vulnerabilities: %s in 7 days, %s in 30 days. '
            'Rule-based and openly sourced. A private project by Dreier Labs, not an official body. Data: <a href="/data/lage.json">data/lage.json</a>, rules: <a href="/RULES.md">RULES.md</a>. '
            'German version: <a href="/">cyberlage.org</a>.</p>') % (e(str(lage["stand"])[:10]), e(kurz), e(k["neu_7_tage"]), e(k["neu_30_tage"]))
    s = re.sub(r"<!--ssr-start-->.*?<!--ssr-end-->", lambda m: "<!--ssr-start-->" + text + "<!--ssr-end-->", s, count=1, flags=re.S)
    return kopf(s, lage, en=True)


def sitemap(lage, berichte=()):
    """Nur die Adressen, die im Index stehen sollen; lastmod für die beiden Startseiten ist der Stand der Daten.
    berichte: [(pfad_de, pfad_en, lastmod oder None)] aus berichtseiten.schreibe."""
    tag = str(lage.get("stand"))[:10]
    zeilen = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    alt = "".join('<xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (c, BASIS + u) for c, u in (("de", "/"), ("en", "/en/"), ("x-default", "/")))
    for u in ("/", "/en/"):
        zeilen.append("  <url><loc>%s%s</loc><lastmod>%s</lastmod>%s</url>" % (BASIS, u, tag, alt))
    for u in ("/hinweise", "/impressum"):
        zeilen.append("  <url><loc>%s%s</loc></url>" % (BASIS, u))
    for de, en_, tag_b in berichte:
        alt_b = "".join('<xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (c, BASIS + u) for c, u in (("de", de), ("en", en_), ("x-default", de)))
        for u in (de, en_):
            zeilen.append("  <url><loc>%s%s</loc>%s%s</url>" % (BASIS, u, "<lastmod>%s</lastmod>" % tag_b if tag_b else "", alt_b))
    return "\n".join(zeilen + ["</urlset>"]) + "\n"


def main():
    try:
        lage = json.loads((WURZEL / "site" / "data" / "lage.json").read_text(encoding="utf-8"))
        text = baustein(lage)
        pfad = WURZEL / "site" / "index.html"
        s = pfad.read_text(encoding="utf-8")
        neu, n = re.subn(r"<!--ssr-start-->.*?<!--ssr-end-->", lambda m: "<!--ssr-start-->" + text + "<!--ssr-end-->", s, flags=re.S)
        if n != 1:
            raise ValueError("Marker fehlen")
        neu = kopf(vorbelegen(neu, lage), lage)
        en = englisch(neu, lage)
    except (OSError, ValueError, KeyError) as err:
        print("FEHLER:", err)
        return 1
    pfad.write_text(neu, encoding="utf-8")
    (WURZEL / "site" / "en").mkdir(exist_ok=True)
    (WURZEL / "site" / "en" / "index.html").write_text(en, encoding="utf-8")  # englische Startseite unter /en/
    import berichtseiten
    try:
        bs = berichtseiten.schreibe(WURZEL / "site", json.loads((WURZEL / "site" / "data" / "berichte.json").read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError) as err:  # ohne Berichte bleibt die Startseite trotzdem aktuell
        print("Hinweis: Berichtsseiten nicht geschrieben:", err)
        bs = []
    import auditseiten
    try:
        bs += auditseiten.schreibe(WURZEL)  # Audit-Seite mit Dreier-Siegel aus data/audit/*.json
    except (OSError, ValueError, KeyError) as err:
        print("Hinweis: Audit-Seite nicht geschrieben:", err)
    import linkseiten
    try:
        bs += linkseiten.schreibe(WURZEL)  # Linkseite aus data/links.json
    except (OSError, ValueError, KeyError) as err:
        print("Hinweis: Linkseite nicht geschrieben:", err)
    (WURZEL / "site" / "sitemap.xml").write_text(sitemap(lage, bs), encoding="utf-8")
    (WURZEL / "site" / "RULES.md").write_text((WURZEL / "RULES.md").read_text(encoding="utf-8"), encoding="utf-8")  # Regeln auch unter cyberlage.org/RULES.md
    (WURZEL / "site" / "data" / "sources.csv").write_text((WURZEL / "data" / "sources.csv").read_text(encoding="utf-8"), encoding="utf-8")  # Quellenliste öffentlich
    (WURZEL / "site" / "LICENSE").write_text((WURZEL / "LICENSE").read_text(encoding="utf-8"), encoding="utf-8")
    print("OK: site/index.html (Text für Crawler)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
