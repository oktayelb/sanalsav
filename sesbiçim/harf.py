from collections import deque

from .ünlü import DOĞUMLAR, ÜNLÜLER, TÜM_ÜNLÜLER, ünlü_komşu_mu
from .ünsüz import (
    BİÇİM_KOMŞULUĞU, YERLER, ÜNSÜZLER, TÜM_ÜNSÜZLER, ünsüz_komşu_mu,
)

BOŞ = "0"

_ALT_RAKAMLAR = "₀₁₂₃₄₅₆₇₈₉"


def alt_yazı(n):
    return "".join(_ALT_RAKAMLAR[int(c)] for c in str(n))


def taban(token):
    s = "".join(c for c in token if c not in _ALT_RAKAMLAR)
    return s or token


def ünlü_mü(token):
    return taban(token) in TÜM_ÜNLÜLER


DİZİ_AYIRICI = "+"


def dizi_yap(harfler):
    return DİZİ_AYIRICI.join(harfler)


def dizi_mi(token):
    return DİZİ_AYIRICI in token


def dizi_harfleri(token):
    return token.split(DİZİ_AYIRICI)


DOĞUM_KAYNAĞI = {dizi_yap(g): v for g, v in DOĞUMLAR.items()}


ÖZEL_KOMŞULAR = {
    frozenset(("y", "i")),
    frozenset(("w", "u")),
    frozenset(("ğ", "ı")),
    frozenset(("ğ", "y")),
    frozenset(("ğ", "v")),
    frozenset(("b", "w")),
    frozenset(("a", "e")),
    frozenset(("a", "o")),
    frozenset(("p", "ʔ")),
    frozenset(("t", "ʔ")),
    frozenset(("k", "ʔ")),
    frozenset(("s", "h")),
}


def _zayıf_mı(h):
    if h in TÜM_ÜNLÜLER:
        return True
    if h == "ğ":
        return True
    yer, biçim, _ = TÜM_ÜNSÜZLER[h]
    return (
        biçim in ("genizsil", "yansıl", "çarpmalı", "kayıcı")
        or yer == "gırtlaksıl"
    )


ZAYIFLAR = {
    h for h in set(TÜM_ÜNLÜLER) | set(TÜM_ÜNSÜZLER) if _zayıf_mı(h)
}

YAZILI_HARFLER = sorted(set(ÜNLÜLER) | set(ÜNSÜZLER))
SANAL_HARFLER = sorted(
    (set(TÜM_ÜNLÜLER) | set(TÜM_ÜNSÜZLER)) - set(YAZILI_HARFLER)
)
HARFLER = sorted(set(YAZILI_HARFLER) | set(SANAL_HARFLER))
_DÜĞÜMLER = HARFLER + [BOŞ]


def _komşu_mu(a, b):
    if frozenset((a, b)) in ÖZEL_KOMŞULAR:
        return True
    if a == BOŞ or b == BOŞ:
        x = b if a == BOŞ else a
        return x in ZAYIFLAR
    if a in TÜM_ÜNSÜZLER and b in TÜM_ÜNSÜZLER:
        return ünsüz_komşu_mu(a, b)
    if a in TÜM_ÜNLÜLER and b in TÜM_ÜNLÜLER:
        return ünlü_komşu_mu(a, b)
    return False


_SANAL_KÜME = set(SANAL_HARFLER)

_KOMŞULUK = {
    d: sorted(
        (e for e in _DÜĞÜMLER if e != d and _komşu_mu(d, e)),
        key=lambda e, d=d: (
            e in _SANAL_KÜME,
            frozenset((d, e)) not in ÖZEL_KOMŞULAR,
            e,
        ),
    )
    for d in _DÜĞÜMLER
}


def _yolları_kur(düğümler, komşuluk):
    yollar = {}
    for kaynak in düğümler:
        önce = {kaynak: None}
        kuyruk = deque([kaynak])
        while kuyruk:
            d = kuyruk.popleft()
            if d == BOŞ and d != kaynak:
                continue
            for e in komşuluk[d]:
                if e not in önce:
                    önce[e] = d
                    kuyruk.append(e)
        for hedef in önce:
            yol_ = []
            x = hedef
            while x is not None:
                yol_.append(x)
                x = önce[x]
            yollar[(kaynak, hedef)] = list(reversed(yol_))
    return yollar


_YOLLAR = _yolları_kur(_DÜĞÜMLER, _KOMŞULUK)


def özellik_uzaklığı(a, b):
    a, b = taban(a), taban(b)
    if a == b:
        return 0
    if frozenset((a, b)) in ÖZEL_KOMŞULAR:
        return 1
    if a in TÜM_ÜNSÜZLER and b in TÜM_ÜNSÜZLER:
        ya, ba, sa = TÜM_ÜNSÜZLER[a]
        yb, bb, sb = TÜM_ÜNSÜZLER[b]
        yf = abs(YERLER.index(ya) - YERLER.index(yb))
        bf = 0 if ba == bb else (
            1 if frozenset((ba, bb)) in BİÇİM_KOMŞULUĞU else 2
        )
        return max(1, yf + bf + (sa != sb))
    if a in TÜM_ÜNLÜLER and b in TÜM_ÜNLÜLER:
        (ha, aa, ya, ua), (hb, ab, yb, ub) = TÜM_ÜNLÜLER[a], TÜM_ÜNLÜLER[b]
        return max(1, abs(ha - hb) + (aa != ab) + (ya != yb) + (ua != ub))
    return 5


def silme_maliyeti(h):
    return 1 if taban(h) in ZAYIFLAR else 3


def uzaklık(a, b):
    if dizi_mi(b):
        kaynak = DOĞUM_KAYNAĞI.get(b)
        if kaynak is None:
            return 99
        ara = uzaklık(a, kaynak)
        return ara + 1 if ara < 99 else 99
    a, b = taban(a), taban(b)
    if a == b:
        return 0
    p = _YOLLAR.get((a, b))
    return len(p) - 1 if p else 99


def yol(a, b):
    a, b = taban(a), taban(b)
    return list(_YOLLAR[(a, b)])


def yollar(a, b, en_çok=12):
    a, b = taban(a), taban(b)
    if a == b:
        return [[a]]
    uz = {a: 0}
    sıra = [a]
    i = 0
    while i < len(sıra):
        d = sıra[i]
        i += 1
        if d == BOŞ and d != a:
            continue
        for e in _KOMŞULUK[d]:
            if e not in uz:
                uz[e] = uz[d] + 1
                sıra.append(e)
    if b not in uz:
        return []
    sonuçlar = []

    def geri(v, kuyruk):
        if len(sonuçlar) >= en_çok:
            return
        if v == a:
            sonuçlar.append([a] + kuyruk)
            return
        for u in sorted(_KOMŞULUK[v]):
            if uz.get(u) == uz[v] - 1 and (u == a or u != BOŞ):
                geri(u, [v] + kuyruk)

    geri(b, [])
    return sonuçlar

