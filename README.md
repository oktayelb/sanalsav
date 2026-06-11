Bu çalışma ,farklı dillere ait sözcük listelerinden ortak bir Ön Diller dizisi oluşturmayı hedefler.
Bu diziyi oluşturmanın yöntemleri henüz kararlaştırılmamıştır.
Ön diller sahip olması gereken özellikler, ortaya sundukları varsayımsal harfler ve sözcüklerin çocuk dillere benzemesi değil, bu varsayımsal köklerin sisteme girdi olarak verilen sözcük listelerine "en düşük istisna" ile kurallı bir biçimde dönüştüren ses değişimlerine sahip olmasıdır.
Bu yazılımın çıktısı, verilen dillerin atası olabilecek, düzenli ses değişim kuralları ile çocuk dillere dönüşebilecek bir Ön Diller serisidir.

Ses değişim yasaları her ne kadar üst üste bindiğinde çok değişik sonuçlar çıkarabilseler de  akustik ve fiziksel sınırları vardır. Bir ön dil yaratırken  sadece kolaylık olsun diye k->f diye bir kural yazmak her ne kadar matematiksel olarak kolay olan seçenek olsa da gerçekçi bir dil gelişimi izlenmesi için bu ses değişiminin k -> g -> v -> f şeklinde açıklanması doğal dillerin yapısı bakımından çok daha gerçekçidir. Bu nedenle bu çalışma yalnız bir Ön dil oluşturmak gibi bir kısıtlamaya tabi olmadan, ses değişimlerini doğal olarak açıklayabileceği sayıda sıralı Ön Dil oluşturmayı hedefler.
Örnek olarak Türkçe  bir ve İngilizce one sözcüklerini düşünecel olursak

---"VARSAYIMSAL ÖRNEK"---

1. ilk Ön Dil : *winer
2. ilk Türkçe Ön Dili: *bier (w->b, n-> 0), ilk İngilizce Ön Dili: *oner  (wi -> o)
3. Türkçe : bir (ie -> i),  İngilizce : *one  ( -r -> 0)
------------------------------------------------------------

Bu örnek, doğruluktan çok sistemin birden çok katmanda bu sonucu yapaileceğini göstermek için konulmuştur
En önemli kıstas, kullanılan kuralların  en yüksek düzenlilikte (kuralbozansızlık) olması ve sesbiçimsel olarak gerçekçi olması (w ->b örneği gibi)


1. VARSAYIMSAL YÖNTEM

Ses değişimleri 4 kategoride incelenebilir
    1. tekil harf değişimi  (tek harfin başka harfe yahut boş harfe (0) dönüşmesi)
    2. Grupça harf değişimi (tek harften çok harf, çok harften tek harf)
    3. harflerin yer değiştirmesi (metathesis, göçüşüm)
    4  Yeni Harf eklenmesi  (boş harfin (0) bir harfe dönüşmesi)

Bu dört işlemi ses kurallarının tümü olarak kabul eden bir model düşünülebilir.

2. VARSAYIMSAL YÖNTEM

Modeli harf verisi üzerinde çalışmaya zorlamak yerine harfleri (ve böylece sözcükleri) matematiksel biçime sokup bu şekilde bir makina öğrenmesi algoritması ile öğretmek. Bu şekilde modelin sonuç olarak vereceği sayıyı tekrardan bir işlemden geçirerek harflere döndürüp, bu iki dilin atası olabilecek diller serisini bulabiliriz.

3. VARSAYIMSAL YÖNTEM

Önden belirlenen bir Ön Dil katman sayısı üzerinden modeli öğrenmeye zorlayarak sonsuz dil katman sorununu çözüp, belirli aşamada (örneğin 2,3. Kullanıcının girdisine bağlı) ortak dil problemini çözmeye zorlayabiliriz. Bu yöntemde iki dilin alfabeleri toplamı * katman sayısı kadar bir alfabe ile ilk dili başlatıp daha sonra buradan devam edilebilir belki. Bu hesap doğru olmasa da en yukardan başlamak,  en alttan başlayarak ilerlemekten daha kolay görünüyor.

