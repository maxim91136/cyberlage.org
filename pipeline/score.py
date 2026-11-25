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
    "Der Ausblick nennt eine Schätzung (EPSS) für neue Lücken. Er gehört nicht zur Stufe und ist kein Befund.",
]


HINWEISE_EN = [
    "No substitute for warnings from the BSI or a CERT.",
    "KEV is a worldwide list of exploited vulnerabilities and contains no information about sectors or affected parties.",
    "The list is meant for matching against your own inventory: defenders know what they run.",
    "The level shows how many vulnerabilities newly count as exploited compared with the last 12 months. It applies in general, not to any particular sector, and says nothing about individual attacks.",
    "ENISA figures apply to the EU as a whole, not to Germany.",
    "The outlook gives an estimate (EPSS) for new flaws. It is not part of the level and not a finding.",
]

QUELLEN_EN = {
    "cisa-kev": ("CISA Known Exploited Vulnerabilities", "CC0 1.0 (per the LICENSE file of cisagov/kev-data)"),
    "enisa": ("ENISA Threat Landscape 2026", "CC BY 4.0"),
    "cert_bund": ("CERT-Bund / BSI Warning and Information Service", "titles and links only, observe the BSI terms of use"),
    "eu_kev": ("EU-KEV (EUVD by ENISA)", "licence not explicitly clarified"),
    "epss": ("EPSS (FIRST)", "free to use with attribution"),
    "nvd": ("NVD (NIST)", "public domain, only publication date and CVSS score"),
    "cvelist": ("CVE List (CVE Program, MITRE)", "CVE Terms of Use: free to use with attribution, only publication date"),
    "sans": ("SANS Internet Storm Center (Infocon)", "Creative Commons per the ISC footer, only the traffic-light status with attribution"),
}


def begruendung_en(anzahl, anzahl_ransomware, regeln):
    if regeln.get("status") != "freigegeben":
        return "Thresholds are not yet approved (draft), so there is no rating."
    text = f"{anzahl} newly added exploited vulnerabilities in {regeln['fenster_tage']} days"
    if anzahl_ransomware >= regeln["ransomware_aufschlag_ab"]:
        text += f", {anzahl_ransomware} of them with known ransomware use (one level higher)"
    return text + "."


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


def pegel_fortschreiben(reihe, alle, regeln, stand, monate=36):
    """Dreier-Pegel als Zahl: neu aufgenommene KEV-Einträge in den letzten 30 Tagen (der Wert, aus dem die Stufe folgt).
    `reihe` ist die gespeicherte Tagesreihe (Liste von Einträgen). Fehlende frühere Tage werden einmalig rückgerechnet
    (quelle 'rueckgerechnet', mit den heutigen Schwellen). Der Wert des Stichtags wird live eingetragen (quelle 'live').
    Frühere Live-Einträge bleiben unverändert, so ist der Verlauf so, wie er veröffentlicht war."""
    tage = regeln["fenster_tage"]
    vorhanden = {p["stand"]: p for p in reihe}
    tag = stand - timedelta(days=round(monate * 365 / 12))
    while tag <= stand:
        iso = tag.isoformat()
        if iso not in vorhanden or tag == stand:
            f = im_fenster(alle, tag, tage)
            r = sum(e["ransomware_bekannt"] for e in f)
            st, _ = bestimme_stufe(len(f), r, regeln)
            vorhanden[iso] = {"stand": iso, "wert": len(f), "ransomware_bekannt": r, "stufe": st,
                              "quelle": "live" if tag == stand else "rueckgerechnet"}
        tag += timedelta(days=1)
    return [vorhanden[k] for k in sorted(vorhanden)]


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


def radar_stufe(wert, cfg):
    """Ordnet den Radar-Score (0 bis 100) einer Stufe aus config/radar_stufen.json zu (obere Grenze ausgeschlossen)."""
    if not isinstance(wert, (int, float)) or not cfg:
        return None
    for st in cfg.get("stufen", []):
        if wert < st["bis"]:
            return st
    return None


