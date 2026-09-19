---
name: project-bosona-cift-maliyeti-cozuldu-20260918
description: 3 AYLIK SORU COZULDU - bosona kari YON DEGIL, cifti 0,847'ye toplamak; biz 0,976'ya topluyoruz, fark 6,48 kr/pay. Yon kenari SIFIR (-0,7 puan). Mekanizma derin iki-tarafli merdiven + pencere sonunda olen tarafi kurusuna toplamak
metadata:
  type: project
---

# BOSONA COZULDU (09-18, kamu veri, son 3 saat)

Adres: 0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed
Veri: son 3 saat, 744 islem (HEPSI BUY), 87 pazar, 81 cozuldu.

## ANA SAYI
| | pay | kenar | tutar |
|---|---|---|---|
| ESLESEN cift | 24.975 | **+7,71 kr/pay** | **+$1.926** |
| TEK TARAF | 13.654 | -2,78 kr/pay | -$380 |
| TOPLAM | 38.630 | +4,00 kr/pay | +$1.546 |

**Karin TAMAMI ciftten. Tek taraf zararda.**

## YON KENARI = SIFIR (kesin)
Tek taraflı bacaklar: ortalama alis **0,3489**, gercek kazanma **%34,2** (27/79),
adil beklenti %34,9 -> **yon kenari -0,7 puan**. bosona BTC'nin yonunu BILMIYOR.
=> "yon tahmin modeli kuralim" yolu OLU. Aktor de kullanmiyor.

## ASIL FARK: CIFT MALIYETI
- bosona 41 iki-tarafli pazarda cift maliyeti **$0,847** (medyan 0,840) -> +15,3 kr/cift
- biz (v3, 9 pencere) **$0,976** (medyan 0,980) -> +2,4 kr/cift
- **FARK 6,48 kr/pay.** Uc aydir aradigimiz bosluk BUDUR.

## MEKANIZMA (ayni pencerede yan yana dogrulandi)
`btc-updown-5m-1789676700`, kazanan Down:
- BIZ: ilk 30 sn dokunustan 20 pay, cift maliyeti 0,97, kar **+$0,30**
- BOSONA: Up 763 pay @ort **0,107** (763'unun TAMAMI son 60 sn'de),
  Down 924 pay @ort **0,261** (420'si son 60 sn'de). Cift maliyeti **0,368**.
  Harcama $323, garanti odeme $763. Up kazansa +$441 / Down kazansa +$602.
  **KAR $602.**
`btc-updown-5m-1789677300`: cift maliyeti 0,410, kar +$188.

MEKANIZMA: Up+Down her zaman $1,00 oder. bosona o paketi **her tarafi O TARAF
UCUZKEN alarak** topluyor. Pencere ici fiyat savruluyor; defterin DERINLIGINDE
iki tarafta da bekleyen alislar savrulmanin iki ucunu da yakaliyor, iki "ucuz
an"in toplami 1,00'in cok altinda kaliyor. Ozellikle **son 60 saniyede olen
tarafi 5-14 kurusa** topluyor (o taraf gercekten degersiz ama cifti tamamliyor).
Biz ilk 30 sn'de DOKUNUSTAN, yani ADIL fiyattan aliyoruz -> sadece makasi kapiyoruz.

## SIMULASYON 6. KEZ YANILTTI
"MERDIVEN testi 222 paya kadar cikildi, hepsi -6,9...-9,9, genislik cevap DEGIL"
diye kapatmistik (project_son_tur_taker_ve_merdiven_20260917). bosona TAM OLARAK
onu yapiyor ve calisiyor. Simulasyonun kuyruk modeli derin emirlerin dolmayacagini
soyluyordu; gercekte SAVRULMA aninda doluyorlar. RESEARCH_DISCIPLINE_PLAYBOOK #38.

## CIFT TAMAMLAMA HAKKINDA DUZELTME
v3'e ekledigim "tek taraf kalirsa eksigi taker al" ozelligi KAR GETIRMEZ:
bosona'nin 79 pazarlik verisi ters secimin ~0 oldugunu soyluyor (-0,7 puan).
Benim "-50 kr/pay ters secim" tahminim 2 PENCERELIK ornekti (7. kez kucuk
orneklem hatasi). Ilk canli tamamlama $4,17 KAYBETTIRDI (Up kazanacakti).
Ozelligi TUT ama yalniz VARYANS kesici olarak; kenar beklentisi sifir/negatif.

## SIRADAKI HAMLE
Kotasyon politikasi: dokunus (OFSET=[0,1]) yerine **derin merdiven, pencere
boyunca acik, ozellikle son 60 saniyede aktif**. Acik sorular:
(1) derin emirler sermaye baglar - kac pay/pencere gerekir,
(2) bosona'nin 3 saatlik +4,00 kr/pay'i 19 gunluk ortalamasinin (+1,77) 2 kati,
    bu pencere tipik olmayabilir,
(3) 5 paylik klip ile bu is olur mu, yoksa olcek mi gerekiyor.
