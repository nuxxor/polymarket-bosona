# BTC5m dışı Bosona araştırması — 21 Eylül 2026

Ana planın çoklu piyasa araştırması ve envanter davranışı aşamasını derinleştirir.
Bu ayrı analiz alanı dışında hiçbir kod/ayar/süreç/bütçe değiştirilmez. LIVE, emir,
ücretli servis, süreç durdurma yok. Eski kaynaklar salt okunur; kullanılan kod
kopyaları source_manifest.json ile donduruldu. Ana plan raw/original_plan.md.

## Kapsam ve baştan sabit kontroller
- BTC5m yalnız önceki rapordan karşılaştırma; yeniden strateji araştırması yok.
- 13–17 Eylül keşif; 18–20 Eylül kronolojik kontrol; 21 Eylül 00:00–12:00 UTC
  ayrı güncelleme. Eski günler önceden görülmüş, hiçbiri gerçek kör test değil.
- Öncelik BTC15m/1h, ETH/SOL5m/15m/1h; yeterli diğer gözlemler betimlenir.
- Sınıf = resmî eventStartTime/endDate + resolutionSource + description;
  slug yalnız aday keşfi. Sonuç, kimlik, token, alış ve ödeme mutabakatı zorunlu.
- İlk saniyedeki dolumlar toplu ilk giriş; 5/10sn paket duyarlılığı. Emir boyu denmez.
- Dört işlem parçası: ilk, aynı yön ek, tamamlama, aşan yeni risk; FIFO paylaştırması
  ile toplam sonuç ayrı. Aynı saniye karşıt yön sırası belirsizliği dışlama kontrolü.
- Hipotezler: sabit gece saati; spot yön/momentum ile giriş; ucuzlayan tarafa ekleme;
  açık envantere göre tamamlama; BTC15m geç ekleme. Başarısız hücreler saklanır.
- Tarihsel kapalı Binance 1dk mumları kapanış+2sn varsayımı ve ts−5/−10sn;
  Chainlink kısa sözleşmelerde Binance referans sadece vekildir. Nihai Gamma
  fiyatToBeat/volume/liquidity karar öncesi kanıt olarak kullanılmaz.
- Geçmiş defter varsa alım ask+ücret+gecikme ile; yoksa gerçekleşebilirlik
  iddiası yok. Bosona dolumuna koşullu deney açık etiketlenir.
- Az sayıda karşılaştırma, eşit pay/pencere, en iyi3 hariç, günler ve ayrı dönemler.
  Kâr değil zarar örnekleri de raporda; taramadan seçilen aday ileri doğrulama ister.

## Kabul ölçütleri
- [x] Eksiksiz aktiviteler, ek kamu verisi, evren ve veri boşlukları kaydı.
- [x] Resmî kurallar ve BTC5m dışı varlık×süre muhasebe tablosu.
- [x] Giriş, seçim, ekleme/tamamlama ve açık risk karşı örnekleri.
- [x] Tek adayın çalıştırılabilir yerel tasarımı, kontrolü ve başarı protokolü.
- [x] Öz-test, hedefli lint/syntax, gerçek API/veri mutabakatı ve aynı sonuçlu tekrar.
- [x] Kısa Türkçe rapor, kaynak/hash/komutlar ve kanıt sınırları.

## Tamamlanan araştırmanın sonucu
- 3.503 BTC5dk dışı işlemli piyasa, 14.014 dolum, 29 grup; ana 8 grupta tüm
  7.956 sözleşme ve toplam 9.110 resmî sonuç. 2.749.016 kamu fiyat örneği.
- Eşit işlem anahtarı içindeki gerçek dolum çokluğu korundu. 158 taze activity,
  39 trades çokluk/miktar kontrolü; son12saatte1.195işlem birebir. Ödeme ihlali0.
- BTC15dk geç ekleme güçlü gözlemsel ipucu; bağımsız uygulama avantajı kanıtlanmadı.
  Saat hipotezi zayıf; davranış aileleri ayrışıyor; ayrı bot/kod sonucu çıkarılmıyor.