def fazit(score, kev_stufe, cfg, tempo_stufe=None):
    """Fester Text: Stufe des Dreier-Pegels (Gesamtscore) mit den beiden Bausteinen KEV-Menge und Tempo, keine Berechnung und keine Vorhersage."""
    st = radar_stufe((score or {}).get("wert"), cfg)
    pg = (cfg or {}).get("pegel", {}).get(kev_stufe)
    if not st or not pg:
        return None
    tp = (cfg or {}).get("tempo", {}).get(tempo_stufe) if tempo_stufe else None
    rang = {"niedrig": 0, "erhoeht": 1, "hoch": 2}
    wirksam = kev_stufe if rang.get(kev_stufe, 0) >= rang.get(tempo_stufe, 0) else tempo_stufe
    hint = (cfg or {}).get("pegel", {}).get(wirksam) or pg
    text = st["satz"] + " " + pg["satz"] + (" " + tp["satz"] if tp else "")
    text_en = st["satz_en"] + " " + pg["satz_en"] + (" " + tp["satz_en"] if tp else "")
    return {"status": cfg.get("status"), "stufe": st["name"], "stufe_en": st["name_en"], "ampel": st.get("ampel"), "kev_stufe": kev_stufe,
            "tempo_stufe": tempo_stufe, "text": text, "text_en": text_en, "hinweis": hint["hinweis"], "hinweis_en": hint["hinweis_en"], "stand": cfg.get("geprueft_am")}


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


def zusatz_ausblick(daten):
    """Ausblick (EPSS + NVD). Nicht Teil der Stufe. Ohne Datei: None ('keine Daten')."""
    if not daten or not isinstance(daten.get("liste"), list):
        return None
    return {k: daten.get(k) for k in ("abgerufen_am", "fenster_tage", "geprueft", "schwelle_hoch",
                                       "hoch_wahrscheinlich", "epss_datum", "liste")}


def zusatz_radar(daten):
    """Lage-Radar (eigene Messungen und Einschätzungen anderer). Nicht Teil der Stufe. Ohne Datei: None."""
    if not daten or not daten.get("zeit_bis_kev"):
        return None
    z = dict(daten["zeit_bis_kev"])
    z["verlauf"] = z.get("verlauf", [])[-36:]
    return {"abgerufen_am": daten.get("abgerufen_am"), "zeit_bis_kev": z, "trefferquote": daten.get("trefferquote"),
            "europa": daten.get("europa"), "sans": daten.get("sans"), "ncsc": daten.get("ncsc"),
            "einschaetzungen": daten.get("einschaetzungen") or [], "gruende": daten.get("gruende") or []}


def mit_bereich(liste, cfg):
    """Hängt an jeden KEV-Eintrag seinen Bereich an (config/bereiche.json); ohne Konfiguration bleibt die Liste, wie sie ist."""
    if not cfg:
        return liste
    import bereiche
    for e in liste:
        e["bereich"] = bereiche.zuordnen(e.get("hersteller"), e.get("produkt"), cfg)
    return liste


