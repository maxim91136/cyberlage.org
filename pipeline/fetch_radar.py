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


def feodo_verlauf(verlauf, messung, heute):
    """Schreibt den Tageswert fort (data/radar/feodo.json). Eigene Zeitreihe, Quelle liefert keine Historie."""
    if messung:
        verlauf[heute.isoformat()] = messung["online"]
    return verlauf


def konsens(lage_stufe, zeit, einschaetzungen, sans, verlauf):
    """Signale: jedes steht für sich auf erhöht (True), normal (False) oder keine Aussage (None).
    Eigene Signale (Stufe und Tempo, beide aus dem KEV) zählen nicht als Bestätigung, nur externe.
    Regeln stehen in RULES.md. Es wird nichts gemittelt."""
    signale = []

    def add(name, name_en, wert, grund, grund_en, art="extern"):
        signale.append({"name": name, "name_en": name_en, "erhoeht": wert, "grund": grund, "grund_en": grund_en, "art": art})

    add("Cyberlage", "Cyberlage", None if lage_stufe is None else lage_stufe in ("erhoeht", "hoch"),
        f"Stufe {lage_stufe}" if lage_stufe else "keine Bewertung", f"level {lage_stufe}" if lage_stufe else "no rating", "eigen")
    j, v = (zeit or {}).get("jetzt") or {}, (zeit or {}).get("vor_12_monaten") or {}
    t = None
    if j.get("n_frisch", 0) >= 10 and v.get("n_frisch", 0) >= 10 and j.get("median_frisch") is not None and v.get("median_frisch") is not None:
        t = v["median_frisch"] / max(j["median_frisch"], 0.5) >= 1.5
    add("Tempo bis KEV", "Speed to KEV", t, "Median mindestens 1,5-mal schneller als vor 12 Monaten", "median at least 1.5x faster than 12 months ago", "eigen")
    bsi = next((e for e in einschaetzungen if e.get("wert") and e.get("basis")), None)
    add("BSI Cyber Index", "BSI Cyber Index", None if not bsi else float(bsi["wert"]) >= 1.2 * float(bsi["basis"]),
        "mindestens 20 % über dem Basisjahr 2024", "at least 20% above the 2024 base year")
    add("SANS Infocon", "SANS Infocon", None if not sans else sans["status"] != "green", "nicht grün", "not green")
    werte = [verlauf[k] for k in sorted(verlauf)]
    f = None
    if len(werte) >= 31:
        alt = sorted(werte[:-1][-90:])
        med = statistics.median(alt)
        f = werte[-1] >= 1.25 * med and werte[-1] - med >= 3  # bei kleinen Zahlen sonst Zufallsrauschen
    add("Botnetz-Server (Feodo)", "Botnet servers (Feodo)", f, "aktive Steuerserver mindestens 25 % und mindestens 3 über dem Median der letzten 90 Tage (ab 30 Messtagen)",
        "active command servers at least 25% and at least 3 above the 90-day median (from 30 days of data)")
    extern = [x for x in signale if x["art"] == "extern" and x["erhoeht"] is not None]
    return {"signale": signale, "erhoeht": sum(1 for x in extern if x["erhoeht"]), "bewertet": len(extern), "messtage_feodo": len(werte)}


def baue(kev, eu, ausblick, cache, prognosen, heute, sans=None, feodo=None, serie=None, ncsc=None):
    eintraege = kev["eintraege"]
    zeit = zeit_bis_aufnahme(eintraege, cache, heute)
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
    serie = feodo_verlauf(serie, feodo, heute)
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
