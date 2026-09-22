# Bağımsız BTC5dk dışı denetim — Astra, 21 Eylül 2026

Kaynaklar MAIN, R, F ve S salt okunur; diğer bağımsız inceleyicilerin sonuçları
girdi değildir. Çalışma alanı yalnız bu dizindir. Emir/deploy/kalıcı süreç yok.
Ana plandaki çoklu piyasa ve envanter araştırmasını, R/F'nin açık ekonomik kabul
aşamasını denetler. Eski BTC5dk operasyon talimatları bu işin yetkisi değildir.

## Kabul ve sıra
- [x] Geçerli talimatlar, MAIN/R/F planları, üç ana rapor tam okundu.
- [x] Kaynak sürümleri/hash ve veri haritası; korunan aday/protokol başlangıç/son hash.
- [x] Ham çokluk, bağımsız Decimal ödeme/maliyet, FIFO/faz ve aynı saniye sırası.
- [x] Zaman erişilebilirliği, resmî mekanizma, aday ve gerçek defter uygulaması denetimi.
- [x] BTC15dk tarihsel ve gerçek defterli kazanç/kayıp/no-add yolları; ücretsiz kamu kontrolü.
- [x] Gözlem birimi/rol için küçük gerekçeli BTC15dk zincir örneği; kanıt sınırları.
- [x] Kontrol grubu, bağımlılık, kalibrasyon ve eşit risk karşılaştırması.
- [x] İki mekanizma önkayıt sonrası yeni veri; tek sonlu ayırıcı deney ve regresyon.
- [x] Türkçe karar/rapor/hata listesi, kaynak/ham cevap/hash/komutlar, lint ve gerçek tekrar.

## Sonraki değerlendirme verisi açılmadan mekanizma önkaydı
Kayıt zamanı: 2026-09-21 18:35:17 UTC. S kesiti bilinen karşı örnektir.
S sonrası sonuç/dolum/defter henüz incelenmedi.
M1: Parçalı pasif emir dolumları, dolum saniyesinde yeni yön kararı görünümü yaratır.
M2: Envanter riskini azaltan karşı alışlar; ucuz çift şartı davranışın yalnız altkümesidir.
M1 parent/orderHash ve maker/taker olaylarıyla; M2 aynı başlangıç envanterinde
tutma/karşı alış risk-ödeme farkıyla sınanır. Fiyat/sonuç tahmini ekonomik edge diye
sunulmaz. İki mekanizmanın birlikte çalışması mümkündür; tek-emir-devamı ile yeni
emir ayrımı ana ayırıcıdır. Güncel yeni kesit keşif olarak etiketlenir, kör test değildir.
Kalıcı avantaj için eski >=10 tam gün/100 giriş/50 ekleme/%95 kapsam kapısı korunur.

## İş bölümü
Muhasebe/çokluk, zaman/aday/defter ve BTC15dk kamu zincir rolü ayrı denetlenir.
Ana çalışma kontroller/istatistik, kaynak dondurma ve birleşik deney/raporu yürütür.
Alt görevler yalnız kendilerine ayrılan alt dizinlere yazar; ortak kaynak değişmez.


## Son kabul denetimi

- Bağımsız Decimal toplam +13.393,820008 USD; 29 grup ve ilk/faz/risk çıktıları gerçek ham veriyle uzlaştı.
- ConditionId, ilk-paket, MERGE-denge ve geçmiş-fiyat erişimi kusurları yerel alternatiflerle gösterildi; paylaşılan aday/protokol değişmedi.
- Yeni defter kesimi 18:38:32.532 UTC'de sabit: 16 tam pencere; ilk eksik ve son açık pencere ayrı. İki mekanizmanın önkaydı korundu; bu küçük kesit kör ileri test sayılmadı.
- Son incelemede çıkan bitiş-sonrası zaman anomalisi, kapsam içindeki iki ilave receipt kontrolünü gerektirdi. Toplam 45 unique transaction önceden belirlenen 50 sınırında kaldı; gerçek blok zamanı emir karar zamanı yapılmadı.
- İşlemsizleri de içeren 816 BTC15 penceresinde gün/saat ve t180 öncesi/sonrası giriş ayrımı sonradan betimsel ek olarak denetlendi; yeni eşik/model seçilmedi.
- Nihai çevrimdışı controller: 16 önemli artifact aynı SHA, 17 Python dosyası syntax/Ruff temiz; bütün bağlı regresyonlar geçti. Dokümantasyon temel sonuçlarla bağımsız alt denetimlerde karşılaştırıldı.
- Tek gelecek deneyin ölçüm protokolü ve sonlu seçicisi teslim edildi; henüz oluşmamış on günlük veri elde edilmiş gibi sunulmadı.

Bu bağımsız araştırma teslimi tamamlandı. R/F'nin ekonomik başarı aşaması açık kalır: yeterli gün/giriş/ekleme ve kontrol üstünlüğü yok. UNDERPOWERED / NOT IDENTIFIABLE sonucu plan başarısı diye çevrilmedi.
