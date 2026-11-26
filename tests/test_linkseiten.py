import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlparse

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "pipeline"))

import linkseiten  # noqa: E402
import pruefen  # noqa: E402

DATEN = json.loads((WURZEL / "data" / "links.json").read_text(encoding="utf-8"))


class LinkDatenTests(unittest.TestCase):
    def test_jeder_eintrag_vollstaendig(self):
        gruppen = {g["id"] for g in DATEN["gruppen"]}
        for x in DATEN["links"]:
            for k in ("id", "gruppe", "name", "url", "betreiber", "pflege", "de", "en", "geprueft_am"):
                self.assertTrue(x.get(k), (x.get("id"), k))
            self.assertIn(x["gruppe"], gruppen)
            self.assertIsInstance(x["im_pegel"], bool)
            self.assertRegex(x["geprueft_am"], r"^\d{4}-\d{2}-\d{2}$")

    def test_adressen_https_ohne_tracking(self):
        for x in DATEN["links"]:
            u = urlparse(x["url"])
            self.assertEqual(u.scheme, "https", x["id"])
            self.assertEqual(u.query, "", "Abfrageteil in %s" % x["id"])
            self.assertEqual(u.fragment, "", x["id"])

    def test_eindeutig(self):
        self.assertEqual(len({x["id"] for x in DATEN["links"]}), len(DATEN["links"]))
        self.assertEqual(len({x["url"] for x in DATEN["links"]}), len(DATEN["links"]))

    def test_kommunaler_notbetrieb_ist_drin(self):
        self.assertIn("kommunaler-notbetrieb.de", [urlparse(x["url"]).netloc for x in DATEN["links"]])

    def test_keine_werbe_oder_sicherheitsversprechen(self):
        for x in DATEN["links"]:
            for sp in ("de", "en"):
                self.assertNotRegex(x[sp].lower(), r"\b(beste[rns]?|sicher|garantiert|best)\b", x["id"])

    def test_prueflauf_kennt_die_links(self):
        ids = {e["id"] for e in pruefen.eintraege()}
        for x in DATEN["links"]:
            self.assertIn("link:" + x["id"], ids)


class LinkSeitenTests(unittest.TestCase):
    def schreibe(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        w = Path(tmp.name)
        (w / "data").mkdir()
        (w / "data" / "links.json").write_text(json.dumps(DATEN), encoding="utf-8")
        return w, linkseiten.schreibe(w)

    def test_beide_sprachen_alle_eintraege(self):
        w, sm = self.schreibe()
        self.assertEqual(sm[0][:2], ("/links/", "/en/links/"))
        for pfad, sp in (("links", "de"), ("en/links", "en")):
            s = (w / "site" / pfad / "index.html").read_text(encoding="utf-8")
            self.assertEqual(s.count('class="ln-k"'), len(DATEN["links"]))
            self.assertNotIn("<script", s)
            self.assertIn('lang="%s"' % sp, s)
            for x in DATEN["links"]:
                self.assertIn(x["url"], s)
            for a in re.findall(r"<a [^>]*>", s):
                if 'href="https://' in a and "cyberlage.org" not in a:
                    self.assertIn('target="_blank"', a)
                    self.assertIn('rel="noopener"', a)
            self.assertEqual(s.count('class="ln-pegel'), sum(1 for x in DATEN["links"] if x["im_pegel"]))

    def test_menue_zeigt_auf_die_seite(self):
        s = (WURZEL / "site" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<a href="/links/" id="n-links">', s)
        en = (WURZEL / "site" / "en" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<a href="/en/links/" id="n-links">', en)


if __name__ == "__main__":
    unittest.main()
