import sys
import tempfile
import unittest
from unittest import mock
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "audit"))

import dateien  # noqa: E402
import dns  # noqa: E402
import fremd  # noqa: E402
import kopfzeilen  # noqa: E402
import tls  # noqa: E402
import lauf  # noqa: E402
import auswertung as score  # noqa: E402

GUT = {"Strict-Transport-Security": "max-age=31536000", "Content-Security-Policy":
       "default-src 'none'; script-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'",
       "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer", "Permissions-Policy": "camera=()", "Server": "cloudflare"}


class AuditTests(unittest.TestCase):
    def test_gute_kopfzeilen(self):
        erg = kopfzeilen.pruefe(GUT)
        self.assertTrue(all(e[2] == "bestanden" for e in erg), [e for e in erg if e[2] != "bestanden"])

    def test_schlechte_kopfzeilen(self):
        erg = {e[1]: e[2] for e in kopfzeilen.pruefe({"Server": "Apache/2.4.1", "Content-Security-Policy": "script-src 'unsafe-inline'"})}
        self.assertEqual(erg["csp-skript"], "nicht_bestanden")
        self.assertEqual(erg["hsts-da"], "nicht_bestanden")
        self.assertEqual(erg["server-version"], "hinweis")

    def test_score_nur_teilweise_geprueft_wird_nicht_bewertet(self):
        r = score.rechne(kopfzeilen.pruefe(GUT))
        self.assertIsNone(r["score"])
        self.assertEqual(r["teilwert"], 100)
        self.assertLess(r["abdeckung"], 0.9)

    def test_score_voll_und_deckel(self):
        alle = [(g, g, "bestanden", "") for g in score.REGELN["gruppen"]]
        self.assertEqual(score.rechne(alle)["score"], 100)
        self.assertEqual(score.rechne(alle)["stufe"], "ohne Befund")
        kaputt = [(g, g, "nicht_bestanden" if g == "tls" else "bestanden", "") for g in score.REGELN["gruppen"]]
        self.assertLessEqual(score.rechne(kaputt)["score"], 59)

    def test_gewichte_ergeben_100(self):
        self.assertEqual(sum(g["gewicht"] for g in score.REGELN["gruppen"].values()), 100)


