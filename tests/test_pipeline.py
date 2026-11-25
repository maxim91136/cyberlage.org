import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))

import bereiche  # noqa: E402
import fetch_ausblick  # noqa: E402
import fetch_radar  # noqa: E402
import fetch_extra  # noqa: E402
import notify  # noqa: E402
import pruefen  # noqa: E402
import fetch_patches  # noqa: E402
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
        self.assertTrue(any("Dreier-Pegel geändert" in x and "hoch" in x for x in n))
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


class TageslageZeitTests(unittest.TestCase):
    def test_ab_sechs_uhr_deutscher_zeit(self):
        from datetime import datetime, timezone
        kev = {"meta": {}, "eintraege": []}
        lage = {"stufe": "hoch", "stufe_begruendung": "x", "kev": {"neu_7_tage": 1, "neu_30_tage": 2}}
        _, z = notify.ermittle(kev, None, None, lage, None, datetime(2026, 11, 23, 12, 0, tzinfo=timezone.utc))
        fruh = datetime(2026, 11, 24, 4, 50, tzinfo=timezone.utc)   # 05:50 Winterzeit: noch nicht
        spaet = datetime(2026, 11, 24, 5, 20, tzinfo=timezone.utc)  # 06:20 Winterzeit: jetzt
        self.assertEqual(notify.ermittle(kev, None, None, lage, z, fruh)[0], [])
        self.assertEqual(len(notify.ermittle(kev, None, None, lage, z, spaet)[0]), 1)
        sommer = datetime(2026, 7, 1, 4, 50, tzinfo=timezone.utc)   # 06:50 Sommerzeit
        _, zs = notify.ermittle(kev, None, None, lage, None, datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc))
        self.assertEqual(len(notify.ermittle(kev, None, None, lage, zs, sommer)[0]), 1)


class RadarTests(unittest.TestCase):
    def test_zeit_bis_aufnahme(self):
        from datetime import date
        kev = [{"cve": "A", "hinzugefuegt": "2026-11-10"}, {"cve": "B", "hinzugefuegt": "2026-11-12"},
               {"cve": "C", "hinzugefuegt": "2026-11-12"}, {"cve": "D", "hinzugefuegt": "2026-11-12"}]
        veroeff = {"A": "2026-11-08", "B": "2026-11-12", "C": "2010-01-01", "D": None}
        z = fetch_radar.zeit_bis_aufnahme(kev, veroeff, date(2026, 11, 24))
        m = z["verlauf"][0]
        self.assertEqual((m["monat"], m["n"], m["n_frisch"]), ("2026-11", 3, 2))  # C alt, D ohne Datum
        self.assertEqual(m["median_frisch"], 1.0)
        self.assertEqual(z["jetzt"]["n"], 3)
        self.assertEqual(z["ohne_datum"], 1)

    def test_trefferquote_merkt_prognosen_und_zaehlt_treffer(self):
        from datetime import date
        ab = {"abgerufen_am": "2026-10-01T00:00:00+00:00", "schwelle_hoch": 0.1,
              "kandidaten": [{"cve": "X", "epss": 0.5, "veroeffentlicht": "2026-09-30"}, {"cve": "Y", "epss": 0.2, "veroeffentlicht": "2026-09-30"}]}
        prog = {}
        kev = [{"cve": "X", "hinzugefuegt": "2026-10-05"}]
        t = fetch_radar.trefferquote(prog, kev, ab, date(2026, 11, 24))
        self.assertEqual((t["prognosen"], t["eingetreten"], t["reif"], t["reif_eingetreten"]), (2, 1, 2, 1))
        self.assertEqual(t["quote_reif"], 0.5)
        self.assertEqual(t["median_tage_bis_eintritt"], 4)
        jung = fetch_radar.trefferquote({}, [], ab, date(2026, 10, 10))
        self.assertIsNone(jung["quote_reif"])
        self.assertEqual(jung["offen"], 2)

    def test_europa_und_score(self):
        eu = {"eintraege": [{"cve": ["A"], "ausgenutzt_seit": "2026-11-08"}, {"cve": ["Q"], "ausgenutzt_seit": "2026-11-08"}]}
        e = fetch_radar.abgleich_eu([{"cve": "A", "hinzugefuegt": "2026-11-10"}], eu)
        self.assertEqual((e["auch_im_cisa"], e["nur_eu"], e["median_abstand_tage"]), (1, 1, 2))
        self.assertIsNone(fetch_radar.abgleich_eu([], None))
        kev = {"meta": {}, "eintraege": []}
        self.assertIsNone(score.werte_aus(kev, REGELN_FREI, [], STAND)["radar"])
        r = score.werte_aus(kev, REGELN_FREI, [], STAND, radar={"abgerufen_am": "x", "zeit_bis_kev": {"verlauf": list(range(50))}})
        self.assertEqual(len(r["radar"]["zeit_bis_kev"]["verlauf"]), 36)
        self.assertTrue(any(q["id"] == "cvelist" for q in r["quellen"]))


class KonsensTests(unittest.TestCase):
    ZEIT = {"jetzt": {"n_frisch": 20, "median_frisch": 5}, "vor_12_monaten": {"n_frisch": 20, "median_frisch": 11}}
    BSI = [{"wert": "170", "basis": "100"}]

    def test_zaehlt_unabhaengige_signale(self):
        k = fetch_radar.konsens("hoch", self.ZEIT, self.BSI, {"status": "green"})
        self.assertEqual((k["erhoeht"], k["bewertet"]), (1, 2))  # nur externe zählen: BSI ja, SANS nein
        namen = {s["name"]: s["erhoeht"] for s in k["signale"]}
        self.assertTrue(namen["KEV-Menge"] and namen["Tempo bis KEV"] and namen["BSI Cyber Index"])
        self.assertFalse(namen["SANS Infocon"])


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



class NcscTests(unittest.TestCase):
    def test_zaehlt_dreissig_tage_und_hoch_hoch(self):
        import datetime, fetch_radar
        x = ('<rss><channel><item><title>a high/high</title><pubDate>Mon, 23 Nov 2026 10:00:00 +0100</pubDate></item>'
             '<item><title>b</title><description>Kans: medium Schade: high</description><pubDate>Sun, 22 Nov 2026 10:00:00 +0100</pubDate></item>'
             '<item><title>alt</title><pubDate>Mon, 01 Jan 2026 10:00:00 +0100</pubDate></item></channel></rss>')
        self.assertEqual(fetch_radar.ncsc_zaehlen(x, datetime.date(2026, 11, 24)), {"advisories_30": 2, "hoch_hoch_30": 1})


class AusschlagTests(unittest.TestCase):
    def test_ausschlag_und_englische_stufe(self):
        import fetch_radar
        k = fetch_radar.konsens("hoch", {}, [{"wert": "170", "basis": "100"}], {"status": "yellow"}, 36, 25)
        d = {x["name_en"]: x for x in k["signale"]}
        self.assertEqual(d["KEV count"]["ausschlag"], 1.44)
        self.assertEqual(d["KEV count"]["grund_en"], "level high")
        self.assertEqual(d["BSI Cyber Index"]["ausschlag"], 1.42)
        self.assertEqual(d["SANS Infocon"]["ausschlag"], 1.1)


class PegelTests(unittest.TestCase):
    def test_reihe_live_bleibt_und_rueckrechnung_fuellt(self):
        import datetime, score
        alle = [{"hinzugefuegt": "2026-11-20", "ransomware_bekannt": 0}, {"hinzugefuegt": "2026-11-23", "ransomware_bekannt": 1}]
        regeln = {"status": "freigegeben", "fenster_tage": 30, "erhoeht_ab": 25, "hoch_ab": 32, "ransomware_aufschlag_ab": 5}
        heute = datetime.date(2026, 11, 24)
        alt = [{"stand": "2026-11-22", "wert": 99, "ransomware_bekannt": 0, "stufe": "hoch", "quelle": "live"}]
        r = score.pegel_fortschreiben(alt, alle, regeln, heute, monate=1)
        d = {p["stand"]: p for p in r}
        self.assertEqual(d["2026-11-22"]["wert"], 99)  # Live-Eintrag bleibt unverändert
        self.assertEqual(d["2026-11-24"]["wert"], 2)
        self.assertEqual(d["2026-11-24"]["quelle"], "live")
        self.assertEqual(d["2026-11-23"]["quelle"], "rueckgerechnet")


