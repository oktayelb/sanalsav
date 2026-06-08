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