- 36 yerel fiyat senaryosu, 5/10sn ve eşit pay/eniyi3hariç karşı örnekler saklandı.
  Kârlı/güçlü aday eşiğini geçen model yok. Tek BTC15 araştırma adayı protocol.json
  içinde; karar motoru ve nedensel defter adaptörü testli; shadow deploy edilmedi.
- 14 temel çıktı tam tekrar çalıştırmada aynı SHA256; regression, Ruff ve compile
  geçti. Asıl repo diğer oturumda ilerledi; bu çalışmanın donmuş src kopyaları aynı.
- RAPOR.md, README.md, results/checks.json ve artifact_manifest.json teslim kanıtı.

## Açık kalan ekonomik kabul
Yeni defterli ileri test, >=10tamgün/100giriş/50ekleme ve masraf sonrası pozitif
kontrol farkı henüz YAPILMADI. Araştırmanın bitmesi stratejinin doğrulandığı anlamına
gelmez. Bu görev yeni shadow/gerçek emir/ücretli servis/süreç veya ayar değişikliği
yapmaz. Üretim scheduler/restart/portföy kesicisi ayrıca uygulama gerektirir.

## 21 Eylül devam görevi: BTC15dk geç ekleme
Yeni kapsam btc15_followup/plan.md içinde. Mevcut aday ve eşikleri donuk kalır.
Kullanıcının yeni açık talebiyle yalnız ayrı, yerel, süreli kamu defteri kaydı
başlatılabilir; mevcut recorder/shadow/Londra süreçleri değiştirilemez.

BTC15dk devam araştırması tamamlandı: btc15_followup/RAPOR.md. Muhasebe
denetimi ve benzer koşul kontrolleri çalıştı; aday değiştirilmedi. Yeni iki
açıklama üstünlük göstermedi. Kullanıcının talep ettiği bağımsız yerel defter
kaydı 72 saat üst sınırla başladı; ekonomik ileri kabul hâlâ açık.

## Ultra ve Fable için ortak bağımsız inceleme promptu — 21 Eylül
Kullanıcı BTC5dk dışı, özellikle BTC15dk strateji araştırmasını eleştirecek iki
inceleyiciye aynı ayrıntılı Markdown promptunu istedi. Bu adım belge hazırlığıdır;
araştırma sonucu, aday ve çalışan kayıtlar değişmez. Kabul: doğrulanmış dosya yolları,
tarihli bulgular/karşı kanıtlar, araştırma boşlukları, yetki sınırları, somut tekrar
ve çıktı ölçütleri; dosyanın okunabildiği ve kritik sayıların kaynakla uyumu kontrolü.

Tamamlandı: `BOSONA_NONBTC5_ULTRA_FABLE_PROMPT.md` (403 satır). 84 açık
yol referansı doğrulandı; son dönem özet/defter rakamları kaynak JSON ile
uzlaştırıldı. Beş donmuş çekirdek dosyanın SHA256 değerleri baseline ile aynı.
Markdown bölüm/backtick ve UTF-8 okuma kontrolleri geçti. Yalnız prompt ve bu
plan notu yazıldı; araştırma kodu, sonuçları ve çalışan süreçler değiştirilmedi.

## Ultra ve Fable sentezi — 21 Eylül
İki sonuç birlikte geldi. Salt okunur iddia/kod denetimi ve küçük karşı
örnekler `ultra_fable_synthesis_20260921/plan.md` kapsamında. Mevcut aday,
protokol, inceleyici çıktıları ve recorder süreçleri korunur. Yeni deney
veya strateji değişikliği bu incelemenin parçası değildir.

