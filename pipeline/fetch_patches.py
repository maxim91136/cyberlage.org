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
from concurrent.futures import ThreadPoolExecutor
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
SCHEMA = 7  # erhöhen, wenn sich die Zählweise ändert: dann werden alle Monate neu geholt


class QuellFehler(Exception):
    pass


def lade_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def _wert(x):
    return x.get("Value", "") if isinstance(x, dict) else (x or "")


def patch_stand(v):
    """Aus den Remediations einer CVE: ("ja", [KB...]) wenn ein Hersteller-Fix (Typ 2) vorliegt, ("nein", []) wenn nur
    Umgehung/Abmilderung/kein Fix, ("unbekannt", []) wenn Microsoft keine Angabe liefert."""
    rems = v.get("Remediations") or []
    if not rems:
        return "unbekannt", []
    kbs = []
    for r in rems:
        if r.get("Type") == 2:
            quelle = " ".join([_wert(r.get("Description")), str(r.get("URL") or ""), str(r.get("FixedBuild") or "")])
            m = re.search(r"\bKB\s*(\d{6,8})\b", quelle, re.I) or re.search(r"(?<![\d.])(\d{6,8})(?![\d.])", quelle)
            kb = m.group(1) if m else ""
            if kb and kb not in kbs:
                kbs.append(kb)
    if any(r.get("Type") == 2 for r in rems):
        return "ja", kbs[:3]
    return "nein", []


def fix_liste(v, produkte):
    """Je Hersteller-Fix (Typ 2): KB-Nummer (falls erkennbar) und für welche Produktfamilie. Bis zu 4, ohne Doppelte."""
    out, gesehen = [], set()
    for r in v.get("Remediations") or []:
        if r.get("Type") != 2:
            continue
        quelle = " ".join([_wert(r.get("Description")), str(r.get("URL") or ""), str(r.get("FixedBuild") or "")])
        m = re.search(r"\bKB\s*(\d{6,8})\b", quelle, re.I) or re.search(r"(?<![\d.])(\d{6,8})(?![\d.])", quelle)
        kb = m.group(1) if m else ""
        fams = sorted({familie(produkte.get(str(pid), "")) for pid in (r.get("ProductID") or [])} - {"Sonstige"})[:2]
        fuer = ", ".join(fams)
        schluessel = (kb, fuer, "" if kb else _wert(r.get("Description"))[:40])
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        out.append({"kb": kb, "fuer": fuer, "text": "" if kb else _wert(r.get("Description"))[:90], "url": "" if kb else str(r.get("URL") or "")[:200]})
        if len(out) >= 4:
            break
    return out


