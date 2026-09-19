---
name: project-twap-maker-olcum-20260917
description: TWAP sinyali + MAKER bid olculdu — sinyal hatasi %0,33 (3.062 pencere, 2 donem), basabas %2-7; her dolum kazandi; kapasite belirsiz
metadata:
  type: project
---

Taker tasarimi yapisal olarak calismiyordu ([[project-twap-taker-yapisal-kusur-20260917]]).
MAKER tasarimi durust kuyruk motoruyla olculdu:
`data/analysis/pm_twap_kilit_20260917_v1/maker_test.py`

## 1) SINYAL HATA ORANI — KARAR SAYISI BU
t=262, |mt|>=2bp (TWAP-esdeger):
| donem | kesin pencere | YANLIS | hata | %95 ust sinir |
|---|---|---|---|---|
| Eylul (tape cl) | 541 | 1 | **%0,18** | %0,74 |
| Agustos (Streams) | 2.521 | 9 | **%0,36** | %0,48 |
| **toplam** | **3.062** | **10** | **%0,33** | — |
|mt|>=5bp'de: Agustos 0/1.673, Eylul 0/355.

BASABAS hata orani (bid fiyatina gore): 0,93 -> %7 | 0,95 -> %5 |
0,97 -> %3 | 0,98 -> %2.
**Olculen %0,33 vs en siki basabas %2 = 6x guvenlik payi.** Her bid seviyesi gecer.

## 2) MAKER DOLUM (409 kesin pencere, Eylul, 5 pay klip, kuyrugun ARKASINDA)
| bid | dolum orani | pay | kr/pay | R2 (seviye defterde yok) |
|---|---|---|---|---|
| 0,93 | %2,0 | 40 | +7,00 | %1,2 |
| 0,95 | %2,4 | 50 | +5,00 | %1,7 |
| 0,97 | %3,4 | 70 | +3,00 | %0,5 |
| 0,98 | %5,1 | 105 | +2,00 | %2,4 |
**Her dolum KAZANDI** (kr/pay tam olarak 1-fiyat).
Kuyruk medyani 249-559 pay.

## 3) KAPASITE — BELIRSIZ
Sinirsiz klip (tasmanin TAMAMINI aldigimiz varsayimi): her bid seviyesinde
~$200/gun (0,93'te 2.780 pay/gun x 7kr; 0,98'de 9.614 x 2kr).
5 pay klip ile: gunde 10-26 pay = ~$0,50/gun.
GERCEK deger ikisinin arasinda ve ancak CANLIDA olculur.

## 4) YERLESIM ANI
t=245 -> -24,91 kr/pay (sinyal o kadar erken guvenilmez)
t=250 -> -7,41 | t=255 -> +3,00 | t=262 -> +3,00
**t>=255 guvenli sinir.**

## 5) NEDEN BU MAKER ONCEKILERDEN FARKLI
Onceki tum maker denemelerini TERS SECIM oldurdu (dolum-kosullu kazanma orani
kosulsuzun altinda). Burada sonucu ZATEN BILIYORUZ; dolan emir %99,7 kazanan
tarafta. Ters secim yok. Kalan tek belirsizlik KAPASITE.

Ilgili: [[project-gec-pencere-twap-kilitlenme-20260917]]

## CANLI v2 — z ESIGI (09-17 00:27 UTC)
`data/analysis/pm_twap_taker_20260917_v1/maker.py --live`
Kural: t>=250'den itibaren her saniye z hesapla; **|z|>=3'u ILK gectigi anda**
kesin tarafa 0,97 post-only bid, 5 pay, 297'de iptal. Kesici -15.

ERKEN YERLESIMIN OLCULEN ETKISI (Eylul, defterli):
| kural | pencere | dolum% | pay | kr/pay | yanlis pay |
|---|---|---|---|---|---|
| z>=3, sabit t=262 | 433 | %4,8 | 105 | **-1,76** | 5 |
| z>=3, ilk-kesin t>=242 | 484 | **%25,6** | 620 | +1,39 | 10 |
| z>=4, ilk-kesin t>=242 | 475 | %13,5 | 320 | +1,44 | 5 |
| **z>=3, ilk-kesin t>=250** | 512 | %17,6 | 445 | **+1,88** | 5 |

**Erken yerlesim dolumu 5 KAT artiriyor** (kuyrukta daha uzun beklemek).

## IKI GERI CEKME
1. **"+3,00 kr/pay, her dolum kazandi" 14 DOLUMLUK SANSTI.** Gercek kenar
   **+1,4..+1,9 kr/pay**. 0,97 bid'de tek yanlis dolum 32 dogru dolumu siler;
   sabit t=262 varyanti tek hatayla EKSIYE dusuyor (-1,76).
2. **ZAYIF TERS SECIM ISARETI:** dolumlarin hata orani %1,6 (2/124), sinyalin
   taban hatasi %0,34. Yani doldugumuz anlar sinyalin yanildigi anlara YAKIN —
   piyasa bize kendisi emin olmadiginda satiyor. Henuz olduruсu degil (kar arti)
   ama izlenecek TEK sey bu.

## INTERNET KESINTISI TESTI (gercek, 30 dk)
Bot dogru davrandi: 107 cl_koptu + yeniden baglanma, 15 mutabakat_hata,
ve **`atla_cl_bayat` ile pencereyi ATLADI** (veri 1.735 sn bayat). Kor islem YOK,
yetim emir YOK, acik pozisyon 0. Bayat-veri kapisi calisiyor.


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🟢 TWAP + MAKER ÖLÇÜLDÜ (09-17): sinyal hatası **%0,33** (3.062 pencere/2 dönem, 10 yanlış), başabaş %2-7 → **6x güvenlik payı**; maker bid 409 kesin pencerede %2-5 dolum ve **her dolum kazandı**; t≥255 güvenli sınır (245 = −24,91); kapasite belirsiz: 5 payla ~$0,5/gün, sınırsız klip tavanı ~$200/gün — gerçek değer ancak canlıda. TERS SEÇİM YOK çünkü sonucu biliyoruz](project_twap_maker_olcum_20260917.md)
