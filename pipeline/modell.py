"""Modell des Dreier-Pegels: Bausteine in Gruppen, versioniert (config/modell.json).

Aktive Bausteine gehen mit ihrem Ausschlag (Messwert im Verhältnis zur Regelschwelle) in den Score ein.
Bausteine im Status "beobachtung" werden täglich gespeichert (data/radar/bausteine.json), zählen aber noch nicht.
Wer ein neues Modell (v2) einführt, rechnet es aus den gespeicherten Einzelwerten rückwirkend neu; die alte Version bleibt als Vergleichsreihe möglich.
Nur Standardbibliothek.
"""
import json
from datetime import timedelta
from pathlib import Path


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
    rw = (hist.get("ransomware") or {}).get("tage")
    if rw:
        # neue Einträge auf Leak-Seiten in den 30 vollständigen Tagen vor dem Stichtag (der laufende Tag ist unvollständig)
        liste = [d for d, n in rw.items() for _ in range(int(n))]
        gestern = plus(bis, -1)
        out["ransomware"] = [{"stand": plus(x["stand"], 1), "wert": x["wert"]} for x in fenster_reihe(liste, 30, plus(min(rw), 30), gestern)]
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


def logbuch_stufenwechsel(logbuch, live_reihe, stufe_von, namen):
    """Trägt Stufenwechsel der gespeicherten Live-Reihe als Ereignis ins Logbuch ein (jeden Wechsel einmal).
    live_reihe: [{stand, wert}] aufsteigend; stufe_von: Funktion Wert -> Stufenschlüssel; namen: {Schlüssel: (deutsch, englisch)}."""
    vorhanden = {(e["datum"], e.get("schluessel")) for e in logbuch.get("eintraege", [])}
    neu = []
    for a, b in zip(live_reihe, live_reihe[1:], strict=False):
        sa, sb = stufe_von(a["wert"]), stufe_von(b["wert"])
        if sa == sb or (b["stand"], "stufe:" + sb) in vorhanden:
            continue
        rauf = b["wert"] > a["wert"]
        neu.append({"datum": b["stand"], "art": "ereignis", "schluessel": "stufe:" + sb,
                    "titel": "Stufenwechsel: von „%s“ auf „%s“" % (namen[sa][0], namen[sb][0]), "titel_en": "Level change: from “%s” to “%s”" % (namen[sa][1], namen[sb][1]),
                    "text": "Der Dreier-Pegel %s von %d auf %d." % ("stieg" if rauf else "fiel", a["wert"], b["wert"]),
                    "text_en": "The Dreier Gauge %s from %d to %d." % ("rose" if rauf else "fell", a["wert"], b["wert"]), "belege": [], "belege_en": []})
    if neu:
        logbuch.setdefault("eintraege", []).extend(neu)
    return neu


def _lb_juenger(logbuch, praefix, stand, tage=7):
    """Gibt es einen Eintrag mit diesem Schlüsselanfang, der höchstens `tage` Tage vor `stand` liegt?"""
    from datetime import date
    s = date.fromisoformat(stand)
    return any((e.get("schluessel") or "").startswith(praefix) and 0 <= (s - date.fromisoformat(e["datum"])).days <= tage
               for e in logbuch.get("eintraege", []))


def logbuch_ausfall(logbuch, stand, fehlend):
    """Trägt Bausteine ohne Wert als Ereignis ein, je Baustein höchstens einmal in sieben Tagen."""
    neu = []
    for name in fehlend:
        if _lb_juenger(logbuch, "ausfall:" + name, stand):
            continue
        neu.append({"datum": stand, "art": "ereignis", "schluessel": "ausfall:" + name,
                    "titel": "Baustein ohne Wert: %s" % name, "titel_en": "Component without a value: %s" % name,
                    "text": "Die Quelle lieferte keinen Wert. Der Baustein zählt so lange nicht mit, der Pegel wird aus den übrigen gerechnet.",
                    "text_en": "The source delivered no value. The component does not count until it does, the gauge is computed from the others.",
                    "belege": [], "belege_en": []})
    logbuch.setdefault("eintraege", []).extend(neu)
    return neu


def logbuch_hoechststand(logbuch, live_reihe, mindest=30):
    """Trägt einen neuen Höchststand der gespeicherten Tagesstände ein: erst ab `mindest` Tagen Reihe, höchstens einmal in sieben Tagen."""
    if len(live_reihe) < mindest:
        return []
    letzter, davor = live_reihe[-1], max(x["wert"] for x in live_reihe[:-1])
    if letzter["wert"] <= davor or _lb_juenger(logbuch, "hoechst", letzter["stand"]):
        return []
    e = {"datum": letzter["stand"], "art": "ereignis", "schluessel": "hoechst:%d" % letzter["wert"],
         "titel": "Höchststand: Dreier-Pegel bei %d" % letzter["wert"], "titel_en": "New high: Dreier Gauge at %d" % letzter["wert"],
         "text": "Höchster gespeicherter Tagesstand seit %s. Bisher höchster Wert: %d." % (live_reihe[0]["stand"], davor),
         "text_en": "Highest stored daily value since %s. Previous high: %d." % (live_reihe[0]["stand"], davor), "belege": [], "belege_en": []}
    logbuch.setdefault("eintraege", []).append(e)
    return [e]


