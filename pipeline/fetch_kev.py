#!/usr/bin/env python3
"""Holt den KEV-Katalog (Known Exploited Vulnerabilities) der CISA.

Es wird eine kompakte, geprüfte Fassung nach data/kev/kev.json geschrieben:
nur die Felder, die die Auswertung braucht, dazu Quelle, Abrufzeit und Lizenz.
Schlägt die Prüfung fehl, bleibt die bisherige Datei unverändert.

Nur Standardbibliothek. Aufruf: python pipeline/fetch_kev.py
"""
import json
import os
import sys
import tempfile
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

QUELLEN = [
    ("cisa.gov",
     "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"),
    ("github-mirror cisagov/kev-data",
     "https://raw.githubusercontent.com/cisagov/kev-data/main/known_exploited_vulnerabilities.json"),
]
LIZENZ = "CC0 1.0 (laut LICENSE-Datei von cisagov/kev-data)"
ZIEL = Path(__file__).resolve().parent.parent / "data" / "kev" / "kev.json"
PFLICHTFELDER = ("cveID", "vendorProject", "product", "dateAdded",
                 "knownRansomwareCampaignUse")
# Ein Katalog, der plötzlich stark schrumpft, ist verdächtig und wird nicht übernommen.
MIN_ANTEIL_ZUM_VORGAENGER = 0.9


class PruefFehler(Exception):
    """Der abgerufene Katalog besteht die Prüfung nicht."""


def lade(url, timeout=60):
    req = urllib.request.Request(
        url, headers={"User-Agent": "cyberlage-datenabruf (privates Projekt)"})
    with urllib.request.urlopen(req, timeout=timeout) as antwort:  # nosec B310 (Adresse über sicher.nur_https geprüft)
        return json.load(antwort)


def pruefe_und_verdichte(roh):
    """Prüft den Rohkatalog und gibt (meta, eintraege) zurück."""
    if not isinstance(roh, dict) or not isinstance(roh.get("vulnerabilities"), list):
        raise PruefFehler("Feld 'vulnerabilities' fehlt oder ist keine Liste")
    liste = roh["vulnerabilities"]
    if not liste:
        raise PruefFehler("Katalog ist leer")
    if "count" in roh and roh["count"] != len(liste):
        raise PruefFehler(f"count ({roh['count']}) passt nicht zur Zahl der Einträge ({len(liste)})")

    eintraege, gesehen = [], set()
    for v in liste:
        for feld in PFLICHTFELDER:
            if not isinstance(v.get(feld), str) or not v[feld].strip():
                raise PruefFehler(f"Pflichtfeld '{feld}' fehlt in {v.get('cveID', '?')}")
        try:
            date.fromisoformat(v["dateAdded"])
        except ValueError:
            raise PruefFehler(f"Ungültiges Datum in {v['cveID']}: {v['dateAdded']}") from None
        if v["cveID"] in gesehen:
            raise PruefFehler(f"Doppelter Eintrag: {v['cveID']}")
        gesehen.add(v["cveID"])
        eintraege.append({
            "cve": v["cveID"],
            "hersteller": v["vendorProject"].strip(),
            "produkt": v["product"].strip(),
            "hinzugefuegt": v["dateAdded"],
            "frist": v.get("dueDate") or None,
            "ransomware_bekannt": v["knownRansomwareCampaignUse"] == "Known",
        })
    eintraege.sort(key=lambda e: (e["hinzugefuegt"], e["cve"]))
    meta = {
        "katalog_version": roh.get("catalogVersion"),
        "veroeffentlicht_am": roh.get("dateReleased"),
        "anzahl": len(eintraege),
        "lizenz": LIZENZ,
    }
    return meta, eintraege


def pruefe_gegen_vorgaenger(eintraege, ziel=ZIEL):
    if not ziel.exists():
        return
    try:
        alt = json.loads(ziel.read_text(encoding="utf-8"))["eintraege"]
    except (ValueError, KeyError):
        return
    if alt and len(eintraege) < len(alt) * MIN_ANTEIL_ZUM_VORGAENGER:
        raise PruefFehler(
            f"Katalog ist von {len(alt)} auf {len(eintraege)} Einträge geschrumpft, nicht übernommen")


def schreibe(meta, eintraege, ziel=ZIEL):
    """Schreibt atomar, ein Eintrag pro Zeile, damit Änderungen im Verlauf lesbar bleiben."""
    text = ('{\n"meta": ' + json.dumps(meta, ensure_ascii=False)
            + ',\n"eintraege": [\n'
            + ",\n".join(json.dumps(e, ensure_ascii=False) for e in eintraege)
            + "\n]\n}\n")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=ziel.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, ziel)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main():
    fehler = []
    for name, url in QUELLEN:
        try:
            meta, eintraege = pruefe_und_verdichte(lade(url))
            pruefe_gegen_vorgaenger(eintraege)
        except Exception as e:  # jede Quelle einzeln versuchen
            fehler.append(f"{name}: {e}")
            continue
        meta["quelle"] = name
        meta["quelle_url"] = url
        meta["abgerufen_am"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        schreibe(meta, eintraege)
        print(f"OK: {meta['anzahl']} Einträge aus {name} "
              f"(Version {meta['katalog_version']}, veröffentlicht {meta['veroeffentlicht_am']})")
        return 0
    print("FEHLER: keine Quelle brauchbar", file=sys.stderr)
    for f in fehler:
        print(" -", f, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
