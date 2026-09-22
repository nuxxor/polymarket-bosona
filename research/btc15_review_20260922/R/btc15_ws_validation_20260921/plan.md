# BTC15 WebSocket gerçekleşme kontrolü

21 Eylül 20:54 UTC: kullanıcı sonraki adımı önce açıklayıp ilerlememizi istedi.
Ana planın çoklu-piyasa araştırmasının devamı; btc15_reconciled_v1'in açık WS
veri kapısı. MAIN, eski aday/protokol, diğer incelemeler ve recorder kaynakları
salt okunur. Yeni emir, shadow, canlı kalibrasyon veya süreç müdahalesi yok.

Önceden sabit kesit: pilotun ilk tam BTC15 penceresi, 21 Eylül 20:45–21:00 UTC
(S=1790023500). Kamu WS öneki 21:02 UTC yerel alım zamanına kadar dondurulur.
Sonuç veya Bosona varlığı seçim girdisi değildir. Önceden abonelik alınmış
başlangıç defteri korunur; açık gzip kuyruğu başarı sayılmaz.

1. Recorder'ın gerçek kaynak/hash/kalp atışı; akışın tam defter+delta+tick
   olarak yeniden kurulması; milisaniye ve token/condition doğrulaması.
   Kabul: boşluklar, sıra/kitap uyuşmazlıkları ve tekilleştirme açık sayılır.
2. Seçili pencerenin WS işlem hash'lerini public trades ve receiptlerle
   miktar/gerçek maker seviyesine aç. Mevcut tüm-katılımcı decoder yeniden
   kullanılır; iki-token/mint olayları çift işlem sayılmaz. Yerel alım,
   sunucu mesajı, blok saati birbirinden ayrılır. Ücretsiz public RPC.
   Kabul: her işlem uzlaşır veya somut eksiklikle işaretlenir; veri kaybı sıfır değil.
3. Kapılar geçerse aynı sabit küçük-risk kollarını yeni veriyle tanısal karşılaştır;
   geçmezse sahte kâr üretmeden en küçük sonraki veri ihtiyacını belirt.
   Genel ekonomi için on gün/100 giriş/50 ekleme eşiği aynen açık.
4. Tek ağsız yeniden çalıştırma, anlamlı regresyonlar, hedefli Ruff/syntax,
   çıktı SHA ve kısa Türkçe rapor. Yalnız bu dizin ve kendi kök planı yazılır.

Kuyruk varsayımları PnL alt–üst sınırı değildir. L2 emir sahipliği/sırası
göstermez; public sunucu zamanı özel eşleşme veya emir kabul saati sayılmaz.

## Kontrol sonucu

- [x] Sabit ilk tam pencere ve 21:02 kesiti donduruldu. 901/901 defter
  noktası, kopma/sıra/fiyat-miktar aynalama hatası yok.
- [x] 932 receipt tüm katılımcı nakit/tokenleriyle; WS 923/923 ve miktar
  tam uzlaştı. 892 WS işlemi pencere içinde; öncesi/sonrası ayrı.
- [x] İlk taker sayfalamasındaki 2 tekrar/2 eksik korundu. İkinci listenin
  932 kaydı ve all-rows 2.609 kaydı zincirle tamamen eşleşti. Sayı tek başına yeterli değil.
- [x] 16 bağımsız kısa kotasyon kontrolü: 15 koşullu/1 post-only ret;
  kuyruk arkası 5, önü 32 pay. Ekonomik PnL veya portföy testi yapılmış sayılmadı.
- [x] M1/M2 olay motoru: simüle edilmiş borsa ve öğrenilmiş envanter, iptal
  yolunda dolum, kümülatif bildirim, post-only ret ve ortak rezerv ayrıldı.
  Altı gerçek-veri senaryosunda risk/nakit ihlali0; ayrı envanterler sonda aynı.
- [x] 18 regresyon, Ruff/syntax, iki ağsız çalıştırmada 6 aynı çıktı SHA.
- [ ] Özel kabul/iptal/öğrenme gecikmesi ve sıra varsayımlarının gerçek
  kalibrasyonu; P0 ile aynı uygulama şartında ekonomik üstünlük gösterilmedi.
- [ ] On günlük ekonomik kabul ve iki saatlik pilotun kalanının kontrolü açık.

RAPOR.md ve results/reproduction.json bu sonlu aşamanın kanıtıdır. Recorder
kaynağı/süresi, eski aday ve ana repo değişmedi; kaynak yardımcıları yeniden
yazılmadı. Sonraki pilot kesitinde bir reconnect görüldü; ilk temiz kesite eklenmedi.
