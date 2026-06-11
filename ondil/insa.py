# -*- coding: utf-8 -*-
"""Ön Dil serisi inşası.

Uygulanan yöntem, README'deki 1. ve 4. varsayımsal yöntemlerin bileşimidir:

1) Anlamca eşleştirilmiş sözcük çiftleri, sesbiçimsel ağırlıklı hizalama ile
   harf harf hizalanır (göçüşüm/metathesis ayrıca yakalanır).
2) Hizalamadan harf karşılıklıkları (ör. Türkçe b ~ İngilizce w) çıkarılır;
   aynı karşılıklık bütün söz varlığında TEK Ön Dil harfine bağlanır, böylece
   kurallar tanım gereği düzenli olur.
3) Ön Dil harfi, iki çocuk harfe de harf grafiğindeki en kısa doğal yolla
   bağlanan harftir (k -> f yerine k -> g -> ğ -> v -> f gibi).
4) Aynı Ön Dil harfi bir dalda birden çok sese gidiyorsa önce bağlam koşulu
   (söz başında, ünlü önünde...) aranır; ayrışmazsa yeni bir Ön Dil harfi
   türetilir (b₂ gibi). Asgari harf hedefi: önce paylaş, sonra bağlamla ayır,
   en son çare olarak harf türet.
5) Her kural doğal yol üzerinden adımlara bölünür; en uzun zincir o dalın
   katman (ara Ön Dil) sayısını belirler.
6) Kurallar katman katman "körce" (köken bilgisi olmadan) uygulanır; bir
   zincirin ara harfi başka bir sözcüğün harfiyle çakışıp onu yanlış yöne
   sürüklerse, o zincirin ara harfleri etiketlenerek (g₃ gibi) ayrıştırılır.
   Sonuçta her sözcük yalnız kurallarla, istisnasız türetilmelidir.
"""

from dataclasses import dataclass, field

from sesbiçim.harf import (
    BOŞ, HARFLER, SANAL_HARFLER, alt_yazı, taban, uzaklık, yol, yollar,
)
from sesbiçim.ünsüz import ÜNSÜZLER

# Sanal (hiçbir yazıda olmayan) harf, ancak yolu gerçekten kısaltıyorsa
# seçilsin: eşitlik bozucu küçük ceza.
_SANAL_CEZA = 0.05
_SANAL_KÜME = set(SANAL_HARFLER)

from .hizalama import hizala
from .kurallar import BAĞLAM_SIRASI, ayır, bağlam_işlevi

DALLAR = (0, 1)


@dataclass
class Grup:
    """Bir Ön Dil harfinin bir daldaki tek refleksi (tek kural)."""

    token: str
    dal: int
    refleks: str  # gerçek harf ya da BOŞ
    bağlam: str = "her yerde"
    korrlar: tuple = ()
    zincir: list = None  # [token, ara..., refleks]; kimliğe eşitse None
    etiketli: bool = False
    yedek_yolları: list = None  # çakışmada denenecek eşdeğer doğal yollar


@dataclass
class KatmanKural:
    kaynak: str
    hedef: str
    bağlam: str
    gruplar: list = field(default_factory=list)


@dataclass
class Seri:
    dal_adları: tuple
    çiftler: list
    hizalamalar: list
    metatez_olayları: list  # (kelime, sütun, (x, y)): 2. dalda xy -> yx
    atama: dict  # karşılıklık -> Ön Dil harfi
    korr_yerleri: dict  # karşılıklık -> [(kelime, sütun)]
    gruplar: list
    proto_kelimeler: list
    katman: list  # dal başına katman sayısı
    tablolar: list  # dal başına {katman: [KatmanKural]}
    türevler: list  # [kelime][dal] -> katman katman biçimler
    istisnalar: list  # (kelime, dal, beklenen, bulunan)
    türetilmiş: list  # bağlamla ayrışmayınca türetilen Ön Dil harfleri
    düzensiz: list = None  # dal başına kural dışı bırakılan karşılıklıklar
    türetim_eşiği: int = 1
    etiketli_sayısı: int = 0


# ---------------------------------------------------------------------------
# 1. aşama: hizalama ve göçüşüm
# ---------------------------------------------------------------------------