Sentez tamamlandı: `ultra_fable_synthesis_20260921/SENTEZ.md`. Rol
sayımları tekrarlandı; Fable replay miktar/boşluk/bütçe karşı örnekleri
çalıştı. S sonuçlarında 12 piyasa/19 kol 15$ sınırını aşıyor. Yeni kontrol
Ruff/syntax geçti; aday/protokol ve kaynaklar korundu. Tam strateji veya
yeni pasif ekonomik motor doğrulanmış sayılmadı.

## Sentez uygulaması — BTC15 birleşik v1
Kullanıcı devamı onayladı. Ayrı `btc15_reconciled_v1_20260921/plan.md`: ham
kimlik/faz/envanter/zaman + rol birleşimi, sonlu replay kusurlarının
düzeltilmesi, gerçek veri kapısı ve tekrarlı kontroller. Aday/protokol ve
çalışan kaynaklar değişmez; yeni shadow veya gerçek emir yok.

Birleşik v1 kontrol aşaması tamamlandı: `btc15_reconciled_v1_20260921/RAPOR.md`.
598 BTC15 piyasası/5.441 dolum uzlaştı; düzeltilmiş 1.150 geç eklemenin 1.077'si
maker. 19 piyasanın 283 receipt dolumu/157 parent uzlaştırıldı. Yeni tanısal
replay'de 14×6 yolda limit ihlali yok; ekonomik çıktı veri eksikliği nedeniyle
null. 16 kontrol, Ruff/syntax ve 13 aynı hashli çıktı geçti; eski aday korunuyor.
Kullanıcının kamu defteri kaydı talebiyle ayrı iki saatlik WS veri pilotu
21 Eylül 20:35:57 UTC başladı; en geç 22:35:57 UTC biter. Eski kayıtlar/süreçler
değişmedi. Pilotun tamamlanması, yeni seçilmiş kohort ve ekonomik kabul açık.

## BTC15 WS gerçekleşme kapısı — 21 Eylül
Kullanıcı sıradaki işi açıklayıp devam etmemizi istedi. Ayrı
`btc15_ws_validation_20260921/plan.md`: ilk tam 20:45–21:00 UTC penceresi,
21:02 alım-zamanı kesiti; defter yeniden kurma, public işlem/receipt/gerçek
maker miktarı ve saat mutabakatı. Girdi kapısı geçmeden ekonomik çıktı yok.
Eski aday ve süreçler korunur; yeni emir veya shadow yok.

İlk WS aşaması: `btc15_ws_validation_20260921/RAPOR.md`. 20:45–21:00 UTC
penceresinde 901/901 defter noktası; 932 receipt ve 923 WS işlemi/miktarı
uzlaştı. İlk API sayfalamasındaki 2 tekrar/2 eksik yeni ayrı listeyle doğrulandı;
orijinal korundu. 16 kısa kotasyon kontrolünde 1 post-only ret, kuyruk arkası
5/önü32 pay; bunlar portföy/strateji PnL'si değil. Ardından ayrı envanterli
M1/M2 olay motoru kuruldu: borsa/öğrenilmiş envanter, iptal sırasındaki dolum,
post-only ret, ortak rezerv ve hedge sınırları. Altı koşullu yolda ihlal0;
M1 bid arkada+0,10$, M2 aynı; önde M2+5,03$ ama10payUp risk taşır.
18 test ve 6 aynı-hashli çıktı geçti. Ekonomi/özel gecikme-sıra kalibrasyonu
açık; ekonomikPnL null ve mevcut aday değişmedi.

## BTC15 WS üç yeni pencere — 21 Eylül 21:50 UTC
Kullanıcı aynı kurallarla yeni tam pencereleri sınamayı onayladı. Ayrı
`btc15_ws_expansion_20260921/plan.md`: 21:00–21:45 UTC üç ardışık pencere,
M1/M2 aynı risk bütçesi, iki kuyruk varsayımı, sabit250/750ms duyarlılığı.
P0 aday kaynağı donuk; aynı dönemin alınma saatli Chainlink kaydı yerel
asıl kamu arşivinden bulundu ve yalnız ayrı önek kopyası alındı. Mevcut
recorder/Londra kaynak-süreç-bütçeleri korunur. İlk yeni pencerenin901/901
defter kesiti iyi olsa da açık bağlantı kopması vardır; ekonomik/test
sonucuna sıfır olarak katılmaz. Zincir/WS mutabakatı ve tekrarlı test sürüyor.

