# Aile Protosu — programın kendi deneyleriyle aile ağacı

Ağaç YALNIZCA programın yeniden-kurulum deneylerinden, aşağıdan yukarı ve hep İKİLİ kuruldu. Hiçbir aile bilgisi, eşik ya da UPGMA ortalaması DIŞARIDAN dayatılmadı. İki düğümü birleştirme maliyeti = temsilci protolarının ikili protosunun Ön Dil harf sayısıdır; hep iki girdi olduğundan ölçü grup boyutundan bağımsızdır (büyük aile protosunun şişen harf sayısı karara girmez). Her adımda en ucuz çift birleşir; köşeli parantezdeki sayı o birleşmenin gerçek proto harf maliyetidir. Kök maliyeti = tüm dillerin protoların-protosu (Hint-Avrupa düzeyi).

## 1. Birleşme sırası (programın çıkarım günlüğü)

| # | maliyet | birleşen A | birleşen B |
|---:|---:|---|---|
| 1 | 39 | Gagavuzca | Türkçe |
| 2 | 41 | Boşnakça | Hırvatça |
| 3 | 54 | Almanca | Hollandaca |
| 4 | 54 | Slovakça | Çekçe |
| 5 | 60 | Kazakça | Türkmence |
| 6 | 67 | Estonca | Fince |
| 7 | 67 | Fransızca | Italyanca |
| 8 | 68 | Azerbaycanca | (Gagavuzca+Türkçe) |
| 9 | 68 | Slovence | (Boşnakça+Hırvatça) |
| 10 | 69 | Ispanyolca | Portekizce |
| 11 | 70 | Isveççe | (Almanca+Hollandaca) |
| 12 | 74 | Lehçe | (Slovakça+Çekçe) |
| 13 | 76 | (Kazakça+Türkmence) | (Azerbaycanca+(Gagavuzca+Türkçe)) |
| 14 | 81 | Ingilizce | (Isveççe+(Almanca+Hollandaca)) |
| 15 | 81 | Romence | (Fransızca+Italyanca) |
| 16 | 84 | Kürtçe | Tacikçe |
| 17 | 90 | (Ispanyolca+Portekizce) | (Romence+(Fransızca+Italyanca)) |
| 18 | 90 | (Slovence+(Boşnakça+Hırvatça)) | (Lehçe+(Slovakça+Çekçe)) |
| 19 | 94 | Arnavutça | Litvanca |
| 20 | 103 | Macarca | (Estonca+Fince) |
| 21 | 107 | (Ingilizce+(Isveççe+(Almanca+Hollandaca))) | (Kürtçe+Tacikçe) |
| 22 | 118 | (Arnavutça+Litvanca) | ((Ingilizce+(Isveççe+(Almanca+Hollandaca)))+(Kürtçe+Tacikçe)) |
| 23 | 125 | ((Kazakça+Türkmence)+(Azerbaycanca+(Gagavuzca+Türkçe))) | ((Slovence+(Boşnakça+Hırvatça))+(Lehçe+(Slovakça+Çekçe))) |
| 24 | 132 | ((Ispanyolca+Portekizce)+(Romence+(Fransızca+Italyanca))) | (Macarca+(Estonca+Fince)) |
| 25 | 149 | ((Arnavutça+Litvanca)+((Ingilizce+(Isveççe+(Almanca+Hollandaca)))+(Kürtçe+Tacikçe))) | (((Kazakça+Türkmence)+(Azerbaycanca+(Gagavuzca+Türkçe)))+((Slovence+(Boşnakça+Hırvatça))+(Lehçe+(Slovakça+Çekçe)))) |
| 26 | 160 | (((Ispanyolca+Portekizce)+(Romence+(Fransızca+Italyanca)))+(Macarca+(Estonca+Fince))) | (((Arnavutça+Litvanca)+((Ingilizce+(Isveççe+(Almanca+Hollandaca)))+(Kürtçe+Tacikçe)))+(((Kazakça+Türkmence)+(Azerbaycanca+(Gagavuzca+Türkçe)))+((Slovence+(Boşnakça+Hırvatça))+(Lehçe+(Slovakça+Çekçe))))) |

