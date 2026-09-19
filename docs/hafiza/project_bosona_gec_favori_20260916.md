---
name: project-bosona-gec-favori-20260916
description: bosona'nin canli tape'i — gec pahali alim davranisi olculdu; kar cift-tamamlamadan DEGIL son 30 sn favori alimindan geliyor (+12,99 kr/pay), 200-270 sn ayni banda TEHLIKE (-7,34)
metadata:
  type: project
---

Kullanici 2026-09-16'da bosona'nin (0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed) pencere
sonuna dogru cok yuksek fiyattan ters bacak aldigini farketti. Olculdu: davranis GERCEK,
ama "zarar kurtarma" DEGIL.

Veri: data-api /trades, 6000 islem = 709 adet 5m penceresi (09-14 → 09-16, ~3 gun),
kazanan etiketi Gamma outcomePrices (709/710). Toplam +$5.454 = **+3,27 kr/pay**.

ALIMLARIN KENARI (kr/pay, [pay]):
```
                 <0.50        0.50-0.70     0.70-0.90      >=0.90
erken 0-60    +1,38[25456]   +6,71[12848]  +17,50[5010]  +8,63[600]
orta 60-200   +1,91[47758]   +7,64[5640]   -0,93[12200]  +6,37[4011]
gec 200-270   +5,12[24511]   +8,80[3290]   -7,34[4623]   +1,00[8080]
SON 270-300   -4,50[4491]   +37,79[715]    +12,19[1466]  +5,02[5850]
```

GEC (t>=200) + PAHALI (p>=0,65) alimlar, o anki envantere gore:
- CIFT TAMAMLAMA (elde olmayan tarafi al): 167 islem, 11.698 pay, **+1,61 kr/pay**, isabet %89
- AYNI TARAFA EKLE: 135 islem, 6.637 pay, **-0,79 kr/pay** (zarar)
- SIFIRDAN YENI: 73 islem, 2.862 pay, **+7,15 kr/pay**, isabet %95

→ Cift tamamlama kar motoru DEGIL (ortalamalarinin altinda); kanamayi durduran
savunma hamlesi. Kar, elde pozisyon YOKKEN gec alinan kesine yakin favoriden geliyor.

DAR HUCRE (t>=270, p 0,70-0,90, onceden pozisyon yok): 12 islem, 392 pay,
**+12,99 kr/pay**, isabet %92, 3/3 gun artida. Bu, [[project-pm-late-window-liquidation-20260914]]
icindeki 17 gunluk toplu tape olcumuyle (+9,58 kr/pay, iki yari ayri gecti) BAGIMSIZ
olarak ortusuyor — ayni hucre, ayni isaret, yakin buyukluk, ayni zaman siniri
(200-270 sn ayni fiyat bandinda EKSI, yalniz son 30 sn ARTI).

bosona'nin artan (tek taraflı kalan) envanteri %52,6 kazaniyor (620 pencerenin 620'sinde
artan var, yalniz 89 pencere tam denge). Bizim canli botun artani 0/4 kaybetti —
[[project-maker-ilk-alim-ters-secim-20260915]] ile tutarli.

## KARAR TESTI YAPILDI (ayni gun) -> HUCRE OLU
`data/analysis/pm_gec_favori_20260916_v1/` — 2.026 pencere (5 coin, 4 gun), PM tam
merdiven defteri (pm:book 0,01'den + price_change deltalari; delta semantigi
dogrulandi %88,8 birebir). Durustluk raporu: **R2 = %0** (hicbir emirde kuyruk
sifir varsayilmadi; Telonex 8-seviye artefakti bu veride YOK).

- On-kayitli hucre (son 30 sn, favori 0,70-0,90, touch maker): 92 emir, 41 dolum,
  **-14,61 kr/pay**.
- Mekanizma: kosulsuz favori kazanma %85,9 (odenen 0,823 -> +3,54 "sinyal"), ama
  **dolum-kosullu kazanma %68,3**. Sinyal var, DOLUM yok. Ters secim olculdu.
- Kalibrasyon (kural-bagimsiz, 1.722 pencere): 0,70-0,90 hucresi populasyon
  duzeyinde bile +5,25 GA[-1,98,+12,49] — sifiri kapsiyor.
- **+9,58 (17 gun toplu tape) ve +12,99 (bosona) KUYRUKSUZ olcumlerdi; GERI CEKILDI.**

## YAN BULGU — ACIK ADAY: 0,98-1,00 bandi
Ayni motor, farkli bant: 1.401 pencere, kaybeden favori **0/1401**, ters secim YOK
(dolum-kosullu %100). 5 payla +0,77 kr/pay; sinirsiz klip 291.652 pay,
**+$945/4 gun (~$236/gun)**, 4/4 gun artida. 3-kurali %95 ust kayip siniri %0,214
vs basabas %0,90.
CANLIDAN ONCE KAPATILACAK IKI ACIK: (1) motor Q ustundeki TUM tasmayi bize veriyor,
rekabet modellenmedi; (2) token'in kendi defteri tamamlayici likiditeyi icermez ->
gercek kuyruk daha derin olabilir. Detay: pm_gec_favori_20260916_v1/SONUC.md


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🎯 BOSONA GEÇ-FAVORİ → HÜCRE ÖLÜ (09-16): dürüst kuyruk motoru 2.026 pencere/5 coin, R2=%0 (sahte kuyruk YOK) → 0,70-0,90 geç favori **−14,61 kr/pay**; sinyal var (koşulsuz %85,9 vs 0,823) ama dolum-koşullu %68,3 = ters seçim; +9,58 ve +12,99 kuyruksuz ölçümlerdi, GERİ ÇEKİLDİ. YAN BULGU açık aday: 0,98-1,00 bandı 0/1401 kayıp, ters seçim yok, ~$236/gün — rekabet ve tamamlayıcı-likidite kuyruğu ölçülmeden para YOK](project_bosona_gec_favori_20260916.md)
