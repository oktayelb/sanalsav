# Değişiklik Günlüğü

Bu projedeki önemli değişiklikler bu dosyada tutulur. Biçim
[Keep a Changelog](https://keepachangelog.com/tr-TR/1.1.0/), sürümleme
[Anlamsal Sürümleme](https://semver.org/lang/tr/) esaslıdır. 2.0.0 öncesi sürümler git
geçmişinden geriye dönük çıkarılmıştır.

## [2.1.0] - 2026-09-25

### Eklenenler
- Açıklama uzunluğu (MDL) ölçütü: rapor, HTML ve `--tarama` seriyi ön dil sözlüğü,
  kurallar ve istisnalar için gereken bit sayısıyla da ölçer.
- Tek konumda işleyen (ezbere yakın) kural sayısı raporlanır.
- `--tarama` tablosuna tek tanıklı kural ve MDL sütunları eklendi.

### Düzeltilenler
- `--eşik` 1'den büyükken kural dışı bırakılan bir karşılık öğrenmeye kısıt olarak
  giriyor ve başka sözcükleri de bozuyordu (Türkçe ~ Azerbaycanca eşik 2'de 5 yerine 50
  istisna). Kural dışı konumlar artık serbesttir; çözülemeyen çakışmada ayrılabilen
  kısmın kuralları yine yazılır.

## [2.0.0] - 2026-09-25

Ön dil harf sayısı gerçekçi türetim ağaçları korunarak azaltıldı. Türkçe ~ İngilizce
Swadesh-100'de ön dil harfi 102'den 70'e, ses düşmesi 182/165'ten 115/99'a indi; istisna
yine 0.

### Eklenenler
- Doğal sınıf ortamları: ses yasaları komşu seslerin sınıfına koşullanabilir (ön/arka,
  yuvarlak/düz, dar/geniş ünlü; ötümlü/ötümsüz, genizsil, akıcı, patlamalı, sızıcı,
  kayıcı, dudaksıl, dişsil, damaksıl ünsüz), iki yanlı ortamlar (ünlüler arasında) ve
  ünlü uyumu (ön/arka ünlülü sözcükte).
- Sıralı ses yasaları: aynı harfe birden çok yasa uyarsa önce işleyen sözcüğü alır
  (karar listesi); raporda yasalar uygulanma sırasıyla listelenir.
- Katman katman yasa öğrenimi (`ondil/zamanlama.py`): her katmanın yasaları o katmanın
  gerçek biçimlerinden çıkarılır; çakışmalar önce gecikmeyle (besleme karşıtı sıra),
  sonra başka doğal yolla, en son etiketle çözülür.
- Etkileşimli HTML görünümü (`ondil/html.py`): ön dil, ara katmanlar ve girdi diller
  ağaç olarak; katman başına harf dağarcığı, yasalar ve sözcük biçimleri; sözcük başına
  tam türetim yolu. Her çalıştırmada rapor yanında üretilir.
- Raporda katman başına ortalama kural sayısı, katman katman harf/kural tablosu, ses
  düşmesi sayısı (ve sözcük boyu farkından kaçınılmaz olanı), ön dil sözcük uzunluğu.
- `--boşluk-cezası` ve `--en-uzun-yol` seçenekleri.
- Testler, `pyproject.toml`, `requirements.txt`, `.gitignore`, sürekli tümleştirme.

### Değişenler
- Hizalamada boşluklar cezalandırılır (varsayılan 1.0): akrabasız sözcükler artık yan
  yana yapıştırılmaz, karşılıklı harfler ses değişimiyle açıklanır. **Sonuçlar 1.x
  sürümünden farklıdır.**
- Kümelemede refleks paylaşmayan kümeler de birleşmeyi dener.
- Bir ön dil harfinin yansımalarına en çok 5 doğal adım (önceden 4).
- Göçüşüm, ikinci dilin son katmanında çıktı harfleri üzerinde uygulanır; başka bir
  sözcükte yanlış yere düşerse o sözcüğün göçüşümü geri alınır.
- Hiç işlemeyen yasalar tablodan atılır.
- README sadeleştirildi; kodlardan yorumlar kaldırıldı.

### Kaldırılanlar
- Eski ara katman onarım döngüsü ve kullanılmayan yardımcılar.
- Geliştirme sırasında denenen gizli "işaret" (laringal) harfli kodlama: harf sayısını
  düşürüyor ama gerçekçi olmayan türetim ağaçları veriyordu; hiç yayımlanmadı.

## [1.0.2] - 2026-09-24

### Kaldırılanlar
- Deneysel dil ağacı ve dil ailesi ön dili betikleri ile belgeleri depodan çıkarıldı.

## [1.0.1] - 2026-07-20

### Düzeltilenler
- İnşa aşamasında hata düzeltmesi.

## [1.0.0] - 2026-06-13

### Değişenler
- Depo düzenlendi, kullanım belgesi güncellendi.

## [0.4.0] - 2026-06-12

### Eklenenler
- İkiden çok dil desteği (yıldız hizalama ile ortak ön dil).
- Deneysel dil ağacı ve dil ailesi ön dili modları.
- 27 dilin Swadesh-100 listesi.
- Dil adıyla çalıştırma (`python3 ana.py türkçe ingilizce`).

## [0.3.0] - 2026-06-11

### Eklenenler
- Tutumluluk eşiği (`--eşik`) ve harf ~ düzenlilik taraması (`--tarama`).
- Türkçe ~ Azerbaycanca akraba çift denetimi.
- Ön dil harflerinin sıfırdan kümelemeyle kurulması; sanal harfler.
- Yedi bölgeli ünsüz sınıflandırması, uzun ünlüler ve uzun ünlü doğumu.
- Ara katmanlarda harf ayrımı (ön dilin ihtiyacı olmayan harfler ara dillerde doğar).
- Kademeli bağlam dağarcığı (kaba, harfe özgü, iki yanlı).

## [0.2.0] - 2026-06-11

### Eklenenler
- İlk çalışan sürüm: hizalama, kural çıkarımı, harf grafiği üzerinden doğal ses yolları,
  katmanlı ön dil serisi ve metin raporu (Türkçe ~ İngilizce).

## [0.1.0] - 2026-06-08

### Eklenenler
- Proje fikri ve varsayımsal yöntemler (README).
- Ses sınıflandırması taslağı ve dil listelerinin biçimi.

[2.1.0]: https://github.com/oktayelb/sanalsav/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/oktayelb/sanalsav/compare/4ec3d22...v2.0.0
[1.0.2]: https://github.com/oktayelb/sanalsav/compare/94b02ad...4ec3d22
[1.0.1]: https://github.com/oktayelb/sanalsav/compare/73ac812...94b02ad
[1.0.0]: https://github.com/oktayelb/sanalsav/compare/d5d335a...73ac812
[0.4.0]: https://github.com/oktayelb/sanalsav/compare/da61e62...d5d335a
[0.3.0]: https://github.com/oktayelb/sanalsav/compare/6d6e57f...da61e62
[0.2.0]: https://github.com/oktayelb/sanalsav/compare/a7998fb...6d6e57f
[0.1.0]: https://github.com/oktayelb/sanalsav/commits/a7998fb
