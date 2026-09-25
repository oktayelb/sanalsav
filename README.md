# Sanal Sav

Farklı dillerin anlamca sıralı sözcük listelerinden (Swadesh-100) ortak, varsayımsal
bir **Ön Dil serisi** kurar: ön ana dil, ara ön diller ve bunları girdi dillere bağlayan
düzenli ses yasaları.

Amaç gerçek bir etimoloji savı değildir. Verilen listelerin, her adımı doğal bir ses
değişimi olan kurallarla ve istisnasız olarak ortak bir ataya bağlanabildiğini göstermek
ve bunun **maliyetini** (gereken ön dil harfi, kural, katman sayısı) ölçmektir. Akraba
diller az harfle, akrabasız diller çok harfle bağlanır.

## Kurulum

Python 3.10 ya da üstü yeterlidir; dış bağımlılık yoktur.

```sh
git clone https://github.com/oktayelb/sanalsav.git
cd sanalsav
python3 ana.py
```

## Kullanım

```sh
python3 ana.py                                  # Türkçe ~ İngilizce (varsayılan)
python3 ana.py türkçe azerbaycanca              # herhangi iki dil
python3 ana.py türkçe azerbaycanca türkmence    # ikiden çok dil
python3 ana.py almanca lehçe --en-uzun-yol 4    # daha kısa ses zincirleri
```

Dil adları `diller/<ad>.txt` dosyalarına çözülür (27 dil hazırdır, bkz.
[diller/README.md](diller/README.md)).

| Seçenek | Varsayılan | Anlamı |
|---|---|---|
| `--rapor YOL` | `rapor_<diller>.txt` | metin raporunun yolu |
| `--html YOL` | rapor adı + `.html` | etkileşimli görünümün yolu |
| `--adlar A,B` | dosya adları | dillerin görünen adları |
| `--en-uzun-yol N` | 5 | bir ön dil harfinden yansımasına en çok doğal adım |
| `--boşluk-cezası X` | 1.0 | hizalamada boşluk cezası |
| `--eşik N` | 1 | yeni harfin kurtarması gereken en az konum (1 = istisnasız) |
| `--tarama` | | harf ~ düzenlilik ödünleşim tablosunu yazdır |
| `--en-az-katman N` | 0 | dal başına en az katman |
| `--ön-dil-incelt` | | türetilmiş harfleri tabanına katmayı dene (yavaş) |

## Çıktı

**Metin raporu** (`rapor_tür_ing.txt`):

- Özet: ön dil harf sayısı, ara katman etiketleri, dalların ön dile uzaklığı,
  katman başına ortalama kural, ses düşmesi, istisna ve düzenlilik
- Katman katman harf dağarcığı ve kural sayısı
- Bütün ses yasaları, katman ve uygulanma sırasıyla
- Her sözcüğün türetimi: `*ÖnDil > *ara biçimler > çocuk dil`

**HTML görünümü** (`rapor_tür_ing.html`): Tarayıcıda açılır. Üstte ön ana dil, altında
her dilin ara katmanları, en altta girdi diller durur. Bir katmana basınca o katmandaki
harfler (doğan / yiten), yasalar (kaç konumda işlediği) ve bütün sözcüklerin biçimleri,
değişen harfler imlenmiş olarak görünür. Bir sözcüğe basınca her adımda hangi yasanın
işlediğiyle bütün yolu açılır. Adrese `#d=1&j=3` eklenirse 2. dilin 3. katmanı,
`#k=20` eklenirse 21. sözcüğün yolu doğrudan açılır.

## Nasıl çalışır

1. **Sesbiçim** (`sesbiçim/`): Harfler tek tek değil, özellik vektörü olarak tanımlıdır
   (ünlü: yükseklik, arkalık, yuvarlaklık, uzunluk; ünsüz: yer, biçim, ötümlülük). Tek
   özelliği bir basamak değişen harfler komşudur; `k -> f` gibi sıçramalar en kısa doğal
   yola bölünür (`k > g > ğ > v > f`). Yazıda olmayan söylenebilir sesler sanal harf
   olarak kendiliğinden üretilir.
2. **Hizalama** (`ondil/hizalama.py`): Aynı anlamdaki sözcükler sesbiçimsel ağırlıklı
   Needleman-Wunsch ile hizalanır. Boşluk cezası, akrabasız sözcüklerin yan yana
   yapıştırılmasını önler. Göçüşüm (`ab ~ ba`) ve uzun ünlü doğumu (`aː > ay`) ayrıca
   yakalanır.
3. **Ön dil harfleri** (`ondil/insa.py`): Ön dil sözcüğü, hizalamanın sütun başına bir
   sesidir. Her harf karşılığı (ör. Türkçe `b` ~ İngilizce `w`) tek bir ön dil harfine
   bağlanır. Aynı harf bir dilde farklı seslere gidiyorsa ayrım önce **doğal ortamlarla**
   (ön ünlü önünde, ünlüler arasında, ötümlü ünsüz ardında, ünlü uyumu…) ve **yasa
   sırasıyla** yapılır; olmazsa yeni harf türetilir (`b₂`).
4. **Katmanlar** (`ondil/zamanlama.py`): Her katmanın yasaları o katmanın gerçek
   biçimlerinden öğrenilir. İki ses zinciri çakışırsa önce gecikme (besleme karşıtı
   sıra), sonra başka bir doğal yol, en son ara harf etiketi (`g₃`) denenir. Dillerin
   ön dile uzaklığı eşit olmak zorunda değildir.
5. **Doğrulama**: Yasalar ön biçime körce (köken bilgisi olmadan) uygulanır; her sözcüğün
   her dilde hedef sözcüğü birebir üretmesi denetlenir.

## Örnek sonuçlar

Swadesh-100, varsayılan ayarlar, istisna 0 (düzenlilik %100):

| Diller | Ön dil harfi | Ara etiket | Katman | Kural / katman |
|---|---|---|---|---|
| Türkçe ~ İngilizce | 70 | 39 | 4 + 6 | 44,7 |
| Türkçe ~ Azerbaycanca | 39 | 9 | 5 + 5 | 18,5 |

Örnek türetimler (Türkçe ~ İngilizce):

```
ben ~ i      *ue₃l     > wen > ben                 *ue₃l     > i
sen ~ you    *ta₅u₃l   > sen                       *ta₅u₃l   > ɟ̥ou > şou > jou > you
köpek ~ dog  *d₂öpi₂k₂ > ɟöpek > ɟ̥öpek > köpek     *d₂öpi₂k₂ > domg > dog
```

## Proje yapısı

```
ana.py              komut satırı
ondil/hizalama.py   sözcük hizalaması
ondil/kurallar.py   ses yasası ortamları ve sıralı ayrım
ondil/insa.py       ön dil harfleri, kümeleme, seri kurulumu
ondil/zamanlama.py  katman katman yasa öğrenimi ve zamanlama
ondil/rapor.py      metin raporu
ondil/html.py       etkileşimli HTML görünümü
sesbiçim/           ünlü/ünsüz özellik uzayı ve doğal ses yolları
diller/             Swadesh-100 listeleri
tests/              testler
```

## Test

```sh
python3 -m unittest discover -s tests
```

## Değişiklikler

Bkz. [CHANGELOG.md](CHANGELOG.md).
