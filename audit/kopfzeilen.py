"""Audit: Prüfgruppe Kopfzeilen (HSTS, CSP, Inhalt, Datenschutz, Altlasten).

Reine Funktionen ohne Netz: Eingabe sind die Antwort-Kopfzeilen einer Seite (Namen klein geschrieben).
Jede Prüfung liefert (gruppe, id, ergebnis, text) mit ergebnis in "bestanden" / "hinweis" / "nicht_bestanden".
Maßstäbe und Quellen stehen in regeln.json."""
import re


def _p(gruppe, pid, ergebnis, text):
    return (gruppe, pid, ergebnis, text)


def hsts(h):
    wert = h.get("strict-transport-security")
    if not wert:
        return [_p("hsts", "hsts-da", "nicht_bestanden", "HSTS fehlt")]
    m = re.search(r"max-age=(\d+)", wert, re.I)
    alter = int(m.group(1)) if m else 0
    if alter >= 31536000:
        return [_p("hsts", "hsts-dauer", "bestanden", "max-age mindestens ein Jahr")]
    return [_p("hsts", "hsts-dauer", "hinweis", "max-age unter einem Jahr")]


def csp(h):
    wert = h.get("content-security-policy")
    if not wert:
        return [_p("csp", "csp-da", "nicht_bestanden", "Content-Security-Policy fehlt")]
    teile = {}
    for stueck in wert.split(";"):
        felder = stueck.split()
        if felder:
            teile[felder[0].lower()] = felder[1:]
    erg = []
    for d in ("default-src", "object-src", "base-uri", "frame-ancestors"):
        ok = d in teile or (d == "object-src" and "default-src" in teile)
        erg.append(_p("csp", "csp-" + d, "bestanden" if ok else "hinweis", d + (" gesetzt" if ok else " fehlt")))
    skript = teile.get("script-src") or teile.get("default-src") or []
    schlecht = [x for x in skript if x in ("'unsafe-inline'", "'unsafe-eval'", "*", "http:", "data:")]
    erg.append(_p("csp", "csp-skript", "nicht_bestanden" if schlecht else "bestanden",
                  "Skripte: unsicher erlaubt (%s)" % ", ".join(schlecht) if schlecht else "Skripte streng eingeschränkt"))
    return erg


def inhalt(h):
    erg = [_p("inhalt", "nosniff", "bestanden" if h.get("x-content-type-options", "").lower() == "nosniff" else "nicht_bestanden",
              "X-Content-Type-Options nosniff")]
    csp_wert = h.get("content-security-policy", "")
    rahmen = "frame-ancestors" in csp_wert or h.get("x-frame-options", "").upper() in ("DENY", "SAMEORIGIN")
    erg.append(_p("inhalt", "einbettung", "bestanden" if rahmen else "nicht_bestanden", "Schutz gegen Einbettung in fremde Seiten"))
    return erg


def datenschutz(h):
    return [
        _p("datenschutz", "referrer", "bestanden" if h.get("referrer-policy") else "hinweis", "Referrer-Policy"),
        _p("datenschutz", "permissions", "bestanden" if h.get("permissions-policy") else "hinweis", "Permissions-Policy"),
    ]


def altlasten(h):
    erg = []
    server = h.get("server", "")
    erg.append(_p("altlasten", "server-version", "hinweis" if re.search(r"\d", server) else "bestanden", "Server-Kopf ohne Versionsnummer"))
    erg.append(_p("altlasten", "powered-by", "hinweis" if h.get("x-powered-by") else "bestanden", "kein X-Powered-By"))
    return erg


def pruefe(h):
    h = {k.lower(): v for k, v in h.items()}
    erg = []
    for f in (hsts, csp, inhalt, datenschutz, altlasten):
        erg += f(h)
    return erg
