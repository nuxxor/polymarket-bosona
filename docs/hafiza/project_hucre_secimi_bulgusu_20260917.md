---
name: project-hucre-secimi-bulgusu-20260917
description: AKTORLERIN ASIL ISI COZULDU (kismen) — kenarin %82'si HUCRE SECIMI; aktorun bulundugu (pencere,token,fiyat) hucresinde HERKES +1,72 kr/pay kazaniyor
metadata:
  type: project
---

19 gunluk zincir-kesin defter (15,9M maker alim dolumu, 568.222 hucre).
Hucre = (pencere, token, YUVARLANMIS FIYAT). Hucre icinde kazanan SABIT.

## ELENEN ACIKLAMALAR
- `has_builder`: %100 False, ayirt etmiyor.
- ZAMAN: ilk 240 sn'de her 30 sn kovasinda kenar arti (+0,61..+3,57) — duz.
- KARSI TARAF: 9.815 farkli adres, en buyugu hacmin %6,4'u — yogunlasma yok.
- KUYRUK SIRASI: **CURUDU.** Aktorlerin sira-1 payi %2,6, kalabaligin %3,2.
  Kenarlari DERIN kuyrukta (sira 6+: aktor +2,39 / kalabalik -0,10).

## BULGU: HUCRE SECIMI
| hucre kumesi | kalabaligin kenari | pay |
|---|---|---|
| **aktorlerin BULUNDUGU** (26.060 hucre) | **+1,72 kr/pay** | 13,8M |
| aktorlerin OLMADIGI (542.162 hucre) | **-0,19 kr/pay** | 203,6M |
| (aktorlerin kendisi) | +2,10 | 3,5M |

**Aktorlerin dokundugu hucrede ALIM YAPAN HERKES kazaniyor.**
Kenarin ~%82'si hucre seciminden; aktorlerin kendi ekstrasi yalnizca +0,38.

## FIYAT KONTROLU — GECTI ("ucuz al" degil)
| fiyat | aktorlu | aktorsuz | fark |
|---|---|---|---|
| <0,30 | +1,26 | +0,87 | +0,39 |
| 0,30-0,45 | +1,58 | +0,79 | +0,79 |
| 0,45-0,55 | +0,81 | -0,48 | +1,29 |
| 0,55-0,70 | +1,50 | -2,04 | **+3,54** |
| >=0,70 | +2,67 | -0,64 | **+3,31** |
Her fiyat seviyesinde fark VAR; aktorlu hucreler her seviyede ARTIDA.

## ONEMLI: ESKI OLCUMLE CELISIYOR
[[project-wave-selector-lane-20260914]] "taklit AUC 0,84 ama o dalgalarda
kalabalik -0,50 kr/pay" diyordu. Bu olcum +1,72 diyor. FARK: eski olcum
PENCERE duzeyindeydi, bu olcum (pencere, token, FIYAT) duzeyinde.
Secim pencerede degil, pencere ICINDEKI FIYAT NOKTASINDA.

## HENUZ KURAL DEGIL — ACIK SORU
Olcum "aktor katildi mi" uzerine kosullu, yani DAIRESEL. Kural olmasi icin
hucre kalitesinin AKTORU GORMEDEN, kamu verisiyle ONGORULMESI gerek.
Aktor kimligi kamu akisinda 2,8-3,2 sn GEC geliyor -> takip etmek ise yaramaz
([[project-research-followup-20260915]]).
Ama hedef artik TEMIZ ve eskisinden FARKLI: pencere degil FIYAT NOKTASI,
ve hedef degiskeni "bu hucrede alim yapan kazanir mi".

Veri: 568.222 hucre, 26.060'i pozitif etiketli. Egitilebilir.

## DORT KONTROLDEN DE GECTI (09-17)
1. **FIYAT**: her fiyat seviyesinde fark var (+0,39..+3,54). "Ucuz al" DEGIL.
2. **PIYASAYA UZAKLIK** (onceki 30 sn VWAP'ine gore): her uzaklik kovasinda
   aktor 1,4-3,1 kurus onde. Kalabalik piyasaya EN YAKIN bantta bile -0,07,
   aktorler +2,81. "Mid'e yakin al" DEGIL.
   | uzaklik | aktor | kalabalik |
   |---|---|---|
   | <-0,10 | +0,05 | +0,10 |
   | -0,10..-0,03 | +1,69 | +0,27 |
   | -0,03..+0,03 | +2,81 | -0,07 |
   | +0,03..+0,10 | +2,52 | -0,55 |
   | >=+0,10 | +2,75 | -0,26 |
3. **KUYRUK DERINLIGI**: her derinlik kovasinda aktor onde (+0,45..+3,67).
4. **CUZDAN KOMPOZISYONU** (en onemlisi): AYNI 457 cuzdan,
   aktorlu hucrelerde **+1,75**, aktorsuz hucrelerde **-0,10** (fark +1,85).
   Eslesmis isaret testi: **336/457 = %73,5** cuzdan aktorlu hucrelerde daha iyi
   (rastgele %50). Kompozisyon artefakti DEGIL.

## DURUM: MEKANIZMA BULUNDU, ONGORUCU BULUNAMADI
Aktorlerin varligi gercekten KARLI HUCRELERI isaretliyor ve bu herkese +1,85
kr/pay degerinde. Dort kontrolden de gecti. AMA:
- Olcum hala aktoru GORMEYI gerektiriyor (kimlik 2,8-3,2 sn gec gelir).
- Bugun denenen IKI kamu ozelligi (fiyat seviyesi, mid'e uzaklik) hucre
  kalitesini ACIKLAMIYOR.
=> Siradaki is: defter sekli / akis dengesizligi / pencere oynakligi gibi
   ozelliklerle 26.565 pozitif etiketli hucreyi ONGORME modeli. Eylul tape'inde
   (4 gun, tam defter) egitilebilir, Agustos ledger'inda dogrulanabilir.
