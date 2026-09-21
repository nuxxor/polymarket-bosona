# Bosona BTC5m — PRO, Ultra ve Fable sentezi

21 Eylül 2026. Amaç: üç incelemenin önemli bulgularını kaybetmeden değerlendirmek; hangi bulgunun araştırmanın yönünü değiştirdiğini, hangisinin henüz hipotez olduğunu ayırmak.

**Kararım:** Mevcut shadow'larla Bosona'nın bütün politikasını çözmüş değiliz. Ucuz taraf/RSI geri dönüşü/kârlı eşleme araştırması bağımsız bir aday olarak kalabilir; Bosona'nın keşfedilmiş modeli diye sunulmamalı. En güçlü yeni araştırma nesnesi, **parçalı gerçekleşebilen emirler, bunların yürütme rolü ve işlem öncesi net envanter**. Muhtemel politika, pasif teklifler ile gerektiğinde aktif alımları birleştiriyor. Kazancı üreten tam fiyatlama, büyüklük ve iptal kuralı hâlâ bilinmiyor.

Bu bir sentez ve salt okunur denetimdir. Raporlardaki “durdur”, “yeni deney aç” önerileri uygulanmadı; kaynaklar, Londra süreçleri, stratejiler ve bütçeler değiştirilmedi.

## 1. Üç incelemeye nasıl ağırlık veriyorum?

| İnceleme | Gerçekte eriştiği kanıt | En değerli katkısı | Sınırı |
|---|---|---|---|
| **PRO** | Güncel brief ve eski `b471fab` paketinden dört piyasanın 26 alış kaydı; `add159d` kaynağına erişememiş | Karşı alışın sentetik çıkış olarak doğru ekonomik temsili; aynı girişten taşıma/kapama karşılaştırması | Güncel kod, runtime ve davranışın tarihsel sıklığı için onay değil |
| **Ultra** | `add159d343948e4b46a5491b9bab4c78fceeeb40`, ham activity çokluğu, eşleşmiş exchange bağlamı, izole kod kontrolleri | Dolum ile kararın ayrılması; parent emir ve rol doğrulamasının önceliği | Emir kimliği ve kesin onchain rol çözülememiş; Londra'ya bağlanmamış |
| **Fable** | Aynı commit, daha geniş rol/ücret/defter analizi ve alt çalışma notları | Maker ağırlığı, iade ekonomisi, kotasyon/kuyruk hipotezi ve uygulama sorunları | Bazı kesin ifadeleri kendi ölçüm sınırlarını aşıyor; dolmamış emirler ve iptaller görünmüyor |

Model adına göre bir kazanan seçmiyorum. PRO'nun ekonomik ayrımı, Ultra'nın kimlik/ölçüm disiplini ve Fable'ın yürütme araştırması birbirini tamamlıyor. Üçü büyük ölçüde aynı tarihsel veriyi kullanıyor; aynı sonuca varmaları üç bağımsız ileri deney değildir.

Bu oturumda PRO'nun paylaşılan tam metnini, Ultra'nın yerel tam raporunu, Fable'ın tam artifact'ini ve ilgili kotasyon/iade alt notlarını okudum. Ultra'nın ana hesap betiğini ayrı çıktı dizininde yeniden çalıştırdım: JSON çıktısı orijinaliyle tamamen eşleşti. PRO'nun dört yolunu depodaki tarihsel activity satırları üzerinden ayrıca doğruladım. Bu kontroller yeni zincir verisi toplandığı veya bütün alt analizlerin yeniden koşulduğu anlamına gelmiyor.

## 2. Araştırmanın yönünü değiştiren bulgular

### 2.1 Dolum sayısı karar sayısı olmayabilir — en önemli kimlik sorunu

Ultra'nın exchange olayıyla eşleşen son-100-saniye örnekleminde 4.331 kaydın 4.015'i, sıfır ücret primi ve karşı-token BUY/aynı-token SELL deseniyle pasif gerçekleşmeyle tutarlı. Bu **kayıt ağırlıklı %92,7**, bütün işlemlerin veya payların oranı değil. Fable'ın daha geniş sınıflandırmasındaki yaklaşık **%93,1 kayıt / %83,3 pay** maker oranıyla yön olarak tutarlı.

Fable ayrıca API'nin `takerOnly=true` filtresiyle son özetinde 1.818/1.818 uyum bildiriyor; bu, yalnız ücret imzasına göre daha güçlü bir çapraz kontrol. Bu API karşılaştırmasını burada yeniden çalıştırmadım. Ultra'nın 1.345 pozitif primli kaydın 1.302'sini dar toleransla ücret formülüne eşleştirmesi ile Fable'ın yuvarlama dahil tam uyum ifadesi de aynı tolerans testi değil. Kesin rol/parent kimliği, fiyat yuvarlama toleransından bağımsız olarak exchange olaylarından doğrulanmalı.

Son-20-saniye “add” grubunun 271 kaydından 157'si önceki aynı taraf dolumuyla aynı saniyede, 210'u en fazla üç saniye sonra. Bir örnekte yedi dolum toplam **297 pay**: önce ücretli 49,72, sonra sıfır primli 247,28 pay. Bu, tek emrin önce hemen, kalanının bekleyerek dolmasıyla açıklanabilir. Birkaç farklı emir de aynı izi bırakabilir; **aynı parent orderHash görülmeden tek emir ilan edemeyiz**.

