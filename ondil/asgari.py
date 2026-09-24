# -*- coding: utf-8 -*-
"""Asgari harfli Ön Dil serisi: az harf, çok katman, çok kural.

Klasik inşa (insa.py) bir Ön Dil harfi bir dalda bağlamla ayrışmayan iki
sese gidince YENİ HARF türetir (b₂, d₇ ...); Türkçe ~ İngilizce için ön dil
100'ü aşkın harfe çıkar. Bu modül aynı düzenlilik güvencesini (her sözcük
yalnız kurallarla, istisnasız türetilir) çok daha küçük bir alfabeyle
sağlar. Harf yerine KATMAN ve KURAL harcanır:

1) ÇAPA ALFABESİ. Her karşılıklık (ör. Türkçe b ~ İngilizce w) küçük bir
   çapa kümesinden (S) bir harfe bağlanır; çapa, bütün reflekslere en çok
   D doğal ses adımı uzaktadır (k -> f yasağı korunur: her kural harf
   grafiğinde TEK adımdır). S, |S| + işaret sayısı en küçük olacak biçimde
   aranır; D büyüdükçe çapa azalır, katman artar.

2) GIRTLAKSIL İŞARETLER (laringaller). Aynı çapa bir dalda birden çok sese
   gidiyorsa ayrım yeni harfle değil, çapanın ardına konan gizli bir
   gırtlaksıl işaretle (H¹, H², ... ; Hint-Avrupa *h₁ *h₂ *h₃ gibi) yapılır.
   İşaret, önündeki sesi "boyar": kural "X -> Y / H² önünde" biçimindedir.
   Aynı işaret harfleri BÜTÜN dallarda kullanılır; her sözcük biriminin
   ardında dal sırasıyla dizilmiş bir işaret öbeği vardır (0. dalın işareti
   önce). k. dal, ilk k katmanda öbeklerin başındaki işareti düşürerek kendi
   işaretini çapaya bitiştirir; bu yüzden dalların ön dile uzaklığı
   (katman sayısı) eşit olmak zorunda değildir. Öbekte yeri tutulması
   gereken ama o dalda işaret istemeyen birim boş işaret (H⁰) alır.
   İşaretler dalın son katmanında düşer (gırtlaksıllar zayıf sestir: tek
   adımda silinir).

3) RENKLENDİRME. Bir dalda (çapa, refleks) çifti bir "iz"dir: çapadan
   reflekse doğal yol boyunca katman katman yürür. Aynı işaret sınıfındaki
   izler, aynı katmanda aynı harfte bulunup farklı yöne gidemez (kurallar
   kördür). İzler sınıflara (H⁰ = işaretsiz, H¹, H², ...) açgözlü renk-
   lendirmeyle yerleştirilir; çakışma, eşdeğer başka bir doğal yol ya da
   yürüyüşün zamanlaması (erken/geç başlama) ile, olmazsa yeni sınıfla
   çözülür. Ara katmanlarda hiçbir etiketli (alt simgeli) harf doğmaz.

4) KÖR DOĞRULAMA. Kurallar yalnız ön biçime katman katman uygulanır;
   her sözcüğün her dalda hedef sözcüğü birebir üretmesi denetlenir.

Göçüşüm (ab ~ ba) ve uzun ünlü doğumu (aː > ay) iki dilde desteklenir;
doğum ve işaretli sözcük düşmesi, işaretlerle aynı anda son katmanda olur.
"""

import random
from collections import Counter
from dataclasses import dataclass, field

from sesbiçim.harf import (
    BOŞ, DOĞUM_KAYNAĞI, HARFLER, SANAL_HARFLER, dizi_harfleri, dizi_mi,
    dizi_yap, uzaklık, yollar, ünlü_mü,
)

from . import insa
from .hizalama import hizala
from .insa import KatmanKural, _kural_seç

_SANAL = set(SANAL_HARFLER)
_ÜST = "⁰¹²³⁴⁵⁶⁷⁸⁹"
İŞARET_KÖKÜ = "H"
GÖÇÜŞÜM_BAĞLAMI = "göçüşüm"


