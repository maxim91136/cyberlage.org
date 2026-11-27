# Cyberlage

**Seismograph der Cyber-Bedrohungslage.** Cyberlage zeigt jeden Tag, wie angespannt die Lage ist, was gerade angegriffen wird und was zuerst gepatcht werden sollte. Alles regelbasiert, aus offenen Quellen und mit Beleg. Ein Werkzeug für die Verteidigung: für Admins, Blue Teams, SOCs und alle, die Systeme schützen.

Live: **https://cyberlage.org** (Deutsch und [Englisch](https://cyberlage.org/en/)). Neues gibt es auch im [Telegram-Kanal](https://t.me/cyberlage_org) und als [RSS-Feed](https://cyberlage.org/feed.xml).

Ein Projekt von [Dreier Labs](https://dreierlabs.com). Ein privates Projekt, keine amtliche Stelle und keine Zusammenarbeit mit einer Behörde.

*In English: Cyberlage is a rule-based, openly sourced daily gauge of the global cyber threat situation (the "Dreier Gauge", 0 to 100) with patch priorities, patch calendar and lifecycle dates. The site is bilingual; this README is in German, the rules in [RULES.md](RULES.md) are the reference for every number.*

## Warum das Repository öffentlich ist

Jede Zahl auf der Seite soll nachprüfbar sein: woher sie kommt, wie sie gerechnet wird und wann sie zuletzt aktualisiert wurde. Deshalb liegen Regeln, Rohdaten, Quellenliste, Auswertung und Tests offen hier. Es soll helfen und zeigen, wie so etwas sauber gebaut werden kann. Die Nutzungsbedingungen stehen unten im Abschnitt Lizenz.

## Was die Seite zeigt

| Teil | Inhalt |
| --- | --- |
| **Lage** | Der Dreier-Pegel mit Verlauf, die zehn Bausteine als Radar, Signale und Rückblick |
| **Handeln** | Patches (was zuerst, womit), Windows-Patch-Level, Patch-Kalender, Lebenszyklen mit Support-Ende (Daten von endoflife.date), Neues zu ausgenutzten Schwachstellen, Hersteller und Linux-Distributionen |
| **Belege** | Logbuch jeder Stufenänderung, Monats-, Quartals- und Jahresberichte, Web-Audit und Code-Audit mit eigenen Siegeln |
| **Info** | Quellen, Begriffe, Methode, Hinweise, FAQ |

## Der Dreier-Pegel

Der **Dreier-Pegel** (englisch *Dreier Gauge*) ist der eigene Gesamtscore: eine Zahl von 0 bis 100 und eine Stufe (ruhig, unauffällig, angespannt, hoch, außergewöhnlich). Er entsteht aus **zehn Bausteinen in vier Gruppen**:

- **Ausnutzung:** KEV-Menge, Tempo bis KEV, EU-KEV, Microsoft (ausgenutzte Lücken im letzten Patch Day)
- **Warnungen:** CERT-Bund, NCSC-NL
- **Angriffsaktivität:** DShield, Ransomware-Opfereinträge
- **Externe Einschätzungen:** BSI Cyber Index, SANS Infocon

Jeder Baustein folgt einer festen Regel mit Schwelle (abgeleitet aus 36 Monaten Verlauf, wo die Quelle so weit zurückreicht). Das Modell ist versioniert (`config/modell.json`), ein Entwurf, und wird nur zusammen mit einem Eintrag in [RULES.md](RULES.md) geändert. Der Name steht für Dreier Labs. Daneben zeigt der **Radar** weitere Messungen, ohne sie mit dem Pegel zu vermischen.

## Grundregeln

- **Quelle, Stand und Lizenz an jedem Wert.** Nichts erscheint ohne Beleg.
- **Regeln statt Bauchgefühl.** Die Bewertung folgt den offenen Regeln in [RULES.md](RULES.md). Schwellen, Stufen und Bausteine ändern sich nur zusammen mit einem Eintrag dort.
- **Keine Daten statt Schätzung.** Was nicht belegt ist, heißt „keine Daten“.
- **Keine einzelnen Betroffenen.** Es wird nur gezeigt, was die Quellen veröffentlichen.
- **Lizenzen zuerst.** Eine Quelle wird nur genutzt, wenn ihre Bedingungen es erlauben, sonst wird nur verlinkt. Siehe [data/sources.csv](data/sources.csv).

## Audits

Die Seite prüft sich selbst und zeigt das Ergebnis mit jeweils eigenem Siegel unter [/audit](https://cyberlage.org/audit/):

- **Web-Audit (Dreier-Web-Siegel):** prüft cyberlage.org und cyberlage.com täglich von außen (Kopfzeilen, TLS, DNS, Mail-Schutz, Weiterleitung). Code in `audit/`, Regeln in [audit/REGELN.md](audit/REGELN.md).
- **Code-Audit (Dreier-Code-Siegel):** prüft den Code dieses Repos täglich (Geheimnisse, Workflows, Abhängigkeiten, Python, JavaScript, Tests, Wartbarkeit). Code in `codeaudit/`, Regeln als Entwurf in [codeaudit/REGELN.md](codeaudit/REGELN.md).

Beide Siegel sind der Stand eines automatischen Laufs mit offenen Regeln, kein Zertifikat einer Prüfstelle.

## Aufbau

| Pfad | Zweck |
| --- | --- |
| `data/` | Quellenregister (`sources.csv`), Rohdaten und Verläufe (KEV, BSI, EU, ENISA, Patches, Radar, Pegel), Ergebnisse der Audits |
| `config/` | Regeln als Daten: `modell.json` (Dreier-Pegel), `regeln.json`, `bereiche.json`, `radar_stufen.json`, `telegram.json` |
| `pipeline/` | Abruf und Auswertung (`fetch_*.py`), Bewertung (`score.py`, `modell.py`), Seiten und Feed (`prerender.py`, `feed.py`, `berichtseiten.py`, `auditseiten.py`), Telegram (`notify.py`), gemeinsame Schutzfunktionen (`sicher.py`) |
| `audit/` | Web-Audit: Prüfungen, Auswertung, Regeln |
| `codeaudit/` | Code-Audit: Prüfungen, Auswertung, Regeln |
| `tests/` | Unit-Tests und der Klicktest (`klicktest.py`, bedient die Seite im Browser) |
| `site/` | Die Seite (Deutsch und Englisch), Ausgabedaten und Feed |
| `.github/workflows/` | `daten.yml` (Datenlauf alle zwei Stunden), `audit.yml`, `codeaudit.yml`, `klicktest.yml`, `quellen-test.yml` |
| `RULES.md` | Alle Regeln: Schwellen, Stufen, Bausteine, Bewertung, Begründungen |

Die Seite wird als statische Dateien über Cloudflare ausgeliefert (`wrangler.jsonc`). Die Daten schreibt der Datenlauf in GitHub Actions ins Repo; die Pipeline braucht nur Python 3 und die Standardbibliothek.

## Lokal ausführen

Nur Python 3, keine weiteren Pakete:

```
python3 -m unittest discover -s tests
python3 pipeline/fetch_kev.py
python3 pipeline/score.py
python3 pipeline/feed.py
python3 pipeline/prerender.py
```

Die übrigen Abrufe (`fetch_*.py`) brauchen Internetzugang zu den jeweiligen Quellen. Der Klicktest (`python3 tests/klicktest.py`) braucht zusätzlich Playwright mit Chromium. Zum Ansehen genügt jeder statische Webserver im Ordner `site/`.

## Hinweis

Die Seite zeigt Zahlen aus öffentlichen Quellen. Sie ersetzt keine Warnung des BSI oder eines CERT. Die Verlinkung auf amtliche Quellen ist kein Hinweis auf eine Zusammenarbeit. Kontakt: siehe [Impressum](https://cyberlage.org/impressum.html); Sicherheitslücken bitte nach [security.txt](https://cyberlage.org/.well-known/security.txt) melden.

## Lizenz

Das Repository ist öffentlich, damit alles nachprüfbar ist. Öffentlich heißt nicht frei verwendbar: Es gelten die Bedingungen in [LICENSE](LICENSE) (Alle Rechte vorbehalten). Lesen, zitieren und zur Prüfung lokal ausführen ist erlaubt. Jede weitere Nutzung, etwa Kopieren, Verändern, Weiterverbreiten, eigene Angebote auf dieser Grundlage oder kommerzielle Nutzung, braucht die vorherige schriftliche Zustimmung. Die Namen „Cyberlage“ und „Dreier-Pegel“ sowie das Logo sind nicht freigegeben. Daten Dritter bleiben bei ihren Urhebern und unterliegen deren Bedingungen. Anfragen: siehe [Impressum](https://cyberlage.org/impressum.html).

## Dank

Danke an alle, deren offene Daten diese Seite möglich machen: CISA, ENISA, BSI und CERT-Bund, NCSC-NL, SANS ISC, FIRST (EPSS), NIST (NVD), RansomLook, Microsoft, Red Hat, SUSE, Canonical, Debian, AlmaLinux, Rocky Linux, Amazon, Cisco, SAP und endoflife.date.
