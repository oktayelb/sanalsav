from sesbiçim.harf import BOŞ, SANAL_HARFLER, dizi_harfleri, dizi_mi, taban

import math

from .insa import GÖÇÜŞÜM, _kural_seç
from .kurallar import BİRLEŞTİRİCİ, _KABALAR, _SINIFLAR

_SANAL = set(SANAL_HARFLER)


def _biçim_yaz(tokenler):
    return "".join(tokenler) if tokenler else "∅"


def türetim_satırı(biçimler):
    metinler = []
    for b in biçimler:
        m = _biçim_yaz(b)
        if not metinler or metinler[-1] != m:
            metinler.append(m)
    return " > ".join(
        m if i == len(metinler) - 1 else "*" + m for i, m in enumerate(metinler)
    )


def katman_adı(dal_adı, j, son_katman):
    if j == 0:
        return "Ön Dil"
    if j == son_katman:
        return dal_adı
    return f"Ön {dal_adı} {j}"


def kural_metni(k):
    if k.bağlam == GÖÇÜŞÜM:
        x, y = dizi_harfleri(k.kaynak)
        return f"*{x}{y} -> {y}{x}  (göçüşüm)"
    if k.hedef == BOŞ:
        hedef, not_ = "∅", ""
    elif dizi_mi(k.hedef):
        hedef, not_ = "".join(dizi_harfleri(k.hedef)), "  (doğum)"
    else:
        hedef = k.hedef
        not_ = "  (korunur)" if k.hedef == k.kaynak else ""
    bağlam = "" if k.bağlam == "her yerde" else f"  / {k.bağlam}"
    return f"*{k.kaynak} -> {hedef}{bağlam}{not_}"


def _etiketli(t):
    return t != BOŞ and not dizi_mi(t) and t != taban(t)


def kural_kullanımı(seri):
    sayı = {}
    for d in range(len(seri.dal_adları)):
        for kt in seri.türevler:
            for j in range(1, seri.katman[d] + 1):
                ks = seri.tablolar[d].get(j, [])
                if ks and ks[0].bağlam == GÖÇÜŞÜM:
                    for k in ks:
                        sayı[id(k)] = sayı.get(id(k), 0) + 1
                    continue
                w = kt[d][j - 1]
                for i in range(len(w)):
                    k = _kural_seç(ks, w, i)
                    if k is not None:
                        sayı[id(k)] = sayı.get(id(k), 0) + 1
    return sayı


def açıklama_uzunluğu(seri, evren):
    A = evren + 1
    atom_sayısı = len(_KABALAR) - 1 + len(_SINIFLAR) + 2 * A
    proto = {t for w in seri.proto_kelimeler for t in w}
    sözlük = sum(len(w) for w in seri.proto_kelimeler) * math.log2(max(2, len(proto)))
    kural = 0.0
    for d in range(len(seri.dal_adları)):
        L = max(2, seri.katman[d])
        for ks in seri.tablolar[d].values():
            for k in ks:
                kural += 2 * math.log2(A) + math.log2(L)
                if k.bağlam not in ("her yerde", GÖÇÜŞÜM):
                    kural += len(k.bağlam.split(BİRLEŞTİRİCİ)) * math.log2(atom_sayısı)
    istisna = sum(len(beklenen) for _, _, beklenen, _ in seri.istisnalar) * math.log2(A)
    return {"sözlük": sözlük, "kural": kural, "istisna": istisna,
            "toplam": sözlük + kural + istisna}


