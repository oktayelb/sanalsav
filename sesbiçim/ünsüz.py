# -*- coding: utf-8 -*-
# ünsüzleri tek tek tanımlamak yerine ünsüz harflerin sahip olabildikleri özellikleri tanımlayıp,
# herhangi bir ünsüz harfi de bu özelliklere sahip/nasahip bir vektör olarak tanımlarsak her türlü
# yeni ünsüz sesin harfini burada tanımlamamız gerekmez, model kendisi bu özellikler üzerinden anlar.

# dudaksıllar, patlayıcılar, burunsullar gibi.

# Her ünsüz üç özellikten oluşur: (yer, biçim, ötümlülük)
#   yer    : boğumlanma bölgesi (kaba ölçek; komşu bölgeler arası geçiş tek adımdır)
#   biçim  : çıkış biçimi (lenisyon zincirlerine göre komşuluk tanımlıdır)
#   ötümlü : True/False (ötümlüleşme/ötümsüzleşme tek adımdır)

YERLER = ["dudaksıl", "dişsil", "damaksıl", "gırtlaksıl"]

BİÇİMLER = ["patlamalı", "yarıkapantılı", "sızıcı", "genizsil", "akıcı", "kayıcı"]

# Doğal dillerde sık görülen biçim geçişleri (lenisyon vb.); bunlar tek adım sayılır.
BİÇİM_KOMŞULUĞU = {
    frozenset(("patlamalı", "yarıkapantılı")),
    frozenset(("yarıkapantılı", "sızıcı")),
    frozenset(("patlamalı", "sızıcı")),
    frozenset(("sızıcı", "kayıcı")),
    frozenset(("kayıcı", "akıcı")),
    frozenset(("patlamalı", "genizsil")),
    frozenset(("genizsil", "akıcı")),
}

ÜNSÜZLER = {
    "p": ("dudaksıl", "patlamalı", False),
    "b": ("dudaksıl", "patlamalı", True),
    "m": ("dudaksıl", "genizsil", True),
    "w": ("dudaksıl", "kayıcı", True),
    "f": ("dudaksıl", "sızıcı", False),
    "v": ("dudaksıl", "sızıcı", True),
    "t": ("dişsil", "patlamalı", False),
    "d": ("dişsil", "patlamalı", True),
    "n": ("dişsil", "genizsil", True),
    "s": ("dişsil", "sızıcı", False),
    "z": ("dişsil", "sızıcı", True),
    "l": ("dişsil", "akıcı", True),
    "r": ("dişsil", "akıcı", True),
    "ç": ("damaksıl", "yarıkapantılı", False),
    "c": ("damaksıl", "yarıkapantılı", True),
    "ş": ("damaksıl", "sızıcı", False),
    "j": ("damaksıl", "sızıcı", True),
    "y": ("damaksıl", "kayıcı", True),
    "k": ("damaksıl", "patlamalı", False),
    "g": ("damaksıl", "patlamalı", True),
    "ğ": ("damaksıl", "kayıcı", True),
    "q": ("damaksıl", "patlamalı", False),
    "x": ("damaksıl", "sızıcı", False),
    "h": ("gırtlaksıl", "sızıcı", False),
}


def ünsüz_komşu_mu(a, b):
    """İki ünsüz arasında tek adımlık doğal bir ses değişimi var mı?

    Özellikleri özdeş harf çiftleri (k~q, l~r gibi) ile yalnız bir özelliği
    bir basamak değişen çiftler (k~g, p~f, t~k gibi) komşu sayılır.
    """
    ya, ba, sa = ÜNSÜZLER[a]
    yb, bb, sb = ÜNSÜZLER[b]
    yf = abs(YERLER.index(ya) - YERLER.index(yb))
    bf = 0 if ba == bb else (1 if frozenset((ba, bb)) in BİÇİM_KOMŞULUĞU else 2)
    sf = 0 if sa == sb else 1
    değişen = (yf > 0) + (bf > 0) + (sf > 0)
    if değişen == 0:
        return True
    return değişen == 1 and yf <= 1 and bf <= 1
