import json
import unittest
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
R = json.loads((WURZEL / "codeaudit" / "regeln.json").read_text(encoding="utf-8"))
WEB = json.loads((WURZEL / "audit" / "regeln.json").read_text(encoding="utf-8"))


class CodeauditRegelnTest(unittest.TestCase):
    def test_gewichte_summe_100(self):
        self.assertEqual(sum(g["gewicht"] for g in R["gruppen"].values()), 100)

    def test_jede_gruppe_hat_werkzeug_und_quelle(self):
        for k, g in R["gruppen"].items():
            for f in ("name", "gewicht", "werkzeug", "quelle"):
                self.assertTrue(g.get(f), k + ": " + f)

    def test_deckelgruppen_gibt_es(self):
        for k in R["deckel"]["gruppen"]:
            self.assertIn(k, R["gruppen"])

    def test_gleiche_skala_wie_web_audit(self):
        for f in ("wertung", "stufen", "abzeichen", "mindest_abdeckung"):
            self.assertEqual(R[f], WEB[f], f)
        self.assertEqual(R["deckel"]["max_score"], WEB["deckel"]["max_score"])


if __name__ == "__main__":
    unittest.main()
