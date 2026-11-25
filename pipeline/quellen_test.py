"""Prüft einzelne Hersteller-Quellen, ohne etwas zu speichern: python pipeline/quellen_test.py fortinet paloalto …
Zeigt je Quelle Zahl der Einträge, davon in 30 Tagen, neuestes Datum und einen Beispieltitel. Für neue Quellen vor dem ersten echten Lauf."""
import sys
from datetime import datetime, timezone

import fetch_patches as fp


def main(ids):
    heute = datetime.now(timezone.utc).date()
    ok = True
    for qid in ids or [q["id"] for q in fp.QUELLEN]:
        try:
            items = fp.hole_quelle(qid, heute)
            z = fp.verdichte_quelle(items, heute)
            neu = max(items, key=lambda i: i["datum"]) if items else None
            print("OK   %-9s %4d Einträge, %3d in 30 Tagen, %2d in 7, neuestes %s | %s | Schwere bekannt: %s | CVEs 30 T: %s" % (
                qid, len(items), z["neu_30"], z["neu_7"], neu["datum"] if neu else "-", (neu["titel"][:70] if neu else "-"), z["schwere_bekannt"], z["cves_30"]))
            if not items:
                ok = False
        except Exception as e:
            ok = False
            print("FEHL %-9s %s: %s" % (qid, type(e).__name__, str(e)[:200]))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
