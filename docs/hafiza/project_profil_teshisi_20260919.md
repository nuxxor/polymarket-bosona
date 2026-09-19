---
name: project-profil-teshisi-20260919
description: Canlı −1.85 bir uygulama hatası değil — zincirde bizim tam profilimiz −2.47 yapıyor; bandımız doğru (+0.77), zamanlamamız yanlıştı (t<60 −0.65 vs t150+ +0.31)
metadata:
  type: project
---

# PROFİL TEŞHİSİ (2026-09-19) — "neden kaybediyoruz" cevaplandı

Yöntem: zincir defterinde (19 gün, 473.070 cüzdan-pencere, yalnız ≤0,40 alan
sınıf) BİZİM TAM PROFİLİMİZE uyan kayıtları bul.

## SONUÇ
```
bizim hucre (5-9 pay klip + hepsi t<60 + ort fiyat 0,25-0,33):
   -2,47 kr/pay [-6,11,+0,85]   9.784 kayit   cift %1
canli sonucumuz: -1,85
```
**Örtüşüyor → bot doğru çalışıyor, YANLIŞ ŞEYİ doğru yapıyor.**

## HANGİ BOYUT
```
SON DOLUM ZAMANI          DOLUM SAYISI           ORTALAMA FIYAT
  t<60 (BIZ)   -0,65        1 dolum   -0,77        <0,15       -0,12
  t60-150      -1,73        2-3       +0,51        0,15-0,25   -0,48
  t150+        +0,31        4-6       +0,01        0,25-0,33   +0,77  <- BIZ, DOGRU
                                                    0,33-0,40   -1,41
MEDYAN BOY: 1-4 -0,49 | 5-9 (BIZ) -0,42 | 10-24 -0,32 | 25+ +0,21
```
**Bandımız doğru, zamanlamamız yanlıştı.** `GEC_KES=60` kararı geri alındı (200).

## KRİTİK METODOLOJİ DERSİ (playbook #58)
Aynı veri, iki farklı birim, ZIT cevap:
- **Dolum düzeyi:** "0,20-0,40 bandında t<60 kenarı **+2,34**" → GEC_KES=60 yaptım
- **Cüzdan-pencere düzeyi:** "işi t<60'ta biten katılımcı **−0,65**" → geri aldım

Strateji kararı **cüzdan-pencere** biriminde verilir; biz o birimde çalışıyoruz.
Dolum düzeyi ölçümü "hangi dolum iyi" der, "hangi politika iyi" DEMEZ.

## AYRICA ÇÜRÜYEN
"İlk bacağı paraya yakın al, ikinci bacağı ucuz al" (bosona'nın 0,53→0,30 ile
0,64 çift kurduğu pencereden çıkardığım hipotez): **ÇÜRÜDÜ.**
İlk bacak fiyatına göre: 0,20-0,35 → **+0,64** [+0,30,+1,07] (en iyi);
0,45-0,55 → −0,18; 0,65-0,80 → −0,49. Ucuz ilk bacak kazanıyor.
bosona'nın o penceresi istisnaydı; aynı gün 13:50'de Down'ı 0,60→0,83 kovalayıp
çifti 1,44'e kurdu ve kaybetti. **Onun kârı bu davranıştan RAĞMEN geliyor.**

## TAVAN KARARI
```
yalniz <=0,40 (BIZ):  cift % 9,2 | cift mal 0,426 | +0,01 kr/pay
0,40 ustu de alan  :  cift %59,9 | cift mal 1,002 | -0,03 kr/pay
```
İkisi de sıfır. Tavan PnL'i değiştirmiyor; kaldırmaya gerek yok.

## ÇİFT MALİYETİ (kısmen totolojik ama yön net)
0,00-0,70 → +16,28 | 0,70-0,85 → +6,29 | 0,95-1,00 → +0,45 | 1,10+ → −8,18

İlgili: [[project-fiyat-zaman-haritasi-20260919]], [[project-gpt-ultra-denetim-20260919]]