class VorbelegenTests(unittest.TestCase):
    def test_startwerte_und_hinweise_im_html(self):
        import prerender
        html_in = ('<div class="stufe mono" id="stufe-wert">…</div><div class="stufe-text" id="stufe-text" data-t="l_lade">Daten werden geladen</div>'
                   '<b id="k7">…</b><b id="k30">…</b><b id="kall">…</b><b id="kr">…</b><ul id="hinweise" class="hinw"></ul>')
        lage = {"stufe": "hoch", "kev": {"neu_7_tage": 10, "neu_30_tage": 36, "gesamt": 1792, "ransomware_bekannt_30_tage": 1}, "hinweise": ["Ein Hinweis"]}
        out = prerender.vorbelegen(html_in, lage)
        self.assertIn('id="stufe-wert">hoch<', out)
        self.assertIn('id="stufe-text" hidden>', out)
        self.assertIn('id="kall">1.792<', out)
        self.assertIn("<li>Ein Hinweis</li>", out)
        self.assertEqual(prerender.vorbelegen(out, lage), out)  # idempotent


class RadarScoreTests(unittest.TestCase):
    def test_mittelwert_und_leere_signale(self):
        import fetch_radar
        sig = [{"ausschlag": 1.0}, {"ausschlag": 3.0}, {"ausschlag": None}]
        self.assertEqual(fetch_radar.radar_score(sig), {"wert": 75, "signale": 2, "von": 3})  # 3,0 wird auf 2,0 gedeckelt: (1+2)/2/2
        self.assertIsNone(fetch_radar.radar_score([{"ausschlag": None}]))

class PruefkalenderTests(unittest.TestCase):
    def test_faellig_und_link_tot(self):
        from datetime import datetime, timezone
        jetzt = datetime(2026, 11, 24, tzinfo=timezone.utc)
        fehl = lambda url: (False, 404)
        ok = lambda url: (True, 200)
        spaet = date(2027, 3, 1)  # nach der 90-Tage-Frist der Gründe, vor der der Jahresangaben
        r1 = pruefen.pruefen(spaet, None, pruefer=ok, jetzt=jetzt)
        namen = [e["id"] for e in r1["eintraege"] if e["faellig"]]
        self.assertIn("r7q3", namen)
        self.assertNotIn("BSI Cyber Index 2026", namen)
        self.assertNotIn("schwellen", namen)  # 183 Tage ab 23.11.2026, am 1.3.2027 noch nicht fällig
        spaeter = pruefen.pruefen(date(2027, 6, 1), None, pruefer=ok, jetzt=jetzt)
        self.assertIn("schwellen", [e["id"] for e in spaeter["eintraege"] if e["faellig"]])
        self.assertIn("radar_stufen", [e["id"] for e in r1["eintraege"] if e["faellig"]])  # 90 Tage ab 24.11.2026, am 1.3.2027 fällig
        # ein Fehlschlag allein ist noch kein toter Link; erst wenn es 24 Stunden lang bei jedem Versuch scheitert
        r2 = pruefen.pruefen(date(2026, 11, 24), None, pruefer=fehl, jetzt=jetzt)
        self.assertFalse(any(e["link_tot"] for e in r2["eintraege"]))
        r2b = pruefen.pruefen(date(2026, 11, 24), r2, pruefer=fehl, jetzt=datetime(2026, 11, 24, 6, tzinfo=timezone.utc))
        self.assertFalse(any(e["link_tot"] for e in r2b["eintraege"]))
        r3 = pruefen.pruefen(date(2026, 11, 25), r2b, pruefer=fehl, jetzt=datetime(2026, 11, 25, 1, tzinfo=timezone.utc))
        self.assertTrue(all(e["link_tot"] for e in r3["eintraege"]))
        self.assertEqual(len(r3["offen"]), len(r3["eintraege"]))
        # eine Erholung setzt den Zähler zurück
        r4 = pruefen.pruefen(date(2026, 11, 25), r3, pruefer=ok, jetzt=datetime(2026, 11, 25, 3, tzinfo=timezone.utc))
        self.assertFalse(any(e["link_tot"] for e in r4["eintraege"]))

    def test_nicht_oefter_als_taeglich(self):
        from datetime import datetime, timezone
        jetzt = datetime(2026, 11, 24, 8, tzinfo=timezone.utc)
        n = []
        def zaehl(url):
            n.append(url)
            return True, 200
        r = pruefen.pruefen(date(2026, 11, 24), None, pruefer=zaehl, jetzt=jetzt)
        erste = len(n)
        pruefen.pruefen(date(2026, 11, 24), r, pruefer=zaehl, jetzt=jetzt.replace(hour=10))
        self.assertEqual(len(n), erste)


class RadarStufenTests(unittest.TestCase):
    def setUp(self):
        import json
        self.cfg = json.loads((Path(__file__).resolve().parent.parent / "config" / "radar_stufen.json").read_text(encoding="utf-8"))

    def test_grenzen(self):
        import score
        namen = {w: score.radar_stufe(w, self.cfg)["name"] for w in (0, 34, 35, 49, 50, 63, 64, 79, 80, 100)}
        self.assertEqual(namen[0], "ruhig"); self.assertEqual(namen[34], "ruhig"); self.assertEqual(namen[35], "unauffällig")
        self.assertEqual(namen[49], "unauffällig"); self.assertEqual(namen[50], "angespannt"); self.assertEqual(namen[63], "angespannt")
        self.assertEqual(namen[64], "hoch"); self.assertEqual(namen[79], "hoch"); self.assertEqual(namen[80], "außergewöhnlich")
        self.assertEqual(namen[100], "außergewöhnlich")

    def test_fazit(self):
        import score
        f = score.fazit({"wert": 61}, "hoch", self.cfg)
        self.assertEqual(f["stufe"], "angespannt")
        self.assertIn("KEV-Menge liegt weit über dem Üblichen", f["text"])
        self.assertTrue(f["text"].startswith("Die Bausteine liegen im Schnitt über"))  # Stufe des Gesamtscores zuerst, dann die Bausteine
        self.assertEqual(f["status"], "vorlaeufig")
        self.assertIsNone(score.fazit(None, "hoch", self.cfg))
        self.assertIsNone(score.fazit({"wert": 61}, "unbekannt", self.cfg))

    def test_alle_stufen_haben_texte(self):
        for st in self.cfg["stufen"]:
            for k in ("name", "name_en", "satz", "satz_en"):
                self.assertTrue(st[k])
        for k in ("niedrig", "erhöht", "hoch"):
            for f in ("satz", "satz_en", "hinweis", "hinweis_en"):
                self.assertTrue(self.cfg["pegel"][k][f])
        self.assertEqual([st["bis"] for st in self.cfg["stufen"]], sorted(st["bis"] for st in self.cfg["stufen"]))


