# BTC15 birleşik araştırma v1 — 21 Eylül

Kullanıcı Ultra/Fable sentezindeki sırayı uygulamamızı istedi. Çıktı yalnız bu
ayrı dizindedir. MAIN, R'nin donmuş adayı/protokolü, inceleyici kod/sonuçları,
Jev/Londra/yerel recorder süreçleri değiştirilmez. Gerçek emir/deploy yok.

1. Ham dilimlerden conditionId'li gerçek çokluk; ilk-saniye fazı; MERGE sonrası
   envanter; karar erişim zamanı düzeltmeleri ve maker/taker rolleri birleşsin.
   Kabul: 3.503 piyasa/14.014 BUY toplamı aynı, BTC15 598/5.441 mutabakat;
   rol×düzeltilmiş faz ve eski/yeni farklar, belirsizlikler açık.
2. Eski kodu kaynak olarak koruyarak ayrı sonlu replay düzeltmesi: miktar
   korunumu/kısmi dolum, ortak açık-emir rezervi, 15$ sert sınır, 5pay klip,
   veri boşluğu, nedensel fiyat ve kabul/iptal gecikmesi. Bilinmeyen eşleşme
   saati emir saati yapılmaz. Kuyruk önü/arkası sonuçları PnL sınırı değildir.
   Kabul: önceki üç karşı örnek ve yeni iki-emir rezerv/zaman testleri;
   gerçek arşivde hiçbir limit ihlali; veri kapısı geçmeden ekonomik PnL null.
3. Aynı donmuş gerçek defter üzerinde çıktıları tekrar üret; gerekli veri
   ve kalan kapıları raporla. Pozitif sonuç için eşik arama veya aday değiştirme.
   Kabul: syntax/Ruff, regresyon, gerçek çalıştırma, aynı hashli tekrar;
   eski çekirdek hashler aynı. Tam özel strateji çözüldü denmez.

Varsayımlar: ilk-saniye paket gerçek emir kimliği değildir; bilinmeyen ilk
bakiyeler ve REDEEM token miktarı uydurulmaz. Kaynakta eşleşme zamanı yoksa
REST+blok-zamanı çalışması yalnız tanısal senaryo olabilir, uygulama testi değil.

## Gerçekleşen kontrol — 21 Eylül

- [x] 3.503/14.014 ham çokluk ve nakit uzlaştı. BTC15 598/5.441; yeni geç
  ekleme 1.150, maker 1.077. Rol×faz/gerçek envanter ve erişim-saati birleşti.
- [x] Seçilmiş cached receipt kohortu yeniden çözüldü: BTC15 19 piyasa,
  283 dolum, 157 parent. İlk gönderim ve eşleşme saati bilinmeyen bırakıldı.
  Bu sonuçtan bağımsız yeni kohort değildir.
- [x] Miktar, kısmi dolum, ortak rezerv, hedge klibi, gecikme ve boşluk
  kontrolleri; gerçek 14 piyasa × 6 yolda limit ihlali yok. Ekonomik sonuç null.
- [x] 16 regresyon, syntax/Ruff; iki ağsız çalıştırmada 13 çıktı aynı SHA256.
  Eski aday/protokol beş çekirdek hash ve REST recorder kaynak hash'i aynı.
- [x] Ek kamu veri ihtiyacı: ayrı 90sn WS ve 12sn sonlu recorder denemesi
  gerçek veriyle geçti. Kullanıcının eksik defteri kaydetme talebi kapsamında
  ayrı 2saat/1GiB sınırlı veri pilotu başladı; eski kayıtlar değişmedi.
- [ ] Pilot 20:35:57–22:35:57 UTC sürüyor; kapanmış tam pencerelerin L2,
  işlem/receipt, iki-token çokluk/saat kontrolü sonraki kapı. Bitmiş sayılmadı.
- [ ] Yeni sonuçtan bağımsız parent kohortu ve ekonomik ileri kabul yapılmadı.
  Replay tanısal düzeltme düzeyinde; WS adaptörü/portföy kapısı açık.

Teslim: RAPOR.md, reproduce.py, results/reproduction.json. Bu aşamanın
muhasebe/motor düzeltmeleri doğrulandı; kârlı strateji veya tam araştırmanın
çözüldüğü iddia edilmez. Mevcut aday korunur; gerçek emir/shadow deploy yok.
