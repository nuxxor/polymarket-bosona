# Bağımsız BTC5m politika incelemesi — 21 Eylül 2026

**Hüküm: kısmen doğru yolda. Ölçüm ve muhasebe ilerliyor; mevcut cheap-side/rebound
shadow'larının Bosona'nın genel karar mekanizmasına yaklaştığı gösterilmiş değil.**
Bu ayrım konusunda güvenim yüksek. En güçlü açıklamam, envantere göre değişebilen
pasif kotasyonlarla seçici agresif işlemleri birleştiren bir yürütme politikası;
bu açıklamaya güvenim orta. Emir kimlikleri ve yerleştirme/iptal zamanları olmadan
tam politika teşhisi yapılamaz.

İncelenen commit: **`add159d343948e4b46a5491b9bab4c78fceeeb40`**, commit zamanı
21 Eylül 15:02:39 UTC. Başlangıçta çalışma ağacı temizdi. Bu inceleme yalnız plan
kaydı, bu rapor ve ayrı analiz çıktıları ekler; üretim kaynaklarına, servislere,
kurallara, bütçelere, emirlere ve credentials'a müdahale etmez.

Tarihsel kohort: **13 Eylül 00:00 ≤ piyasa başlangıcı < 20 Eylül 22:30 UTC**.
Ham activity sorgu aralığı 12 Eylül 00:00–20 Eylül 22:29:59; 36 kesintisiz dilim,
49.640 bütün-piyasa kaydı, dilim başına 1–5 sayfa. Snapshot sorguları
20 Eylül 23:03:46.189–23:04:14.440 UTC'de alınmış. Son tarihsel özellik dolumu
20 Eylül 22:29:34 UTC. Altı-piyasa ekonomik kontrolünün kesimi **21 Eylül 14:20**;
runtime arşivinin capture zamanı 14:20:25.321. Katılım günlüğünün son kaydı
14:47:10.059, runtime capture 14:47:50 UTC. Bunlar tarihli arşivlerdir;
bu incelemede mevcut Londra servisine bağlanılmadı.

Yerel inventory SHA256 `01018c5239fcfeff8f70a2a0b28aaacdcf1600aa32d535833ced8c82a22528ec`,
katılım manifestiyle eşleşiyor. Seçici inventory_v2 arşivi
`63735c54a76c897dbe5aeb7a676a3b038417f6351aaa9063e645debdd012fa0d`.
Yerel rebound `149485cee51b3172726a838cc3c9092cbdc64c0781489dcc0145f0a6218c022d`.
Tarihsel ana rapor analiz hash'i `0cbcd565c0e6c61ad02825b90e18342f95875a25d67c1262a8c0aa42d05dac2b`,
tarihsel derin politika hash'i `b825c37449e1069c8bcedfa4037d6dd9ee620bdd667da1e4d6b36905fb1a0690`;
bugünkü iki yerel kaynak sırasıyla `c5168e5ad7334149c21de0484d99dec264f2a18f1b6c3be3a04967b4cb15e6ff`
ve `3fd35f1b172cabf1b3fa2e7f06c59b03196f94486b5831e5dfbcd89ea9241c98`.
Farklı sürümlerin ileri sonuçları birleştirilmemeli.

## En değerli yeni ipucu: karar birimi yanlış seçilmiş olabilir

Son 100 saniyedeki 4.331 dolumu, transaction hash üzerinden arşiv exchange
olaylarıyla birleştirdim. Kapsam 690 piyasa, 6.242 geç kaydın %69,4'ü.

| Aktörün BUY kaydına karşı exchange olayı | Kayıt | API `cash_price-price` |
|---|---:|---|
| Karşı token `BUY` | 3.599 | Hepsinde yaklaşık sıfır |
| Aynı token `SELL` | 416 | Hepsinde yaklaşık sıfır |
| Aynı token `BUY` | 316 | Hepsinde pozitif |

Son grupta 316/316 miktar exchange olayıyla aynı. İlk iki grup **4.015/4.331,
%92,7**: pasif/maker gerçekleşmesiyle tutarlı. Karşı-token alımları, tamamlayıcı
tokenların eşleştirilmesi yoluyla aktörün bekleyen alışını doldurabilir. Bu tablo
kesin onchain rol tayini değildir: tx düzeyindeki olay bazen birden fazla
dolumun toplamıdır; `orderHash` ve `OrdersMatched` rolü hâlâ gerekli.

