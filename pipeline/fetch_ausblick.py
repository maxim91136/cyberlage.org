#!/usr/bin/env python3
"""Ausblick: neue CVEs (NVD) mit ihrer EPSS-Wahrscheinlichkeit (FIRST), ohne die schon im KEV stehenden.

Nur Standardbibliothek. Übernommen werden Kennung, Veröffentlichungsdatum, CVSS-Wert und EPSS-Werte,
keine Beschreibungstexte. Schlägt der Abruf fehl, bleibt die alte Datei bestehen.

Quellen und Bedingungen:
- NVD API 2.0 (gemeinfrei, erbetener Hinweis: "This product uses data from the NVD API but is not endorsed or
  certified by the NVD."). Ohne Schlüssel gelten 5 Anfragen je 30 Sekunden.
- EPSS von FIRST (kostenlos, mit Quellenangabe: "See EPSS at https://www.first.org/epss").
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
UA = "cyberlage.org (privates Projekt von Dreier Labs, https://cyberlage.org)"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
EPSS_URL = "https://api.first.org/data/v1/epss"
DATEI = WURZEL / "data" / "ausblick" / "ausblick.json"
FENSTER_TAGE = 14
HOCH_AB = 0.10          # EPSS-Wahrscheinlichkeit, ab der wir "hoch wahrscheinlich" zählen
LISTE_MAX = 10
SEITE = 2000            # Höchstwert pro NVD-Seite
EPSS_BLOCK = 100


class QuellFehler(Exception):
    pass


def lade_json(url, versuche=4):
    letzter = None
    for i in range(versuche):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as ex:
            letzter = ex
            if ex.code not in (403, 429, 500, 502, 503, 504):
                break
        except (urllib.error.URLError, TimeoutError, ValueError) as ex:
            letzter = ex
        time.sleep(8 * (i + 1))
    raise QuellFehler(f"{url.split('?')[0]}: {letzter}")


def cvss_wert(metriken):
    """Höchster vorhandener Basiswert aus v4.0, v3.1, v3.0, sonst None."""
    for schluessel in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30"):
        werte = []
        for m in (metriken or {}).get(schluessel, []) or []:
            w = (m.get("cvssData") or {}).get("baseScore")
            if isinstance(w, (int, float)):
                werte.append(float(w))
        if werte:
            return max(werte)
    return None


def parse_nvd(daten):
    """Liste von {cve, veroeffentlicht (YYYY-MM-DD), cvss}. Abgelehnte CVEs fallen weg."""
    ergebnis = []
    for v in (daten or {}).get("vulnerabilities", []) or []:
        c = v.get("cve") or {}
        kennung = c.get("id")
        if not kennung or str(c.get("vulnStatus", "")).lower() == "rejected":
            continue
        ergebnis.append({
            "cve": kennung,
            "veroeffentlicht": str(c.get("published", ""))[:10],
            "cvss": cvss_wert(c.get("metrics")),
            "beschreibung": kurzbeschreibung(c.get("descriptions")),
            "produkt": produkt_aus_cpe(c.get("configurations")),
        })
    return ergebnis


def kurzbeschreibung(beschreibungen, max_zeichen=170):
    """Erster Satz der englischen Beschreibung aus der NVD, gekürzt. Leer, wenn keine vorhanden ist."""
    for b in beschreibungen or []:
        if b.get("lang") == "en" and b.get("value"):
            text = " ".join(str(b["value"]).split())
            satz = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
            return (satz if len(satz) <= max_zeichen else satz[:max_zeichen - 1].rstrip() + "…")
    return ""


def produkt_aus_cpe(konfigurationen):
    """Hersteller und Produkt aus dem ersten CPE-Eintrag ("cpe:2.3:a:hersteller:produkt:..."), sonst leer."""
    for k in konfigurationen or []:
        for n in k.get("nodes", []) or []:
            for m in n.get("cpeMatch", []) or []:
                teile = str(m.get("criteria", "")).split(":")
                if len(teile) > 5 and teile[3] and teile[4] and teile[3] != "*" and teile[4] != "*":
                    return (teile[3] + " " + teile[4]).replace("_", " ")
    return ""


def parse_epss(daten):
    """{cve: (epss, perzentil, datum)}; Zahlen kommen als Text zurück."""
    ergebnis = {}
    for z in (daten or {}).get("data", []) or []:
        try:
            ergebnis[z["cve"]] = (float(z["epss"]), float(z["percentile"]), str(z.get("date", "")))
        except (KeyError, TypeError, ValueError):
            continue
    return ergebnis


def baue(cves, epss, kev_ids, jetzt, fenster_tage=FENSTER_TAGE, n=LISTE_MAX):
    """Ohne KEV-Einträge und ohne CVEs ohne EPSS-Wert. Sortiert nach Wahrscheinlichkeit, absteigend."""
    zeilen = []
    for c in cves:
        werte = epss.get(c["cve"])
        if werte is None or c["cve"] in kev_ids:
            continue
        zeilen.append({
            "cve": c["cve"],
            "epss": round(werte[0], 5),
            "perzentil": round(werte[1], 5),
            "veroeffentlicht": c["veroeffentlicht"],
            "cvss": c["cvss"],
            "beschreibung": c.get("beschreibung", ""),
            "produkt": c.get("produkt", ""),
            "link": f"https://nvd.nist.gov/vuln/detail/{c['cve']}",
        })
    zeilen.sort(key=lambda z: (-z["epss"], z["cve"]))
    daten = sorted({w[2] for w in epss.values() if w[2]})
    return {
        "abgerufen_am": jetzt.isoformat(timespec="seconds"),
        "fenster_tage": fenster_tage,
        "geprueft": len(zeilen),
        "schwelle_hoch": HOCH_AB,
        "hoch_wahrscheinlich": sum(1 for z in zeilen if z["epss"] >= HOCH_AB),
        "epss_datum": daten[-1] if daten else None,
        "liste": zeilen[:n],
        "kandidaten": [{"cve": z["cve"], "epss": z["epss"], "veroeffentlicht": z["veroeffentlicht"]}
                       for z in zeilen if z["epss"] >= HOCH_AB],
    }


def hole_nvd(jetzt):
    start = (jetzt - timedelta(days=FENSTER_TAGE)).strftime("%Y-%m-%dT%H:%M:%S.000")
    ende = jetzt.strftime("%Y-%m-%dT%H:%M:%S.000")
    alle, index, gesamt = [], 0, None
    while gesamt is None or index < gesamt:
        q = urllib.parse.urlencode({"pubStartDate": start, "pubEndDate": ende,
                                    "resultsPerPage": SEITE, "startIndex": index})
        d = lade_json(f"{NVD_URL}?{q}")
        gesamt = int(d.get("totalResults", 0))
        alle += parse_nvd(d)
        index += int(d.get("resultsPerPage") or SEITE)
        if index < gesamt:
            time.sleep(7)
    return alle


def hole_epss(kennungen):
    ergebnis = {}
    kennungen = list(kennungen)
    for i in range(0, len(kennungen), EPSS_BLOCK):
        block = kennungen[i:i + EPSS_BLOCK]
        q = urllib.parse.urlencode({"cve": ",".join(block), "limit": EPSS_BLOCK}, safe=",")
        ergebnis.update(parse_epss(lade_json(f"{EPSS_URL}?{q}")))
        time.sleep(1)
    return ergebnis


def main():
    jetzt = datetime.now(timezone.utc)
    kev = json.loads((WURZEL / "data" / "kev" / "kev.json").read_text(encoding="utf-8"))
    kev_ids = {e["cve"] for e in kev["eintraege"]}
    try:
        cves = hole_nvd(jetzt)
        if not cves:
            raise QuellFehler("NVD lieferte keine neuen CVEs")
        epss = hole_epss([c["cve"] for c in cves if c["cve"] not in kev_ids])
        if not epss:
            raise QuellFehler("EPSS lieferte keine Werte")
    except QuellFehler as ex:
        print(f"FEHLER: {ex}", file=sys.stderr)
        return 1
    ergebnis = baue(cves, epss, kev_ids, jetzt)
    DATEI.parent.mkdir(parents=True, exist_ok=True)
    DATEI.write_text(json.dumps(ergebnis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {DATEI.relative_to(WURZEL)} ({len(cves)} neue CVEs, {ergebnis['geprueft']} mit EPSS, "
          f"{ergebnis['hoch_wahrscheinlich']} ab {int(HOCH_AB * 100)} %)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
