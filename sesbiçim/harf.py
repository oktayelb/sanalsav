# -*- coding: utf-8 -*-
"""Harfler arası "doğal ses yolu" hesabı.

Bütün harfler (ünlü + ünsüz + boş ses) bir grafiğin düğümleridir; iki harf
arasında tek adımlık doğal bir ses değişimi varsa kenar vardır. Böylece
README'deki k -> f sorunu kendiliğinden çözülür: k ile f arasındaki en kısa
yol k -> g -> ... -> f gibi ara duraklardan geçer ve her Ön Dil katmanı bu
zincirin bir adımını üstlenir.

Boş ses (0) yalnız uç düğümdür: silinme/türeme yolun son/ilk adımı olabilir
ama iki gerçek harf arasındaki yol boş sesin "içinden" geçemez.
"""

from collections import deque

from .ünlü import ÜNLÜLER, ünlü_komşu_mu
from .ünsüz import ÜNSÜZLER, ünsüz_komşu_mu

BOŞ = "0"

_ALT_RAKAMLAR = "₀₁₂₃₄₅₆₇₈₉"


def alt_yazı(n):
    """Bir sayıyı alt simge dizgesine çevirir (2 -> ₂)."""
    return "".join(_ALT_RAKAMLAR[int(c)] for c in str(n))


def taban(token):
    """Türetilmiş/etiketli bir harfin (b₂ gibi) taban harfini verir."""
    s = "".join(c for c in token if c not in _ALT_RAKAMLAR)
    return s or token


def ünlü_mü(token):
    return taban(token) in ÜNLÜLER


# Özellik adımlarıyla yakalanamayan ama doğal dillerde iyi bilinen geçişler.
ÖZEL_KOMŞULAR = {
    frozenset(("y", "i")),  # yarı ünlü ~ ünlü
    frozenset(("w", "u")),
    frozenset(("ğ", "ı")),
    frozenset(("g", "ğ")),  # yumuşama
    frozenset(("ğ", "v")),  # ağız/dialekt geçişi (öğün ~ övün)
    frozenset(("b", "w")),  # b ~ w (README'deki *winer > bier örneği)
    frozenset(("a", "e")),  # açık ünlü incelmesi
    frozenset(("a", "o")),  # açık ünlü yuvarlaklaşması
}

# Tek adımda düşebilen / türeyebilen "zayıf" sesler. Güçlü ünsüzler ancak
# önce bu seslerden birine zayıflayarak (lenisyon) silinebilir.
ZAYIFLAR = {"h", "ğ", "y", "w", "m", "n", "r", "l"} | set(ÜNLÜLER)

HARFLER = sorted(set(ÜNLÜLER) | set(ÜNSÜZLER))
_DÜĞÜMLER = HARFLER + [BOŞ]


def _komşu_mu(a, b):
    if frozenset((a, b)) in ÖZEL_KOMŞULAR:
        return True
    if a == BOŞ or b == BOŞ:
        x = b if a == BOŞ else a
        return x in ZAYIFLAR
    if a in ÜNSÜZLER and b in ÜNSÜZLER:
        return ünsüz_komşu_mu(a, b)
    if a in ÜNLÜLER and b in ÜNLÜLER:
        return ünlü_komşu_mu(a, b)
    return False


_KOMŞULUK = {
    d: [e for e in _DÜĞÜMLER if e != d and _komşu_mu(d, e)] for d in _DÜĞÜMLER
}


def _yolları_kur():
    yollar = {}
    for kaynak in _DÜĞÜMLER:
        önce = {kaynak: None}
        kuyruk = deque([kaynak])
        while kuyruk:
            d = kuyruk.popleft()
            if d == BOŞ and d != kaynak:
                continue  # boş sesin içinden geçilmez
            for e in _KOMŞULUK[d]:
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


_YOLLAR = _yolları_kur()


def uzaklık(a, b):
    """İki harf arasındaki en kısa doğal yolun adım sayısı."""
    a, b = taban(a), taban(b)
    if a == b:
        return 0
    p = _YOLLAR.get((a, b))
    return len(p) - 1 if p else 99


def yol(a, b):
    """İki harf arasındaki en kısa doğal yol (uç noktalar dahil)."""
    a, b = taban(a), taban(b)
    return list(_YOLLAR[(a, b)])


def yollar(a, b, en_çok=12):
    """İki harf arasındaki BÜTÜN en kısa doğal yollar (en fazla en_çok).

    Ara katman çakışmalarında harf etiketlemeden önce eşdeğer uzunlukta
    başka bir doğal yol denemek için kullanılır.
    """
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
