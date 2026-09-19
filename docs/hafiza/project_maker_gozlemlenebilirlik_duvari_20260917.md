---
name: project-maker-gozlemlenebilirlik-duvari-20260917
description: Ucuz-taraf kosulsuz kenari da kuyruktan sag cikmadi — maker tarafi 4. kez ayni mekanizmayla oldu; gozlemlenebilirlik duvarina carptik
metadata:
  type: project
---

## SON TEST: UCUZ TARAF (px<0,20), DURUST KUYRUK
Hucre duzeyinde kosulsuz **+1,62 kr/pay** ([[project-fiyat-zaman-yuzeyi-20260917]]).
Dolum duzeyinde (t=5'te ucuz tarafa post-only bid, kuyrugun arkasi, 297 iptal):

| bid | pencere | dolum% | pay | kr/pay | %95 GA | R2 |
|---|---|---|---|---|---|---|
| 0,12 | 27 | %77,8 | 105 | -2,48 | - | %18,5 |
| 0,15 | 54 | %74,1 | 197 | -4,06 | - | %20,4 |
| 0,18 | 95 | %84,2 | 400 | +0,75 | [-8,62,+4,45] | %15,8 |
| 0,22 | 153 | %85,0 | 646 | -4,20 | [-12,00,-0,20] | %31,4 GECERSIZ |

Dolum orani YUKSEK (%74-85) — pahali tarafin tersine doluyoruz. Ama kenar EKSI.
Hicbir konfigurasyonda GA sifiri disliyan arti yok.

## AYNI MEKANIZMA, DORDUNCU KEZ
1. base.py iki-tarafli kotasyon: -8,07 kr/pay (12/12 konfig eksi)
2. Gec-favori 0,70-0,90 maker: -14,61 (dolum-kosullu isabet %68,3 vs kosulsuz %85,9)
3. TWAP maker canli pilot: -$4,25 (dolanlarin medyan |z| 3,24, dolmayanlarin 6,92)
4. Ucuz taraf kosulsuz: hucrede +1,62 -> dolumda -2,5..-4,2

**Tek cumle: hucre duzeyinde kenar GORUNUYOR, dolum duzeyinde KAYBOLUYOR.
Cunku dolduran taraf, kenarin yanlis oldugu durumlari secerek dolduruyor.**

## GOZLEMLENEBILIRLIK DUVARI
Aktorlerin kenari hucre seciminde ve DORT kontrolden gecti
([[project-hucre-secimi-bulgusu-20260917]]). Ama onlarin ayni ters secime NEDEN
maruz kalmadigini olcemiyoruz: kamu veride yalniz DOLAN emirler var,
DOLMAYAN/IPTAL edilen emirleri yok. Yani "onlarin dolum orani ve kuyruk
davranisi" PRENSIP OLARAK gozlemlenemez.
Olculebilir kalan tek sey kendi canli dolumlarimiz — ki 4 kez olctuk, 4'unde de
ters secim cikti.

## NE DEGISIRSE ACILIR
- Polymarket order-admission/cancel gecmisi kamuya acilirsa (su an yok).
- Ya da maker olmayan bir yurutme yolu bulunursa. **BU DA KAPANDI (09-17):**

## SON KAPI: UCUZ TARAFI TAKER ALMAK — KAPANDI
ASK **VAR** (ucuz tarafin %100'unde), makas medyan tam **1 kurus**.
Ama almak KARLI DEGIL:
| an | pencere | NET kr/islem | %95 GA | artida gun |
|---|---|---|---|---|
| t=5 | 252 | **-4,04** | [-16,38, +0,06] | 1/4 |
| t=60 | 338 | **-4,62** | [-11,57, +0,96] | 1/4 |
Bid'deki +1,62 -> 1 kurus makas + 0,9-1,2 kurus taker ucreti -> eksi.

**MAKER KULVARI TAM KAPANDI:** dort maker yolu + bir taker yolu, besi de eksi.
