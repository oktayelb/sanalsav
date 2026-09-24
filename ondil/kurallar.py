# -*- coding: utf-8 -*-
"""Ses değişim kurallarının bağlam koşulları.

Bir Ön Dil harfi bir dalda birden çok sese gidiyorsa, kuralları ayrıştırmak
için önce buradaki bağlam koşulları denenir (asgari harf hedefi: yeni harf
türetmeden önce bağlamla genelleme). Bağlam dağarcığı kademelidir:

  A) KABA atomlar  : söz başı/sonu/içi, ünlü/ünsüz önünde/ardında (en genel)
  B) HARFE ÖZGÜ    : "k önünde", "a ardında" (belirli komşu harf)
  C) İKİ YANLI     : bir sol + bir sağ atomun birleşimi ("ünlü ardında ve
                     k önünde") — en özgül

Arama bu sırayla yapılır: ayrımı sağlayan EN GENEL bağlam seçilir, böylece
harf sayısı düşerken kurallar gereksizce özelleşmez (harf↔kural ödünleşimi).
Uygulamada bir konuma birden çok kural uyarsa en ÖZGÜL olan kazanır
(bkz. bağlam_özgüllük); "her yerde" en sona kalır.
"""

from functools import lru_cache

from sesbiçim.harf import taban, ünlü_mü
from sesbiçim.ünlü import TÜM_ÜNLÜLER
from sesbiçim.ünsüz import TÜM_ÜNSÜZLER

BİRLEŞTİRİCİ = " ve "  # iki-yanlı bağlam adlarını birleştiren sözcük

# Bir ses yasası bir ORTAMA koşullanıyorsa o ortamın en az bu kadar tanığı
# (örnek konumu) olmalı. Tek örneğe ortam uydurmak ezberdir; dilbilimsel
# olarak düzenli ses değişimi birden çok örnekte görülmelidir. Desteği bu
# eşiğin altında kalan bölünmeler bağlamla AYRILMAZ (None döner) — çağıran
# o zaman koşulsuz temiz bir harf türetir (harf sayısı artabilir ama kural
# tek bir kelimeyi ezberlemez).
MIN_BAĞLAM_DESTEĞİ = 2


def _başta(w, i):
    return i == 0


def _sonda(w, i):
    return i == len(w) - 1


def _ünlü_önünde(w, i):
    return i + 1 < len(w) and ünlü_mü(w[i + 1])


def _ünsüz_önünde(w, i):
    return i + 1 < len(w) and not ünlü_mü(w[i + 1])


def _ünlü_ardında(w, i):
    return i > 0 and ünlü_mü(w[i - 1])


def _ünsüz_ardında(w, i):
    return i > 0 and not ünlü_mü(w[i - 1])


def _içte(w, i):
    return 0 < i < len(w) - 1


def _her_yerde(w, i):
    return True


# Kaba (sınıf/konum) atomlar; sol-yanlı ve sağ-yanlı olarak ayrılır (iki-yanlı
# birleşim için bir sol + bir sağ atom seçilir). "söz içinde" iki yanı da
# kısıtladığından tek başına da denenir.
_SOL_KABA = [
    ("söz başında", _başta),
    ("ünlü ardında", _ünlü_ardında),
    ("ünsüz ardında", _ünsüz_ardında),
]
_SAĞ_KABA = [
    ("söz sonunda", _sonda),
    ("ünlü önünde", _ünlü_önünde),
    ("ünsüz önünde", _ünsüz_önünde),
]
_TEKİL_KABA = [("söz içinde", _içte)]

_KABALAR = dict(_SOL_KABA + _SAĞ_KABA + _TEKİL_KABA + [("her yerde", _her_yerde)])
# Geriye-dönük uyum / kaba sıralama (özgül atomlar bu listede yer almaz)
BAĞLAM_SIRASI = [ad for ad, _ in
                 _SOL_KABA + _SAĞ_KABA + _TEKİL_KABA] + ["her yerde"]


# --- doğal sınıflar ----------------------------------------------------------
# Gerçek ses yasaları tek bir komşu harfe değil, SINIFA koşullanır: "ön ünlü
# önünde" (damaksıllaşma), "ötümlü ünsüz ardında", "genizsil önünde",
# "ünlüler arasında" (yumuşama), ünlü uyumu ("ön ünlülü sözcükte")...
# Sınıflar harf adlarından değil, sesbiçim/ özellik vektörlerinden hesaplanır.

