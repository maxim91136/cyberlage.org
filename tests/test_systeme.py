import copy
import unittest
from datetime import date, datetime, timezone

from test_pipeline import _ms_dok  # noqa: E402  (tests liegen im selben Ordner)

import fetch_patches


def _dok_mit_fix():
    d = _ms_dok()
    d["ProductTree"]["Branch"][0]["Items"][0]["Items"] += [
        {"ProductID": "7", "Value": "Windows 11 Version 25H2 for x64-based Systems"},
        {"ProductID": "8", "Value": "HEIF Image Extension on Windows 11 version 24H2"},
        {"ProductID": "9", "Value": "Windows Server 2022, 23H2 Edition (Server Core installation)"},
        {"ProductID": "10", "Value": "Windows Server 2012 R2 (Server Core installation)"}]
    v = d["Vulnerability"]
    v[0]["ProductStatuses"] = [{"Type": 3, "ProductID": ["1", "7", "8", "9"]}]  # Windows-Kernel: kritisch, ausgenutzt
    v[0]["Remediations"] = [{"Type": 2, "FixedBuild": "10.0.26100.9911", "Description": {"Value": "5132043"}, "ProductID": ["1"]},
                            {"Type": 2, "FixedBuild": "10.0.26200.9911", "Description": {"Value": "5132043"}, "ProductID": ["7"]},
                            {"Type": 2, "FixedBuild": "1.2.62.0", "Description": {"Value": "Release Notes"}, "ProductID": ["8"]}]
    v[1]["ProductStatuses"] = [{"Type": 3, "ProductID": ["3", "2", "10"]}]
    v[1]["Remediations"] = [{"Type": 2, "FixedBuild": "10.0.26100.33822", "Description": {"Value": "5131080"}, "ProductID": ["2"]}]
    return d


class SystemeTests(unittest.TestCase):
    def test_schluessel(self):
        k = fetch_patches.os_schluessel
        self.assertEqual(k("Windows 11 Version 24H2 for x64-based Systems"), "Windows 11 24H2")
        self.assertEqual(k("Windows 11 version 26H1 for ARM64-based Systems"), "Windows 11 26H1")
        self.assertEqual(k("Windows 10 Version 22H2 for 32-bit Systems"), "Windows 10 22H2")
        self.assertEqual(k("Windows Server 2025 (Server Core installation)"), "Windows Server 2025")
        self.assertEqual(k("Windows Server 2012 R2"), "Windows Server 2012 R2")
        for kein in ("HEIF Image Extension on Windows 11 version 24H2", "Windows Server 2022, 23H2 Edition (Server Core installation)",
                     "Microsoft Edge (Chromium-based)", "Azure Linux 3.0", ""):
            self.assertIsNone(k(kein), kein)

    def test_zaehlung_build_und_kb(self):
        s = fetch_patches.verdichte_dokument(_dok_mit_fix(), [])["systeme"]
        self.assertEqual(list(s), ["Windows 11 25H2", "Windows 11 24H2", "Windows Server 2025", "Windows Server 2012 R2"])  # 11 vor Server, neu zuerst
        self.assertEqual(s["Windows 11 24H2"], {"cves": 1, "kritisch": 1, "ausgenutzt": 1, "kb": "5132043", "build": "10.0.26100.9911"})
        self.assertEqual(s["Windows 11 25H2"]["build"], "10.0.26200.9911")
        self.assertEqual(s["Windows Server 2025"]["kb"], "5131080")
        self.assertEqual((s["Windows Server 2025"]["kritisch"], s["Windows Server 2025"]["ausgenutzt"]), (0, 0))
        self.assertEqual(s["Windows Server 2012 R2"]["kb"], "")  # ohne Fix-Angabe bleibt es leer, nichts wird geraten

    def test_letzte_zwei_monate_werden_nachgeholt(self):
        jetzt = datetime(2026, 11, 20, tzinfo=timezone.utc)
        liste = {"value": [{"ID": "2026-Nov", "CurrentReleaseDate": "2026-11-10T08:00:00Z", "CvrfUrl": "u"}]}
        geholt = []

        def hole(url):
            geholt.append(url)
            return _dok_mit_fix()
        a = fetch_patches.aktualisiere(None, liste, hole, [], jetzt)
        alt = copy.deepcopy(a)
        alt["monate"]["2026-Nov"].pop("systeme")  # Stand vor dieser Änderung
        fetch_patches.aktualisiere(alt, liste, hole, [], jetzt)
        self.assertEqual(len(geholt), 2)  # nachgeholt
        fetch_patches.aktualisiere(a, liste, hole, [], jetzt)
        self.assertEqual(len(geholt), 2)  # mit Systemen und unverändert: nicht erneut


class LifecycleTests(unittest.TestCase):
    def test_kompakt_und_filter(self):
        roh = {"windows": [{"cycle": "11-25h2-w", "releaseDate": "2025-09-30", "eol": "2027-10-12", "support": "2027-10-12", "extendedSupport": False, "latest": "10.0.26200", "lts": False},
                           {"cycle": "7", "releaseDate": "2009-10-22", "eol": "2020-01-14", "extendedSupport": "2023-01-10"},
                           {"cycle": "10-22h2-w", "eol": "2025-10-14", "extendedSupport": "2026-10-13"},
                           {"cycle": "ohne-datum", "eol": False}],
               "windows-server": [{"cycle": "2025", "eol": "2034-11-14", "support": "2029-11-13", "lts": True}]}
        lc = fetch_patches.aktualisiere_lifecycle(None, date(2026, 11, 26), datetime(2026, 11, 26, tzinfo=timezone.utc), lambda u: roh[u.split("/")[-1][:-5]])
        z = {x["zyklus"]: x for x in lc["produkte"]["windows"]["zyklen"]}
        self.assertEqual(set(z), {"11-25h2-w", "10-22h2-w"})  # 7 ist zu lange vorbei, ohne Datum fällt raus
        self.assertEqual(z["11-25h2-w"]["erweitert"], "")  # „false“ wird leer
        self.assertEqual(z["10-22h2-w"]["erweitert"], "2026-10-13")
        self.assertEqual(lc["produkte"]["windows-server"]["zyklen"][0]["lts"], True)
        self.assertEqual(lc["meta"]["fehler"], [])

    def test_ausfall_behaelt_alten_stand(self):
        alt = {"produkte": {"windows": {"name": "Windows", "zyklen": [{"zyklus": "x", "eol": "2030-01-01"}]}}}
        def kaputt(u):
            raise OSError("nein")
        lc = fetch_patches.aktualisiere_lifecycle(alt, date(2026, 11, 26), datetime(2026, 11, 26, tzinfo=timezone.utc), kaputt)
        self.assertEqual(lc["produkte"]["windows"]["zyklen"][0]["zyklus"], "x")
        self.assertEqual(len(lc["meta"]["fehler"]), 2)


if __name__ == "__main__":
    unittest.main()
