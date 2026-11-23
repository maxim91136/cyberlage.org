#!/usr/bin/env python3
"""Meldet Neues in einen Telegram-Kanal (nur Standardbibliothek).

Gemeldet wird nur, was sich seit dem letzten Lauf geändert hat:
  - neue Einträge im CISA-KEV (Ransomware-Treffer hervorgehoben)
  - neue KRITISCHE CERT-Bund-Warnungen (Titel, Schweregrad, Link)
  - neue EU-KEV-Einträge
  - Wechsel der Stufe
  - einmal täglich eine kurze Zusammenfassung (ab 07:00 UTC)

Zustand: data/notify_state.json. Beim ersten Lauf wird nur der Stand gemerkt, nichts gesendet.
Ohne TELEGRAM_BOT_TOKEN und TELEGRAM_CHAT_ID wird nur angezeigt, was gesendet würde, und der Zustand bleibt unverändert.
Schlägt das Senden fehl, bleibt der Zustand unverändert, der nächste Lauf versucht es erneut.
"""
import html
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
ZUSTAND = WURZEL / "data" / "notify_state.json"
SEITE = "https://cyberlage.org"
STUFENNAME = {"niedrig": "niedrig", "erhoeht": "erhöht", "hoch": "hoch", None: "keine Bewertung"}
MAX_ZEILEN = 10
MAX_ZEICHEN = 3800  # Telegram erlaubt 4096


def e(t):
    return html.escape(str(t), quote=False)