def _ms_dok(monat="2026-Nov", cves=None, aktuell="2026-11-10T08:00:00Z"):
    """Kleines CVRF-Beispiel in der Form der MSRC-Schnittstelle."""
    cves = cves if cves is not None else [
        ("CVE-2026-0001", "Windows Kernel Elevation of Privilege Vulnerability", "Critical", "Elevation of Privilege", "Publicly Disclosed:No;Exploited:Yes;Latest Software Release:Exploitation Detected", ["1", "2"]),
        ("CVE-2026-0002", "Microsoft Word Remote Code Execution Vulnerability", "Important", "Remote Code Execution", "Publicly Disclosed:Yes;Exploited:No;", ["3"]),
        ("CVE-2026-0003", "Chromium: CVE-2026-0003 Use after free in Blink", "Important", "Remote Code Execution", "Publicly Disclosed:No;Exploited:No;", ["4"]),
        ("CVE-2026-0004", "Azure Service Information Disclosure Vulnerability", "Moderate", "Information Disclosure", "Publicly Disclosed:No;Exploited:No;", ["5"]),
        ("CVE-2026-0005", "kernel: some Linux flaw", "", "", "", ["6"]),
    ]
    return {
        "DocumentTracking": {"Identification": {"ID": {"Value": monat}}, "InitialReleaseDate": "2026-11-10T08:00:00Z", "CurrentReleaseDate": aktuell},
        "ProductTree": {"Branch": [{"Items": [{"Items": [
            {"ProductID": "1", "Value": "Windows 11 Version 24H2 for x64-based Systems"},
            {"ProductID": "2", "Value": "Windows Server 2025"},
            {"ProductID": "3", "Value": "Microsoft Word 2021"},
            {"ProductID": "4", "Value": "Microsoft Edge (Chromium-based)"},
            {"ProductID": "5", "Value": "Azure Stack HCI"},
            {"ProductID": "6", "Value": "Azure Linux 3.0 x64 kernel 6.6"}]}]}]},
        "Vulnerability": [{"CVE": c, "Title": {"Value": t},
                           "Threats": [{"Type": 3, "Description": {"Value": sv}}, {"Type": 0, "Description": {"Value": imp}}, {"Type": 1, "Description": {"Value": ex}}],
                           "ProductStatuses": [{"Type": 3, "ProductID": ids}]} for c, t, sv, imp, ex, ids in cves],
    }


class PatchTests(unittest.TestCase):
    def test_verdichten(self):
        m = fetch_patches.verdichte_dokument(_ms_dok(), kev_cves=["CVE-2026-0001"])
        self.assertEqual(m["cves"], 3)                      # Chromium nicht mitgezählt
        self.assertEqual(m["davon_chromium_ausgenommen"], 1)
        self.assertEqual(m["davon_azure_linux_ausgenommen"], 1)
        self.assertEqual(m["schwere"]["Critical"], 1)
        self.assertEqual(m["schwere"]["Important"], 1)
        self.assertEqual(m["ausgenutzt"], 1)
        self.assertEqual(m["oeffentlich_bekannt"], 1)
        self.assertEqual(m["im_kev"], 1)
        self.assertEqual(m["familien"]["Windows 11"], 1)
        self.assertEqual(m["familien"]["Windows Server"], 1)
        self.assertEqual(m["familien"]["Office und SharePoint"], 1)
        self.assertEqual(m["familien"]["Cloud und Dienste"], 1)
        self.assertEqual(m["auswirkung"]["Elevation of Privilege"], 1)

    def test_bewertung(self):
        monat = {"cves": 80, "ausgenutzt": 2, "schwere": {"Critical": 5}}
        vor = [{"cves": 60}] * 6
        b = fetch_patches.bewerte(monat, vor)
        self.assertEqual(b["groesse"], "größer als üblich")
        self.assertEqual(b["dringlichkeit"], "dringend")
        self.assertEqual(b["empfehlung"], "Zuerst die Patches für die 2 bereits ausgenutzten Lücken einspielen. Danach die monatlichen Sammelupdates für Windows und Office einspielen: Sie enthalten auch die 5 als kritisch eingestuften Lücken.")
        b1 = fetch_patches.bewerte({"cves": 80, "ausgenutzt": 1, "schwere": {"Critical": 1}}, vor)
        self.assertEqual(b1["empfehlung"], "Zuerst den Patch für die bereits ausgenutzte Lücke einspielen. Danach die monatlichen Sammelupdates für Windows und Office einspielen: Sie enthalten auch die als kritisch eingestufte Lücke.")
        self.assertEqual(fetch_patches.bewerte({"cves": 60, "ausgenutzt": 0, "schwere": {"Critical": 3}}, vor)["empfehlung"], "Die monatlichen Sammelupdates für Windows und Office zeitnah einspielen: Sie enthalten auch die 3 als kritisch eingestuften Lücken.")
        b2 = fetch_patches.bewerte({"cves": 60, "ausgenutzt": 0, "schwere": {"Critical": 0}}, vor)
        self.assertEqual((b2["groesse"], b2["dringlichkeit"]), ("üblicher Umfang", "normal"))
        b3 = fetch_patches.bewerte({"cves": 60, "ausgenutzt": 0, "schwere": {"Critical": 1}}, [{"cves": 60}])
        self.assertIn("noch kein Vergleich", b3["groesse"])  # unter 3 Vormonaten kein Vergleich

    def test_monatsliste_filtert(self):
        liste = {"value": [{"ID": "1999-Sep"}, {"ID": "2026-Oct"}, {"ID": "2026-Nov"}, {"ID": "2026-Sep"}, {"ID": "2026-Nov-Mariner"}]}
        self.assertEqual([e["ID"] for e in fetch_patches.monatsliste(liste, 2)], ["2026-Oct", "2026-Nov"])

    def test_nachtrag_und_nicht_neu_holen(self):
        from datetime import datetime, timezone
        jetzt = datetime(2026, 11, 20, tzinfo=timezone.utc)
        liste = {"value": [{"ID": "2026-Nov", "CurrentReleaseDate": "2026-11-10T08:00:00Z", "CvrfUrl": "u"}]}
        geholt = []
        def hole(url):
            geholt.append(url)
            return _ms_dok()
        a = fetch_patches.aktualisiere(None, liste, hole, [], jetzt)
        self.assertEqual(len(geholt), 1)
        b = fetch_patches.aktualisiere(a, liste, hole, [], jetzt)
        self.assertEqual(len(geholt), 1)  # unverändert: nicht erneut geholt
        # Out-of-Band: Dokument wurde später um eine Lücke ergänzt
        liste2 = {"value": [{"ID": "2026-Nov", "CurrentReleaseDate": "2026-11-18T08:00:00Z", "CvrfUrl": "u"}]}
        mehr = _ms_dok(aktuell="2026-11-18T08:00:00Z")
        mehr["Vulnerability"].append({"CVE": "CVE-2026-0009", "Title": {"Value": "Windows OOB Remote Code Execution Vulnerability"},
                                      "Threats": [{"Type": 3, "Description": {"Value": "Critical"}}, {"Type": 1, "Description": {"Value": "Exploited:Yes"}}],
                                      "ProductStatuses": [{"Type": 3, "ProductID": ["1"]}]})
        c = fetch_patches.aktualisiere(b, liste2, lambda u: mehr, [], jetzt)
        m = c["monate"]["2026-Nov"]
        self.assertEqual(m["cves"], 4)
        self.assertEqual(m["nachtraege"][0]["neue_cves"], 1)
        self.assertEqual(m["nachtraege"][0]["ausgenutzt_neu"], 1)

    def test_fehler_je_monat_ist_nicht_fatal(self):
        from datetime import datetime, timezone
        jetzt = datetime(2026, 11, 20, tzinfo=timezone.utc)
        liste = {"value": [{"ID": "2026-Oct", "CurrentReleaseDate": "x", "CvrfUrl": "u1"}, {"ID": "2026-Nov", "CurrentReleaseDate": "y", "CvrfUrl": "u2"}]}
        def hole(url):
            if url == "u1":
                raise OSError("Zeitüberschreitung")
            return _ms_dok()
        r = fetch_patches.aktualisiere(None, liste, hole, [], jetzt)
        self.assertEqual(list(r["monate"]), ["2026-Nov"])
        self.assertEqual(len(r["meta"]["fehler"]), 1)
        with self.assertRaises(fetch_patches.QuellFehler):
            fetch_patches.aktualisiere(None, liste, lambda u: (_ for _ in ()).throw(OSError("x")), [], jetzt)


