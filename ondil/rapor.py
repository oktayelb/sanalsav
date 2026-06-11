# -*- coding: utf-8 -*-
"""Ön Dil serisi sonuç raporu üretimi."""

from sesbiçim.harf import BOŞ, SANAL_HARFLER, dizi_harfleri, dizi_mi, taban

from .insa import DALLAR


def _biçim_yaz(tokenler):
    return "".join(tokenler) if tokenler else "∅"


def _türetim_satırı(biçimler, son_yıldızsız=True):
    metinler = []
    for b in biçimler:
        m = _biçim_yaz(b)
        if not metinler or metinler[-1] != m:
            metinler.append(m)
    parçalar = []
    for i, m in enumerate(metinler):
        son = i == len(metinler) - 1
        parçalar.append(m if (son and son_yıldızsız) else "*" + m)
    return " > ".join(parçalar)


def _katman_adı(dal_adı, j, son_katman):
    if j == 0:
        return "Ön Dil"
    if j == son_katman:
        return dal_adı
    return f"Ön {dal_adı} {j}"


def rapor_üret(seri):
    S = []
    ad0, ad1 = seri.dal_adları
    n = len(seri.çiftler)

    # --- istatistikler ---
    proto_dağarcık = sorted({t for w in seri.proto_kelimeler for t in w})
    temel = [t for t in proto_dağarcık if t == taban(t)]
    türetilmiş = [t for t in proto_dağarcık if t != taban(t)]
    kural_sayısı = []
    bağlamlı = []
    korunma = []
    for dal in DALLAR:
        kurallar = [k for j in seri.tablolar[dal] for k in seri.tablolar[dal][j]]
        değişim = [k for k in kurallar if k.hedef != k.kaynak]
        kural_sayısı.append(len(değişim))
        korunma.append(len(kurallar) - len(değişim))
        bağlamlı.append(sum(1 for k in değişim if k.bağlam != "her yerde"))
    istisna = len(seri.istisnalar)
    düzenlilik = 100.0 * (2 * n - istisna) / (2 * n)

    S.append("=" * 72)
    S.append(" SANAL SAV — Varsayımsal Ön Dil Serisi Raporu")
    S.append(f" Diller: {ad0} ~ {ad1} (yazılış esaslı, anlam sıralı liste)")
    S.append("=" * 72)
    S.append("")
    S.append("Bu rapor gerçek bir etimoloji savı DEĞİLDİR. Amaç, verilen iki")
    S.append("sözcük listesini düzenli ses değişim kurallarıyla ortak bir Ön Dil")
    S.append("serisine bağlamanın hesaplamayla her zaman mümkün olduğunu ve bu")
    S.append("bağlamanın MALİYETİNİN (türetilen harf ve kural sayısının) gerçek")
    S.append("akrabalık için bir ölçü olarak kullanılabileceğini göstermektir.")
    S.append("")

    S.append("-" * 72)
    S.append("1. ÖZET")
    S.append("-" * 72)
    kural_dışı_tür = sum(len(d) for d in seri.düzensiz)
    kural_dışı_konum = sum(
        len(seri.korr_yerleri[ç]) for dal in (0, 1) for ç in seri.düzensiz[dal]
    )
    S.append(f"  sözcük çifti                    : {n}")
    S.append(f"  harf karşılıklığı türü          : {len(seri.atama)}")
    S.append(f"  türetim eşiği (tutumluluk)      : {seri.türetim_eşiği} "
             f"(yeni harf en az bu kadar konumu kurtarmalı)")
    S.append(f"  kural dışı bırakılan            : {kural_dışı_tür} karşılıklık türü, "
             f"{kural_dışı_konum} konum")
    S.append(f"  Ön Dil harf dağarcığı           : {len(proto_dağarcık)} "
             f"(temel {len(temel)} + türetilmiş {len(türetilmiş)})")
    S.append(f"  katman sayısı                   : {ad0} dalı {seri.katman[0]}, "
             f"{ad1} dalı {seri.katman[1]}")
    S.append(f"  ses değişim kuralı              : {ad0} dalı {kural_sayısı[0]} "
             f"({bağlamlı[0]} bağlamlı, +{korunma[0]} korunma), "
             f"{ad1} dalı {kural_sayısı[1]} "
             f"({bağlamlı[1]} bağlamlı, +{korunma[1]} korunma)")
    S.append(f"  göçüşüm (metathesis) kuralı     : {len(set(ç for _, _, ç in seri.metatez_olayları))}")
    doğum_kuralı = sum(
        1
        for dal in DALLAR
        for j in seri.tablolar[dal]
        for k in seri.tablolar[dal][j]
        if dizi_mi(k.hedef)
    )
    S.append(f"  doğum (tek harf > çok harf)     : {doğum_kuralı} kural, "
             f"{len(seri.doğum_olayları)} konum (yalnız uzun ünlüler)")
    S.append(f"  ara katmanda doğan ayrım harfi  : {seri.etiketli_sayısı} "
             f"(katmanlara dağılmış; ortak ön ek paylaşılır)")
    S.append(f"  istisna                         : {istisna} / {2 * n} türetim")
    S.append(f"  düzenlilik                      : %{düzenlilik:.1f}")
    S.append("")

    S.append("-" * 72)
    S.append("2. ÖN DİL HARF DAĞARCIĞI (katman 0)")
    S.append("-" * 72)
    sıklık = {}
    for w in seri.proto_kelimeler:
        for t in w:
            sıklık[t] = sıklık.get(t, 0) + 1
    sanal_küme = set(SANAL_HARFLER)
    yazılı_temel = [t for t in temel if t not in sanal_küme]
    sanal_temel = [t for t in temel if t in sanal_küme]
    S.append("  temel harfler      : " + " ".join(yazılı_temel))
    if sanal_temel:
        S.append("  sanal harfler      : " + " ".join(sanal_temel)
                 + "   (hiçbir yazıda yok; özellik uzayından kurulan sınıflar)")
    if türetilmiş:
        S.append("  türetilmiş harfler : " + " ".join(türetilmiş))
        S.append("")
        S.append("  (Bütün Ön Dil harfleri soyuttur: her biri, kurallı biçimde bir")
        S.append("   arada yaşayabilen karşılıklıkların kümesidir. Alt simgeli harf,")
        S.append("   özellik uzayında aynı çapaya oturmak zorunda kalmış İKİNCİ bir")
        S.append("   kümedir; sayısının yüksekliği, listeleri ortak atadan düzenli")
        S.append("   ses değişimiyle türetmenin 'pahalı' olduğunu gösterir.)")
    S.append("")

    # --- katman dağarcık boyutları (her katman bir "alt ön dil") ---
    # Her katmanın kendi harf dağarcığı vardır; bir harfin ön dilde bulunması
    # gerekmez, gerçekte ilk kullanıldığı (doğduğu) katmanda sayılır. Aşağıda
    # her katmanın harf sayısı ve o katmanda DOĞAN (önceki katmanda olmayan)
    # harf sayısı verilir.
    S.append("  Katman başına harf dağarcığı (her katman bir alt ön dil):")
    seri_harfleri = set()
    for dal, ad in ((0, ad0), (1, ad1)):
        katman_kümeleri = []
        for j in range(seri.katman[dal] + 1):
            harfler = {t for kt in seri.türevler for t in kt[dal][j]}
            katman_kümeleri.append(harfler)
            seri_harfleri |= harfler
        parçalar = []
        for j, küme in enumerate(katman_kümeleri):
            if j == 0:
                parçalar.append(str(len(küme)))
            else:
                doğan = len(küme - katman_kümeleri[j - 1])
                parçalar.append(f"{len(küme)} (+{doğan} doğan)")
        S.append(f"    {ad:<10}: " + " > ".join(parçalar))
    S.append(f"    seri boyunca toplam ayrı harf: {len(seri_harfleri)}")
    S.append("")

    S.append("-" * 72)
    S.append("3. SES DEĞİŞİM KURALLARI")
    S.append("-" * 72)
    if seri.metatez_olayları:
        S.append(f"  Göçüşüm ({ad1} dalı, katman 1 öncesi):")
        for ç in sorted({ç for _, _, ç in seri.metatez_olayları}):
            S.append(f"    *{ç[0]}{ç[1]} -> {ç[1]}{ç[0]}")
        S.append("")
    for dal, ad in ((0, ad0), (1, ad1)):
        S.append(f"  {ad} dalı:")
        for j in range(1, seri.katman[dal] + 1):
            kurallar = seri.tablolar[dal].get(j, [])
            if not kurallar:
                continue
            kaynak_adı = _katman_adı(ad, j - 1, seri.katman[dal])
            hedef_adı = _katman_adı(ad, j, seri.katman[dal])
            S.append(f"    Katman {j} ({kaynak_adı} -> {hedef_adı}): "
                     f"{len(kurallar)} kural")
            for k in kurallar:
                if k.hedef == BOŞ:
                    hedef, not_ = "∅", ""
                elif dizi_mi(k.hedef):
                    hedef = "".join(dizi_harfleri(k.hedef))
                    not_ = "  (doğum: tek harften çok harf)"
                else:
                    hedef = k.hedef
                    not_ = "  (korunur)" if k.hedef == k.kaynak else ""
                bağlam = "" if k.bağlam == "her yerde" else f"  / {k.bağlam}"
                S.append(f"      *{k.kaynak} -> {hedef}{bağlam}{not_}")
        S.append("")

    S.append("-" * 72)
    S.append("4. SÖZLÜK VE TÜRETİMLER")
    S.append("-" * 72)
    S.append("  Her satır: Ön Dil biçimi > ara Ön Dil biçimleri > çocuk dil.")
    S.append("  (✗ imli türetimler kural dışı karşılıklık içerir; 5. bölüm.)")
    S.append("")
    bozuklar = {(kno, dal) for kno, dal, _, _ in seri.istisnalar}
    for kno, (anlam, a, b) in enumerate(seri.çiftler):
        proto = "*" + _biçim_yaz(seri.proto_kelimeler[kno])
        S.append(f"  {kno + 1:>3}. {anlam}  ({a} ~ {b})   Ön Dil: {proto}")
        for dal, ad in ((0, ad0), (1, ad1)):
            im = "  ✗" if (kno, dal) in bozuklar else ""
            S.append(f"       {ad:<9}: "
                     f"{_türetim_satırı(seri.türevler[kno][dal])}{im}")
    S.append("")

    S.append("-" * 72)
    S.append("5. İSTİSNALAR")
    S.append("-" * 72)
    if not seri.istisnalar:
        S.append("  İstisna yok: bütün sözcükler yalnız kurallarla türetildi.")
    else:
        for kno, dal, beklenen, bulunan in seri.istisnalar:
            ad = seri.dal_adları[dal]
            S.append(f"  {kno + 1:>3}. {seri.çiftler[kno][0]} ({ad}): "
                     f"beklenen '{beklenen}', kurallar '{bulunan}' üretti")
    S.append("")

    S.append("-" * 72)
    S.append("6. DEĞERLENDİRME")
    S.append("-" * 72)
    oran = 100.0 * len(türetilmiş) / max(1, len(proto_dağarcık))
    S.append(f"  Ön Dil dağarcığının %{oran:.0f} kadarı türetilmiş (zorlama) harftir")
    S.append(f"  ve {ad0} ile {ad1} listelerini ortak ataya bağlamak için toplam")
    S.append(f"  {kural_sayısı[0] + kural_sayısı[1]} kural gerekmiştir. Tutumluluk eşiği yükseltildikçe harf")
    S.append("  sayısı düşer ama düzenlilik de düşer: harf sayısı ile istisna")
    S.append("  sayısı arasındaki bu ödünleşim eğrisi (bkz. --tarama) iki listenin")
    S.append("  akrabalık derecesinin sayısal ölçüsüdür; akraba dillerde az harfle")
    S.append("  yüksek düzenlilik aynı anda elde edilir, akraba olmayanlarda")
    S.append("  edilemez. README'de istenen dört işlem türü")
    S.append("  (tekil değişim, grupça değişim, göçüşüm, ekleme/silme) kuralların")
    S.append("  bileşimiyle kapsanmış; k -> f gibi sıçramalar yerine her kural")
    S.append("  harf grafiğindeki en kısa doğal yola (k > g > ğ > ...) bölünerek")
    S.append("  katmanlı bir Ön Dil serisi elde edilmiştir.")
    S.append("")
    return "\n".join(S)
