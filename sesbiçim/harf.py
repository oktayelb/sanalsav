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

from .ünlü import DOĞUMLAR, ÜNLÜLER, TÜM_ÜNLÜLER, ünlü_komşu_mu
from .ünsüz import (
    BİÇİM_KOMŞULUĞU, YERLER, ÜNSÜZLER, TÜM_ÜNSÜZLER, ünsüz_komşu_mu,
)

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


# --- çok-harf (doğum) dizileri ---------------------------------------------
# README'deki "grupça değişim"in tek harften çok harf yarısı: şimdilik
# yalnız uzun ünlüler doğurabilir (bkz. ünlü.DOĞUMLAR). Bir dizi, ayırıcıyla
# birleştirilmiş harf dizgesidir ("u+v+u"); böylece karşılıklık ve kural
# tablolarında tek bir belirteç gibi taşınır ama harflerine açılabilir.
DİZİ_AYIRICI = "+"


def dizi_yap(harfler):
    return DİZİ_AYIRICI.join(harfler)


def dizi_mi(token):
    return DİZİ_AYIRICI in token


def dizi_harfleri(token):
    return token.split(DİZİ_AYIRICI)


DOĞUM_KAYNAĞI = {dizi_yap(g): v for g, v in DOĞUMLAR.items()}


# Özellik adımlarıyla yakalanamayan ama doğal dillerde iyi bilinen geçişler.
# (g ~ ğ artık doğal kenardır: aynı yer, patlamalı ~ sızıcı, ikisi de ötümlü.)
ÖZEL_KOMŞULAR = {
    frozenset(("y", "i")),  # yarı ünlü ~ ünlü
    frozenset(("w", "u")),
    frozenset(("ğ", "ı")),
    frozenset(("ğ", "y")),  # Türkçe yazım gerçeği: değil ~ deyil
    frozenset(("ğ", "v")),  # ağız/dialekt geçişi (öğün ~ övün)
    frozenset(("b", "w")),  # b ~ w (README'deki *winer > bier örneği)
    frozenset(("a", "e")),  # açık ünlü incelmesi
    frozenset(("a", "o")),  # açık ünlü yuvarlaklaşması
    # boğumsuzlaşma (debuccalization): ağız kapanması gırtlağa iner
    frozenset(("p", "ʔ")),
    frozenset(("t", "ʔ")),
    frozenset(("k", "ʔ")),
    frozenset(("s", "h")),
}

# Tek adımda düşebilen / türeyebilen "zayıf" sesler. Güçlü ünsüzler ancak
# önce bu seslerden birine zayıflayarak (lenisyon) silinebilir. Ad listesi
# yerine özellik kuralı: ünlüler, genizsil/akıcı/kayıcı ünsüzler ve
# gırtlaksıllar zayıftır (hesaplamayla üretilen harfler de kapsanır).


def _zayıf_mı(h):
    if h in TÜM_ÜNLÜLER:
        return True
    if h == "ğ":
        return True  # yumuşak g yazıda da sıkça düşer (dağ ~ da)
    yer, biçim, _ = TÜM_ÜNSÜZLER[h]
    return (
        biçim in ("genizsil", "yansıl", "çarpmalı", "kayıcı")
        or yer == "gırtlaksıl"
    )


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

# Komşular yazılı harfler, sonra bilinen özel geçişler önce gelecek biçimde
# sıralanır: eş uzunluktaki yollar arasında doğal/yazılı duraklı olan seçilsin.
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


def özellik_uzaklığı(a, b):
    """Hizalama için doğrudan özellik uzaklığı (türetim yolundan bağımsız).

    Hizalama yazılı sözcükleri karşılaştırır; iki harfin BENZERLİĞİNİ ölçer,
    aralarındaki tarihsel yolu değil. Bu yüzden grafik adımı yerine özellik
    farklarının toplamı kullanılır; ince yer ölçeği hizalamayı bozamaz.
    """
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
    return 5  # ünlü ~ ünsüz (köprü çiftleri dışında uzak)


def silme_maliyeti(h):
    """Hizalamada bir harfi boşlukla eşlemenin maliyeti."""
    return 1 if taban(h) in ZAYIFLAR else 3


def uzaklık(a, b):
    """İki harf arasındaki en kısa doğal yolun adım sayısı.

    Hedef bir doğum dizisiyse (u+v+u gibi) yol, doğuran uzun ünlüye gidip
    son adımda doğurmaktır: uzaklık = (a -> uzun ünlü) + 1.
    """
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
