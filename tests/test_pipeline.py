import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))

import fetch_ausblick  # noqa: E402
import fetch_extra  # noqa: E402
import notify  # noqa: E402
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


REGELN_OFFEN = {"status": "entwurf", "fenster_tage": 30, "erhoeht_ab": 1, "hoch_ab": 3, "ransomware_aufschlag_ab": 1}
REGELN_FREI = dict(REGELN_OFFEN, status="freigegeben")
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

    def test_entwurf_der_regeln_ergibt_keine_stufe_aber_zahlen_und_liste(self):
        r = score.werte_aus(self.kev, REGELN_OFFEN, [], STAND)
        self.assertIsNone(r["stufe"])
        self.assertEqual(r["kev"]["neu_30_tage"], 3)
        self.assertEqual(len(r["neu"]), 3)

    def test_liste_neueste_zuerst_mit_link_und_ohne_technikdetails(self):
        r = score.werte_aus(self.kev, REGELN_OFFEN, [], STAND)
        daten = [x["hinzugefuegt"] for x in r["neu"]]
        self.assertEqual(daten, sorted(daten, reverse=True))
        self.assertTrue(all(x["link"].startswith("https://nvd.nist.gov/vuln/detail/CVE") or x["link"].endswith(x["cve"])
                            for x in r["neu"]))
        self.assertEqual(set(r["neu"][0]), {"cve", "hersteller", "produkt", "hinzugefuegt", "frist",
                                            "ransomware_bekannt", "link"})

    def test_stufen_nach_schwellen(self):
        def kev_mit(n, ransom=0):
            return {"meta": self.kev["meta"], "eintraege": [
                kev_klein(f"C{i}", "h", "p", "2026-11-20", ransom=i < ransom) for i in range(n)]}
        regeln = dict(REGELN_FREI, erhoeht_ab=5, hoch_ab=8, ransomware_aufschlag_ab=3)
        stufe = lambda n, r=0: score.werte_aus(kev_mit(n, r), regeln, [], STAND)["stufe"]
        self.assertEqual(stufe(4), "niedrig")
        self.assertEqual(stufe(5), "erhoeht")
        self.assertEqual(stufe(8), "hoch")
        self.assertEqual(stufe(4, 3), "erhoeht")   # Ransomware-Aufschlag
        self.assertEqual(stufe(9, 3), "hoch")      # nie ueber 'hoch'
        self.assertEqual(stufe(4, 2), "niedrig")   # unter dem Aufschlag-Schwellwert

    def test_verlauf_wochenweise_mit_schwellen(self):
        r = score.werte_aus(self.kev, REGELN_FREI, [], STAND)
        v = r["verlauf"]
        self.assertEqual(len(v), 53)
        self.assertEqual(v[-1]["stand"], STAND.isoformat())
        self.assertEqual(v[-1]["neu"], r["kev"]["neu_30_tage"])
        self.assertEqual(v[0]["stand"], "2025-11-24")
        self.assertEqual(r["schwellen"]["erhoeht_ab"], REGELN_FREI["erhoeht_ab"])

    def test_nur_geprueft_wird_uebernommen(self):
        zeile = {"kennzahl": "k", "wert": "31.8", "einheit": "%", "berichtsjahr": "2025", "seite": "20",
                 "geltungsbereich": "EU", "quelle": "ENISA", "quelle_url": "u", "lizenz": "CC BY 4.0"}
        r = score.werte_aus(self.kev, REGELN_FREI,
                            [dict(zeile, status="geprueft"), dict(zeile, kennzahl="x", status="ungeprueft")], STAND)
        self.assertEqual([s["kennzahl"] for s in r["sektor"]], ["k"])
        self.assertEqual(r["sektor"][0]["geltungsbereich"], "EU")

    def test_projektangabe_und_hinweise(self):
        r = score.werte_aus(self.kev, REGELN_FREI, [], STAND)
        self.assertEqual(r["projekt"]["von"], "Dreier Labs")
        self.assertIn("keine amtliche Stelle", r["projekt"]["art"])

    def test_echte_konfiguration_ist_lesbar(self):
        wurzel = Path(__file__).resolve().parent.parent
        regeln = json.loads((wurzel / "config" / "regeln.json").read_text(encoding="utf-8"))
        self.assertLess(regeln["erhoeht_ab"], regeln["hoch_ab"])
        self.assertIn(regeln["status"], ("entwurf", "freigegeben"))
        for z in score.lese_csv(wurzel / "data" / "enisa.csv"):
            float(z["wert"])
            self.assertIsNone(z.get(None))


