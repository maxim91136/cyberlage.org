import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))

import fetch_kev  # noqa: E402
import score  # noqa: E402


def roh(*eintraege, **extra):
    d = {"catalogVersion": "2026.11.20", "dateReleased": "2026-11-20T17:48:39Z",
         "count": len(eintraege), "vulnerabilities": list(eintraege)}
    d.update(extra)
    return d


def kev_roh(cve, hersteller="Microsoft", produkt="Exchange Server", datum="2026-11-20", ransom="Unknown"):
    return {"cveID": cve, "vendorProject": hersteller, "product": produkt,
            "dateAdded": datum, "dueDate": "2026-12-11", "knownRansomwareCampaignUse": ransom}


def kev_klein(cve, hersteller, produkt, datum, ransom=False):
    return {"cve": cve, "hersteller": hersteller, "produkt": produkt,
            "hinzugefuegt": datum, "frist": None, "ransomware_bekannt": ransom}


REGELN_OFFEN = {"status": "entwurf", "fenster_tage": 30, "erhoeht_ab": 1, "hoch_ab": 3}
REGELN_FREI = dict(REGELN_OFFEN, status="freigegeben")
EXCH = {"hersteller": "Microsoft", "produkt": "Exchange Server", "status": "freigegeben"}
STAND = date(2026, 11, 23)


class AbrufTests(unittest.TestCase):
    def test_verdichtet_und_sortiert(self):
        meta, e = fetch_kev.pruefe_und_verdichte(roh(
            kev_roh("CVE-2", datum="2026-11-20", ransom="Known"),
            kev_roh("CVE-1", datum="2026-11-01")))
        self.assertEqual([x["cve"] for x in e], ["CVE-1", "CVE-2"])
        self.assertTrue(e[1]["ransomware_bekannt"])
        self.assertFalse(e[0]["ransomware_bekannt"])
        self.assertEqual(meta["anzahl"], 2)

    def test_lehnt_fehlerhafte_daten_ab(self):
        schlecht = [
            {},
            roh(),  # leer
            roh(kev_roh("CVE-1"), count=5),
            roh(kev_roh("CVE-1"), kev_roh("CVE-1")),  # doppelt
            roh(kev_roh("CVE-1", datum="kein-datum")),
            roh({"cveID": "CVE-1"}),  # Pflichtfelder fehlen
        ]
        for r in schlecht:
            with self.subTest(r=str(r)[:60]):
                with self.assertRaises(fetch_kev.PruefFehler):
                    fetch_kev.pruefe_und_verdichte(r)

    def test_schrumpfender_katalog_wird_abgelehnt(self):
        with tempfile.TemporaryDirectory() as t:
            ziel = Path(t) / "kev.json"
            alt = [kev_klein(f"CVE-{i}", "A", "B", "2026-01-01") for i in range(100)]
            fetch_kev.schreibe({"anzahl": 100}, alt, ziel)
            with self.assertRaises(fetch_kev.PruefFehler):
                fetch_kev.pruefe_gegen_vorgaenger(alt[:50], ziel)
            fetch_kev.pruefe_gegen_vorgaenger(alt[:95], ziel)  # kleiner Rückgang ist ok

    def test_schreiben_ist_lesbar_und_gueltig(self):
        with tempfile.TemporaryDirectory() as t:
            ziel = Path(t) / "x" / "kev.json"
            fetch_kev.schreibe({"anzahl": 1}, [kev_klein("CVE-1", "Ä", "B", "2026-01-01")], ziel)
            daten = json.loads(ziel.read_text(encoding="utf-8"))
            self.assertEqual(daten["eintraege"][0]["hersteller"], "Ä")


