#!/usr/bin/env python3
"""Holt zwei weitere öffentliche Quellen und verdichtet sie (nur Standardbibliothek).

1. CERT-Bund/BSI Warnungen (WID-Feed, RSS): nur Kennung, Schweregrad, Titel, Datum, Link. Keine Beschreibungstexte.
2. EU-KEV über die EUVD von ENISA (JSON): Kennung, CVE, Hersteller, Werte, Datum, Link.

Aufruf: python pipeline/fetch_extra.py [bsi|eu]   (ohne Argument beides)
Schlägt eine Quelle fehl, bleibt die alte Datei bestehen und der Lauf meldet den Fehler.
"""
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import sicher

WURZEL = Path(__file__).resolve().parent.parent
UA = "cyberlage.org (privates Projekt von Dreier Labs, https://cyberlage.org)"
BSI_URL = "https://wid.cert-bund.de/content/public/securityAdvisory/rss"
EU_URLS = [
    "https://euvdservices.enisa.europa.eu/api/search?exploited=true&size=100&page=0",
    "https://euvdservices.enisa.europa.eu/api/exploitedvulnerabilities",
]
BSI_DATEI = WURZEL / "data" / "bsi" / "warnungen.json"
EU_DATEI = WURZEL / "data" / "eu" / "kev.json"
BEHALTEN_TAGE = 120
SCHWEREN = ("kritisch", "hoch", "mittel", "niedrig")


class QuellFehler(Exception):
    pass


def lade(url):
    req = urllib.request.Request(sicher.nur_https(url), headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:  # nosec B310 (Adresse über sicher.nur_https geprüft)
        return r.read()


# ---------- CERT-Bund / BSI ----------
def parse_bsi(xml_bytes):
    try:
        wurzel = sicher.xml_lesen(xml_bytes)
    except ET.ParseError as e:
        raise QuellFehler(f"BSI-Feed kein gültiges XML: {e}") from None
    items = wurzel.findall("./channel/item")
    if not items:
        raise QuellFehler("BSI-Feed ohne Einträge")
    ergebnis = {}
    for it in items:
        titel = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        m = re.search(r"name=(WID-SEC-\d{4}-\d+)", link)
        schwere = (it.findtext("category") or "").strip().lower()
        if not m or schwere not in SCHWEREN:
            continue  # unvollständig, wird übersprungen statt geraten
        try:
            datum = parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc)
        except (TypeError, ValueError):
            continue
        status = "update" if titel.upper().startswith("[UPDATE]") else "neu"
        kurz = re.sub(r"^(\[[^\]]*\]\s*)+", "", titel).strip()
        ergebnis[m.group(1)] = {"id": m.group(1), "schwere": schwere, "status": status,
                                "titel": kurz, "datum": datum.date().isoformat(), "link": link}
    if not ergebnis:
        raise QuellFehler("BSI-Feed: kein Eintrag war auswertbar")
    return ergebnis


# ---------- EU-KEV (EUVD) ----------
def _zeit(text):
    if not text:
        return None
    t = str(text).replace(" ", " ").replace(" ", " ").strip()
    for fmt in ("%b %d, %Y, %I:%M:%S %p", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_eu(roh):
    daten = json.loads(roh)
    items = daten.get("items") if isinstance(daten, dict) else daten
    if not isinstance(items, list) or not items:
        raise QuellFehler("EUVD: keine Liste oder leer")
    ergebnis = {}
    for e in items:
        eid = e.get("id")
        seit = _zeit(e.get("exploitedSince"))
        if not eid or not seit:
            continue
        cves = [a for a in re.split(r"\s+", e.get("aliases") or "") if a.startswith("CVE-")]
        hersteller = sorted({v.get("vendor", {}).get("name") for v in (e.get("enisaIdVendor") or [])
                             if isinstance(v, dict) and v.get("vendor", {}).get("name")})
        ergebnis[eid] = {"id": eid, "cve": cves, "hersteller": hersteller,
                         "ausgenutzt_seit": seit, "veroeffentlicht": _zeit(e.get("datePublished")),
                         "cvss": e.get("baseScore"), "epss": e.get("epss"),
                         "link": f"https://euvd.enisa.europa.eu/vulnerability/{eid}"}
    if not ergebnis:
        raise QuellFehler("EUVD: kein Eintrag war auswertbar")
    return ergebnis


# ---------- gemeinsam ----------
def zusammenfuehren(datei, neu, datumsfeld, jetzt):
    alt = {}
    if datei.exists():
        alt = {e["id"]: e for e in json.loads(datei.read_text(encoding="utf-8")).get("eintraege", [])}
    alt.update(neu)
    grenze = (jetzt - timedelta(days=BEHALTEN_TAGE)).date().isoformat()
    behalten = [e for e in alt.values() if (e.get(datumsfeld) or "9999") >= grenze]
    return sorted(behalten, key=lambda e: (e.get(datumsfeld) or "", e["id"]), reverse=True)


def schreibe(datei, meta, eintraege):
    datei.parent.mkdir(parents=True, exist_ok=True)
    tmp = datei.with_suffix(".tmp")
    tmp.write_text(json.dumps({"meta": meta, "eintraege": eintraege}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(datei)


def lauf_bsi(jetzt):
    neu = parse_bsi(lade(BSI_URL))
    eintraege = zusammenfuehren(BSI_DATEI, neu, "datum", jetzt)
    meta = {"quelle": "CERT-Bund / BSI Warn- und Informationsdienst", "quelle_url": "https://wid.cert-bund.de/",
            "hinweis": "Nur Kennung, Schweregrad, Titel, Datum und Link. Beschreibungstexte werden nicht übernommen.",
            "abgerufen_am": jetzt.isoformat(timespec="seconds"), "anzahl": len(eintraege)}
    schreibe(BSI_DATEI, meta, eintraege)
    print(f"OK: {BSI_DATEI.relative_to(WURZEL)} ({len(eintraege)} Einträge)")


def lauf_eu(jetzt):
    fehler = []
    for url in EU_URLS:
        try:
            neu = parse_eu(lade(url))
            break
        except Exception as e:  # nächste Adresse versuchen
            fehler.append(f"{url}: {e}")
    else:
        raise QuellFehler("EUVD nicht abrufbar: " + " | ".join(fehler))
    eintraege = zusammenfuehren(EU_DATEI, neu, "ausgenutzt_seit", jetzt)
    meta = {"quelle": "EU-KEV über die EU-Schwachstellendatenbank (EUVD) von ENISA", "quelle_url": "https://euvd.enisa.europa.eu/",
            "hinweis": "Lizenz nicht ausdrücklich geklärt. Nur Kennung, CVE, Hersteller, Werte, Datum und Link.",
            "abgerufen_am": jetzt.isoformat(timespec="seconds"), "anzahl": len(eintraege)}
    schreibe(EU_DATEI, meta, eintraege)
    print(f"OK: {EU_DATEI.relative_to(WURZEL)} ({len(eintraege)} Einträge)")


def main(argv):
    jetzt = datetime.now(timezone.utc)
    ziele = argv or ["bsi", "eu"]
    rc = 0
    for z in ziele:
        try:
            {"bsi": lauf_bsi, "eu": lauf_eu}[z](jetzt)
        except Exception as e:
            print(f"FEHLER ({z}): {e}", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
