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

### Für Steve, 26.11. (Warteliste aus der Nacht, Bau-Chat)
- **Web-Check-Scan (26.11.)**: Kopfzeilen, TLS, Mail (SPF/DMARC), keine Tracker bestätigt. DNSSEC von Steve bei Cloudflare aktiviert (26.11.); Wirkung später mit neuem Scan prüfen (DS-Eintrag gefunden?). Erledigt: `site/.well-known/security.txt` (Kontakt wie im Impressum, **läuft am 26.11.2027 ab: vorher erneuern**) und `site/llms.txt`. Nach dem Deploy live prüfen (`/.well-known/security.txt`, `/llms.txt`). Noch offen: CAA-Einträge bei Cloudflare (Steve), HSTS `includeSubDomains` (Steve entscheidet; wirkt ein Jahr lang auf alle Unterdomains).
- **Hinweis „mehrfach geprüft" auf der Seite** (Idee von Steve, schafft Vertrauen): kurzer Satz in `hinweise.html` / Fußbereich, de und en. Nur wahrheitsgemäß: automatische Tests (100 Unit-Tests, Klicktest mit 4.300+ Prüfungen bei jedem Push), SEO-Prüfung und Sicherheitsprüfung des Quelltexts mit KI-Werkzeugen, Quellen-Test der Daten. Nicht als „unabhängiges Audit" oder „Pentest" bezeichnen, solange keine externe Stelle geprüft hat. Datum der letzten Prüfung nennen.

Erledigt in der Nacht (Auftrag von Steve):
- **Zeile für englische Browser** auf der deutschen Startseite („This page is available in English. Switch to English“, mit × dauerhaft ausblendbar, `i18n.js`). Keine automatische Weiterleitung.
- **Eigene Seiten je Bericht:** `/bericht/2026-10/`, `/bericht/2026-Q3/`, `/bericht/2025/`, englisch unter `/en/bericht/…`, Übersicht `/bericht/`. Fertiges HTML ohne Skript aus `pipeline/berichtseiten.py` (aufgerufen von `prerender.py`), mit eigenem Titel, Beschreibung, Canonical, hreflang, JSON-LD; alle 98 Adressen stehen in der Sitemap. „Link kopieren“ im Abschnitt „berichte“ zeigt jetzt auf die eigene Seite. Klicktest prüft Übersicht, eine Auswahl an Seiten und die Hinweiszeile.

Entscheiden:
3. **Sicherheitsprüfung (finecomb, 26.11., Stand fb60d1f):** nichts Kritisches oder Hohes, sechs kleinere Punkte. Einzelheiten stehen bewusst nicht in diesem öffentlichen Repo, sondern im Bau-Chat. Beheben?
4. **LinkedIn-Post „Wettrennen“:** berichtigte Fassung liegt im Bau-Chat (5 Tage gelten für ausgenutzte Lücken; „zwei Jahre davor“).

Nur Steve kann das:
5. **Search Console:** Sitemap neu einreichen (jetzt 102 Adressen), `/en/` und eine Berichtsseite über die URL-Prüfung anstoßen, bei `/` die gerenderte Seite ansehen (muss jetzt Deutsch sein, mit der englischen Hinweiszeile oben).
6. **Lizenztext** vor dem Markenkauf gegenlesen lassen (alt, weiter offen).

Klein, kann der Bau-Chat danach erledigen:
7. Kurztext der Startseite aus dem `<noscript>`-Block in sichtbaren Text holen.
8. Sprunglinks im Menü für „logbuch“ und „berichte“.
9. Hinweis per Telegram und Eintrag im RSS-Feed, wenn ein neuer Monatsbericht da ist (Link auf die eigene Seite).
11. Eigenes Vorschaubild je Bericht (heute zeigt jede Berichtsseite das allgemeine `og.png`).
10. `LICENSE` und `README` sagen noch „Quelltext nicht veröffentlicht“, das Repo ist wieder öffentlich: Formulierung prüfen.

