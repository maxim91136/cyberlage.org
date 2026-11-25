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


def nur_gruppe(cfg, gruppe):
    """Modell, reduziert auf eine Gruppe (für die Reihe, die über den ganzen Zeitraum gleich definiert ist)."""
    return dict(cfg, gruppen=[g for g in cfg["gruppen"] if g["id"] == gruppe], bausteine=[b for b in cfg["bausteine"] if b["gruppe"] == gruppe])


def ausnutzung_reihe(kev_reihe, erhoeht_ab, tempo_reihe, tempo_erhoeht_bis, cfg):
    """Tagesreihe der Gruppe Ausnutzung (KEV-Menge, Tempo bis KEV), 0 bis 100. Für diese Bausteine gibt es 36 Monate echte Daten,
    die Reihe ist deshalb über den ganzen Zeitraum gleich definiert. Nur die heutigen Schwellen werden rückwirkend angewendet."""
    tempo = {p["stand"]: p["wert"] for p in tempo_reihe or []}
    sub = nur_gruppe(cfg, "ausnutzung")
    out = []
    for p in kev_reihe:
        d = p["stand"]
        einzel = {}
        if erhoeht_ab:
            einzel["kev_menge"] = p["wert"] / erhoeht_ab
        if d in tempo and tempo_erhoeht_bis:
            einzel["tempo"] = tempo_erhoeht_bis / max(tempo[d], 1.0)
        sc = score(einzel, sub)
        if sc:
            out.append({"stand": d, "ausnutzung": sc["wert"], "n": sc["signale"]})
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


def erstdatum(eintraege):
    """{Kennung: letztes Datum} -> {Kennung: Datum der Erstveröffentlichung}.
    Die Quellen nennen bei aktualisierten Meldungen nur das Datum der Aktualisierung. Die Kennungen werden aber je Jahr
    fortlaufend vergeben. Eine Meldung kann deshalb nicht später erschienen sein als jede Meldung mit höherer Nummer
    desselben Jahres, und nicht später als am 31.12. ihres Jahres. Das früheste dieser Daten ist ihr Erstdatum."""
    jahre = {}
    for k, d in eintraege.items():
        t = k.rsplit("-", 2)
        jahre.setdefault(t[-2], []).append((int(t[-1]), k, d))
    out = {}
    for jahr, xs in jahre.items():
        grenze = jahr + "-12-31"
        for _, k, d in sorted(xs, reverse=True):
            grenze = min(grenze, d)
            out[k] = grenze
    return out


def fenster_reihe(daten, tage, von, bis):
    """Liste von ISO-Daten -> [{stand, wert}] je Tag: Anzahl der Daten im Fenster (stand - tage, stand]."""
    from collections import Counter
    from datetime import date
    c = Counter(daten)
    d0, d1 = date.fromisoformat(von), date.fromisoformat(bis)
    out, summe = [], 0
    t = d0 - timedelta(days=tage - 1)
    while t <= d1:
        summe += c.get(t.isoformat(), 0)
        alt = t - timedelta(days=tage)
        summe -= c.get(alt.isoformat(), 0) if alt >= d0 - timedelta(days=tage - 1) else 0
        if t >= d0:
            out.append({"stand": t.isoformat(), "wert": summe})
        t += timedelta(days=1)
    return out


def quantil(werte, q):
    xs = sorted(werte)
    if not xs:
        return None
    i = (len(xs) - 1) * q
    lo = int(i)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def archiv_reihen(hist, bis):
    """Tageswerte der Archiv-Bausteine aus echten Meldungen. hist: {cert_bund, ncsc_nl, eu_kev, microsoft} (Inhalte der Dateien
    unter data/radar/historie, fehlende sind None). Gibt {baustein_id: [{stand, wert}]} zurück; jede Reihe beginnt erst dort,
    wo das erste volle Fenster im Archiv liegt."""
    from datetime import date
    out = {}
    plus = lambda iso, n: (date.fromisoformat(iso) + timedelta(days=n)).isoformat()
    c = (hist.get("cert_bund") or {})
    if c.get("eintraege") and c.get("vollstaendig_bis"):
        erst = erstdatum({k: v[0] for k, v in c["eintraege"].items()})
        tage = [erst[k] for k, v in c["eintraege"].items() if v[1] in ("k", "h")]
        out["cert_bund"] = fenster_reihe(tage, 30, plus(c["vollstaendig_bis"], 30), bis)
    n = (hist.get("ncsc_nl") or {}).get("eintraege")
    if n:
        erst = erstdatum(n)
        out["ncsc_nl"] = fenster_reihe(list(erst.values()), 30, plus(min(n.values()), 30), bis)
    e = hist.get("eu_kev") or {}
    if e.get("eintraege"):
        out["eu_kev"] = fenster_reihe(list(e["eintraege"].values()), 30, max(plus(min(e["eintraege"].values()), 30), plus(bis, -1130)), bis)
    dsh = (hist.get("dshield") or {}).get("tage")
    if dsh:
        # Angreifende Quellen je Tag, Mittel der sieben vollständigen Tage vor dem Stichtag (der laufende Tag ist noch unvollständig)
        tage = sorted(dsh)
        d0, d1 = date.fromisoformat(tage[0]) + timedelta(days=7), date.fromisoformat(bis)
        reihe, t = [], d0
        while t <= d1:
            fenster = [dsh[x][2] for x in ((t - timedelta(days=n)).isoformat() for n in range(1, 8)) if x in dsh]
            if len(fenster) >= 5:
                reihe.append({"stand": t.isoformat(), "wert": round(sum(fenster) / len(fenster))})
            t += timedelta(days=1)
        out["dshield"] = reihe
    m = (hist.get("microsoft") or {}).get("monate")
    if m:
        xs = sorted(m.values(), key=lambda x: x["tag"])
        reihe, t, i, wert = [], date.fromisoformat(xs[0]["tag"]), 0, None
        ende = date.fromisoformat(bis)
        while t <= ende:
            while i < len(xs) and xs[i]["tag"] <= t.isoformat():
                wert = xs[i]["ausgenutzt"]
                i += 1
            reihe.append({"stand": t.isoformat(), "wert": wert})
            t += timedelta(days=1)
        out["ms_ausgenutzt"] = reihe
    return out


def rueck_reihe(ausschlaege, cfg, ohne_gruppen=("extern",)):
    """ausschlaege: {baustein_id: {stand: ausschlag}}. Rechnet den Pegel je Tag aus allen Bausteinen, die an dem Tag einen
    echten Wert haben. Gruppen ohne Archiv (externe Einschätzungen) bleiben außen vor. Gibt [{stand, ausnutzung, n}] zurück."""
    sub = dict(cfg, gruppen=[g for g in cfg["gruppen"] if g["id"] not in ohne_gruppen],
               bausteine=[b for b in cfg["bausteine"] if b["gruppe"] not in ohne_gruppen])
    tage = sorted(set().union(*[set(v) for v in ausschlaege.values()])) if ausschlaege else []
    out = []
    for d in tage:
        sc = score({k: v.get(d) for k, v in ausschlaege.items()}, sub)
        if sc:
            out.append({"stand": d, "ausnutzung": sc["wert"], "n": sc["signale"]})
    return out
