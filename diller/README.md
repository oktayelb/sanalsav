# Dil listeleri

Her dil bir dosyadır. Her satır `anlam sözcük` biçimindedir ve bütün dosyalar aynı
anlam sırasını (Swadesh-100) izler; program sözcükleri anlamlarıyla değil sırasıyla
eşleştirir. `#` ile başlayan satırlar açıklamadır.

- Yazılış esaslıdır; okunuş kullanılmaz.
- Eylemler kök biçimiyle verilir (iç, ye, gör…), `-mek/-mak` gibi ekler yapay kural
  üretmesin diye.
- Bütün harfler `sesbiçim/` tablolarında tanımlı olmalıdır; tanımsız harf varsa
  program hangi harf olduğunu söyleyerek durur.

## Mevcut diller (27)

| Aile | Diller |
|---|---|
| Türk | türkçe, azerbaycanca, türkmence, gagavuzca, kazakça |
| Germen | almanca, ingilizce, hollandaca, isveççe |
| Roman | romence, ispanyolca, italyanca, fransızca, portekizce |
| İran | tacikçe, kürtçe (Kurmancî) |
| Arnavut | arnavutça |
| Ural | estonca, fince, macarca |
| Balt | litvanca |
| Slav | slovence, hırvatça, boşnakça, slovakça, lehçe, çekçe |

## Yazılış normalleştirmesi

Sesbiçim tabloları Latin tabanlıdır; tabloda karşılığı olmayan harfler en yakın yazılı
harfe çevrilmiştir (her dosyanın başında belirtilir). Başlıcaları:

- Almanca `ß → ss`
- Romence `ă → ə`, `â/î → ı`, `ș → ş`, `ț → ţ`
- Kürtçe `ê → e`, `î → i`, `û → u`
- Arnavutça `ë → ə`, ünlü `y → ü` (`dh/gj/sh` gibi ikili harfler korunur)
- Türkmence `ä → ə`, `ž → j`, `ň → n`, `y → ı`, `ý → y`
- Tacikçe Kiril'den Latin'e (`ғ → ğ`, `қ → q`, `ҳ → h`, `х → x`, `ҷ → c`, `ч → ç`, `ш → ş`)
- Slav dilleri `c → ţ`, `č/ć → ç`, `š → ş`, `ž → j`, kayıcı `j → y`
- Estonca `õ → ı`; Fince ünlü `y → ü`; Slovakça uzun ünlüler kısalır, `ch → x`
- Kazakça `ä → ə`, `ñ` korunur
- Roman dilleri aksanları tabana indirir, `ç → s`, İspanyolca `ñ` korunur
- Hollandaca/İsveççe kayıcı `j → y`; İsveççe `å → o`, `ä → ə`, `y → ü`
- Lehçe/Çekçe/Macarca ıslıklılar sese göre (Macarca `s → ş`, `sz → s`, `zs → j`),
  `c [ts] → ţ`, `gy → c`
- Litvanca uzun/burunsu ünlüler sadeleşir
