#!/usr/bin/env python3
import argparse
import pathlib
import sys

from sesbiçim.harf import YAZILI_HARFLER
from ondil import hizalama, insa
from ondil.html import html_üret
from ondil.insa import seri_oluştur
from ondil.rapor import istatistik, rapor_üret


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
    p = argparse.ArgumentParser(
        description="Verilen sözcük listelerinden varsayımsal Ön Dil serisi kurar.")
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
    p.add_argument("--boşluk-cezası", type=float, default=1.0,
                   help="hizalamada her boşluğa eklenen ceza (0 = eski, "
                        "boşluğu ucuz hizalama: akrabasız sözcükler yan yana "
                        "dizilir, her dal öbürünün harflerini siler)")
    p.add_argument("--en-uzun-yol", type=int, default=5,
                   help="bir Ön Dil harfinin herhangi bir yansımasına en çok kaç "
                        "doğal ses adımı olabilir (büyüdükçe harf azalabilir, "
                        "katman artar)")
    p.add_argument("--html", default=None,
                   help="etkileşimli HTML görünümü (boşsa rapor adından türetilir)")
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
    hizalama.BOŞLUK_CEZASI = args.boşluk_cezası
    insa.EN_UZUN_YOL = args.en_uzun_yol

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

    çiftler = [
        (listeler[0][i][0],) + tuple(l[i][1] for l in listeler)
        for i in range(boy)
    ]
    B = len(yollar)

    if args.tarama:
        print("Eşik taraması (harf ~ düzenlilik ~ açıklama uzunluğu):")
        print(f"  {'eşik':>4}  {'harf':>5}  {'kural':>6}  {'tek tanık':>9}  "
              f"{'istisna':>7}  {'düzenlilik':>10}  {'MDL (bit)':>10}")
        for eşik in (1, 2, 3, 4, 5, 8):
            ist = istatistik(seri_oluştur(çiftler, adlar, args.en_az_katman, eşik))
            print(f"  {eşik:>4}  {len(ist['proto']):>5}  {ist['toplam_kural']:>6}  "
                  f"{ist['tek_tanıklı']:>9}  {ist['istisna']:>7}  "
                  f"%{ist['düzenlilik']:>9.1f}  {ist['mdl']['toplam']:>10.0f}")
        print()

    seri = seri_oluştur(çiftler, adlar, args.en_az_katman,
                        args.türetim_eşiği, ön_dil_incelt=args.ön_dil_incelt)
    metin = rapor_üret(seri)
    html_yolu = args.html or str(pathlib.Path(args.rapor).with_suffix(".html"))
    pathlib.Path(html_yolu).write_text(html_üret(seri), encoding="utf-8")

    pathlib.Path(args.rapor).write_text(metin + "\n", encoding="utf-8")
    print(metin)
    print(f"(rapor {args.rapor} dosyasına da yazıldı)")
    print(f"(etkileşimli görünüm: {html_yolu})")


if __name__ == "__main__":
    main()

