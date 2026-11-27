"""Audit-Seite mit dem Dreier-Siegel: /audit/ (Deutsch) und /en/audit/ (Englisch), dazu je Domain ein Siegel als SVG.

Fertiges HTML ohne Skript. Die Zahlen kommen aus data/audit/<domain>.json (geschrieben von audit/lauf.py im Tageslauf), die Gruppen,
Gewichte, Quellen und Stufen aus audit/regeln.json; hier wird nichts gerechnet. Einzelbefunde stehen nie auf der Seite, nur Zahlen.
Das Siegel ist kein Zertifikat einer Prüfstelle, sondern der Stand eines automatischen Laufs: Score, Adresse, Datum. Ist der Lauf
älter als SIEGEL_TAGE, wird es grau."""
import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import berichtseiten as bs

BASIS = bs.BASIS
SIEGEL_TAGE = 3  # täglicher Lauf plus Luft: älter heißt, der Lauf ist ausgefallen
REPO_AUDIT = "https://github.com/maxim91136/cyberlage.org/tree/main/audit"
FARBE = {"ruhig": "#6fe0a0", "angespannt": "#e3b341", "hoch": "#ff8a7a", "ausserordentlich": "#ff3b5c", "grau": "#8b98a3"}
AMPEL = {"ohne Befund": "ruhig", "kleine Mängel": "angespannt", "Mängel": "hoch", "erhebliche Mängel": "ausserordentlich"}
METALL = {"gold": "#f0c04a", "silber": "#cfd8df", "bronze": "#cd7f4f"}  # Ring des Abzeichens
ABZ_NAME = {"de": {"gold": "Gold", "silber": "Silber", "bronze": "Bronze"}, "en": {"gold": "Gold", "silber": "Silver", "bronze": "Bronze"}}
STUFE_EN = {"ohne Befund": "no findings", "kleine Mängel": "minor deficiencies", "Mängel": "deficiencies", "erhebliche Mängel": "significant deficiencies",
            "nicht bewertet (zu wenig geprüft)": "not rated (too little checked)"}
GRUPPE_EN = {"tls": "TLS and certificate", "csp": "Content Security Policy", "fremd": "Third-party content", "hsts": "HSTS", "dns": "DNS (CAA, DNSSEC)",
             "mail": "Domain mail", "weiterleitung": "Redirects", "inhalt": "Content type and framing", "cookies": "Cookies", "auffindbar": "Discoverability",
             "datenschutz": "Privacy headers", "altlasten": "Legacy leftovers"}
LAUF_UHR = "05:20"  # UTC, steht so in .github/workflows/audit.yml (ein Test prüft das)
WEITERLEITUNG_ENTFAELLT = ("csp", "fremd", "inhalt", "datenschutz", "altlasten", "auffindbar")  # gleich audit/lauf.py NICHT_ZUTREFFEND (ein Test prüft das)
REIHE = ("cyberlage.org", "cyberlage.com")  # Reihenfolge auf der Seite

