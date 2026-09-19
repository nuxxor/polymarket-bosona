---
name: project-twap-geri-uzatma-kapandi-20260917
description: TWAP kilidini t=240 oncesine uzatma denendi — sinyal VAR ama piyasa t=180'den beri 0,99 veriyor; kenar tam t=240'ta doguyor
metadata:
  type: project
---

Fikir: TWAP60 purussuz (60 sn hareketli ortalama) -> TWAP60(S+300) ile
TWAP60(S+240) korelasyonlu -> t=240'tan ONCE de mekanik bilgi olabilir.
Skor: beklenen hedef = (bilinen + n_kal*P_t)/60, std kalan sureye gore olcekli.

## SINYAL GERCEKTEN ERKEN VAR (Agustos, 4.430 pencere)
| t | \|z\|>=3 pencere | hata |
|---|---|---|
| 120 | 176 | %4,55 |
| 180 | 774 | %4,01 |
| 200 | 1.165 | %3,00 |
| 220 | 1.546 | %1,62 |
| 240 | 2.116 | %0,66 |
| 262 | 2.531 | %0,20 |

## AMA PIYASA DAHA IYI BILIYOR -> KENAR YOK
Kesin tarafin MEDYAN islem fiyati **t=180'den itibaren 0,990** (hic degismiyor).
Basabas hata = %1,0 her t'de.

| t | hata | basabas | PAY |
|---|---|---|---|
| 180 | %4,02 | %1,0 | **-3,0** |
| 200 | %3,01 | %1,0 | -2,0 |
| 220 | %1,62 | %1,0 | -0,6 |
| **240** | %0,66 | %1,0 | **+0,3** |
| 250 | %0,35 | %1,0 | +0,6 |
| 262 | %0,20 | %1,0 | +0,8 |

**Kenar tam t=240'ta doguyor** — settlement penceresi [S+240,S+300]'un actigi an.
Daha erken girmek ISE YARAMIYOR: piyasa 0,99'da, biz henuz yeterince emin degiliz.

## SONUC
Bugunku kural (t>=250, z>=3, bid 0,97) cikarilabilir olanin SINIRINDA.
Geriye uzatma kulvari KAPANDI. TWAP ailesinden cikacak baska sey yok gibi.
Kalan buyuk soru hala AKTORLERIN ILK 240 SANIYESI ([[project-zincir-kesin-19gun-rol-20260917]]:
maker +1,95/+2,26 kr/pay, bizim ayni politika simulasyonumuz -8).

Ilgili: [[project-gec-pencere-twap-kilitlenme-20260917]], [[project-olcekli-esik-ve-fiyat-tavani-20260917]]


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🔚 TWAP GERİYE UZATMA KAPANDI (09-17): sinyal t=120den itibaren var (t=220de %1,62 hata) AMA kesin tarafın medyan işlem fiyatı **t=180den beri 0,990** → başabaş %1,0, kenar ancak t=240ta doğuyor (+0,3 puan). Daha erken girmek işe yaramıyor. Bugünkü kural çıkarılabilir olanın SINIRINDA; TWAP ailesi tükendi](project_twap_geri_uzatma_kapandi_20260917.md)
