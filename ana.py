#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SANAL SAV — verilen iki sözcük listesinden varsayımsal Ön Dil serisi kurar.

Kullanım:
    python3 ana.py [dil1_dosyası] [dil2_dosyası] [--rapor rapor.txt]

Dosya biçimi: her satırda "anlam<boşluk>sözcük"; iki dosya aynı anlam
sırasını izlemelidir (bkz. diller/README.md). Varsayılan olarak Türkçe ve
İngilizce Swadesh-100 listeleri kullanılır.
"""

import argparse
import pathlib
import sys

from sesbiçim.harf import HARFLER
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
    bilinmeyen = sorted({h for s in sözcükler for h in s if h not in HARFLER})
    if bilinmeyen:
        raise SystemExit(
            f"{ad}: sesbiçim tablolarında tanımsız harf(ler): "
            + " ".join(bilinmeyen)
        )


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dil1", nargs="?", default="diller/türkçe.txt")
    p.add_argument("dil2", nargs="?", default="diller/ingilizce.txt")
    p.add_argument("--ad1", default=None, help="1. dilin görünen adı")
    p.add_argument("--ad2", default=None, help="2. dilin görünen adı")
    p.add_argument("--rapor", default="rapor.txt", help="rapor dosyası")
    p.add_argument("--en-az-katman", type=int, default=0,
                   help="dallar için en az katman sayısı")
    args = p.parse_args(argv)

    ad1 = args.ad1 or pathlib.Path(args.dil1).stem.capitalize()
    ad2 = args.ad2 or pathlib.Path(args.dil2).stem.capitalize()

    l1 = liste_yükle(args.dil1)
    l2 = liste_yükle(args.dil2)
    if len(l1) != len(l2):
        raise SystemExit(
            f"Listeler aynı uzunlukta olmalı: {len(l1)} != {len(l2)}"
        )
    for (a1, _), (a2, _) in zip(l1, l2):
        if a1 != a2:
            print(f"uyarı: anlam etiketi uyuşmuyor: {a1!r} ~ {a2!r}",
                  file=sys.stderr)

    harfleri_doğrula(ad1, [s for _, s in l1])
    harfleri_doğrula(ad2, [s for _, s in l2])

    çiftler = [(a1, s1, s2) for (a1, s1), (_, s2) in zip(l1, l2)]
    seri = seri_oluştur(çiftler, (ad1, ad2), args.en_az_katman)
    metin = rapor_üret(seri)

    pathlib.Path(args.rapor).write_text(metin + "\n", encoding="utf-8")
    print(metin)
    print(f"(rapor {args.rapor} dosyasına da yazıldı)")


if __name__ == "__main__":
    main()
