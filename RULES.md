# Bewertungsregeln

Diese Regeln bestimmen, was auf der Seite als Zahl und als Warnstufe erscheint. Sie werden öffentlich geführt. Jede Änderung ist im Verlauf des Repos sichtbar. Umgesetzt sind sie in `pipeline/score.py`, die Einstellungen stehen in `config/`.

## Der Dreier-Pegel

Der **Dreier-Pegel** (englisch: *Dreier Gauge*) ist der eigene Gesamtscore von Cyberlage und Dreier Labs, keine Norm und kein Branchenstandard. Er fasst die Bausteine zu einer Zahl von 0 bis 100 zusammen und leitet daraus eine Stufe ab (ruhig, unauffällig, angespannt, hoch, außergewöhnlich). Wer Fragen oder Einwände zur Methode hat, kann auf GitHub ein Issue öffnen.

**Bausteine** (alle gleich gewichtet, Gewichte und Schwellen sind ein Entwurf und stehen offen in `config/regeln.json` und `config/radar_stufen.json`): KEV-Menge, Tempo bis KEV, BSI Cyber Index, SANS Infocon. Jeder Baustein hat eine feste Regelschwelle, sein Ausschlag ist der Messwert im Verhältnis zur Schwelle (höchstens 2,0). Der Pegel ist der Mittelwert der Ausschläge der Bausteine mit Messwert, umgerechnet auf 0 bis 100 (50: Schwellen im Schnitt erreicht, 100: im Schnitt doppelt so weit). Fehlt ein Messwert, zählt der Baustein nicht mit; die Zahl der beteiligten Bausteine steht dabei. KEV-Menge und Tempo bis KEV haben keinen eigenen Namen, es sind Bausteine. Der Tagesstand wird seit dem 24.11.2026 in `data/radar/score.json` gespeichert und nicht rückgerechnet.

Stufen: unter 30 ruhig, 30 bis 49 unauffällig, 50 bis 63 angespannt, 64 bis 79 hoch, ab 80 außergewöhnlich (vorläufig, siehe unten).

### Baustein KEV-Menge

Die **KEV-Menge** ist ein Baustein des Dreier-Pegels: die Zahl der in den letzten 30 Tagen neu in den CISA-KEV aufgenommenen Einträge. Aus ihm folgt die Stufe mit den Marken unten (erhöht ab 25, hoch ab 32, bei mindestens 5 Ransomware-Einträgen eine Stufe höher); der Ausschlag im Gesamtscore ist die Zahl geteilt durch 25. Es wird nichts gewichtet oder umgerechnet. Der Stand wird jeden Tag in `data/pegel.json` fortgeschrieben. Einträge mit `quelle: live` sind am Stichtag berechnet und werden danach nicht mehr geändert. Frühere Tage sind einmalig mit den heutigen Schwellen rückgerechnet und als `rueckgerechnet` gekennzeichnet.

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

**Konsens (Gegenüberstellung, nicht Teil der Stufe).** Der Radar stellt unserer Stufe unabhängige Quellen gegenüber und prüft, ob sie in dieselbe Richtung zeigen. Die Stufe selbst wird dadurch nicht verändert: Sie bleibt allein aus dem KEV berechenbar und nachprüfbar. Jedes Signal folgt einer festen Regel und steht auf erhöht, normal oder „noch keine Aussage“: BSI Cyber Index (erhöht ab 120 % des Basisjahres 2024, von Hand erfasst), SANS Infocon (erhöht, wenn nicht grün). Unsere eigenen Signale (Stufe, Tempo bis KEV) werden angezeigt, zählen aber nicht als Bestätigung, weil beide aus dem KEV stammen. Es wird nichts gemittelt.

**Telegram.** Wenig Rauschen: Sofort gesendet wird nur ein Stufenwechsel oder ein neuer KEV-Eintrag mit bekannter Ransomware-Nutzung. Alles andere Neue (KEV, kritische CERT-Bund-Warnungen, EU-KEV) wird gesammelt und einmal täglich ab 06:00 deutscher Zeit (vor 07:00) in einer Tageslage gesendet. Der Ausblick wird nicht gemeldet.