- **Ausbau „Handeln“ für mehr Rollen (QS baut, Auftrag von Steve 25.11.).** Drin: (1) „Angegriffen, nach Bereich“ (KEV der letzten 30 Tage in fünf Bereichen, `config/bereiche.json`, `pipeline/bereiche.py`); (2) Hersteller-Quellen Fortinet, Palo Alto Networks und Mozilla über einen allgemeinen Feed-Leser (`parse_feed`, `parse_mozilla`), jede Quelle hat jetzt ein Feld `bereich` und erscheint im passenden Bereich. Offen: Ivanti, Citrix, Adobe, VMware/Broadcom, Apple (erst Quelle suchen, dann mit dem Prüflauf `quellen-test` testen, erst danach aufnehmen); Oracle-Feed gibt dem Lauf 403. Danach: Schalter „Lage zuerst / Handeln zuerst“. Nicht geplant: einzelne Produkte zum Ankreuzen (Inventar). Bitte nicht parallel an denselben Stellen bauen, sondern hier eintragen.
- **Repo ist seit 25.11.2026 abends wieder öffentlich (Entscheidung von Steve).** Laufzeit der Actions ist damit frei. Folge: Code, Verlauf, Issues und Lauf-Protokolle sind für alle lesbar. Nichts Vertrauliches in Commits, Issues oder Protokoll-Ausgaben schreiben; Zugangsdaten nur als GitHub-Geheimnisse. Der Verlauf (302 Commits) wurde am 25.11. nach Tokens, Schlüsseln, Passwörtern und Chat-Kennungen durchsucht: kein Fund. Handstarts trotzdem sparsam halten, wegen der Quellen.
- **Live prüfen nach dem Patch-Abruf ab 22 Uhr UTC (25.11.):** Stehen Ivanti (Fernwartung) und Apple (Arbeitsplatz) als Quellen auf der Seite? Der Handlauf von 19:46 UTC lief noch mit dem Stand vor 6a45c46. Die acht Bereiche und „Diese Woche zuerst patchen“ je Bereich sind live (von Steve am 25.11. abends gesehen).
- **Zweig `quellen-probe` liegt noch im Repo.** Löschen schlug bei Steve („Branch could not be deleted“) und bei der QS fehl; keine Schutzregel, kein Regelsatz gefunden, Ursache offen. Harmlos (ein Test-Commit, nichts Vertrauliches). Später noch einmal löschen, nicht zusammenführen.
- **Bereich „Sonstige“ beobachten:** Hersteller, die dort wiederholt auftauchen, in `config/bereiche.json` nachtragen.
- **Prüfkalender:** Nach dem nächsten Datenlauf prüfen, dass bei „Schwellen des Dreier-Pegels“ nicht mehr „nicht erreichbar“ steht (Link zeigt seit 9dc9bac auf https://cyberlage.org/RULES.md).
- **Handstarts des Datenlaufs sparsam einsetzen.** Jeder Handstart fragt alle Patch-Quellen ab; am 25.11. schlug einer nach rund einem Dutzend Handstarts fehl (vermutlich gebremste Quelle). Der Zeitplan reicht.
- **Geschmacksfragen, bewusst nicht angefasst:** Diagrammschrift 10 px, Ticker-Links 21 px hoch, drei eingeklappte Bereiche.

- **Bau-Chat, 25.11. abends (zur Kenntnis für die QS):** Der Pegel hat jetzt zehn Bausteine in vier Gruppen. Neu: Gruppe Angriffsaktivität mit DShield (angreifende Quellen je Tag, SANS ISC, 7-Tage-Mittel, Schwelle 175.000) und Ransomware (neue Einträge auf Leak-Seiten in 30 Tagen, RansomLook, Schwelle 855). Jede Gruppe hat mindestens zwei Bausteine. Grenze ruhig/unauffällig 35. RULES.md hat einen Abschnitt „Begründung der Modellentscheidungen“ mit Empfindlichkeitsanalyse, Test außerhalb der Stichprobe und Verlässlichkeit der Quellen. Neu ist `site/data/status.json` (Stand, Pegel, fehlende Bausteine); Sentinel3 prüft darüber Frische und Vollständigkeit und kennt die neuen Quellen. Signale-Kacheln stehen nach Gruppen geordnet, „Gruppen und Einzelwerte“ ist ein kompakter Block.
- **Aufbau von Teil 2 (umgesetzt von der QS, 25.11. abends):** „Was betreue ich?“ steht jetzt als erster Block in „patches“, nicht mehr als Unterklappe, und „patches“ ist beim Öffnen von Teil 2 schon aufgeklappt. Der Block zeigt nach Wahl des Bereichs: Hersteller-Kacheln (Zahlen aus den Quellen, nächster Patch-Tag, ehrlicher Hinweis, wo keine offene Quelle angebunden ist) und darunter das gerade Angegriffene aus dem KEV. Katalog der Hersteller je Bereich: `KAT` in `site/app.js` (zeigeBereiche). Neue Quelle = Eintrag in `QUELLEN` (fetch_patches.py) mit `bereich` plus Eintrag in `KAT`.

- **Logbuch (Bau-Chat, 25.11. abends, Auftrag von Steve):** Neuer Abschnitt „logbuch“ in Teil 1 nach dem Rückblick. Daten in `data/logbuch.json`, drei Arten: Erkenntnis (von Hand, mit Belegen), Ereignis (der Datenlauf trägt Stufenwechsel selbst ein, `modell.logbuch_stufenwechsel`), Modell. Erste Einträge: „Wettrennen“ und „zehn Bausteine“. Regel in RULES.md („Logbuch“): Einträge werden nicht nachträglich geändert. Lokal mit Playwright bei 1280 und 390 px geprüft, Deutsch und Englisch. **Fehler Bau-Chat:** Der Push kam um 22:16 UTC mitten in den Handstart von 22:12; dessen Schritt „Änderungen speichern“ scheiterte am Konflikt in `site/data/lage.json`, die Daten dieses Laufs sind nicht gespeichert (Stand blieb 20:14). Ein Ersatzlauf ist danach von Hand gestartet. Nachtrag: Der Datenlauf trägt jetzt auch Höchststände (ab 30 Tagen Reihe) und Bausteine ohne Wert ein, je höchstens einmal in sieben Tagen. Offen: Jahresbericht aus Logbuch und Jahresdaten (noch nicht gebaut), Sprunglink im Menü. Hinweis zur Trägheitsregel: Solange die Stufe an der Grenze 64 pendelt, schreibt das Logbuch jeden Wechsel als Ereignis; das spricht für die Trägheitsregel.

- **Berichte je Monat, Quartal und Jahr (Bau-Chat, 25.11. nachts, Auftrag von Steve):** Neuer Abschnitt „berichte“ in Teil 1 nach dem Logbuch. `modell.berichte` rechnet bei jedem Lauf alle abgeschlossenen Zeiträume aus der Tagesreihe (zurzeit 35 Monate, 11 Quartale, 2 Jahre) nach `site/data/berichte.json`; die Seite lädt die Datei erst beim Aufklappen. Je Bericht: Mittel, Höchst-/Tiefststand, Stufenwechsel, Tage je Stufe, Bausteine, Logbuch-Einträge, Satz und Link zum Kopieren (`?bericht=2026-10`). Regeln in RULES.md („Berichte“). Lokal geprüft bei 1280 und 390 px, Deutsch und Englisch. Offen: Sprunglink im Menü, Berichte in sitemap/Feed, Hinweis per Telegram bei neuem Monatsbericht. Bekannt: Vor dem 25.11.2026 sind die Werte zurückgerechnet (ohne Externe Einschätzungen), das steht in jedem Bericht.

- **Logbuch, Titel „Wettrennen“ berichtigt (Bau-Chat, 25.11. nachts, Entscheidung Steve: direkt ändern):** „als in den zwei Jahren davor“ statt „drei“; die Daten umfassen drei Jahre, verglichen wird mit den zwei davor. Einmalige Ausnahme am Tag der Anlage, die Regel „Einträge nicht ändern“ gilt weiter.

- **Zeitfenster im Fazit (Bau-Chat, 25.11. nachts, Auftrag von Steve):** Neue Zeile „Zeitfenster“ im Fazit über „Zuerst patchen“: Tempo bis KEV in Tagen (Median) und Anteil innerhalb von 30 Tagen, mit Sprung zum Verlauf im Rückblick. Nur Anzeige vorhandener Werte (`tempo.wert`, `radar.zeit_bis_kev.jetzt.anteil_30`), keine neue Regel. Lokal geprüft bei 390 und 1280 px, Deutsch und Englisch.

- **„Was betreue ich?“: Knopf „Alle“ (Bau-Chat, 25.11. nachts, Auftrag von Steve):** Erster Knopf „Alle N“ zeigt die Rangliste „Diese Woche zuerst patchen“ und die angegriffenen Lücken über alle Bereiche, je Eintrag mit Bereichsnamen; die lange Liste zeigt zuerst zehn, der Rest per Knopf. „Alle“ ist die Vorgabe, solange kein Bereich gewählt wurde. Hersteller-Kacheln erscheinen erst nach Wahl eines Bereichs. Nur Anzeige, keine Regel geändert. Lokal geprüft bei 390 und 1280 px, Deutsch und Englisch.

- **„Was betreue ich?“: zwei Zahlen je Knopf (Bau-Chat, 26.11., nach Hinweis von Steve):** Bisher stand nur die KEV-Zahl am Knopf; „Windows und Microsoft 0“ bei zehn kritischen Einträgen in der Rangliste las sich wie „nichts zu tun“. Jetzt stehen beide Zahlen am Knopf (zuerst patchen · neu angegriffen), mit Legende darunter und in der Infozeile. Dazu Fehler behoben: Der Knopf „alle N zeigen“ blieb stehen, wenn man von „Alle“ in einen Bereich ohne KEV-Einträge wechselte.

- **Klicktest (Bau-Chat, 26.11., Auftrag von Steve):** `tests/klicktest.py` bedient die Seite mit Playwright in zwei Breiten (390, 1280) und zwei Sprachen: jede Klappe, jeden Bereich nach jedem anderen, jeden Bericht, Reiter, Direktlinks, Sprachknopf; prüft Skriptfehler, Überstand, Zahlen am Knopf gegen Listen, Platzhalter im Text, Sprungziele. Rund 4.000 Prüfungen, etwa 90 Sekunden. Läuft als Workflow `klicktest` bei jedem Push an `site/`, täglich 06:40 UTC und auf Knopfdruck; lokal `python tests/klicktest.py`. Gegenprobe: Der Fehler „alle zeigen bleibt stehen“ wird gefunden. Bitte bei neuen Bedienelementen eine Prüfung ergänzen. Grenze: Der Test findet Bedienfehler, keine missverständlichen Zahlen.

- **Kopf des Pegels geschärft (Bau-Chat, 26.11., Auftrag von Steve, ein Commit zum Zurücknehmen):** (1) Stufe und Zahl stehen in einer Zeile über der Skala („HOCH 65 / 100“), der gestrichelte Kasten mit der zweiten Zahl ist weg. (2) Unter der Skala nur noch Abstand zur nächsten Stufe und 90-Tage-Verlauf; die Erklärung „50 heißt …“ steht weiter in „so entsteht der pegel“ und in den Fragen. Fehlt ein Baustein, steht „aus 9 von 10 Bausteinen“ bei der Zahl. (3) Der Zeiger läuft beim Laden einmal von 0 auf den Wert (nicht bei „Bewegung reduzieren“). (4) Handy-Menü: drei Zeilen bleiben, enger gesetzt; eine Wischzeile wurde verworfen, weil sie /patches, /termine, /neu versteckt. Am Handy liegt der Pegel jetzt ganz im ersten Bildschirm. Neu im HTML: `.nav-links` um die beiden Linkzeilen (ohne Wirkung, `display:contents`), `#stufe-zahl`. Lokal geprüft bei 360, 390, 1280 px, Deutsch und Englisch, Klicktest grün.

- **Suchmaschinen (Bau-Chat, 26.11., Auftrag von Steve nach Code-Prüfung mit dem Plugin SEO Audit):** (1) Sprache hängt jetzt an der Adresse: `/` ist immer Deutsch, `/en/` ist Englisch (`site/en/index.html`, erzeugt von `prerender.py` aus der deutschen Seite, mit eigenem Titel, Beschreibung, Canonical, Kurztext). Beide Seiten nennen sich gegenseitig per `hreflang` (de, en, x-default). Vorher entschied die Browsersprache; der Crawler von Google rendert englisch und hätte die Seite englisch indexiert. Der Sprachknopf wechselt die Adresse und behält `?bericht=…`. Hinweise und Impressum haben keine eigene englische Adresse, sie folgen der zuletzt besuchten Sprache. Folge: Wer mit englischem Browser `/` aufruft, sieht Deutsch und den Knopf EN (bewusst keine automatische Weiterleitung). (2) Titel: Tagesstand vorn, fester Teil dahinter („HOCH 65 · Cyberlage: Cyber-Bedrohungslage heute“), im HTML und im Browser gleich. (3) `sitemap.xml` schreibt jetzt `prerender.py`: `/`, `/en/` mit `lastmod` = Datenstand und hreflang, `/hinweise`, `/impressum` ohne `.html`. (4) JSON-LD `WebSite` und `Dataset` auf beiden Startseiten; Hinweise mit Beschreibung und Canonical. (5) Alle Pfade in `index.html`, `i18n.js`, `app.js` beginnen jetzt mit `/` (nötig für `/en/`). `daten.yml` nimmt `site/en` und `site/sitemap.xml` mit. Klicktest prüft beide Adressen mit jeweils „falscher“ Browsersprache. **Annahme, live zu prüfen:** Cloudflare liefert `/hinweise.html` unter `/hinweise` aus. **Offen:** eigene Seiten je Bericht (`/bericht/2026-10`); Text der Startseite steht weiter im `<noscript>`-Block; in der Search Console `/en/` und die neue Sitemap einreichen (Steve).

## Entscheidungen von Steve

- **Keine Trägheitsregel (25.11. abends).** Die Stufe wechselt genau an der Grenze, auch wenn der Pegel um einen Punkt pendelt („irgendwo muss er ja umswitchen“). Steht in RULES.md unter „Logbuch“. Nicht erneut vorschlagen.

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

## Erledigt (Sicherheitsprüfung, 26.11.2026)

Finecomb-Prüfung des Repos (nur lesen): nichts Kritisches oder Hohes, Geheimnis-Suche sauber. Die sechs Punkte aus der Prüfung sind behoben:

1. **Speichern im Datenlauf**: neues `pipeline/speichern.sh` (bei Konflikt wird auf dem neuesten Stand neu gerechnet statt abgebrochen); `daten.yml` mit `concurrency`-Gruppe, damit nie zwei Läufe zugleich schreiben.
2. **Telegram-Links** (`notify.py`): neue Funktion `verweis()` – nur https-Adressen werden zu Links, Anführungszeichen werden maskiert.
3. **CSV-Export** (`app.js`): Zellen, die mit = + - @ beginnen, bekommen ein Hochkomma davor.
4. **CVE-Kennung** (`fetch_radar.py`): nur das feste Format wird abgerufen.
5. **Workflows**: Actions auf Commit-Kennungen festgelegt (Kommentar zeigt die Version), Playwright auf 1.63.0 festgelegt, Diagnoseschritt gibt keine Adressen und keine Bot-Nummer mehr aus.
6. **Kopfzeilen** (`site/_headers`): Content-Security-Policy und Strict-Transport-Security; das Skript im Impressum liegt jetzt in `site/impressum.js`.

Tests: 100 Unit-Tests OK (3 neu), Klicktest 4322/0. Die CSP wirkt nur auf Cloudflare; lokal geprüft, dass es keine Inline-Skripte, Inline-Handler oder fremden Quellen gibt.

**Offen / nach dem Push prüfen:** live Kopfzeilen und Seite (Konsole ohne CSP-Fehler); beim nächsten Datenlauf prüfen, dass `speichern.sh` sauber durchläuft; Action-Kennungen gelegentlich erneuern (Dependabot für Actions wäre eine Option).

## Erledigt (QS, 25.11.2026)

- Menü /abo öffnete am linken Rand (548bb72).
- Diagramm-Achse „00 %“, doppelt gezeichneter KEV-Verlauf, englische Monatskürzel auf der deutschen Seite, EPSS auf 100 % gerundet, Sitemap mit Feed (b054634).
- Vorschaubild og.png, Red-Hat-Titel ohne „@sha256“, Radar-Beschriftung frei (1a1128f).
- Skala unter dem Pegel zeigte fest „30“ statt der gültigen Grenze 35 (1940f7b).
- Fazit: Patch-Einträge mit Produktname und Grund-Etikett (e4dab85).
- Externe Links im selben Tab, Prüfkalender-Links auf privates Repo, deutsche Reste auf der englischen Seite (9dc9bac).

## Wie die QS prüft

Lokal mit Playwright (1280 px und 390 px, Deutsch und Englisch, alle Klappen offen) und live über Chrome. Geprüft werden: Skriptfehler, seitliches Scrollen, tote Sprunglinks, leere Elemente, „undefined/NaN“, Sprachreste, Stand der Daten. Nicht geprüft wird die inhaltliche Richtigkeit der Quelldaten.