4. VARSAYIMSAL YÖNTEM

Verilen dillerin sözcük listelerini tek tek (her bir ortak sözcük bazında) inceleyen, halihazırdaki Ön dil savına uymayan bir kural geldiğinde yeni bir katman ekleyen bir yaklaşım. 


Sorun şu ki yeterince farklı harfler varsayılarak (p1,p2,p3,p4,p5...) bu problem nafile bir şekilde çözülebilir, ancak bizim yöntemlerimize bunu asgari harf ile yapmayı öğretmemiz gerekli. 

Aynı şekilde bir sorun: aşırı spesifik fazlaca kuralla da  bu ön dil serisi çözüme ulaşabilir, ancak bir  olabilecek en "genel" kuralları istiyoruz. Yani aslında kural sayısını minimize etmek ve kuralları genelleştirmek de bir hedef. 

En sonki proto dil ile çocuk dillerin arasındaki mesafe sabit olmak zorunda dersek/demezsek neler olacağı bilinmeli.  İki dil de proto dile 3 dil uzakta olursa farklı, birisi bir dil diğeri üç dil uzak olursa farklı olur. Bu düşüncenin doğal sonucu olarak bir dili diğerinin atası varsayıp "ikisi arasında" (ikisine gelen değil de bir dilder diğerine) bir proto dil eşleşmesi yaptırılabilir. Yani herhangi iki dil arasında ses kuralları bulmaya dönüşüyor.

Projenin sonluk hedefi verilen herhangi iki dil arasında akrabalık ilişkisi gösteren varsayımsal diller oluşturmaktır.

"ÖNEMLİ"

Bu proje yapılırken dillerdeki sözcüklerin okunuşu değil, yazılışı esas alınmalıdır. Yazılış esası üzerinden ilerlenmelidir. Yanli bhiçbir zaman kelimenin okunuşunu bulmamıza gerek yok, sadece yazılışı yeterli olacaktır. 
---

GERÇEKLEŞTİRİM

Yukarıdaki 1. ve 4. varsayımsal yöntemlerin bileşimi kodlanmıştır. Akış:

1. "sesbiçim/" : Her harf (ünlü/ünsüz) tek tek değil, özellik vektörü olarak tanımlıdır
   (ünlüler: yükseklik-arkalık-yuvarlaklık; ünsüzler: yer-biçim-ötümlülük). Yer ölçeği
   IPA'ya uygun 7 bölgedir (dudaksıl, dişdudaksıl, dişsil, öndamaksıl, artdamaksıl,
   küçükdilsil, gırtlaksıl); l yansıl, r çarpmalı ayrı biçim sınıflarıdır; ğ tarihsel
   değeriyle artdamaksıl sızıcıdır (/ɣ/), q küçükdilsildir. Böylece hiçbir iki yazılı
   harf aynı koordinata düşmez (l~r, k~q, y~ğ, ş~x hepsi tam 1 adımdır). Tek özelliği
   bir basamak değişen harfler "komşu"dur; çok özellikli sıçramalar (k -> f) en kısa
   doğal yola (k > ɟ̥ > ç ya da p > ɸ > f gibi) bölünür. Boğumsuzlaşma (t/k/p -> ʔ,
   s -> h) ve b ~ w, ğ ~ y gibi iyi bilinen geçişler özel komşudur. Silinme yalnız
   zayıf seslerden (gırtlaksıllar, genizsiller, yan/çarpmalı akıcılar, kayıcılar,
   ünlüler) tek adımda olur; güçlü ünsüzler önce zayıflar (k > ʔ > ∅), sonra düşer.
   Hizalama ise türetim yolundan bağımsız, doğrudan özellik uzaklığıyla çalışır.
2. "ondil/hizalama.py" : Anlamca eşleşen sözcük çiftleri, yerine koyma maliyeti = harf
   grafiği uzaklığı olacak biçimde hizalanır (Needleman-Wunsch). Bitişik ab ~ ba
   çaprazlamaları göçüşüm (metathesis) olarak ayrıca yakalanır.
