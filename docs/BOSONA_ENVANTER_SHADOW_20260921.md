# Envanter deneyi — 21 Eylül 2026

Bosona'nın gizli karar kuralını bulmuş değiliz. Yeni deney, önceki tek alımlı
shadow'da olmayan **pozisyonu taşıma, tamamlama ve ekleme** kararlarını sınar.
Emir istemcisi, cüzdan veya API anahtarı kullanmaz; bütün işlemler sanaldır.

## Araştırmanın daralttığı soru

13–20 Eylül kayıtlarında ilk alım medyanı 43 saniye/44¢; son karşılaştırma
döneminde 90 saniye/42¢. Bu değişim sabit “90. saniyede al” kuralı çıkarmayı
desteklemiyor. Yeni deney farklı anlarda fırsat arıyor; miktarı tahmin edilmiş
bir Bosona oranına göre büyütmüyor.

Son dönemin 159 karşı taraf alım kaydından 93'ü FIFO eşleşmesinde pozitif
katkı veriyor. Hepsini kâr kilitleme işlemi sayamayız. Tamamlama ve yeniden
riske girme aynı dolumda da bulunabiliyor. Bu kayıt sayıları bağımsız emir
sayısı değil; aynı saniyedeki dolumların sırası da kesin emir sırası değil.

Basit TWAP olasılığına göre en az 3¢ avantaj görünen eski ek alımlar da
kontrol edildi: 273 pencerede +$795,59; en iyi üç pencere hariç −$462,12.
Üstelik bunlar aktörün dolumlarına koşullu hesaplar. Bu tahmini yeni güçlü
yön modeli diye kullanmadık. Mevcut ucuz-taraf toparlanma koşulunu sabit
tutup envanter yönetiminin katkısını ölçüyoruz; giriş kalitesi hâlâ açık soru.

Yeni deney Bosona'nın 88–91¢'lik geç eklemelerini açıklamaz. Ucuz giriş
koşulunu kaldırarak sırf benzer işlem sayısına ulaşmayı başarı saymıyoruz.
Bu sınır ileri sonuç raporunda korunacak.

## Sabitlenen deney

Londra: `/home/ubuntu/polymarket-bosona-inventory-v1/`.
Gerçek süreç başlangıcı **21 Eylül 12:45:32 UTC / 15:45:32 Türkiye**.
İlk atama **12:50 UTC / 15:50 Türkiye**; atamalar 24 Eylül aynı saatte biter.
Toplam 72 saat, ardından en fazla 25 dakika sonuç takibi.

Her BTC5m penceresinde t=30,40,…,290: aynı anda iki politika değerlendirilir.

| Karar | `pair` — kontrol | `pair_add` — aday |
|---|---|---|
| İlk giriş / dengelendikten sonra yeni giriş | t≤200; ucuz taraf ask<50¢, o yönde RSI14<40 ve 10 sn momentum>0 | Aynı |
| Karşı tarafı tamamlama | Açık FIFO maliyeti + ücretli yeni alış ≤98¢/çift | Aynı |
| Aynı açık yöne ek alım | Yok | Aynı toparlanma koşulu yeniden geçerliyse; önceki alımdan ≥20 sn sonra |
| Klibi | En fazla 5 pay; tamamlama açık miktarla sınırlı | Aynı |
| Pencere risk limitleri | En fazla 10 açık pay, $15 toplam alış, en kötü sonuç ≥−$5 | Aynı |

Risk limitleri ve zamanlar optimum olarak bulunmadı; önceden sabitlenen
deney sınırları. Gerçek para bütçesi veya LIVE zarar kesicisi değişmedi.
Tamamlanan çift otomatik yeni alım üretmez: yeni giriş koşulu yeniden
geçerli olmalı. Tamamlama, RSI değişti veya BTC bağlamı eksildi diye
engellenmez; alınacak tarafta taze, yeterli satış derinliği ve ekonomik
maliyet sınırı gerekir. Önceki eşleşmiş ucuz çiftler maliyet tavanına katılmaz.

