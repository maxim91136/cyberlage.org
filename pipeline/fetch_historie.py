#!/usr/bin/env python3
"""Holt die Verlaufsdaten der Bausteine, die nicht aus dem CISA-KEV stammen (nur Standardbibliothek).

Es wird nichts geschätzt oder simuliert: gespeichert werden nur Kennung und Datum (und Schweregrad) echter Meldungen.
Aus diesen Rohdaten rechnet modell.py die Tageswerte für jeden Stichtag der Vergangenheit.

1. CERT-Bund (WID, öffentliche JSON-Schnittstelle): Kennung, letztes Veröffentlichungsdatum, Schweregrad.
2. NCSC-NL (CSAF-Verzeichnis, changes.csv): Kennung und letztes Änderungsdatum.
3. EU-KEV (EUVD von ENISA): Kennung und Datum "ausgenutzt seit".
4. Microsoft (MSRC CVRF): je Patch Day die Zahl der als ausgenutzt gekennzeichneten Lücken.

Jede Quelle ist für sich fehlertolerant: schlägt sie fehl, bleibt der alte Stand erhalten.
"""
import csv
import io
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sicher

WURZEL = Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "data" / "radar" / "historie"
UA = "cyberlage.org (privates Projekt von Dreier Labs, https://cyberlage.org)"
TAGE = 1100 + 40   # 36 Monate plus das längste Fenster
CERT_URL = "https://wid.cert-bund.de/content/public/securityAdvisory?size=%d&sort=published,desc&page=%d"
NCSC_URL = "https://advisories.ncsc.nl/csaf/v2/changes.csv"
EU_URL = "https://euvdservices.enisa.europa.eu/api/search?exploited=true&size=100&page=%d"
KLASSE = {"kritisch": "k", "hoch": "h", "mittel": "m", "niedrig": "n"}


