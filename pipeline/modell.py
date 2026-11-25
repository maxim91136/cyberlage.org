"""Modell des Dreier-Pegels: Bausteine in Gruppen, versioniert (config/modell.json).

Aktive Bausteine gehen mit ihrem Ausschlag (Messwert im Verhältnis zur Regelschwelle) in den Score ein.
Bausteine im Status "beobachtung" werden täglich gespeichert (data/radar/bausteine.json), zählen aber noch nicht.
Wer ein neues Modell (v2) einführt, rechnet es aus den gespeicherten Einzelwerten rückwirkend neu; die alte Version bleibt als Vergleichsreihe möglich.
Nur Standardbibliothek.
"""
import json
from datetime import timedelta


def lade(pfad):
    return json.loads(pfad.read_text(encoding="utf-8"))


def score(einzel, cfg):
    """einzel: {baustein_id: ausschlag oder None}. Gibt {wert, signale, von, gruppen} zurück oder None ohne Messwert."""
    ob = cfg.get("obergrenze", 2.0)
    aktiv = [b for b in cfg["bausteine"] if b["status"] == "aktiv"]
    gruppen, werte = [], []
    for g in cfg["gruppen"]:
        xs = [min(einzel[b["id"]], ob) for b in aktiv if b["gruppe"] == g["id"] and isinstance(einzel.get(b["id"]), (int, float))]
        if xs:
            m = sum(xs) / len(xs)
            werte.append(m)
            gruppen.append({"id": g["id"], "name": g["name"], "name_en": g["name_en"], "ausschlag": round(m, 2), "n": len(xs)})
    n = sum(1 for b in aktiv if isinstance(einzel.get(b["id"]), (int, float)))
    if not werte:
        return None
    return {"wert": round(sum(werte) / len(werte) / ob * 100), "signale": n, "von": len(aktiv), "gruppen": gruppen}


def rueckrechnung(kev_reihe, erhoeht_ab, tempo_reihe, tempo_erhoeht_bis, cfg):
    """Tagesreihe des Scores aus den aktiven Bausteinen mit Historie (KEV-Menge, Tempo). BSI und SANS haben keine Tagesreihe."""
    tempo = {p["stand"]: p["wert"] for p in tempo_reihe or []}
    out = []
    for p in kev_reihe:
        d = p["stand"]
        einzel = {}
        if erhoeht_ab:
            einzel["kev_menge"] = p["wert"] / erhoeht_ab
        if d in tempo and tempo_erhoeht_bis:
            einzel["tempo"] = tempo_erhoeht_bis / max(tempo[d], 1.0)
        s = score(einzel, cfg)
        if s:
            out.append({"stand": d, "wert": s["wert"], "signale": s["signale"], "von": s["von"], "rueck": True})
    return out


def beobachtung_heute(stand, cert_bund, eu_kev, microsoft, ncsc):
    """Rohwerte der Beobachtungs-Bausteine für den Stichtag (ohne Schwelle, daher ohne Ausschlag). None = keine Daten."""
    out = {}
    if cert_bund:
        von = (stand - timedelta(days=7)).isoformat()
        out["cert_bund"] = sum(1 for e in cert_bund.get("eintraege", []) if e["datum"] > von and e["schwere"] in ("kritisch", "hoch"))
    if eu_kev:
        von = (stand - timedelta(days=30)).isoformat()
        out["eu_kev"] = sum(1 for e in eu_kev.get("eintraege", []) if von < e["ausgenutzt_seit"] <= stand.isoformat())
    if microsoft and microsoft.get("monate"):
        letzter = microsoft["monate"][sorted(microsoft["monate"], key=lambda k: microsoft["monate"][k]["erste_veroeffentlichung"])[-1]]
        out["ms_ausgenutzt"] = letzter.get("ausgenutzt")
    if ncsc and isinstance(ncsc.get("advisories_30"), int):
        out["ncsc_nl"] = ncsc["advisories_30"]
    return out


def speichern(alt, stand, version, aktiv, beobachtung):
    """Tageswerte fortschreiben (ein Eintrag je Tag, der Stichtag wird ersetzt)."""
    reihe = [p for p in (alt or {}).get("reihe", []) if p["stand"] != stand.isoformat()]
    reihe.append({"stand": stand.isoformat(), "modell": version,
                  "aktiv": {k: (None if v is None else round(v, 3)) for k, v in aktiv.items()}, "beobachtung": beobachtung})
    return {"meta": {"hinweis": "Einzelwerte je Tag: aktiv = Ausschlag, beobachtung = Rohwert. Ein neues Modell rechnet daraus rückwirkend neu."}, "reihe": reihe}
