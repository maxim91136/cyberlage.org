#!/usr/bin/env python3
"""Patch-Berichte aus öffentlichen Herstellerquellen (nur Standardbibliothek, ohne Konto).

Stufe 1: Microsoft Security Response Center, CVRF v3.0 (JSON). Je Monat ein Bericht (Patch Day), spätere
Änderungen am Monatsdokument (Out-of-Band, Nachträge) werden als Nachtrag mit der Zahl neuer Lücken festgehalten.
Ausgenommen und getrennt gezählt: Chromium-Lücken im Edge und Paketlücken von Azure Linux (frühere Bezeichnung Mariner), weil sie den Patch Day sonst um ein Vielfaches aufblähen. Gezählt wird nur: Lücken je Schweregrad, ausgenutzt, öffentlich bekannt, Auswirkungsart, betroffene Produktfamilie,
Überschneidung mit dem CISA-KEV. Keine Beschreibungstexte, keine Eigenbewertung der Schwere.

Stufe 2 und 3: Sicherheitsmeldungen von Linux-Distributionen (Ubuntu, Debian, Red Hat) und von Cisco, nur als Zählung
(neu in 7 und 30 Tagen, davon kritisch, genannte CVEs) mit Kennung, Titel, Datum und Link der letzten Meldungen. Keine Texte.
Schreibt data/patches/microsoft.json und data/patches/hersteller.json. Schlägt die Quelle fehl, bleibt die alte Datei bestehen und der Lauf meldet es.
"""
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timedelta
from email.utils import parsedate_to_datetime
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


# ---------- Stufe 2 und 3: Distributionen und Hersteller ----------
UBUNTU_URL = "https://ubuntu.com/security/notices.json?limit=100&order=newest"
REDHAT_URL = "https://access.redhat.com/hydra/rest/securitydata/cvrf.json?after=%s&per_page=500"
DEBIAN_URLS = ["https://www.debian.org/security/dsa-long.en.rdf", "https://www.debian.org/security/dsa.en.rdf"]
CISCO_URL = "https://sec.cloudapps.cisco.com/security/center/psirtrss20/CiscoSecurityAdvisory.xml"
HERSTELLER_DATEI = WURZEL / "data" / "patches" / "hersteller.json"
CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}")
FENSTER = 30