def _ünlü_öz(t):
    return TÜM_ÜNLÜLER.get(taban(t))


def _ünsüz_öz(t):
    return TÜM_ÜNSÜZLER.get(taban(t))


_SINIF_TANIMI = {
    "ön ünlü": lambda t: (v := _ünlü_öz(t)) is not None and v[1] == 0,
    "arka ünlü": lambda t: (v := _ünlü_öz(t)) is not None and v[1] == 1,
    "yuvarlak ünlü": lambda t: (v := _ünlü_öz(t)) is not None and v[2] == 1,
    "düz ünlü": lambda t: (v := _ünlü_öz(t)) is not None and v[2] == 0,
    "dar ünlü": lambda t: (v := _ünlü_öz(t)) is not None and v[0] == 0,
    "geniş ünlü": lambda t: (v := _ünlü_öz(t)) is not None and v[0] > 0,
    "ötümlü ünsüz": lambda t: (c := _ünsüz_öz(t)) is not None and c[2],
    "ötümsüz ünsüz": lambda t: (c := _ünsüz_öz(t)) is not None and not c[2],
    "genizsil": lambda t: (c := _ünsüz_öz(t)) is not None and c[1] == "genizsil",
    "akıcı": lambda t: (c := _ünsüz_öz(t)) is not None
                        and c[1] in ("yansıl", "çarpmalı"),
    "patlamalı": lambda t: (c := _ünsüz_öz(t)) is not None
                           and c[1] in ("patlamalı", "yarıkapantılı"),
    "sızıcı": lambda t: (c := _ünsüz_öz(t)) is not None and c[1] == "sızıcı",
    "kayıcı": lambda t: (c := _ünsüz_öz(t)) is not None and c[1] == "kayıcı",
    "dudaksıl": lambda t: (c := _ünsüz_öz(t)) is not None
                          and c[0] in ("dudaksıl", "dişdudaksıl"),
    "dişsil": lambda t: (c := _ünsüz_öz(t)) is not None and c[0] == "dişsil",
    "damaksıl": lambda t: (c := _ünsüz_öz(t)) is not None
                          and c[0] in ("öndamaksıl", "artdamaksıl", "küçükdilsil"),
}


def _sınıf_komşu(sınıf, yön):
    f = _SINIF_TANIMI[sınıf]
    if yön == "önünde":
        return lambda w, i: i + 1 < len(w) and f(w[i + 1])
    return lambda w, i: i > 0 and f(w[i - 1])


def _uyum(sınıf):
    """Ünlü uyumu: sözcüğün ilk ünlüsü bu sınıftansa (ön/arka ünlülü sözcük)."""
    f = _SINIF_TANIMI[sınıf]

    def işlev(w, i):
        for t in w:
            if ünlü_mü(t):
                return f(t)
        return False
    return işlev


_SINIF_SOL = [(f"{s} ardında", _sınıf_komşu(s, "ardında")) for s in _SINIF_TANIMI]
_SINIF_SAĞ = [(f"{s} önünde", _sınıf_komşu(s, "önünde")) for s in _SINIF_TANIMI]
_UYUM = [(f"{s}lü sözcükte", _uyum(s)) for s in ("ön ünlü", "arka ünlü",
                                                 "yuvarlak ünlü", "düz ünlü")]
_SINIFLAR = dict(_SINIF_SOL + _SINIF_SAĞ + _UYUM)


def _harf_işlevi(harf, yön):
    if yön == "önünde":
        return lambda w, i: i + 1 < len(w) and taban(w[i + 1]) == harf
    return lambda w, i: i > 0 and taban(w[i - 1]) == harf


def _atom_işlevi(ad):
    """Tek bir atom adını (kaba ya da harfe özgü) işlevine çevirir."""
    if ad in _KABALAR:
        return _KABALAR[ad]
    if ad in _SINIFLAR:
        return _SINIFLAR[ad]
    harf, yön = ad.rsplit(" ", 1)
    return _harf_işlevi(harf, yön)


@lru_cache(maxsize=None)
def bağlam_işlevi(ad):
    """Bir bağlam adını (atom ya da iki-yanlı birleşim) işlevine çevirir."""
    if BİRLEŞTİRİCİ in ad:
        işlevler = [_atom_işlevi(p) for p in ad.split(BİRLEŞTİRİCİ)]
        return lambda w, i: all(f(w, i) for f in işlevler)
    return _atom_işlevi(ad)


