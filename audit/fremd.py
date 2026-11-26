"""Audit: Gruppen Fremde Inhalte und Cookies. Reine Funktionen ohne Netz.
Maßstäbe: MDN HTTP Observatory (Subresource Integrity, gemischte Inhalte, CORS, Cookies)."""
from html.parser import HTMLParser
from urllib.parse import urlparse


class _Sammler(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ress = []  # (tag, adresse, hat_integrity)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        adr = a.get("src") if tag in ("script", "img", "iframe", "source", "audio", "video", "embed") else a.get("href") if tag == "link" and "stylesheet" in (a.get("rel") or "") else None
        if adr:
            self.ress.append((tag, adr, "integrity" in a))


def _p(gruppe, pid, ergebnis, text):
    return (gruppe, pid, ergebnis, text)


def fremde_inhalte(html, host, kopf):
    s = _Sammler()
    try:
        s.feed(html or "")
    except Exception:  # fehlerhaftes HTML darf den Lauf nicht abbrechen
        return [_p("fremd", "html-lesbar", "nicht_geprueft", "Seite konnte nicht gelesen werden")]
    fremd = [(t, a, i) for t, a, i in s.ress if urlparse(a).netloc and urlparse(a).netloc.lower() != host.lower()]
    skripte = [x for x in fremd if x[0] == "script" or x[0] == "link"]
    erg = [_p("fremd", "gemischt", "nicht_bestanden" if any(a.lower().startswith("http://") for _t, a, _i in s.ress) else "bestanden", "keine Inhalte über http auf der https-Seite"),
           _p("fremd", "fremde-skripte", "bestanden" if not skripte else "nicht_bestanden", "keine fremden Skripte oder Stile" if not skripte else "%d fremde Skripte oder Stile eingebunden" % len(skripte))]
    if skripte:
        ohne = [x for x in skripte if not x[2]]
        erg.append(_p("fremd", "sri", "bestanden" if not ohne else "nicht_bestanden", "fremde Skripte mit Subresource Integrity" if not ohne else "%d fremde Skripte ohne Subresource Integrity" % len(ohne)))
    acao = (kopf or {}).get("access-control-allow-origin", "")
    erg.append(_p("fremd", "cors", "hinweis" if acao.strip() == "*" else "bestanden", "CORS nicht offen für alle (*)" if acao.strip() != "*" else "Access-Control-Allow-Origin ist * (offen für alle)"))
    return erg


def cookies(kopf):
    roh = (kopf or {}).get("set-cookie", "")
    liste = [c for c in roh.split("\n") if c.strip()]
    if not liste:
        return [_p("cookies", "keine", "nicht_zutreffend", "keine Cookies gesetzt")]
    erg = []
    for c in liste:
        teile = [t.strip().lower() for t in c.split(";")]
        name = c.split("=", 1)[0].strip()
        for pid, ok, text in (("secure", "secure" in teile, "Secure"), ("httponly", "httponly" in teile, "HttpOnly"),
                              ("samesite", any(t.startswith("samesite=") for t in teile), "SameSite")):
            erg.append(_p("cookies", "%s-%s" % (pid, name), "bestanden" if ok else "nicht_bestanden", "Cookie %s: %s" % (name, text)))
    return erg
