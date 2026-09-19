---
name: project-actor-breakthrough-tour-20260914
description: Aktör "breakthrough" turu (09-14, Fable): kâr çift marjı DEĞİL tek taraflı envanter (%75-95); kenar sönüyor (+3,4→+1,1¢); 6 açı + hakem 0 kural; kapanış-sonrası, pencere-öncesi gap ve 15m/5m baskınlık kulvarları ölçülüp kapatıldı; sıradaki = tail-gap çok-pazar ön-kayıt
metadata:
  type: project
---

**2026-09-14 (Fable, ultracode).** Paket `data/analysis/pm_actor_breakthrough_20260914_v1/` (REPORT_TR.md,
NEXT_CONTRACT.md, core/*.py, 6 açı klasörü + hakem json'ları, SYNTHESIS.md) ve
`pm_nested_dominance_20260914_v1/` (tape ayrıştırıcı + dominance.py). Canlı emir yok.

**Handoff'un ana sorusu cevaplandı (kesin ayrışım, `core/decompose.py`):** mo-money +$53k: eşleşen çift
+$10k (çift maliyeti 0,984, +1,56¢/çift), tek taraflı +$50,6k (+4,74¢/pay GA[+2,4;+7,1], 0,544'te %59 kazanma,
payların %45'i). bosona +$48k: +$16,5k / +$36,3k (+3,68¢). Saf MM wb27b: çift +$98k / tek taraflı −$98k → 0.
→ Aktörler çift tamamlamıyor; kenar YÖN. "İki tarafı <1,00 doldur" yanlış çerçeve.
**Sönme:** yarılar +3,35→+1,12 / +3,57→+1,02; mint akışı (%87) 2. yarı +0,4-0,9¢; aynı-token satış (%12) +2,5-5,7.
**Hücre içi seçim:** her zaman×fiyat hücresinde aktör pop'u 3-12¢ geçiyor. Perp agresör akışı yeni korelat
(aktör ilk dakika +578k$ vs pop −19k$) ama pop'a koşullanınca ≤+0,7¢.
**6 açı + 2 hakem/kural:** hiçbir aday kural hayatta değil (ileri bakış, sonuç-koşullu seçim, survivor, en iyi 3
gün). Alım-tek davranış 2.447 cüzdanda kenar 0. open_prior ajanı gap işaretini ters okudu, bir hakem ters
rakamı onayladı → ajan yön iddiasını kendin doğrula (lessons 09-14).
**Kapatılan yeni kulvarlar:** (1) kapanış-sonrası kesinlik: 180 uyuşmazlık penceresinde piyasa ≤5 sn'de
çözüyor, kazanan ucuza alınmıyor (0 pay); (2) pencere-öncesi oluşan referans: t=−10 tahmini gap piyasada
fiyatlı (0,615 vs 0,634); (3) 15m vs 3. 5m baskınlık sınırı (Up15≥Up5, d>0): 40 çift/5 coin, ihlal %0-2,
orta senaryo doğru fiyatlı; kaymalar son dakika (15m 0,99'da) = düz 5m yön görüşü.
**Zayıf iz:** açılış |gap|≥8bp'de favori ~8¢ ucuz (108 pencere, GA sıfıra değiyor) → NEXT_CONTRACT.md:
çok-pazar tape'te 5 coin×(5m,15m), |gap|≥8/12bp, t∈[S+1,S+5] favori taker (ask≤0,80) + maker kolu,
25 pay; kapı ≥300 pencere, gün-kümeli GA>0, ex-top3>0, iki yarı>0. Geçmezse kulvar kapanır.
**Tuzaklar:** SETTLEMENT_DEFS ref/twap_240_300 = BINANCE (ref_spot0 = Binance S−1); Chainlink est ile
karıştırma 2,1bp baz (p95 10,5) → isabet %95→%85. Blok-saatli t_rel_s>300 ≠ kapanış sonrası.
**Durum:** aktör-kopya kulvarı PARK. Yeniden açma: Londra ms'de aktör emri kimlikli görülebilirse
(tailgating) veya Eylül aktör kenarı ≥+2¢'e dönerse. İlgili: [[project-pm-late-window-liquidation-20260914]],
[[project-operator-a-maker-policy-fable-20260910]], [[project-disagreement-falsification-20260913]].


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🧩 AKTÖR BREAKTHROUGH TURU (09-14, Fable): kâr çift marjı DEĞİL tek taraflı yön envanteri (%75-95, +4,7¢ @0,544 %59); kenar sönüyor +3,4→+1,1¢; 6 açı+hakem 0 kural; kapanış-sonrası/pencere-öncesi gap/15m-5m baskınlık kulvarları ölçülüp KAPATILDI; SETTLEMENT_DEFS ref = Binance tuzağı; sıradaki = tail-gap çok-pazar ön-kayıt (NEXT_CONTRACT.md)](project_actor_breakthrough_tour_20260914.md)
