"""Prüfkalender: Welche von Hand gepflegten Angaben sind fällig, welche Quellen sind nicht mehr erreichbar?

Liest data/radar/gruende.csv und einschaetzungen.csv, prüft die Links (erreichbare höchstens einmal je 24 Stunden, fehlgeschlagene bei jedem Lauf erneut)
und schreibt data/radar/pruefung.json. Dazu einen Text für ein GitHub-Issue (Pfad aus PRUEFUNG_MD,
nur wenn etwas offen ist). Prüft nur Erreichbarkeit und Frist, nicht den Inhalt: Ob eine Zahl noch
stimmt, entscheidet ein Mensch; das Datum geprueft_am wird nur von Hand gesetzt.
Fristen (Tage seit geprueft_am): jährliche Angaben 330, Gründe 90, Schwellen des Dreier-Pegels 183 (halbjährlich), Stufen und Modell des Dreier-Pegels 90 (vorläufig, danach aus eigener Verteilung ableiten).
"""
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
RADAR = WURZEL / "data" / "radar"
UA = "cyberlage.org (privates Projekt von Dreier Labs, https://cyberlage.org)"
FRIST = {"jaehrlich": 330, "grund": 90, "schwellen": 183, "radar_stufen": 90}
NEU_NACH_STUNDEN = 24