T = {
    "de": {"pfad": "/audit/", "start": "/", "titel": "Web-Audit: Dreier-Siegel für cyberlage.org und cyberlage.com · Cyberlage", "h1": "Web-Audit",
           "intro": "Ein selbst gebautes, regelbasiertes Web-Audit prüft diese Adressen jeden Tag von außen: Kopfzeilen, Verschlüsselung, DNS, Mail-Schutz und Weiterleitung. "
                    "Wie beim Dreier-Pegel liegen Regeln, Gewichte und Quellen offen. Hier gilt: hoch ist gut.",
           "beschr": "Das Dreier-Siegel zeigt den Stand des automatischen Web-Audits von cyberlage.org und cyberlage.com: Score, Datum, Prüfgruppen. Regeln und Quellen offen.",
           "abz": "Abzeichen", "kein_abz": "keins", "stand": "Stand", "profil": "Profil", "seite": "Seite", "weiter": "Weiterleitung auf %s", "regeln": "Regeln", "abdeckung": "Abdeckung",
           "befunde": "Befunde", "hinweise": "Hinweise", "ohne": "keine", "offen": "Einzelheiten zu offenen Punkten werden erst nach der Behebung genannt.",
           "veraltet": "Der letzte Lauf ist älter als %d Tage, das Siegel ist deshalb grau.", "kein_score": "ohne Score", "entfaellt": "entfällt",
           "h_gruppen": "Prüfgruppen", "gruppen_leg": "Wert je Gruppe: Anteil der bestandenen Prüfungen. „entfällt“: trifft auf diese Adresse nicht zu, etwa Cookies, wenn keine gesetzt werden.",
           "h_wann": "Wann und wie geprüft wird",
           "wann": ("Der Lauf startet jeden Tag automatisch gegen %s Uhr UTC (%s Uhr MEZ) in GitHub Actions. Zusätzlich kann er von Hand gestartet werden.",
                    "Jede Adresse wird mit höchstens etwa 40 kurzen Abrufen von außen geprüft, ohne Anmeldung, mit dem Kennzeichen „cyberlage-audit“ und einem Link auf die Hinweise.",
                    "Der neue Lauf ersetzt den vorigen. Die Seite zeigt immer den letzten Lauf mit Datum und Uhrzeit (UTC).",
                    "Fällt ein Lauf aus, bleibt der letzte Stand sichtbar. Nach mehr als %d Tagen ohne neuen Lauf wird das Siegel grau.",
                    "Ist eine Adresse nicht erreichbar, gibt es kein Ergebnis, statt falscher Befunde.",
                    "Der Betreiber wird nur benachrichtigt, wenn sich das Ergebnis gegenüber dem letzten Lauf ändert.",
                    "Regeln, Gewichte und Grenzen ändern sich nur mit einer neuen Regelversion (jetzt %s). Jede Änderung steht im Verlauf des Quelltexts."),
           "h_ausn": "Ausnahmen für reine Weiterleitungen", "ausn_hint": "Diese Adresse leitet nur weiter, deshalb gelten Ausnahmen:", "ausn_link": "siehe Ausnahmen",
           "ausn": ("%s liefert keine Seite aus, sondern leitet nur auf %s weiter. Dafür gilt ein eigenes Profil „Weiterleitung“.",
                    "Es entfallen die Gruppen, die Seiteninhalt voraussetzen: %s. Sie zählen weder gut noch schlecht, die Abdeckung bleibt bei 100 %%.",
                    "Stattdessen wird zusätzlich geprüft: dauerhafte Weiterleitung (301) mit Pfad und Abfrage auf das Ziel, ebenso bei www, ob das Ziel antwortet, und ob die Domain ausdrücklich keine Mail annimmt (Null-MX).",
                    "Alle übrigen Prüfungen (TLS, HSTS, DNSSEC, CAA, SPF, DMARC) gelten unverändert und mit denselben Gewichten.",
                    "Die Seite %s wird getrennt und vollständig geprüft."),
           "h_rechnen": "So wird gerechnet", "h_massstab": "Maßstäbe", "gruppe": "Gruppe", "gewicht": "Gewicht", "quelle": "Quelle",
           "rechnen": ("Jede Prüfung zählt 1 (bestanden), ½ (Hinweis) oder 0 (nicht bestanden). Nicht zutreffende Prüfungen zählen nicht, nicht geprüfte senken die Abdeckung.",
                       "Der Wert einer Gruppe ist der Mittelwert ihrer Prüfungen. Der Score ist das gewichtete Mittel der Gruppen mal 100.",
                       "Hat die Gruppe TLS oder Weiterleitung den Wert 0, ist der Score höchstens %d.",
                       "Ohne %d %% geprüftes Gewicht gibt es keinen Score, nur einen Teilwert."),
           "h_stufen": "Stufen und Abzeichen", "ab": "ab %d",
           "h_siegel": "Was das Dreier-Siegel ist und was nicht",
           "siegel": ("Das Siegel zeigt Score, Abzeichen (Gold, Silber, Bronze), Adresse und Datum des letzten Laufs. Ohne Datum gilt es nicht.",
                      "Es ist kein Zertifikat einer Prüfstelle und kein Gütesiegel einer Behörde, kein unabhängiges Audit und kein Penetrationstest. Es sagt nicht, dass eine Seite sicher ist, nur dass bestimmte öffentlich messbare Punkte erfüllt sind.",
                      "Geprüft wird nur von außen, mit offenen Regeln. Schwachstellensuche und Angriffstests gehören nicht dazu."),
           "svg": "Siegel als SVG", "quell": "Quelltext des Web-Audits", "heute": "Dreier-Pegel heute", "andere": "English", "alle": "Berichte",
           "fuss": "Ein privates Projekt von Dreier Labs, keine amtliche Stelle. Feste Regeln, keine Vorhersage."},
    "en": {"pfad": "/en/audit/", "start": "/en/", "titel": "Web audit: Dreier Seal for cyberlage.org and cyberlage.com · Cyberlage", "h1": "Web audit",
           "intro": "A self-built, rule-based web audit checks these addresses from the outside every day: headers, encryption, DNS, mail protection and redirects. "
                    "As with the Dreier Gauge, rules, weights and sources are open. Here, high is good.",
           "beschr": "The Dreier Seal shows the state of the automated web audit of cyberlage.org and cyberlage.com: score, date, check groups. Rules and sources are open.",
           "abz": "Badge", "kein_abz": "none", "stand": "As of", "profil": "Profile", "seite": "Site", "weiter": "Redirect to %s", "regeln": "Rules", "abdeckung": "Coverage",
           "befunde": "Findings", "hinweise": "Notes", "ohne": "none", "offen": "Details on open items are named only after they are fixed.",
           "veraltet": "The last run is older than %d days, so the seal is grey.", "kein_score": "no score", "entfaellt": "n/a",
           "h_gruppen": "Check groups", "gruppen_leg": "Value per group: share of checks passed. “n/a”: does not apply to this address, for example cookies when none are set.",
           "h_wann": "When and how it runs",
           "wann": ("The run starts automatically every day at about %s UTC (%s CET) in GitHub Actions. It can also be started by hand.",
                    "Each address is checked from the outside with at most about 40 short requests, without logging in, identified as “cyberlage-audit” with a link to the notices.",
                    "The new run replaces the previous one. The page always shows the latest run with date and time (UTC).",
                    "If a run fails, the last state stays visible. After more than %d days without a new run the seal turns grey.",
                    "If an address cannot be reached there is no result rather than false findings.",
                    "The operator is notified only when the result changes compared with the last run.",
                    "Rules, weights and limits change only with a new rules version (now %s). Every change is in the history of the source code."),
           "h_ausn": "Exceptions for pure redirects", "ausn_hint": "This address only redirects, so exceptions apply:", "ausn_link": "see exceptions",
           "ausn": ("%s does not serve a page, it only redirects to %s. It is checked with its own profile, “Redirect”.",
                    "Groups that need page content are left out: %s. They count neither good nor bad, and coverage stays at 100 %%.",
                    "Instead, additional checks apply: a permanent redirect (301) to the target keeping path and query, the same for www, whether the target answers, and whether the domain explicitly accepts no mail (Null MX, RFC 7505).",
                    "All other checks (TLS, HSTS, DNSSEC, CAA, SPF, DMARC) apply unchanged and with the same weights.",
                    "The site %s is checked separately and in full."),
           "h_rechnen": "How it is calculated", "h_massstab": "Standards", "gruppe": "Group", "gewicht": "Weight", "quelle": "Source",
           "rechnen": ("Each check counts 1 (passed), ½ (note) or 0 (failed). Checks that do not apply are left out, checks not run lower the coverage.",
                       "A group’s value is the mean of its checks. The score is the weighted mean of the groups times 100.",
                       "If the group TLS or Redirects has the value 0, the score is capped at %d.",
                       "Without %d %% of the weight checked there is no score, only a partial value."),
           "h_stufen": "Levels and badges", "ab": "from %d",
           "h_siegel": "What the Dreier Seal is and is not",
           "siegel": ("The seal shows the score, badge (gold, silver, bronze), address and date of the latest run. Without the date it means nothing.",
                      "It is not a certificate from an assessment body or an official quality mark, not an independent audit and not a penetration test. It does not say a site is secure, only that certain publicly measurable points are met.",
                      "Checks are made from the outside only, with open rules. Vulnerability scanning and attack tests are not part of it."),
           "svg": "Seal as SVG", "quell": "Source code of the web audit", "heute": "Dreier Gauge today", "andere": "Deutsch", "alle": "Reports",
           "fuss": "A private project by Dreier Labs, not an official body. Fixed rules, no forecast."},
}


