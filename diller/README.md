Kullanıcının Ön Dil hesaplamasını yapmak istediği diller bu dosyada olacak.

Buradaki sorun, verilen sözcük listesinin sıradaş olması gerekli. Model sözcüklerin anlamlarını bilmeyeceğinden,  farklı dillerdeki aynı anlama gelen sözcükleri bir şekilde anlaması gerekiyor.
Örneğin 
Türkçe listesi ev köpek güneş 
İngilizce listesi sun house dog 

şeklinde olursa model kuzen akraba olacak olan sözcükleri bilemeyeceğinden, sözcükleri belirli bir sırayla vermek bir çözüm olabilir.

bir başka çözüm ise her dilin sıralı sıvadaş listesi (en temel 100 sözcük) verilerek yapılabilir. Böylece ilk aşamada basit bir çözüm olup, sonrasında daha genel hale getirilebilir (hem veri toplamak hem de veriyi anlamdaş sözcükleri anlayabilecek şekilde yorumlamak için) 
---

DOSYA BİÇİMİ

Her dil bir dosyadır; her satır "anlam sözcük" biçimindedir ve bütün dosyalar aynı anlam
sırasını izler (sıralı Swadesh çözümü). "#" ile başlayan satırlar yorumdur. İlk deneme
için türkçe.txt ve ingilizce.txt Swadesh-100 listeleri eklenmiştir; eylemler Türkçede
kök biçimiyle (iç, ye, gör...) verilmiştir ki -mek/-mak eki yapay kural üretmesin.
Yazılış esaslıdır; okunuş kullanılmaz.

MEVCUT DİLLER

  türkçe, ingilizce, azerbaycanca, almanca, romence, kürtçe (Kurmancî),
  arnavutça, türkmence, tacikçe.

Herhangi iki dosya çift olarak verilebilir:
  python3 ana.py diller/türkçe.txt diller/türkmence.txt

YAZILIŞ NORMALİZASYONU

Sesbiçim tabloları Latin tabanlıdır ve kısa ünlü uzayı doludur; bu yüzden tabloda
karşılığı olmayan grafemler en yakın yazılı harfe çevrilir (her dosyanın başında
belgelidir). Başlıca çeviriler: Almanca ß->ss; Romence ă->ə, â/î->ı, ș->ş, ț->ç;
Kürtçe ê->e, î->i, û->u; Arnavutça ë->ə, ünlü y->ü (ikili harfler dh/gj/sh/...
korunur); Türkmence ä->ə, ž->j, ň->n, y->ı, ý->y; Tacikçe Kiril'den Latin'e
(ғ->ğ, қ->q, ҳ->h, х->x, ҷ->c, ч->ç, ш->ş). Bu listeler ilk taslaktır; sözcük
seçimleri (özellikle eş anlamlılar ve eylem citation biçimleri) gözden geçirilebilir.

NOT: harf sayısı bir akrabalık ölçüsü olabilir belki.
