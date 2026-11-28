"""Tests für fetch_historie (mit Fake-Abruf und Temp-Ordner), codeaudit/lauf.py und quellen_test. Kein Netz."""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "pipeline"))
sys.path.insert(0, str(WURZEL))

import fetch_historie as fh  # noqa: E402
import quellen_test  # noqa: E402
from codeaudit import lauf  # noqa: E402

JETZT = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)


class HistorieBasis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        p = mock.patch.object(fh, "ZIEL", Path(self.tmp.name))
        p.start()
        self.addCleanup(p.stop)


class DateienTest(HistorieBasis):
    def test_schreiben_und_lesen(self):
        fh.schreibe("x.json", {"b": 1, "a": [1, 2]})
        self.assertEqual(fh.lese("x.json"), {"a": [1, 2], "b": 1})
        self.assertEqual(fh.lese("fehlt.json"), {})
        (Path(self.tmp.name) / "kaputt.json").write_text("{", encoding="utf-8")
        self.assertEqual(fh.lese("kaputt.json"), {})

    def test_lade_lehnt_http_ab(self):
        with self.assertRaises(ValueError):
            fh.lade("http://example.org/x")


class CertTest(HistorieBasis):
    def seite(self, *eintraege):
        return {"content": [{"name": n, "published": d, "classification": k} for n, d, k in eintraege]}

    def test_parse(self):
        s = self.seite(("WID-SEC-2026-1", "2026-11-20T10:00:00Z", "Kritisch"), ("WID-SEC-2026-2", "2026-11-19", "hoch"), ("falsch", "2026-11-19", "hoch"), ("WID-SEC-2026-3", "kaputt", "hoch"), ("WID-SEC-2026-4", "2026-11-18", "unbekannt"))
        self.assertEqual(fh.parse_cert(s), {"WID-SEC-2026-1": ["2026-11-20", "k"], "WID-SEC-2026-2": ["2026-11-19", "h"]})
        self.assertEqual(fh.parse_cert(None), {})

    def test_holen_blaettert_bis_zur_grenze(self):
        seiten = [self.seite(("WID-SEC-2026-1", "2026-11-20", "hoch")), self.seite(("WID-SEC-2020-1", "2020-01-01", "mittel"))]
        aufrufe = []

        def lade(url):
            aufrufe.append(url)
            return json.dumps(seiten[len(aufrufe) - 1]).encode()
        meldung = fh.hole_cert(JETZT, lade=lade, pause=0)
        self.assertEqual(len(aufrufe), 2)
        self.assertIn("2 Meldungen", meldung)
        d = fh.lese("cert_bund.json")
        self.assertEqual(set(d["eintraege"]), {"WID-SEC-2026-1", "WID-SEC-2020-1"})
        self.assertTrue(d["vollstaendig_bis"])

    def test_zweiter_lauf_blaettert_nur_kurz_zurueck(self):
        fh.schreibe("cert_bund.json", {"abgerufen_am": "2026-11-26T00:00:00+00:00", "vollstaendig_bis": "2023-10-01", "eintraege": {"WID-SEC-2026-9": ["2026-11-01", "h"]}})
        n = []

        def lade(url):
            n.append(1)
            return json.dumps(self.seite(("WID-SEC-2026-1", "2026-11-10", "hoch"))).encode()
        fh.hole_cert(JETZT, lade=lade, pause=0)
        self.assertEqual(len(n), 1)
        self.assertEqual(len(fh.lese("cert_bund.json")["eintraege"]), 2)

    def test_leere_antwort_beendet(self):
        fh.hole_cert(JETZT, lade=lambda u: b'{"content": []}', pause=0)
        self.assertEqual(fh.lese("cert_bund.json")["eintraege"], {})


class NcscTest(HistorieBasis):
    def test_parse_und_holen(self):
        text = "2026/ncsc-2026-0001.json,2026-11-20T10:00:00Z\n2026/ncsc-2026-0002.json,2026-11-21\nkurz\nx.json,2026-01-01\n"
        self.assertEqual(fh.parse_ncsc(text), {"NCSC-2026-0001": "2026-11-20", "NCSC-2026-0002": "2026-11-21"})
        self.assertIn("2 Advisories", fh.hole_ncsc(JETZT, lade=lambda u: text.encode()))
        with self.assertRaises(ValueError):
            fh.hole_ncsc(JETZT, lade=lambda u: b"nichts")


