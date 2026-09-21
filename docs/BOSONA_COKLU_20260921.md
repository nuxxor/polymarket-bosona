# Bosona: BTC / ETH / SOL ve süreler arası karşılaştırma

**Gözlenen davranış tek sabit fiyat/zaman/envanter ayarıyla özetlenmiyor.**
BTC'de iki tarafı kurmak yaygın; ETH/SOL kısa pencerelerde daha sık tek yönlü
kalıyor. Aynı varlığın saatlik davranışı da kısa penceresinden farklı olabiliyor.
Ayrı botlar çalıştığı kanıtlanmış değil: aynı yazılım piyasa koşullarına göre
farklı kararlar da üretebilir. Shadow kuralları BTC5m için sınadığımız
hipotezlerdir; Bosona'nın bütün stratejisinin bulunmuş kodu değildir.

## Kapsam

Pencere başlangıcı 13 Eylül 00:00 UTC'den itibaren, sonu 21 Eylül 00:30 UTC'ye
kadar olan **4.062 işlemli piyasa / 30.111 BUY kaydı / dokuz grup** incelendi.
Başlangıç öncesi alımlar için aktivite 10 Eylül'den itibaren alındı. Önceki
tam aktivite dilimleri kullanıldı; BTC'ye filtrelenmiş özetler kullanılmadı.
Toplam kaynak 63.821 aktivite kaydı; başka varlıklar, 4 saatlik ve günlük
sözleşmeler dokuz grubun sonucuna katılmadı.

İncelenen bütün piyasalarda token/yön/condition, süre ve resmî sonuç doğrulandı;
kapsam içi dışlanan piyasa sıfır. Sayfalama tamlığı kontrol edildi. İptal veya
yerleştirme kararları kamu dolumlarından türetilmedi. Hiç dolumu bulunmayan
piyasaların niçin seçilmediği burada modellenmedi.

PnL, kazanmış miktarın sonuç ödemesi eksi API usdcSize alış maliyetidir.
Rebate ve sabit giderler hariçtir; MERGE/REDEEM ikinci kez kâr yazılmaz.
FIFO maliyet dağılımı gizli stratejinin ispatı değildir. Aynı saniyedeki
zıt yönlü kayıtların sırası belirsiz olabilir; bunları dışlayan sonuçlar da
saklandı. PnL, farklı hacimler arasında strateji üstünlüğü kanıtı sayılmaz.

## Piyasa bazında fark

İlk alış fiyatı/zamanı piyasa başına ilk saniyedeki alımlar birlikte hesaplanarak
piyasalar arası medyan verildi. İki taraf oranı, hem Up hem Down alınmış
olmasıdır; sonunda dengeli kalmak veya kârlı çift kurmak değildir.

| Piyasa | İşlemli pencere | İlk alış (sn) | İlk fiyat | İki taraf alınmış | İşlem PnL |
|---|---:|---:|---:|---:|---:|
| BTC 5dk | 1.857 | 44 | 44¢ | %64,6 | +8.919,20 $ |
| ETH 5dk | 582 | 123 | 49¢ | %17,4 | +1.422,25 $ |
| SOL 5dk | 376 | 158,5 | 75¢ | %8,2 | +1.242,13 $ |
| BTC 15dk | 598 | 151 | 48,9¢ | %71,2 | +4.563,55 $ |
| ETH 15dk | 126 | 191 | 53,5¢ | %10,3 | +118,30 $ |
| SOL 15dk | 140 | 204 | 80¢ | %39,3 | +148,70 $ |
| BTC 1saat | 181 | 151 | 47¢ | %71,3 | +2.921,84 $ |
| ETH 1saat | 127 | 651 | 58¢ | %74,0 | −250,54 $ |
| SOL 1saat | 75 | 702 | 68¢ | %37,3 | +205,99 $ |

Yüksek ödenmiş fiyat tek başına o anda defterin favorisinin alındığını kanıtlamaz.
Eşit beş pay/pencere, günler, en iyi üç hariç ve son 24 saat sonuçları
report.json içinde ayrı duruyor. Örneğin BTC15m'nin son 24 saatlik 34
penceresi −776,36 $; bütün dönemin pozitifliği her kesitte kazandığı anlamına gelmez.

Gün, ilk fiyat bandı ve ilk alışın göreli zamanı eşleştirildiğinde de fark kaldı:
- BTC–ETH: 115 ortak hücre, 1.753 BTC / 567 ETH penceresi; aynı ağırlıkla
  iki taraflılık **%58,0 / %18,3**.
- BTC–SOL: 97 ortak hücre, 1.475 BTC / 345 SOL penceresi; **%56,4 / %10,1**.

Fiyat sınırları 0,30/0,50/0,70; göreli zaman %10/⅓/⅔. Her hücreye küçük
grubun sayısı ağırlık verildi. Bu betimleyici kontrol likiditeyi, gerçekleşmeyen
emirleri veya özel envanter hedefini eşitlemez; kesin ayrı algoritma kanıtı değildir.

## Shadow hipotezi ne kadar genel?

BTC5m son 20 saniyede açık yöne ekleme önceki hesapla aynen eşleşti:
**271 kayıt, +1.888,81 $**. Aynı tanım ETH5m'de 66 kayıtta **+3,03 $**,
SOL5m'de 13 kayıtta **+24,66 $**. Miktarlar farklı; eşit bütçe deneyi değildir.
Kazancın aynı alt davranışta yoğunlaştığını varsaymak için yeterli dayanak yok.