class HerstellerPatchTests(unittest.TestCase):
    def test_ubuntu_redhat(self):
        u = fetch_patches.parse_ubuntu({"notices": [
            {"id": "USN-1-1", "published": "2026-11-20T16:08:41.2", "title": "Kernel vulnerabilities", "cves_ids": ["CVE-2026-1111", "CVE-2026-2222"]},
            {"id": "USN-2-1", "published": "2026-10-01T10:00:00", "title": "alt", "cves_ids": []},
            {"id": "USN-3-1", "published": "kaputt", "title": "x"}]})
        self.assertEqual([x["id"] for x in u], ["USN-1-1", "USN-2-1"])
        z = fetch_patches.verdichte_quelle(u, date(2026, 11, 24))
        self.assertEqual((z["neu_7"], z["neu_30"], z["cves_30"], z["schwere_bekannt"], z["kritisch_30"]), (1, 1, 2, False, None))
        r = fetch_patches.parse_redhat([{"RHSA": "RHSA-2026:1", "severity": "Critical", "released_on": "2026-11-22T00:00:00Z", "CVEs": ["CVE-2026-3333"]},
                                         {"RHSA": "RHSA-2026:2", "severity": "Important", "released_on": "2026-11-23T00:00:00Z", "CVEs": []}])
        z = fetch_patches.verdichte_quelle(r, date(2026, 11, 24))
        self.assertEqual((z["neu_30"], z["kritisch_30"], z["hoch_30"]), (2, 1, 1))

    def test_bereiche_zuordnung(self):
        cfg = json.loads((Path(__file__).resolve().parent.parent / "config" / "bereiche.json").read_text(encoding="utf-8"))
        z = lambda h, p: bereiche.zuordnen(h, p, cfg)
        self.assertEqual(z("Cisco", "IOS XE"), "netzwerk")               # nicht Arbeitsplatz wegen "ios"
        self.assertEqual(z("Hewlett Packard Enterprise (HPE)", "Juniper Session Smart Router"), "netzwerk")
        self.assertEqual(z("Apple", "iOS and iPadOS"), "arbeitsplatz")
        self.assertEqual(z("Microsoft", "Office"), "arbeitsplatz")
        self.assertEqual(z("Microsoft", "Windows"), "windows")
        self.assertEqual(z("Microsoft", "SharePoint Server"), "windows")
        self.assertEqual(z("SAP", "NetWeaver"), "anwendungen")
        self.assertEqual(z("WordPress", "Plugin"), "linux")               # nicht Arbeitsplatz wegen "word"
        self.assertEqual(z("Apache", "Tomcat"), "linux")
        self.assertEqual(z("Unbekannt GmbH", "Ding"), "sonstige")
        for b in cfg["bereiche"]:
            __import__("re").compile(b["muster"])

    def test_bereiche_in_der_lage(self):
        cfg = json.loads((Path(__file__).resolve().parent.parent / "config" / "bereiche.json").read_text(encoding="utf-8"))
        kev = {"meta": {"quelle": "CISA KEV", "quelle_url": "https://example.org", "abgerufen_am": "2026-11-23T00:00:00+00:00", "katalog_version": "t", "veroeffentlicht_am": "2026-11-23", "lizenz": "CC0"}, "eintraege": [{"cve": "CVE-2026-1", "hersteller": "Fortinet", "produkt": "FortiOS", "hinzugefuegt": "2026-11-20", "frist": "2026-12-11", "ransomware_bekannt": False},
                             {"cve": "CVE-2026-2", "hersteller": "Mozilla", "produkt": "Firefox", "hinzugefuegt": "2026-11-01", "frist": "2026-11-22", "ransomware_bekannt": False}]}
        r = score.werte_aus(kev, REGELN_FREI, [], date(2026, 11, 23), bereiche_cfg=cfg)
        self.assertEqual({e["cve"]: e["bereich"] for e in r["neu"]}, {"CVE-2026-1": "netzwerk", "CVE-2026-2": "arbeitsplatz"})
        b = {x["id"]: x for x in r["bereiche"]["liste"]}
        self.assertEqual((b["netzwerk"]["anzahl"], b["netzwerk"]["anzahl_7"], b["arbeitsplatz"]["anzahl"], b["arbeitsplatz"]["anzahl_7"], b["windows"]["anzahl"]), (1, 1, 1, 0, 0))
        self.assertNotIn("bereiche", score.werte_aus(kev, REGELN_FREI, [], date(2026, 11, 23)))

    def test_feed_rss_und_atom(self):
        rss = b"""<rss><channel><item><title>PAN-SA-2026-0004 Chromium: Monthly Vulnerability Update (Severity: MEDIUM)</title><link>https://security.paloaltonetworks.com/PAN-SA-2026-0004</link>
          <pubDate>Wed, 18 Nov 2026 17:00:00 GMT</pubDate><description>Fixes CVE-2026-1111 and CVE-2026-2222</description></item>
          <item><title>ohne Datum</title><link>https://x.example/1</link></item></channel></rss>"""
        r = fetch_patches.parse_feed(rss, "paloalto", fetch_patches.FEEDS["paloalto"][1])
        self.assertEqual(len(r), 1)
        self.assertEqual((r[0]["id"], r[0]["schwere"], r[0]["cves"], r[0]["datum"].isoformat()), ("PAN-SA-2026-0004", "mittel", ["CVE-2026-1111", "CVE-2026-2222"], "2026-11-18"))
        atom = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>FG-IR-26-123 Buffer overflow in FortiOS</title><link href="https://fortiguard.fortinet.com/psirt/FG-IR-26-123"/><updated>2026-11-20T10:00:00Z</updated><summary>text</summary></entry></feed>"""
        r = fetch_patches.parse_feed(atom, "fortinet", fetch_patches.FEEDS["fortinet"][1])
        self.assertEqual((r[0]["id"], r[0]["link"], r[0]["schwere"], r[0]["cves"]), ("FG-IR-26-123", "https://fortiguard.fortinet.com/psirt/FG-IR-26-123", None, []))
        with self.assertRaises(fetch_patches.QuellFehler):
            fetch_patches.parse_feed(b"<html>kaputt", "x")

    def test_mozilla_uebersicht(self):
        seite = """<h2 class="c-h">November 17, 2026</h2><ul><li class="level-item"><a href="/en-US/security/advisories/mfsa2026-91/"><span class="level high">MFSA 2026-91</span> Security Vulnerabilities fixed in Firefox 158</a></li>
          <li><a href="/en-US/security/advisories/mfsa2026-90/">MFSA 2026-90 Security Vulnerabilities fixed in Thunderbird 158</a></li></ul><h2>October 20, 2026</h2><ul><li><a href="/en-US/security/advisories/mfsa2026-80/">MFSA 2026-80 Firefox ESR 140.16</a></li></ul>"""
        r = fetch_patches.parse_mozilla(seite)
        self.assertEqual([(i["id"], i["datum"].isoformat()) for i in r], [("MFSA 2026-91", "2026-11-17"), ("MFSA 2026-90", "2026-11-17"), ("MFSA 2026-80", "2026-10-20")])
        self.assertEqual(r[0]["titel"], "MFSA 2026-91 Security Vulnerabilities fixed in Firefox 158")
        self.assertEqual(r[0]["link"], "https://www.mozilla.org/en-US/security/advisories/mfsa2026-91/")
        self.assertEqual(fetch_patches.parse_mozilla("<p>nichts</p>"), [])

    def test_neue_quellen_fallen_weich_aus(self):
        def lade(url):
            if "paloaltonetworks" in url:
                return b"<rss><channel><item><title>CVE-2026-0233 ADEM (Severity: HIGH)</title><link>https://security.paloaltonetworks.com/CVE-2026-0233</link><pubDate>Fri, 20 Nov 2026 17:00:00 GMT</pubDate></item></channel></rss>"
            raise OSError("aus")
        heute = date(2026, 11, 23)
        self.assertEqual(len(fetch_patches.hole_quelle("paloalto", heute, lade)), 1)
        with self.assertRaises(fetch_patches.QuellFehler):
            fetch_patches.hole_quelle("fortinet", heute, lade)
        self.assertTrue(all(q.get("bereich") for q in fetch_patches.QUELLEN))

    def test_redhat_container_titel(self):
        r = fetch_patches.parse_redhat([{"RHSA": "RHSA-2026:7", "released_on": "2026-11-23T00:00:00Z", "CVEs": [],
                                         "released_packages": ["registry.redhat.io/exploit-intelligence/agent-client-rhel9@sha256:abc123", "ruby-3.3.1-1.el9", "ruby-debuginfo-3.3.1-1.el9"]}])
        self.assertEqual(r[0]["titel"], "RHSA-2026:7: exploit-intelligence/agent-client-rhel9, ruby")

    def test_redhat_csv(self):
        csv = '"2026/rhsa-2026_1234.json","2026-11-20T12:00:00+00:00"\n"2026/rhba-2026_9.json","2026-11-20T12:00:00+00:00"\n"2026/rhsa-2026_1234.json","2026-11-21T01:00:00+00:00"\n'
        r = fetch_patches.parse_redhat_csv(csv)
        self.assertEqual([(x["id"], str(x["datum"])) for x in r], [("RHSA-2026:1234", "2026-11-20")])  # RHBA ignoriert, Duplikat einmal

    def test_debian_cisco(self):
        rdf = b"""<?xml version="1.0"?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns="http://purl.org/rss/1.0/" xmlns:dc="http://purl.org/dc/elements/1.1/">
        <item><title>DSA-6012-1 libfoo -- security update</title><link>https://www.debian.org/security/2026/dsa-6012</link><dc:date>2026-11-21</dc:date><description>CVE-2026-4444</description></item></rdf:RDF>"""
        d = fetch_patches.parse_debian(rdf)
        self.assertEqual((d[0]["id"], d[0]["cves"]), ("DSA-6012-1", ["CVE-2026-4444"]))
        rss = b"""<?xml version="1.0"?><rss version="2.0"><channel><item><title>PHP Affecting Cisco Products</title>
        <link>https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-php?vs_f=x</link><pubDate>2026-11-23 20:20:00.0</pubDate>
        <description>&lt;b&gt;Security Impact Rating:&lt;/b&gt; Critical CVE-2026-5555</description></item></channel></rss>"""
        c = fetch_patches.parse_cisco(rss)
        self.assertEqual((c[0]["schwere"], c[0]["cves"], c[0]["link"].endswith("cisco-sa-php")), ("kritisch", ["CVE-2026-5555"], True))
        with self.assertRaises(fetch_patches.QuellFehler):
            fetch_patches.parse_cisco(b"kein xml")

    def test_aktualisieren_fail_soft(self):
        from datetime import datetime, timezone
        jetzt = datetime(2026, 11, 24, 6, tzinfo=timezone.utc)
        def lade(url):
            if "ubuntu" in url:
                return json.dumps({"notices": [{"id": "USN-9-1", "published": "2026-11-23T10:00:00", "title": "t", "cves_ids": []}]}).encode()
            raise OSError("gesperrt")
        r = fetch_patches.aktualisiere_hersteller(None, date(2026, 11, 24), jetzt, lade)
        self.assertEqual(r["quellen"]["ubuntu"]["status"], "ok")
        self.assertEqual(r["quellen"]["ubuntu"]["neu_30"], 1)
        self.assertEqual(r["quellen"]["cisco"]["status"], "fehler")
        # ein früher gültiger Stand bleibt bei einem Fehler erhalten
        r2 = fetch_patches.aktualisiere_hersteller(r, date(2026, 11, 25), jetzt, lambda u: (_ for _ in ()).throw(OSError("x")))
        self.assertEqual(r2["quellen"]["ubuntu"]["neu_30"], 1)
        self.assertEqual(r2["quellen"]["ubuntu"]["status"], "fehler")


