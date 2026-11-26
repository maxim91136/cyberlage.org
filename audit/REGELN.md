# Web-Audit mit Dreier-Siegel: Regeln und Regelpflege

Version **1.0**, Stand 26.11.2026. Maßgeblich ist `audit/regeln.json`, dieses Dokument erklärt sie und regelt, wie sie sich ändert. Dasselbe Regelwerk gilt in Cyberlage und in Dreier Labs (beide Repos tragen dieselbe `regeln.json`; die Prüfsumme der Siegel-Test in beiden Repos fällt auf, wenn die Siegelerzeugung auseinanderläuft).

## Was die Version festlegt

Prüfpunkte, Gewichte der zwölf Gruppen, Wertung (bestanden 1, Hinweis 0,5, nicht bestanden 0), den Deckel von 59 bei Mängeln in TLS oder Weiterleitung, die Mindestabdeckung von 90 %, die Stufen (95 ohne Befund, 80 kleine Mängel, 60 Mängel, darunter erhebliche Mängel) und die Abzeichen (Gold ab 95, Silber ab 80, Bronze ab 60). Jedes Ergebnis und jedes Siegel nennt die Version, nach der geprüft wurde. Ein Ergebnis gilt nur zusammen mit dieser Angabe und seinem Datum.

## Versionsnummern: zwei Zahlen

- **1.0 auf 1.1:** neuer oder strengerer Prüfpunkt, aktualisierte Quelle. Gewichte, Stufen und Abzeichen-Grenzen bleiben.
- **1.x auf 2.0:** Änderung an Gewichten, Wertung, Stufen oder Abzeichen-Grenzen. Das trifft jedes Siegel und ist deshalb selten.
- Tippfehler und Quellenangaben ändern die Version nicht, sie stehen im Protokoll unten.

## So läuft eine Änderung

1. **Anlass:** eine Quelle ändert ihre Empfehlung (Mozilla, OWASP, BSI, ein RFC) oder die Durchsicht findet eine Lücke.
2. **Ankündigen:** Der Punkt kommt auf die Beobachtungsliste unten, mit frühestem Datum. Auf der Liste wird noch nichts gemessen, niemand verliert Punkte. Mindestens 60 Tage Vorlauf.
3. **Einführen:** Version erhöhen in `audit/regeln.json` (beide Repos, identisch), Test anpassen, Eintrag im Protokoll. Dann laufen alle Adressen neu. Bis dahin bleiben die Ergebnisse der alten Version stehen; Dreier Labs übernimmt Ergebnisse von Cyberlage nur bei gleicher Version.
4. **Ausmustern:** Ein überholter Prüfpunkt fliegt mit Begründung raus (Protokoll), ebenfalls mit Version.

Nichts wird rückwirkend umgerechnet. Ein Siegel ist eine datierte Momentaufnahme und wird nach 3 Tagen ohne neuen Lauf grau.

## Durchsicht

Vierteljährlich (Februar, Mai, August, November) werden die Quellen der zwölf Gruppen gegengelesen. Der Prüfkalender von Cyberlage (`pipeline/pruefen.py`) meldet die Fälligkeit nach 92 Tagen anhand von `stand` in `regeln.json`. Die Durchsicht wird auch eingetragen, wenn nichts zu ändern ist (`stand` neu setzen, Protokoll ergänzen).

## Beobachtungsliste (angekündigt, noch nicht gemessen)

Frühestens zur Durchsicht im Februar 2027 (nach dem 26.02.2027) zu entscheiden:

- **MTA-STS und TLS-RPT** (RFC 8461, RFC 8460) für Domains, die Mail empfangen.
- **Prüfung des www-Hosts** (Zertifikat, Weiterleitung) zusätzlich zur Hauptadresse.
- **Cross-Origin-Opener-Policy und Cross-Origin-Resource-Policy** (OWASP Secure Headers Project).
- **Schlüsselstärke des Zertifikats und Cipher-Suites** (BSI TR-02102-2, Mozilla Server Side TLS). Mit der reinen Standardbibliothek nicht sauber lesbar; geht nur mit einer Abhängigkeit, also nur nach Entscheidung von Steve.

## Geprüft und nicht aufgenommen

- **HSTS-Preload und includeSubDomains:** nicht umkehrbar bzw. von keinem der Maßstäbe verlangt, ein Hinweis darauf wäre keine Schwäche.

## Protokoll

- **1.0 (26.11.2026):** Erste feste Fassung, vorher 0.1-Entwurf. Prüfpunkte gegen MDN HTTP Observatory, OWASP Secure Headers Project, Mozilla Server Side TLS, BSI TR-02102-2 und die genannten RFCs gegengelesen; keine weiteren Prüfpunkte aufgenommen, Beobachtungsliste angelegt. Siegel trägt die Version im Titel (Hover und Bildschirmleser). Vierteljährliche Durchsicht in den Prüfkalender aufgenommen.
