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
    "ə": (2, 0, 0),  # açık ön düz (Azerbaycan yazısı)
    "ö": (1, 0, 1),  # orta ön yuvarlak
    "o": (1, 1, 1),  # orta arka yuvarlak
    "a": (2, 1, 0),  # açık arka düz
}

# Yazıda karşılığı olmayan ünlü bileşimleri: 3×2×2 = 12 bileşimlik uzayın
# ÜNLÜLER'de dolmayan 3 boşluğu. Uzay tamamen kapalı olduğundan ek bir ad
# havuzuna gerek yoktur. Bu harfler hem ara durak hem de Ön Dil harfi
# (çapa) olarak kullanılabilir.
VARSAYIMSAL_ÜNLÜLER = {
    "ʌ": (1, 1, 0),  # orta arka düz
    "œ": (2, 0, 1),  # açık ön yuvarlak
    "ɒ": (2, 1, 1),  # açık arka yuvarlak
}

TÜM_ÜNLÜLER = {**ÜNLÜLER, **VARSAYIMSAL_ÜNLÜLER}


def ünlü_komşu_mu(a, b):
    """İki ünlü arasında tek adımlık doğal bir ses kayması var mı?

    - Arkalık ve yuvarlaklık aynıyken yüksekliğin BİR kademe kayması (e > i gibi)
      tek adımdır; kapalı > açık zıplaması (i > ə) iki adımdır, komşu sayılmaz.
    - Yükseklik aynıyken arkalık YA DA yuvarlaklıktan yalnız biri değişirse tek adımdır.
    """
    ha, aa, ya = TÜM_ÜNLÜLER[a]
    hb, ab, yb = TÜM_ÜNLÜLER[b]
    if aa == ab and ya == yb and abs(ha - hb) == 1:
        return True
    if ha == hb and (aa != ab) + (ya != yb) == 1:
        return True
    return False
