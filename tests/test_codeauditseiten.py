import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "pipeline"))

import auditseiten  # noqa: E402
import codeauditseiten  # noqa: E402

REGELN = json.loads((WURZEL / "codeaudit" / "regeln.json").read_text(encoding="utf-8"))
JETZT = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)


def zus(score=82, stufe="kleine Mängel", stand="2026-11-27T00:28Z", befunde=1):
    return {"repo": "maxim91136/cyberlage.org", "stand": stand, "regeln": "0.1-entwurf", "score": score, "teilwert": score or 80, "stufe": stufe, "abdeckung": 1.0,
            "gruppen": {g: 1.0 for g in REGELN["gruppen"]}, "befunde": befunde, "hinweise": 2, "nicht_geprueft": 0}


class CodeauditseitenTests(unittest.TestCase):
    def werk(self, code=True):
        w = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, w, True)
        (w / "audit").mkdir()
        shutil.copy(WURZEL / "audit" / "regeln.json", w / "audit" / "regeln.json")
        (w / "codeaudit").mkdir()
        shutil.copy(WURZEL / "codeaudit" / "regeln.json", w / "codeaudit" / "regeln.json")
        (w / "data" / "audit").mkdir(parents=True)
        (w / "data" / "audit" / "cyberlage.org.json").write_text(json.dumps({"domain": "cyberlage.org", "stand": "2026-11-27T05:20Z", "profil": "seite", "regeln": "1.0", "score": 100, "teilwert": 100,
                                                                              "stufe": "ohne Befund", "abdeckung": 1.0, "gruppen": {"tls": 1.0}, "befunde": 0, "hinweise": 0, "nicht_geprueft": 0}), encoding="utf-8")
        if code:
            (w / "data" / "codeaudit").mkdir()
            (w / "data" / "codeaudit" / "cyberlage.org.json").write_text(json.dumps(zus()), encoding="utf-8")
        return w

    def test_seite_hat_code_abschnitt_und_eigenes_siegel(self):
        w = self.werk()
        auditseiten.schreibe(w, JETZT)
        for pfad, wort in (("site/audit/index.html", "Code-Audit"), ("site/en/audit/index.html", "Code audit")):
            t = (w / pfad).read_text(encoding="utf-8")
            self.assertIn('id="code-audit"', t)
            self.assertIn(wort, t)
            self.assertIn("/audit/siegel/code-cyberlage.org.svg", t)
        svg = (w / "site" / "audit" / "siegel" / "code-cyberlage.org.svg").read_text(encoding="utf-8")
        self.assertIn("DREIER-CODE-SIEGEL", svg)
        self.assertIn("ENTWURF 0.1", svg)
        self.assertIn("SILBER", svg)
        self.assertIn("DREIER-SIEGEL", (w / "site" / "audit" / "siegel" / "cyberlage.org.svg").read_text(encoding="utf-8"))

    def test_ohne_code_daten_keine_code_seite(self):
        w = self.werk(code=False)
        auditseiten.schreibe(w, JETZT)
        self.assertNotIn("code-audit", (w / "site" / "audit" / "index.html").read_text(encoding="utf-8"))
        self.assertFalse((w / "site" / "audit" / "siegel" / "code-cyberlage.org.svg").exists())

    def test_keine_einzelbefunde_nur_zahlen(self):
        w = self.werk()
        auditseiten.schreibe(w, JETZT)
        t = (w / "site" / "audit" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Befunde: 1", t)
        for verboten in ("gitleaks_", "bandit:", "B310", "S314", "nicht_bestanden"):
            self.assertNotIn(verboten, t)

    def test_siegel_grau_bei_altem_lauf(self):
        d = zus(stand="2026-11-20T00:00Z")
        svg = codeauditseiten.siegel(d, JETZT, REGELN)
        self.assertIn(auditseiten.FARBE["grau"], svg)
        self.assertIn("letzter Lauf", codeauditseiten.fuss_text(d, REGELN, "de", JETZT))

    def test_fusstext(self):
        self.assertEqual(codeauditseiten.fuss_text(zus(), REGELN, "de", JETZT), "Code-Audit: 82 / 100 · Silber · 27.11.2026 · Regeln 0.1-entwurf")
        self.assertTrue(codeauditseiten.fuss_text(zus(), REGELN, "en", JETZT).startswith("Code audit: 82 / 100 · Silver"))

    def test_alle_gruppen_haben_englischen_namen(self):
        for g in REGELN["gruppen"]:
            self.assertIn(g, codeauditseiten.GRUPPE_EN)

    def test_zeitplan_stimmt_mit_workflow(self):
        wf = (WURZEL / ".github" / "workflows" / "codeaudit.yml").read_text(encoding="utf-8")
        h, m = codeauditseiten.LAUF_UHR.split(":")
        self.assertIn('cron: "%d %d * * *"' % (int(m), int(h)), wf)

    def test_web_siegel_unveraendert(self):
        regeln = json.loads((WURZEL / "audit" / "regeln.json").read_text(encoding="utf-8"))
        d = {"stand": "2026-11-27T05:20Z", "score": 100}
        svg = auditseiten.siegel("cyberlage.org", d, JETZT, regeln)
        self.assertIn("DREIER-SIEGEL", svg)
        self.assertIn("REGELN 1.0", svg)
        self.assertNotIn("ENTWURF", svg)


if __name__ == "__main__":
    unittest.main()
