#!/usr/bin/env python3
"""Patch-Berichte aus öffentlichen Herstellerquellen (nur Standardbibliothek, ohne Konto).

Stufe 1: Microsoft Security Response Center, CVRF v3.0 (JSON). Je Monat ein Bericht (Patch Day), spätere
Änderungen am Monatsdokument (Out-of-Band, Nachträge) werden als Nachtrag mit der Zahl neuer Lücken festgehalten.
Ausgenommen und getrennt gezählt: Chromium-Lücken im Edge und Paketlücken von Azure Linux (frühere Bezeichnung Mariner), weil sie den Patch Day sonst um ein Vielfaches aufblähen. Gezählt wird nur: Lücken je Schweregrad, ausgenutzt, öffentlich bekannt, Auswirkungsart, betroffene Produktfamilie,
Überschneidung mit dem CISA-KEV. Keine Beschreibungstexte, keine Eigenbewertung der Schwere.

Schreibt data/patches/microsoft.json. Schlägt die Quelle fehl, bleibt die alte Datei bestehen und der Lauf meldet es.
"""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

WURZEL = Path(__file__).resolve().parent.parent
UA = "cyberlage.org (privates Projekt von Dreier Labs, https://cyberlage.org)"
MS_LISTE = "https://api.msrc.microsoft.com/cvrf/v3.0/updates"
MS_DOK = "https://api.msrc.microsoft.com/cvrf/v3.0/cvrf/%s"
MS_QUELLE = "https://msrc.microsoft.com/update-guide"
MS_DATEI = WURZEL / "data" / "patches" / "microsoft.json"
MONATE = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MONAT_ID = re.compile(r"^(\d{4})-(" + "|".join(MONATE) + r")$")
SCHWEREN = ("Critical", "Important", "Moderate", "Low")
BEHALTEN_MONATE = 36
HISTORIE_MONATE = 12  # Vergleichsbasis für die Bewertung
SCHEMA = 2  # erhöhen, wenn sich die Zählweise ändert: dann werden alle Monate neu geholt


class QuellFehler(Exception):
    pass


def lade_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))


def _wert(x):
    return x.get("Value", "") if isinstance(x, dict) else (x or "")


def sammle_produkte(knoten, out=None):
    """ProductID -> Name aus beliebig tief verschachtelten Zweigen des ProductTree."""
    out = {} if out is None else out
    if isinstance(knoten, dict):
        if "ProductID" in knoten and "Value" in knoten and not isinstance(knoten["Value"], (dict, list)):
            out[str(knoten["ProductID"])] = knoten["Value"]
        for v in knoten.values():
            sammle_produkte(v, out)
    elif isinstance(knoten, list):
        for v in knoten:
            sammle_produkte(v, out)
    return out


def familie(name):
    n = name or ""
    if re.search(r"Azure Linux|Mariner", n):
        return "Azure Linux"
    if re.search(r"Windows 11", n):
        return "Windows 11"
    if re.search(r"Windows 10", n):
        return "Windows 10"
    if re.search(r"Windows Server|Windows (Hyper-V|Admin)|Windows Server Update", n):
        return "Windows Server"
    if re.search(r"Windows", n):
        return "Windows (andere)"
    if re.search(r"Edge", n):
        return "Edge"
    if re.search(r"Office|Excel|Word|Outlook|PowerPoint|SharePoint|Teams|OneNote|Visio|Project", n):
        return "Office und SharePoint"
    if re.search(r"Exchange", n):
        return "Exchange"
    if re.search(r"SQL Server|\.NET|Visual Studio|ASP\.NET|PowerShell", n):
        return "Entwicklung und Server"
    if re.search(r"Azure|Dynamics|Power |Microsoft 365|Copilot|Defender|Intune|Entra", n):
        return "Cloud und Dienste"
    return "Sonstige"


