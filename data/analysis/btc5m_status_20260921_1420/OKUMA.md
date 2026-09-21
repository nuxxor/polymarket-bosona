# BTC5m kısa kontrol — 21 Eylül 17:20 TR

Yeni sürümlerin ilk altı penceresi: 16:50–17:20 TR. Londra kaynak
hashleri ve PID'ler aynı; runtime ve strateji değiştirilmedi.

- Envanter: 162/162 planlı karar, 144 geçerli bağlam, 18 fiyat boşluğu.
  27 geçerli karar tek taraflı defterle; scheduler hatası yok.
- Rebound: 17/18 geçerli karar; ana son 20 saniye 5/6. Bir fiyat boşluğu.
  Alınamayan favori karşılaştırmaları `null`; sıfır PnL değildir.
- Ücret sonrası 250ms sanal sonuç: kontrol −$0,39053, eklemeli +$0,23117.
  İkisinde de üç işlemli pencere; eklemeli kolda 3 ilk, 3 ek, 4 tamamlama.
  Bağımsız hızlı kollar: kontrol −$0,24764, eklemeli +$0,02529.
- Altı aynı piyasada Bosona: 134 kamu dolumu, API maliyetiyle −$158,631739;
  iade/sabit gider hariç. Büyük hacmi bizim beş payla eşit performans
  karşılaştırması sayılmaz. Altı piyasanın altısında işlem yapmış; biz üçünde.
- İlk yön, üç ortak işlemli pencerede ikisinde aynı. ±15 saniye yakınında
  yalnız bir Bosona yönü görülen dört eşleşmenin ikisinde yön aynı.
  Küçük örnek: davranış benzerliğinde ilerleme kanıtı sayılmaz.
- İlk alış medyanı Bosona 71 saniye / 29¢, biz 150 saniye / 16¢;
  işlemli pencere kümeleri farklı, bu yalnız betimleyici karşılaştırmadır.

İlk alım/ekleme/tamamlama akışı çalışıyor. Aynı yönü, zamanı ve fiyatı
seçtiğimizi henüz gösteremiyoruz; kalıcı ekonomik üstünlük iddiası yok.

Kontroller: gerçek activity/trades kayıt çokluğu, kimlik/token, altı resmî
sonuç, bağımsız Decimal toplamları, FIFO/risk/ücret/gecikme/tekillik,
üretim kaynak hashleri ve Ruff/compile geçti. Tekrar: bu dizindeki
`check.py`; dondurulmuş API yanıtlarını kullanır, çalışan süreçlere yazmaz.
