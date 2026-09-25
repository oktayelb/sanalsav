from sesbiçim.harf import BOŞ, alt_yazı, dizi_mi, taban

from .kurallar import sıralı_ayır

EN_ÇOK_TUR = 3000
EK_KATMANLAR = (0, 1, 2, 3, 4, 6, 8)


def _biçimler(sıra, zincir, j):
    çıktı = []
    for s in sıra:
        t = zincir[s][j]
        if t != BOŞ:
            çıktı.append((t, s))
    return çıktı


def katman_öğren(sözcükler, zincirler, j):
    önceki = [[t for t, _ in _biçimler(sıra, zincirler[k], j - 1)]
              for k, sıra in enumerate(sözcükler)]
    öbek = {}
    sütun_yeri = {}
    for k, sıra in enumerate(sözcükler):
        for i, (t, s) in enumerate(_biçimler(sıra, zincirler[k], j - 1)):
            z = zincirler[k][s]
            öbek.setdefault(t, {}).setdefault((z[j], id(z)), []).append((k, i))
            sütun_yeri[(k, i)] = s
    kurallar = {}
    çakışmalar = []
    for X in sorted(öbek):
        anahtarlar = öbek[X]
        hedefler = {a[0] for a in anahtarlar}
        if len(hedefler) == 1:
            (Y,) = hedefler
            if Y != X:
                kurallar[(X, Y, "her yerde")] = 0
            continue
        boy = {}
        for (Y, _), yy in anahtarlar.items():
            boy[Y] = boy.get(Y, 0) + len(yy)
        sıralı = sorted(anahtarlar.items(),
                        key=lambda kv: (-boy[kv[0][0]], str(kv[0][0]), -len(kv[1])))
        ayrım, takılan = sıralı_ayır(sıralı, önceki, hedef=lambda a: a[0])
        if ayrım is None:
            çakışmalar.append((X, takılan, {
                a: [(k, sütun_yeri[(k, i)]) for k, i in yy]
                for a, yy in anahtarlar.items()
            }))
            continue
        for (Y, _), (bağlam, öncelik) in ayrım.items():
            if Y == X and bağlam == "her yerde":
                continue
            anahtar = (X, Y, bağlam)
            kurallar[anahtar] = min(kurallar.get(anahtar, öncelik), öncelik)
    return [(x, y, b, o) for (x, y, b), o in kurallar.items()], çakışmalar


def _yollar(g):
    from .insa import _yol_seçenekleri
    return _yol_seçenekleri(g) or [[g.token]]