class TempoTests(unittest.TestCase):
    CFG = {"mindest_n": 10, "erhoeht_bis": 5, "hoch_bis": 3, "fenster_tage": 90}

    def test_stufe(self):
        st = fetch_radar.tempo_stufe
        self.assertEqual(st(6.5, 40, self.CFG), "niedrig")
        self.assertEqual(st(5.0, 40, self.CFG), "erhoeht")
        self.assertEqual(st(3.0, 40, self.CFG), "hoch")
        self.assertEqual(st(2.0, 40, self.CFG), "hoch")
        self.assertIsNone(st(2.0, 9, self.CFG))      # zu wenige frische Lücken
        self.assertIsNone(st(None, 40, self.CFG))
        self.assertIsNone(st(5.0, 40, None))

    def test_reihe_und_median(self):
        from datetime import date
        kev = [{"cve": "CVE-%d" % i, "hinzugefuegt": "2026-11-%02d" % (10 + i % 10)} for i in range(12)]
        veroeff = {"CVE-%d" % i: "2026-11-%02d" % (10 + i % 10 - 4) for i in range(12)}  # immer 4 Tage vorher
        med, n = fetch_radar.tempo_median(kev, veroeff, date(2026, 11, 24))
        self.assertEqual((med, n), (4, 12))
        reihe = fetch_radar.tempo_reihe(kev, veroeff, date(2026, 11, 24), tage=5)
        self.assertTrue(reihe and reihe[-1]["wert"] == 4 and reihe[-1]["stand"] == "2026-11-24")

    def test_konsens_mit_tempo(self):
        zeit = {"jetzt": {"n_frisch": 50, "median_frisch": 4.0}, "vor_12_monaten": {"n_frisch": 50, "median_frisch": 11.0}}
        k = fetch_radar.konsens("hoch", zeit, [], None, 39, 25, tempo_cfg=self.CFG)
        namen = {x["name_en"]: x for x in k["signale"]}
        self.assertIn("KEV pace", namen)
        self.assertTrue(namen["KEV pace"]["erhoeht"])
        self.assertEqual(namen["KEV pace"]["ausschlag"], 1.25)  # 5 / 4
        self.assertEqual(namen["KEV pace"]["art"], "eigen")     # zählt nicht als Bestätigung

    def test_fazit_mit_tempo(self):
        import score
        cfg = json.loads((Path(__file__).resolve().parent.parent / "config" / "radar_stufen.json").read_text(encoding="utf-8"))
        f = score.fazit({"wert": 61}, "niedrig", cfg, "hoch")
        self.assertIn("Tempo bis KEV ist ungewöhnlich schnell", f["text"])
        self.assertEqual(f["hinweis"], cfg["pegel"]["hoch"]["hinweis"])  # die höhere der beiden Stufen bestimmt den Hinweis