def verdichte_dokument(doc, kev_cves=()):
    """CVRF-Dokument -> Kennzahlen eines Monats. Fehlende Felder bleiben unberücksichtigt, nichts wird geraten."""
    kev = set(kev_cves)
    ident = ((doc.get("DocumentTracking") or {}).get("Identification") or {}).get("ID")
    dok_id = _wert(ident)
    verfolgung = doc.get("DocumentTracking") or {}
    produkte = sammle_produkte(doc.get("ProductTree") or {})
    schwere = {k: 0 for k in SCHWEREN}
    schwere["unbekannt"] = 0
    auswirkung, fam = {}, {}
    ausgenutzt, oeffentlich, in_kev, cves, chromium, azure_linux = [], [], [], [], 0, 0
    gesehen = set()
    for v in doc.get("Vulnerability") or []:
        cve = v.get("CVE")
        if not cve or cve in gesehen:
            continue
        gesehen.add(cve)
        titel = _wert(v.get("Title"))
        if titel.lower().startswith("chromium"):
            chromium += 1  # Edge übernimmt Chromium-Lücken; getrennt gezählt, damit sie die Monatszahl nicht verzerren
            continue
        betroffen = set()
        for st in v.get("ProductStatuses") or []:
            for pid in st.get("ProductID") or []:
                betroffen.add(familie(produkte.get(str(pid), "")))
        if betroffen and betroffen <= {"Azure Linux"}:
            azure_linux += 1  # Linux-Paketlücken von Azure Linux (frühere Bezeichnung Mariner) sind kein Patch Day, getrennt gezählt
            continue
        cves.append(cve)
        sev, imp, ex_text = None, None, ""
        for t in v.get("Threats") or []:
            art = t.get("Type")
            text = _wert(t.get("Description"))
            if art == 3 and sev is None:
                sev = text
            elif art == 0 and imp is None:
                imp = text
            elif art == 1 and not ex_text:
                ex_text = text
        schwere[sev if sev in SCHWEREN else "unbekannt"] += 1
        if imp:
            auswirkung[imp] = auswirkung.get(imp, 0) + 1
        if re.search(r"Exploited:\s*Yes", ex_text, re.I):
            ausgenutzt.append(cve)
        if re.search(r"Publicly Disclosed:\s*Yes", ex_text, re.I):
            oeffentlich.append(cve)
        if cve in kev:
            in_kev.append(cve)
        for f in betroffen:
            fam[f] = fam.get(f, 0) + 1
    return {
        "id": dok_id,
        "erste_veroeffentlichung": verfolgung.get("InitialReleaseDate"),
        "aktuell": verfolgung.get("CurrentReleaseDate"),
        "schema": SCHEMA, "cves": len(cves), "davon_chromium_ausgenommen": chromium, "davon_azure_linux_ausgenommen": azure_linux,
        "schwere": schwere,
        "ausgenutzt": len(ausgenutzt), "ausgenutzt_cves": sorted(ausgenutzt)[:25],
        "oeffentlich_bekannt": len(oeffentlich), "oeffentlich_cves": sorted(oeffentlich)[:25],
        "im_kev": len(in_kev), "im_kev_cves": sorted(in_kev)[:25],
        "auswirkung": dict(sorted(auswirkung.items(), key=lambda kv: -kv[1])[:8]),
        "familien": dict(sorted(fam.items(), key=lambda kv: -kv[1])),
        "cve_liste": sorted(cves),
    }


def bewerte(monat, vorherige):
    """Feste Regeln, keine Vorhersage: Größe gegen den Median der bis zu 12 Vormonate, dazu Dringlichkeit nach Ausnutzung."""
    zahlen = [m["cves"] for m in vorherige[-HISTORIE_MONATE:] if isinstance(m.get("cves"), int)]
    med = median(zahlen) if len(zahlen) >= 3 else None
    if med:
        verh = monat["cves"] / med
        groesse = "größer als üblich" if verh >= 1.25 else ("kleiner als üblich" if verh <= 0.8 else "üblicher Umfang")
        groesse_en = "larger than usual" if verh >= 1.25 else ("smaller than usual" if verh <= 0.8 else "usual size")
    else:
        verh, groesse, groesse_en = None, "noch kein Vergleich (zu wenig Vormonate)", "no comparison yet (too few earlier months)"
    kritisch = monat["schwere"].get("Critical", 0)
    if monat["ausgenutzt"] > 0:
        stufe = "dringend"
        empf = "Die %d bereits ausgenutzten Lücken zuerst einspielen, danach die kritischen (%d)." % (monat["ausgenutzt"], kritisch)
        empf_en = "Apply the %d already exploited flaws first, then the critical ones (%d)." % (monat["ausgenutzt"], kritisch)
    elif kritisch > 0:
        stufe = "zeitnah"
        empf = "Kritische Lücken (%d) zeitnah einspielen, den Rest im normalen Zyklus." % kritisch
        empf_en = "Apply critical flaws (%d) promptly, the rest in the normal cycle." % kritisch
    else:
        stufe = "normal"
        empf = "Im normalen Patchzyklus einspielen."
        empf_en = "Apply in the normal patch cycle."
    return {"groesse": groesse, "groesse_en": groesse_en, "verhaeltnis_median": round(verh, 2) if verh else None,
            "median_vormonate": med, "dringlichkeit": stufe, "empfehlung": empf, "empfehlung_en": empf_en}


