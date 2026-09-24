# -*- coding: utf-8 -*-
"""Asgari harfli Ön Dil serisinin metin raporu."""

from sesbiçim.harf import BOŞ, SANAL_HARFLER, dizi_harfleri, dizi_mi

from .asgari import GÖÇÜŞÜM_BAĞLAMI, işaret_adı, işaret_mi, işaret_no

_SANAL = set(SANAL_HARFLER)


def _yaz(tokenler):
    return "".join(tokenler) if tokenler else "∅"


def _türetim(biçimler):
    metinler = []
    for b in biçimler:
        m = _yaz(b)
        if not metinler or metinler[-1] != m:
            metinler.append(m)
    return " > ".join(
        (m if i == len(metinler) - 1 else "*" + m) for i, m in enumerate(metinler)
    )


def katman_adı(dal_adı, j, son):
    if j == 0:
        return "Ön Dil"
    if j == son:
        return dal_adı
    return f"Ön {dal_adı} {j}"


def kural_metni(k):
    if k.bağlam == GÖÇÜŞÜM_BAĞLAMI:
        x, y = dizi_harfleri(k.kaynak)
        return f"*{x}{y} -> {y}{x}  (göçüşüm)"
    if k.hedef == BOŞ:
        hedef = "∅"
    elif dizi_mi(k.hedef):
        hedef = "".join(dizi_harfleri(k.hedef)) + "  (doğum)"
    else:
        hedef = k.hedef
    bağlam = "" if k.bağlam == "her yerde" else f"  / {k.bağlam}"
    korunur = "  (korunur)" if k.hedef == k.kaynak else ""
    return f"*{k.kaynak} -> {hedef}{bağlam}{korunur}"


def istatistik(seri):
    """Rapor ve HTML'in ortak sayıları."""
    B = len(seri.dal_adları)
    proto = sorted({t for w in seri.proto_kelimeler for t in w})
    işaretler = sorted((t for t in proto if işaret_mi(t)), key=işaret_no)
    çapalar = [t for t in proto if not işaret_mi(t)]
    dallar = []
    for d in range(B):
        L = seri.katman[d]
        katmanlar = []
        önceki = set(proto)
        for j in range(0, L + 1):
            harfler = {t for kt in seri.türevler for t in kt[d][j]}
            kurallar = seri.tablolar[d].get(j, []) if j else []
            ses = [k for k in kurallar if not işaret_mi(k.kaynak)]
            katmanlar.append({
                "j": j,
                "harf": sorted(harfler),
                "doğan": sorted(harfler - önceki) if j else [],
                "yiten": sorted(önceki - harfler) if j else [],
                "kural": len(kurallar),
                "ses_kuralı": len(ses),
                "işaret_kuralı": len(kurallar) - len(ses),
            })
            önceki = harfler
        toplam = sum(k["kural"] for k in katmanlar)
        ses = sum(k["ses_kuralı"] for k in katmanlar)
        dallar.append({
            "ad": seri.dal_adları[d],
            "katman": L,
            "ön_katman": seri.ön_katman[d],
            "kural": toplam,
            "ses_kuralı": ses,
            "ortalama": toplam / L if L else 0.0,
            "ses_ortalama": ses / L if L else 0.0,
            "katmanlar": katmanlar,
        })
    türetim = B * len(seri.çiftler)
    tüm_harf = set(proto)
    for d in range(B):
        for kt in seri.türevler:
            for b in kt[d]:
                tüm_harf |= set(b)
    toplam_kural = sum(x["kural"] for x in dallar)
    toplam_katman = sum(x["katman"] for x in dallar)
    return {
        "proto": proto,
        "çapalar": çapalar,
        "işaretler": işaretler,
        "sanal_çapa": [t for t in çapalar if t in _SANAL],
        "dallar": dallar,
        "türetim": türetim,
        "istisna": len(seri.istisnalar),
        "düzenlilik": 100.0 * (türetim - len(seri.istisnalar)) / türetim,
        "tüm_harf": len(tüm_harf),
        "toplam_kural": toplam_kural,
        "toplam_katman": toplam_katman,
        "genel_ortalama": toplam_kural / toplam_katman if toplam_katman else 0.0,
    }


