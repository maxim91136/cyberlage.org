#!/usr/bin/env python3
"""Lage-Radar: eigene Messungen aus offenen Daten. Nur Standardbibliothek.

1. Zeit bis zur Aufnahme: Tage zwischen Veröffentlichung einer CVE (CVE-Liste, MITRE/CVE Program)
   und ihrer Aufnahme in den CISA-KEV, je Monat. Gezählt wird "frisch" = CVE war bei Aufnahme höchstens
   365 Tage alt (alte Lücken, die spät aufgenommen werden, verzerren sonst den Median).
2. Trefferquote des Ausblicks: Prognosen (EPSS >= 10 %) werden beim ersten Auftreten gespeichert und später
   gegen den KEV geprüft.
3. Abgleich EU-KEV und CISA-KEV (Überschneidung und Abstand der Daten).
4. SANS Internet Storm Center Infocon (Ampel).
5. Feodo Tracker (abuse.ch, CC0): Zahl aktiver Botnetz-Steuerserver, als eigene Tageszeitreihe (data/radar/feodo.json).
Außerdem werden die von Hand geführten Einschätzungen und Gründe (CSV) eingelesen.

Veröffentlichungsdaten ändern sich nicht, sie werden in data/radar/veroeffentlicht.json zwischengespeichert.
Schlägt etwas fehl, bleibt der betreffende Teil leer (null), nichts wird geschätzt.
"""
import csv
import json
import statistics
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
RADAR = WURZEL / "data" / "radar"
UA = "cyberlage.org (privates Projekt von Dreier Labs, https://cyberlage.org)"
CVE_URL = "https://raw.githubusercontent.com/CVEProject/cvelistV5/main/cves/{y}/{g}xxx/{c}.json"
SANS_URL = "https://isc.sans.edu/api/infocon?json"
NCSC_URL = "https://advisories.ncsc.nl/rss/advisories"
FEODO_URL = "https://feodotracker.abuse.ch/downloads/ipblocklist.json"
FEODO_ALLE_URL = "https://feodotracker.abuse.ch/downloads/ipblocklist_aggressive.csv"  # alle je gesehenen Steuerserver mit first_seen und last_online
FEODO_RUECK_TAGE = 1100
ANFANG = "2022-01"      # früheste Monate im Verlauf
FRISCH_TAGE = 365
REIF_TAGE = 30          # so lange gilt eine Prognose als noch offen