def werte_aus(kev, regeln, enisa, stand, bsi=None, eu=None, telegram_link=None, ausblick=None, radar=None, bereiche_cfg=None):
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
        "neu": mit_bereich(liste_neu(fenster), bereiche_cfg),
        "bereiche": {"status": (bereiche_cfg or {}).get("status"), "geprueft_am": (bereiche_cfg or {}).get("geprueft_am"), "liste": []},
        "schwellen": {k: regeln.get(k) for k in ("erhoeht_ab", "hoch_ab", "ransomware_aufschlag_ab", "basis_monate", "median")},
        "verlauf": verlauf(alle, regeln, stand, wochen=round(regeln.get("basis_monate", 12) * 52 / 12)),
        "telegram": {"link": telegram_link},
        "cert_bund": zusatz_bsi(bsi, stand, tage),
        "eu_kev": zusatz_eu(eu, stand, tage),
        "ausblick": zusatz_ausblick(ausblick),
        "radar": zusatz_radar(radar),
    }
    ergebnis["stufe"], ergebnis["stufe_begruendung"] = bestimme_stufe(len(fenster), ransom, regeln)
    if bereiche_cfg:
        import bereiche
        ergebnis["bereiche"]["liste"] = bereiche.uebersicht(ergebnis["neu"], bereiche_cfg, stand)
    else:
        ergebnis.pop("bereiche", None)
    if ergebnis.get("radar"):
        import fetch_radar
        r = ergebnis["radar"]
        r["konsens"] = fetch_radar.konsens(ergebnis["stufe"], r["zeit_bis_kev"], r["einschaetzungen"], r.get("sans"),
                                       len(fenster), regeln.get("erhoeht_ab"), tempo_cfg=regeln.get("tempo"))
        r["pruefung"] = lese_optional(WURZEL / "data" / "radar" / "pruefung.json")

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
    if ergebnis.get("ausblick"):
        ab = ergebnis["ausblick"]["abgerufen_am"]
        ergebnis["quellen"] += [
            {"id": "epss", "name": "EPSS (FIRST)", "link": "https://www.first.org/epss/",
             "lizenz": "kostenlos mit Quellenangabe", "abgerufen_am": ab},
            {"id": "nvd", "name": "NVD (NIST)", "link": "https://nvd.nist.gov/",
             "lizenz": "gemeinfrei, nur Veröffentlichungsdatum und CVSS-Wert", "abgerufen_am": ab},
        ]
    if ergebnis.get("radar"):
        ab = ergebnis["radar"]["abgerufen_am"]
        ergebnis["quellen"].append({"id": "cvelist", "name": "CVE-Liste (CVE Program, MITRE)", "link": "https://github.com/CVEProject/cvelistV5",
                                    "lizenz": "CVE Terms of Use: frei nutzbar mit Quellenangabe, nur Veröffentlichungsdatum", "abgerufen_am": ab})
        if ergebnis["radar"].get("ncsc"):
            ergebnis["quellen"].append({"id": "ncsc", "name": "NCSC-NL Beveiligingsadviezen", "link": "https://advisories.ncsc.nl/",
                                        "lizenz": "Lizenz nicht geprüft, nur Zahl der Advisories mit Quellenangabe", "lizenz_en": "licence not checked, only the number of advisories with source attribution", "abgerufen_am": ergebnis["radar"]["abgerufen_am"]})
        if ergebnis["radar"].get("sans"):
            ergebnis["quellen"].append({"id": "sans", "name": "SANS Internet Storm Center (Infocon)", "link": "https://isc.sans.edu/",
                                        "lizenz": "Creative Commons laut Fußzeile des ISC, nur Ampelstatus mit Quellenangabe", "abgerufen_am": ergebnis["radar"]["sans"]["abgerufen_am"]})
    ergebnis["hinweise"] = HINWEISE
    ergebnis["hinweise_en"] = HINWEISE_EN
    ergebnis["stufe_begruendung_en"] = begruendung_en(len(fenster), ransom, regeln)
    for q in ergebnis["quellen"]:
        if q.get("id") in QUELLEN_EN:
            q["name_en"], q["lizenz_en"] = QUELLEN_EN[q["id"]]
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
                         lese_optional(WURZEL / "data" / "eu" / "kev.json"),
                         (lese_optional(WURZEL / "config" / "telegram.json") or {}).get("kanal_link"),
                         lese_optional(WURZEL / "data" / "ausblick" / "ausblick.json"),
                         lese_optional(WURZEL / "data" / "radar" / "radar.json"),
                         lese_optional(WURZEL / "config" / "bereiche.json"))
    pfad = WURZEL / "data" / "pegel.json"
    gespeichert = (lese_optional(pfad) or {}).get("reihe", [])
    reihe = pegel_fortschreiben(gespeichert, kev["eintraege"], regeln, stand)
    pfad.write_text(json.dumps({"meta": {"name": "KEV-Menge", "wert": "neu aufgenommene KEV-Einträge in den letzten 30 Tagen",
                                          "marken": {"erhoeht_ab": regeln.get("erhoeht_ab"), "hoch_ab": regeln.get("hoch_ab")},
                                          "hinweis": "live = am Stichtag berechnet und nicht mehr verändert; rueckgerechnet = nachträglich mit den heutigen Schwellen"},
                                  "reihe": reihe}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    (WURZEL / "site" / "data").mkdir(parents=True, exist_ok=True)
    (WURZEL / "site" / "data" / "pegel.json").write_text(pfad.read_text(encoding="utf-8"), encoding="utf-8")  # auch unter cyberlage.org/data/pegel.json abrufbar
    if ergebnis.get("radar") and (ergebnis["radar"].get("konsens") or {}).get("score"):
        sp = WURZEL / "data" / "radar" / "score.json"
        rs = ergebnis["radar"]["konsens"]["score"]
        import modell
        mcfg = lese_optional(WURZEL / "config" / "modell.json")
        aus = {x["name_en"]: x.get("ausschlag") for x in ergebnis["radar"]["konsens"]["signale"]}
        einzel = {b["id"]: aus.get(b.get("signal")) for b in mcfg["bausteine"] if b["status"] == "aktiv" and b.get("signal")}
        # Archiv-Bausteine: Tageswerte aus echten Meldungen (data/radar/historie), Ausschlag = Wert / Schwelle
        hd = WURZEL / "data" / "radar" / "historie"
        archiv = modell.archiv_reihen({k: lese_optional(hd / (k + ".json")) for k in ("cert_bund", "ncsc_nl", "eu_kev", "microsoft", "dshield", "ransomware")}, stand.isoformat())
        arch_aus = {}
        kon = ergebnis["radar"]["konsens"]
        for bst in mcfg["bausteine"]:
            if bst["status"] != "aktiv" or not bst.get("schwelle") or bst["id"] not in archiv:
                continue
            reihe_b = [x for x in archiv[bst["id"]] if x["wert"] is not None]
            arch_aus[bst["id"]] = {x["stand"]: x["wert"] / bst["schwelle"] for x in reihe_b}
            heute_w = reihe_b[-1]["wert"] if reihe_b and reihe_b[-1]["stand"] == stand.isoformat() else None
            einzel[bst["id"]] = None if heute_w is None else heute_w / bst["schwelle"]
            kon["signale"].append({"name": bst["kurz"], "name_en": bst["kurz"], "erhoeht": None if heute_w is None else heute_w >= bst["schwelle"],
                                   "grund": bst["regel"], "grund_en": bst["regel_en"], "art": "extern", "baustein": bst["id"],
                                   "ausschlag": None if heute_w is None else round(heute_w / bst["schwelle"], 2),
                                   "wert": heute_w, "schwelle": bst["schwelle"], "misst": bst["name"], "misst_en": bst["name_en"],
                                   "zeitraum": bst["zeitraum"], "zeitraum_en": bst["zeitraum_en"], "daten_seit": reihe_b[0]["stand"] if reihe_b else None})
        folge = {}
        for nr, bst in enumerate(mcfg["bausteine"]):
            folge[bst.get("signal") or bst["id"]] = nr
        kon["signale"].sort(key=lambda x: folge.get(x.get("baustein") or x["name_en"], 99))
        ext = [x for x in kon["signale"] if x["art"] == "extern" and x["erhoeht"] is not None]
        kon["erhoeht"], kon["bewertet"] = sum(1 for x in ext if x["erhoeht"]), len(ext)
        ms = modell.score(einzel, mcfg)
        if ms:
            rs.update(wert=ms["wert"], signale=ms["signale"], von=ms["von"], gruppen=ms["gruppen"], modell=mcfg["version"])
        beob = modell.beobachtung_heute(stand, lese_optional(WURZEL / "data" / "bsi" / "warnungen.json"), lese_optional(WURZEL / "data" / "eu" / "kev.json"),
                                        lese_optional(WURZEL / "data" / "patches" / "microsoft.json"), ergebnis["radar"].get("ncsc"))
        beob = {b["id"]: beob.get(b["id"]) for b in mcfg["bausteine"] if b["status"] == "beobachtung"}
        bp = WURZEL / "data" / "radar" / "bausteine.json"
        bp.write_text(json.dumps(modell.speichern(lese_optional(bp), stand, mcfg["version"], einzel, beob), ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        rs["beobachtung"] = [dict(b, wert=beob.get(b["id"])) for b in mcfg["bausteine"] if b["status"] == "beobachtung"]
        rs["modell_gruppen"] = [dict(g, bausteine=[{"id": b["id"], "signal": b.get("signal") or b.get("kurz"), "name": b.get("kurz") or b["name"], "name_en": b.get("kurz") or b["name_en"], "status": b["status"], "historie": b.get("historie"),
                                                    "ausschlag": None if einzel.get(b["id"]) is None else round(einzel[b["id"]], 2)}
                                                   for b in mcfg["bausteine"] if b["gruppe"] == g["id"] and b["status"] == "aktiv"]) for g in mcfg["gruppen"]]
        sr = [p for p in (lese_optional(sp) or {}).get("reihe", []) if p["stand"] != stand.isoformat()]
        # Ein Modell: frühere Live-Tage werden aus den gespeicherten Einzelwerten und den Archivdaten mit dem heutigen Modell neu gerechnet.
        gesp = {x["stand"]: x.get("aktiv") or {} for x in (lese_optional(bp) or {}).get("reihe", [])}
        sr = [x for x in sr if x["stand"] in gesp]  # Tage ohne gespeicherte Einzelwerte lassen sich nicht nach dem heutigen Modell rechnen
        for x in sr:
            if x["stand"] in gesp:
                e_d = dict(gesp[x["stand"]])
                e_d.update({k: v[x["stand"]] for k, v in arch_aus.items() if x["stand"] in v})
                neu_sc = modell.score(e_d, mcfg)
                if neu_sc:
                    x.update(wert=neu_sc["wert"], signale=neu_sc["signale"], von=neu_sc["von"], modell=mcfg["version"])
        sr.append({"stand": stand.isoformat(), "wert": rs["wert"], "signale": rs["signale"], "von": rs["von"], "modell": rs.get("modell")})
        sp.write_text(json.dumps({"meta": {"name": "Dreier-Pegel (Gesamtscore)", "hinweis": "Tagesstand des vollen Pegels, live gespeichert; die Rückrechnung aus den Archivdaten steht in lage.json"},
                                  "reihe": sr}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        rs["live_seit"] = sr[0]["stand"]
        rs["reihe"] = sr[-90:]
        rtempo = (ergebnis["radar"].get("zeit_bis_kev") or {}).get("tempo_reihe") or []
        ar = dict(arch_aus)
        if regeln.get("erhoeht_ab"):
            ar["kev_menge"] = {x["stand"]: x["wert"] / regeln["erhoeht_ab"] for x in reihe}
        tb = (regeln.get("tempo") or {}).get("erhoeht_bis")
        if tb:
            ar["tempo"] = {x["stand"]: tb / max(x["wert"], 1.0) for x in rtempo}
        kev_tage = {x["stand"] for x in reihe}
        alt = [x for x in modell.rueck_reihe(ar, mcfg) if x["stand"] in kev_tage]
        live = {x["stand"]: x for x in sr}
        rs["reihe_voll"] = [{"stand": x["stand"], "ausnutzung": x["ausnutzung"], "n": x["n"],
                             "wert": live[x["stand"]]["wert"] if x["stand"] in live else None,
                             "signale": live[x["stand"]]["signale"] if x["stand"] in live else None} for x in alt]
    import fetch_radar
    tcfg = regeln.get("tempo")
    zk = (ergebnis.get("radar") or {}).get("zeit_bis_kev") or {}
    tj = zk.get("jetzt") or {}
    if tcfg and tj:
        ergebnis["tempo"] = {"wert": tj.get("median_frisch"), "n": tj.get("n_frisch"), "fenster_tage": tcfg.get("fenster_tage", 90),
                             "stufe": fetch_radar.tempo_stufe(tj.get("median_frisch"), tj.get("n_frisch"), tcfg),
                             "marken": {"erhoeht_bis": tcfg["erhoeht_bis"], "hoch_bis": tcfg["hoch_bis"]},
                             "stand": stand.isoformat(), "reihe": zk.get("tempo_reihe", [])[-90:]}
        zk.pop("tempo_reihe", None)  # steht gekürzt unter tempo.reihe, vollständig in data/radar/radar.json
    stufen_cfg = lese_optional(WURZEL / "config" / "radar_stufen.json")
    rsc = ((ergebnis.get("radar") or {}).get("konsens") or {}).get("score")
    if rsc and stufen_cfg:
        st = radar_stufe(rsc["wert"], stufen_cfg)
        if st:
            rsc["stufe"] = {"name": st["name"], "name_en": st["name_en"], "ampel": st.get("ampel"), "satz": st["satz"], "satz_en": st["satz_en"], "status": stufen_cfg.get("status")}
        ergebnis["fazit"] = fazit(rsc, ergebnis["stufe"], stufen_cfg, (ergebnis.get("tempo") or {}).get("stufe"))
        sig = [x for x in ergebnis["radar"]["konsens"]["signale"] if isinstance(x.get("ausschlag"), (int, float))]
        ueber = sorted([x for x in sig if x["ausschlag"] >= 1], key=lambda x: -x["ausschlag"])
        if ergebnis.get("fazit") and sig:
            de = lambda v: ("%.1f" % v).replace(".", ",")
            top = ueber[:3]
            ergebnis["fazit"]["treiber"] = ("%d von %d Bausteinen liegen an oder über ihrer Schwelle" % (len(ueber), len(sig))) + (
                ", am stärksten: " + ", ".join("%s (%s-fach)" % (x["name"], de(x["ausschlag"])) for x in top) + "." if top else ".")
            ergebnis["fazit"]["treiber_en"] = ("%d of %d components are at or above their threshold" % (len(ueber), len(sig))) + (
                ", strongest: " + ", ".join("%s (%.1fx)" % (x["name_en"], x["ausschlag"]) for x in top) + "." if top else ".")
            ergebnis["fazit"]["stufe_satz"], ergebnis["fazit"]["stufe_satz_en"] = rsc["stufe"]["satz"], rsc["stufe"]["satz_en"]
            th = (stufen_cfg.get("treiber_hinweise") or {}).get((top[0].get("baustein") or top[0]["name_en"]) if top else "")
            if th:
                ergebnis["fazit"]["hinweis"] += " " + th["de"]
                ergebnis["fazit"]["hinweis_en"] += " " + th["en"]
            ergebnis["fazit"]["text"] += " " + ergebnis["fazit"]["treiber"]
            ergebnis["fazit"]["text_en"] += " " + ergebnis["fazit"]["treiber_en"]
        ergebnis["radar_skala"] = {"status": stufen_cfg.get("status"),
                                   "stufen": [{"bis": x["bis"], "name": x["name"], "name_en": x["name_en"], "ampel": x.get("ampel")} for x in stufen_cfg["stufen"]]}
    ms = lese_optional(WURZEL / "data" / "patches" / "microsoft.json")
    if ms and ms.get("monate"):
        kompakt = {k: {f: w for f, w in m.items() if f != "cve_liste"} for k, m in ms["monate"].items()}
        ergebnis["patches"] = {"microsoft": {"meta": ms.get("meta"), "monate": kompakt}}
    prio = lese_optional(WURZEL / "data" / "patches" / "prioritaet.json")
    if prio and prio.get("liste") is not None:
        bcfg = lese_optional(WURZEL / "config" / "bereiche.json")
        if bcfg and isinstance(prio.get("liste"), list):  # Bereich je Eintrag: Quelle entscheidet, bei Microsoft der Titel der Lücke
            import bereiche
            import fetch_patches
            nach_quelle = {q["name"]: q.get("bereich") for q in fetch_patches.QUELLEN}
            for e in prio["liste"]:
                e["bereich"] = nach_quelle.get(e.get("quelle")) or bereiche.zuordnen("Microsoft", e.get("titel", ""), bcfg)
        ergebnis.setdefault("patches", {})["prioritaet"] = prio
    hers = lese_optional(WURZEL / "data" / "patches" / "hersteller.json")
    if hers and hers.get("quellen"):
        ergebnis.setdefault("patches", {})["hersteller"] = {"meta": hers.get("meta"), "quellen": {k: {f: w for f, w in q.items() if f != "reihe"} for k, q in hers["quellen"].items()}}
    ergebnis["kev_menge"] = {"wert": reihe[-1]["wert"], "stufe": ergebnis["stufe"], "marken": {"erhoeht_ab": regeln.get("erhoeht_ab"), "hoch_ab": regeln.get("hoch_ab")},
                             "live_seit": next((p["stand"] for p in reihe if p["quelle"] == "live"), None), "reihe": reihe[-90:]}
    # Der Dreier-Pegel ist der Gesamtscore aus allen Bausteinen (KEV-Menge, Tempo bis KEV, externe Signale).
    ergebnis["kev_stufe"] = ergebnis["stufe"]
    if rsc and rsc.get("stufe"):
        ergebnis["stufe"] = next((x["ampel"] for x in stufen_cfg["stufen"] if x["name"] == rsc["stufe"]["name"]), None)
        ergebnis["stufe_begruendung"] = "Gesamtscore %s von 100 aus %s von %s Bausteinen." % (rsc["wert"], rsc["signale"], rsc["von"])
        ergebnis["stufe_begruendung_en"] = "Overall score %s of 100 from %s of %s components." % (rsc["wert"], rsc["signale"], rsc["von"])
        ergebnis["pegel"] = {"wert": rsc["wert"], "signale": rsc["signale"], "von": rsc["von"], "stufe": rsc["stufe"], "status": stufen_cfg.get("status"),
                             "live_seit": rsc.get("live_seit"), "modell": rsc.get("modell"), "von_bausteine": rsc.get("von"), "reihe": rsc.pop("reihe_voll", rsc.get("reihe", []))}
    else:
        ergebnis["stufe"], ergebnis["stufe_begruendung"], ergebnis["stufe_begruendung_en"], ergebnis["pegel"] = None, "Der Gesamtscore ist noch nicht berechenbar.", "The overall score cannot be computed yet.", None
    ziel = WURZEL / "site" / "data" / "lage.json"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    # Schlanke Ausgabe: die lange Tagesreihe des Pegels spaltenweise (ein Wert je Tag ab "start"), ohne Einrückung
    pg = ergebnis.get("pegel") or {}
    lang = pg.get("reihe") or []
    if len(lang) > 1 and all(date.fromisoformat(lang[i + 1]["stand"]) - date.fromisoformat(lang[i]["stand"]) == timedelta(days=1) for i in range(len(lang) - 1)):
        pg["reihe_k"] = {"start": lang[0]["stand"], "a": [x["ausnutzung"] for x in lang], "n": [x["n"] for x in lang],
                         "live": {x["stand"]: [x["wert"], x["signale"]] for x in lang if x.get("wert") is not None}}
        del pg["reihe"]
    ziel.write_text(json.dumps(ergebnis, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    # Kleine Statusdatei für die Überwachung: Stand, Pegel und ob alle Bausteine einen Wert haben
    sig = [x for x in ((ergebnis.get("radar") or {}).get("konsens") or {}).get("signale", [])]
    fehlend = [x["name"] for x in sig if not isinstance(x.get("ausschlag"), (int, float))]
    pgs = ergebnis.get("pegel") or {}
    status = {"stand": ergebnis.get("stand"), "abgerufen_am": (ergebnis.get("radar") or {}).get("abgerufen_am"), "stufe": ergebnis.get("stufe"),
              "pegel": pgs.get("wert"), "bausteine": pgs.get("signale"), "von": pgs.get("von"), "fehlend": fehlend,
              "vollstaendig": bool(pgs.get("von")) and pgs.get("signale") == pgs.get("von") and not fehlend}
    (WURZEL / "site" / "data" / "status.json").write_text(json.dumps(status, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"OK: {ziel.relative_to(WURZEL)} (Stand {stand}, Dreier-Pegel: {ergebnis['stufe']}, KEV-Menge: {ergebnis['kev_stufe']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
