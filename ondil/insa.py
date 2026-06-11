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
    BOŞ, DOĞUM_KAYNAĞI, HARFLER, SANAL_HARFLER, alt_yazı, dizi_harfleri,
    dizi_mi, dizi_yap, taban, uzaklık, yol, yollar, ünlü_mü,
    özellik_uzaklığı,
)
from sesbiçim.ünsüz import ÜNSÜZLER

# Sanal (hiçbir yazıda olmayan) harf, ancak yolu gerçekten kısaltıyorsa
# seçilsin: eşitlik bozucu küçük ceza.
_SANAL_CEZA = 0.05
_SANAL_KÜME = set(SANAL_HARFLER)

from .hizalama import hizala
from .kurallar import BAĞLAM_SIRASI, ayır, ayır_biçimlerle, bağlam_işlevi

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
    etiketli_konum: set = None  # zincirde alt simge takılmış ara düğüm konumları
    katman_bağlamı: dict = None  # {katman_no: bağlam}: ara katmanda koşullu kural


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
    doğum_olayları: list = field(default_factory=list)  # (kelime, sütun, çift)


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


def _doğum_eşi(sütunlar, i):
    """i konumunda uzun ünlü doğum örüntüsü arar; (çift, sütun_sayısı) döner.

    Pencere içindeki her dalın harfleri boşluklar atılarak sıkıştırılır
    (hizalama gövdeyi boşluklu sütunlara dağıtabilir). İki örüntü tanınır
    (önce geniş pencere denenir):
    - İki dal da AYNI uzun ünlünün FARKLI gövdesi: aa ~ ay, uvu ~ ubu.
    - Bir dal gövde, öbür dalda yalnız tek bir ünlü sağ: uvu ~ u, ağa ~ a.
      İki harflik gövde (ay tipi) tek ünlüyle yalnız söz sonunda eşlenir;
      yoksa olağan kayıcı silinmeleri toptan uzun ünlüye dönerdi.
    """
    n = len(sütunlar)
    for boy in (4, 3, 2):
        if i + boy > n:
            continue
        pencere = sütunlar[i:i + boy]
        yanlar = [[p[d] for p in pencere if p[d] != BOŞ] for d in DALLAR]
        diziler = [dizi_yap(y) if len(y) >= 2 else None for y in yanlar]
        kaynaklar = [DOĞUM_KAYNAĞI.get(d) if d else None for d in diziler]
        if (kaynaklar[0] is not None and kaynaklar[0] == kaynaklar[1]
                and diziler[0] != diziler[1]):
            return (diziler[0], diziler[1]), boy
        for dal in DALLAR:
            if kaynaklar[dal] is None:
                continue
            if len(yanlar[dal]) == 2 and i + boy != n:
                continue
            karşı = yanlar[1 - dal]
            if len(karşı) != 1 or not ünlü_mü(karşı[0]):
                continue
            if özellik_uzaklığı(yanlar[dal][0], karşı[0]) > 2:
                continue
            çift = ((diziler[dal], karşı[0]) if dal == 0
                    else (karşı[0], diziler[dal]))
            return çift, boy
    return None, 0