def lese(pfad, vorgabe=None):
    try:
        return json.loads(Path(pfad).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return vorgabe


def lese_csv(pfad):
    try:
        with open(pfad, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def tag(text):
    return date.fromisoformat(text[:10])


def cve_url(c):
    _, jahr, nummer = c.split("-")
    return CVE_URL.format(y=jahr, g=int(nummer) // 1000, c=c)


def hole_datum(c):
    for _ in range(3):
        try:
            req = urllib.request.Request(cve_url(c), headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.loads(r.read())
            return c, (d.get("cveMetadata", {}).get("datePublished") or "")[:10] or None
        except urllib.error.HTTPError as ex:
            if ex.code == 404:
                return c, None
        except (urllib.error.URLError, TimeoutError, ValueError):
            pass
    return c, False  # nicht erreichbar: nicht speichern, nächster Lauf versucht es erneut


def veroeffentlichungen(kev_eintraege, cache):
    gesucht = [x["cve"] for x in kev_eintraege if x["hinzugefuegt"][:7] >= ANFANG and x["cve"] not in cache]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for c, d in pool.map(hole_datum, gesucht):
            if d is not False:
                cache[c] = d
    return cache


def zeit_bis_aufnahme(kev_eintraege, veroeff, heute):
    monate = {}
    for x in kev_eintraege:
        monat = x["hinzugefuegt"][:7]
        v = veroeff.get(x["cve"])
        if monat < ANFANG or not v:
            continue
        tage = (tag(x["hinzugefuegt"]) - tag(v)).days
        monate.setdefault(monat, []).append(max(tage, 0))
    verlauf = []
    for m in sorted(monate):
        t = monate[m]
        frisch = [d for d in t if d <= FRISCH_TAGE]
        verlauf.append({
            "monat": m, "n": len(t), "n_frisch": len(frisch),
            "median_frisch": statistics.median(frisch) if frisch else None,
            "anteil_30": round(sum(1 for d in t if d <= 30) / len(t), 3),
        })

    def fenster(ende, tage=90):
        a = ende - timedelta(days=tage)
        t = []
        for x in kev_eintraege:
            v = veroeff.get(x["cve"])
            d = tag(x["hinzugefuegt"])
            if v and a < d <= ende:
                t.append(max((d - tag(v)).days, 0))
        frisch = [d for d in t if d <= FRISCH_TAGE]
        return {"bis": ende.isoformat(), "n": len(t), "n_frisch": len(frisch),
                "median_frisch": statistics.median(frisch) if frisch else None,
                "anteil_30": round(sum(1 for d in t if d <= 30) / len(t), 3) if t else None}

    return {"verlauf": verlauf, "jetzt": fenster(heute), "vor_12_monaten": fenster(heute - timedelta(days=365)),
            "vor_24_monaten": fenster(heute - timedelta(days=730)), "frisch_tage": FRISCH_TAGE,
            "ohne_datum": sum(1 for x in kev_eintraege if x["hinzugefuegt"][:7] >= ANFANG and not veroeff.get(x["cve"]))}


def tempo_median(kev_eintraege, veroeff, ende, fenster_tage=90):
    """Median der Tage von der Veröffentlichung bis zur KEV-Aufnahme (nur "frische" Lücken) der im Fenster aufgenommenen Einträge."""
    a = ende - timedelta(days=fenster_tage)
    t = []
    for x in kev_eintraege:
        v = veroeff.get(x["cve"])
        d = tag(x["hinzugefuegt"])
        if v and a < d <= ende:
            t.append(max((d - tag(v)).days, 0))
    frisch = [d for d in t if d <= FRISCH_TAGE]
    return (statistics.median(frisch) if frisch else None), len(frisch)


def tempo_reihe(kev_eintraege, veroeff, heute, tage=1100, fenster_tage=90, mindest_n=10):
    """Tagesreihe des Dreier-Tempos: gleitender 90-Tage-Median der Tage bis zur KEV-Aufnahme. Aus festen Daten berechnet,
    deshalb jederzeit neu ableitbar. Tage mit weniger als mindest_n frischen Lücken bleiben ohne Wert."""
    out = []
    for i in range(tage, -1, -1):
        d = heute - timedelta(days=i)
        med, n = tempo_median(kev_eintraege, veroeff, d, fenster_tage)
        if med is not None and n >= mindest_n:
            out.append({"stand": d.isoformat(), "wert": med, "n": n})
    return out


def tempo_stufe(median, n, cfg):
    """Dreier-Tempo: je kleiner der Median, desto schneller werden Lücken ausgenutzt gemeldet. Stufen nach festen Marken (Tage)."""
    if not cfg or median is None or n is None or n < cfg.get("mindest_n", 10):
        return None
    if median <= cfg["hoch_bis"]:
        return "hoch"
    if median <= cfg["erhoeht_bis"]:
        return "erhoeht"
    return "niedrig"


def trefferquote(prognosen, kev_eintraege, ausblick, heute):
    """prognosen: {cve: {"erstmals": datum, "epss": wert}} wird fortgeschrieben."""
    kev = {x["cve"]: x["hinzugefuegt"] for x in kev_eintraege}
    for k in (ausblick or {}).get("kandidaten", []):
        prognosen.setdefault(k["cve"], {"erstmals": (ausblick["abgerufen_am"] or "")[:10], "epss": k["epss"]})
    treffer = reif = reif_treffer = offen = 0
    tage = []
    for c, p in prognosen.items():
        d = kev.get(c)
        alter = (heute - tag(p["erstmals"])).days
        if d and tag(d) >= tag(p["erstmals"]):
            treffer += 1
            tage.append((tag(d) - tag(p["erstmals"])).days)
            p["eingetreten"] = d
        if alter >= REIF_TAGE:
            reif += 1
            reif_treffer += 1 if p.get("eingetreten") else 0
        elif not p.get("eingetreten"):
            offen += 1
    return {"prognosen": len(prognosen), "eingetreten": treffer, "offen": offen,
            "reif": reif, "reif_eingetreten": reif_treffer,
            "quote_reif": round(reif_treffer / reif, 3) if reif else None,
            "median_tage_bis_eintritt": statistics.median(tage) if tage else None,
            "seit": min((p["erstmals"] for p in prognosen.values()), default=None),
            "schwelle": (ausblick or {}).get("schwelle_hoch"), "reif_nach_tagen": REIF_TAGE}


def abgleich_eu(kev_eintraege, eu):
    if not eu or not eu.get("eintraege"):
        return None
    kev = {x["cve"]: x["hinzugefuegt"] for x in kev_eintraege}
    gemeinsam, abstaende, eu_zuerst = 0, [], 0
    for x in eu["eintraege"]:
        cves = [c for c in x.get("cve") or [] if c in kev]
        if not cves or not x.get("ausgenutzt_seit"):
            continue
        gemeinsam += 1
        d = (tag(kev[cves[0]]) - tag(x["ausgenutzt_seit"])).days
        abstaende.append(d)
        eu_zuerst += 1 if d > 0 else 0
    return {"eu_eintraege": len(eu["eintraege"]), "auch_im_cisa": gemeinsam,
            "nur_eu": len(eu["eintraege"]) - gemeinsam,
            "median_abstand_tage": statistics.median(abstaende) if abstaende else None,
            "eu_datum_frueher": eu_zuerst}


def hole_sans():
    try:
        req = urllib.request.Request(SANS_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            status = json.loads(r.read()).get("status")
        if status in ("green", "yellow", "orange", "red"):
            return {"status": status, "abgerufen_am": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    except (urllib.error.URLError, TimeoutError, ValueError, AttributeError):
        pass
    return None


def ncsc_zaehlen(xml_text, heute):
    """Zählt Advisories des niederländischen NCSC der letzten 30 Tage und davon die mit Kans und Schade je 'high'."""
    import re
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    wurzel = ET.fromstring(xml_text)
    gesamt = hoch = 0
    for it in wurzel.iter("item"):
        d = it.findtext("pubDate")
        try:
            tag = parsedate_to_datetime(d).date()
        except (TypeError, ValueError):
            continue
        if not 0 <= (heute - tag).days < 30:
            continue
        gesamt += 1
        text = " ".join(filter(None, [it.findtext("title"), it.findtext("description")]))
        k = re.search(r"kans\W+(high|medium|low)", text, re.I)
        sc = re.search(r"schade\W+(high|medium|low)", text, re.I)
        if (k and k.group(1).lower() == "high" and sc and sc.group(1).lower() == "high") or re.search(r"high/high", text, re.I):
            hoch += 1
    return {"advisories_30": gesamt, "hoch_hoch_30": hoch} if gesamt else None


def hole_ncsc(heute):
    """NCSC-NL Beveiligingsadviezen (RSS ohne Konto). None, wenn nicht erreichbar oder nicht lesbar."""
    try:
        req = urllib.request.Request(NCSC_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            return ncsc_zaehlen(r.read(), heute)
    except Exception:
        return None


def hole_feodo():
    """Zahl der derzeit aktiven Botnetz-Steuerserver (Feodo Tracker, abuse.ch, CC0). None, wenn nicht erreichbar."""
    try:
        req = urllib.request.Request(FEODO_URL, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            daten = json.loads(r.read())
        if isinstance(daten, list):
            return {"online": sum(1 for x in daten if str(x.get("status", "")).lower() == "online"), "gelistet": len(daten)}
    except (urllib.error.URLError, TimeoutError, ValueError, AttributeError):
        pass
    return None


def parse_feodo_alle(text, heute, tage=FEODO_RUECK_TAGE):
    """Rückrechnung aus der Liste aller je gesehenen Steuerserver: Ein Server zählt an einem Tag als aktiv, wenn er an diesem Tag
    zwischen first_seen und last_online lag. Näherung: Zwischenzeiten ohne Erreichbarkeit sind nicht bekannt, die Rückrechnung
    liegt daher eher über der Live-Zählung (Status online). Gibt {Datum: Zahl} für die letzten `tage` Tage vor `heute` zurück."""
    kopf, zeilen = None, []
    for z in text.splitlines():
        z = z.strip()
        if not z:
            continue
        if z.startswith("#"):
            if "first_seen" in z and "last_online" in z:
                kopf = [c.strip().strip('"') for c in z.lstrip("# ").split(",")]
            continue
        zeilen.append(z)
    if not kopf:
        raise ValueError("Feodo-Liste ohne Kopfzeile")
    i0, i1 = kopf.index("first_seen_utc") if "first_seen_utc" in kopf else kopf.index("first_seen"), kopf.index("last_online")
    von_bis = []
    for row in csv.reader(zeilen):
        try:
            a = datetime.strptime(row[i0].strip()[:10], "%Y-%m-%d").date()
            b = datetime.strptime(row[i1].strip()[:10], "%Y-%m-%d").date() if row[i1].strip() else heute
        except (ValueError, IndexError):
            continue
        von_bis.append((a, b))
    if not von_bis:
        raise ValueError("Feodo-Liste ohne lesbare Einträge")
    out = {}
    for n in range(1, tage + 1):
        d = heute - timedelta(days=n)
        out[d.isoformat()] = sum(1 for a, b in von_bis if a <= d <= b)
    return out


def feodo_rueckrechnen(verlauf, text, heute):
    """Füllt fehlende Tage der eigenen Reihe aus der Rückrechnung. Echte Messungen werden nie überschrieben.
    Gibt die Liste der rückgerechneten Tage zurück (für die Anzeige)."""
    neu = parse_feodo_alle(text, heute)
    gefuellt = sorted(d for d in neu if d not in verlauf)
    for d in gefuellt:
        verlauf[d] = neu[d]
    return gefuellt


def feodo_verlauf(verlauf, messung, heute):
    """Schreibt den Tageswert fort (data/radar/feodo.json). Eigene Zeitreihe, Quelle liefert keine Historie."""
    if messung:
        verlauf[heute.isoformat()] = messung["online"]
    return verlauf


_STUFE_EN = {"niedrig": "low", "erhoeht": "elevated", "hoch": "high"}


ZEITRAUM = {
    "KEV pace": ("90 Tage, gleitender Median", "90 days, rolling median"),
    "KEV count": ("letzte 30 Tage", "last 30 days"),
    "Speed to KEV": ("letzte 90 Tage gegen vor 12 Monaten", "last 90 days vs 12 months ago"),
    "BSI Cyber Index": ("Jahr 2026 gegen Basisjahr 2024", "year 2026 vs base year 2024"),
    "SANS Infocon": ("aktueller Stand", "current reading"),
    "Botnet servers (Feodo)": ("heute gegen Median der letzten 90 Tage", "today vs median of the last 90 days"),
}


def radar_score(signale, obergrenze=2.0):
    """Experimentell: gleich gewichteter Mittelwert der Ausschläge (Messwert im Verhältnis zur Regelschwelle) aller Signale,
    die einen Wert haben, umgerechnet auf 0 bis 100 (50 = Schwelle im Schnitt erreicht, 100 = im Schnitt doppelt so weit).
    Die Zeiträume der Signale sind verschieden. Kein objektives Maß, fließt in keine Stufe ein."""
    werte = [min(x["ausschlag"], obergrenze) for x in signale if isinstance(x.get("ausschlag"), (int, float))]
    if not werte:
        return None
    return {"wert": round(sum(werte) / len(werte) / obergrenze * 100), "signale": len(werte), "von": len(signale)}


def konsens(lage_stufe, zeit, einschaetzungen, sans, verlauf, neu30=None, erhoeht_ab=None, tempo_cfg=None):
    """Signale: jedes steht für sich auf erhöht (True), normal (False) oder keine Aussage (None).
    Eigene Signale (Stufe und Tempo, beide aus dem KEV) zählen nicht als Bestätigung, nur externe.
    Regeln stehen in RULES.md. Es wird nichts gemittelt."""
    signale = []

    def add(name, name_en, wert, grund, grund_en, art="extern", ausschlag=None):
        """ausschlag: Messwert im Verhältnis zur Regelschwelle (1,0 = Schwelle erreicht), nur für die Radar-Grafik."""
        signale.append({"name": name, "name_en": name_en, "erhoeht": wert, "grund": grund, "grund_en": grund_en, "art": art,
                        "ausschlag": None if ausschlag is None else round(ausschlag, 2)})

    add("KEV-Menge", "KEV count", None if lage_stufe is None else lage_stufe in ("erhoeht", "hoch"),
        f"Stufe {lage_stufe}" if lage_stufe else "keine Bewertung", f"level {_STUFE_EN.get(lage_stufe, lage_stufe)}" if lage_stufe else "no rating", "eigen",
        (neu30 / erhoeht_ab) if neu30 is not None and erhoeht_ab else {"niedrig": 0.5, "erhoeht": 1.0, "hoch": 1.5}.get(lage_stufe))
    j, v = (zeit or {}).get("jetzt") or {}, (zeit or {}).get("vor_12_monaten") or {}
    t = None
    if j.get("n_frisch", 0) >= 10 and v.get("n_frisch", 0) >= 10 and j.get("median_frisch") is not None and v.get("median_frisch") is not None:
        t = v["median_frisch"] / max(j["median_frisch"], 0.5) >= 1.5
    if tempo_cfg:
        med, n = j.get("median_frisch"), j.get("n_frisch", 0)
        st = tempo_stufe(med, n, tempo_cfg)
        add("Tempo bis KEV", "KEV pace", None if st is None else st in ("erhoeht", "hoch"),
            "Median höchstens %s Tage bis zur KEV-Aufnahme (schnellstes Viertel der letzten 36 Monate)" % tempo_cfg["erhoeht_bis"],
            "median at most %s days to KEV listing (fastest quarter of the last 36 months)" % tempo_cfg["erhoeht_bis"], "eigen",
            None if st is None else tempo_cfg["erhoeht_bis"] / max(med, 1.0))
    else:
        add("Tempo bis KEV", "Speed to KEV", t, "Median mindestens 1,5-mal schneller als vor 12 Monaten", "median at least 1.5x faster than 12 months ago", "eigen",
            None if t is None else v["median_frisch"] / max(j["median_frisch"], 0.5) / 1.5)
    bsi = next((e for e in einschaetzungen if e.get("wert") and e.get("basis")), None)
    add("BSI Cyber Index", "BSI Cyber Index", None if not bsi else float(bsi["wert"]) >= 1.2 * float(bsi["basis"]),
        "mindestens 20 % über dem Basisjahr 2024", "at least 20% above the 2024 base year",
        ausschlag=None if not bsi else float(bsi["wert"]) / (1.2 * float(bsi["basis"])))
    add("SANS Infocon", "SANS Infocon", None if not sans else sans["status"] != "green", "nicht grün", "not green",
        ausschlag=None if not sans else {"green": 0.4, "yellow": 1.1, "orange": 1.5, "red": 2.0}.get(sans["status"]))
    werte = [verlauf[k] for k in sorted(verlauf)]
    f = fa = None
    if len(werte) >= 31:
        alt = sorted(werte[:-1][-90:])
        med = statistics.median(alt)
        f = werte[-1] >= 1.25 * med and werte[-1] - med >= 3  # bei kleinen Zahlen sonst Zufallsrauschen
        fa = werte[-1] / (1.25 * med) if med else None
        if fa is not None and not f:
            fa = min(fa, 0.99)
    add("Botnetz-Server (Feodo)", "Botnet servers (Feodo)", f, "aktive Steuerserver mindestens 25 % und mindestens 3 über dem Median der letzten 90 Tage (ab 30 Messtagen)",
        "active command servers at least 25% and at least 3 above the 90-day median (from 30 days of data)",
        ausschlag=fa)
    for x in signale:
        x["zeitraum"], x["zeitraum_en"] = ZEITRAUM.get(x["name_en"], ("", ""))
    extern = [x for x in signale if x["art"] == "extern" and x["erhoeht"] is not None]
    return {"score": radar_score(signale), "signale": signale, "erhoeht": sum(1 for x in extern if x["erhoeht"]), "bewertet": len(extern), "messtage_feodo": len(werte)}


def baue(kev, eu, ausblick, cache, prognosen, heute, sans=None, feodo=None, serie=None, ncsc=None):
    eintraege = kev["eintraege"]
    zeit = zeit_bis_aufnahme(eintraege, cache, heute)
    zeit["tempo_reihe"] = tempo_reihe(eintraege, cache, heute)
    return {
        "abgerufen_am": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "zeit_bis_kev": zeit,
        "trefferquote": trefferquote(prognosen, eintraege, ausblick, heute),
        "europa": abgleich_eu(eintraege, eu),
        "sans": sans,
        "ncsc": ncsc,
        "feodo": feodo,
        "feodo_serie": serie or {},
        "einschaetzungen": lese_csv(RADAR / "einschaetzungen.csv"),
        "gruende": lese_csv(RADAR / "gruende.csv"),
    }


def main():
    kev = lese(WURZEL / "data" / "kev" / "kev.json")
    if not kev:
        print("FEHLER: KEV-Daten fehlen")
        return 1
    cache = lese(RADAR / "veroeffentlicht.json", {})
    prognosen = lese(RADAR / "prognosen.json", {})
    serie = lese(RADAR / "feodo.json", {})
    try:
        cache = veroeffentlichungen(kev["eintraege"], cache)
    except Exception as ex:  # Netz kaputt: mit dem Stand im Cache weiterrechnen
        print("WARNUNG: CVE-Liste nicht vollständig erreichbar:", ex)
    heute = datetime.now(timezone.utc).date()
    feodo = hole_feodo()
    rueck = lese(RADAR / "feodo_rueck.json", {"tage": []})
    if len(rueck.get("tage", [])) < 1000:  # einmalig: Historie aus der Liste aller je gesehenen Steuerserver auffüllen
        try:
            req = urllib.request.Request(FEODO_ALLE_URL, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                rueck["tage"] = sorted(set(rueck.get("tage", [])) | set(feodo_rueckrechnen(serie, r.read().decode("utf-8", "replace"), heute)))
        except Exception as ex:  # fail-soft: ohne Historie bleibt es bei der eigenen Messreihe
            print("WARNUNG: Feodo-Historie nicht abrufbar:", ex)
    serie = feodo_verlauf(serie, feodo, heute)
    (RADAR / "feodo_rueck.json").write_text(json.dumps({"hinweis": "Tage, die aus der Liste aller je gesehenen Steuerserver rückgerechnet wurden (first_seen bis last_online), keine Live-Messung", "tage": rueck.get("tage", [])}, indent=0) + "\n", encoding="utf-8")
    ergebnis = baue(kev, lese(WURZEL / "data" / "eu" / "kev.json"), lese(WURZEL / "data" / "ausblick" / "ausblick.json"),
                    cache, prognosen, heute, hole_sans(), feodo, serie, hole_ncsc(heute))
    RADAR.mkdir(parents=True, exist_ok=True)
    (RADAR / "veroeffentlicht.json").write_text(json.dumps(cache, sort_keys=True, indent=0) + "\n", encoding="utf-8")
    (RADAR / "feodo.json").write_text(json.dumps(serie, sort_keys=True, indent=0) + "\n", encoding="utf-8")
    (RADAR / "prognosen.json").write_text(json.dumps(prognosen, sort_keys=True, indent=0) + "\n", encoding="utf-8")
    (RADAR / "radar.json").write_text(json.dumps(ergebnis, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    z = ergebnis["zeit_bis_kev"]["jetzt"]
    print(f"OK: data/radar/radar.json (Median frisch {z['median_frisch']} Tage, {len(cache)} Daten im Cache, "
          f"{ergebnis['trefferquote']['prognosen']} Prognosen)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
