# Bewertungsregeln

Diese Regeln bestimmen, was auf der Seite als Zahl und als Warnstufe erscheint. Sie werden öffentlich geführt. Jede Änderung ist im Verlauf des Repos sichtbar. Umgesetzt sind sie in `pipeline/score.py`, die Einstellungen stehen in `config/`.

## Der Dreier-Pegel

Die Stufe unten heißt **Dreier-Pegel** (englisch: *Dreier Gauge*). Das ist der eigene Score von Cyberlage und Dreier Labs, keine Norm und kein Branchenstandard. Wer Fragen oder Einwände zur Methode hat, kann auf GitHub ein Issue öffnen.

### Pegelstand (Zahl)

Der Dreier-Pegel hat auch einen Zahlenwert, den **Pegelstand**: die Zahl der in den letzten 30 Tagen neu in den CISA-KEV aufgenommenen Einträge. Aus ihm folgt die Stufe mit den Marken unten (erhöht ab 25, hoch ab 32, bei mindestens 5 Ransomware-Einträgen eine Stufe höher). Es wird nichts gewichtet oder umgerechnet. Der Stand wird jeden Tag in `data/pegel.json` fortgeschrieben. Einträge mit `quelle: live` sind am Stichtag berechnet und werden danach nicht mehr geändert. Frühere Tage sind einmalig mit den heutigen Schwellen rückgerechnet und als `rueckgerechnet` gekennzeichnet.

## Grundsätze

1. Die Stufe entsteht nur aus den Regeln unten, nie von Hand.
2. Jeder Wert zeigt Quelle, Stand und Lizenz.
3. Fehlen Daten oder Freigaben, steht in der Ausgabe `null` bzw. „keine Daten“. Es wird nichts geschätzt.
4. Es werden keine einzelnen Betroffenen genannt. Die Stufe gilt allgemein, nicht für einen bestimmten Sektor.
5. Nur Quellen mit Status „grün“ gehen in die Berechnung ein. Alles andere wird nur verlinkt.

## Eingaben

| Eingabe | Quelle | Aktualisierung | Geltungsbereich |
| --- | --- | --- | --- |
| Neu aufgenommene ausgenutzte Schwachstellen | CISA KEV | täglich | weltweit |
| Kennzeichen „in Ransomware-Kampagnen genutzt“ | CISA KEV | täglich | weltweit |
| Neue CVEs der letzten 14 Tage ohne KEV-Eintrag, mit EPSS-Wahrscheinlichkeit (Ausblick, nicht Teil der Stufe) | NVD (Veröffentlichung, CVSS), FIRST EPSS | alle zwei Stunden | weltweit |
| Anteil der öffentlichen Verwaltung an erfassten Ereignissen (Einordnung, nicht Teil der Stufe) | ENISA Threat Landscape | jährlich, von Hand | EU |

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

**Herleitung der Schwellen.** Aus der Verteilung der 30-Tage-Zählung über die letzten 36 Monate (täglich gemessen 23.11.2023 bis 23.11.2026, das Anlaufjahr 2022 ausgenommen): Median 19, 75. Perzentil 25, 90. Perzentil 32; Ransomware-bekannt 90. Perzentil 5. Festgelegt: erhöht ab 25, hoch ab 32, Aufschlag ab 5. Zum Vergleich ergaben 12 Monate 31/37 und 24 Monate 29/34; der Katalog wird aktiver, deshalb die längere Basis. Die Werte stehen mit Begründung in `config/regeln.json` und müssen gelegentlich neu geprüft werden.

**Ausblick.** Er zeigt, was als Nächstes in den KEV-Katalog kommen könnte, und beeinflusst die Stufe nicht. Geprüft werden alle bei der NVD veröffentlichten CVEs der letzten 14 Tage, die nicht im KEV stehen. EPSS (FIRST) schätzt die Wahrscheinlichkeit, dass eine Schwachstelle in den nächsten 30 Tagen ausgenutzt wird. Gezählt werden die mit mindestens 10 %, angezeigt werden die zehn höchsten mit Datum, Wahrscheinlichkeit, CVSS und Link. Abgelehnte CVEs fallen weg, fehlt ein EPSS-Wert, wird die CVE nicht bewertet. Das ist eine Schätzung, kein Nachweis. Quellenhinweise: „See EPSS at https://www.first.org/epss“ und „This product uses data from the NVD API but is not endorsed or certified by the NVD“.

