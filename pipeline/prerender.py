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


def baustein(lage):
    e = lambda t: html.escape(str(t))
    k = lage["kev"]
    zeilen = [
        f'<p class="panel pad"><b>Die globale Cyberlage, Stand {e(lage["stand"])}, Dreier-Pegel: {e(NAME.get(lage.get("stufe"), "keine Bewertung"))}.</b> '
        f'{e(lage.get("stufe_begruendung") or "")} Neu im CISA-Katalog ausgenutzter Schwachstellen: {e(k["neu_7_tage"])} in 7 Tagen, {e(k["neu_30_tage"])} in 30 Tagen. '
        'Regelbasiert und offen belegt. Ein privates Projekt von Dreier Labs, keine amtliche Stelle.</p>',
        '<p class="panel pad">Die Zahlen stehen als Rohdaten unter <a href="data/lage.json">data/lage.json</a>, die Regeln unter <a href="RULES.md">RULES.md</a>. Für die Ansicht mit Verlauf und Listen wird JavaScript benötigt.</p>',
    ]
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
