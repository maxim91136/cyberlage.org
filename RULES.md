# Bewertungsregeln

Diese Regeln bestimmen, was auf der Seite als Zahl und als Warnstufe erscheint. Sie werden öffentlich geführt. Jede Änderung ist im Verlauf des Repos sichtbar. Umgesetzt sind sie in `pipeline/score.py`, die Einstellungen stehen in `config/`.

## Der Dreier-Pegel

Der **Dreier-Pegel** (englisch: *Dreier Gauge*) ist der eigene Gesamtscore von Cyberlage und Dreier Labs, keine Norm und kein Branchenstandard. Er fasst die Bausteine zu einer Zahl von 0 bis 100 zusammen und leitet daraus eine Stufe ab (ruhig, unauffällig, angespannt, hoch, außergewöhnlich). Wer Fragen oder Einwände zur Methode hat, kann auf GitHub ein Issue öffnen.

**Bausteine** (zehn, in vier Gruppen; Schwellen und Gruppen stehen offen in `config/modell.json`, `config/regeln.json` und `config/radar_stufen.json`): KEV-Menge, Tempo bis KEV, EU-KEV, Microsoft (Gruppe Ausnutzung), CERT-Bund, NCSC-NL (Gruppe Warnungen), DShield, Ransomware (Gruppe Angriffsaktivität), BSI Cyber Index, SANS Infocon (Gruppe Externe Einschätzungen). Jeder Baustein hat eine feste Regelschwelle, sein Ausschlag ist der Messwert im Verhältnis zur Schwelle (höchstens 2,0). Erst wird je Gruppe gemittelt, dann über die Gruppen, umgerechnet auf 0 bis 100 (50: Schwellen im Schnitt erreicht, 100: im Schnitt doppelt so weit). Fehlt ein Messwert, zählt der Baustein nicht mit; die Zahl der beteiligten Bausteine steht dabei. Die Bausteine haben keinen eigenen Namen. Der Tagesstand des vollen Pegels wird seit dem 25.11.2026 in `data/radar/score.json` gespeichert; der Verlauf davor wird aus Archivdaten rückgerechnet (siehe unten).

Stufen: unter 35 ruhig, 35 bis 49 unauffällig, 50 bis 63 angespannt, 64 bis 79 hoch, ab 80 außergewöhnlich (vorläufig, siehe unten).

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


## Gesamtscore: Rechnung

Der Dreier-Pegel ist ein eigenes Modell von Dreier Labs. Er fasst die Ausschläge aller Signale mit Messwert zusammen: Mittelwert, alle gleich gewichtet, Ausschlag je Signal höchstens 2,0, umgerechnet auf 0 bis 100 (50 = Regelschwellen im Schnitt erreicht, 100 = im Schnitt doppelt so weit). Beteiligt sind die Signale der Radar-Grafik. Ein Signal ohne Messwert zählt nicht mit, die Zahl der beteiligten Signale steht dabei. Die Zeiträume sind verschieden (30 Tage bis Jahresvergleich) und werden je Signal genannt. Eigene Signale (Dreier-Pegel, Tempo bis KEV) und fremde Quellen gehen beide ein. Der SANS-Wert ist eine feste Darstellungsgröße (grün 0,4, gelb 1,1, orange 1,5, rot 2,0). Der Score ist deshalb nicht objektiv und nur als Gesamteindruck gedacht. Der Tagesstand wird ab dem ersten Tag in `data/radar/score.json` live gespeichert, rückgerechnet wird nicht.

## Prüfkalender
Von Hand gepflegte Angaben (`data/radar/gruende.csv`, `einschaetzungen.csv`) tragen `geprueft_am`. `pipeline/pruefen.py` läuft in jedem Lauf der Aktion und tut zweierlei: Es prüft höchstens einmal am Tag, ob jeder Link erreichbar ist (ein Link gilt erst als tot, wenn jeder Versuch 24 Stunden lang fehlschlägt), und es vergleicht `geprueft_am` mit der Frist: 330 Tage bei jährlichen Angaben, 90 Tage bei Gründen. Dazu gehören auch die Schwellen des Dreier-Pegels (`geprueft_am` in `config/regeln.json`), die alle 183 Tage von Hand neu abgeleitet und bestätigt werden: Sie sind feste Werte, und wird der KEV-Katalog dauerhaft aktiver, stünde der Pegel sonst immer häufiger auf „hoch“. Ist etwas fällig oder tot, steht es auf der Seite („Prüfung fällig“, „Link prüfen“) und ein GitHub-Issue „Prüfung fällig“ wird geöffnet; es schließt sich selbst, sobald alles geprüft ist. Das Skript prüft nur Frist und Erreichbarkeit, nicht den Inhalt; `geprueft_am` setzt ein Mensch, nachdem er die Quelle gelesen hat. Antwortet ein Server mit „verboten“ (401, 403, 429), weil er Automaten nicht liest, zählt das als erreichbar. Ergebnis: `data/radar/pruefung.json`.
Auf der Seite steht der Prüfkalender unter „info“ → „prüfkalender“ (jede Angabe mit Prüfdatum, Frist und Erreichbarkeit); unter den Gründen im Rückblick steht der Prüfstand in einer Zeile.

