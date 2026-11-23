#!/usr/bin/env python3
"""Wertet die Daten nach den offenen Regeln aus (siehe RULES.md).

Liest:   data/kev/kev.json, data/enisa.csv, config/regeln.json, optional data/bsi/warnungen.json und data/eu/kev.json
Schreibt: site/data/lage.json

Grundsätze: Es gehen nur geprüfte ENISA-Werte und der KEV-Katalog ein. Die Stufe misst die
Aktivität im Katalog (neu aufgenommene, ausgenutzte Schwachstellen), nicht die Zahl der Angriffe.
Ohne freigegebene Schwellen steht null in der Ausgabe und es wird nichts geschätzt.

Nur Standardbibliothek. Aufruf: python pipeline/score.py [--stand JJJJ-MM-TT]
"""
import csv
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
STUFEN = ["niedrig", "erhoeht", "hoch"]

PROJEKT = {
    "name": "Cyberlage",
    "von": "Dreier Labs",
    "link": "https://dreierlabs.com",
    "art": "Privates Projekt, keine amtliche Stelle",
}

HINWEISE = [
    "Kein Ersatz für Warnungen des BSI oder eines CERT.",
    "KEV ist eine weltweite Liste ausgenutzter Schwachstellen und enthält keine Angaben zu Sektoren oder Betroffenen.",
    "Die Liste ist für den Abgleich mit dem eigenen Bestand gedacht: Wer verteidigt, weiß selbst, was im Einsatz ist.",
    "Die Stufe zeigt, wie viele Schwachstellen neu als ausgenutzt gelten, im Vergleich zu den letzten 12 Monaten. Sie gilt allgemein, nicht für einen bestimmten Sektor, und sagt nichts über einzelne Angriffe.",
    "ENISA-Werte gelten für die EU insgesamt, nicht für Deutschland.",
]


