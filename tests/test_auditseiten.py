import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "pipeline"))

import auditseiten  # noqa: E402

JETZT = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)
REGELN = json.loads((WURZEL / "audit" / "regeln.json").read_text(encoding="utf-8"))


def zus(domain, score=100, stufe="ohne Befund", stand="2026-11-26T09:57Z", befunde=0, profil="seite", gruppen=None):
    return {"domain": domain, "stand": stand, "profil": profil, "regeln": "0.1-entwurf", "score": score, "teilwert": score, "stufe": stufe, "abdeckung": 1.0,
            "gruppen": gruppen if gruppen is not None else {"tls": 1.0, "hsts": 1.0}, "befunde": befunde, "hinweise": 0, "nicht_geprueft": 0}


class AuditseitenTests(unittest.TestCase):
    def werk(self, *eintraege):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        w = Path(tmp.name)
        (w / "data" / "audit").mkdir(parents=True)
        (w / "audit").mkdir()
        (w / "audit" / "regeln.json").write_text((WURZEL / "audit" / "regeln.json").read_text(encoding="utf-8"), encoding="utf-8")
        for z in eintraege:
            (w / "data" / "audit" / (z["domain"] + ".json")).write_text(json.dumps(z), encoding="utf-8")
        return w

    def test_schreibt_seiten_und_siegel(self):
        w = self.werk(zus("cyberlage.com", profil="weiterleitung"), zus("cyberlage.org"))
        sm = auditseiten.schreibe(w, JETZT)
        self.assertEqual(sm, [("/audit/", "/en/audit/", "2026-11-26")])
        de = (w / "site" / "audit" / "index.html").read_text(encoding="utf-8")
        en = (w / "site" / "en" / "audit" / "index.html").read_text(encoding="utf-8")
        self.assertLess(de.index("cyberlage.org"), de.index("cyberlage.com"))  # feste Reihenfolge
        self.assertIn('lang="de"', de)
        self.assertIn('lang="en"', en)
        self.assertIn("Weiterleitung auf cyberlage.org", de)
        self.assertIn("Redirect to cyberlage.org", en)
        self.assertIn("no findings", en)
        self.assertNotIn("<script", de + en)
        svg = (w / "site" / "audit" / "siegel" / "cyberlage.org.svg").read_text(encoding="utf-8")
        self.assertIn("DREIER-SIEGEL", svg)
        self.assertIn("2026-11-26", svg)
        self.assertIn("#f0c04a", svg)

    def test_abzeichen_nach_score(self):
        a = lambda sc: auditseiten.abzeichen(sc, REGELN)
        self.assertEqual([a(100), a(95), a(94), a(80), a(79), a(60), a(59), a(0), a(None)], ["gold", "gold", "silber", "silber", "bronze", "bronze", None, None, None])
        self.assertEqual([g for g, _n in REGELN["abzeichen"]], [g for g, _n in REGELN["stufen"]][:3])  # Grenzen wie die Stufen

    def test_siegel_zeigt_abzeichen(self):
        gold = auditseiten.siegel("x.de", zus("x.de", 100), JETZT, REGELN)
        silber = auditseiten.siegel("x.de", zus("x.de", 85, "kleine Mängel"), JETZT, REGELN)
        bronze = auditseiten.siegel("x.de", zus("x.de", 65, "Mängel"), JETZT, REGELN)
        keins = auditseiten.siegel("x.de", zus("x.de", 40, "erhebliche Mängel"), JETZT, REGELN)
        for svg, name, farbe in ((gold, "GOLD", "#f0c04a"), (silber, "SILBER", "#cfd8df"), (bronze, "BRONZE", "#cd7f4f")):
            self.assertIn(">%s</text>" % name, svg)
            self.assertIn(farbe, svg)
        self.assertNotIn(">GOLD<", keins + silber + bronze)
        self.assertIn("#ff3b5c", keins)
        self.assertIn("/ 100", keins)
        self.assertNotIn("<polygon", gold)

    def test_siegel_wird_grau_wenn_lauf_zu_alt(self):
        alt = zus("cyberlage.org", stand="2026-11-10T05:20Z")
        svg = auditseiten.siegel("cyberlage.org", alt, JETZT, REGELN)
        self.assertIn("#8b98a3", svg)
        self.assertNotIn("<polygon", svg)
        w = self.werk(alt)
        auditseiten.schreibe(w, JETZT)
        self.assertIn("grau", (w / "site" / "audit" / "index.html").read_text(encoding="utf-8").replace("ist deshalb grau", "grau"))

    def test_ohne_score_grau_und_ohne_zahl(self):
        z = zus("cyberlage.org", score=None, stufe="nicht bewertet (zu wenig geprüft)")
        svg = auditseiten.siegel("cyberlage.org", z, JETZT, REGELN)
        self.assertIn("#8b98a3", svg)
        self.assertIn("Score –", svg)

    def test_befunde_nur_als_zahl_ohne_einzelheiten(self):
        w = self.werk(zus("cyberlage.org", score=80, stufe="kleine Mängel", befunde=2))
        auditseiten.schreibe(w, JETZT)
        de = (w / "site" / "audit" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Befunde: 2", de)
        self.assertIn("erst nach der Behebung", de)

    def test_ohne_daten_nichts_geschrieben(self):
        w = self.werk()
        self.assertEqual(auditseiten.schreibe(w, JETZT), [])
        self.assertFalse((w / "site").exists())

    def test_alle_gruppen_haben_englischen_namen(self):
        regeln = json.loads((WURZEL / "audit" / "regeln.json").read_text(encoding="utf-8"))
        self.assertEqual(set(regeln["gruppen"]), set(auditseiten.GRUPPE_EN))
        for _g, n in regeln["stufen"]:
            self.assertIn(n, auditseiten.STUFE_EN)
            self.assertIn(n, auditseiten.AMPEL)

    def test_keine_unsicher_aussage(self):
        for sp in ("de", "en"):
            for text in auditseiten.T[sp]["siegel"]:
                self.assertNotIn("is secure" if sp == "en" else "ist sicher.", text.replace("not say a site is secure", "").replace("nicht, dass eine Seite sicher ist", ""))


if __name__ == "__main__":
    unittest.main()