## Stufen des Dreier-Pegels und Fazit (vorläufig)
Der Dreier-Pegel (0 bis 100) bekommt eine Stufe aus `config/radar_stufen.json`: unter 35 ruhig, 35 bis 49 unauffällig, 50 bis 63 angespannt, 64 bis 79 hoch, ab 80 außergewöhnlich. Die Grenzen hängen am Dreier-Pegel: Der Score ist 50, wenn die Signale im Schnitt ihre Regelschwelle erreichen; 28 entspricht dem 25. Perzentil der 30-Tage-Zählung der letzten 36 Monate, 38 dem Median, 50 dem 75. Perzentil (Schwelle erhöht), 64 dem 90. Perzentil (Schwelle hoch), 80 etwa dem 98. Perzentil. Gerundet auf 30, 50, 64, 80. Das **Fazit** auf der Seite ist ein fester Satz aus der Stufe des Dreier-Pegels (zuerst) und den Aussagen der beiden KEV-Bausteine, dazu ein Hinweis für Verteidiger je Pegelstufe. Es rechnet nichts und sagt nichts voraus. Die Stufen sind vorläufig, weil der Radar-Score noch keine eigene Verteilung hat; im Prüfkalender steht die erste Prüfung nach 90 Tagen (ab 24.11.2026): Dann werden die Grenzen aus der eigenen Verteilung des Scores neu abgeleitet. Das Fazit nennt zusätzlich, wie viele Bausteine an oder über ihrer Schwelle liegen, und die bis zu drei stärksten mit ihrem Ausschlag.

## Baustein Tempo bis KEV
Die KEV-Menge zählt die **Menge**, das Tempo bis KEV misst die **Geschwindigkeit**: gleitender 90-Tage-Median der Tage von der Veröffentlichung einer Lücke bis zu ihrer Aufnahme in den KEV (nur Lücken, die bei Aufnahme höchstens 365 Tage alt waren; mindestens 10 davon im Fenster, sonst keine Bewertung). Kleiner Median heißt schneller. Marken aus der Tagesverteilung der letzten 36 Monate (1098 Tage): 10. Perzentil 3 Tage, 25. Perzentil 5, Median 6,5, 75. Perzentil 8, 90. Perzentil 10,5. Festgelegt in `config/regeln.json` (Abschnitt `tempo`): **erhöht bis 5 Tage**, **hoch bis 3 Tage**. Beide Signale stammen aus demselben Katalog; sie sind verschiedene Achsen (mehr Lücken heißt nicht schnellere Aufnahme), zählen aber nicht als unabhängige Bestätigung. Im Radar-Score zählt das Tempo bis KEV mit Ausschlag `erhöht_bis / Median` (1,0 bei 5 Tagen, gedeckelt bei 2). Das Fazit nennt beide Stufen; der Hinweis für Verteidiger richtet sich nach der höheren. Die Marken werden mit den Schwellen des Dreier-Pegels halbjährlich geprüft (`geprueft_am` in `config/regeln.json`).

## Patch-Berichte (/patches)
Quellen ohne Konto: Microsoft Security Response Center (CVRF 3.0), Ubuntu Security Notices (JSON), Debian Security Advisories (RSS), Red Hat (CSAF-Verzeichnis), SUSE (Monatsarchiv der Liste sle-security-updates), AlmaLinux (RSS je Version), Rocky Linux (öffentliche JSON-Schnittstelle), Amazon Linux (RSS für AL2023 und AL2), Cisco (RSS), SAP (öffentliche Monatsseiten des Security Patch Day; Hinweistexte nur mit SAP for Me). Adobe wird nur verlinkt: kein Feed ohne Konto. Es wird nur gezählt und verlinkt; Schweregrad, Ausnutzung und Bekanntheit stammen von den Herstellern und fehlen, wo sie nicht geliefert werden.
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
Der Verlauf im Rückblick zeigt zwei Linien. (1) Der Pegel aus allen Bausteinen mit Archiv, je Tag aus echten Meldungen rückgerechnet (die heutigen Schwellen werden rückwirkend angewendet): KEV-Menge, Tempo bis KEV, EU-KEV, Microsoft, CERT-Bund, DShield und Ransomware über 36 Monate, NCSC-NL ab Juni 2024. An Tagen, für die eine Quelle noch kein Archiv hat, fehlt dieser Baustein; die Zahl der beteiligten Bausteine steht in der Legende. (2) Der volle Dreier-Pegel einschließlich der externen Einschätzungen, live gespeichert ab dem 25.11.2026. Für BSI Cyber Index (jährlich, von Hand) und SANS Infocon (nur Tagesstand) gibt es kein Archiv; für sie wird nichts geschätzt. Die Rückrechnung wird bei jedem Lauf neu aus den Archivdaten berechnet (`data/radar/historie/`); gespeichert wird zusätzlich der Live-Wert (`data/radar/score.json`).

