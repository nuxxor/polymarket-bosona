---
name: project_queue_age_scale_20260914
description: BTC5m aktör 'kuyruk yaşı/ölçek/yerleşim zamanı' turu (09-14): 18¢ fark kalibrasyon artefaktı; akış kuralı düzeltmesi (%84 tamamlayıcı token); erken yerleşim işareti çevirmiyor; mekanizma = dolum-sonrası sürüklenme; ML etiketi bilgili/bilgisiz dalga
metadata:
  type: project
---

Paket: `data/analysis/pm_queue_age_scale_20260914_v1/` (CONTRACT, REPORT_TR, RESULTS.json, replay_fixed.py, loader.py).
Handoff: `data/analysis/HANDOFF_FABLE_20260914.md` Bölüm 2-TER.

- "Kaybeden tarafta aktör 0,289 / biz 0,469" = sonuca koşullu ortalama, edge değil. Pay-ağırlıklı: aktör 28g +1,91¢/pay
  (gün-kümeli GA [+1,11;+2,76], 3 cüzdanın üçü de artı; taker kolu da ücret sonrası +2…+3,5¢); bizim touch −2,46¢.
- Motor: engine_fix + akış kuralı: maker bid'i dolduran akışın %84'ü TAMAMLAYICI token'daki taker alışı; run.py saymıyordu.
  Yeniden üretim T0 −5,4→−2,5; D45 +3,3 (GA sıfırı içerir). Yenileme/chase −1,4: tazelik çözüm değil.
- Yerleşim zamanı: Londra kaydı ve tape.py S−300'de abone → T−1 saat replay edilemez. Kalıcılık: t=60 derinliğinin
  T−299'dan beri duran kısmı %5-9 → T−299 vekil. T−299 touch/sığ −1,9…−2,2¢; DEEP(bb−30…−45) +3,1¢ (2.239 pay, ex3 +$23, GA [−1,8;+7,7]).
- Kuyruk yaşı ÇÜRÜDÜ (seviye yaşı medyan 12 s, eski seviyeler 0¢, %48 tam süpürme). Ölçek ÇÜRÜDÜ (>8 fiyat −10,4¢).
- Mekanizma: dolum-sonrası 60 s sürüklenme: bizim touch −2,8¢, DEEP +2,25¢, aktör ≈0. Londra'da aktör kârının tamamı
  WS print'ine bağlanamayan %14 payda (972 dolum; 241'inde PC seviye düşüşü var).
- ML etiketi: dalga bilgili (Binance ≥1 bp/5 s) → iptal/al; bilgisiz → beklet/derin kota. Sonraki: dalga-koşullu replay;
  tape.py'ye ≥2 saat erken abonelik; kayıp print altkümesini zincirle doğrula.

**Why:** 8 hipotez kontrolsüz "bulgu" olmuştu; bu turda kontrol önce yazıldı. **How to apply:** yeni replay'de
replay_fixed.py + loader.py kullan; süpürme için t−200 ms durumu; tx eşlemesinde fiyat filtresi koyma.


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🧭 KUYRUK YAŞI/ÖLÇEK/YERLEŞİM ZAMANI (09-14): '18¢ fark' kalibrasyon artefaktı (aktör 28g +1,9¢, biz touch −2,5¢); akış kuralı düzeltmesi (%84 tamamlayıcı token); erken yerleşim işareti çevirmiyor, DEEP@T−299 +3,1¢ GA≥0 içerir; kuyruk yaşı+ölçek ÇÜRÜDÜ; mekanizma dolum-sonrası sürüklenme; ML etiketi bilgili/bilgisiz dalga](project_queue_age_scale_20260914.md)
