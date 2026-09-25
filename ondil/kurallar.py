from functools import lru_cache

from sesbiçim.harf import taban, ünlü_mü
from sesbiçim.ünlü import TÜM_ÜNLÜLER
from sesbiçim.ünsüz import TÜM_ÜNSÜZLER

BİRLEŞTİRİCİ = " ve "

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
    if ad in _KABALAR:
        return _KABALAR[ad]
    if ad in _SINIFLAR:
        return _SINIFLAR[ad]
    harf, yön = ad.rsplit(" ", 1)
    return _harf_işlevi(harf, yön)


@lru_cache(maxsize=None)
def bağlam_işlevi(ad):
    if BİRLEŞTİRİCİ in ad:
        işlevler = [_atom_işlevi(p) for p in ad.split(BİRLEŞTİRİCİ)]
        return lambda w, i: all(f(w, i) for f in işlevler)
    return _atom_işlevi(ad)


def bağlam_özgüllük(ad):
    if ad == "her yerde":
        return (1, 0, ad)
    atomlar = ad.split(BİRLEŞTİRİCİ)
    genellik = sum(2 if a in _KABALAR else 1 if a in _SINIFLAR else 0
                   for a in atomlar)
    return (-len(atomlar), genellik, ad)


def _ayrı(f, kendi, diğer):
    return all(f(w, i) for w, i in kendi) and not any(f(w, i) for w, i in diğer)


def _bağlam_ara(kendi, diğer):
    if not kendi or not diğer:
        return None

    for ad in (a for a, _ in _SOL_KABA + _SAĞ_KABA + _TEKİL_KABA):
        if _ayrı(_KABALAR[ad], kendi, diğer):
            return ad

    for ad, f in _SINIF_SOL + _SINIF_SAĞ + _UYUM:
        if _ayrı(f, kendi, diğer):
            return ad

    sol_sınıf = [(ad, f) for ad, f in _SOL_KABA + _SINIF_SOL + _UYUM
                 if all(f(w, i) for w, i in kendi)]
    sağ_sınıf = [(ad, f) for ad, f in _SAĞ_KABA + _SINIF_SAĞ
                 if all(f(w, i) for w, i in kendi)]
    for sad, sf in sol_sınıf:
        for rad, rf in sağ_sınıf:
            if not any(sf(w, i) and rf(w, i) for w, i in diğer):
                return sad + BİRLEŞTİRİCİ + rad

    if len(kendi) < MIN_BAĞLAM_DESTEĞİ:
        return None

    sol_harfler = sorted({taban(w[i - 1]) for w, i in kendi if i > 0})
    sağ_harfler = sorted({taban(w[i + 1]) for w, i in kendi if i + 1 < len(w)})
    sol_özgül = [(f"{p} ardında", _harf_işlevi(p, "ardında")) for p in sol_harfler]
    sağ_özgül = [(f"{p} önünde", _harf_işlevi(p, "önünde")) for p in sağ_harfler]
    for ad, f in sol_özgül + sağ_özgül:
        if _ayrı(f, kendi, diğer):
            return ad

    sol_aday = sol_sınıf + [(ad, f) for ad, f in sol_özgül
                            if all(f(w, i) for w, i in kendi)]
    sağ_aday = sağ_sınıf + [(ad, f) for ad, f in sağ_özgül
                            if all(f(w, i) for w, i in kendi)]
    for sad, sf in sol_aday:
        for rad, rf in sağ_aday:
            if not any(sf(w, i) and rf(w, i) for w, i in diğer):
                return sad + BİRLEŞTİRİCİ + rad
    return None


def ayır(kendi_yerleri, diğer_yerleri, protolar):
    kendi = [(protolar[k], i) for k, i in kendi_yerleri]
    diğer = [(protolar[k], i) for k, i in diğer_yerleri]
    return _bağlam_ara(kendi, diğer)


def sıralı_ayır(gruplar, protolar, varsayılan_adayı=6, hedef=None, kısmi=False):
    hedef = hedef or (lambda a: a)
    if not gruplar:
        return {}, None
    if len({hedef(a) for a, _ in gruplar}) < 2:
        return {a: ("her yerde", 0) for a, _ in gruplar}, None
    en_kötü = None
    en_iyi_kısmi = None
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
        takılan_konum = sum(len(yy) for _, yy in kalan)
        if en_iyi_kısmi is None or takılan_konum < en_iyi_kısmi[0]:
            sonuç[varsayılan[0]] = ("her yerde", len(sonuç))
            en_iyi_kısmi = (takılan_konum, sonuç, [a for a, _ in kalan])
    if kısmi:
        return en_iyi_kısmi[1], en_iyi_kısmi[2]
    return None, en_kötü

