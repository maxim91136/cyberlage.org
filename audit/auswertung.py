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
    nicht_geprueft = []
    zutreffend_nicht = set()
    durchgefallen = set()  # Gruppen mit mindestens einer nicht bestandenen Prüfung
    for g, pid, erg, _text in ergebnisse:
        if erg == "nicht_geprueft":  # zählt weder als bestanden noch als nicht bestanden und senkt die Abdeckung
            nicht_geprueft.append(pid)
            continue
        if erg == "nicht_zutreffend":  # trifft auf die Seite nicht zu (z. B. Cookies ohne Cookies): zählt für die Abdeckung, nicht für den Wert
            zutreffend_nicht.add(g)
            continue
        gruppen.setdefault(g, []).append(wert[erg])
        if erg == "nicht_bestanden":
            durchgefallen.add(g)
    gesamt = sum(x["gewicht"] for x in regeln["gruppen"].values())
    geprueft = sum(regeln["gruppen"][g]["gewicht"] for g in set(gruppen) | zutreffend_nicht)
    abdeckung = geprueft / gesamt
    werte = {g: sum(v) / len(v) for g, v in gruppen.items()}
    gewertet = sum(regeln["gruppen"][g]["gewicht"] for g in werte)
    summe = sum(werte[g] * regeln["gruppen"][g]["gewicht"] for g in werte) / gewertet * 100 if gewertet else 0
    score = round(summe)
    if regeln["deckel"].get("schon_ein_fund"):  # Code-Audit: ein einziger Fund in einer Deckelgruppe deckelt den Score
        gedeckelt = any(g in durchgefallen for g in regeln["deckel"]["gruppen"])
    else:  # Web-Audit: nur wenn die ganze Gruppe 0 erreicht
        gedeckelt = any(werte.get(g, 1) == 0 for g in regeln["deckel"]["gruppen"])
    if gedeckelt:
        score = min(score, regeln["deckel"]["max_score"])
    voll = abdeckung >= regeln["mindest_abdeckung"]
    return {"score": score if voll else None, "teilwert": score, "abdeckung": round(abdeckung, 2),
            "gruppen": {g: round(v, 2) for g, v in werte.items()}, "nicht_geprueft": nicht_geprueft,
            "stufe": stufe(score, regeln) if voll else "nicht bewertet (zu wenig geprüft)"}
