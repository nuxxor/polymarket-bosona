---
name: project-zincir-kesin-19gun-rol-20260917
description: 19 gunluk zincir-kesin defter — her iki cuzdan HER IKI ROLDE de artida, GA sifiri disliyor; kenar YON kenari (52 kr oder, %54 kazanir), spread degil
metadata:
  type: project
---

Kaynak: `data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER/{maker,taker}.parquet`
19,2M kayit, 08-14 -> 09-01, BTC 5m, **role etiketli ve ucret ZINCIRDEN**.
Kazanan etiketi Gamma (4.430/4.506 pencere): `pm_ayni_fiyat_20260917_v1/hunt_kazanan.json`

| cuzdan | rol | pay | odedigi | kazanma | NET kr/pay | %95 GA | artida gun |
|---|---|---|---|---|---|---|---|
| mo-money | maker | 1.748.464 | 51,57 | %53,82 | **+2,26** | [+1,55,+3,04] | 17/19 |
| mo-money | taker | 559.489 | 51,73 | %55,53 | +2,51 | [+0,30,+5,09] | 12/19 |
| bosona | maker | 1.751.446 | 52,09 | %54,04 | **+1,95** | [+1,10,+2,92] | 16/19 |
| bosona | taker | 366.408 | 48,10 | %53,00 | +3,63 | [+1,40,+6,05] | 13/19 |

**Dort hucrenin dordu de arti, dordunun de GA'si sifiri disliyor.** Ikisi de
YALNIZ ALIM yapiyor (satis 0). Toplam: mo-money +2,32 / bosona +2,24 kr/pay.

## ONCEKI IKI OKUMAM YANLISTI — IKISI DE KUCUK ORNEKLEM
1. "bosona maker +0,29, karinin %90'i TAKER" -> 34 SAATLIK artefakt. Zincirde
   bosona maker +1,95 (hacmin %83'u, karin %72'si). Rol ayrimi hikayesi COKTU.
2. "bosona taker 19 gunde +0,64 GA[-0,92,+2,31]" (data-api, 08-28->09-16) ile
   zincirdeki +3,63 (08-14->09-01) CELISIYOR ama donemler farkli ve
   [[project-bosona-bakiye-ve-vol-kosullu-20260916]] zaten kenarin sonduğunu
   gosteriyor (haftalik 38->22->16->13k). Agustos ortasi iyi, Eylul sonu zayif.

## ASIL BULGU: KENAR YON KENARI, SPREAD DEGIL
Aktorler **51,6-52,1 kurusa** aliyor (bizim politika 43,41) ve **%54** kazaniyor.
Yani ucuz underdog toplamiyorlar; ~adil fiyattan alip fiyatin ima ettiginden
**2 puan daha sik hakli cikiyorlar**. Biz 43,41 odeyip %35,3 kazaniyoruz —
adil fiyatin 8 puan ALTINDA.
=> Fark "daha ucuza almak" DEGIL. Hangi fiyattan alirsan al, onlar o fiyatin
   ima ettiginden iyi, biz kotuyuz.
=> Cift-kotasyon/spread yakalama cercevesi YANLIS: 52 kr'den iki tarafi birden
   almak 1,04 eder, garanti zarar. Tek tarafli yon aliyorlar.

## SIRADAKI
Ayni klasorde BINANCE_FLOW_1S / BINANCE_FUT_1S / BINANCE_SPOT_100MS parquet'leri
ayni doneme hizali. 1,75M dolum x 19 gun ile sinyal aramasi icin temiz zemin:
"dolum anindaki gozlemlenebilir durum, onlarin yonunu ongoruyor mu?"

Ilgili: [[project-rol-ayrimi-iki-farkli-is-20260917]] (DUZELTILDI),
[[project-denetim-duzeltmesi-kazanma-orani-20260917]]


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [⛓️ ZİNCİR-KESİN 19 GÜN (09-17): FILL_PARTY_LEDGER ile her iki cüzdan **her iki rolde de artıda, 4/4 GA sıfırı dışlıyor** (mo-money maker +2,26 [+1,55,+3,04] 17/19 gün; bosona maker +1,95; takerlar +2,51/+3,63) → "bosona taker mo-money maker" ayrımım 34 SAATLİK ARTEFAKTTI, çöktü. ASIL BULGU: aktörler **51,6-52,1 kr ödeyip %54 kazanıyor** = YÖN kenarı, spread değil; biz 43,41 ödeyip %35,3 → hangi fiyatta olursa olsun onlar fiyatın ima ettiğinden iyi biz kötü](project_zincir_kesin_19gun_rol_20260917.md)