Örneğin t=250'de verilen bir emir t=256, 257 ve 259'da doluyorsa, bunları üç ayrı RSI kararı saymak yanlış açıklama üretir. Hatta dolum anındaki göstergenin uygunluğu emir kararına ait olmayabilir. Bu nedenle daha fazla indikatör taramadan önce karar birimini düzeltmek gerekir.

**Önemli ek ayrım:** Maker ağırlığı, kârın tamamının maker işlemlerinden geldiğini göstermez. Yeniden üretilen eski 19.761 kayıtlı hesapta sıfır primli grubun nakit maliyetli katkısı **+3.027,49 $**, pozitif primli grubunki **+5.291,95 $**. Bunlar gerçekleşmiş bacak katkıları; birbirinden bağımsız iki stratejinin PnL'si değildir. Biri diğerinin oluşturduğu envanteri kapatıyor olabilir. Saf maker açıklaması da saf yön tahmini kadar erken bir genelleme olur.

### 2.2 Karşı BUY bazen çıkıştır — PRO'nun en güçlü katkısı

Nakit giriş eksi çıkışı `N`, eldeki tokenler `U` ve `D`, Up sonucunu `Y` olarak yazınca:

```text
terminal servet = N + U·Y + D·(1−Y)
                = (N+D) + (U−D)·Y
```

