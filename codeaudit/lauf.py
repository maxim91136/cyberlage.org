"""Code-Audit: ein Lauf für dieses Repo. Startet die Prüfwerkzeuge, rechnet den Score (Regeln: codeaudit/regeln.json) und schreibt die Zusammenfassung.

Das Protokoll ist öffentlich: es zeigt nur Score und Zahlen. Einzelbefunde gehen nur privat per Telegram (TELEGRAM_AUDIT_CHAT_ID).
Fehlt ein Werkzeug oder liefert es nichts Lesbares, heißt die Prüfung "nicht geprüft" (senkt die Abdeckung, zählt weder gut noch schlecht).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "pipeline"))
from audit import auswertung  # noqa: E402
from codeaudit import pruefungen  # noqa: E402
import notify  # noqa: E402

REGELN = json.loads((Path(__file__).parent / "regeln.json").read_text(encoding="utf-8"))
ZEIT = 600


def starte(befehl, **kw):
    """Gibt (Rückgabewert, stdout) zurück; (None, "") wenn das Werkzeug fehlt oder zu lange braucht."""
    if shutil.which(befehl[0]) is None:
        return None, ""
    try:
        r = subprocess.run(befehl, cwd=WURZEL, capture_output=True, text=True, timeout=ZEIT, check=False, **kw)
    except (subprocess.TimeoutExpired, OSError):
        return None, ""
    return r.returncode, r.stdout


def json_aus(text):
    try:
        return json.loads(text)
    except ValueError:
        return None


def gitleaks(nur_arbeitsbaum):
    with tempfile.TemporaryDirectory() as d:
        bericht = Path(d) / "g.json"
        befehl = ["gitleaks", "detect", "--no-banner", "--redact", "--report-format", "json", "--report-path", str(bericht)] + (["--no-git"] if nur_arbeitsbaum else [])
        rc, _ = starte(befehl)
        if rc is None or rc not in (0, 1) or not bericht.exists():
            return None
        return json_aus(bericht.read_text(encoding="utf-8")) or []


def sammle():
    """Führt alle Werkzeuge aus und gibt die Liste der Einzelprüfungen zurück."""
    erg = []
    erg += pruefungen.gitleaks(gitleaks(True), gitleaks(False))
    wf = {p.name: p.read_text(encoding="utf-8") for p in sorted((WURZEL / ".github" / "workflows").glob("*.y*ml"))}
    erg += pruefungen.workflow_dateien(wf)
    offline = [] if (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")) else ["--offline"]  # ohne Token keine Abfragen an GitHub
    rc, aus = starte(["zizmor", "--format", "json"] + offline + [".github/workflows"])
    erg += pruefungen.zizmor(json_aus(aus) if rc is not None and aus.strip() else None)
    hat_abh = any((WURZEL / n).exists() for n in ("requirements.txt", "package.json", "package-lock.json", "pyproject.toml", "Pipfile.lock"))
    rc, aus = starte(["osv-scanner", "--format", "json", "-r", "."]) if hat_abh else (None, "")
    erg += pruefungen.osv(json_aus(aus) if aus.strip() else None, hat_abh)
    rc, aus = starte(["bandit", "-r", "pipeline", "audit", "codeaudit", "-f", "json", "-q"])
    bandit = json_aus(aus) if rc is not None else None
    rc, aus = starte(["ruff", "check", "--select", "F,B", "--output-format", "json", "pipeline", "audit", "codeaudit", "tests"])
    ruff = json_aus(aus) if rc is not None else None
    erg += pruefungen.python_werkzeuge(bandit, ruff)
    rc, aus = starte(["eslint", "-c", "codeaudit/eslint.config.js", "-f", "json", "site/app.js", "site/termine.js", "site/radar.js", "site/tabellen.js", "site/i18n.js", "site/matrix.js", "site/modus.js", "site/impressum.js", "site/hilfe.js"])
    erg += pruefungen.eslint(json_aus(aus) if rc is not None and aus.strip() else None)
    erg += tests()
    rc, aus = starte(["radon", "cc", "-j", "pipeline", "audit", "codeaudit"])
    erg += pruefungen.wartbarkeit(json_aus(aus) if rc is not None else None, pruefungen.zeilenzahlen(WURZEL))
    return erg


def tests():
    if shutil.which("coverage") is None:
        rc, _ = starte([sys.executable, "-m", "unittest", "discover", "-s", "tests"])
        return pruefungen.tests(None if rc is None else rc == 0, None)
    rc, _ = starte(["coverage", "run", "--source=pipeline,audit,codeaudit", "-m", "unittest", "discover", "-s", "tests"])
    if rc is None:
        return pruefungen.tests(None, None)
    with tempfile.TemporaryDirectory() as d:
        ziel = Path(d) / "c.json"
        starte(["coverage", "json", "-o", str(ziel)])
        z = json_aus(ziel.read_text(encoding="utf-8")) if ziel.exists() else None
    prozent = (z or {}).get("totals", {}).get("percent_covered")
    return pruefungen.tests(rc == 0, prozent)


def zusammenfassung(erg, jetzt=None):
    r = auswertung.rechne(erg, REGELN)
    jetzt = jetzt or datetime.now(timezone.utc)
    return {"repo": "maxim91136/cyberlage.org", "stand": jetzt.strftime("%Y-%m-%dT%H:%MZ"), "regeln": REGELN["version"], "score": r["score"], "teilwert": r["teilwert"],
            "stufe": r["stufe"], "abdeckung": r["abdeckung"], "gruppen": r["gruppen"],
            "befunde": sum(1 for x in erg if x[2] == "nicht_bestanden"), "hinweise": sum(1 for x in erg if x[2] == "hinweis"), "nicht_geprueft": len(r["nicht_geprueft"])}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--zusammenfassung")
    ap.add_argument("--details", action="store_true", help="Einzelbefunde auf der Ausgabe zeigen (nur lokal: Protokolle sind öffentlich)")
    ap.add_argument("--telegram", action="store_true")
    ap.add_argument("--immer", action="store_true")
    a = ap.parse_args(argv)
    alt = None
    if a.zusammenfassung and Path(a.zusammenfassung).exists():
        alt = json_aus(Path(a.zusammenfassung).read_text(encoding="utf-8"))
    erg = sammle()
    zus = zusammenfassung(erg)
    print(json.dumps(zus, ensure_ascii=False, indent=1))
    if a.details:
        for g, pid, e, text in erg:
            if e != "bestanden":
                print("%-14s %-22s %-16s %s" % (g, pid, e, text))
    if a.telegram:
        geaendert = not alt or any(alt.get(k) != zus.get(k) for k in ("score", "stufe", "befunde", "hinweise", "gruppen", "nicht_geprueft"))
        token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_AUDIT_CHAT_ID")
        if not (a.immer or geaendert):
            print("Keine Änderung gegenüber dem letzten Lauf, keine Telegram-Meldung")
        elif token and chat:
            offen = [x for x in erg if x[2] in ("nicht_bestanden", "hinweis", "nicht_geprueft")]
            zeilen = ["• %s: %s (%s)" % (notify.e(x[0]), notify.e(x[3]), notify.e(x[2])) for x in offen] or ["alles bestanden"]
            kopf = "<b>Code-Audit</b>: Score %s, %s (Lauf %s UTC)" % (zus["score"] if zus["score"] is not None else "ohne Score (Teilwert %s)" % zus["teilwert"], notify.e(zus["stufe"]), zus["stand"].replace("T", " ").rstrip("Z"))
            notify.sende((kopf + "\n" + "\n".join(zeilen))[:3800], token, chat)
        else:
            print("Telegram nicht eingerichtet (TELEGRAM_AUDIT_CHAT_ID fehlt), nichts gesendet")
    if a.zusammenfassung:
        Path(a.zusammenfassung).parent.mkdir(parents=True, exist_ok=True)
        Path(a.zusammenfassung).write_text(json.dumps(zus, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
