"""Audit: Gesamtscore aus Einzelprüfungen und der Regeldatei (regeln.json). Reine Rechnung, kein Netz."""
import json
from pathlib import Path

REGELN = json.loads((Path(__file__).parent / "regeln.json").read_text(encoding="utf-8"))


def stufe(score, regeln=REGELN):
    for grenze, name in regeln["stufen"]:
        if score >= grenze:
            return name


def rechne(ergebnisse, regeln=REGELN):
    """ergebnisse: Liste (gruppe, id, ergebnis, text). Gruppen ohne Prüfung zählen als nicht geprüft.
    Gibt Score (oder None bei zu wenig Abdeckung), Abdeckung, Gruppenwerte und die Stufe zurück."""
    wert = regeln["wertung"]
    gruppen = {}
    for g, _pid, erg, _text in ergebnisse:
        gruppen.setdefault(g, []).append(wert[erg])
    gesamt = sum(x["gewicht"] for x in regeln["gruppen"].values())
    geprueft = sum(regeln["gruppen"][g]["gewicht"] for g in gruppen)
    abdeckung = geprueft / gesamt
    werte = {g: sum(v) / len(v) for g, v in gruppen.items()}
    summe = sum(werte[g] * regeln["gruppen"][g]["gewicht"] for g in werte) / geprueft * 100 if geprueft else 0
    score = round(summe)
    if any(werte.get(g, 1) == 0 for g in regeln["deckel"]["gruppen"]):
        score = min(score, regeln["deckel"]["max_score"])
    voll = abdeckung >= regeln["mindest_abdeckung"]
    return {"score": score if voll else None, "teilwert": score, "abdeckung": round(abdeckung, 2),
            "gruppen": {g: round(v, 2) for g, v in werte.items()},
            "stufe": stufe(score, regeln) if voll else "nicht bewertet (zu wenig geprüft)"}