Sonlu karşılaştırma tamamlandı: `btc15_ws_expansion_20260921/RAPOR.md`.
1.759receipt/1.757WS uzlaştı. Üç atamanın biri kopma nedeniyle eksik, ikisi
veri-uygun; eski bağlantı saat uyarısı pencere öncesi tam görüntüyle ayrıldı.
24M1/M2 yolu limit ihlalsiz; üç saat-sırası belirsizliği null. Ana250ms/
kuyrukarkası M1=M2−1,84033524$, bid−1sent−4,45$. P0 iki geçerli bağlamda
filtrelenip sıfır dolum; 55¢/olasılık/zaman eşikleri korunuyor. M2 nakit
karşıörneği:14,50$harcama sonrası3,084$hedge bütçeye sığmıyor. 16kontrol,
Ruff/syntax ve21çıktıda iki aynı hash geçti. Kamu kayıt süreçleri aynı ve
güncel. Ekonomik PnL/özel gecikme-kuyruk kalibrasyonu/uzun ileri test açık.

## BTC15 yürütme ve dengeleme nakdi — 21 Eylül 22:23 UTC
Kullanıcı gerçek emir saatlerini salt okunur incelemeyi ve aynı15$ içinde
dengeleme nakdi ayıran ayrı M2 kolunu onayladı. Kapsam/kabul ölçütleri
`btc15_execution_reserve_20260921/plan.md`: önceki kol eşdeğerliği,
nakit+mutlaknet<=15 garantisi (bekleyen emirlerin bütün dolum köşelerinde),
21:45/22:00/22:15 UTC önceden atanmış üç pencere. BTC5 stratejisi
araştırılmaz; donmuş M4v2 kaydı yalnız emir yürütme saatleri içindir.
Aday/protokol/önceki çıktılar ve recorder/Londra süreçleri korunur.

Bu adım tamamlandı: `btc15_execution_reserve_20260921/RAPOR.md`.12kabul
edilmiş emrin SDK kabul ortancası57,4ms; private eşleşme/öğrenme saati yok.
Üç BTC15 atamasında1.915receipt/1.908WS eşleşmesi denetlendi; üçüncüde
zincirde görünen tek WS işlemi eksik, ekonomik sonuç null. İki uygun
pencerede750ms/arka eskiM2−0,801005$, rezervliM2−0,90$; finansman güvencesi
var ama ekonomik üstünlük yok, rezervli yollarda taker hedge dolumu da yok.
17kontrol, Ruff/syntax ve25çıktıda iki aynı hash geçti. Fable180girişin
102'sinin55¢üzerinde gerçekleştiği, fiyat koruma kontratının değiştiği
doğrulandı. Aday ve çalışan eski süreçler aynı. WS pilotu depolama sınırında
22:33:54UTC kendiliğinden kapandı; uzun ekonomik test/özel saat kalibrasyonu açık.

## BTC15 ham akış tamlığı — 21 Eylül22:53UTC
Kullanıcı sonraki adımı onayladı. Ayrı `btc15_feed_integrity_20260922/plan.md`:
eski kayıp işlemi aç;23:00–23:15UTC tek önceden atanmış BTC15 sözleşmesini
iki bağımsız public WS bağlantısında ham mesaj/UTC/monotonic/sıra ile kaydet.
23:17kesit/23:17:10bitiş,512MiBham/2GiBboşalan sınırı. Eski recorder ve
Londra süreçleri değişmez. Her akış ayrı receipt/API/book/miktar/saat
kapısından geçer; birleşim tek gerçek kuyruk akışı sayılmaz. PnL/politika
optimizasyonu yok. Yeni M5/M6 kapalı saat kanıtları yalnız salt okunur;
kendi private bildirim saati yokluğu kamu LTP saatinden doldurulmaz.

