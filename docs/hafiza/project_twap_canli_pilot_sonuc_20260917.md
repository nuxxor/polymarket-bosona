---
name: project-twap-canli-pilot-sonuc-20260917
description: TWAP maker pilotu 8 saat canli kostu — TERS SECIM olculdu, strateji bu haliyle olu; -$4.25
metadata:
  type: project
---

`pm_twap_taker_20260917_v1/maker.py --live`, 00:27-08:37 UTC, 5 pay klip,
bid 0,97, z>=3, t>=250. **Sonuc: 83 pencere, 76 emir, 5 dolum, PnL -$4,25.**
Kesici (-15) atmadi; operator karariyla durduruldu.

## 1) DOLUM ORANI SIMULASYONUN COK ALTINDA
Simulasyon %17,6 -> **CANLI %6,6** (5/76). 2,7 kat dusuk. Rekabet etkisi
simule edilemiyordu; canli cevap verdi.

## 2) TERS SECIM OLCULDU — ASIL BULGU
| \|z\| | emir | dolan | dolum% |
|---|---|---|---|
| 3-4 | 20 | 4 | **%20,0** |
| 4-6 | 14 | 0 | %0 |
| 6-10 | 23 | 1 | %4,3 |
| 10+ | 19 | 0 | **%0** |

Dolanlarin medyan \|z\|: **3,24**. Dolmayanlarin: **6,92**.
**Yalnizca en az emin oldugumuz anda dolduruluyoruz.** Sonuc bariz oldugunda
(\|z\|>6) kimse satmiyor. Kaybeden dolum da z=3,15'teydi.

## 3) O BANTTA MARJ YOK
\|z\| 3-4 bandinin tarihsel hata orani (Agustos): t=250 -> %1,96 (6/306),
t=262 -> %1,49. Basabas (bid 0,97) **%3,00**. Pay 1 puan, %95 UST SINIR %4,3
= basabasin USTUNDE. Istatistiksel olarak kurulamiyor.
Daha ucuza kacis YOK: \|z\| 3-4 bandinda bile piyasa medyan **0,98** veriyor.

## 4) KESIN VURUS: POST-ONLY REDLERI
7 pencerede ask <=0,97 idi (post-only reddetti). O 7 pencerede sinyalimiz
**yalnizca 5/7 = %71 dogru**; taker alsaydik **-$8,95**.
=> Piyasa "kesin" tarafi ucuza satiyorsa, SEBEBI piyasanin HAKLI olmasi.
   Hem maker dolumlari hem taker firsatlari TERS SECILMIS.

## HUKUM
Kural bu haliyle OLU. Sinyal dogru (%0,33 taban hata) ama **sinyalin guclu
oldugu yerde kimse islem yapmiyor, islem yapilan yerde sinyal zayif.**
Bu, projede her maker denemesini olduren mekanizmanin aynisi — bu sefer
8 saatte $4,25'e olculdu.

Yeniden acma tetigi: bid'i dusurup dolum alabilecegimiz bir yer bulunursa
(su an yok: bant fark etmeksizin piyasa 0,97-0,99'da) veya sinyal \|z\|>6
bandinda dolum alabilecek bir mekanizma bulunursa.


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🔴 TWAP CANLI PİLOT SONUCU (09-17, 8 saat): 76 emir 5 dolum **PnL −$4,25**; dolum oranı sim %17,6 → canlı **%6,6**; **TERS SEÇİM ÖLÇÜLDÜ**: dolanların medyan |z|=3,24 dolmayanların 6,92, |z|>6da dolum %0 → sadece en az emin olduğumuz anda dolduruluyoruz; o bantta hata %1,96 vs başabaş %3 (üst sınır %4,3 = geçmiyor); post-only reddedilen 7 pencerede sinyal %71 doğru, taker alsak −$8,95. KURAL BU HALİYLE ÖLÜ](project_twap_canli_pilot_sonuc_20260917.md)

## PARK EDILDI (09-17 08:45 UTC, operator karari)
- Canli bot DURDU (`bitti sebep=STOP`), acik pozisyon 0, acik emir 0.
- `cl_direct_rec.py` durduruldu (kulvara ozeldi; bedava relay ayni veriyi veriyor).
- `tape.py` CALISMAYA DEVAM (bu kulvarin degil; 0,98 hucresi kapisini besliyor).
- Kod ve veri korundu: `pm_twap_taker_20260917_v1` (runner, maker+taker surumleri),
  `pm_twap_kilit_20260917_v1` (32M, sinyal+maker olcumleri), `pm_twap_geri_20260917_v1`.

### YENIDEN ACMA TETIKLERI
1. \|z\|>6 bandinda dolum alabilecek bir mekanizma bulunursa (su an %0 dolum,
   ve hata orani o bantta %0,00 — kenar ORADA ama erisilemiyor).
2. Piyasanin 0,97'nin ALTINDA kotasyon verdigi sistematik bir durum bulunursa
   (su an \|z\| bandi fark etmeksizin medyan 0,98).
3. Baska bir venue/vade (15m, 4h TWAP pazarlari) ayni mekanigi tasiyorsa —
   orada rekabet daha az olabilir. HIC BAKILMADI.

### KULVARDAN CIKAN KALICI SERMAYE
- TWAP kilit mekanizmasi dogrulandi (settlement son 60 sn'de hesaplanabilir).
- Ters secimi 8 saatte olcen canli duzenek (maker.py) — baska kurallara takilabilir.
- Bayat-veri kapisi (`atla_cl_bayat`) iki internet kesintisinde sinandi ve tuttu.