def fix_hinweis(v):
    """Erster Hersteller-Fix (Typ 2) mit Beschreibung und Link, wenn keine KB-Nummer erkennbar ist."""
    for r in v.get("Remediations") or []:
        if r.get("Type") == 2:
            return _wert(r.get("Description"))[:90], str(r.get("URL") or "")[:200]
    return "", ""


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
    ausgenutzt, oeffentlich, in_kev, cves, chromium, azure_linux, kandidaten = [], [], [], [], 0, 0, []
    ohne_fix = []
    gesehen = set()
    for v in doc.get("Vulnerability") or []:
        cve = v.get("CVE")
        if not cve or cve in gesehen:
            continue
        gesehen.add(cve)
        titel = _wert(v.get("Title"))
        if titel.lower().startswith("chromium") or "in google chrome prior to" in titel.lower():
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
        patch, kbs = patch_stand(v)
        fix_t, fix_u = fix_hinweis(v)
        fixe = fix_liste(v, produkte)
        if patch == "nein":
            ohne_fix.append(cve)
        ist_aus = bool(re.search(r"Exploited:\s*Yes", ex_text, re.I))
        ist_oeff = bool(re.search(r"Publicly Disclosed:\s*Yes", ex_text, re.I))
        if ist_aus or ist_oeff or cve in kev or sev == "Critical":
            fam_c = set()
            for st in v.get("ProductStatuses") or []:
                for pid in st.get("ProductID") or []:
                    fam_c.add(familie(produkte.get(str(pid), "")))
            kandidaten.append({"cve": cve, "titel": titel[:120], "schwere": sev, "ausgenutzt": ist_aus, "oeffentlich": ist_oeff, "kev": cve in kev,
                               "patch": patch, "kb": kbs, "fix_text": fix_t, "fix_url": fix_u, "fixe": fixe, "familien": sorted(fam_c - {"Sonstige"})[:3]})
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
        "ohne_fix": len(ohne_fix), "ohne_fix_cves": sorted(ohne_fix)[:25],
        "im_kev": len(in_kev), "im_kev_cves": sorted(in_kev)[:25],
        "auswirkung": dict(sorted(auswirkung.items(), key=lambda kv: -kv[1])[:8]),
        "familien": dict(sorted(fam.items(), key=lambda kv: -kv[1])),
        "cve_liste": sorted(cves),
        "kandidaten": sorted(kandidaten, key=lambda k: (not k["kev"], not k["ausgenutzt"], not k["oeffentlich"], k["cve"]))[:40],
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
    n_aus = monat["ausgenutzt"]
    if n_aus > 0:
        stufe = "dringend"
        erst = "den Patch für die bereits ausgenutzte Lücke" if n_aus == 1 else "die Patches für die %d bereits ausgenutzten Lücken" % n_aus
        erst_en = "the patch for the already exploited flaw" if n_aus == 1 else "the patches for the %d already exploited flaws" % n_aus
        dann = "" if kritisch == 0 else (", danach den Patch für die als kritisch eingestufte Lücke" if kritisch == 1 else ", danach die Patches für die %d als kritisch eingestuften" % kritisch)
        dann_en = "" if kritisch == 0 else (", then the patch for the flaw rated critical" if kritisch == 1 else ", then the patches for the %d rated critical" % kritisch)
        empf = "Zuerst %s einspielen%s." % (erst, dann)
        empf_en = "Apply %s first%s." % (erst_en, dann_en)
    elif kritisch > 0:
        stufe = "zeitnah"
        was = "Den Patch für die als kritisch eingestufte Lücke" if kritisch == 1 else "Die Patches für die %d als kritisch eingestuften Lücken" % kritisch
        was_en = "The patch for the flaw rated critical" if kritisch == 1 else "The patches for the %d flaws rated critical" % kritisch
        empf = "%s zeitnah einspielen, den Rest im normalen Zyklus." % was
        empf_en = "%s should be applied promptly, the rest in the normal cycle." % was_en
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
    zu_holen = []
    for e in ziel:
        mid = e["ID"]
        vorher = monate.get(mid)
        if vorher and vorher.get("schema") != SCHEMA:
            vorher = None  # alte Zählweise: neu holen, keine Nachträge daraus ableiten
        if vorher and vorher.get("aktuell") == e.get("CurrentReleaseDate"):
            continue
        zu_holen.append((e, vorher))

    def hole(paar):
        e, _ = paar
        try:
            return hole_dok(e.get("CvrfUrl") or MS_DOK % e["ID"]), None
        except Exception as ex:  # fail-soft je Monat
            return None, "%s: %s" % (e["ID"], ex)

    with ThreadPoolExecutor(max_workers=4) as pool:  # die Monatsdokumente sind groß, vier gleichzeitig
        ergebnisse = list(pool.map(hole, zu_holen))
    for (e, vorher), (doc, fehl) in zip(zu_holen, ergebnisse):
        mid = e["ID"]
        if fehl:
            fehler.append(fehl)
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
    for m in reihe[:-2]:
        m.pop("kandidaten", None)
    if not reihe:
        raise QuellFehler("keine Monatsberichte")
    return {"meta": {"quelle": "Microsoft Security Response Center (CVRF 3.0)", "quelle_url": MS_QUELLE, "listen_url": MS_LISTE,
                     "abgerufen_am": jetzt.isoformat(timespec="seconds"),
                     "hinweis": "Zählung je CVE; Chromium-Lücken im Edge und Linux-Paketlücken von Azure Linux sind ausgenommen und getrennt ausgewiesen. Schweregrad, Ausnutzung und Bekanntheit stammen vom Hersteller.",
                     "fehler": fehler},
            "monate": {m["id"]: m for m in reihe}}


