---
name: project-dolum-kalitesi-canli-20260917
description: Genis maker canli dolum-kalitesi olcumu — dokunusa koyunca %100 dolum, simulasyonun dedigi ters secim ERKEN VERIDE GORULMEDI
metadata:
  type: project
---

`data/analysis/pm_dolum_kalitesi_20260917_v1/ladder.py --live`
Baslangic 09-17 15:11 UTC. Kesici **-50**, klip 5 pay, pencere basina azami ~$10.

## AMAC (kar DEGIL)
Aylardir cevaplayamadigimiz tek soru: kalabaligin GERCEK dolumlari iyi
hucrelerde derin kuyrukta bile +0,91 kr/pay; bizim SIMULE ettigimiz her yeni
emir -7. Ikisini uzlastiran tek sey kuyruk varsayimi — ve o yalnizca KENDI
canli dolumlarimizla sinanir.

## KURAL (secim YOK, kasten)
t=S+5'te iki tokenin defteri okunur; her tarafta **en iyi bid ve bir alti**
(2 seviye x 2 taraf = 4 emir), her biri 5 pay post-only. Pencere sonu -3 sn iptal.
Sinyal/secim YOK — dolum kalitesini secimden arindirilmis olcmek icin.

## NIHAI SONUC (3 saat, 15:11-17:59 UTC, kesici atmadi, operator durdurdu)
**108 emir | 103 dolum = %95,4 | 24 post-only red | 31 cozulen pencere | 465 pay**
**PnL -$15,05 = -3,24 kr/pay | pencere-bootstrap GA [-10,76, +3,76] | artida 21/31**

### YAPI — base.py ile AYNI
| tip | pencere | pay | kr/pay | artida |
|---|---|---|---|---|
| IKI TARAF (cift) | 20 | 355 | **+2,76** | 18/20 |
| TEK TARAF | 11 | 110 | **-22,59** | 3/11 |

### TERS SECIM DOGRULANDI
Tek taraflilar: 110 pay, odedigi **49,9 kr**, kazanma **%27,3**.
Adil %49,9 -> **-22,6 puan**. (kaba hata payi ±20,9 puan, 22 bacak)
Simulasyonun soyledigi sey, isaret olarak DOGRU cikti.

### SEVIYE
| seviye | dolum | pay | odedigi | kazanma | kr/pay |
|---|---|---|---|---|---|
| 0 (dokunus) | 51 | 255 | 49,5 | %45,1 | -4,43 |
| 1 (bir tik alt) | 42 | 210 | 49,4 | %47,6 | -1,79 |

### SIMULASYON vs CANLI — KARISIK KARNE
| olcut | simulasyon | canli | hukum |
|---|---|---|---|
| dolum orani | %10-25 | **%95** | sim TAMAMEN YANLIS |
| kenar | -6,9..-9,9 | **-3,24** (GA sifiri kapsiyor) | sim yon DOGRU, buyukluk abartili |
| ters secim | var | **VAR** (%27,3 vs %49,9) | sim DOGRU |

### 1,5 SAATTEKI OKUMAM YANLISTI — DUZELTILDI
1,5 saatte "seviye 1 = +7,61", "ters secim YOK (2/4=%50)" demistim.
3 saatte: seviye 1 = -1,79, ters secim VAR (%27,3). **Ikisi de gurultuymus.**
(Bugun dorduncu kez: kucuk ornekten iddia etme.)

### CIKIS KURALI PROJEKSIYONU
base.py olcumu tek taraflilarin kaybinin ~%80'inin t=120 satisiyla kurtarildigini
gosteriyordu. Bu kosuya uygulanirsa:
| kurtarma | kenar | rebate ile |
|---|---|---|
| %50 | -0,50 | -0,17 |
| %60 | +0,01 | +0,34 |
| %80 | **+1,04** | **+1,37** |
=> Cikis kuralli hali BASABAS ile +1,4 kr/pay arasi. Is degil ama TANIMLI yol.

## NEDEN ONCEKILERDEN FARKLI OLABILIR
Onceki testlerin cogu bid'in ALTINA koyuyordu (base.py: bid-0,05). Bu sefer
**DOKUNUSA** koyuyoruz -> ya yeni seviyenin basindayiz ya kisa kuyruktayiz.
Simulasyonun "gozlenen boyutun tamami onumuzde" varsayimi dokunusta
fazla kotumser olabilir.
Ayrica ikinci pencere base.py'nin BECEREMEDIGI cift yakalamayi yapti.

**UYARI: n=2 pencere. Bugun uc kez kucuk ornekten fazla iddia edildi.
Anlamli sayi ~50 dolum.**

Ilgili: [[feedback-simulasyon-yaniltti-canli-sart-20260917]]
