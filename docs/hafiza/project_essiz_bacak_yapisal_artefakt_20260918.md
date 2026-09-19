---
name: project-essiz-bacak-yapisal-artefakt-20260918
description: DIS DENETIM MERKEZ IDDIAMI CURUTTU - "essiz bacak 16/16 kaybetti = -26,7 puan ters secim" YAPISAL ARTEFAKT. Adil martingale + simetrik merdivende essiz bacak %100 kaybeder ve EV=0. Cift maliyeti de tek basina olcut degil. Gercek kenar ~0,6-1,5 kr/pay mertebesinde, yuzlerce pencere gerektirir
metadata:
  type: project
---

# ESSIZ BACAK: TERS SECIM DEGIL, YAPISAL ARTEFAKT (09-18)

## CURUTULEN IDDIA
"Essiz kalan bacak 16 pencerede 16 kez kaybetti; adil beklenti %26,7; demek ki
-26,7 puan ters secim var" -> **YANLIS**.

## KANIT (dis denetcinin argumani, kendi simulasyonumla dogrulandim)
Simetrik merdiven + surekli (siçramasiz) adil fiyat sureci:
- Up alisimiz P'den dolduysa Up'in adil degeri P'dir.
- Up KAZANACAKSA 1'e giderken (1-P)'den GECMEK ZORUNDA.
- O noktada Down'in degeri P olur -> Down alisimiz da dolar -> CIFT olur.
- **Yani yalniz Up elde kalmissa, Up KAYBETMISTIR. Tanim geregi.**
P(essiz bacak kazanir) = 0, ters secimden DEGIL, GEOMETRIDEN.

Kendi simulasyonum (4000 pencere, SIFIR kenarli martingale, ayni merdiven):
  eslesen +26,61 kr/pay | eslesmeyen -18,00 | TOPLAM -0,36 (~0)
  **ESSIZ BACAK KAZANMA ORANI: %0,00 (0/3887)**
Yani dort olcumumuzun (cift maliyeti ~0,56, eslesen ~+22, eslesme ~%55,
essiz kazanma %0) HEPSI sifir kenarla uyumlu.

## DIGER CURUTULENLER
1. **Cift maliyeti tek basina olcut DEGIL.** Lot eslestirme yontemine gore
   0,50143 / 0,55993 / 0,61859 cikiyor; toplam PnL hepsinde +0,83520 sabit.
   Ucuz KAYBEDEN bir lot eklemek metrigi "iyilestirip" kari DUSURUYOR.
   -> "bosona'yi 0,56'ya karsi 0,847 ile gectik" GERI CEKILDI.
2. **"Denge sinirini kaldir +3,19$" GECERSIZ.** (a) Simulasyonum mevcut sistemi
   yeniden uretemiyor (-1,06 vs gercek +0,8352). (b) Iptal edilen emirlerin
   sonraki dolumlari logda YOK - gerceklesmis islemleri yeniden siralayarak
   hesaplanamaz. (c) KOD HATAM: `sinir = 0.01 if yas>=GEC_ESIK else DENGE_SINIR-0.5`
   - "sinirsiz" kolunda t>=180 kurali ACIK kaldi, sinirsiz hic test edilmedi.
3. **Pencere sayisi <-> pay agirligi karistirildi.** "bosona yon kenari -0,7 puan"
   bu hatadan geliyordu, GERI CEKILDI.
4. 19 pencere temiz deney degil: asgari indirim filtresi ve gec-denge kurali
   orneklem ORTASINDA eklendi (6 dolmus emir mevcut filtreden gecmezdi).

## AYAKTA KALAN GERCEK FARK (pay-agirlikli, ayni 18 pencere)
| | essiz pay | ort alis | KAZANAN PAY ORANI |
|---|---|---|---|
| biz | 215 | 0,2651 | **%0,00** |
| bosona | 8.549 | 0,3361 | **%8,64** |
Dogru kiyas noktasi adil fiyat DEGIL, simetrik merdivenin **yapisal tabani %0**.
Biz tam tabandayiz, bosona TABANIN USTUNDE. Essiz bacak farkimizin (-26,68 vs
-21,92) tamami bu. Modele gore essiz KAZANAN ancak (a) merdiven SIMETRIK DEGILSE
ya da (b) fiyat ayna seviyeyi SICRAYARAK atlarsa olusur. bosona'da hangisi?
**ACIK SORU - siradaki arastirma yonu.**

## GERCEK KENAR MERTEBESI
Adil piyasada HICBIR pasif kotasyon duzeni kenar uretmez (EV=0). Kenar ancak:
  (a) maker rebate: 0,126-0,336 kr/pay (bizim 0,10-0,40 bandimizda)
  (b) dolumun adil degerin altinda olmasi = makasin yarisi ~0,5 kr/pay
Toplam ~0,6-0,85 kr/pay. bosona'nin 19 gunluk zincir-kesin +1,77'si de bu mertebede.
=> **-26,7'lik bir delik degil, ~1 kurusluk bir kenar ariyoruz.**
=> Olcum icin ONLARCA degil YUZLERCE pencere gerekiyor.

## BASA BAS FORMULU (denetciden, dogrulandi)
PnL/N = f(1-C)/2 - (1-f)L - k     (f=eslesen pay orani, C=cift maliyeti,
                                    L=essiz pay basina zarar, k=diger masraf)
Mevcut: f=0,5526 C=0,55993 L=0,26681 -> basa bas L=0,27172
**Tampon yalnizca 0,49 kurus/essiz pay.**

## DUZELTILEN KOD KUSURU (canlida dogrulandi)
RISK CIFT SAYIMI: acilis_maruziyeti() borsadaki acik pozisyonlari okuyor, ama
onlar AYNI ZAMANDA pen[] penceresinin dolumlari -> toplam_risk() iki kez sayiyor.
Canli log 00:38: dis_risk=3,50 + pencere_risk=3,95 = risk 7,45 (gercegi 3,95).
Kesiciyi ~2x kotumser yapip kosuyu erken durduruyordu. Izlenen pazarlar
DIS_RISK'ten cikarildi -> dis_risk=0,0, risk 7,0 -> 3,5.

## DENETCININ BEKLEYEN KOD BULGULARI (henuz duzeltilmedi)
- t>=180'de envanter ESITSE fonksiyon hemen donuyor -> iki taraftaki bekleyen
  emirler yeni ciplak pozisyon uretebiliyor
- hafif taraftaki acik emir miktari EKSIK MIKTARLA sinirlanmiyor
  (10 Up/5 Down -> Down supurulunce 10 Up/20 Down olabiliyor)
- denge kontrolu dolumlardan SONRA calisiyor -> 10 pay kesin ust sinir degil (logda 15)
- belirsiz iptal durumu kalan emir riskinden dusuyor -> rezerv kaybolabiliyor
- bos emir listesi / bozuk state sifir gecmis sayilabiliyor
- iptal sirasinda bulunan dolum ayri 'dolum' olayi uretmiyor
- olc4.py agirlikli cift maliyeti gosterip GA'yi agirliksiz pencere ortalamasindan uretiyor