## 2. Çıkarılan ağaç
```
[160]  (27 dil)
├─ [132]  (8 dil)
│  ├─ [90]  (5 dil)
│  │  ├─ [69]  (2 dil)
│  │  │  ├─ Ispanyolca
│  │  │  └─ Portekizce
│  │  └─ [81]  (3 dil)
│  │     ├─ Romence
│  │     └─ [67]  (2 dil)
│  │        ├─ Fransızca
│  │        └─ Italyanca
│  └─ [103]  (3 dil)
│     ├─ Macarca
│     └─ [67]  (2 dil)
│        ├─ Estonca
│        └─ Fince
└─ [149]  (19 dil)
   ├─ [118]  (8 dil)
   │  ├─ [94]  (2 dil)
   │  │  ├─ Arnavutça
   │  │  └─ Litvanca
   │  └─ [107]  (6 dil)
   │     ├─ [81]  (4 dil)
   │     │  ├─ Ingilizce
   │     │  └─ [70]  (3 dil)
   │     │     ├─ Isveççe
   │     │     └─ [54]  (2 dil)
   │     │        ├─ Almanca
   │     │        └─ Hollandaca
   │     └─ [84]  (2 dil)
   │        ├─ Kürtçe
   │        └─ Tacikçe
   └─ [125]  (11 dil)
      ├─ [76]  (5 dil)
      │  ├─ [60]  (2 dil)
      │  │  ├─ Kazakça
      │  │  └─ Türkmence
      │  └─ [68]  (3 dil)
      │     ├─ Azerbaycanca
      │     └─ [39]  (2 dil)
      │        ├─ Gagavuzca
      │        └─ Türkçe
      └─ [90]  (6 dil)
         ├─ [68]  (3 dil)
         │  ├─ Slovence
         │  └─ [41]  (2 dil)
         │     ├─ Boşnakça
         │     └─ Hırvatça
         └─ [74]  (3 dil)
            ├─ Lehçe
            └─ [54]  (2 dil)
               ├─ Slovakça
               └─ Çekçe
```

## 3. Maliyet kesitlerinde ortaya çıkan gruplar

Bir kesit değeri seçince, o maliyetin ALTINDA birleşmiş kollar birer grup sayılır (programın kendiliğinden bulduğu aileler ve alt-bölünmeleri):

**Kesit ≤ 50:**
- {Gagavuzca, Türkçe} (2)
- {Boşnakça, Hırvatça} (2)
- (tek başına: Ispanyolca, Portekizce, Romence, Fransızca, Italyanca, Macarca, Estonca, Fince, Arnavutça, Litvanca, Ingilizce, Isveççe, Almanca, Hollandaca, Kürtçe, Tacikçe, Kazakça, Türkmence, Azerbaycanca, Slovence, Lehçe, Slovakça, Çekçe)

**Kesit ≤ 70:**
- {Isveççe, Almanca, Hollandaca} (3)
- {Azerbaycanca, Gagavuzca, Türkçe} (3)
- {Slovence, Boşnakça, Hırvatça} (3)
- {Ispanyolca, Portekizce} (2)
- {Fransızca, Italyanca} (2)
- {Estonca, Fince} (2)
- {Kazakça, Türkmence} (2)
- {Slovakça, Çekçe} (2)
- (tek başına: Romence, Macarca, Arnavutça, Litvanca, Ingilizce, Kürtçe, Tacikçe, Lehçe)

**Kesit ≤ 90:**
- {Slovence, Boşnakça, Hırvatça, Lehçe, Slovakça, Çekçe} (6)
- {Ispanyolca, Portekizce, Romence, Fransızca, Italyanca} (5)
- {Kazakça, Türkmence, Azerbaycanca, Gagavuzca, Türkçe} (5)
- {Ingilizce, Isveççe, Almanca, Hollandaca} (4)
- {Estonca, Fince} (2)
- {Kürtçe, Tacikçe} (2)
- (tek başına: Macarca, Arnavutça, Litvanca)

## 4. Küme bağdaşıklığı (kendi ağacından, kesit ≤ 90)

Ağacın kendi bulduğu her aile, TEK bir çok-dilli Ön Dil olarak yeniden kuruldu (yıldız hizalama). Dil başına harf düşük ve düzenlilik %100 ise küme gerçek bağdaşık bir birimdir:

| Aile | dil | Ön Dil harfi | dil başına | düzenlilik | istisna |
|---|---:|---:|---:|---:|---:|
| Slovence+Boşnakça+Hırvatça+Lehçe+Slovakça+Çekçe | 6 | 192 | 32.0 | %99.7 | 2 |
| Ispanyolca+Portekizce+Romence+Fransızca+Italyanca | 5 | 200 | 40.0 | %100.0 | 0 |
| Kazakça+Türkmence+Azerbaycanca+Gagavuzca+Türkçe | 5 | 126 | 25.2 | %100.0 | 0 |
| Ingilizce+Isveççe+Almanca+Hollandaca | 4 | 149 | 37.2 | %100.0 | 0 |
| Estonca+Fince | 2 | 67 | 33.5 | %100.0 | 0 |
| Kürtçe+Tacikçe | 2 | 84 | 42.0 | %100.0 | 0 |

## 5. Denetim: aynı boyda KARMA küme

En büyük gerçek ailenin boyunda, her aileden birer dil seçilerek kasıtlı karma bir küme kuruldu. Aynı dil sayısında karma küme gerçek aileden belirgin pahalı ve daha az düzenli olur; akrabalık harf maliyetinin DOĞRUDAN sonucudur:

| Küme | dil | Ön Dil harfi | dil başına | düzenlilik | istisna |
|---|---:|---:|---:|---:|---:|
| Kazakça+Türkmence+Azerbaycanca+Gagavuzca+Türkçe (gerçek aile) | 5 | 126 | 25.2 | %100.0 | 0 |
| Slovence+Ispanyolca+Kazakça+Ingilizce+Estonca+Kürtçe (karma) | 6 | 333 | 55.5 | %98.7 | 8 |

