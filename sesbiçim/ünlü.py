ÜNLÜLER = {
    "i": (0, 0, 0, 0),
    "ü": (0, 0, 1, 0),
    "ı": (0, 1, 0, 0),
    "u": (0, 1, 1, 0),
    "e": (1, 0, 0, 0),
    "ə": (2, 0, 0, 0),
    "ö": (1, 0, 1, 0),
    "o": (1, 1, 1, 0),
    "a": (2, 1, 0, 0),
}

UZUNLUK_İMİ = "ː"

_KISA_SANALLAR = {
    "ʌ": (1, 1, 0, 0),
    "œ": (2, 0, 1, 0),
    "ɒ": (2, 1, 1, 0),
}

VARSAYIMSAL_ÜNLÜLER = dict(_KISA_SANALLAR)
for _ad, (_yük, _ark, _yuv, _) in {**ÜNLÜLER, **_KISA_SANALLAR}.items():
    VARSAYIMSAL_ÜNLÜLER[_ad + UZUNLUK_İMİ] = (_yük, _ark, _yuv, 1)

TÜM_ÜNLÜLER = {**ÜNLÜLER, **VARSAYIMSAL_ÜNLÜLER}

DOĞUMLAR = {}
for _ad, (_yük, _ark, _yuv, _) in ÜNLÜLER.items():
    _uzun = _ad + UZUNLUK_İMİ
    _gövde_ünsüzleri = ["y", "ğ", "h"] + (["v", "w", "b"] if _yuv else [])
    DOĞUMLAR[(_ad, _ad)] = _uzun
    for _g in _gövde_ünsüzleri:
        DOĞUMLAR[(_ad, _g, _ad)] = _uzun
        DOĞUMLAR[(_ad, _g)] = _uzun


def ünlü_komşu_mu(a, b):
    ha, aa, ya, ua = TÜM_ÜNLÜLER[a]
    hb, ab, yb, ub = TÜM_ÜNLÜLER[b]
    if aa == ab and ya == yb and ua == ub and abs(ha - hb) == 1:
        return True
    if ha == hb and ua == ub and (aa != ab) + (ya != yb) == 1:
        return True
    if (ha, aa, ya) == (hb, ab, yb) and ua != ub:
        return True
    return False

