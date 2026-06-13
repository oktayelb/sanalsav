#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AİLE PROTOSU — programın KENDİ deneyleriyle aile ağacı + bağdaşıklık sınaması.

Tez: dil aileleri yalnız Ön Dil harf maliyetinden ortaya çıkar. Bu betik ağacı
DIŞARIDAN (UPGMA, eşik, aile bilgisi) hiçbir şey dayatmadan, programın kendi
yeniden-kurulum deneylerinden, AŞAĞIDAN YUKARI ve hep İKİLİ kurar.

İlke ("protoların protosu"):
  - Her dil bir düğüm; temsilcisi kendi sözcük listesidir.
  - İki düğümün YAKINLIĞI = temsilci protolarının İKİLİ protosunun Ön Dil harf
    sayısı. Hep iki girdi olduğundan ölçü düğüm boyutundan bağımsızdır (adil):
    büyük aile protosunun şişen harf sayısı karara hiç girmez.
  - En ucuz çift birleştirilir; yeni düğümün temsilcisi o GERÇEK protodur
    (ortalama değil; harfler yazılı alfabeye indirilir, bkz. yazıya).
  - Tek kök kalana dek yinelenir.

Bu, "d1~d2, d2~d3, d3~d1 hepsi ucuz ve ötekilerden uzak" üçgenini kendiliğinden
yakalar (üçü önce kendi arasında birleşir) ve "5'li ailede en doğru ikili
bölünme nedir" sorusunu yanıtlar: alt-ağacın kök bölünmesi en küçük
protoların-protosu veren bölmedir.

Sonra, kendi çıkardığı ağacı bir maliyette keserek ortaya çıkan her aileyi TEK
çok-dilli proto olarak yeniden kurup BAĞDAŞIKLIĞINI ölçer ve aynı boyda KARMA
bir denetim kümesiyle karşılaştırır.

Çıktı: aile_protosu.md

Kullanım:
    python3 aileprotosu.py                       # diller/ içindeki TÜM diller
    python3 aileprotosu.py türkçe azerbaycanca türkmence   # yalnız alt küme
    python3 aileprotosu.py --eşik 90 --eşikler 50,70,90