def istatistik(seri):
    adlar = list(seri.dal_adları)
    B = len(adlar)
    proto = sorted({t for w in seri.proto_kelimeler for t in w})
    proto_küme = set(proto)
    dallar = []
    etiketler = set()
    for d in range(B):
        L = seri.katman[d]
        katmanlar = []
        önceki = set(proto)
        for j in range(L + 1):
            harfler = {t for kt in seri.türevler for t in kt[d][j]}
            if 0 < j < L:
                etiketler |= {t for t in harfler if _etiketli(t)} - proto_küme
            kurallar = seri.tablolar[d].get(j, []) if j else []
            değişim = [k for k in kurallar if k.hedef != k.kaynak]
            katmanlar.append({
                "j": j,
                "harf": sorted(harfler),
                "doğan": sorted(harfler - önceki) if j else [],
                "yiten": sorted(önceki - harfler) if j else [],
                "kural": len(değişim),
                "korunma": len(kurallar) - len(değişim),
                "bağlamlı": sum(1 for k in değişim if k.bağlam != "her yerde"),
            })
            önceki = harfler
        kural = sum(k["kural"] for k in katmanlar)
        silme = sum(1 for h in seri.hizalamalar for ç in h if ç[d] == BOŞ)
        en_az_silme = sum(
            max(0, max(len(w) for w in row[1:]) - len(row[1 + d]))
            for row in seri.çiftler
        )
        dallar.append({
            "ad": adlar[d], "katman": L, "kural": kural,
            "bağlamlı": sum(k["bağlamlı"] for k in katmanlar),
            "korunma": sum(k["korunma"] for k in katmanlar),
            "ortalama": kural / L if L else 0.0,
            "silme": silme, "en_az_silme": en_az_silme,
            "katmanlar": katmanlar,
        })
    türetim = B * len(seri.çiftler)
    tüm_harf = set(proto)
    for kt in seri.türevler:
        for d in range(B):
            for b in kt[d]:
                tüm_harf |= set(b)
    toplam_kural = sum(x["kural"] for x in dallar)
    kullanım = kural_kullanımı(seri)
    tek_tanıklı = sum(1 for d in range(B) for ks in seri.tablolar[d].values()
                      for k in ks if k.hedef != k.kaynak and kullanım.get(id(k)) == 1)
    toplam_katman = sum(x["katman"] for x in dallar)
    proto_boy = sum(len(w) for w in seri.proto_kelimeler) / len(seri.proto_kelimeler)
    çocuk_boy = [sum(len(row[1 + d]) for row in seri.çiftler) / len(seri.çiftler)
                 for d in range(B)]
    return {
        "proto": proto,
        "temel": [t for t in proto if t == taban(t)],
        "türetilmiş": [t for t in proto if t != taban(t)],
        "sanal": [t for t in proto if taban(t) in _SANAL],
        "etiketler": sorted(etiketler),
        "dallar": dallar,
        "türetim": türetim,
        "istisna": len(seri.istisnalar),
        "düzenlilik": 100.0 * (türetim - len(seri.istisnalar)) / türetim,
        "tüm_harf": len(tüm_harf),
        "toplam_kural": toplam_kural,
        "toplam_katman": toplam_katman,
        "genel_ortalama": toplam_kural / toplam_katman if toplam_katman else 0.0,
        "proto_boy": proto_boy,
        "çocuk_boy": çocuk_boy,
        "tek_tanıklı": tek_tanıklı,
        "mdl": açıklama_uzunluğu(seri, len(tüm_harf)),
    }