Bu sonlu adım tamamlandı: `btc15_feed_integrity_20260922/RAPOR.md`.
İki ham akışta 351/351 pencere-içi eşleşme, 662 maker parçası ve 901/901
defter noktası. 363 receipt ve API/WS evreninden bağımsız 680 blok taraması
uzlaştı. İlk iki taker API listesinde eksik satış sonraki listede eklendi;
ilk kapı MISSING_DATA olarak korundu. Eski eşit özetli kayıp gerçek;
167 grubun 166’sı eksiksiz olduğundan genel tekilleştirme varsayımı çürüdü.
Public LTP saati kesin eşleşme saati değil; ekonomik PnL null. 8 kontrol,
Ruff/syntax ve 16 aynı-hashli çıktı geçti. Yeni süreli kayıt kapandı, eski
REST PID 1714322 aynı. Aday/protokoller/MAIN/Londra değişmedi. Sonraki açık
iş: önceden sabitlenmiş kapanış mutabakatı ve belirsiz yürütme saati sınırları;
uzun dönem ekonomik kabul henüz yok.

## BTC15 gelecek bilgisi ve yürütme duyarlılığı — 22 Eylül
Kullanıcı üç adımı onayladı. `btc15_timing_sensitivity_20260922/plan.md`:
sekiz mevcut atama, geç API/sonuç muhasebesi ayrı; aynı P0/M1/M2/rezervli M2,
sabit altı saat profili ve iki eşzaman sırası/kuyruk varsayımı. Eski veri
kapıları korunur; yeni gölge/emir/kayıt süreci yok. Eşik taraması değil,
gerçekleşme duyarlılığı; test/lint/ağsız aynı-hashli tekrar kabul koşulu.

Üç sonlu adım tamamlandı: `btc15_timing_sensitivity_20260922/RAPOR.md`.
Gelecek API/sonuç karar girdisinden ayrıldı;72gerçekbağlamda geleceği
silme kontrolü aynı.8atama/6uygun/576koşulluyol;2verieksikliğisıfırsayılmadı.
Sabit6saatprofili×2kuyruk×2sıra×4kol; anaM1−2,6953$,M2−2,7680$,
rezervliM2−1,7141$,P0+0,4857$. M1tüm24senaryoda negatif; M2yalnız
kuyrukönü/geçöğrenmede+1,7063$,eniyipencerehariç−3,3166$. Sağlamedgeyok.
Kabul defteri geçerliliğiyle3sentkararspreadfiltresiayrıldı;14yanlış-null
yoldüzeldi,diğer562veP0aynı.23kontrol,Ruff/syntax,8hesapçıktısındaaynı
hashlitekrarveraporyenidenüretimgeçti. Anaaday/55sent/protokol/süreçler
korundu;yenigölge/emir/kayıtyok. Kalibre ekonomi ve uzunileri kabul açık.

## BTC15 maker fiyat avantajı — 22 Eylül
Kullanıcı üç adımı sırayla onayladı: 1/5/10sn dolum sonrası fiyat hareketi,
aynı koşullardaki diğer makerlar, ardından en fazla iki karar öncesi açıklama.
`btc15_markout_20260922/plan.md` sonuç hesaplanmadan eşleştirme ve hipotezleri
sabitler. Önceki sekiz WS ataması, gerçek parent/rol ve veri kapıları korunur.
Kamu mesajı saati eşleşme saati sayılmaz; markout gerçekleşebilir PnL değildir.
Yeni shadow/emir/recorder veya mevcut aday/protokol değişikliği yok.