**Schlagzeile und Kennzahlen.** Der Satz oben auf der Seite folgt einer festen Regel: Verglichen wird der Median bis zur KEV-Aufnahme (frische Lücken, letzte 90 Tage) mit dem Wert vor 12 Monaten, vorausgesetzt beide beruhen auf mindestens 10 Einträgen. Ist der alte Wert mindestens 1,5-mal so hoch, steht „rund x-mal schneller“, ist er höchstens zwei Drittel so hoch, „langsamer“, sonst „ungefähr so schnell“. Die drei Kennzahlen sind: neu im KEV in 30 Tagen, Median bis zur Aufnahme und Anteil binnen 30 Tagen, jeweils mit dem Vergleichswert.

**Radar.** Eigene Messungen und Einschätzungen anderer, nichts davon geht in die Stufe. (1) Zeit bis zur Aufnahme: Tage zwischen Veröffentlichung einer CVE (CVE-Liste) und Aufnahme in den KEV, je Monat; der Median zählt nur „frische“ Lücken (bei Aufnahme höchstens 365 Tage alt), dazu der Anteil binnen 30 Tagen. Das ist die Aufnahme, nicht der erste Angriff. (2) Trefferquote: Jede Prognose des Ausblicks (EPSS ab 10 %) wird beim ersten Auftreten gespeichert (`data/radar/prognosen.json`); die Quote gilt erst für Prognosen, die älter als 30 Tage sind, und zählt, wie viele davon im KEV stehen. (3) Abgleich EU-KEV und CISA-KEV: Überschneidung und Abstand der Daten. (4) Vergleichsleiste: BSI-Gesamturteil (jährlich, von Hand, mit Beleg) und SANS-Infocon (live), jeweils mit dem, was sie messen. Gründe stehen mit Quelle in `data/radar/gruende.csv`. Geopolitik wird nicht gemessen.

**Konsens (Gegenüberstellung, nicht Teil der Stufe).** Der Radar stellt unserer Stufe unabhängige Quellen gegenüber und prüft, ob sie in dieselbe Richtung zeigen. Die Stufe selbst wird dadurch nicht verändert: Sie bleibt allein aus dem KEV berechenbar und nachprüfbar. Jedes Signal folgt einer festen Regel und steht auf erhöht, normal oder „noch keine Aussage“: BSI Cyber Index (erhöht ab 120 % des Basisjahres 2024, von Hand erfasst), SANS Infocon (erhöht, wenn nicht grün), Feodo Tracker (aktive Botnetz-Steuerserver mindestens 25 % und mindestens 3 über dem Median der letzten 90 Tage, erst ab 30 eigenen Messtagen, Zeitreihe in `data/radar/feodo.json`). Unsere eigenen Signale (Stufe, Tempo bis KEV) werden angezeigt, zählen aber nicht als Bestätigung, weil beide aus dem KEV stammen. Es wird nichts gemittelt.

**Telegram.** Wenig Rauschen: Sofort gesendet wird nur ein Stufenwechsel oder ein neuer KEV-Eintrag mit bekannter Ransomware-Nutzung. Alles andere Neue (KEV, kritische CERT-Bund-Warnungen, EU-KEV) wird gesammelt und einmal täglich ab 06:00 deutscher Zeit (vor 07:00) in einer Tageslage gesendet. Der Ausblick wird nicht gemeldet.

**Feed.** `site/feed.xml` enthält die neu aufgenommenen KEV-Einträge und die kritischen CERT-Bund-Warnungen (Titel, Datum, Link, Quelle), jeweils mit fester ID. Der Kanalkopf nennt die aktuelle Stufe. Der Ausblick steht nicht im Feed.

## Stand der Freigaben

- Schwellen: **freigegeben** am 23.11.2026 (erhöht ab 25, hoch ab 32, Ransomware-Aufschlag ab 5, Fenster 30 Tage, Basis 36 Monate).

## Offene Fragen

- Passen die Schwellen? Zum Beispiel Rückblick auf Monate mit bekannten Großlagen.
- Wie wird die EU-weite ENISA-Zahl neben den Tageswerten dargestellt, ohne sie als deutschen Wert auszugeben?
- Soll die Rückstufung nach einer Ruhephase eigens geregelt werden, oder reicht das gleitende Fenster?


## Radar-Grafik

Die Grafik im Radar zeigt je Signal einen Punkt. Der Abstand zur Mitte ist der Messwert im Verhältnis zur Regelschwelle des Signals (gestrichelter Ring = Schwelle erreicht, äußerer Ring = doppelt so weit). Cyberlage: neue KEV-Einträge in 30 Tagen geteilt durch die Schwelle für erhöht. Tempo bis KEV: Verbesserung des Medians gegenüber vor 12 Monaten geteilt durch 1,5. BSI Cyber Index: Wert geteilt durch 120 % des Basisjahres. SANS Infocon: grün 0,4, gelb 1,1, orange 1,5, rot 2,0 (feste Darstellungswerte). Feodo: aktive Steuerserver geteilt durch das 1,25-Fache des 90-Tage-Medians, unter der Schwelle höchstens 0,99. Ohne Messwert steht ein leerer Kreis nahe der Mitte. Die Grafik ändert keine Regel und mittelt nichts. NCSC-NL, EU-KEV und ENISA sind Kontext und haben keine Schwelle, sie stehen nur als Kacheln darunter.


