# -*- coding: utf-8 -*-
# ünlüleri tek tek tanımlamak yerine ünlü harflerin sahip olabildikleri özellikleri tanımlayıp,
# herhangi bir ünlü harfi de bu özelliklere sahip/nasahip bir vektör olarak tanımlarsak her türlü
# yeni ünlü sesin harfini burada tanımlamamız gerekmez, model kendisi bu özellikler üzerinden anlar.

# kalın, ince , düz , yuvarlak gibi.

# Her ünlü üç boyutlu bir özellik vektörüdür:
#   (yükseklik, arkalık, yuvarlaklık)
#   yükseklik : 0 kapalı, 1 orta, 2 açık
#   arkalık   : 0 ön (ince), 1 arka (kalın)
#   yuvarlak  : 0 düz, 1 yuvarlak
#
# Yazılış esaslı çalışıldığı için harfe en tipik ses değeri atanır.

ÜNLÜLER = {
    "i": (0, 0, 0),  # kapalı ön düz
    "ü": (0, 0, 1),  # kapalı ön yuvarlak
    "ı": (0, 1, 0),  # kapalı arka düz
    "u": (0, 1, 1),  # kapalı arka yuvarlak
    "e": (1, 0, 0),  # orta ön düz
    "ö": (1, 0, 1),  # orta ön yuvarlak
    "o": (1, 1, 1),  # orta arka yuvarlak
    "a": (2, 1, 0),  # açık arka düz
}


def ünlü_komşu_mu(a, b):
    """İki ünlü arasında tek adımlık doğal bir ses kayması var mı?

    - Arkalık ve yuvarlaklık aynıyken yükseklik kayması (a > ı gibi) tek adımdır.
    - Yükseklik aynıyken arkalık YA DA yuvarlaklıktan yalnız biri değişirse tek adımdır.
    """
    ha, aa, ya = ÜNLÜLER[a]
    hb, ab, yb = ÜNLÜLER[b]
    if aa == ab and ya == yb and ha != hb:
        return True
    if ha == hb and (aa != ab) + (ya != yb) == 1:
        return True
    return False
