Kullanıcının Ön Dil hesaplamasını yapmak istediği diller bu dosyada olacak.

Buradaki sorun, verilen sözcük listesinin sıradaş olması gerekli. Model sözcüklerin anlamlarını bilmeyeceğinden,  farklı dillerdeki aynı anlama gelen sözcükleri bir şekilde anlaması gerekiyor.
Örneğin 
Türkçe listesi ev köpek güneş 
İngilizce listesi sun house dog 

şeklinde olursa model kuzen akraba olacak olan sözcükleri bilemeyeceğinden, sözcükleri belirli bir sırayla vermek bir çözüm olabilir.

bir başka çözüm ise her dilin sıralı sıvadaş listesi (en temel 100 sözcük) verilerek yapılabilir. Böylece ilk aşamada basit bir çözüm olup, sonrasında daha genel hale getirilebilir (hem veri toplamak hem de veriyi anlamdaş sözcükleri anlayabilecek şekilde yorumlamak için) 