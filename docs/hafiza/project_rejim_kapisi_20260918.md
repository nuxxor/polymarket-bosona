---
name: project-rejim-kapisi-20260918
description: Oynaklık kapısı (önceki pencere >=16.4 bps -> A, altı -> B) 18 Eylül 18:13 UTC'de canlıya alındı; yön üç bağımsız dilimde tutuyor ama güven aralığı sıfırı kapsıyor
metadata:
  type: project
---

# REJİM KAPISI — canlı, 2026-09-18 18:13 UTC

`ab.py` içinde `KAPI_ACIK=True`, `ESIK_BPS=16.4`. Pencere açılışında Binance
futures'tan önceki 5 dakikanın 1dk mumları çekilir, salınım baz puan olarak
hesaplanır: `>=16.4 -> A kolu (derin merdiven)`, `<16.4 -> B kolu (mid-takipli)`.
Ölçüm alınamazsa eski rastgele atamaya düşer (`KAPI_DUSTU`), ticaret durmaz.

## Neden bu eksen
- Oynaklık pencereden pencereye KALICI: ardışık korelasyon **rho +0.716**,
  üst->üst %79, alt->alt %78 (şans %50), n=94 ardışık pencere. ÖNDEN BİLİNEBİLİR.
- "Trend mi savrulma mı" ekseni kalıcı DEĞİL: **rho −0.07**, %43/%45.
  A'nın en büyük ayrışması orada (savrulma +6.61 / trend −11.86 kr/pay) ama
  öngörülemediği için kapıya SOKULMADI. Bu ayrım önemli: en güçlü sinyal
  ticarete dönüşmeyebilir.

## Kanıt (üç bağımsız dilim, yön hep aynı)
| dilim | A oynak | A sakin |
|---|---|---|
| 87 pencere, tüm gün, bookticker ölçüsü | +1.72 | −6.09 |
| aynı, Binance kline ölçüsü (rho 0.997) | +1.72 | −6.09 |
| son 3 saat, bağımsız dilim | +5.58 | −6.07 |

## SINIRLARI — körü körüne inanma
- Tek günün verisi. Eşik **medyandan** seçildi. 2 eksen × 2 kol tarandı
  (çoklu karşılaştırma riski gerçek).
- Kapılı karmanın güven aralığı **sıfırı kapsıyor**: +$4.33, GA95[−35,+44].
- Kapının **B yarısı kırılgan**: ölçüyü bookticker'dan kline'a çevirince
  B-sakin +1.57'den −0.15'e düştü. Sadece **A yarısı** iki ölçüde de aynı.
  Beklenti buna göre kurulmalı: kazanç A'yı sakin pencereden çekmekten gelir.
- Kapının yakalayamadığı durum: oynak AMA trend pencere. 18:35 ve 18:40
  pencereleri tam buydu, ikisinde de çift kurulamadı.

Ön kayıt: `data/analysis/pm_merdiven_ab_20260918_v5/ONKAYIT_REJIM_KAPISI.md`
Değerlendirme: kapı sonrası >=40 pencere biriktiğinde. Hipotezi doğuran veriyle
test etmek yasak.

İlgili: [[project-cift-ekonomisi-a-vs-b-20260918]], [[project-olcek-kaniti-20260918]]
