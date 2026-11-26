#!/usr/bin/env python3
"""Audit-Lauf für eine eigene Domain: Abruf, Prüfungen, Score.

    python audit/lauf.py cyberlage.org --zusammenfassung data/audit/cyberlage.org.json [--details]

Die Zusammenfassung enthält nur Score, Stufe, Abdeckung, Gruppenwerte und Zahl der Befunde. Einzelbefunde (Texte der
nicht bestandenen Prüfungen) stehen nur auf der Ausgabe, wenn --details gesetzt ist: das Repo und die Protokolle sind öffentlich.
Läuft nicht in der Entwicklungsumgebung (kein Netz), sondern in GitHub Actions."""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
import notify  # noqa: E402
import abruf  # noqa: E402
import dns  # noqa: E402
import fremd  # noqa: E402
import auswertung  # noqa: E402
import dateien  # noqa: E402
import kopfzeilen  # noqa: E402
import tls  # noqa: E402

ERLAUBT = {"cyberlage.org", "cyberlage.com", "dreierlabs.com"}  # nur eigene Domains
OHNE_MAIL = {"cyberlage.org", "cyberlage.com"}  # Domains, die keine Mail verschicken: SPF "-all" ist das Ziel
WEITERLEITUNG = {"cyberlage.com": "cyberlage.org"}  # Profil "Weiterleitung": Domain -> Ziel. Alle anderen haben das Profil "Seite".
TESTPFAD = "/hinweise?pruefung=weiterleitung"  # Pfad und Abfrage müssen auf dem Ziel ankommen
NICHT_ZUTREFFEND = {  # Gruppen, die bei einer reinen Weiterleitung keinen Inhalt zum Prüfen haben
    "csp": "keine Seite, nur Weiterleitung", "fremd": "keine Seite, nur Weiterleitung", "inhalt": "keine Seite, nur Weiterleitung",
    "datenschutz": "keine Seite, nur Weiterleitung", "altlasten": "keine Seite, nur Weiterleitung", "auffindbar": "security.txt, robots und Sitemap liegen auf dem Ziel"}


def pruefe(host, jetzt=None):
    jetzt = jetzt or datetime.now(timezone.utc)
    erg = []
    status, kopf, startseite, _ort = abruf.hole(host, "/")
    if status is None:  # kein Netz oder Domain nicht erreichbar: kein Ergebnis, statt lauter falscher Befunde
        raise ConnectionError("%s ist nicht erreichbar, kein Ergebnis" % host)
    erg += fremd.fremde_inhalte(startseite, host, kopf) + fremd.cookies(kopf)
    erg += kopfzeilen.pruefe(kopf) if status == 200 else [("hsts", "start-da", "nicht_bestanden", "Startseite antwortet mit Status %s" % status)]
    s, _k, _t, ort = abruf.hole(host, "/", https=False)
    erg += tls.weiterleitung(s, ort, host)
    cert, ok = abruf.zertifikat(host)
    erg += tls.zertifikat(cert, jetzt, ok) + tls.versionen(abruf.versionen(host))
    caa, _ = abruf.doh(host, "CAA")
    ds, _ = abruf.doh(host, "DS")
    _a, ad = abruf.doh(host, "A")
    erg += dns.caa(caa) + dns.dnssec(ds, ad)
    spf, _ = abruf.doh(host, "TXT")
    dm, _ = abruf.doh("_dmarc." + host, "TXT")
    erg += (dns.spf(spf, host in OHNE_MAIL) if spf is not None else [("mail", "spf", "nicht_geprueft", "TXT-Abfrage fehlgeschlagen")]) \
        + (dns.dmarc(dm) if dm is not None else [("mail", "dmarc", "nicht_geprueft", "DMARC-Abfrage fehlgeschlagen")])
    s, k, t, _o = abruf.hole(host, "/.well-known/security.txt")
    erg += dateien.security_txt(s, k.get("content-type"), t, jetzt)
    s, _k, t, _o = abruf.hole(host, "/robots.txt")
    erg += dateien.robots(s, t)
    s, _k, t, _o = abruf.hole(host, "/sitemap.xml")
    adr, _f = dateien.sitemap_adressen(t, host) if s == 200 else ([], None)
    antworten = {a: abruf.hole(host, a.split(host, 1)[1])[0] for a in adr[:10]} if adr else None  # Stichprobe, höflich
    erg += dateien.sitemap(s, t, host, antworten)
    return erg


