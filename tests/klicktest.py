"""Klicktest der Seite: bedient sie im Browser und prüft feste Regeln.

Aufruf: python tests/klicktest.py            (braucht: pip install playwright && playwright install chromium)
Läuft nicht mit `unittest discover` (Dateiname ohne test_), weil er einen Browser braucht.
Geprüft wird in zwei Breiten (Handy 390, Desktop 1280) und zwei Sprachen:
  1. Laden ohne Skriptfehler, nichts ragt über den Rand, alle Teile sind zu.
  2. Jede Klappe einzeln auf: kein Fehler, kein Überstand.
  3. "Was betreue ich?": jeden Bereich nach jedem anderen wählen; Zahlen am Knopf, Listen und Knöpfe passen zusammen.
  4. Berichte: jeden Zeitraum in jeder Art wählen; jeder Bericht ist vollständig.
  5. Reiter in "neu", Direktlinks (?bericht=, #patches), Sprachknopf, eigene Berichtsseiten, Hinweiszeile für englische Browser.
  6. Am Ende, alles aufgeklappt: kein "undefined", "NaN" oder "[object" im Text, Sprungziele vorhanden, kein Knopf ohne Namen.
"""
import functools
import json
import http.server
import pathlib
import re
import sys
import threading

from playwright.sync_api import sync_playwright

SITE = pathlib.Path(__file__).resolve().parent.parent / "site"
BREITEN = ((390, 844, "Handy"), (1280, 900, "Desktop"))
# Sprache hängt an der Adresse. Der Browser meldet absichtlich die jeweils andere Sprache: sie darf nichts entscheiden.
SPRACHEN = (("en-US", "de", "/"), ("de-DE", "en", "/en/"))
MUELL = re.compile(r"undefined|NaN|\[object|\bnull\b")


class Pruefer:
    def __init__(self):
        self.fehler, self.geprueft, self.wo = [], 0, ""

    def ok(self, bedingung, text):
        self.geprueft += 1
        if not bedingung:
            self.fehler.append("%s: %s" % (self.wo, text))


def rand(pg):
    """Pixel, um die die Seite breiter ist als das Fenster (0 = nichts ragt über den Rand)."""
    return pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")


def lade(pg, url, p):
    pg.goto(url)
    pg.wait_for_function("document.getElementById('stand') && document.getElementById('stand').textContent.trim().length > 3", timeout=15000)
    pg.wait_for_timeout(500)
    p.ok(rand(pg) <= 1, "nach dem Laden ragt etwas %d px über den Rand" % rand(pg))


def menue_auf(pg):
    """Auf dem Handy liegen die Menüpunkte hinter dem Knopf „Menü“: aufklappen, falls zu."""
    if pg.locator("#menue-knopf").is_visible() and pg.get_attribute("#menue-knopf", "aria-expanded") != "true":
        pg.click("#menue-knopf")
        pg.wait_for_timeout(200)


def pruefe_klappen(pg, p):
    p.ok(pg.evaluate("[...document.querySelectorAll('details.teil')].every(d => !d.open)"), "ein Teil ist beim Laden schon aufgeklappt")
    n = pg.evaluate("document.querySelectorAll('main details').length")
    p.ok(n >= 10, "nur %d Klappen gefunden" % n)
    for i in range(n):
        name = pg.evaluate("""i => { const d = document.querySelectorAll('main details')[i];
            for (let e = d; e; e = e.parentElement) if (e.tagName === 'DETAILS') e.open = true;
            return d.id || (d.querySelector('summary') || {}).textContent || String(i); }""", i)
        pg.wait_for_timeout(30)
        r = rand(pg)
        p.ok(r <= 1, "Klappe „%s“ offen: %d px über dem Rand" % (str(name).strip()[:40], r))
    pg.evaluate("document.querySelectorAll('main details').forEach(d => d.open = false)")


