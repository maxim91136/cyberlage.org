import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audit.auswertung import rechne  # noqa: E402
from codeaudit import pruefungen as p  # noqa: E402
import json  # noqa: E402

R = json.loads((Path(__file__).resolve().parent.parent / "codeaudit" / "regeln.json").read_text(encoding="utf-8"))
SHA = "a" * 40


def erg(liste):
    return {x[1]: x[2] for x in liste}


class PruefungenTest(unittest.TestCase):
    def test_gitleaks(self):
        self.assertEqual(erg(p.gitleaks([], []))["gitleaks_verlauf"], "bestanden")
        self.assertEqual(erg(p.gitleaks([{"a": 1}], []))["gitleaks_arbeitsbaum"], "nicht_bestanden")
        self.assertEqual(erg(p.gitleaks(None, None))["gitleaks_verlauf"], "nicht_geprueft")

    def test_workflows_gepinnt_und_rechte(self):
        gut = "permissions:\n  contents: read\njobs:\n  a:\n    steps:\n      - uses: actions/checkout@%s # v4\n" % SHA
        schlecht = "jobs:\n  a:\n    steps:\n      - uses: actions/checkout@v4\n      - uses: ./lokal\n"
        self.assertEqual(erg(p.workflow_dateien({"a.yml": gut})), {"actions_gepinnt": "bestanden", "berechtigungen": "bestanden"})
        self.assertEqual(erg(p.workflow_dateien({"b.yml": schlecht})), {"actions_gepinnt": "nicht_bestanden", "berechtigungen": "nicht_bestanden"})
        self.assertEqual(erg(p.workflow_dateien({}))["actions_gepinnt"], "nicht_geprueft")

    def test_zizmor(self):
        self.assertEqual(erg(p.zizmor([{"determinations": {"severity": "High"}}]))["zizmor"], "nicht_bestanden")
        self.assertEqual(erg(p.zizmor([{"determinations": {"severity": "Medium"}}]))["zizmor"], "hinweis")
        self.assertEqual(erg(p.zizmor([{"determinations": {"severity": "Low"}}]))["zizmor"], "bestanden")
        self.assertEqual(erg(p.zizmor(None))["zizmor"], "nicht_geprueft")

    def test_osv(self):
        self.assertEqual(erg(p.osv(None, False))["osv"], "bestanden")
        self.assertEqual(erg(p.osv(None, True))["osv"], "nicht_geprueft")
        self.assertEqual(erg(p.osv({"results": [{"packages": [{"vulnerabilities": [{}]}]}]}, True))["osv"], "nicht_bestanden")

    def test_python(self):
        e = erg(p.python_werkzeuge({"results": [{"issue_severity": "MEDIUM"}]}, []))
        self.assertEqual((e["bandit"], e["ruff"]), ("hinweis", "bestanden"))
        self.assertEqual(erg(p.python_werkzeuge({"results": [{"issue_severity": "HIGH"}]}, [{}]))["bandit"], "nicht_bestanden")

    def test_eslint_zaehlt_nur_fehler(self):
        self.assertEqual(erg(p.eslint([{"messages": [{"severity": 1}]}]))["eslint"], "bestanden")
        self.assertEqual(erg(p.eslint([{"messages": [{"severity": 2}]}]))["eslint"], "nicht_bestanden")

    def test_tests_und_abdeckung(self):
        self.assertEqual(erg(p.tests(True, 85))["abdeckung"], "bestanden")
        self.assertEqual(erg(p.tests(True, 70))["abdeckung"], "hinweis")
        self.assertEqual(erg(p.tests(False, 40)), {"tests_gruen": "nicht_bestanden", "abdeckung": "nicht_bestanden"})
        self.assertEqual(erg(p.tests(None, None))["abdeckung"], "nicht_geprueft")

    def test_wartbarkeit(self):
        e = erg(p.wartbarkeit({"a.py": [{"complexity": 31}]}, {"a.py": 1600}))
        self.assertEqual((e["komplexitaet"], e["dateilaenge"]), ("nicht_bestanden", "hinweis"))
        self.assertEqual(erg(p.wartbarkeit({"a.py": [{"complexity": 5}]}, {"a.py": 10})), {"komplexitaet": "bestanden", "dateilaenge": "bestanden"})

    def test_alles_zusammen_ergibt_score_mit_regeln(self):
        alle = (p.gitleaks([], []) + p.workflow_dateien({"a.yml": "permissions:\n  x: y\n- uses: a/b@%s\n" % SHA}) + p.zizmor([]) + p.osv(None, False)
                + p.python_werkzeuge({"results": []}, []) + p.eslint([]) + p.tests(True, 90) + p.wartbarkeit({}, {}))
        r = rechne(alle, R)
        self.assertEqual((r["score"], r["abdeckung"]), (100, 1.0))

    def test_fehlendes_geheimnis_deckelt(self):
        alle = (p.gitleaks([{"x": 1}], []) + p.workflow_dateien({"a.yml": "permissions:\n  x: y\n- uses: a/b@%s\n" % SHA}) + p.zizmor([]) + p.osv(None, False)
                + p.python_werkzeuge({"results": []}, []) + p.eslint([]) + p.tests(True, 90) + p.wartbarkeit({}, {}))
        self.assertLessEqual(rechne(alle, R)["score"], 59)


if __name__ == "__main__":
    unittest.main()
