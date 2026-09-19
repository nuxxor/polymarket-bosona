---
name: project-ucuz-bant-deney-sonucu-20260919
description: Ucuz bant canlı deneyi 142/300'de bütçe projeksiyonu nedeniyle sonlandı — −1.85 kr/pay, BELİRSİZ (sıfırdan 0.82σ); replay modelinin canlı doğrulaması sağlandı
metadata:
  type: project
---

# UCUZ BANT DENEYİ — SONUÇ (2026-09-19)

Ön kayıt: `data/analysis/pm_merdiven_ab_20260918_v5/ONKAYIT_UCUZ_BANT_20260919.md`
Konfigürasyon: yalnız kol A, ızgara [0,40…0,03], klip 5, **tavan 0,40**, kol B KAPALI.

## SONUÇ: BELİRSİZ (erken sonlandı)
```
142 / 300 pencere | 2.074 pay | -$38,35 | -1,85 kr/pay
sifirdan 0,82 sigma  -> istatistiksel olarak SIFIRDAN AYIRT EDILEMIYOR
onkayit beklentisi +1,00'in 1,27 sigma altinda
borsa PnL -51,11 = kesici butcesinin %51'i, 142 pencerede
```
**Neden erken bitti:** bot 12 saatlik MAX_SAAT sınırına takılıp kendi durdu.
O anda projeksiyon 300 pencerede ~−$108 gösteriyordu, kesici −$100. Devam
kararı verilmedi. **"Çürüdü" DEĞİL, "bu bütçeyle tamamlanamadı".**

## YAPISAL BULGU (örneklemden bağımsız, net)
```
CIFT kurulan  : %41 pencere  +15,40 kr/pay
TEK tarafli   : %59 pencere  -25,41 kr/pay
```
Çift kurabildiğimizde ekonomi bosona'nın +1,95'inden çok daha iyi. Eksik olan
tek şey ÇİFT KURMA SIKLIĞI (biz %41, bosona %65). Bu, 19 günlük zincir
verisinden çıkan tabloyla birebir aynı — canlı veri onu doğruladı.

## EN DEĞERLİ ÇIKTI: REPLAY MODELİ DOĞRULANDI
GPT Ultra'nın sabit-akış replay'i mevcut politikayı **−0,645 kr/pay** tahmin
etmişti; canlıda 142 pencerede **−1,85** çıktı. Aynı yön, aynı mertebe.
Bu, o modelin cancel60 için verdiği **+2,061 [+0,468,+3,693]** tahminine
dolaylı güven kazandırıyor — ve replay'i artık ucuz bir ön eleme aracı olarak
kullanabiliriz.

## TAVANIN DOĞRULANMASI
142 pencerede **0,40 üstü dolum SIFIR**. Mekanik olarak çalıştı. Dün ölçülen
"zararın tamamı 0,40 üstünde" bulgusu gereği kol B kapalı kaldı.

## SIRADAKİ
`ONKAYIT_CANCEL60_20260919.md` hazır (kod DEĞİŞTİRİLMEDİ, operatör onayı bekliyor):
`GEC_KES 200→60`, `UCUZ_ESIK 0,25→0,40`. Kesici −60, kontrol noktası 200 pencere,
beklenti +0,5…+1,5 (replay'in +2,06'sı DEĞİL — o gerçek kuyruk önceliğini modellemiyor).

İlgili: [[project-gpt-ultra-denetim-20260919]], [[project-fiyat-zaman-haritasi-20260919]]
