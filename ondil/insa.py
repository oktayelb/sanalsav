from dataclasses import dataclass, field

from sesbiçim.harf import (
    BOŞ, DOĞUM_KAYNAĞI, HARFLER, SANAL_HARFLER, alt_yazı, dizi_harfleri,
    dizi_mi, dizi_yap, taban, uzaklık, yol, yollar, ünlü_mü,
    özellik_uzaklığı,
)
from sesbiçim.ünsüz import ÜNSÜZLER

_SANAL_CEZA = 0.05
_SANAL_KÜME = set(SANAL_HARFLER)

from .hizalama import hizala
from . import kurallar, zamanlama
from .kurallar import (
    ayır, bağlam_işlevi, bağlam_özgüllük, sıralı_ayır,
)

DALLAR = (0, 1)


@dataclass
class Grup:
    token: str
    dal: int
    refleks: str
    bağlam: str = "her yerde"
    korrlar: tuple = ()
    zincir: list = None
    öncelik: int = 0
    serbest: bool = False


@dataclass
class KatmanKural:
    kaynak: str
    hedef: str
    bağlam: str
    gruplar: list = field(default_factory=list)
    öncelik: int = 50


@dataclass
class Seri:
    dal_adları: tuple
    çiftler: list
    hizalamalar: list
    metatez_olayları: list
    atama: dict
    korr_yerleri: dict
    gruplar: list
    proto_kelimeler: list
    katman: list
    tablolar: list
    türevler: list
    istisnalar: list
    türetilmiş: list
    düzensiz: list = None
    türetim_eşiği: int = 1
    etiketli_sayısı: int = 0
    doğum_olayları: list = field(default_factory=list)


def _metatez_ayıkla(sütunlar):
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


def _hizala_çok(kelimeler):
    N = len(kelimeler)
    ref = max(range(N), key=lambda i: len(kelimeler[i]))
    profil = []
    ref_kolon = []
    for c in kelimeler[ref]:
        kol = [BOŞ] * N
        kol[ref] = c
        profil.append(kol)
        ref_kolon.append(kol)
    for i in range(N):
        if i == ref:
            continue
        rk = 0
        bekleyen = []
        for r, x in hizala(kelimeler[ref], kelimeler[i]):
            if r != BOŞ:
                if bekleyen:
                    idx = profil.index(ref_kolon[rk])
                    for ek in bekleyen:
                        profil.insert(idx, ek)
                        idx += 1
                    bekleyen = []
                ref_kolon[rk][i] = x
                rk += 1
            else:
                kol = [BOŞ] * N
                kol[i] = x
                bekleyen.append(kol)
        for ek in bekleyen:
            profil.append(ek)
    return [tuple(kol) for kol in profil]


def _aday_seç(çift):
    en_iyi, en_puan = None, None
    yedek_iyi, yedek_puan = None, None
    for p in HARFLER:
        ds = [uzaklık(p, y) for y in çift]
        uzak = sum(1 for d in ds if d >= 99)
        sonlu = [d for d in ds if d < 99]
        ençok = max(sonlu) if sonlu else 0
        toplam = sum(sonlu)
        if p in çift:
            toplam -= 0.25
        if p in ÜNSÜZLER and ÜNSÜZLER[p][2]:
            toplam += 0.1
        if p in _SANAL_KÜME:
            toplam += _SANAL_CEZA
        c = (ençok, toplam)
        if uzak == 0:
            if en_puan is None or (c, p) < (en_puan, en_iyi):
                en_iyi, en_puan = p, c
        if yedek_puan is None or (uzak, c, p) < yedek_puan:
            yedek_iyi, yedek_puan = p, (uzak, c, p)
    return en_iyi if en_iyi is not None else yedek_iyi


def _proto_kelimeler(hizalamalar, atama):
    return [[atama[ç] for ç in sütunlar] for sütunlar in hizalamalar]


def _refleks_ayır(refgrup, korr_yerleri, protolar):
    def sıklık(çler):
        return sum(len(korr_yerleri[ç]) for ç in çler)

    sıralı = sorted(refgrup.items(), key=lambda kv: (-sıklık(kv[1]), kv[0]))
    gruplar = [(r, [y for ç in çler for y in korr_yerleri[ç]])
               for r, çler in sıralı]
    return sıralı_ayır(gruplar, protolar)


GEVŞEKLİK = 0.5

EN_UZUN_YOL = 5