Tüm tarihsel defterde 18.416/19.761 kaydın nakit fiyatı işlem fiyatıyla aynı;
pozitif primli 1.345 kaydın 1.302'si, pay başına `0.07*p*(1-p)` ile 0,000001
toleransında uyuşuyor. Resmî doküman taker ücretini bu formülle tanımlıyor,
maker ücretini sıfır veriyor. Bu nedenle ücret primi yararlı bir rol vekilidir;
tek başına kesin kimlik değildir. [Resmî ücretler](https://docs.polymarket.com/trading/fees).

Son-20 "ekleme" 271 kaydın **157'si önceki aynı yönlü dolumla aynı saniyede**,
210'u en fazla üç saniye sonra. `1789402200` piyasasında t256'daki yedi Up
dolumu **tam 297 pay** ediyor. İlk 49,72 pay ücretli aynı-token BUY; kalan
247,28 pay, karşı-token Down BUY olayları ve sıfır primle eşleşiyor.
Tek emrin önce agresif, kalanının pasif dolması bu izi açıklayabilir;
birden fazla emir de açıklayabilir. Aynı `orderHash` bulunmadan seçilemez.

Dolayısıyla ana soru "neden 271 kez yeniden almayı seçti?" olmamalı.
**Önce kaç emir verdiği, bu emirlerin hangi fiyatlarda beklediği ve karşı taraf
geldiğinde nasıl dolduğu çözülmeli.** Fill düzeyindeki zaman/RSI, çok daha önce
yerleştirilmiş bir emrin karar girdisi olmayabilir. Bu, yalnız gecikme problemi değil.

Yeniden üretim: `data/analysis/bosona_independent_review_20260921/check.py`;
`calculations.json` içinde `execution_roles`, `late20_same_side_predecessor`.
Transaction başına ilk exchange olayını tutan kaynak: `analiz/izleme/bosona_derin.py:215,399`.
Fill düzeyindeki davranış değişkenleri: aynı dosya `:526–545`.

## Doğrulanmış sorunlar ve sonuçları

**1. Tarihsel BTC5m defterinde de çokluk kaybı var.**
`bosona_gec_arastirma.py:86` ayrık zaman dilimlerini dict ile tekilleştiriyor.
Ham dilimlerde yedi piyasada yedi ilave aynı-görünümlü BUY var; aynı sayfanın
bitişik kayıtları, sayfalama sınırındaki çakışma değiller. Altısında MERGE/REDEEM
ödemesi, tekilleştirilmiş alışların mümkün kıldığı miktarı aşıyor; çokluk
korununca uyuşmazlık ortadan kalkıyor. Örneğin `1789295100`: defterde 148
kazanan Up, REDEEM 296; `1789931100`: defterde 249 Down, MERGE 498.
Yedinci kaybeden kopya ödeme hesabıyla bağımsız doğrulanamıyor.

| Ölçü | Saklanan defter | Ham çokluğu koruyan hesap |
|---|---:|---:|
| BUY kayıtları | 19.761 | 19.768 |
| Pay | 832.952,214479 | 833.991,214479 |
| Alış nakit maliyeti | $374.401,582805 | $375.049,792805 |
| Terminal ödeme hakkı | $382.721,021269 | $383.363,021269 |
| API cash-cost PnL | **+$8.319,438464** | **+$8.313,228464** |
| En iyi üç piyasa hariç | +$6.059,701494 | +$6.053,491494 |

Bu kusur toplam kârı açıklamıyor; miktar ve envanter yollarını bozuyor.
Ham çoklukla FIFO çift/açık katkıları +$14.860,777709/−$6.547,549245.
Son-20 ekleme 271/66/+$1.888,805825 aynen kalıyor; son-100 ekleme katkısı
$2.784,242434'ten +$2.737,204952'ye değişiyor.
`activity_key():50` condition/slug içermediği için 44 farklı sıfır-dolar REDEEM
de düşmüş. Toplam doları değiştirmese de arşiv tam değil.

Ham kapsamda SELL/SPLIT ve pencere-öncesi BUY görülmedi. Bu, daha önceki bütün
yaşam-boyu hareketlerin yokluğu kanıtı değildir. Terminal entitlement ile
görünür MERGE+REDEEM arasında $484,340869 var; $482,92'si son piyasanın kesim
sonrasına kalabilecek ödemesi. Geriye kalan $1,420869/25 piyasa kesin açıklanmadı.
MERGE gelirini terminal token ödemesine tekrar eklemek çift sayımdır.
Rebate/sabit maliyetler hariçtir; sonuç wallet cash flow veya sermaye getirisi değildir.

**2. Eklemelerden bağımsız geç girişe geçiş, mekanizma çıkarımı değil.**
Mevcut envanter, eski emirler, rol ve büyüklük değişirken yalnız başarılı dolum
özelliklerini yeni tek atımlık taker kuralına taşımak nedensel karşılaştırma sağlamaz.
Kayıt başına beş pay normalizasyonu da parçalanmaya bağımlı
(`bosona_derin.py:386`). Son-20 sonuç kayıt başına +$185,69, piyasa başına
toplam beş payla +$27,26. Saklanan19.761kayıtlı defterde tüm tarihsel piyasalar
aynı yöntemle toplam beş paya indirildiğinde **−$53,26533**;
gerçek miktarlı +$8.319,44'tan çok farklı.
Bu boy/seçim heterojenliğinin önemini gösterir; optimal sizing veya uygulanabilir
karşı strateji ispatlamaz. Satın alma turnover'ı sermaye ihtiyacı değildir;
eşzamanlı açık risk ve nakdin serbest kalma zamanı ayrıca ölçülmeli.

İlk dolumların 744/1.842'si ≥50¢, 745/1.842'si t30'dan önce. t200 sonrası
kapanış öncesi 116 ilk dolum, 348 reopen kaydı var. Ham çokluk korunmuş
5.585 tamamlamanın 1.806'sı negatif FIFO eşleşme katkılı; 1.922'sinin ortalama
eşleşme maliyeti >98¢. Bunlar lot dağılımına ve fill sırasına bağlı sayılar;
41 sırası belirsiz piyasa çıkarılsa da çok sayıda negatif eşleşme kalıyor.
Erken ucuz giriş, t200 reopen kesimi ve 98¢ tavanı araştırmacının deney sınırları;
Bosona'nın genel kuralları değiller.

**3. Kapsam ekonomik kuralın bir parçası olmuş.**
`policy():665–671` bütün adaylara iki taraflı executable book ve tam TWAP
özelliklerini şart koşuyor. t280'de yalnız 140/2.286 piyasa (%6,12) uygun;
t210/240/270/290 kapsamı 1.222/804/266/58. Farklı zaman PnL'lerini aynı
evrende karşılaştırmıyoruz. Yeni tek taraflı-book sürümü farklı bir örnekleme açılıyor.

Güncel `bosona_rebound_shadow.py:104` de RSI/10 saniye momentum kararına
gerekmediği halde `final_up_prob` istiyor; exact ref/TWAP/60 saniye tarihçe
ek bir filtre oluyor. 13:21 arşivindeki aynı 167 karar, aynı causal clock ve
books ile: mevcut düzeltilmiş bağlam **114**, gerekli girdilerle **123** geçerli.
Ek dokuzun sekizi sinyalsiz, biri Down sinyalli. Önceki 114 seçim değişmiyor.
Bu bir PnL backtest'i değil; kalan veri boşluklarının hepsinin zorunlu sinyal
girdisinde olmadığının kanıtı. Kuralları sessizce değiştirmek yerine bu bağımlılık
belgelenmeli, değiştirilirse yeni sürüm ve yeni ileri evren kullanılmalı.

**4. Seçim sonrası kanıt temiz test değil.**
60 metrik/225 kova ve 50 kural-zaman karşılaştırması denetlenebiliyor.
24.900 satırdan 50 politika toplamı uzlaşıyor; istatistiksel bağımsızlık çıkmıyor.
Aktöre koşullu `mechanism():747–748` rebound etiketi ucuz taraf/50¢ şartını
içermiyor; executable kuralın aynısı değil. Tam koşul, public−5 bağlamı ölçülebilen
173 son-20 eklemenin yalnız 25'ine/5 piyasaya, miktarın %4,4'üne uyuyor.
Bu zaman gerçek emir kararı olmadığından hem eşleşme hem uyumsuzluk ihtiyatla okunmalı.

Adayı tamamen anlamsız da saymıyorum. Aynı 140 t280 uygun pencerede, aynı
250 ms ask derinliği/ücretle küçük ablasyon:

| Politika | İşlem | PnL | En iyi üç hariç |
|---|---:|---:|---:|
| Yalnız cheap ask<50¢ | 140 | +$2,61544 | −$11,32038 |
| RSI/momentum rebound | 23 | +$19,93476 | +$7,47245 |

Özgün 23 maliyet aynen yeniden üretildi. Gate eski örnekte faydalı; bu da
seçimden sonra ölçüldüğü için kör test veya Bosona mekanizması kanıtı değil.

**5. Daha küçük, doğrulanmış mum sınırı kusuru.**
`bosona_rebound_shadow.py:30–49` mumun kapanmışlığını HTTP request başlangıcına
değil receipt zamanına göre süzüyor. 59,500'de istenen kısmi mum 62,200'de
gelirse 59,999 kapanışlı snapshot kapalı kabul edilebilir ve yenilenmeyebilir.
İzole reproducer bunu gösterdi. 146 arşiv mum yanıtında gerçekleşmiş örnek yok;
geçmiş PnL'yi etkilediği doğrulanmadı. Ölçüm birimi probleminden daha düşük öncelikli.

Altı-piyasa `check.py` izole kopyada PASS ve tam JSON eşitliği verdi:
delayed pair −$0,39053; pair+add +$0,23117; Bosona 134 BUY/−$158,631739.
162 planlı karar ile 144 geçerli bağlam farklı sayılardır. Küçük sanal kâr
veya 2/3 ilk-yön uyumu davranış yakınsaması kanıtı değil.

## Üç piyasa yolu

Aşağıdaki t değerleri **public dolum yaşıdır**, emir gönderme zamanı değil.
UP/DOWN envanteri o ana kadarki brüt satın alınan paylardır; varsa MERGE
iki taraftan eşit pay düşürür, net yönü değiştirmez. Risk tabanı terminal
`min(Up,Down)-alış nakdi`; muhasebesel pairing, fiziksel MERGE emri demek değildir.
İki ana örnek sonuç uçlarından açıklayıcı olarak seçildi; frekans/edge tahmini değiller.

**Kazanç: `btc-updown-5m-1789676700`, 17 Eylül 20:25–20:30 UTC, sonuç Down.**

| Public t | Dolumlar | Önce net Down → sonra net Down | Alış maliyeti |
|---|---|---:|---:|
| 123–124 | 120,178572 Down @44¢ | 0 →120,178572 | $52,878572 |
| 204–208 | 261,402650 Down @10¢ | 120,178572→381,581222 | $26,140265 |
| 229–231 | 123,138462 Down @35¢ | 381,581222→504,719684 | $43,098462 |
| 246–249 | 419,738952 Down @26–29¢ | 504,719684→924,458636 | $118,725857 |
| 279–288 | 763,190941 Up @5–14¢ | 924,458636→161,267695 | $81,774703 |

Son toplam **763,190941 Up / 924,458636 Down**, nakit $322,617859,
terminal ödeme $924,458636, **+$601,840777**. FIFO +$484,342274 çift,
+$117,498503 açık katkı; buna rağmen en son alınan Up miktarının gerçekleşmiş
marjinal katkısı **−$81,774703**. Bu Up alımları en kötü sonucu
−$240,843156'dan **+$440,573082**'ye taşıdı. Demek ki doğru/yanlış yön etiketi,
işlemin risk yönetimi işlevini anlatmıyor.

Public208 için önceden bilinen context203: ref **76.653,32110**, spot
**76.672,63900**, TWAP **76.657,94801**, Down bid/ask **12/13¢**;
Down yönlü RSI28,17 ama 10s momentum negatif. Actor Down10¢ doluyor.
Public246 için context241: spot76.656,06066 hâlâ ref üstünde, TWAP76.667,34251;
Down38/39¢, actor29¢. Bu farklar birkaç saniye içindeki piyasa hareketini de
içerir; kesin anlık maker indirimi diye okunamaz. Public279/context274'te
spot ref altına geçmişken TWAP hâlâ üstündedir: spot ve settlement ölçüsü ayrışır.
Ucuz Down eklemeleri, sonra kaybeden Up ile risk azaltma görülür;
gizli tahmin veya niyet kanıtlanmaz.

**Kayıp ve tercih ettiğim açıklamaya karşıörnek: `1789402200`,
14 Eylül 16:10–16:15 UTC, sonuç Down.**

| Public t | Up dolumları | Önce→sonra Up | Bu grubun nihai katkısı |
|---|---|---:|---:|
| 93 | 297 @73¢ | 0→297 | −$216,81 |
| 198 | 10 @77¢ | 297→307 | −$7,70 |
| 217 | 53,485715 @65¢ | 307→360,485715 | −$34,765715 |
| 256 | 7 kayıt, toplam297 @yaklaşık75¢ | 360,485715→657,485715 | −$223,260490 |
| 268–271 | 70,217392 @71–77¢ | 657,485715→727,703107 | −$53,467392 |
| 273 | 87 @33¢ | 727,703107→814,703107 | −$28,71 |

Down alımı yok; ödeme sıfır; **−$564,713597**. Ucuz giriş/tek kârlı çift modeli
bu yolu açıklamaz. Pasif dolmak da otomatik avantaj değildir: son 87 pay33¢,
Down sonucu nedeniyle kaybeder.

Public268/context263'te ref **78.421,76592**, spot **78.426,65799**,
TWAP **78.436,53704**, Up55/56¢, RSI28,50 ve pozitif kısa momentum.
Actor71¢ dolumu birkaç saniye sonra. Public273/context268'de spot
**78.421,83168**, TWAP **78.434,87598**, Up76/77¢; actor33¢ gerçekleşmesi
exchange270,405'te. Kısa sürede sert yeniden fiyatlama var; eski ucuz bekleyen
emrin olumsuz haberden sonra dolması da, yeni aktif karar da mümkündür.
Buradaki modelin yüksek Up olasılığı kazanan sonucu garantilemez.

İki ana piyasadaki 18 farklı public−5 bağlamının **18 bid/ask ve 18 spot değeri**
iki ham saatlik tape'den doğrulandı. Tek tape'deki TWAP17/18 eşleşti;
bir fark birleşik doğrudan-feed kaynağıyla ayrıca çözülmedi. Bütün 18,65GB
ham geçmiş yeniden işlenmedi. Geçmiş RSI mumlarının yerel publication receipt
zamanı ayrıca kanıtlanmış değil.

**98¢ varsayımına doğrudan karşıörnek:** `1789582500`, 16 Eylül18:15.
t6–7'de 254,771819 Down, maliyet $136,137019. t39'da 254,77 Up,
ücretli maliyet $152,110930: net yön neredeyse sıfır, kilitlenen taban
**−$33,477949**. Daha sonra yeniden Down riskini büyütüp Up85/97¢
tamamlamaları yapıyor; nihai Up sonucu rağmen toplam **−$442,268793**.
Bu, zarar kilitleyerek risk azaltmayı yasaklayan shadow tavanının aktörün
genel davranış kuralı olmadığını gösterir.

## Açıklayıcılık ve sınanabilirliğe göre mekanizmalar

**1. Envanterle değişen kotasyonlar + seçici agresif alım.**
Destek: %92,7 pasif-benzeri eşleşme, aynı fiyatlı parçalar, ücret/rol ayrımı.
Karşı kanıt: ücretli büyük alımların varlığı; fiyat avantajının olumsuz
seçilmeye yenildiği kayıp örneği. Gerekli causal girdiler: o anda bilinen
bid/ask/derinlik, fair-value vekili, kalan süre, kendi açık miktarı,
kendi bekleyen emirleri ve risk kapasitesi. Öngörü: çok sayıda görünen
ekleme az sayıda parent order'a iner; pasif gerçekleşmeler karşı-token
BUY veya aynı-token SELL akışıyla gelir; bazı emirler kısmen agresif sonra
pasif dolabilir. Ayırıcı: orderHash ve match rolünü çöz, emir başına
ilk/son fill ve fiyatı göster. Çürütme: yeni kapsanan örnekte filllerin çoğu
farklı agresif emirlerse ve rol/fiyat farkı kalmıyorsa bu baskın açıklama reddedilir.
Bu hipotez saf grid veya her iki tarafa kör quote demek değildir.

**2. Yön tahmininden ayrı, bazen zararına çalışan envanter yönetimi.**
Destek: kazanç örneğinin kaybeden Up alımları risk tabanını iyileştiriyor;
zarar kilitleyen eşleşmeler. Karşı kanıt: yönü hiç kapatmayan büyük
kazanç/kayıplar; sabit risk nötrleme de genel model değil. Girdiler:
kendi net payı, lot maliyetleri, mevcut karşı ask/bid, kalan süre ve güncel
settlement olasılığı. Öngörü: karşı-alım olasılığı, piyasa durumuna ek olarak
açık yön/büyüklükle değişir; bazı karşı alımlar mevcut zararı kilitler;
yeniden açılış mümkündür. Ayırıcı: aynı piyasa koşullarında farklı envanterli
anları karşılaştır; sonra aynı ilk girişle yönetim ablasyonu. Çürütme:
parent-order parçaları temizlendikten sonra envanter, fiyat/zamanın ötesinde
karşı alımı veya miktarı açıklamıyorsa bağımsız yönetim açıklaması geriler.
FIFO label tek başına bu testi geçiremez.

**3. Settlement/TWAP'a göre göreli fiyat değeri ve buna bağlı büyüklük.**
Destek: hem ucuz hem88–91¢ alımlar; spot/TWAP ayrışmaları; gerçek miktar ile
eş-piyasa ölçeklemenin çok farklı sonucu. Karşı kanıt: mevcut fair-edge
filtrelerinin ex-top3 başarısızlığı, pahalı yanlış eklemeler ve aşırı emin
olasılık modeli. t280 sonraki dönemde statik model normalized RMSE2,76;
varsayılan1 değil. Girdiler: piyasaya özgü resmî ref, alınmış Chainlink TWAP60,
spot yolu/volatilite, kalan ortalama penceresi, executable fiyat+ücret,
kendi risk kapasitesi. Öngörü: düşük fiyat veya favori olmak değil,
kalibre edilmiş ödeme olasılığı eksi marjinal maliyet yönü/boyu açıklar.
Ayırıcı: özellikle spot ve TWAP'ın ters yön söylediği anlarda, kalibre
TWAP modelini aynı koşullu market-mid/spot tabanıyla karşılaştır.
Çürütme: yeni veride TWAP farkı fiyat/rol/envanter sonrası ek açıklama
sağlamaz veya avantaj sadece gerçekleşmiş dolum fiyatında görünürse,
bu kamu girdileriyle bağımsız directional-alpha iddiası reddedilir.

Resmî piyasa kuralları BTC/USD60s TWAP akışını gösteriyor. Buna rağmen
Chainlink'in tam örnekleme sınırları/ağırlıkları açıklanmıyor; spotlardan
üretilen rolling average tam settlement feed yerine geçmez.
[İncelenen piyasa](https://polymarket.com/event/btc-updown-5m-1789998600),
[resmî TWAP dokümanı](https://docs.polymarket.com/market-data/chainlink-twap).

## Tek sonraki deney: parent-order ve yürütme rolünü ayrıştır

Yeni parametre taraması veya yeni shadow yerine **tek bir public-data teşhis
protokolü** öneriyorum. Bu rapor protokolü çalıştırmaz, servis başlatmaz.
Önce iki örnek piyasada decoder/muhasebe kontrolü; sonra
**22 Eylül00:00–6 Ekim00:00 UTC**, bütün **4.032 BTC5m pencere** önceden atanır.
Piyasası bulunmayan, veri kaybı olan, aktör filli olmayan ve unresolved
pencereler ayrı kalır. Aktörün filli olmayan pencereye "emir vermedi" denmez.

Minimum ek veri: halka açık transaction receipts ve kullanılan exchange
sürümünün ABI'si; `OrderFilled`, `OrdersMatched`, block/tx/log index,
actor orderHash, token/condition, gerçek rol/miktar/fee. Eşleşen miktar ve
cash'i event loglarından doğrula; maker/taker aggregate loglarını iki kez
sayma. Solidity event'indeki `maker` alanını tek başına pasif rol sayma:
emrin imzalayanı ile match'teki likidite rolünü ayır.
Mevcut book/spot/TWAP kayıtları exchange/observed time, local receipt ve
karar cutoff'u birlikte korumalı; receipt ve first-fill zamanı placement
zamanını vermez. İptal/hiç dolmayan emir verisi varsa faydalı, yoksa açık sınır.
[V2 resmî event arayüzü](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/interfaces/ITrading.sol).

```text
for market in fixed_4032_window_universe:
    activity = all_public_events_preserving_multiplicity(market_lifetime)
    logs = decode_versioned_exchange_logs(activity.transaction_hashes)
    reconcile_wallet_token_quantity_cash_and_fee(activity, logs)
    fills = canonical_unique_events(chain, exchange, tx_hash, log_index)
    parents = group(fills, actor_order_hash, token, side)
    reconcile_initial_inventory_and_merge_split_redeem_transfer_events()
    reconstruct_inventory_in_exchange_time_order(fills, all_inventory_events)
    label_distinct_parent_changes_and_partial_fills_separately(parents)
    attach_received_before_cutoff_books_spot_twap(fills)

    # Actor-conditioned price diagnostics, NOT a deployable policy.
    # Give each parent a total weight of 5 shares, distributed over its fills.
    actor_edge = sum(fill_weight * (payout - actor_cash_per_share))
    ask_edge   = sum(fill_weight * (payout - available_ask_plus_fee))
    execution_component = actor_edge - ask_edge
    report_role_parent_inventory_price_markouts_and_coverage()
```

`tx/log_index` tekil olay kimliğidir, karar sırası değildir. Zincir settlement
sırası exchange gerçekleşme sırasından farklı olabilir. Envanterde exchange
zamanı önceliklidir; kesin eşleşmeyen/eşzamanlı olaylarda mümkün sıraların
etiket ve risk sınırları raporlanır. Yerel/exchange saat farkı ve belirsizliği
kaydedilir; saat hatası250ms ayrımını aşarsa o quote teşhisi geçersizdir.

Ask yerine koyma, her fillin exchange zamanından250ms önce yerel olarak
alınmış, en fazla500ms yaşında, beş pay derinlikli book ile yapılır;
yetersiz quote `null`. Bu belirlenmiş proxy, actor karar/fill garantisi değildir.
Tutarları aynı kapsamdaki fiyat çiftlerinde kıyasla. Dolumdan sonraki1s/5s
mid değişimleri sonuç değişkenidir, karar girdisi değildir. Parent eş-pay
ölçeği arbitrary parçalanma etkisini azaltır; boy becerisini veya kendi
sermayeli stratejiyi kanıtlamaz.

Birincil iki betimleyici hedef: (i) pasif gerçekleşen **pay miktarı / toplam
pay miktarı**; (ii) son-20 "add" **kayıtlarının** ne kadarının daha önce
dolmaya başlamış aynı parent order'ın devamı olduğu. İlki için kayıt ve
parent oranları, ikincisi için miktar ağırlığı duyarlılık olarak verilir.
Fill-level mevcut etiketler baseline, parent-level etiketler
ablasyon. İkinci hedef özellikle "yeniden karar verme" varsayımını sınar;
distinct order yine de placement zamanını vermez.

Ön kayıtlı karar:

- İlgili hem kayıt sayısının hem pay hacminin en az%95'i role/orderHash ve cash bakımından uzlaşmadan
  mekanizma hükmü yok; eksiklerin fiyat/süre/PnL dağılımı ayrıca gösterilir.
  Book-price teşhisinde payda ayrıca raporlanır; missing0 yapılmaz.
- İki birincil oran için gün kümeli, iki-gün blok duyarlılıklı eşzamanlı
  aralıklar kullanılır (her hedef için%97,5 aralık). "Çoğunluk" iddiası
  için alt sınır>%50 ise devam; üst sınır<%50 ise o iddia reddedilir;
  arada kalırsa belirsiz. 14 gün/işlem adedi otomatik güç sayılmaz.
- Ödeme/fiyat ayrışması aynı kapsam, günlük ve piyasa kümeleri, en iyi
  üç piyasa hariç, her-günü-sırayla-dışarıda sonuçlarla verilir. Teşhis
  sonrası eşik değiştirilmez; başarı çıkana kadar örneklem uzatılmaz.
  Aralık genişse bir sonraki örneklem büyüklüğü ekonomik olarak önemli
  önceden seçilmiş fark ve gözlenen **günler arası** varyansla planlanır.
- Pasif çoğunluk doğrulanır, parent parçalanması baskın çıkarsa tekrarlanan
  RSI-add anlatısı durdurulur; araştırma quote fiyatı/boyu ve adverse-selection
  kontrolüne taşınır. Yeni emirler baskınsa envanterle koşullu karar testine
  devam edilir. Sırf PnL pozitif diye bir mekanizma kabul edilmez.

**Ekonomik değer kapısı ayrı:** Bu deney aktöre koşullu; `ask_edge` bile
işlem zamanlarını Bosona'dan aldığı için deployable backtest değildir.
Mevcut araştırmadan bağımsız uygulanabilir ekonomik avantaj sonucu çıkmıyor.
Yönetim etkisi distinct-parent düzeyinde kalırsa, takipte en küçük uygun
politika testi: bütün kollara aynı t30 giriş denemesi, aynı5 pay/aynı fiyat,
kendi envanteri; hold kontrolüne karşı tek sabit yönetim kuralı. İlk giriş
kalitesi böyle sabitlenir. Özgür girişli deneme ancak bu fark yeni veride
ücret sonrası anlamlıysa yapılır; actor gelecekteki fill/qty kullanılmaz.

O politika testinin ön kayıtlı ekonomik ölçüsü ücretli dolar/**atanmış**
pencere ve eşlenmiş fark; başarısız veri/uygulama, unresolved ve gözlenen
zero ayrı. Ekonomik olarak asgari kabul edilebilir fark operasyon maliyetiyle
önceden belirlenmeli; kümeli alt sınır bu farkı geçmeli, ex-top3 pozitif
kalmalı. Peak acquisition cash, unmatched-share-seconds, worst payoff ve
drawdown raporlanmalı. Aynı pencere limiti daha yüksek katılımda aynı toplam
risk değildir. Davranış skoru ise ilk-fill zaman dağılımı, distinct aksiyon
türü, fiyat/mid farkı, net-envanter yolu ve parent boyuyla ölçülür;
side accuracy ve fill adedi tek başına kullanılmaz.

Katılım deneyi **hem yararlı bir giriş-seçiciliği kontrolü hem gerekçesi
çözülmemiş yön riski**. Rebound ile karşılaştırması giriş evreni, zaman,
maliyet ve sonraki yönetim yolunu birlikte değiştirir; saf yönetim ablasyonu
değildir. Şimdiki donmuş sonuçları sürüm bazında koruyun. RSI adayını dar
bağımsız benchmark olarak tutun; Bosona'yı çözdüğümüzün kanıtı diye yükseltmeyin.
Yeni shadow çoğaltmayı ve dolum adedini davranış yakınlığı saymayı bırakın.

## Kontroller, yeniden üretim ve sınırlar

Ana offline kontrol, ağ veya anahtar gerektirmez:

```bash
python -B /home/taygun/Masaüstü/polymarket-bosona/data/analysis/bosona_independent_review_20260921/check.py
```

`calculations.json` giriş hash'lerini, üç tam yolu, yeni rol tablosunu,
çokluk ve ücret vekili hesaplarını taşır. Ana kontrol ve hedefli Ruff geçti.
Destek paketindeki `accounting/audit.py` stdlib/Decimal ile FIFO'yu da
bağımsız kurar; ilk argüman depo yolu. `supporting_checks.zip` içindeki
diğer betikler bu makinenin mutlak yollarını kullanır; başka makinede yol
uyarlaması gerekir. `raw_check.py` iki haricî ham tape dosyasını gerektirir;
paket ham tape'i içermez. `supporting_manifest.json` paket dosyalarının hash'leri.

Çalıştırıldı: izole altı-piyasa `check.py`; beş gerçek-scheduler/sahte-girdi
senaryolu `check_inventory_shadow.py`; eski mum hatasını yakalayan mutation;
`bosona_derin.py check`; 8 katılım fillinin yeniden execution hesabı;
çokluk/Decimal/FIFO ve 50 politika toplamı; iki ham saat/18 bağlam;
aynı140pencerede tek cheap-only ablasyonu; ilgili kaynaklarda Ruff/syntax.

Çalıştırılmadı: Londra'ya bağımlı `runtime_check.py`, mevcut servis sağlık
kontrolü, tam18,65GB yeniden çıkarım, gerçek emir/kuyruk/latency deneyi.
Yedi taze trade-API isteği ve public Polygon RPC receipt isteği403;
Polygonscan receipt sayfası da erişilemedi. Dolayısıyla onchain rol/parent
kimliği çözüldü demiyorum. Emir yerleştirme/iptal, gerçekleşmeyen teklif,
kuyruk sırası, hedge/diğer cüzdan, gerçek toplam sermaye ve rebate ataması
henüz tanımlanamıyor. Aynı observable dolum yolunu farklı hidden politikalar
üretebilir. Kamu verisinin izin verdiği en küçük faydalı hedef, bu belirsizliği
daraltan **emir düzeyinde yürütme ve envanter modeli**dir.
