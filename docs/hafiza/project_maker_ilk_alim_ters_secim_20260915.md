---
name: project-maker-ilk-alim-ters-secim-20260915
description: Maker ilk-alım ön-kayıtlı testi GEÇMEDİ — ters seçim ölçüldü (dolan %43,2 vs dolmayan %89,0 tutturma); taker'da ücret, maker'da ters seçim kenarı yiyor, BTC5m kulvarı park
metadata:
  type: project
---

`data/analysis/pm_maker_ilk_alim_20260915_v1/` — kurallar sonuç görülmeden mühürlendi
(`maker.py` başı). Veri: btc5m zincir dolumları 24 Ağu–1 Eyl, 9 gün, 2.592 pencere,
**12.287.019 bacak** (data-api). Defter azalması iptal/dolum ayrımı yapamadığı için
zincir şarttı (bkz. bayat-iptal artefaktı [[project-bulgu-raporu-refute-20260914]]).

**v1 GEÇERSİZDİ** (Codex 4 hata buldu, hepsi doğrulandı: ileri bakış — kararların
yalnız %53'ü filtresiz aynı; rol karışımı — data-api'de maker/taker alanı YOK ve
takerOnly=false her bacağı döndürür; saat — ts SANİYE granülasyonunda; post-only
kabulü denetlenmemiş). Yeniden toplandı: takerOnly=true, 4.552.201 taker bacağı.

**DÜZELTİLMİŞ SONUÇ:** 2.225 pencere, post-only RED 270, dolan %72,7 →
**net −5,72 kr/pay GA [−7,90, −3,14]** (taker tabanı −0,61).

**YAPISAL:** kaybeden token'ların **%100'ü** bizi dolduruyor; kazananların %34,6'sı
doldurmuyor. Hata değil: 0/1'e yakınsayan piyasada bekleyen alış ancak fiyat
üstünden aşağı yürürse dolar — o da token ölürken olur.

**ASIL BULGU — KUYRUK POZİSYONU BELİRLEYİCİ DEĞİŞKEN:**
sıranın başı (kuyruk=0) **+3,09 kr/pay GA [+1,16, +5,14]** | ×0,25 −1,56 |
×0,50 −3,43 | sıranın sonu −5,72. **Kuyruk ~8,8 kr/pay değerinde** — ücretten (1,7),
makastan (~1,5), sinyal kalitesinden (~1,6) BÜYÜK. Aktörlerin "tahtada görünmeyen
dolum-düzeyi seçimi" dediğimiz kenar BUDUR: bilgi değil **zaman önceliği**.

**KUYRUK SATIN ALINAMIYOR:** bid+1tik −5,47 (post-only RED 270→953), bid+2tik −3,57
(RED 1.413), 100ms varış −5,14 (kuyruk 686→575, sıfıra değil). Fiyat iyileştirme
işe yaramıyor çünkü varışta kitap kaymış; hız işe yaramıyor çünkü önümüzdeki
derinlik milisaniyelerle değil saniyelerle birikmiş.

**KARAR:** kulvar PARK ama artık "bilmiyoruz" değil, ÖLÇÜLMÜŞ DUVAR.
**TETİK:** pencere açılışında (derinlik birikmeden) koyup bekleyen sürekli-kotasyon
politikası + kuyruk yaşı takibi. DEEP@T−299 ölçümümüz bu kapıya değmişti
(+3,1 kr/pay, GA sıfırı içeriyordu) — kuyruk pozisyonu artık ölçülebildiğine göre
o test doğru değişkenle YENİDEN kurulabilir. Bkz [[project-queue-age-scale-20260914]].


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🧲 KUYRUK POZİSYONU = ASIL DEĞİŞKEN (09-15 gece): maker ilk-alım sıranın SONUNDA −5,72 kr/pay GA[−7,90,−3,14], sıranın BAŞINDA **+3,09 GA[+1,16,+5,14]** → kuyruk ~8,8 kr/pay, ücretten/makastan/sinyalden BÜYÜK; aktör kenarı = bilgi değil ZAMAN ÖNCELİĞİ; kuyruk satın alınamıyor (bid+1tik −5,47 & post-only RED 3,5×, 100ms varış −5,14); kaybeden tokenların %100'ü bizi dolduruyor; v1 testim 4 hatalıydı (ileri bakış/rol/saat/post-only), takerOnly=true ile 4,55M bacak yeniden toplandı; TETİK = pencere açılışında koy-bekle sürekli kotasyon](project_maker_ilk_alim_ters_secim_20260915.md)
