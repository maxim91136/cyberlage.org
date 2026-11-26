"""Audit: Gruppen DNS (CAA, DNSSEC) und Mail der Domain (SPF, DMARC). Reine Funktionen ohne Netz.
Maßstäbe: RFC 8659 (CAA), RFC 4033 bis 4035 (DNSSEC), RFC 7208 (SPF), RFC 7489 (DMARC), RFC 7505 (Null-MX)."""
import re


def _p(gruppe, pid, ergebnis, text):
    return (gruppe, pid, ergebnis, text)


def txt_werte(antworten):
    """DNS-over-HTTPS liefert TXT als "\"teil1\" \"teil2\"": Anführungszeichen weg, Teile zusammenfügen."""
    aus = []
    for a in antworten or []:
        teile = re.findall(r'"((?:[^"\\]|\\.)*)"', a)
        aus.append("".join(teile) if teile else a)
    return aus


def caa(eintraege):
    """eintraege: Liste der CAA-Antworten oder None, wenn die Abfrage scheiterte."""
    if eintraege is None:
        return [_p("dns", "caa", "nicht_geprueft", "CAA-Abfrage fehlgeschlagen")]
    return [_p("dns", "caa", "bestanden" if eintraege else "hinweis", "CAA-Einträge legen fest, wer Zertifikate ausstellen darf" if eintraege else "keine CAA-Einträge")]


def dnssec(ds_eintraege, validiert):
    """ds_eintraege: DS-Antworten (None bei Fehler); validiert: AD-Merker einer Antwort des validierenden Resolvers."""
    if ds_eintraege is None:
        return [_p("dns", "dnssec", "nicht_geprueft", "DNSSEC-Abfrage fehlgeschlagen")]
    if not ds_eintraege:
        return [_p("dns", "dnssec", "nicht_bestanden", "DNSSEC ist nicht aktiv (kein DS-Eintrag bei der Registrierung)")]
    return [_p("dns", "dnssec", "bestanden" if validiert else "nicht_bestanden",
               "DNSSEC aktiv und gültig" if validiert else "DS-Eintrag da, aber die Antwort wird nicht als gültig bestätigt")]


def spf(txt, ohne_mail=False):
    """ohne_mail: die Domain verschickt keine Mail, dann ist '-all' das Ziel."""
    werte = [t for t in txt_werte(txt) if t.lower().startswith("v=spf1")]
    if not werte:
        return [_p("mail", "spf", "nicht_bestanden", "SPF fehlt")]
    if len(werte) > 1:
        return [_p("mail", "spf", "nicht_bestanden", "mehrere SPF-Einträge (RFC 7208: genau einer)")]
    wert = werte[0].lower()
    if wert.rstrip().endswith("-all"):
        return [_p("mail", "spf", "bestanden", "SPF streng (-all)")]
    if wert.rstrip().endswith("~all"):
        return [_p("mail", "spf", "bestanden" if not ohne_mail else "hinweis", "SPF mit ~all" + (" (ohne Mail wäre -all besser)" if ohne_mail else ""))]
    return [_p("mail", "spf", "hinweis", "SPF endet nicht mit -all oder ~all")]


def dmarc(txt):
    werte = [t for t in txt_werte(txt) if t.lower().startswith("v=dmarc1")]
    if not werte:
        return [_p("mail", "dmarc", "nicht_bestanden", "DMARC fehlt")]
    m = re.search(r"(?i)\bp\s*=\s*(\w+)", werte[0])
    regel = (m.group(1).lower() if m else "")
    if regel == "reject":
        return [_p("mail", "dmarc", "bestanden", "DMARC streng (p=reject)")]
    if regel == "quarantine":
        return [_p("mail", "dmarc", "bestanden", "DMARC mit p=quarantine")]
    return [_p("mail", "dmarc", "hinweis", "DMARC ohne Wirkung (p=%s)" % (regel or "fehlt"))]