## Radar-Score (Experiment)

Der Radar-Score ist ein **Experiment** und nicht Teil des Dreier-Pegels. Er fasst die Ausschläge aller Signale mit Messwert zusammen: Mittelwert, alle gleich gewichtet, Ausschlag je Signal höchstens 2,0, umgerechnet auf 0 bis 100 (50 = Regelschwellen im Schnitt erreicht, 100 = im Schnitt doppelt so weit). Beteiligt sind die Signale der Radar-Grafik. Ein Signal ohne Messwert zählt nicht mit, die Zahl der beteiligten Signale steht dabei. Die Zeiträume sind verschieden (30 Tage bis Jahresvergleich) und werden je Signal genannt. Eigene Signale (Dreier-Pegel, Tempo bis KEV) und fremde Quellen gehen beide ein. Der SANS-Wert ist eine feste Darstellungsgröße (grün 0,4, gelb 1,1, orange 1,5, rot 2,0). Der Score ist deshalb nicht objektiv und nur als Gesamteindruck gedacht. Der Tagesstand wird ab dem ersten Tag in `data/radar/score.json` live gespeichert, rückgerechnet wird nicht.

## Prüfkalender
Von Hand gepflegte Angaben (`data/radar/gruende.csv`, `einschaetzungen.csv`) tragen `geprueft_am`. `pipeline/pruefen.py` läuft in jedem Lauf der Aktion und tut zweierlei: Es prüft höchstens einmal am Tag, ob jeder Link erreichbar ist (ein Link gilt erst als tot, wenn jeder Versuch 24 Stunden lang fehlschlägt), und es vergleicht `geprueft_am` mit der Frist: 330 Tage bei jährlichen Angaben, 90 Tage bei Gründen. Dazu gehören auch die Schwellen des Dreier-Pegels (`geprueft_am` in `config/regeln.json`), die alle 183 Tage von Hand neu abgeleitet und bestätigt werden: Sie sind feste Werte, und wird der KEV-Katalog dauerhaft aktiver, stünde der Pegel sonst immer häufiger auf „hoch“. Ist etwas fällig oder tot, steht es auf der Seite („Prüfung fällig“, „Link prüfen“) und ein GitHub-Issue „Prüfung fällig“ wird geöffnet; es schließt sich selbst, sobald alles geprüft ist. Das Skript prüft nur Frist und Erreichbarkeit, nicht den Inhalt; `geprueft_am` setzt ein Mensch, nachdem er die Quelle gelesen hat. Antwortet ein Server mit „verboten“ (401, 403, 429), weil er Automaten nicht liest, zählt das als erreichbar. Ergebnis: `data/radar/pruefung.json`.
Auf der Seite steht der Prüfkalender unter „info“ → „prüfkalender“ (jede Angabe mit Prüfdatum, Frist und Erreichbarkeit); unter den Gründen im Rückblick steht der Prüfstand in einer Zeile.

## Stufen des Radar-Scores und Fazit (vorläufig)
Der Radar-Score (0 bis 100) bekommt eine Stufe aus `config/radar_stufen.json`: unter 30 ruhig, 30 bis 49 unauffällig, 50 bis 63 erhöht, 64 bis 79 hoch, ab 80 außergewöhnlich. Die Grenzen hängen am Dreier-Pegel: Der Score ist 50, wenn die Signale im Schnitt ihre Regelschwelle erreichen; 28 entspricht dem 25. Perzentil der 30-Tage-Zählung der letzten 36 Monate, 38 dem Median, 50 dem 75. Perzentil (Schwelle erhöht), 64 dem 90. Perzentil (Schwelle hoch), 80 etwa dem 98. Perzentil. Gerundet auf 30, 50, 64, 80. Das **Fazit** auf der Seite ist ein fester Satz aus der Radar-Stufe und der Stufe des Dreier-Pegels, dazu ein Hinweis für Verteidiger je Pegelstufe. Es rechnet nichts und sagt nichts voraus. Die Stufen sind vorläufig, weil der Radar-Score noch keine eigene Verteilung hat; im Prüfkalender steht die erste Prüfung nach 90 Tagen (ab 24.11.2026): Dann werden die Grenzen aus der eigenen Verteilung des Scores neu abgeleitet.
