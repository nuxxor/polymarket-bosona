---
name: project-takeronly-hatasi-20260918
description: data-api /trades varsayılanı takerOnly=true — bosona hakkındaki TÜM ölçümlerimiz onun yalnız taker akışından yapılmış; gerçek kenarı +5.06 kr/pay ve aynı pencerelerde biz +3.20'yiz
metadata:
  type: project
---

# takerOnly HATASI — bosona ölçümlerinin tamamı eksik akıştan (2026-09-18)

`https://data-api.polymarket.com/trades?user=...` **varsayılan olarak
takerOnly=true** döndürüyor. Doğrulandı:
```
varsayilan        : 500 islem, BTC5m 228 islem / 30.264 pay
takerOnly=true    : 500 islem, BTC5m 228 islem / 30.264 pay   <- AYNI
takerOnly=false   : 500 islem, BTC5m 389 islem / 19.746 pay
```
Bu projedeki bosona sayılarının **hepsi** taker akışından üretilmişti. Oysa
kendi ölçümümüz onun **%83,6 maker** olduğunu söylüyordu — yani kârının
ana gövdesini hiç görmemişiz.

## AYNI 48 pencerede düzeltilmiş tablo
```
                            pay      PnL        kr/pay    GA95
bosona TAKER only        15.259   + 966.32$    +6.33    [-903,+3029]  sifiri KAPSIYOR
bosona TUM (maker dahil) 51.865   +2624.91$    +5.06    [+613,+4724]  sifiri DISLIYOR
BIZ                       1.315   +  42.09$    +3.20
```

### Bunun değiştirdikleri
1. **Kenarı +6,33 değil +5,06 kr/pay.** Taker görünümü onu %25 ABARTIYORDU.
2. Ama tam akışta **GA sıfırı dışlıyor** — taker görünümünde kapsıyordu.
   Yani kenarı gerçek; sadece sandığımızdan küçük.
3. **Hacmi 3,4 kat daha büyük** (51.865 vs 15.259 pay).
4. **Eşleşme oranı %75,9**, taker görünümündeki %26,3 değil.
5. **Çift maliyeti 0,8699** — bizim A kolumuzun **0,5745**'inden KÖTÜ.

## En önemli sonuç
**Çift maliyeti kaldıraç DEĞİL.** O çifti 0,87'ye kuruyor, biz 0,57'ye
kuruyoruz ve o kazanıyor. Günlerdir "çift maliyetinde onu geçtik" diye
sevindiğimiz metrik, onun kârının kaynağı değilmiş.

Kalan farklar: **eşleşme oranı** (%75,9 vs A'nın %42,4) ve **hacim**
(51.865 vs 1.315 pay, 39 kat).

## Uyarılar
- 48 pencere iki akışın KESİŞİMİ; son saatlere kayık bir örneklem.
- Bizim +3,20'mizin de GA'sı sıfırı kapsıyor (48 pencere, ~±$51).
- bosona zaman damgaları saniye çözünürlükte, bizimkiler ms — markout
  karşılaştırmasında bu asimetri onun lehine küçük bir sapma yaratabilir.

İlgili: [[project-bosona-cift-maliyeti-cozuldu-20260918]] (o dosyadaki 0,847 ve
+7,71 kr/pay TAKER-ONLY veriden geldi, güvenilmez),
[[project-cift-ekonomisi-a-vs-b-20260918]], [[project-olcek-kaniti-20260918]]
