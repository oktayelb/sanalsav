# -*- coding: utf-8 -*-
# ünsüzleri tek tek tanımlamak yerine ünsüz harflerin sahip olabildikleri özellikleri tanımlayıp,
# herhangi bir ünsüz harfi de bu özelliklere sahip/nasahip bir vektör olarak tanımlarsak her türlü
# yeni ünsüz sesin harfini burada tanımlamamız gerekmez, model kendisi bu özellikler üzerinden anlar.

# dudaksıllar, patlayıcılar, burunsullar gibi.

# Her ünsüz üç özellikten oluşur: (yer, biçim, ötümlülük)
#   yer    : boğumlanma bölgesi (IPA sırasına uygun 7'li ölçek; komşu
#            bölgeler arası geçiş tek adımdır)
#   biçim  : çıkış biçimi (doğal geçişlere göre komşuluk tanımlıdır;
#            yansıl (l) ile çarpmalı/titrek (r) ayrı sınıflardır)
#   ötümlü : True/False (ötümlüleşme/ötümsüzleşme tek adımdır)

YERLER = [
    "dudaksıl",      # çift dudak: p, b, m, w
    "dişdudaksıl",   # diş-dudak: f, v
    "dişsil",        # diş / dişeti: t, d, n, s, z, l, r
    "öndamaksıl",    # dişeti-damak / öndamak: ç, c, ş, j, y
    "artdamaksıl",   # artdamak: k, g, x, ğ
    "küçükdilsil",   # küçükdil: q
    "gırtlaksıl",    # gırtlak: h
]

BİÇİMLER = [
    "patlamalı",
    "yarıkapantılı",
    "sızıcı",
    "genizsil",
    "yansıl",      # yan akıcı (lateral): l
    "çarpmalı",    # çarpmalı/titrek (rhotic): r
    "kayıcı",
]

# Doğal dillerde sık görülen biçim geçişleri; bunlar tek adım sayılır.
# l ~ r artık sıfır değil tek adımdır (yansıl ~ çarpmalı).
BİÇİM_KOMŞULUĞU = {
    frozenset(("patlamalı", "yarıkapantılı")),
    frozenset(("yarıkapantılı", "sızıcı")),
    frozenset(("patlamalı", "sızıcı")),
    frozenset(("patlamalı", "genizsil")),
    frozenset(("patlamalı", "çarpmalı")),  # çarpmalılaşma (t -> ɾ)
    frozenset(("sızıcı", "kayıcı")),
    frozenset(("sızıcı", "yansıl")),       # ɬ köprüsü
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
    "ğ": ("artdamaksıl", "sızıcı", True),  # tarihsel /ɣ/: kayıcı değil sızıcı
    "q": ("küçükdilsil", "patlamalı", False),
    "h": ("gırtlaksıl", "sızıcı", False),
}


def ünsüz_komşu_mu(a, b):
    """İki ünsüz arasında tek adımlık doğal bir ses değişimi var mı?

    Yalnız bir özelliği, yalnız bir basamak değişen çiftler komşu sayılır
    (yer ölçekte ±1, biçim komşuluk çizelgesinden, ötümlülük serbest).
    """
    ya, ba, sa = TÜM_ÜNSÜZLER[a]
    yb, bb, sb = TÜM_ÜNSÜZLER[b]
    yf = abs(YERLER.index(ya) - YERLER.index(yb))
    bf = 0 if ba == bb else (1 if frozenset((ba, bb)) in BİÇİM_KOMŞULUĞU else 2)
    sf = 0 if sa == sb else 1
    değişen = (yf > 0) + (bf > 0) + (sf > 0)
    if değişen == 0:
        return True
    return değişen == 1 and yf <= 1 and bf <= 1


# Yazıda karşılığı olmayan ünsüz bileşimleri tek tek tanımlanmaz: özellik
# uzayının tamamı hesaplamayla taranır (insan ses aygıtının üretemeyeceği
# bileşimler dışarıda bırakılır). Bilinen bileşimler IPA imini alır,
# kalanlar ad havuzundan im alır. Bu harfler hem ara durak hem de Ön Dil
# harfi (çapa) olarak kullanılabilir (ör. k > ʔ > ∅, k > g > ŋ > n).


def _olanaksız_mı(yer, biçim, ötümlü):
    """Gerçekçilik kuralı: söylenemeyen bileşim, harf olamaz."""
    if yer == "gırtlaksıl":
        if biçim not in ("patlamalı", "sızıcı"):
            return True  # gırtlakta geniz/yan/çarpma/kayma olmaz
        if biçim == "patlamalı" and ötümlü:
            return True  # kapalı gırtlak titreşemez (ötümlü hamza yok)
    if biçim == "yansıl" and yer in ("dudaksıl", "dişdudaksıl", "küçükdilsil"):
        return True  # dudakla ve küçükdille yan akıcı yapılmaz
    if biçim == "çarpmalı" and yer == "artdamaksıl":
        return True  # dil sırtı çarpamaz/titreyemez
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
# Adlandırma sırası: (1) bilinen IPA imi, (2) ötümlülük eşinin adından
# türetme (m -> m̥ "ötümsüz m", φ -> φ̬ "ötümlü φ"), (3) soyut ad havuzu.
# Havuz imleri bilerek IPA-dışı (Yunan) seçilmiştir: yanlış ses çağrışımı
# yapmasınlar; ne oldukları yalnız özellik vektörüyle tanımlıdır.
_AD_HAVUZU = ["φ", "ψ", "θ", "δ", "γ", "λ", "μ", "ν", "π", "σ", "ζ", "ω"]
_ÖTÜMSÜZ_İMİ = "̥"  # birleşik alt halka (X̥)
_ÖTÜMLÜ_İMİ = "̬"   # birleşik alt çengel (X̬)

VARSAYIMSAL_ÜNSÜZLER = {}
_yazılı_bileşimler = set(ÜNSÜZLER.values())
_havuz_no = 0


def _bileşimin_adı(bileşim):
    """Bileşimin yazılı, IPA ya da üretilmiş adını arar."""
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