3. "ondil/insa.py" : Hizalamadan çıkan her harf karşılıklığı bütün söz varlığında TEK
   Ön Dil harfine bağlanır; kurallar bu yüzden tanım gereği düzenlidir. Aynı Ön Dil harfi
   bir dalda iki ayrı sese gidiyorsa önce bağlam koşulu (söz başında, ünlü önünde...)
   aranır, ayrışmazsa yeni harf türetilir (b₂ gibi). Asgari harf hedefi: önce paylaş,
   sonra bağlamla ayır, en son çare harf türet. En uzun kural zinciri katman (ara Ön Dil)
   sayısını belirler; iki dalın ataya uzaklığı eşit olmak zorunda değildir.
4. Kurallar katman katman "körce" (köken bilgisi olmadan) uygulanıp doğrulanır; raporda
   istisna sayısı, kural sayısı, türetilmiş harf sayısı ve katman başına dağarcık boyutu
   verilir. Türetilmiş harf ve kural sayısının yüksekliği, iki listeyi ortak ataya
   bağlamanın "maliyeti"dir ve akrabalık derecesinin sayısal ölçüsü olarak okunabilir
   (43. satırdaki "nafile çözüm" kaygısının ölçülebilir hale getirilmiş biçimi).

KULLANIM

    python3 ana.py                            # Türkçe ~ İngilizce Swadesh-100 (varsayılan)
    python3 ana.py diller/a.txt diller/b.txt  # herhangi iki liste
    python3 ana.py --rapor sonuç.txt          # rapor dosyası adı