### Entfallener Baustein: Feodo Tracker
Der Feodo Tracker (abuse.ch) war als Baustein „Botnetz-Server“ vorgesehen und ist entfernt. Grund: Seine Datensätze sind leer, weil Polizeiaktionen (Emotet 2021, Operation Endgame 2024) die verfolgten Botnetze zerschlagen haben; es gibt dort keine aktiven Steuerserver mehr, die man zählen könnte. Ein Baustein ohne Daten trägt nichts zum Score bei. Ein Ersatz mit Tageshistorie, ohne Konto und mit freier Nutzung für eine öffentliche Seite wird gesucht; bis dahin zählt der Score ohne ihn.

### Modell des Dreier-Pegels (versioniert, `config/modell.json`)
Der Dreier-Pegel ist modular: ein Modell, zehn Bausteine in vier Gruppen. Rechenregel: Ausschlag = Messwert im Verhältnis zur Schwelle; Gruppenwert = Mittelwert der Ausschläge der Bausteine der Gruppe (je höchstens 2,0); Pegel = Mittelwert der Gruppenwerte, auf 0 bis 100 umgerechnet; Gruppen ohne Messwert zählen nicht mit. So wiegt ein Thema nicht doppelt, weil mehrere Bausteine dazu messen. Jede Gruppe beantwortet eine eigene Frage: Ausnutzung (was wird nachweislich angegriffen?), Warnungen (wovor wird gewarnt?), Angriffsaktivität (wie viel wird angegriffen?), Externe Einschätzungen (wie schätzen andere die Lage ein?). Gruppe Ausnutzung: KEV-Menge, Tempo bis KEV, EU-KEV (neu als ausgenutzt gemeldet, 30 Tage), Microsoft (ausgenutzte Lücken im letzten Patch Day). Gruppe Warnungen: CERT-Bund (neue Warnungen kritisch und hoch, 30 Tage), NCSC-NL (neue Advisories, 30 Tage). Gruppe Angriffsaktivität: DShield (angreifende Quellen je Tag aus der Tagesübersicht des SANS Internet Storm Center, Mittel der sieben vollständigen Tage vor dem Stichtag; gezählt werden die Quell-Adressen, nicht die Meldungen, weil ihre Zahl kaum davon abhängt, wie viele Sensoren melden) und Ransomware (neue Einträge auf den Leak-Seiten von Ransomware-Gruppen in den 30 vollständigen Tagen vor dem Stichtag, Quelle RansomLook; gespeichert wird nur die Zahl je Tag, keine Namen). Gruppe Externe Einschätzungen: BSI Cyber Index, SANS Infocon.

**Schwellen:** Jede Schwelle ist das 75. Perzentil (oberes Viertel) der eigenen Historie des Bausteins, täglich gemessen über 36 Monate bis 25.11.2026 (NCSC-NL: seit Juni 2024): KEV-Menge 25, Tempo bis KEV 5 Tage, EU-KEV 26, Microsoft 3, CERT-Bund 126, NCSC-NL 43, DShield 175.000, Ransomware 855. Grundlagen stehen in `config/modell.json` und `config/regeln.json`. Das Jahr 2026 liegt bei den Warnungen deutlich über den Vorjahren (CERT-Bund etwa dreimal so viele kritische und hohe Warnungen wie 2024); die Schwellen bleiben bewusst auf 36 Monate bezogen, damit dieser Anstieg sichtbar ist. **Erstdatum:** CERT-Bund und NCSC-NL nennen bei aktualisierten Meldungen nur das Datum der Aktualisierung. Die Kennungen werden je Jahr fortlaufend vergeben; als Erstdatum einer Meldung gilt deshalb das früheste Datum unter ihr selbst und allen Meldungen mit höherer Nummer desselben Jahres. Das ist eine Obergrenze aus echten Daten, keine Schätzung von Werten. **Microsoft:** Die Kennzeichnung „ausgenutzt“ ist der Stand des Monatsberichts beim Abruf.

**Fortschreibung:** Täglich werden die Einzelwerte gespeichert (`data/radar/bausteine.json`). Ändern sich Schwellen oder Bausteine, wird der Verlauf aus den Archivdaten neu gerechnet; es gibt immer nur ein gültiges Modell.

## Begründung der Modellentscheidungen

Jede Festlegung im Dreier-Pegel ist eine Entscheidung. Hier steht, warum sie so getroffen wurde und was eine Prüfung an den Daten ergibt. Prüfzeitraum: 25.11.2023 bis 25.11.2026 (1.097 Tage), rückgerechnete Reihe aus acht Bausteinen in drei Gruppen (ohne die Gruppe Externe Einschätzungen, die kein Archiv hat), gerechnet am 25.11.2026.

