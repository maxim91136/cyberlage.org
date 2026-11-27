"""Code-Audit auf der Audit-Seite: Abschnitt „Code-Audit“ mit dem Dreier-Code-Siegel (eigenes Siegel, eigener Score).

Die Zahlen kommen aus data/codeaudit/cyberlage.org.json (geschrieben von codeaudit/lauf.py), Gruppen, Gewichte, Werkzeuge und Stufen aus
codeaudit/regeln.json; hier wird nichts gerechnet. Einzelbefunde stehen nie auf der Seite, nur Zahlen. Fertiges HTML ohne Skript."""
import json
from pathlib import Path

import auditseiten as au
import berichtseiten as bs

REPO = "maxim91136/cyberlage.org"
SVG_NAME = "code-cyberlage.org"
LAUF_UHR = "05:40"  # UTC, steht so in .github/workflows/codeaudit.yml (ein Test prüft das)
KOPF = {"kopf": "DREIER-CODE-SIEGEL", "name": "Dreier-Code-Siegel"}
REPO_CODE = "https://github.com/maxim91136/cyberlage.org/tree/main/codeaudit"
GRUPPE_EN = {"geheimnisse": "Secrets in code and history", "workflows": "Workflows and permissions", "abhaengigkeiten": "Dependencies",
                     "python": "Python: security and error patterns", "javascript": "JavaScript: security and error patterns", "tests": "Tests", "wartbarkeit": "Maintainability"}

T = {
    "de": {"h": "Code-Audit", "profil": "Code-Repository",
           "intro": "Ein zweites, eigenes Siegel prüft den Code dieses Projekts: Geheimnisse, Workflows, Abhängigkeiten, Python, JavaScript, Tests und Wartbarkeit. "
                    "Es ist vom Web-Audit unabhängig und kann anders ausfallen. Regeln, Gewichte und Werkzeuge liegen offen. Hier gilt: hoch ist gut.",
           "entwurf": "Die Regeln sind noch ein Entwurf (Version %s). Schwellen und Prüfpunkte können sich bis Version 1.0 ändern; dann werden sie festgeschrieben.",
           "leg": "Wert je Gruppe: Anteil der bestandenen Prüfungen.",
           "h_wann": "Wann und wie geprüft wird",
           "wann": ("Der Lauf startet jeden Tag automatisch gegen %s Uhr UTC in GitHub Actions. Zusätzlich kann er von Hand gestartet werden.",
                    "Die Werkzeuge laufen in festen Versionen. Fehlt eines oder liefert es nichts Lesbares, heißt die Prüfung „nicht geprüft“: Sie zählt weder gut noch schlecht und senkt die Abdeckung.",
                    "Ohne %d %% geprüftes Gewicht gibt es keinen Score, nur einen Teilwert.",
                    "Schon ein einziger Fund bei Geheimnissen oder Workflows begrenzt den Score auf höchstens %d.",
                    "Einzelbefunde gehen nur privat an den Betreiber, öffentlich stehen nur Score und Zahlen. Gemeldet wird nur bei einer Änderung gegenüber dem letzten Lauf.",
                    "Der neue Lauf ersetzt den vorigen. Nach mehr als %d Tagen ohne neuen Lauf wird das Siegel grau."),
           "h_werk": "Gruppen, Werkzeuge und Gewichte", "gruppe": "Gruppe", "gewicht": "Gewicht", "werkzeug": "Werkzeug", "quelle": "Maßstab",
           "h_nicht": "Was das Dreier-Code-Siegel ist und was nicht",
           "nicht": ("Das Siegel zeigt den Stand eines automatischen Laufs: Score, Abzeichen (Gold, Silber, Bronze), Projekt und Datum.",
                     "Es ist kein Sicherheitsgutachten, keine Prüfung durch Menschen und kein Penetrationstest. Ein bestandener Prüfpunkt heißt nur, dass das jeweilige Werkzeug nichts gefunden hat.",
                     "Wartbarkeit ist ein Richtwert (Komplexität, Dateilänge) und hat nur geringes Gewicht."),
           "quell": "Quelltext des Code-Audits", "kurz": "Code-Audit"},
    "en": {"h": "Code audit", "profil": "Code repository",
           "intro": "A second, separate seal checks the code of this project: secrets, workflows, dependencies, Python, JavaScript, tests and maintainability. "
                    "It is independent of the web audit and can turn out differently. Rules, weights and tools are open. Here, high is good.",
           "entwurf": "The rules are still a draft (version %s). Thresholds and checks may change until version 1.0, when they are fixed.",
           "leg": "Value per group: share of checks passed.",
           "h_wann": "When and how it runs",
           "wann": ("The run starts automatically every day at about %s UTC in GitHub Actions. It can also be started by hand.",
                    "The tools run in fixed versions. If one is missing or returns nothing readable, the check is “not checked”: it counts neither good nor bad and lowers the coverage.",
                    "Without %d %% of the weight checked there is no score, only a partial value.",
                    "A single finding in secrets or workflows caps the score at %d.",
                    "Individual findings go only to the operator, privately; the public sees only score and numbers. A message is sent only when the result changes compared with the last run.",
                    "The new run replaces the previous one. After more than %d days without a new run the seal turns grey."),
           "h_werk": "Groups, tools and weights", "gruppe": "Group", "gewicht": "Weight", "werkzeug": "Tool", "quelle": "Standard",
           "h_nicht": "What the Dreier Code Seal is and is not",
           "nicht": ("The seal shows the state of an automatic run: score, badge (gold, silver, bronze), project and date.",
                     "It is not a security assessment, not a review by people and not a penetration test. A passed check only means the tool found nothing.",
                     "Maintainability is a rule of thumb (complexity, file length) and carries little weight."),
           "quell": "Source code of the code audit", "kurz": "Code audit"},
}