class PrioritaetTests(unittest.TestCase):
    def test_reihenfolge_und_zeitfenster(self):
        heute = date(2026, 11, 25)
        monat = {"erste_veroeffentlichung": "2026-11-10T08:00:00Z", "kandidaten": [
            {"cve": "CVE-A", "titel": "kritisch", "schwere": "Critical", "ausgenutzt": False, "oeffentlich": False, "kev": False, "familien": ["Windows 11"]},
            {"cve": "CVE-B", "titel": "ausgenutzt", "schwere": "Important", "ausgenutzt": True, "oeffentlich": False, "kev": False, "familien": []},
            {"cve": "CVE-C", "titel": "im KEV", "schwere": "Important", "ausgenutzt": True, "oeffentlich": False, "kev": True, "familien": []},
            {"cve": "CVE-D", "titel": "epss", "schwere": "Important", "ausgenutzt": False, "oeffentlich": False, "kev": False, "familien": []},
            {"cve": "CVE-E", "titel": "unauffällig", "schwere": "Important", "ausgenutzt": False, "oeffentlich": False, "kev": False, "familien": []}]}
        alt = dict(monat, erste_veroeffentlichung="2026-08-10T08:00:00Z")  # zu alt, nicht mehr "diese Woche"
        alt = dict(alt, kandidaten=[dict(monat["kandidaten"][2], cve="CVE-ALT")])
        pr = fetch_patches.priorisiere([alt, monat], {}, [], {"CVE-D": (0.4, 0.9, "2026-11-25")}, heute)
        self.assertEqual([k["cves"][0] for k in pr["liste"]], ["CVE-C", "CVE-B", "CVE-D", "CVE-A"])
        self.assertEqual([k["stufe"] for k in pr["liste"]], [1, 2, 3, 4])
        self.assertEqual(pr["liste"][0]["rang"], 1)
        self.assertIn("EPSS 40 %", pr["liste"][2]["grund"])

    def test_distribution_mit_kev(self):
        heute = date(2026, 11, 25)
        items = [{"id": "USN-1-1", "datum": date(2026, 11, 22), "titel": "Kernel", "link": "u", "schwere": None, "cves": ["CVE-K1", "CVE-X"]},
                 {"id": "USN-2-1", "datum": date(2026, 11, 22), "titel": "andere", "link": "u2", "schwere": None, "cves": ["CVE-X"]}]
        z = fetch_patches.verdichte_quelle(items, heute, kev=["CVE-K1"])
        self.assertEqual(z["im_kev_30"], 1)
        self.assertEqual(z["im_kev_meldungen"][0]["cves_kev"], ["CVE-K1"])
        hs = {"quellen": {"ubuntu": dict(z, name="Ubuntu Security Notices", status="ok", typ="distribution", letzte=[])}}
        pr = fetch_patches.priorisiere([], hs, ["CVE-K1"], {}, heute)
        self.assertEqual(len(pr["liste"]), 1)
        self.assertEqual(pr["liste"][0]["quelle"], "Ubuntu Security Notices")
        self.assertEqual(pr["liste"][0]["stufe"], 1)

    def test_epss_fehler_ist_nicht_fatal(self):
        def lade(url):
            raise OSError("gesperrt")
        self.assertEqual(fetch_patches.hole_epss(["CVE-1"], lade), {})
        ok = lambda url: {"data": [{"cve": "CVE-1", "epss": "0.5", "percentile": "0.9", "date": "2026-11-25"}]}
        self.assertEqual(fetch_patches.hole_epss(["CVE-1"], ok)["CVE-1"][0], 0.5)


class PatchMeldeTests(unittest.TestCase):
    def setUp(self):
        from datetime import datetime, timezone
        self.jetzt = datetime(2026, 11, 25, 9, 0, tzinfo=timezone.utc)  # Mittwoch
        self.kev = {"meta": {}, "eintraege": [kev_klein("CVE-1", "Cisco", "X", "2026-11-20")]}
        monat = {"id": "2026-Nov", "erste_veroeffentlichung": "2026-11-10T08:00:00Z", "aktuell": "2026-11-10T08:00:00Z", "cves": 120, "schwere": {"Critical": 9},
                 "ausgenutzt": 2, "oeffentlich_bekannt": 1, "im_kev": 2, "ausgenutzt_cves": ["CVE-2026-0001"], "nachtraege": [],
                 "bewertung": {"groesse": "größer als üblich", "dringlichkeit": "dringend", "empfehlung": "Ausgenutzte zuerst."}}
        self.lage = {"stufe": "hoch", "stufe_begruendung": "39 neu.", "kev": {"neu_7_tage": 9, "neu_30_tage": 39},
                     "patches": {"microsoft": {"monate": {"2026-Nov": monat}}, "prioritaet": {"liste": [
                         {"rang": 1, "quelle": "Microsoft", "link": "https://m/1", "cves": ["CVE-2026-0001"], "titel": "t", "grund": "Steht im CISA-KEV."}]}},
                     "fazit": {"ampel": "angespannt", "kev_stufe": "hoch", "tempo_stufe": "erhoeht", "status": "vorlaeufig", "text": "Der Dreier-Pegel steht auf hoch.", "hinweis": "Täglich abgleichen."}}

    def test_ohne_vorstand_nur_merken(self):
        n, _ = notify.patch_nachrichten(self.lage, None, self.jetzt)
        self.assertEqual(n, [])
        n, z = notify.patch_nachrichten(self.lage, {"ms": {"2026-Nov": {"aktuell": "x", "nachtraege": 0}}}, self.jetzt)
        self.assertEqual(n, [])  # bekannter Monat ohne Nachtrag

    def test_neuer_patchday_und_nachtrag(self):
        self.lage["patches"]["microsoft"]["monate"]["2026-Nov"]["erste_veroeffentlichung"] = "2026-11-18T08:00:00Z"  # innerhalb der 10 Tage
        n, z = notify.patch_nachrichten(self.lage, {"ms": {}}, self.jetzt)
        self.assertEqual(len(n), 1)
        self.assertIn("Patch Day 2026-Nov", n[0])
        self.assertIn("120 CVEs", n[0])
        self.assertIn("Dringlichkeit: <b>dringend</b>", n[0])
        self.lage["patches"]["microsoft"]["monate"]["2026-Nov"]["nachtraege"] = [{"am": "2026-11-18", "neue_cves": 3, "ausgenutzt_neu": 1}]
        n2, _ = notify.patch_nachrichten(self.lage, z, self.jetzt)
        self.assertEqual(len(n2), 1)
        self.assertIn("Nachtrag", n2[0])
        self.assertIn("3 neue", n2[0])

    def test_alter_monat_nicht_nachtraeglich_melden(self):
        self.lage["patches"]["microsoft"]["monate"]["2026-Nov"]["erste_veroeffentlichung"] = "2026-09-10T08:00:00Z"
        n, _ = notify.patch_nachrichten(self.lage, {"ms": {}}, self.jetzt)
        self.assertEqual(n, [])

    def test_fazit_nur_bei_aenderung_oder_montags(self):
        zustand = {"gesehen": {"kev": ["CVE-1"], "bsi": [], "eu": []}, "stufe": "hoch", "zusammenfassung": "2026-11-24", "offen": {"kev": [], "bsi": [], "eu": []},
                   "patches": {"ms": {"2026-Nov": {"aktuell": "2026-11-10T08:00:00Z", "nachtraege": 0}}}, "fazit_gesendet": None}
        n, z = notify.ermittle(self.kev, None, None, self.lage, zustand, self.jetzt)
        tages = [x for x in n if "Tageslage" in x][0]
        self.assertIn("Fazit", tages)
        self.assertIn("Diese Woche zuerst patchen", tages)
        self.assertEqual(z["fazit_gesendet"], "angespannt|hoch|erhoeht")
        # gleicher Stand, kein Montag: kein Fazit
        z["zusammenfassung"] = "2026-11-24"
        n2, _ = notify.ermittle(self.kev, None, None, self.lage, z, self.jetzt)
        self.assertNotIn("Fazit", [x for x in n2 if "Tageslage" in x][0])
        # Montag: Wochenstand
        from datetime import datetime, timezone
        montag = datetime(2026, 11, 30, 9, 0, tzinfo=timezone.utc)
        z["zusammenfassung"] = "2026-11-29"
        n3, _ = notify.ermittle(self.kev, None, None, self.lage, z, montag)
        self.assertIn("Fazit", [x for x in n3 if "Tageslage" in x][0])


