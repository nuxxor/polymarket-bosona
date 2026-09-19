---
name: pm-btc15m-strategy-search-20260913
description: Polymarket BTC15m ön-kayıtlı strateji araması — 9.785 pencere/103 gün/7 aile/50 parametre; 46'sı eksi, test şartı (≥200 işlem) karşılanmadı → ADAY YOK, kulvar kapandı. Tek canlı iz momentum devamı 10bp (iki dönem de artı, günde $10-20, GA sıfırı kapsıyor, kapasite yok: en iyi ask medyan 170 pay). Hız sorunu YOK (60 sn geç emir bozmuyor)
type: project
---

# Polymarket BTC15m strateji araması — 2026-09-13 (ön kayıtlı, tek test geçişi)

Paket: `data/analysis/pm_btc15m_strategy_search_20260913_v1/` (PREREGISTRATION.md sha edef0130,
build_panel.py, evaluate.py, test_pass.py, TRAIN_RESULT.txt, TEST_RESULT.txt, DEPTH_CHECK.txt,
LATENCY_CHECK.txt, REPORT_TR.md, panel/ 103 gün).

Veri: Telonex `telonex_polymarket_btc15m_crossvenue_20260825` (65 GB, 26 Nis-24 Ağu, 25 seviye defter
+ kotasyon) × Binance 250 ms `c3_binance_futures_raw_250ms_lag105_v2` (18 Ara-6 Ağu). Kesişim 103 gün,
9.785 pencere. Eğitim 26 Nis-30 Haz, test 1 Tem-6 Ağu.

**Sonuç: ADAY YOK.** 50 parametrenin 46'sı eksi; kör kontroller de eksi (hep Up −3,91c/pay).
Eğitim şartını yalnız momentum devamı 20bp geçti (t=60s +9,96c/pay GA [+373,+1294]); testte 14 işlem
(şart ≥200) → düştü. Ortalamaya dönüş kesin eksi (−3..−13c), geç favori/zayıf eksi, bayat kotasyon
sinyali YOK (Polymarket kotasyonları hep taze).

**Tek canlı iz:** momentum devamı t=60s 10bp — eğitim +$557/393 işlem, test +$633/124, birleşik
+$1.189/517 (günde $13,8), 49/86 gün artı, ama hiçbir GA sıfırın üstünde değil.
- HIZ SORUNU YOK: emir 60 sn geç verilse sonuç bozulmuyor (10bp'de +$16,4/gün'e çıkıyor); sinyal
  sonrası ask ortalama −0,64c hareket ediyor. Yani dakikalar süren fiyatlama tembelliği, yarış değil.
- KAPASİTE YOK: sinyal anında en iyi ask medyan 170 pay; 100 payda 2,3c/pay, 300 payda 1,4c/pay,
  1000 payda işlem kalmıyor. Tavan ~$10-20/gün = $300-600/ay.

Kalıcı varlık: temiz panel + boru hattı (bir gün ≈ 20 sn). Yeni fikir çıkarsa aynı disiplinle
saatler içinde test edilir. Ön kayıt gereği parametre taraması genişletilmedi, yeni aile eklenmedi.


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🔚 PM BTC15m STRATEJİ ARAMASI (09-13): 9.785 pencere/7 aile/50 parametre ön-kayıtlı → ADAY YOK; tek iz momentum 10bp günde $10-20 ama GA sıfırı kapsıyor ve kapasite yok (ask medyan 170 pay); hız sorunu YOK](project_pm_btc15m_strategy_search_20260913.md)