def işaret_adı(sınıf):
    """Sınıf numarasının işaret harfi: 0 -> H⁰ (boş işaret), 3 -> H³."""
    return İŞARET_KÖKÜ + "".join(_ÜST[int(c)] for c in str(sınıf))


def işaret_mi(tok):
    return tok.startswith(İŞARET_KÖKÜ) and len(tok) > 1 and tok[1] in _ÜST


@dataclass
class AsgariSeri:
    dal_adları: tuple
    çiftler: list
    hizalamalar: list
    çapalar: list  # kullanılan çapa harfleri (S)
    işaretler: list  # kullanılan işaret harfleri (H⁰ dahil)
    sütun_çapası: dict  # karşılıklık -> çapa
    sınıflar: list  # dal başına {(çapa, refleks): sınıf}
    izler: list  # dal başına {(çapa, refleks): katman katman harf zinciri}
    ön_katman: list  # dal başına işaret düşürme katmanı sayısı
    katman: list  # dal başına toplam katman sayısı
    proto_kelimeler: list
    tablolar: list  # dal başına {katman: [KatmanKural]}
    türevler: list  # [kelime][dal] -> katman katman biçimler
    istisnalar: list
    göçüşümler: list  # dal başına [(x, y)]
    doğum_olayları: list = field(default_factory=list)
    en_uzun_yol: int = 0
    arama_özeti: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# 1. aşama: hizalama
# ---------------------------------------------------------------------------

def _hizalamalar(çiftler, N, göçüşüm_yasak):
    """Klasik inşanın hizalamasını kullanır (iki dilde doğum + göçüşüm)."""
    hizalamalar, doğumlar, göçler = [], [], []
    insa.DALLAR = tuple(range(N))
    for kno, row in enumerate(çiftler):
        kelimeler = [list(w) for w in row[1:]]
        if N == 2:
            sütunlar, d_olayları = insa._doğum_ayıkla(hizala(*kelimeler))
            for sütun, çift in d_olayları:
                doğumlar.append((kno, sütun, çift))
            if kno not in göçüşüm_yasak:
                sütunlar, olaylar = insa._metatez_ayıkla(sütunlar)
                for sütun, çift in olaylar:
                    göçler.append((kno, sütun, çift))
        else:
            sütunlar = insa._hizala_çok(kelimeler)
        hizalamalar.append(sütunlar)
    return hizalamalar, doğumlar, göçler


# ---------------------------------------------------------------------------
# 2. aşama: çapa alfabesi (küçük S) ve karşılıklıkların çapalara dağıtımı
# ---------------------------------------------------------------------------

