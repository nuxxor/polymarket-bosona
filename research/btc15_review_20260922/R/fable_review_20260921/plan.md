# Fable bağımsız inceleme — BTC5dk dışı Bosona, öncelik BTC15dk — 21 Eylül 2026

Başlangıç: 21 Eylül 2026 18:34 UTC. Dizin: `R/fable_review_20260921/` (R = nonbtc5 araştırma dizini).
MAIN, R, F, S salt okunur. Kendi kopyalarım `code/`, ham indirmeler `raw/`, sonuçlar `results/`,
alt ajan çalışmaları `agents/<ad>/`. Aday (`candidate.py`) ve `protocol.json` değişmez.
Gerçek emir, LIVE, shadow, ücretli servis, yeni kalıcı süreç, recorder müdahalesi yok.
Kamu API (data-api, gamma, clob, Binance, Polygon public JSON-RPC) yalnız sınırlı, ≥1 sn aralıklı, önbellekli.

## Kabul ölçütleri
- [x] Üç rapor + manifest + kaynak zinciri okunmuş; her karar değiştiren iddia için
      iddia → kaynak/sürüm(SHA) → yeniden hesap → karşı örnek → hüküm zinciri.
- [x] Muhasebe: BTC15dk tablosu ham activity dilimlerinden Decimal ile bağımsız yeniden üretim;
      en az bir kazanç, bir kayıp piyasası ham kayıttan ödemeye kadar.
- [x] Gözlem birimi: dolum → transaction → orderHash (kamu receipt) → rol; aynı saniye/5/10 sn paket duyarlılığı.
- [x] Zaman/sızıntı: bağlam, referans, uygulama örneği ve etiket pencereleri için nedensellik denetimi.
- [x] Kontrol grupları/istatistik: eşleştirme, sınıf dengesizliği, tekrar kullanım, bootstrap.
- [x] Yeni gerçek defter (S ve sonrası, donmuş UTC kesit + hash): dolum fiyatı vs bid/ask, seviye varlığı.
- [x] En fazla iki mekanizma + tek ayırıcı deney; çalıştırılabilir sonlu kod.
- [x] Regresyon testleri, ruff/syntax, gerçek veri çalıştırması; Türkçe kısa özet + ayrıntılı rapor.

## ÖN KAYIT (sonraki değerlendirme verisi açılmadan önce yazıldı — 18:45 UTC)

### Şimdiye kadar bakılan veri
13 Eyl–21 Eyl 12:00 tarihsel (R), F sonuçları, S kesiti (14:25–18:05 UTC). Henüz açılmayan: 18:05 UTC sonrası
`books_72h` kayıtları ve o dönemin Bosona dolumları. Bunlar yalnız "yeni dönem" olarak ayrı raporlanacak;
hipotez seçimi aşağıda dondurulmuştur.

### Ön hesap (18:40 UTC'de yapıldı)
Ücret imzası: activity `usdcSize − size·price` ya 0 (maker) ya `0,07·size·p·(1−p)` (taker); 14.014 dolumda
%100 kapsam, "other" 0. Sunucu `takerOnly=true` bayrağıyla 8 BTC15dk piyasasında 156/156 uyum.
BTC15dk: 4.396 maker / 1.045 taker kayıt; geç ekleme (600–899 sn, `add`) 1.099 maker / 74 taker.
S kesiti: 116 maker / 15 taker; maker dolumlarının 63/116'sı t−1'de tam best bid.

### Seçilen en fazla iki mekanizma (değerlendirme verisi görülmeden)
**M1 — Model fiyatlı pasif kotasyon (value-maker).** Bosona alış emirlerini dinlenen (maker) emir olarak koyar;
"geç ekleme" bir zaman tetiklemeli karar değil, önceden konmuş emrin fiyat hareketiyle dolmasıdır.
Öngörüler: (a) dolumların ≥%85'i maker; (b) maker dolum fiyatı t−1'de ≤ best bid, çoğunlukla = best bid;
(c) dolum öncesi o seviyede ≥ qty boy vardır ve dolum sonrası azalır; (d) maker dolumlarını izleyen kısa
vadede fiyat dolum tarafına karşı hareket eder (adverse selection) ama resmî sonuca göre kümülatif net
pozitif olabilir; (e) yeni dönemde bu katkı dalgalanır, tek gün negatif olabilir.
Yanlışlanma: maker payı <%60; dolum fiyatları best bid'den sistematik yukarıda; seviye önceden görünmüyor.

**M2 — Envanter/risk azaltımı için aktif tamamlama (inventory hedger).** Açık risk büyüdüğünde Bosona spread'i
geçerek (taker) karşı tarafı alır; çift maliyeti >1 olsa da en kötü sonucu iyileştirir.
Öngörüler: (a) tamamlamalar taker-ağırlıklı; (b) taker dolum fiyatı t−1'de ≥ best ask; (c) taker tamamlamaların
nakit-PnL katkısı negatif, en kötü sonuç iyileşmesi pozitif; (d) taker olasılığı açık risk ve kalan süreyle artar.
Yanlışlanma: taker dolumlar açık riskten bağımsız; taker tamamlamalar en kötü sonucu iyileştirmiyor.

Eski açıklama (mevcut aday): t=180 taker giriş + t=600 taker ekleme + olasılık farkı filtresi. Bu, gözlem
birimi (dolum=karar) varsayımına dayanır; M1 doğruysa yanlış uygulama modelidir.

