# BTC15 kamu akışı: tamlık ve saat deneyi

22 Eylül 2026 Türkiye / 21 Eylül UTC. Tek, önceden atanmış veri deneyi.

**Sonuç:** Yeni ham kayıtta iki bağlantı da piyasa içindeki 351 zincir
eşleşmesini ve 662 maker dolum parçasını yakaladı. İşlem API’sinin ilk iki
taker listesinde bir satış eksikti; sonraki sorguda eklendi. Dondurulmuş
ilk veri kapısı `MISSING_DATA` olarak korunuyor. Tam kamu akışı, gerçek
kuyruk konumu ve dolum saatinin kalibre edildiği anlamına gelmiyor.
Ekonomik PnL `null`; aday ve strateji eşikleri değiştirilmedi.

## Ne yaptık?

BTC15 `1790031600`, 21 Eylül 23:00–23:15 UTC önceden atandı. Slug yalnız
keşif için kullanıldı; resmî başlangıç/bitiş, iki token ve Chainlink
60 saniyelik TWAP çözümleme kuralı mevcut sınıflandırıcıyla doğrulandı.
Plan 22:53’te yazıldı, kayıt 22:56:08’de başladı. Alım kesiti 23:17,
otomatik durma hedefi 23:17:10, kapanış 23:17:11 oldu.