class AuswertungTests(unittest.TestCase):
    def setUp(self):
        self.kev = {"meta": {"lizenz": "CC0", "quelle": "test"}, "eintraege": [
            kev_klein("A", "Microsoft", "Exchange Server", "2026-11-20", ransom=True),
            kev_klein("B", "Microsoft", "Internet Key Exchange (IKE) Service Extensions", "2026-11-21"),
            kev_klein("C", "Microsoft", "Exchange Server", "2026-10-01"),  # außerhalb 30 Tage
            kev_klein("D", "Andere", "Exchange Server", "2026-11-22"),
        ]}

    def test_fenstergrenzen(self):
        # 30 Tage bis einschließlich 23.11. sind der 25.10. bis 23.11.: der 25.10. zählt, der 24.10. nicht
        e = [kev_klein("X", "a", "b", "2026-10-25"), kev_klein("Y", "a", "b", "2026-10-24"),
             kev_klein("Z", "a", "b", "2026-11-24")]  # Zukunft zählt nicht
        self.assertEqual([x["cve"] for x in score.im_fenster(e, STAND, 30)], ["X"])

    def test_ohne_freigegebene_produkte_keine_bewertung(self):
        r = score.werte_aus(self.kev, [], REGELN_FREI, [], STAND)
        self.assertIsNone(r["stufe"])
        self.assertIsNone(r["verwaltungsbezug"]["neu"])
        self.assertEqual(r["kev"]["neu_30_tage"], 3)

    def test_entwurf_der_regeln_ergibt_keine_stufe_aber_zahlen(self):
        r = score.werte_aus(self.kev, [EXCH], REGELN_OFFEN, [], STAND)
        self.assertIsNone(r["stufe"])
        self.assertEqual(r["verwaltungsbezug"]["neu"], 1)

    def test_exakte_zuordnung_kein_teiltreffer(self):
        p = {"hersteller": "Microsoft", "produkt": "Exchange", "status": "freigegeben"}
        r = score.werte_aus(self.kev, [p], REGELN_FREI, [], STAND)
        self.assertEqual(r["verwaltungsbezug"]["neu"], 0)  # weder 'Exchange Server' noch 'IKE'

    def test_stufe_und_ransomware_aufschlag(self):
        r = score.werte_aus(self.kev, [EXCH], REGELN_FREI, [], STAND)
        # 1 relevanter Eintrag -> erhoeht, Ransomware bekannt -> eine Stufe hoeher
        self.assertEqual(r["stufe"], "hoch")
        ohne = {"meta": self.kev["meta"], "eintraege": [kev_klein("A", "Microsoft", "Exchange Server", "2026-11-20")]}
        self.assertEqual(score.werte_aus(ohne, [EXCH], REGELN_FREI, [], STAND)["stufe"], "erhoeht")
        keiner = {"meta": self.kev["meta"], "eintraege": []}
        self.assertEqual(score.werte_aus(keiner, [EXCH], REGELN_FREI, [], STAND)["stufe"], "niedrig")

    def test_nur_geprueft_wird_uebernommen(self):
        zeile = {"kennzahl": "k", "wert": "31.8", "einheit": "%", "berichtsjahr": "2025", "seite": "20",
                 "geltungsbereich": "EU", "quelle": "ENISA", "quelle_url": "u", "lizenz": "CC BY 4.0"}
        r = score.werte_aus(self.kev, [], REGELN_FREI,
                            [dict(zeile, status="geprueft"), dict(zeile, kennzahl="x", status="ungeprueft")], STAND)
        self.assertEqual([s["kennzahl"] for s in r["sektor"]], ["k"])
        self.assertEqual(r["sektor"][0]["geltungsbereich"], "EU")

    def test_projektangabe_und_hinweise(self):
        r = score.werte_aus(self.kev, [], REGELN_FREI, [], STAND)
        self.assertEqual(r["projekt"]["von"], "Dreier Labs")
        self.assertTrue(any("Dreier Labs" in h for h in r["hinweise"]))

    def test_produktliste_wird_gefiltert(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "p.csv"
            p.write_text("hersteller,produkt,status,begruendung,beleg_url\n"
                         "A,B,freigegeben,Grund,http://x\nC,D,entwurf,offen,\n", encoding="utf-8")
            self.assertEqual([x["hersteller"] for x in score.lade_produkte(p)], ["A"])

    def test_echte_konfiguration_ist_lesbar(self):
        wurzel = Path(__file__).resolve().parent.parent
        for z in score.lese_csv(wurzel / "config" / "produkte.csv"):
            self.assertEqual(len(z), 5)
            self.assertIsNone(z.get(None), "Zeile hat zu viele Spalten (Komma im Text?)")
        json.loads((wurzel / "config" / "regeln.json").read_text(encoding="utf-8"))
        for z in score.lese_csv(wurzel / "data" / "enisa.csv"):
            float(z["wert"])
            self.assertIsNone(z.get(None))


if __name__ == "__main__":
    unittest.main()
