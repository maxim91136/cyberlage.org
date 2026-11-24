#!/usr/bin/env python3
"""Schreibt site/feed.xml (RSS 2.0) aus site/data/lage.json. Nur Standardbibliothek.

Einträge: neu aufgenommene KEV-Einträge (Fenster) und kritische CERT-Bund-Warnungen
(nur Titel, Datum und Link mit Quellenangabe). Der Kanalkopf nennt die aktuelle Stufe.
Die Einträge haben feste IDs (CVE bzw. WID), Reader zeigen jeden nur einmal.
"""
import json
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

WURZEL = Path(__file__).resolve().parent.parent
SEITE = "https://cyberlage.org"
NAME = {"niedrig": "niedrig", "erhoeht": "erhöht", "hoch": "hoch", None: "keine Bewertung"}
MAX_EINTRAEGE = 60


def tag(datum):
    return datetime.strptime(datum, "%Y-%m-%d").replace(hour=12, tzinfo=timezone.utc)


def eintraege(lage):
    liste = []
    for n in lage.get("neu") or []:
        zus = " (in Ransomware-Kampagnen genutzt)" if n.get("ransomware_bekannt") else ""
        liste.append({
            "id": "kev-" + n["cve"],
            "titel": f"KEV: {n['cve']} – {n.get('hersteller', '')} {n.get('produkt', '')}{zus}".replace("  ", " "),
            "text": f"Neu im CISA-Katalog ausgenutzter Schwachstellen ({n['hinzugefuegt']}). Frist für Bundesbehörden der USA: {n.get('frist') or 'keine Angabe'}. Quelle: CISA KEV.",
            "link": n.get("link") or SEITE,
            "datum": n["hinzugefuegt"],
        })
    for w in (lage.get("cert_bund") or {}).get("liste") or []:
        if w.get("schwere") != "kritisch":
            continue
        liste.append({
            "id": "wid-" + w["id"],
            "titel": f"CERT-Bund kritisch: {w['titel']}",
            "text": f"Warnung {w['id']} vom {w['datum']}. Quelle: CERT-Bund / BSI Warn- und Informationsdienst.",
            "link": w.get("link") or SEITE,
            "datum": w["datum"],
        })
    for k, m in ((((lage.get("patches") or {}).get("microsoft") or {}).get("monate")) or {}).items():
        b = m.get("bewertung") or {}
        datum = str(m.get("erste_veroeffentlichung") or "")[:10]
        if len(datum) != 10:
            continue
        liste.append({
            "id": "ms-" + k,
            "titel": f"Microsoft Patch Day {k}: {m['cves']} CVEs, {m['ausgenutzt']} ausgenutzt, {m['im_kev']} im KEV",
            "text": f"Dringlichkeit: {b.get('dringlichkeit', '–')}. Umfang: {b.get('groesse', '–')}. {b.get('empfehlung', '')} Ohne Chromium (Edge) und Azure-Linux-Paketlücken. Quelle: Microsoft Security Response Center.",
            "link": SEITE + "/#patches",
            "datum": datum,
        })
    liste.sort(key=lambda x: x["datum"], reverse=True)
    return liste[:MAX_EINTRAEGE]


def baue(lage):
    items = eintraege(lage)
    stand = tag(lage["stand"])
    kopf = f"Dreier-Pegel: {NAME.get(lage.get('stufe'), 'keine Bewertung')}. {lage.get('stufe_begruendung') or ''}".strip()
    teile = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>',
        "<title>Cyberlage</title>",
        f"<link>{SEITE}/</link>",
        f"<description>{escape(kopf)} Regelbasiertes Lagebild aus offenen Quellen. Ein Projekt von Dreier Labs.</description>",
        "<language>de</language>",
        f'<atom:link href="{SEITE}/feed.xml" rel="self" type="application/rss+xml"/>',
        f"<lastBuildDate>{format_datetime(stand)}</lastBuildDate>",
    ]
    for i in items:
        teile.append(
            "<item>"
            f"<title>{escape(i['titel'])}</title><link>{escape(i['link'])}</link>"
            f'<guid isPermaLink="false">{escape(i["id"])}</guid>'
            f"<pubDate>{format_datetime(tag(i['datum']))}</pubDate>"
            f"<description>{escape(i['text'])}</description></item>"
        )
    teile.append("</channel></rss>\n")
    return "\n".join(teile)


def main():
    try:
        lage = json.loads((WURZEL / "site" / "data" / "lage.json").read_text(encoding="utf-8"))
        xml = baue(lage)
    except (OSError, ValueError, KeyError) as err:
        print("FEHLER:", err)
        return 1
    (WURZEL / "site" / "feed.xml").write_text(xml, encoding="utf-8")
    print("OK: site/feed.xml,", xml.count("<item>"), "Einträge")
    return 0


if __name__ == "__main__":
    sys.exit(main())