**Feed.** `site/feed.xml` enthält die neu aufgenommenen KEV-Einträge und die kritischen CERT-Bund-Warnungen (Titel, Datum, Link, Quelle), jeweils mit fester ID. Der Kanalkopf nennt die aktuelle Stufe. Der Ausblick steht nicht im Feed.

## Stand der Freigaben

- Schwellen: **freigegeben** am 23.11.2026 (erhöht ab 25, hoch ab 32, Ransomware-Aufschlag ab 5, Fenster 30 Tage, Basis 36 Monate).

## Offene Fragen

- Passen die Schwellen? Zum Beispiel Rückblick auf Monate mit bekannten Großlagen.
- Wie wird die EU-weite ENISA-Zahl neben den Tageswerten dargestellt, ohne sie als deutschen Wert auszugeben?
- Soll die Rückstufung nach einer Ruhephase eigens geregelt werden, oder reicht das gleitende Fenster?


## Radar-Grafik

Die Grafik im Radar zeigt je Signal einen Punkt. Der Abstand zur Mitte ist der Messwert im Verhältnis zur Regelschwelle des Signals (gestrichelter Ring = Schwelle erreicht, äußerer Ring = doppelt so weit). Cyberlage: neue KEV-Einträge in 30 Tagen geteilt durch die Schwelle für erhöht. Tempo bis KEV: Verbesserung des Medians gegenüber vor 12 Monaten geteilt durch 1,5. BSI Cyber Index: Wert geteilt durch 120 % des Basisjahres. SANS Infocon: grün 0,4, gelb 1,1, orange 1,5, rot 2,0 (feste Darstellungswerte). Ohne Messwert steht ein leerer Kreis nahe der Mitte. Die Grafik ändert keine Regel und mittelt nichts. NCSC-NL, EU-KEV und ENISA sind Kontext und haben keine Schwelle, sie stehen nur als Kacheln darunter.


## Gesamtscore: Rechnung (Experiment)

Der Dreier-Pegel ist ein **Experiment**. Er fasst die Ausschläge aller Signale mit Messwert zusammen: Mittelwert, alle gleich gewichtet, Ausschlag je Signal höchstens 2,0, umgerechnet auf 0 bis 100 (50 = Regelschwellen im Schnitt erreicht, 100 = im Schnitt doppelt so weit). Beteiligt sind die Signale der Radar-Grafik. Ein Signal ohne Messwert zählt nicht mit, die Zahl der beteiligten Signale steht dabei. Die Zeiträume sind verschieden (30 Tage bis Jahresvergleich) und werden je Signal genannt. Eigene Signale (Dreier-Pegel, Tempo bis KEV) und fremde Quellen gehen beide ein. Der SANS-Wert ist eine feste Darstellungsgröße (grün 0,4, gelb 1,1, orange 1,5, rot 2,0). Der Score ist deshalb nicht objektiv und nur als Gesamteindruck gedacht. Der Tagesstand wird ab dem ersten Tag in `data/radar/score.json` live gespeichert, rückgerechnet wird nicht.

