import multiprocessing
import os
from types import SimpleNamespace

from sesbiçim.harf import taban, uzaklık

from . import insa
from .rapor import açıklama_uzunluğu

_ORTAK = {}


def ölç(sonuç, dal_adları):
    evren = {t for w in sonuç["protolar"] for t in w}
    for kt in sonuç["türevler"]:
        for biçimler in kt:
            for b in biçimler:
                evren |= set(b)
    seri = SimpleNamespace(
        dal_adları=dal_adları, proto_kelimeler=sonuç["protolar"],
        katman=sonuç["katman"], tablolar=sonuç["tablolar"],
        istisnalar=sonuç["istisnalar"])
    return açıklama_uzunluğu(seri, len(evren))["toplam"]


def _harf_sayısı(atama):
    return len(set(atama.values()))


def _adaylar(atama, korr_yerleri):
    küme = {}
    for ç, t in atama.items():
        küme.setdefault(t, []).append(ç)
    kullanım = {t: sum(len(korr_yerleri[ç]) for ç in çler) for t, çler in küme.items()}
    adaylar = []
    for Y in sorted(küme, key=lambda t: (kullanım[t], t)):
        refleksler = {r for ç in küme[Y] for r in ç}
        for H in sorted(küme, key=lambda t: (-kullanım[t], t)):
            if H == Y or uzaklık(taban(Y), taban(H)) > 1:
                continue
            if all(uzaklık(taban(H), r) <= insa.EN_UZUN_YOL for r in refleksler):
                adaylar.append((Y, H))
    return adaylar


def _birleşik(atama, çiftler):
    ad = {}
    for Y, H in çiftler:
        ad[Y] = H
    def kök(t):
        while t in ad:
            t = ad[t]
        return t
    return {ç: kök(t) for ç, t in atama.items()}


def _dene(çift):
    o = _ORTAK
    aday = _birleşik(o["atama"], [çift])
    sonuç = insa._tamamla(aday, o["düzensiz"], o["korr_yerleri"], o["hizalamalar"],
                          o["metatezler"], o["çiftler"], o["en_az_katman"],
                          katmanlar=o["katmanlar"], geç_ayrışma=True)
    if sonuç["istisnalar"]:
        return çift, None
    return çift, ölç(sonuç, o["dal_adları"])


def _katmanlar(sonuç, metatezler):
    katman = list(sonuç["katman"])
    if metatezler:
        katman[1] -= 1
    return [[T] for T in katman]


def birleştir(atama, düzensiz, korr_yerleri, hizalamalar, metatezler, çiftler,
              en_az_katman, taban_sonuç, dal_adları, ölçüt="mdl", süreç=None,
              günlük=None):
    günlük = günlük or (lambda *_: None)
    süreç = süreç or os.cpu_count() or 1
    geçerli_atama = dict(atama)
    geçerli_sonuç = taban_sonuç
    geçerli_mdl = ölç(taban_sonuç, dal_adları)
    günlük(f"başlangıç: {_harf_sayısı(geçerli_atama)} harf, MDL {geçerli_mdl:.0f}")
    bağlam = multiprocessing.get_context("fork")
    başarısız = set()

    def doğrula(aday_atama):
        sonuç = insa._tamamla(aday_atama, düzensiz, korr_yerleri, hizalamalar,
                              metatezler, çiftler, en_az_katman,
                              katmanlar=_katmanlar(geçerli_sonuç, metatezler),
                              geç_ayrışma=True)
        if sonuç["istisnalar"]:
            return None, None
        return sonuç, ölç(sonuç, dal_adları)

    while True:
        adaylar = [ç for ç in _adaylar(geçerli_atama, korr_yerleri)
                   if ç not in başarısız]
        if not adaylar:
            break
        _ORTAK.clear()
        _ORTAK.update(atama=geçerli_atama, düzensiz=düzensiz, korr_yerleri=korr_yerleri,
                      hizalamalar=hizalamalar, metatezler=metatezler, çiftler=çiftler,
                      en_az_katman=en_az_katman, dal_adları=dal_adları,
                      katmanlar=_katmanlar(geçerli_sonuç, metatezler))
        with bağlam.Pool(süreç) as havuz:
            sonuçlar = havuz.map(_dene, adaylar, chunksize=1)
        başarısız |= {ç for ç, m in sonuçlar if m is None}
        uygun = sorted((m, ç) for ç, m in sonuçlar
                       if m is not None and (ölçüt == "harf" or m <= geçerli_mdl))
        günlük(f"  {len(adaylar)} aday denendi, {len(uygun)} uygun")
        if not uygun:
            break
        kabul_edilen = []
        for _, (Y, H) in uygun:
            if Y not in set(geçerli_atama.values()) or H not in set(geçerli_atama.values()):
                continue
            aday = _birleşik(geçerli_atama, [(Y, H)])
            sonuç, m = doğrula(aday)
            if sonuç is None or (ölçüt == "mdl" and m > geçerli_mdl):
                continue
            geçerli_atama, geçerli_sonuç, geçerli_mdl = aday, sonuç, m
            kabul_edilen.append(f"{Y}→{H}")
        if not kabul_edilen:
            break
        etkilenen = {t for k in kabul_edilen for t in k.split("→")}
        başarısız = {ç for ç in başarısız if not (set(ç) & etkilenen)}
        günlük(f"  kabul: {', '.join(kabul_edilen)} -> "
               f"{_harf_sayısı(geçerli_atama)} harf, MDL {geçerli_mdl:.0f}")
    son = insa._tamamla(geçerli_atama, düzensiz, korr_yerleri, hizalamalar, metatezler,
                        çiftler, en_az_katman, geç_ayrışma=True)
    if son["istisnalar"]:
        son = geçerli_sonuç
    return geçerli_atama, son
