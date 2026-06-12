#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SANAL SAV — verilen sözcük listelerinden varsayımsal Ön Dil serisi kurar.

Kullanım:
    python3 ana.py türkçe ingilizce
    python3 ana.py türkçe azerbaycanca türkmence [--eşik 2]

İKİ ya da DAHA ÇOK dil ADI verilir (diller/<ad>.txt olarak çözülür); ikiden
çok dilde ortak ön dil yıldız hizalamayla kurulur. Dosya biçimi: her satırda
"anlam<boşluk>sözcük"; bütün dosyalar aynı anlam sırasını izlemelidir
(bkz. diller/README.md). Rapor adı verilmezse 'rapor_<kısaltmalar>.txt'
olarak dillerden türetilir. Varsayılan diller: Türkçe ve İngilizce.
"""

import argparse
import pathlib
import sys

from sesbiçim.harf import YAZILI_HARFLER
from ondil.insa import seri_oluştur
from ondil.rapor import rapor_üret


def liste_yükle(yol):
    çiftler = []
    for satır in pathlib.Path(yol).read_text(encoding="utf-8").splitlines():
        satır = satır.strip()
        if not satır or satır.startswith("#"):
            continue
        parçalar = satır.split()
        if len(parçalar) < 2:
            raise SystemExit(f"{yol}: bozuk satır: {satır!r}")
        çiftler.append((parçalar[0], parçalar[1]))
    return çiftler


def harfleri_doğrula(ad, sözcükler):
    bilinmeyen = sorted(
        {h for s in sözcükler for h in s if h not in YAZILI_HARFLER}
    )
    if bilinmeyen:
        raise SystemExit(
            f"{ad}: sesbiçim tablolarında tanımsız harf(ler): "
            + " ".join(bilinmeyen)
        )


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("diller", nargs="*",
                   default=["türkçe", "ingilizce"],
                   help="iki ya da DAHA ÇOK dil ADI (ör. türkçe ingilizce); "
                        "diller/<ad>.txt olarak çözülür. Dosya yolu da verilebilir.")
    p.add_argument("--adlar", default=None,
                   help="dillerin görünen adları, virgülle ayrılmış "
                        "(boşsa dosya adından türetilir)")
    p.add_argument("--rapor", default=None,
                   help="rapor dosyası (boşsa 'rapor_<kısaltmalar>.txt' "
                        "olarak verilen dillerden türetilir)")
    p.add_argument("--en-az-katman", type=int, default=0,
                   help="dallar için en az katman sayısı")
    p.add_argument("--eşik", dest="türetim_eşiği", type=int, default=1,
                   help="yeni bir Ön Dil harfi en az bu kadar konumu "
                        "kurtarmalı; altında kalan karşılıklıklar istisna "
                        "sayılır (varsayılan 1 = tam düzenlilik garantisi)")
    p.add_argument("--tarama", action="store_true",
                   help="farklı eşik değerleri için harf/düzenlilik "
                        "ödünleşim tablosunu yazdır")
    p.add_argument("--ön-dil-incelt", action="store_true",
                   help="alt katmanda ayrışabilen türetilmiş Ön Dil "
                        "harflerini tabanına geri katarak ön dili incelt "
                        "(düzenlilik korunur; yavaştır, kazanç genelde küçük)")
    args = p.parse_args(argv)

    if len(args.diller) < 2:
        raise SystemExit("En az iki dil gerekir.")

    # kullanıcı sadece dil ADI yazar (türkçe); diller/<ad>.txt olarak çözülür.
    # Geriye uyum: dosya yolu (/ içeren ya da .txt ile biten) doğrudan kullanılır.
    def yola_çevir(d):
        if "/" in d or d.endswith(".txt"):
            return pathlib.Path(d)
        return pathlib.Path("diller") / f"{d}.txt"

    yollar = [yola_çevir(d) for d in args.diller]
    for y in yollar:
        if not y.exists():
            raise SystemExit(f"Dil dosyası bulunamadı: {y}")

    if args.adlar:
        adlar = [a.strip() for a in args.adlar.split(",")]
        if len(adlar) != len(yollar):
            raise SystemExit("--adlar sayısı dil sayısıyla eşleşmeli.")
    else:
        adlar = [y.stem.capitalize() for y in yollar]

    if args.rapor is None:
        kısa = "_".join(y.stem[:3] for y in yollar)
        args.rapor = f"rapor_{kısa}.txt"

    listeler = [liste_yükle(y) for y in yollar]
    boy = len(listeler[0])
    for y, l in zip(yollar, listeler):
        if len(l) != boy:
            raise SystemExit(
                f"Listeler aynı uzunlukta olmalı: {y} {len(l)} != {boy}"
            )
    for i in range(boy):
        anlamlar = {l[i][0] for l in listeler}
        if len(anlamlar) > 1:
            print(f"uyarı: anlam etiketi uyuşmuyor: {anlamlar}", file=sys.stderr)

    for ad, l in zip(adlar, listeler):
        harfleri_doğrula(ad, [s for _, s in l])

    # her satır: (anlam, sözcük0, sözcük1, ...)  — değişken sayıda dil
    çiftler = [
        (listeler[0][i][0],) + tuple(l[i][1] for l in listeler)
        for i in range(boy)
    ]
    B = len(yollar)

    if args.tarama:
        print("Eşik taraması (harf sayısı ~ düzenlilik ödünleşimi):")
        print(f"  {'eşik':>4}  {'Ön Dil harfi':>12}  {'türetilmiş':>10}  "
              f"{'kural':>6}  {'istisna':>7}  {'düzenlilik':>10}")
        for eşik in (1, 2, 3, 4, 5, 8):
            s = seri_oluştur(çiftler, adlar, args.en_az_katman, eşik)
            dağarcık = {t for w in s.proto_kelimeler for t in w}
            türetilmiş = sum(1 for t in dağarcık if any(c in "₀₁₂₃₄₅₆₇₈₉" for c in t))
            kural = sum(
                1
                for dal in range(B)
                for ks in s.tablolar[dal].values()
                for k in ks
                if k.hedef != k.kaynak
            )
            türetim = B * boy
            düzenlilik = 100.0 * (türetim - len(s.istisnalar)) / türetim
            print(f"  {eşik:>4}  {len(dağarcık):>12}  {türetilmiş:>10}  "
                  f"{kural:>6}  {len(s.istisnalar):>7}  %{düzenlilik:>9.1f}")
        print()

    seri = seri_oluştur(çiftler, adlar, args.en_az_katman,
                        args.türetim_eşiği, ön_dil_incelt=args.ön_dil_incelt)
    metin = rapor_üret(seri)

    pathlib.Path(args.rapor).write_text(metin + "\n", encoding="utf-8")
    print(metin)
    print(f"(rapor {args.rapor} dosyasına da yazıldı)")


if __name__ == "__main__":
    main()
