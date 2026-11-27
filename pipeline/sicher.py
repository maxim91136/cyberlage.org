"""Gemeinsame Schutzfunktionen für alle Abrufe (nur Standardbibliothek).

- nur_https: Abrufe gehen ausschließlich an https-Adressen (kein file:, ftp:, http:).
- xml_lesen: XML aus fremden Quellen wird nur gelesen, wenn es keine DOCTYPE- oder ENTITY-Angaben enthält.
  Damit sind Entity-Bomben und externe Entitäten ausgeschlossen, auch wenn die Parser-Bibliothek sie zuließe.
"""
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit


def nur_https(url):
    teile = urlsplit(str(url))
    if teile.scheme != "https" or not teile.hostname:
        raise ValueError("nur https-Adressen erlaubt: " + str(url)[:80])
    return url


def xml_lesen(daten):
    roh = daten if isinstance(daten, (bytes, bytearray)) else str(daten).encode("utf-8", errors="replace")
    kopf = roh.lower()
    if b"<!doctype" in kopf or b"<!entity" in kopf:
        raise ET.ParseError("XML mit DOCTYPE oder ENTITY wird nicht gelesen")
    return ET.fromstring(roh)  # nosec B314 (DOCTYPE und ENTITY vorher abgelehnt)
