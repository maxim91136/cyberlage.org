"""Code-Audit: macht aus Werkzeugausgaben Einzelprüfungen (gruppe, id, ergebnis, text). Reine Rechnung, kein Netz, keine Werkzeugaufrufe.

Ergebnis ist "bestanden", "hinweis", "nicht_bestanden" oder "nicht_geprueft" (Werkzeug fehlte oder lieferte nichts Lesbares).
Schwellen stehen hier und in codeaudit/REGELN.md; sie sind seit Version 1.0 festgeschrieben und ändern sich nur mit einem Eintrag in RULES.md.
"""
import re
from pathlib import Path

SCHWELLE_ABDECKUNG = (80, 60)      # Zeilenabdeckung in %: ab 80 bestanden, ab 60 Hinweis
KOMPLEXITAET_MAX = 30              # radon: eine Funktion darüber gilt als nicht bestanden
DATEI_ZEILEN_MAX = 1500            # Quelldatei länger: Hinweis
SHA = re.compile(r"@[0-9a-f]{40}(\s|$)")


def _p(gruppe, pid, erg, text):
    return (gruppe, pid, erg, text)


def _zahl_pruefung(gruppe, pid, funde, ok_text, schlecht_text, hinweis_ab=None):
    """funde None = nicht geprüft; 0 = bestanden; sonst nicht bestanden (oder Hinweis bis hinweis_ab)."""
    if funde is None:
        return _p(gruppe, pid, "nicht_geprueft", "Werkzeug lieferte kein lesbares Ergebnis")
    if funde == 0:
        return _p(gruppe, pid, "bestanden", ok_text)
    if hinweis_ab is not None and funde <= hinweis_ab:
        return _p(gruppe, pid, "hinweis", "%d: %s" % (funde, schlecht_text))
    return _p(gruppe, pid, "nicht_bestanden", "%d: %s" % (funde, schlecht_text))


def gitleaks(funde_arbeitsbaum, funde_verlauf):
    """Je Liste der Funde (JSON-Liste von gitleaks) oder None."""
    n = lambda x: None if x is None else len(x)  # noqa: E731
    return [_zahl_pruefung("geheimnisse", "gitleaks_arbeitsbaum", n(funde_arbeitsbaum), "keine Geheimnisse im Arbeitsbaum", "Funde im Arbeitsbaum"),
            _zahl_pruefung("geheimnisse", "gitleaks_verlauf", n(funde_verlauf), "keine Geheimnisse im Verlauf", "Funde im Verlauf")]


def workflow_dateien(dateien):
    """dateien: {Name: Text} der Workflows. Eigene Prüfung ohne Werkzeug: Actions auf Commit gepinnt, Berechtigungen gesetzt."""
    if not dateien:
        return [_p("workflows", "actions_gepinnt", "nicht_geprueft", "keine Workflow-Dateien gefunden"),
                _p("workflows", "berechtigungen", "nicht_geprueft", "keine Workflow-Dateien gefunden")]
    ungepinnt, ohne_rechte = 0, 0
    for text in dateien.values():
        for z in text.splitlines():
            m = re.match(r"\s*-?\s*uses:\s*(\S+)", z)
            if m and not m.group(1).startswith("./") and not SHA.search(z + " "):
                ungepinnt += 1
        if not re.search(r"^permissions:", text, re.M):
            ohne_rechte += 1
    return [_zahl_pruefung("workflows", "actions_gepinnt", ungepinnt, "alle Actions auf einen Commit gepinnt", "Actions nicht auf einen Commit gepinnt"),
            _zahl_pruefung("workflows", "berechtigungen", ohne_rechte, "jeder Workflow setzt seine Berechtigungen", "Workflows ohne eigene Berechtigungen")]


def zizmor(funde):
    """funde: JSON-Liste von zizmor oder None. Hohe Funde nicht bestanden, mittlere Hinweis."""
    if funde is None:
        return [_p("workflows", "zizmor", "nicht_geprueft", "zizmor lieferte kein lesbares Ergebnis")]
    def stufe(f):
        return str((f.get("determinations") or {}).get("severity", f.get("severity", ""))).lower()
    hoch = sum(1 for f in funde if stufe(f) in ("high", "critical"))
    mittel = sum(1 for f in funde if stufe(f) == "medium")
    if hoch:
        return [_p("workflows", "zizmor", "nicht_bestanden", "%d hohe Funde" % hoch)]
    if mittel:
        return [_p("workflows", "zizmor", "hinweis", "%d mittlere Funde" % mittel)]
    return [_p("workflows", "zizmor", "bestanden", "keine hohen oder mittleren Funde")]