def pruefe_bereiche(pg, p):
    pg.evaluate("document.getElementById('teil2').open = true; document.querySelectorAll('#teil2 details.sek').forEach(d => d.open = true)")
    pg.wait_for_timeout(100)
    ids = pg.evaluate("[...document.querySelectorAll('#p-bereich .b-btns button')].map(b => b.dataset.b)")
    p.ok(len(ids) >= 3 and ids[0] == "alle", "Bereichsknöpfe fehlen oder „Alle“ steht nicht vorn: %s" % ids)
    zustand = """() => { const box = document.getElementById('p-bereich'), an = [...box.querySelectorAll('.b-btns button[aria-pressed=true]')];
        const z = an[0] ? an[0].querySelector('.b-z').textContent.split('·').map(x => parseInt(x, 10)) : [];
        const li = [...box.querySelectorAll('ul.b-liste li')];
        return { an: an.map(b => b.dataset.b), patch: z[0], kev: z[1], rang: box.querySelectorAll('.b-zu ol li').length, rangLeer: !!box.querySelector('.b-zu p.dim'),
                 kevSichtbar: li.filter(x => !x.hidden && !x.classList.contains('dim')).length, kevAlle: li.filter(x => !x.classList.contains('dim')).length,
                 kevLeer: li.some(x => x.classList.contains('dim')), mehr: box.querySelectorAll('.b-mehr').length, kacheln: box.querySelectorAll('.b-k').length,
                 text: box.innerText }; }"""
    for a in ids:
        for b in ids:
            if a == b:
                continue
            pg.click("#p-bereich .b-btns button[data-b=%s]" % a)
            pg.click("#p-bereich .b-btns button[data-b=%s]" % b)
            z, weg = pg.evaluate(zustand), "erst „%s“, dann „%s“" % (a, b)
            p.ok(z["an"] == [b], "%s: gewählt ist %s" % (weg, z["an"]))
            p.ok(z["rang"] == min(z["patch"], 5) and (z["patch"] > 0 or z["rangLeer"]), "%s: Rangliste zeigt %d Einträge, am Knopf steht %d" % (weg, z["rang"], z["patch"]))
            p.ok(z["kevAlle"] == z["kev"] and z["kevLeer"] == (z["kev"] == 0), "%s: Liste „angegriffen“ hat %d Einträge, am Knopf steht %d" % (weg, z["kevAlle"], z["kev"]))
            soll_mehr = 1 if (b == "alle" and z["kev"] > 10) else 0
            p.ok(z["mehr"] == soll_mehr, "%s: Knopf „alle zeigen“ %d-mal vorhanden, erwartet %d" % (weg, z["mehr"], soll_mehr))
            p.ok(z["kevSichtbar"] == (min(z["kev"], 10) if b == "alle" else z["kev"]), "%s: %d sichtbare Einträge bei %d" % (weg, z["kevSichtbar"], z["kev"]))
            p.ok(not (b == "alle" and z["kacheln"]), "%s: Hersteller-Kacheln ohne gewählten Bereich" % weg)
            p.ok(not MUELL.search(z["text"]), "%s: Platzhalter im Text (%s)" % (weg, (MUELL.search(z["text"]) or [""])[0]))
            p.ok(rand(pg) <= 1, "%s: %d px über dem Rand" % (weg, rand(pg)))
    pg.click("#p-bereich .b-btns button[data-b=alle]")
    if pg.locator("#p-bereich .b-mehr").count():
        pg.click("#p-bereich .b-mehr")
        z = pg.evaluate(zustand)
        p.ok(z["kevSichtbar"] == z["kev"] and z["mehr"] == 0, "„alle zeigen“ zeigt %d von %d" % (z["kevSichtbar"], z["kev"]))
    pg.evaluate("document.querySelectorAll('main details').forEach(d => d.open = false)")