PRUEFSUMME_DATEIEN = ("modell.json", "radar_stufen.json", "regeln.json")  # alles, was den Pegel und seine Stufe bestimmt


def pruefsumme(verzeichnis):
    """SHA-256 über die Regeldateien des Pegels (kanonisches JSON, ohne Formatierung). Ein Test hält sie fest:
    wer Schwellen, Bausteine oder Stufen ändert, muss Version, Änderungsprotokoll und RULES.md mitführen."""
    import hashlib
    h = hashlib.sha256()
    for n in PRUEFSUMME_DATEIEN:
        h.update(n.encode() + b"\0")
        h.update(json.dumps(json.loads((Path(verzeichnis) / n).read_text(encoding="utf-8")), sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    return h.hexdigest()


def logbuch_modell(logbuch, mcfg):
    """Trägt jede Version aus dem Änderungsprotokoll (config/modell.json) einmal als Modell-Eintrag ins Logbuch ein."""
    vorhanden = {e.get("schluessel") for e in logbuch.get("eintraege", [])}
    neu = []
    for a in mcfg.get("aenderungen", []):
        schluessel = "modell:" + a["version"]
        if schluessel in vorhanden:
            continue
        neu.append({"datum": a["datum"], "art": "modell", "schluessel": schluessel,
                    "titel": "Modell des Dreier-Pegels: %s" % a["version"], "titel_en": "Dreier Gauge model: %s" % a["version"],
                    "text": a["text"], "text_en": a["text_en"], "belege": [], "belege_en": []})
    if neu:
        logbuch.setdefault("eintraege", []).extend(neu)
    return neu


MONATE = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember")
MONATE_EN = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def _zeitraeume(erster, letzter):
    """Alle Monate, Quartale und Jahre, die ganz zwischen `erster` und `letzter` (date, einschließlich) liegen."""
    from datetime import date, timedelta
    out = []
    for jahr in range(erster.year, letzter.year + 1):
        grenzen = [("jahr", "%d" % jahr, date(jahr, 1, 1), date(jahr, 12, 31), "%d" % jahr, "%d" % jahr)]
        for q in range(4):
            ende = date(jahr + (q == 3), (q * 3 + 3) % 12 + 1, 1) - timedelta(days=1)
            grenzen.append(("quartal", "%d-Q%d" % (jahr, q + 1), date(jahr, q * 3 + 1, 1), ende, "Q%d %d" % (q + 1, jahr), "Q%d %d" % (q + 1, jahr)))
        for mo in range(12):
            ende = date(jahr + (mo == 11), (mo + 1) % 12 + 1, 1) - timedelta(days=1)
            grenzen.append(("monat", "%d-%02d" % (jahr, mo + 1), date(jahr, mo + 1, 1), ende, "%s %d" % (MONATE[mo], jahr), "%s %d" % (MONATE_EN[mo], jahr)))
        out += [g for g in grenzen if g[2] >= erster and g[3] <= letzter]
    return out


def _baustein_mittel(bausteine, alle, vor, mindest_anteil, obergrenze):
    """Mittel je Baustein im Zeitraum (Ausschläge höchstens `obergrenze`); `roh` für den Vergleich mit dem nächsten Zeitraum."""
    bs = []
    for b in bausteine:
        v = [min(b["aus"][d], obergrenze) for d in alle if b["aus"].get(d) is not None]
        if len(v) < mindest_anteil * len(alle):
            continue
        bm = sum(v) / len(v)
        alt = vor.get("b", {}).get(b["id"])
        bs.append({"id": b["id"], "name": b["name"], "name_en": b["name_en"], "roh": bm, "mittel": round(bm, 2),
                   "ueber": round(100 * sum(1 for x in v if x >= 1) / len(v)), "delta": None if alt is None else round(bm - alt, 2)})
    return bs


def _stufenverteilung(da, wert, stufe):
    """Tage je Ampelfarbe und Zahl der Wechsel zwischen aufeinanderfolgenden vorhandenen Tagen."""
    je = {}
    for d in da:
        a = stufe(wert[d])["ampel"]
        je[a] = je.get(a, 0) + 1
    wechsel = sum(1 for a, b in zip(da, da[1:], strict=False) if stufe(wert[a])["ampel"] != stufe(wert[b])["ampel"])
    return je, wechsel


def _berichtssaetze(art, titel, titel_en, mittel, st, delta, wert, hoch, tief, wechsel, top):
    """Der Bericht als deutscher und englischer Satz."""
    de = lambda v, n=1: ("%.*f" % (n, v)).replace(".", ",")
    kurz = lambda iso: "%d.%d." % (int(iso[8:10]), int(iso[5:7]))
    kurz_en = lambda iso: "%d %s" % (int(iso[8:10]), MONATE_EN[int(iso[5:7]) - 1][:3])
    dv, dv_en = {"monat": ("Vormonat", "previous month"), "quartal": ("Vorquartal", "previous quarter"), "jahr": ("Vorjahr", "previous year")}[art]
    vgl = "" if delta is None else (", unverändert zum %s" % dv if abs(delta) < 0.05 else ", %s Punkte %s als im %s" % (de(abs(delta)), "höher" if delta > 0 else "niedriger", dv))
    vgl_en = "" if delta is None else (", unchanged from the %s" % dv_en if abs(delta) < 0.05 else ", %.1f points %s than in the %s" % (abs(delta), "higher" if delta > 0 else "lower", dv_en))
    satz = "%s: Dreier-Pegel im Mittel %s von 100 (%s)%s. Höchststand %d (%s), Tiefststand %d (%s), %d %s." % (
        titel, de(mittel), st["name"], vgl, wert[hoch], kurz(hoch), wert[tief], kurz(tief), wechsel, "Stufenwechsel")
    satz_en = "%s: Dreier Gauge averaged %.1f out of 100 (%s)%s. High %d (%s), low %d (%s), %d level change%s." % (
        titel_en, mittel, st["name_en"], vgl_en, wert[hoch], kurz_en(hoch), wert[tief], kurz_en(tief), wechsel, "" if wechsel == 1 else "s")
    if top:
        satz += " Stärkster Baustein: %s, im Mittel das %s-Fache der Schwelle, an %d %% der Tage an oder über der Schwelle." % (top["name"], de(top["mittel"]), top["ueber"])
        satz_en += " Strongest component: %s, on average %.1fx its threshold, at or above it on %d%% of days." % (top["name_en"], top["mittel"], top["ueber"])
    return satz, satz_en


def berichte(tage, bausteine, logbuch, stufen, stand, mindest_anteil=0.9, obergrenze=2.0):
    """Berichte je abgeschlossenem Monat, Quartal und Jahr aus der Tagesreihe des Pegels.
    tage: [{stand, wert}] aufsteigend; bausteine: [{id, name, name_en, aus: {stand: ausschlag}}];
    stufen: [{bis, name, name_en, ampel}]; stand: heutiges Datum (ISO), der laufende Zeitraum bekommt keinen Bericht.
    Ausschläge der Bausteine zählen wie im Pegel höchstens mit `obergrenze`."""
    from datetime import date, timedelta
    if not tage:
        return []
    wert = {x["stand"]: x["wert"] for x in tage}
    stufe = lambda w: next((s for s in stufen if w < s["bis"]), stufen[-1])
    out, vorher = [], {}
    for art, kennung, von, bis, titel, titel_en in _zeitraeume(date.fromisoformat(tage[0]["stand"]), date.fromisoformat(stand) - timedelta(days=1)):
        alle = [(von + timedelta(days=i)).isoformat() for i in range((bis - von).days + 1)]
        da = [d for d in alle if d in wert]
        if len(da) < mindest_anteil * len(alle):
            continue
        vor = vorher.get(art) or {}
        vor = vor if vor.get("bis") == (von - timedelta(days=1)).isoformat() else {}  # nur mit dem unmittelbar vorangehenden Zeitraum vergleichen
        w = [wert[d] for d in da]
        mittel = sum(w) / len(w)
        st = stufe(round(mittel))
        hoch, tief = max(da, key=lambda d: (wert[d], d)), min(reversed(da), key=lambda d: wert[d])  # bei gleichem Wert der spätere Tag
        je, wechsel = _stufenverteilung(da, wert, stufe)
        bs = _baustein_mittel(bausteine, alle, vor, mindest_anteil, obergrenze)
        top = max(bs, key=lambda x: x["mittel"]) if bs else None
        alt_m = vor.get("mittel")
        delta = None if alt_m is None else round(mittel - alt_m, 1)
        eintraege = [{"datum": e["datum"], "art": e["art"], "titel": e["titel"], "titel_en": e["titel_en"]}
                     for e in sorted(logbuch.get("eintraege", []), key=lambda e: e["datum"]) if von.isoformat() <= e["datum"] <= bis.isoformat()]
        satz, satz_en = _berichtssaetze(art, titel, titel_en, mittel, st, delta, wert, hoch, tief, wechsel, top)
        out.append({"id": kennung, "art": art, "titel": titel, "titel_en": titel_en, "von": von.isoformat(), "bis": bis.isoformat(), "tage": len(da),
                    "mittel": round(mittel, 1), "stufe": {"name": st["name"], "name_en": st["name_en"], "ampel": st["ampel"]}, "delta": delta,
                    "hoch": {"wert": wert[hoch], "datum": hoch}, "tief": {"wert": wert[tief], "datum": tief}, "wechsel": wechsel,
                    "je_stufe": [{"ampel": s["ampel"], "name": s["name"], "name_en": s["name_en"], "tage": je[s["ampel"]]} for s in stufen if s["ampel"] in je],
                    "bausteine": bs, "logbuch": eintraege, "satz": satz, "satz_en": satz_en})
        vorher[art] = {"bis": bis.isoformat(), "mittel": mittel, "b": {x["id"]: x["roh"] for x in bs}}
        for x in bs:
            del x["roh"]
    return sorted(out, key=lambda x: x["bis"], reverse=True)
