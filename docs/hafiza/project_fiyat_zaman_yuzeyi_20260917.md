---
name: project-fiyat-zaman-yuzeyi-20260917
description: Hucre kalitesi ONGORULEBILIR ve sinyal tamamen FIYAT x PENCERE ANI yuzeyinde; donem-kararli harita cikarildi
metadata:
  type: project
---

`data/analysis/pm_hucre_secimi_20260917_v1/` — 546.339 hucre ozellik tablosu
(19 gun, sizintisiz: her ozellik hucrenin ILK dolumundan ONCEKI veriden).

## MODEL OOS CALISTI
Zaman bolmeli (egitim 11 gun / dogrulama 4 / TEST 4 gun hic gorulmedi):
| dilim | TEST kenari |
|---|---|
| en iyi %10 | **+3,43** |
| en iyi %25 | +2,31 |
| TUMU | -0,09 |
| en kotu %10 | -3,30 |
| (aktorlu hucreler) | +0,11 |

## AMA SINYAL TAMAMEN px x t'DE
| model | en iyi %10 (TEST) |
|---|---|
| 10 ozellikli TAM | +3,58 |
| **px + t (iki ozellik)** | **+5,73** |
| yalniz px | +1,77 |
Diger 8 ozellik (akis dengesi, momentum, hacim, seviye sayisi...) KATKI YOK,
hatta zarar veriyor. Kara kutuya gerek yok — YUZEY okunabilir.

## DONEM-KARARLI YUZEY (ilk yari 08-14..22 / ikinci yari 08-23..09-01, ikisinde de >+1,0)
| fiyat | t | n | ort kenar |
|---|---|---|---|
| 0,55-0,70 | 255-301 | 1.042 | **+7,68** |
| 0,70-0,85 | 255-301 | 2.776 | **+6,85** |
| 0,55-0,70 | 210-255 | 4.010 | +5,89 |
| **0,15-0,30** | **-60..30** | 13.779 | **+4,42** |
| 0,70-0,85 | 210-255 | 8.550 | +2,73 |
| 0,15-0,30 | 30-90 | 24.671 | +2,27 |
| 0,00-0,15 | 30-90 | 6.943 | +2,23 |
| 0,30-0,45 | -60..30 | 54.336 | +1,11 |

KARARLI NEGATIF de var: 0,30-0,45 @ t=210-255 (-11,5), 0,15-0,30 @ 255+ (-5,4),
0,70-0,85 @ t<90 (-3,7). Yani yuzey iki yonlu bilgi veriyor.

IKI AILE:
1. GEC PENCERE FAVORI (0,55-0,85, t>=210): bilinen aile;
   [[project-pm-late-window-liquidation-20260914]] ve TWAP kulvari ayni yer.
2. **ERKEN PENCERE UCUZ TARAF (0,00-0,30, t<90): BIZIM ICIN YENI.** +2,2..+4,4.

## ZORUNLU UYARI — BU HENUZ KURAL DEGIL
Yuzey HUCRE duzeyinde, GERCEKLESMIS dolumlar uzerinden. Icermedigi iki sey:
(a) kuyruk pozisyonu, (b) dolum-duzeyi ters secim.
**TWAP kulvari tam burada oldu:** hucre kenari +6,40 iken canli dolumlar
ters secilmis cikti ve -$4,25 verdi ([[project-twap-canli-pilot-sonuc-20260917]]).
Bu haritanin da ayni sinavdan gecmesi gerekir. Once ERKEN-UCUZ ailesinde
durust kuyruk motoruyla dolum simulasyonu.

## FIYAT-ESLESTIRILMIS KONTROL (TEST donemi) — CERCEVEYI DUZELTIYOR
| px kovasi | modelin ust %10'u | geri kalan | FARK |
|---|---|---|---|
| 0,00-0,20 | +1,33 | **+1,62** | **-0,29** |
| 0,20-0,35 | +5,50 | +2,22 | +3,27 |
| 0,35-0,50 | +3,29 | +0,33 | +2,96 |
| 0,50-0,65 | +2,46 | -2,26 | +4,72 |
| **0,65-0,80** | **+6,01** | -3,96 | **+9,97** |
| 0,80-1,01 | +0,21 | -0,91 | +1,13 |

**IKI AYRI OLGU, KARISTIRILMAMALI:**
1. **UCUZ TARAF (px<0,20): KOSULSUZ kalibrasyon sapmasi.** Kalabalik orada
   secim yapmadan +1,62 kazaniyor; MODEL KATKI YAPMIYOR (-0,29).
   Yani "erken-ucuz ailesi YENI bir SECIM bulgusu" DEGIL — basit ve eskiden beri
   oradaki bir sapma. Neden arbitraj edilmedigi ayri soru (muhtemelen dolum
   duzeyinde ters secim).
2. **PAHALI TARAF (px 0,50-0,80): SECIM GEREKTIRIYOR.** Secimsiz -2,3..-4,0,
   modelle +2,5..+6,0. Modelin tum degeri BURADA.
   Ama burasi TWAP canli pilotunun ters secimden oldugu bolge
   ([[project-twap-canli-pilot-sonuc-20260917]]).

DUZELTME: onceki notta "erken-ucuz ailesi BIZIM ICIN YENI (secim bulgusu)"
dedim; fiyat-eslestirilmis kontrol bunu CURUTTU. O bant kosulsuz, secim degil.