def pruefe_berichte(pg, p):
    pg.evaluate("document.getElementById('teilb').open = true; document.getElementById('k-berichte').open = true")
    pg.wait_for_selector("#br-box article", timeout=10000)
    gesamt = 0
    for art in ("monat", "quartal", "jahr"):
        pg.click("#br-art button[data-art=%s]" % art)
        werte = pg.evaluate("[...document.getElementById('br-wahl').options].map(o => o.value)")
        p.ok(len(werte) >= 1, "Berichte „%s“: keine Auswahl" % art)
        p.ok(pg.evaluate("document.querySelectorAll('#br-art [aria-selected=true]').length") == 1, "Berichte „%s“: nicht genau ein Reiter gewählt" % art)
        for w in werte:
            pg.select_option("#br-wahl", w)
            z = pg.evaluate("""() => { const a = document.querySelector('#br-box article'); if (!a) return null;
                return { titel: a.querySelector('h3').textContent, satz: a.querySelector('.br-satz').textContent, kz: a.querySelectorAll('.br-kz').length,
                         band: [...a.querySelectorAll('.br-band .sg')].reduce((s, x) => s + parseFloat(x.style.width), 0), zeilen: a.querySelectorAll('.br-tab tbody tr').length,
                         text: a.innerText, n: document.querySelectorAll('#br-box article').length }; }""")
            gesamt += 1
            if not z:
                p.ok(False, "Bericht %s: nichts angezeigt" % w)
                continue
            p.ok(z["n"] == 1 and z["titel"].strip() and len(z["satz"]) > 60, "Bericht %s: Kopf oder Satz fehlt" % w)
            p.ok(z["kz"] == 4 and z["zeilen"] >= 5, "Bericht %s: %d Kennzahlen, %d Bausteine" % (w, z["kz"], z["zeilen"]))
            p.ok(abs(z["band"] - 100) < 0.5, "Bericht %s: Band „Tage je Stufe“ ergibt %.1f %%" % (w, z["band"]))
            p.ok(not MUELL.search(z["text"]), "Bericht %s: Platzhalter im Text (%s)" % (w, (MUELL.search(z["text"]) or [""])[0]))
        p.ok(rand(pg) <= 1, "Berichte „%s“: %d px über dem Rand" % (art, rand(pg)))
    p.ok(gesamt >= 10, "nur %d Berichte" % gesamt)
    pg.evaluate("document.querySelectorAll('main details').forEach(d => d.open = false)")


def pruefe_reiter(pg, p):
    pg.evaluate("document.getElementById('teil2').open = true; document.querySelectorAll('#teil2 details.sek').forEach(d => d.open = true)")
    for t in pg.evaluate("[...document.querySelectorAll('#neu [role=tab]')].map(b => b.id)"):
        pg.click("#" + t)
        z = pg.evaluate("""t => { const b = document.getElementById(t), f = document.getElementById(b.getAttribute('aria-controls'));
            return { an: b.getAttribute('aria-selected'), feld: !!f && !f.hidden, offen: [...document.querySelectorAll('#neu [role=tabpanel]')].filter(x => !x.hidden).length }; }""", t)
        p.ok(z["an"] == "true" and z["feld"] and z["offen"] == 1, "Reiter %s: gewählt=%s, Feld sichtbar=%s, sichtbare Felder=%d" % (t, z["an"], z["feld"], z["offen"]))
    pg.evaluate("document.querySelectorAll('main details').forEach(d => d.open = false)")


def pruefe_alles_offen(pg, p):
    pg.evaluate("document.querySelectorAll('main details').forEach(d => d.open = true)")
    pg.wait_for_timeout(600)
    text = pg.evaluate("document.querySelector('main').innerText")
    m = MUELL.search(text)
    p.ok(not m, "Platzhalter im Text: „…%s…“" % (text[max(m.start() - 40, 0):m.end() + 20].replace("\n", " ") if m else ""))
    p.ok(rand(pg) <= 1, "alles offen: %d px über dem Rand" % rand(pg))
    tot = pg.evaluate("""[...document.querySelectorAll('a[href^="#"]')].map(a => a.getAttribute('href').slice(1)).filter(h => h && !document.getElementById(h))""")
    p.ok(not tot, "Sprungziele fehlen: %s" % sorted(set(tot))[:8])
    leer = pg.evaluate("""[...document.querySelectorAll('button, a[href]')].filter(b => b.offsetParent && !b.textContent.trim() && !b.getAttribute('aria-label') && !b.title && !b.querySelector('img,svg'))
        .map(b => b.outerHTML.slice(0, 80))""")
    p.ok(not leer, "Knopf oder Link ohne Namen: %s" % leer[:3])
    schlecht = pg.evaluate("""[...document.querySelectorAll('main a[href]')].map(a => a.getAttribute('href')).filter(h => /^(javascript:|undefined|null)/.test(h) || h === '')""")
    p.ok(not schlecht, "kaputte Links: %s" % schlecht[:3])