class DateiTlsTests(unittest.TestCase):
    JETZT = datetime(2026, 11, 26, tzinfo=timezone.utc)

    def erg(self, liste):
        return {e[1]: e[2] for e in liste}

    def test_security_txt_gut_schlecht(self):
        gut = "Contact: mailto:a@b.de\nExpires: 2027-11-26T00:00:00.000Z\n"
        self.assertTrue(all(v == "bestanden" for v in self.erg(dateien.security_txt(200, "text/plain; charset=utf-8", gut, self.JETZT)).values()))
        alt = self.erg(dateien.security_txt(200, "text/plain", "Contact: x\nExpires: 2026-01-01T00:00:00Z", self.JETZT))
        self.assertEqual(alt["sectxt-expires"], "nicht_bestanden")
        fern = self.erg(dateien.security_txt(200, "text/plain", "Contact: x\nExpires: 2030-01-01T00:00:00Z", self.JETZT))
        self.assertEqual(fern["sectxt-expires"], "hinweis")
        ohne = self.erg(dateien.security_txt(200, "text/html", "nichts", self.JETZT))
        self.assertEqual((ohne["sectxt-contact"], ohne["sectxt-expires"], ohne["sectxt-typ"]), ("nicht_bestanden", "nicht_bestanden", "hinweis"))
        self.assertEqual(dateien.security_txt(404, None, "", self.JETZT)[0][2], "nicht_bestanden")

    def test_sitemap(self):
        xml = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://x.de/</loc></url><url><loc>https://fremd.de/a</loc></url></urlset>'
        self.assertEqual(dateien.sitemap_adressen(xml, "x.de")[0], ["https://x.de/"])
        self.assertEqual(dateien.sitemap_adressen("kein xml", "x.de")[1], "kein gültiges XML")
        self.assertEqual(self.erg(dateien.sitemap(200, xml, "x.de", {"https://x.de/": 200}))["sitemap-antworten"], "bestanden")
        self.assertEqual(self.erg(dateien.sitemap(200, xml, "x.de", {"https://x.de/": 404}))["sitemap-antworten"], "nicht_bestanden")
        self.assertEqual(self.erg(dateien.sitemap(200, "<x/>", "x.de"))["sitemap-da"], "nicht_bestanden")

    def test_robots(self):
        self.assertEqual(self.erg(dateien.robots(200, "User-agent: *\nSitemap: https://x.de/sitemap.xml"))["robots-sitemap"], "bestanden")
        self.assertEqual(self.erg(dateien.robots(200, "User-agent: *"))["robots-sitemap"], "hinweis")

    def test_tls_versionen(self):
        gut = self.erg(tls.versionen({"TLSv1": "nein", "TLSv1.1": "nein", "TLSv1.2": "ja", "TLSv1.3": "ja"}))
        self.assertEqual((gut["tls13"], gut["tls-alt-aus"]), ("bestanden", "bestanden"))
        schlecht = self.erg(tls.versionen({"TLSv1": "ja", "TLSv1.1": "nein", "TLSv1.3": "nein"}))
        self.assertEqual((schlecht["tls13"], schlecht["tls-alt-aus"]), ("hinweis", "nicht_bestanden"))
        unklar = self.erg(tls.versionen({"TLSv1": "unklar", "TLSv1.1": "nein", "TLSv1.3": "ja"}))
        self.assertEqual(unklar["tls-alt-aus"], "nicht_geprueft")

    def test_zertifikat_und_weiterleitung(self):
        cert = {"notAfter": "Feb 21 21:09:42 2027 GMT"}
        self.assertEqual(self.erg(tls.zertifikat(cert, self.JETZT, True))["zert-laufzeit"], "bestanden")
        self.assertEqual(self.erg(tls.zertifikat({"notAfter": "Nov 30 00:00:00 2026 GMT"}, self.JETZT, True))["zert-laufzeit"], "hinweis")
        self.assertEqual(self.erg(tls.zertifikat({"notAfter": "Nov 01 00:00:00 2026 GMT"}, self.JETZT, True))["zert-laufzeit"], "nicht_bestanden")
        self.assertEqual(self.erg(tls.zertifikat(None, self.JETZT, False))["zert-kette"], "nicht_bestanden")
        self.assertEqual(tls.weiterleitung(301, "https://x.de/", "x.de")[0][2], "bestanden")
        self.assertEqual(tls.weiterleitung(302, "https://x.de/", "x.de")[0][2], "hinweis")
        self.assertEqual(tls.weiterleitung(301, "https://fremd.de/", "x.de")[0][2], "nicht_bestanden")
        self.assertEqual(tls.weiterleitung(200, None, "x.de")[0][2], "nicht_bestanden")
        self.assertEqual(tls.weiterleitung(None, None, "x.de")[0][2], "nicht_geprueft")

    def test_nicht_geprueft_senkt_abdeckung_nicht_den_score(self):
        alle = [(g, g, "bestanden", "") for g in score.REGELN["gruppen"]]
        alle.append(("tls", "extra", "nicht_geprueft", ""))
        r = score.rechne(alle)
        self.assertEqual(r["score"], 100)
        self.assertEqual(r["nicht_geprueft"], ["extra"])

    def test_ohne_erreichbarkeit_kein_ergebnis(self):
        with mock.patch.object(lauf.abruf, "hole", return_value=(None, {}, "", None)):
            self.assertEqual(lauf.main(["cyberlage.org"]), 3)

    def test_nur_eigene_domains(self):
        self.assertEqual(lauf.main(["fremde-seite.example"]), 2)


