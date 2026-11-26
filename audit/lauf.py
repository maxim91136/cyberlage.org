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
import auswertung  # noqa: E402
import dateien  # noqa: E402
import kopfzeilen  # noqa: E402
import tls  # noqa: E402

ERLAUBT = {"cyberlage.org", "dreierlabs.com"}  # nur eigene Domains


def pruefe(host, jetzt=None):
    jetzt = jetzt or datetime.now(timezone.utc)
    erg = []
    status, kopf, _text, _ort = abruf.hole(host, "/")
    if status is None:  # kein Netz oder Domain nicht erreichbar: kein Ergebnis, statt lauter falscher Befunde
        raise ConnectionError("%s ist nicht erreichbar, kein Ergebnis" % host)
    erg += kopfzeilen.pruefe(kopf) if status == 200 else [("hsts", "start-da", "nicht_bestanden", "Startseite antwortet mit Status %s" % status)]
    s, _k, _t, ort = abruf.hole(host, "/", https=False)
    erg += tls.weiterleitung(s, ort, host)
    cert, ok = abruf.zertifikat(host)
    erg += tls.zertifikat(cert, jetzt, ok) + tls.versionen(abruf.versionen(host))
    s, k, t, _o = abruf.hole(host, "/.well-known/security.txt")
    erg += dateien.security_txt(s, k.get("content-type"), t, jetzt)
    s, _k, t, _o = abruf.hole(host, "/robots.txt")
    erg += dateien.robots(s, t)
    s, _k, t, _o = abruf.hole(host, "/sitemap.xml")
    adr, _f = dateien.sitemap_adressen(t, host) if s == 200 else ([], None)
    antworten = {a: abruf.hole(host, a.split(host, 1)[1])[0] for a in adr[:10]} if adr else None  # Stichprobe, höflich
    erg += dateien.sitemap(s, t, host, antworten)
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
        erg = pruefe(a.domain)
    except ConnectionError as ex:
        print("FEHLER:", ex)
        return 3
    r = auswertung.rechne(erg)
    zus = {"domain": a.domain, "stand": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "regeln": auswertung.REGELN["version"],
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