## Prüfkalender
Von Hand gepflegte Angaben (`data/radar/gruende.csv`, `einschaetzungen.csv`) tragen `geprueft_am`. `pipeline/pruefen.py` läuft in jedem Lauf der Aktion und tut zweierlei: Es prüft höchstens einmal am Tag, ob jeder Link erreichbar ist (ein Link gilt erst als tot, wenn jeder Versuch 24 Stunden lang fehlschlägt), und es vergleicht `geprueft_am` mit der Frist: 330 Tage bei jährlichen Angaben, 90 Tage bei Gründen. Dazu gehören auch die Schwellen des Dreier-Pegels (`geprueft_am` in `config/regeln.json`), die alle 183 Tage von Hand neu abgeleitet und bestätigt werden: Sie sind feste Werte, und wird der KEV-Katalog dauerhaft aktiver, stünde der Pegel sonst immer häufiger auf „hoch“. Ist etwas fällig oder tot, steht es auf der Seite („Prüfung fällig“, „Link prüfen“) und ein GitHub-Issue „Prüfung fällig“ wird geöffnet; es schließt sich selbst, sobald alles geprüft ist. Das Skript prüft nur Frist und Erreichbarkeit, nicht den Inhalt; `geprueft_am` setzt ein Mensch, nachdem er die Quelle gelesen hat. Antwortet ein Server mit „verboten“ (401, 403, 429), weil er Automaten nicht liest, zählt das als erreichbar. Ergebnis: `data/radar/pruefung.json`.
Auf der Seite steht der Prüfkalender unter „info“ → „prüfkalender“ (jede Angabe mit Prüfdatum, Frist und Erreichbarkeit); unter den Gründen im Rückblick steht der Prüfstand in einer Zeile.

## Stufen des Dreier-Pegels und Fazit (vorläufig)
Der Dreier-Pegel (0 bis 100) bekommt eine Stufe aus `config/radar_stufen.json`: unter 30 ruhig, 30 bis 49 unauffällig, 50 bis 63 angespannt, 64 bis 79 hoch, ab 80 außergewöhnlich. Die Grenzen hängen am Dreier-Pegel: Der Score ist 50, wenn die Signale im Schnitt ihre Regelschwelle erreichen; 28 entspricht dem 25. Perzentil der 30-Tage-Zählung der letzten 36 Monate, 38 dem Median, 50 dem 75. Perzentil (Schwelle erhöht), 64 dem 90. Perzentil (Schwelle hoch), 80 etwa dem 98. Perzentil. Gerundet auf 30, 50, 64, 80. Das **Fazit** auf der Seite ist ein fester Satz aus der Stufe des Dreier-Pegels (zuerst) und den Aussagen der beiden KEV-Bausteine, dazu ein Hinweis für Verteidiger je Pegelstufe. Es rechnet nichts und sagt nichts voraus. Die Stufen sind vorläufig, weil der Radar-Score noch keine eigene Verteilung hat; im Prüfkalender steht die erste Prüfung nach 90 Tagen (ab 24.11.2026): Dann werden die Grenzen aus der eigenen Verteilung des Scores neu abgeleitet.

## Baustein Tempo bis KEV
Die KEV-Menge zählt die **Menge**, das Tempo bis KEV misst die **Geschwindigkeit**: gleitender 90-Tage-Median der Tage von der Veröffentlichung einer Lücke bis zu ihrer Aufnahme in den KEV (nur Lücken, die bei Aufnahme höchstens 365 Tage alt waren; mindestens 10 davon im Fenster, sonst keine Bewertung). Kleiner Median heißt schneller. Marken aus der Tagesverteilung der letzten 36 Monate (1098 Tage): 10. Perzentil 3 Tage, 25. Perzentil 5, Median 6,5, 75. Perzentil 8, 90. Perzentil 10,5. Festgelegt in `config/regeln.json` (Abschnitt `tempo`): **erhöht bis 5 Tage**, **hoch bis 3 Tage**. Beide Signale stammen aus demselben Katalog; sie sind verschiedene Achsen (mehr Lücken heißt nicht schnellere Aufnahme), zählen aber nicht als unabhängige Bestätigung. Im Radar-Score zählt das Tempo bis KEV mit Ausschlag `erhöht_bis / Median` (1,0 bei 5 Tagen, gedeckelt bei 2). Das Fazit nennt beide Stufen; der Hinweis für Verteidiger richtet sich nach der höheren. Die Marken werden mit den Schwellen des Dreier-Pegels halbjährlich geprüft (`geprueft_am` in `config/regeln.json`).