class _ÇapaArama:
    """|S| + (en kalabalık çapanın refleks çeşitliliği) en küçük olsun.

    Bir çapanın bir dalda k farklı refleksi varsa en az k-1 işaret gerekir;
    bu yüzden çeşitlilik, işaret sayısının alt sınırıdır. Asıl işaret
    sayısı renklendirmeden sonra belli olur; burada vekil ölçü kullanılır.
    """

    def __init__(self, sıklık, N, D, tohum=0):
        self.sıklık = sıklık
        self.korrlar = sorted(sıklık, key=lambda ç: (-sıklık[ç], ç))
        self.N = N
        self.D = D
        self.rnd = random.Random(tohum)
        self._uz = {}
        self._önbellek = {}
        # her karşılıklığa D içinde ulaşabilen harfler
        self.olur = {
            ç: [p for p in HARFLER if self.enuzak(p, ç) <= D]
            for ç in self.korrlar
        }

    def enuzak(self, p, ç):
        a = self._uz.get((p, ç))
        if a is None:
            ds = [uzaklık(p, y) for y in ç]
            a = (max(ds), sum(ds))
            self._uz[(p, ç)] = a
        return a[0] if isinstance(a, tuple) else a

    def toplam_yol(self, p, ç):
        self.enuzak(p, ç)
        return self._uz[(p, ç)][1]

    def dağıt(self, S):
        """Karşılıklıkları S'ye dağıtır; (puan, atama) ya da None."""
        anahtar = frozenset(S)
        if anahtar not in self._önbellek:
            self._önbellek[anahtar] = self._dağıt(sorted(S))
        return self._önbellek[anahtar]

    def _dağıt(self, S):
        izinli = {}
        for ç in self.korrlar:
            a = [p for p in S if self.enuzak(p, ç) <= self.D]
            if not a:
                return None
            izinli[ç] = a
        N = self.N
        çeşit = [{p: Counter() for p in S} for _ in range(N)]
        atama = {}

        def ekle(ç, p, k=1):
            atama[ç] = p
            for d in range(N):
                çeşit[d][p][ç[d]] += k
                if çeşit[d][p][ç[d]] == 0:
                    del çeşit[d][p][ç[d]]

        for ç in sorted(self.korrlar, key=lambda ç: (len(izinli[ç]), -self.sıklık[ç], ç)):
            p = min(
                izinli[ç],
                key=lambda p: (
                    max(len(çeşit[d][p]) + (ç[d] not in çeşit[d][p])
                        for d in range(N)),
                    self.enuzak(p, ç), self.toplam_yol(p, ç), p,
                ),
            )
            ekle(ç, p)

        def ençok():
            return max(len(çeşit[d][p]) for d in range(N) for p in S)

        # iyileştirme: en kalabalık hücreden bir refleks öbeğini taşı
        for _ in range(400):
            m = ençok()
            dolu = sorted((d, p) for d in range(N) for p in S
                          if len(çeşit[d][p]) == m)
            ilerledi = False
            for d, p in dolu:
                for r in sorted(çeşit[d][p], key=lambda r: (çeşit[d][p][r], r)):
                    öbek = [ç for ç in self.korrlar if atama[ç] == p and ç[d] == r]
                    ortak = set(S)
                    for ç in öbek:
                        ortak &= set(izinli[ç])
                    ortak.discard(p)
                    for q in sorted(ortak):
                        for ç in öbek:
                            ekle(ç, p, -1)
                            ekle(ç, q)
                        if all(len(çeşit[x][q]) < m for x in range(N)) and \
                                len(çeşit[d][p]) < m:
                            ilerledi = True
                            break
                        for ç in öbek:
                            ekle(ç, q, -1)
                            ekle(ç, p)
                    if ilerledi:
                        break
                if ilerledi:
                    break
            if not ilerledi:
                break

        # ikincil: çeşitliliği artırmadan yolları kısalt (daha az katman)
        m = ençok()
        for ç in self.korrlar:
            p = atama[ç]
            for q in sorted(izinli[ç], key=lambda q: (self.enuzak(q, ç), q)):
                if q == p or self.enuzak(q, ç) >= self.enuzak(p, ç):
                    continue
                ekle(ç, p, -1)
                ekle(ç, q)
                if all(len(çeşit[x][q]) <= m for x in range(N)):
                    break
                ekle(ç, q, -1)
                ekle(ç, p)

        m = ençok()
        kullanılan = sorted(set(atama.values()))
        yol = max(self.enuzak(atama[ç], ç) for ç in self.korrlar)
        sanal = sum(1 for p in kullanılan if p in _SANAL)
        puan = (len(kullanılan) + m, yol, sanal, len(kullanılan))
        return puan, atama

    def ara(self, boylar=range(3, 10), deneme=6, adım=50):
        """Her |S| için rastgele başlangıç + takas yerel araması."""
        adaylar = [p for p in HARFLER
                   if any(p in self.olur[ç] for ç in self.korrlar)]
        sonuçlar = []
        for n in boylar:
            en_iyi = None
            for _ in range(deneme):
                S = self.rnd.sample(adaylar, n)
                r = self.dağıt(S)
                if r is None:
                    continue
                puan, atama = r
                for _ in range(adım):
                    i = self.rnd.randrange(n)
                    yeni = list(S)
                    yeni[i] = self.rnd.choice(adaylar)
                    if len(set(yeni)) < n:
                        continue
                    r2 = self.dağıt(yeni)
                    if r2 is not None and r2[0] < puan:
                        S, (puan, atama) = yeni, r2
                if en_iyi is None or puan < en_iyi[0]:
                    en_iyi = (puan, sorted(S), atama)
            if en_iyi is not None:
                sonuçlar.append(en_iyi)
        sonuçlar.sort(key=lambda x: x[0])
        return sonuçlar