# ---------- Stufe 2 und 3: Distributionen und Hersteller ----------
UBUNTU_URL = "https://ubuntu.com/security/notices.json?limit=20&offset=%d"
UBUNTU_SEITEN = 20  # höchstens 400 Meldungen, genug für 30 Tage
REDHAT_URLS = ["https://access.redhat.com/hydra/rest/securitydata/csaf.json?after=%s", "https://access.redhat.com/hydra/rest/securitydata/cvrf.json?after=%s"]
REDHAT_CSV = ["https://security.access.redhat.com/data/csaf/v2/advisories/releases.csv", "https://security.access.redhat.com/data/csaf/v2/advisories/changes.csv"]  # releases: Veröffentlichungsdatum, changes: letzte Änderung
DEBIAN_URLS = ["https://www.debian.org/security/dsa-long.rdf", "https://www.debian.org/security/dsa.rdf", "https://www.debian.org/security/dsa-long.en.rdf", "https://www.debian.org/security/dsa.en.rdf"]
CISCO_URL = "https://sec.cloudapps.cisco.com/security/center/psirtrss20/CiscoSecurityAdvisory.xml"
HERSTELLER_DATEI = WURZEL / "data" / "patches" / "hersteller.json"
PRIO_DATEI = WURZEL / "data" / "patches" / "prioritaet.json"
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


def parse_redhat_csv(text):
    """changes.csv der Red-Hat-CSAF-Ablage: Zeilen wie "2026/rhsa-2026_1234.json","2026-11-10T12:00:00+00:00". Nur RHSA (Sicherheitsmeldungen), ohne Schweregrad."""
    out, gesehen = [], set()
    for zeile in text.splitlines():
        m = re.match(r'"?\d{4}/rhsa-(\d{4})_(\d+)\.json"?,"?([^",]+)"?', zeile, re.I)
        if not m:
            continue
        d = _datum(m.group(3))
        rid = "RHSA-%s:%s" % (m.group(1), m.group(2))
        if not d or rid in gesehen:
            continue
        gesehen.add(rid)
        out.append({"id": rid, "datum": d, "titel": rid, "link": "https://access.redhat.com/errata/RHSA-%s:%s" % (m.group(1), m.group(2)), "schwere": None, "cves": []})
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


