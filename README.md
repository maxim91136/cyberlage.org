# Cyberlage

Ein Seismograph für die Cyberlage: Lagebild aus ausgenutzten Schwachstellen und offenen Quellen, mit dem eigenen Score (Dreier-Pegel) und einem Radar daneben. Für alle, die verteidigen.

**Ein Projekt von [Dreier Labs](https://dreierlabs.com).** Ein privates Projekt, keine amtliche Stelle und keine Zusammenarbeit mit einer Behörde.

Status: öffentlich unter https://cyberlage.org (Beta). Neues gibt es auch im [Telegram-Kanal](https://t.me/cyberlage_org) und als [RSS-Feed](https://cyberlage.org/feed.xml).

## Der Dreier-Pegel

Der **Dreier-Pegel** (englisch: *Dreier Gauge*) ist der eigene Score von Cyberlage: eine Stufe (niedrig, erhöht, hoch), die allein aus den neu aufgenommenen Einträgen des CISA-KEV-Katalogs in 30 Tagen abgeleitet wird, mit Schwellen aus der 36-Monats-Verteilung und einem Aufschlag bei Ransomware. Der Name steht für Dreier Labs. Es ist unsere eigene Methode, die Regeln stehen offen in [RULES.md](RULES.md). Daneben zeigt der **Radar** andere Messungen und Einschätzungen, ohne sie mit dem Pegel zu vermischen.

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
| `pipeline/fetch_extra.py` | Holt CERT-Bund-Warnungen und EU-KEV (Kontext, nicht Teil der Stufe) |
| `pipeline/fetch_ausblick.py` | Holt neue CVEs der letzten 14 Tage (NVD) und ihre EPSS-Wahrscheinlichkeit (FIRST), schreibt `data/ausblick/ausblick.json` |
| `pipeline/fetch_radar.py` | Lage-Radar: Zeit bis zur KEV-Aufnahme (CVE-Liste), Trefferquote des Ausblicks, EU-Abgleich, SANS-Ampel; liest `data/radar/*.csv` (Einschätzungen und Gründe, von Hand mit Beleg) |
| `pipeline/prerender.py` | Schreibt die wichtigsten Werte als Text ins HTML, für Crawler ohne JavaScript |
| `pipeline/feed.py` | Schreibt `site/feed.xml` (RSS) aus `site/data/lage.json` |
| `pipeline/notify.py` | Telegram-Kanal: einmal täglich die Tageslage, sofort nur bei Stufenwechsel und Ransomware-Alarm |
| `pipeline/score.py` | Wertet nach den Regeln aus und schreibt `site/data/lage.json` |
| `tests/` | Tests für Abruf und Auswertung |
| `site/` | Die Seite (Deutsch und Englisch), Ausgabedaten und Feed |
| `.github/workflows/daten.yml` | Aktualisierung, alle zwei Stunden und von Hand startbar |

## Lokal ausführen

Nur Python 3, keine weiteren Pakete:

```
python3 -m unittest discover -s tests
python3 pipeline/fetch_kev.py
python3 pipeline/fetch_ausblick.py   # nur mit Internetzugang zu NVD und FIRST
python3 pipeline/score.py
python3 pipeline/feed.py
```

## Hinweis

Die Seite zeigt Zahlen aus öffentlichen Quellen. Sie ersetzt keine Warnung des BSI oder eines CERT. Die Verlinkung auf amtliche Quellen ist kein Hinweis auf eine Zusammenarbeit.
