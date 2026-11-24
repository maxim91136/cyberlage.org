#!/usr/bin/env python3
"""Schreibt die wichtigsten Werte als echten Text in site/index.html (Bereich <noscript>),
damit auch Crawler und Filter ohne JavaScript Inhalt sehen. Nur Standardbibliothek."""
import html
import json
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
NAME = {"niedrig": "niedrig", "erhoeht": "erhöht", "hoch": "hoch", None: "keine Bewertung"}


def baustein(lage):
    e = lambda t: html.escape(str(t))
    k = lage["kev"]
    zeilen = [
        f'<p class="panel pad"><b>Die globale Cyberlage, Stand {e(lage["stand"])}, Dreier-Pegel: {e(NAME.get(lage.get("stufe"), "keine Bewertung"))}.</b> '
        f'{e(lage.get("stufe_begruendung") or "")} Neu im CISA-Katalog ausgenutzter Schwachstellen: {e(k["neu_7_tage"])} in 7 Tagen, {e(k["neu_30_tage"])} in 30 Tagen. '
        'Regelbasiert und offen belegt. Ein privates Projekt von Dreier Labs, keine amtliche Stelle.</p>',
        '<p class="panel pad">Die Zahlen stehen als Rohdaten unter <a href="data/lage.json">data/lage.json</a>, die Regeln auf <a href="https://github.com/maxim91136/cyberlage.org/blob/main/RULES.md">GitHub</a>. Für die Ansicht mit Verlauf und Listen wird JavaScript benötigt.</p>',
    ]
    return "".join(zeilen)


def main():
    try:
        lage = json.loads((WURZEL / "site" / "data" / "lage.json").read_text(encoding="utf-8"))
        text = baustein(lage)
        pfad = WURZEL / "site" / "index.html"
        s = pfad.read_text(encoding="utf-8")
        neu, n = re.subn(r"<!--ssr-start-->.*?<!--ssr-end-->", lambda m: "<!--ssr-start-->" + text + "<!--ssr-end-->", s, flags=re.S)
        if n != 1:
            raise ValueError("Marker fehlen")
    except (OSError, ValueError, KeyError) as err:
        print("FEHLER:", err)
        return 1
    pfad.write_text(neu, encoding="utf-8")
    print("OK: site/index.html (Text für Crawler)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
