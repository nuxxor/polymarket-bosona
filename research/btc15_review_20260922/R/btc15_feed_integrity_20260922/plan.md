# BTC15 kamu akışı ve saat yeterliliği — 21 Eylül 22:53 UTC

Kullanıcı sonraki veri/yürütme adımını onayladı. Ana planın çoklu-piyasa
araştırması; önceki `btc15_execution_reserve_20260921` sonrasındaki açık veri
ve saat kapısı. MAIN ve bütün eski kaynak/çıktı/süreçler salt okunur.
Yalnız bu yeni dizin ve araştırma kök planı güncellenir. Emir/LIVE/shadow,
özel API/anahtar okuma, ücretli servis, Londra/recorder ayarı değişikliği yok.

Önceden atanmış tek yeni sözleşme: BTC15 21 Eylül23:00–23:15UTC,
başlangıç1790031600. İsim yalnız keşif; resmî başlangıç/bitiş/iki token/
ChainlinkTWAP60 mekanizması doğrulanır. Bitiş+120sn alım kesiti23:17UTC;
yazıcı23:17:10UTC'de biter. Hazırlık başlangıca yetişmezse eksik sayılır;
başka kârlı pencere seçilmez. Bu bir veri deneyi, PnL seçimi/optimizasyonu yok.

1. [x] Eski22:15 penceresindeki kayıp transaction'ı resmî receipt ve API
   karşı örneğiyle aç; filtre kaybı/bağlantı/yayın kaybı kanıt sınırlarını ayır.
2. [x] Aynı iki kamu tokenini iki bağımsız WS bağlantısıyla aynı makinede
   kaydet; ham mesajı ayrıştırmadan önce sıra/UTC/monotonic/bağlantı kimliğiyle
   sakla. HTTP keşif/paging okuyucu döngüsünü durdurmasın. Bozuk/bilinmeyen
   mesaj silinmesin; reconnect/timeout/heartbeat ve kapalı gzip hash'i olsun.
   Toplam512MiB ham kayıt,2GiB boş alan tabanı,30dk azami süre; otomatik bitiş.
3. [x] Her bağlantının tamlık kapısı ayrı: receipt/işlem miktarı ve çokluğu,
   zaman, book/delta, kopma, karar öncesi tam snapshot. Birleşim tek akış diye
   sunulmaz; kopya LTP miktarı iki kez sayılmaz. Kapanmış API tekrar listeleri
   değişirse ilk cevap korunur; eksik saat blok saatinden üretilmez.
4. [x] Yeni M5/M6 kapalı emir kanıtları salt okunur: private bildirim/
   gerçek eşleşme saati yoksa kalibrasyon iddiası yok. Aynı fiyat/miktarlı
   L2 düşüşü eşleşme kimliği veya kuyruk kredisi sayılmaz. P0/M1/M2 aynı.
5. [x] Ham-mesaj/sıra/çokluk/kayıp-saat negatif kontrolleri, gerçek kamu
   kayıt smoke'u, tam atanan pencere raporu, hedefli lint/syntax, aynı-hash
   ağsız tekrar. Uzun dönem ekonomik kabul ayrı ve açık kalır.

Receipts için eski1000/piyasa kamu bütçesi korunur; iki RPC çapraz kontrol.
Kapanış sonrası ilk tam trade listesi ve ayrı tekrar alınır. Bağımsız
bağlantılar aynı sağlayıcı/makineyi paylaşır; ortak kaybı giderme garantisi yok.

23:13UTC ek doğrulama, sonuç/kâr görülmeden: WS+/trades evreninin ortak
eksik kalmasını denetlemek için bağımsız eth_getLogs. Sabit[S,bitiş+120sn)
blok-zamanı aralığı, bilinen V2Exchange OrdersMatched, iki token filtresi;
en fazla1000blok,20blokluk parçalar, ilk/sonparça ikinciRPCteyidi. İlk
protokol/recorder değiştirilmez. Ek log varsa iki akış da eksik sayılır;
blok saati eşleşme saati yapılmaz. Kamu bütçeli/sonlu okuma, emir yok.

Tamamlandı — 21 Eylül 23:28 UTC / 22 Eylül Türkiye. Ham kayıt ve gerçek
çıktı kontrol edildi: iki akışta 351/351 piyasa-içi eşleşme, 662 maker
parçası, 901/901 defter noktası. 363 receipt; bağımsız 680 blok taramasında
yeni/eksik eşleşme yok. Kesit sonrası kopmalar korunuyor. İlk iki taker
API listesi bir satış eksik; sonraki ayrı listede yalnız bu satır eklenmiş.
Eski MISSING_DATA hükmü değişmedi, ekonomik PnL null. 8 kontrol, Ruff,
syntax; ağ çağrıları yasakken iki koşuda 16 aynı-hashli çıktı. 12 doğrudan
kaynak ve önceki teslim manifestleri korundu. Kayıt kendiliğinden kapandı;
eski REST PID 1714322 çalışıyor. P0/protokoller/MAIN/Londra değiştirilmedi.
Uzun dönem ekonomik kabul ve private saat/kuyruk kalibrasyonu açık.