def lade(url, timeout=60):
    req = urllib.request.Request(sicher.nur_https(url), headers={"User-Agent": UA, "Accept": "application/json, text/csv, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def lese(name):
    try:
        return json.loads((ZIEL / name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def schreibe(name, daten):
    ZIEL.mkdir(parents=True, exist_ok=True)
    tmp = ZIEL / (name + ".tmp")
    tmp.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(ZIEL / name)


def parse_cert(seite):
    """Eine Seite der WID-Schnittstelle -> {Kennung: [Datum, Klasse]}."""
    out = {}
    for e in (seite or {}).get("content", []):
        name, pub, kl = e.get("name"), str(e.get("published") or "")[:10], KLASSE.get(str(e.get("classification") or "").lower())
        if name and re.match(r"WID-SEC-\d{4}-\d+$", name) and re.match(r"\d{4}-\d\d-\d\d$", pub) and kl:
            out[name] = [pub, kl]
    return out


def hole_cert(jetzt, lade=lade, pause=0.4, max_seiten=120, groesse=500):
    alt = lese("cert_bund.json")
    eintraege = dict(alt.get("eintraege", {}))
    grenze = (jetzt - timedelta(days=TAGE)).date().isoformat()
    # Aktualisierte Meldungen rücken nach oben. Es genügt deshalb, bis kurz vor den letzten Abruf zurückzublättern.
    stopp = grenze
    if alt.get("vollstaendig_bis") and alt.get("abgerufen_am"):
        stopp = max(grenze, (datetime.fromisoformat(alt["abgerufen_am"]) - timedelta(days=3)).date().isoformat())
    seiten = 0
    fertig = False
    for p in range(max_seiten):
        neu = parse_cert(json.loads(lade(CERT_URL % (groesse, p))))
        seiten += 1
        if not neu:
            fertig = True
            break
        eintraege.update(neu)
        if min(v[0] for v in neu.values()) < stopp:
            fertig = True
            break
        time.sleep(pause)
    daten = {"quelle": "CERT-Bund / BSI Warn- und Informationsdienst", "quelle_url": "https://wid.cert-bund.de/",
             "hinweis": "Je Kennung das letzte Veröffentlichungsdatum (bei Aktualisierungen das der Aktualisierung) und der Schweregrad: k kritisch, h hoch, m mittel, n niedrig.",
             "abgerufen_am": jetzt.isoformat(timespec="seconds"),
             "vollstaendig_bis": grenze if (fertig and (alt.get("vollstaendig_bis") or stopp == grenze)) else alt.get("vollstaendig_bis"),
             "eintraege": eintraege}
    schreibe("cert_bund.json", daten)
    return "CERT-Bund: %d Meldungen, %d Seiten, vollständig bis %s" % (len(eintraege), seiten, daten["vollstaendig_bis"])


def parse_ncsc(text):
    out = {}
    for zeile in csv.reader(io.StringIO(text)):
        if len(zeile) < 2:
            continue
        m = re.search(r"(ncsc-\d{4}-\d+)\.json", zeile[0], re.I)
        if m and re.match(r"\d{4}-\d\d-\d\d", zeile[1]):
            out[m.group(1).upper()] = zeile[1][:10]
    return out


def hole_ncsc(jetzt, lade=lade):
    alt = lese("ncsc_nl.json")
    eintraege = dict(alt.get("eintraege", {}))
    neu = parse_ncsc(lade(NCSC_URL).decode("utf-8", "replace"))
    if not neu:
        raise ValueError("changes.csv ohne lesbare Zeilen")
    eintraege.update(neu)
    schreibe("ncsc_nl.json", {"quelle": "NCSC-NL Beveiligingsadviezen (CSAF)", "quelle_url": "https://advisories.ncsc.nl/",
                              "hinweis": "Je Kennung das Datum der letzten Änderung.", "abgerufen_am": jetzt.isoformat(timespec="seconds"),
                              "eintraege": eintraege})
    return "NCSC-NL: %d Advisories, ältestes Änderungsdatum %s" % (len(eintraege), min(eintraege.values()))


def hole_eu(jetzt, lade=lade, max_seiten=40, pause=0.5):
    import fetch_extra
    alt = lese("eu_kev.json")
    eintraege = dict(alt.get("eintraege", {}))
    seiten = 0
    for p in range(max_seiten):
        try:
            neu = fetch_extra.parse_eu(lade(EU_URL % p))
        except fetch_extra.QuellFehler:
            break
        seiten += 1
        frisch = {k: v["ausgenutzt_seit"] for k, v in neu.items()}
        eintraege.update(frisch)
        if len(neu) < 100:
            break
        time.sleep(pause)
    schreibe("eu_kev.json", {"quelle": "EU-KEV über die EUVD von ENISA", "quelle_url": "https://euvd.enisa.europa.eu/",
                             "hinweis": "Je Kennung das Datum 'ausgenutzt seit'.", "abgerufen_am": jetzt.isoformat(timespec="seconds"),
                             "eintraege": eintraege})
    return "EU-KEV: %d Einträge, %d Seiten, ältestes Datum %s" % (len(eintraege), seiten, min(eintraege.values()))


def hole_ms(jetzt, lade=lade, monate=37, je_lauf=24):
    import fetch_patches
    alt = lese("microsoft.json")
    mon = dict(alt.get("monate", {}))
    # Was der Patch-Lauf schon hat, wird übernommen (gleiche Zählweise).
    ms = fetch_patches.lese_datei(fetch_patches.MS_DATEI) or {}
    for mid, m in (ms.get("monate") or {}).items():
        if m.get("erste_veroeffentlichung") and isinstance(m.get("ausgenutzt"), int):
            mon[mid] = {"tag": m["erste_veroeffentlichung"][:10], "ausgenutzt": m["ausgenutzt"], "cves": m.get("cves")}
    liste = fetch_patches.lade_json(fetch_patches.MS_LISTE)
    fehlend = [e for e in fetch_patches.monatsliste(liste, monate) if e["ID"] not in mon]
    fehler = []
    for e in fehlend[-je_lauf:]:
        try:
            doc = fetch_patches.lade_json(e.get("CvrfUrl") or fetch_patches.MS_DOK % e["ID"])
            v = fetch_patches.verdichte_dokument(doc, ())
            tag = (v.get("erste_veroeffentlichung") or e.get("InitialReleaseDate") or "")[:10]
            if tag:
                mon[e["ID"]] = {"tag": tag, "ausgenutzt": v["ausgenutzt"], "cves": v.get("cves")}
        except Exception as ex:  # fail-soft je Monat
            fehler.append("%s: %s" % (e["ID"], ex))
    schreibe("microsoft.json", {"quelle": "Microsoft Security Response Center (CVRF 3.0)", "quelle_url": fetch_patches.MS_QUELLE,
                                "hinweis": "Je Patch Day die Zahl der von Microsoft als ausgenutzt gekennzeichneten Lücken, Stand des Dokuments beim Abruf.",
                                "abgerufen_am": jetzt.isoformat(timespec="seconds"), "monate": mon})
    return "Microsoft: %d Monate, %d fehlten, Fehler: %s" % (len(mon), len(fehlend), "; ".join(fehler) or "keine")


DSHIELD_URL = "https://isc.sans.edu/api/dailysummary/%s/%s?json"


def parse_dshield(daten):
    """Antwort der DShield-Tagesübersicht -> {Datum: [Meldungen, Ziele, Quellen]}. Verträgt Liste oder Objekt mit Liste."""
    if isinstance(daten, dict):
        daten = next((v for v in daten.values() if isinstance(v, list)), [])
    out = {}
    for e in daten or []:
        if not isinstance(e, dict):
            continue
        d = str(e.get("date") or "")[:10]
        try:
            werte = [int(e.get(k)) for k in ("records", "targets", "sources")]
        except (TypeError, ValueError):
            continue
        if re.match(r"\d{4}-\d\d-\d\d$", d):
            out[d] = werte
    return out


def hole_dshield(jetzt, lade=lade, pause=1.0):
    alt = lese("dshield.json")
    tage = dict(alt.get("tage", {}))
    ende = jetzt.date()
    start = (jetzt - timedelta(days=TAGE)).date()
    if tage:
        start = max(start, datetime.fromisoformat(max(tage)).date() - timedelta(days=7))
    roh = None
    t = start
    while t <= ende:
        bis = min(t + timedelta(days=180), ende)
        antwort = lade(DSHIELD_URL % (t.isoformat(), bis.isoformat()))
        if roh is None:
            roh = antwort[:300].decode("utf-8", "replace")
        tage.update(parse_dshield(json.loads(antwort)))
        t = bis + timedelta(days=1)
        time.sleep(pause)
    if not tage:
        raise ValueError("keine Tageswerte, Antwort begann mit: %s" % roh)
    schreibe("dshield.json", {"quelle": "SANS Internet Storm Center / DShield, Tagesübersicht", "quelle_url": "https://isc.sans.edu/",
                              "hinweis": "Je Tag: Meldungen (records), meldende Ziele (targets), angreifende Quellen (sources) aus den Firewall- und Honeypot-Protokollen der DShield-Teilnehmer. Nutzung mit Quellenangabe: SANS Technology Institute, Internet Storm Center.",
                              "abgerufen_am": jetzt.isoformat(timespec="seconds"), "tage": tage})
    return "DShield: %d Tage, %s bis %s, Antwortbeginn: %s" % (len(tage), min(tage), max(tage), (roh or "")[:160].replace("\n", " "))


RANSOM_URL = "https://www.ransomlook.io/api/posts?days=%d"


def parse_ransom(daten):
    """Antwort von RansomLook -> {Datum: Zahl der Einträge}. Gespeichert wird nur die Zahl je Tag, keine Namen.
    Die Struktur wird nicht vorausgesetzt: gezählt wird jedes Objekt mit einem Feld 'discovered'."""
    tage = {}

    def lauf(x):
        if isinstance(x, dict):
            d = str(x.get("discovered") or "")[:10]
            if re.match(r"\d{4}-\d\d-\d\d$", d):
                tage[d] = tage.get(d, 0) + 1
            for v in x.values():
                if isinstance(v, (dict, list)):
                    lauf(v)
        elif isinstance(x, list):
            for v in x:
                lauf(v)
    lauf(daten)
    return tage


def hole_ransom(jetzt, lade=lade):
    alt = lese("ransomware.json")
    tage = dict(alt.get("tage", {}))
    n = 14 if len(tage) > 400 else TAGE
    antwort = lade(RANSOM_URL % n, timeout=180)
    neu = parse_ransom(json.loads(antwort))
    if not neu:
        raise ValueError("keine Einträge, Antwort begann mit: %s" % antwort[:200].decode("utf-8", "replace"))
    aeltester = min(neu)
    for d, z in neu.items():
        if d != aeltester or d not in tage:   # der älteste Tag der Antwort ist meist angeschnitten
            tage[d] = z
    schreibe("ransomware.json", {"quelle": "RansomLook (offenes Projekt, beobachtet Leak-Seiten von Ransomware-Gruppen)", "quelle_url": "https://www.ransomlook.io/",
                                 "hinweis": "Je Tag die Zahl neu entdeckter Einträge auf Leak-Seiten. Das sind Behauptungen der Täter, keine bestätigten Vorfälle. Gespeichert wird nur die Zahl, keine Namen.",
                                 "abgerufen_am": jetzt.isoformat(timespec="seconds"), "tage": tage})
    return "RansomLook: %d Tage, %s bis %s, Summe %d, Antwort %d Bytes, Beginn: %s" % (len(tage), min(tage), max(tage), sum(tage.values()), len(antwort), antwort[:120].decode("utf-8", "replace").replace("\n", " "))


def main(argv):
    jetzt = datetime.now(timezone.utc)
    rc = 0
    for name, fn in (("cert", hole_cert), ("ncsc", hole_ncsc), ("eu", hole_eu), ("ms", hole_ms), ("dshield", hole_dshield), ("ransom", hole_ransom)):
        if argv and name not in argv:
            continue
        try:
            print("OK:", fn(jetzt))
        except Exception as e:
            print("FEHLER %s: %s" % (name, e))
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