def lese(pfad, vorgabe):
    try:
        return json.loads(Path(pfad).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return vorgabe


def kuerzen(zeilen, kopf, fuss=""):
    sichtbar = zeilen[:MAX_ZEILEN]
    text = kopf + "\n" + "\n".join(sichtbar)
    if len(zeilen) > MAX_ZEILEN:
        text += f"\n… und {len(zeilen) - MAX_ZEILEN} weitere, alle auf {SEITE}"
    if fuss:
        text += "\n\n" + fuss
    return text[:MAX_ZEICHEN]


def ermittle(kev, bsi, eu, lage, zustand, jetzt):
    """Gibt (nachrichten, neuer_zustand) zurück. Reine Funktion, gut testbar."""
    kev_ids = [x["cve"] for x in kev["eintraege"]]
    bsi_ids = [x["id"] for x in (bsi or {}).get("eintraege", [])]
    eu_ids = [x["id"] for x in (eu or {}).get("eintraege", [])]
    stufe = lage.get("stufe")
    neu_zustand = {"gesehen": {"kev": kev_ids, "bsi": bsi_ids, "eu": eu_ids}, "stufe": stufe,
                   "zusammenfassung": zustand.get("zusammenfassung") if zustand else None}
    nachrichten = []
    if zustand is None:  # erster Lauf: nur merken
        neu_zustand["zusammenfassung"] = jetzt.date().isoformat()
        return [], neu_zustand
    g = zustand.get("gesehen", {})

    neu_kev = [x for x in kev["eintraege"] if x["cve"] not in set(g.get("kev", []))]
    if neu_kev:
        neu_kev.sort(key=lambda x: (not x["ransomware_bekannt"], x["hersteller"], x["cve"]))
        zeilen = [f"• {e(x['hersteller'])} {e(x['produkt'])} – <a href=\"https://nvd.nist.gov/vuln/detail/{e(x['cve'])}\">{e(x['cve'])}</a>"
                  + (" – <b>Ransomware bekannt</b>" if x["ransomware_bekannt"] else "") for x in neu_kev]
        nachrichten.append(kuerzen(zeilen, f"<b>Neu im CISA-KEV ({len(neu_kev)})</b>\nSchwachstellen, die nachweislich ausgenutzt werden:",
                                   "Quelle: CISA KEV (CC0)"))

    alt_bsi = set(g.get("bsi", []))
    neu_bsi = [x for x in (bsi or {}).get("eintraege", []) if x["id"] not in alt_bsi and x["schwere"] == "kritisch"]
    if neu_bsi:
        zeilen = [f"• <a href=\"{e(x['link'])}\">{e(x['titel'])}</a>" for x in neu_bsi]
        nachrichten.append(kuerzen(zeilen, f"<b>CERT-Bund: {len(neu_bsi)} neue kritische Warnung(en)</b>",
                                   "Quelle: CERT-Bund / BSI (Titel und Link)"))

    alt_eu = set(g.get("eu", []))
    neu_eu = [x for x in (eu or {}).get("eintraege", []) if x["id"] not in alt_eu]
    if neu_eu:
        zeilen = [f"• {e(', '.join(x['hersteller']) or '–')} – <a href=\"{e(x['link'])}\">{e((x['cve'] or [x['id']])[0])}</a>" for x in neu_eu]
        nachrichten.append(kuerzen(zeilen, f"<b>Neu im EU-KEV ({len(neu_eu)})</b>", "Quelle: EUVD / ENISA"))

    if zustand.get("stufe") != stufe:
        nachrichten.append(f"<b>Stufe geändert:</b> {STUFENNAME.get(zustand.get('stufe'), e(zustand.get('stufe')))} → "
                           f"<b>{STUFENNAME.get(stufe, e(stufe))}</b>\n{e(lage.get('stufe_begruendung', ''))}\n{SEITE}")

    heute = jetzt.date().isoformat()
    if zustand.get("zusammenfassung") != heute and jetzt.hour >= 7:
        k = lage["kev"]
        zeilen = [f"Stufe: <b>{STUFENNAME.get(stufe, e(stufe))}</b>",
                  f"CISA-KEV: {k['neu_7_tage']} neu in 7 Tagen, {k['neu_30_tage']} in 30 Tagen"]
        if lage.get("cert_bund"):
            c = lage["cert_bund"]
            zeilen.append(f"CERT-Bund: {c['kritisch_7_tage']} kritisch, {c['hoch_7_tage']} hoch in 7 Tagen")
        if lage.get("eu_kev"):
            zeilen.append(f"EU-KEV: {lage['eu_kev']['neu_30_tage']} neu in 30 Tagen")
        nachrichten.append("<b>Cyberlage, Tageslage</b>\n" + "\n".join(zeilen) + f"\n{SEITE}")
        neu_zustand["zusammenfassung"] = heute
    return nachrichten, neu_zustand


def sende(text, token, chat):
    daten = urllib.parse.urlencode({"chat_id": chat, "text": text, "parse_mode": "HTML",
                                    "disable_web_page_preview": "true"}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=daten)
    with urllib.request.urlopen(req, timeout=30) as r:
        if json.loads(r.read()).get("ok") is not True:
            raise RuntimeError("Telegram hat die Nachricht nicht angenommen")


def main():
    jetzt = datetime.now(timezone.utc)
    kev = lese(WURZEL / "data" / "kev" / "kev.json", None)
    lage = lese(WURZEL / "site" / "data" / "lage.json", None)
    if not kev or not lage:
        print("FEHLER: Daten fehlen", file=sys.stderr)
        return 1
    bsi = lese(WURZEL / "data" / "bsi" / "warnungen.json", None)
    eu = lese(WURZEL / "data" / "eu" / "kev.json", None)
    zustand = lese(ZUSTAND, None)
    nachrichten, neu = ermittle(kev, bsi, eu, lage, zustand, jetzt)
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        print(f"Trockenlauf (kein Token/Kanal): {len(nachrichten)} Nachricht(en) würden gesendet.")
        for n in nachrichten:
            print("---\n" + n)
        return 0
    try:
        for n in nachrichten:
            sende(n, token, chat)
    except Exception as ex:
        print(f"FEHLER beim Senden: {ex}", file=sys.stderr)
        return 1  # Zustand bleibt, nächster Lauf versucht es erneut
    ZUSTAND.parent.mkdir(parents=True, exist_ok=True)
    ZUSTAND.write_text(json.dumps(neu, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"OK: {len(nachrichten)} Nachricht(en) gesendet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