def pruefe_weiterleitung(host, ziel, jetzt=None):
    """Profil Weiterleitung: nur die Prüfungen, die für eine Domain gelten, die nur auf eine andere führt."""
    jetzt = jetzt or datetime.now(timezone.utc)
    erg = []
    status, kopf, _t, ort = abruf.hole(host, TESTPFAD)
    if status is None:
        raise ConnectionError("%s ist nicht erreichbar, kein Ergebnis" % host)
    erg += tls.ziel_weiterleitung(status, ort, ziel, TESTPFAD)
    erg += kopfzeilen.hsts({k.lower(): v for k, v in kopf.items()})
    erg += fremd.cookies(kopf)
    s, _k, _t, o = abruf.hole("www." + host, TESTPFAD)  # die www-Adresse führt auf dasselbe Ziel
    erg += [(g, "www-" + i, e, t + " (www)") for g, i, e, t in tls.ziel_weiterleitung(s, o, ziel, TESTPFAD)]
    zs, _k, _t, _o = abruf.hole(ziel, TESTPFAD.split("?")[0])  # das Ziel antwortet (wird als eigene Domain voll geprüft)
    erg.append(("weiterleitung", "ziel-antwortet", "bestanden" if zs == 200 else "nicht_bestanden" if zs else "nicht_geprueft",
                "das Ziel antwortet mit 200" if zs == 200 else "das Ziel antwortet nicht mit 200 (Status %s)" % zs))
    s, _k, _t, ort = abruf.hole(host, "/", https=False)
    erg += tls.http_zu_https_domain(s, ort, host, ziel)
    cert, ok = abruf.zertifikat(host)
    erg += tls.zertifikat(cert, jetzt, ok) + tls.versionen(abruf.versionen(host))
    caa, _ = abruf.doh(host, "CAA")
    ds, _ = abruf.doh(host, "DS")
    _a, ad = abruf.doh(host, "A")
    erg += dns.caa(caa) + dns.dnssec(ds, ad)
    spf, _ = abruf.doh(host, "TXT")
    dm, _ = abruf.doh("_dmarc." + host, "TXT")
    mx, _ = abruf.doh(host, "MX")
    erg += (dns.spf(spf, True) if spf is not None else [("mail", "spf", "nicht_geprueft", "TXT-Abfrage fehlgeschlagen")]) \
        + (dns.dmarc(dm) if dm is not None else [("mail", "dmarc", "nicht_geprueft", "DMARC-Abfrage fehlgeschlagen")]) + dns.null_mx(mx)
    erg += [(g, "nz-" + g, "nicht_zutreffend", t) for g, t in NICHT_ZUTREFFEND.items()]
    return erg


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("domain")
    ap.add_argument("--zusammenfassung")
    ap.add_argument("--details", action="store_true", help="Einzelbefunde auf der Ausgabe zeigen (nur lokal sinnvoll: Protokolle sind öffentlich)")
    ap.add_argument("--telegram", action="store_true", help="Einzelbefunde privat per Telegram senden (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)")
    a = ap.parse_args(argv)
    if a.domain not in ERLAUBT:
        print("Nur eigene Domains werden geprüft:", ", ".join(sorted(ERLAUBT)))
        return 2
    try:
        erg = pruefe_weiterleitung(a.domain, WEITERLEITUNG[a.domain]) if a.domain in WEITERLEITUNG else pruefe(a.domain)
    except ConnectionError as ex:
        print("FEHLER:", ex)
        return 3
    r = auswertung.rechne(erg)
    zus = {"domain": a.domain, "stand": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "profil": "weiterleitung" if a.domain in WEITERLEITUNG else "seite", "regeln": auswertung.REGELN["version"],
           "score": r["score"], "teilwert": r["teilwert"], "stufe": r["stufe"], "abdeckung": r["abdeckung"], "gruppen": r["gruppen"],
           "befunde": sum(1 for x in erg if x[2] == "nicht_bestanden"), "hinweise": sum(1 for x in erg if x[2] == "hinweis"),
           "nicht_geprueft": len(r["nicht_geprueft"])}
    print(json.dumps(zus, ensure_ascii=False, indent=1))
    if a.details:
        for g, pid, e, text in erg:
            if e != "bestanden":
                print("%-14s %-16s %-16s %s" % (g, pid, e, text))
    if a.telegram:
        offen = [x for x in erg if x[2] != "bestanden"]
        zeilen = ["• %s: %s (%s)" % (notify.e(x[0]), notify.e(x[3]), notify.e(x[2])) for x in offen] or ["alles bestanden"]
        kopf = "<b>Audit %s</b> (Lauf %s UTC): Score %s, %s" % (notify.e(a.domain), zus["stand"].replace("T", " ").rstrip("Z"), zus["score"] if zus["score"] is not None else "ohne Score (Teilwert %s)" % zus["teilwert"], notify.e(zus["stufe"]))
        token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
        if token and chat:
            notify.sende((kopf + "\n" + "\n".join(zeilen))[:3800], token, chat)
        else:
            print("Telegram nicht eingerichtet, nichts gesendet")
    if a.zusammenfassung:
        Path(a.zusammenfassung).parent.mkdir(parents=True, exist_ok=True)
        Path(a.zusammenfassung).write_text(json.dumps(zus, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
