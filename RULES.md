# Bewertungsregeln

Diese Regeln bestimmen, was auf der Seite als Zahl und als Warnstufe erscheint. Sie werden öffentlich geführt. Jede Änderung ist im Verlauf des Repos sichtbar. Umgesetzt sind sie in `pipeline/score.py`, die Einstellungen stehen in `config/`.

## Grundsätze

1. Die Stufe entsteht nur aus den Regeln unten, nie von Hand.
2. Jeder Wert zeigt Quelle, Stand und Lizenz.
3. Fehlen Daten oder Freigaben, steht in der Ausgabe `null` bzw. „keine Daten“. Es wird nichts geschätzt.
4. Es werden nur Sektoren und Trends gezeigt, keine einzelnen Behörden.
5. Nur Quellen mit Status „grün“ gehen in die Berechnung ein. Alles andere wird nur verlinkt.

## Eingaben

| Eingabe | Quelle | Aktualisierung | Geltungsbereich |
| --- | --- | --- | --- |
| Neu aufgenommene ausgenutzte Schwachstellen | CISA KEV | täglich | weltweit |
| Kennzeichen „in Ransomware-Kampagnen genutzt“ | CISA KEV | täglich | weltweit |
| Anteil des Sektors an erfassten Ereignissen | ENISA Threat Landscape | jährlich, von Hand | EU |

ENISA-Werte werden nur übernommen, wenn sie in `data/enisa.csv` den Status `geprueft` haben und Seitenangabe, Berichtsjahr und Geltungsbereich tragen. Sie werden nie als deutsche Werte dargestellt.

## Berechnung

**Fenster.** Gezählt werden die Einträge der letzten `fenster_tage` Tage bis einschließlich des Stands (Standard 30 Tage, also bei Stand 23.11. der 25.10. bis 23.11.).

**Kennzahlen aus KEV (immer, ohne Produktliste):** Gesamtzahl, neu in 7 Tagen, neu im Fenster, davon mit bekannter Ransomware-Nutzung.

**Keine Produktliste.** Die Seite zeigt alle neu aufgenommenen Einträge mit Hersteller und Produkt. Wer verteidigt, weiß selbst, was im Einsatz ist, und gleicht die Liste mit dem eigenen Bestand ab (Filter im Browser, nichts wird übertragen). Es gibt keine Annahmen darüber, was in der Verwaltung läuft.

**Stufe.** Sie misst die Aktivität im KEV-Katalog, nicht die Zahl der Angriffe. Nur wenn die Schwellen in `config/regeln.json` den Status `freigegeben` haben:

| Neu aufgenommene Einträge im Fenster | Stufe |
| --- | --- |
| weniger als `erhoeht_ab` | niedrig |
| ab `erhoeht_ab` | erhöht |
| ab `hoch_ab` | hoch |

Sind mindestens `ransomware_aufschlag_ab` der Einträge mit bekannter Ransomware-Nutzung gekennzeichnet, steigt die Stufe um eine (höchstens bis „hoch“). Die Ausgabe nennt immer die Begründung in Worten.

**Herleitung der Schwellen.** Aus der Verteilung der 30-Tage-Zählung über die letzten 12 Monate (täglich gemessen bis 23.11.2026): Median 26, 75. Perzentil 31, 90. Perzentil 37; Ransomware-bekannt 90. Perzentil 5. Vorschlag: erhöht ab 31, hoch ab 37, Aufschlag ab 5. Die Werte stehen mit Begründung in `config/regeln.json` und müssen gelegentlich neu geprüft werden.

## Stand der Freigaben

- Schwellen: **freigegeben** am 23.11.2026 (erhöht ab 31, hoch ab 37, Ransomware-Aufschlag ab 5, Fenster 30 Tage).

## Offene Fragen

- Passen die Schwellen? Zum Beispiel Rückblick auf Monate mit bekannten Großlagen.
- Wie wird die EU-weite ENISA-Zahl neben den Tageswerten dargestellt, ohne sie als deutschen Wert auszugeben?
- Soll die Rückstufung nach einer Ruhephase eigens geregelt werden, oder reicht das gleitende Fenster?
