"""Matrix-Modus ist ein abschaltbares Modul: Standard aus, nur über die Markierung <!--matrix--> eingebunden."""
import re, unittest
from pathlib import Path
W = Path(__file__).resolve().parent.parent


class T(unittest.TestCase):
    def test_modul_eingebunden_und_standard_aus(self):
        s = (W / "site" / "index.html").read_text(encoding="utf-8")
        m = re.search(r"<!--matrix-->(.*?)<!--/matrix-->", s, re.S)
        self.assertTrue(m, "Markierung <!--matrix--> fehlt")
        self.assertIn("/matrix.css", m.group(1))
        self.assertIn("/matrix.js", m.group(1))
        self.assertEqual(s.count("matrix.js"), 1)
        self.assertNotRegex(s.split("</head>")[0].split("<html")[1].split(">")[0], "matrix")  # nicht von Haus aus an

    def test_dateien_ohne_netz_und_ohne_inline(self):
        js = (W / "site" / "matrix.js").read_text(encoding="utf-8")
        for verboten in ("fetch(", "XMLHttpRequest", "http://", "https://", "eval(", "innerHTML"):
            self.assertNotIn(verboten, js)
        self.assertIn("prefers-reduced-motion", js)

    def test_englische_seite_hat_das_modul(self):
        en = W / "site" / "en" / "index.html"
        if en.exists():
            self.assertIn("/matrix.js", en.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