BTC15m son üçte birde açık yöne ekleme: 1.164 kayıt **+3.364,40 $**.
BTC saatlikte aynı tanım: 214 kayıt **−44,95 $**. Saatliğin toplamı pozitifken
bu katkının negatif olması kazanç kaynağını süreler arasında otomatik taşımamayı gerektiriyor.

Her varlığın Binance kapalı 1dk mumlarından basit RSI14 ve son dakika hareketi
çıkarıldı. Kamu işlem zamanından 5sn ve 10sn önce bakıldı; kapanış+2sn korundu.
Ödenmiş fiyat<0,50 ve kendi yönünde RSI<40 ile örtüşen pay oranı BTC5m **%17,8**,
ETH5m **%7,3**, SOL5m **%3,2**. Bu kısmi koşul karşılaştırmasıdır: gerçek emir
karar zamanı, iki taraflı karar defteri ve son 10sn Chainlink dönüşü kanıtlanmaz.
Dakikalık dönüş 10 saniyelik sinyal yerine geçirilmedi. Tarihsel kapanış+2sn,
gerçek bağlantı receipt kanıtı değil, açıkça belirtilmiş erişim varsayımıdır.

Modelleme ayrımı varlık **ve** süredir. BTC15m geç eklemeleri, BTC5m rebound
ve SOL5m daha yüksek fiyatlı/çoğunlukla tek yönlü alımlar ayrı sınanmalıdır.
Bu tur bunlar için yeni bir canlı strateji veya üçüncü strateji shadow'u açılmadı.

## Saatliklerin sonuç kuralı farklı

İncelenen 5/15dk sözleşmeler ilgili varlığın **Chainlink TWAP60** akışıyla;
saatlikler **Binance 1H mumunun açılış/kapanışıyla** sonuçlanıyor. Altı
saatlik örneğin sonucu bağımsız Binance mumundan da aynı çıktı.
[Chainlink TWAP açıklaması](https://docs.polymarket.com/market-data/chainlink-twap),
[ETH saatlik örnek](https://polymarket.com/event/ethereum-up-or-down-september-20-2026-8pm-et),
[ETH 15dk örnek](https://polymarket.com/event/eth-updown-15m-1789948800).

Ham Gamma cevapları markets/ altında saklandı. Başlangıç için oluşturulma
tarihi değil eventStartTime kullanıldı. Bir saatliğe aynı TWAP kapanış
hesabını taşımak bu yüzden aynı problemi çözmez.

## Gece geçişi sabit mi?

Türkiye saatiyle 00:00–06:00 diliminde, incelenen BTC/ETH/SOL gruplarının
alış dolarları içinde BTC5m payı **19 Eylül gecesi %65,7**, **20 Eylül gecesi
%7,1**; 20 Eylül gecesi BTC15m payı **%72,5**. Diğer tam gecelerde BTC5m
yaklaşık %51–63. Büyük geçiş mevcut; her gece aynı saatte BTC5m'yi bırakma
davranışı bu kesitte yok. Likidite, volatilite veya ödülün geçişe neden olduğu
burada kanıtlanmış değil. 13 ve 21 Eylül gece dilimleri kısmi; tam gecelerle
aynı kabul edilmedi. Ayrıntı: context.json / night_cash.

## Gecikme gözlemcisi Londra'da çalışıyor

İki dondurulmuş shadow'un kaynak hash'leri ve süreçleri korundu.
bosona-latency yalnız **rebound shadow'un yazdığı kararları** izliyor;
rebound ve aynı karardaki favori kontrolü için beklemesiz yeni defter istiyor.
Eski üç kurallı shadow'un kendi kararlarına müdahale etmiyor.

Günlük 5ms aralıkla okunuyor; bildirim 100ms'den geç gelirse veri boşluğu.
Süre karar kaydı + gözlemci gecikmesi + HTTP'dir; gerçek emir kabul/dolum
gecikmesi değildir. 250ms'lik orijinal uygulama ile aynı taraf, aynı beş pay
ve aynı ücret hesabı eşleştirilir. Eşleşmeyen defterler ayrıca sayılır.

İlk eşleşme 21 Eylül **01:04 UTC**, t=240: bildirim **1ms**, yeni defter
**48ms**, beklemeli defter **280ms**. Rebound sinyali yoktu. Favori kontrolünde
erken fiyatın beş pay maliyeti **0,04661 $** daha düşüktü. Bu tek örnek
rebound kazancı veya hızın kalıcı faydası değildir.

Londra: /home/ubuntu/polymarket-bosona-rebound/data/latency/.
quotes.jsonl ham gözlemleri, comparison.json maliyet farklarını zaman dilimine
göre ayrı tutar. Bitiş rebound atamalarının sonundan 30sn sonra.
Observer hash: c2d1071f5037db05656a070f32a750b2cfc3abcfffa00bbdb6fa81d56781e9b8.
Yeni bütçe veya gerçek emir yok.

## Doğrulama

Dokuz grubun en iyi/en kötü örnekleri olarak 18 piyasa tekrar /trades
API'sinden kontrol edildi: işlem kimlikleri, miktarlar ve brüt PnL aynı.
Altı saatlik piyasanın Binance sonucu eşleşti. Grup/pencere/işlem toplamları,
geçmiş mum zamanları, FIFO, maliyet farkı, sıfır sinyal ve eksik eşleşme
kontrolleri, hedefli Ruff ve derleme geçti.

Kod: analiz/izleme/bosona_coklu.py:
check → fetch → candles → analyze → context → matched → validate.
Gecikme: analiz/izleme/bosona_latency.py check.
Kanıtlar ve hash'ler: data/analysis/bosona_coklu_20260921/.
[Kamu activity alanlarının resmî tanımı](https://docs.polymarket.com/api-reference/core/get-user-activity).

