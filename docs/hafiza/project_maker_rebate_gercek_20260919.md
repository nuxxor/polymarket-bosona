---
name: project-maker-rebate-gercek-20260919
description: Maker fee rebate GERÇEKTEN ödeniyor — $13/24sa, 4.820 pay üzerinden 0.27 kr/pay; kol A'nın beklenen kenarının %28'i ve VARYANSSIZ
metadata:
  type: project
---

# MAKER REBATE ÖDENİYOR — 0,27 kr/pay (2026-09-19)

Operatör bildirdi, hesaptan doğrulandı: **$13 maker rebate yattı, 24 saatlik dönem.**
Aynı dönemdeki gerçek borsa hacmi (tüm BUY dolumları, data-api `takerOnly=false`):
**4.820 pay / $1.678 notional** → **0,27 kr/pay**.

Bu, dokümante edilen tavanla uyumlu (ücret havuzunun %20'si, p=0,5'te azami 0,35 kr/pay,
bizim 0,10-0,40 bandımızda 0,13-0,34). **project_pm_odul_rebate_gercekleri_20260917'deki
0,35 tavanı DOĞRUYMUŞ.** İlk hesabımda 0,71 demiştim — yalnız botun logladığı dolumlara
bakmıştım (1.830 pay), borsa 4.820 gösteriyor.

## AYRIM
- **Likidite ödülü** BTC 5m'de hâlâ FONLANMIYOR (`clobRewards = null`, `rewardsMinSize=50`).
- **Maker ücret rebate'i** AYRI bir program ve ÖDENİYOR. İkisini karıştırma.

## EKONOMİYE ETKİSİ
```
                          islem kenari   rebate   TOPLAM
kol A (olculen bant)         +0,70       +0,27    +0,97
kol B (kapali)               -1,05       +0,27    -0,78   <- hala negatif, kapali kalsin
```
Kol A tam gün: 17,5 pay/pencere × 288 pencere = ~5.040 pay/gün → **~$13,6/gün rebate.**

**Rebate VARYANSSIZ.** İşlem kenarı +0,70 ± çok; rebate +0,27 ± sıfır. Yani beklenen
toplamın %28'i risksiz. Ön kayıttaki +1,0 beklentisi bu ikisinin toplamıyla örtüşüyor.

## HİÇ OPTİMİZE EDİLMEDİ — açık soru
- Rebate hacimle DOĞRUSAL mı ölçekleniyor?
- Boy/makas eşiği var mı (likidite ödülünün 50 pay eşiği gibi)?
- İşlem kenarı ~0 olan bir bantta bile +0,27 varsa, **hacim farmlamak** kârlı mı?
Bunlar GPT Ultra brief'inde 3. öncelik olarak verildi.

İlgili: [[project-pm-odul-rebate-gercekleri-20260917]], [[project-fiyat-zaman-haritasi-20260919]]
