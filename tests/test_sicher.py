import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sicher  # noqa: E402
from audit import dateien  # noqa: E402


class SicherTest(unittest.TestCase):
    def test_nur_https(self):
        self.assertEqual(sicher.nur_https("https://endoflife.date/api/x.json"), "https://endoflife.date/api/x.json")
        for schlecht in ("http://a.de/", "file:///etc/passwd", "ftp://a.de/x", "//a.de/x", "https:///x", ""):
            with self.assertRaises(ValueError, msg=schlecht):
                sicher.nur_https(schlecht)

    def test_xml_normal(self):
        self.assertEqual(sicher.xml_lesen(b"<a><b>1</b></a>").find("b").text, "1")
        self.assertEqual(sicher.xml_lesen("<a/>").tag, "a")

    def test_xml_mit_entity_wird_abgelehnt(self):
        bombe = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><x>&a;</x>'
        with self.assertRaises(ET.ParseError):
            sicher.xml_lesen(bombe)
        with self.assertRaises(ET.ParseError):
            sicher.xml_lesen(b"<!DocType x><x/>")

    def test_audit_sitemap_lehnt_doctype_ab(self):
        adr, fehler = dateien.sitemap_adressen('<!DOCTYPE s [<!ENTITY a "b">]><urlset><url><loc>https://h.de/&a;</loc></url></urlset>', "h.de")
        self.assertEqual(adr, [])
        self.assertTrue(fehler)


if __name__ == "__main__":
    unittest.main()
