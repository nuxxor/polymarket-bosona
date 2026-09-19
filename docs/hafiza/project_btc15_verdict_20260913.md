---
name: btc15-verdict-20260913
description: BTC15 üç soruluk karar analizi — sızıntı 0,70-0,80 bandı; bozulma = kalibrasyon kayması (+2,8 → −6,3 puan, marj sadece 4 puandı, z=1,95 p=0,051); kurtarma kuralı "streak gate + giriş<0,70" bozuk dönemde OOS +385 sanal (~+$62/gün) ama %90 GA sıfıra değiyor → para koymadan yerel gölge testi, 2 hafta, ön-kayıtlı tetik
type: project
---

# BTC15 karar raporu — 2026-09-13 (yerel, sunucu kapalı)

Paket: `data/analysis/btc15_verdict_20260913_v1/` (REPORT_TR.md, RESULT.txt, build/analyze/rescue/oos.py).
Veri: yerel yedekteki iki kamu gölgesi birleştirildi, 1.672 pencere / 415 seçim, 22 Ağu-12 Eyl.

1. **Fiyat haritası:** başabaş ≈ giriş fiyatı. 0,70-0,80 bandı yapısal eksi (isabet %72 vs başabaş %74,6,
   −437 toplam); eğitim döneminde de en zayıf banttı (+3,0 fazla, +16) → filtre veriye uydurma değil.
   Diğer bantlar artı: 0,55-0,62 +6,9 puan, 0,62-0,70 +7,2 puan, 0,80+ +6,7 puan.
2. **Rejim:** isabet 75,7% → 70,6% → 62,9% (Ağu sonu / 1-7 Eyl / 8-12 Eyl) GİRDİLER SABİTKEN
   (giriş 0,645-0,655, olasılık 0,69-0,70, edge 0,039-0,041, PM spread 0,010). Mekanizma = kalibrasyon
   kayması: model %69 diyor, gerçek %72,5'ten %62,9'a düştü (sapma +2,8 → −6,3 puan). Marj ~4 puandı.
   İki dönem farkı z=1,95 p=0,051 (sınırda, şans tam elenmiyor).
3. **Kurtarma (dürüst OOS: kural eski dönemden, test 8-12 Eyl):** filtresiz −676 | gate −> +44 |
   fiyat<0,70 tek başına −203 | **gate + fiyat<0,70 → +385 sanal (52 işlem, %73,1 isabet, 3/5 gün artı,
   gün-blok %90 [−26,+804])**. Gerçek kalibrasyon 0,80 ile ≈ +$308 / 5 gün ≈ +$62/gün, ~10 işlem/gün.

**Karar:** para koymadan ileri test. İki kamu gölgesi hiçbir anahtar istemiyor (gizli env varsa çalışmayı
REDDEDİYOR), yalnız Polymarket gamma+CLOB ws ve Predict graphql+ws dinliyor → bu bilgisayarda bedava koşar.
Tetik (ön-kayıt): 2 hafta, ≥100 filtreli pencere, gün-blok %90 GA sıfırın üstünde, isabet başabaş+4 puan,
günlerin ≥%60'ı artı. Tutmazsa kulvar KALICI kapanır.


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [⚖️ BTC15 KARAR (09-13): sızıntı 0,70-0,80 bandı; bozulma kalibrasyon kayması (marj 4 puan, kayma 6 puan); kurtarma 'gate + giriş<0,70' bozuk dönemde OOS +385 sanal ama GA sıfıra değiyor → bedava yerel gölge testi 2 hafta, tetik tutmazsa kalıcı kapanış](project_btc15_verdict_20260913.md)
