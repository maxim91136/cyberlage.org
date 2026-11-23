#!/usr/bin/env python3
"""Wertet die Daten nach den offenen Regeln aus (siehe RULES.md).

Liest:   data/kev/kev.json, data/enisa.csv, config/produkte.csv, config/regeln.json
Schreibt: site/data/lage.json

Grundsätze: Es gehen nur freigegebene Produkte und nur geprüfte ENISA-Werte ein.
Fehlt die Grundlage, steht null in der Ausgabe und es wird nichts geschätzt.

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
    "Ein Projekt von Dreier Labs. Privates Projekt, keine amtliche Stelle. Kein Ersatz für Warnungen des BSI oder eines CERT.",
    "KEV ist eine weltweite Liste ausgenutzter Schwachstellen und enthält keine Angaben zu Sektoren.",
    "ENISA-Werte gelten für die EU insgesamt, nicht für Deutschland.",
    "Der Bezug zur Verwaltung beruht auf einer öffentlich geführten Produktliste. Sie ist eine Einschätzung.",
]


def lese_csv(pfad):
    with open(pfad, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def lade_produkte(pfad):
    """Nur Einträge mit Status 'freigegeben' zählen."""
    return [p for p in lese_csv(pfad) if p["status"].strip().casefold() == "freigegeben"]


def passt(eintrag, produkt):
    """Hersteller und Produktname müssen übereinstimmen (Groß-/Kleinschreibung egal).

    Bewusst kein Teiltreffer: 'Exchange' würde sonst auch 'Internet Key Exchange' treffen.
    Namensvarianten im KEV werden als eigene Zeilen in produkte.csv geführt.
    """
    return (eintrag["hersteller"].casefold() == produkt["hersteller"].strip().casefold()
            and eintrag["produkt"].casefold() == produkt["produkt"].strip().casefold())


def im_fenster(eintraege, stand, tage):
    """Einträge der letzten `tage` Tage bis einschließlich `stand`."""
    von = stand - timedelta(days=tage)
    return [e for e in eintraege if von < date.fromisoformat(e["hinzugefuegt"]) <= stand]


def bestimme_stufe(anzahl_relevant, anzahl_ransomware, regeln):
    """Gibt (stufe, begruendung) zurück. Ohne freigegebene Schwellen gibt es keine Stufe."""
    if regeln.get("status") != "freigegeben":
        return None, "Schwellen sind noch nicht freigegeben (Entwurf), daher keine Bewertung."
    ebene = 0
    if anzahl_relevant >= regeln["erhoeht_ab"]:
        ebene = 1
    if anzahl_relevant >= regeln["hoch_ab"]:
        ebene = 2
    text = f"{anzahl_relevant} neue Einträge zu freigegebenen Produkten in {regeln['fenster_tage']} Tagen"
    if anzahl_ransomware > 0:
        ebene = min(ebene + 1, len(STUFEN) - 1)
        text += f", davon {anzahl_ransomware} mit bekannter Ransomware-Nutzung (eine Stufe höher)"
    return STUFEN[ebene], text + "."


def werte_aus(kev, produkte, regeln, enisa, stand):
    tage = regeln["fenster_tage"]
    alle = kev["eintraege"]
    fenster = im_fenster(alle, stand, tage)
    ergebnis = {
        "projekt": PROJEKT,
        "stand": stand.isoformat(),
        "kev": {
            "gesamt": len(alle),
            "neu_7_tage": len(im_fenster(alle, stand, 7)),
            f"neu_{tage}_tage": len(fenster),
            f"ransomware_bekannt_{tage}_tage": sum(e["ransomware_bekannt"] for e in fenster),
        },
        "verwaltungsbezug": {
            "freigegebene_produkte": len(produkte),
            "fenster_tage": tage,
            "neu": None,
            "davon_ransomware_bekannt": None,
        },
        "stufe": None,
        "stufe_begruendung": "",
    }
    if not produkte:
        ergebnis["stufe_begruendung"] = (
            "Keine freigegebene Produktliste, daher kein Bezug zur Verwaltung und keine Bewertung.")
    else:
        relevant = [e for e in fenster if any(passt(e, p) for p in produkte)]
        ransom = sum(e["ransomware_bekannt"] for e in relevant)
        ergebnis["verwaltungsbezug"]["neu"] = len(relevant)
        ergebnis["verwaltungsbezug"]["davon_ransomware_bekannt"] = ransom
        ergebnis["stufe"], ergebnis["stufe_begruendung"] = bestimme_stufe(len(relevant), ransom, regeln)

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
    ergebnis["hinweise"] = HINWEISE
    return ergebnis


def main(argv):
    stand = datetime.now(timezone.utc).date()
    if "--stand" in argv:
        stand = date.fromisoformat(argv[argv.index("--stand") + 1])
    kev = json.loads((WURZEL / "data" / "kev" / "kev.json").read_text(encoding="utf-8"))
    regeln = json.loads((WURZEL / "config" / "regeln.json").read_text(encoding="utf-8"))
    produkte = lade_produkte(WURZEL / "config" / "produkte.csv")
    enisa = lese_csv(WURZEL / "data" / "enisa.csv")
    ergebnis = werte_aus(kev, produkte, regeln, enisa, stand)
    ziel = WURZEL / "site" / "data" / "lage.json"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(ergebnis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: {ziel.relative_to(WURZEL)} (Stand {stand}, Stufe: {ergebnis['stufe']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