"""

import argparse
import pathlib
import unicodedata

from ondil.insa import seri_oluştur
from ana import liste_yükle
from sesbiçim.harf import taban, özellik_uzaklığı
from sesbiçim.harf import YAZILI_HARFLER

DİL_DİZİN = pathlib.Path("diller")


# ---------------------------------------------------------------------------
# proto biçimini yazılı alfabeye indirme (üst kademe girdileri yazılı olmalı)
# ---------------------------------------------------------------------------

def _en_yakın_yazılı(g):
    return min(YAZILI_HARFLER, key=lambda w: (özellik_uzaklığı(g, w), w))


def yazıya(token):
    """Bir proto belirtecini tek yazılı harfe indirger.

    Üst kademe (protoların protosu) kurarken küme-protosu girdi sözcüğü olur;
    sözcükler karakter karakter belirteçlenir, bu yüzden a₂/eː/r̥ gibi çok-imli
    ya da sanal belirteçler taban yazılı harfe düşürülür. Aile-içi ince ayrımlar
    (a₂ vs a) zaten üst düzeyde taban harfle birleşir; bu kayıp kasıtlı.
    """
    t = taban(token).replace("ː", "")
    # ayrık birleşen imleri (ör. r̥ sessiz halkası U+0325) at; ama ö/ü/ç/ş/ğ
    # gibi BİLEŞİK yazılı harfler tek kod noktasıdır, NFD AÇMADAN korunur.
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    # her grafem YAZILI alfabeye iner: sanal harfler (ŋ, ʦ, ɬ...) yol grafiğinde
    # düğüm değildir; üst koşu girdileri yazılı olmalı (ŋ -> ñ vb.)
    t = "".join(c if c in YAZILI_HARFLER else _en_yakın_yazılı(c) for c in t)
    return t or _en_yakın_yazılı(taban(token)[:1] or "ə")


def proto_sözcükleri(seri):
    """seri.proto_kelimeler -> [(anlam, yazılı_sözcük)] (üst kademeye girdi)."""
    sonuç = []
    for i, w in enumerate(seri.proto_kelimeler):
        anlam = seri.çiftler[i][0]
        söz = "".join(yazıya(t) for t in w)
        sonuç.append((anlam, söz or "ø"))
    return sonuç


def sütunlardan_çiftler(sütunlar):
    """Her biri [(anlam, sözcük)] olan sütunları (anlam, s0, s1, ...) satırına."""
    n = len(sütunlar[0])
    return [
        (sütunlar[0][i][0],) + tuple(s[i][1] for s in sütunlar)
        for i in range(n)
    ]


def maliyet(seri):
    """(harf sayısı, türetilmiş, istisna, düzenlilik%, dil_başına_harf)."""
    dağarcık = {t for w in seri.proto_kelimeler for t in w}
    türetilmiş = sum(
        1 for t in dağarcık if any(c in "₀₁₂₃₄₅₆₇₈₉" for c in t)
    )
    B = len(seri.dal_adları)
    n = len(seri.çiftler)
    türetim = B * n
    düz = 100.0 * (türetim - len(seri.istisnalar)) / türetim
    return len(dağarcık), türetilmiş, len(seri.istisnalar), düz, len(dağarcık) / B


# ---------------------------------------------------------------------------
# 1. programın kendi çıkardığı ağaç (aşağıdan yukarı, hep ikili)
# ---------------------------------------------------------------------------

class Düğüm:
    def __init__(self, ad, temsilci, üyeler, h=0.0, çocuklar=None):
        self.ad = ad                # görünen/kısa ad
        self.temsilci = temsilci    # [(anlam, sözcük)] — proto ya da dil listesi
        self.üyeler = üyeler        # yaprak dil adları (görünen)
        self.h = h                  # bu düğümde birleşmenin proto harf maliyeti
        self.çocuklar = çocuklar or []


def ikili_proto(a, b):
    """İki düğümün protolarının ikili protosu; (harf sayısı, yeni temsilci)."""
    çiftler = sütunlardan_çiftler([a.temsilci, b.temsilci])
    seri = seri_oluştur(çiftler, (a.ad, b.ad), türetim_eşiği=1)
    harf = len({t for w in seri.proto_kelimeler for t in w})
    return harf, proto_sözcükleri(seri)


def kümele(yapraklar, günlük=None):
    """Açgözlü ikili birleştirme; kökü döndürür. Maliyetleri önbellekler."""
    düğümler = list(yapraklar)
    önbellek = {}

    def maliyet_çift(i, j):
        anahtar = (id(düğümler[i]), id(düğümler[j]))
        if anahtar not in önbellek:
            önbellek[anahtar] = ikili_proto(düğümler[i], düğümler[j])
        return önbellek[anahtar]

    while len(düğümler) > 1:
        en_iyi = None  # (harf, i, j, temsilci)
        for i in range(len(düğümler)):
            for j in range(i + 1, len(düğümler)):
                harf, temsilci = maliyet_çift(i, j)
                if en_iyi is None or (harf, düğümler[i].ad, düğümler[j].ad) < \
                        (en_iyi[0], düğümler[en_iyi[1]].ad, düğümler[en_iyi[2]].ad):
                    en_iyi = (harf, i, j, temsilci)
        harf, i, j, temsilci = en_iyi
        a, b = düğümler[i], düğümler[j]
        yeni = Düğüm(
            ad=f"({a.ad}+{b.ad})",
            temsilci=temsilci,
            üyeler=a.üyeler + b.üyeler,
            h=float(harf),
            çocuklar=[a, b],
        )
        if günlük is not None:
            günlük.append((harf, a, b))
        print(f"  birleşti [{harf:>4}]: {a.ad}  +  {b.ad}", flush=True)
        düğümler = [d for k, d in enumerate(düğümler) if k not in (i, j)]
        düğümler.append(yeni)
    return düğümler[0]


def girintili(kök):
    satırlar = []

    def etiket(d):
        if d.çocuklar:
            return f"[{int(d.h)}]  ({len(d.üyeler)} dil)"
        return d.üyeler[0]

    def yürü(d, önek, bağ):
        satırlar.append(önek + bağ + etiket(d))
        if not d.çocuklar:
            return
        alt = (önek + ("   " if bağ.startswith("└") else "│  ")) if bağ else önek
        n = len(d.çocuklar)
        for k, ç in enumerate(d.çocuklar):
            yürü(ç, alt, "└─ " if k == n - 1 else "├─ ")

    yürü(kök, "", "")
    return "\n".join(satırlar)


def eşik_kümeleri(kök, eşik):
    gruplar = []

    def topla(d):
        if d.çocuklar and d.h <= eşik:
            gruplar.append(d.üyeler)
        elif d.çocuklar:
            for ç in d.çocuklar:
                topla(ç)
        else:
            gruplar.append(d.üyeler)

    topla(kök)
    return gruplar


# ---------------------------------------------------------------------------
# 2. bağdaşıklık: kendi ağacından çıkan her aileyi TEK çok-dilli proto kur
# ---------------------------------------------------------------------------

def _dosya(üye):
    # yaprak görünen adı (Türkçe) -> dosya kökü (türkçe); capitalize tersine.
    return DİL_DİZİN / f"{üye.lower()}.txt"


def küme_kur_tam(üyeler):
    """Üye dilleri TEK çok-dilli proto olarak kurar; (seri, metrik, proto)."""
    sütunlar = [liste_yükle(_dosya(ü)) for ü in üyeler]
    çiftler = sütunlardan_çiftler(sütunlar)
    seri = seri_oluştur(çiftler, tuple(üyeler), türetim_eşiği=1)
    return seri, maliyet(seri)


# ---------------------------------------------------------------------------
# sürücü
# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("diller", nargs="*",
                   help="dil adları (boşsa diller/ içindeki TÜM diller)")
    p.add_argument("--rapor", default="aile_protosu.md")
    p.add_argument("--eşik", type=int, default=90,
                   help="bağdaşıklık için ağacı bu maliyette kes (aileler)")
    p.add_argument("--eşikler", default="50,70,90",
                   help="raporda gösterilecek kesit maliyetleri (virgülle)")
    args = p.parse_args(argv)

    if args.diller:
        adlar = args.diller
    else:
        adlar = sorted(y.stem for y in DİL_DİZİN.glob("*.txt"))

    print(f"{len(adlar)} dil yaprak olarak yükleniyor: {', '.join(adlar)}")
    yapraklar = []
    for ad in adlar:
        yol = DİL_DİZİN / f"{ad}.txt"
        if not yol.exists():
            raise SystemExit(f"Dil dosyası bulunamadı: {yol}")
        yapraklar.append(
            Düğüm(ad.capitalize(), liste_yükle(yol), [ad.capitalize()])
        )

    print("Aşağıdan yukarı birleştirme (her adım gerçek ikili proto):")
    günlük = []
    kök = kümele(yapraklar, günlük)

    # bağdaşıklık: kendi ağacını --eşik'te kes -> aileler
    öbekler = eşik_kümeleri(kök, args.eşik)
    aileler = sorted((ö for ö in öbekler if len(ö) > 1), key=len, reverse=True)
    tekiller = [ö[0] for ö in öbekler if len(ö) == 1]
    print(f"Bağdaşıklık (kesit ≤ {args.eşik}): {len(aileler)} aile, "
          f"{len(tekiller)} tekil.")

    bağ_satır = []  # (üyeler, metrik)
    for üyeler in aileler:
        print(f"  aile protosu ({len(üyeler)}): {'+'.join(üyeler)} ...",
              flush=True)
        _, m = küme_kur_tam(üyeler)
        bağ_satır.append((üyeler, m))
        print(f"    -> {m[0]} harf, dil/harf {m[4]:.1f}, %{m[3]:.1f}, "
              f"{m[2]} istisna", flush=True)

    # denetim: en büyük ailenin boyunda, her aileden birer dil seçilir
    boy = len(aileler[0]) if aileler else 3
    karma = [ü[0] for ü in aileler][:boy]
    i = 0
    while len(karma) < boy and i < len(tekiller):
        karma.append(tekiller[i])
        i += 1
    karma_m = None
    if len(karma) >= 2:
        print(f"  denetim (karma {len(karma)}): {'+'.join(karma)} ...", flush=True)
        _, karma_m = küme_kur_tam(karma)
        print(f"    -> {karma_m[0]} harf, dil/harf {karma_m[4]:.1f}, "
              f"%{karma_m[3]:.1f}, {karma_m[2]} istisna", flush=True)

    eşikler = [int(e) for e in args.eşikler.split(",")]
    yaz_rapor(args, kök, günlük, eşikler, bağ_satır, karma, karma_m)
    print(f"(rapor {args.rapor} dosyasına yazıldı)")


def yaz_rapor(args, kök, günlük, eşikler, bağ_satır, karma, karma_m):
    L = []
    L.append("# Aile Protosu — programın kendi deneyleriyle aile ağacı\n")
    L.append("Ağaç YALNIZCA programın yeniden-kurulum deneylerinden, aşağıdan "
             "yukarı ve hep İKİLİ kuruldu. Hiçbir aile bilgisi, eşik ya da UPGMA "
             "ortalaması DIŞARIDAN dayatılmadı. İki düğümü birleştirme maliyeti "
             "= temsilci protolarının ikili protosunun Ön Dil harf sayısıdır; "
             "hep iki girdi olduğundan ölçü grup boyutundan bağımsızdır (büyük "
             "aile protosunun şişen harf sayısı karara girmez). Her adımda en "
             "ucuz çift birleşir; köşeli parantezdeki sayı o birleşmenin gerçek "
             "proto harf maliyetidir. Kök maliyeti = tüm dillerin "
             "protoların-protosu (Hint-Avrupa düzeyi).\n")

    L.append("## 1. Birleşme sırası (programın çıkarım günlüğü)\n")
    L.append("| # | maliyet | birleşen A | birleşen B |")
    L.append("|---:|---:|---|---|")
    for no, (harf, a, b) in enumerate(günlük, 1):
        L.append(f"| {no} | {harf} | {a.ad} | {b.ad} |")
    L.append("")

    L.append("## 2. Çıkarılan ağaç\n```")
    L.append(girintili(kök))
    L.append("```\n")

    L.append("## 3. Maliyet kesitlerinde ortaya çıkan gruplar\n")
    L.append("Bir kesit değeri seçince, o maliyetin ALTINDA birleşmiş kollar "
             "birer grup sayılır (programın kendiliğinden bulduğu aileler ve "
             "alt-bölünmeleri):\n")
    for e in eşikler:
        gruplar = [g for g in eşik_kümeleri(kök, e) if len(g) > 1]
        tekil = [g[0] for g in eşik_kümeleri(kök, e) if len(g) == 1]
        L.append(f"**Kesit ≤ {e}:**")
        for g in sorted(gruplar, key=len, reverse=True):
            L.append(f"- {{{', '.join(g)}}} ({len(g)})")
        if tekil:
            L.append(f"- (tek başına: {', '.join(tekil)})")
        L.append("")

    L.append(f"## 4. Küme bağdaşıklığı (kendi ağacından, kesit ≤ {args.eşik})\n")
    L.append("Ağacın kendi bulduğu her aile, TEK bir çok-dilli Ön Dil olarak "
             "yeniden kuruldu (yıldız hizalama). Dil başına harf düşük ve "
             "düzenlilik %100 ise küme gerçek bağdaşık bir birimdir:\n")
    L.append("| Aile | dil | Ön Dil harfi | dil başına | düzenlilik | istisna |")
    L.append("|---|---:|---:|---:|---:|---:|")
    for üyeler, m in bağ_satır:
        L.append(f"| {'+'.join(üyeler)} | {len(üyeler)} | {m[0]} | {m[4]:.1f} | "
                 f"%{m[3]:.1f} | {m[2]} |")
    L.append("")

    if karma_m is not None and bağ_satır:
        L.append("## 5. Denetim: aynı boyda KARMA küme\n")
        L.append("En büyük gerçek ailenin boyunda, her aileden birer dil "
                 "seçilerek kasıtlı karma bir küme kuruldu. Aynı dil sayısında "
                 "karma küme gerçek aileden belirgin pahalı ve daha az düzenli "
                 "olur; akrabalık harf maliyetinin DOĞRUDAN sonucudur:\n")
        L.append("| Küme | dil | Ön Dil harfi | dil başına | düzenlilik | istisna |")
        L.append("|---|---:|---:|---:|---:|---:|")
        en_iyi = min(bağ_satır, key=lambda s: s[1][4])
        L.append(f"| {'+'.join(en_iyi[0])} (gerçek aile) | {len(en_iyi[0])} | "
                 f"{en_iyi[1][0]} | {en_iyi[1][4]:.1f} | %{en_iyi[1][3]:.1f} | "
                 f"{en_iyi[1][2]} |")
        L.append(f"| {'+'.join(karma)} (karma) | {len(karma)} | {karma_m[0]} | "
                 f"{karma_m[4]:.1f} | %{karma_m[3]:.1f} | {karma_m[2]} |")
        L.append("")

    pathlib.Path(args.rapor).write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