def lese(pfad):
    try:
        with open(pfad, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    except OSError:
        return []


def eintraege():
    """Alle Angaben mit Link und Prüfdatum."""
    out = []
    for r in lese(RADAR / "gruende.csv"):
        out.append({"id": r["id"], "bereich": "grund", "name": r.get("quelle") or r["id"], "link": r.get("link", ""), "geprueft_am": r.get("geprueft_am", "")})
    for r in lese(RADAR / "einschaetzungen.csv"):
        out.append({"id": r["name"], "bereich": "jaehrlich" if r.get("art") == "jaehrlich" else "grund", "name": r["name"],
                    "link": r.get("link", ""), "geprueft_am": r.get("geprueft_am", "")})
    try:
        regeln = json.loads((WURZEL / "config" / "regeln.json").read_text(encoding="utf-8"))
        out.append({"id": "schwellen", "bereich": "schwellen", "name": "Schwellen des Dreier-Pegels",
                    "link": "https://cyberlage.org/RULES.md", "geprueft_am": regeln.get("geprueft_am", "")})
    except (OSError, ValueError):
        pass
    try:
        stufen = json.loads((WURZEL / "config" / "radar_stufen.json").read_text(encoding="utf-8"))
        out.append({"id": "radar_stufen", "bereich": "radar_stufen", "name": "Stufen des Dreier-Pegels (%s)" % stufen.get("status", "").replace("vorlaeufig", "vorläufig"),
                    "link": "https://cyberlage.org/RULES.md", "geprueft_am": stufen.get("geprueft_am", "")})
    except (OSError, ValueError):
        pass
    try:
        mod = json.loads((WURZEL / "config" / "modell.json").read_text(encoding="utf-8"))
        out.append({"id": "modell", "bereich": "radar_stufen", "name": "Modell des Dreier-Pegels %s: Bausteine, Gruppen, Schwellen (%s)" % (mod.get("version", ""), mod.get("status", "").replace("vorlaeufig", "vorläufig")),
                    "link": "https://cyberlage.org/RULES.md", "geprueft_am": mod.get("geprueft_am", "")})
    except (OSError, ValueError):
        pass
    return out


def erreichbar(url):
    """(ok, status). Nur https; ein einzelner Fehler ist kein Beweis (siehe tot)."""
    if not url.startswith("https://"):
        return False, "kein https-Link"
    for methode in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=methode, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as a:
                return True, a.status
        except urllib.error.HTTPError as e:
            if methode == "GET":
                # 401/403/429: Der Server antwortet, lässt aber keine Automaten lesen. Das zählt als erreichbar.
                return e.code < 400 or e.code in (401, 403, 429), e.code
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if methode == "GET":
                return False, type(e).__name__
    return False, "unbekannt"


def tot(e, jetzt):
    """Ein Link gilt als tot, wenn jeder Versuch seit mindestens 24 Stunden fehlschlägt (und es mehrere waren)."""
    if int(e.get("fehler_in_folge", 0)) < 2 or not e.get("erster_fehler_um"):
        return False
    try:
        return jetzt - datetime.fromisoformat(e["erster_fehler_um"]) >= timedelta(hours=NEU_NACH_STUNDEN)
    except ValueError:
        return False


def pruefen(heute, alt, pruefer=erreichbar, jetzt=None):
    jetzt = jetzt or datetime.now(timezone.utc)
    alt_nach_id = {e["id"]: e for e in (alt or {}).get("eintraege", [])}
    liste = eintraege()

    def eins(e):
        frueher = alt_nach_id.get(e["id"], {})
        seit = frueher.get("link_geprueft_um")
        if seit and frueher.get("link") == e["link"] and frueher.get("erreichbar"):
            try:
                if jetzt - datetime.fromisoformat(seit) < timedelta(hours=NEU_NACH_STUNDEN):
                    return dict(frueher, **{k: e[k] for k in ("bereich", "name", "geprueft_am")})
            except ValueError:
                pass
        ok, status = pruefer(e["link"])
        fehler = 0 if ok else int(frueher.get("fehler_in_folge", 0)) + 1
        erster = None if ok else (frueher.get("erster_fehler_um") if frueher.get("fehler_in_folge") else None) or jetzt.isoformat(timespec="seconds")
        return dict(e, erreichbar=ok, status=status, fehler_in_folge=fehler, erster_fehler_um=erster, link_geprueft_um=jetzt.isoformat(timespec="seconds"))

    with ThreadPoolExecutor(max_workers=4) as pool:
        ergebnis = list(pool.map(eins, liste))
    offen = []
    for e in ergebnis:
        try:
            faellig_am = date.fromisoformat(e["geprueft_am"][:10]) + timedelta(days=FRIST[e["bereich"]])
        except ValueError:
            faellig_am = heute
        e["faellig_am"] = faellig_am.isoformat()
        e["faellig"] = heute >= faellig_am
        e["link_tot"] = tot(e, jetzt)
        if e["faellig"]:
            offen.append("%s: Prüfung fällig seit %s (zuletzt geprüft %s)" % (e["name"], e["faellig_am"], e["geprueft_am"] or "nie"))
        if e["link_tot"]:
            offen.append("%s: Link nicht erreichbar (%s), %s" % (e["name"], e["status"], e["link"]))
    return {"stand": heute.isoformat(), "fristen_tage": FRIST, "eintraege": ergebnis, "offen": offen}


def main():
    heute = datetime.now(timezone.utc).date()
    pfad = RADAR / "pruefung.json"
    try:
        alt = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        alt = None
    res = pruefen(heute, alt)
    pfad.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md = Path(os.environ.get("PRUEFUNG_MD", "/tmp/cyberlage_pruefung.md"))
    if res["offen"]:
        md.write_text("Von Hand gepflegte Angaben brauchen eine Prüfung:\n\n" + "\n".join("- " + o for o in res["offen"]) +
                      "\n\nNach der Prüfung `geprueft_am` in `data/radar/gruende.csv` bzw. `einschaetzungen.csv` auf das heutige Datum setzen "
                      "(und den Wert, falls er sich geändert hat). Dieses Issue schließt sich beim nächsten Lauf selbst.\n", encoding="utf-8")
    elif md.exists():
        md.unlink()
    print("Prüfkalender: %d Einträge, %d offen" % (len(res["eintraege"]), len(res["offen"])))
    for o in res["offen"]:
        print("  -", o)
    return 0


if __name__ == "__main__":
    sys.exit(main())
