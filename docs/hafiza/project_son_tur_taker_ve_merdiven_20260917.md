---
name: project-son-tur-taker-ve-merdiven-20260917
description: Taker adli inceleme + merdiven testi — ikisi de kapali; geriye tek soru kaldi ve yalniz KENDI canli dolumlarimizla cevaplanir
metadata:
  type: project
---

Operator uyarisi (hakli): "dolmayan emirlere takilma, para DOLAN emirlerden geliyor."
Buna gore dolan emirler uzerinden tam tur atildi.

## 1) TAKER ADLI INCELEME (bosona, 09-15, 158 islem)
Tape donemimde bosona +$1.740 kazanmis; **$1.570'i (%90) TAKER**.
138 islem BTC (hacmin %95,6'si), odedigi 50,9 kr, isabet %64,4, **+12,12 kr/pay**.
Alt coinler ZARAR (-11,81).
- **BTC momentumu ACIKLAMIYOR**: yon uyumu 3/5/10/20/30/60 sn geri bakista
  %37-56 (yani ~yazi-tura). Momentum-uyumlu +6,80 / uyumsuz +1,76 — zayif.
- **AMA BU TEK GUN.** 19 gunluk API olcumu taker icin +0,64 GA[-0,92,+2,31].
  09-15 istisnai bir gun; kalici kenar degil.
- Uzun vadede (zincir, 19 gun) asil motor MAKER: 1,75M pay x +1,95 = ~$34k,
  taker 366k x +3,63 = ~$13k.

## 2) MERDIVEN TESTI — YAPISAL FARK DEGILMIS
Simdiye kadarki tum testler 1 pencere=1 fiyat=1 emirdi. bosona her seviyeye,
iki tarafa, gun boyu kotasyon veriyor (430 pay/pencere). Simule edildi:
| kural | pay/pencere | kr/pay | GA |
|---|---|---|---|
| tek emir (en iyi bid) | 8 | -7,77 | [-8,59,-5,86] |
| merdiven 0,30-0,70 | 108 | -9,87 | [-11,15,-5,61] |
| merdiven 0,10-0,90 | 202 | -7,31 | [-8,12,-5,39] |
| merdiven 0,02-0,98 | 222 | -6,94 | [-7,67,-5,09] |
0/4 gun artida, hepsi. **Genislik cevap DEGIL.**

## 3) 15dk/4saat PAZARLARI — MEKANIZMA VAR, KENAR YOK
15dk settlement kurali 277/277 dogrulandi. Kismi-TWAP sinyali son 40/30/20/10
sn'de **235-263 pencerede SIFIR hata**. Ama piyasa yine 0,99'da
(kesin tarafin hacminin %83-91'i >0,98). 5dk ile AYNI duvar.

## GERIYE KALAN TEK SORU
Celiski: kalabaligin GERCEK dolumlari iyi hucrelerde derin kuyrukta bile +0,91;
bizim SIMULE ettigimiz her yeni emir -7. Ikisini uzlastiran tek sey kuyruk
varsayimi ("gozlenen boyutun tamami onumuzde").
Bu varsayim yalnizca KENDI CANLI DOLUMLARIMIZLA sinanabilir.
Tek canli testimiz (TWAP, 8 saat, 5 dolum) simulasyonu DOGRULADI (-$4,25)
ama 5 dolum hicbir sey ifade etmez.
=> Karar: genis, kucuk-klipli, uzun sureli canli maker ile KENDI dolum
   kalitemizi olcmek. Maliyet simulasyon hakliysa ~$180/gun (tek emir, 5 pay).