# ---------------------------------------------------------------------------
# 3. aşama: dal başına iz renklendirmesi (işaret sınıfları + zamanlama)
# ---------------------------------------------------------------------------

def _yol_adayları(A, R, en_çok=24):
    if dizi_mi(R):
        kaynak = DOĞUM_KAYNAĞI[R]
        return [p + [R] for p in yollar(A, kaynak, en_çok)]
    return yollar(A, R, en_çok)


def _dal_renklendir(izler, ön, T, geç_önce):
    """izler: [(çapa, refleks, ağırlık)]. Katman 1..ön işaret düşürmedir;
    yürüyüşler ön+1 .. ön+T katmanlarındadır.

    Döner: ({iz: sınıf}, {iz: zincir}, sınıf_sayısı) ya da None.
    Tutarlılık: (katman, harf, sınıf) -> tek hedef.
    """
    L = ön + T
    tablo = {}
    sınıf, zincir = {}, {}
    sıralı = sorted(izler, key=lambda z: (-z[2], z[0], z[1]))
    for A, R, _ in sıralı:
        yerleşti = False
        c = 0
        while not yerleşti:
            if c > 60:
                return None
            for p in _yol_adayları(A, R):
                ℓ = len(p) - 1
                if ℓ > T:
                    continue
                # işaretli düşme ve her doğum son katmana sabitlenir
                sabit = dizi_mi(R) or (c != 0 and R == BOŞ)
                zamanlar = [T - ℓ] if sabit else list(range(0, T - ℓ + 1))
                if geç_önce:
                    zamanlar.reverse()
                for t in zamanlar:
                    z = [A] * (ön + t + 1) + p[1:] + [R] * (T - t - ℓ)
                    uygun = True
                    for j in range(ön + 1, L + 1):
                        X = z[j - 1]
                        if X == BOŞ:
                            break
                        Y = tablo.get((j, X, c))
                        if Y is not None and Y != z[j]:
                            uygun = False
                            break
                    if not uygun:
                        continue
                    for j in range(ön + 1, L + 1):
                        if z[j - 1] == BOŞ:
                            break
                        tablo[(j, z[j - 1], c)] = z[j]
                    sınıf[(A, R)] = c
                    zincir[(A, R)] = z
                    yerleşti = True
                    break
                if yerleşti:
                    break
            c += 1
    return sınıf, zincir, max(sınıf.values(), default=0)


def _dal_planla(izler, ön, gevşeklik_listesi=(0, 1, 2, 3)):
    """En az sınıflı (sonra en sığ) renklendirmeyi arar."""
    en_kısa = max(
        (min(len(p) - 1 for p in _yol_adayları(A, R)) for A, R, _ in izler),
        default=0,
    )
    en_iyi = None
    for g in gevşeklik_listesi:
        for geç in (False, True):
            r = _dal_renklendir(izler, ön, en_kısa + g, geç)
            if r is None:
                continue
            puan = (r[2], g)
            if en_iyi is None or puan < en_iyi[0]:
                en_iyi = (puan, r, en_kısa + g)
    _, (sınıf, zincir, K), T = en_iyi
    return sınıf, zincir, K, T


# ---------------------------------------------------------------------------
# 4. aşama: ön biçimler, kural tabloları, kör türetim
# ---------------------------------------------------------------------------

def _ön_biçim(sütunlar, sütun_çapası, sınıflar, N):
    """Her birim: çapa + dal sırasıyla işaret öbeği (sondaki boşlar atılır)."""
    w = []
    for ç in sütunlar:
        A = sütun_çapası[ç]
        w.append(A)
        öbek = [sınıflar[d][(A, ç[d])] for d in range(N)]
        while öbek and öbek[-1] == 0:
            öbek.pop()
        w.extend(işaret_adı(c) for c in öbek)
    return w


