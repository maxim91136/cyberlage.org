# Code-Audit mit Dreier-Code-Siegel: Entwurf der Regeln

Version **0.1 (Entwurf)**, Stand 27.11.2026. Maßgeblich ist `codeaudit/regeln.json`. Noch nichts gemessen, nichts auf der Seite.

## Grundsätze

- **Eigenes Siegel**, eigener Score, getrennt vom Dreier-Siegel des Web-Audits. Beide dürfen sich unterscheiden.
- **Hoch = gut**, Wertung wie beim Web-Audit: bestanden 1, Hinweis 0,5, nicht bestanden 0. Stufen und Abzeichen wie dort (95, 80, 60), damit die Siegel gleich zu lesen sind.
- **Kein Score ohne Abdeckung:** unter 90 % geprüftem Gewicht nur ein Teilwert. Was ein Werkzeug nicht prüfen konnte, heißt „nicht geprüft“ und zählt weder gut noch schlecht.
- **Deckel 59** bei Mängeln in „Geheimnisse“ oder „Workflows“: ein Fund dort wiegt mehr als jede Menge guter Punkte anderswo.
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