| Entscheidung | Begründung | Prüfung an den Daten |
|---|---|---|
| Messwert im Verhältnis zur Schwelle (Ausschlag) | Die Bausteine haben verschiedene Einheiten (Lücken, Tage, Warnungen, Adressen, Einträge). Erst das Verhältnis zur eigenen Schwelle macht sie vergleichbar. | Jeder Baustein lag an 25 bis 33 Prozent der Tage an oder über seiner Schwelle, die Bausteine sind also gleich streng. |
| Schwelle = 75. Perzentil der eigenen Historie | „Auffällig“ heißt: höher als an drei von vier Tagen. Das Perzentil ist unempfindlich gegen einzelne Ausreißer, anders als Mittelwert plus Standardabweichung. Die Wahl von 75 ist eine Konvention, kein Naturgesetz. | Siehe oben: 25 bis 33 Prozent der Tage über der Schwelle, wie beabsichtigt. |
| Kappung des Ausschlags bei 2,0 | Ein einzelner Ausreißer soll den Pegel nicht bestimmen. | An 18 Prozent der Tage war mindestens ein Baustein gekappt. Ohne Kappung wäre der Pegel an einzelnen Tagen um bis zu 35 Punkte abgewichen. Mit Kappung bei 1,5 oder 3,0 weicht er im Mittel um rund 1 Punkt ab. |
| Gruppen, erst je Gruppe mitteln | Mehrere Bausteine, die dasselbe messen, sollen nicht mehrfach zählen. | EU-KEV und KEV-Menge korrelieren mit 0,99, CERT-Bund und NCSC-NL mit 0,72. Ohne Gruppen wiche der Pegel im Mittel um 2,0 und höchstens um 7 Punkte ab. |
| Jede Gruppe hat mindestens zwei Bausteine | Hängt eine Gruppe an einem einzigen Wert, bestimmt dieser ein Viertel des Pegels und ein Ausfall nimmt dem Pegel eine ganze Sicht. | Mit DShield allein bewegte dessen Weglassen den Pegel im Mittel um 5,4 Punkte (höchstens 25). Seit Ransomware dazukam, sind es 3,0 (höchstens 13). |
| Gruppen gleich gewichtet | Es gibt keine belastbare Grundlage, eine Frage (was wird angegriffen, wovor wird gewarnt, wie viel wird angegriffen, wie schätzen andere ein) höher zu gewichten als eine andere. Gleichgewicht ist die Annahme mit den wenigsten Voraussetzungen. | Nicht prüfbar, weil es keine unabhängige Messung der „wahren“ Lage gibt. |
| Fenster: 30 Tage für Zählungen, 7 Tage für DShield | 30 Tage glätten Wochentage und Patch-Zyklen. DShield liefert Tageswerte mit hohem Grundrauschen, 7 Tage glätten den Wochenrhythmus und reagieren trotzdem zügig. | DShield: Median 153.956, 75. Perzentil 175.109 im 7-Tage-Mittel. |
| DShield zählt Quellen, nicht Meldungen | Die Zahl der Meldungen hängt davon ab, wie viele Sensoren gerade melden (zwischen rund 1.100 und 3.900 Ziele je Halbjahr). Die Zahl der angreifenden Adressen ist davon weitgehend unabhängig. | Halbjahres-Mediane der Quellen zwischen 135.000 und 171.000, ohne Sprung beim Wechsel der Sensorzahl. |
| Ransomware neben DShield in einer Gruppe | Beide messen Angriffe, aber Verschiedenes: DShield Versuche (wer klopft an), Ransomware Folgen (wer wurde getroffen). | Die beiden Reihen laufen nicht gleich (Korrelation −0,25), sie ergänzen sich also und doppeln sich nicht. |
| Stufengrenzen 35, 50, 64, 80 | 50 heißt: Schwellen im Schnitt erreicht. 64 trennt die obersten rund 8 Prozent der Tage ab, unter 35 liegt das ruhigste Fünftel. 80 ist für Ausnahmen reserviert. | Spanne der Reihe 22 bis 73; 80 wurde nie erreicht. Verteilung: ruhig 21 %, unauffällig 58 %, angespannt 13 %, hoch 8 %. |

**Empfindlichkeit: Was passiert, wenn ein Baustein fehlt?** Jeder Baustein wurde einmal weggelassen und der Pegel neu gerechnet.

| Ohne | Korrelation mit dem vollen Pegel | Mittlere Abweichung (Punkte) | Größte Abweichung | Gleiche Stufe an |
|---|---|---|---|---|
| KEV-Menge | 0,99 | 1,0 | 4 | 92 % der Tage |
| EU-KEV | 0,99 | 1,0 | 4 | 92 % |
| Tempo bis KEV | 0,98 | 1,6 | 8 | 86 % |
| NCSC-NL | 0,98 | 1,9 | 8 | 82 % |
| Microsoft | 0,97 | 2,1 | 6 | 81 % |
| CERT-Bund | 0,96 | 2,2 | 8 | 86 % |
| DShield | 0,95 | 3,0 | 13 | 78 % |
| Ransomware | 0,92 | 3,0 | 13 | 80 % |

Ergebnis: Kein einzelner Baustein bestimmt den Pegel. Lässt man einen weg, ändert er sich im Mittel um 1 bis 3 Punkte und bleibt an 78 bis 92 Prozent der Tage in derselben Stufe. Am stärksten wirken die beiden Bausteine der Angriffsaktivität, weil ihre Gruppe nur zwei Bausteine hat.