def pruefe_direktlinks(pg, basis, p):
    lade(pg, basis + "?bericht=2025", p)
    pg.wait_for_selector("#br-box article", timeout=10000)
    z = pg.evaluate("({offen: document.getElementById('k-berichte').open && document.getElementById('teilb').open, wahl: document.getElementById('br-wahl').value, art: document.querySelector('#br-art [aria-selected=true]').dataset.art})")
    p.ok(z == {"offen": True, "wahl": "2025", "art": "jahr"}, "Direktlink ?bericht=2025 zeigt %s" % z)
    lade(pg, basis + "#patches", p)
    pg.wait_for_timeout(400)
    p.ok(pg.evaluate("document.getElementById('teil2').open"), "#patches klappt Teil 2 nicht auf")
    p.ok(pg.evaluate("location.hash") == "", "#patches bleibt in der Adresse stehen")
    pg.reload()
    pg.wait_for_timeout(800)
    p.ok(not pg.evaluate("document.getElementById('teil2').open"), "Teil 2 ist nach dem Neuladen noch offen")


def pruefe_menue_und_kurztext(pg, basis, p):
    lade(pg, basis, p)
    kt = pg.evaluate("(() => { const k = document.getElementById('hero-kurz'); const h = document.getElementById('stufe-zahl'); "
                     "return {text: k.textContent.trim(), sichtbar: k.offsetHeight > 0, pegel: ((h.textContent.match(/(\\d+)\\s*\\/\\s*100/) || [])[1] || '')} })()")
    p.ok(kt["sichtbar"] and len(kt["text"]) > 40, "Kurztext unter dem Pegel fehlt oder ist leer: %s" % kt)
    p.ok(kt["pegel"] and (" " + kt["pegel"] + " ") in kt["text"], "Kurztext nennt nicht den Wert der Pegel-Karte (%s): %s" % (kt["pegel"], kt["text"]))
    for abschnitt, knopf in (("logbuch", "k-logbuch"), ("berichte", "k-berichte")):
        lade(pg, basis, p)
        menue_auf(pg)
        pg.click('.navin a[data-sec="%s"]' % abschnitt)
        pg.wait_for_timeout(1600)  # der Sprung läuft weich und ist bei langen Wegen nach 700 ms noch unterwegs
        z = pg.evaluate("({auf: document.getElementById('%s').open && document.getElementById('teilb').open, oben: Math.round(document.getElementById('%s').getBoundingClientRect().top)})" % (knopf, abschnitt))
        p.ok(z["auf"], "Menüpunkt /%s klappt den Abschnitt nicht auf" % abschnitt)
        p.ok(0 <= z["oben"] < 300, "Menüpunkt /%s springt nicht zum Abschnitt (oben bei %s px)" % (abschnitt, z["oben"]))
        p.ok(rand(pg) <= 1, "nach Menüsprung zu /%s %d px über dem Rand" % (abschnitt, rand(pg)))


def pruefe_menueknopf(pg, basis, p):
    lade(pg, basis, p)
    if not pg.locator("#menue-knopf").is_visible():
        p.ok(pg.locator("#n-audit").is_visible(), "Desktop: Menüpunkte müssen ohne Knopf sichtbar sein")
        return
    p.ok(not pg.locator("#n-audit").is_visible(), "Handy: Menüpunkte sind zugeklappt sichtbar")
    pg.click("#menue-knopf")
    p.ok(pg.locator("#n-audit").is_visible() and pg.locator('.navin a[data-sec="lage"]').is_visible(), "Handy: Menü öffnet nicht")
    p.ok(rand(pg) <= 1, "Handy: geöffnetes Menü %d px über dem Rand" % rand(pg))
    pg.keyboard.press("Escape")
    p.ok(not pg.locator("#n-audit").is_visible() and pg.get_attribute("#menue-knopf", "aria-expanded") == "false", "Handy: Escape schließt das Menü nicht")


