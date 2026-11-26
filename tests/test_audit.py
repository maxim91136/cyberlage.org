import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "audit"))

import kopfzeilen  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