**Prüfung außerhalb der Stichprobe.** Dass jeder Baustein an rund einem Viertel der Tage über seiner Schwelle liegt, folgt aus der Definition der Schwelle. Aussagekräftiger ist ein Test mit getrennten Zeiträumen: Schwellen nur aus den ersten zwei Jahren ableiten (25.11.2023 bis 24.11.2025), dann am dritten Jahr prüfen (25.11.2025 bis 25.11.2026, 366 Tage). Gerechnet am 25.11.2026.

| Baustein | Schwelle aus 2 Jahren | Schwelle aus 3 Jahren (gültig) | Tage über der Schwelle im Lernzeitraum | im Testjahr |
|---|---|---|---|---|
| Ransomware | 671 | 855 | 25 % | 99 % |
| CERT-Bund | 91 | 126 | 26 % | 92 % |
| KEV-Menge | 21 | 25 | 28 % | 75 % |
| EU-KEV | 21,5 | 26 | 25 % | 72 % |
| NCSC-NL (Lernzeitraum ab Juni 2024) | 40 | 43 | 27 % | 58 % |
| Tempo bis KEV | 5 Tage | 5 Tage | 30 % | 40 % |
| Microsoft | 3 | 3 | 37 % | 23 % |
| DShield | 179.172 | 175.000 | 25 % | 14 % |

Ergebnis: (1) Die Form des Pegels ist stabil. Mit den Schwellen aus zwei Jahren verläuft er im Testjahr fast gleich wie mit den gültigen (Korrelation 0,99). (2) Das Niveau ist es nicht. Mit den älteren Schwellen läge der Pegel im Testjahr im Mittel 7 Punkte höher (Median 56 statt 48,5) und nur an 51 Prozent der Tage in derselben Stufe. (3) Der Grund ist ein Niveausprung im Jahr 2026 bei allem, was Lücken, Warnungen und Ransomware-Einträge zählt: Ransomware lag an 99, CERT-Bund an 92 Prozent der Tage über der Schwelle der Vorjahre. Bei Ransomware kommt hinzu, dass die Quelle mit der Zeit mehr Gruppen beobachtet. Angriffsversuche (DShield) und Microsoft zeigen den Sprung nicht. (4) Folgerung: Der Pegel misst Abweichung von einem Bezugszeitraum, und das Ergebnis hängt davon ab, welcher Zeitraum das ist. Die Schwellen werden deshalb nicht laufend nachgezogen, sondern bleiben fest und werden zu den Terminen im Prüfkalender überprüft; jede Änderung steht mit Datum in diesen Regeln.

**Verlässlichkeit der Quellen.** Ein Baustein nützt nur, wenn seine Quelle über Jahre liefert. Neun der zehn Bausteine kommen aus sechs Quellen, die Behörden oder Hersteller sind (CISA, ENISA, Microsoft, BSI mit CERT-Bund, NCSC-NL) oder ein seit über zwanzig Jahren betriebenes Institut (SANS ISC mit DShield und Infocon). Der zehnte, Ransomware, kommt von RansomLook, einem ehrenamtlich betriebenen offenen Projekt, und hat damit das höchste Ausfallrisiko. Zwei weitere Abhängigkeiten sind zu beachten: Der BSI Cyber Index erscheint nur jährlich und wird von Hand eingetragen; und je zwei Bausteine hängen an derselben Quelle (KEV-Menge und Tempo bis KEV an der CISA, DShield und Infocon am SANS ISC), ein Ausfall dort träfe also zwei Bausteine zugleich. Fällt eine Quelle aus, zählt ihr Baustein nicht mit, die Zahl der beteiligten Bausteine steht am Pegel, und die Gruppe wird aus den übrigen gebildet. Das Modell selbst muss dafür nicht geändert werden. Bleibt eine Quelle dauerhaft weg, wird der Baustein mit Datum und Begründung in diesen Regeln gestrichen (wie Feodo Tracker).

**Grenzen des Modells.** (1) Es gibt keine unabhängige Messung der tatsächlichen Bedrohung, an der sich der Pegel eichen ließe; geprüft werden kann nur seine innere Stimmigkeit. (2) Sechs von zehn Bausteinen zählen Meldungen und Warnungen, zwei messen Angriffsaktivität, zwei sind Einschätzungen. (3) Die Schwellen beziehen sich auf 36 Monate; steigt das Niveau dauerhaft, steht der Pegel länger im oberen Bereich. (4) BSI Cyber Index und SANS Infocon haben kein Tagesarchiv und fehlen in der rückgerechneten Reihe. (5) Erstdaten bei CERT-Bund und NCSC-NL sind aus der fortlaufenden Kennung abgeleitet. (6) Die Zeitreihen sind nicht stationär (siehe Prüfung außerhalb der Stichprobe): Die Stufe hängt vom gewählten Bezugszeitraum ab. (7) Ransomware-Einträge sind Behauptungen der Täter, keine bestätigten Vorfälle, und ihre Zahl hängt auch davon ab, wie viele Gruppen die Quelle beobachtet. (8) Der Programmcode ist nicht veröffentlicht; nachrechnen lässt sich der Pegel aus diesen Regeln und den offenen Rohdaten.