def _çapa_bul(korrlar, korr_yerleri):
    en_iyi, en_puan = None, None
    for p in HARFLER:
        puan = 0.0
        uygun = True
        for ç in korrlar:
            ds = [uzaklık(p, y) for y in ç]
            if max(ds) > EN_UZUN_YOL:
                uygun = False
                break
            puan += len(korr_yerleri[ç]) * sum(ds)
        if p in _SANAL_KÜME:
            puan += _SANAL_CEZA
        if uygun and (en_puan is None or (puan, p) < (en_puan, en_iyi)):
            en_iyi, en_puan = p, puan
    return en_iyi


def _birleşebilir(k1, k2, korr_yerleri, protolar):
    korrlar = sorted(k1["korrlar"] | k2["korrlar"])
    çapa = _çapa_bul(korrlar, korr_yerleri)
    if çapa is None:
        return None

    for dal in DALLAR:
        gruplar = {}
        for ç in korrlar:
            gruplar.setdefault(ç[dal], []).append(ç)
        if len(gruplar) < 2:
            continue
        if _refleks_ayır(gruplar, korr_yerleri, protolar)[0] is None:
            return None
    return çapa


def _kümele(korr_yerleri, hizalamalar, sayaç, eşik):
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
    hak = 200000
    değişti = True
    while değişti and hak > 0:
        değişti = False
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

    değişti = True
    while değişti and hak > 0:
        değişti = False
        çiftler = sorted(
            (uzaklık(kümeler[i]["çapa"], kümeler[j]["çapa"]), i, j)
            for i in canlı for j in canlı if i < j
        )
        for _, i, j in çiftler:
            if i not in canlı or j not in canlı or hak <= 0:
                continue
            hak -= 1
            çapa = _birleşebilir(kümeler[i], kümeler[j], korr_yerleri, protolar)
            if çapa is None:
                continue
            kümeler[i]["korrlar"] |= kümeler[j]["korrlar"]
            kümeler[i]["çapa"] = çapa
            canlı.discard(j)
            yeniden_adlandır(i)
            değişti = True

    def küme_sıklığı(ki):
        return sum(len(korr_yerleri[ç]) for ç in kümeler[ki]["korrlar"])

    kalanlar = [ki for ki in sorted(canlı) if küme_sıklığı(ki) >= eşik]
    if not kalanlar:
        kalanlar = sorted(canlı)

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
    toplam = sum(len(korr_yerleri[ç]) for ç in çler)

    def puan(p):
        ceza = _SANAL_CEZA if taban(p) in _SANAL_KÜME else 0.0
        return ceza + sum(
            len(korr_yerleri[ç]) * sum(uzaklık(p, y) for y in ç)
            for ç in çler
        ) / toplam

    adaylar = [(puan(p), 0, p) for p in HARFLER]
    for t in kullanılan_tokenlar:
        if t != taban(t):
            adaylar.append((puan(taban(t)) + 0.01, 1, t))
    adaylar.sort()
    return adaylar


def _çakışma_çöz(atama, korr_yerleri, hizalamalar, sayaç, eşik=1,
                 ön_düzensiz=None):
    türetilmiş = []
    düzensiz = [set(d) for d in ön_düzensiz] if ön_düzensiz else [set() for _ in DALLAR]
    denenmiş = {}
    deneme_hakkı = 4000

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
            _, takılan = _refleks_ayır(refgrup, korr_yerleri, protolar)
            if takılan:
                refleks = min(takılan, key=lambda r: (sıklık(refgrup[r]), r))
                sorunlu = (tok, dal, refgrup[refleks])
                break

        if sorunlu is None:
            break

        tok, dal, çler = sorunlu
        for ç in çler:
            denenmiş.setdefault(ç, set()).add(tok)
        if sıklık(çler) < eşik:
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

    protolar = _proto_kelimeler(hizalamalar, atama)
    gruplar = []
    for (tok, dal) in sorted(kova):
        refgrup = kova[(tok, dal)]
        ayrım, _ = _refleks_ayır(refgrup, korr_yerleri, protolar)
        assert ayrım is not None, (tok, dal)
        for refleks, çler in sorted(refgrup.items()):
            bağlam, öncelik = ayrım[refleks]
            gruplar.append(
                Grup(token=tok, dal=dal, refleks=refleks, bağlam=bağlam,
                     korrlar=tuple(sorted(çler)), öncelik=öncelik)
            )
    return gruplar, türetilmiş, protolar, düzensiz


def _zincir_kur(g):
    b = taban(g.token)
    if dizi_mi(g.refleks):
        kaynak = DOĞUM_KAYNAĞI[g.refleks]
        if b == kaynak:
            return [g.token, g.refleks]
        return [g.token] + yol(b, kaynak)[1:] + [g.refleks]
    if g.refleks == g.token:
        return None
    if g.refleks == b:
        return [g.token, b]
    return [g.token] + yol(b, g.refleks)[1:]