def bağlam_özgüllük(ad):
    """Sıralama anahtarı: KÜÇÜK = daha özgül = çakışmada kazanır.

    Daha çok atomlu bağlam daha özgüldür; eşitlikte harfe özgü atom sınıf
    atomundan özgüldür. "her yerde" en az özgüldür (her zaman kaybeder).
    """
    if ad == "her yerde":
        return (1, 0, ad)
    atomlar = ad.split(BİRLEŞTİRİCİ)
    # kaba atom en genel (2), doğal sınıf ortada (1), harfe özgü en özgül (0)
    genellik = sum(2 if a in _KABALAR else 1 if a in _SINIFLAR else 0
                   for a in atomlar)
    return (-len(atomlar), genellik, ad)


def _ayrı(f, kendi, diğer):
    return all(f(w, i) for w, i in kendi) and not any(f(w, i) for w, i in diğer)


def _bağlam_ara(kendi, diğer, kaba=False):
    """kendi'yi diğer'den ayıran EN GENEL bağlamı arar (yoksa None).

    Kademe: (A) kaba tekil atomlar, (B) harfe özgü tekil atomlar, (C) bir
    sol + bir sağ atomun iki-yanlı birleşimi. İlk ayıran bağlam döner.

    kaba="sınıf" ise kaba atomlar ve doğal sınıflar denenir (ara katmanlar
    için); kaba=True ise yalnız (A) denenir: harfe özgü/iki-yanlı koşullar belirli
    komşu harfe bağlı olduğundan kör türetimde ara katman biçimi ideal
    zincirden saparsa kırılır; ara katman ayrımında bu yüzden kaba (sınıf)
    bağlamlarla sınırlı kalınır (proto seviyesi katman-1'de güvenlidir).
    """
    if not kendi or not diğer:
        return None

    # A) kaba tekil atomlar (en genel; ünlü/ünsüz/konum doğal sınıflardır,
    # tek örnekte bile makul bir ses değişimi ortamıdır)
    for ad in (a for a, _ in _SOL_KABA + _SAĞ_KABA + _TEKİL_KABA):
        if _ayrı(_KABALAR[ad], kendi, diğer):
            return ad
    if kaba is True:
        return None

    # B1) doğal sınıf atomları (ön ünlü önünde, ötümlü ünsüz ardında, uyum).
    # Sınıfa koşullu yasa geneldir ve öbür bütün sözcüklere karşı sınanır
    # (bu ortamdaki hiçbir başka sözcük aykırı düşmez); tek tanık yeter.
    for ad, f in _SINIF_SOL + _SINIF_SAĞ + _UYUM:
        if _ayrı(f, kendi, diğer):
            return ad

    # C1) iki yanlı sınıf birleşimi: "ünlüler arasında" tipi ortamlar
    sol_sınıf = [(ad, f) for ad, f in _SOL_KABA + _SINIF_SOL + _UYUM
                 if all(f(w, i) for w, i in kendi)]
    sağ_sınıf = [(ad, f) for ad, f in _SAĞ_KABA + _SINIF_SAĞ
                 if all(f(w, i) for w, i in kendi)]
    for sad, sf in sol_sınıf:
        for rad, rf in sağ_sınıf:
            if not any(sf(w, i) and rf(w, i) for w, i in diğer):
                return sad + BİRLEŞTİRİCİ + rad
    if kaba == "sınıf":
        return None

    # Harfe özgü bağlamlar ancak yeterli tanık varsa: belirli bir komşu
    # harfe bağlı bir kuralı tek örneğe uydurmak ezberdir.
    if len(kendi) < MIN_BAĞLAM_DESTEĞİ:
        return None

    # B2) harfe özgü tekil atomlar (kendi konumlarının komşu harflerinden)
    sol_harfler = sorted({taban(w[i - 1]) for w, i in kendi if i > 0})
    sağ_harfler = sorted({taban(w[i + 1]) for w, i in kendi if i + 1 < len(w)})
    sol_özgül = [(f"{p} ardında", _harf_işlevi(p, "ardında")) for p in sol_harfler]
    sağ_özgül = [(f"{p} önünde", _harf_işlevi(p, "önünde")) for p in sağ_harfler]
    for ad, f in sol_özgül + sağ_özgül:
        if _ayrı(f, kendi, diğer):
            return ad

    # C2) harfe özgü atom içeren iki yanlı birleşim
    sol_aday = sol_sınıf + [(ad, f) for ad, f in sol_özgül
                            if all(f(w, i) for w, i in kendi)]
    sağ_aday = sağ_sınıf + [(ad, f) for ad, f in sağ_özgül
                            if all(f(w, i) for w, i in kendi)]
    for sad, sf in sol_aday:
        for rad, rf in sağ_aday:
            if not any(sf(w, i) and rf(w, i) for w, i in diğer):
                return sad + BİRLEŞTİRİCİ + rad
    return None


