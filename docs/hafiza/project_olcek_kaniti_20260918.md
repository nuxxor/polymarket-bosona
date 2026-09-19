---
name: project-olcek-kaniti-20260918
description: Aynı pencerede çift maliyetimiz bosona'dan İYİ (0.473 vs 0.525) ama 40 pay vs 404 pay — kaybettiğimiz şey strateji değil ölçek; ayrıca kamu akışı parça parça dolduğu için erken okuma yanıltıyor
metadata:
  type: project
---

# ÖLÇEK KANITI + KAMU AKIŞI METODOLOJİSİ (2026-09-18 yakın izleme)

## En temiz tek satır (S=1789756200, vol 25.5 bps, aynı pencere)
```
BIZ      40 pay | cift  30@0.473 | essiz  10 Down@0.166 | +16.25$ (+40.6 kr/pay)
BOSONA  404 pay | cift 198@0.525 | essiz 206 Down@0.100 | +232.18$ (+57.5 kr/pay)
```
**Çift maliyetinde ONU GEÇTİK** (0.473 < 0.525). Fark ölçekte: 10 kat pay.
Mekanizma doğru çalıştığında kuruş/pay yarışabiliyoruz. Bu, "giriş fiyatını
eşitleyebiliyoruz, markout'u eşitleyemiyoruz" bulgusunun yanındaki ikinci sütun.

Ölçek hipotezi (TEST EDİLMEDİ): bosona 100-500 pay bekletiyor, biz 5.
5 paylık emir her süpürmede gider -> kötü markout, az hacim. Test: klip 5->25,
markout'u yeniden ölç. Bütçe engeli: tabana ~$28, 3-4 pencere sürer.

## ÇÜRÜYEN HİPOTEZ: "ölçekli ızgara"
İddiam: "sakin pencerede fiyat A'nın derin seviyelerine inmiyor, ızgara
salınıma oranlanmalı." **Gerçek dolumlar tam tersini söyledi:**
```
seviye   SAKIN dolum%   OYNAK dolum%
 0.22        49%            33%      <- sakinde DAHA COK doluyor
 0.15        17%            18%
 0.10         2%             2%
pencere basina dolan seviye: SAKIN 2.9 / OYNAK 2.5
iki tarafi da dolan pencere: SAKIN %44 / OYNAK %41
```
Sakin pencerede A daha çok doluyor. Sorun dolum DEĞİL. Asıl fark eşsiz bacakta:
sakin %3.8 kazanıyor, oynak %12.5 (yapısal taban %0; oynak pencerede sıçrama
eşsiz bacağı bazen doğru tarafta bırakıyor).

Yan bulgu: **0.10 / 0.06 / 0.03 seviyeleri 196 kez konup 2 kez doldu.**
Yedi seviyenin üçü pratikte dekor.

## METODOLOJİ DERSİ — kamu akışı parça parça dolar
data-api trade akışı bir pencereyi ZAMAN İÇİNDE doldurur (medyan gecikme 298 sn,
kuyruk daha uzun). Erken okumada bosona "tek taraflı 124 pay almış" görünüyordu;
yarım saat sonra aynı pencere iki taraflı çıktı. **Bugün iki kez oldu ve iki kez
de yanlış çıkarım ürettim** ("bosona çift kurmamış" -> geri çekildi).
KURAL: bosona'nın pencere düzeyinde çift/eşsiz ayrımı, pencere bitiminden en az
20 dk sonra okunmadan yorumlanmaz.

Aynı tuzağın ikinci biçimi: "t>=250'de 5/5 kazanmış" dedim — son pencerelerden
seçilmiş dilimdi. Tam örneklem: t>=240 & px>=0.60 -> 12 işlem, 10/12,
+5.26 kr/pay, **GA95[−22.4,+31.8] sıfırı kapsıyor**. Geç-favori MAKER kulvarı
(taker'ı 4 ay/33.509 gözlemle çürüdü, [[project-gec-favori-curudu-20260918]])
açık bir soru olarak duruyor ama kanıt değil.

İlgili: [[project-rejim-kapisi-20260918]], [[project-cift-ekonomisi-a-vs-b-20260918]]