def pruefe_sprachknopf(pg, basis, sprache, p):
    lade(pg, basis + "?bericht=2025", p)
    p.ok(pg.evaluate("document.documentElement.lang") == sprache, "Sprache ist %s statt %s" % (pg.evaluate("document.documentElement.lang"), sprache))
    andere = "en" if sprache == "de" else "de"
    menue_auf(pg)
    pg.click("#sprache")
    pg.wait_for_function("document.documentElement.lang === '%s'" % andere, timeout=10000)
    pg.wait_for_timeout(500)
    p.ok(pg.evaluate("document.getElementById('sprache').textContent.trim().toLowerCase()") == sprache, "Sprachknopf zeigt nach dem Wechsel nicht „%s“" % sprache.upper())
    pfad = pg.evaluate("location.pathname + location.search")
    p.ok(pfad == ("/en/" if andere == "en" else "/") + "?bericht=2025", "Sprachknopf führt nach %s" % pfad)
    kopf = pg.evaluate("({kanon: document.querySelector('link[rel=canonical]').href, titel: document.title, alt: document.querySelectorAll('link[hreflang]').length})")
    p.ok(kopf["kanon"].endswith("/en/" if andere == "en" else "cyberlage.org/") and kopf["alt"] == 3, "Kopf nach Sprachwechsel: %s" % kopf)
    p.ok(("threat level" in kopf["titel"]) == (andere == "en"), "Titel passt nicht zur Sprache: %s" % kopf["titel"])
    p.ok(rand(pg) <= 1, "nach Sprachwechsel %d px über dem Rand" % rand(pg))


