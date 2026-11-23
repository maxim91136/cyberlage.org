# Bewertungsregeln (Entwurf)

Diese Regeln bestimmen, was auf der Seite als Zahl und als Warnstufe erscheint. Sie sind ein Entwurf und werden öffentlich geführt. Jede Änderung ist im Verlauf des Repos sichtbar. Umgesetzt sind sie in `pipeline/score.py`, die Einstellungen stehen in `config/`.

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

**Verwaltungsbezug.** Ein Eintrag zählt als verwaltungsrelevant, wenn Hersteller und Produktname **genau** (Groß-/Kleinschreibung egal) mit einer freigegebenen Zeile in `config/produkte.csv` übereinstimmen. Es gibt bewusst keinen Teiltreffer, weil „Exchange“ sonst auch „Internet Key Exchange“ träfe. Namensvarianten im KEV stehen als eigene Zeilen in der Liste. Eine Zeile gilt nur mit Status `freigegeben`, Begründung und Beleg.

**Stufe.** Nur wenn die Schwellen in `config/regeln.json` den Status `freigegeben` haben **und** mindestens ein Produkt freigegeben ist:

| Neue verwaltungsrelevante Einträge im Fenster | Stufe |
| --- | --- |
| weniger als `erhoeht_ab` | niedrig |
| ab `erhoeht_ab` | erhöht |
| ab `hoch_ab` | hoch |

Ist unter den verwaltungsrelevanten Einträgen mindestens einer mit bekannter Ransomware-Nutzung, steigt die Stufe um eine (höchstens bis „hoch“). Die Ausgabe nennt immer die Begründung in Worten.

## Stand der Freigaben

- Schwellen: **Entwurf** (Vorschlag: erhöht ab 1, hoch ab 3, Fenster 30 Tage). Solange das so ist, gibt es keine Stufe.
- Produktliste: **keine Freigaben**. Die Zeilen sind Entwürfe ohne Beleg. Solange das so ist, gibt es keinen Verwaltungsbezug.

## Offene Fragen

- Welche Produkte gehören auf die Liste, und womit wird jedes belegt (Verbreitung in der Verwaltung)?
- Passen die Schwellen? Dafür sollten wir sie an einigen vergangenen Monaten testen.
- Wie wird die EU-weite ENISA-Zahl neben den Tageswerten dargestellt, ohne sie als deutschen Wert auszugeben?
- Soll die Rückstufung nach einer Ruhephase eigens geregelt werden, oder reicht das gleitende Fenster?