Çıktı: Ön Dil sözlüğü, katman katman ses değişim kuralları, her sözcüğün
*ÖnDil > ara biçimler > çocuk dil türetimi ve özet istatistik (rapor.txt).
Varsayılan türetim eşiği 1'dir: rapor her zaman %100 düzenlilikli tam çözümü
verir (eşik 1'de istisna tanım gereği sıfırdır); eğri --tarama ile incelenir.

TUTUMLULUK KISITI (ASGARİ HARF)

43. satırdaki kaygının çözümü: sınırsız harf türetimiyle her iki liste "nafile" biçimde
ortak ataya bağlanabildiğinden, sisteme "ne kadar az harf o kadar iyi" kısıtı eklendi.
Yeni bir Ön Dil harfi ancak en az --türetim-eşiği kadar konumu kurtarıyorsa türetilir;
daha seyrek karşılıklıklar kural dışı (istisna) bırakılır ve raporda ✗ ile işaretlenir.
Böylece harf sayısı ile düzenlilik arasındaki ödünleşim ölçülebilir hale gelir
(--tarama ile eğri yazdırılır).

SIFIRDAN SOYUT HARF (KÜMELEME)

Ön Dil harfleri çocuk alfabelerinden KOPYALANMAZ. Sistem sıfır harfle başlar: her
harf karşılıklığı (ör. Türkçe b ~ İngilizce w) önce kendi başına bir aday harftir;
kurallı biçimde (aynı refleks ya da bağlamla ayrışan refleksler) bir arada
yaşayabilen adaylar tek soyut harfte birleştirilir. Yani bir Ön Dil harfi, bu
kümenin ta kendisidir; "b" gibi bir adla yazılması yalnız gösterimdir. Gerçekçilik
kuralı çapa ile korunur: her kümeye özellik uzayında öyle bir nokta seçilir ki
bütün refleksler o noktadan en çok 4 doğal ses adımı uzakta olsun (k -> f yasağı
burada da geçerlidir). Aynı çapaya oturmak zorunda kalan ikinci küme alt simge
alır (t₂ gibi) ve raporda "türetilmiş" sayılır.

SANAL HARF SINIFLARI

Çapa ve ara duraklar yazılı harflerle sınırlı değildir. Sanal harfler dosyada
tek tek tanımlanmaz: özellik uzayının TAMAMI hesaplamayla taranır ve yazıda
karşılığı olmayan her söylenebilir bileşim sanal harf olur (insan ses aygıtının
üretemeyeceği bileşimler — ötümlü hamza, gırtlak genizsili — dışarıda bırakılır;
gerçekçilik kuralı). Bilinen bileşimler IPA imini alır (ʔ, ŋ, ʦ, ʎ, ɦ, ʌ, œ...),
kalanlar ad havuzundan im alır (θ, π...). Bu, sesbiçim/ dosyalarının başındaki
vizyonun gerçekleşmesidir: harfleri değil özellikleri tanımla, model yeni
harfleri kendisi kursun.

Sanal harfler yalnız ara durak değildir; Ön Dilin KENDİSİNDE de harf (çapa)
olabilirler: Türkçe ~ Azerbaycanca'da *πu > şu / o (π: ötümsüz damak kayıcısı)
ve *θ -> p (θ: ötümsüz m) gibi kuruluşlar kendiliğinden çıkar. Zincirleri de
kısaltıp doğallaştırırlar: k > ʔ > ∅ silinmesi, k > g > ŋ > n genizsilleşmesi.
Eşitlikte yazılı harf yeğlenir (sanal harf ancak yolu gerçekten kısaltıyorsa
seçilir) ve hizalama yalnız yazılı harf grafiğini görür: sanal harfler sözcük
karşılaştırmasını değil, yalnız yeniden kurmayı etkiler.

Harf türetimi ve etiketleme ayrıca iki "son çare" mekanizmasıyla geciktirilir:

1. KONAK HARF: Bağlamla ayrışmayan bir grup için yeni harf türetmeden önce, biraz
   daha uzak ama uyumlu mevcut bir harf konak olarak denenir.
2. EŞDEĞER YOL: Ara katmanlarda zinciri çakışan bir kural, harf etiketlenmeden önce
   harf grafiğindeki aynı uzunluktaki BAŞKA bir doğal yola kaydırılmayı dener.

Hepsi doğrulama döngüsünün içinde çalıştığından düzenlilik garantisi bozulmaz.
Alfabe sıkıştıkça kural sayısının bir miktar artması beklenen bilgi-kuramsal
bedeldir (az harf = çok kural). Türkçe ~ İngilizce Swadesh-100 için:

    eşik  Ön Dil harfi  türetilmiş  kural  istisna  düzenlilik
       1           104          73    345        0     %100.0
       3            68          41    237       65     % 67.5
       8            29          11     66      169     % 15.5

Az harf ile yüksek düzenlilik AYNI ANDA elde edilemiyorsa listeler akraba değildir;
akraba dillerde bu eğri düz kalır (az harf, az kural, yüksek düzenlilik). Yani eğrinin
kendisi, iki dilin akrabalık derecesinin sayısal ölçüsüdür.

DOĞRULAMA: TÜRKÇE ~ AZERBAYCANCA KARŞILAŞTIRMASI

Yöntemin akrabalık ölçüsü olarak çalıştığını sınamak için aynı tarama, akraba olduğu
bilinen Türkçe ~ Azerbaycanca çifti üzerinde yinelendi (diller/azerbaycanca.txt;
anlamca standart karşılıklar kullanıldığından it, sümük, od, yaxşı gibi kökendaş
olmayan maddeler de listede bırakıldı):

    eşik   Türkçe~İngilizce            Türkçe~Azerbaycanca
           harf / kural / düzenlilik   harf / kural / düzenlilik
       1   104  / 345   / %100         66  / 168   / %100
       3    68  / 237   / %67.5        45  / 115   / %87.0
       5    44  / 133   / %35.0        30  /  44   / %71.5
       8    29  /  66   / %15.5        22  /  23   / %52.0

Beklenen sonuç doğrulandı: akraba çiftte eğri düz kalıyor — eşik 5'te yalnız 30
soyut harf ve 44 kuralla düzenlilik %71.5'te tutunuyor (kalan istisnaların çoğu
zaten kökendaş olmayan maddeler), akraba olmayan çiftte aynı noktada %35'e,
eşik 8'de %15.5'a çöküyor. Düzenli
kurallar da gerçek ses denkliklerini kendiliğinden buluyor: k -> q (kadın ~ qadın),
t -> d (taş ~ daş), e -> ə (sen ~ sən), ünlü ardında h -> x (tohum ~ toxum) gibi.
