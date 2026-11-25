"""Ordnet KEV-Einträge nach Hersteller und Produkt einem Bereich zu (config/bereiche.json). Nur Standardbibliothek.
Die Regeln werden der Reihe nach geprüft, die erste passende gilt; sonst 'sonstige'. Reine Namenszuordnung."""
import re


def zuordnen(hersteller, produkt, cfg):
    text = ("%s | %s" % (hersteller or "", produkt or "")).lower()
    for b in (cfg or {}).get("bereiche", []):
        if re.search(b["muster"], text):
            return b["id"]
    return ((cfg or {}).get("sonstige") or {}).get("id", "sonstige")


def uebersicht(eintraege, cfg, stand, tage_kurz=7):
    """Je Bereich: Name, Zweck und Zahl der Einträge im Fenster und in den letzten tage_kurz Tagen."""
    from datetime import date, timedelta
    grenze = (stand - timedelta(days=tage_kurz)).isoformat() if isinstance(stand, date) else ""
    liste = list((cfg or {}).get("bereiche", [])) + [(cfg or {}).get("sonstige") or {"id": "sonstige", "name": "Sonstige", "name_en": "Other"}]
    out = []
    for b in liste:
        mein = [e for e in eintraege if e.get("bereich") == b["id"]]
        out.append({"id": b["id"], "name": b["name"], "name_en": b.get("name_en", b["name"]), "fuer": b.get("fuer", ""), "fuer_en": b.get("fuer_en", ""),
                    "anzahl": len(mein), "anzahl_7": sum(1 for e in mein if grenze and e.get("hinzugefuegt", "") > grenze)})
    return out