Karar sonrası yeniden defter okunur. Açılışta ortalama fiyat 50¢'ye ulaşırsa,
karar maliyeti pay başına 1¢'den fazla aşılırsa veya risk sınırı bozulursa
sanal işlem reddedilir. Tamamlamada gerçek yeniden okunan fiyatla FIFO
tavanı yeniden kontrol edilir. Maker dolumu veya iade varsayılmaz; piyasanın
ücret tarifesi ve alınabilir satış derinliği kullanılır.
[Resmî ücret formülü](https://docs.polymarket.com/trading/fees).

Her politika **ek beklemesiz yeni HTTP fiyatı** ve **en az 250 ms sonraki
fiyat** ile ayrı envanter tutar: dört sanal portföy, tek süreç. Erken HTTP
isteği yavaşsa 250 ms kolu da daha geç kalabilir; gerçek ölçülen süre yazılır.
Bunlar gerçek emir kabul/dolum gecikmesi değildir. Ana karşılaştırma
`pair_add_250 − pair_250`, atanmış pencere başına ücret sonrası dolardır.
Hızlı portföyler duyarlılık kontrolüdür; dört PnL tek portföy gibi toplanmaz.

## Ölçüm düzeltmesi ve sürüm ayrımı

Eski hazırlık döngüsü t245'te önbellek 30 saniye yaşlanmadığı için yeni
kapanmış mumu almıyordu. Artık son mumun kapanış zamanı ile yayımlanmış
olması gereken son dakika karşılaştırılıyor. Gerçek döngü testinde
t270/t280 kararları t239,999'da kapanan mumu kullanıyor.

`bosona-rebound-v2`, aynı yeni kaynak dizininde ayrı `data/rebound_v2/`
çıktısıyla başladı. Eski 240/270/280 kuralları ve 250 ms maliyet yöntemi
korunur; eski kayıtların içine yeni sürüm yazılmaz. Birincil yine t280.
Eski shadow süreçleri ve Jev değişmedi. Yeni envanter süreci
`bosona-inventory`, kayıtları `data/inventory/` altında.

Yeni envanter kolunda yalnız tamamlama için alış teklifi bulunması şart
değil; gerçek, taze satış teklifi yeterli. Girişte iki tarafın geçerli
alış/satış bilgisi gerekir. Boş defter fiyatla doldurulmaz. Eski rebound'un
iki taraflı defter şartı değişmedi; dolayısıyla düzeltme bütün geç defter
eksiklerini çözdüğümüz anlamına gelmez.

## Doğrulama ve sonraki okuma

Yerel ve Londra'da aynı çalıştırılabilir kontrol geçti: gerçek hazırlık
döngüsü, ilk/ek/tamamlama/yeniden giriş, ücretli maliyet, kısmi açık miktar,
önceki ucuz çiftin yeni pahalı çifti gizleyememesi, bütçe/açık pay sınırı,
açık envanterle yeniden başlatma, mükerrer kayıt, geç fiyat reddi, kaynak
sabitleme, tek yazıcı ve sonuç ödemesi. Hedefli Ruff ve derleme geçti.

```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/analiz/izleme/check_inventory_shadow.py"
```

Envanter günlüğünde `decision.context_gap` / `book_errors` veri eksiğini,
`intents=null` ise ilgili kararın yokluğunu gösterir. Veri eksiği olan anlar
başarılı “bekle” kararı sayılmaz. `execution.rejected` fiyat/derinlik/risk
reddidir. Karardan sonra kesilen süreçte tamamlanmamış işlem yeniden
oynatılmaz; günlükte karar var/işlem yok olarak kalır. `resolution` yalnız
resmî sonuçla yazılır; başlangıç verisi eksik pencerelerin gözlenen $0
işlemi tam kapsanmış sıfır işlemli pencereyle karıştırılmamalı.

İleri rapor: toplam dolar/atanmış pencere, eksik veri, ilk alım fiyat/zamanı,
ekleme ve tamamlama payı, açık miktar/süre, en büyük düşüş, en iyi üç
pencere hariç sonuç; Bosona'nın aynı sözleşmelerdeki görünür davranışıyla
birlikte değerlendirilecek. En az üç gün ve 100 seçilmiş işlem olmadan
kalıcı avantaj iddiası yok; bunlara ulaşmak da tek başına başarı değil.

Araştırma: `data/analysis/bosona_inventory_20260921/inventory_research.json`.
Kaynak ve runtime kanıtları aynı dizinde saklanır. Ekonomik sonuç henüz yok;
başlatılmış olmak kârlılık doğrulaması değildir.

**İlk gerçek pencere, 15:50–15:55 Türkiye:** envanter kolunda 27 planlı
karar kaydı; dokuzunda geçerli giriş bağlamı var ve giriş sinyali yok.
14 kayıtta fiyat geçmişi tazelik şartını geçmiyor; dört kayıtta iki taraflı
defter yok. Sanal alış sıfır. Fiyat boşlukları mum hatası değil: kaydedilmiş
spot geçmişinin bazı noktaları 3.000 ms sınırını aşıyor; sınır gevşetilmedi.

Rebound v2 t240'ta gerçek karar ve 250 ms sonrası sanal fiyat kaydetti;
t270/t280'de gerekli defter boştu. Her iki geç anda hazırlanan son mum
t239,999 kapanışı: mum düzeltmesi gerçek kayıtta da doğrulandı. Bu iki anı
geçerli strateji denemesi veya sıfır PnL diye saymıyoruz. Dolayısıyla
ilk pencere kârlılık/benzerlik sonucu üretmiyor.

Sayısal kontrol: `runtime_validation.json`; ilk günlük kesitleri
`inventory_forward.jsonl`, `rebound_v2_forward.jsonl`; kaynak/PID/manifest
kanıtı `runtime_boot.json`; Londra kontrol çıktısı `checks.log`.

## 16:21 Türkiye ara kontrolü

Yeni iki süreç aynı PID ve kaynaklarla çalışıyor. Envanter kolunda 167
karar anının 63'ünde giriş bağlamı geçerli; 68 fiyat geçmişi ve 36 defter
eksiği var. Düzeltilmiş rebound'da 18 denemenin yalnız t240'taki biri
geçerli: 14 boş defter, üç eski fiyat bağlamı. Ana t280 henüz ölçülemedi.

16:15 penceresinde ilk sanal çift kuruldu: 5 Up ve 5 Down, 250 ms
portföyünde ücretli toplam maliyet $2,62118; iki yönde de $5 sonuç ödemesi,
dolayısıyla yön bağımsız sanal katkı +$2,37882. Ek beklemesiz portföyde
+$2,42977. Kontrol ve ekleme politikası burada aynı işlemleri yaptı;
eklemenin katkısı henüz sınanmış değil. Resmî sonuç sorgusu kesitte hâlâ
bekliyor. 16:20 penceresinde ayrıca 5 Up / $2,48736 açık maliyet var;
bu pozisyonun sonucu yukarıdaki çift katkısına dahil değil.

İki yeni süreçteki 71 eski bağlam hatasının tamamında kapalı mum güncel.
Hepsinde fiyat geçmişinin en az bir örneği 3.000 ms sınırını aşıyor;
57 olayda yalnız geçmiş örnekler eski, anlık spot/TWAP geçerli. Eski
örneklerin yaş medyanı 3.064 ms, en büyüğü 7.302 ms. Bu ölçüm eksikliği
ayrı bir sorun; fiyat tazeliği sınırı bu durum kontrolünde değiştirilmedi.

Günlük tekilliği, gerçek fiyat-alım gecikmesi, FIFO tavanı, Decimal
maliyetleri, risk sınırları ve resmî sonuç/bekleyen ayrımı doğrulandı.
Kanıt: `data/analysis/bosona_inventory_20260921/status_1321/report.json`.

## Veri yolu düzeltmesi — 21 Eylül

Geçmiş fiyat seçimi artık **karar anına kadar alınmış** raporların olay
zamanıyla yapılıyor. Örneğin t−10 fiyatının t−8'de ulaşması, t anındaki
kararda kullanılmasını engellemiyor. Karardan sonra gelen veya geleceğe
tarihli veri kullanılmıyor; 3.000 ms tazelik sınırı aynı.

Tek taraflı defter gerçek eksikleriyle saklanıyor. Tam defterlerde mevcut
orta fiyat sıralaması korunuyor; eksik kotasyonda yalnız ucuz tarafın
satış fiyatı diğer tarafın alış fiyatından küçükse sıralama yapılabiliyor.
Gerçek satış derinliği olmayan tarafta sanal dolum yok. Rebound karşılaştırma
kolu alınamıyorsa maliyet ve sonuç `null`; sıfır kazanç gibi sayılmamalı.
Giriş sinyali, FIFO çift tavanı, risk ve gecikme sınırları değişmedi.

Kayıtlı 167 kararın aynı zaman kesiminde geçerli bağlamı 63→114 oldu;
eski 68 fiyat hatasının 51'i giderildi. Önceden geçerli hiçbir karar
kaybedilmedi. Gerçek veri boşlukları korunuyor; eski eksik defterleri
yeniden oluşturmadık ve bu replay'den PnL çıkarmadık.

Yeni kaynak dizini `/home/ubuntu/polymarket-bosona-inventory-v2/`;
`bosona-inventory-v2` PID112062 ve `bosona-rebound-v3` PID112442.
Yeni atamalar **21 Eylül 13:50 UTC / 16:50 TR** başlangıçlı, 72 saat.
Önceki süreçler ve kayıtlar kendi donmuş sürümleriyle devam ediyor;
yeni sonuçlar onlarla tek seri olarak birleştirilmeyecek.

Yerel/Londra gerçek scheduler testleri, gelecek veri ve eski fiyat reddi,
tek taraflı defterde bağımsız dolum/eksik sonuç, FIFO/risk/gecikme,
açık envanterle restart, kaynak kilidi, Ruff ve compile geçti.
Kanıt ve tekrar çalıştırılabilir kontroller:
`data/analysis/btc5m_feed_fix_20260921/`.

İlk tam ileri pencere doğrulandı: envanter 27 planlı kararın tamamını
kaydetti; 19 geçerli bağlam, 8 gerçek fiyat boşluğu, tek taraflı defterle
6 geçerli karar ve dört bağımsız kolda toplam 12 sanal dolum. Rebound
t240/270/280'in üçünde de geçerli karar ve ücretli sanal alış üretti.
Favori karşılaştırması iki kez alınabilir; bir kez satış kotasyonu eksik
olduğu için maliyet `null`. Eksik sonucu sıfıra çevirmedik. Akışta gözlenen
6 saniyelik gerçek fiyat boşluğu halen tazelik filtresine takılıyor.
Kaynak hashleri, gerçek defterden ücret/maliyet, FIFO ve risk sınırları,
250 ms gecikme ve günlük tekilliği `runtime_verified.json` ile doğrulandı.
Bu kontrol ekonomik üstünlük veya kazanç sonucu değildir.

## Her pencereye katılım deneyi — 21 Eylül

Operatörün daha fazla pencereye katılım isteği üzerine ayrı
`inventory_participation_v1` kuruldu. İlk giriş t30..200 arasında her 10
saniyede aranır: taze, kimliği doğrulanmış defterde beş pay alınabilen
taraflar arasından ücret dahil maliyeti düşük olan seçilir; eşitlikte Up.
İlk giriş RSI/momentum veya 50¢ filtresini beklemez. Bu istisna yalnız
ilk alışa aittir; sonraki ekleme/reopen filtreleri ve FIFO tamamlama aynıdır.
Pencere başına 5 pay klip, 10 açık pay, $15 alış, $5 en kötü sonuç sınırı
korundu. Her pencereye giriş hedeflenir; veri/derinlik/uygulama yoksa dolum
uydurulmaz. Bunlar bağımsız sanal portföyler, gerçek emir değil.

Londra: `/home/ubuntu/polymarket-bosona-participation-v1/`, tmux
`bosona-participation`, PID123275. İlk atama **21 Eylül 14:45 UTC / 17:45 TR**;
72 saat + 25 dakika sonuç takibi. Eski seçici sürüm ve rebound kaynak/PID'leri
korundu. Ana karşılaştırma aynı atanmış pencerelerde seçici `pair_add_250`
ile yeni katılımcı `pair_add_250`: katılım, ücretli net dolar ve açık risk.

Yerel/Londra gerçek scheduler testi: seçici sürümün iki pencerede hiç
girmediği girdilerde katılımcı her ikisine de girdi. t30 eski defteri reddetti,
t40 kötüleşen uygulama fiyatını reddetti, t50 giriş yaptı. Açık envanterle
yeniden başlatmada ilk alım tekrarlanmadı; profil değiştirme reddedildi.
İlk giriş istisnası ekleme veya tekrar açılışa uygulanamadı. Mevcut
regresyonlar, Ruff/compile ve manifest/kaynak kontrolü geçti.

Önceki altı pencerenin kayıtlı karar defterlerinde yeni kuralla 6/6 giriş
niyeti üretilebiliyor. Bu yalnız karar kapsamı kontrolüdür; o geçmişte yeni
uygulama fiyatı veya PnL üretmedik. Kanıt: `data/analysis/btc5m_participation_20260921/`.

İlk gerçek pencere teyidi: t30,082'de hızlı, t30,325'te gecikmeli kollar
5 Down aldı; her bağımsız kolun ücretli sanal maliyeti $2,38694. Mevcut
seçici giriş sinyali `None` iken yeni ilk giriş çalıştı. İlk beş planlı
kararda scheduler hatası yok. Gerçek defter tazeliği, ücret/maliyet,
250 ms istek zamanı, ilk alım tekilliği, risk ve kaynak hash'i
`runtime_verified.json` içinde doğrulandı. Henüz ekonomik sonuç yok.