def _ön_düşürme_kuralları(protolar, ön):
    """İlk `ön` katmanda her öbeğin BAŞINDAKİ işareti düşüren kurallar.

    Öbek başı, işaret olmayan bir harfin ardındadır. Önce kaba bağlam
    (ünlü ardında) denenir; ünsüz çapalar için harfe özgü bağlam yazılır.
    Her katmanda öbek başı yeniden hesaplanır.
    """
    tablolar = {}
    biçimler = [list(w) for w in protolar]
    for j in range(1, ön + 1):
        kurallar = {}
        yeni_biçimler = []
        for w in biçimler:
            yeni = []
            for i, t in enumerate(w):
                if işaret_mi(t) and i > 0 and not işaret_mi(w[i - 1]):
                    önceki = w[i - 1]
                    bağlam = ("ünlü ardında" if ünlü_mü(önceki)
                              else f"{önceki} ardında")
                    kurallar[(t, BOŞ, bağlam)] = KatmanKural(t, BOŞ, bağlam)
                    continue
                yeni.append(t)
            yeni_biçimler.append(yeni)
        biçimler = yeni_biçimler
        tablolar[j] = sorted(kurallar.values(),
                             key=lambda k: (k.kaynak, k.bağlam))
    return tablolar


def _dal_tablosu(zincirler, sınıflar, ön, L, işaretler, protolar,
                 göçler):
    """Bir dalın bütün katman kuralları."""
    tablo = {j: [] for j in range(1, L + 1)}
    for j, ks in _ön_düşürme_kuralları(protolar, ön).items():
        tablo[j].extend(ks)
    anahtarlar = {}
    for iz, z in zincirler.items():
        c = sınıflar[iz]
        for j in range(ön + 1, L + 1):
            if z[j - 1] == BOŞ:
                break
            anahtarlar[(j, z[j - 1], c)] = z[j]
    varsayılan = {(j, X): Y for (j, X, c), Y in anahtarlar.items() if c == 0}
    for (j, X, c), Y in sorted(anahtarlar.items(),
                               key=lambda kv: (kv[0][0], kv[0][2], kv[0][1])):
        if c == 0:
            if Y != X:
                tablo[j].append(KatmanKural(X, Y, "her yerde"))
        else:
            if Y != varsayılan.get((j, X), X):
                tablo[j].append(
                    KatmanKural(X, Y, f"{işaret_adı(c)} önünde"))
    # son katman: kalan bütün işaretler düşer
    for H in işaretler:
        tablo[L].append(KatmanKural(H, BOŞ, "her yerde"))
    if göçler:
        tablo[L + 1] = [
            KatmanKural(dizi_yap([x, y]), dizi_yap([y, x]), GÖÇÜŞÜM_BAĞLAMI)
            for x, y in göçler
        ]
    return {j: ks for j, ks in tablo.items()}


def _göçüşüm_uygula(w, kurallar):
    çiftler = {tuple(dizi_harfleri(k.kaynak)) for k in kurallar}
    w = list(w)
    i = 0
    while i < len(w) - 1:
        if (w[i], w[i + 1]) in çiftler:
            w[i], w[i + 1] = w[i + 1], w[i]
            i += 2
        else:
            i += 1
    return w


def kör_türet(proto, tablolar, katman):
    """Ön biçimi yalnız kurallarla (köken bilgisi olmadan) çocuk dile indirir."""
    w = list(proto)
    biçimler = [list(w)]
    for j in range(1, katman + 1):
        kurallar = tablolar.get(j, [])
        if kurallar and kurallar[0].bağlam == GÖÇÜŞÜM_BAĞLAMI:
            w = _göçüşüm_uygula(w, kurallar)
            biçimler.append(list(w))
            continue
        yeni = []
        for i in range(len(w)):
            k = _kural_seç(kurallar, w, i)
            if k is None:
                yeni.append(w[i])
            elif dizi_mi(k.hedef):
                yeni.extend(dizi_harfleri(k.hedef))
            else:
                yeni.append(k.hedef)
        w = [t for t in yeni if t != BOŞ]
        biçimler.append(list(w))
    return biçimler


# ---------------------------------------------------------------------------
# ana akış
# ---------------------------------------------------------------------------