## Patch-Berichte (/patches)
Quellen ohne Konto: Microsoft Security Response Center (CVRF 3.0), Ubuntu Security Notices (JSON), Debian Security Advisories (RSS), Red Hat (CSAF-Verzeichnis), Cisco (RSS), SAP (öffentliche Monatsseiten des Security Patch Day; Hinweistexte nur mit SAP for Me). Adobe wird nur verlinkt: kein Feed ohne Konto. Es wird nur gezählt und verlinkt; Schweregrad, Ausnutzung und Bekanntheit stammen von den Herstellern und fehlen, wo sie nicht geliefert werden.
- **Microsoft, je Patch Day:** Zählung je CVE nach Schweregrad, ausgenutzt, öffentlich bekannt, Auswirkungsart, betroffener Produktfamilie, Überschneidung mit dem CISA-KEV. Nicht mitgezählt, aber ausgewiesen: Chromium-Lücken im Edge und Paketlücken von Azure Linux (früher Mariner), weil sie den Patch Day sonst um ein Vielfaches aufblähen. Spätere Ergänzungen des Monatsdokuments (Out-of-Band) stehen als Nachtrag.
- **Bewertung (fest, keine Vorhersage):** Umfang gegen den Median der bis zu 12 Vormonate (ab 3 Vormonaten): ab dem 1,25-Fachen „größer als üblich“, bis zum 0,8-Fachen „kleiner als üblich“, sonst „üblicher Umfang“. Dringlichkeit: „dringend“ bei mindestens einer vom Hersteller als ausgenutzt gemeldeten Lücke, „zeitnah“ bei kritischen Lücken, sonst „normal“.
- **Diese Woche zuerst:** höchstens acht Einträge in fester Reihenfolge: 1. im CISA-KEV, 2. vom Hersteller als ausgenutzt gemeldet, 3. EPSS ab 10 %, 4. vom Hersteller als kritisch eingestuft; innerhalb einer Stufe nach EPSS. Berücksichtigt werden Microsoft-Patch-Days der letzten 30 Tage, Linux-Meldungen (nur mit KEV-Bezug) und Cisco der letzten 14 Tage.
- **Distributionen und Hersteller:** neu in 7 und 30 Tagen, davon kritisch (nur wo geliefert), genannte CVEs, Meldungen mit KEV-Bezug. Jede Quelle wird einzeln und fail-soft abgerufen.
- **Telegram:** Patch Day (bis 10 Tage nach Veröffentlichung) und Nachträge sofort; das Fazit in der Tageslage nur bei geänderter Stufen-Kombination (Dreier-Pegel, Tempo bis KEV, Radar) und montags als Wochenstand; dazu die ersten drei Einträge von „Diese Woche zuerst“.

### Patch-Rangliste: Bewertung und Reihenfolge
- Je Eintrag zeigen wir den CVSS-Basiswert. Bei Microsoft stammt er aus dem Sicherheitsupdate-Datensatz (CVRF), bei den übrigen aus der NVD (Cache `data/patches/cvss.json`, höchstens 20 neue Abfragen je Lauf, Fehler lassen den Wert offen). Meldungen mit mehreren CVEs zeigen bis zu drei Werte, die höchsten zuerst.
- Die Reihenfolge bestimmt die Stufe (1 im CISA-KEV, 2 vom Hersteller als ausgenutzt gemeldet, 3 EPSS ab 10 %, 4 vom Hersteller als kritisch eingestuft), innerhalb der Stufe zuerst EPSS, dann CVSS, dann die Kennung. Der CVSS-Wert beschreibt die Schwere, nicht die Angriffslage: Er entscheidet deshalb nur innerhalb einer Stufe.