def ayır_biçimlerle(kendi, diğer, kaba=False):
    """_bağlam_ara'nın doğrudan (kelime_biçimi, konum) çiftleriyle çağrılışı.

    `kendi`/`diğer` herhangi bir katmanın biçimlerinden gelebilir; böylece
    aynı bağlam koşulları ara Ön Dil katmanlarında da denenir (ayrım proto'da
    değil, sesler kaydıktan sonraki bir alt dilde belirebilir). Ara katman
    için kaba=True verilir (harfe özgü koşullar kör türetimde kırılgandır).
    """
    return _bağlam_ara(kendi, diğer, kaba=kaba)


def ayır(kendi_yerleri, diğer_yerleri, protolar):
    """Bir kural grubunu diğerlerinden ayıran bağlam koşulu arar (proto biçim).

    Koşul, grubun bütün görüldüğü yerlerde doğru, diğer bütün gruplarınkinde
    yanlış olmalıdır. Bulunamazsa None döner (o zaman yeni harf türetilir).
    """
    kendi = [(protolar[k], i) for k, i in kendi_yerleri]
    diğer = [(protolar[k], i) for k, i in diğer_yerleri]
    return _bağlam_ara(kendi, diğer)


def sıralı_ayır(gruplar, protolar, varsayılan_adayı=6, hedef=None):
    """Refleks gruplarını SIRALI kurallarla (karar listesi) ayırır.

    gruplar: [(anahtar, [(kelime, konum), ...])], sıklık sırasıyla. Biri
    "her yerde" (varsayılan) kalır; öbürleri sırayla dizilir: sıradaki
    kuralın bağlamı kendi konumlarının hepsinde doğru, KENDİSİNDEN SONRA
    gelen (ve başka yere giden) grupların konumlarında yanlış olmalıdır.
    Önceki kuralların aldığı konumlar artık onu bağlamaz (gerçek ses
    tarihinde önce işleyen yasa sözcüklerini alır, sonraki yasa yalnız
    kalanları ayırmak zorundadır). Bu, her grubun ÖBÜR BÜTÜN gruplardan tek
    bağlamla ayrılmasını isteyen eski ölçütten kesin olarak güçlüdür.

    hedef: anahtardan çıktıyı veren işlev (verilirse aynı çıktıya giden
    gruplar birbirinden ayrılmak zorunda değildir: aynı değişim iki ayrı
    ortamda iki yasayla olabilir). Verilmezse her anahtar ayrı çıktıdır.

    Döner: ({anahtar: (bağlam, öncelik)}, None) ya da (None, takılanlar).
    """
    hedef = hedef or (lambda a: a)
    if not gruplar:
        return {}, None
    if len({hedef(a) for a, _ in gruplar}) < 2:
        return {a: ("her yerde", 0) for a, _ in gruplar}, None
    en_kötü = None
    for v in range(min(max(varsayılan_adayı, 1), len(gruplar))):
        varsayılan = gruplar[v]
        vh = hedef(varsayılan[0])
        kalan = [g for i, g in enumerate(gruplar) if i != v]
        sonuç = {}
        while kalan:
            bulundu = False
            for idx, (anahtar, yer) in enumerate(kalan):
                h = hedef(anahtar)
                diğer = [y for i, (a2, yy) in enumerate(kalan)
                         if i != idx and hedef(a2) != h for y in yy]
                if vh != h:
                    diğer += varsayılan[1]
                if not diğer:
                    bağlam = "her yerde"
                else:
                    bağlam = ayır(yer, diğer, protolar)
                if bağlam is not None:
                    sonuç[anahtar] = (bağlam, len(sonuç))
                    kalan.pop(idx)
                    bulundu = True
                    break
            if not bulundu:
                break
        if not kalan:
            sonuç[varsayılan[0]] = ("her yerde", len(sonuç))
            return sonuç, None
        if en_kötü is None or len(kalan) < len(en_kötü):
            en_kötü = [a for a, _ in kalan]
    return None, en_kötü
