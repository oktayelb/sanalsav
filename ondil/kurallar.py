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

from sesbiçim.harf import taban, ünlü_mü

BİRLEŞTİRİCİ = " ve "  # iki-yanlı bağlam adlarını birleştiren sözcük


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


def _harf_işlevi(harf, yön):
    if yön == "önünde":
        return lambda w, i: i + 1 < len(w) and taban(w[i + 1]) == harf
    return lambda w, i: i > 0 and taban(w[i - 1]) == harf


def _atom_işlevi(ad):
    """Tek bir atom adını (kaba ya da harfe özgü) işlevine çevirir."""
    if ad in _KABALAR:
        return _KABALAR[ad]
    harf, yön = ad.rsplit(" ", 1)
    return _harf_işlevi(harf, yön)


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
    sınıf_sayısı = sum(1 for a in atomlar if a in _KABALAR)
    return (-len(atomlar), sınıf_sayısı, ad)


def _ayrı(f, kendi, diğer):
    return all(f(w, i) for w, i in kendi) and not any(f(w, i) for w, i in diğer)


def _bağlam_ara(kendi, diğer, kaba=False):
    """kendi'yi diğer'den ayıran EN GENEL bağlamı arar (yoksa None).

    Kademe: (A) kaba tekil atomlar, (B) harfe özgü tekil atomlar, (C) bir
    sol + bir sağ atomun iki-yanlı birleşimi. İlk ayıran bağlam döner.

    kaba=True ise yalnız (A) denenir: harfe özgü/iki-yanlı koşullar belirli
    komşu harfe bağlı olduğundan kör türetimde ara katman biçimi ideal
    zincirden saparsa kırılır; ara katman ayrımında bu yüzden kaba (sınıf)
    bağlamlarla sınırlı kalınır (proto seviyesi katman-1'de güvenlidir).
    """
    if not kendi or not diğer:
        return None

    # A) kaba tekil atomlar (en genel)
    for ad in (a for a, _ in _SOL_KABA + _SAĞ_KABA + _TEKİL_KABA):
        if _ayrı(_KABALAR[ad], kendi, diğer):
            return ad
    if kaba:
        return None

    # B) harfe özgü tekil atomlar (kendi konumlarının komşu harflerinden)
    sol_harfler = sorted({taban(w[i - 1]) for w, i in kendi if i > 0})
    sağ_harfler = sorted({taban(w[i + 1]) for w, i in kendi if i + 1 < len(w)})
    sol_özgül = [(f"{p} ardında", _harf_işlevi(p, "ardında")) for p in sol_harfler]
    sağ_özgül = [(f"{p} önünde", _harf_işlevi(p, "önünde")) for p in sağ_harfler]
    for ad, f in sol_özgül + sağ_özgül:
        if _ayrı(f, kendi, diğer):
            return ad

    # C) iki-yanlı birleşim: bir sol atom (kaba ya da özgül) + bir sağ atom.
    # Birleşim kendi'nin TAMAMINDA doğru olmalı; bu yüzden yalnız kendi'nin
    # tamamını kapsayan atomlar aday alınır (gereksiz çiftler elenir).
    sol_aday = [(ad, f) for ad, f in _SOL_KABA + sol_özgül
                if all(f(w, i) for w, i in kendi)]
    sağ_aday = [(ad, f) for ad, f in _SAĞ_KABA + sağ_özgül
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
