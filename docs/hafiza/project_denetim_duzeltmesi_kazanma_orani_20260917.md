---
name: project-denetim-duzeltmesi-kazanma-orani-20260917
description: Dis denetim 3 hata buldu — 2'si gercek; "%50,2 kazanma orani = yon kenari yok" cikarimim GERI CEKILDI; dogru cerceve aynı fiyata 12,9 puan kazanma farki
metadata:
  type: feedback
---

2026-09-17, dis denetim raporu (ChatGPT/Astra). Iddialari TEK TEK dogruladim.

## KABUL ETTIKLERIM (dogrulandi)

**1. "%50,2 kazanma orani = yon kenari yok" CIKARIMIM YANLISTI. GERI CEKILDI.**
Pazar-sayisi kazanma orani, pay-agirlikli kar DEGILDIR. Dogru ozdeslik:
`kenar/pay = (pay-agirlikli kazanma) - (pay-agirlikli ort. odenen fiyat)`
Kendi replay'imle yeniden hesap (709 pencere, 166.547 pay):
- bosona: **44,95 kr oder, %48,22 kazanir -> +3,27 kr/pay**
- bizim politika (DELTA=0,05): **43,41 kr oder, %35,34 kazanir -> -8,07 kr/pay**
Pazar-sayisi orani %50,1; pay-agirlikli %48,22. FARKLI ISTATISTIKLER.

**2. `uygunluk.py` gercek dolumu COZULDU'dan okuyordu (hata).** Kesici pencereyi
cozmeden durunca dolmus emir "dolmadi" sayiliyordu. 1 emri etkiledi (S=1789529100).
DUZELTME: gercek dolum artik `dolum` olaylarindan (borsanin size_matched'i).
Duzeltilmis sonuc: motor 33/48 tam dolum ongordu, GERCEK **39/48, 194,9928 pay**
(denetimin rakamiyla BIREBIR ayni). "Motor doldu dedi dolmadi" 1'den **0'a** dustu.

**3. Kuyruk motoru IPTALLERI saymiyor (G2).** Onumuzdeki emirler iptal ederse
ilerleriz; motor yalniz islem hacmiyle azaltiyor. Yon: dolumu EKSIK sayar.

## REDDETTIKLERIM (veriyle)
- "Duzeltme motorun temkinli oldugunu curutur" — bu ornekte TERSI cikti:
  motor PnL **-$14,30** ongordu, GERCEK **-$9,25**. Kacirdigi 6 dolum net
  **+$5,05 KARLIYDI**. (Mantiklari genel olarak dogru: az tahmin != alt sinir.
  Ama bu veride yon temkinli.)
- "25 pencerenin bir kismi saat sinirinda dusmus" — dusmemis, 25/25 cikarilmis.

## YENI VE ASIL CERCEVE (bundan sonra bu kullanilacak)
**Ayni ortalama fiyati odiyoruz, 12,9 PUAN daha az kazaniyoruz.**
Adil piyasada 43,41 kr odeyen %43,41 kazanir. bosona +3,3 puan IYI, biz -8,1 puan KOTU.
Derinlik taramasi da bunu dogruluyor (fiyat duser, kazanma orani ayni miktarda duser,
kenar -8'de cakili): 0,03 -> 45,43kr/%37,94; 0,05 -> 43,41/%35,34; 0,09 -> 39,40/%30,91.
→ Soru artik dar: AYNI FIYATTA neden onlarin dolumlari kazaniyor bizimkiler kaybediyor?
Ucret degil (maker 0), rebate degil (azami 0,35), fiyat secimi degil (fiyatlar ayni).
Tamamen **o fiyatta HANGI dolumlari aldigin** meselesi.

Prompt bu cerceveye gore guncellendi (RETRACTION bolumu eklendi).
Ilgili: [[project-bosona-bakiye-ve-vol-kosullu-20260916]], [[feedback-verify-agent-output-20260729]]


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [⚖️ DIŞ DENETİM DÜZELTMESİ (09-17): "%50,2 kazanma oranı = yön kenarı yok" çıkarımım **GERİ ÇEKİLDİ** (pazar-sayısı ≠ pay-ağırlıklı); doğru çerçeve → bosona 44,95 kr ödeyip %48,22 kazanıyor (+3,27), biz 43,41 kr ödeyip %35,34 (−8,07) = **aynı fiyat, 12,9 puan fark**; uygunluk.py gerçek dolumu COZULDUden okuyordu (düzeltildi, motor 33/48 vs gerçek 39/48 = 194,9928 pay, denetimle birebir); motorun kaçırdığı 6 dolum +$5,05 KÂRLIYDI → "temkinli" yönü bu veride ayakta](project_denetim_duzeltmesi_kazanma_orani_20260917.md)
