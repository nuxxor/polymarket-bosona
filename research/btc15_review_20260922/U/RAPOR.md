# Bosona BTC5dk dışı bağımsız araştırma — 21 Eylül 2026

**Sonuç: NOT IDENTIFIABLE / ekonomik olarak UNDERPOWERED.** Ekonomik avantajı bağımsız uygulanabilen bir Bosona politikası çıkarılamadı. Buna karşılık muhasebe kimliği, eylem etiketi, envanter girdisi ve zaman seçiminin dört somut kusuru bulundu; etkileri yeniden hesaplandı. Pasif parçalı dolum ile ayrı aktif risk kararını BTC15dk zincirinde ayırabildik. Emir gönderim/iptal zamanını ve gizli hedefi ayıramıyoruz.

[Kısa karar](KARAR.md), [hata listesi ve yamalar](HATALAR.md), [29 grup](GROUPS.md), [tek sonraki deney](DENEY.md), [tekrar komutları](README.md).

## 1. Kapsam, veri sürümü ve bağımsızlık

MAIN, R, F ve S salt okunur kaynaklardır. Başka bağımsız inceleyicinin sonucu kullanılmadı. Çalışma ve alt denetimler yalnız bu benzersiz dizine yazdı. Emir, LIVE, shadow, ücretli API, commit/push veya süreç müdahalesi yapılmadı. BTC5dk yeni strateji hedefi yapılmadı; mevcut receipt decoder yalnız ortak teknik yardımcı olarak kullanıldı, sonuçları taşınmadı.

Başlangıç sırası talimatlar/planlar → R/F/S raporları → manifest/kod → muhasebe/zaman → gerçek defterli yollar oldu. İki mekanizma 18:35:17 UTC'de [plan.md](plan.md) içine yazıldı. S zaten bilinen karşı örnektir. S sonrası kayıt ilk kez 18:38:32,532 UTC kesimiyle açıldı. Bu kesit seçimden sonra incelendi fakat gerçekleşmesi seçimden önce olan pencereler içerir; temiz ileri test değildir.

**DOĞRULANDI:** R manifestindeki 11.782 dosya, F'deki 187 dosya ve S'deki 72 dosya kontrol edildi. R/F'de yalnız sonradan genişlemiş plan.md eski manifestten farklı; S birebir. Beş korunan çekirdek dosyanın hash'i aynı. R'nin beş donmuş src kopyası doğru; MAIN'in gec/derin kaynakları bunlardan farklı sürüme ilerlemiş. Eski hesabın kaynağı güncel MAIN diye sunulmadı. [Sürüm ve hash kanıtı](provenance.json).

**DOĞRULANDI:** 65.511 ham aktivitenin örtüşme/çokluk birleştirmesi eski cache'i birebir üretti; bu tek başına kimlik anahtarının doğru olduğunu göstermedi. Bağımsız conditionId denetimi ayrıca 10 kayıp MERGE/575$ ve 143 sıfır REDEEM buldu. Gerçek eşit BUY çokluğu korunuyor. Kaybolan MERGE çiftinin token değeri nakde dönüşür: sonuç PnL değişmez, güncel token/nakit akışı değişir. [Bağımsız hesap](accounting/result.json), [yeni kamu mutabakatı](accounting/collision_result.json).

## 2. BTC5dk dışı evren ve ekonomik hesap

Ana dönem 13 Eylül 00:00–21 Eylül 12:00 UTC. 13–17 keşif, 18–20 kronolojik kıyas; bütün bu günler önceden incelenmişti. 21 Eylül 00–12 güncellemesinde BTC15dk dolumu yok. PnL resmî ödeme eksi API nakit maliyetidir; rebate/gas/sabit gider dahil tüm cüzdan getirisi değildir.

**DOĞRULANDI:** 3.503 işlemli piyasa, 14.014 BUY, 29 grup, toplam **+13.393,820008$**. Resmî evren 9.110; bunun 7.956'sı tam taranan sekiz ana grubun takvimidir. 5.607 sözleşmede gözlenen işlem yok; bunlar veri eksiği değil. Diğer 21 grubun işlemsiz takvimi tamamlanmadığı için seçim paydası bilinmiyor. 1.423 kaynak piyasa dönem dışında; bunlar başarısız strateji veya sıfır getirili pencere sayılmadı. Tutulan tarihsel evrende çözümsüz piyasa yok. Geniş evrende “bilinmeyen bütün piyasa sayısı” ölçülmüş değildir.