class AusblickTextTests(unittest.TestCase):
    def test_beschreibung_und_produkt(self):
        import fetch_ausblick as fa
        d = [{"lang": "es", "value": "x"}, {"lang": "en", "value": "A use-after-free in Foo allows remote code execution. More text follows."}]
        self.assertEqual(fa.kurzbeschreibung(d), "A use-after-free in Foo allows remote code execution.")
        self.assertEqual(fa.kurzbeschreibung(None), "")
        lang = [{"lang": "en", "value": "x" * 400}]
        self.assertTrue(len(fa.kurzbeschreibung(lang)) <= 170)
        konf = [{"nodes": [{"cpeMatch": [{"criteria": "cpe:2.3:a:apache:http_server:2.4:*:*:*:*:*:*:*"}]}]}]
        self.assertEqual(fa.produkt_aus_cpe(konf), "apache http server")
        self.assertEqual(fa.produkt_aus_cpe([{"nodes": [{"cpeMatch": [{"criteria": "cpe:2.3:o:*:*"}]}]}]), "")
        r = fa.parse_nvd({"vulnerabilities": [{"cve": {"id": "CVE-1", "published": "2026-11-20T00:00:00", "descriptions": d, "configurations": konf}}]})
        self.assertEqual(r[0]["produkt"], "apache http server")
        self.assertTrue(r[0]["beschreibung"].startswith("A use-after-free"))


class PatchStandTests(unittest.TestCase):
    def test_patch_stand(self):
        self.assertEqual(fetch_patches.patch_stand({"Remediations": [{"Type": 2, "Description": {"Value": "5068861"}}]}), ("ja", ["5068861"]))
        self.assertEqual(fetch_patches.patch_stand({"Remediations": [{"Type": 1, "Description": {"Value": "Mitigation"}}]}), ("nein", []))
        self.assertEqual(fetch_patches.patch_stand({}), ("unbekannt", []))

    def test_ohne_patch_nicht_in_rangliste(self):
        from datetime import date
        ms = [{"erste_veroeffentlichung": "2026-11-11T08:00:00Z", "kandidaten": [
            {"cve": "CVE-1", "titel": "A", "schwere": "Critical", "ausgenutzt": True, "oeffentlich": False, "kev": True, "patch": "ja", "kb": ["5068861"], "familien": ["Windows"]},
            {"cve": "CVE-2", "titel": "B", "schwere": "Critical", "ausgenutzt": True, "oeffentlich": False, "kev": True, "patch": "nein", "kb": [], "familien": ["Windows"]}]}]
        r = fetch_patches.priorisiere(ms, {}, [], {}, date(2026, 11, 25))
        self.assertEqual([k["cves"][0] for k in r["liste"]], ["CVE-1"])
        self.assertIn("KB5068861", r["liste"][0]["patch_text"])
        self.assertEqual([k["cves"][0] for k in r["ohne_patch"]], ["CVE-2"])


