# Aile Protosu — gerçek çok-dilli yeniden-kurulumla tez sınaması

Kaynak ağaç: `tüm_diller.md` (UPGMA, aile bilgisi GÖMÜLÜ DEĞİL). Ağaç **75** harf mesafesinde kesildi; ortaya çıkan her küme TEK bir çok-dilli Ön Dil (proto) olarak yeniden kuruldu. Buradaki sayılar UPGMA *ortalaması* değil, kümenin tamamını tek protodan türetmenin GERÇEK maliyetidir.

## 1. Küme bağdaşıklığı (gerçek aile protoları)

| Küme | dil | Ön Dil harfi | dil başına | düzenlilik | istisna |
|---|---:|---:|---:|---:|---:|
| Türkçe+Gagavuzca+Kazakça+Azerice+Türkmence | 5 | 128 | 25.6 | %100.0 | 0 |
| Slovakça+Çekçe+Slovence+Hırvatça+Boşnakça | 5 | 144 | 28.8 | %100.0 | 0 |
| İngilizce+İsveççe+Almanca+Hollandaca | 4 | 149 | 37.2 | %100.0 | 0 |
| İspanyolca+Portekizce+İtalyanca+Fransızca | 4 | 153 | 38.2 | %100.0 | 0 |
| Estonca+Fince | 2 | 67 | 33.5 | %100.0 | 0 |

Veri-türevli her küme tek protodan ucuza ve yüksek düzenlilikle kurulur — kümeler gerçek bağdaşık birimlerdir.

## 2. Grupların grubu (üst-proto / Hint-Avrupa düzeyi)

Küme protoları + tekil diller (12 girdi) birlikte beslendi: *Tür…, *Slo…, *İng…, *İsp…, *Est…, Arnavutça, Lehçe, Macarca, Romence, Tacikçe, Kürtçe, Litvanca.

- Üst-proto Ön Dil harfi: **1038** (dil başına 86.5)
- Düzenlilik: %97.8, istisna: 27

Üst düzeyde dil başına harf, aile-içi kümelerdekinden belirgin yüksektir: aile-içi yakınlık aileler-arası yakınlıktan ölçülebilir biçimde fazladır.

## 3. Denetim: aynı boyda KARMA küme

En büyük gerçek kümenin boyunda, her aileden birer dil seçilerek kasıtlı karma bir küme kuruldu:

| Küme | dil | Ön Dil harfi | dil başına | düzenlilik | istisna |
|---|---:|---:|---:|---:|---:|
| Türkçe+Gagavuzca+Kazakça+Azerice+Türkmence (gerçek aile) | 5 | 128 | 25.6 | %100.0 | 0 |
| Türkçe+Slovakça+İngilizce+İspanyolca+Estonca (karma) | 5 | 283 | 56.6 | %98.4 | 8 |

Aynı dil sayısında, gerçek aile kümesi karma kümeden belirgin ucuz ve daha düzenli; karma kümede istisnalar (kökendaş olmayan sözcükler) belirir. Akrabalık, harf maliyetinin DOĞRUDAN sonucudur.

