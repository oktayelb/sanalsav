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

from .ünlü import ÜNLÜLER, TÜM_ÜNLÜLER, ünlü_komşu_mu
from .ünsüz import ÜNSÜZLER, TÜM_ÜNSÜZLER, ünsüz_komşu_mu

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
    return taban(token) in TÜM_ÜNLÜLER


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
# önce bu seslerden birine zayıflayarak (lenisyon) silinebilir. Ad listesi
# yerine özellik kuralı: ünlüler, genizsil/akıcı/kayıcı ünsüzler ve
# gırtlaksıllar zayıftır (hesaplamayla üretilen harfler de kapsanır).


def _zayıf_mı(h):
    if h in TÜM_ÜNLÜLER:
        return True
    yer, biçim, _ = TÜM_ÜNSÜZLER[h]
    return biçim in ("genizsil", "akıcı", "kayıcı") or yer == "gırtlaksıl"


ZAYIFLAR = {
    h for h in set(TÜM_ÜNLÜLER) | set(TÜM_ÜNSÜZLER) if _zayıf_mı(h)
}

# Yazılı harfler: girdi dillerinin alfabelerinde bulunabilenler.
YAZILI_HARFLER = sorted(set(ÜNLÜLER) | set(ÜNSÜZLER))
# Sanal harfler: yalnız Ön Dil çapası ve ara durak olarak kullanılanlar.
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

# Komşular yazılı harfler önce gelecek biçimde sıralanır: eş uzunluktaki
# yollar arasında sanal duraklı olanı ancak gerekiyorsa seçilsin.
_KOMŞULUK = {
    d: sorted(
        (e for e in _DÜĞÜMLER if e != d and _komşu_mu(d, e)),
        key=lambda e: (e in _SANAL_KÜME, e),
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
                continue  # boş sesin içinden geçilmez
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

# Hizalama, yazılı sözcükleri karşılaştırdığı için yalnız yazılı harflerin
# grafiğini görür; sanal harfler sadece yeniden kurma (çapa, zincir)
# tarafında iş görür. Böylece sanal harf eklemek hizalamayı bozmaz.
_YAZILI_DÜĞÜMLER = YAZILI_HARFLER + [BOŞ]
_YAZILI_KOMŞULUK = {
    d: [e for e in _KOMŞULUK[d] if e in set(_YAZILI_DÜĞÜMLER)]
    for d in _YAZILI_DÜĞÜMLER
}
_YAZILI_YOLLAR = _yolları_kur(_YAZILI_DÜĞÜMLER, _YAZILI_KOMŞULUK)


def yazılı_uzaklık(a, b):
    """Yalnız yazılı harflerden geçen en kısa yolun adım sayısı."""
    a, b = taban(a), taban(b)
    if a == b:
        return 0
    p = _YAZILI_YOLLAR.get((a, b))
    return len(p) - 1 if p else 99


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