class DnsFremdTests(unittest.TestCase):
    def erg(self, liste):
        return {e[1]: e[2] for e in liste}

    def test_spf(self):
        self.assertEqual(dns.spf(['"v=spf1 -all"'], True)[0][2], "bestanden")
        self.assertEqual(dns.spf(['"v=spf1 include:x ~all"'], True)[0][2], "hinweis")
        self.assertEqual(dns.spf(['"google-site-verification=abc"'])[0][2], "nicht_bestanden")
        self.assertEqual(dns.spf(['"v=spf1 -all"', '"v=spf1 ~all"'])[0][2], "nicht_bestanden")
        self.assertEqual(dns.spf(['"v=spf1 a "mx" -all"'])[0][2] in ("bestanden", "hinweis"), True)

    def test_dmarc(self):
        self.assertEqual(dns.dmarc(['"v=DMARC1; p=reject; adkim=s"'])[0][2], "bestanden")
        self.assertEqual(dns.dmarc(['"v=DMARC1; p=none"'])[0][2], "hinweis")
        self.assertEqual(dns.dmarc([])[0][2], "nicht_bestanden")

    def test_caa_und_dnssec(self):
        self.assertEqual(dns.caa([])[0][2], "hinweis")
        self.assertEqual(dns.caa(['0 issue "pki.goog"'])[0][2], "bestanden")
        self.assertEqual(dns.caa(None)[0][2], "nicht_geprueft")
        self.assertEqual(dns.dnssec([], False)[0][2], "nicht_bestanden")
        self.assertEqual(dns.dnssec(["2371 13 2 abc"], True)[0][2], "bestanden")
        self.assertEqual(dns.dnssec(["2371 13 2 abc"], False)[0][2], "nicht_bestanden")
        self.assertEqual(dns.dnssec(None, False)[0][2], "nicht_geprueft")

    def test_fremde_inhalte(self):
        sauber = '<script src="/app.js"></script><link rel="stylesheet" href="/s.css"><img src="/a.png"><a href="https://fremd.de">x</a>'
        r = self.erg(fremd.fremde_inhalte(sauber, "x.de", {}))
        self.assertTrue(all(v == "bestanden" for v in r.values()), r)
        schlecht = '<script src="https://cdn.fremd.de/a.js"></script><img src="http://x.de/a.png">'
        r = self.erg(fremd.fremde_inhalte(schlecht, "x.de", {"access-control-allow-origin": "*"}))
        self.assertEqual((r["gemischt"], r["fremde-skripte"], r["sri"], r["cors"]), ("nicht_bestanden", "nicht_bestanden", "nicht_bestanden", "hinweis"))
        mit = self.erg(fremd.fremde_inhalte('<script src="https://c.de/a.js" integrity="sha384-x"></script>', "x.de", {}))
        self.assertEqual(mit["sri"], "bestanden")

    def test_cookies(self):
        self.assertEqual(fremd.cookies({})[0][2], "nicht_zutreffend")
        r = self.erg(fremd.cookies({"set-cookie": "sid=1; Secure; HttpOnly; SameSite=Lax\nx=2"}))
        self.assertEqual((r["secure-sid"], r["httponly-sid"], r["samesite-sid"], r["secure-x"]), ("bestanden", "bestanden", "bestanden", "nicht_bestanden"))

    def test_nicht_zutreffend_zaehlt_fuer_abdeckung(self):
        alle = [(g, g, "bestanden", "") for g in score.REGELN["gruppen"] if g != "cookies"] + [("cookies", "keine", "nicht_zutreffend", "")]
        r = score.rechne(alle)
        self.assertEqual((r["score"], r["abdeckung"]), (100, 1.0))


class MeldungTests(unittest.TestCase):
    ALT = {"score": 100, "stufe": "ohne Befund", "befunde": 0, "hinweise": 0, "nicht_geprueft": 0, "gruppen": {"tls": 1.0}, "stand": "2026-11-26T05:20Z"}

    def test_nur_bei_aenderung(self):
        neu = dict(self.ALT, stand="2026-11-27T05:20Z")
        self.assertFalse(lauf.hat_sich_geaendert(self.ALT, neu))  # nur der Zeitstempel ist neu
        self.assertTrue(lauf.hat_sich_geaendert(self.ALT, dict(neu, score=94)))
        self.assertTrue(lauf.hat_sich_geaendert(self.ALT, dict(neu, befunde=1)))
        self.assertTrue(lauf.hat_sich_geaendert(self.ALT, dict(neu, gruppen={"tls": 0.5})))
        self.assertTrue(lauf.hat_sich_geaendert(None, neu))


class TestmeldungTests(unittest.TestCase):
    def test_immer_sendet_auch_ohne_aenderung(self):
        gespeichert = []
        erg = [("tls", "x", "bestanden", "")]
        with mock.patch.object(lauf, "pruefe", return_value=erg), mock.patch.object(lauf, "_sende", side_effect=gespeichert.append), \
                tempfile.TemporaryDirectory() as tmp:
            ziel = str(Path(tmp) / "a.json")
            lauf.main(["cyberlage.org", "--zusammenfassung", ziel, "--telegram"])  # erster Lauf: gilt als geändert
            n = len(gespeichert)
            lauf.main(["cyberlage.org", "--zusammenfassung", ziel, "--telegram"])  # unverändert: still
            self.assertEqual(len(gespeichert), n)
            lauf.main(["cyberlage.org", "--zusammenfassung", ziel, "--telegram", "--immer"])
            self.assertEqual(len(gespeichert), n + 1)
            self.assertIn("Test der Meldung", gespeichert[-1])