def _e(t):
    return html.escape(str(t), quote=True)


def lies(wurzel):
    """Liest die Zusammenfassungen. Gibt [(domain, dict)] in fester Reihenfolge zurück, unbekannte Domains zuletzt."""
    ordner = Path(wurzel) / "data" / "audit"
    daten = {}
    for f in sorted(ordner.glob("*.json")) if ordner.is_dir() else []:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            daten[d["domain"]] = d
        except (OSError, ValueError, KeyError):
            continue
    return sorted(daten.items(), key=lambda x: (REIHE.index(x[0]) if x[0] in REIHE else len(REIHE), x[0]))


def _stand(d):
    return datetime.strptime(d["stand"], "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)


def abzeichen(score, regeln):
    """Gold, Silber oder Bronze nach den Grenzen aus regeln.json (gleich den Stufen); darunter und ohne Score keins."""
    if score is None:
        return None
    for grenze, name in regeln["abzeichen"]:
        if score >= grenze:
            return name
    return None


def _version(v, sp):
    """Regelversion für die Anzeige: auf der englischen Seite „-entwurf“ als „-draft“."""
    return v.replace("-entwurf", "-draft") if sp == "en" else v


def _quelle(q, sp):
    """Quellenangabe für die Anzeige; auf der englischen Seite die deutschen Wörter ersetzt."""
    return q.replace(" bis ", " to ").replace("Sitemaps-Protokoll", "Sitemaps protocol") if sp == "en" else q


def farbe(d, jetzt, regeln):
    """Farbe des Siegels: Metall des Abzeichens; ohne Abzeichen die Warnfarbe der Stufe; grau ohne Score oder bei zu altem Lauf."""
    if d.get("score") is None or jetzt - _stand(d) > timedelta(days=SIEGEL_TAGE):
        return FARBE["grau"]
    abz = abzeichen(d["score"], regeln)
    return METALL[abz] if abz else FARBE[AMPEL.get(d["stufe"], "ausserordentlich")]


def siegel(domain, d, jetzt, regeln):
    """Das Dreier-Siegel als SVG, ein Stempel mit Strichring: oben DREIER-SIEGEL, in der Mitte der Score, darunter das Abzeichen
    (GOLD, SILBER, BRONZE; darunter nur „/ 100“), unten Adresse und Datum (ISO). Ring in der Farbe des Metalls; grau bei zu altem Lauf."""
    f = farbe(d, jetzt, regeln)
    abz = None if f == FARBE["grau"] else abzeichen(d["score"], regeln)
    if f == FARBE["grau"]:
        abz = abzeichen(d.get("score"), regeln)  # grau, aber das zuletzt erreichte Abzeichen bleibt lesbar
    score = "–" if d.get("score") is None else str(d["score"])
    tag = d["stand"][:10]
    titel = "Dreier-Siegel: %s, Score %s%s, Stand %s, Regeln %s" % (domain, score, ", " + ABZ_NAME["de"][abz] if abz else "", tag, regeln["version"])
    ticks = "".join('<line x1="100" y1="6" x2="100" y2="%d" transform="rotate(%d 100 100)"/>' % (13 if i % 5 else 16, i * 6) for i in range(60))
    gross = 52 if len(score) < 3 else 46
    mono = 'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"'
    if abz:
        unten = ('<rect x="68" y="120" width="64" height="21" rx="3" fill="none" stroke="%s" stroke-width="1.4"/>'
                 '<text x="100" y="135" %s font-size="12" font-weight="700" letter-spacing="2.4" fill="%s" text-anchor="middle">%s</text>') % (f, mono, f, ABZ_NAME["de"][abz].upper())
    else:
        unten = '<text x="100" y="130" %s font-size="11" letter-spacing="1" fill="#8b98a3" text-anchor="middle">/ 100</text>' % mono
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200" role="img" aria-label="%s"><title>%s</title>'
            '<circle cx="100" cy="100" r="98" fill="#0b1114"/>'
            '<g stroke="%s" stroke-width="1.6" opacity=".75">%s</g>'
            '<circle cx="100" cy="100" r="92" fill="none" stroke="%s" stroke-width="3"/>'
            '<circle cx="100" cy="100" r="68" fill="none" stroke="%s" stroke-width="1.2" opacity=".55"/>'
            '<defs><path id="o" d="M 24,100 A 76,76 0 0,1 176,100"/><path id="u" d="M 16,100 A 84,84 0 0,0 184,100"/></defs>'
            '<text %s font-size="12.5" font-weight="700" letter-spacing="3.2" fill="%s" text-anchor="middle"><textPath href="#o" startOffset="50%%">DREIER-SIEGEL</textPath></text>'
            '<text %s font-size="10" letter-spacing="1.4" fill="#c9d4dc" text-anchor="middle"><textPath href="#u" startOffset="50%%">%s · %s</textPath></text>'
            '<text x="100" y="%d" %s font-size="%d" font-weight="700" fill="%s" text-anchor="middle">%s</text>%s'
            '<text x="100" y="157" %s font-size="8.5" letter-spacing="1.4" fill="#8b98a3" text-anchor="middle">REGELN %s</text>'
            '</svg>') % (_e(titel), _e(titel), f, ticks, f, f, mono, f, mono, _e(domain.upper()), tag, 108 if len(score) < 3 else 106, mono, gross, f, _e(score), unten, mono, _e(regeln["version"]))


