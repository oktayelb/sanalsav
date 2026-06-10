# -*- coding: utf-8 -*-
"""Sesbiçimsel ağırlıklı sözcük hizalaması (Needleman-Wunsch).

İki sözcüğün harfleri, yerine koyma maliyeti = harf grafiğindeki uzaklık,
boşluk maliyeti = harfin silinme yolu uzunluğu olacak biçimde hizalanır.
Sonuç, her sütunu (a_harfi, b_harfi) olan bir karşılıklık listesidir;
boşluklar BOŞ ("0") ile gösterilir.
"""

from sesbiçim.harf import BOŞ, uzaklık


def _silme(h):
    return uzaklık(h, BOŞ)


def hizala(a, b):
    n, m = len(a), len(b)
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    Y = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = D[i - 1][0] + _silme(a[i - 1])
        Y[i][0] = "Y"
    for j in range(1, m + 1):
        D[0][j] = D[0][j - 1] + _silme(b[j - 1])
        Y[0][j] = "S"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            seçenekler = [
                (D[i - 1][j - 1] + uzaklık(a[i - 1], b[j - 1]), "Ç"),
                (D[i - 1][j] + _silme(a[i - 1]), "Y"),
                (D[i][j - 1] + _silme(b[j - 1]), "S"),
            ]
            D[i][j], Y[i][j] = min(seçenekler, key=lambda s: s[0])
    sütunlar = []
    i, j = n, m
    while i > 0 or j > 0:
        yön = Y[i][j]
        if yön == "Ç":
            sütunlar.append((a[i - 1], b[j - 1]))
            i, j = i - 1, j - 1
        elif yön == "Y":
            sütunlar.append((a[i - 1], BOŞ))
            i -= 1
        else:
            sütunlar.append((BOŞ, b[j - 1]))
            j -= 1
    return list(reversed(sütunlar))
