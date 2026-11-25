# QS-Briefkasten

Gemeinsame Notiz zwischen dem Chat, der Cyberlage baut, und der Qualitätssicherung (QS-Chat von Dreier Labs).
Steve soll nicht zwischen den Chats vermitteln müssen. Wer am Repo arbeitet, liest diese Datei zuerst und trägt am Ende ein.

## So wird die Datei benutzt

- **Vor der Arbeit:** „Offen“ und „Entscheidungen“ lesen.
- **Nach der Arbeit:** Erledigtes von „Offen“ nach „Erledigt“ verschieben (mit Datum und Commit), Neues unter „Offen“ eintragen.
- Kurz bleiben: ein Punkt, ein bis zwei Sätze. Kein Protokoll der ganzen Arbeit, dafür gibt es die Commits.
- Regeländerungen (Schwellen, Stufen, Bausteine) gehören weiter in RULES.md. Hier steht nur, dass etwas ansteht oder entschieden wurde.
- Die Datei liegt außerhalb von `site/` und wird nicht veröffentlicht.

## Offen

- **Ausbau „Handeln“ für mehr Rollen (läuft, QS baut, Auftrag von Steve 25.11.).** Schritt 1 ist drin: „Angegriffen, nach Bereich“ (KEV der letzten 30 Tage in fünf Bereichen, `config/bereiche.json`, `pipeline/bereiche.py`). Geplant, in dieser Reihenfolge: (2) Netzwerk-Hersteller als eigene Quellen (Fortinet, Ivanti, Citrix, Palo Alto), nur wo es eine offene, stabile Quelle gibt; (3) Arbeitsplatz und Anwendungen (Firefox, Adobe, Oracle, VMware); (4) Schalter „Lage zuerst / Handeln zuerst“. Nicht geplant: einzelne Produkte zum Ankreuzen (Inventar). Bitte nicht parallel an denselben Stellen bauen, sondern hier eintragen.
- **Bereich „Sonstige“ beobachten:** Hersteller, die dort wiederholt auftauchen, in `config/bereiche.json` nachtragen.
- **Trägheitsregel für die Stufe (Entscheidung von Steve offen).** In den letzten 90 Tagen lag der Pegel zwischen 62 und 73, die Grenze zu „hoch“ (64) mitten darin: 8 Stufenwechsel in 90 Tagen. Vorschlag der QS: Stufe wechselt erst, wenn der Pegel die Grenze um 2 Punkte überschreitet oder 3 Tage in Folge auf der anderen Seite liegt. Vor dem Bauen an den 36 Monaten prüfen, wie viele Wechsel das spart und wie viel Verzögerung es kostet. Nicht die Stufe am 90-Tage-Band ausrichten (dann sähe eine dauerhaft schlechte Lage normal aus).
- **Prüfkalender:** Nach dem nächsten Datenlauf prüfen, dass bei „Schwellen des Dreier-Pegels“ nicht mehr „nicht erreichbar“ steht (Link zeigt seit 9dc9bac auf https://cyberlage.org/RULES.md).
- **Handstarts des Datenlaufs sparsam einsetzen.** Jeder Handstart fragt alle Patch-Quellen ab; am 25.11. schlug einer nach rund einem Dutzend Handstarts fehl (vermutlich gebremste Quelle). Der Zeitplan reicht.
- **Geschmacksfragen, bewusst nicht angefasst:** Diagrammschrift 10 px, Ticker-Links 21 px hoch, drei eingeklappte Bereiche.

## Entscheidungen von Steve

- 25.11.2026: Die Patch-Seite soll mehr Rollen bedienen (Admins, Netzwerk, Anwendungsverantwortliche, SOC). Priorisierung macht die QS; gebaut wird nur, was echten Mehrwert hat. Zwei Sichten (Lage/Handeln) statt freier Anpassung.
- 25.11.2026: Radar und Bausteine-Vergleich stehen oben und offen. Am Radar selbst nichts ändern. Schwenk: eine Minute je Umlauf.
- 25.11.2026: Kopfbereich zentriert, Blue-Team-Abzeichen unter dem Pegel-Kasten.
- 25.11.2026: „Experiment“ steht nicht mehr im Kopf.
- 25.11.2026: Externe Links öffnen in einem neuen Tab.
- 25.11.2026: Der Radar ist der Dreier-Pegel (ein Modell, ein Score).

## Geprüft und verworfen

- „Der Pegel bewegt sich kaum“ (Fremdkritik): stimmt nur für die letzten 90 Tage. Über 36 Monate liegt er zwischen 22 und 73, Median 40. Kritik am Pegel immer gegen den 3-Jahres-Verlauf im Rückblick prüfen.
- Zweiter Score neben dem 90-Tage-Verlauf („zuletzt 69“): entfernt, weil die rückgerechnete Reihe ohne BSI Cyber Index und SANS rechnet und dem Wert oben widersprach.

## Erledigt (QS, 25.11.2026)

- Menü /abo öffnete am linken Rand (548bb72).
- Diagramm-Achse „00 %“, doppelt gezeichneter KEV-Verlauf, englische Monatskürzel auf der deutschen Seite, EPSS auf 100 % gerundet, Sitemap mit Feed (b054634).
- Vorschaubild og.png, Red-Hat-Titel ohne „@sha256“, Radar-Beschriftung frei (1a1128f).
- Skala unter dem Pegel zeigte fest „30“ statt der gültigen Grenze 35 (1940f7b).
- Fazit: Patch-Einträge mit Produktname und Grund-Etikett (e4dab85).
- Externe Links im selben Tab, Prüfkalender-Links auf privates Repo, deutsche Reste auf der englischen Seite (9dc9bac).

## Wie die QS prüft

Lokal mit Playwright (1280 px und 390 px, Deutsch und Englisch, alle Klappen offen) und live über Chrome. Geprüft werden: Skriptfehler, seitliches Scrollen, tote Sprunglinks, leere Elemente, „undefined/NaN“, Sprachreste, Stand der Daten. Nicht geprüft wird die inhaltliche Richtigkeit der Quelldaten.