class KanalTests(unittest.TestCase):
    def test_audit_geht_nur_in_den_audit_kanal(self):
        env = {"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "lage"}
        with mock.patch.dict(lauf.os.environ, env, clear=True), mock.patch.object(lauf.notify, "sende") as sende:
            lauf._sende("x")
            sende.assert_not_called()  # ohne eigenen Audit-Kanal wird nichts an den Lage-Kanal gesendet
        with mock.patch.dict(lauf.os.environ, dict(env, TELEGRAM_AUDIT_CHAT_ID="audit"), clear=True), mock.patch.object(lauf.notify, "sende") as sende:
            lauf._sende("x")
            sende.assert_called_once_with("x", "t", "audit")


class WeiterleitungTests(unittest.TestCase):
    PFAD = "/hinweise?pruefung=weiterleitung"
    ZIEL = "https://cyberlage.org" + PFAD

    def test_ziel(self):
        z = lambda st, ort: tls.ziel_weiterleitung(st, ort, "cyberlage.org", self.PFAD)[0][2]
        self.assertEqual(z(301, self.ZIEL), "bestanden")
        self.assertEqual(z(308, self.ZIEL), "bestanden")
        self.assertEqual(z(302, self.ZIEL), "hinweis")
        self.assertEqual(z(301, "https://cyberlage.org/"), "hinweis")  # Pfad geht verloren
        self.assertEqual(z(301, "https://fremd.example/hinweise"), "nicht_bestanden")
        self.assertEqual(z(301, "https://cyberlage.org.fremd.example/"), "nicht_bestanden")
        self.assertEqual(z(200, None), "nicht_bestanden")
        self.assertEqual(z(None, None), "nicht_geprueft")

    def test_http(self):
        h = lambda st, ort: tls.http_zu_https_domain(st, ort, "cyberlage.com", "cyberlage.org")[0][2]
        self.assertEqual(h(301, "https://cyberlage.com/x"), "bestanden")
        self.assertEqual(h(301, "https://cyberlage.org/x"), "bestanden")
        self.assertEqual(h(302, "https://cyberlage.org/x"), "hinweis")
        self.assertEqual(h(301, "http://cyberlage.org/x"), "nicht_bestanden")
        self.assertEqual(h(200, None), "nicht_bestanden")
        self.assertEqual(h(None, None), "nicht_geprueft")

    def test_null_mx(self):
        self.assertEqual(dns.null_mx(["0 ."])[0][2], "bestanden")
        self.assertEqual(dns.null_mx([])[0][2], "hinweis")
        self.assertEqual(dns.null_mx(["10 mail.example."])[0][2], "nicht_bestanden")
        self.assertEqual(dns.null_mx(["0 .", "10 mail.example."])[0][2], "nicht_bestanden")
        self.assertEqual(dns.null_mx(None)[0][2], "nicht_geprueft")

    def lauf(self, ort=None, mx=("0 .",)):
        ort = ort or self.ZIEL
        zert = {"notAfter": "Feb 21 21:09:42 2027 GMT"}
        def hole(host, pfad="/", https=True):
            if host == "cyberlage.org":
                return 200, {}, "", None
            if not https:
                return 301, {}, "", "https://cyberlage.org/"
            return 301, {"strict-transport-security": "max-age=31536000", "server": "cloudflare"}, "", ort
        def doh(name, typ):
            return {"CAA": ['0 issue "pki.goog"'], "DS": ["2371 13 2 abc"], "A": ([], True), "MX": list(mx),
                    "TXT": ['"v=spf1 -all"'] if not name.startswith("_dmarc") else ['"v=DMARC1; p=reject"']}[typ], True
        with mock.patch.object(lauf.abruf, "hole", side_effect=hole), mock.patch.object(lauf.abruf, "zertifikat", return_value=(zert, True)), \
                mock.patch.object(lauf.abruf, "versionen", return_value={"TLSv1": "nein", "TLSv1.1": "nein", "TLSv1.2": "ja", "TLSv1.3": "ja"}), \
                mock.patch.object(lauf.abruf, "doh", side_effect=lambda n, t: (doh(n, t)[0] if t != "A" else doh(n, t)[0][0], doh(n, t)[1] if t != "A" else True)):
            erg = lauf.pruefe_weiterleitung("cyberlage.com", "cyberlage.org", datetime(2026, 11, 26, tzinfo=timezone.utc))
        return erg, score.rechne(erg)

    def test_voller_lauf_score_100(self):
        erg, r = self.lauf()
        self.assertEqual((r["score"], r["abdeckung"], r["stufe"]), (100, 1.0, "ohne Befund"), [e for e in erg if e[2] not in ("bestanden", "nicht_zutreffend")])

    def test_falsches_ziel_ist_befund(self):
        erg, r = self.lauf(ort="https://fremd.example/")
        self.assertEqual([e[1] for e in erg if e[2] == "nicht_bestanden"], ["ziel", "www-ziel"])
        self.assertNotEqual(r["stufe"], "ohne Befund")

    def test_fehlender_null_mx_ist_nur_hinweis(self):
        _erg, r = self.lauf(mx=())
        self.assertTrue(90 <= r["score"] < 100, r)

    def test_profile(self):
        self.assertEqual(lauf.WEITERLEITUNG, {"cyberlage.com": "cyberlage.org"})
        self.assertTrue(set(lauf.WEITERLEITUNG) <= lauf.ERLAUBT and set(lauf.WEITERLEITUNG.values()) <= lauf.ERLAUBT)
        self.assertEqual(set(lauf.NICHT_ZUTREFFEND), {"csp", "fremd", "inhalt", "datenschutz", "altlasten", "auffindbar"})


if __name__ == "__main__":
    unittest.main()