def osv(ausgabe, hat_abhaengigkeiten):
    """ausgabe: JSON von osv-scanner oder None. Ohne Abhängigkeitsdateien gilt die Gruppe als bestanden (Standardbibliothek)."""
    if not hat_abhaengigkeiten:
        return [_p("abhaengigkeiten", "osv", "bestanden", "keine Abhängigkeiten außerhalb der Standardbibliothek")]
    if ausgabe is None:
        return [_p("abhaengigkeiten", "osv", "nicht_geprueft", "osv-scanner lieferte kein lesbares Ergebnis")]
    n = sum(len(p.get("vulnerabilities") or []) for r in ausgabe.get("results") or [] for p in r.get("packages") or [])
    return [_zahl_pruefung("abhaengigkeiten", "osv", n, "keine bekannten Schwachstellen", "bekannte Schwachstellen in Abhängigkeiten")]


def python_werkzeuge(bandit, ruff):
    """bandit: JSON-Objekt oder None; ruff: JSON-Liste oder None."""
    out = []
    if bandit is None:
        out.append(_p("python", "bandit", "nicht_geprueft", "bandit lieferte kein lesbares Ergebnis"))
    else:
        erg = bandit.get("results") or []
        hoch = sum(1 for r in erg if str(r.get("issue_severity")).upper() == "HIGH")
        mittel = sum(1 for r in erg if str(r.get("issue_severity")).upper() == "MEDIUM")
        out.append(_p("python", "bandit", "nicht_bestanden", "%d hohe Funde" % hoch) if hoch else
                   _p("python", "bandit", "hinweis", "%d mittlere Funde" % mittel) if mittel else
                   _p("python", "bandit", "bestanden", "keine hohen oder mittleren Funde"))
    out.append(_zahl_pruefung("python", "ruff", None if ruff is None else len(ruff), "keine Fehlermuster (Regeln F, B)", "Fehlermuster (Regeln F, B)"))
    return out


def eslint(ausgabe):
    """ausgabe: JSON-Liste von eslint oder None. Zählt nur Fehler (Schweregrad 2)."""
    if ausgabe is None:
        return [_p("javascript", "eslint", "nicht_geprueft", "eslint lieferte kein lesbares Ergebnis")]
    n = sum(1 for d in ausgabe for m in d.get("messages") or [] if m.get("severity") == 2)
    return [_zahl_pruefung("javascript", "eslint", n, "keine Fehler (no-undef, no-eval, no-implied-eval, no-new-func)", "Fehler")]


def tests(ok, abdeckung):
    """ok: True/False/None (Tests grün), abdeckung: Prozent oder None."""
    out = [_p("tests", "tests_gruen", "nicht_geprueft", "Tests nicht gelaufen") if ok is None else
           _p("tests", "tests_gruen", "bestanden" if ok else "nicht_bestanden", "alle Tests grün" if ok else "Tests schlagen fehl")]
    if abdeckung is None:
        out.append(_p("tests", "abdeckung", "nicht_geprueft", "Abdeckung nicht gemessen"))
    else:
        erg = "bestanden" if abdeckung >= SCHWELLE_ABDECKUNG[0] else "hinweis" if abdeckung >= SCHWELLE_ABDECKUNG[1] else "nicht_bestanden"
        out.append(_p("tests", "abdeckung", erg, "Zeilenabdeckung %.0f %%" % abdeckung))
    return out


def wartbarkeit(radon, zeilen):
    """radon: JSON {Datei: [Funktionen mit "complexity"]} oder None; zeilen: {Datei: Zeilenzahl}."""
    out = []
    if radon is None:
        out.append(_p("wartbarkeit", "komplexitaet", "nicht_geprueft", "radon lieferte kein lesbares Ergebnis"))
    else:
        zu_komplex = sum(1 for fs in radon.values() if isinstance(fs, list) for f in fs if f.get("complexity", 0) > KOMPLEXITAET_MAX)
        out.append(_zahl_pruefung("wartbarkeit", "komplexitaet", zu_komplex, "keine Funktion über Komplexität %d" % KOMPLEXITAET_MAX, "Funktionen über Komplexität %d" % KOMPLEXITAET_MAX))
    lang = sum(1 for n in zeilen.values() if n > DATEI_ZEILEN_MAX)
    out.append(_zahl_pruefung("wartbarkeit", "dateilaenge", lang, "keine Datei über %d Zeilen" % DATEI_ZEILEN_MAX, "Dateien über %d Zeilen" % DATEI_ZEILEN_MAX, hinweis_ab=99))
    return out


def zeilenzahlen(wurzel, muster=("pipeline/*.py", "audit/*.py", "site/*.js", "site/*.css", "tests/*.py")):
    wurzel = Path(wurzel)
    res = {}
    for m in muster:
        for p in sorted(wurzel.glob(m)):
            res[str(p.relative_to(wurzel))] = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
    return res