def _metatez_ayıkla(sütunlar):
    """ab ~ ba biçimindeki bitişik çaprazlamaları göçüşüm olarak ayıklar.

    Ön Dil sırası 1. dalın sırası kabul edilir; 2. dal göçüşüm kuralı alır.
    """
    olaylar = []
    yeni = []
    i = 0
    while i < len(sütunlar):
        if i + 1 < len(sütunlar):
            (a1, b1), (a2, b2) = sütunlar[i], sütunlar[i + 1]
            if (
                BOŞ not in (a1, b1, a2, b2)
                and a1 != a2
                and a1 == b2
                and a2 == b1
            ):
                yeni.append((a1, a1))
                yeni.append((a2, a2))
                olaylar.append((len(yeni) - 2, (a1, a2)))
                i += 2
                continue
        yeni.append(sütunlar[i])
        i += 1
    return yeni, olaylar


# ---------------------------------------------------------------------------
# 2. aşama: karşılıklık başına Ön Dil harfi adayı
# ---------------------------------------------------------------------------

def _aday_seç(çift):
    """Her iki çocuk harfe de toplamda en kısa doğal yolla bağlanan harf."""
    x, y = çift
    en_iyi, en_puan = None, None
    for p in HARFLER:
        c = uzaklık(p, x) + uzaklık(p, y)
        if c >= 99:
            continue
        if p == x or p == y:
            c -= 0.25  # değişmeyen dal = daha az kural
        if p in ÜNSÜZLER and ÜNSÜZLER[p][2]:
            c += 0.1  # eşitlikte ötümsüz (arkaik) biçim yeğlenir
        if p in _SANAL_KÜME:
            c += _SANAL_CEZA
        if en_puan is None or (c, p) < (en_puan, en_iyi):
            en_iyi, en_puan = p, c
    return en_iyi


def _proto_kelimeler(hizalamalar, atama):
    return [[atama[ç] for ç in sütunlar] for sütunlar in hizalamalar]


# Yedek konak harf ararken göze alınan ortalama ek yol adımı.
# Büyük tutmak harf sayısını düşürür ama zincirleri (dolayısıyla kural
# sayısını) uzatır; 0.5 ikisini dengeler.
GEVŞEKLİK = 0.5

# Gerçekçilik sınırı: bir Ön Dil harfinin herhangi bir refleksi, harfin
# çapasından en çok bu kadar doğal adım uzakta olabilir.
EN_UZUN_YOL = 4


def _çapa_bul(korrlar, korr_yerleri):
    """Kümedeki BÜTÜN reflekslere EN_UZUN_YOL içinde bağlanan en ucuz çapa.

    Çapa, soyut Ön Dil harfinin özellik uzayındaki yeridir; ses
    değişimlerinin gerçekçi kalmasını sağlar. Bulunamazsa küme olamaz.
    """
    en_iyi, en_puan = None, None
    for p in HARFLER:
        puan = 0.0
        uygun = True
        for ç in korrlar:
            d0, d1 = uzaklık(p, ç[0]), uzaklık(p, ç[1])
            if max(d0, d1) > EN_UZUN_YOL:
                uygun = False
                break
            puan += len(korr_yerleri[ç]) * (d0 + d1)
        if p in _SANAL_KÜME:
            puan += _SANAL_CEZA
        if uygun and (en_puan is None or (puan, p) < (en_puan, en_iyi)):
            en_iyi, en_puan = p, puan
    return en_iyi


def _birleşebilir(k1, k2, korr_yerleri, protolar):
    """İki küme tek soyut harfte kurallı yaşayabilir mi? Çapasını döndürür."""
    korrlar = sorted(k1["korrlar"] | k2["korrlar"])
    çapa = _çapa_bul(korrlar, korr_yerleri)
    if çapa is None:
        return None

    def sıklık(çler):
        return sum(len(korr_yerleri[ç]) for ç in çler)

    for dal in DALLAR:
        gruplar = {}
        for ç in korrlar:
            gruplar.setdefault(ç[dal], []).append(ç)
        if len(gruplar) < 2:
            continue
        sıralı = sorted(gruplar.items(), key=lambda kv: (-sıklık(kv[1]), kv[0]))
        for refleks, çler in sıralı[1:]:
            kendi = [y for ç in çler for y in korr_yerleri[ç]]
            diğer = [
                y
                for r2, ç2ler in gruplar.items()
                if r2 != refleks
                for ç2 in ç2ler
                for y in korr_yerleri[ç2]
            ]
            if ayır(kendi, diğer, protolar) is None:
                return None
    return çapa


