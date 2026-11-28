# Code-Audit mit Dreier-Code-Siegel: Regeln

Version **1.0**, Stand 27.11.2026. Maßgeblich ist `codeaudit/regeln.json`. Seit Version 1.0 sind Gruppen, Gewichte, Schwellen und Prüfpunkte festgeschrieben; Änderungen gibt es nur mit neuer Version und Eintrag in `RULES.md`.

## Grundsätze

- **Eigenes Siegel**, eigener Score, getrennt vom Dreier-Web-Siegel. Beide dürfen sich unterscheiden.
- **Hoch = gut**, Wertung wie beim Web-Audit: bestanden 1, Hinweis 0,5, nicht bestanden 0. Stufen und Abzeichen wie dort (95, 80, 60), damit die Siegel gleich zu lesen sind.
- **Kein Score ohne Abdeckung:** unter 90 % geprüftem Gewicht nur ein Teilwert. Was ein Werkzeug nicht prüfen konnte, heißt „nicht geprüft“ und zählt weder gut noch schlecht.
- **Deckel 59** schon bei **einer** nicht bestandenen Prüfung in „Geheimnisse“ oder „Workflows“ (beim Web-Audit erst, wenn die ganze Gruppe 0 erreicht): ein Fund dort wiegt mehr als jede Menge guter Punkte anderswo.
- **Nur eigene Repos.** Nur das Ergebnis mit Datum wird öffentlich: Score, Stufe, Gruppenwerte, Zahl der Befunde. **Einzelbefunde gehen privat an Steve**, nie ins öffentliche Protokoll.
- **Keine Schätzung:** jeder Wert stammt aus einem Werkzeuglauf mit Version und Datum, der Bericht nennt beides.
- **Wartbarkeit** ist ein Richtwert (Komplexität, Dateilänge), kein Sicherheitsbefund, und hat nur 10 % Gewicht.

## Gruppen und Gewichte (Summe 100)

| Gruppe | Gewicht | Werkzeug |
| --- | --- | --- |
| Geheimnisse im Code und Verlauf | 20 | gitleaks |
| Workflows und Berechtigungen | 18 | zizmor, OpenSSF Scorecard |
| Abhängigkeiten | 12 | osv-scanner |
| Python | 14 | bandit, ruff (F, B, S) |
| JavaScript | 12 | eslint |
| Tests | 14 | unittest, coverage.py |
| Wartbarkeit | 10 | radon |

## Offene Entscheidungen vor Version 1.0

1. Einzelne Prüfpunkte je Gruppe und ihre Schwellen (z. B. Abdeckung ab wie viel Prozent „bestanden“).
2. Stand und Lizenz jedes Werkzeugs vor der Einführung prüfen (aus dem Kopf eingetragen, nicht belegt).
3. Die Werkzeuge laufen nur in GitHub Actions (hier nicht installierbar); Ablauf und Sperrgruppe wie `audit.yml`.
4. Dieselbe Regelpflege wie beim Web-Audit (Vorlauf 60 Tage, Version in Stein) erst ab 1.0.

## Prüfpunkte und Schwellen (Version 1.0, 27.11.2026)

- **Geheimnisse:** gitleaks im Arbeitsbaum und im Verlauf; jeder Fund = nicht bestanden.
- **Workflows:** eigene Prüfung ohne Werkzeug (jede Action auf einen 40-stelligen Commit gepinnt, jeder Workflow setzt `permissions:`), dazu zizmor (hohe Funde nicht bestanden, mittlere Hinweis).
- **Abhängigkeiten:** osv-scanner, aber nur wenn es Abhängigkeitsdateien gibt; ohne sie bestanden (nur Standardbibliothek).
- **Python:** bandit (hohe Funde nicht bestanden, mittlere Hinweis), ruff Regeln F und B (jeder Fund nicht bestanden).
- **JavaScript:** eslint mit `no-undef`, `no-eval`, `no-implied-eval`, `no-new-func`; nur Fehler zählen (`codeaudit/eslint.config.js`). ESLint wird mit `npm ci` aus `werkzeuge/package-lock.json` installiert (feste Version samt aller Abhängigkeiten, mit Prüfsummen, ohne Installationsskripte).
- **Tests:** alle grün (bestanden/nicht bestanden); Zeilenabdeckung ab 80 % bestanden, ab 60 % Hinweis, darunter nicht bestanden.
- **Wartbarkeit:** keine Funktion über zyklomatische Komplexität 30 (radon); Dateien über 1500 Zeilen = Hinweis.
- Alles, was ein Werkzeug nicht liefert, ist „nicht geprüft“. Die Schwellen sind mit Version 1.0 festgeschrieben.
- **Begründete Ausnahmen** stehen im Code, nicht in der Wertung: `.github/zizmor.yml` (artipacked, weil die Workflows selbst ins Repo schreiben und keine Artefakte hochladen; ein Test hält das fest) und `# nosec`-Kommentare mit Grund an den Abrufen (Adresse vorher über `pipeline/sicher.py` auf https geprüft). Jede neue Ausnahme braucht eine Begründung an der Stelle.