def _doğum_ayıkla(sütunlar):
    """Uzun ünlü doğum örüntülerini tek karşılıklık sütununa indirir.

    Tek harften çok harf türetme (README'deki grupça değişimin ilk yarısı)
    şimdilik yalnız uzun ünlülere tanınır: yakalanan pencere tek sütuna
    çekilir, Ön Dil harfi adayı doğuran uzun ünlü olur ve doğum, kuralın
    son adımı olarak uygulanır.
    """
    olaylar = []
    yeni = []
    i = 0
    while i < len(sütunlar):
        çift, boy = _doğum_eşi(sütunlar, i)
        if çift is not None:
            yeni.append(çift)
            olaylar.append((len(yeni) - 1, çift))
            i += boy
        else:
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
    if dizi_mi(g.refleks):
        # doğum: önce doğuran uzun ünlüye yürünür, son adımda doğrulur
        kaynak = DOĞUM_KAYNAĞI[g.refleks]
        if b == kaynak:
            return [g.token, g.refleks]
        return [g.token] + yol(b, kaynak)[1:] + [g.refleks]
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
            ilk = True
            for j in range(1, len(g.zincir)):
                if g.zincir[j - 1] == g.zincir[j]:
                    continue  # doğum zinciri dolgusu: bu katmanda durulur
                if g.katman_bağlamı and j in g.katman_bağlamı:
                    # ara katmanda bulunmuş koşul (proto bağlamı değil, o
                    # katmanın biçimlerinden çıkan ayrım)
                    bağlam = g.katman_bağlamı[j]
                else:
                    bağlam = g.bağlam if ilk else "her yerde"
                ilk = False
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
    """Kör türetimde yanlış sonuç veren grupları, EN SIĞ hata katmanlarıyla
    döndürür: {grup_kimliği: en_küçük_hata_katmanı}.

    Hata katmanı j ise, o gruba özgü ayrım j-1 konumundaki ara düğümü
    damgalamakla yapılır; böylece etiket zincirin tamamına değil yalnız
    ayrımın gerektiği derinliğe basılır (ön ek paylaşılır).
    """
    çakışan = {}
    kelime_gez = {}  # (kno, dal) -> (gezingeler, grup_sırası, atla)
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
            kelime_gez[(kno, dal)] = (gezingeler, grup_sırası, atla)
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
                        # Hem bu konumun grubu hem de yanlış seçilen kuralı
                        # üreten gruplar j. katmanda çakışır; ikisi de o
                        # katmanda damgalanabilir (kısa/kimlik zincirli grup
                        # damgalanamadığında, o düğümden GEÇEN uzun zincir
                        # damgalanarak ayrım sağlanır).
                        adaylar = [grup_sırası[p]]
                        if kural:
                            adaylar.extend(kural.gruplar)
                        for g2 in adaylar:
                            if g2 is None:
                                continue
                            önceki = çakışan.get(id(g2))
                            çakışan[id(g2)] = j if önceki is None else min(önceki, j)
    return çakışan, kelime_gez


def _ara_katman_dene(g, j, kelime_gez):
    """Hata katmanı j'deki çakışmayı, ETİKETLEMEDEN, o katmanın biçimleri
    üzerinde bir bağlam koşuluyla ayırmayı dener.

    g'nin j. katmandaki geçişi (kaynak s -> hedef t); aynı kaynaktan FARKLI
    hedefe giden konumlardan ayıran bir bağlam, layer-(j-1) biçimleri üzerinde
    aranır. Bulunursa s->t geçişine sahip bütün gruplara o katman için bağlam
    yazılır (kural koşullu olur, yeni harf doğmaz). Böylece ayrım proto'da
    değil, gerçekte ayrıştığı alt dilde belirir.
    """
    z = g.zincir or [g.token]
    s = z[min(j - 1, len(z) - 1)]
    t = z[min(j, len(z) - 1)]
    if s == t:
        return False  # bu katmanda g zaten durağan
    if g.katman_bağlamı and j in g.katman_bağlamı:
        return False  # bu katmanda bağlam zaten denendi: ilerleme yok
    kendi, diğer = [], []
    for (kno, dal), (gez, gs, atla) in kelime_gez.items():
        if dal != g.dal:
            continue
        konumlar = [p for p in range(len(gez)) if gez[p][j - 1] != BOŞ]
        w = [gez[p][j - 1] for p in konumlar]
        for idx, p in enumerate(konumlar):
            if atla[p] or gez[p][j - 1] != s:
                continue
            (kendi if gez[p][j] == t else diğer).append((w, idx))
    bağlam = ayır_biçimlerle(kendi, diğer)
    if bağlam is None:
        return False
    for g2 in kelime_gez_grupları(kelime_gez, g.dal, j, s, t):
        if g2.katman_bağlamı is None:
            g2.katman_bağlamı = {}
        g2.katman_bağlamı[j] = bağlam
    return True


