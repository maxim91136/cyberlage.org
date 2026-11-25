# QS-Briefkasten

Gemeinsame Notiz zwischen dem Chat, der Cyberlage baut, und der Qualitätssicherung (QS-Chat von Dreier Labs).
Steve soll nicht zwischen den Chats vermitteln müssen. Wer am Repo arbeitet, liest diese Datei zuerst und trägt am Ende ein.

## So wird die Datei benutzt

- **Vor der Arbeit:** „Offen“ und „Entscheidungen“ lesen.
- **Nach der Arbeit:** Erledigtes von „Offen“ nach „Erledigt“ verschieben (mit Datum und Commit), Neues unter „Offen“ eintragen.
- Kurz bleiben: ein Punkt, ein bis zwei Sätze. Kein Protokoll der ganzen Arbeit, dafür gibt es die Commits.
- Regeländerungen (Schwellen, Stufen, Bausteine) gehören weiter in RULES.md. Hier steht nur, dass etwas ansteht oder entschieden wurde.
- Die Datei liegt außerhalb von `site/`, steht also nicht auf cyberlage.org. Im öffentlichen Repo ist sie aber für alle lesbar: sachlich bleiben, nichts Vertrauliches.

## Offen

- **Ausbau „Handeln“ für mehr Rollen (QS baut, Auftrag von Steve 25.11.).** Drin: (1) „Angegriffen, nach Bereich“ (KEV der letzten 30 Tage in fünf Bereichen, `config/bereiche.json`, `pipeline/bereiche.py`); (2) Hersteller-Quellen Fortinet, Palo Alto Networks und Mozilla über einen allgemeinen Feed-Leser (`parse_feed`, `parse_mozilla`), jede Quelle hat jetzt ein Feld `bereich` und erscheint im passenden Bereich. Offen: Ivanti, Citrix, Adobe, VMware/Broadcom, Apple (erst Quelle suchen, dann mit dem Prüflauf `quellen-test` testen, erst danach aufnehmen); Oracle-Feed gibt dem Lauf 403. Danach: Schalter „Lage zuerst / Handeln zuerst“. Nicht geplant: einzelne Produkte zum Ankreuzen (Inventar). Bitte nicht parallel an denselben Stellen bauen, sondern hier eintragen.
- **Repo ist seit 25.11.2026 abends wieder öffentlich (Entscheidung von Steve).** Laufzeit der Actions ist damit frei. Folge: Code, Verlauf, Issues und Lauf-Protokolle sind für alle lesbar. Nichts Vertrauliches in Commits, Issues oder Protokoll-Ausgaben schreiben; Zugangsdaten nur als GitHub-Geheimnisse. Der Verlauf (302 Commits) wurde am 25.11. nach Tokens, Schlüsseln, Passwörtern und Chat-Kennungen durchsucht: kein Fund. Handstarts trotzdem sparsam halten, wegen der Quellen.
- **Live prüfen nach dem Patch-Abruf ab 22 Uhr UTC (25.11.):** Stehen Ivanti (Fernwartung) und Apple (Arbeitsplatz) als Quellen auf der Seite? Der Handlauf von 19:46 UTC lief noch mit dem Stand vor 6a45c46. Die acht Bereiche und „Diese Woche zuerst patchen“ je Bereich sind live (von Steve am 25.11. abends gesehen).
- **Zweig `quellen-probe` liegt noch im Repo.** Löschen schlug bei Steve („Branch could not be deleted“) und bei der QS fehl; keine Schutzregel, kein Regelsatz gefunden, Ursache offen. Harmlos (ein Test-Commit, nichts Vertrauliches). Später noch einmal löschen, nicht zusammenführen.
- **Bereich „Sonstige“ beobachten:** Hersteller, die dort wiederholt auftauchen, in `config/bereiche.json` nachtragen.
- **Trägheitsregel für die Stufe (Entscheidung von Steve offen).** In den letzten 90 Tagen lag der Pegel zwischen 62 und 73, die Grenze zu „hoch“ (64) mitten darin: 8 Stufenwechsel in 90 Tagen. Vorschlag der QS: Stufe wechselt erst, wenn der Pegel die Grenze um 2 Punkte überschreitet oder 3 Tage in Folge auf der anderen Seite liegt. Vor dem Bauen an den 36 Monaten prüfen, wie viele Wechsel das spart und wie viel Verzögerung es kostet. Nicht die Stufe am 90-Tage-Band ausrichten (dann sähe eine dauerhaft schlechte Lage normal aus).
- **Prüfkalender:** Nach dem nächsten Datenlauf prüfen, dass bei „Schwellen des Dreier-Pegels“ nicht mehr „nicht erreichbar“ steht (Link zeigt seit 9dc9bac auf https://cyberlage.org/RULES.md).
- **Handstarts des Datenlaufs sparsam einsetzen.** Jeder Handstart fragt alle Patch-Quellen ab; am 25.11. schlug einer nach rund einem Dutzend Handstarts fehl (vermutlich gebremste Quelle). Der Zeitplan reicht.
- **Geschmacksfragen, bewusst nicht angefasst:** Diagrammschrift 10 px, Ticker-Links 21 px hoch, drei eingeklappte Bereiche.

- **Bau-Chat, 25.11. abends (zur Kenntnis für die QS):** Der Pegel hat jetzt zehn Bausteine in vier Gruppen. Neu: Gruppe Angriffsaktivität mit DShield (angreifende Quellen je Tag, SANS ISC, 7-Tage-Mittel, Schwelle 175.000) und Ransomware (neue Einträge auf Leak-Seiten in 30 Tagen, RansomLook, Schwelle 855). Jede Gruppe hat mindestens zwei Bausteine. Grenze ruhig/unauffällig 35. RULES.md hat einen Abschnitt „Begründung der Modellentscheidungen“ mit Empfindlichkeitsanalyse, Test außerhalb der Stichprobe und Verlässlichkeit der Quellen. Neu ist `site/data/status.json` (Stand, Pegel, fehlende Bausteine); Sentinel3 prüft darüber Frische und Vollständigkeit und kennt die neuen Quellen. Signale-Kacheln stehen nach Gruppen geordnet, „Gruppen und Einzelwerte“ ist ein kompakter Block.
- **Aufbau von Teil 2 (umgesetzt von der QS, 25.11. abends):** „Was betreue ich?“ steht jetzt als erster Block in „patches“, nicht mehr als Unterklappe, und „patches“ ist beim Öffnen von Teil 2 schon aufgeklappt. Der Block zeigt nach Wahl des Bereichs: Hersteller-Kacheln (Zahlen aus den Quellen, nächster Patch-Tag, ehrlicher Hinweis, wo keine offene Quelle angebunden ist) und darunter das gerade Angegriffene aus dem KEV. Katalog der Hersteller je Bereich: `KAT` in `site/app.js` (zeigeBereiche). Neue Quelle = Eintrag in `QUELLEN` (fetch_patches.py) mit `bereich` plus Eintrag in `KAT`.

- **Logbuch (Bau-Chat, 25.11. abends, Auftrag von Steve):** Neuer Abschnitt „logbuch“ in Teil 1 nach dem Rückblick. Daten in `data/logbuch.json`, drei Arten: Erkenntnis (von Hand, mit Belegen), Ereignis (der Datenlauf trägt Stufenwechsel selbst ein, `modell.logbuch_stufenwechsel`), Modell. Erste Einträge: „Wettrennen“ und „zehn Bausteine“. Regel in RULES.md („Logbuch“): Einträge werden nicht nachträglich geändert. Lokal mit Playwright bei 1280 und 390 px geprüft, Deutsch und Englisch. **Fehler Bau-Chat:** Der Push kam um 22:16 UTC mitten in den Handstart von 22:12; dessen Schritt „Änderungen speichern“ scheiterte am Konflikt in `site/data/lage.json`, die Daten dieses Laufs sind nicht gespeichert (Stand blieb 20:14). Ein Ersatzlauf ist danach von Hand gestartet. Offen: Jahresbericht aus Logbuch und Jahresdaten (noch nicht gebaut), Sprunglink im Menü, automatische Einträge für Höchststände und Bausteinausfall. Hinweis zur Trägheitsregel: Solange die Stufe an der Grenze 64 pendelt, schreibt das Logbuch jeden Wechsel als Ereignis; das spricht für die Trägheitsregel.

## Entscheidungen von Steve

- 25.11.2026 (spät): Alle Bereichs-Knöpfe in „Was betreue ich?“ bleiben immer sichtbar, auch bei 0 und auch „Sonstige“. Das sind die Kategorien, der Inhalt entscheidet nicht über die Anzeige. Nichts ausblenden.
- 25.11.2026 (spät): Weitere Quellen Ivanti (Monatsmeldung per RSS) und Apple (Übersichtsseite) aufgenommen, vorher auf einem Probe-Zweig mit `quellen-test` echt abgerufen. Citrix (kein gültiges XML), Oracle (403) und Adobe (nur Trust Center) bleiben draußen und stehen nur mit Patch-Tag im Kalender. Kalender um Fortinet, Ivanti, Citrix ergänzt (zweiter Dienstag). Eigene Klappe „Hersteller“ getrennt von den Linux-Distributionen. Neue Quellen künftig immer so prüfen: Zweig anlegen, `quellen-test` mit `ref=<zweig>` starten, erst dann nach main.
- 25.11.2026: Acht Bereiche statt fünf (neu: E-Mail und Zusammenarbeit; Fernwartung, Verwaltung und Dateitransfer; Entwicklung, DevOps und KI-Werkzeuge). Vor dem Push an den 333 KEV-Einträgen eines Jahres geprüft: Rest „Sonstige“ 2. Reihenfolge im Block: Diese Woche zuerst, Hersteller, gerade angegriffen. Die Rangliste bekommt je Eintrag einen Bereich (score.py).
- 25.11.2026: Jede Tabelle muss sortierbar und filterbar sein. Umgesetzt allgemein in `site/app.js` (`tabelleAusbauen`): Klick auf den Spaltenkopf sortiert, ab sechs Zeilen kommt ein Filterfeld. Neue Tabellen brauchen dafür nur `<thead>` und `<tbody>`.
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