def lese_datei(pfad):
    try:
        return json.loads(Path(pfad).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def monatsliste(liste_json, anzahl):
    """Die letzten Monatsdokumente (ID wie 2026-Nov) aus der Updateliste, neueste zuletzt."""
    eintraege = []
    for e in (liste_json or {}).get("value", []):
        m = MONAT_ID.match(e.get("ID", ""))
        if m:
            eintraege.append((int(m.group(1)), MONATE.index(m.group(2)), e))
    eintraege.sort(key=lambda t: (t[0], t[1]))
    return [e for _, _, e in eintraege][-anzahl:]


def aktualisiere(alt, liste_json, hole_dok, kev_cves, jetzt):
    """Baut den neuen Stand. Nur Monate, deren Dokument sich seit dem letzten Abruf geändert hat (CurrentReleaseDate), werden neu geholt."""
    alt = alt or {}
    monate = dict(alt.get("monate", {}))
    ziel = monatsliste(liste_json, HISTORIE_MONATE + 1)
    fehler = []
    for e in ziel:
        mid = e["ID"]
        vorher = monate.get(mid)
        if vorher and vorher.get("schema") != SCHEMA:
            vorher = None  # alte Zählweise: neu holen, keine Nachträge daraus ableiten
        if vorher and vorher.get("aktuell") == e.get("CurrentReleaseDate"):
            continue
        try:
            doc = hole_dok(e.get("CvrfUrl") or MS_DOK % mid)
        except Exception as ex:  # fail-soft je Monat
            fehler.append("%s: %s" % (mid, ex))
            continue
        neu = verdichte_dokument(doc, kev_cves)
        neu["id"] = mid
        neu["erste_veroeffentlichung"] = neu["erste_veroeffentlichung"] or e.get("InitialReleaseDate")
        neu["aktuell"] = neu["aktuell"] or e.get("CurrentReleaseDate")
        nachtraege = list((vorher or {}).get("nachtraege", []))
        if vorher:
            vorhanden = set(vorher.get("cve_liste", []))
            zusaetzlich = [c for c in neu["cve_liste"] if c not in vorhanden]
            if zusaetzlich:
                nachtraege.append({"am": neu["aktuell"], "neue_cves": len(zusaetzlich),
                                   "ausgenutzt_neu": len([c for c in zusaetzlich if c in set(neu["ausgenutzt_cves"])])})
        neu["nachtraege"] = nachtraege
        monate[mid] = neu
    reihe = sorted(monate.values(), key=lambda m: m.get("erste_veroeffentlichung") or "")
    for i, m in enumerate(reihe):
        m["bewertung"] = bewerte(m, reihe[:i])
    reihe = reihe[-BEHALTEN_MONATE:]
    if not reihe:
        raise QuellFehler("keine Monatsberichte")
    return {"meta": {"quelle": "Microsoft Security Response Center (CVRF 3.0)", "quelle_url": MS_QUELLE, "listen_url": MS_LISTE,
                     "abgerufen_am": jetzt.isoformat(timespec="seconds"),
                     "hinweis": "Zählung je CVE; Chromium-Lücken im Edge und Linux-Paketlücken von Azure Linux sind ausgenommen und getrennt ausgewiesen. Schweregrad, Ausnutzung und Bekanntheit stammen vom Hersteller.",
                     "fehler": fehler},
            "monate": {m["id"]: m for m in reihe}}


def kev_cves():
    try:
        kev = json.loads((WURZEL / "data" / "kev" / "kev.json").read_text(encoding="utf-8"))
        return [x["cve"] for x in kev["eintraege"]]
    except (OSError, ValueError, KeyError):
        return []


def main():
    jetzt = datetime.now(timezone.utc)
    alt = lese_datei(MS_DATEI)
    try:
        liste = lade_json(MS_LISTE)
        neu = aktualisiere(alt, liste, lade_json, kev_cves(), jetzt)
    except Exception as e:
        print("Microsoft-Patches: Abruf fehlgeschlagen, alter Stand bleibt (%s)" % e)
        return 0
    MS_DATEI.parent.mkdir(parents=True, exist_ok=True)
    MS_DATEI.write_text(json.dumps(neu, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    letzter = list(neu["monate"].values())[-1]
    print("Microsoft-Patches: %d Monate, zuletzt %s mit %d CVEs (%d ausgenutzt)" % (len(neu["monate"]), letzter["id"], letzter["cves"], letzter["ausgenutzt"]))
    for f in neu["meta"]["fehler"]:
        print("  Fehler:", f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
