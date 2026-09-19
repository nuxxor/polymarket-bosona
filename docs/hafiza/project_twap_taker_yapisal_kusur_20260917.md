---
name: project-twap-taker-yapisal-kusur-20260917
description: TWAP kuralinin TAKER tasarimi yapisal olarak calismaz — kazanan tarafin ASK'i yok; dogru tasarim MAKER (kazanan tarafa bid koy, kaybedeni alan mint etsin)
metadata:
  type: project
---

2026-09-17. Operator canliya cikmaya razi oldu; runner yazildi
(`data/analysis/pm_twap_taker_20260917_v1/taker.py`, birim testleri gecti,
kesici -15, FAK taker, salt-kayit kuru kosu). **KURU KOSUDA ISLEM OLMADI** ve
sebebi yapisal cikti. CANLIYA CIKILMADI.

## BULGU: KAZANAN TARAFIN ASK'I YOK
Canli defter ornegi (kesin pencere, t~265):
```
Up   : bid [(0,99, 158.907), (0,98, 223), (0,97, 280)]   ask BOS (0 kayit)
Down : bid []                                             ask [(0,01, 158.856), ...]
```
PM defteri aynali: Up ask = Down bid'in yansimasi. Kaybeden tarafa (Down) kimse
BID koymadigi icin kazanan tarafta (Up) hic ASK yok. **Taker olarak alinacak
sey YOK.**

## FIRSAT MEVCUDIYETI (541 kesin pencere, Eylul, t 262-294)
| fiyat tavani | firsatli pencere | oran | toplam pay |
|---|---|---|---|
| 0,97 | 20 | **%3,7** | 30.935 |
| 0,98 | 40 | %7,4 | 39.537 |
| 0,99 | 363 | %67,1 | 188.267 |
| 1,00 | 455 | %84,1 | 207.637 |

0,97'de firsat neredeyse yok; 0,99'da bol ama kar 1 kurus (ucret sonrasi ~0,9).
Ucuz firsat oldugunda da ANLIK: pencerelerin cogunda 1-4 saniye, ilk firsat
medyan t=265.

## DOGRU TASARIM: MAKER
Gercek mekanizma tamamlayici MINT: kaybedeni ucuza alan biri, bizim
kazanan-taraf BID'imize karsi eslesir. Yani kazanan tarafa BID KOYULUR, taker
olarak alinmaz. **Aktorlerin %76-83 MAKER olmasi bununla birebir ortusuyor**
([[project-rol-ayrimi-iki-farkli-is-20260917]]).

AVANTAJ: sinyal sayesinde bu maker emrinin TERS SECIM RISKI YOK — hangi tarafin
kazandigini zaten biliyoruz. Kalan tek soru KUYRUK/DOLUM orani.
DEZAVANTAJ: kuyruk modeli geri geliyor — bu projede her backtesti kiran sey.

## DERS
Backtest "0,98 alti baski VAR" diyordu; baski = GERCEKLESMIS islem, ama o
islemin bizim icin ALINABILIR olmasi ayri sey. **Likidite yonunu (bid mi ask mi)
kontrol etmeden 'alinabilir hacim' deme.**

## SIRADAKI
Kazanan tarafa maker bid koyma kuralini dürüst kuyruk motoruyla olc:
t>=262, |mt|>=2bp, kazanan tarafa 0,95-0,98 arasi bid, kuyrugun arkasinda.
Dolum orani ve kenar olculmeden canli YOK.


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🛑 TWAP TAKER TASARIMI YAPISAL OLARAK ÇALIŞMAZ (09-17): kazanan tarafın ASK'ı YOK (PM defteri aynalı, kaybedene bid koyan yok) → taker olarak alınacak şey yok; fırsat 0,97'de %3,7 ve 1-4 saniyelik. DOĞRU TASARIM MAKER: kazanan tarafa bid koy, kaybedeni alan MINT etsin — aktörlerin %76-83 maker olmasıyla birebir örtüşüyor. Sinyal sayesinde ters seçim riski YOK, kalan tek soru kuyruk. CANLIYA ÇIKILMADI](project_twap_taker_yapisal_kusur_20260917.md)