def rapor_üret(seri):
    ist = istatistik(seri)
    S = []
    adlar = list(seri.dal_adları)
    B = len(adlar)
    g = max(len(a) for a in adlar)

    S.append("=" * 72)
    S.append(" SANAL SAV — Varsayımsal Ön Dil Serisi Raporu")
    S.append(f" Diller: {' ~ '.join(adlar)} (yazılış esaslı, anlam sıralı liste)")
    S.append("=" * 72)
    S.append("")
    S.append("Bu rapor gerçek bir etimoloji savı DEĞİLDİR. Verilen listeler, her")
    S.append("adımı doğal bir ses değişimi olan düzenli yasalarla ortak bir Ön Dil")
    S.append("serisine bağlanır. Ön dil sözcüğü hizalamanın sütun başına bir sesidir")
    S.append("(gizli harf yok); harf sayısı, yeni harf yerine doğal ortamlar")
    S.append("(ön ünlü önünde, ünlüler arasında, ünlü uyumu...), yasa sırası ve")
    S.append("ara katmanlar kullanılarak en aza indirilir.")
    S.append("")

    S.append("-" * 72)
    S.append("1. ÖZET")
    S.append("-" * 72)
    S.append(f"  dil sayısı                      : {B}")
    S.append(f"  anlam (sözcük) sayısı           : {len(seri.çiftler)}")
    S.append(f"  Ön Dil harf dağarcığı           : {len(ist['proto'])} "
             f"(temel {len(ist['temel'])} + türetilmiş {len(ist['türetilmiş'])})")
    S.append(f"  ara katmanda etiketli harf      : {len(ist['etiketler'])}")
    S.append(f"  seri boyunca toplam ayrı harf   : {ist['tüm_harf']}")
    S.append("  ön dile uzaklık (katman sayısı) : "
             + ", ".join(f"{x['ad']} {x['katman']}" for x in ist["dallar"]))
    S.append("  ses değişim kuralı              :")
    for x in ist["dallar"]:
        S.append(f"      {x['ad']:<14} {x['kural']} kural ({x['bağlamlı']} bağlamlı, "
                 f"+{x['korunma']} korunma)")
    S.append("  KATMAN BAŞINA ORTALAMA KURAL    :")
    for x in ist["dallar"]:
        S.append(f"      {x['ad']:<14} {x['ortalama']:.2f} kural/katman "
                 f"({x['kural']} kural / {x['katman']} katman)")
    S.append(f"      {'bütün seri':<14} {ist['genel_ortalama']:.2f} kural/katman "
             f"({ist['toplam_kural']} kural / {ist['toplam_katman']} katman)")
    S.append(f"  tek konumda işleyen kural       : {ist['tek_tanıklı']} / {ist['toplam_kural']}")
    m = ist["mdl"]
    S.append(f"  AÇIKLAMA UZUNLUĞU (MDL)         : {m['toplam']:.0f} bit "
             f"(sözlük {m['sözlük']:.0f} + kural {m['kural']:.0f} + istisna {m['istisna']:.0f})")
    S.append(f"  ön dil sözcük uzunluğu (ort.)   : {ist['proto_boy']:.2f} ses "
             f"({', '.join(f'{a} {b:.2f}' for a, b in zip(adlar, ist['çocuk_boy']))})")
    S.append("  silinen ses (ses düşmesi)       :")
    for x in ist["dallar"]:
        S.append(f"      {x['ad']:<14} {x['silme']} "
                 f"(sözcük boyu farkından kaçınılmaz olan: {x['en_az_silme']})")
    göç = {ç for _, _, ç in seri.metatez_olayları}
    S.append(f"  göçüşüm (metathesis) kuralı     : {len(göç)}")
    if seri.doğum_olayları:
        S.append(f"  doğum (tek harf > çok harf)     : {len(seri.doğum_olayları)} konum "
                 "(yalnız uzun ünlüler)")
    S.append(f"  istisna                         : {ist['istisna']} / {ist['türetim']} türetim")
    S.append(f"  düzenlilik                      : %{ist['düzenlilik']:.1f}")
    S.append("")

    S.append("-" * 72)
    S.append("2. ÖN DİL HARF DAĞARCIĞI VE KATMANLAR")
    S.append("-" * 72)
    S.append("  temel harfler      : " + " ".join(t for t in ist["temel"]
                                                 if t not in _SANAL))
    sanal = [t for t in ist["temel"] if t in _SANAL]
    if sanal:
        S.append("  sanal harfler      : " + " ".join(sanal)
                 + "   (hiçbir yazıda yok; özellik uzayından)")
    if ist["türetilmiş"]:
        S.append("  türetilmiş harfler : " + " ".join(ist["türetilmiş"]))
        S.append("    (alt simgeli harf, aynı yere oturan ikinci bir sestir: o sesin")
        S.append("     yansımaları hiçbir doğal ortamla ya da yasa sırasıyla öbür sesten")
        S.append("     ayrılamadığı için ayrı harf olmak zorundadır)")
    if ist["etiketler"]:
        S.append("  ara katman etiketleri: " + " ".join(ist["etiketler"]))
    S.append("")
    S.append("  Katman başına harf dağarcığı ve kural sayısı:")
    for x in ist["dallar"]:
        S.append(f"    {x['ad']}:")
        for k in x["katmanlar"]:
            ad = katman_adı(x["ad"], k["j"], x["katman"])
            if k["j"] == 0:
                S.append(f"      {k['j']:>2}. {ad:<16} {len(k['harf']):>3} harf")
            else:
                S.append(f"      {k['j']:>2}. {ad:<16} {len(k['harf']):>3} harf "
                         f"(+{len(k['doğan'])} doğan, -{len(k['yiten'])} yiten), "
                         f"{k['kural']} kural")
    S.append("")

    S.append("-" * 72)
    S.append("3. SES DEĞİŞİM KURALLARI")
    S.append("-" * 72)
    S.append("  Aynı harfe birden çok yasa uyarsa üstteki önce işler (yasa sırası);")
    S.append("  sırası belirtilmeyen yasa 'her yerde' geçerlidir.")
    S.append("")
    for d, ad in enumerate(adlar):
        x = ist["dallar"][d]
        S.append(f"  {ad} dalı ({x['katman']} katman, ortalama "
                 f"{x['ortalama']:.2f} kural/katman):")
        for j in range(1, seri.katman[d] + 1):
            kurallar = seri.tablolar[d].get(j, [])
            if not kurallar:
                continue
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
    for kno, row in enumerate(seri.çiftler):
        S.append(f"  {kno + 1:>3}. {row[0]}  ({' ~ '.join(row[1:])})   "
                 f"Ön Dil: *{_biçim_yaz(seri.proto_kelimeler[kno])}")
        for d, ad in enumerate(adlar):
            im = "  ✗" if (kno, d) in bozuk else ""
            S.append(f"       {ad:<{g}}: {türetim_satırı(seri.türevler[kno][d])}{im}")
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
    return "\n".join(S)

