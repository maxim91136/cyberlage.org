"""Audit: Gruppe Auffindbarkeit (security.txt, robots.txt, Sitemap). Reine Funktionen ohne Netz.
Maßstäbe: RFC 9116 (security.txt), Sitemaps-Protokoll (sitemaps.org). Quellen und Stand in regeln.json."""
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

G = "auffindbar"


def _p(pid, ergebnis, text):
    return (G, pid, ergebnis, text)


def security_txt(status, inhalt_typ, text, jetzt):
    """RFC 9116: Contact und Expires sind Pflicht, Expires muss in der Zukunft liegen und soll höchstens ein Jahr entfernt sein."""
    if status != 200:
        return [_p("sectxt-da", "nicht_bestanden", "security.txt nicht erreichbar (Status %s)" % status)]
    erg = [_p("sectxt-da", "bestanden", "security.txt erreichbar"),
           _p("sectxt-typ", "bestanden" if (inhalt_typ or "").lower().startswith("text/plain") else "hinweis", "Inhaltstyp text/plain")]
    felder = {}
    for zeile in (text or "").splitlines():
        if ":" in zeile and not zeile.lstrip().startswith("#"):
            k, v = zeile.split(":", 1)
            felder.setdefault(k.strip().lower(), []).append(v.strip())
    erg.append(_p("sectxt-contact", "bestanden" if felder.get("contact") else "nicht_bestanden", "Contact vorhanden"))
    if not felder.get("expires"):
        erg.append(_p("sectxt-expires", "nicht_bestanden", "Expires fehlt"))
        return erg
    try:
        ablauf = datetime.fromisoformat(felder["expires"][0].replace("Z", "+00:00"))
        if ablauf.tzinfo is None:
            ablauf = ablauf.replace(tzinfo=timezone.utc)
    except ValueError:
        erg.append(_p("sectxt-expires", "nicht_bestanden", "Expires ist kein gültiges Datum"))
        return erg
    if ablauf <= jetzt:
        erg.append(_p("sectxt-expires", "nicht_bestanden", "security.txt ist abgelaufen"))
    elif ablauf - jetzt < timedelta(days=30):
        erg.append(_p("sectxt-expires", "hinweis", "security.txt läuft in weniger als 30 Tagen ab"))
    elif ablauf - jetzt > timedelta(days=366):
        erg.append(_p("sectxt-expires", "hinweis", "Expires liegt mehr als ein Jahr in der Zukunft (RFC 9116: soll unter einem Jahr liegen)"))
    else:
        erg.append(_p("sectxt-expires", "bestanden", "Expires gültig"))
    return erg


def robots(status, text):
    if status != 200:
        return [_p("robots-da", "hinweis", "robots.txt nicht erreichbar (Status %s)" % status)]
    erg = [_p("robots-da", "bestanden", "robots.txt erreichbar")]
    erg.append(_p("robots-sitemap", "bestanden" if re.search(r"(?im)^\s*sitemap\s*:\s*https://", text or "") else "hinweis", "robots.txt nennt die Sitemap"))
    return erg


def sitemap_adressen(xml_text, host):
    """Gibt (adressen, fehler) zurück. Nur Adressen des eigenen Hosts über https zählen."""
    if not xml_text or len(xml_text) > 5_000_000:
        return [], "leer oder zu groß"
    try:
        wurzel = ET.fromstring(xml_text)
    except ET.ParseError:
        return [], "kein gültiges XML"
    adr = [e.text.strip() for e in wurzel.iter() if e.tag.endswith("}loc") or e.tag == "loc"]
    return [a for a in adr if a.startswith("https://%s/" % host)], None


def sitemap(status, xml_text, host, antworten=None):
    """antworten: optional {adresse: statuscode} für eine Stichprobe der Sitemap-Adressen."""
    if status != 200:
        return [_p("sitemap-da", "hinweis", "Sitemap nicht erreichbar (Status %s)" % status)]
    adr, fehler = sitemap_adressen(xml_text, host)
    if fehler or not adr:
        return [_p("sitemap-da", "nicht_bestanden", "Sitemap ungültig: %s" % (fehler or "keine Adressen des eigenen Hosts"))]
    erg = [_p("sitemap-da", "bestanden", "Sitemap gültig, %d Adressen" % len(adr))]
    if antworten is not None:
        kaputt = [a for a, s in antworten.items() if s != 200]
        erg.append(_p("sitemap-antworten", "nicht_bestanden" if kaputt else "bestanden",
                      "%d von %d geprüften Sitemap-Adressen antworten nicht mit 200" % (len(kaputt), len(antworten)) if kaputt else "Stichprobe der Sitemap-Adressen antwortet mit 200"))
    return erg