def fuss_text(d, regeln, sp, jetzt):
    """Kurzer Text neben dem Siegel im Fuß der Startseite: Score, Abzeichen, Datum; bei zu altem Lauf nur das Datum."""
    datum = bs._datum(d["stand"][:10], sp)
    if farbe(d, jetzt, regeln) == FARBE["grau"]:
        return ("Web-Audit: letzter Lauf %s" if sp == "de" else "Web audit: last run %s") % datum
    abz = abzeichen(d["score"], regeln)
    return ("Web-Audit: " if sp == "de" else "Web audit: ") + "%d / 100%s · %s · %s %s" % (d["score"], " · " + ABZ_NAME[sp][abz] if abz else "", datum, "Regeln" if sp == "de" else "Rules", regeln["version"])


def _stufe(d, sp):
    s = d.get("stufe", "")
    return STUFE_EN.get(s, s) if sp == "en" else s


def _karte(domain, d, regeln, sp, jetzt, weiter):
    t = T[sp]
    f = farbe(d, jetzt, regeln)
    alt = f == FARBE["grau"]
    abz = abzeichen(d.get("score"), regeln)
    datum = bs._datum(d["stand"][:10], sp)
    stand = "%s %s UTC" % (datum, d["stand"][11:16])
    profil = t["weiter"] % weiter if d.get("profil") == "weiterleitung" and weiter else t["seite"]
    score = "–" if d.get("score") is None else "%d" % d["score"]
    zeilen = [(t["stand"], stand), (t["profil"], profil), (t["regeln"], _version(regeln["version"], sp)), (t["abdeckung"], "%d %%" % round(100 * d["abdeckung"])), (t["abz"], ABZ_NAME[sp][abz] if abz else t["kein_abz"])]
    bef = "%s · %s" % ("%s: %s" % (t["befunde"], d["befunde"] or t["ohne"]), "%s: %s" % (t["hinweise"], d["hinweise"] or t["ohne"]))
    z = ['<article class="au-karte" style="--ra:%s"><div class="au-sg">%s</div><div class="au-info">' % (f, siegel(domain, d, jetzt, regeln)),
         '<h2 class="au-dom">%s</h2><p class="au-sc mono"><strong>%s</strong> / 100 <span class="au-st">%s</span></p>' % (_e(domain), _e(score), _e(_stufe(d, sp) if d.get("score") is not None else t["kein_score"]))]
    z.append('<dl class="au-dl mono">%s</dl>' % "".join("<div><dt class=\"dim\">%s</dt><dd>%s</dd></div>" % (_e(a), _e(b)) for a, b in zeilen))
    z.append('<p class="au-bef mono">%s</p>' % _e(bef))
    if d.get("profil") == "weiterleitung":
        z.append('<p class="dim au-hint">%s <a href="#ausnahmen">%s</a></p>' % (_e(t["ausn_hint"]), _e(t["ausn_link"])))
    if d["befunde"]:
        z.append('<p class="dim au-hint">%s</p>' % _e(t["offen"]))
    if alt and d.get("score") is not None:
        z.append('<p class="dim au-hint">%s</p>' % _e(t["veraltet"] % SIEGEL_TAGE))
    z.append('<p class="au-ln mono"><a href="/audit/siegel/%s.svg">%s</a></p></div></article>\n' % (_e(domain), _e(t["svg"])))
    gz = []
    for g, info in regeln["gruppen"].items():
        name = GRUPPE_EN[g] if sp == "en" else info["name"]
        w = d["gruppen"].get(g)
        if w is None:
            gz.append('<div class="au-k au-n"><b>%s</b><span class="mono dim">%s</span><div class="au-bar"><i style="width:0"></i></div></div>' % (_e(name), _e(t["entfaellt"])))
        else:
            c = FARBE["ruhig"] if w >= 1 else FARBE["angespannt"] if w >= 0.5 else FARBE["ausserordentlich"]
            gz.append('<div class="au-k"><b>%s</b><span class="mono">%d %%</span><div class="au-bar" style="--c:%s"><i style="width:%d%%"></i></div></div>' % (_e(name), round(100 * w), c, round(100 * w)))
    z.append('<div class="au-grid">%s</div>\n' % "".join(gz))
    return "".join(z)