def verdichte_quelle(items, heute, kev=()):
    """Zählung der Meldungen der letzten 7 und 30 Tage. Fehlt eine Angabe (z. B. Schweregrad), wird sie nicht geraten."""
    inner = [i for i in items if 0 <= (heute - i["datum"]).days < FENSTER]
    sieben = [i for i in inner if (heute - i["datum"]).days < 7]
    mit_sev = [i for i in inner if i["schwere"]]
    cves = set(c for i in inner for c in i["cves"])
    letzte = sorted(inner, key=lambda i: (i["datum"], i["id"]), reverse=True)[:10]
    kev = set(kev)
    mit_kev = [dict(id=i["id"], datum=i["datum"].isoformat(), titel=i["titel"][:140], link=i["link"], cves_kev=sorted(set(i["cves"]) & kev)[:6])
               for i in sorted(inner, key=lambda i: (i["datum"], i["id"]), reverse=True) if set(i["cves"]) & kev]
    return {"im_kev_30": len(mit_kev), "im_kev_meldungen": mit_kev[:8], "neu_7": len(sieben), "neu_30": len(inner), "kritisch_30": len([i for i in inner if i["schwere"] == "kritisch"]) if mit_sev else None,
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
        alle = []
        for seite in range(UBUNTU_SEITEN):
            teil = parse_ubuntu(json.loads(lade(UBUNTU_URL % (seite * 20)).decode("utf-8")))
            if not teil:
                break
            alle += teil
            if min(i["datum"] for i in teil) < heute - timedelta(days=FENSTER):
                break
        return list({i["id"]: i for i in alle}.values())  # doppelte Kennungen (Seitenüberlappung) nur einmal
    if qid == "redhat":
        ab = (heute - timedelta(days=FENSTER + 2)).isoformat()
        letzter = None
        for u in REDHAT_URLS:
            try:
                return parse_redhat(json.loads(lade(u % ab).decode("utf-8")))
            except Exception as e:
                letzter = e
        for u in REDHAT_CSV:
            try:
                r = parse_redhat_csv(lade(u).decode("utf-8", "replace"))
                if r:
                    return r
            except Exception as e:
                letzter = e
        raise QuellFehler("Red Hat: %s" % letzter)
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


def aktualisiere_hersteller(alt, heute, jetzt, lade=lade_roh, kev=()):
    alt = alt or {}
    quellen = dict(alt.get("quellen", {}))
    for q in QUELLEN:
        vorher = quellen.get(q["id"], {})
        try:
            items = hole_quelle(q["id"], heute, lade)
            if not items:
                raise QuellFehler("keine Einträge erkannt")
            z = verdichte_quelle(items, heute, kev)
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


# ---------- Diese Woche zuerst ----------
EPSS_HOCH = 0.10
ZEIT_MS_TAGE = 30
ZEIT_HERSTELLER_TAGE = 14


def hole_epss(cves, lade=lade_json):
    """EPSS-Wahrscheinlichkeiten (FIRST) für die Kandidaten; Fehler führen nur zu fehlenden Werten."""
    import fetch_ausblick
    out, liste = {}, sorted(set(cves))
    for i in range(0, len(liste), 100):
        try:
            out.update(fetch_ausblick.parse_epss(lade("%s?cve=%s" % (fetch_ausblick.EPSS_URL, ",".join(liste[i:i + 100])))))
        except Exception:
            continue
    return out


def priorisiere(ms_monate, hersteller, kev, epss, heute, maximum=8):
    """Rangliste nach festen Regeln: 1 im KEV (nachweislich angegriffen), 2 vom Hersteller als ausgenutzt gemeldet,
    3 EPSS ab 10 %, 4 vom Hersteller als kritisch eingestuft. Innerhalb einer Stufe nach EPSS, dann nach Kennung."""
    kev = set(kev)
    kand, gesehen, ohne = [], set(), []
    for m in ms_monate or []:
        try:
            tage = (heute - datetime.fromisoformat(str(m.get("erste_veroeffentlichung")).replace("Z", "+00:00")).date()).days
        except (TypeError, ValueError):
            continue
        if tage > ZEIT_MS_TAGE or tage < 0:
            continue
        for k in m.get("kandidaten", []):
            e = (epss.get(k["cve"]) or (None,))[0]
            if k["cve"] in kev or k.get("kev"):
                stufe, g, ge = 1, "Steht im CISA-KEV: Die Lücke wird nachweislich angegriffen.", "Listed in the CISA KEV: the flaw is proven to be attacked."
            elif k["ausgenutzt"]:
                stufe, g, ge = 2, "Microsoft meldet aktive Ausnutzung.", "Microsoft reports active exploitation."
            elif e is not None and e >= EPSS_HOCH:
                stufe, g, ge = 3, "Hohe Ausnutzungswahrscheinlichkeit (EPSS %d %%)." % round(e * 100), "High likelihood of exploitation (EPSS %d%%)." % round(e * 100)
            elif k["schwere"] == "Critical":
                stufe, g, ge = 4, "Von Microsoft als kritisch eingestuft.", "Rated critical by Microsoft."
            else:
                continue
            if k["cve"] in gesehen:
                continue
            gesehen.add(k["cve"])
            pst = k.get("patch", "unbekannt")
            kb = k.get("kb") or []
            if pst == "nein":
                ohne.append({"stufe": stufe, "quelle": "Microsoft", "titel": k["titel"], "cves": [k["cve"]], "grund": g, "grund_en": ge,
                             "betrifft": ", ".join(k["familien"]), "datum": str(m.get("erste_veroeffentlichung"))[:10],
                             "link": "https://msrc.microsoft.com/update-guide/vulnerability/" + k["cve"]})
                continue
            if pst == "ja":
                ft = k.get("fix_text") or ""
                pt = "Patch liegt vor" + (": KB" + ", KB".join(kb) if kb else (": " + ft if ft else ""))
                pt_en = "Patch available" + (": KB" + ", KB".join(kb) if kb else (": " + ft if ft else ""))
            else:
                pt, pt_en = "Patch-Stand bei Microsoft prüfen", "Check patch status with Microsoft"
            kand.append({"stufe": stufe, "epss": e, "quelle": "Microsoft", "titel": k["titel"], "cves": [k["cve"]], "grund": g, "grund_en": ge,
                         "patch": pst, "patch_text": pt, "patch_text_en": pt_en, "patch_link": k.get("fix_url") or "", "fixe": k.get("fixe") or [],
                         "betrifft": ", ".join(k["familien"]), "datum": str(m.get("erste_veroeffentlichung"))[:10],
                         "link": "https://msrc.microsoft.com/update-guide/vulnerability/" + k["cve"]})
    for q in (hersteller or {}).get("quellen", {}).values():
        if q.get("status") != "ok":
            continue
        for x in q.get("im_kev_meldungen", []):
            try:
                tage = (heute - datetime.fromisoformat(x["datum"]).date()).days
            except (TypeError, ValueError):
                continue
            neue = [c for c in x["cves_kev"] if c not in gesehen]
            if tage > ZEIT_HERSTELLER_TAGE or not neue:
                continue
            gesehen.update(neue)
            kand.append({"stufe": 1, "epss": None, "quelle": q["name"], "titel": x["titel"], "cves": neue,
                         "grund": "Schließt %d Lücke(n) aus dem CISA-KEV: nachweislich angegriffen." % len(neue),
                         "grund_en": "Closes %d flaw(s) from the CISA KEV: proven to be attacked." % len(neue),
                         **({"patch": "ja", "patch_text": "Das Update liegt vor (Meldung des Herstellers)", "patch_text_en": "The update is available (vendor advisory)"} if q.get("typ") != "hersteller" else
                            {"patch": "pruefen", "patch_text": "Fix-Stand im Advisory prüfen", "patch_text_en": "Check fix status in the advisory"}), "betrifft": q["name"], "datum": x["datum"], "link": x["link"]})
        for x in q.get("letzte", []):
            if x.get("schwere") != "kritisch" or q.get("typ") != "hersteller":
                continue
            try:
                tage = (heute - datetime.fromisoformat(x["datum"]).date()).days
            except (TypeError, ValueError):
                continue
            if tage <= ZEIT_HERSTELLER_TAGE and x["id"] not in gesehen:
                gesehen.add(x["id"])
                kand.append({"stufe": 4, "epss": None, "quelle": q["name"], "titel": x["titel"], "cves": [], "grund": "Vom Hersteller als kritisch eingestuft.",
                             "grund_en": "Rated critical by the vendor.", "patch": "pruefen", "patch_text": "Fix-Stand im Advisory prüfen", "patch_text_en": "Check fix status in the advisory", "betrifft": q["name"], "datum": x["datum"], "link": x["link"]})
    kand.sort(key=lambda k: (k["stufe"], -(k["epss"] or 0), k["cves"][0] if k["cves"] else k["titel"]))
    for i, k in enumerate(kand[:maximum], 1):
        k["rang"] = i
    return {"stand": heute.isoformat(), "regeln": "Nur Lücken, für die ein Patch vorliegt oder im Advisory zu prüfen ist. 1 im CISA-KEV, 2 vom Hersteller als ausgenutzt gemeldet, 3 EPSS ab 10 %, 4 vom Hersteller als kritisch eingestuft",
            "gesamt": len(kand), "liste": kand[:maximum], "ohne_patch": sorted(ohne, key=lambda k: (k["stufe"], k["cves"][0]))[:6]}


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
        hs = aktualisiere_hersteller(lese_datei(HERSTELLER_DATEI), jetzt.date(), jetzt, kev=kev_cves())
        HERSTELLER_DATEI.parent.mkdir(parents=True, exist_ok=True)
        HERSTELLER_DATEI.write_text(json.dumps(hs, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        for k, q in hs["quellen"].items():
            print("  %s: %s, neu 7 Tage %s, 30 Tage %s%s" % (k, q["status"], q.get("neu_7"), q.get("neu_30"), (" (%s)" % q["fehler"]) if q.get("fehler") else ""))
    except Exception as e:
        print("Hersteller-Patches: Fehler (%s)" % e)
    try:
        ms = lese_datei(MS_DATEI) or {}
        hs = lese_datei(HERSTELLER_DATEI) or {}
        kev = set(kev_cves())
        monate = list((ms.get("monate") or {}).values())
        kand = [k["cve"] for m in monate[-2:] for k in m.get("kandidaten", [])]
        epss = hole_epss(kand)
        pr = priorisiere(monate, hs, kev, epss, jetzt.date())
        PRIO_DATEI.write_text(json.dumps(pr, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        print("Priorität: %d Einträge insgesamt, %d angezeigt, EPSS für %d Kandidaten" % (pr["gesamt"], len(pr["liste"]), len(epss)))
    except Exception as e:
        print("Priorität: Fehler (%s)" % e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
