#!/usr/bin/env python3
"""Meldet Neues in einen Telegram-Kanal (nur Standardbibliothek).

Wenig Rauschen: sofort gesendet wird nur
  - ein Wechsel der Stufe
  - ein neuer KEV-Eintrag mit bekannter Ransomware-Nutzung
Alles andere Neue (KEV, kritische CERT-Bund-Warnungen, EU-KEV) wird gesammelt und einmal
täglich in einer Tageslage gesendet (ab 06:00 deutscher Zeit, also vor 07:00).

Zustand: data/notify_state.json. Beim ersten Lauf wird nur der Stand gemerkt, nichts gesendet.
Ohne TELEGRAM_BOT_TOKEN und TELEGRAM_CHAT_ID wird nur angezeigt, was gesendet würde, und der Zustand bleibt unverändert.
Schlägt das Senden fehl, bleibt der Zustand unverändert, der nächste Lauf versucht es erneut.
"""
import html
import json
import time
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
ZUSTAND = WURZEL / "data" / "notify_state.json"
SEITE = "https://cyberlage.org"
STUFENNAME = {"niedrig": "niedrig", "erhoeht": "erhöht", "hoch": "hoch", None: "keine Bewertung"}
TAGESLAGE_AB = 6  # volle Stunde, deutsche Zeit
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


def zeile_kev(x):
    return (f"• {e(x['hersteller'])} {e(x['produkt'])} – <a href=\"https://nvd.nist.gov/vuln/detail/{e(x['cve'])}\">{e(x['cve'])}</a>"
            + (" – <b>Ransomware bekannt</b>" if x["ransomware_bekannt"] else ""))


def abschnitt(zeilen, kopf):
    if not zeilen:
        return ""
    text = kopf + "\n" + "\n".join(zeilen[:MAX_ZEILEN])
    if len(zeilen) > MAX_ZEILEN:
        text += f"\n… und {len(zeilen) - MAX_ZEILEN} weitere, alle auf {SEITE}"
    return text


def ermittle(kev, bsi, eu, lage, zustand, jetzt):
    """Gibt (nachrichten, neuer_zustand) zurück. Reine Funktion, gut testbar.

    Sofort gesendet wird nur, was Alarm ist: Stufenwechsel und neue KEV-Einträge mit
    bekannter Ransomware-Nutzung. Alles andere Neue sammelt sich in "offen" und geht
    einmal täglich (ab 07:00 UTC) in einer Tageslage hinaus."""
    kev_ids = [x["cve"] for x in kev["eintraege"]]
    bsi_ids = [x["id"] for x in (bsi or {}).get("eintraege", [])]
    eu_ids = [x["id"] for x in (eu or {}).get("eintraege", [])]
    stufe = lage.get("stufe")
    neu_zustand = {"gesehen": {"kev": kev_ids, "bsi": bsi_ids, "eu": eu_ids}, "stufe": stufe,
                   "zusammenfassung": zustand.get("zusammenfassung") if zustand else None,
                   "offen": {"kev": [], "bsi": [], "eu": []}}
    nachrichten = []
    if zustand is None:  # erster Lauf: nur merken
        neu_zustand["zusammenfassung"] = jetzt.date().isoformat()
        return [], neu_zustand
    g = zustand.get("gesehen", {})
    offen = {k: list((zustand.get("offen") or {}).get(k, [])) for k in ("kev", "bsi", "eu")}

    neu_kev = [x for x in kev["eintraege"] if x["cve"] not in set(g.get("kev", []))]
    neu_kev.sort(key=lambda x: (x["hersteller"], x["cve"]))
    alarm = [x for x in neu_kev if x["ransomware_bekannt"]]
    offen["kev"] += [zeile_kev(x) for x in neu_kev if not x["ransomware_bekannt"]]
    if alarm:
        nachrichten.append(kuerzen([zeile_kev(x) for x in alarm],
                                   f"<b>Alarm: {len(alarm)} neu im CISA-KEV, in Ransomware-Kampagnen genutzt</b>",
                                   "Quelle: CISA KEV (CC0)"))

    alt_bsi = set(g.get("bsi", []))
    offen["bsi"] += [f"• <a href=\"{e(x['link'])}\">{e(x['titel'])}</a>" for x in (bsi or {}).get("eintraege", [])
                     if x["id"] not in alt_bsi and x["schwere"] == "kritisch"]
    alt_eu = set(g.get("eu", []))
    offen["eu"] += [f"• {e(', '.join(x['hersteller']) or '–')} – <a href=\"{e(x['link'])}\">{e((x['cve'] or [x['id']])[0])}</a>"
                    for x in (eu or {}).get("eintraege", []) if x["id"] not in alt_eu]

    if zustand.get("stufe") != stufe:
        nachrichten.append(f"<b>Stufe geändert:</b> {STUFENNAME.get(zustand.get('stufe'), e(zustand.get('stufe')))} → "
                           f"<b>{STUFENNAME.get(stufe, e(stufe))}</b>\n{e(lage.get('stufe_begruendung', ''))}\n{SEITE}")

    lokal = jetzt.astimezone(ZoneInfo("Europe/Berlin"))  # Tageslage ab 06:00 deutscher Zeit, damit sie vor 07:00 da ist
    heute = lokal.date().isoformat()
    if zustand.get("zusammenfassung") != heute and lokal.hour >= TAGESLAGE_AB:
        k = lage["kev"]
        zeilen = [f"Stufe: <b>{STUFENNAME.get(stufe, e(stufe))}</b>",
                  f"CISA-KEV: {k['neu_7_tage']} neu in 7 Tagen, {k['neu_30_tage']} in 30 Tagen"]
        if lage.get("cert_bund"):
            c = lage["cert_bund"]
            zeilen.append(f"CERT-Bund: {c['kritisch_7_tage']} kritisch, {c['hoch_7_tage']} hoch in 7 Tagen")
        if lage.get("eu_kev"):
            zeilen.append(f"EU-KEV: {lage['eu_kev']['neu_30_tage']} neu in 30 Tagen")
        teile = ["<b>Cyberlage, Tageslage</b>\n" + "\n".join(zeilen)]
        for liste, kopf in ((offen["kev"], f"<b>Neu im CISA-KEV ({len(offen['kev'])})</b>"),
                            (offen["bsi"], f"<b>CERT-Bund, neue kritische Warnungen ({len(offen['bsi'])})</b>"),
                            (offen["eu"], f"<b>Neu im EU-KEV ({len(offen['eu'])})</b>")):
            if liste:
                teile.append(abschnitt(liste, kopf))
        if not any(offen.values()):
            teile.append("Seit der letzten Tageslage nichts Neues.")
        text = "\n\n".join(teile) + f"\n\nQuellen: CISA KEV (CC0), CERT-Bund / BSI (Titel, Link), EUVD / ENISA\n{SEITE}"
        nachrichten.append(text[:MAX_ZEICHEN])
        neu_zustand["zusammenfassung"] = heute
        offen = {"kev": [], "bsi": [], "eu": []}
    neu_zustand["offen"] = offen
    return nachrichten, neu_zustand