def _dene(gruplar, sözcükler, sütun_grubu, T, sayaç):
    for g in gruplar:
        yol_ = min(_yollar(g), key=len)
        g.yol_sırası = 0
        g.zincir = _yerleştir(yol_, T)

    def zincir_haritası():
        return [{s: g.zincir for s, g in sg.items()} for sg in sütun_grubu]

    def boşluk(z):
        if dizi_mi(z[-1]):
            return 0
        n = 0
        while n < len(z) - 1 and z[-1 - n - 1] == z[-1]:
            n += 1
        return n

    def ertele(z, q):
        return z[:q] + [z[q - 1]] + z[q:-1]

    def etiketle(g, başla):
        z = list(g.zincir)
        while başla > 1 and z[başla - 1] == z[başla]:
            başla -= 1
        son = len(z) - 1
        while son > 0 and z[son] == z[-1]:
            son -= 1
        yeni = {}
        değişti = False
        for i in range(max(1, başla), son + 1):
            d = z[i]
            if d == BOŞ or dizi_mi(d) or d == g.token:
                continue
            if d not in yeni:
                b = taban(d)
                sayaç[b] = sayaç.get(b, 1) + 1
                yeni[d] = b + alt_yazı(sayaç[b])
            z[i] = yeni[d]
            değişti = True
        g.zincir = z
        return değişti

    def onar(g, j):
        z = g.zincir
        X = z[j - 1]
        hareket = z[j] != X
        pay = boşluk(z)
        if pay >= 1:
            if hareket and X != g.token:
                g.zincir = ertele(z, j)
                return True
            if not hareket:
                e = max((i for i in range(1, j) if z[i - 1] != z[i]), default=None)
                if e is not None and z[e - 1] != g.token:
                    kaydır = min(pay, j + 1 - e)
                    for _ in range(kaydır):
                        z = ertele(z, e)
                    g.zincir = z
                    return True
        yollar_ = [p for p in _yollar(g) if len(p) - 1 <= T]
        while g.yol_sırası + 1 < len(yollar_):
            g.yol_sırası += 1
            aday = _yerleştir(yollar_[g.yol_sırası], T)
            if aday != z:
                g.zincir = aday
                return True
        if X != z[-1] and X != g.token:
            etiketli = any(d != taban(d) and d != g.token for d in z[1:-1]
                           if d != BOŞ and not dizi_mi(d))
            return etiketle(g, 1 if etiketli else j - 1)
        return False

    def çakışma_onar(j, çakışma):
        X, takılan, yerler = çakışma
        adaylar = sorted(takılan, key=lambda a: (len(yerler[a]), str(a[0])))
        adaylar += sorted((a for a in yerler if a not in takılan),
                          key=lambda a: (len(yerler[a]), str(a[0])))
        for Y in adaylar:
            grs = {}
            for k, s in yerler[Y]:
                g = sütun_grubu[k][s]
                grs[id(g)] = g
            for g in sorted(grs.values(), key=lambda g: (g.token, str(g.refleks))):
                if onar(g, j):
                    return True
        return False

    for tur in range(EN_ÇOK_TUR):
        zh = zincir_haritası()
        tablo = {}
        ilk = None
        for j in range(1, T + 1):
            kurallar, çakışmalar = katman_öğren(sözcükler, zh, j)
            tablo[j] = kurallar
            if çakışmalar:
                ilk = (j, çakışmalar)
                break
        if ilk is None:
            return tablo, _etiket_say(gruplar), 0
        j, çakışmalar = ilk
        onarıldı = False
        onarılan = set()
        for çakışma in çakışmalar:
            gids = {id(sütun_grubu[k][s_]) for ys in çakışma[2].values()
                    for k, s_ in ys}
            if gids & onarılan:
                continue
            if çakışma_onar(j, çakışma):
                onarıldı = True
                onarılan |= gids
        if not onarıldı:
            break
    zh = zincir_haritası()
    tablo = {jj: katman_öğren(sözcükler, zh, jj)[0] for jj in range(1, T + 1)}
    çözülemeyen = sum(len(katman_öğren(sözcükler, zh, jj)[1]) for jj in range(1, T + 1))
    return tablo, _etiket_say(gruplar), çözülemeyen


def _etiket_say(gruplar):
    ön = {g.token for g in gruplar}
    return len({d for g in gruplar for d in g.zincir
                if d != BOŞ and not dizi_mi(d) and d != taban(d) and d not in ön})


def _yerleştir(yol_, T):
    ℓ = len(yol_) - 1
    if dizi_mi(yol_[-1]):
        return yol_[:-1] + [yol_[-2]] * (T - ℓ) + yol_[-1:]
    return yol_ + [yol_[-1]] * (T - ℓ)


def zamanla(gruplar, sözcükler, sütun_grubu, T_başlangıç, sayaç,
            en_az_katman=0):
    en_iyi = None
    taban_T = max(T_başlangıç, en_az_katman)
    for ek in EK_KATMANLAR:
        T = taban_T + ek
        deneme_sayaç = dict(sayaç)
        tablo, etiket, çözülemeyen = _dene(gruplar, sözcükler, sütun_grubu,
                                           T, deneme_sayaç)
        puan = (çözülemeyen, etiket, T)
        if en_iyi is None or puan < en_iyi[0]:
            en_iyi = (puan, T, tablo, etiket, çözülemeyen, deneme_sayaç,
                      {id(g): g.zincir for g in gruplar})
        if çözülemeyen == 0 and etiket == 0:
            break
    _, T, tablo, etiket, çözülemeyen, yeni_sayaç, zincirler = en_iyi
    sayaç.update(yeni_sayaç)
    for g in gruplar:
        g.zincir = zincirler[id(g)]
    return T, tablo, etiket, çözülemeyen