class CvssTests(unittest.TestCase):
    def test_hole_cvss_cache_und_fehler(self):
        def lade(url):
            if "CVE-2" in url:
                raise OSError("x")
            return {"vulnerabilities": [{"cve": {"metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 9.8}}]}}}]}
        cache = fetch_patches.hole_cvss(["CVE-1", "CVE-2"], {"CVE-3": 5.0}, lade=lade, pause=0)
        self.assertEqual(cache["CVE-1"], 9.8)
        self.assertNotIn("CVE-2", cache)  # Fehler: Wert bleibt offen
        self.assertEqual(cache["CVE-3"], 5.0)

    def test_rang_innerhalb_stufe_nach_epss_dann_cvss(self):
        from datetime import date
        ms = [{"erste_veroeffentlichung": "2026-11-11T08:00:00Z", "kandidaten": [
            {"cve": "CVE-A", "titel": "A", "schwere": "Critical", "ausgenutzt": True, "oeffentlich": False, "kev": True, "patch": "ja", "cvss": 7.0, "familien": []},
            {"cve": "CVE-B", "titel": "B", "schwere": "Critical", "ausgenutzt": True, "oeffentlich": False, "kev": True, "patch": "ja", "cvss": 9.0, "familien": []}]}]
        r = fetch_patches.priorisiere(ms, {}, [], {}, date(2026, 11, 25))
        self.assertEqual([k["cves"][0] for k in r["liste"]], ["CVE-B", "CVE-A"])
        self.assertEqual(r["liste"][0]["cvss"], [{"cve": "CVE-B", "score": 9.0}])
        self.assertEqual(r["liste"][0]["stufe_name"], "im CISA-KEV, nachweislich angegriffen")


class OhnePatchChromiumTests(unittest.TestCase):
    def test_chromium_getrennt_mit_version(self):
        doc = {"DocumentTracking": {"Identification": {"ID": {"Value": "2026-Nov"}}, "InitialReleaseDate": "2026-11-10T08:00:00"}, "ProductTree": {}, "Vulnerability": [
            {"CVE": "CVE-C1", "Title": {"Value": "Use after free in XML in Google Chrome prior to 157.0.8103.50 allowed x"}, "Threats": [{"Type": 1, "Description": {"Value": "Exploited:Yes"}}],
             "Remediations": [{"Type": 2, "FixedBuild": "157.0.3300.20", "Description": {"Value": "Release Notes"}}]},
            {"CVE": "CVE-C2", "Title": {"Value": "Chromium: CVE-x Heap overflow"}, "Remediations": [{"Type": 2, "FixedBuild": "156.0.3200.1"}]}]}
        r = fetch_patches.verdichte_dokument(doc, [])
        self.assertEqual(r["cves"], 0)
        self.assertEqual(r["chromium"]["anzahl"], 2)
        self.assertEqual(r["chromium"]["edge"], "157.0.3300.20")
        self.assertEqual(r["chromium"]["chrome"], "157.0.8103.50")
        self.assertEqual([x["cve"] for x in r["chromium"]["kev"]], ["CVE-C1"])


class SapTests(unittest.TestCase):
    def test_parse_sap(self):
        import fetch_patches as fp
        h = ("<p>On 10th of March 2026, SAP security patch day saw the release of 2 new security notes.</p>"
             "<td>[CVE-2026-0001] Missing authorization in SAP S/4HANA</td><td>Product - SAP S/4HANA</td><td>High</td><td>7.5</td><td>3698553</td>"
             "<td>[CVE-2026-0002] Hot thing in SAP Commerce</td><td>Product - X</td><td>Critical</td><td>9.1</td>"
             "<p>1 previously released security notes were updated.</p><td>[CVE-2025-1] alt</td>")
        r = fp.parse_sap(h, "u")
        self.assertEqual(len(r), 2)
        self.assertEqual(r[0]["datum"].isoformat(), "2026-03-10")
        self.assertEqual(r[0]["schwere"], "hoch")
        self.assertEqual(r[1]["schwere"], "kritisch")
        self.assertEqual(r[1]["cves"], ["CVE-2026-0002"])


class ModellTests(unittest.TestCase):
    CFG = {"obergrenze": 2.0, "gruppen": [{"id": "a", "name": "A", "name_en": "A"}, {"id": "b", "name": "B", "name_en": "B"}],
           "bausteine": [{"id": "x", "gruppe": "a", "status": "aktiv"}, {"id": "y", "gruppe": "a", "status": "aktiv"},
                         {"id": "z", "gruppe": "b", "status": "aktiv"}, {"id": "w", "gruppe": "b", "status": "beobachtung"}]}

    def test_score_mittelt_je_gruppe_und_ignoriert_beobachtung(self):
        import modell
        s = modell.score({"x": 1.0, "y": 3.0, "z": 0.5, "w": 2.0}, self.CFG)  # x,y -> (1+2)/2=1,5 ; z 0,5 ; Mittel 1,0 -> 50
        self.assertEqual(s["wert"], 50)
        self.assertEqual((s["signale"], s["von"]), (3, 3))

    def test_gruppe_ohne_messwert_zaehlt_nicht(self):
        import modell
        s = modell.score({"x": 1.0}, self.CFG)
        self.assertEqual(s["wert"], 50)
        self.assertEqual(len(s["gruppen"]), 1)
        self.assertIsNone(modell.score({}, self.CFG))

    def test_ausnutzung_reihe_nur_ausnutzungsgruppe(self):
        import modell
        cfg = {"obergrenze": 2.0, "gruppen": [{"id": "ausnutzung", "name": "A", "name_en": "A"}, {"id": "extern", "name": "E", "name_en": "E"}],
               "bausteine": [{"id": "kev_menge", "gruppe": "ausnutzung", "status": "aktiv"}, {"id": "tempo", "gruppe": "ausnutzung", "status": "aktiv"},
                             {"id": "bsi", "gruppe": "extern", "status": "aktiv"}]}
        r = modell.ausnutzung_reihe([{"stand": "2026-01-01", "wert": 25}, {"stand": "2026-01-02", "wert": 50}], 25, [{"stand": "2026-01-01", "wert": 5.0}], 5, cfg)
        self.assertEqual((r[0]["ausnutzung"], r[0]["n"]), (50, 2))
        self.assertEqual((r[1]["ausnutzung"], r[1]["n"]), (100, 1))


class ArchivTests(unittest.TestCase):
    def test_erstdatum_nimmt_fruehestes_datum_hoeherer_nummern(self):
        import modell
        e = modell.erstdatum({"WID-SEC-2026-0001": "2026-03-01", "WID-SEC-2026-0002": "2026-01-05", "WID-SEC-2026-0003": "2026-01-07", "WID-SEC-2025-0900": "2026-02-01"})
        self.assertEqual(e["WID-SEC-2026-0001"], "2026-01-05")
        self.assertEqual(e["WID-SEC-2026-0003"], "2026-01-07")
        self.assertEqual(e["WID-SEC-2025-0900"], "2025-12-31")

    def test_fenster_reihe_zaehlt_gleitend(self):
        import modell
        r = modell.fenster_reihe(["2026-01-01", "2026-01-02", "2026-01-02", "2026-01-05"], 2, "2026-01-02", "2026-01-05")
        self.assertEqual([x["wert"] for x in r], [3, 2, 0, 1])

    def test_archiv_microsoft_ist_stufenreihe(self):
        import modell
        r = modell.archiv_reihen({"microsoft": {"monate": {"a": {"tag": "2026-01-01", "ausgenutzt": 2}, "b": {"tag": "2026-01-03", "ausgenutzt": 0}}}}, "2026-01-04")
        self.assertEqual([x["wert"] for x in r["ms_ausgenutzt"]], [2, 2, 0, 0])

    def test_rueck_reihe_ohne_externe(self):
        import modell
        cfg = {"obergrenze": 2.0, "gruppen": [{"id": "a", "name": "A", "name_en": "A"}, {"id": "extern", "name": "E", "name_en": "E"}],
               "bausteine": [{"id": "x", "gruppe": "a", "status": "aktiv"}, {"id": "y", "gruppe": "extern", "status": "aktiv"}]}
        r = modell.rueck_reihe({"x": {"2026-01-01": 1.0}, "y": {"2026-01-01": 2.0}}, cfg)
        self.assertEqual(r, [{"stand": "2026-01-01", "ausnutzung": 50, "n": 1}])


class DistroTests(unittest.TestCase):
    def test_suse_mbox(self):
        import fetch_patches as p
        txt = ("From null at suse.de  Mon Nov  2 08:30:35 2026\nFrom: null at suse.de\nDate: Mon, 02 Nov 2026 08:30:35 -0000\n"
               "Subject: SUSE-SU-2026:4984-1: important: Security update for the\n Linux Kernel\nMessage-ID: <x>\n\n# Security update\nCross-References:\n  * CVE-2026-53016\n\n"
               "From null at suse.de  Mon Nov  2 09:00:00 2026\nDate: Mon, 02 Nov 2026 09:00:00 -0000\nSubject: SUSE-RU-2026:1-1: moderate: Recommended update\n\nx\n")
        r = p.parse_suse(txt)
        self.assertEqual(len(r), 1)
        self.assertEqual((r[0]["id"], r[0]["schwere"], r[0]["cves"], r[0]["titel"]), ("SUSE-SU-2026:4984-1", "hoch", ["CVE-2026-53016"], "SUSE-SU-2026:4984-1: Linux Kernel"))
        self.assertTrue(r[0]["link"].endswith("/2026/suse-su-20264984-1/"))

    def test_alma_rocky_amazon(self):
        import fetch_patches as p
        rss = b"<rss><channel><item><title>[ALSA-2026:53844] Important: iscsi security update</title><link>https://e/x.html</link><pubDate>Wed, 12 Aug 2026 09:24:35 +0000</pubDate><description>fix CVE-2026-1234</description></item></channel></rss>"
        a = p.parse_alma(rss)[0]
        self.assertEqual((a["id"], a["schwere"], a["cves"]), ("ALSA-2026:53844", "hoch", ["CVE-2026-1234"]))
        r = p.parse_rocky({"advisories": [{"name": "RLSA-2026:103408", "synopsis": "Important: gnome-remote-desktop security update", "severity": "SEVERITY_IMPORTANT",
                                           "publishedAt": "2026-11-25T12:07:26.538210Z", "cves": [{"name": "CVE-2026-132858"}]}]})[0]
        self.assertEqual((r["titel"], r["schwere"], r["cves"]), ("RLSA-2026:103408: gnome-remote-desktop security update", "hoch", ["CVE-2026-132858"]))
        am = p.parse_amazon(b"<rss><channel><item><title>ALAS2023-2026-3508 (important): firefox</title><link>https://a/x</link><pubDate>Fri, 20 Nov 2026 16:24:00 GMT</pubDate><description>CVE-2026-115506, CVE-2026-117610</description></item></channel></rss>")[0]
        self.assertEqual((am["id"], am["schwere"], len(am["cves"])), ("ALAS2023-2026-3508", "hoch", 2))


class DshieldTests(unittest.TestCase):
    def test_parse_und_sieben_tage_mittel_ohne_laufenden_tag(self):
        import fetch_historie, modell
        self.assertEqual(fetch_historie.parse_dshield([{"date": "2026-01-01", "records": "9", "targets": 2, "sources": 100}, {"date": "x"}]), {"2026-01-01": [9, 2, 100]})
        tage = {"2026-01-%02d" % i: [0, 0, 100 * i] for i in range(1, 10)}
        r = modell.archiv_reihen({"dshield": {"tage": tage}}, "2026-01-09")["dshield"]
        self.assertEqual(r[0], {"stand": "2026-01-08", "wert": 400})   # Mittel aus 1. bis 7.
        self.assertEqual(r[-1], {"stand": "2026-01-09", "wert": 500})  # der 9. selbst zählt nicht mit


class RansomTests(unittest.TestCase):
    def test_parse_zaehlt_nur_und_fenster_ohne_laufenden_tag(self):
        import fetch_historie, modell
        self.assertEqual(fetch_historie.parse_ransom({"posts": [{"post_title": "X", "discovered": "2026-01-02T10:00:00"}, {"discovered": "2026-01-02 11:00:00"}, {"discovered": None}]}), {"2026-01-02": 2})
        tage = {"2026-01-%02d" % i: 1 for i in range(1, 32)}; tage["2026-02-01"] = 50
        r = modell.archiv_reihen({"ransomware": {"tage": tage}}, "2026-02-01")["ransomware"]
        self.assertEqual(r[-1], {"stand": "2026-02-01", "wert": 30})  # 2. bis 31. Januar, der laufende Tag zählt nicht


if __name__ == "__main__":
    unittest.main()