BSI_XML = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>[NEU] [kritisch] Foo Server: Schwachstelle</title><link>https://wid.cert-bund.de/portal/wid/securityadvisory?name=WID-SEC-2026-1111</link>
<description>langer Text</description><category>kritisch</category><pubDate>Mon, 23 Nov 2026 12:37:03 GMT</pubDate></item>
<item><title>[UPDATE] [hoch] Bar: Mehrere Schwachstellen</title><link>https://wid.cert-bund.de/portal/wid/securityadvisory?name=WID-SEC-2026-2222</link>
<description>x</description><category>hoch</category><pubDate>Sun, 22 Nov 2026 08:00:00 GMT</pubDate></item>
<item><title>kaputt</title><link>https://x/y</link><category>hoch</category><pubDate>Sun, 22 Nov 2026 08:00:00 GMT</pubDate></item>
</channel></rss>"""

EU_JSON = json.dumps([
    {"id": "EUVD-2026-1", "aliases": "CVE-2026-1\nGHSA-x\n", "baseScore": 9.3, "epss": 1.2,
     "datePublished": "Oct 15, 2026, 8:30:32 PM", "exploitedSince": "Nov 16, 2026, 12:00:00 AM",
     "enisaIdVendor": [{"vendor": {"name": "BeyondTrust"}}]},
    {"id": "EUVD-2026-2", "aliases": "CVE-2026-2", "exploitedSince": None},
]).encode()


class ZusatzQuellenTests(unittest.TestCase):
    def test_bsi_parser_nimmt_nur_kennzahlen_und_keine_beschreibung(self):
        r = fetch_extra.parse_bsi(BSI_XML)
        self.assertEqual(set(r), {"WID-SEC-2026-1111", "WID-SEC-2026-2222"})  # unvollstaendiger Eintrag fehlt
        e = r["WID-SEC-2026-1111"]
        self.assertEqual((e["schwere"], e["status"], e["datum"]), ("kritisch", "neu", "2026-11-23"))
        self.assertEqual(e["titel"], "Foo Server: Schwachstelle")
        self.assertNotIn("beschreibung", e)
        self.assertNotIn("langer Text", json.dumps(e))
        self.assertEqual(r["WID-SEC-2026-2222"]["status"], "update")

    def test_bsi_parser_lehnt_kaputtes_ab(self):
        for roh in (b"nicht xml", b"<rss><channel></channel></rss>"):
            with self.assertRaises(fetch_extra.QuellFehler):
                fetch_extra.parse_bsi(roh)

    def test_eu_parser(self):
        r = fetch_extra.parse_eu(EU_JSON)
        self.assertEqual(list(r), ["EUVD-2026-1"])  # Eintrag ohne exploitedSince wird nicht geraten
        e = r["EUVD-2026-1"]
        self.assertEqual((e["cve"], e["hersteller"], e["ausgenutzt_seit"]), (["CVE-2026-1"], ["BeyondTrust"], "2026-11-16"))
        self.assertEqual(e["veroeffentlicht"], "2026-10-15")
        with self.assertRaises(fetch_extra.QuellFehler):
            fetch_extra.parse_eu(b"[]")

    def test_zusammenfuehren_behaelt_und_kuerzt(self):
        from datetime import datetime, timezone
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "x.json"
            d.write_text(json.dumps({"meta": {}, "eintraege": [
                {"id": "alt", "datum": "2026-01-01"}, {"id": "mittel", "datum": "2026-10-01"}]}), encoding="utf-8")
            jetzt = datetime(2026, 11, 23, tzinfo=timezone.utc)
            r = fetch_extra.zusammenfuehren(d, {"neu": {"id": "neu", "datum": "2026-11-22"}}, "datum", jetzt)
            self.assertEqual([e["id"] for e in r], ["neu", "mittel"])  # 'alt' ist aelter als 120 Tage

    def test_score_nimmt_zusatzquellen_oder_null(self):
        kev = {"meta": {}, "eintraege": []}
        leer = score.werte_aus(kev, REGELN_FREI, [], STAND)
        self.assertIsNone(leer["cert_bund"])
        self.assertIsNone(leer["eu_kev"])
        bsi = {"meta": {"quelle": "q", "quelle_url": "u"}, "eintraege": [
            {"id": "A", "schwere": "kritisch", "datum": "2026-11-22", "titel": "t", "link": "l"},
            {"id": "B", "schwere": "mittel", "datum": "2026-11-22", "titel": "t", "link": "l"},
            {"id": "C", "schwere": "hoch", "datum": "2026-09-01", "titel": "t", "link": "l"}]}
        eu = {"meta": {"quelle": "q", "quelle_url": "u"}, "eintraege": [{"id": "E", "ausgenutzt_seit": "2026-11-16"}]}
        r = score.werte_aus(kev, REGELN_FREI, [], STAND, bsi, eu)
        self.assertEqual(r["cert_bund"]["kritisch_7_tage"], 1)
        self.assertEqual(len(r["cert_bund"]["liste"]), 1)  # nur kritisch/hoch im Fenster
        self.assertEqual(r["eu_kev"]["neu_30_tage"], 1)


class MeldeTests(unittest.TestCase):
    def setUp(self):
        from datetime import datetime, timezone
        self.jetzt = datetime(2026, 11, 23, 9, 0, tzinfo=timezone.utc)
        self.kev = {"meta": {}, "eintraege": [kev_klein("CVE-1", "Cisco", "X & Y", "2026-11-20"),
                                              kev_klein("CVE-2", "Apache", "Roller", "2026-11-20", ransom=True)]}
        self.bsi = {"eintraege": [{"id": "W1", "schwere": "kritisch", "titel": "Foo <b>", "link": "https://w/1", "datum": "2026-11-23"},
                                  {"id": "W2", "schwere": "hoch", "titel": "Bar", "link": "https://w/2", "datum": "2026-11-23"}]}
        self.lage = {"stufe": "erhoeht", "stufe_begruendung": "34 neu.", "kev": {"neu_7_tage": 9, "neu_30_tage": 34}}

    def test_erster_lauf_merkt_nur(self):
        n, z = notify.ermittle(self.kev, self.bsi, None, self.lage, None, self.jetzt)
        self.assertEqual(n, [])
        self.assertEqual(z["gesehen"]["kev"], ["CVE-1", "CVE-2"])

    def test_sofort_nur_ransomware_rest_in_tageslage(self):
        _, z = notify.ermittle(self.kev, self.bsi, None, self.lage, None, self.jetzt)
        z["zusammenfassung"] = "2026-11-23"
        kev2 = {"meta": {}, "eintraege": self.kev["eintraege"] + [
            kev_klein("CVE-3", "Fortinet", "FortiOS", "2026-11-23", ransom=True),
            kev_klein("CVE-4", "Zyxel", "Box", "2026-11-23")]}
        bsi2 = {"eintraege": self.bsi["eintraege"] + [
            {"id": "W3", "schwere": "kritisch", "titel": "Neu", "link": "https://w/3", "datum": "2026-11-23"},
            {"id": "W4", "schwere": "hoch", "titel": "Egal", "link": "https://w/4", "datum": "2026-11-23"}]}
        n, z2 = notify.ermittle(kev2, bsi2, None, self.lage, z, self.jetzt)
        self.assertEqual(len(n), 1)  # nur der Ransomware-Alarm
        self.assertIn("CVE-3", n[0]); self.assertIn("Alarm", n[0]); self.assertNotIn("CVE-4", n[0])
        self.assertEqual(len(z2["offen"]["kev"]), 1)
        self.assertEqual(len(z2["offen"]["bsi"]), 1)
        n2, z3 = notify.ermittle(kev2, bsi2, None, self.lage, z2, self.jetzt)
        self.assertEqual(n2, [])  # nichts doppelt, nichts zwischendurch
        from datetime import datetime, timezone
        morgen = datetime(2026, 11, 24, 8, 0, tzinfo=timezone.utc)
        n3, z4 = notify.ermittle(kev2, bsi2, None, self.lage, z3, morgen)
        self.assertEqual(len(n3), 1)  # eine Tageslage mit allem Offenen
        self.assertIn("CVE-4", n3[0]); self.assertIn("Neu", n3[0]); self.assertNotIn("Egal", n3[0]); self.assertNotIn("CVE-3", n3[0])
        self.assertEqual(z4["offen"], {"kev": [], "bsi": [], "eu": []})

    def test_html_wird_maskiert(self):
        _, z = notify.ermittle(self.kev, self.bsi, None, self.lage, None, self.jetzt)
        z["gesehen"]["bsi"] = []; z["zusammenfassung"] = None
        n, _ = notify.ermittle(self.kev, self.bsi, None, self.lage, z, self.jetzt)
        self.assertIn("Foo &lt;b&gt;", n[0])

    def test_stufenwechsel_und_tageslage_einmal(self):
        _, z = notify.ermittle(self.kev, self.bsi, None, self.lage, None, self.jetzt)
        z["zusammenfassung"] = None
        lage2 = dict(self.lage, stufe="hoch")
        n, z2 = notify.ermittle(self.kev, self.bsi, None, lage2, z, self.jetzt)
        self.assertTrue(any("Stufe geändert" in x and "hoch" in x for x in n))
        self.assertTrue(any("Tageslage" in x for x in n))
        n2, _ = notify.ermittle(self.kev, self.bsi, None, lage2, z2, self.jetzt)
        self.assertEqual(n2, [])

    def test_lange_liste_wird_gekuerzt(self):
        _, z = notify.ermittle({"meta": {}, "eintraege": []}, None, None, self.lage, None, self.jetzt)
        z["zusammenfassung"] = None
        viele = {"meta": {}, "eintraege": [kev_klein(f"CVE-{i}", "H", "P", "2026-11-23") for i in range(25)]}
        n, _ = notify.ermittle(viele, None, None, self.lage, z, self.jetzt)
        self.assertIn("15 weitere", n[0])
        self.assertLessEqual(len(n[0]), notify.MAX_ZEICHEN)


class AusblickTests(unittest.TestCase):
    NVD = {"totalResults": 3, "vulnerabilities": [
        {"cve": {"id": "CVE-2026-1001", "published": "2026-11-20T10:15:00.000", "vulnStatus": "Analyzed",
                 "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 9.8}}, {"cvssData": {"baseScore": 7.5}}]}}},
        {"cve": {"id": "CVE-2026-1002", "published": "2026-11-21T08:00:00.000", "vulnStatus": "Rejected"}},
        {"cve": {"id": "CVE-2026-1003", "published": "2026-11-22T08:00:00.000", "vulnStatus": "Received",
                 "metrics": {"cvssMetricV30": [{"cvssData": {"baseScore": 5.0}}]}}},
    ]}
    EPSS = {"data": [
        {"cve": "CVE-2026-1001", "epss": "0.730000000", "percentile": "0.985000000", "date": "2026-11-23"},
        {"cve": "CVE-2026-1003", "epss": "0.020000000", "percentile": "0.610000000", "date": "2026-11-23"},
        {"cve": "CVE-2026-1004", "epss": "kaputt", "percentile": "0.1", "date": "2026-11-23"},
    ]}

    def test_nvd_ohne_abgelehnte_und_mit_hoechstem_cvss(self):
        v = fetch_ausblick.parse_nvd(self.NVD)
        self.assertEqual([x["cve"] for x in v], ["CVE-2026-1001", "CVE-2026-1003"])
        self.assertEqual(v[0]["cvss"], 9.8)
        self.assertEqual(v[0]["veroeffentlicht"], "2026-11-20")
        self.assertEqual(v[1]["cvss"], 5.0)

    def test_epss_zahlen_und_kaputte_zeilen(self):
        e = fetch_ausblick.parse_epss(self.EPSS)
        self.assertEqual(set(e), {"CVE-2026-1001", "CVE-2026-1003"})
        self.assertAlmostEqual(e["CVE-2026-1001"][0], 0.73)

    def test_baue_ohne_kev_sortiert_und_zaehlt(self):
        from datetime import datetime, timezone
        cves = fetch_ausblick.parse_nvd(self.NVD)
        e = fetch_ausblick.parse_epss(self.EPSS)
        r = fetch_ausblick.baue(cves, e, {"CVE-2026-1003"}, datetime(2026, 11, 24, tzinfo=timezone.utc))
        self.assertEqual([z["cve"] for z in r["liste"]], ["CVE-2026-1001"])  # 1003 steht schon im KEV
        self.assertEqual(r["geprueft"], 1)
        self.assertEqual(r["hoch_wahrscheinlich"], 1)
        r2 = fetch_ausblick.baue(cves, e, set(), datetime(2026, 11, 24, tzinfo=timezone.utc))
        self.assertEqual([z["cve"] for z in r2["liste"]], ["CVE-2026-1001", "CVE-2026-1003"])
        self.assertEqual(r2["hoch_wahrscheinlich"], 1)
        self.assertEqual(r2["epss_datum"], "2026-11-23")

    def test_ohne_ausblick_ist_der_wert_none_und_stufe_unveraendert(self):
        kev = {"meta": {}, "eintraege": [kev_klein("CVE-1", "H", "P", "2026-11-20")]}
        a = score.werte_aus(kev, REGELN_FREI, [], STAND)
        self.assertIsNone(a["ausblick"])
        r = score.werte_aus(kev, REGELN_FREI, [], STAND, ausblick={"liste": [], "geprueft": 0})
        self.assertEqual(r["stufe"], a["stufe"])
        self.assertTrue(any(q["id"] == "epss" for q in r["quellen"]))
        self.assertTrue(any(q["id"] == "nvd" for q in r["quellen"]))


class FeedTests(unittest.TestCase):
    def test_feed(self):
        import sys, xml.dom.minidom
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
        import feed
        lage = {"stand": "2026-11-24", "stufe": "hoch", "stufe_begruendung": "36 & mehr.",
                "neu": [{"cve": "CVE-1-1", "hersteller": "A<b>", "produkt": "P", "hinzugefuegt": "2026-11-23", "frist": None, "ransomware_bekannt": True, "link": "https://x/y?a=1&b=2"}],
                "cert_bund": {"liste": [{"id": "WID-1", "schwere": "kritisch", "titel": "T", "datum": "2026-11-22", "link": "https://w"},
                                        {"id": "WID-2", "schwere": "hoch", "titel": "U", "datum": "2026-11-22", "link": "https://w"}]}}
        x = feed.baue(lage)
        xml.dom.minidom.parseString(x.encode())
        self.assertEqual(x.count("<item>"), 2)
        self.assertIn("kev-CVE-1-1", x)
        self.assertNotIn("wid-WID-2", x)
        self.assertIn("Ransomware", x)


if __name__ == "__main__":
    unittest.main()
