---
name: project-research-followup-20260915
description: Derin araştırma (RESEARCH_PROMPT_actor_selection) önerilerinin uygulanması (15 Eyl): H1 ampirik öldü (kendi 4.084 dolumumuzda taker cüzdanı yok), çok-borsa arşivleri indirildi, Kalshi print'leri var, çok-borsalı tahminci + aktör ayrıştırma testi ve Londra hız replay'i koşuldu (sonuçlar EK'te)
metadata:
  type: project
---

**2026-09-15 gece.** Araştırma çıktısı: en olası mekanizma H3+H5 (çok-borsalı 5-30 sn tahmin + colocated icra); H1 belgeyle
ölü (user channel yalnız `taker_order_id` hash veriyor). Uygulama paketi `data/analysis/pm_wave_selector_20260914_v1/ledger/`
(download_archives.sh, kalshi_features.py, multivenue.py) ve `london/latency_replay.py`.

- **H1 ampirik teyit:** `pm_live_mm_15m_20260914_v4/ACCOUNT_*.json` içindeki 4.084 kendi dolum kaydımızda alanlar:
  taker_order_id (hash), own_maker_orders, trader_side, match_time, transaction_hash — taker cüzdanı YOK. H1 kapalı.
- **Veri:** binance-vision spot+perp aggTrades ve metrics (14 Ağu–1 Eyl, 9-10 Eyl), Bybit perp+spot işlemleri indirildi
  (`data/binance_vision/{spot,futures_um}/aggTrades`, `data/external/bybit/`). OKX/Coinbase arşivi yok (404), Binance
  liquidationSnapshot/bookTicker 404. Kalshi BTC15m print'leri `data/external/kalshi_btc15m_trades/TRADES.jsonl`
  (13 Ağu–3 Eyl, 1.990 pazar); önceki tur (08-19) Kalshi→PM 50-250 ms artık öncülük 0,22-0,25 bulmuştu.
- **Test tasarımı:** defter dalgaları (1,48M) + 100 ms çok-borsa akış/getiri/basis/lead + Kalshi özellikleri; gün bölmesi
  10/9; üç model (taban, +çok-borsa, +Kalshi) ve aktör-taklit sınıflandırıcısı; saf tahminci (PM girdisi yok, Binance
  sonraki 10/30 sn) ile dalga skorlama; ölçüt = AUC(aktör dalgası | skor). Londra hız replay'i: derinlik 3/5/6¢ × L 10/120/370 ms × klip 25/300, tahminsiz.

## SONUÇLAR (15 Eyl gece)
- **RTDS kamu kimlikli akış (`wss://ws-live-data.polymarket.com`, topic activity / trades+orders_matched, auth yok):** her işlemi
  proxyWallet+isim+fiyat+boyut+tx ile veriyor, tx başına 2-5 satır (iki taraf da kimlikli). Ama gecikme: CLOB print'inden
  **p50 2,8 sn (orders_matched) / 3,2 sn (trades)** sonra, blok-saati sınıfı. → Gerçek zamanlı karşı taraf kimliği KAMUDA YOK;
  kimlik ancak dalga bittikten sonra. H1'in kamu versiyonu ilk giriş için ölü; hafıza için zincirle aynı (zaten test edildi).
  Paket `pm_rtds_probe_20260915_v1/` (rtds_probe.py, join_tape.py, 1.800 mesaj/4 dk).
- **Londra hız replay'i (`london/latency_replay.py`, tahminsiz, onların tarzı):** 3¢ ve 6¢ derinlikte her gecikmede eksi
  (−0,6…−1,1); 5¢/300 pay: L=10 ms +2,29 [+0,27;+4,23], L=120 +1,84 [−0,11;+3,92], L=370 +1,88 [−0,13;+3,99]; 25 pay +0,5…+0,9
  (GA sıfır). 10 ms ile 370 ms aynı → hız tek başına kenar değil (H5 = enabler doğrulandı); 5¢ hücresi 18 konfigürasyon
  içinden seçilmiş, >1¢ kuralı gereği şüpheli.
- **Kalshi özellikleri:** TRADES.jsonl 51,5M print, YES fiyatı, dalgaların %99'una eşlendi (1 sn çözünürlük, 4 sn dürüst marj).
  Yerel ms Kalshi verisi yalnız 23 Tem–8 Ağu (Dublin); Ağu 15-17 Londra verisi yerelde yok → 50-250 ms artık öncülük testi
  yeni eşzamanlı kayıt ister (Kalshi WS + PM + Binance).

- **ÇOK-BORSALI TAHMİNCİ + AKTÖR AYRIŞTIRMA (`ledger/quick_sep.py`, tam sürüm `multivenue.py`):** 1,48M dalga, 19 taban + 34
  çok-borsa (Binance spot/perp + Bybit perp/spot 100 ms akış/getiri/lead/basis) + 5 Kalshi özelliği; gün bölmesi 10/9.
  Kenar modelleri: test top-%2 −0,34 (taban) / +0,46 (+çok-borsa) / +0,16 (+Kalshi); desil 1→10: −1,9 → +0,9¢;
  **AUC(aktör dalgası | kenar skoru) = 0,46-0,51 → aktör dalgaları ayrışmıyor.** TAKLİT sınıflandırıcısı (aktör katılımını
  tahmin): **test AUC 0,839**, seçtiği dalgalarda aktör payı %25 (taban %2,2) — ama o dalgalarda kalabalığın kenarı **−0,50¢**.
  SONUÇ: aktörlerin HANGİ dalgaya girdiği kamu özelliklerinden tahmin edilebiliyor; o dalgalarda para kazanmak edilemiyor.
  Kenar dalga seçiminde değil, dalga İÇİNDEKİ icrada (seviye/zaman/kuyruk). Araştırmanın go/no-go kapısı: GEÇMEDİ.
  Kalan tek pre-registered test: taklit-seçili dalgalar × 5¢/300 pay derin emir (Londra hız replay'inde tek artı hücre,
  18'den seçilmiş) — >1¢ kuralı ve seçim kuşkusuyla; canlı için değil, replay için.

- **DALGA-İÇİ İCRA (`london/intrawave.py`, Londra 9-10 Eyl, 335k print / 108k dalga, aktör 5.766 print / 497k pay):**
  print seviyesinde aktör kenarı −0,23¢ ≈ kalabalık −0,26 (Eylül sönmesi). Pozisyon (ilk print / <100 ms / 100-300 / 300-1000 / >1 s)
  × derinlik (bb üstü / bb / 1-2¢ / 3-5¢ / 6¢+) hücrelerinde kalabalığın artıda olduğu tek istikrarlı hücre "ilk print" (+0,82) ve
  "bb'de" (+0,23) — bunlar kuyruk-gerçek replay'de zaten eksi çıkan "dokunuşa katıl" hücreleri. Aktör hücreleri gürültülü
  (+22/−25/+29/−11), 1-2¢ ve 3-5¢ derinlikte −7/−9. Taklit modeli Londra'da AUC 0,863, işaretli dalgalarda aktör payı %26;
  o dalgalarda kalabalık HER hücrede eksi (−1,3…−4,5), aktörler bazı hücrelerde +9…+36, bazılarında −28…−50 (n küçük).
  SONUÇ: aynı dalga, aynı pozisyon, aynı derinlik → onların dolumu kazanıyor, kalabalığınki kaybediyor; dalga-içi fark
  kamu koordinatlarında (zaman/derinlik/boyut) DEĞİL. "Onların dalgasında para kazanmayı öğrenmek" bu veriyle desteklenmiyor.
  Aktör boyut imzası: medyan 11 pay (kalabalık 8), p90 192 (61); dalga başında ilk print olma %27; girdikleri dalgalar
  medyan 118 pay (diğerleri 20).
- **Tam çok-borsa koşusu (gün-kümeli GA):** top-%2 kenarı taban +0,00 [−1,51;+1,65] / +çok-borsa −0,45 [−1,67;+0,76] /
  +Kalshi +0,06 [−1,53;+1,28]; AUC(aktör|skor) 0,47/0,46/0,46; TAKLİT AUC 0,840, seçtiği dalgalar −0,50 [−1,11;−0,01]
  (anlamlı EKSİ). Saf tahminci ayrı betikte (`ledger/pure_forecaster.py`).
- **DÜZELTİLMİŞ (Binance spot µs→ms) + SAF TAHMİNCİ (`ledger/fix_bnspot_rerun.py`):** çok-borsa dalga modeli top-%2 +0,24 /
  +Kalshi −1,19, AUC(aktör|skor) 0,456/0,461 → değişmedi. **Saf 10 sn Binance tahmincisi (spot+perp+Bybit perp akış/getiri,
  PM girdisi yok): OOS corr 0,173 (30 sn: 0,093); üst desil +0,71 bp / alt desil −0,69 bp** — Synth'in Kalshi 0,173'üyle aynı
  büyüklük, yani kalabalık-seviyesi tahmin kamu veriyle kurulabiliyor. Aktör dalgalarına uygulanınca AUC 0,550 (ilk kez >0,5,
  zayıf), dalga kenarı üst quintil +0,19 / alt −0,11¢. → Tahmin gerçek, aktör seçimini az açıklıyor, PM'de kuruşa dönüşmüyor.
- **H3+H5 birleşimi (`london/forecast_combo.py`):** 10 sn tahmincisi Londra dalgalarını puanladı; onların tarzı (3/5¢, 25/300 pay, L=120)
  tahminin desteklediği dalgalarda 4/4 hücre eksi (−0,4…−1,6); tek artı 5¢/300 "orta" grupta +3,00 [+0,49;+5,62] ve "karşı"
  grupta +1,43 → tahminle ilgisiz, seçilmiş hücre. REDDEDİLDİ. Tam rapor: `pm_research_followup_20260915_v1/REPORT_TR.md`.
KAPANIŞ: araştırmanın önerdiği her adım (H1 ampirik, RTDS, hız replay, Kalshi, çok-borsa+aktör ayrıştırma, saf tahminci,
dalga-içi icra, tahmin+tarz birleşimi) uygulandı; hiçbiri kamu veriden kopyalanabilir kenar vermedi. Kalan üç iş operatör kararı
(canlı user-WS `owner` denetimi, Kalshi WS kaydı, Londra kutusu).
- **Motor büyütme (`london/car_test.py`):** Bybit spot + Kalshi YES 2/5/30 sn eklenince 10 sn OOS corr 0,1739 → 0,1753 (Kalshi hiçbir
  şey katmıyor; Synth'in "Kalshi bilgi taşır" tezinin artık bilgisi bizim venue setinde yok). Motor tavanı bu veriyle ≈0,17-0,18.
- **'ARABA' TESTİ (tahmin güdümlü dokunuş maker'ı, Londra):** kontrol (her saniye dokunuşa post) −1,67 [−2,49;−0,80] (25 pay) / −0,37 (300);
  tahmin üst-quintil post + medyan altı iptal: −0,66 [−2,57;+1,45] / +0,07; 1¢ altı: −0,24 / +0,58 [−2,65;+3,70]. Motor ≈ +1¢'lik filtre,
  kayıp kuralı sıfıra çekiyor, kâra çevirmiyor. Rapor EK B. KAPANIŞ HÜKMÜ: kamu veri + arşivle araba yok; motor filtre olarak saklanır.

## SATIŞ / HODL / GEÇ-PENCERE SORUSU (15 Eyl 01:30)
- **Hiç satmıyorlar:** zincir defteri 19 gün BTC5m: 0 satış (maker+taker, 100% alım); venue aktivite kaydı son 3 gün: 0 SELL, son 500
  işlem 100% BUY; mo-money ömür boyu 9 SELL (Şubat, NBA), bosona 0. SPLIT 0 (set mint etmiyorlar).
- **Çıkış = MERGE + REDEEM:** eşleşen çiftleri merge ile USDC'ye çeviriyorlar (%94-98'i pencere KAPANMADAN, medyan 83 sn önce);
  tek taraflı kalan resolve'a kadar tutuluyor, kazanan redeem ediliyor. Son 3 gün: mo-money 748 merge (139k çift), 3.026 redeem
  (326k pay); bosona 606 merge, 3.234 redeem. (Data API TRADE sayfalaması 5.500'de 400 veriyor → alım toplamı eksik; merge/redeem tam.)
- **Son 60 sn'de kazanana yığmıyorlar, tersine:** net geç envanter kazanan tarafta yalnız %42-45 (|net|≥50 pay); geç alımların
  ortalama fiyatı 0,39 (Up ve Down eşit) = UNDERDOG. Buna rağmen geç alımlar +5,99 / +5,52 ¢/pay = +$24k / +$22k ≈ toplam kârın yarısı
  (underdog'ları %45 kazanıyor; kalabalığın geç underdog alımları %5-15 kazanıyor, −0,2…−1,3¢).
- **Chainlink referanslı geç hücreler (`pm_actor_live_watch_20260915_v1/late_underdog.py`):** kalabalıkta underdog bandı her hücrede ≈0/eksi;
  favori bandında P_emp−fiyat>0 hücreleri +0,7…+3,5¢ (GA>0, bilinen kapasite-sınırlı hücreler). Aktörler geç alımlarını P_emp−fiyat>+5¢
  hücrelerine yığıyor (%40 vs kalabalık %19) — yani kilitli-TWAP benzeri bir şey kullanıyorlar — ama aynı hücrede +13…+20¢ (kalabalık +1…+4).
- **Canlı izleme (RTDS, 40 dk, `watch.py`):** ilk 3 dakikada 31 dolum, ikisi de 15m penceresinde t=747-754'te Down'ı 0,119-0,22'den alıyor
  (underdog). Pencere sonuçlarıyla dolum başına tablo watch.log sonunda.
- **CANLI İZLEME SONUCU (RTDS, 40 dk, 8 kapanmış pencere/hesap, `pm_actor_live_watch_20260915_v1/watch.log`):** bosona +$17 (+0,84¢/pay,
  2.062 pay), mo-money +$107 (+7,3¢, 1.459 pay). Görülen mekanizma: **her yöne salınan pencerede düşen tarafın derinine bekleyen alış** —
  15m 1789434900'da t=745 Down 0,119×~300, t=843-853 Down 0,45-0,61, t=862 Up 0,21-0,24×300 (kazandı, +77¢/pay), t=868 Up 0,97;
  yani Down@0,12 + Up@0,22 = çift maliyeti ~0,34. Sakin pencerelerde küçük kayıplar (−$15…−$63: underdog'u 0,14-0,30'dan alıp
  kaybetmek). Profil = uzun-oynaklık: çok küçük kayıp, seyrek büyük whipsaw kazancı; hep alım, hiç satış, çiftler merge.
- **KÂR YAPISI DÜZELTMESİ (kamu fiyat yoluyla):** "whipsaw" yorumum YANLIŞTI. Pencere içi Up-fiyat aralığına göre (taker print'leri,
  10 sn kova): TAM DÖNÜŞ pencerelerinde (Up ≥0,70 ve ≤0,30, %28) aktörler KAYBEDİYOR (−2,73¢, −$38k); kâr ORTA hareketli pencerelerde
  (aralık 0,2-0,6: +6…+13¢, +$121k = kârın %152'si); aralık 0,6-0,8: −4,1¢. Kalabalık aynı pencerelerde −0,14…−0,24; yalnız aşırı
  aralıkta (0,8-1,0) +0,63. Konsantrasyon gerçek: en iyi %5 pencere = kârın %153-157'si, %43 pencere zararda, medyan +$11; top-%5
  hariç −1,2¢/pay. Canlı izlediğim 15m penceresi (+$183, tam dönüş) istisnaydı, kural değil.
- **Aralık ayrışımı (aktörler):** 0,2-0,4 → +12,7¢ (tek taraflı %65 pay, 0,72 fiyatta %90 kazanma); 0,4-0,6 → +5,2¢ (0,55'te %64);
  0,6-0,8 → −3,1¢ (çift 1,01, %55 pencere zararda); 0,8-1,0 → +1,4¢. Orta pencerelerde tek taraflı == trend yönü yalnız %53 → yön
  değil, fiyat-üstü kazanma. Rapor §9: `pm_research_followup_20260915_v1/REPORT_TR.md`.
- **COPY-TRADE karşı-olgusalı (Londra 9-10 Eyl, 6.314 aktör dolumu tx-eşli, 15 Eyl akşam):** aktörün kendi dolum kenarı −0,13¢ (Eylül);
  kopyacı 3 sn sonra (RTDS gecikmesi) ask'ten alır: ask − onların fiyatı +1,9¢, ücret 1,75¢ → **COPY-TAKER −3,1¢/pay**; yeni bid'e
  maker olarak (dolarsa, iyimser) −0,9¢. Fillerin %32'sinde ask 3 sn içinde ≥2¢ kaçmış. Copy-trade KAPALI.
- **EMİR-KOPYA (tailgating) karşı-olgusalı, en hızlı mümkün kopya (`pm_actor_live_watch_20260915_v1/quote_copy.py`):** 5.758 aktör
  yerleşimi anonim defterde tanımlandı (yerleşim→dolum medyan 138 ms). Onların seviyesine 10 ms sonra 25 payla katılınca (kuyrukta
  arkalarında): %50 doluyor, dolanlarda **−3,68¢/pay** (180 ms: −3,14; 370 ms: −3,73); onların aynı dolumları −0,05¢. Mekanizma:
  bize ulaşan süpürmeler büyük/bilgili olanlar (ters seçim), onların kârlı küçük kuyruk dolumları bize ulaşmıyor. → Kopyanın hiçbir
  hızı çalışmıyor: 3 sn dolum-kopya −3,1, 10 ms emir-kopya −3,7.

## KENDİ STRATEJİMİZ v0 (15 Eyl akşam, ilk-ilkeler; `pm_own_strategy_20260915_v1_late_fav.py`)
Kural (önceden yazıldı): t∈[250,290] her 5 sn; Chainlink kilitli-TWAP est → P_emp(k) (Ağustos kalibrasyonu); favori k için
P_emp≥0,75 & P_emp−best_bid≥5¢ & bid≤0,92 → best_bid'e post-only 25 pay; kapı düşünce/t=297 iptal; veto: 10 sn tahmin k'ya karşı.
Londra 246 pencere, dürüst kuyruk: KONTROL (favoriye katıl, bid≥0,75) 9 dolum +2,4¢ GA[−18;+17]; KAPI 4 dolum/100 pay **+23,0¢**
[+16,8;+28,3] (4/4 kazandı) ≈ $11,5/gün; +veto 3 dolum +22,3. n=4 → istatistik değil; kapasite sorunu (favori bid çoğu zaman >0,92).
Sıradaki: aynı kural 10 pazarda (çok-pazar tape 30 saat, Binance vekil est) kapasite ölçümü.
- **v0 10 pazarda (`pm_own_strategy_20260915_v1_multi.py`, 2.048 pencere/30 sa, Binance vekil est):** KAPI 74 dolum / 1.143 pay, **−0,40¢**
  [−12,2;+10,9], %68 kazanma @0,69, −$4,6; KONTROL 109 dolum −3,74¢. BTC5m kapı 21 dolum +0,01¢. → Londra'daki +23¢ (4 dolum) gürültüydü;
  v0 kural ne kenar ne kapasite veriyor. Kendi-strateji v0 KAPALI.

## CLONE v1 (15 Eyl gece, `pm_own_strategy_20260915_v1_clone.py`): ölçülen davranışların TAMAMI tek politika, Londra 246 pencere
Parametreler onların ölçümünden (tarama yok): dalga başında dokunuş−5¢, L=120, TTL 1,6 s, |Up-mid−mid(t=5)|>0,30'da kota çekme, son 60 sn
P_emp−bid≥5¢ ise dokunuşa alış, çiftler merge. Sonuç (¢/pay, pencere-GA): FULL 25 pay −0,35 [−2,5;+1,8]; EXC yok +0,15; R-only −0,41;
LT-only +5,3 (505 pay, n yok); **FULL clip 300: +2,02 [−1,0;+5,1], 142k pay, ≈$717/gün; R-only/EXC yok/300: +2,27 [−0,5;+5,1], 167k pay,
≈$950/gün**; artı pencere %44-50; eşleşme %65-74. Yorum: 300 paylık derin reaktif alış = büyük süpürmelere seçilim (ex-ante bilinmez);
aynı "5¢/300" hücresi; GA sıfırı kapsıyor; 2 gün. >1¢ kuralı → çok-pazar tape'te (2.048+ pencere) doğrulanmadan hiçbir şey.
$25 stop ile 300 pay uyumsuz (tek kayıp −$135). Sıradaki: aynı politika 10 pazarda.

- **CLONE v1 çok-pazar (10 pazar, ~30 sa, `pm_own_strategy_20260915_v1_clone_multi.py`):**
  R, clip 25, EXC 0.30           796   73,664    61.2%      -1.26 [  -3.39,  +0.82]   -929.1   40%
  R, clip 25, no EXC             862   88,861    64.7%      -1.43 [  -2.76,  +0.19]  -1274.3   41%
  R, clip 300, EXC 0.30          796  207,662    54.9%      +0.15 [  -3.20,  +3.23]   +318.8   40%
  R, clip 300, no EXC            862  255,715    59.5%      -0.35 [  -2.81,  +2.03]   -890.6   41%
  → Londra'nın 5¢/300 hücresi (+2,0…+2,3) örneklem dışında TEKRARLANMADI (300/EXC +0,15 [−3,2;+3,2]); 25 pay −1,3/−1,4. Clone v1 KAPALI.


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🅿️ AKTÖR-KOPYA KULVARI PARK (09-15 03:00): araştırma takibi — H1 ampirik ölü, RTDS kimlik 2,8-3,2 sn geç, hız=enabler, çok-borsa+Kalshi modeli aktör AUC 0,46, taklit AUC 0,84 ama o dalgalarda −0,5¢, dalga-içi fark görünmez, saf 10 sn tahminci corr 0,17 = +1¢ filtre (araba yok); satış yok/merge+redeem; kâr %5 pencereden, orta-hareketli pencerelerde, tam dönüşte zarar. Yeniden açma: canlı user-WS `owner` denetimi / Kalshi WS kaydı / Londra kutusu (operatör kararı)](project_research_followup_20260915.md)
