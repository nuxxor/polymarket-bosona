---
name: project-aktor-paradoksu-odul-hipotezi-20260916
description: Aktorler %84 MAKER + %50,2 kazanma orani + NEGATIF realized PnL — kenar ticaret karinda degil, Polymarket tesvik programlarinda olabilir
metadata:
  type: project
---

2026-09-16. Operator "bir yerde hesap hatasi var" dedi; su celiskiyi kurduk.

## OLCULEN GERCEKLER
**Maker/taker (kendi olcumumuz, data-api /trades takerOnly=true vs false,
ORTAK 1 gunluk zaman penceresine kisitlanmis, yalniz 5m pazarlar):**
- bosona : **%83,6 MAKER** (pay bazinda), %16,4 taker
- mo-money: **%73,3 MAKER**, %26,7 taker
DIKKAT: iki sorguyu ham toplamla kiyaslama — farkli zaman araligi donduruyorlar
(taker payi >%100 cikiyor). Ortak [lo,hi] araligina kisitla.

**Nansen cuzdan ozeti (09-16):**
| | bosona | mo-money |
|---|---|---|
| yas | 118 gun | 405 gun |
| pazar | 81.700 | 80.900 |
| **kazanma orani** | **%50,2** | **%50,2** |
| **Realized PnL** | **-$394,2k** | **-$325,7k** |
| Unrealized | +$691,9k | +$702,6k |
| Total | +$297,7k | +$376,9k |

→ 80 bin pazarda %50,2 = YON BILGISI YOK. Ve realized PnL NEGATIF.

## TESVIK HIPOTEZI — OPERATOR EMRIYLE KAPATILDI (09-16)
Operator: "liquidity reward'i tamamen cikar, kendi isimize odaklan, rebate'e
liquidity rewards asla karistirma." Kulvar disi. Bir daha ONERME.

**Maker rebate ARITMETIKLE de kapandi (kendi hesabimiz):**
Her taker dolumunun karsisinda tam bir maker var -> toplam maker fee_equivalent
= toplam taker fee_equivalent -> pro-rata payimiz kendi dolan hacmimize inar:
`rebate_pay_basina = 0,20 * 0,07 * p * (1-p)`

| p | 0,50 | 0,70 | 0,80 | 0,90 | 0,99 |
|---|---|---|---|---|---|
| kr/pay | **0,350** | 0,294 | 0,224 | 0,126 | 0,014 |

Azami **+0,35 kr/pay**, olctugumuz **-8,07 kr/pay** kotasyon maliyetine karsi
= acigin yalnizca **%4,3'u**. Rebate CEVAP DEGIL. Bundan sonra maker geliri SIFIR
kabul edilir.

## ACIK KALAN MEKANIK SORULAR (prompt bunlarin uzerine kuruldu)
- G1 MERDIVEN: biz taraf basina TEK emir simule ediyoruz (best_bid-DELTA).
  Onlar ayni anda cok seviyeli merdiven veriyor olabilir -> kuyruk pozisyonu,
  dolum dagilimi ve envanter sekli bizim modelde temsil EDILEMIYOR.
- G2 KUYRUK KURALI: "gozlenen seviye boyutunun TAMAMI onumuzde" varsayimi dogru mu?
  cancel/replace, boyut artisinda oncelik kaybi, vs.
- G3 HESAP BIRIMI: 5 coin x 5m/15m/4saat es zamanli; envanter netlesiyorsa
  pencere-basi muhasebemiz anlamsiz.
- G4 TERS SECIM: bizim artan envanter 0/4 kaybediyor, onlarinki %52,6 kazaniyor.
  Fark nereden?
- **G5 (EN KRITIK) PREMIS TESTI:** Nansen bosona realized PnL **-$394,2k** diyor,
  bizim 3 gunluk replay'imiz **+$5.454**. Bunlar celisiyor. Eger aktorler
  ticarette KARLI DEGILSE, motorumuz dogru, -8,07 dogru ve haftalardir
  kar etmeyen cuzdanlari kovaliyoruz demektir. ONCE BU TEST EDILMELI.

Deep-research prompt yazildi:
`data/analysis/prompts/DEEP_RESEARCH_20260916_AKTOR_PARADOKSU.md`

Ilgili: [[project-delta-tarama-kapanis-20260916]] (12/12 konfig eksi — bu hipotez
dogruysa o sonuc DOGRU ama ALAKASIZ), [[project-098-hucresi-dogrulama-20260916]]


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🧨 AKTÖR PARADOKSU (09-16): bosona %83,6 / mo-money %73,3 MAKER (ortak zaman penceresiyle ölç, ham toplam yanıltır), ikisi de %50,2 kazanma oranı (80bin pazar = YÖN YOK), ikisinin de **realized PnL NEGATİF** (−$394k/−$326k); rebate aritmetikle KAPANDI (azami +0,35 kr/pay = açığın %4,3ü, maker geliri artık SIFIR kabul); liquidity rewards OPERATÖR EMRİYLE KULVAR DIŞI, bir daha önerme; açık: G5 premis testi — aktörler gerçekten kârlı mı?](project_aktor_paradoksu_odul_hipotezi_20260916.md)
