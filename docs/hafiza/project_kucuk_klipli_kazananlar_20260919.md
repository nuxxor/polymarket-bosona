---
name: project-kucuk-klipli-kazananlar-20260919
description: Defterde BİZİM KLİP BOYUMUZDA (medyan 5-7 pay) kazanan 132 cüzdan var, bazılarının GA'sı sıfırı dışlıyor — "kenar boy ister" sonucu ÇÜRÜDÜ, ve bosona 475 içinde ancak 22. sırada
metadata:
  type: project
---

# KÜÇÜK KLİPLİ KAZANANLAR (2026-09-19) — kulvarı yeniden açan bulgu

Operatör park kararını reddetti; haklıydı. Zincir-kesin defterde (19 gün,
13,7M maker BUY dolumu, 220,9M pay, 4.430 pencere) cüzdan bazlı bakınca:

- **≥50k paylık 475 cüzdanın 234'ü (%49) artıda.**
- **bosona 22/475.** Onu tek örnek sanmak hataydı.
- Küçük klipli sınıf (medyan dolum ≤15 pay, ≥500 pencere, ≥15 gün): **229 cüzdan,
  132'si artıda.**

## BİZİM BOYUMUZDA KAZANANLAR (gün-kümeli GA95)
```
cuzdan      pay        pen   boy  fiyat   t     kr/pay      GA95         arti gun
0x037c0f46  149.571   1564    7   0.205   28    +4.67  [+1.22,+8.67]   13/16
0x8d1d5d1c   73.673   2237    6   0.322   99    +4.23  [+1.71,+6.97]   15/19
0x5d5f7080   58.891   2562    5   0.434  147    +3.23  [+1.56,+4.96]   17/19
0x3387ac61  886.375   3006   14   0.489   -8    +2.82  [+1.65,+3.87]   17/19
0x32ed2e54 1.748.464  4151   13   0.434  147    +2.26  [+1.55,+3.06]   17/19 (mo-money)
0xc2ad03f7 1.751.446  4052   14   0.437  147    +1.95  [+1.09,+2.93]   16/19 (bosona)
```
`0x5d5f7080` medyan **5 pay** — bizim klibimizin aynısı, 2.562 pencere, 17/19 gün artı.

## EN AZ ÜÇ FARKLI KAZANAN PROFİL
1. **Sığ-ucuz, erken** — `0x037c0f46`: hacminin **%100'ü 0.00-0.30**, medyan t=25-33 sn.
   0.10-0.20 +5,72 / 0.20-0.30 +4,25. **0,30 üstünde HİÇ emri yok.**
   Bizim kol A'ya çok yakın; farkı (a) en üst basamak 0,40 değil 0,30,
   (b) dolumlar ilk 30 saniyede.
2. **Pencere-öncesi** — `0x3387ac61`: medyan t = **−8 sn**, 886k pay, +2,82.
   Pencere açılmadan kotasyon. Hiç test etmedik ([[project-prewindow-pair-maker-20260916]]).
3. **Pahalı bantta seçici** — `0x361528e2`: hacminin %53'ü 0,60-1,00'da ve orada
   **+5,20**, oysa o bandın piyasa ortalaması −1,97. Saf seçicilik.

## BU NEYİ ÇÜRÜTTÜ
- "Kenar boy ister / kuyruk önceliği parayla alınır" → bu cüzdanlar 5-7 payla
  ve kuyruğun arkasında kazanıyor. 250+ gradyanı gerçek ama **tek yol değil**.
- "BTC 5m maker kulvarı park" → 132 küçük klipli cüzdan artıda; kulvar açık,
  bizim uygulamamız yanlış.
- "bosona'yı çöz" çerçevesi → yanlış soru. Doğru soru: **bizim boyumuzda kazanan
  132 cüzdanın ortak özelliği ne?**

## SIRADAKİ
Fiyat × zaman haritası (pencere-eşit ağırlık, gün-kümeli GA) — nerede durulmalı.
Sonra `counterparty` ve `has_builder` alanları; ikisine de hiç bakılmadı.

İlgili: [[project-btc5m-maker-kapanis-20260919]] (park kararı GERİ ÇEKİLDİ),
[[project-takeronly-hatasi-20260918]]
