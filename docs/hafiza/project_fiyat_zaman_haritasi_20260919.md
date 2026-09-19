---
name: project-fiyat-zaman-haritasi-20260919
description: 19 günlük zincir verisinden maker kenarının fiyat×zaman haritası — 17 hücrenin GA'sı sıfırı dışlıyor; kaybımızın sebebi strateji değil YER ve ZAMAN, ve en güçlü hücreye (0.60-0.80 @ t≥240, +10.92) hiç girmemişiz
metadata:
  type: project
---

# FİYAT × ZAMAN HARİTASI (2026-09-19) — kulvarın asıl haritası

Kaynak: `FILL_PARTY_LEDGER/maker.parquet`, 19 gün, 13,7M maker BUY dolumu,
220,9M pay, 4.430 pencere. **Pencere-eşit ağırlık** (pay-ağırlıklı sayılar
hacim yoğunluğundan gelir, katılımcının yaşadığı bu değildir), gün-kümeli
önyükleme. 48 hücre tarandı, 17'sinin GA'sı sıfırı dışlıyor.

## ARTI HÜCRELER (GA sıfırı dışlıyor)
```
fiyat       zaman     kr/pay        GA95           pencere
0.60-0.80   240+      +10.92  [+9.40,+12.23]       1270    <- EN GUCLU
0.10-0.20   0-60       +7.53  [+4.80,+10.48]       1273
0.60-0.80   180-240    +5.45  [+3.89,+6.76]        2520
0.20-0.30   0-60       +4.92  [+3.22,+6.74]        2868
0.50-0.60   240+       +4.38  [+2.46,+6.37]         791
0.10-0.20   60-120     +4.23  [+2.86,+5.73]        2594
0.50-0.60   180-240    +4.19  [+2.53,+5.80]        1599
0.00-0.10   60-180     +3.42                       1216/2485
0.50-0.60   0-120      +3.06 / +3.28
0.30-0.40   ONCE(t<0)  +2.26  [+0.19,+4.35]        1617
0.80-1.01   240+       +1.06  [+0.92,+1.21]        4413 (21,7M pay)
```

## EKSİ HÜCRELER (GA sıfırı dışlıyor)
```
0.30-0.40   240+      -11.66  [-13.22,-10.04]
0.40-0.50   240+       -9.67
0.20-0.30   240+       -9.66
0.10-0.20   240+       -7.12
0.40-0.50   180-240    -7.25
0.30-0.40   180-240    -6.49
0.40-0.50   60-240     -4.4 .. -4.65
0.80-1.01   0-240      -1.9 .. -5.6
```

## MEKANİZMA
- **Ucuz + ERKEN = artı**: erken panikleyenin karşı tarafısın, fiyat çoğu zaman döner.
- **Ucuz + GEÇ = eksi**: birazdan sıfırlanacak bileti alıyorsun. Aynı fiyat, ters işaret.
- **Pahalı + GEÇ = artı**: sonuç fiilen belli, fiyat hâlâ 0,70.
- **0,40-0,50 her zaman eksi**: karar noktası, bilgili akışın hedefi.

## BİZİM İKİ KOLUMUZ DA EKSİ HÜCRELERDE YAŞIYORDU
- **Kol A**: ucuz bantta ama emirleri pencere boyunca AÇIK → dolumlar fiyat
  çöktüğünde yani GEÇ oluyor → −7…−11,7 hücreleri. `GEC_KES=200` bile geç;
  zehir 120'den sonra başlıyor.
- **Kol B**: 0,40-0,50'de, yani her zaman dilimde eksi olan tek bantta.
- **0,60-0,80 @ t≥240 (+10,92)**: haritanın en güçlü hücresi, **hiç girmedik**
  (A 0,40'ta biter, B mid altında durur).

## AYRIM: bu, 0,95 geç-favorisi DEĞİL
Fable 0,85-0,95'i ölçüp negatif buldu; 0,99'da kuyruk 29.000 pay.
**0,60-0,80 bambaşka bir hücre** — kuyruk sorunu yok, kapı sorunu yok,
pencere başına ~1.750 pay hacim var.

## UYARI
Harita, o hücrede DOLAN ortalama maker'ın kazancıdır; oraya emir koyanın
aynısını alacağı kanıtlanmadı. Lehte işaret: 0,20-0,40'ta bizim gerçekleşenimiz
piyasanın pencere-ortalamasıyla tutarlıydı. Doğrulama: aynı hücreleri dolum
boyuna göre ayır (1-9 pay = bizim klip) — `analiz/hucre_boy.py`.

İlgili: [[project-kucuk-klipli-kazananlar-20260919]]
