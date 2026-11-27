"""Erzeugt site/og.png (Vorschaubild für Links) im Matrix-Stil neu: dezenter Zeichenregen hinter dem bisherigen Bild.

Rein Optik, keine Zahlen im Bild (ein Pegelwert im Bild wäre morgen veraltet). Aufruf: python pipeline/og_matrix.py [Quelle.png] [Ziel.png]
Der Regen liegt nur dort, wo das Ausgangsbild leer ist, Logo, Titel und Rahmen bleiben pixelgenau. Zufall ist fest (Startwert), das Ergebnis ist wiederholbar.
Schrift: Noto Sans CJK (Katakana), nur zum Erzeugen des Bildes nötig, nicht für die Seite."""
import random
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

GL = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉ0123456789"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"


def erzeuge(quelle, ziel):
    basis = Image.open(quelle).convert("RGB")
    b, h = basis.size
    rnd = random.Random(2611)
    regen = Image.new("RGB", (b, h), (0, 0, 0))
    d = ImageDraw.Draw(regen)
    schrift = ImageFont.truetype(FONT, 17)
    zeile, spalte = 20, 22
    for x in range(8, b, spalte):
        laenge = rnd.randint(6, 22)
        kopf = rnd.randint(-5, h // zeile + 4)
        for i in range(laenge):
            y = (kopf - i) * zeile
            if not -zeile < y < h:
                continue
            st = max(0.0, 1 - i / laenge)
            farbe = (255, 255, 255) if i == 0 else (int(40 * st), int(235 * st), int(150 * st))
            d.text((x, y), rnd.choice(GL), font=schrift, fill=farbe)
    regen = regen.filter(ImageFilter.GaussianBlur(0.4))
    # Der Regen wird zu den Rändern hin kräftiger und in der Mitte leiser, damit Titel und Pegelrahmen lesbar bleiben.
    maske = Image.new("L", (b, h), 0)
    md = ImageDraw.Draw(maske)
    md.ellipse((b * 0.12, h * 0.1, b * 0.88, h * 0.9), fill=255)
    maske = maske.filter(ImageFilter.GaussianBlur(90))
    kraft = Image.eval(maske, lambda v: int(95 + (255 - v) * 0.30))
    regen = Image.composite(regen, Image.new("RGB", (b, h), (0, 0, 0)), Image.new("L", (b, h), 255))
    regen = ImageChops.multiply(regen, Image.merge("RGB", (kraft, kraft, kraft)))
    # Nur dort einblenden, wo das Ausgangsbild leer ist (Hintergrundhelligkeit), Gitterlinien dürfen darunter bleiben.
    hell = basis.convert("L").point(lambda v: 255 if v > 30 else 0).filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(2))
    frei = ImageChops.invert(hell)
    ergebnis = Image.composite(ImageChops.add(basis, regen), basis, frei)
    ergebnis.save(ziel, optimize=True)
    return ergebnis.size


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "site/og.png"
    z = sys.argv[2] if len(sys.argv) > 2 else q
    print(erzeuge(q, z))