def _yol_seçenekleri(g):
    b = taban(g.token)
    R = g.refleks
    if R == g.token:
        return None
    if dizi_mi(R):
        kaynak = DOĞUM_KAYNAĞI[R]
        yl = [[b]] if b == kaynak else yollar(b, kaynak, 24)
        return [[g.token] + p[1:] + [R] for p in yl]
    if R == b:
        return [[g.token, b]]
    return [[g.token] + p[1:] for p in yollar(b, R, 24)]


def _kural_seç(kurallar, w, i):
    adaylar = [
        k for k in kurallar
        if k.kaynak == w[i] and bağlam_işlevi(k.bağlam)(w, i)
    ]
    if not adaylar:
        return None
    return min(adaylar, key=lambda k: (k.öncelik, bağlam_özgüllük(k.bağlam)))


GÖÇÜŞÜM = "göçüşüm"


def kör_türet(proto, dal, tablolar, katman, metatez_kuralları=None):
    w = list(proto)
    biçimler = [list(w)]
    for j in range(1, katman + 1):
        ks = tablolar.get(j, [])
        if ks and ks[0].bağlam == GÖÇÜŞÜM:
            çiftler = {tuple(dizi_harfleri(k.kaynak)) for k in ks}
            w = list(w)
            i = 0
            while i < len(w) - 1:
                if (w[i], w[i + 1]) in çiftler:
                    w[i], w[i + 1] = w[i + 1], w[i]
                    i += 2
                else:
                    i += 1
            biçimler.append(list(w))
            continue
        yeni = []
        for i in range(len(w)):
            k = _kural_seç(tablolar.get(j, []), w, i)
            if k is None:
                yeni.append(w[i])
            elif dizi_mi(k.hedef):
                yeni.extend(dizi_harfleri(k.hedef))
            else:
                yeni.append(k.hedef)
        w = [t for t in yeni if t != BOŞ]
        biçimler.append(list(w))
    return biçimler


_RAKAM_TERS = {a: str(i) for i, a in enumerate("₀₁₂₃₄₅₆₇₈₉")}


def _altsayı(tok):
    s = "".join(_RAKAM_TERS[c] for c in tok if c in _RAKAM_TERS)
    return int(s) if s else 1


def _sayaç_tohumu(atama):
    sayaç = {}
    for tok in set(atama.values()):
        b = taban(tok)
        sayaç[b] = max(sayaç.get(b, 1), _altsayı(tok) if tok != b else 1)
    return sayaç


def _gruplar_kur(atama, korr_yerleri, hizalamalar, düzensiz):
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
        ayrım, _ = _refleks_ayır(refgrup, korr_yerleri, protolar)
        for sıra_no, (refleks, çler) in enumerate(
                sorted(refgrup.items(), key=lambda kv: (-sıklık(kv[1]), kv[0]))):
            if ayrım is not None:
                bağlam, öncelik = ayrım[refleks]
            else:
                bağlam, öncelik = "her yerde", 50 + sıra_no
            gruplar.append(
                Grup(token=tok, dal=dal, refleks=refleks, bağlam=bağlam,
                     korrlar=tuple(sorted(çler)), öncelik=öncelik)
            )
    return gruplar