Üç adım tamamlandı: `btc15_markout_20260922/RAPOR.md`.8atama/6uygun,
5.240makerBUY;Bosona22dolum/14parent/5piyasa.1/5/10snmarkout
+0,678/−0,225/−0,417sent/pay;gerçekleşebilirPnLdeğil.22/22kontrol,
10sngörelifark+1,072sent;%93tekpiyasada,tekparentçıkarılıncaişaretdeğişiyor.
Fiyatdevamlılığızayıf/zamanaduyarlı,yönlüakışdesteklenmedi;yeniadayyok.
34başkamakerparçasındaücretgörüldü;rolzincirden,ücretsıfırvarsayımındandeğil.
10kontrol/48gerçeknedensellikbağlamı,Ruff/syntaxve12çıktıdaikiağsızaynıhash
geçti.Aday/protokol/kaynaklar/süreçlerkorundu.Çokgünlüekonomikkabulaçık.

## G1 canlı pilotundan aktarım — 22 Eylül
Kullanıcı aynı repodaki G1 test/canlı performansını okuyup geliştirme derslerini
çıkarmamızı istedi. `g1_transfer_review_20260922/plan.md`: mevcut BTC5 G1 pilotu
salt okunur incelenir; yeni BTC5 strateji araştırması veya BTC15'e kâr aktarımı
varsayılmaz. Eski hesap devri, tüm atanmış pencereler ve gerçek yürütme kanıtı
ayrılır. G1/ana repo/Londra/aday/süreç/bütçe değiştirilmez.

G1 incelemesi tamamlandı: `g1_transfer_review_20260922/RAPOR.md`.
İlk 30dk/6 piyasa +9,206314 dolar; 63 kabul/36 dolmuş parent/40 gerçek
maker dolumu. A/B özel kayıt, activity, zincir ve Gamma eşleşti.
FIFO çift +2,800171, açık pozisyon +6,406143; BTC15 avantajı kanıtı değil.
G1'in bant içinde emri koruması/net5/pasif tamamlama politikası önceki
BTC15 M1/M2'den farklı. Sırada kendi dolan ve dolmayan emirleriyle L2
kuyruk modelini sınamak, sonra eşit limitlerle koruma/yenileme karşılaştırması
var; bu görevde kuyruk kalibrasyonu veya yeni deney/deploy yapılmadı.
Dört çıktı ağsız aynı hash, kümülatif dolum saati/politika regresyonu,
Ruff/syntax geçti. Donmuş P0 ve Londra kaynak/süreç/bütçelerine dokunulmadı.

## BTC15 teknik yürütme devamı — 22 Eylül
Kullanıcı G1'in BTC5 olduğunu, yalnız teknolojik iyileştirmelerinden
öğrenmemizi ve BTC15 araştırmasına dönmemizi belirtti.
`btc15_transport_v2_20260922/plan.md`: kabul etkinliği/POST cevabı/iptal
etkinliği/teyit/dolum öğrenilmesi ayrılır; aynı BTC15 politikaları ve
risk sınırları, eski sekiz atama. G1 stratejisi aktarılmaz, P0 korunur.

BTC15 teknik adımı tamamlandı: `btc15_transport_v2_20260922/RAPOR.md`.
Kabul etkinliği/POST cevabı/iptal etkisi/teyit/dolum öğrenilmesi ayrıldı;
POST cevabı yokken iptal erteleniyor, rezerv teyide kadar korunuyor.
BTC15 karar dalı aynen; 192 eski yol birebir. 480 ana + 288 karşı-deneme
limit ihlalsiz. Bir sent geride p95/arka +3,6968 dolar, eski −500ms işlem
stresinde −3,35; yalnız eski iptal teyidiyle −3,00. Yeni kârlı aday yok.
17 kontrol/Ruff/syntax; dokuz hesap çıktısı ağsız aynı hash. G1'in
stratejisi veya BTC5 kârı aktarılmadı. Sayısal saatler yalnız teknik stres;
BTC15 kalibrasyonu ve yeni çok günlük ekonomik kabul açık. Kaynaklar,
P0/protokol, Londra ve mevcut süreç/bütçeler korundu.