def kelime_gez_grupları(kelime_gez, dal, j, s, t):
    """j. katmanda s->t geçişine sahip (çakışan değil) bütün grupları toplar."""
    bulunan = {}
    for (kno, d), (gez, gs, atla) in kelime_gez.items():
        if d != dal:
            continue
        for p in range(len(gez)):
            if atla[p] or gs[p] is None:
                continue
            if gez[p][j - 1] == s and gez[p][j] == t:
                bulunan[id(gs[p])] = gs[p]
    return list(bulunan.values())


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
    """Çakışan bir zincirin YALNIZ hata katmanındaki ara düğümüne alt simge
    takar (zincirin tamamına değil): ayrım, gerektiği derinlikte doğar, daha
    sığ katmanlar paylaşılmaya devam eder. Damga bir katmanda yetmezse
    (öncül kural artık damgalı düğümü üretemiyorsa) çakışma döngüsü bir
    sonraki turda bir sol komşuyu da damgalar; böylece etiket olabildiğince
    derinde tutulur ve ancak zorlanınca ön dile doğru genişler.
    """
    def uygula(g, hata_katmanı):
        if not g.zincir or len(g.zincir) <= 2:
            return False
        if g.etiketli_konum is None:
            g.etiketli_konum = set()
        # Hata veren kuralın kaynak düğümü; zincirin gerçek orta-düğüm
        # aralığına kıstırılır (kısa zincirler son düğüme sabitlendiği için
        # hata katmanı boyu aşabilir). Düğüm zaten damgalıysa bir sol komşuya
        # kayılır: ayrım olabildiğince derinde tutulur, gerekirse ön dile
        # doğru genişler; en kötü durumda eski tam-damgalamaya iner.
        konum = min(hata_katmanı - 1, len(g.zincir) - 2)
        while konum >= 1 and konum in g.etiketli_konum:
            konum -= 1
        if konum < 1:
            return False  # bütün ara düğümler damgalı: ilerleme yok
        b = taban(g.zincir[konum])
        sayaç[b] = sayaç.get(b, 1) + 1
        g.zincir[konum] = b + alt_yazı(sayaç[b])
        g.etiketli_konum.add(konum)
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
            if k is None:
                yeni.append(w[i])
            elif dizi_mi(k.hedef):
                yeni.extend(dizi_harfleri(k.hedef))  # doğum: tek harf > çok
            else:
                yeni.append(k.hedef)
        w = [t for t in yeni if t != BOŞ]
        biçimler.append(list(w))
    return biçimler


# ---------------------------------------------------------------------------
# 7. aşama: ön dil inceltme (alt katmana erteleme)
# ---------------------------------------------------------------------------

_RAKAM_TERS = {a: str(i) for i, a in enumerate("₀₁₂₃₄₅₆₇₈₉")}


def _altsayı(tok):
    s = "".join(_RAKAM_TERS[c] for c in tok if c in _RAKAM_TERS)
    return int(s) if s else 1


def _sayaç_tohumu(atama):
    """Etiket sayaçlarını mevcut belirteçlerle çakışmayacak biçimde tohumlar."""
    sayaç = {}
    for tok in set(atama.values()):
        b = taban(tok)
        sayaç[b] = max(sayaç.get(b, 1), _altsayı(tok) if tok != b else 1)
    return sayaç


def _gruplar_kur(atama, korr_yerleri, hizalamalar, düzensiz):
    """Sabit bir atamadan grupları kurar; ayrışmayan çakışmayı TÜRETMEDEN
    erteler (azınlık refleks "her yerde" kalır, alt katmanda çözülür).

    _çakışma_çöz'ün son aşamasının türetimsiz kardeşidir: yeni Ön Dil harfi
    üretmez, yalnız proto'da ayrışabilen refleksleri bağlamlar. Ayrışmayanlar
    aşağı bırakılır; _tamamla'daki çözüm döngüsü (ara katman bağlamı / etiket)
    halleder, halledemezse istisna doğar ve birleşme reddedilir.
    """
    protolar = _proto_kelimeler(hizalamalar, atama)
    kova = {}
    for ç, tok in atama.items():
        for dal in DALLAR:
            if ç in düzensiz[dal]:
                continue
            kova.setdefault((tok, dal), {}).setdefault(ç[dal], set()).add(ç)

    def sıklık(çler):
        return sum(len(korr_yerleri[ç]) for ç in çler)

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
                    y for r2, ç2ler in refgrup.items() if r2 != refleks
                    for ç2 in ç2ler for y in korr_yerleri[ç2]
                ]
                bağlam = ayır(kendi, diğer, protolar) or "her yerde"
            gruplar.append(
                Grup(token=tok, dal=dal, refleks=refleks, bağlam=bağlam,
                     korrlar=tuple(sorted(çler)))
            )
    return gruplar


