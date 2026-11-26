"""Audit: Gruppen TLS und Weiterleitung. Auswertungen sind reine Funktionen; der Abruf (ssl, socket) steht in abruf.py.
Maßstäbe: BSI TR-02102-2, Mozilla Server Side TLS, RFC 8996 (TLS 1.0 und 1.1 abgekündigt), Mozilla Observatory (Redirections)."""
from datetime import datetime, timezone
import ssl


def _p(gruppe, pid, ergebnis, text):
    return (gruppe, pid, ergebnis, text)


def zertifikat(cert, jetzt, verbindung_ok):
    """cert: Ergebnis von getpeercert() einer geprüften Verbindung. verbindung_ok: Kette und Hostname hat Python geprüft."""
    erg = [_p("tls", "zert-kette", "bestanden" if verbindung_ok else "nicht_bestanden", "Zertifikatskette und Hostname stimmen")]
    if not cert:
        return erg + [_p("tls", "zert-laufzeit", "nicht_bestanden", "kein Zertifikat gelesen")]
    ende = datetime.fromtimestamp(ssl.cert_time_to_seconds(cert["notAfter"]), timezone.utc)
    tage = (ende - jetzt).days
    if tage < 0:
        erg.append(_p("tls", "zert-laufzeit", "nicht_bestanden", "Zertifikat abgelaufen"))
    elif tage < 14:
        erg.append(_p("tls", "zert-laufzeit", "hinweis", "Zertifikat läuft in %d Tagen ab" % tage))
    else:
        erg.append(_p("tls", "zert-laufzeit", "bestanden", "Zertifikat noch %d Tage gültig" % tage))
    return erg


def versionen(ergebnis):
    """ergebnis: {"TLSv1": ..., "TLSv1.1": ..., "TLSv1.2": ..., "TLSv1.3": ...} mit "ja", "nein" oder "unklar" (lokal nicht prüfbar)."""
    erg = []
    wert = ergebnis.get("TLSv1.3")
    erg.append(_p("tls", "tls13", {"ja": "bestanden", "nein": "hinweis"}.get(wert, "nicht_geprueft"), "TLS 1.3 wird angeboten"))
    alt = [ergebnis.get("TLSv1"), ergebnis.get("TLSv1.1")]
    if "ja" in alt:
        erg.append(_p("tls", "tls-alt-aus", "nicht_bestanden", "TLS 1.0 oder 1.1 wird noch angeboten (RFC 8996)"))
    elif all(a == "nein" for a in alt):
        erg.append(_p("tls", "tls-alt-aus", "bestanden", "TLS 1.0 und 1.1 sind abgeschaltet"))
    else:
        erg.append(_p("tls", "tls-alt-aus", "nicht_geprueft", "TLS 1.0 und 1.1 lokal nicht prüfbar"))
    return erg


def weiterleitung(status, ort, host):
    """Antwort auf http://host/ ohne Weiterleitung zu folgen."""
    if status in (301, 302, 303, 307, 308) and (ort or "").startswith("https://%s" % host):
        return [_p("weiterleitung", "http-zu-https", "bestanden" if status in (301, 308) else "hinweis",
                   "http leitet auf https um" if status in (301, 308) else "http leitet nur vorläufig (Status %s) auf https um" % status)]
    if status is None:
        return [_p("weiterleitung", "http-zu-https", "nicht_geprueft", "Port 80 nicht erreichbar")]
    return [_p("weiterleitung", "http-zu-https", "nicht_bestanden", "http leitet nicht auf https des gleichen Hosts um (Status %s)" % status)]


def http_zu_https_domain(status, ort, host, ziel):
    """Profil Weiterleitung: http://host/ darf auf https://host/ oder gleich auf https://ziel/ führen (beides ist verschlüsselt)."""
    if status is None:
        return [_p("weiterleitung", "http-zu-https", "nicht_geprueft", "Port 80 nicht erreichbar")]
    gut = status in (301, 308)
    if status in (301, 302, 303, 307, 308) and any((ort or "").startswith(v) for v in ("https://%s/" % host, "https://%s" % ziel)):
        return [_p("weiterleitung", "http-zu-https", "bestanden" if gut else "hinweis",
                   "http leitet verschlüsselt um" if gut else "http leitet nur vorläufig (Status %s) um" % status)]
    return [_p("weiterleitung", "http-zu-https", "nicht_bestanden", "http leitet nicht auf https um (Status %s)" % status)]


def ziel_weiterleitung(status, ort, ziel, pfad):
    """Profil Weiterleitung: https://host<pfad> muss dauerhaft (301 oder 308) auf https://ziel<pfad> führen, Pfad und Abfrage bleiben."""
    if status is None:
        return [_p("weiterleitung", "ziel", "nicht_geprueft", "Weiterleitungsdomain nicht erreichbar")]
    erwartet = "https://%s%s" % (ziel, pfad)
    if status not in (301, 302, 303, 307, 308):
        return [_p("weiterleitung", "ziel", "nicht_bestanden", "keine Weiterleitung (Status %s)" % status)]
    if not (ort or "").startswith("https://%s/" % ziel):
        return [_p("weiterleitung", "ziel", "nicht_bestanden", "Weiterleitung führt nicht auf https://%s" % ziel)]
    if ort != erwartet:
        return [_p("weiterleitung", "ziel", "hinweis", "Weiterleitung führt auf das richtige Ziel, aber Pfad oder Abfrage gehen verloren")]
    if status not in (301, 308):
        return [_p("weiterleitung", "ziel", "hinweis", "Weiterleitung nur vorläufig (Status %s), dauerhaft wäre 301" % status)]
    return [_p("weiterleitung", "ziel", "bestanden", "dauerhafte Weiterleitung auf das Ziel, Pfad und Abfrage bleiben")]
