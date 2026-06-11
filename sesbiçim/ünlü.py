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

# Yazıda karşılığı olmayan ünlü bileşimleri tek tek tanımlanmaz: özellik
# uzayının tamamı hesaplamayla taranır. Bilinen bileşimlere IPA imi verilir,
# kalanlar ad havuzundan im alır. Bu harfler hem ara durak hem de Ön Dil
# harfi (çapa) olarak kullanılabilir.
_IPA_İMLERİ = {
    (1, 1, 0): "ʌ",  # orta arka düz
    (2, 0, 1): "œ",  # açık ön yuvarlak
    (2, 1, 1): "ɒ",  # açık arka yuvarlak
}
_AD_HAVUZU = ["ɘ", "ɵ", "ɞ", "ɐ"]

VARSAYIMSAL_ÜNLÜLER = {}
_yazılı_bileşimler = set(ÜNLÜLER.values())
_havuz_no = 0
for _yükseklik in (0, 1, 2):
    for _arkalık in (0, 1):
        for _yuvarlak in (0, 1):
            _b = (_yükseklik, _arkalık, _yuvarlak)
            if _b in _yazılı_bileşimler:
                continue
            _ad = _IPA_İMLERİ.get(_b)
            if _ad is None:
                _ad = _AD_HAVUZU[_havuz_no]
                _havuz_no += 1
            VARSAYIMSAL_ÜNLÜLER[_ad] = _b

TÜM_ÜNLÜLER = {**ÜNLÜLER, **VARSAYIMSAL_ÜNLÜLER}


def ünlü_komşu_mu(a, b):
    """İki ünlü arasında tek adımlık doğal bir ses kayması var mı?

    - Arkalık ve yuvarlaklık aynıyken yükseklik kayması (a > ı gibi) tek adımdır.
    - Yükseklik aynıyken arkalık YA DA yuvarlaklıktan yalnız biri değişirse tek adımdır.
    """
    ha, aa, ya = TÜM_ÜNLÜLER[a]
    hb, ab, yb = TÜM_ÜNLÜLER[b]
    if aa == ab and ya == yb and ha != hb:
        return True
    if ha == hb and (aa != ab) + (ya != yb) == 1:
        return True
    return False
