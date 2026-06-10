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

from sesbiçim.harf import BOŞ, HARFLER, alt_yazı, taban, uzaklık, yol
from sesbiçim.ünsüz import ÜNSÜZLER

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
        if en_puan is None or (c, p) < (en_puan, en_iyi):
            en_iyi, en_puan = p, c
    return en_iyi


def _proto_kelimeler(hizalamalar, atama):
    return [[atama[ç] for ç in sütunlar] for sütunlar in hizalamalar]


# ---------------------------------------------------------------------------
# 3. aşama: çakışma çözümü (önce bağlam, sonra harf türetimi)
# ---------------------------------------------------------------------------

def _çakışma_çöz(atama, korr_yerleri, hizalamalar, sayaç):
    """Aynı Ön Dil harfi bir dalda iki ayrı sese gidiyorsa ayrıştırır.

    Sıklığı en yüksek refleks "her yerde" kuralı olur; diğerleri için
    kendilerini bütün öbür reflekslerden ayıran bir bağlam aranır.
    Ayrışmayan grup, yeni türetilmiş bir Ön Dil harfine taşınır.
    """
    türetilmiş = []

    def sıklık(çler):
        return sum(len(korr_yerleri[ç]) for ç in çler)

    while True:
        protolar = _proto_kelimeler(hizalamalar, atama)
        kova = {}
        for ç, tok in atama.items():
            for dal in DALLAR:
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
                    sorunlu = (tok, çler)
                    break
            if sorunlu:
                break

        if sorunlu is None:
            break

        tok, çler = sorunlu
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
    return gruplar, türetilmiş, protolar


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
                     katman, tablolar):
    çakışan = set()
    met_kelime = {}
    for kno, sütun, _ in metatezler:
        met_kelime.setdefault(kno, []).append(sütun)
    for kno in range(çift_sayısı):
        sütunlar = hizalamalar[kno]
        for dal in DALLAR:
            gezingeler = []
            grup_sırası = []
            for ç in sütunlar:
                g = grup_bul[(atama[ç], dal, ç[dal])]
                gezingeler.append(_gezinge(g, atama[ç], katman[dal]))
                grup_sırası.append(g)
            if dal == 1:
                for s in met_kelime.get(kno, []):
                    gezingeler[s], gezingeler[s + 1] = gezingeler[s + 1], gezingeler[s]
                    grup_sırası[s], grup_sırası[s + 1] = grup_sırası[s + 1], grup_sırası[s]
            for j in range(1, katman[dal] + 1):
                konumlar = [p for p in range(len(gezingeler))
                            if gezingeler[p][j - 1] != BOŞ]
                w = [gezingeler[p][j - 1] for p in konumlar]
                for idx, p in enumerate(konumlar):
                    beklenen = gezingeler[p][j]
                    kural = _kural_seç(tablolar[dal].get(j, []), w, idx)
                    bulunan = kural.hedef if kural else w[idx]
                    if bulunan != beklenen:
                        if kural:
                            çakışan.update(id(g2) for g2 in kural.gruplar)
                        çakışan.add(id(grup_sırası[p]))
    return çakışan


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

def seri_oluştur(çiftler, dal_adları=("A", "B"), en_az_katman=0):
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

    atama = {ç: _aday_seç(ç) for ç in korr_yerleri}

    sayaç = {}
    gruplar, türetilmiş, protolar = _çakışma_çöz(
        atama, korr_yerleri, hizalamalar, sayaç
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
            katman, tablolar,
        )
        if not çakışan:
            break
        yeni_etiket = False
        for g in gruplar:
            if id(g) in çakışan and etiket_uygula(g):
                yeni_etiket = True
                etiketli_sayısı += 1
        if not yeni_etiket:
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
        etiketli_sayısı=etiketli_sayısı,
    )