class EuTest(HistorieBasis):
    def test_holen(self):
        import fetch_extra
        with mock.patch.object(fetch_extra, "parse_eu", return_value={"EUVD-1": {"ausgenutzt_seit": "2026-11-01"}}):
            self.assertIn("1 Einträge", fh.hole_eu(JETZT, lade=lambda u: b"{}", pause=0))
        self.assertEqual(fh.lese("eu_kev.json")["eintraege"], {"EUVD-1": "2026-11-01"})

    def test_quellfehler_beendet_ohne_absturz(self):
        import fetch_extra
        fh.schreibe("eu_kev.json", {"eintraege": {"EUVD-0": "2026-01-01"}})
        with mock.patch.object(fetch_extra, "parse_eu", side_effect=fetch_extra.QuellFehler("x")):
            self.assertIn("1 Einträge", fh.hole_eu(JETZT, lade=lambda u: b"{}", pause=0))


class DshieldRansomTest(HistorieBasis):
    def test_parse_dshield(self):
        d = [{"date": "2026-11-20", "records": "5", "targets": 2, "sources": 3}, {"date": "x", "records": 1, "targets": 1, "sources": 1}, {"date": "2026-11-21", "records": "a", "targets": 1, "sources": 1}, "kaputt"]
        self.assertEqual(fh.parse_dshield(d), {"2026-11-20": [5, 2, 3]})
        self.assertEqual(fh.parse_dshield({"x": d}), {"2026-11-20": [5, 2, 3]})
        self.assertEqual(fh.parse_dshield(None), {})

    def test_hole_dshield(self):
        antwort = json.dumps([{"date": "2026-11-20", "records": 5, "targets": 2, "sources": 3}]).encode()
        with mock.patch.object(fh.time, "sleep"):
            self.assertIn("1 Tage", fh.hole_dshield(JETZT, lade=lambda u: antwort, pause=0))
            self.assertIn("2026-11-20", fh.lese("dshield.json")["tage"])
            with self.assertRaises(ValueError):
                self.setUp()
                fh.hole_dshield(JETZT, lade=lambda u: b"[]", pause=0)

    def test_parse_ransom(self):
        d = {"a": [{"discovered": "2026-11-20 10:00", "name": "x"}, {"discovered": "2026-11-20", "x": {"discovered": "2026-11-19"}}], "b": {"discovered": "kaputt"}}
        self.assertEqual(fh.parse_ransom(d), {"2026-11-20": 2, "2026-11-19": 1})

    def test_hole_ransom(self):
        antwort = json.dumps([{"discovered": "2026-11-19"}, {"discovered": "2026-11-20"}, {"discovered": "2026-11-20"}]).encode()
        self.assertIn("2 Tage", fh.hole_ransom(JETZT, lade=lambda u, timeout=0: antwort))
        t = fh.lese("ransomware.json")["tage"]
        self.assertEqual(t["2026-11-20"], 2)
        with self.assertRaises(ValueError):
            fh.hole_ransom(JETZT, lade=lambda u, timeout=0: b"[]")

    def test_main_meldet_fehler_je_quelle(self):
        def kaputt(jetzt):
            raise ValueError("nein")
        with mock.patch.object(fh, "hole_ncsc", kaputt), mock.patch.object(fh, "hole_cert", lambda j: "ok"):
            ein = io.StringIO()
            with redirect_stdout(ein):
                rc = fh.main(["ncsc", "cert"])
            self.assertEqual(rc, 1)
            self.assertIn("FEHLER ncsc: nein", ein.getvalue())
            self.assertIn("OK: ok", ein.getvalue())


