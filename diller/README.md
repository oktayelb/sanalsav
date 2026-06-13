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

MEVCUT DİLLER (27)

  Türk: türkçe, azerbaycanca, türkmence, gagavuzca, kazakça
  Germen: almanca, ingilizce, hollandaca, isveççe
  Roman: romence, ispanyolca, italyanca, fransızca, portekizce
  İran: tacikçe, kürtçe (Kurmancî)
  Arnavut: arnavutça
  Ural: estonca, fince, macarca
  Balt: litvanca
  Slav: slovence, hırvatça, boşnakça, slovakça, lehçe, çekçe

Çiftler arası ön dil harf maliyeti (akrabalık ölçüsü) için bkz. ../sanalsav/tüm_diller.md.

Herhangi iki ya da DAHA ÇOK dosya verilebilir (ikiden çok dilde ortak ön dil
yıldız hizalamayla kurulur):
  python3 ana.py diller/türkçe.txt diller/türkmence.txt
  python3 ana.py diller/türkçe.txt diller/azerbaycanca.txt diller/türkmence.txt

YAZILIŞ NORMALİZASYONU

Sesbiçim tabloları Latin tabanlıdır ve kısa ünlü uzayı doludur; bu yüzden tabloda
karşılığı olmayan grafemler en yakın yazılı harfe çevrilir (her dosyanın başında
belgelidir). Başlıca çeviriler: Almanca ß->ss; Romence ă->ə, â/î->ı, ș->ş, ț->ţ;
Kürtçe ê->e, î->i, û->u; Arnavutça ë->ə, ünlü y->ü (ikili harfler dh/gj/sh/...
korunur); Türkmence ä->ə, ž->j, ň->n, y->ı, ý->y; Tacikçe Kiril'den Latin'e
(ғ->ğ, қ->q, ҳ->h, х->x, ҷ->c, ч->ç, ш->ş); Sloven/Slav c->ţ, č/ć->ç, š->ş,
ž->j, kayıcı j->y; Eston õ->ı; Fin ünlü y->ü; Slovak uzun ünlüler kısaltılır,
ch->x; Kazak ä->ə, ñ korunur. Roman dilleri (İsp/İta/Fra/Por): aksanlar tabana
indirgenir, ç->s (Fr/Pt'de [s]), İsp ñ korunur. Germen (Hol/İsv): kayıcı j->y,
İsv å->o ä->ə y->ü. Lehçe/Çekçe/Macarca: ıslıklılar sese göre (Macar s->ş,
sz->s, zs->j), c[ts]->ţ, gy->c. Litvanca: uzun/burunsu ünlüler sadeleşir.
Genel kural: ş, c, j, x, q, ğ, ö, ü, ı zaten
yazılı; [ts]=ţ ve [ŋ]=ñ yeni eklendi (sesbiçim/ünsüz.py). č->ç olduğundan
Hırvatçanın č/ć ayrımı kaba boğumlanma ölçeğinde birleşir. Bu listeler ilk
taslaktır; sözcük seçimleri (eş anlamlılar, eylem citation biçimleri) gözden
geçirilebilir.

NOT: harf sayısı bir akrabalık ölçüsü olabilir belki.