İki ayrı kamu WebSocket bağlantısında mesajlar **ayrıştırılmadan önce**
saklandı. Ham sıra, bağlantı numarası, UTC alım saati ve monoton saat var.
Bozuk/bilinmeyen/binary mesaj sessizce silinmiyor. HTTP keşfi bağlantıdan
önce yapıldı; REST sayfalaması okuyucu döngüsüne girmedi. Kayıt toplam
512 MiB ham veri, 2 GiB boş alan ve süre sınırıyla kendiliğinden kapandı.
İki bağlantının kitapları birleştirilerek yapay bir kuyruk oluşturulmadı.
[Resmî kamu akışı](https://docs.polymarket.com/market-data/realtime-data).

| Kontrol | A | B |
|---|---:|---:|
| Ham WebSocket frame | 205.807 | 205.807 |
| Kesit içi LTP mesajı, hazırlık dahil | 358 | 358 |
| Piyasa içi zincir eşleşmesi | 351 | 351 |
| Piyasa içi maker parçası | 662 | 662 |
| Geçerli defter örneği | 901/901 | 901/901 |
| Ayrıştırma/kimlik/sıra sorunu | 0 | 0 |
| Kesit içinde kopma | 0 | 0 |
| Kaynak → yerel alım ortancası | 38 ms | 36 ms |
| İlk veri kapısı | MISSING_DATA | MISSING_DATA |

İki akışın ortak işlem kimlikleri ve kaynak saatleri aynı. Hazırlık dahil
680 maker parçasında yalnız A’da/B’de kalan yok. Aynı dolumun B−A yerel
alım farkı ortanca −1 ms, aralık −262…188 ms. Bu iki ayrı makine/saat
ölçümü değil; aynı bilgisayar ve sağlayıcı ortak kayıp yaşayabilir.
Kaynak → alım farkı da kesin eşleşme gecikmesi değildir.

Kapanış kuyruğunda A 23:17:03,159, B 23:17:03,134’te koptu; yaklaşık
2,2 saniye sonra yeniden bağlandı. İkisi de sabit 23:17 kesitinden sonra.
Ham toplam 332.035.546 bayt; iki gzip toplam yaklaşık 43,1 MB.
Eski REST kaydedicisi PID 1714322 çalışır durumda; bu deneyin kendi
süreli kaydedicisi kapandı. Eski süreçlerin ayarlarına müdahale edilmedi.

## API ile zinciri neden ayrı denetliyoruz?

363 transaction receipt’i hatasız çözüldü. Akış/API evreninin ortak eksik
olmasına karşı bağımsız `eth_getLogs` taraması da yapıldı: sabit 23:00–23:17
blok-zamanı aralığında 680 blok, 34 sorgu, 11.337 V2 Exchange eşleşme logu.
İki tokenin 351 eşleşmesi tam olarak mevcut receipt’lerle uzlaştı; iki yönde
de fark yok. İlk/son sorgu ikinci kamu RPC’sinde aynı. Blok saati kesin
borsa eşleşme saati olarak kullanılmadı. Kontrol 23:13’te, sonuçtan önce
plana eklendi. [Standart log sorgusu](https://ethereum.org/en/developers/docs/apis/json-rpc/#eth_getlogs).

Piyasa-geneli `takerOnly=true` listesi 23:18:09 ve 23:20:08’de 362 satırdı.
99,9¢’den 5 paylık bir gerçek SELL eksikti: brüt 4,995 $, ücret 0,000340 $.
İki WebSocket, genel API ve iki RPC receipt’i bu satışı doğruluyor.
23:23:36’daki kullanıcı filtreli taker sorgusunda satış var; 23:24:14’te
piyasa-geneli liste de 363 satıra çıktı. Böylece kalıcı rol hatası
kanıtlanmadı; sorgu yanıtının zamanla değiştiği gösterildi. Sunucudaki
gecikme/cache nedenini bilmiyoruz. İlk cevaplar ve ilk kapı değiştirilmedi.
[Resmî işlem API’si](https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets).

Kimlik: `0x5e4df61d3d65c1b423cac070fcd5507d9933c1ce885abbc9dc13816feeca31cd`,
OrdersMatched log 445; `results/api_diagnostic.json` bütün karşılaştırmayı
ve alım zamanlı ham cevapları işaret eder. Gamma ilk sorguda henüz
`closed=false` döndü; 0,9995 fiyatını resmî kazanan sonucu saymadık.

## Önceki kayıp işlem ve saat karşı örneği

Eski 22:15 penceresindeki kayıp gerçek: aynı blok/token/yön/fiyat ve
7,833334 pay özetine sahip iki ayrı emir var. Alıcılar, emir hash’leri ve
maker parçaları farklı. İkinci kamu RPC ve bağımsız blok logu doğruluyor;
eski WS’de yalnız bir transaction var. Eksik saati komşu işlemden üretmedik.

“Aynı fiyat ve miktar otomatik tekilleştiriliyor” genel açıklaması çürüdü:
yedi önceki BTC15 penceresinde aynı ekonomik özetli 167 grup / 379 gerçek
eşleşme bulundu. 166 grubun bütün işlemleri kayıtta; yalnız bir grupta
bir eksik var. Eski kaydedici yalnız tanınan olayları sakladığı için
yayın kaybı, ulaşmayan frame ve ayrıştırma/filtre kaybı kesin ayrılamıyor.
Yeni ham kayıt bu ayrımı gelecekte denetlenebilir kılıyor; tek temiz
pencere eski kaybın nedenini kanıtlamıyor.

Diğer oturumun kapalı M5/M6 kanıtı yalnız emir saatleri için salt okunur
kullanıldı; BTC5 stratejisi araştırılmadı. Beş gerçek dolum receipt/emir
kimliğiyle doğrulandı. Birinde public LTP kaynak saati, ilk `MATCHED`
GET cevabının UTC değerinden 141,541338 ms sonra. Saat alanları arasındaki
senkronizasyon ölçülmediğinden bunu kesin fiziksel gecikme saymıyoruz.
Ama LTP’nin kesin eşleşme saati olduğu da doğrulanmış değil.

L2 miktar azalması iptal veya eşleşme olabilir; emir kimliği vermez.
Aynı hacim delta ve LTP üzerinden iki kez kuyruktan düşülemez.
Private eşleşme saati, gerçek kuyruk konumu ve kalibre ekonomik sonuç
hâlâ bilinmiyor. Hesap akışına bağlanılmadı, anahtar okunmadı, emir
verilmedi. [Hesap bildirimlerinin kapsamı](https://docs.polymarket.com/trading/realtime-order-updates).

## Sonraki adım ve karar sınırı

1. Sonraki veri protokolünde canlı karar kesiti ile kapanış sonrası
   mutabakatı ayır. İlk API cevabını koru; sınırlı tekrarlarla sonradan
   değişen listeyi ayrıca raporla. Rol ve çokluk kontrolünü zincir kimliğiyle
   yap. Bu protokol değişikliği eski pencereyi geriye dönük başarılı yapmaz.
2. Ham WS + bağımsız blok taramasını yeni, önceden atanmış pencerelerde
   kullan. İki bağlantının aynı işlemi kaçırması hâlâ mümkün; tek pencere
   uzun dönem veri güvenilirliği kanıtı değil.
3. Yürütme simülasyonunda kamu yayım saatini kesin dolum saati sayma.
   Saat/iptal sırası belirsizliğini sonuç aralığı veya `null` olarak koru.
   Kendi kabul/iptal/dolum bildirimleri aynı saat alanında olmadan tek bir
   kuyruk-PnL sayısını ekonomik kanıt diye sunma. Mevcut yetki kamu verisi
   ve yerel analiz; yeni hesap bağlantısı veya gerçek emir bu adımın parçası değil.

Bu adım kayıt ve teşhis altyapısını iyileştirdi. Bosona’nın kotasyon
fiyatı, boyutu ve iptal kuralı çözülmedi; kârlı taklit henüz kanıtlanmadı.

## Tekrar üretim

`record.py` tekrar başlatılmaz: eski ham dizine ikinci yazıcıyı reddeder.
`audit.py` önceki veri/receipt/defter yardımcılarını yeniden kullanır;
`check.py` ham kayıt, süre/boyut sınırı, bozuk mesaj, çokluk, saat ve eksik
RPC logu karşı örneklerini sınar. Kaynaklar ve protokol hash ile korunur.

```bash
P=/home/taygun/Masaüstü/KararAtlas/base1/bin/python3
N=/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_feed_integrity_20260922
OPENBLAS_NUM_THREADS=1 "$P" -B "$N/audit.py" repeat
"$P" -B "$N/check.py"
"$P" -m ruff check "$N/record.py" "$N/audit.py" "$N/check.py"
```

Kamu edinimi `audit.py fetch`, ardından `scan`, `compare`, `diagnostic` ile
önbelleğe alındı. `repeat` ağ çağrılarını yasaklayarak iki kez çalışır ve
sonuç hash’lerini karşılaştırır. Ham cevaplar URL/alım zamanı ile saklıdır;
`results/reproducibility.json`, `results/checks.json` ve teslim manifesti
somut doğrulamayı içerir. Eski aday, protokoller ve kaynak hash’leri aynı.

Doğrulama: 8 çalıştırılabilir kontrol, syntax ve hedefli Ruff geçti. Ağ
çağrıları kapatılmış iki koşuda 16 çıktı aynı hash ile üretildi. Son kontrol
bunları tekrar doğruladı; 12 doğrudan kaynak ve önceki teslim hash’leri aynı.
