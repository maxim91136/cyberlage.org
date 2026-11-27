"""Durchlauf-Tests: score.main und prerender.main laufen auf einer Kopie des Repos im Temp-Ordner (kein Netz, das echte Repo bleibt unberührt)."""
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "pipeline"))
sys.path.insert(0, str(WURZEL))

import prerender  # noqa: E402
import score  # noqa: E402


class DurchlaufTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.kopie = Path(cls.tmp.name)
        for n in ("data", "config", "site", "audit", "codeaudit"):
            shutil.copytree(WURZEL / n, cls.kopie / n, ignore=shutil.ignore_patterns("__pycache__"))
        for n in ("RULES.md", "LICENSE"):
            shutil.copy(WURZEL / n, cls.kopie / n)
        with mock.patch.object(score, "WURZEL", cls.kopie):
            ein = io.StringIO()
            with redirect_stdout(ein):
                cls.rc_score = score.main(["--stand", "2026-11-26"])
            cls.aus_score = ein.getvalue()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_score_schreibt_lage_status_und_pegel(self):
        self.assertEqual(self.rc_score, 0)
        self.assertIn("OK: site/data/lage.json", self.aus_score)
        lage = json.loads((self.kopie / "site" / "data" / "lage.json").read_text(encoding="utf-8"))
        self.assertIn(lage["stufe"], ("niedrig", "erhoeht", "ruhig", "unauffaellig", "angespannt", "hoch", "ausserordentlich"))
        self.assertTrue(0 <= lage["pegel"]["wert"] <= 100)
        status = json.loads((self.kopie / "site" / "data" / "status.json").read_text(encoding="utf-8"))
        self.assertEqual(status["stufe"], lage["stufe"])
        self.assertTrue((self.kopie / "data" / "pegel.json").exists())

    def test_prerender_schreibt_seiten(self):
        with mock.patch.object(prerender, "WURZEL", self.kopie), redirect_stdout(io.StringIO()) as aus:
            rc = prerender.main()
        self.assertEqual(rc, 0, aus.getvalue())
        index = (self.kopie / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn("<!--ssr-start-->", index)
        self.assertIn("Dreier-Pegel", index)
        en = (self.kopie / "site" / "en" / "index.html").read_text(encoding="utf-8")
        self.assertIn('lang="en"', en)
        self.assertTrue((self.kopie / "site" / "sitemap.xml").read_text(encoding="utf-8").startswith("<?xml"))
        self.assertTrue((self.kopie / "site" / "audit" / "index.html").exists())

    def test_prerender_ohne_lage_meldet_fehler(self):
        with tempfile.TemporaryDirectory() as leer, mock.patch.object(prerender, "WURZEL", Path(leer)), redirect_stdout(io.StringIO()) as aus:
            self.assertEqual(prerender.main(), 1)
        self.assertIn("FEHLER", aus.getvalue())

    def test_siegel_fuss_ohne_daten_ist_leer(self):
        with tempfile.TemporaryDirectory() as leer, mock.patch.object(prerender, "WURZEL", Path(leer)):
            self.assertEqual(prerender.siegel_fuss(), "")


if __name__ == "__main__":
    unittest.main()