def lies(wurzel):
    """Liest die Zusammenfassung des letzten Laufs; ohne Datei oder Inhalt None."""
    try:
        d = json.loads((Path(wurzel) / "data" / "codeaudit" / "cyberlage.org.json").read_text(encoding="utf-8"))
        d["stand"], d["gruppen"], d["abdeckung"], d["befunde"], d["hinweise"]
        return d
    except (OSError, ValueError, KeyError):
        return None


def regeln_lesen(wurzel):
    return json.loads((Path(wurzel) / "codeaudit" / "regeln.json").read_text(encoding="utf-8"))


def siegel(d, jetzt, regeln):
    return au.siegel("cyberlage.org", d, jetzt, regeln, **KOPF)


def kopf(sp, d, regeln, jetzt):
    """Obere Hälfte: Überschrift, Einleitung, Karte mit Siegel und Gruppen."""
    t = T[sp]
    z = ['<h2 class="mono" id="code-audit">%s</h2>\n<p class="dim au-intro">%s</p>\n' % (au._e(t["h"]), au._e(t["intro"]))]
    if "entwurf" in regeln["version"]:
        z.append('<p class="dim au-hint">%s</p>\n' % au._e(t["entwurf"] % regeln["version"].split("-")[0]))
    z.append(au._karte("cyberlage.org", d, regeln, sp, jetzt, None, svg=SVG_NAME, profil_text=t["profil"], kopf=KOPF, gruppe_en=GRUPPE_EN))
    z.append('<p class="dim au-leg">%s</p>\n' % au._e(t["leg"]))
    return "".join(z)


def details(sp, regeln):
    """Untere Hälfte: Ablauf, Gruppen mit Werkzeugen und Gewichten, Grenzen des Siegels."""
    t = T[sp]
    wann = (t["wann"][0] % LAUF_UHR, t["wann"][1], t["wann"][2] % round(100 * regeln["mindest_abdeckung"]), t["wann"][3] % regeln["deckel"]["max_score"], t["wann"][4], t["wann"][5] % au.SIEGEL_TAGE)
    z = ['<h3 class="mono">%s</h3>\n<ul class="au-ul">%s</ul>\n' % (au._e(t["h_wann"]), "".join("<li>%s</li>" % au._e(x) for x in wann))]
    zeilen = "".join('<tr><td>%s</td><td class="mono">%d</td><td>%s</td><td class="dim">%s</td></tr>' % (au._e(GRUPPE_EN[g] if sp == "en" else i["name"]), i["gewicht"], au._e(i["werkzeug"]), au._e(i["quelle"])) for g, i in regeln["gruppen"].items())
    z.append('<h3 class="mono">%s</h3>\n<div class="br-tab"><table><thead><tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr></thead><tbody>%s</tbody></table></div>\n' % (
        au._e(t["h_werk"]), au._e(t["gruppe"]), au._e(t["gewicht"]), au._e(t["werkzeug"]), au._e(t["quelle"]), zeilen))
    z.append('<h3 class="mono">%s</h3>\n<ul class="au-ul">%s</ul>\n' % (au._e(t["h_nicht"]), "".join("<li>%s</li>" % au._e(x) for x in t["nicht"])))
    z.append('<p class="bs-nav mono"><a href="%s">%s</a></p>\n' % (REPO_CODE, au._e(t["quell"])))
    return "".join(z)


def fuss_text(d, regeln, sp, jetzt):
    """Kurztext neben dem Siegel im Fuß der Startseite; bei zu altem Lauf nur das Datum."""
    datum = bs._datum(d["stand"][:10], sp)
    k = T[sp]["kurz"] + ": "
    if au.farbe(d, jetzt, regeln) == au.FARBE["grau"]:
        return (k + "letzter Lauf %s" if sp == "de" else k + "last run %s") % datum
    abz = au.abzeichen(d["score"], regeln)
    return k + "%d / 100%s · %s · %s %s" % (d["score"], " · " + au.ABZ_NAME[sp][abz] if abz else "", datum, "Regeln" if sp == "de" else "Rules", au._version(regeln["version"], sp))