def lese_csv(pfad):
    with open(pfad, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def im_fenster(eintraege, stand, tage):
    """Einträge der letzten `tage` Tage bis einschließlich `stand`."""
    von = stand - timedelta(days=tage)
    return [e for e in eintraege if von < date.fromisoformat(e["hinzugefuegt"]) <= stand]


def bestimme_stufe(anzahl, anzahl_ransomware, regeln):
    """Gibt (stufe, begruendung) zurück. Ohne freigegebene Schwellen gibt es keine Stufe."""
    if regeln.get("status") != "freigegeben":
        return None, "Schwellen sind noch nicht freigegeben (Entwurf), daher keine Bewertung."
    ebene = 0
    if anzahl >= regeln["erhoeht_ab"]:
        ebene = 1
    if anzahl >= regeln["hoch_ab"]:
        ebene = 2
    text = f"{anzahl} neu aufgenommene ausgenutzte Schwachstellen in {regeln['fenster_tage']} Tagen"
    if anzahl_ransomware >= regeln["ransomware_aufschlag_ab"]:
        ebene = min(ebene + 1, len(STUFEN) - 1)
        text += f", davon {anzahl_ransomware} mit bekannter Ransomware-Nutzung (eine Stufe höher)"
    return STUFEN[ebene], text + "."


def liste_neu(fenster):
    """Neueste zuerst. Nur Angaben aus dem KEV plus ein Link zur CVE-Seite, keine Technikdetails."""
    return [
        {
            "cve": e["cve"],
            "hersteller": e["hersteller"],
            "produkt": e["produkt"],
            "hinzugefuegt": e["hinzugefuegt"],
            "frist": e["frist"],
            "ransomware_bekannt": e["ransomware_bekannt"],
            "link": f"https://nvd.nist.gov/vuln/detail/{e['cve']}",
        }
        for e in sorted(fenster, key=lambda e: (e["hinzugefuegt"], e["cve"]), reverse=True)
    ]


def verlauf(alle, regeln, stand, wochen=52):
    """Rückblick: dieselbe Rechnung für jeden Wochenstand der letzten `wochen` Wochen (mit den heutigen Schwellen)."""
    tage = regeln["fenster_tage"]
    punkte = []
    for i in range(wochen, -1, -1):
        d = stand - timedelta(days=7 * i)
        fenster = im_fenster(alle, d, tage)
        ransom = sum(e["ransomware_bekannt"] for e in fenster)
        stufe, _ = bestimme_stufe(len(fenster), ransom, regeln)
        punkte.append({"stand": d.isoformat(), "neu": len(fenster), "ransomware_bekannt": ransom, "stufe": stufe})
    return punkte


def lese_optional(pfad):
    try:
        return json.loads(Path(pfad).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def zusatz_bsi(daten, stand, tage):
    """CERT-Bund-Warnungen im Fenster. Ohne Datei: None ('keine Daten')."""
    if not daten:
        return None
    von = (stand - timedelta(days=tage)).isoformat()
    bis = stand.isoformat()
    im = [e for e in daten["eintraege"] if von < e["datum"] <= bis]
    sieben = (stand - timedelta(days=7)).isoformat()
    return {
        "quelle": daten["meta"]["quelle"], "quelle_url": daten["meta"]["quelle_url"],
        "abgerufen_am": daten["meta"].get("abgerufen_am"),
        "fenster_tage": tage,
        "daten_seit": min(e["datum"] for e in daten["eintraege"]),
        "kritisch_7_tage": sum(1 for e in im if e["schwere"] == "kritisch" and e["datum"] > sieben),
        "hoch_7_tage": sum(1 for e in im if e["schwere"] == "hoch" and e["datum"] > sieben),
        "kritisch_30_tage": sum(1 for e in im if e["schwere"] == "kritisch"),
        "hoch_30_tage": sum(1 for e in im if e["schwere"] == "hoch"),
        "liste": [e for e in im if e["schwere"] in ("kritisch", "hoch")][:40],
    }


def zusatz_eu(daten, stand, tage):
    if not daten:
        return None
    von = (stand - timedelta(days=tage)).isoformat()
    bis = stand.isoformat()
    im = [e for e in daten["eintraege"] if von < e["ausgenutzt_seit"] <= bis]
    return {
        "quelle": daten["meta"]["quelle"], "quelle_url": daten["meta"]["quelle_url"],
        "abgerufen_am": daten["meta"].get("abgerufen_am"), "fenster_tage": tage,
        "daten_seit": min(e["ausgenutzt_seit"] for e in daten["eintraege"]),
        "neu_30_tage": len(im), "liste": im[:40],
    }


def werte_aus(kev, regeln, enisa, stand, bsi=None, eu=None):
    tage = regeln["fenster_tage"]
    alle = kev["eintraege"]
    fenster = im_fenster(alle, stand, tage)
    ransom = sum(e["ransomware_bekannt"] for e in fenster)
    ergebnis = {
        "projekt": PROJEKT,
        "stand": stand.isoformat(),
        "kev": {
            "gesamt": len(alle),
            "neu_7_tage": len(im_fenster(alle, stand, 7)),
            f"neu_{tage}_tage": len(fenster),
            f"ransomware_bekannt_{tage}_tage": ransom,
        },
        "fenster_tage": tage,
        "stufe": None,
        "stufe_begruendung": "",
        "neu": liste_neu(fenster),
        "schwellen": {k: regeln.get(k) for k in ("erhoeht_ab", "hoch_ab", "ransomware_aufschlag_ab")},
        "verlauf": verlauf(alle, regeln, stand),
        "cert_bund": zusatz_bsi(bsi, stand, tage),
        "eu_kev": zusatz_eu(eu, stand, tage),
    }
    ergebnis["stufe"], ergebnis["stufe_begruendung"] = bestimme_stufe(len(fenster), ransom, regeln)

    ergebnis["sektor"] = [
        {
            "kennzahl": z["kennzahl"],
            "wert": float(z["wert"]),
            "einheit": z["einheit"],
            "berichtsjahr": z["berichtsjahr"],
            "seite": z["seite"],
            "geltungsbereich": z["geltungsbereich"],
            "quelle": z["quelle"],
            "link": z["quelle_url"],
            "lizenz": z["lizenz"],
        }
        for z in enisa if z["status"].strip().casefold() == "geprueft"
    ]
    ergebnis["quellen"] = [
        {
            "id": "cisa-kev",
            "name": "CISA Known Exploited Vulnerabilities",
            "link": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
            "lizenz": kev["meta"].get("lizenz"),
            "quelle_abruf": kev["meta"].get("quelle"),
            "veroeffentlicht_am": kev["meta"].get("veroeffentlicht_am"),
            "abgerufen_am": kev["meta"].get("abgerufen_am"),
        }
    ] + [
        {"id": "enisa", "name": q, "link": link, "lizenz": lizenz}
        for q, link, lizenz in sorted({(z["quelle"], z["link"], z["lizenz"]) for z in ergebnis["sektor"]})
    ]
    for schluessel, name, lizenz in (("cert_bund", "CERT-Bund / BSI Warn- und Informationsdienst", "nur Titel und Links, Nutzungsbedingungen des BSI beachten"),
                                      ("eu_kev", "EU-KEV (EUVD von ENISA)", "Lizenz nicht ausdrücklich geklärt")):
        z = ergebnis.get(schluessel)
        if z:
            ergebnis["quellen"].append({"id": schluessel, "name": name, "link": z["quelle_url"], "lizenz": lizenz,
                                        "abgerufen_am": z.get("abgerufen_am")})
    ergebnis["hinweise"] = HINWEISE
    return ergebnis


def main(argv):
    stand = datetime.now(timezone.utc).date()
    if "--stand" in argv:
        stand = date.fromisoformat(argv[argv.index("--stand") + 1])
    kev = json.loads((WURZEL / "data" / "kev" / "kev.json").read_text(encoding="utf-8"))
    regeln = json.loads((WURZEL / "config" / "regeln.json").read_text(encoding="utf-8"))
    enisa = lese_csv(WURZEL / "data" / "enisa.csv")
    ergebnis = werte_aus(kev, regeln, enisa, stand,
                         lese_optional(WURZEL / "data" / "bsi" / "warnungen.json"),
                         lese_optional(WURZEL / "data" / "eu" / "kev.json"))
    ziel = WURZEL / "site" / "data" / "lage.json"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(ergebnis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {ziel.relative_to(WURZEL)} (Stand {stand}, Stufe: {ergebnis['stufe']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
