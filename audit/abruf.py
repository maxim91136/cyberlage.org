"""Audit: Netzabruf mit der Standardbibliothek. Höfliche, wenige Anfragen mit klarem User-Agent. Nur für eigene Domains."""
import http.client
import json
import socket
import ssl

UA = "cyberlage-audit/0.1 (+https://cyberlage.org/hinweise)"
ZEIT = 15
MAX = 2_000_000


def hole(host, pfad="/", https=True):
    """Gibt (status, kopfzeilen_klein, text, ort) zurück, folgt keiner Weiterleitung. Fehler: (None, {}, "", None)."""
    try:
        if https:
            k = http.client.HTTPSConnection(host, timeout=ZEIT, context=ssl.create_default_context())
        else:
            k = http.client.HTTPConnection(host, timeout=ZEIT)
        k.request("GET", pfad, headers={"User-Agent": UA, "Accept": "*/*"})
        r = k.getresponse()
        kopf = {n.lower(): v for n, v in r.getheaders()}
        if r.msg.get_all("Set-Cookie"):
            kopf["set-cookie"] = "\n".join(r.msg.get_all("Set-Cookie"))
        text = r.read(MAX).decode("utf-8", errors="replace")
        k.close()
        return r.status, kopf, text, kopf.get("location")
    except (OSError, http.client.HTTPException, ssl.SSLError):
        return None, {}, "", None


def zertifikat(host):
    """(cert, ok): geprüfte Verbindung. Bei Prüfungsfehler (None, False)."""
    try:
        with socket.create_connection((host, 443), timeout=ZEIT) as s:
            with ssl.create_default_context().wrap_socket(s, server_hostname=host) as t:
                return t.getpeercert(), True
    except (OSError, ssl.SSLError):
        return None, False


def versionen(host):
    """Prüft einzeln, welche TLS-Versionen der Server annimmt. 'unklar', wenn die lokale OpenSSL-Version die Version nicht anbietet."""
    erg = {}
    for name, v in (("TLSv1", ssl.TLSVersion.TLSv1), ("TLSv1.1", ssl.TLSVersion.TLSv1_1), ("TLSv1.2", ssl.TLSVersion.TLSv1_2), ("TLSv1.3", ssl.TLSVersion.TLSv1_3)):
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.minimum_version = ctx.maximum_version = v
            try:
                ctx.set_ciphers("ALL:@SECLEVEL=0")
            except ssl.SSLError:
                pass
            with socket.create_connection((host, 443), timeout=ZEIT) as s:
                with ctx.wrap_socket(s, server_hostname=host):
                    erg[name] = "ja"
        except ssl.SSLError as ex:
            erg[name] = "unklar" if "NO_PROTOCOLS_AVAILABLE" in str(ex).upper() else "nein"  # lokal nicht anbietbar, sonst vom Server abgelehnt
        except (ValueError, NotImplementedError):
            erg[name] = "unklar"
        except OSError:
            erg[name] = "unklar"
    return erg


def doh(name, typ):
    """DNS-over-HTTPS (Cloudflare, JSON). Gibt (antworten_als_text_liste, ad_merker) zurück, bei Fehler (None, False)."""
    try:
        k = http.client.HTTPSConnection("cloudflare-dns.com", timeout=ZEIT, context=ssl.create_default_context())
        k.request("GET", "/dns-query?name=%s&type=%s" % (name, typ), headers={"Accept": "application/dns-json", "User-Agent": UA})
        r = k.getresponse()
        d = json.loads(r.read(200_000).decode("utf-8", errors="replace"))
        k.close()
        if r.status != 200 or d.get("Status") not in (0, 3):  # 0 = ok, 3 = Name existiert nicht
            return None, False
        nummer = {"A": 1, "MX": 15, "TXT": 16, "DS": 43, "CAA": 257}[typ]
        return [a.get("data", "") for a in d.get("Answer", []) if a.get("type") == nummer], bool(d.get("AD"))
    except (OSError, ValueError, http.client.HTTPException, ssl.SSLError):
        return None, False
