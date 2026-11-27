import re
import unittest
from pathlib import Path

WF = Path(__file__).resolve().parent.parent / ".github" / "workflows"


class DatenLaufTests(unittest.TestCase):
    def test_wartender_lauf_holt_neuesten_stand(self):
        """Läufe der Gruppe "daten" warten aufeinander. Checkout ohne ref nähme den Commit vom Zeitpunkt der
        Einreihung: Der wartende Lauf kennt dann den Meldestand des ersten nicht und Telegram sendet doppelt."""
        text = (WF / "daten.yml").read_text(encoding="utf-8")
        self.assertIn("group: daten", text)
        self.assertRegex(text, r"actions/checkout@[0-9a-f]{40}[^\n]*\n\s+with:\n\s+ref: main")

    def test_codeaudit_workflow(self):
        """Das Code-Audit läuft in der Gruppe "daten", holt den neuesten Stand (ref: main), setzt Berechtigungen und pinnt jede Action."""
        text = (WF / "codeaudit.yml").read_text(encoding="utf-8")
        self.assertIn("group: daten", text)
        self.assertRegex(text, r"actions/checkout@[0-9a-f]{40}[^\n]*\n\s+with:\n\s+ref: main")
        self.assertRegex(text, r"(?m)^permissions:")
        for z in re.findall(r"uses:\s*(\S+)", text):
            self.assertRegex(z, r"@[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