def _kümele(korr_yerleri, hizalamalar, sayaç, eşik):
    """Karşılıklıkları en az sayıda SOYUT Ön Dil harfinde toplar.

    Ön Dil harfleri çocuk alfabelerinden kopyalanmaz: sistem sıfır harfle
    başlar (her karşılıklık türü kendi kümesidir) ve kurallı biçimde bir
    arada yaşayabilen kümeler açgözlü olarak birleştirilir. Bir harf,
    böyle bir kümenin kendisidir; çapası yalnız gerçekçilik içindir.
    Toplam sıklığı eşik altında kalan kümeler kendi harfini alamaz:
    konumları en yakın sağ kalan harfe ev sahipliği verilir, kaderlerini
    (kurallı üyelik / bağlam / istisna) dal bazında 2. aşama belirler.
    """
    sıra = sorted(korr_yerleri, key=lambda ç: (-len(korr_yerleri[ç]), ç))
    kümeler = [{"korrlar": {ç}, "çapa": _aday_seç(ç)} for ç in sıra]

    def geçici_ad(ki):
        return kümeler[ki]["çapa"] + alt_yazı(9000 + ki)

    atama = {}
    for ki, k in enumerate(kümeler):
        for ç in k["korrlar"]:
            atama[ç] = geçici_ad(ki)
    protolar = _proto_kelimeler(hizalamalar, atama)

    def yeniden_adlandır(ki):
        tok = geçici_ad(ki)
        for ç in kümeler[ki]["korrlar"]:
            atama[ç] = tok
            for kno, s in korr_yerleri[ç]:
                protolar[kno][s] = tok

    canlı = set(range(len(kümeler)))
    hak = 20000  # güvenlik sınırı
    değişti = True
    while değişti and hak > 0:
        değişti = False
        # yalnız en az bir refleksi paylaşan kümeler birleşmeyi dener
        kova = {}
        for ki in sorted(canlı):
            for ç in kümeler[ki]["korrlar"]:
                for dal in DALLAR:
                    kova.setdefault((dal, ç[dal]), set()).add(ki)
        for anahtar in sorted(kova):
            ortaklar = sorted(kova[anahtar])
            for x, i in enumerate(ortaklar):
                if i not in canlı:
                    continue
                for j in ortaklar[x + 1:]:
                    if j not in canlı or i not in canlı or hak <= 0:
                        continue
                    hak -= 1
                    çapa = _birleşebilir(
                        kümeler[i], kümeler[j], korr_yerleri, protolar
                    )
                    if çapa is None:
                        continue
                    kümeler[i]["korrlar"] |= kümeler[j]["korrlar"]
                    kümeler[i]["çapa"] = çapa
                    canlı.discard(j)
                    yeniden_adlandır(i)
                    değişti = True

    def küme_sıklığı(ki):
        return sum(len(korr_yerleri[ç]) for ç in kümeler[ki]["korrlar"])

    # tutumluluk: eşik altı kümeler kendi harfini alamaz; korrları en yakın
    # sağ kalan harfe ev sahipliği verilir. Orada uyum/bağlam bulurlarsa
    # kurallı yaşarlar; çatışırlarsa kararı dal bazında 2. aşama verir.
    kalanlar = [ki for ki in sorted(canlı) if küme_sıklığı(ki) >= eşik]
    if not kalanlar:  # küçük girdilerde emniyet
        kalanlar = sorted(canlı)

    # kalıcı adlar: çapa harfi; aynı çapayı paylaşan ek kümeler alt simge alır
    adet = {}
    son_ad = {}
    sıralı = sorted(
        kalanlar,
        key=lambda ki: (kümeler[ki]["çapa"], -küme_sıklığı(ki),
                        min(kümeler[ki]["korrlar"])),
    )
    for ki in sıralı:
        ç_ = kümeler[ki]["çapa"]
        adet[ç_] = adet.get(ç_, 0) + 1
        tok = ç_ if adet[ç_] == 1 else ç_ + alt_yazı(adet[ç_])
        if adet[ç_] > 1:
            sayaç[ç_] = max(sayaç.get(ç_, 1), adet[ç_])
        son_ad[ki] = tok
        for ç in kümeler[ki]["korrlar"]:
            atama[ç] = tok

    # düşen kümelerin konumları en yakın sağ kalan harfe ev sahipliği verilir
    for ki in sorted(canlı):
        if ki in kalanlar:
            continue
        for ç in kümeler[ki]["korrlar"]:
            ev = min(
                kalanlar,
                key=lambda k2: (
                    uzaklık(kümeler[k2]["çapa"], ç[0])
                    + uzaklık(kümeler[k2]["çapa"], ç[1]),
                    son_ad[k2],
                ),
            )
            atama[ç] = son_ad[ev]
    return atama


