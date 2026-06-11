# -*- coding: utf-8 -*-
# ünlüleri tek tek tanımlamak yerine ünlü harflerin sahip olabildikleri özellikleri tanımlayıp,
# herhangi bir ünlü harfi de bu özelliklere sahip/nasahip bir vektör olarak tanımlarsak her türlü
# yeni ünlü sesin harfini burada tanımlamamız gerekmez, model kendisi bu özellikler üzerinden anlar.

# kalın, ince , düz , yuvarlak gibi.

# Her ünlü dört boyutlu bir özellik vektörüdür:
#   (yükseklik, arkalık, yuvarlaklık, uzunluk)
#   yükseklik : 0 kapalı, 1 orta, 2 açık
#   arkalık   : 0 ön (ince), 1 arka (kalın)
#   yuvarlak  : 0 düz, 1 yuvarlak
#   uzunluk   : 0 kısa, 1 uzun
#
# Yazılış esaslı çalışıldığı için harfe en tipik ses değeri atanır. Türk
# yazılarında uzunluk imlenmediğinden bütün yazılı ünlüler kısadır; uzun
# ünlüler sanal harftir (im: harf + "ː") ve başka yazıların ikiz/uzun
# ünlülerini ve büzülmeleri (ağa > ā, uvu > ū) temsil etmek için uzayda
# hazır durur.

ÜNLÜLER = {
    "i": (0, 0, 0, 0),  # kapalı ön düz
    "ü": (0, 0, 1, 0),  # kapalı ön yuvarlak
    "ı": (0, 1, 0, 0),  # kapalı arka düz
    "u": (0, 1, 1, 0),  # kapalı arka yuvarlak
    "e": (1, 0, 0, 0),  # orta ön düz
    "ə": (2, 0, 0, 0),  # açık ön düz (Azerbaycan yazısı)
    "ö": (1, 0, 1, 0),  # orta ön yuvarlak
    "o": (1, 1, 1, 0),  # orta arka yuvarlak
    "a": (2, 1, 0, 0),  # açık arka düz
}

UZUNLUK_İMİ = "ː"

# Kısa sanal ünlüler: 3×2×2'lik kısa uzayın ÜNLÜLER'de dolmayan 3 boşluğu.
_KISA_SANALLAR = {
    "ʌ": (1, 1, 0, 0),  # orta arka düz
    "œ": (2, 0, 1, 0),  # açık ön yuvarlak
    "ɒ": (2, 1, 1, 0),  # açık arka yuvarlak
}

# Sanal ünlüler: 3 kısa boşluk + kısa uzayın tamamının uzun eşleri (12 harf).
# Hepsi hem ara durak hem Ön Dil harfi (çapa) olarak kullanılabilir.
VARSAYIMSAL_ÜNLÜLER = dict(_KISA_SANALLAR)
for _ad, (_yük, _ark, _yuv, _) in {**ÜNLÜLER, **_KISA_SANALLAR}.items():
    VARSAYIMSAL_ÜNLÜLER[_ad + UZUNLUK_İMİ] = (_yük, _ark, _yuv, 1)

TÜM_ÜNLÜLER = {**ÜNLÜLER, **VARSAYIMSAL_ÜNLÜLER}
UZUN_ÜNLÜLER = {_a for _a, _ö in TÜM_ÜNLÜLER.items() if _ö[3] == 1}

# DOĞUMLAR: tek harften çok harf türetme (README'deki "grupça değişim"in
# ilk yarısı) şimdilik yalnız uzun ünlülere tanınan bir hamledir. Her uzun
# ünlü, kısa eşinin çevresinde iyi bilinen büzülme/açılma gövdelerini
# doğurabilir:
#   ikiz yazım     : aː > aa            (başka yazıların uzun ünlü imi)
#   büzülme gövdesi: aː > ağa / aha,  uː > uvu / uwu / ubu,  iː > iyi
#   çift ünlüleşme : aː > ay  (söz sonunda; -aa > -ay tipi)
# Gövde ünsüzü ünlünün niteliğine bağlıdır: y/ğ/h her ünlüyle, v/w/b yalnız
# yuvarlak ünlülerle. Eşleme {harf dizisi -> doğuran uzun ünlü} yönündedir.
DOĞUMLAR = {}
for _ad, (_yük, _ark, _yuv, _) in ÜNLÜLER.items():
    _uzun = _ad + UZUNLUK_İMİ
    _gövde_ünsüzleri = ["y", "ğ", "h"] + (["v", "w", "b"] if _yuv else [])
    DOĞUMLAR[(_ad, _ad)] = _uzun
    for _g in _gövde_ünsüzleri:
        DOĞUMLAR[(_ad, _g, _ad)] = _uzun
        DOĞUMLAR[(_ad, _g)] = _uzun


def ünlü_komşu_mu(a, b):
    """İki ünlü arasında tek adımlık doğal bir ses kayması var mı?

    - Öbür özellikler aynıyken yüksekliğin BİR kademe kayması (e > i gibi)
      tek adımdır; kapalı > açık zıplaması (i > ə) iki adımdır, komşu sayılmaz.
    - Yükseklik ve uzunluk aynıyken arkalık YA DA yuvarlaklıktan yalnız biri
      değişirse tek adımdır.
    - Nitelik tamamen aynıyken uzama/kısalma (a > aː) tek adımdır.
    """
    ha, aa, ya, ua = TÜM_ÜNLÜLER[a]
    hb, ab, yb, ub = TÜM_ÜNLÜLER[b]
    if aa == ab and ya == yb and ua == ub and abs(ha - hb) == 1:
        return True
    if ha == hb and ua == ub and (aa != ab) + (ya != yb) == 1:
        return True
    if (ha, aa, ya) == (hb, ab, yb) and ua != ub:
        return True
    return False