## Bereiche: Angegriffenes nach Zuständigkeit (seit 25.11.2026, vorläufig)

**Zweck.** Wer nur einen Teil der IT betreut, soll sehen, was in seinem Teil nachweislich angegriffen wird. Grundlage sind allein die KEV-Einträge der letzten 30 Tage; es kommt keine neue Quelle dazu.

**Regel.** Jeder Eintrag bekommt genau einen Bereich, nach Hersteller und Produkt, über feste Suchmuster in `config/bereiche.json`. Die Muster werden in dieser Reihenfolge geprüft, das erste passende gilt: E-Mail und Zusammenarbeit; Fernwartung, Verwaltung und Dateitransfer; Netzwerk, Randgeräte und Industrie; Entwicklung, DevOps und KI-Werkzeuge; Arbeitsplatz; Windows und Microsoft; Unternehmens-Anwendungen; Linux, Webserver und Open Source. Passt keines, steht der Eintrag unter „Sonstige“. Die Reihenfolge entscheidet Zweifelsfälle: Die genauen Produktbereiche stehen vor den Herstellern. Exchange und SharePoint sind Zusammenarbeit (nicht Windows), Cisco Unified Communications ist Zusammenarbeit und Ivanti Endpoint Manager Fernwartung (nicht Netzwerk), Cisco IOS ist Netzwerk (nicht Arbeitsplatz wegen „ios“), Office und Acrobat sind Arbeitsplatz, ColdFusion und Adobe Commerce Unternehmens-Anwendungen.

**Prüfung der Zuordnung (25.11.2026).** An den 333 KEV-Einträgen der letzten 365 Tage: Zusammenarbeit 39, Fernwartung 31, Netzwerk 88, Entwicklung 39, Arbeitsplatz 36, Windows 27, Anwendungen 28, Linux 43, Sonstige 2. Die Muster wurden an genau diesen Einträgen geschärft; die niedrige Restzahl gilt deshalb für die Vergangenheit, nicht als Zusage für künftige Hersteller.

**Grenzen.** (1) Reine Zuordnung nach Namen, keine Aussage darüber, was bei wem im Einsatz ist. (2) Ein leerer Bereich heißt nur: In 30 Tagen kam dort nichts neu in den KEV; zu patchen gibt es trotzdem. (3) „Sonstige“ ist kein Fehler, sondern ehrlich: Dort steht, was die Muster noch nicht kennen. Neue Hersteller werden nachgetragen. (4) Die Zuordnung ändert weder Pegel noch die Reihenfolge unter „Diese Woche zuerst“.

**Hersteller-Quellen je Bereich (seit 25.11.2026).** Zusätzlich zu den KEV-Einträgen zeigt jeder Bereich die Meldungen der Hersteller, für die es eine offene Quelle ohne Konto gibt: Netzwerk (Cisco, Fortinet, Palo Alto Networks, Ivanti), Arbeitsplatz (Mozilla für Firefox und Thunderbird, Apple), Unternehmens-Anwendungen (SAP), Fernwartung (Ivanti), Linux (Ubuntu, Debian, Red Hat, SUSE, AlmaLinux, Rocky Linux, Amazon Linux), Windows und Zusammenarbeit (Microsoft Patch Day). Gezählt wird wie bei den übrigen Quellen: Meldungen der letzten 7 und 30 Tage, Schweregrad nur, wenn der Hersteller ihn im Feed nennt. Ivanti fasst seine Lücken in einer Monatsmeldung zusammen, Apple nennt in der Übersicht keine CVEs; die Zahlen dieser beiden sind deshalb klein und nicht mit den anderen vergleichbar. Jede neue Quelle wird vor der Aufnahme mit dem Prüflauf `quellen-test` abgerufen. Nicht aufgenommen: Oracle (Feed antwortet dem Lauf mit 403), Citrix (Feed liefert kein gültiges XML), Adobe (Hinweise nur noch im Trust Center, ohne abrufbare Liste), VMware/Broadcom (noch nicht geprüft); alle geprüft am 25.11.2026. Für Adobe, Oracle und Citrix steht der Patch-Tag im Kalender. Fehlt eine Quelle, heißt das nicht, dass dort nichts zu patchen ist.

**Patch-Tage im Kalender.** Zweiter Dienstag im Monat: Microsoft, Adobe, SAP, Fortinet, Ivanti, Citrix (jeweils nach eigener Angabe des Herstellers). Dritter Dienstag: Oracle. Außerplanmäßige Meldungen sind jederzeit möglich.

## Lebenszyklen (/lebenszyklen, seit 26.11.2026)

Die Rubrik zeigt, bis wann Hersteller ein System mit Sicherheitsupdates versorgen. Sie hat keinen Einfluss auf den Dreier-Pegel. Quelle: endoflife.date (offene Daten, Herstellerangaben), abgerufen im Datenlauf (`data/patches/lifecycle.json`, Stand je Abruf auf der Seite). Produkte: Windows, Windows Server, Ubuntu, Debian, Red Hat Enterprise Linux, SUSE Linux Enterprise Server, AlmaLinux, Rocky Linux, Amazon Linux, Apple macOS, Cisco IOS XE, Fortinet FortiOS, Palo Alto PAN-OS, Mozilla Firefox (nur ESR). Ohne Quelle bei endoflife.date und deshalb nicht geführt: Ivanti, SAP, Microsoft Edge. Es wird nichts geschätzt; nennt die Quelle kein Datum, steht „noch kein Datum genannt“.