def _konak_adayları(çler, korr_yerleri, kullanılan_tokenlar):
    """Bir kural grubunun taşınabileceği konak harfler, puan sırasıyla.

    Asgari harf hedefinin asıl aracı: çakışan bir grup için yeni harf
    türetmeden önce, biraz daha uzak ama boşta/uyumlu GERÇEK bir harf
    (ya da zaten türetilmiş bir harf) konak olarak denenir.
    """
    toplam = sum(len(korr_yerleri[ç]) for ç in çler)

    def puan(p):
        ceza = _SANAL_CEZA if taban(p) in _SANAL_KÜME else 0.0
        return ceza + sum(
            len(korr_yerleri[ç]) * (uzaklık(p, ç[0]) + uzaklık(p, ç[1]))
            for ç in çler
        ) / toplam

    adaylar = [(puan(p), 0, p) for p in HARFLER]
    for t in kullanılan_tokenlar:
        if t != taban(t):
            adaylar.append((puan(taban(t)) + 0.01, 1, t))
    adaylar.sort()
    return adaylar


# ---------------------------------------------------------------------------
# 3. aşama: çakışma çözümü (önce bağlam, sonra harf türetimi)
# ---------------------------------------------------------------------------

def _çakışma_çöz(atama, korr_yerleri, hizalamalar, sayaç, eşik=1,
                 ön_düzensiz=None):
    """Aynı Ön Dil harfi bir dalda iki ayrı sese gidiyorsa ayrıştırır.

    Sıklığı en yüksek refleks "her yerde" kuralı olur; diğerleri için
    kendilerini bütün öbür reflekslerden ayıran bir bağlam aranır.

    Ayrışmayan grup için sırasıyla:
    1) yedek konak harf denenir (boşta/uyumlu gerçek bir harf ya da zaten
       türetilmiş bir harf; yeni harf İCAT ETMEDEN çözme girişimi),
    2) konak bulunamazsa tutumluluk eşiği uygulanır: yeni bir Ön Dil
       harfi ancak en az "eşik" konumu kurtarıyorsa türetilir; daha
       seyrek gruplar kural dışı (istisna) bırakılır.
    """
    türetilmiş = []
    # dal başına kural dışı bırakılan karşılıklıklar (kümelemeden devralınır)
    düzensiz = [set(d) for d in ön_düzensiz] if ön_düzensiz else [set(), set()]
    denenmiş = {}  # korr -> bu korrun başarısız olduğu konak harfler
    deneme_hakkı = 4000  # güvenlik sınırı; aşılırsa doğrudan türetime dönülür

    def sıklık(çler):
        return sum(len(korr_yerleri[ç]) for ç in çler)

    while True:
        protolar = _proto_kelimeler(hizalamalar, atama)
        kova = {}
        for ç, tok in atama.items():
            for dal in DALLAR:
                if ç in düzensiz[dal]:
                    continue
                kova.setdefault((tok, dal), {}).setdefault(ç[dal], set()).add(ç)

        sorunlu = None
        for (tok, dal) in sorted(kova):
            refgrup = kova[(tok, dal)]
            if len(refgrup) < 2:
                continue
            sıralı = sorted(refgrup.items(), key=lambda kv: (-sıklık(kv[1]), kv[0]))
            for refleks, çler in sıralı[1:]:
                kendi = [y for ç in çler for y in korr_yerleri[ç]]
                diğer = [
                    y
                    for r2, ç2ler in refgrup.items()
                    if r2 != refleks
                    for ç2 in ç2ler
                    for y in korr_yerleri[ç2]
                ]
                if ayır(kendi, diğer, protolar) is None:
                    sorunlu = (tok, dal, çler)
                    break
            if sorunlu:
                break

        if sorunlu is None:
            break

        tok, dal, çler = sorunlu
        for ç in çler:
            denenmiş.setdefault(ç, set()).add(tok)
        if sıklık(çler) < eşik:
            # harf türetmeye (ve konak aramaya) değmez: istisna kalır
            düzensiz[dal].update(çler)
            continue
        if deneme_hakkı > 0:
            adaylar = _konak_adayları(çler, korr_yerleri, set(atama.values()))
            en_iyi = adaylar[0][0]
            yeni_konak = None
            for puanı, _, p in adaylar:
                if puanı > en_iyi + GEVŞEKLİK:
                    break
                if p == tok or any(p in denenmiş.get(ç, ()) for ç in çler):
                    continue
                yeni_konak = p
                break
            if yeni_konak is not None:
                deneme_hakkı -= 1
                for ç in sorted(çler):
                    atama[ç] = yeni_konak
                continue
        b = taban(tok)
        sayaç[b] = sayaç.get(b, 1) + 1
        yeni = b + alt_yazı(sayaç[b])
        türetilmiş.append(yeni)
        for ç in sorted(çler):
            atama[ç] = yeni

    # son durumdaki grupları, bağlamlarıyla birlikte kur
    protolar = _proto_kelimeler(hizalamalar, atama)
    gruplar = []
    for (tok, dal) in sorted(kova):
        refgrup = kova[(tok, dal)]
        sıralı = sorted(refgrup.items(), key=lambda kv: (-sıklık(kv[1]), kv[0]))
        for sıra_no, (refleks, çler) in enumerate(sıralı):
            if sıra_no == 0:
                bağlam = "her yerde"
            else:
                kendi = [y for ç in çler for y in korr_yerleri[ç]]
                diğer = [
                    y
                    for r2, ç2ler in refgrup.items()
                    if r2 != refleks
                    for ç2 in ç2ler
                    for y in korr_yerleri[ç2]
                ]
                bağlam = ayır(kendi, diğer, protolar)
                assert bağlam is not None, (tok, dal, refleks)
            gruplar.append(
                Grup(token=tok, dal=dal, refleks=refleks, bağlam=bağlam,
                     korrlar=tuple(sorted(çler)))
            )
    return gruplar, türetilmiş, protolar, düzensiz