def seite(sp, daten, regeln, jetzt):
    t = T[sp]
    pfad_de, pfad_en = "/audit/", "/en/audit/"
    weiter = {dom: "cyberlage.org" for dom, d in daten if d.get("profil") == "weiterleitung"}
    z = [bs._kopf(sp, t["titel"], t["beschr"], pfad_de, pfad_en), '<main class="wrap bs-main"><h1>%s</h1>\n<p class="dim au-intro">%s</p>\n' % (_e(t["h1"]), _e(t["intro"]))]
    z += [_karte(dom, d, regeln, sp, jetzt, weiter.get(dom)) for dom, d in daten]
    z.append('<p class="dim au-leg">%s</p>\n' % _e(t["gruppen_leg"]))
    h, m = (int(x) for x in LAUF_UHR.split(":"))
    wann = (t["wann"][0] % (LAUF_UHR, "%02d:%02d" % (h + 1, m)), t["wann"][1], t["wann"][2], t["wann"][3] % SIEGEL_TAGE, t["wann"][4], t["wann"][5], t["wann"][6] % _version(regeln["version"], sp))
    z.append('<h2 class="mono">%s</h2>\n<ul class="au-ul">%s</ul>\n' % (_e(t["h_wann"]), "".join("<li>%s</li>" % _e(x) for x in wann)))
    wd = [(dom, d) for dom, d in daten if d.get("profil") == "weiterleitung"]
    if wd:
        doms = ", ".join(dom for dom, _d in wd)
        ziele = ", ".join(sorted({weiter[dom] for dom, _d in wd}))
        fehlt = ", ".join((GRUPPE_EN[g] if sp == "en" else i["name"]) for g, i in regeln["gruppen"].items() if g in WEITERLEITUNG_ENTFAELLT)
        ausn = (t["ausn"][0] % (doms, ziele), t["ausn"][1] % fehlt, t["ausn"][2], t["ausn"][3], t["ausn"][4] % ziele)
        z.append('<h2 class="mono" id="ausnahmen">%s</h2>\n<ul class="au-ul">%s</ul>\n' % (_e(t["h_ausn"]), "".join("<li>%s</li>" % _e(x) for x in ausn)))
    z.append('<h2 class="mono">%s</h2>\n<ul class="au-ul">%s</ul>\n' % (_e(t["h_rechnen"]), "".join("<li>%s</li>" % _e(x % v if "%" in x else x) for x, v in zip(
        t["rechnen"], (None, None, regeln["deckel"]["max_score"], round(100 * regeln["mindest_abdeckung"])), strict=False))))
    def _abz_text(g):
        a = abzeichen(g, regeln)
        return ABZ_NAME[sp][a] if a else t["kein_abz"]
    stufen = "".join('<li class="ra-%s"><span>%s</span><span class="mono">%s · %s</span></li>' % (AMPEL.get(n, "ruhig"), _e(STUFE_EN.get(n, n) if sp == "en" else n), _e(_abz_text(g)), _e(t["ab"] % g)) for g, n in regeln["stufen"])
    z.append('<h2 class="mono">%s</h2>\n<ul class="bs-liste au-stufen">%s</ul>\n' % (_e(t["h_stufen"]), stufen))
    z.append('<h2 class="mono">%s</h2>\n<div class="br-tab"><table><thead><tr><th>%s</th><th>%s</th><th>%s</th></tr></thead><tbody>%s</tbody></table></div>\n' % (
        _e(t["h_massstab"]), _e(t["gruppe"]), _e(t["gewicht"]), _e(t["quelle"]),
        "".join('<tr><td>%s</td><td class="mono">%d</td><td class="dim">%s</td></tr>' % (_e(GRUPPE_EN[g] if sp == "en" else i["name"]), i["gewicht"], _e(_quelle(i["quelle"], sp))) for g, i in regeln["gruppen"].items())))
    z.append('<h2 class="mono">%s</h2>\n<ul class="au-ul">%s</ul>\n' % (_e(t["h_siegel"]), "".join("<li>%s</li>" % _e(x) for x in t["siegel"])))
    andere = pfad_de if sp == "en" else pfad_en
    z.append('<p class="bs-nav mono"><a href="%s">%s</a> · <a href="%s">%s</a> · <a href="%s">%s</a> · <a href="/RULES.md">RULES</a> · <a href="%s" hreflang="%s">%s</a></p>\n'
             '<p class="mono dim fine">%s</p>\n</main></body></html>\n' % (
                 t["start"], _e(t["heute"]), bs.T[sp]["pfad"], _e(t["alle"]), REPO_AUDIT, _e(t["quell"]), andere, "de" if sp == "en" else "en", _e(t["andere"]), _e(t["fuss"])))
    return "".join(z)


def schreibe(wurzel, jetzt=None):
    """Schreibt site/audit/index.html, site/en/audit/index.html und site/audit/siegel/<domain>.svg.
    Gibt [(pfad_de, pfad_en, lastmod)] für die Sitemap zurück, bei fehlenden Daten []."""
    wurzel = Path(wurzel)
    jetzt = jetzt or datetime.now(timezone.utc)
    daten = lies(wurzel)
    if not daten:
        return []
    regeln = json.loads((wurzel / "audit" / "regeln.json").read_text(encoding="utf-8"))
    site = wurzel / "site"
    for sp in ("de", "en"):
        ziel = site / T[sp]["pfad"].strip("/")
        ziel.mkdir(parents=True, exist_ok=True)
        (ziel / "index.html").write_text(seite(sp, daten, regeln, jetzt), encoding="utf-8")
    (site / "audit" / "siegel").mkdir(parents=True, exist_ok=True)
    for dom, d in daten:
        (site / "audit" / "siegel" / ("%s.svg" % dom)).write_text(siegel(dom, d, jetzt, regeln) + "\n", encoding="utf-8")
    return [("/audit/", "/en/audit/", max(d["stand"][:10] for _dom, d in daten))]