| Grup | İşlemli / tam evren | Dolum | PnL $ | İlk sn / fiyat¢ / pay medyan | İki taraf % | FIFO çift / kalan yön $ |
|---|---:|---:|---:|---:|---:|---:|
| BTC15dk |598/816|5.441|4.428,55|151 /48,9 /49,8|71,2|−2.220,64 /6.649,19|
| BTC saatlik |193/204|1.494|3.351,10|174 /47,0 /49,8|71,0|2.513,48 /837,61|
| ETH5dk |643/2.448|1.673|1.529,10|119 /46,0 /23,6|17,7|−603,90 /2.133,00|
| ETH15dk |131/816|210|85,69|202 /53,0 /19,6|9,9|1,66 /84,03|
| ETH saatlik |136/204|700|−155,38|657 /58,5 /22,9|75,7|−448,66 /293,28|
| SOL5dk |413/2.448|620|1.307,11|154 /76,0 /22,2|9,0|−439,22 /1.746,33|
| SOL15dk |154/816|370|167,97|204 /80,0 /30,0|39,6|−325,14 /493,11|
| SOL saatlik |81/204|213|239,69|747 /68,0 /17,9|37,0|−141,10 /380,79|

Tam 29 grubun ilk giriş, faz miktarı, iki taraflılık, tepe risk ve en iyi 3 hariç sonucu [GROUPS.md](GROUPS.md) içindedir. BTC15dk tepe zarar medyanı 101,64$, azami 810,90$; en iyi 3 hariç toplam +3.025,27$. ETH saatlikte yüksek iki taraf oranına rağmen hem toplam hem çift katkısı negatiftir. **GÖZLEMSEL DESTEK:** aynı basit çift-toplama davranışı bütün grupları açıklamıyor. Likidite/özel hedefler eksikken ayrı bot sonucu çıkmaz.

Net fark ve iki sonuç ödeme vektörü, MERGE ile aynı kalır: `qUp−cash`, `qDown−cash`. MERGE miktarı m ise iki q'dan m, net maliyetten m düşer. Bu yüzden alış/nihai ödeme PnL'si doğrudur; “mevcut iki taraf dengesi” için kümülatif alış q'su kullanılamaz. Kapsamda BUY dışı satış/split yok; görülürse mevcut yordamlar reddediyor. Başka piyasalar, pre-cohort sermaye ve açık emir rezervi içermeyen ölçü tam portföy riski değildir.

**DOĞRULANDI — piyasa seçimi:** Sekiz tam UTC günün 768 BTC15 penceresinde 598 işlemli piyasa var (%77,86). Günlük sayılar sırasıyla 56, 54, 93, 93, 87, 95, 84, 36/96; 21 Eylül'ün işlemsiz 48 penceresi yarım gün olarak ayrıldı. 24 saatin 17'sinde aynı saat bir gün 0/4, başka gün 4/4 işlemli. Bir günü çıkarınca genel katılım %74,85–83,63 oluyor. Bu, tek saat veya gece kuralını göstermiyor. [Gün×saat paydası ve bütün kıyaslar](accounting/SELECTION.md).

**KANIT YETERSİZ — ilk giriş koşulları:** t180'de 326 piyasaya zaten girilmiş; o andaki fiyat/oynaklık ilk girişlerini açıklayamaz. Henüz girilmemiş tam gün risk setinde 271 sonraki ilk giriş ve 170 işlemsiz pencere var; ortak bağlam/fiyat sırasıyla yalnız 186/117 piyasada. Normalize sigma medyanı 0,3321/0,3590 baz puan/√sn, ucuz token fiyatı 41,5¢/35,5¢. Bunlar eski bağlam sürümü ve medyanda 47,5/48 sn yaşlı kamu fiyat vekilidir; bid/ask ve tarihsel yerel fiyat-alım saati yok. Nihai hacim/likidite kullanılmadı. Dağılım farkından bağımsız giriş avantajı veya nedensel saat seçimi çıkmıyor.

## 3. İlk giriş, dolum ve karar birimi

**DOĞRULANDI:** BTC15dk ilk saniye/ilk 5 sn/ilk 10 sn toplam miktar medyanı 49,805 /70,502 /80,875 pay. İlk dolum ilk emir miktarı değildir. İlgili 5.441 dolum, aynı saniye tanımında 4.014; 5 sn tanımında 3.178; 10 sn tanımında 2.828 paket olur; paketler orderHash yerine geçmez. Karma yönlü paket sayısı aynı saniyede 18, 5 sn tanımında 61, 10 sn tanımında 92: geniş paket birleştirmesi gerçek ayrı kararları da birleştirebilir.

