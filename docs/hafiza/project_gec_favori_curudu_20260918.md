---
name: project-gec-favori-curudu-20260918
description: GEC FAVORI ALIMI (taker) CURUDU - 33.509 gozlem/7.941 pencere/4 ay BTC 15dk: isabet oranı ask fiyatinin AYNISI (0,9279->%93,2; 0,9843->%98,6), kenar +0,03 kr/pay, GA sifiri kapsiyor. bosona'nin 12/12'si sans (0,931^25=%16,6). Arsivdeki +9,3 hatasi: gerceklesmis islem fiyati != alinabilir ask
metadata:
  type: project
---

# GEC FAVORI ALIMI CURUDU (09-18, 4 aylik Telonex verisi)

## HIPOTEZ
"Pencerenin son dakikasinda TWAP kilidi yuzunden sonuc belli; favoriyi ask'tan
almak yuksek isabetli ve karli." Uc kaynak destekliyordu:
  - bosona 09-18 gecesi: t>=240 & p>=0,65 -> 12/12 kazandi, +6,27 kr/pay
  - kendi arsivimiz: "t>=260 & fiyat>=0,65, 143k pay, %97 isabet, +9,3 kr/pay, 19/19 gun"
  - bizim derin merdiven o islemin KARSI tarafindaydi (7/7 kayip, -14,86 kr/pay)

## OLCUM
Veri: `data/parquet/telonex_polymarket_btc15m_crossvenue_20260825/book_snapshot_25`
      (25 seviye defter, 121 gun, 11.548 pencere iki tarafi da olan)
Sonuc: `telonex_predict_btc15m_pro_20260825/metadata/polymarket_btc15m_markets_*.parquet`
       -> `result_id`
Kod: `data/analysis/pm_gec_favori_telonex_20260918/{analiz.py,ozet.py}`
Yontem: kapanisa 60/50/40/30/20/10 sn kala, o andan ONCEKI son defter goruntusu,
favori = yuksek bid'li taraf, GERCEK ask'tan alim, resmi taker ucreti 0,07*p*(1-p).
**Dolum varsayimi YOK** (ask'tan almak gercekten uygulanabilir).

## SONUC: KENAR YOK
33.509 gozlem, 7.941 pencere. 30 hucrenin HEPSINDE GA sifiri kapsiyor.
| kalan | esik | islem | ort ask | isabet | kr/pay | GA95 |
|---|---|---|---|---|---|---|
| 60 | 0,65 | 6.677 | 0,9279 | %93,2 | +0,03 | [-0,54,+0,59] |
| 60 | 0,90 | 5.037 | 0,9740 | %97,6 | +0,06 | [-0,36,+0,45] |
| 60 | 0,95 | 4.213 | 0,9843 | %98,6 | +0,06 | [-0,31,+0,41] |
| 20 | 0,50 | 4.491 | 0,9090 | %91,9 | +0,55 | [-0,21,+1,23] |
| 10 | 0,65 | 3.276 | 0,9388 | %93,8 | -0,39 | [-1,18,+0,37] |

**ISABET ORANI = ASK FIYATI, her esikte.** Ders kitabi verimli fiyatlama.
Ay ay tutarsiz: 04 +3,44 (215 islem) / 05 -0,94 / 06 -0,01 / 07 +0,38 / 08 +0,24.
Derinlik SORUN DEGIL: medyan ask 156 pay, %61'inde 100+ pay.

## IKI ILLUZYONUN ACIKLAMASI
1. **bosona'nin 12/12'si SANS.** 25 islem, ort fiyat 0,9311 -> hepsinin kazanma
   olasiligi 0,931^25 = **%16,6**. Altida bir. Sasirtici degil.
2. **Arsivdeki +9,3 kr/pay METODOLOJIK HATA:** o calisma GERCEKLESMIS ISLEM
   FIYATLARINI olcmus, ALINABILIR ASK'i degil. Biri 0,65'ten alim yaptiysa onun
   BEKLEYEN EMRI dolmustur = MAKER'dir. Ayni anda ask'tan alsan 0,95 odersin.
   => O +9,3, MAKER tarafinin kazanciydi. Aynali defterde maker tarafinda olmak,
   birinin 0,92'lik alisini 0,08'lik alisiyla eslemesi demek — yani BIZIM DERIN
   MERDIVENIMIZIN yaptigi isin KARSI TARAFI.
   **KURAL: "gerceklesmis islem fiyati" ile "alinabilir ask" ayni sey DEGILDIR.
   Aktor verisinden strateji cikarirken hangi TARAFTA oldugunu belirle.**

## KOPYALAMA DA KAPALI (09-18 olculdu)
bosona'nin islemlerinin kamu data-api'de gorunme gecikmesi: 27 islem, medyan
**298 sn**, %25-%75 = 268-328 sn, min 32 / max 568. 15dk penceresinin ucte biri
ile tamami geciyor. Zincir ustu (Polygon ~2 sn) teorik olarak mumkun ama
arsivimiz saf taklidi zaten -2,50 kr/pay olcmus.
