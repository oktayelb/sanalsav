# Tüm Dil Çiftleri — Ön Dil Harf Maliyeti

Üretim: `ana.py` / `seri_oluştur`, türetim eşiği 1 (%100 düzenlilik), 2026-06-11.

Her hücre, o iki dilin Swadesh-100 listesini ortak bir Ön Dile bağlamak için gereken **Ön Dil harf sayısıdır** (düşük = daha akraba). Diller ailelerine göre gruplanmıştır; köşegen bloklar (Türk dilleri; Germen dilleri) düşük değerleriyle kendini gösterir.

| ~ | Türkçe | Azerice | Türkmence | Almanca | İngilizce | Romence | Tacikçe | Kürtçe | Arnavutça |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Türkçe** | — | 69 | 71 | 104 | 102 | 105 | 101 | 100 | 103 |
| **Azerice** | 69 | — | 61 | 102 | 104 | 104 | 103 | 105 | 109 |
| **Türkmence** | 71 | 61 | — | 98 | 100 | 105 | 102 | 103 | 105 |
| **Almanca** | 104 | 102 | 98 | — | 73 | 94 | 96 | 93 | 96 |
| **İngilizce** | 102 | 104 | 100 | 73 | — | 93 | 95 | 96 | 96 |
| **Romence** | 105 | 104 | 105 | 94 | 93 | — | 98 | 94 | 101 |
| **Tacikçe** | 101 | 103 | 102 | 96 | 95 | 98 | — | 81 | 103 |
| **Kürtçe** | 100 | 105 | 103 | 93 | 96 | 94 | 81 | — | 99 |
| **Arnavutça** | 103 | 109 | 105 | 96 | 96 | 101 | 103 | 99 | — |

## Çiftler — en akrabadan en uzağa (Ön Dil harfi)

| # | çift | Ön Dil harfi | ses değişim kuralı |
|---:|---|---:|---:|
| 1 | Azerice ~ Türkmence | 61 | 175 |
| 2 | Türkçe ~ Azerice | 69 | 170 |
| 3 | Türkçe ~ Türkmence | 71 | 213 |
| 4 | Almanca ~ İngilizce | 73 | 239 |
| 5 | Tacikçe ~ Kürtçe | 81 | 289 |
| 6 | İngilizce ~ Romence | 93 | 331 |
| 7 | Almanca ~ Kürtçe | 93 | 376 |
| 8 | Almanca ~ Romence | 94 | 353 |
| 9 | Romence ~ Kürtçe | 94 | 382 |
| 10 | İngilizce ~ Tacikçe | 95 | 338 |
| 11 | İngilizce ~ Arnavutça | 96 | 354 |
| 12 | Almanca ~ Arnavutça | 96 | 360 |
| 13 | İngilizce ~ Kürtçe | 96 | 369 |
| 14 | Almanca ~ Tacikçe | 96 | 391 |
| 15 | Türkmence ~ Almanca | 98 | 356 |
| 16 | Romence ~ Tacikçe | 98 | 356 |
| 17 | Kürtçe ~ Arnavutça | 99 | 388 |
| 18 | Türkmence ~ İngilizce | 100 | 362 |
| 19 | Türkçe ~ Kürtçe | 100 | 376 |
| 20 | Türkçe ~ Tacikçe | 101 | 361 |
| 21 | Romence ~ Arnavutça | 101 | 371 |
| 22 | Türkmence ~ Tacikçe | 102 | 350 |
| 23 | Türkçe ~ İngilizce | 102 | 356 |
| 24 | Azerice ~ Almanca | 102 | 412 |
| 25 | Azerice ~ Tacikçe | 103 | 371 |
| 26 | Tacikçe ~ Arnavutça | 103 | 377 |
| 27 | Türkmence ~ Kürtçe | 103 | 382 |
| 28 | Türkçe ~ Arnavutça | 103 | 404 |
| 29 | Azerice ~ İngilizce | 104 | 374 |
| 30 | Azerice ~ Romence | 104 | 388 |
| 31 | Türkçe ~ Almanca | 104 | 399 |
| 32 | Türkmence ~ Romence | 105 | 399 |
| 33 | Türkçe ~ Romence | 105 | 401 |
| 34 | Türkmence ~ Arnavutça | 105 | 405 |
| 35 | Azerice ~ Kürtçe | 105 | 415 |
| 36 | Azerice ~ Arnavutça | 109 | 412 |

## Notlar

- Harf sayısı bir AKRABALIK ölçüsüdür: iki listeyi düzenli ses değişimiyle ortak ataya bağlamanın maliyeti. Türk dilleri birbirine ucuz, Hint-Avrupa dilleri Türkçeye pahalı bağlanır.
- Listeler ilk taslaktır (bkz. diller/README.md yazılış normalizasyonu); sözcük seçimleri düzeltildikçe değerler değişebilir.
- Değerler simetriktir varsayılmıştır (çift bir kez hesaplanıp yansıtılmıştır); dal sırası küçük sapmalar verebilir.