### Tek sonraki deney (taslak, veriyle rafine edilecek)
Kuyruksuz, sınırlı pasif dolum replay'i: 72 saatlik 1 sn L2 bandı + aynı piyasaların kamu `/trades` baskıları ile,
sabit bir model-fiyatlı alış kotasyonu kuralının (M1) kötümser (fiyat geçilmesi: ask ≤ kotasyon) ve iyimser
(kotasyon fiyatında herhangi bir satış baskısı) dolum sınırları arasında ücret sonrası sonucu; M2 kolu açık/kapalı.
Başarı/yanlışlanma ölçüsü raporda.

## İlerleme
- [x] Talimat/plan/rapor/manifest/kaynak okuması (18:34–18:40 UTC)
- [x] Ücret imzası rol sınıflandırması + sunucu çapraz kontrol + S defter testi
- [x] Workflow 1: 10 boyutlu denetim + karşıt doğrulama + eksiklik eleştirmeni (263 ajan; 110 bulgu, 91 hayatta, 19 çürütüldü; results/audit_verification.md)
- [x] Mekanizma karşılaştırması, yeni dönem kesiti (20:33 UTC), tek deney replay'i (S 14 + kör 10 piyasa) — RAPOR_FABLE.md bölüm 6–7
- [x] Rapor (RAPOR_FABLE.md, OZET.md), regresyon (role_classifier, test_passive_replay), ruff temiz, results/manifest.json, artifact https://claude.ai/code/artifact/e8aceadf-73d0-437e-b4fd-f29e3436cf9d

## ÖN KAYIT 2 — tek sonraki deney: kuyruk-konumlu pasif dolum replay'i (18:58 UTC, S dönemi sonuçları görülmeden)
Veri: 1 sn L2 bandı (F/raw/books_72h; S kesiti + sonraki tam saatler) + aynı piyasaların kamu piyasa-geneli `/trades`
baskıları (data-api, tüm cüzdanlar, takerOnly=true satırları = eşleşme başına taker tarafı) + resmî sonuç (Gamma).
Sabit kurallar (eşik taraması yok; 3 kol + 1 kontrol):
- P0 kontrol: mevcut adayın t=180 taker girişi (5 pay, ≤55¢, model farkı ≥5¢) + t=600 ekleme + FIFO≤0,98 tamamlama — gerçek ask ile.
- P1a "touch-maker": age 30..840 her saniye, iki tokende de best bid fiyatına 5 paylık alış kotasyonu (spread ≤3¢ ve
  iki taraflı defter şartı); touch değişirse iptal/yeniden koy (kuyruk sıfırlanır); token başına aynı anda tek kotasyon;
  net açık pay |Up−Down| ≤ 10 iken yalnız azaltan tarafa kotasyon; nakit ≤15 $, en kötü sonuç ≥ −5 $ (adayla aynı limitler).
- P1b "touch−1": P1a ile aynı, fiyat best bid − 1 tik (0,01).
- P2 = P1a + M2 taker hedge: |net| ≥ 10 pay olduğunda karşı tarafı ask'tan (ücretli) alarak neti 0'a indir (fiyat sınırı yok,
  yalnız limitler); bu kol "1 $ üstü tamamlama" davranışının maliyet/faydasını ölçer.
Dolum modeli (kuyruk konumu, 1 sn çözünürlük): kotasyon konduğunda kuyruk_önü = o fiyattaki görünen bid boyu;
her taker SELL baskısı (kendi tokende, fiyat ≤ kotasyon) veya taker BUY baskısı (diğer tokende, fiyat ≥ 1−kotasyon; mint eşleşmesi)
kuyruğu tüketir. KÖTÜMSER: önümüzdeki hiç kimse iptal etmez → dolum ancak kümülatif baskı ≥ kuyruk_önü + 5. İYİMSER: kuyrukta
ilkiz → ilk baskıda dolum. Kısmi dolum yok (5 pay ya hep ya hiç). Defter boşluğu (>3 sn) sırasında kotasyon askıda sayılır.
Ölçüler: piyasa başına ücret sonrası nakit PnL (kötümser/iyimser), dolum sayısı, taker hedge maliyeti, en kötü sonuç,
piyasa/gün kümeli bootstrap; rebate (0,2·0,07·Σq·p(1−p)) yalnız ayrı satırda, birincil sonuca dahil değil.
Yanlışlanma: kötümser sınırda P1a ve P1b'nin piyasa-kümeli %95 üst sınırı ≤ 0 ise "pasif kotasyon edge'i bu veriyle yok".
Kabul için gereken örneklem: ≥10 tam UTC gün, ≥100 kotasyonlu piyasa (protokoldeki kapı düşürülmez); 72 saat UNDERPOWERED.
S dönemi (14 piyasa) bilinen karşı örnek; sonraki saatler ayrı raporlanır.

## Kapanış (21 Eyl 2026 20:37 UTC)
Teslim: RAPOR_FABLE.md, OZET.md, results/, code/, raw/, agents/. Bosona 20 Eyl 12:44 UTC'den 21 Eyl 12:00'ye BTC15dk'da yok; yeni dönem 14:25→20:33 UTC. Donmuş aday/protokol hash'leri değişmedi (results/manifest.json inputs). Recorder PID 1714322 dokunulmadı.
