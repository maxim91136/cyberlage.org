# Cyberlage

Lagebild: die Cyberlage, abgeleitet aus ausgenutzten Schwachstellen und offenen Quellen. Für alle, die verteidigen.

**Ein Projekt von [Dreier Labs](https://dreierlabs.com).** Ein privates Projekt, keine amtliche Stelle und keine Zusammenarbeit mit einer Behörde.

Status: im Aufbau, noch nicht veröffentlicht.

## Grundregeln

- **Quelle, Stand und Lizenz an jedem Wert.** Nichts erscheint ohne Beleg.
- **Regeln statt Bauchgefühl.** Die Bewertung folgt den offenen Regeln in [RULES.md](RULES.md).
- **Keine einzelnen Betroffenen.** Es wird nur gezeigt, was die Quellen veröffentlichen.
- **Nicht belegt heißt „keine Daten“.** Es wird nichts geschätzt.
- **Lizenzen zuerst.** Eine Quelle wird nur genutzt, wenn ihre Bedingungen es erlauben. Sonst wird nur verlinkt. Siehe [data/sources.csv](data/sources.csv).

## Aufbau

| Pfad | Zweck |
| --- | --- |
| `data/sources.csv` | Quellenregister mit Lizenz und Status (grün, gelb, rot, offen) |
| `data/kev/kev.json` | Kompakte, geprüfte Fassung des CISA-KEV-Katalogs mit Abrufzeit |
| `data/enisa.csv` | ENISA-Kennzahlen von Hand erfasst, mit Seitenangabe und Prüfstatus |
| `config/regeln.json` | Schwellen der Bewertung, mit Status (Entwurf oder freigegeben) |
| `pipeline/fetch_kev.py` | Holt und prüft den KEV-Katalog |
| `pipeline/score.py` | Wertet nach den Regeln aus und schreibt `site/data/lage.json` |
| `tests/` | Tests für Abruf und Auswertung |
| `site/` | Platzhalterseite und Ausgabedaten |
| `.github/workflows/daten.yml` | Aktualisierung, vorerst nur von Hand startbar |

## Lokal ausführen

Nur Python 3, keine weiteren Pakete:

```
python3 -m unittest discover -s tests
python3 pipeline/fetch_kev.py
python3 pipeline/score.py
```

## Hinweis

Die Seite zeigt Zahlen aus öffentlichen Quellen. Sie ersetzt keine Warnung des BSI oder eines CERT. Die Verlinkung auf amtliche Quellen ist kein Hinweis auf eine Zusammenarbeit.
