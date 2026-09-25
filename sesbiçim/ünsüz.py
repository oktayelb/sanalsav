YERLER = [
    "dudaksıl",
    "dişdudaksıl",
    "dişsil",
    "öndamaksıl",
    "artdamaksıl",
    "küçükdilsil",
    "gırtlaksıl",
]

BİÇİMLER = [
    "patlamalı",
    "yarıkapantılı",
    "sızıcı",
    "genizsil",
    "yansıl",
    "çarpmalı",
    "kayıcı",
]

BİÇİM_KOMŞULUĞU = {
    frozenset(("patlamalı", "yarıkapantılı")),
    frozenset(("yarıkapantılı", "sızıcı")),
    frozenset(("patlamalı", "sızıcı")),
    frozenset(("patlamalı", "genizsil")),
    frozenset(("patlamalı", "çarpmalı")),
    frozenset(("sızıcı", "kayıcı")),
    frozenset(("sızıcı", "yansıl")),
    frozenset(("genizsil", "yansıl")),
    frozenset(("genizsil", "çarpmalı")),
    frozenset(("yansıl", "çarpmalı")),
    frozenset(("kayıcı", "yansıl")),
    frozenset(("kayıcı", "çarpmalı")),
}

ÜNSÜZLER = {
    "p": ("dudaksıl", "patlamalı", False),
    "b": ("dudaksıl", "patlamalı", True),
    "m": ("dudaksıl", "genizsil", True),
    "w": ("dudaksıl", "kayıcı", True),
    "f": ("dişdudaksıl", "sızıcı", False),
    "v": ("dişdudaksıl", "sızıcı", True),
    "t": ("dişsil", "patlamalı", False),
    "d": ("dişsil", "patlamalı", True),
    "n": ("dişsil", "genizsil", True),
    "ţ": ("dişsil", "yarıkapantılı", False),
    "s": ("dişsil", "sızıcı", False),
    "z": ("dişsil", "sızıcı", True),
    "l": ("dişsil", "yansıl", True),
    "r": ("dişsil", "çarpmalı", True),
    "ç": ("öndamaksıl", "yarıkapantılı", False),
    "c": ("öndamaksıl", "yarıkapantılı", True),
    "ş": ("öndamaksıl", "sızıcı", False),
    "j": ("öndamaksıl", "sızıcı", True),
    "y": ("öndamaksıl", "kayıcı", True),
    "k": ("artdamaksıl", "patlamalı", False),
    "g": ("artdamaksıl", "patlamalı", True),
    "x": ("artdamaksıl", "sızıcı", False),
    "ğ": ("artdamaksıl", "sızıcı", True),
    "ñ": ("artdamaksıl", "genizsil", True),
    "q": ("küçükdilsil", "patlamalı", False),
    "h": ("gırtlaksıl", "sızıcı", False),
}


def ünsüz_komşu_mu(a, b):
    ya, ba, sa = TÜM_ÜNSÜZLER[a]
    yb, bb, sb = TÜM_ÜNSÜZLER[b]
    yf = abs(YERLER.index(ya) - YERLER.index(yb))
    bf = 0 if ba == bb else (1 if frozenset((ba, bb)) in BİÇİM_KOMŞULUĞU else 2)
    sf = 0 if sa == sb else 1
    değişen = (yf > 0) + (bf > 0) + (sf > 0)
    if değişen == 0:
        return True
    return değişen == 1 and yf <= 1 and bf <= 1


def _olanaksız_mı(yer, biçim, ötümlü):
    if yer == "gırtlaksıl":
        if biçim not in ("patlamalı", "sızıcı"):
            return True
        if biçim == "patlamalı" and ötümlü:
            return True
    if biçim == "yansıl" and yer in ("dudaksıl", "dişdudaksıl", "küçükdilsil"):
        return True
    if biçim == "çarpmalı" and yer == "artdamaksıl":
        return True
    if biçim == "kayıcı" and yer == "küçükdilsil":
        return True
    return False


_IPA_İMLERİ = {
    ("dudaksıl", "sızıcı", False): "ɸ",
    ("dudaksıl", "sızıcı", True): "β",
    ("dudaksıl", "çarpmalı", True): "ʙ",
    ("dudaksıl", "kayıcı", False): "ʍ",
    ("dişdudaksıl", "genizsil", True): "ɱ",
    ("dişdudaksıl", "çarpmalı", True): "ⱱ",
    ("dişdudaksıl", "kayıcı", True): "ʋ",
    ("dişsil", "yarıkapantılı", False): "ʦ",
    ("dişsil", "yarıkapantılı", True): "ʣ",
    ("dişsil", "yansıl", False): "ɬ",
    ("dişsil", "kayıcı", True): "ɹ",
    ("öndamaksıl", "patlamalı", True): "ɟ",
    ("öndamaksıl", "genizsil", True): "ɲ",
    ("öndamaksıl", "yansıl", True): "ʎ",
    ("artdamaksıl", "genizsil", True): "ŋ",
    ("artdamaksıl", "yansıl", True): "ʟ",
    ("artdamaksıl", "kayıcı", True): "ɰ",
    ("küçükdilsil", "patlamalı", True): "ɢ",
    ("küçükdilsil", "genizsil", True): "ɴ",
    ("küçükdilsil", "sızıcı", False): "χ",
    ("küçükdilsil", "sızıcı", True): "ʁ",
    ("küçükdilsil", "çarpmalı", True): "ʀ",
    ("gırtlaksıl", "patlamalı", False): "ʔ",
    ("gırtlaksıl", "sızıcı", True): "ɦ",
}
_AD_HAVUZU = ["φ", "ψ", "θ", "δ", "γ", "λ", "μ", "ν", "π", "σ", "ζ", "ω"]
_ÖTÜMSÜZ_İMİ = "̥"
_ÖTÜMLÜ_İMİ = "̬"

VARSAYIMSAL_ÜNSÜZLER = {}
_yazılı_bileşimler = set(ÜNSÜZLER.values())
_havuz_no = 0


def _bileşimin_adı(bileşim):
    ad = _IPA_İMLERİ.get(bileşim)
    if ad is not None:
        return ad
    for _kaynak in (ÜNSÜZLER, VARSAYIMSAL_ÜNSÜZLER):
        for _a, _v in _kaynak.items():
            if _v == bileşim:
                return _a
    return None


for _yer in YERLER:
    for _biçim in BİÇİMLER:
        for _ötümlü in (False, True):
            _b = (_yer, _biçim, _ötümlü)
            if _b in _yazılı_bileşimler or _olanaksız_mı(*_b):
                continue
            _ad = _IPA_İMLERİ.get(_b)
            if _ad is None:
                _eş_ad = _bileşimin_adı((_yer, _biçim, not _ötümlü))
                if _eş_ad is not None and len(_eş_ad) == 1:
                    _ad = _eş_ad + (_ÖTÜMLÜ_İMİ if _ötümlü else _ÖTÜMSÜZ_İMİ)
                else:
                    if _havuz_no >= len(_AD_HAVUZU):
                        raise RuntimeError("sanal ünsüz ad havuzu tükendi")
                    _ad = _AD_HAVUZU[_havuz_no]
                    _havuz_no += 1
            VARSAYIMSAL_ÜNSÜZLER[_ad] = _b

TÜM_ÜNSÜZLER = {**ÜNSÜZLER, **VARSAYIMSAL_ÜNSÜZLER}