def sende(text, token, chat):
    daten = urllib.parse.urlencode({"chat_id": chat, "text": text, "parse_mode": "HTML",
                                    "disable_web_page_preview": "true"}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=daten)
    letzter = None
    for versuch in range(2):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                if json.loads(r.read()).get("ok") is not True:
                    raise RuntimeError("Telegram hat die Nachricht nicht angenommen")
            return
        except urllib.error.HTTPError as ex:
            if ex.code == 429 and versuch < 1:
                try:
                    warte = int(json.loads(ex.read()).get("parameters", {}).get("retry_after", 30))
                except Exception:
                    warte = 30
                time.sleep(min(warte, 60) + 2 + versuch)
                continue
            raise RuntimeError(f"Telegram antwortet mit {ex.code}: {ex.read().decode(errors='replace')[:200]}")
        except (TimeoutError, OSError) as ex:
            letzter = ex
            time.sleep(5)
    raise RuntimeError(f"Telegram nicht erreichbar: {letzter}")


def diagnose():
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN", ""), os.environ.get("TELEGRAM_CHAT_ID", "")
    print(f"Token gesetzt: {bool(token)} (Länge {len(token)}), Bot-Nummer: {' '.join(token.split(':')[0])}, Chat-ID: {chat!r}")
    try:
        urllib.request.urlopen("https://api.telegram.org/bot0:fantasie/getMe", timeout=20)
    except urllib.error.HTTPError as ex:
        print("Fantasie-Token ->", ex.code, ex.read().decode(errors="replace")[:200])
    except Exception as ex:
        print("Fantasie-Token ->", type(ex).__name__, ex)
    try:
        print("Adresse:", urllib.request.urlopen("https://api.ipify.org", timeout=15).read().decode())
    except Exception as ex:
        print("Adresse: nicht ermittelbar", ex)
    for name, extra in (("getMe", {}), ("getChat", {"chat_id": chat}), ("getChatMember", {"chat_id": chat})):
        if name == "getChatMember":
            try:
                me = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getMe", timeout=20).read())
                extra["user_id"] = me["result"]["id"]
            except Exception:
                continue
        url = f"https://api.telegram.org/bot{token}/{name}?" + urllib.parse.urlencode(extra)
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                antwort = json.loads(r.read())
        except urllib.error.HTTPError as ex:
            antwort = ex.read().decode(errors="replace")[:300]
        except Exception as ex:
            antwort = f"{type(ex).__name__}: {ex}"
        print(name, "->", antwort)
    return 0


def test_senden():
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        print("FEHLER: TELEGRAM_BOT_TOKEN oder TELEGRAM_CHAT_ID fehlt", file=sys.stderr)
        return 1
    try:
        sende(f"<b>Cyberlage</b>: Testmeldung. Der Kanal ist verbunden, ab jetzt kommen neue Einträge und kritische Warnungen hierher.\n{SEITE}", token, chat)
    except Exception as ex:
        print(f"FEHLER beim Senden: {ex}", file=sys.stderr)
        return 1
    print("OK: Testmeldung gesendet")
    return 0


def main():
    if "--diagnose" in sys.argv[1:]:
        return diagnose()
    if "--test" in sys.argv[1:]:
        return test_senden()
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