### Patch-Kalender, Filter und Export
- **Termine (/termine):** Microsoft Patch Day, Adobe und SAP Security Patch Day am zweiten Dienstag des Monats. Oracle am dritten Dienstag jedes Monats: Critical Patch Update im Januar, April, Juli und Oktober, in den übrigen Monaten das Critical Security Patch Update (Quelle: Oracle Security Alerts, oracle.com/security-alerts; Oracle meldet jeden Termin am Donnerstag davor an). Die Daten werden im Browser aus diesen Regeln berechnet und nicht gespeichert. Außerplanmäßige Updates sind nicht vorhersehbar und erscheinen im Ticker, sobald Microsoft einen Nachtrag meldet.
- **Betrifft mich?:** Der Filter sucht die eingegebenen Begriffe (durch Komma getrennt) im Text jedes Eintrags der Rangliste. Er läuft nur im Browser; der Suchtext und die „erledigt“-Haken liegen im lokalen Speicher des Browsers und werden nirgends hin übertragen.
- **Export:** Kurzfassung (Text), CSV und Markdown (Checkliste) enthalten die gerade sichtbaren, also gefilterten Einträge mit CVE, Titel, CVSS, EPSS, Stufe, Lösung und Link.

### Edge und Chrome, Lücken ohne Patch
- **Chromium (Edge, Chrome):** Chromium-Lücken stehen in Microsofts Monatsdatensatz, kommen aber laufend mit den Browser-Updates. Wir zählen sie getrennt und zeigen als Lösung die höchste Edge-Fixversion des Monats (aus Microsofts Angaben je CVE) und die höchste Chrome-Version aus den Titeln der Meldungen („prior to …“). Als ausgenutzt gelten Lücken, die Microsoft so meldet oder die im CISA-KEV stehen.
- **Lücken ohne Patch:** Wir zeigen sie nur, wo der Hersteller selbst keinen Patch angibt (bei Microsoft: nur Umgehung oder Abmilderung). Der CISA-KEV enthält keinen Patch-Stand; sein Standardtext „Abmilderung oder Abschalten“ steht auch bei Lücken mit Patch und wird deshalb nicht dafür verwendet. Die Seite sagt offen, dass dadurch viele Lücken ohne Patch unsichtbar bleiben.
- **Kalender-Export:** Die Schaltflächen im Patch-Kalender erzeugen im Browser eine .ics-Datei (einzelner Termin oder vier wiederkehrende Serien: Microsoft, Adobe und SAP am zweiten Dienstag, Oracle am dritten Dienstag) mit Erinnerung am Vortag um 9 Uhr. Es wird nichts an einen Server gesendet.

### Rückgerechneter Verlauf des Dreier-Pegels
Der Verlauf im Rückblick reicht 36 Monate zurück. Für Tage vor dem 24.11.2026 wird der Score aus den Bausteinen rückgerechnet, für die es Historie gibt: KEV-Menge (Tageszählung) und Tempo bis KEV (gleitender 90-Tage-Median). Rechnung wie beim Live-Wert: Mittelwert der Ausschläge, höchstens 2,0, auf 0 bis 100 umgerechnet. BSI Cyber Index (jährlich, von Hand) und SANS Infocon (nur Tagesstand) haben keine Tagesreihe und fehlen in der Rückrechnung; wie viele Bausteine je Tag beteiligt waren, steht im Tooltip. Rückgerechnete Tage sind in der Grafik gedämpft dargestellt. Am Übergang zum Live-Wert (mit allen verfügbaren Bausteinen) kann der Verlauf springen. Die Rückrechnung wird bei jedem Lauf neu aus festen Daten berechnet und nicht gespeichert; gespeichert wird nur der Live-Wert (`data/radar/score.json`).

### Entfallener Baustein: Feodo Tracker
Der Feodo Tracker (abuse.ch) war als Baustein „Botnetz-Server“ vorgesehen und ist entfernt. Grund: Seine Datensätze sind leer, weil Polizeiaktionen (Emotet 2021, Operation Endgame 2024) die verfolgten Botnetze zerschlagen haben; es gibt dort keine aktiven Steuerserver mehr, die man zählen könnte. Ein Baustein ohne Daten trägt nichts zum Score bei. Ein Ersatz mit Tageshistorie, ohne Konto und mit freier Nutzung für eine öffentliche Seite wird gesucht; bis dahin zählt der Score ohne ihn.