def _kur(çiftler, dal_adları, hizalamalar, doğumlar, göçler, D, tohum,
         aday_sayısı):
    N = len(dal_adları)
    sıklık = Counter(ç for sütunlar in hizalamalar for ç in sütunlar)
    arama = _ÇapaArama(sıklık, N, D, tohum)
    adaylar = arama.ara()
    if not adaylar:
        return None

    özet = []
    en_iyi = None
    for puan, S, atama in adaylar[:aday_sayısı]:
        planlar = []
        for d in range(N):
            ağırlık = Counter()
            for ç, n in sıklık.items():
                ağırlık[(atama[ç], ç[d])] += n
            izler = [(A, R, n) for (A, R), n in ağırlık.items()]
            planlar.append(_dal_planla(izler, ön=d))
        K = max(p[2] for p in planlar)
        boş_gerekli = any(
            any(planlar[d][0][(atama[ç], ç[d])] == 0
                and any(planlar[e][0][(atama[ç], ç[e])] for e in range(d + 1, N))
                for d in range(N))
            for ç in sıklık
        )
        harf = len(set(atama.values())) + K + (1 if boş_gerekli else 0)
        derinlik = sum(d + p[3] for d, p in enumerate(planlar))
        özet.append((harf, len(set(atama.values())), K, derinlik, S))
        anahtar = (harf, derinlik)
        if en_iyi is None or anahtar < en_iyi[0]:
            en_iyi = (anahtar, S, atama, planlar)

    _, S, atama, planlar = en_iyi
    sınıflar = [p[0] for p in planlar]
    zincirler = [p[1] for p in planlar]
    ön_katman = list(range(N))
    katman = [ön_katman[d] + planlar[d][3] for d in range(N)]

    protolar = [_ön_biçim(s, atama, sınıflar, N) for s in hizalamalar]
    işaretler = sorted({t for w in protolar for t in w if işaret_mi(t)})

    göç_dal = [[] for _ in range(N)]
    for _, _, çift in göçler:
        if çift not in göç_dal[1]:
            göç_dal[1].append(çift)
    tablolar = [
        _dal_tablosu(zincirler[d], sınıflar[d], ön_katman[d], katman[d],
                     işaretler, protolar, sorted(göç_dal[d]))
        for d in range(N)
    ]
    for d in range(N):
        if göç_dal[d]:
            katman[d] += 1

    türevler, istisnalar = [], []
    for kno, row in enumerate(çiftler):
        kt = []
        for d in range(N):
            biçimler = kör_türet(protolar[kno], tablolar[d], katman[d])
            bulunan = "".join(biçimler[-1])
            if bulunan != row[1 + d]:
                istisnalar.append((kno, d, row[1 + d], bulunan))
            kt.append(biçimler)
        türevler.append(kt)

    return AsgariSeri(
        dal_adları=tuple(dal_adları), çiftler=çiftler,
        hizalamalar=hizalamalar, çapalar=sorted(set(atama.values())),
        işaretler=işaretler, sütun_çapası=atama, sınıflar=sınıflar,
        izler=zincirler, ön_katman=ön_katman, katman=katman,
        proto_kelimeler=protolar, tablolar=tablolar, türevler=türevler,
        istisnalar=istisnalar, göçüşümler=göç_dal, doğum_olayları=doğumlar,
        en_uzun_yol=D, arama_özeti=sorted(özet)[:8],
    )


def seri_oluştur(çiftler, dal_adları, en_uzun_yol=7, tohum=0, aday_sayısı=6):
    """Asgari harfli seri. Göçüşüm kuralı başka bir sözcükte yanlış yere
    düşerse o sözcüğün göçüşümü geri alınır (sıradan değişimle açıklanır)."""
    N = len(dal_adları)
    göçüşüm_yasak = set()
    while True:
        hizalamalar, doğumlar, göçler = _hizalamalar(çiftler, N, göçüşüm_yasak)
        seri = _kur(çiftler, dal_adları, hizalamalar, doğumlar, göçler,
                    en_uzun_yol, tohum, aday_sayısı)
        if seri is None:
            raise SystemExit(
                f"en uzun yol {en_uzun_yol} ile her karşılıklığa ulaşan "
                "çapa bulunamadı; --en-uzun-yol değerini büyütün")
        göç_kelimeleri = {kno for kno, _, _ in göçler}
        bozuk = {kno for kno, _, _, _ in seri.istisnalar}
        if not göç_kelimeleri or not bozuk:
            return seri
        # göçüşüm yanlış yere de uygulandıysa göçüşümü kaldır ve yeniden kur
        göçüşüm_yasak |= göç_kelimeleri