def pruefe_berichtseiten(pg, wurzel, sprache, p):
    """Eigene Seiten je Bericht: Übersicht, eine Auswahl an Seiten, Nachbar-Links, Kopf."""
    pfad = "/en/bericht/" if sprache == "en" else "/bericht/"
    pg.goto(wurzel + pfad)
    ziele = pg.evaluate("[...document.querySelectorAll('.bs-liste a')].map(a => a.getAttribute('href'))")
    p.ok(len(ziele) >= 40 and all(z.startswith(pfad) for z in ziele), "Übersicht %s: %d Links" % (pfad, len(ziele)))
    p.ok(rand(pg) <= 1, "Übersicht %s: %d px über dem Rand" % (pfad, rand(pg)))
    for z in sorted(set(ziele[:4] + ziele[-2:] + ziele[len(ziele) // 2:len(ziele) // 2 + 2])):
        antwort = pg.goto(wurzel + z)
        d = pg.evaluate("""() => { const a = document.querySelector('article.br'); if (!a) return null;
            return { h1: a.querySelector('h1').textContent, satz: a.querySelector('.br-satz').textContent, kz: a.querySelectorAll('.br-kz').length,
                     band: [...a.querySelectorAll('.br-band .sg')].reduce((s, x) => s + parseFloat(x.style.width), 0), zeilen: a.querySelectorAll('.br-tab tbody tr').length,
                     kanon: document.querySelector('link[rel=canonical]').href, alt: document.querySelectorAll('link[hreflang]').length, lang: document.documentElement.lang,
                     skripte: document.querySelectorAll('script:not([type="application/ld+json"]):not([src="/matrix.js"])').length, text: document.body.innerText }; }""")
        p.ok(antwort.status == 200 and d is not None, "Berichtsseite %s lädt nicht" % z)
        if not d:
            continue
        p.ok(d["h1"].strip() and len(d["satz"]) > 60 and d["kz"] == 4 and d["zeilen"] >= 5, "Berichtsseite %s unvollständig" % z)
        p.ok(abs(d["band"] - 100) < 0.5, "Berichtsseite %s: Band ergibt %.1f %%" % (z, d["band"]))
        p.ok(d["kanon"].endswith(z) and d["alt"] == 3 and d["lang"] == sprache and d["skripte"] == 0, "Berichtsseite %s: Kopf %s" % (z, {k: d[k] for k in ("kanon", "alt", "lang", "skripte")}))
        p.ok(not MUELL.search(d["text"]), "Berichtsseite %s: Platzhalter im Text" % z)
        p.ok(rand(pg) <= 1, "Berichtsseite %s: %d px über dem Rand" % (z, rand(pg)))
    if pg.locator(".bs-nb a").count():
        ziel = pg.locator(".bs-nb a").first.get_attribute("href")
        pg.click(".bs-nb a >> nth=0")
        p.ok(pg.evaluate("location.pathname") == ziel and pg.locator("article.br").count() == 1, "Nachbar-Link führt nicht nach %s" % ziel)


def _pruefe_fuss_siegel(pg, pfad, p):
    """Web- und Code-Siegel im Fuß der Startseite: da, geladen, richtig verlinkt und beschriftet."""
    fs = pg.evaluate("""() => { const a = document.getElementById('fuss-siegel'); if (!a) return null; const i = a.querySelector('img');
        return { href: a.getAttribute('href'), text: a.querySelector('span').textContent, geladen: i.complete && i.naturalWidth > 0, sichtbar: a.offsetHeight > 0 }; }""")
    org = json.loads((SITE.parent / "data" / "audit" / "cyberlage.org.json").read_text(encoding="utf-8"))
    p.ok(fs is not None and fs["sichtbar"], "Siegel im Fuß der Startseite fehlt")
    if fs:
        p.ok(fs["href"] == pfad and fs["geladen"], "Siegel im Fuß: Link %s, Bild geladen: %s" % (fs["href"], fs["geladen"]))
        p.ok(fs["text"].startswith(("Web-Audit:", "Web audit:")) and (" %d / 100" % org["score"] in fs["text"] or "last run" in fs["text"] or "letzter Lauf" in fs["text"]), "Siegel im Fuß: Text %s" % fs["text"])
    cs = pg.evaluate("""() => { const a = document.getElementById('fuss-siegel-code'); if (!a) return null; const i = a.querySelector('img');
        return { href: a.getAttribute('href'), text: a.querySelector('span').textContent, geladen: i.complete && i.naturalWidth > 0, sichtbar: a.offsetHeight > 0 }; }""")
    p.ok(cs is not None and cs["sichtbar"], "Code-Siegel im Fuß der Startseite fehlt")
    if cs:
        p.ok(cs["href"] == pfad + "#code-audit" and cs["geladen"], "Code-Siegel im Fuß: Link %s, Bild geladen: %s" % (cs["href"], cs["geladen"]))
        p.ok(cs["text"].startswith(("Code-Audit:", "Code audit:")), "Code-Siegel im Fuß: Text %s" % cs["text"])
    p.ok(rand(pg) <= 1, "Fuß mit zwei Siegeln: %d px über dem Rand" % rand(pg))


def _pruefe_audit_karten(pg, sprache, pfad, p):
    """Karten, Kacheln, Zahlen und Kopf der Audit-Seite gegen data/audit und data/codeaudit."""
    daten = {}
    for f in sorted((SITE.parent / "data" / "audit").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        daten[d["domain"]] = d
    seite = pg.evaluate("""() => ({ karten: [...document.querySelectorAll('.au-karte')].map(k => ({ dom: k.querySelector('.au-dom').textContent, score: k.querySelector('.au-sc strong').textContent,
            code: k.querySelector('svg').textContent.includes('DREIER-CODE-SIEGEL'), svg: k.querySelectorAll('svg').length, svgtext: k.querySelector('svg').textContent, kacheln: k.nextElementSibling.querySelectorAll('.au-k').length })),
        skripte: document.querySelectorAll('script:not([type="application/ld+json"]):not([src="/matrix.js"])').length, lang: document.documentElement.lang, alt: document.querySelectorAll('link[hreflang]').length,
        kanon: document.querySelector('link[rel=canonical]').href, text: document.body.innerText })""")
    web = [k for k in seite["karten"] if not k["code"]]
    code = [k for k in seite["karten"] if k["code"]]
    p.ok(len(web) == len(daten) and len(daten) >= 2, "Audit-Seite zeigt %d Karten für %d Domains" % (len(web), len(daten)))
    cd = json.loads((SITE.parent / "data" / "codeaudit" / "cyberlage.org.json").read_text(encoding="utf-8"))
    p.ok(len(code) == 1 and code[0]["score"] == str(cd["score"]) and code[0]["svg"] == 1 and code[0]["kacheln"] == len(cd["gruppen"]), "Code-Audit auf der Audit-Seite: %s" % code)
    p.ok(pg.locator("#code-audit").count() == 1, "Code-Audit: Abschnitt mit Anker #code-audit fehlt")
    for k in web:
        d = daten.get(k["dom"])
        p.ok(d is not None and k["score"] == str(d["score"]), "Audit-Seite %s: Score %s statt %s" % (k["dom"], k["score"], d and d["score"]))
        p.ok(k["svg"] == 1 and "DREIER-WEB-SIEGEL" in k["svgtext"] and k["kacheln"] == 12, "Audit-Seite %s: Siegel oder Kacheln fehlen (%s)" % (k["dom"], {x: k[x] for x in ("svg", "kacheln")}))
    p.ok(seite["skripte"] == 0 and seite["lang"] == sprache and seite["alt"] == 3 and seite["kanon"].endswith(pfad), "Audit-Seite: Kopf %s" % {x: seite[x] for x in ("skripte", "lang", "alt", "kanon")})
    p.ok(not MUELL.search(seite["text"]), "Audit-Seite: Platzhalter im Text")
    zur = pg.locator(".bs-zurueck a")
    p.ok(zur.count() == 1 and zur.get_attribute("href") == ("/en/" if sprache == "en" else "/"), "Audit-Seite: Zurück-Link zum Dreier-Pegel fehlt")
    p.ok(rand(pg) <= 1, "Audit-Seite: %d px über dem Rand" % rand(pg))


def pruefe_auditseite(pg, wurzel, sprache, p):
    """Menüpunkt /audit führt auf die Audit-Seite in der Sprache; Siegel, Kacheln und Zahlen stimmen mit data/audit überein."""
    pfad = "/en/audit/" if sprache == "en" else "/audit/"
    lade(pg, wurzel + ("/en/" if sprache == "en" else "/"), p)
    p.ok(pg.locator("#n-audit").get_attribute("href") == pfad, "Menüpunkt /audit zeigt auf %s" % pg.locator("#n-audit").get_attribute("href"))
    p.ok(rand(pg) <= 1, "Menü mit /audit: %d px über dem Rand" % rand(pg))
    _pruefe_fuss_siegel(pg, pfad, p)
    menue_auf(pg)
    pg.click("#n-audit")
    pg.wait_for_load_state()
    p.ok(pg.evaluate("location.pathname") == pfad, "Menüpunkt /audit führt nach %s" % pg.evaluate("location.pathname"))
    _pruefe_audit_karten(pg, sprache, pfad, p)
    r = pg.request.get(wurzel + "/audit/siegel/cyberlage.org.svg")
    p.ok(r.status == 200 and "svg" in r.headers.get("content-type", ""), "Siegel-Datei: Status %s, Typ %s" % (r.status, r.headers.get("content-type")))


def pruefe_linkseite(pg, wurzel, sprache, p):
    """Menüpunkt /links führt auf die Linkseite in der Sprache; alle Einträge aus data/links.json stehen da, externe Links öffnen im neuen Tab."""
    pfad = "/en/links/" if sprache == "en" else "/links/"
    lade(pg, wurzel + ("/en/" if sprache == "en" else "/"), p)
    p.ok(pg.locator("#n-links").get_attribute("href") == pfad, "Menüpunkt /links zeigt auf %s" % pg.locator("#n-links").get_attribute("href"))
    p.ok(rand(pg) <= 1, "Menü mit /links: %d px über dem Rand" % rand(pg))
    menue_auf(pg)
    pg.click("#n-links")
    pg.wait_for_load_state()
    p.ok(pg.evaluate("location.pathname") == pfad, "Menüpunkt /links führt nach %s" % pg.evaluate("location.pathname"))
    daten = json.loads((SITE.parent / "data" / "links.json").read_text(encoding="utf-8"))
    seite = pg.evaluate("""() => ({ karten: document.querySelectorAll('.ln-k').length, skripte: document.querySelectorAll('script:not([type="application/ld+json"]):not([src="/matrix.js"])').length,
        lang: document.documentElement.lang, links: [...document.querySelectorAll('.ln-k h3 a')].map(a => ({ h: a.href, t: a.target, r: a.rel })), text: document.body.innerText })""")
    p.ok(seite["karten"] == len(daten["links"]), "Linkseite zeigt %d Karten für %d Einträge" % (seite["karten"], len(daten["links"])))
    p.ok(all(l["t"] == "_blank" and "noopener" in l["r"] for l in seite["links"]), "Linkseite: externe Links ohne neuen Tab")
    p.ok({l["h"] for l in seite["links"]} == {x["url"] for x in daten["links"]}, "Linkseite: Adressen weichen von data/links.json ab")
    p.ok(seite["skripte"] == 0 and seite["lang"] == sprache, "Linkseite: Skripte %d, Sprache %s" % (seite["skripte"], seite["lang"]))
    p.ok(not MUELL.search(seite["text"]), "Linkseite: Platzhalter im Text")
    zur = pg.locator(".bs-zurueck a")
    p.ok(zur.count() == 1 and zur.get_attribute("href") == ("/en/" if sprache == "en" else "/"), "Linkseite: Zurück-Link zum Dreier-Pegel fehlt")
    p.ok(rand(pg) <= 1, "Linkseite: %d px über dem Rand" % rand(pg))


def pruefe_en_zeile(pg, wurzel, sprache, p):
    """Hinweis für englische Browser: nur auf der deutschen Startseite, führt nach /en/, lässt sich dauerhaft ausblenden.
    Der Test-Browser meldet auf der deutschen Seite Englisch, auf der englischen Deutsch (siehe SPRACHEN)."""
    lade(pg, wurzel + ("/en/" if sprache == "en" else "/"), p)
    n = pg.locator(".en-zeile").count()
    if sprache == "en":
        p.ok(n == 0, "Hinweiszeile erscheint auf /en/")
        return
    p.ok(n == 1 and pg.locator(".en-zeile a").get_attribute("href").startswith("/en/"), "Hinweiszeile für englische Browser fehlt (%d)" % n)
    p.ok(rand(pg) <= 1, "Hinweiszeile: %d px über dem Rand" % rand(pg))
    pg.click(".en-zeile button")
    p.ok(pg.locator(".en-zeile").count() == 0, "Hinweiszeile bleibt nach dem Ausblenden stehen")
    pg.reload()
    pg.wait_for_timeout(600)
    p.ok(pg.locator(".en-zeile").count() == 0, "Hinweiszeile kommt nach dem Neuladen wieder")


def main():
    class Still(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Still, directory=str(SITE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    basis = "http://127.0.0.1:%d" % server.server_port
    p = Pruefer()
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for locale, sprache, pfad in SPRACHEN:
            for breite, hoehe, name in BREITEN:
                p.wo = "%s %s" % (name, sprache.upper())
                ctx = browser.new_context(viewport={"width": breite, "height": hoehe}, locale=locale)
                pg = ctx.new_page()
                skript = []
                pg.on("pageerror", lambda e, s=skript: s.append(str(e)[:200]))
                pg.on("console", lambda m, s=skript: s.append(m.text[:200]) if m.type == "error" and "favicon" not in m.text else None)
                schritte = (("Klappen", lambda: pruefe_klappen(pg, p)), ("Bereiche", lambda: pruefe_bereiche(pg, p)), ("Berichte", lambda: pruefe_berichte(pg, p)),
                            ("Reiter", lambda: pruefe_reiter(pg, p)), ("Alles offen", lambda: pruefe_alles_offen(pg, p)),
                            ("Direktlinks", lambda: pruefe_direktlinks(pg, basis + pfad, p)), ("Sprachknopf", lambda: pruefe_sprachknopf(pg, basis + pfad, sprache, p)),
                            ("Menü und Kurztext", lambda: pruefe_menue_und_kurztext(pg, basis + pfad, p)), ("Menüknopf", lambda: pruefe_menueknopf(pg, basis + pfad, p)), ("Berichtsseiten", lambda: pruefe_berichtseiten(pg, basis, sprache, p)), ("Audit-Seite", lambda: pruefe_auditseite(pg, basis, sprache, p)), ("Linkseite", lambda: pruefe_linkseite(pg, basis, sprache, p)), ("Hinweiszeile", lambda: pruefe_en_zeile(pg, basis, sprache, p)))
                try:
                    lade(pg, basis + pfad, p)
                    p.ok(pg.evaluate("document.documentElement.lang") == sprache, "Sprache der Seite %s ist %s" % (pfad, pg.evaluate("document.documentElement.lang")))
                    for titel, schritt in schritte:
                        try:
                            schritt()
                        except Exception as e:  # ein Schritt, der abbricht, ist ein Befund; die übrigen laufen weiter
                            p.ok(False, "%s abgebrochen: %s" % (titel, str(e).splitlines()[0][:200]))
                            lade(pg, basis + pfad, p)
                except Exception as e:
                    p.ok(False, "Seite nicht ladbar: %s" % str(e).splitlines()[0][:200])
                p.ok(not skript, "Skriptfehler: %s" % skript[:3])
                ctx.close()
        browser.close()
    server.shutdown()
    print("Klicktest: %d Prüfungen, %d Fehler" % (p.geprueft, len(p.fehler)))
    for f in p.fehler[:60]:
        print("  FEHLER", f)
    return 1 if p.fehler else 0


if __name__ == "__main__":
    sys.exit(main())