def _tamamla(atama, düzensiz, korr_yerleri, hizalamalar, metatezler,
             çiftler, en_az_katman):
    """Bir atamadan tam seriyi kurup kör türetimle doğrular.

    Döner: {gruplar, katman, tablolar, türevler, istisnalar, protolar,
    etiketli_sayısı, met_kuralları}. Ön dil inceltme bunu aday atamalar
    üzerinde çağırıp istisna sıfır kalan birleşmeleri kabul eder.
    """
    sayaç = _sayaç_tohumu(atama)
    protolar = _proto_kelimeler(hizalamalar, atama)
    gruplar = _gruplar_kur(atama, korr_yerleri, hizalamalar, düzensiz)
    for g in gruplar:
        g.zincir = _zincir_kur(g)
    katman = [
        max(max((len(g.zincir) - 1 for g in gruplar
                 if g.dal == dal and g.zincir), default=0), en_az_katman)
        for dal in DALLAR
    ]
    for g in gruplar:
        if g.zincir and dizi_mi(g.zincir[-1]):
            eksik = katman[g.dal] - (len(g.zincir) - 1)
            if eksik > 0:
                g.zincir = (g.zincir[:-1]
                            + [g.zincir[-2]] * eksik + [g.zincir[-1]])
    grup_bul = {(g.token, g.dal, g.refleks): g for g in gruplar}
    etiket_uygula = _etiketle(gruplar, sayaç)
    etiketli_sayısı = 0
    while True:
        tablolar = _katman_tablosu(gruplar, katman)
        çakışan, kelime_gez = _çakışmaları_bul(
            len(çiftler), hizalamalar, atama, grup_bul, metatezler,
            katman, tablolar, düzensiz,
        )
        if not çakışan:
            break
        değişiklik = False
        for g in gruplar:
            if id(g) not in çakışan:
                continue
            j = çakışan[id(g)]
            if _ara_katman_dene(g, j, kelime_gez):
                değişiklik = True
            elif _yol_değiştir(g):
                değişiklik = True
            elif etiket_uygula(g, j):
                değişiklik = True
                etiketli_sayısı += 1
        if not değişiklik:
            break
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
            if "".join(biçimler[-1]) != hedef_sözcük:
                istisnalar.append((kno, dal, hedef_sözcük, "".join(biçimler[-1])))
            kelime_türevi.append(biçimler)
        türevler.append(kelime_türevi)

    return {
        "gruplar": gruplar, "katman": katman, "tablolar": tablolar,
        "türevler": türevler, "istisnalar": istisnalar, "protolar": protolar,
        "etiketli_sayısı": etiketli_sayısı, "met_kuralları": met_kuralları,
    }


def _proto_say(atama):
    return len(set(atama.values()))


def _proto_inceleme(atama, düzensiz, korr_yerleri, hizalamalar, metatezler,
                    çiftler, en_az_katman, taban_sonuç):
    """Türetilmiş Ön Dil harflerini açgözlülükle TABANINA (ya da kardeş
    belirtece) geri katmayı dener; yalnız istisna sıfır kalan ve ön dil
    harfini gerçekten azaltan birleşmeleri tutar.

    Böylece "sırf alt katmanda ayrışacağı için" ön dilde duran harfler
    silinir; ayrım, gerçekte gerektiği katmanda (ara katman bağlamı/etiket
    ile) doğar. Kör doğrulayıcı güvencesi: kabul edilen her atama %100
    düzenlidir, dolayısıyla seri hiçbir zaman bozulmaz.
    """
    en_iyi_atama = dict(atama)
    en_iyi_sonuç = taban_sonuç
    while True:
        türetilmişler = sorted(
            {t for t in en_iyi_atama.values() if t != taban(t)},
            key=lambda t: (sum(1 for x in en_iyi_atama.values() if x == t), t),
        )
        kabul = False
        for Y in türetilmişler:
            if Y not in set(en_iyi_atama.values()):
                continue  # önceki birleşmeyle gitmiş olabilir
            b = taban(Y)
            kardeşler = sorted(
                {t for t in en_iyi_atama.values()
                 if taban(t) == b and t != Y},
                key=lambda t: (t != b, t),  # önce taban harfin kendisi
            )
            for konak in kardeşler:
                aday = {ç: (konak if x == Y else x)
                        for ç, x in en_iyi_atama.items()}
                if _proto_say(aday) >= _proto_say(en_iyi_atama):
                    continue
                sonuç = _tamamla(aday, düzensiz, korr_yerleri, hizalamalar,
                                 metatezler, çiftler, en_az_katman)
                if not sonuç["istisnalar"]:
                    en_iyi_atama, en_iyi_sonuç = aday, sonuç
                    kabul = True
                    break
            if kabul:
                break  # taban değişti: baştan tara
        if not kabul:
            break
    return en_iyi_atama, en_iyi_sonuç


