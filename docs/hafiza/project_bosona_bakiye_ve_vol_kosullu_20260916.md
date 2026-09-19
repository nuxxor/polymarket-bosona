---
name: project-bosona-bakiye-ve-vol-kosullu-20260916
description: bosona haftalik testere bakiye deseni (karlilik KANITLANDI, ~3-6 kr/pay) + oynaklik kosullu test (mekanizma gercek, ongoru YOK)
metadata:
  type: project
---

## 1) BOSONA KARLILIGI ARTIK ACIK SORU DEGIL — UC KAYNAK AYNI YERE CIKIYOR
Operator "her gun polygonscan'den bakiyesini izliyorum, ufak ufak artiyor,
bazen geriliyor" dedi. Nansen gunluk PUSD bakiyesi (30 gun) deseni gosterdi:

**HAFTALIK TESTERE:** hafta boyu birikiyor, HER PAZARTESI ~26k tabanina supuruluyor.
Sifirlama gunleri: 08-24, 08-31, 09-07, 09-14 (hepsi Pazartesi).

| hafta | birikim |
|---|---|
| 08-17..23 | +38,1k |
| 08-25..30 | +22,1k |
| 09-01..06 | +16,0k |
| 09-08..13 | +12,9k |

Ortalama **+22,3k/hafta = ~$3.182/gun**. Olculen hacim ~55.516 pay/gun ->
**+5,73 kr/pay**. Bizim zincir replay'imiz +3,27 kr/pay, Nansen total
+$297,7k/118g = $2.523/gun. **Uc kaynak da 3-6 kr/pay diyor.**
→ "Belki karli degillerdir" kacamak kapisi KAPANDI. Motorumuz bir sey kaciriyor.
→ Nansen'in "realized -$394k" rakami muhasebe artefakti (redemption'lari dislyor).
→ **KENAR SONUYOR:** 38,1 -> 22,1 -> 16,0 -> 12,9 k/hafta, monoton dusus.

## 2) OYNAKLIK KOSULLU TEST — MEKANIZMA GERCEK, ONGORU YOK
Operator hipotezi: "BTC oynayinca hem Up hem Down oynuyor, emirleri doluyor."
1.265 emirde test edildi (`pm_delta_tarama_20260916_v1/vol_testi.py`):

| kosul | cift tamamlanma | kr/pay | GA | artida gun |
|---|---|---|---|---|
| tum pencereler (taban) | %50,4 | -8,07 | [-8,48,-6,49] | 0/4 |
| **pencere-ici denge>=0,45 VE hacim>=40k** | **%88,4** | **+2,58** | [+1,81,+3,72] | **4/4** |

**Basabas %79,8'i asan ILK hucre bu.** Mekanizma DOGRULANDI.
AMA hicbir nedensel ongorucu tutmuyor (S+2'de bilinebilenler):

| nedensel ongorucu | cift% | kr/pay |
|---|---|---|
| S+2'de \|p_up-p_down\|<=0,12 | %49,9 | -8,52 |
| onceki pencere hacmi >=40k | %57,8 | -4,85 |
| onceki pencere denge >=0,45 | %56,4 | -5,45 |
| onceki 5dk BTC getiri std, ust %10 (Chainlink TWAP) | %54,7 | -5,26 |
| onceki 5dk BTC fiyat araligi, ust ceyrek | %62,0 | -3,51 |
| en iyi kombinasyon | %59,4 | **-3,73** |

Pencerenin dengeli olacagini BILMEK +6,3 kr/pay degerinde; ONGOREMIYORUZ.
Acik soru: ya kacirdigimiz bir ongorucu var, ya da bosona ongormeden —
yalnizca dengeli pencerelerde dolan, dengesizlerde maliyeti olmayan bir
kotasyon bicimiyle — kazaniyor.

Ilgili: [[project-aktor-paradoksu-odul-hipotezi-20260916]] (prompt guncellendi),
[[project-delta-tarama-kapanis-20260916]]


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🔑 BOSONA BAKİYE TESTERESİ + VOL-KOŞULLU TEST (09-16): PUSD bakiyesi hafta boyu birikip HER PAZARTESİ ~26k tabanına süpürülüyor → +22,3k/hafta = **+5,73 kr/pay**, zincir replay +3,27 ve Nansen ile TUTUYOR → kârlılık KANITLANDI, "belki kârlı değiller" kapandı; kenar sönüyor (38→22→16→13k/hafta). Oynaklık: pencere-içi denge≥0,45 & hacim≥40k → çift %88,4, **+2,58 kr/pay GA[+1,81,+3,72] 4/4 gün** (başabaşı aşan İLK hücre) ama hiçbir nedensel öngörücü tutmuyor (en iyi −3,73)](project_bosona_bakiye_ve_vol_kosullu_20260916.md)