class LaufTest(unittest.TestCase):
    def test_json_aus(self):
        self.assertEqual(lauf.json_aus('{"a":1}'), {"a": 1})
        self.assertIsNone(lauf.json_aus("kein json"))

    def test_starte_fehlendes_werkzeug(self):
        self.assertEqual(lauf.starte(["gibt-es-nicht-xyz"]), (None, ""))
        rc, aus = lauf.starte([sys.executable, "-c", "print('hallo')"])
        self.assertEqual((rc, aus.strip()), (0, "hallo"))

    def test_starte_zeitueberschreitung(self):
        with mock.patch.object(lauf, "ZEIT", 0.2):
            self.assertEqual(lauf.starte([sys.executable, "-c", "import time; time.sleep(5)"]), (None, ""))

    def test_gitleaks_ohne_werkzeug(self):
        with mock.patch.object(lauf, "starte", return_value=(None, "")):
            self.assertIsNone(lauf.gitleaks(True))

    def test_gitleaks_mit_bericht(self):
        def falsch(befehl, **kw):
            Path(befehl[befehl.index("--report-path") + 1]).write_text("[]", encoding="utf-8")
            return 0, ""
        with mock.patch.object(lauf, "starte", falsch):
            self.assertEqual(lauf.gitleaks(False), [])

    def test_zusammenfassung(self):
        erg = [("geheimnisse", "a", "bestanden", ""), ("tests", "b", "hinweis", "x"), ("workflows", "c", "nicht_geprueft", "")]
        z = lauf.zusammenfassung(erg, JETZT)
        self.assertEqual((z["stand"], z["regeln"], z["hinweise"], z["befunde"]), ("2026-11-27T12:00Z", "1.0", 1, 0))
        self.assertEqual(z["nicht_geprueft"], 1)

    def test_tests_ohne_coverage(self):
        with mock.patch.object(lauf.shutil, "which", return_value=None), mock.patch.object(lauf, "starte", return_value=(0, "")):
            self.assertTrue(lauf.tests())
        with mock.patch.object(lauf.shutil, "which", return_value=None), mock.patch.object(lauf, "starte", return_value=(None, "")):
            self.assertTrue(lauf.tests())

    def test_tests_mit_coverage_ohne_lauf(self):
        with mock.patch.object(lauf.shutil, "which", return_value="/x/coverage"), mock.patch.object(lauf, "starte", return_value=(None, "")):
            self.assertTrue(lauf.tests())

    def test_tests_mit_coverage_und_bericht(self):
        def fake(befehl, **kw):
            if befehl[1] == "json":
                Path(befehl[befehl.index("-o") + 1]).write_text(json.dumps({"totals": {"percent_covered": 85.0}}), encoding="utf-8")
            return 0, ""
        with mock.patch.object(lauf.shutil, "which", return_value="/x/coverage"), mock.patch.object(lauf, "starte", fake):
            erg = lauf.tests()
        self.assertTrue(all(e[2] == "bestanden" for e in erg))

    def test_main_schreibt_zusammenfassung_und_meldet_ohne_telegram(self):
        erg = [("geheimnisse", "a", "bestanden", ""), ("tests", "b", "nicht_bestanden", "Test rot")]
        ohne = {k: v for k, v in lauf.os.environ.items() if not k.startswith("TELEGRAM_")}  # CI setzt diese Variablen: nie echt senden
        with tempfile.TemporaryDirectory() as d, mock.patch.object(lauf, "sammle", return_value=erg), mock.patch.dict(lauf.os.environ, ohne, clear=True), mock.patch.object(lauf.notify, "sende", side_effect=AssertionError("darf nicht senden")):
            ziel = Path(d) / "u" / "z.json"
            aus = io.StringIO()
            with redirect_stdout(aus):
                self.assertEqual(lauf.main(["--zusammenfassung", str(ziel), "--details", "--telegram"]), 0)
            self.assertIn("Test rot", aus.getvalue())
            self.assertIn("Telegram nicht eingerichtet", aus.getvalue())
            self.assertEqual(json.loads(ziel.read_text(encoding="utf-8"))["befunde"], 1)
            aus = io.StringIO()
            with redirect_stdout(aus):
                lauf.main(["--zusammenfassung", str(ziel), "--telegram"])
            self.assertIn("Keine Änderung", aus.getvalue())

    def test_main_sendet_privat_bei_aenderung(self):
        erg = [("tests", "b", "nicht_bestanden", "Test rot")]
        gesendet = []
        env = {"TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_AUDIT_CHAT_ID": "c"}
        with mock.patch.object(lauf, "sammle", return_value=erg), mock.patch.dict(lauf.os.environ, env, clear=True), mock.patch.object(lauf.notify, "sende", lambda *a: gesendet.append(a)), redirect_stdout(io.StringIO()):
            lauf.main(["--telegram"])
        self.assertEqual(len(gesendet), 1)
        self.assertIn("Test rot", gesendet[0][0])


class QuellenTestTest(unittest.TestCase):
    def test_main(self):
        items = [{"datum": "2026-11-20", "titel": "Titel"}]
        z = {"neu_30": 1, "neu_7": 1, "schwere_bekannt": 0, "cves_30": 0}
        with mock.patch.object(quellen_test.fp, "hole_quelle", return_value=items), mock.patch.object(quellen_test.fp, "verdichte_quelle", return_value=z), redirect_stdout(io.StringIO()) as aus:
            self.assertEqual(quellen_test.main(["x"]), 0)
        self.assertIn("OK   x", aus.getvalue())
        with mock.patch.object(quellen_test.fp, "hole_quelle", return_value=[]), mock.patch.object(quellen_test.fp, "verdichte_quelle", return_value=z), redirect_stdout(io.StringIO()):
            self.assertEqual(quellen_test.main(["x"]), 1)
        with mock.patch.object(quellen_test.fp, "hole_quelle", side_effect=ValueError("boom")), redirect_stdout(io.StringIO()) as aus:
            self.assertEqual(quellen_test.main(["x"]), 1)
        self.assertIn("FEHL x", aus.getvalue())


if __name__ == "__main__":
    unittest.main()
