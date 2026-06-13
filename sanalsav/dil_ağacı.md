# Dil Ailesi Ağacı (harf-sayısı mesafelerinden, UPGMA)

Kaynak matris: `/home/oktay/Masaüstü/code/python/sanalsav/sanalsav/tüm_diller.md` (27 dil). Bu ağaç YALNIZCA
Ön Dil harf-sayısı mesafelerinden üretilmiştir; hiçbir dil-ailesi
bilgisi koda girilmemiştir. Yöntem: ağırlıklı ortalama bağlantılı
hiyerarşik kümeleme (UPGMA). Her iç düğüm bir GRUPtur; üst düğümler
grupların gruplarıdır (en üstte tüm diller). Köşeli parantezdeki sayı,
o iki (alt)grubun birleştiği ortalama harf mesafesidir.

## Girintili ağaç
```
[102]  (27 dil)
   ├─ [70]  (5 dil)
   │  ├─ [39]  (2 dil)
   │  │  ├─ Türkçe
   │  │  └─ Gagavuzca
   │  └─ [68]  (3 dil)
   │     ├─ Kazakça
   │     └─ [61]  (2 dil)
   │        ├─ Azerice
   │        └─ Türkmence
   └─ [101]  (22 dil)
      ├─ Arnavutça
      └─ [98]  (21 dil)
         ├─ [77]  (6 dil)
         │  ├─ Lehçe
         │  └─ [71]  (5 dil)
         │     ├─ [54]  (2 dil)
         │     │  ├─ Slovakça
         │     │  └─ Çekçe
         │     └─ [64]  (3 dil)
         │        ├─ Slovence
         │        └─ [42]  (2 dil)
         │           ├─ Hırvatça
         │           └─ Boşnakça
         └─ [97]  (15 dil)
            ├─ Macarca
            └─ [94]  (14 dil)
               ├─ [91]  (9 dil)
               │  ├─ [72]  (4 dil)
               │  │  ├─ İngilizce
               │  │  └─ [66]  (3 dil)
               │  │     ├─ İsveççe
               │  │     └─ [54]  (2 dil)
               │  │        ├─ Almanca
               │  │        └─ Hollandaca
               │  └─ [82]  (5 dil)
               │     ├─ Romence
               │     └─ [75]  (4 dil)
               │        ├─ [69]  (2 dil)
               │        │  ├─ İspanyolca
               │        │  └─ Portekizce
               │        └─ [69]  (2 dil)
               │           ├─ İtalyanca
               │           └─ Fransızca
               └─ [92]  (5 dil)
                  ├─ [82]  (2 dil)
                  │  ├─ Tacikçe
                  │  └─ Kürtçe
                  └─ [92]  (3 dil)
                     ├─ Litvanca
                     └─ [67]  (2 dil)
                        ├─ Estonca
                        └─ Fince
```

## Yatay dendrogram
```
Türkçe     ─────────────────┼
                            │─────────────┼
Gagavuzca  ─────────────────┼             │
                                          │─────────────┼
Kazakça    ──────────────────────────────┼│             │
                                         │┼             │
Azerice    ───────────────────────────┼  │              │
                                      │──┼              │
Türkmence  ───────────────────────────┼                 │
                                                        │
Arnavutça  ─────────────────────────────────────────────┼
                                                        │
Lehçe      ──────────────────────────────────┼          │
                                             │          │
Slovakça   ────────────────────────┼         │────────┼ │
                                   │──────┼  │        │ │
Çekçe      ────────────────────────┼      │  │        │ │
                                          │──┼        │ │
Slovence   ────────────────────────────┼  │           │ │
                                       │──┼           │ │
Hırvatça   ───────────────────┼        │              │ │
                              │────────┼              │ │
Boşnakça   ───────────────────┼                       │─┼
                                                      │
Macarca    ───────────────────────────────────────────┼
                                                      │
İngilizce  ────────────────────────────────┼          │
                                           │───────┼  │
İsveççe    ─────────────────────────────┼  │       │  │
                                        │──┼       │  │
Almanca    ────────────────────────┼    │          │  │
                                   │────┼          │─┼│
Hollandaca ────────────────────────┼               │ ││
                                                   │ ││
Romence    ────────────────────────────────────┼   │ ││
                                               │   │ ││
İspanyolca ──────────────────────────────┼     │───┼ ││
                                         │──┼  │     ││
Portekizce ──────────────────────────────┼  │  │     ││
                                            │──┼     │┼
İtalyanca  ──────────────────────────────┼  │        │
                                         │──┼        │
Fransızca  ──────────────────────────────┼           │
                                                     │
Tacikçe    ────────────────────────────────────┼     │
                                               │────┼│
Kürtçe     ────────────────────────────────────┼    ││
                                                    │┼
Litvanca   ────────────────────────────────────────┼│
                                                   │┼
Estonca    ──────────────────────────────┼         │
                                         │─────────┼
Fince      ──────────────────────────────┼

(sola = yakın akraba; sağa = uzak. en sağ ≈ 102 harf)
```

## Eşik kesitleri (otomatik küme = ortaya çıkan aile)

**mesafe ≤ 60** → 4 çok-üyeli küme:
- Türkçe Gagavuzca
- Slovakça Çekçe
- Hırvatça Boşnakça
- Almanca Hollandaca

**mesafe ≤ 75** → 5 çok-üyeli küme:
- Türkçe Gagavuzca Kazakça Azerice Türkmence
- Slovakça Çekçe Slovence Hırvatça Boşnakça
- İngilizce İsveççe Almanca Hollandaca
- İspanyolca Portekizce İtalyanca Fransızca
- Estonca Fince

**mesafe ≤ 90** → 6 çok-üyeli küme:
- Türkçe Gagavuzca Kazakça Azerice Türkmence
- Lehçe Slovakça Çekçe Slovence Hırvatça Boşnakça
- İngilizce İsveççe Almanca Hollandaca
- Romence İspanyolca Portekizce İtalyanca Fransızca
- Tacikçe Kürtçe
- Estonca Fince

**mesafe ≤ 100** → 2 çok-üyeli küme:
- Türkçe Gagavuzca Kazakça Azerice Türkmence
- Lehçe Slovakça Çekçe Slovence Hırvatça Boşnakça Macarca İngilizce İsveççe Almanca Hollandaca Romence İspanyolca Portekizce İtalyanca Fransızca Tacikçe Kürtçe Litvanca Estonca Fince

## Not
Kümeler bilinen dil aileleriyle örtüşür (Türk, Roman, Germen, Slav,
Ural...) ama bu örtüşme GİRDİ DEĞİL, SONUÇtur: yalnız harf maliyetinden
çıkmıştır. Mutlak mesafelerde bir taban bulunduğundan (akraba olmayan
çiftler bile ~90+), yöntem her sıkı aileyi net çeker ama üst-aileleri
(ör. Hint-Avrupa'yı Ural'dan) tam ayıramaz; köşegen bloklar ailedir,
en üstteki büyük birleşme ise Hint-Avrupa + Ural süper-grubudur.
