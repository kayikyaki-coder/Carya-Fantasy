#!/usr/bin/env python3
"""Etiketli Carya haritasina imparatorluk kasabalarini isler.

Kaynak: harita/carya_haritasi_etiketli_eski.jpg (kasabasiz orijinal, yedek; degistirilmez)
Cikti:  harita/carya_haritasi_etiketli.jpg

Kasabalar, metin/imparatorluk/kasabalar.md'deki anlatimlara gore bagli olduklari
buyuksehrin yakinina yerlestirildi. Sehirlerden ayirt edilsinler diye kucuk ici bos
daire ve parsomen kenarli kucuk italik yazi ile cizilir. Konum degistirmek icin
KASABALAR listesini duzenleyip betigi yeniden calistirin.

Gerekli: Pillow.
"""
import os

from PIL import Image, ImageDraw, ImageFont

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KAYNAK = os.path.join(KOK, "harita", "carya_haritasi_etiketli_eski.jpg")
CIKTI = os.path.join(KOK, "harita", "carya_haritasi_etiketli.jpg")
FONT = "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"

KARA = (237, 222, 196)      # haritadaki kara rengi
KIYI = (52, 62, 72)         # kiyi cizgisi
YAZI = (58, 40, 24)         # kasaba adi
HALE = (244, 234, 214)      # yazinin cevresindeki parsomen kenari

# (ad, x, y, yazi yonu, gerekce)
# Sehir noktalari (1414x2000): Florentina 252,663 / Greenhall 455,663 / Venture 329,741 /
# Arcan's Gate 343,846 / Aquamere 372,974 / Serenquill 440,484
KASABALAR = [
    # Florentina
    ("Kayıtçılar", 318, 598, "l", "başkente çok yakın memur kasabası"),
    ("Son Durak", 392, 515, "r", "kuzeyden, Serenquill yolundan gelirken Florentina'dan önceki son durak"),
    ("Karnabahar", 366, 568, "r", "başkentin kuzeydoğusundaki geniş tarım arazileri"),
    ("Zevk Adası", 196, 706, "l", "Florentina açıklarında ada"),
    # Serenquill
    ("Son Kale", 412, 392, "r", "Serenquill'in kuzeye en yakın garnizonu, kuzey krallığına doğru"),
    ("Tavşanlı", 545, 465, "r", "bataklık kenarında kırsal kasaba"),
    ("Mürekkepçi", 505, 528, "r", "nehir ve bataklık kollarında mürekkep balıkçılığı"),
    # Venture
    ("Tüccar Yolu", 440, 742, "r", "Venture'a kara yoluyla gelen kervanların son durağı, iç bölgede"),
    ("Mavi Koru", 578, 690, "r", "göl kıyısı ile orman hattının kesişimi (Greenhall ormanlarına bakan göl)"),
    ("Kara Liman", 314, 778, "l", "Venture'ın güneyinde kıyıda liman"),
    ("Kuştepe", 560, 790, "r", "iç bölgede yüksek yamaç ve maden damarları"),
    # Arcan's Gate
    ("Mühürpazar", 432, 822, "r", "şehrin hemen yanında büyülü eşya pazarı"),
    ("Yeşilcam", 452, 882, "r", "şehrin doğusundaki seralar ve tarlalar"),
    # Aquamere
    ("Berevin", 398, 1046, "r", "Aquamere'in güney hattında, Arcan's Gate'e de erzak taşıyan tarım kasabası"),
]

# Zevk Adasi icin kucuk bir ada (haritada adasi yok)
ADA = [(178, 700), (186, 692), (199, 690), (211, 695), (216, 704), (212, 714), (200, 720), (186, 718), (179, 710)]


def main():
    im = Image.open(KAYNAK).convert("RGB")
    d = ImageDraw.Draw(im)
    d.polygon(ADA, fill=KARA)
    d.line(ADA + [ADA[0]], fill=KIYI, width=4, joint="curve")

    font = ImageFont.truetype(FONT, 17)
    r = 6
    for ad, x, y, yon, _ in KASABALAR:
        d.ellipse((x - r, y - r, x + r, y + r), fill=HALE, outline=(20, 20, 20), width=3)
        w = d.textlength(ad, font=font)
        tx = x + r + 6 if yon == "r" else x - r - 6 - w
        d.text((tx, y), ad, font=font, fill=YAZI, anchor="lm", stroke_width=3, stroke_fill=HALE)
    im.save(CIKTI, quality=90, optimize=True)
    print(f"{len(KASABALAR)} kasaba islendi -> {os.path.relpath(CIKTI, KOK)}")


if __name__ == "__main__":
    main()