# ---------------------------------------------------------------------------
# ana akış
# ---------------------------------------------------------------------------

def seri_oluştur(çiftler, dal_adları=("A", "B"), en_az_katman=0,
                 türetim_eşiği=1, ön_dil_incelt=False):
    sözcükler = [(list(a), list(b)) for _, a, b in çiftler]

    hizalamalar = []
    metatezler = []
    doğumlar = []
    for kno, (a, b) in enumerate(sözcükler):
        sütunlar, d_olayları = _doğum_ayıkla(hizala(a, b))
        sütunlar, olaylar = _metatez_ayıkla(sütunlar)
        hizalamalar.append(sütunlar)
        for sütun, çift in d_olayları:
            doğumlar.append((kno, sütun, çift))
        for sütun, çift in olaylar:
            metatezler.append((kno, sütun, çift))

    korr_yerleri = {}
    for kno, sütunlar in enumerate(hizalamalar):
        for s, ç in enumerate(sütunlar):
            korr_yerleri.setdefault(ç, []).append((kno, s))

    sayaç = {}
    # 1. aşama: sıfırdan soyut harf kurma (kümeleme)
    atama = _kümele(korr_yerleri, hizalamalar, sayaç, türetim_eşiği)
    # 2. aşama: kalan çakışmaların çözümü (bağlam / konak / türetim).
    # Burada tam çözülmüş (istisnasız) bir taban atama elde edilir.
    _g, türetilmiş, _p, düzensiz = _çakışma_çöz(
        atama, korr_yerleri, hizalamalar, sayaç, türetim_eşiği
    )

    # 3. aşama: taban seriyi kur (atama artık türetilmiş harfleri içeriyor)
    taban_sonuç = _tamamla(atama, düzensiz, korr_yerleri, hizalamalar,
                           metatezler, çiftler, en_az_katman)

    # 4. aşama (opsiyonel): ön dili incelt — alt katmanda ayrışabilen
    # türetilmiş harfleri tabanına geri katıp ayrımı gerçekte gerektiği
    # katmana ertele (yalnız istisna sıfır kalan birleşmeler kabul edilir;
    # düzenlilik bozulmaz). Pahalı (her aday için tam yeniden kurma) olduğundan
    # varsayılan kapalıdır; ön dil karşıtlıklarının çoğu katman 1'de hemen
    # ayrıştığından (indirgenemez proto karşıtlığı) kazanç genelde küçüktür.
    if ön_dil_incelt:
        atama, sonuç = _proto_inceleme(
            atama, düzensiz, korr_yerleri, hizalamalar, metatezler, çiftler,
            en_az_katman, taban_sonuç,
        )
    else:
        sonuç = taban_sonuç

    gruplar = sonuç["gruplar"]
    katman = sonuç["katman"]
    tablolar = sonuç["tablolar"]
    türevler = sonuç["türevler"]
    istisnalar = sonuç["istisnalar"]
    protolar = sonuç["protolar"]
    etiketli_sayısı = sonuç["etiketli_sayısı"]
    # ön dilde fiilen kalan türetilmiş harfler (inceltmeden sonra)
    türetilmiş = sorted({t for t in atama.values() if t != taban(t)})

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
        doğum_olayları=doğumlar,
    )