Farbe nach Restzeit bis zum Support-Ende (Tage ab heute): schon vorbei = rot („beendet“); vorbei, aber erweiterter Support (ESU, ESM) läuft noch = blau; bis 182 Tage = gelb; bis 365 Tage = hell gelb; darüber = grün. Windows 10 und 11 werden für Enterprise/Education, Pro und LTSC geführt, Home und IoT nicht. Einträge, deren Support vor mehr als 400 Tagen endete, fallen heraus. Das Board im Seitenkopf nennt die nächsten Support-Enden der Betriebssysteme innerhalb von 120 Tagen.

## Linkseite (/links, seit 26.11.2026)

Die Seite sammelt von Hand ausgewählte Angebote zu Lage, Schwachstellen und Angriffsdaten (`data/links.json`). Sie hat keinen Einfluss auf den Dreier-Pegel, auf Schwellen oder Stufen. Aufnahme nur nach Einzelprüfung: erreichbar, Betreiber erkennbar, Aktualität sichtbar; Pflegeart (amtlich, automatisch, von Hand) und Prüfdatum stehen am Eintrag. Angebote, die in den Pegel einfließen, sind als „im Dreier-Pegel“ markiert. Keine bezahlten oder vermittelten Links, keine Abfrageteile oder Tracking in den Adressen. Von Hand gepflegte Fallsammlungen (etwa zu Kommunen) sind Einordnung und werden nicht in Werte übernommen. Der Prüfkalender prüft die Erreichbarkeit; die Frist je Eintrag beträgt 180 Tage.

## Logbuch

Das Logbuch (`data/logbuch.json`, auf der Seite unter „logbuch“) hält fest, was sich aus den Daten ergeben hat. Einträge werden nicht nachträglich geändert oder gelöscht, auch wenn sich die Lage ändert; Korrekturen stehen als neuer Eintrag. Drei Arten: **Erkenntnis** (von Hand geschrieben, jede mit Belegen aus den Daten oder aus diesen Regeln), **Ereignis** (schreibt der Datenlauf selbst: jeder Stufenwechsel des gespeicherten Tagesstands, mit altem und neuem Wert; ein neuer Höchststand der gespeicherten Tagesstände, erst ab 30 Tagen Reihe und höchstens einmal in sieben Tagen; ein Baustein ohne Wert, je Baustein höchstens einmal in sieben Tagen) und **Modell** (Änderungen an Bausteinen, Schwellen oder Stufen, mit Verweis auf diese Regeln). Aus dem Logbuch und den Jahresdaten entsteht der Jahresbericht.

**Stufe ohne Trägheit (Entscheidung Steve, 25.11.2026).** Die Stufe folgt dem Pegel des Tages ohne Verzögerung und ohne Puffer: 63 ist „angespannt“, 64 ist „hoch“. Pendelt der Pegel um eine Grenze, wechselt die Stufe mit, und das Logbuch hält jeden Wechsel fest. Eine Regel, die Wechsel verzögert, wurde geprüft und verworfen: Sie würde die Stufe vom Wert lösen.

## Berichte je Monat, Quartal und Jahr

Für jeden abgeschlossenen Monat, jedes abgeschlossene Quartal und Jahr rechnet der Datenlauf einen Bericht (`site/data/berichte.json`, auf der Seite unter „berichte“, dazu je Bericht eine eigene Seite ohne eigenes Skript (einzige Ausnahme auf allen Unterseiten: das abschaltbare, rein optische Matrix-Modul `matrix.js`, standardmäßig aus, siehe QS): `/bericht/2026-10/`, `/bericht/2026-Q3/`, `/bericht/2025/`, englisch unter `/en/bericht/…`, Übersicht unter `/bericht/`). Der laufende Zeitraum bekommt keinen Bericht. Alle Zahlen stammen aus der Tagesreihe des Pegels, nichts wird geschätzt:

- **Grundlage.** Vor dem ersten gespeicherten Tagesstand (25.11.2026) ist der Tageswert aus den Archivdaten zurückgerechnet (acht Bausteine, ohne die Gruppe Externe Einschätzungen, für die es kein Archiv gibt); ab dann zählt der gespeicherte Tagesstand aller Bausteine. Jeder Bericht nennt, worauf er beruht. Ein Zeitraum bekommt nur einen Bericht, wenn für mindestens 90 % seiner Tage ein Wert vorliegt.
- **Kennzahlen.** Mittel der Tageswerte (eine Nachkommastelle), Stufe des gerundeten Mittels, Höchst- und Tiefststand mit Datum (bei gleichem Wert der spätere Tag), Zahl der Stufenwechsel von Tag zu Tag, Tage je Stufe, Veränderung des Mittels zum unmittelbar vorangehenden Zeitraum gleicher Art.
- **Bausteine.** Je Baustein das Mittel des Ausschlags (Messwert im Verhältnis zur Schwelle, wie im Pegel höchstens 2,0), der Anteil der Tage an oder über der Schwelle und die Veränderung zum vorangehenden Zeitraum. Ein Baustein erscheint nur, wenn er für mindestens 90 % der Tage einen Wert hat.
- **Text.** Der Satz zum Kopieren wird nach festem Muster aus diesen Zahlen gebildet, ohne Wertung.
- **Stand der Schwellen.** Berichte werden bei jedem Lauf mit dem heutigen Modell neu gerechnet. Ändern sich Schwellen oder Bausteine, ändern sich auch die Zahlen früherer Zeiträume; die Änderung steht dann als Modell-Eintrag im Logbuch.