İlk saniye parçalarını ilk gruba almak geç-add sayısını **1.173/277 piyasa/+3.389,908592$ →1.150/274/+3.364,652672$** yapıyor. 5 sn tanımı 1.134/269/+3.252,47; 10 sn 1.122/266/+3.126,96$. Bu düzeltmeler ilk paket hassasiyetidir. Tüm paketleri başındaki envanterle atomik etiketlemek farklı sorudur:10 sn paket düzeyinde geç-add katkısı +870,47$, en iyi 3 hariç−62,24$ olur. Bu daha doğru gerçek emir modeli diye seçilmedi. Paket büyüdükçe iki yön içeren paketli piyasalar tamamen dışlanır ve 600 sn sınır üyeliği değişir; aynı kohort üzerindeki saf paketleme etkisi değildir.

Aynı saniye işlem sırasını değiştirince toplam PnL sabitken faz katkısı da değişiyor: Up-önce geç-add+3.279,99, Down-önce+3.480,60; daha geniş ters sıra duyarlılığı+3.127,58$. Bunlar bütün olası sıraların keskin alt/üst sınırı değildir. Zincirli örneklerde block/transaction/log sırası kullanıldı; tarihsel tüm piyasalar için zincir sırası çözülmüş değil.

**DOĞRULANDI:** dört gerekçeli S piyasasının bütün 42 API satırı/42 transaction'ı 26 orderHash'e çözüldü; 38 maker, 4 taker rolü. Public receiptler ile outcome miktarı ve collateral nakdi eksiksiz uzlaştı; ilk receipt iki ücretsiz Polygon sağlayıcısında aynı. V2 sözleşme ve ABI [resmî kaynak](https://github.com/Polymarket/ctf-exchange-v2) ile doğrulandı. Bu örnek sonuçlara göre seçilmiş tanısal dört vakadır; tüm BTC15dk maker oranı diye genellenemez.

API satırı tek match de değildir: t604'te 205 paylık bir taker satırı aynı OrdersMatched içinde dört karşı emirle, t741'de 48,54 paylık satır üç karşı emirle eşleşiyor. V2 OrderFilled'daki `maker` alanı emir sahibidir; agresör rolü OrdersMatched taker hash'iyle ayrıldı. Karşı outcome BUY/mint akışı dahil nakit/token korunumu kontrol edildi. Dört taker satırındaki 9,38221$ ücret zaten usdcSize içindedir. Üzerine varsayımsal taker ücreti eklemek çift ücret olur. [Receipt/parent kanıtı](onchain/results.json), [tam yollar](onchain/PATHS.md).

Seçilen 26 geç-add satırının 16'sı ilk görülen parent dolumu; 6'sı önceki saniyeden aynı parent, 4'ü aynı-saniye parent parçası. Paylar 1.026,214 /231,071 /220,118. Hiçbir parent 600 sn sınırını aşmıyor; ilk-son dolum en çok 3 sn. **KARŞI KANIT:** “geç eklemelerin hepsi çok önceden açılmış ilk emirdir” açıklaması bu örneği karşılamıyor. İlk görülen parent dolumu yeni gönderilmiş emir demek değildir; maker rolü uzun süre beklemeyi kanıtlamaz.

## 4. Geç eklemenin kazancı, kontrol grubu ve miktar

| Aynı düzeltilmiş 274 BTC15 piyasası | Toplam katkı $ | En iyi 3 hariç $ |
|---|---:|---:|
| Gerçek boy |3.364,65|2.011,97|
| Piyasa başına toplam 5 ek pay |49,35|36,35|
| Piyasa başına toplam 5$ ek alış nakdi |−69,92|−211,94|
| Tüm piyasa yolunun gerçekleşmiş tepe riskini 5$'a ölçekle |−9,02|−75,51|

**KARŞI KANIT:** ham dolar katkısı bağımsız yön avantajı veya eşit bütçe sonucu değildir. Son satır gelecekte gerçekleşen tepe riski kullanır; yalnız sonradan muhasebe normalizasyonudur, pozisyon büyüklüğü kuralı olarak kullanılamaz. İlk üç satır da gözlenen dolumlara koşulludur. [Günlük ölçek karşılaştırmaları](statistics/scaled_late_rows.json).

F risk setindeki 3.524 durum 418 piyasadan geliyor; 598 işlemli veya 816 takvim penceresinin eşit örneklemi değil. 2.443 keşif/1.081 kronolojik. 231 add, 3.035 gözlenen işlem yok, 258 başka eylem; 29 add aralığında karşı yön de var. “Hiç add yok” sabit sınıf tahmini kronolojik doğrulukta%93,06 verir. Yüksek accuracy bu problemde başarı değildir.

Önceden açık pozisyon yoksa add riski yoktur; o durum negatif eğitim örneği diye doldurulmadı. 5 sn kör aralıkta dolum dışlaması ve bağlam eksikliği örneklem seçer. Ayrıca pencerenin ilerideki karşıt aynı-saniye olayı 8 piyasada 47 geçmiş durumu dışlıyor; 25'inin orijinal fiyat/bağlamı hazır. Bu örneklem sızıntısı ayrıntısıyla [hata listesinde](HATALAR.md).

|18–20 Eylül kontrol tasarımı|Çift / ekleme piyasası|5 pay normal fark $|Tanısal%95 aralık $|
|---|---:|---:|---:|
| Eski yakın eşleştirme |46/39|−11,62|eski piyasa:−52,39…30,01|
| Aynı çiftler, iki kolun bağlı piyasa kümeleri |46/39|−11,62|−56,65…33,15|
| Karma add+karşı yönü çıkar |39/34|−10,19|−54,47…25,00|
| Aynı gün, karma olay yok, yeniden eşleştir |31/26|+15,24|−19,61…50,18|
| Aynı gün, piyasa iki kolda/tekrar kullanılmaz |23/23|+15,41|−14,91…45,86|

**KANIT YETERSİZ:** eşleştirme işareti değiştiriyor; her aralık 0'ı içeriyor. Pozitif son iki tasarım yeni strateji seçimi değildir; keşif duyarlılığıdır. Eski 46 çiftte 38 kontrol piyasası, 8 tekrar kullanılan kontrol, 11 iki kollu piyasa, 16 farklı-gün çifti var. 39 bağımsız etki varsayımı yerine 20 bağlantılı piyasa kümesi oluşuyor. Üç günle gün-bootstrap kalıcı güven vermez. 20 Eylül'ü çıkarınca eski fark +3,43$ oluyor. 68 kazanan/kaybeden çifti ise sonucu bilerek eşleştirir; temel kazanma sıklığını veya politika edge'ini belirleyemez.

**DOĞRULANDI:** F'nin 9 temel çıktı dosyası kendi çıkış yolumuzda birebir aynı hash ile yeniden üretildi. H2'de gerçekleşmiş MERGE sonrası kalan q kullanınca 788 durum/123 piyasanın denge değeri değişti. Logloss 0,250642→**0,252378**; AUC 0,5709→0,5453. Aday-koşul açıklama modeli 0,249292; H1 0,253290. Düzeltilmiş H2 farkının piyasa aralığı[−0,01323; +0,00718], gün aralığı[−0,00907; +0,01224]. Üstünlük yok. [Aynı model, düzeltilmiş girdiler](statistics/merge_corrected/hypothesis_models.json).

Aktör envanterinden küçük kendi portföyümüze aktarım da büyük: mutlak net medyan 149,39 pay; 2.882/3.524 durum adayın 10 pay sınırından, 2.691 durum 5$ risk sınırından büyük. Aday envanteri uygun yalnız 29 durum. Bu modelin 5 pay botunda aynı dağılımda çalışacağını varsayamayız.

## 5. Zaman, resmî kapanış ve olasılık

Kısa sözleşmelerde resmî Chainlink 60 sn TWAP başlangıç ve kapanış kıyaslanır; saatlikler Binance 1 H açılış/kapanışı, günlükler ET öğlen 1 dk kapanışı ve eşitlikte 50–50 kuralıdır. Slug keşif içindir; resmî metadata sınıflandırması yeniden kullanıldı. Dönem Eylül olduğundan DST geçişi içermiyor; ET dönüşümü zoneinfo ile. BTC15 sonucunu saatlik mekanizmaya taşımak geçersiz.

**DOĞRULANDI:** Resmî bitişte veya sonrasında 92 dolum/55 piyasa var; BTC15 altkümesi 24 dolum/5 piyasa, +141,420815$ katkı. Bu dolumlar toplam nakit PnL'sinde korunur, `600≤age<900` geç-add kümesine girmez. İki örnekte API timestamp'i gerçek blok timestamp'iyle eşleşti; kapanıştan 31 dk 17 sn ve 16 dk 26 sn sonra zincire yazılmışlar. Doğru condition/token ve nakit uzlaştı. **ÖLÇÜLEMİYOR:** bu, off-chain eşleşme veya emir gönderiminin kapanıştan sonra olduğu anlamına gelmez. Karar zamanı diye kullanılamaz. [Tam sayım](accounting/postclose_fills.json), [iki receipt kontrolü](onchain/postclose_results.json).

**DOĞRULANDI:** S'de 14 başlangıç TWAP'ı metadata priceToBeat ile aynı; 13 mevcut finalPrice aynı, 14 sonuç yönü akışla aynı. Başlangıç TWAP raporu kaynak makineye 882–1781 ms sonra ulaşıyor. İlk saniye kararı için başlangıç değeri hazır kabul edilemez; t180 için hazırdır. Metadata'nın sonradan gelen fiyatı yalnız doğrulama için, karar girdisi olarak kullanılmadı. [Referans kontrolleri](execution/s_reference_checks.json).

Kaynak makine ayrıca doğrulandı: Chainlink yazıcısı yerel PID 63900, özgün `polymarket/data/tape_cl_direct` dosyasına yazıyor; rcv=time.time() alım anı. 14–17 kapalı saatlerin SHA'sı MAIN aynasıyla birebir; ayna 18:35'te kopyalanmış. Dolayısıyla mtime alım anı değildir; yerel özgün kaydın rcv'si kullanılabilir. Yazıcı flush ile tüketici okuması arasındaki kesin süre ölçülmedi. [Makine, FD, kod ve hash kanıtı](execution/local_price_provenance.json). Bu denetim hiçbir fiyat/kayıt sürecini değiştirmedi.

Eski 20.533 bağlam 222 kaynak dosyadan yeniden üretildi. Beş bilinen bozuk tarihsel saat kaynağı eski yöntemdeki gibi dışlandı; sessizce tam sayılmadı. Aynı 3 sn güncel tazelikle geçmiş hedef/karar erişim ayrımı düzeltilince 20.881 bağlam oluşuyor. 9.792 planlı t180…840 noktasında 7.046→7.158; t180 bağlamı 591→600.18.736 ortak olasılık değişiyor: bu salt “9 fazla giriş fırsatı” değildir, örnek seçimi sigma'yı değiştirir. Politika fiyat senaryosunda 21 giriş→23; 4 eski gider, 6 yeni gelir; ekleme yine 1.

Normal modelin Brownian ortalama varyansı matematiksel olarak tutarlı: kalan r≥60 iken `sigma²(r−40)`, r<60 iken `sigma²r³/10800`; son dakika bilinen katkısı ayrı. Sayısal covariance integraliyle doğrulandı. Fakat bu gerçek Chainlink feed'inin birebir yeniden üretimi değildir. Özel feed'in ağırlık/sınır/yuvarlama detayları yayımlanmıyor. [Resmî TWAP açıklaması](https://docs.polymarket.com/market-data/chainlink-twap).

**KARŞI KANIT:** t600 kronolojik 170 piyasa model Brier 0,19933/logloss 1,08277; aynı noktaların ortalama 45,006 sn eski Up fiyatı Brier 0,16623/logloss 0,49668. Fiyat baseline'ı defter değil. p≥0,9 olan 59 örnekte ortalama 0,98121 ama Up oranı 0,81356; >%99 emin 64 tahminin 9'u yanlış. t840/870 hata azalır fakat vade sonuna yaklaşma ve gecikmiş baseline nedeniyle bu doğrudan edge değildir. [Ufuk/dönem/bin kalibrasyonu](execution/calibration.json), [aynı-piyasa fiyat kıyası](execution/calibration_market_comparison.json).

## 6. Yeni gerçek defter ve donmuş adayın yerel sonucu

**DOĞRULANDI:** kayıt PID 1714322, kod hash'i ve başlangıç/bitiş değişmedi; kalp atışı ile canlı süreç doğrulandı. 18:38:32,532 UTC'de byte sınırıyla dondurulmuş 15.191 çift snapshot/30.382 taraf; 2 timeout, en büyük başarılı aralık 5,061 sn. 27.592 taraf beş pay/spread/tazelik koşulunda, 2.754 boş/tek taraflı, 36 geniş/çapraz. Son açık gzip footer eksikliği yalnız son açık dosyada beklenen uç olarak kaydedildi; kapalı saatlerde hata yok. Satır/byte/SHA ve kesim [manifestte](new_period/freeze_manifest.json).

| Kapalı ve baştan kayıtlı BTC15 dönem | Piyasa / işlemli / dolum | Bosona toplam PnL $ | Geç-add dolum / katkı $ |
|---|---:|---:|---:|
| S:14:30–18:00 UTC |14/12/126|+165,630507|54 /−254,167917|
| Yeni kesit:14:30–18:30 UTC |16/14/144|+119,230867|61 /−329,593073|
| S'de açık 18:00 penceresinin tamamı |1/1/4|+58,845216|0 /0|
| S sonrası tamamen görülmemiş 18:15 penceresi |1/1/14|−105,244856|7 /−75,425156|

18:30 penceresi kesimde açık:300 Up+300 Down, 273,50402$ maliyet, iki sonuçta +26,49598$ ödeme tabanı; gerçekleşmiş kapalı PnL'ye katılmadı. İlk 14:15 eksik pencere de ayrı. 18 piyasanın start=1 tam kamu geçmişi ayrıca kontrol edildi: başlangıçtan önce kaçan TRADE 0. Public activity/trades çokluğu ve Decimal hesaplar uzlaştı. Yeni kesit adayın PnL'si değil aktör hesabıdır.

**KARŞI KANIT:** S'deki 54 geç eklemede−5/−10 sn gerçek ask bulunmasına rağmen katkı negatiftir; tarihsel kazanma hikâyesi tek başına yetmez. Book-side uygunluk%90,89, politika veri kapsamı değildir. S'de 168 planlı aday anının tamamında defter kaydı var; 156'sında iki taraf alınabilirlik koşulunu sağlıyor, 167'sinde eski fiyat bağlamı var. Bağlam ve alınabilirliğin kesişimi 155/168 (%92,26), zaman düzeltmesiyle 156/168 (%92,86). On iki boş/tek taraflı durum veri edinme kaybı değildir. Protokolde %95 kapsamın payı tanımlanmadığı için bu oran tek başına kesin veri kapısı ihlali sayılmaz. Edinim kapsamı ile işlem uygunluğu ayrı raporlanmalı; eksik tarafa 1−p konmadı.

| S'nin 14 penceresinde aynı girişli kollar | Giriş / ekleme / tamamlama | Ücretli sanal PnL $ |
|---|---:|---:|
| Donmuş bağlam, ilk alımı tut |2/0/0|+0,78343|
| Donmuş bağlam, yalnız tamamlama |2/0/1|−1,30057|
| Donmuş bağlam, managed |2/0/1|−1,30057|
| Geçmiş erişim düzeltmesi, tut |1/0/0|+2,61306|
| Aynı düzeltme, tamamlama veya managed |1/0/1|+0,52906|

**UNDERPOWERED:** ikinci blok bir hata duyarlılığıdır; kazancı seçerek yeni aday yapılmadı. İki sürümün ilk girişleri farklıdır; yönetim üstünlüğü gibi karşılaştırılmaz. Her sürüm içinde ilk girişler kollar arasında aynı. Karardan≥250 ms sonra gerçekten istenen ilk snapshot yanıtı 399–1393 ms sonra, medyan 1039,5 ms. “250 ms'de dolduk” denmedi. 5 payderinlik/ücret/risk kontrolü mevcut; hiç emir gönderilmedi, maker fill/queue varsayılmadı. Portföy kesicisi/scheduler üretim testi değildir. [Kararlar](execution/s_decisions.json), [kendi envanterli replay](execution/s_candidate_replay.json).

## 7. Kazanç, kayıp ve gözlenen eklemesizlik yolları

Aşağıdaki defterler kamu dolum saniyesinden 5 sn önce alınmıştır; Bosona'nın gerçek karar saati bilinmiyor. Tüm 42 adımın iki ödeme vektörü ve parent kimliği [case_paths.json](case_paths.json) içinde. Aşağıda önemli adımlar, maliyetler ücret dahil API nakdidir.

Tarihsel iki tam yol da [CASES.md](accounting/CASES.md) içinde bağımsız hesaplandı: `1789564500` Down sonucunda −461,200785$, `1789708500` Up sonucunda +635,164129$. İlk vakada t321'de iki sonuç +11,25$'a dengelenmişken sonraki yeniden açılışlar ve yön değişimleri zarara götürüyor. İlk dengelemenin ardından elde tutmak farklı bir kontrol yoludur; aktörün sonraki dolumlarını aynı envanterde kopyalamak mümkün değildir. Tarihsel yollar için gerçek geçmiş L2/parent kimliği iddia edilmiyor; aşağıdaki S vakaları bu boşluğu sınırlı ve somut örneklerle inceliyor.

| Vaka / resmî sonuç | Karar öncesi gözlenebilir durum | Eylem / rol / parent | En kötü sonuç değişimi | Sonuç |
|---|---|---|---|---|
| `1790001900`, Up | t399: boş envanter |300 Down/36$, iki parça tekmaker parent|0→−36$|İlk yön kaybeder|
| aynı kayıp |t802 öncesi 517,218802 Down; nakit 56,788849; −5 snask 8,9¢|ayrı 300 Down taker, 31,89$|−56,788849→−88,678849$|Aynı risk büyür|
| aynı kayıp |t819 öncesi 924,661573 Down; nakit 127,517132; −5 snask 22¢|başka 300 Down taker, 94,41$|−127,517132→−221,927132$|Piyasa−221,927132$; geç katkı−185,927132$|
| `1790008200`, Down |t 879 boş; −5 snDownask 96¢|17,548388 Down maker, 12,108388$|0→−12,108388$|Daha eski/başka fiyatlı emir olasılığı; karar zamanı bilinmiyor|
| aynı kazanç |t 881 ilk 19,218388 Down tamamlanır; −5 snask 98¢|1,67 ve 300 Down ikiayrı maker parent; 300 pay 231$|−13,294088→−244,294088$|Piyasa+74,9243$; geç+69,4843$|
| `1790010000`, Down |300 Up/255$; t604−5 snDownask 23¢|205 Down tek taker, 47,56246$; dört karşı emir|−255→−97,56246$|FIFO çift 1,082012$/pay: pahalı çift, gerçek risk azaltımı|
| aynı |t 741 net 95 Up; −5 snDownask 11¢|48,54 Down taker, 12,26935$|−97,56246→−61,29181$|Aynı işlev, yine ayrı parent|
| aynı |t816'da 298,272939 MERGE sonrası t849:1,727061 Up/0 Down; net nakit maliyeti 23,268812$|tek maker parent t849–850:281,07143 Down; 1,727061 tamamlama+279,344369 yeni risk|−23,268812→−263,263181$|Yedi satır, tek imzalı emir; son piyasa+16,081188$|
| `1790002800`, Up; no-add |t600:131,39 Up/0 Down; nakit 90,6388$; Upask 99¢/Downask 2¢|t600–899 gözlenen dolum yok|taban−90,6388$ değişmez|Piyasa+40,7512$; dolmayan/iptal emirler bilinmiyor|

**DOĞRULANDI:** t816 MERGE receipt'inde iki outcome'dan 298,272939 yakım ve aynı miktar USDC.e ödemesi uzlaştı. Aynı transaction içindeki başka condition'a ait 166$ ayrıca ayrıldı. TRADE nakdi pUSD, bu doğrudan CTF MERGE ödemesi USDC.e: rapor nominal dolar muhasebesidir; bu iki bakiyenin anında aynı işlem bütçesi olduğu varsayılmadı. Toplam zincir denetimi 42 TRADE + 1 MERGE + 2 geç-zincir kontrolüyle 45 ayrı transaction, önceden belirlenen 50 sınırının altında.

**DOĞRULANDI:** pahalı tamamlama zarar kilitlemekle birlikte önceki daha büyük kaybı azaltabilir. Tarihsel 902 maliyeti>1 tamamlamanın 794'ü tabanı iyileştirir. Saf kapatan qpay için taban değişimi `q×(1−yeni birim maliyet)`; önceki maliyetin yüksek olması bunu ortadan kaldırmaz. Aşan miktar ayrı yeni risktir; 237 tarihsel tamamlama açığı aşar.

**KARŞI KANIT:** no-add vakasında beşDown alınabilir ücretli maliyet 0,10686$; bu, aynı envanterde tabanı 4,89314$ iyileştirirken gerçekleşmiş Up sonucunu 0,10686$ azaltırdı. Bu tek adımlı envanter/ödeme aritmetiğidir, dolum garantili politika backtest'i değildir. “Her ucuz çifti tamamla” veya “her an tabanı en yükseğe çıkar” açıklaması gözlenen dolumsuzluğu açıklamaz. Dolmamış bir emir olması hâlâ mümkündür.

## 8. En fazla iki mekanizma ve tanımlanamazlık

| Mekanizma | Destek | Karşı kanıt | Ayırıcı gözlem / fikri değiştiren koşul |
|---|---|---|---|
| M1: pasif imzalı emirlerin parçalı dolması, satırların sahte çoklu karar görünümü yaratması |42 satır 26 parent; birparent 7 satır ve reopen→add; maker 38/42|16/26 geç-add ilk görülenparent; örnekte en uzun 3 sn, 600 snöncesinden taşınanparent yok; 4 taker|Sonuçtan bağımsız yeni örnekte miktar ağırlıklı aynı-parent devam payının piyasa ve gün %95 alt sınırları %50 üstündeyse baskınlık desteklenir; ikisinin üst sınırı da %50 altındaysa reddedilir; aksi hâlde belirsiz. Yerleştirme/iptal kaydı olmadan bekleme süresi ve fiyatın dolumu tetikleme nedenselliği çözülmez.|
| M2: maliyeti>1 olsa da envanter tabanını düzelten karşı alış, ardından ayrı yön riski |794/902 pahalı tamamlamada taban artıyor; t604/t 741 zincirli aktif karşı alış|aynı aktör daha sonra neti aşan tek parentla riski büyütüyor; no-add ucuz tamamlama fırsatı; düzeltilmişH 2 tahmini üstün değil|Aynı ön-risk/fiyat/süre ve gerçek parentta risk azaltma değişkenleri yeni veride kontrolün tahmin hatasını iyileştirirse destek artar. Tekbaşına “risk azaltıyor” ekonomik karar kuralı değildir.|

Bu ikisi birbirini dışlamaz: bir envanter tercihi pasif emirle uygulanabilir. Ölçülen şey rol/parent/marjinal risk ayrımıdır; iki özel algoritmadan hangisinin çalıştığı değildir. Dolumları önceden konan emre zamanlayan bir politika ile aynı emirleri çok kısa süre önce gönderen politika, aynı orderHash/receipt/1 snbook gözlemini üretebilir. Gizli iptal/dolmayan emir yolu değiştirilerek aynı dolumlar korunabilir. **NOT IDENTIFIABLE:** kamu gözleminden tek özel kontrolcü ve maker kuyruk ekonomisi çıkarılamaz.

**Aday neden benzemiyor?**277 geç-ekleme piyasasında donmuş girişte 79 veri eksiği, 50 olasılık, 82 fiyat tavanı, 59 sonraki-fiyat vekili reddi; yalnız 7 giriş. Dördü ilgili Bosona geç dolumundan önce dengelenmiş; yalnız üçü t600 öncesinde. Kalan üçte 23 dolum 630 sonrası; 18'i−5 snfiyat/olasılık/riskten geçse de aday yalnız 600'de ekler. Bu kapılar örtüşür ve ilk-paket düzeltmesi öncesi donmuş tanısal kohorttur. Envanter yolu, eylem zamanı ve uygulama türü birlikte farklı; 55¢tavanını tek başına kaldırmak çözüm değildir.

## 9. Karar ve sonraki iş

**Hemen düzeltilecek:** condition-kimliğini, MERGE sonrası kalan q'yu, ilk-paket etiketini ve hedef-olay/karar-alım ayrımını sürümlü araştırma kopyasında kullan; bağlı çıktıları tekrar üret. Yamalar/çalışan doğru alternatifler burada; ortak aday/protokol değişmedi.

**Bırakılacak iddialar:** her doluma yeni karar denmesi; geç-add geçmiş dolarıyla bağımsız edge ilanı; fiyat-örneği replay'ine taker backtest denmesi; tek-gün ters sonuçtan ters strateji seçimi. FIFO çift katkısını amaç fonksiyonu, pasif rolü garanti maker kârı sayma.

**Tek sonraki deney:** [DENEY.md](DENEY.md). Sonuçtan bağımsız 40 piyasalık parent/rol/risk ölçümü. Mevcut 42 tx finite çalışması yürütüldü, sonraki seçici ve kontroller bırakıldı. Bağımsız yeni politika için giriş sinyali ve maker sıra modeli yetersiz olduğundan ikinci bir işlem adayı uydurulmadı. Donmuşv 0 yalnız kontrol olarak kalıyor.

Ekonomik kabul için ≥10 tam UTC gün, ≥100 gerçekleşebilir giriş, ≥50 eklemeli piyasa, ≥%95 veri kapsamı, masraf sonrası pozitif mutlak sonuç/kontrol farkı, piyasa/gün alt sınırı>0 ve en iyi 3 hariç pozitiflik birlikte gerekli. Bu şartların birlikte sağlandığı gösterilemedi. Sonuç **UNDERPOWERED**; evrensel “yalnız ucuz çift” ve “her satır yeni karar” açıklamaları **REJECTED**; özel politika/garanti maker uygulaması **NOT IDENTIFIABLE**.

## 10. Doğrulama ve araştırma hesabı

Bağımsız Decimal/FIFO/çokluk, condition-kollision, ilk paket/sıra/MERGE, gelecekte alınan fiyat, yanlış token/condition, ücret çifti, eksik taraf/derinlik ve gerçek 42 receipt negatif kontrolleri bırakıldı. Hedefli Ruff/syntax, gerçek arşiv çalışması ve offline hashli tekrar [verification.json](verification.json) içinde. Bütün denetim ayrıntıları alt dizin raporlarında korunur.

Eski 36 fiyat kombinasyonu ve başarısız modeller arşivde; zaman düzeltmesi aynı 36 kombinasyonun duyarlılık tekrarıdır. Yeni eşleştirme denetimleri 4 tasarım, olay paketlemesi 0/5/10 sn, iki bağlam sürümü ve aynı üç yönetim kolu olarak açık kaydedildi; en iyi sonuç seçilmedi. Sonuçlara göre seçilmiş dört zincir vakası evren tahmini sayılmadı. Yeni bağımlılık kurulmadı; Python/NumPy/sklearn/Ruff sürümleri provenance içinde.

Resmî/API kaynakları: [activity](https://docs.polymarket.com/api-reference/core/get-user-activity), [trades](https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets), [ücret](https://docs.polymarket.com/trading/fees), [ChainlinkTWAP](https://docs.polymarket.com/market-data/chainlink-twap), [ExchangeV 2](https://github.com/Polymarket/ctf-exchange-v2). Ham ücretsizAPI/RPC cevapları, URL/istek/alım zamanları ve resmi kaynak hash'leri `new_period/raw`, `accounting/raw_collision_checks`, `onchain/raw`, `execution/official_sources.json` içindedir.