def _tamamla(atama, düzensiz, korr_yerleri, hizalamalar, metatezler,
             çiftler, en_az_katman):
    sayaç = _sayaç_tohumu(atama)
    protolar = _proto_kelimeler(hizalamalar, atama)
    gruplar = _gruplar_kur(atama, korr_yerleri, hizalamalar, düzensiz)
    for g in gruplar:
        g.zincir = _zincir_kur(g)
    grup_bul = {(g.token, g.dal, g.refleks): g for g in gruplar}
    met_kuralları = sorted({çift for _, _, çift in metatezler})

    katman, tablolar = [], []
    etiketli_sayısı = 0
    for dal in DALLAR:
        dal_grupları = [g for g in gruplar if g.dal == dal]
        serbestler = []
        sözcükler, sütun_grubu = [], []
        for kno, sütunlar in enumerate(hizalamalar):
            sg = {}
            for s, ç in enumerate(sütunlar):
                tok = atama[ç]
                if ç in düzensiz[dal]:
                    g = Grup(token=tok, dal=dal, refleks=tok, serbest=True)
                    serbestler.append(g)
                    sg[s] = g
                else:
                    sg[s] = grup_bul[(tok, dal, ç[dal])]
            sözcükler.append(list(range(len(sütunlar))))
            sütun_grubu.append(sg)
        T0 = max([len(g.zincir) - 1 for g in dal_grupları if g.zincir] + [0])
        T, tablo, etiket, _ = zamanlama.zamanla(
            dal_grupları + serbestler, sözcükler, sütun_grubu,
            T0, sayaç, en_az_katman)
        etiketli_sayısı += etiket
        katman.append(T)
        tablolar.append({
            jj: sorted((KatmanKural(x, y, b, öncelik=o) for x, y, b, o in ks),
                       key=lambda k: (k.kaynak, k.öncelik, k.hedef))
            for jj, ks in tablo.items()
        })
    for g in gruplar:
        if g.zincir and all(x == g.token for x in g.zincir):
            g.zincir = None
    if met_kuralları:
        katman[1] += 1
        tablolar[1][katman[1]] = [
            KatmanKural(dizi_yap([x, y]), dizi_yap([y, x]), GÖÇÜŞÜM)
            for x, y in met_kuralları
        ]

    for dal in DALLAR:
        kullanılan = set()
        for kno in range(len(çiftler)):
            w = list(protolar[kno])
            for j in range(1, katman[dal] + 1):
                ks = tablolar[dal].get(j, [])
                if ks and ks[0].bağlam == GÖÇÜŞÜM:
                    kullanılan |= {id(k) for k in ks}
                    w = kör_türet(w, dal, {1: ks}, 1)[-1]
                    continue
                for i in range(len(w)):
                    k = _kural_seç(ks, w, i)
                    if k is not None:
                        kullanılan.add(id(k))
                w = kör_türet(w, dal, {1: ks}, 1)[-1]
        for j in tablolar[dal]:
            tablolar[dal][j] = [k for k in tablolar[dal][j] if id(k) in kullanılan]

    türevler = []
    istisnalar = []
    for kno, row in enumerate(çiftler):
        kelimeler = row[1:]
        kelime_türevi = []
        for dal in DALLAR:
            hedef_sözcük = kelimeler[dal]
            biçimler = kör_türet(protolar[kno], dal, tablolar[dal], katman[dal])
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
                continue
            b = taban(Y)
            kardeşler = sorted(
                {t for t in en_iyi_atama.values()
                 if taban(t) == b and t != Y},
                key=lambda t: (t != b, t),
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
                break
        if not kabul:
            break
    return en_iyi_atama, en_iyi_sonuç


def seri_oluştur(çiftler, dal_adları=("A", "B"), en_az_katman=0,
                 türetim_eşiği=1, ön_dil_incelt=False, göçüşüm_yasak=frozenset()):
    global DALLAR
    kurallar.MIN_BAĞLAM_DESTEĞİ = max(2, türetim_eşiği)
    sözcükler = [[list(w) for w in row[1:]] for row in çiftler]
    N = len(sözcükler[0])
    DALLAR = tuple(range(N))
    if len(dal_adları) != N:
        dal_adları = tuple(f"Dil{i + 1}" for i in range(N))

    hizalamalar = []
    metatezler = []
    doğumlar = []
    for kno, kelimeler in enumerate(sözcükler):
        if N == 2:
            a, b = kelimeler
            sütunlar, d_olayları = _doğum_ayıkla(hizala(a, b))
            olaylar = []
            if kno not in göçüşüm_yasak:
                sütunlar, olaylar = _metatez_ayıkla(sütunlar)
            for sütun, çift in d_olayları:
                doğumlar.append((kno, sütun, çift))
            for sütun, çift in olaylar:
                metatezler.append((kno, sütun, çift))
        else:
            sütunlar = _hizala_çok(kelimeler)
        hizalamalar.append(sütunlar)

    korr_yerleri = {}
    for kno, sütunlar in enumerate(hizalamalar):
        for s, ç in enumerate(sütunlar):
            korr_yerleri.setdefault(ç, []).append((kno, s))

    sayaç = {}
    atama = _kümele(korr_yerleri, hizalamalar, sayaç, türetim_eşiği)
    _g, türetilmiş, _p, düzensiz = _çakışma_çöz(
        atama, korr_yerleri, hizalamalar, sayaç, türetim_eşiği
    )

    taban_sonuç = _tamamla(atama, düzensiz, korr_yerleri, hizalamalar,
                           metatezler, çiftler, en_az_katman)

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
    türetilmiş = sorted({t for t in atama.values() if t != taban(t)})

    met_kelimeleri = {kno for kno, _, _ in metatezler}
    if met_kelimeleri and any(dal == 1 for _, dal, _, _ in istisnalar):
        return seri_oluştur(çiftler, dal_adları, en_az_katman, türetim_eşiği,
                            ön_dil_incelt, göçüşüm_yasak | met_kelimeleri)

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