def lade_roh(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def _tag(e):
    return e.tag.rsplit("}", 1)[-1]


def _kind(e, name):
    for k in e:
        if _tag(k) == name:
            return (k.text or "").strip()
    return ""


def _datum(text):
    """ISO oder RFC 822 oder 'YYYY-MM-DD hh:mm:ss.0' -> date, sonst None."""
    t = (text or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
    try:
        return parsedate_to_datetime(t).date()
    except (TypeError, ValueError):
        return None


def parse_ubuntu(daten):
    out = []
    for n in (daten or {}).get("notices", []):
        d = _datum(n.get("published"))
        if not d or n.get("is_hidden"):
            continue
        out.append({"id": n.get("id", ""), "datum": d, "titel": n.get("title") or n.get("summary") or "", "link": "https://ubuntu.com/security/notices/" + n.get("id", ""),
                    "schwere": None, "cves": [c for c in (n.get("cves_ids") or []) if CVE_RE.fullmatch(str(c))]})
    return out


def parse_redhat(daten):
    out = []
    for n in daten if isinstance(daten, list) else []:
        d = _datum(n.get("released_on"))
        rid = n.get("RHSA") or ""
        if not d or not rid:
            continue
        sev = (n.get("severity") or "").strip().lower() or None
        out.append({"id": rid, "datum": d, "titel": rid, "link": n.get("resource_url") or "https://access.redhat.com/errata/" + rid.replace(":", "-"),
                    "schwere": {"critical": "kritisch", "important": "hoch", "moderate": "mittel", "low": "niedrig"}.get(sev, sev),
                    "cves": [c for c in (n.get("CVEs") or []) if CVE_RE.fullmatch(str(c))]})
    return out


def parse_debian(xml_bytes):
    try:
        wurzel = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise QuellFehler("Debian-Feed kein gültiges XML: %s" % e)
    out = []
    for it in wurzel.iter():
        if _tag(it) != "item":
            continue
        titel, link, datum = _kind(it, "title"), _kind(it, "link"), _datum(_kind(it, "date") or _kind(it, "pubDate"))
        m = re.match(r"(DSA-\d+-\d+)", titel)
        if not datum or not m:
            continue
        out.append({"id": m.group(1), "datum": datum, "titel": titel, "link": link, "schwere": None,
                    "cves": sorted(set(CVE_RE.findall(" ".join((k.text or "") for k in it.iter()))))})
    return out


def parse_cisco(xml_bytes):
    try:
        wurzel = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise QuellFehler("Cisco-Feed kein gültiges XML: %s" % e)
    out = []
    for it in wurzel.iter("item"):
        titel, link = _kind(it, "title"), _kind(it, "link").split("?")[0]
        datum = _datum(_kind(it, "pubDate"))
        text = re.sub(r"<[^>]+>", " ", html.unescape(_kind(it, "description")))  # Beschreibung ist HTML, das selbst maskiert geliefert wird
        m = re.search(r"Security Impact Rating:?\s*(Critical|High|Medium|Low|Informational)", text, re.I)
        sev = {"critical": "kritisch", "high": "hoch", "medium": "mittel", "low": "niedrig"}.get(m.group(1).lower()) if m else None
        if not datum or not titel:
            continue
        out.append({"id": link.rsplit("/", 1)[-1] or titel, "datum": datum, "titel": titel, "link": link, "schwere": sev, "cves": sorted(set(CVE_RE.findall(text)))})
    return out


def verdichte_quelle(items, heute):
    """Zählung der Meldungen der letzten 7 und 30 Tage. Fehlt eine Angabe (z. B. Schweregrad), wird sie nicht geraten."""
    inner = [i for i in items if 0 <= (heute - i["datum"]).days < FENSTER]
    sieben = [i for i in inner if (heute - i["datum"]).days < 7]
    mit_sev = [i for i in inner if i["schwere"]]
    cves = set(c for i in inner for c in i["cves"])
    letzte = sorted(inner, key=lambda i: (i["datum"], i["id"]), reverse=True)[:10]
    return {"neu_7": len(sieben), "neu_30": len(inner), "kritisch_30": len([i for i in inner if i["schwere"] == "kritisch"]) if mit_sev else None,
            "hoch_30": len([i for i in inner if i["schwere"] == "hoch"]) if mit_sev else None, "cves_30": len(cves),
            "schwere_bekannt": bool(mit_sev),
            "letzte": [{"id": i["id"], "datum": i["datum"].isoformat(), "titel": i["titel"][:140], "link": i["link"], "schwere": i["schwere"]} for i in letzte]}


QUELLEN = [
    {"id": "ubuntu", "name": "Ubuntu Security Notices", "typ": "distribution", "url": "https://ubuntu.com/security/notices", "lizenz": "Lizenz nicht ausdrücklich geklärt, nur Zählung, Kennung, Titel, Datum, Link"},
    {"id": "debian", "name": "Debian Security Advisories", "typ": "distribution", "url": "https://www.debian.org/security/", "lizenz": "Lizenz nicht ausdrücklich geklärt, nur Zählung, Kennung, Titel, Datum, Link"},
    {"id": "redhat", "name": "Red Hat Security Advisories", "typ": "distribution", "url": "https://access.redhat.com/security/security-updates/", "lizenz": "Lizenz nicht ausdrücklich geklärt, nur Zählung, Kennung, Titel, Datum, Link"},
    {"id": "cisco", "name": "Cisco Security Advisories", "typ": "hersteller", "url": "https://sec.cloudapps.cisco.com/security/center/publicationListing.x", "lizenz": "Feed nennt nur ein Urheberrecht, keine Nutzungsbedingungen; nur Zählung, Kennung, Titel, Datum, Link"},
]


def hole_quelle(qid, heute, lade=lade_roh):
    if qid == "ubuntu":
        return parse_ubuntu(json.loads(lade(UBUNTU_URL).decode("utf-8")))
    if qid == "redhat":
        return parse_redhat(json.loads(lade(REDHAT_URL % (heute - timedelta(days=FENSTER + 2)).isoformat()).decode("utf-8")))
    if qid == "debian":
        letzter = None
        for u in DEBIAN_URLS:
            try:
                return parse_debian(lade(u))
            except Exception as e:
                letzter = e
        raise QuellFehler("Debian: %s" % letzter)
    if qid == "cisco":
        return parse_cisco(lade(CISCO_URL))
    raise QuellFehler("unbekannte Quelle " + qid)


def aktualisiere_hersteller(alt, heute, jetzt, lade=lade_roh):
    alt = alt or {}
    quellen = dict(alt.get("quellen", {}))
    for q in QUELLEN:
        vorher = quellen.get(q["id"], {})
        try:
            items = hole_quelle(q["id"], heute, lade)
            if not items:
                raise QuellFehler("keine Einträge erkannt")
            z = verdichte_quelle(items, heute)
            reihe = [p for p in vorher.get("reihe", []) if p["stand"] != heute.isoformat()]
            reihe.append({"stand": heute.isoformat(), "neu_30": z["neu_30"]})
            quellen[q["id"]] = dict(q, **z, abgerufen_am=jetzt.isoformat(timespec="seconds"), status="ok", reihe=reihe[-400:])
        except Exception as e:  # fail-soft je Quelle: alter Stand bleibt, Fehler wird vermerkt
            if vorher:
                quellen[q["id"]] = dict(vorher, status="fehler", fehler=str(e)[:200])
            else:
                quellen[q["id"]] = dict(q, status="fehler", fehler=str(e)[:200], neu_7=None, neu_30=None, letzte=[])
    return {"meta": {"hinweis": "Nur Zählung und Verweise auf die Meldungen der Hersteller. Schweregrade stammen von den Herstellern und fehlen, wo sie nicht geliefert werden.",
                     "abgerufen_am": jetzt.isoformat(timespec="seconds")}, "quellen": quellen}


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
        MS_DATEI.parent.mkdir(parents=True, exist_ok=True)
        MS_DATEI.write_text(json.dumps(neu, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        letzter = list(neu["monate"].values())[-1]
        print("Microsoft-Patches: %d Monate, zuletzt %s mit %d CVEs (%d ausgenutzt)" % (len(neu["monate"]), letzter["id"], letzter["cves"], letzter["ausgenutzt"]))
        for f in neu["meta"]["fehler"]:
            print("  Fehler:", f)
    except Exception as e:
        print("Microsoft-Patches: Abruf fehlgeschlagen, alter Stand bleibt (%s)" % e)
    try:
        hs = aktualisiere_hersteller(lese_datei(HERSTELLER_DATEI), jetzt.date(), jetzt)
        HERSTELLER_DATEI.parent.mkdir(parents=True, exist_ok=True)
        HERSTELLER_DATEI.write_text(json.dumps(hs, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        for k, q in hs["quellen"].items():
            print("  %s: %s, neu 7 Tage %s, 30 Tage %s%s" % (k, q["status"], q.get("neu_7"), q.get("neu_30"), (" (%s)" % q["fehler"]) if q.get("fehler") else ""))
    except Exception as e:
        print("Hersteller-Patches: Fehler (%s)" % e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