# ---------------------------------------------------------------------------
# 4. aşama: kural zincirleri ve katman tabloları
# ---------------------------------------------------------------------------

def _zincir_kur(g):
    b = taban(g.token)
    if g.refleks == g.token:
        return None  # değişmeyen harf
    if g.refleks == b:
        return [g.token, b]  # türetilmiş harfin taban harfe dönmesi
    return [g.token] + yol(b, g.refleks)[1:]


def _katman_tablosu(gruplar, katman):
    """Dal başına {katman_no: [KatmanKural]}; özdeş kurallar birleştirilir."""
    tablolar = []
    for dal in DALLAR:
        tablo = {j: {} for j in range(1, katman[dal] + 1)}
        değişenler = {g.token for g in gruplar if g.dal == dal and g.zincir}
        for g in gruplar:
            if g.dal != dal:
                continue
            if not g.zincir:
                # Değişmeyen harf: aynı harfin değişen bir grubu varsa,
                # "her yerde" kuralından korunmak için açık korunma kuralı.
                if g.token in değişenler and 1 in tablo:
                    anahtar = (g.token, g.token, g.bağlam)
                    kural = tablo[1].get(anahtar)
                    if kural is None:
                        kural = KatmanKural(*anahtar)
                        tablo[1][anahtar] = kural
                    kural.gruplar.append(g)
                continue
            for j in range(1, len(g.zincir)):
                bağlam = g.bağlam if j == 1 else "her yerde"
                anahtar = (g.zincir[j - 1], g.zincir[j], bağlam)
                kural = tablo[j].get(anahtar)
                if kural is None:
                    kural = KatmanKural(*anahtar)
                    tablo[j][anahtar] = kural
                kural.gruplar.append(g)
        tablolar.append({j: sorted(t.values(), key=lambda k: (k.kaynak, k.hedef))
                         for j, t in tablo.items()})
    return tablolar


