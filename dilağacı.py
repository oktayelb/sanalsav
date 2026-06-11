#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dil ailesi ağacı — harf-sayısı mesafelerinden hiyerarşik kümeleme.

`tüm_diller.md` içindeki Ön Dil harf-sayısı matrisini (diller arası akrabalık
maliyeti) okur ve UPGMA (ağırlıklı ortalama bağlantılı hiyerarşik kümeleme) ile
bir ağaç kurar. HİÇBİR dil-ailesi bilgisi koda girmez; gruplama tamamen harf
maliyetinden doğar. Çıktı: girintili ağaç, yatay ASCII dendrogram ve eşik
kesitleri; hem ekrana yazılır hem de bir markdown dosyasına kaydedilir.

Kullanım:
    python3 dilağacı.py [matris.md] [--çıktı dil_ağacı.md]

Matris dosyası, `ana.py --tarama` benzeri akışla üretilen `tüm_diller.md`
biçimindedir: kod başlıklı bir markdown tablosu (köşegen "—").
"""

import argparse
import pathlib

# Matris başlığındaki kısa kodları görünen adlara çevirir (yalnız etikettir;
# gruplama bu adlardan değil, sayısal mesafelerden çıkar).
KOD2AD = {
    "Tür": "Türkçe", "Aze": "Azerice", "Tkm": "Türkmence", "Gag": "Gagavuzca",
    "Kaz": "Kazakça", "Est": "Estonca", "Fin": "Fince", "Mac": "Macarca",
    "Alm": "Almanca", "İng": "İngilizce", "Hol": "Hollandaca", "İsv": "İsveççe",
    "Rom": "Romence", "İsp": "İspanyolca", "İta": "İtalyanca", "Fra": "Fransızca",
    "Por": "Portekizce", "Tac": "Tacikçe", "Kür": "Kürtçe", "Arn": "Arnavutça",
    "Lit": "Litvanca", "Slv": "Slovence", "Hır": "Hırvatça", "Boş": "Boşnakça",
    "Slk": "Slovakça", "Leh": "Lehçe", "Çek": "Çekçe",
}

EŞİKLER = (60, 75, 90, 100)  # otomatik küme (ortaya çıkan aile) kesitleri


class Düğüm:
    """Kümeleme ağacının bir düğümü (yaprak ya da iç grup)."""

    def __init__(self, ad=None, çocuklar=None, h=0.0, üyeler=None):
        self.ad = ad
        self.çocuklar = çocuklar or []
        self.h = h  # bu düğümde birleşen iki (alt)grubun ortalama harf mesafesi
        self.üyeler = üyeler if üyeler is not None else [ad]


# ---------------------------------------------------------------------------
# 1. matrisi ayrıştır
# ---------------------------------------------------------------------------

def matris_oku(yol):
    """Markdown harf-maliyeti tablosunu {(kod, kod): mesafe} sözlüğüne çevirir."""
    satırlar = pathlib.Path(yol).read_text(encoding="utf-8").splitlines()
    başlık_no = next(
        i for i, s in enumerate(satırlar)
        if s.startswith("| |") and "Tür" in s
    )
    kodlar = [c.strip() for c in satırlar[başlık_no].strip().strip("|").split("|")][1:]
    D = {}
    for satır in satırlar[başlık_no + 2: başlık_no + 2 + len(kodlar)]:
        hücreler = [c.strip() for c in satır.strip().strip("|").split("|")]
        a = hücreler[0].replace("*", "").strip()
        for kod, v in zip(kodlar, hücreler[1:]):
            if v != "—":
                D[(a, kod)] = float(int(v))
    return kodlar, D


# ---------------------------------------------------------------------------
# 2. UPGMA hiyerarşik kümeleme
# ---------------------------------------------------------------------------

def upgma(kodlar, D):
    """En yakın iki kümeyi yinelemeli birleştirir; ağacın kökünü döndürür.

    Küme mesafesi = üye sayısına göre ağırlıklı ortalama (UPGMA): birleşince
    yeni kümenin k'ye uzaklığı (n_i·d_ik + n_j·d_jk)/(n_i+n_j) olur.
    """
    kümeler = {k: Düğüm(ad=k, üyeler=[k]) for k in kodlar}
    dist = {(a, b): D[(a, b)] for a in kodlar for b in kodlar if a != b}
    boy = {k: 1 for k in kodlar}
    aktif = list(kodlar)
    while len(aktif) > 1:
        i, j = min(
            ((a, b) for x, a in enumerate(aktif) for b in aktif[x + 1:]),
            key=lambda p: dist[p],
        )
        d = dist[(i, j)]
        yeni = f"({i},{j})"
        kümeler[yeni] = Düğüm(
            ad=yeni, çocuklar=[kümeler[i], kümeler[j]], h=d,
            üyeler=kümeler[i].üyeler + kümeler[j].üyeler,
        )
        ni, nj = boy[i], boy[j]
        for k in aktif:
            if k in (i, j):
                continue
            nd = (ni * dist[(i, k)] + nj * dist[(j, k)]) / (ni + nj)
            dist[(yeni, k)] = dist[(k, yeni)] = nd
        aktif.remove(i)
        aktif.remove(j)
        aktif.append(yeni)
        boy[yeni] = ni + nj
    return kümeler[aktif[0]]


# ---------------------------------------------------------------------------
# 3. görselleştirme
# ---------------------------------------------------------------------------

def girintili_ağaç(kök):
    """Kutu-çizim karakterleriyle girintili ağaç satırları üretir."""
    çıktı = []

    def yaz(d, önek="", son=True, kök_mü=False):
        bağ = "" if kök_mü else ("└─ " if son else "├─ ")
        if d.çocuklar:
            çıktı.append(önek + bağ + f"[{d.h:.0f}]  ({len(d.üyeler)} dil)")
            alt = önek + ("   " if son else "│  ")
            for k, ç in enumerate(d.çocuklar):
                yaz(ç, alt, k == len(d.çocuklar) - 1)
        else:
            çıktı.append(önek + bağ + KOD2AD[d.ad])

    yaz(kök, kök_mü=True)
    return çıktı


def yatay_dendrogram(kök, en=46):
    """Sola=yakın, sağa=uzak akrabalık; birleşmeler harf mesafesine göre konumlu."""
    yaprak_sıra = []

    def yaprakları(d):
        if d.çocuklar:
            for ç in d.çocuklar:
                yaprakları(ç)
        else:
            yaprak_sıra.append(d.ad)

    yaprakları(kök)
    satır_no = {ad: i * 2 for i, ad in enumerate(yaprak_sıra)}
    boy_g = len(yaprak_sıra) * 2 - 1
    hmax = kök.h
    alan = max(len(KOD2AD[k]) for k in yaprak_sıra) + 1
    grid = [[" "] * (alan + en + 2) for _ in range(boy_g)]

    def x_of(h):
        return alan + int(round(h / hmax * (en - 1)))

    def çiz(d):
        if not d.çocuklar:
            y = satır_no[d.ad]
            for k, c in enumerate(KOD2AD[d.ad]):
                grid[y][k] = c
            for x in range(alan, x_of(0) + 1):
                if grid[y][x] == " ":
                    grid[y][x] = "─"
            return y, x_of(0)
        ylar, xlar = [], []
        for ç in d.çocuklar:
            yy, xx = çiz(ç)
            ylar.append(yy)
            xlar.append(xx)
        xn = x_of(d.h)
        for yy, xx in zip(ylar, xlar):
            for x in range(xx, xn + 1):
                if grid[yy][x] == " ":
                    grid[yy][x] = "─"
        for y in range(min(ylar), max(ylar) + 1):
            if grid[y][xn] == " ":
                grid[y][xn] = "│"
            elif grid[y][xn] == "─":
                grid[y][xn] = "┼"
        return (min(ylar) + max(ylar)) // 2, xn

    çiz(kök)
    return "\n".join("".join(r).rstrip() for r in grid), hmax


def eşik_kümeleri(kök, eşik):
    """Verilen mesafenin altında kalan (yani o eşikte 'aynı' sayılan) kümeler."""
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


def _ad_listesi(üyeler):
    return " ".join(KOD2AD[m] for m in üyeler)


# ---------------------------------------------------------------------------
# ana akış
# ---------------------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("matris", nargs="?", default="tüm_diller.md",
                   help="harf-maliyeti matrisini içeren markdown dosyası")
    p.add_argument("--çıktı", default="dil_ağacı.md", help="kaydedilecek dosya")
    args = p.parse_args(argv)

    kodlar, D = matris_oku(args.matris)
    kök = upgma(kodlar, D)
    ağaç = girintili_ağaç(kök)
    dendro, hmax = yatay_dendrogram(kök)

    S = ["# Dil Ailesi Ağacı (harf-sayısı mesafelerinden, UPGMA)", ""]
    S.append(f"Kaynak matris: `{args.matris}` ({len(kodlar)} dil). Bu ağaç YALNIZCA")
    S.append("Ön Dil harf-sayısı mesafelerinden üretilmiştir; hiçbir dil-ailesi")
    S.append("bilgisi koda girilmemiştir. Yöntem: ağırlıklı ortalama bağlantılı")
    S.append("hiyerarşik kümeleme (UPGMA). Her iç düğüm bir GRUPtur; üst düğümler")
    S.append("grupların gruplarıdır (en üstte tüm diller). Köşeli parantezdeki sayı,")
    S.append("o iki (alt)grubun birleştiği ortalama harf mesafesidir.")
    S.append("")
    S.append("## Girintili ağaç")
    S.append("```")
    S += ağaç
    S.append("```")
    S.append("")
    S.append("## Yatay dendrogram")
    S.append("```")
    S.append(dendro)
    S.append(f"\n(sola = yakın akraba; sağa = uzak. en sağ ≈ {hmax:.0f} harf)")
    S.append("```")
    S.append("")
    S.append("## Eşik kesitleri (otomatik küme = ortaya çıkan aile)")
    for e in EŞİKLER:
        g = [_ad_listesi(u) for u in eşik_kümeleri(kök, e) if len(u) > 1]
        S.append(f"\n**mesafe ≤ {e}** → {len(g)} çok-üyeli küme:")
        for u in g:
            S.append(f"- {u}")
    S.append("")
    S.append("## Not")
    S.append("Kümeler bilinen dil aileleriyle örtüşür (Türk, Roman, Germen, Slav,")
    S.append("Ural...) ama bu örtüşme GİRDİ DEĞİL, SONUÇtur: yalnız harf maliyetinden")
    S.append("çıkmıştır. Mutlak mesafelerde bir taban bulunduğundan (akraba olmayan")
    S.append("çiftler bile ~90+), yöntem her sıkı aileyi net çeker ama üst-aileleri")
    S.append("(ör. Hint-Avrupa'yı Ural'dan) tam ayıramaz; köşegen bloklar ailedir,")
    S.append("en üstteki büyük birleşme ise Hint-Avrupa + Ural süper-grubudur.")

    metin = "\n".join(S) + "\n"
    pathlib.Path(args.çıktı).write_text(metin, encoding="utf-8")

    # ekrana da yaz
    print("\n".join(ağaç))
    print("\n" + dendro)
    print(f"\n(ölçek: en sağ ≈ {hmax:.0f} harf)")
    print(f"\n(ağaç {args.çıktı} dosyasına yazıldı)")


if __name__ == "__main__":
    main()