`U−D` açık yön riskidir. Elde Down varken Up almak, açık miktara kadar bu riski azaltır. Up'ın net nakit maliyeti `p` ise, o miktarda Down için `1−p` çıkış değeri oluşturur. Eş miktar merge edilirse tokenler collateral'a dönüşür; ücret yokken terminal ekonomik durum değişmez. Kullanılabilir nakit ve kapasite ayrıca değişebilir. [Resmî pozisyon yönetimi](https://docs.polymarket.com/trading/positions/manage).

PRO'nun 21:20 örneğinde önceden alınmış Down'lar **31,74193 $** kaybedecek durumdadır. Sonradan **38,77 Up @0,959** alınması toplam pencereyi kârlı yapmaz; fakat gerçekleşen Up sonucunda zararı **1,58957 $ azaltır**. Eski maliyet toplam muhasebede durur, aynı mevcut pozisyondan taşıma/kapama farkında birbirini götürür.

Bu, “yüksek maliyetli karşı alımların hepsi doğrudur” demek değildir. Ters sonuçta aynı kapama değer kaybettirebilir. Kararın iyi olup olmadığı bugünkü fiyat ve belirsizliğe bağlıdır; sonucu gördükten sonra başarılı stop-loss niyeti atayamayız.

**0,98 sınırı Bosona'nın evrensel kuralı olarak yanlışlandı.** Ancak bu sınırın bizim botta kaldırılması da bu araştırmayla doğrulanmış bir iyileştirme değil. Önce risk azaltımını ayrı karar sınıfı olarak ölçmeliyiz.

### 2.3 Fiyatı beklemek ile o anda satın almak farklı ekonomi üretir

Fable'ın maker teşhisi, mevcut ask'tan alan shadow'ların neden Bosona'nın fiyat avantajını yakalayamayabileceğine güçlü bir açıklama getiriyor. Maker ücretinin sıfır, kripto taker ücretinin `q × 0,07 × p × (1−p)` olması da farkı büyütür. Tarihsel nakit maliyetine ücret ikinci kez eklenmemelidir. [Resmî ücretler](https://docs.polymarket.com/trading/fees).

Fakat **“biz aynı mint'in karşı koltuğuna oturuyoruz” her alış için kanıtlanmış değil**. Bosona Up'a 0,08 bid koyarken bizim Up'ı 0,09 ask'tan almamız, aynı sonuç yönünü daha pahalı almaktır. Otomatik olarak Bosona'nın ters yönüne bahis yapmak değildir. Gerçek karşı taraf/mint eşleşmesi işlem kimliğiyle gösterilmelidir.

Fable'ın 1.470.921 gözlemde bulduğu `bid(Up)+ask(Down)=1` aynalaması, iki tokenin ekonomik ve defter ilişkisini anlamak için önemli. Ama “ucuz taraf” her bağlamda anlamsızlaşmaz: kazanma ihtimaline göre pahalı/ucuz olma sorusu hâlâ vardır. Aynalı kayıtlar iki bağımsız fiyat kanıtı gibi sayılmamalıdır.

### 2.4 İadeler araştırma modeline girmeli; garantili gelir diye yazılmamalı

Fable, ham veride **18 iade hareketi / yaklaşık 4.112,99 $** buluyor. Bu bütün ilgili cüzdan akışı; tamamı BTC5m kârı değildir. BTC5m tarihsel kohortuna verdiği yaklaşık **1.933,17 $**, maker ve taker ücret eşdeğerleriyle hesaplanan atıftır. Ödeme günü ile kazanılma günü, piyasa kapsamı ve gerçek günlük nakit mutabakatı ayrı tutulmalıdır.

Önceki raporlarımız açıkça “rebate hariç” dediği için başlık PnL'si bu yüzden aritmetik olarak yanlış değildi. Ancak Bosona'nın ekonomik motivasyonunu araştırırken bu bileşeni sürekli dışarıda bırakmak eksikliktir.

Güncel resmî maker programında kripto payı %20; bireysel ödeme, ücret eşdeğeri payının ilgili havuza uygulanmasıyla hesaplanıyor. Her doluma koşulsuz sabit ödeme varsaymamalıyız. [Maker programı](https://docs.polymarket.com/programs/maker-rebates).

**Fable'ın “belgelenmemiş %18” ifadesine düzeltme:** Güncel resmî taker programında %18, son 30 günlük **200.000 $ ağırlıklı hacim** eşiğindeki Gold kademesidir. Eşik altındaki hesapların oranı farklıdır; 2.000 $ altında sıfırdır. Bosona verisindeki %18 deseni bu kademeyle tutarlı olabilir, tarihsel hesap kademesinin ayrıca doğrulanması gerekir. [Taker programı](https://docs.polymarket.com/programs/taker-rebates).

Kazanılmış iadenin çözüm yönüne bağlı olmaması, gelecekte bu geliri üretmenin “varyanssız/risk almadan” olduğu anlamına gelmez. Dolmak için taşınan envanter, olumsuz fiyat hareketi, program ve hacim koşulları vardır. Bizim beş paylık deneylerimiz Bosona'nın iade oranını otomatik devralmaz.

## 3. Fable'ın kotasyon hipotezinde güçlü olan ve henüz çıkaramayacağımız şeyler

Fable'ın tam raporunun altındaki `p2/n1_report.md` ölçümü, özet cümlelerden daha temkinli:

| Ölçüm | Yararlı çıkarım | Çıkaramayacağımız sonuç |
|---|---|---|
| 249 ve katlarında aktör dolum kümeleri | Tekrarlayan büyüklük/emir parçalanması araştırılmalı | Her 249 pay artışı Bosona'dır; tek parent'tır |
| 42.042 adet +249 defter artışı; ilgili alt kümede yalnız %6,6 ardından yakın aktör dolumu | Basit büyüklük parmak izi çok sayıda yanlış eşleşme üretir | 249 görür görmez Bosona tespit edildi |
| 444 dolumla ilişkilendirilmiş yerleşim | Fiyat seviyeleri ve akışa tepki için koşullu örneklem sağlar | Dolmayan/iptal edilen bütün teklifler görülüyor |
| Yerleşimlerin %17,1'i son olaydan ≤5 ms; medyan yaklaşık 50 ms | Hızlı akış bağlantısı araştırmaya değer | Botun bütün karar gecikmesi 5 ms veya colocation bunu garantiler |
| İlişkili seviye miktarı diliminin medyan ömrü yaklaşık 0,75 s | Kısa ömürlü defter hareketleri var | Doğrulanmış Bosona cancel TTL=0,75 s |
| Dokunuşta %39,9; bir tik geride %19,4; iki tik geride %16,0 | Pasif teklif fiyatı önemli aday | Tek ve sabit merdiven parametresi bulundu |
| Bilinen trade olayları tape hacminin yaklaşık %72,3'ünü kapsıyor | Replay'de gözlenmeyen gerçekleşme aralığı gerekir | Trade görünmeyen her miktar azalışı iptaldir |

İlişkilendirme daha sonra gerçekleşen aktör dolumuyla seçildiği için seçim yanlılığı var. Toplu olay yayını ve saat eşleşmesi de 5 ms yorumunu etkileyebilir. Görülen tek taraflılık, görünmeyen karşı taraf emirlerinin yokluğunu kanıtlamaz. Kuyruk önündeki miktarın ne kadarının iptal edildiği de bilinmiyor.

**Sonuç:** Kuyruk avantajı ciddi aday; “tam botu bulduk: 249 pay, 5 ms, 0,75 s” sonucuna henüz ulaşmadık. Londra'da olmak ölçülmüş emir-kabul/iptal/gerçekleşme gecikmesi veya kuyruk önceliği kanıtı değildir.

Fable'ın üçüncü mekanizması, son 25 saniyedeki 0,88–0,97 pasif alımlar, ayrı aday olarak korunmalı: bildirdiği 157 dolum, pay ağırlıklı %99,6 kazanma ve yaklaşık +632 $ ilginç. Ancak aynı araştırmadan seçilmiş dar hücre, ileri doğrulama değil. O fiyatların taker olarak alınabildiği de gösterilmedi; bu yüzden “son saniyede favoriyi al” kuralına çevrilmemeli.

Alt çalışmadaki 591 uygun “kilit” gözleminde 0,98 altı ask bulunmaması, pasif fiyatın erişilebilirliğini özellikle önemli kılıyor. Başka fiyat/zaman hücrelerinde tahmin edilen yüksek olasılığın kötü kalibrasyonu da bütün pahalı alımları güvenli saymamıza engel. Bu hücreler aynı evrenmiş gibi birleştirilmemeli.

## 4. Düzeltme ve kapsam envanteri — Fable K1–K13 dahil

“Doğrulandı” aşağıda ya bu oturumdaki tekrar/kod okumasını ya da açıkça belirtilen inceleme kanıtını ifade eder. Bütün sayısal alt analizleri burada yeniden üretmedim.

| Konu / kaynak | Sentez ve işlem karşılığı |
|---|---|
| **Çokluk kaybı — Ultra, Fable K1** | Yeniden üretildi: ham 19.768 BUY, saklanan 19.761. +1.039 pay ve +648,21 $ maliyetle PnL **8.319,438464 → 8.313,228464**. Gerçek dolumları dict/set ile silen anahtarlar araştırma, `muhasebe.py` ve `record_fills_tape.py` yollarında var. Sadece slug eklemek aynı görünümlü gerçek dolum sorununu çözmez. Kaydedici tekrarlarını ayıran multiset/olay kimliği gerekir. Tape'deki %1,2 miktar kaybı Fable bulgusudur; tamamını yeniden ölçmedim. |
| **Nakit olayları ve 44 REDEEM — Ultra, K1/K2** | Condition içermeyen anahtar ayrı sıfır ödemeleri silebiliyor. Rebate, sell, split, merge, redeem, transfer ve pencere öncesi envanter ayrı korunmalı. Sonuç ödeme hakkı ile aynı tarihe kadar fiilen alınmış redeem aynı şey değil. Ham kayıttaki tüm kalan nakit farklarının açıklanmış olduğunu söylemiyorum. |
| **Ücretli nakit / fiyat bazlı brüt — K3** | `usdcSize` ile `qty×price` farklı ölçüler. Yaklaşık 10.109,29 $ fiyat bazlı toplamla 8.319,44 $ nakit bazlı toplamın farkı ücret bileşeni. Aynı tabloda net/brüt karıştırılmamalı; tarihsel ücrete güncel tarife körlemesine eklenmemeli. |
| **Aynı saniyede sıra — PRO, K4** | Fable 1.440/1.842 piyasada 13.203 aynı-saniye kayıt bildiriyor. Yalnız farklı yönlü 41 örneğe bakmak yeterli değil; aynı yönlü farklı maliyetli lotların sırası sonraki FIFO etiketini de etkiler. Net miktar değişmeyebilir, maliyet ataması değişebilir. Belirsiz sıra için aralık gerekir. |
| **Gerçek fiyat / gecikmeli ask — K5, PRO, Ultra** | +53,24 ile −217,02 arasındaki 270,26 $ fark aynı ödeme altında fiyat/maliyet farkıdır. Fable'ın ücret/spread/gecikme ayrıştırması yararlı; örneklem eşitliği kontrol edilmeden bütün farkı gecikmeye yazamayız. Kamu, exchange, kaynak ve yerel alınma saatleri ayrı tutulmalı. |
| **Çoklu tarama — K6** | Ultra'nın 50 kural×zaman karşılaştırması ile Fable'ın 776–790 araştırma karşılaştırması aynı sayım birimi değil. Daha geniş keşif ve aynı veride seçim sorunu ikisinde de var; bunları bağımsız test sayısıymış gibi birleştirmemeliyiz. Tarihsel 270'in 280'i geçmesi şimdi 270'e geçme gerekçesi değil. |
| **Gizli kapsam filtresi — K7/K11, Ultra** | `decide()` kullanılmayan `final_up_prob` alanını şart koşuyor; asıl RSI/momentum adayından daha ağır veri gereksinimi oluşuyor. Ultra'nın aynı 167 kararında 114 yerine 123 bağlam geçerli, ek dokuzun biri sinyalli. Bu kod yolunu okudum. Eksik veriyi sıfır işlem/başarılı bekleme saymamalıyız. |
| **Sürüm/donma — K8** | Eski protokol hash'inin değişen ana kaynakla uyuşmaması incelenmeli. Ancak **21 Eylül 17:46 UTC Londra snapshot'ında üç güncel süreç kaynağı kendi manifest'iyle birebir eşleşiyor**. Yeni sürümler ayrı başlangıçla çalışıyor. Eski belge bağı ile canlı deneyin sessizce değiştirilmesini aynı kusur saymıyorum; eski hash'i yeni dosyaya uydurarak geçmiş silinmemeli. |
| **Tamamlama kayması — K9** | Kodda tamamlamanın `max_cost` sınırı kalan 0,98 çift bütçesi; girişteki karar fiyatı +1¢/pay koruması aynı biçimde uygulanmıyor. Fable'ın +6,975¢/pay örneği bu ayrımla tutarlı. **Sınırsız maliyet değil**, farklı sınır. Eğer tüm emirler için 1¢ deniyorsa uygulama/belge uyumsuzluğu var. Sıkılaştırmanın tamamlanmaya etkisi yeni deney kapsamıdır. |
| **Katılım fiyat bandı / alt sınır — K10** | İlk katılımda 0,50 tavanının kaldırılması açık deney tercihiydi; nakit, açık pay, en kötü ödeme ve fiyat kayması sınırları var. Bunu başlı başına kazara sınırsız alım diye tanımlamam. Düşük fiyatların zararlı bulunmasından yeni keyfî alt fiyat bandı çıkmaz; geçerli fiyat/tick kontrolü ile strateji filtresi ayrılmalı. |
| **Favori kontrolü ölçülemiyor — K12** | Karşılaştırma için aynı anda yeterli ask derinliği yoksa sonuç null kalmalı. Eski 5/5 eksikliğe ek olarak son ortak 35 pencerede t280 favori maliyeti geçerli 28 bağlamın yalnız üçünde ölçüldü. Bu kontrol ekonomik hüküm vermek için yeterli kapsam sağlamıyor. |
| **`outcomeIndex:999` — K13** | Fable ham activity'de 190 BTC5m satırı bildiriyor; ikinci dönem seçimi/yorumunu ciddi etkileyebilir. Sadece outcome metninden körlemesine taraf atamamak; condition'ın resmî token eşlemesiyle düzeltmek ve ham satırı saklamak gerekir. Son 35 piyasanın doğru token eşleşmesi tarihsel 190 satırı onarmaz. |
| **Mum istek/yanıt sınırı — Ultra** | Bu oturumda izole yanıtla yeniden ürettim: dakika kapanmadan istenmiş kısmi mum, yanıt dakika+2 saniyeyi geçince kapanmış sayılabiliyor. Filtre `received` zamanını kullanıyor. Ultra'nın 146 eski yanıtta gerçekleşmiş örnek bulamaması, kontrollü kusuru ortadan kaldırmaz; tarihsel PnL etkisi gösterilmedi. |

Bu görevde bunlara yama uygulanmadı. Bir sonraki uygulama görevinde önce kanonik kayıt/kimlik ve nedensel zaman kusurları düzeltilmeli. Deney filtresi değişiklikleri onarım gibi gösterilmeden ayrı sürümlenmelidir.

## 5. İstatistik ve ekonomik yorumda korunacak ayrımlar

1. **Takvim evreni:** `[13 Eylül 00:00, 20 Eylül 22:30)` aralığı 2.286 slot. 1.842 gözlenen piyasa dışındaki 444 slot otomatik veri kaybı değil; tam veri/işlem yok, tam veri/işlem var, eksik, çözülmemiş, piyasa yok ayrılmalı. Son 22:30 başlangıcını dahil etmek evreni 2.287 yapar.
2. **FIFO katkısı nedensel kazanç değil:** Çiftin ödemesi sonuçtan bağımsızdır. Kazananları ters çevirmek çift katkısını değiştirmemeli. Bu, muhasebenin özelliğidir; çift kurmanın hiçbir ekonomik avantaj üretemeyeceğini kanıtlamaz. FIFO/LIFO ile bileşenler değişirken toplam sabit kalabilir. Çift tabanı ve açık risk takibi korunmalı; bunların ayrı t-istatistikleri strateji keşfi diye kullanılmamalı.
3. **Ağırlıklandırma:** Kayıt başına beş pay parçalanmayı ödüllendirir. Son-20 grubu bu şekilde +185,69 $, piyasa başına toplam beş payla +27,26 $; bütün tarihsel piyasalar beşer toplam paya ölçeklenince −53,27 $. Sonuncuyu yeniden ürettim. Hiçbiri uygulanabilir yeni politika PnL'si veya miktarın nedensel edge olduğunu kanıtlamaz.
4. **Yoğunlaşma ve belirsizlik:** PRO'nun adayda en iyi üç payı %62,52 ve sonraki dönemde tek gün payı %95,72 hesapları, Ultra'nın dar örneklemi ve Fable'ın işlem PnL aralığının sıfırı kesmesi ciddiye alınmalı. Fable, tarihsel toplam için yaklaşık **[−799, +17.567] $**, medyan pencere **−1,92 $**, en iyi on piyasanın toplamın **%67'si** olduğunu bildiriyor. İade atamasıyla verdiği **[+1.357, +20.702] $** aralığı aynı araştırma dönemine ait. Büyük kazançlara dayanmak otomatik ret değildir; boy/risk kapasitesini önemli kılar. “Sıfırdan ayırt edilemedi” ifadesi “edge kesin sıfır” anlamına gelmez. İadeyle pozitifleşen tarihsel bootstrap aralığı ileri doğrulama değildir; bu aralıkları burada yeniden bootstrap etmedim.
5. **RSI adayı tamamen anlamsız ilan edilmemeli:** Ultra aynı 140 pencerede cheap-only +2,62 $ / ex-top3 −11,32 $; rebound +19,93 $ / ex-top3 +7,47 $ buluyor. Fable'ın daha sonraki ex-top3 yaklaşık +0,16 $, görülmemiş küçük örnek −2,53 $ ve t280 ucuzluk koşulunun 140/140'ı geçmesi, genelleme iddiasını zayıflatıyor. Aynı veriyle daha iyi saat/eşik seçmeye devam etmek çözüm değil. Ask fiyatından türetilen beklenen kazanma sayısı da kusursuz gerçek olasılık değildir.
6. **Katılım saf yönetim ablasyonu değil:** Pencere sayısıyla beraber ilk giriş zamanı, fiyatı, toplam harcanan nakit ve sonraki envanter yolu değişiyor. Fable'ın t30/t150 ve sürüklenme teşhisleri bu karışmayı gösteriyor; kesin günlük zarar tahmini olarak alınmamalı. Deney “ilk katılım politikasının toplam etkisi” olarak okunabilir, yalnız giriş kapısının izole etkisi olarak değil.
7. **Tamamlamaları silen karşı-olgusal hesap:** Fable'ın bütün karşı alımları çıkarıp sonraki gerçek alımları koruyarak bulduğu +3.797 $ fark, gerçekleşmiş bacakların betimleyici katkısıdır. Değişmiş envanterde Bosona'nın sonraki işlemlerini aynı tutmak bütün botun alternatif PnL'sini vermez. Bu yüzden PRO'nun aynı başlangıçtan tek olay/hold karşılaştırması daha temiz bir kapsam sunuyor.
8. **“Varyans −%19” düzeltmesi:** Fable'ın ayrıntılı tablosunda 137,451 → 110,755 değerleri **standart sapma**. Azalma %19,42; bunların karesindeki varyans azalması yaklaşık %35,07. Alt rapor sd ayrımını doğru yazıyor, özet bunu varyans diye kısaltmış. Ayrıca iki sayı da yukarıdaki aktör-koşullu karşılaştırmanın sınırlamalarını taşıyor.
9. **Oracle:** TWAP referansını spotla özdeşleştirmemek doğru. Ancak özel Chainlink feed'inin tam örnekleme/ağırlıklandırma ayrıntıları yayımlanmış değil. Karar anında alınmış resmî başlangıç eşiği, feed kimliği, rapor ve receipt zamanı gerekir. Kendi ortalamamız bir tahmindir; resmî feed'in kesin kopyası değil. [Resmî TWAP açıklaması](https://docs.polymarket.com/market-data/chainlink-twap).

## 6. Örnek yolların her biri neyi sınırlıyor?

| Piyasa başlangıcı / kaynak | Sonuç veya davranış | Sentez |
|---|---|---|
| 19 Eylül 21:10 / PRO | Erken 0,71–0,74 Down; **+76,36 $** | Ucuz-taraf ve geç-giriş zorunluluğuna karşı örnek; niyet/fiyatlama sinyali bilinmiyor |
| 19 Eylül 21:20 / PRO | Son Up karşı alımı **+1,59 $** yerel katkı; toplam **−30,15 $** | Pahalı çift ile kötü son karar aynı şey değil |
| 19 Eylül 21:30 / PRO | 0,44 ilk Down, 0,74 geç ekleme; **+4,74 $** | Her eklemede ucuzluk kapısı aktörün bu yolunu dışlıyor |
| 19 Eylül 21:35 / PRO | Pahalı karşı alım ve merge; **−210,23 $** | 0,98 üstü risk azaltımı ikinci bağımsız piyasa örneği |
| 17 Eylül 20:25 / Ultra | **+601,84 $**; son kaybeden Up'lar maliyetli ama tabanı −240,84'ten +440,57'ye çıkarıyor | Yanlış sonuç tarafını almak, risk açısından anlamsız olmak zorunda değil; çift katkısı ile son bacak katkısı farklı |
| 14 Eylül 16:10 / Ultra ve Fable B | Yedi parçalı 297 pay, toplam **−564,71 $** | Pasif dolum ve büyük miktar avantaj garantisi değil; aleyhe seçilim ve hızla değişen bağlam var |
| 16 Eylül 18:15 / Ultra | Erken dengelenince taban **−33,48 $**, sonra toplam **−442,27 $** | Aktör zararı kilitleyebiliyor; mekanik sürekli nötrlük de uygulamıyor |
| 15 Eylül 16:35 / Fable A (`1789490100`) | Yaklaşık **+984 $**, pasif basamakların büyük alıcılarla dolması | Karşı taraf akışı/yürütme ciddi aday; eksik Chainlink nedeniyle yön sinyali yok denemez |
| 20 Eylül 21:05 / Fable C | Ucuz Up yükselse de satış yok; sonra yeni risk ve aktif karşı alımlar; yaklaşık **−155 $** | İyi fiyat hareketi gerçekleşmiş kâr değil; pasif giriş ve acil risk azaltımı ayrılmalı |
| 20 Eylül 16:50 / Fable D | Yaklaşık 0,91 pasif Down, **+63,66 $** | Pahalı kazanan alım yalnız son-saniye çözüm kilidi gerektirmiyor |
| 20 Eylül 19:35 / Fable E | 44 maker dolumu, **+376,25 $**, iki taraflı birikim | FIFO'nun “tamamlama” etiketi mutlaka ayrı agresif kapama niyeti demek değil |

İlk dört yolun aritmetiği bu oturumda doğrulandı; sonraki üç Ultra yolunun hesapları tekrar çalıştı. Fable A/C/D/E'nin ayrıntılı yolu rapordan okunmuştur; burada bütün ham book çıkarımı yeniden yapılmadı. Örnekler baskın sıklığı tahmin etmek için seçilmiş rastgele örneklem değildir.

## 7. Üç öneriyi birleştiren araştırma sırası

**Önce tek bir emir/rol/envanter mekanizma çalışması; sonra gerekiyorsa kotasyon deneyi.** Şu an bir sonraki indikatörü veya yeni shadow'u seçmek öncelik değil.

### A — Kayıt kimliği ve yürütme rolü

Mevcut kazanç/kayıp örneklerinde sürüme uygun exchange olaylarını çöz: transaction + log/fill kimliği, actor orderHash, net token, nakit ve ücret. `maker` isimli sözleşme alanını tek başına pasif likidite rolü sayma; hangi emrin eşleşmeyi başlattığını ayrıştır. Bir transaction birden fazla gerçek dolum/parent barındırabilir.

Önce yedi dolumluk 297 pay örneği gibi sınanabilir vakalarda miktar/nakit mutabakatı; sonra aynı orderHash'e ait dolumları grupla. Kayıt, parent ve pay ağırlıklarını ayrı raporla. Geç “add”lerin ne kadarı zaten dolmaya başlamış parent'ın devamı? Pasif pay oranı nedir? Aynı parent içindeki envanter değişikliği ile yeni emir kararını ayır.

Onchain kayıtlar parent'ın dolan parçalarını gösterebilir; **hiç dolmayan emir, kesin gönderim anı ve bütün iptaller yine görünmeyebilir**. Decoder bu bilinmezliği sihirli biçimde çözmez. `log_index` kayıt kimliğidir; bütün ekonomik eşleşmelerin gerçek exchange zaman sırası olduğu ayrıca varsayılmamalı.

### B — Aynı başlangıçtan risk azaltımı

PRO'nun testini parent/rol bilgisiyle uygula. Piyasadaki ilk güvenilir azaltıcı alıştan hemen önceki pozisyonu sabitle; tek miktarı taşıma ve gözlenen karşı alımla eşleme hesaplarını karşılaştır. Sonraki Bosona işlemlerini iki hesaba da ekleme:

```text
yerel fark = q × (1 − karşı tokenin net nakit fiyatı − eldeki tarafın sonuç ödemesi)
```

Bir alış sıfırı aşıyorsa açık miktara kadar azaltıcı, kalanı yeni ters risk. Eski eşleşmiş lotları yeniden dağıtmadan FIFO ve uygun lot maliyet sınırlarını göster. Karşı alımın sentetik satış fiyatını o anda yürütülebilir net bid'le karşılaştır. Sonuç yalnız değerlendirme etiketi olsun.

İlk azaltıcı dolum daha önce verilmiş bir emrin devamıysa bunu ayrıca işaretle: yerel ödeme etkisi hesaplanabilir, fakat o saniyede yeni risk yönetimi kararı verildiği söylenemez. Bu, PRO ile Ultra'yı birlikte kullanmanın esas faydası.

### C — Kuyrukta ulaşılabilir fiyatın sınanması

Kimlik ve veri kapsamı yeterliyse Fable'ın kuyruk-arkası replay fikri güçlü bir sonraki adım. Beş paylık, küçük ve önceden sabitlenmiş kotasyon kuralı; gerçek tick, iptal/yeniden yerleştirme gecikmesi ve kendi envanteriyle denenmeli. Kuyruk önü iyimser sınır, kuyruk arkası daha ihtiyatlı sınır olarak ayrılabilir.

Fakat aggregate L2 defterden kesin dolum üretmek mümkün olmayabilir. Önümüzdeki miktar, ön/arka iptaller, eksik trade olayları, mint'in iki bacağını çift saymama, kısmi dolum ve iptal kabulüne kadar eski emrin canlılığı hesaba katılmalı. Eksik veri iyimser varsayımla doldurulmasın; mümkün dolum/PnL aralıkları verilsin. Tek-taraf/çift-taraf ve k=0..3 konfigürasyonları yeni bir geniş optimizasyon taramasına dönüşmesin.

Her arka-kuyruk varyantı negatifken ön-kuyruk pozitif çıkarsa, bu **test edilen kurala ve simülasyon varsayımlarına** karşı kanıttır. “Bosona yalnız kuyruk rantıyla kazanıyor; herhangi bir maker bot imkânsız” sonucu değildir. Her saniye çift taraf teklif veren replay, sub-saniye tek taraflı olduğu iddia edilen gizli politikanın birebir kopyası olarak sunulmamalı.

### D — Sonraki bağımsız ekonomi testi için kapılar

Üç rapordaki 14 gün / 4.032 takvim slotu önerisi işe yarar bir ön kayıt çerçevesi. Ultra'nın önerdiği `[22 Eylül 00:00, 6 Ekim 00:00)` aralığı burada **başlatılmış otomasyon değil**. Günleri veya eşikleri sonucu gördükten sonra değiştirmemek gerekir; 14 gün yeterli güç garantisi değildir.

- Kayıt ve payın en az %95 mutabakatı ile olay bağlamının kapsamı ayrı ölçülmeli. Bu mühendislik eşiği, ekonomik başarı değil.
- Pasif çoğunluk ve aynı-parent devamı iddiaları ayrı, gün kümeli ve eşzamanlı belirsizlikle değerlendirilir. Sonuç eksik/sıfır/çözülmemiş ayrımı korunur.
- Ultra'nın çoğunluk iddialarında alt sınırın %50 üstünde olması destek, üst sınırın %50 altında olması ret, arada kalması belirsizlik olarak önceden tanımlanabilir. PRO'nun yerel ekonomik farkında aralık sıfırı kesiyorsa belirsiz, üst sınır bile sıfır veya altındaysa pozitif katkı savı reddedilir. Bunlar farklı iddiaların kapılarıdır.
- PRO'nun ≥10 piyasada, azaltıcı payın ≥%10'unda lot seçimine dayanıklı >1 kapanış ölçüsü **araştırma önceliği eşiği** olarak kullanılabilir; Bosona parametresi değildir. %2–10 veya geniş aralık belirsiz kalır.
- İlk olayın yerel farkı, medyanı, gün etkisi, en iyi üç hariç sonucu; ayrıca açık-pay-saniye, azami nakit ve en kötü ödeme tabanı raporlanır. Davranış ve ekonomik katkı ayrı hüküm alır.
- Bağımsız işlem stratejisi ancak kendi giriş zamanı/miktarı/envanteri ve o anda alınmış verilerle çalışır. Aktörün gelecekteki dolumu, fiyatı veya order zamanı karar girdisi olamaz. İadeler actual/modeled ve hesap kademesiyle ayrı raporlanır.

Fable'ın replay için önerdiği en az bir `k≥1` kolunda **net >0,5¢/pay**, sıfırı dışlayan pencere kümeli aralık ve en iyi on piyasa hariç pozitiflik şartları da kayda değer bir öneri olarak saklanmalı. Bu sayılar keşfedilmiş optimum değil; replay veri belirsizliği çözülmeden geçerli başarı ölçümü sayılmaz. Gün kümeleri, her günü sırayla dışarıda bırakma ve toplam risk bütçesi ayrıca gereklidir.

Eski shadow'ları donmuş karşılaştırma adayları olarak etiketlemek yeterli; sonuçlarını yeni modele ekleyip tek uzun başarılı deney görüntüsü yaratmamalıyız. Bu sentez, onları durdurma veya yeni canlı risk açma talimatı vermiyor.

## 8. Son shadow kontrolü bu sentezi değiştiriyor mu?

21 Eylül **17:46 UTC / 20:46 Türkiye** snapshot'ında üç güncel süreç ve manifest hash'leri uyumlu. Aynı **14:45–17:40 UTC başlangıçlı 35 kapanmış pencerede**, 250 ms kollarının ücretli sanal sonuçları:

| Kol | İşlemli pencere | PnL | En iyi üç pencere çıkarılınca |
|---|---:|---:|---:|
| Seçici pair | 19/35 | +3,71 $ | Ayrı kontrol, ana ekleme karşılaştırması değil |
| Seçici pair+add | 19/35 | **+8,76 $** | **+1,48 $** |
| Her-pencere katılım pair | 35/35 | −3,82 $ | Ayrı kontrol |
| Her-pencere katılım pair+add | 35/35 | **+2,28 $** | **−8,55 $** |

Ana t280 rebound beş sanal alımda **−0,37 $**. Seçici+add kendi daha erken başlangıcından beri 46 pencerede +8,57 $, en iyi üç hariç yalnız +0,06 $. Bu ölçüler fiyat/ücret modeli altında paper PnL; gerçek maker dolumu, rebate veya bağımsız politika doğrulaması değil.

İki inventory günlüğünde 945 zamanlanmış an = 944 karar + bir kayıtlı geç karar var; sırasıyla 120/114 eksik veya eski bağlam. Süreçlerin çalışması veri kapsamının kusursuz olduğu anlamına gelmiyor.

Bosona aynı 35 piyasanın 33'ünde 282 BUY ve 24.581,69 payla, API nakit maliyeti/sonuç ödeme hesabında **−1.671,55 $**; tek 16:30 penceresi **−1.631,82 $**. İşlem boyları çok farklı, dolayısıyla bu dönemdeki ham dolar üstünlüğü bizim daha iyi model olduğumuz anlamına gelmez. İlk taraf uyumu seçicide 7/19, katılımda 17/33; fazla katılım tek başına politika yakınlığı göstermiyor.

[Ayrıntılı durum okuması](../data/analysis/btc5m_status_20260921_1740/OKUMA.md).

## 9. Kaynaklar, tekrar çalıştırma ve sınırlar

- PRO: kullanıcının bu oturumda paylaştığı tam rapor, dört yol ve deney protokolü; eski `b471fab` snapshot kapsamı.
- [Ultra tam rapor](BOSONA_BTC5M_INDEPENDENT_REVIEW_20260921.md), [ana kontrol](../data/analysis/bosona_independent_review_20260921/check.py).
- [Fable tam artifact](https://claude.ai/code/artifact/50cdf486-1488-4e27-96cb-b2e370de10a3); alt notlar: yerel Fable scratchpad `p2/n1_report.md`, `p2/n2_report.md`, `p2/n2/rebate_table.json`, `p2sum/ref_c3_rebate_altexpl.md`. Alt tablonun sınırlamaları özet iddialarının değerlendirmesinde kullanıldı.
- [Bu oturumun doğrulaması](../data/analysis/bosona_review_synthesis_20260921/verification.json), [birebir yeniden üretilen Ultra hesapları](../data/analysis/bosona_review_synthesis_20260921/calculations.json), [küçük ek kontrol](../data/analysis/bosona_review_synthesis_20260921/check.py).

Ek kontrol komutu:

```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/bosona_review_synthesis_20260921/check.py"
```

Maliyetli tarihsel tekrar için mevcut Ultra `check.py` modülü import edilip `OUT` bu sentezin çıktı dizinine yönlendirildi; orijinal hesap dosyasına dokunulmadı. Ham çokluk, 4.331 rol vekili, üç piyasa yolu ve ücret hesapları yeniden çalıştı. Dört PRO yolu ayrıca aynı çıktıdan bağımsız activity toplamıyla denetlendi. Mum sınırı kontrollü yanıtla tekrarlandı; güncel runtime hash'leri snapshot'tan kontrol edildi.

Saklanan defterin **5.577 tamamlama / 1.917 adet 0,98 üstü** sayısı ile Ultra'nın çokluk korunmuş defter için raporladığı **5.585 / 1.922** aynı sürüm değildir; toplamlar karıştırılmamalı. Ham çokluk PnL'si bu oturumda yeniden üretildi; ham defterin bütün davranış etiketleri ve Fable'ın bütün bootstrap/replay alt hesapları yeniden koşulmadı.

Tam 18,65 GB tape çıkarımı, yeni onchain parent decoder, bütün günlük iade ataması, görünmeyen emir/iptaller, haricî hedge ve toplam sermaye hâlâ bu sentezin doğruladığı kapsam dışında. **Araştırma nesnesi konusunda ciddi ilerleme var; çalışır kâr sinyali bulunmuş değil.**