def _kural_seç(kurallar, w, i):
    adaylar = [
        k for k in kurallar
        if k.kaynak == w[i] and bağlam_işlevi(k.bağlam)(w, i)
    ]
    if not adaylar:
        return None
    return min(adaylar, key=lambda k: BAĞLAM_SIRASI.index(k.bağlam))


# ---------------------------------------------------------------------------
# 5. aşama: kör uygulamada çakışan zincirleri etiketleyerek ayrıştırma
# ---------------------------------------------------------------------------

def _gezinge(g, token, L):
    z = g.zincir or [token]
    return [z[min(j, len(z) - 1)] for j in range(L + 1)]


def _çakışmaları_bul(çift_sayısı, hizalamalar, atama, grup_bul, metatezler,
                     katman, tablolar, düzensiz):
    çakışan = set()
    met_kelime = {}
    for kno, sütun, _ in metatezler:
        met_kelime.setdefault(kno, []).append(sütun)
    for kno in range(çift_sayısı):
        sütunlar = hizalamalar[kno]
        for dal in DALLAR:
            gezingeler = []
            grup_sırası = []
            atla = []  # kural dışı (istisna) konumlar denetlenmez
            for ç in sütunlar:
                tok = atama[ç]
                if ç in düzensiz[dal]:
                    gezingeler.append([tok] * (katman[dal] + 1))
                    grup_sırası.append(None)
                    atla.append(True)
                else:
                    g = grup_bul[(tok, dal, ç[dal])]
                    gezingeler.append(_gezinge(g, tok, katman[dal]))
                    grup_sırası.append(g)
                    atla.append(False)
            if dal == 1:
                for s in met_kelime.get(kno, []):
                    gezingeler[s], gezingeler[s + 1] = gezingeler[s + 1], gezingeler[s]
                    grup_sırası[s], grup_sırası[s + 1] = grup_sırası[s + 1], grup_sırası[s]
                    atla[s], atla[s + 1] = atla[s + 1], atla[s]
            for j in range(1, katman[dal] + 1):
                konumlar = [p for p in range(len(gezingeler))
                            if gezingeler[p][j - 1] != BOŞ]
                w = [gezingeler[p][j - 1] for p in konumlar]
                for idx, p in enumerate(konumlar):
                    if atla[p]:
                        continue
                    beklenen = gezingeler[p][j]
                    kural = _kural_seç(tablolar[dal].get(j, []), w, idx)
                    bulunan = kural.hedef if kural else w[idx]
                    if bulunan != beklenen:
                        if kural:
                            çakışan.update(id(g2) for g2 in kural.gruplar)
                        çakışan.add(id(grup_sırası[p]))
    return çakışan


def _yol_değiştir(g):
    """Çakışan zincire, harf etiketlemeden önce eşdeğer başka yol dener."""
    if not g.zincir or len(g.zincir) <= 2 or g.etiketli:
        return False
    if g.yedek_yolları is None:
        g.yedek_yolları = [
            [g.token] + p[1:]
            for p in yollar(taban(g.token), g.zincir[-1])
        ]
    while g.yedek_yolları:
        aday = g.yedek_yolları.pop(0)
        if aday != g.zincir:
            g.zincir = aday
            return True
    return False


def _etiketle(gruplar, sayaç):
    """Çakışan zincirlerin ara harflerine ayırt edici alt simge takılır."""
    def uygula(g):
        if g.etiketli or not g.zincir or len(g.zincir) <= 2:
            return False
        yeni = [g.zincir[0]]
        for h in g.zincir[1:-1]:
            b = taban(h)
            sayaç[b] = sayaç.get(b, 1) + 1
            yeni.append(b + alt_yazı(sayaç[b]))
        yeni.append(g.zincir[-1])
        g.zincir = yeni
        g.etiketli = True
        return True

    return uygula


# ---------------------------------------------------------------------------
# 6. aşama: kör türetim ve doğrulama
# ---------------------------------------------------------------------------

def _metatez_uygula(w, kurallar):
    w = list(w)
    i = 0
    while i < len(w) - 1:
        if (taban(w[i]), taban(w[i + 1])) in kurallar:
            w[i], w[i + 1] = w[i + 1], w[i]
            i += 2
        else:
            i += 1
    return w