def rapor_üret(seri, karşılaştırma=None):
    """karşılaştırma: klasik inşanın {harf, türetilmiş, katman, kural} özeti."""
    ist = istatistik(seri)
    adlar = list(seri.dal_adları)
    S = []
    S.append("=" * 72)
    S.append(" SANAL SAV — Asgari Harfli Ön Dil Serisi Raporu")
    S.append(f" Diller: {' ~ '.join(adlar)} (yazılış esaslı, anlam sıralı liste)")
    S.append("=" * 72)
    S.append("")
    S.append("Amaç: verilen listeleri ortak bir Ön Dil serisine EN AZ HARFLE,")
    S.append("istisnasız ve düzenli ses kurallarıyla bağlamak. Harf yerine katman")
    S.append("ve kural harcanır; her kural harf grafiğinde tek doğal adımdır.")
    S.append("")

    S.append("-" * 72)
    S.append("1. ÖZET")
    S.append("-" * 72)
    S.append(f"  dil sayısı                      : {len(adlar)}")
    S.append(f"  anlam (sözcük) sayısı           : {len(seri.çiftler)}")
    S.append(f"  Ön Dil harf dağarcığı           : {len(ist['proto'])} "
             f"(çapa {len(ist['çapalar'])} + gırtlaksıl işaret {len(ist['işaretler'])})")
    S.append("  türetilmiş (alt simgeli) harf   : 0")
    S.append("  ara katmanda etiketli harf      : 0")
    S.append(f"  en uzun ses zinciri (D)         : {seri.en_uzun_yol} adım")
    S.append("  ön dile uzaklık (katman sayısı) :")
    for x in ist["dallar"]:
        S.append(f"      {x['ad']:<14} {x['katman']} katman"
                 f" ({x['ön_katman']} işaret düşürme + "
                 f"{x['katman'] - x['ön_katman']} ses katmanı)")
    S.append("  kural sayısı                    :")
    for x in ist["dallar"]:
        S.append(f"      {x['ad']:<14} {x['kural']} kural "
                 f"({x['ses_kuralı']} ses kuralı + "
                 f"{x['kural'] - x['ses_kuralı']} işaret kuralı)")
    S.append("  KATMAN BAŞINA ORTALAMA KURAL    :")
    for x in ist["dallar"]:
        S.append(f"      {x['ad']:<14} {x['ortalama']:.2f} kural/katman "
                 f"(yalnız ses kuralı: {x['ses_ortalama']:.2f})")
    S.append(f"      {'bütün seri':<14} {ist['genel_ortalama']:.2f} kural/katman "
             f"({ist['toplam_kural']} kural / {ist['toplam_katman']} katman)")
    S.append(f"  seri boyunca toplam ayrı harf   : {ist['tüm_harf']}")
    if seri.doğum_olayları:
        S.append(f"  doğum (tek harf > çok harf)     : {len(seri.doğum_olayları)} konum")
    göç = sum(len(g) for g in seri.göçüşümler)
    S.append(f"  göçüşüm (metathesis) kuralı     : {göç}")
    S.append(f"  istisna                         : {ist['istisna']} / {ist['türetim']} türetim")
    S.append(f"  düzenlilik                      : %{ist['düzenlilik']:.1f}")
    S.append("")

    if karşılaştırma:
        k = karşılaştırma
        S.append("  Klasik inşa ile karşılaştırma (aynı listeler, eşik 1):")
        S.append(f"      {'':<22}{'klasik':>10}{'asgari':>10}")
        S.append(f"      {'Ön Dil harfi':<22}{k['harf']:>10}{len(ist['proto']):>10}")
        S.append(f"      {'türetilmiş harf':<22}{k['türetilmiş']:>10}{0:>10}")
        S.append(f"      {'ara katman etiketi':<22}{k['etiket']:>10}{0:>10}")
        S.append(f"      {'katman':<22}{k['katman']:>10}"
                 f"{' + '.join(str(x['katman']) for x in ist['dallar']):>10}")
        S.append(f"      {'kural':<22}{k['kural']:>10}{ist['toplam_kural']:>10}")
        S.append(f"      {'düzenlilik':<22}{'%' + format(k['düzenlilik'], '.1f'):>10}"
                 f"{'%' + format(ist['düzenlilik'], '.1f'):>10}")
        S.append("")

    S.append("-" * 72)
    S.append("2. ÖN DİL HARF DAĞARCIĞI (katman 0)")
    S.append("-" * 72)
    S.append("  çapa harfleri      : " + " ".join(ist["çapalar"]))
    if ist["sanal_çapa"]:
        S.append("    (sanal olanlar   : " + " ".join(ist["sanal_çapa"])
                 + " — hiçbir yazıda yok, özellik uzayından)")
    S.append("  gırtlaksıl işaret  : " + " ".join(ist["işaretler"]))
    S.append("")
    S.append("  Çapa, bir karşılıklık kümesinin özellik uzayındaki yeridir: bütün")
    S.append(f"  refleksleri ondan en çok {seri.en_uzun_yol} doğal adım uzaktadır. İşaretler")
    S.append("  Hint-Avrupa laringalleri (*h₁ *h₂ *h₃) gibi gizli gırtlak sesleridir:")
    S.append("  önlerindeki sesi 'boyar' (kural: X -> Y / H² önünde), sonra düşerler.")
    S.append("  Her birimin ardında dal sırasıyla bir işaret öbeği durur; k. dal ilk")
    S.append("  k katmanda öbek başlarını düşürüp kendi işaretine ulaşır. H⁰ yalnız")
    S.append("  yer tutucudur (o dalda boyama yok).")
    S.append("")
    S.append("  Katman başına harf dağarcığı (her katman bir alt ön dil):")
    for x in ist["dallar"]:
        parçalar = []
        for k in x["katmanlar"]:
            parçalar.append(str(len(k["harf"])) if k["j"] == 0
                            else f"{len(k['harf'])} (+{len(k['doğan'])})")
        S.append(f"    {x['ad']:<10}: " + " > ".join(parçalar))
    S.append("")
    S.append("  Çapa -> refleks izleri ve işaret sınıfları:")
    for d, ad in enumerate(adlar):
        S.append(f"    {ad} dalı:")
        for (A, R), c in sorted(seri.sınıflar[d].items(),
                                key=lambda kv: (kv[0][0], kv[1], kv[0][1])):
            z = seri.izler[d][(A, R)]
            adımlar = []
            for t in z:
                t = "∅" if t == BOŞ else ("".join(dizi_harfleri(t)) if dizi_mi(t) else t)
                if not adımlar or adımlar[-1] != t:
                    adımlar.append(t)
            işaret = "—" if c == 0 else işaret_adı(c)
            S.append(f"      *{A} [{işaret:>2}] : {' > '.join(adımlar)}")
    S.append("")

    S.append("-" * 72)
    S.append("3. SES DEĞİŞİM KURALLARI (katman katman)")
    S.append("-" * 72)
    for d, ad in enumerate(adlar):
        x = ist["dallar"][d]
        S.append(f"  {ad} dalı ({x['katman']} katman, ortalama "
                 f"{x['ortalama']:.2f} kural/katman):")
        for j in range(1, seri.katman[d] + 1):
            kurallar = seri.tablolar[d].get(j, [])
            S.append(f"    Katman {j} ({katman_adı(ad, j - 1, seri.katman[d])} -> "
                     f"{katman_adı(ad, j, seri.katman[d])}): {len(kurallar)} kural")
            for k in kurallar:
                S.append(f"      {kural_metni(k)}")
        S.append("")

    S.append("-" * 72)
    S.append("4. SÖZLÜK VE TÜRETİMLER")
    S.append("-" * 72)
    S.append("  Her satır: Ön Dil biçimi > ara Ön Dil biçimleri > çocuk dil.")
    S.append("")
    bozuk = {(kno, d) for kno, d, _, _ in seri.istisnalar}
    g = max(len(a) for a in adlar)
    for kno, row in enumerate(seri.çiftler):
        S.append(f"  {kno + 1:>3}. {row[0]}  ({' ~ '.join(row[1:])})   "
                 f"Ön Dil: *{_yaz(seri.proto_kelimeler[kno])}")
        for d, ad in enumerate(adlar):
            im = "  ✗" if (kno, d) in bozuk else ""
            S.append(f"       {ad:<{g}}: {_türetim(seri.türevler[kno][d])}{im}")
    S.append("")

    S.append("-" * 72)
    S.append("5. İSTİSNALAR")
    S.append("-" * 72)
    if not seri.istisnalar:
        S.append("  İstisna yok: bütün sözcükler yalnız kurallarla türetildi.")
    for kno, d, beklenen, bulunan in seri.istisnalar:
        S.append(f"  {kno + 1:>3}. {seri.çiftler[kno][0]} ({adlar[d]}): "
                 f"beklenen '{beklenen}', kurallar '{bulunan}' üretti")
    S.append("")

    S.append("-" * 72)
    S.append("6. ÇAPA ARAMASI (harf ~ katman ödünleşimi)")
    S.append("-" * 72)
    S.append(f"  {'harf':>4}  {'çapa':>4}  {'işaret':>6}  {'derinlik':>8}  çapa kümesi")
    for harf, n, K, derinlik, küme in seri.arama_özeti:
        S.append(f"  {harf:>4}  {n:>4}  {K:>6}  {derinlik:>8}  {' '.join(küme)}")
    S.append("  (harf = çapa + işaret (+ H⁰); derinlik = dalların katman toplamı)")
    S.append("")
    return "\n".join(S)
