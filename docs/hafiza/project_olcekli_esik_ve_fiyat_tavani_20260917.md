---
name: project-olcekli-esik-ve-fiyat-tavani-20260917
description: Oynakliga gore olcekli esik (z) sinyali t=242'ye geri tasiyor — ama piyasa O AN ZATEN 0,99; erken girmek UCUZ fiyat getirmiyor
metadata:
  type: project
---

## 1) OLCEKLI ESIK CALISIYOR
Sabit bp esigi erken saniyelerde bozuluyordu (t=245 -> -24,91 kr/pay).
Dogru olcek: kalan n2 saniyenin ORTALAMASININ std'si (rastgele yuruyus)
`std = sigma * sqrt((2n2^2+3n2+1)/(6n2))`, sigma = son 120 sn 1sn getiri std'si.
`z = (P_t - gerekli)/std`

Agustos, hata orani (|z| esigine gore):
| t | \|z\|>=3 pencere | yanlis | hata | \|z\|>=4 pencere | yanlis | hata |
|---|---|---|---|---|---|---|
| 245 | 1.782 | 6 | %0,34 | 1.483 | 3 | %0,20 |
| 250 | 2.258 | 8 | %0,35 | 1.952 | 2 | %0,10 |
| 255 | 2.209 | 4 | %0,18 | 1.930 | 1 | %0,05 |
| 262 | 2.531 | 5 | %0,20 | 2.330 | 2 | %0,09 |

**t=245'te bile hata %0,34** — sabit esigin t=262'deki %0,36'siyla ayni,
ama 17 saniye ONCE. Isleme acik sure 35 -> 52 saniye.

## 2) AMA ERKEN GIRMEK UCUZ FIYAT GETIRMIYOR — ONEMLI
Eylul, |z|>=3'un ILK saglandigi an (479 pencere, dogruluk %99,58):
- medyan t = **242 sn** (p25 242, p75 254) — yani neredeyse settlement penceresi
  acilir acilmaz belli oluyor
- o andaki KESIN TARAFIN best_bid'i: **medyan 0,99**, p25 0,97, p75 0,99

| ilk kesin an | pencere | medyan bid | dogruluk |
|---|---|---|---|
| 240-249 | 326 | 0,99 | %99,7 |
| 250-259 | 59 | 0,98 | %98,3 |
| 260-269 | 39 | 0,98 | %100 |

**PIYASA BIZIMLE AYNI ANDA BILIYOR.** "Once gir, ucuza al" fikri YANLIS.
Kenarimiz 0,97-0,99'da duran +1..+3 kurusluk artik.
=> Aktorlerin ayni hucredeki 0,65-0,80 dolumlari BASKA bir seyden geliyor
   (piyasanin henuz cozmedigi/koptugu anlar), bizim sinyalimizden degil.

## 3) OLCEKLI ESIGIN GERCEK FAYDASI
Ucuz fiyat degil, **daha cok pencere (479 vs 409) ve daha uzun kuyruk suresi**
(t=242'den yerlesirsen 55 sn beklersin, 262'den 35 sn). Yani DOLUM ORANI artar.

## 4) MALIYET GERCEGI
Chainlink Data Streams **$150/ay = $5/gun** (standart + TWAP30 + TWAP60,
saniyede 1 rapor). Kuralin 5 pay klipteki beklentisi ~$1/gun.
**Abonelik maliyetini karsilamak icin gunde ~167 dolan pay gerekiyor**
(+3 kr/pay ile). Su anki tahmin ~35 pay/gun.
=> Pilot su haliyle NET EKSI. Klip buyutulmeden bu kural aboneligi odemez.

Ilgili: [[project-twap-maker-olcum-20260917]], [[project-gec-pencere-twap-kilitlenme-20260917]]


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [📐 ÖLÇEKLİ EŞİK + FİYAT TAVANI (09-17): z=(P−gerekli)/(σ√(n₂/3)) ile sinyal t=242ye iniyor, hata %0,34 (sabit eşik orada −24,91 veriyordu); AMA piyasa O AN ZATEN 0,99 veriyor (479 pencere, medyan ilk-kesin-an t=242, medyan bid 0,99) → "erken gir ucuza al" YANLIŞ, faydası sadece daha çok pencere + daha uzun kuyruk süresi. MALİYET: Streams $150/ay=$5/gün, 5 payla beklenti ~$1/gün → abonelik için ~167 pay/gün gerek](project_olcekli_esik_ve_fiyat_tavani_20260917.md)