## Code-Audit (Entwurf 0.1, seit 27.11.2026)

Eigenes Siegel („Dreier-Code-Siegel“), eigener Score, getrennt vom Web-Audit. Regeln: `codeaudit/regeln.json`, Erklärung: `codeaudit/REGELN.md`. Sieben Gruppen, Gewichte 20/18/12/14/12/14/10, Skala, Stufen und Mindestabdeckung wie beim Web-Audit, Deckel 59 schon bei einer nicht bestandenen Prüfung in Geheimnisse oder Workflows. Noch nichts gemessen, nichts auf der Seite; Werkzeuge und Prüfpunkte sind vor Version 1.0 zu belegen (Stand, Lizenz). Einzelbefunde nur privat.
Schwellen Entwurf 0.1 (27.11.2026): Testabdeckung ab 80 % bestanden, ab 60 % Hinweis; Funktionen bis Komplexität 30; Dateien bis 1500 Zeilen ohne Hinweis. Einzelheiten: `codeaudit/REGELN.md`.
Das Dreier-Code-Siegel steht auf `/audit` (Abschnitt „Code-Audit“) und im Fuß der Startseite; solange die Regeln ein Entwurf sind, trägt es „ENTWURF 0.1“ statt „REGELN x“.

## Nachtrag: Bereich Citrix, Virtualisierung und Terminalserver (27.11.2026)

Neunter Bereich bei „Angegriffenes nach Zuständigkeit“, geprüft vor Netzwerk und Unternehmens-Anwendungen: Citrix einschließlich NetScaler, VMware (ESX, vCenter, Horizon, Tools), Microsoft Remote Desktop Services und Parallels RAS. Citrix und NetScaler standen vorher unter Netzwerk, VMware unter Unternehmens-Anwendungen, Remote Desktop Services unter Windows. VMware Spring und Tanzu bleiben bei den Anwendungen, VMware SD-WAN bleibt außerhalb, weil das keine Virtualisierung ist. Neu geprüft an den 342 KEV-Einträgen der letzten 365 Tage (Stand 27.11.2026): Zusammenarbeit 44, Fernwartung 31, Citrix/Virtualisierung 11, Netzwerk 82, Entwicklung 39, Arbeitsplatz 36, Windows 27, Anwendungen 23, Linux 43, Sonstige 6. Für Citrix gibt es keine offene Quelle der Meldungen des Herstellers, die sich ohne Konto abrufen lässt (der Feed lieferte dem Abruf am 25.11.2026 kein gültiges XML); angezeigt werden deshalb die angegriffenen Lücken aus dem KEV und der Patch-Tag im Kalender. Lebenszyklen: neu Citrix Virtual Apps and Desktops sowie VMware ESXi, Horizon und vCenter Server (endoflife.date); für Citrix NetScaler gibt es dort keinen Eintrag, das steht auf der Seite offen so.

## Nachtrag: Code-Audit Version 1.0 (27.11.2026)

Die Regeln des Code-Audits sind von „0.1-entwurf“ auf **1.0** festgeschrieben: sieben Gruppen, Gewichte 20/18/12/14/12/14/10, Stufen 95/80/60, Mindestabdeckung 90 %, Deckel 59 bei einem Fund in Geheimnisse oder Workflows, Schwellen unverändert (Testabdeckung 80 %/60 %, Komplexität bis 30, Dateien bis 1500 Zeilen). Das Dreier-Code-Siegel trägt damit „REGELN 1.0“ statt „ENTWURF 0.1“, der Entwurfshinweis auf `/audit` entfällt. Ab jetzt ändern sich Schwellen, Gruppen und Gewichte nur mit neuer Version und eigenem Eintrag hier.

## Nachtrag: Namen der Siegel (27.11.2026)

Das Siegel des Web-Audits heißt jetzt **Dreier-Web-Siegel** (bisher „Dreier-Siegel“), das des Code-Audits **Dreier-Code-Siegel**. „Dreier-Siegel“ ist der Familienname beider. Geändert wurden nur Name und Stempeltext (oben im Siegel: DREIER-WEB-SIEGEL); Prüfpunkte, Gewichte, Schwellen, Stufen und Regelversion bleiben unverändert (Web-Audit 1.0, Code-Audit 1.0). Ältere Einträge in dieser Datei sprechen noch vom „Dreier-Siegel“ und meinen das Web-Siegel.
