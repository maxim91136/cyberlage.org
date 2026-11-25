#!/usr/bin/env python3
"""Schreibt die wichtigsten Werte als echten Text in site/index.html (Bereich <noscript>),
damit auch Crawler und Filter ohne JavaScript Inhalt sehen. Nur Standardbibliothek."""
import html
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
                      + '. Stufen: unter 30 ruhig, 30 bis 49 unauffällig, 50 bis 63 angespannt, 64 bis 79 hoch, ab 80 außergewöhnlich.</p>')
    zeilen.append('<p class="panel pad">Die Zahlen stehen als Rohdaten unter <a href="data/lage.json">data/lage.json</a>, die Regeln unter <a href="RULES.md">RULES.md</a>. Für die Ansicht mit Verlauf und Listen wird JavaScript benötigt.</p>')
    return "".join(zeilen)


def vorbelegen(s, lage):
    """Startwerte direkt ins HTML, damit vor dem Laden der Daten kein Platzhalter steht. JavaScript überschreibt sie danach."""
    e = lambda t: html.escape(str(t))
    k = lage["kev"]
    if lage.get("stufe"):
        s = re.sub(r'(<div class="stufe mono" id="stufe-wert">)[^<]*(</div>)', lambda m: m.group(1) + e(NAME[lage["stufe"]]) + m.group(2), s, count=1)
        s = re.sub(r'<div class="stufe-text" id="stufe-text"[^>]*>[^<]*</div>', '<div class="stufe-text" id="stufe-text" hidden></div>', s, count=1)
    for kennung, wert in (("k7", k.get("neu_7_tage")), ("k30", k.get("neu_30_tage")), ("kall", k.get("gesamt")), ("kr", k.get("ransomware_bekannt_30_tage"))):
        if isinstance(wert, int):
            s = re.sub(r'(<b id="%s">)[^<]*(</b>)' % kennung, lambda m: m.group(1) + f"{wert:,}".replace(",", ".") + m.group(2), s, count=1)
    kurz = kurzlage(lage)
    if kurz:
        fest = " Seismograph der Cyber-Bedrohungslage aus acht offenen Bausteinen, regelbasiert und nachprüfbar. Ein Werkzeug für alle, die Systeme verteidigen. Ein Projekt von Dreier Labs."
        s = re.sub(r'(<meta name="description" content=")[^"]*(">)', lambda m: m.group(1) + e(kurz + fest) + m.group(2), s, count=1)
        s = re.sub(r'(<meta property="og:description" content=")[^"]*(">)', lambda m: m.group(1) + e(kurz + " Regelbasiert aus offenen Quellen.") + m.group(2), s, count=1)
        pg = lage["pegel"]
        s = re.sub(r'<a id="hero-pegel"[^>]*>[^<]*</a>', lambda m: '<a id="hero-pegel" class="hero-pegel mono st-%s" href="#lage">Dreier-Pegel heute: %s · %d / 100  · Details</a>' % (e(lage["stufe"]), e(NAME[lage["stufe"]].upper()), pg["wert"]), s, count=1)
    li = "".join(f"<li>{e(t)}</li>" for t in lage.get("hinweise") or [])
    if li:
        s = re.sub(r'(<ul id="hinweise" class="hinw">).*?(</ul>)', lambda m: m.group(1) + li + m.group(2), s, count=1, flags=re.S)
    return s


def main():
    try:
        lage = json.loads((WURZEL / "site" / "data" / "lage.json").read_text(encoding="utf-8"))
        text = baustein(lage)
        pfad = WURZEL / "site" / "index.html"
        s = pfad.read_text(encoding="utf-8")
        neu, n = re.subn(r"<!--ssr-start-->.*?<!--ssr-end-->", lambda m: "<!--ssr-start-->" + text + "<!--ssr-end-->", s, flags=re.S)
        if n != 1:
            raise ValueError("Marker fehlen")
        neu = vorbelegen(neu, lage)
    except (OSError, ValueError, KeyError) as err:
        print("FEHLER:", err)
        return 1
    pfad.write_text(neu, encoding="utf-8")
    (WURZEL / "site" / "RULES.md").write_text((WURZEL / "RULES.md").read_text(encoding="utf-8"), encoding="utf-8")  # Regeln auch unter cyberlage.org/RULES.md
    (WURZEL / "site" / "data" / "sources.csv").write_text((WURZEL / "data" / "sources.csv").read_text(encoding="utf-8"), encoding="utf-8")  # Quellenliste öffentlich
    (WURZEL / "site" / "LICENSE").write_text((WURZEL / "LICENSE").read_text(encoding="utf-8"), encoding="utf-8")
    print("OK: site/index.html (Text für Crawler)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