def kör_türet(proto, dal, tablolar, katman, metatez_kuralları):
    """Ön biçimi yalnız kurallarla (köken bilgisi olmadan) çocuk dile indirir."""
    w = list(proto)
    if dal == 1 and metatez_kuralları:
        w = _metatez_uygula(w, metatez_kuralları)
    biçimler = [list(w)]
    for j in range(1, katman + 1):
        yeni = []
        for i in range(len(w)):
            k = _kural_seç(tablolar.get(j, []), w, i)
            yeni.append(k.hedef if k else w[i])
        w = [t for t in yeni if t != BOŞ]
        biçimler.append(list(w))
    return biçimler


# ---------------------------------------------------------------------------
# ana akış
# ---------------------------------------------------------------------------

def seri_oluştur(çiftler, dal_adları=("A", "B"), en_az_katman=0,
                 türetim_eşiği=1):
    sözcükler = [(list(a), list(b)) for _, a, b in çiftler]

    hizalamalar = []
    metatezler = []
    for kno, (a, b) in enumerate(sözcükler):
        sütunlar, olaylar = _metatez_ayıkla(hizala(a, b))
        hizalamalar.append(sütunlar)
        for sütun, çift in olaylar:
            metatezler.append((kno, sütun, çift))

    korr_yerleri = {}
    for kno, sütunlar in enumerate(hizalamalar):
        for s, ç in enumerate(sütunlar):
            korr_yerleri.setdefault(ç, []).append((kno, s))

    sayaç = {}
    # 1. aşama: sıfırdan soyut harf kurma (kümeleme)
    atama = _kümele(korr_yerleri, hizalamalar, sayaç, türetim_eşiği)
    # 2. aşama: kalan çakışmaların çözümü (bağlam / konak / türetim)
    gruplar, türetilmiş, protolar, düzensiz = _çakışma_çöz(
        atama, korr_yerleri, hizalamalar, sayaç, türetim_eşiği
    )

    for g in gruplar:
        g.zincir = _zincir_kur(g)

    katman = [
        max(
            max((len(g.zincir) - 1 for g in gruplar
                 if g.dal == dal and g.zincir), default=0),
            en_az_katman,
        )
        for dal in DALLAR
    ]

    grup_bul = {(g.token, g.dal, g.refleks): g for g in gruplar}
    etiket_uygula = _etiketle(gruplar, sayaç)
    etiketli_sayısı = 0
    while True:
        tablolar = _katman_tablosu(gruplar, katman)
        çakışan = _çakışmaları_bul(
            len(çiftler), hizalamalar, atama, grup_bul, metatezler,
            katman, tablolar, düzensiz,
        )
        if not çakışan:
            break
        değişiklik = False
        for g in gruplar:
            if id(g) not in çakışan:
                continue
            if _yol_değiştir(g):  # önce eşdeğer doğal yol dene
                değişiklik = True
            elif etiket_uygula(g):  # son çare: ara harf etiketi
                değişiklik = True
                etiketli_sayısı += 1
        if not değişiklik:
            break  # ayrıştırılamayan kalıntı; istisna olarak raporlanır

    tablolar = _katman_tablosu(gruplar, katman)
    met_kuralları = sorted({çift for _, _, çift in metatezler})

    türevler = []
    istisnalar = []
    for kno, (anlam, a, b) in enumerate(çiftler):
        kelime_türevi = []
        for dal, hedef_sözcük in ((0, a), (1, b)):
            biçimler = kör_türet(
                protolar[kno], dal, tablolar[dal], katman[dal],
                met_kuralları if dal == 1 else [],
            )
            sonuç = "".join(biçimler[-1])
            if sonuç != hedef_sözcük:
                istisnalar.append((kno, dal, hedef_sözcük, sonuç))
            kelime_türevi.append(biçimler)
        türevler.append(kelime_türevi)

    return Seri(
        dal_adları=dal_adları,
        çiftler=çiftler,
        hizalamalar=hizalamalar,
        metatez_olayları=metatezler,
        atama=atama,
        korr_yerleri=korr_yerleri,
        gruplar=gruplar,
        proto_kelimeler=protolar,
        katman=katman,
        tablolar=tablolar,
        türevler=türevler,
        istisnalar=istisnalar,
        türetilmiş=türetilmiş,
        düzensiz=düzensiz,
        türetim_eşiği=türetim_eşiği,
        etiketli_sayısı=etiketli_sayısı,
    )
