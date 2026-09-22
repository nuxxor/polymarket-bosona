# Bosona — BTC5dk dışı, öncelik BTC15dk: bağımsız inceleme (Fable, 21 Eylül 2026)

Dizin: `R/fable_review_20260921/` (R = `/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921`).
MAIN/R/F/S salt okunur kaldı; `candidate.py` ve `protocol.json` değişmedi; gerçek emir, shadow, ücretli servis, süreç müdahalesi yok.
Ön kayıt `plan.md` (18:45 ve 18:58 UTC), ajan brifingi `AGENT_BRIEF.md`, kod `code/`, sonuçlar `results/`, ham indirmeler `raw/`, alt ajan çalışmaları `agents/`.
Zaman damgaları UTC; yerel = UTC+3.

Hüküm etiketleri: **DOĞRULANDI** (kendi kodumla yeniden üretildi ve bağımsız kaynakla uzlaştı), **GÖZLEMSEL DESTEK** (tutarlı ama nedensel/kesin değil), **KARŞI KANIT**, **KANIT YETERSİZ**, **ÖLÇÜLEMİYOR**.

---

## 1. Kısa karar özeti

**En önemli beş bulgu**

1. **Bosona'nın BTC15dk dolumları ağırlıkla maker (pasif) dolumdur; "geç ekleme" bir karar anı değil, kotasyon dolumudur.** 5.441 dolumun 4.387'si maker (ücret imzası: `usdcSize − size·price` = 0), 1.054'ü taker (= 0,07·size·p·(1−p)); kapsam %100, belirsiz kayıt 0. Sunucu `takerOnly=true` bayrağıyla 8 piyasada 156/156, zincir `OrdersMatched` rolüyle 303/303 uyum. Geç eklemelerin (600–899 sn, `add`) 1.099/1.173'ü maker. — DOĞRULANDI.
2. **Mevcut aday yanlış uygulama modelini test ediyor.** `btc15_inventory_discount_v0` %100 taker (ask+ücret) alım varsayar; t=180'de olasılık filtresiyle giriş yapar. Oysa (a) Bosona'nın ilk dolumlarının 557/598'i maker; (b) olasılık modeli 720–300 sn kalanken piyasa fiyatından **daha kötü** kalibre (Brier 0,2167 vs 0,2115; 0,1868 vs 0,1829), yalnız son 300 sn'de üstün. Adayın Bosona'ya benzememesi parametre değil mekanizma farkıdır. — DOĞRULANDI.
3. **Geç maker ekleme kârı sağlam değil, 10 piyasada yoğun.** +2.925,81 $ (267 piyasa); en iyi 3 hariç +1.693,61; **en iyi 10 hariç −4,89 $**. BTC15dk toplam kârının (4.428,55 $) %86'sı 10 piyasadan; en iyi 20 hariç −1.847,80 $. Yeni gerçek defterli dönemde (14:30–18:00 UTC, 14 piyasa) geç ekleme −254,17 $; sonraki 10 tam piyasada (18:00–20:30) Bosona toplam +310,29 $ ama maker −11,66 / taker +321,94, geç maker ekleme −20,23 $. — DOĞRULANDI (yoğunlaşma), KARŞI KANIT (geç ekleme yeni dönemde).
4. **Kotasyonlar saniyeler içinde vurulan taze emirler; kuyruk konumu belirleyici ve 1 sn REST bandıyla ölçülemiyor.** S döneminde maker dolumlarında dolum fiyatındaki seviye 1–10 sn önce 80/116 dolumda görünüyor (36'sında hiç görünmüyor); seviye yaşı medyan 4,0 sn, ≥30 sn yalnız 9. Zincirde çok dolumlu 51 emrin kamu zaman aralığı medyan 0 sn, maks 9 sn; 600 sn'den önce dolan hiçbir emir 600 sn sonrasında devam etmiyor (0/105). Ön kayıtlı kuyruk-konumlu pasif replay'de dokunuşa konan kotasyonların 88/94'ü yalnız fiyat seviyeyi aşınca doluyor (saf adverse selection). — DOĞRULANDI (ölçüm), ÖLÇÜLEMİYOR (kuyruk önceliği).
5. **Önceki araştırmanın kontrol tasarımı ve replay'i yapısal kusurlu.** `candidate.replay()` uygulama fiyatını karar sonrası ≤90 sn'lik gelecek örnekten alıp o örneğin "edge"ine göre işlemi atlıyor (look-ahead); eşleştirme kaliperleri (3¢/30 sn/25 $) sonuçtan sonra eklenmiş ve kronolojik sonuç kalipere göre −11,62 ile +7,10 arasında değişiyor; "ekleme yok" kontrolleri "emir yok" değil "satıcı gelmedi" demek (maker mekanizmasıyla akış seçilimi). — DOĞRULANDI (kod okuması + yeniden hesap; ajan sayıları doğrulama turunda).

**Hangi eski iddia değişti:** "BTC15dk geç eklemelerinde tekrar eden avantaj var" → mekanik olarak "Bosona'nın taze bid'leri son üçte birde sık vuruluyor"; kâr 10 piyasaya yoğun, yeni dönemde negatif. "Tamamlama yalnız ucuz çift için" zaten çürüktü; şimdi rolüyle netleşti: tamamlamalar taker-ağırlıklı (862 taker / 820 maker kayıt; taker tamamlama nakit-PnL −3.084,65 $) ve en kötü sonucu iyileştiren risk azaltımı (870/895 kayıtta iyileşme, toplam +30.673 $ en kötü sonuç iyileşmesi). H1/H2 lojistik kıyası ise gözlem birimi hatası taşıyor (etiket = "bid'e satış geldi").

**Stratejiyi çözmeye ne kadar yakınız:** Mekanizma ailesi netleşti (M1 taze pasif kotasyon + M2 taker risk azaltımı), ama kâr üreten fiyatlama/boy/iptal kuralı ve kuyruk önceliği bu veriyle **tanımlanamıyor** (NOT IDENTIFIABLE). Aynı kamu dolumlarını "dokunuşa katıl", "model fiyatından iskonto", "karşı akışa tepki" kuralları birlikte üretebilir; ayrım için emir yerleştirme/iptal zamanları gerekir ve bunlar kamu verisinde yok.

**Önce ne yapılmalı:** (1) Adayın taker+t=180 tasarımını BIRAK; (2) `role_classifier` etiketini bütün BTC5dk-dışı analizlere ekle ve H1/H2/kontrol tablolarını rol ayrımıyla yeniden kur; (3) tek sonraki deney olarak WebSocket L2 delta + kamu piyasa-geneli baskı kaydıyla **kuyruk-konumlu pasif kotasyon replay'i** (bölüm 7) — ölçüm protokolü hazır, 1 sn REST bandı yetersiz.

---

## 2. Kapsam, veri ve yeniden çalıştırılan hesaplar

| Kaynak | Kullanım | Kesim/hash |
|---|---|---|
| `R/results/fills.json`, `windows.json`, `universe.json` | 14.014 dolum / 3.503 piyasa; rol etiketi eklendi | F/baseline_hashes.json ile aynı (fills c397e9ac…, windows 8e9f02e4…) |
| `R/raw/activity*.json`, `activity_checks/` | D1 bağımsız muhasebe yeniden üretimi | — |
| `R/raw/btc15_context.json` | 20.533 bağlam; kalibrasyon | manifest R/raw/btc15_context_manifest.json |
| `R/raw/histories/` | kamu fiyat vekili (ask/bid DEĞİL) | — |
| `S/raw/book_validation_prefix.json.gz` | 14:25:08–18:05:40 UTC donmuş 1 sn L2 bandı | ad5bccfc… (S/manifest.json) |
| `F/raw/books_72h/books_20260921_14…20.jsonl.gz` | S sonrası defter; son dosya açık uçlu | okunan son snapshot 1790022811196 (20:33:31 UTC) |
| `MAIN/data/tape_cl_direct/cld_20260921_13…18.jsonl.gz`, orijinal kaydedici `/home/taygun/Masaüstü/polymarket/data/tape_cl_direct/cld_20260921_16…20.jsonl.gz` (salt okunur) | yeni dönem Chainlink (rcv/obs) | cld_20 açık uçlu, kısmi okundu |
| Kamu API (önbellekli, ≥1 sn aralık) | `/trades` takerOnly, piyasa-geneli baskılar (S 15 piyasa + sonrası 24 piyasa; sayfa kayması olan 1 piyasa yeniden indirildi, eski kopya `.stale`), activity, Gamma | `raw/taker_only_checks/`, `raw/market_trades/`, `raw/new_period/` |
| Polygon public JSON-RPC (ajan D3) | 303 receipt, 34 piyasa | `agents/D3_order_identity/raw/receipts/` |

Kod (hepsi `code/`, ruff temiz, çalıştırıldı): `role_classifier.py` (+ öz-test), `btc15_role_tables.py`, `s_period_role_book.py`, `s_period_level_age.py`, `passive_replay.py` (+ `test_passive_replay.py` 5 sentetik regresyon), `fetch_new_period.py`, `new_period_summary.py`, `cross_asset_table.py`, `paths.py`, `calibration_check.py`.

---

## 3. Soru 1–6 cevapları

### 3.1 Neyi gerçekten açıkladık, neyi dolumlardan hikâye yazdık?

**Açıklanan (DOĞRULANDI):** Muhasebe (598 piyasa, 5.441 dolum, +4.428,55 $; ödeme sınırı ihlali 0; MERGE/REDEEM tekrarları düzeltilmiş), resmî mekanizma (816/816 priceToBeat/finalPrice uyumu; saatlik 204/204 Binance mumu), referans gözlenebilirliği (S+1,4 sn medyan, maks 2,5 sn), FIFO parça toplamlarının PnL ile uzlaşması.

**Hikâye olan:** "Geç ekleme = değer fırsatına tepki / t=600 civarı karar" (H1) ve "envanter maliyetine göre ekleme kararı" (H2). Her iki modelin etiketi, ~%94'ü maker olan dolumlardır; yani "sonraki 30 sn'de Bosona'nın bid'ine satıcı geldi mi?" sorusunu tahmin ediyorlar. Adayın `ceiling_pass` (fiyat ≤55¢) özelliğinin AUC 0,632'yi taşıması mekaniktir: ucuz taraf = düşen taraf = bid'e satış gelen taraf. Aynı biçimde "ucuzlayan/pahalılaşan yöne ekleme" tabloları bir kararı değil, fiyat hareketiyle vurulan bid'leri sınıflandırıyor.

### 3.2 Bizi yanıltan hatalar

| # | Hata | Sınıf | Kanıt | Etki |
|---|---|---|---|---|
| H-1 | Dolum = karar (gözlem birimi) | doğru hesabın yanlış yorumu | rol dağılımı; F/RAPOR'un "74 dolumda nakit fiyat farkı" notu tam olarak 74 taker geç eklemedir | H1/H2, eşleştirme, no-add kontrolleri, aday tasarımı |
| H-2 | Taker uygulama modeli | yanlış uygulama modeli | aday %100 taker; Bosona maker %71 (pay) | S döneminde aynı dolumlar taker olsaydı 116 maker dolumda ≈ −243 $ (D5 hesabı) |
| H-3 | `candidate.replay()` look-ahead | yanlış uygulama modeli | `candidate.py:162-179`: uygulama fiyatı `now+0,25…+90 sn` sonraki örnek; "execution_value_lost"/"price_limit" o gelecek fiyata bakarak işlemi atlıyor | 36 senaryonun tamamı; 21 giriş/1 ekleme sayıları bu filtreye bağlı |
| H-4 | Kaliperler sonradan | yetersiz/seçilmiş örneklem | F/plan.md:26-30 ("kalite düzeltmesi"); kronolojik fark kalipere göre −11,62 / +7,10 (dar) / −8,33 (gevşek) (D4 yeniden çalıştırma) | 18–20 Eylül karşılaştırması kanıt değil |
| H-5 | "Ekleme yok" ≠ "emir yok" | yanlış kontrol grubu | maker mekanizması; S döneminde işlemsiz 2 pencerede Bosona-benzeri bid izi yok (D7) ama bu 1 sn örnekleme sınırıyla ölçülemez | no-add kontrolleri akış seçilimi |
| H-6 | Olasılık modeli erken dönemde piyasadan kötü | doğru hesabın yanlış yorumu | `results/calibration_check.json` | t=180 "edge≥5¢" filtresi gürültü seçiyor |
| H-7 | Rol sınıflandırıcıda mutlak tolerans | aritmetik | kendi ilk sürümümde 0,002·qty mutlak tolerans p<0,03 / p>0,97'de taker'ı maker sayıyordu; ücrete göreli toleransla 92/14.014 kayıt değişti (BTC15dk 9) | düzeltildi; sonuçlar bu sürümle |
| H-8 | protocol.json her `report.py` çalıştırmasında yeniden yazılıyor | kodda yazılı ama korunmayan kural | `R/report.py:86` (D10) | donmuş protokolün üzerine yazma riski |
| H-9 | Portföy limitleri/−10 $ kesici kodda yok | kodda yazılı uygulanmayan kural | `candidate.py:allowed()` yalnız piyasa limitleri | tek-piyasa replay'de etkisiz, ileri deneyde eksik |

Aritmetik/veri hatası bulunmadı: BTC15dk tablosu, örnek piyasalar (+635,16 / −461,20), BTC saatlik/ETH5/SOL5 toplamları bağımsız Decimal kodla birebir (ajan D1; RAPOR sayıları D10 ve D9 tarafından kaynaklarla eşleştirildi). D9'un "en iyi 3 hariç 4.648 $" sayısı hatalıdır (toplamdan büyük olamaz); doğru değer 3.025,27 $ (`results/btc15_role_phase_table.json:total_concentration`).

### 3.3 Emir seçimi mi, bekleyen emrin dolması mı, pozisyon yönetimi mi?

Üçü de var, ama ağırlık ve rol farklı:

| Faz | Kayıt maker/taker | Pay maker/taker | Nakit PnL maker/taker | Yorum |
|---|---:|---:|---:|---|
| İlk giriş | 557 / 41 | 37.135 / 5.876 | +2.359 / −34 | pasif giriş |
| Ekleme (aynı yön) | 2.682 / 110 | 124.129 / 13.664 | +3.904 / +1.359 | pasif büyüme |
| Tamamlama (karşı yön) | 820 / 862 | 34.670 / 66.010 | −499 / −3.085 | aktif risk azaltımı |
| Karma / yeniden açılış | 328 / 41 | 25.242 / 6.452 | +257 / +166 | |

Bekleyen emrin dolması: evet ama "uzun süre bekleyen" değil; taze kotasyon (seviye yaşı medyan 4 sn). Pozisyon yönetimi: evet, taker tamamlamalar açık riski küçültüyor (895 taker tamamlamanın 870'inde en kötü sonuç iyileşiyor). Emir "seçimi" (fiyat/zaman/boy): kamu verisiyle gözlenemiyor; yalnız dolan kısım görülüyor.

### 3.4 Aday neden Bosona'ya benzemiyor?

- **Rol:** aday taker, Bosona maker (ilk giriş 557/598 maker). Aynı fiyattan taker dolmak ücret + spread maliyeti getirir.
- **Zaman:** adayın tek giriş anı t=180; Bosona ilk dolum medyanı 151 sn ama 30–800 sn'ye yayılıyor ve bu bir "karar anı" değil, ilk vurulan bid.
- **Fiyat/olasılık:** adayın "model olasılığı − ücretli maliyet ≥ 5¢" kapısı, modelin piyasadan kötü olduğu bölgede (720–300 sn kalan) çalışıyor. D7'nin küçük örnekli kontrolü (36 pencere) ilk yönle model olasılığı arasında uyum bulmuyor; bu sayı zayıf (KANIT YETERSİZ) ama kalibrasyon tablosuyla tutarlı.
- **Envanter yolu:** aday 5 pay/10 net/15 $ ile erken neti sıfırlıyor; Bosona yüzlerce pay biriktirip taker ile hedge ediyor. Adayın ekleme fırsatlarını "yapısal olarak silmesi" (7 girişin 4'ünde ekleme öncesi net=0) doğru ama ikincil.
- **Gerçek defterde aday (P0, S dönemi 14 piyasa):** 2 piyasada işlem, 3 dolum, −1,30 $; kör 10 piyasada (18:00–20:30) 0 giriş (karar defteri tek taraflı/bayat 11, Chainlink eksik 1); 17:00–18:00'deki 1 piyasada 2 dolum +0,53 $ (`results/replay_*/replay.json`). Look-ahead düzeltilmiş tarihsel senaryo için bölüm 3.7.

### 3.5 Hemen düzelt / araştır / bırak

| Öneri | Etki | Doğrulama koşulu |
|---|---|---|
| **BIRAK:** t=180 taker giriş + t=600 ekleme + edge≥5¢ (aday v0) | Bosona'yı modellemiyor; gerçek defterde 14 piyasada 2 giriş | — (donmuş dosya aynen kalır; yeni sürüm ayrı) |
| **BIRAK:** H1/H2 lojistik kıyası ve no-add eşleştirmesi mevcut haliyle | etiket = akış, kontrol = akış yok | rol etiketiyle yeniden kurulup aynı sonuç çıkarsa geri alınır |
| **DÜZELT:** `candidate.replay()` uygulama fiyatını karar anındaki/önceki örnekten al, gelecek örnekle filtreleme | 36 senaryo; sayılar değişir | düzeltilmiş replay'de giriş/ekleme sayıları ve PnL raporlanır |
| **DÜZELT:** `report.py` protokolü yeniden yazmasın; protokol hash'i test edilsin | donmuş protokol bütünlüğü | sha256 kontrolü checks.json'a |
| **DÜZELT:** rol etiketi (`role_classifier`) bütün fill tablolarına; her PnL tablosu maker/taker ayrımıyla | yorumlar değişir | 156/156 sunucu, 303/303 zincir uyumu regresyonu |
| **ARAŞTIR:** kuyruk-konumlu pasif kotasyon (bölüm 7) | tek ayırıcı deney | kötümser sınır alt CI>0 |
| **ARAŞTIR:** taker risk azaltımının (M2) kural şekli: hangi açık riskte, hangi kalan sürede spread geçiliyor | 862 taker tamamlama | lojistik/kural modeli, rol etiketli; gün-kümeli CI |

### 3.6 En fazla iki mekanizma ve tek deney

Ön kayıt (plan.md 18:45 UTC, sonuçlar görülmeden): **M1** taze pasif kotasyon; **M2** taker risk azaltımı. Test sonuçları bölüm 6; deney bölüm 7.

### 3.7 Eleştirmen ve boşluk turu (8 ek ajan; doğrulama etiketleri bölüm 8)

- **Look-ahead düzeltilince aday 21 değil 180 giriş yapıyor** (`agents/gap_candidate_replay_lookahead_fix/`): karar filtreleri karar anı fiyatıyla, uygulama sonraki örnekle. `discount/0¢/managed`: 180 giriş, 4 ekleme, 139 tamamlama, PnL +28,79 $ (en iyi 3 hariç +15,53; keşif +18,82 / kronolojik +12,63 / 21 Eyl −2,66; piyasa CI [−12,5; +68,3]); 2¢ kayma +11,37; 5¢ kayma −4,27. Eski "21 giriş / 1 ekleme" tablosu (F/RAPOR bölüm 2) ve "aday neden bu kadar az giriyor" tartışması look-ahead filtresinin eseri. Düzeltilmiş senaryo yine 1 dk'lık fiyat vekiliyle taker varsayımı; ekonomik kanıt değil. — DOĞRULANDI (ajan; yeniden koştu, regresyon testi var).
- **Kapanış sınırı:** işlem 20 Eyl 12:44:19 UTC'de tamamen durmuş; sonrasında açılan 92 piyasanın hepsi işlemsiz, öncesinde 724 piyasada %82,6 işlemli. Öncesindeki 126 işlemsiz pencerenin %77,7'si Pazartesi/Pazar; 09–13 UTC'de işlemsizlik %25–34. — DOĞRULANDI (benim 93 pencere hesabımla uyumlu).
- **İlk giriş zamanı** sabit değil (medyan 151 sn, IQR 318 sn, 3–1.886 sn); oynaklık/uzaklık/edge ile korelasyon yok (|r|<0,15); saat etkisi (55–303 sn medyan); %13,9'u ilk 10 sn'de. Maker için beklenen: ilk dolum karşı akış geldiğinde olur. — GÖZLEMSEL DESTEK.
- **S döneminde tamamlamalar da maker-ağırlıklı:** sonucu kesin 32 tamamlamanın 19'u maker, 13'ü taker (açık piyasa dahil 21/34; ajanın "%61,8" sayısı doğrulama turunda düzeltildi); "ask geçiş backtest" çerçevesi bu dönem için yanlış. — DOĞRULANDI (kendi hesabım).
- **Kotasyon yaşı ve sonuç (S, küçük n):** ajan, 30 sn+ sabit bid'den dolan 24 maker dolumunun 22'sinin kaybeden tarafta, yalnız t−1'de görünen 16 dolumun 11'inin kazanan tarafta olduğunu bildirdi. Doğrulama turu bulguyu ÇÜRÜTTÜ: iki grup farklı piyasalarda, sonuç dağılımı karıştırıcı ve "post-mid≈0,50" spread artefaktı. — ÇÜRÜTÜLDÜ (2/3 mercek).
- **Eşzamanlılık / "aynı bot" sorusu:** aynı anda medyan 8 grupta açık pozisyon (maks 17; sayı doğrulandı, "protokol limiti uygulanıyor" yorumu çürütüldü); 13.948 tx'te çapraz-grup batching 0 (hayatta). Ajanın "kayıp sonrası diğer gruplar −%5,6" bulgusu 3/3 mercekte ÇÜRÜTÜLDÜ: yalnız en büyük 20 olay kullanılmış, 190 olayın tamamında diğer grupların aktivitesi +%39,5. Gruplar arası bağ zayıf; tek/ayrı bot ayrımı çözülmez. — GÖZLEMSEL DESTEK (yalnız batching ve çakışma sayıları).
- **Saatlik mekanizma:** ETH/SOL/BNB saatlik 561 piyasada priceToBeat/finalPrice Binance 1H mumuyla %100; BTC ile aynı kural. — DOĞRULANDI.
- **M1/M2 piyasa bazlı sınıflama (ajan):** 598 piyasanın %72,2'si M1-baskın, %24,2'si M2-baskın. Ajanın "M2 başarısız (tamamlama PnL negatif)" yorumu, promptun uyardığı hataya düşüyor: nakit-PnL negatifliği risk azaltımının başarısızlığı değil; en kötü sonuç iyileşmesi ölçüsü pozitif (bölüm 3.3). — yorum reddedildi, sınıflama betimleyici.

---

## 4. Varlık × süre tablosu (BTC5dk hariç; kaynak `results/cross_asset_table.md`)

| Grup | İşlemli/evren | Dolum | PnL $ | En iyi 3 hariç | En iyi 10 hariç | Maker payı (pay) | PnL maker / taker | Taker tamamlama PnL | İlk giriş yaş/fiyat medyan | İlk giriş maker | İki yön % | Tepe risk medyan $ | Sonda açık pay medyan |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC 15dk | 598/816 | 5.441 | 4.428,55 | 3.025,27 | 611,60 | 0,706 | 6.021 / −1.593 | −2.789 | 151 sn / 48,9¢ | 557 | 71,2 | 101,64 | 148,0 |
| BTC saatlik | 193/204 | 1.494 | 3.351,10 | 2.095,78 | 620,87 | 0,887 | 2.200 / 1.152 | +1.152 | 174 sn / 47,0¢ | 193 | 71,0 | 81,20 | 70,7 |
| ETH 5dk | 643/2.448 | 1.673 | 1.529,10 | 693,86 | 190,85 | 0,851 | 1.510 / 20 | −223 | 119 sn / 46,0¢ | 612 | 17,7 | 13,50 | 36,0 |
| ETH 15dk | 131/816 | 210 | 85,69 | 11,10 | −128,39 | 0,949 | 113 / −28 | −28 | 202 sn / 53,0¢ | 131 | 9,9 | 13,50 | 26,9 |
| ETH saatlik | 136/204 | 700 | −155,38 | −328,96 | −545,92 | 0,780 | −96 / −60 | −56 | 657 sn / 58,5¢ | 135 | 75,7 | 30,03 | 3,3 |
| SOL 5dk | 413/2.448 | 620 | 1.307,11 | 1.111,38 | 762,75 | 0,977 | 1.258 / 49 | +49 | 154 sn / 76,0¢ | 413 | 9,0 | 21,66 | 32,5 |
| SOL 15dk | 154/816 | 370 | 167,97 | 108,73 | 15,42 | 0,899 | 228 / −60 | −60 | 204 sn / 80,0¢ | 154 | 39,6 | 23,85 | 24,3 |
| SOL saatlik | 81/204 | 213 | 239,69 | 132,29 | −40,94 | 0,934 | 237 / 3 | +3 | 747 sn / 68,0¢ | 81 | 37,0 | 21,50 | 25,6 |
| BNB saatlik | 153/— | 1.026 | 623,48 | 479,76 | 309,14 | 0,927 | 676 / −52 | −52 | 1.177 sn / 48,0¢ | 153 | 60,8 | 17,62 | 16,1 |
| DOGE 5dk | 219/— | 276 | 526,07 | 467,23 | 357,15 | 0,972 | 503 / 24 | +24 | 160 sn / 80,0¢ | 219 | 11,0 | 11,62 | 18,0 |
| XRP 5dk | 336/— | 475 | 678,74 | 543,57 | 330,62 | 0,974 | 685 / −6 | −6 | 188 sn / 53,0¢ | 336 | 11,0 | 8,05 | 16,8 |

Evren yalnız ana sekiz grupta tam (işlemsizler dahil); diğerlerinde yalnız işlemli piyasalar. PnL = resmî ödeme − API nakit maliyeti; rebate/sabit gider hariç. BTC15dk ücret: taker ücreti 1.253,07 $ ödenmiş; maker rebate üst sınırı (0,2·0,07·Σq·p(1−p)) 541,84 $; Gold %18 taker iadesi 225,55 $ — üst sınır satırlarıdır, PnL'ye dahil değildir.

**Okuma:** Maker ağırlığı bütün gruplarda (BTC15dk en düşük: 0,71 pay). BTC15dk ve BTC saatlik dışındaki gruplarda ilk giriş %100 maker. Taker tamamlama nakit-PnL'si BTC saatlik hariç her yerde ≤0; BTC saatlikte taker tamamlama +1.152 $ (Binance 1H mekanizması, geç giriş, %71 iki yön) — mekanizma farkı, tek "bot" iddiası için kanıt yok (KANIT YETERSİZ). BTC15dk kârı en yoğun grup: en iyi 10 hariç 611,60 $ (toplamın %14'ü), en iyi 20 hariç −1.847,80 $; 598 piyasanın 315'i pozitif, medyan +2,58 $.

Gün bazında BTC15dk maker/taker: 13 Eyl +762/−704, 14 +112/+117, 15 +513/+1.486, 16 −459/+239, 17 +1.340/−617, 18 +3.280/−993, 19 +1.010/−613, 20 −536/−507. Tek gün (18 Eyl) maker kârının %54'ü.

**Piyasa seçimi:** işlemsiz 218 pencerenin çoğu blok halinde: 14 Eyl 10:45 (9 pencere), 14 Eyl 13:15 (10), 20 Eyl 09:00 (14) ve **20 Eyl 12:45'ten 21 Eyl 12:00'ye 93 ardışık pencere (≈23 saat)**. RAPOR'un "21 Eyl 00–12 UTC'de dolum yok" cümlesi doğrudur (48 piyasa, 0 işlemli). Yani seçim pencere bazlı bir filtre değil, açık/kapalı rejimdir; 18–20 Eyl "kronolojik kontrol" BTC15dk için fiilen 20 Eyl 12:45'te bitiyor.

---

## 5. BTC15dk ayrıntı

### 5.1 Rol × faz (kaynak `results/btc15_role_phase_table.json`)

Bölüm 3.3 tablosu. Ek: maker dolumlarında ¢/pay +2,72; taker −1,73. Geç maker ekleme fiyat dilimine göre ¢/pay: 0,0x −0,8; 0,1x +3,0; 0,2x +8,9; 0,3x +6,7; 0,4x +15,6; 0,5x +11,5; 0,6x +2,7; 0,7x −4,5; 0,8x +8,5; 0,9x +6,1 (n 43–153/dilim; keşif tablosu, kural değil).

Kamu fiyat vekiliyle dolum sonrası hareket (ask değil): maker dolumdan 60/120/300 sn sonra token fiyatı ortalama +0,6 / +2,4 / +0,4¢ (medyan +0,5 / +1,5 / −1,95). Sistematik adverse selection görünmüyor ama vekil 1 dk'lık örnek; S döneminde gerçek defterle D8 ölçümü eksik kaldı (ajan zaman kısıtı) — ÖLÇÜLEMİYOR (bu turda).

### 5.2 Gözlem birimi: dolum → transaction → emir → rol (kaynak `results/order_identity_recomputed.json`; ajan D3 receipt'leri)

34 piyasa, 303 activity satırı, 303 transaction, 303 Bosona'ya ait zincir dolumu (receipt'lerdeki 1.076 olayın 773'ü karşı taraflara ait; ajanın "tx başına 3,55 dolum" başlığı sahip filtresi hatasıdır ve çürütülmüştür). Miktar/nakit uzlaşması 303/303; ücret-imzası rolü ↔ zincir rolü 303/303 (262 maker, 41 taker). 303 dolum 165 emirden: 114 emir tek dolum, 51 emir 2–17 dolum (4.474 pay / 17.766 pay). Çok dolumlu emirlerin kamu zaman aralığı medyan 0 sn, maks 9 sn. 600 sn öncesinde dolan bir emrin 600 sn sonrasında devamı: 0; 600+ sn'de ilk dolan emir: 105. Aynı saniye/5/10 sn paketleme orderHash'ten 5–7 kat az "emir" sayar (D3-F5; ajan) — paketleme emir kimliği değildir. Emir yerleştirme/iptal zamanı zincirde yok — ÖLÇÜLEMİYOR.

### 5.3 Yeni gerçek defterli dönem

S kesiti (14:30–18:00, 14 tam piyasa): 126 dolum, 111 maker / 15 taker; PnL +165,63 $ = maker +570,35 / taker −404,72; geç ekleme 54 dolum (52 maker) −254,17 $ (S sayıları birebir yeniden üretildi).
S sonrası (18:00–20:30, 10 tam piyasa, 7 işlemli): 35 dolum, 28 maker / 7 taker; PnL +310,29 $ = maker −11,66 / taker +321,94; geç ekleme 12 dolum (12 maker) −20,23 $. İlk 4 piyasada −87,00 $ iken sonraki 6 piyasada taker dolumlarıyla toplam pozitife döndü; maker ve geç-ekleme katkısı hâlâ negatif. (`results/new_period_blind.json`, kesim: son tam snapshot 20:33:31 UTC)

Defter ilişkisi (S, `results/s_period_fills_role_book.json`, `s_period_level_age_summary.json`): maker dolumlarında fiyat ≤ best bid(t−1) 83/116, = best bid 63/116; t−3'te = best bid 34/116. Seviye (≥ qty boy) 1–10 sn önce görülüyor: 80/116; ilk görülme gecikmesi 1 sn: 58, 2 sn: 15, 3 sn: 6; seviye yaşı medyan 4,0 sn, p75 9,0 sn, ≥5 sn 30, ≥30 sn 9. Taker dolumlarında fiyat ≥ best ask(t−1) 9/15 (kalan 6'sı 1 sn içinde hareket eden defterle tutarlı). Kamu activity zamanı blok zamanıdır ve eşleşmeden ~2–3 sn sonra gelir (BTC5dk emir kimliği çalışmasında 253,3 → 256 sn); bu yüzden "t−1 defteri" çoğu zaman eşleşme sonrasıdır — ölçümler 1–10 sn taramayla yapıldı.

Defter kalitesi: 13.219 çift snapshot / 26.438 taraf; %90,89 taze-iki taraflı-≤3¢-5 pay (S sayıları D8 tarafından doğrulandı); 2 zaman aşımı; en uzun boşluk 5,06 sn.

### 5.4 Somut yollar (kaynak `results/paths.json`; sütunlar: yaş, yön, pay, fiyat, rol, faz, önce/sonra en kötü sonuç, model olasılığı t−5)

**Kazanç — btc-updown-15m-1789708500 (Up kazandı, +635,16 $, 31 dolum, 29 maker/2 taker):** 79 sn Up 8,5 @0,41 maker (ilk; model 0,45); 375–522 sn Up 12,5/4,2/50 @0,25–0,28 maker (model 0,27–0,32); 823 sn **Up 232 @0,30 maker, model 0,101 (edge −0,20)** → +162,5; 835 sn Up 300 @0,595 **taker** (+116); 843 sn Up 300 @0,416 maker (+175); 847 sn Down 15 @0,60 taker tamamlama (−9,3, en kötü sonuç −488→−483); 852 sn 16 parça Up @0,599 maker (model 0,343). Tepe en kötü sonuç −586,79 $. Modelin "edge" işareti Bosona'nın alımlarıyla ters; kâr fiyat hareketi + sonuçtan.

**Kayıp — btc-updown-15m-1789564500 (Down kazandı, −461,20 $, 15 dolum, 11 maker/4 taker):** 279 sn Down 69 @0,42 maker; 321 sn Up 69 @0,40 **taker** tamamlama (çift 0,8168, kilit +11,25); 604 sn Down 232 @0,80 taker yeniden açılış (model 0,82); 669–670 sn Up 120+112 @0,56/0,61 taker tamamlama (çift maliyeti >1: −46,6/−49,1 çift; en kötü sonuç −177→−84); 777–778 sn Up 185+76 @0,79 maker (model 0,67–0,70) → −206; 849 sn Up 300 @0,54 maker (model 0,765, edge +0,225) → −162; 855 sn Up 22 @0,39 maker (model 0,83). Model son dakikada Up'ı %77–83 görürken Down kazandı; fiyat 78 sn'de 0,79→0,39 çöktü.

**Yeni dönem kayıp — btc-updown-15m-1790001900 (Up kazandı, −221,93 $, 20 dolum, 18 maker/2 taker):** 399 sn Down 300 @0,12 maker (seviye 9 sn önce görünüyor); 753–790 sn 12 küçük Down maker dolumu @0,055–0,099 (best bid 0,04–0,097; çoğu seviye 1 sn bandında görünmüyor); 802 sn Down 300 @0,10 **taker** (best ask t−5 0,089); 805 sn Down 81 @0,397 maker; 819 sn Down 300 @0,30 taker (best ask t−5 0,22) → −94,4. En kötü sonuç −222 $'a büyüyerek gerçekleşti. Çöken tarafa hem pasif hem aktif alım; risk azaltımı değil, yön riski.

**Yeni dönem kazanç — btc-updown-15m-1790001000 (Up kazandı, +200,77 $, 41 dolum, 41 maker):** 5 sn Up 97 @0,45 (ilk saniye paketi, seviye 2–3 sn önce görünüyor); 299–543 sn Down 96,9…298,9 @0,09–0,14 maker (Down çöküyor, en kötü sonuç +40→−9); 612–639 sn Up 8…210+193 @0,23–0,42 maker (fiyat best bid'e eşit, seviye yaşı 1–7 sn) → +308; 705–791 sn Down 100…300 @0,07–0,27 maker (tekrar Down). İki tarafta da taze bid'ler, boy yüzlerce pay.

**Gözlenen ekleme olmayan kontrol (F/no_add_controls çifti):** ekleme durumu 1789853400, 600 sn, Up @0,425, risk 118,8 $, model edge +0,019 → sonraki 30 sn'de 100 @0,59 ve 10 @0,43 **maker** dolum (−63,3 $; Down kazandı). Kontrol 1789750800, 600 sn, Up @0,405, risk 102 $, edge −0,21 → hiç dolum yok; Up kazandı (varsayımsal 5 pay +2,89 $). "Kontrol"de emir olup olmadığı bilinmiyor; ekleme durumunda ise dolum best bid'in üstünde bir fiyata (0,59) geldi — 1 dk'lık kamu fiyat vekili (0,425) gerçek defteri temsil etmiyor.

---

## 6. İki mekanizma karşılaştırması (ön kayıtlı)

| | M1 taze pasif kotasyon | M2 taker risk azaltımı | Eski açıklama (zamanlı taker ekleme) |
|---|---|---|---|
| Öngörü (a) | dolumların ≥%85'i maker → **%81 kayıt / %71 pay** (BTC15dk), geç ekleme %94 | tamamlamalar taker-ağırlıklı → **862/1.682 kayıt, 66.010/100.680 pay** | ekleme t≈600 taker → **2/1.173 tam 600 sn, 74 taker** |
| Öngörü (b) | fiyat ≤ best bid(t−1) → 83/116; = best bid 63/116 | taker fiyat ≥ best ask(t−1) → 9/15 | t=180 giriş → ilk dolum yaşı 30–800 sn yayılı |
| Öngörü (c) | seviye önce görünür → 80/116 (1–10 sn), yaş medyan 4 sn | taker tamamlama en kötü sonucu iyileştirir → 870/895, +30.673 $ | olasılık edge → model erken dönemde piyasadan kötü |
| Öngörü (d) | adverse selection → vekilde görünmüyor (ÖLÇÜLEMİYOR gerçek defterle) | taker olasılığı riskle artar → **ölçülmedi** (KANIT YETERSİZ) | — |
| Yeni dönem | maker +570 (S) / −414 (sonrası) | taker −405 (S) / +327 (sonrası) | aday 2/14 + 1/6 piyasa |
| Hüküm | GÖZLEMSEL DESTEK (rol, seviye), kural tanımlanamıyor | GÖZLEMSEL DESTEK; kural şekli açık | KARŞI KANIT |

**Tanımlanamazlık (açık ifade):** M1'in fiyatlama kuralı ("dokunuşa katıl", "model fiyatı − iskonto", "karşı akışa tepki") kamu dolumlarından ayırt edilemez; S döneminde maker dolumlarının %54'ü tam best bid'de, %46'sı altında/üstünde. Yerleştirme zamanı, iptaller ve dolmayan emirler görünmüyor. Ekonomik olarak belirleyici olan kuyruk önceliği 1 sn REST bandından çıkarılamaz (dokunuşta kuyruk önü medyan 369 pay; replay dolumlarının 88/94'ü seviye aşılınca).

---

## 7. Tek sonraki deney: kuyruk-konumlu pasif kotasyon replay'i

**Ayrım:** "Bosona-benzeri taze pasif kotasyon (M1) — bizim uygulayabileceğimiz kuyruk konumuyla — masraf sonrası pozitif mi?" Aynı zamanda M2 hedge kolunun maliyet/faydasını ölçer.

**Veri:** (1) BTC15dk iki tokenin **WebSocket L2 delta** kaydı (her değişim, zaman damgalı) — mevcut 1 sn REST kaydedici yeterli değil; (2) kamu piyasa-geneli `/trades` baskıları (takerOnly=true/false; maker-taraf baskılar = kuyruk tüketimi); (3) Gamma resmî sonuç; (4) Chainlink referans (kontrol kolu için).
**Kollar (sabit, eşik taraması yok):** P0 mevcut aday (gerçek defter), P1a dokunuşa 5 pay iki tokende, P1b dokunuş−1 tik, P2 = P1a + |net|≥10'da taker hedge; limitler adayla aynı (5 pay klip, 10 net, 15 $ nakit, −5 $ en kötü).
**Dolum modeli:** kotasyon anındaki görünen kuyruk; kötümser = önümüzde iptal yok, dolum ancak kümülatif maker-taraf baskı ≥ kuyruk+5 (veya seviye aşılınca); iyimser = kuyrukta ilk. Delta kaydıyla kuyruk önü iptalleri de ölçülür (REST'te ölçülemez).
**Ölçüler:** piyasa başına ücret sonrası nakit PnL (kötümser/iyimser), dolum sayısı, hedge maliyeti, en kötü sonuç; piyasa/gün kümeli %95 CI; rebate ayrı satır.
**Kabul/yanlışlama:** ≥10 tam UTC gün, ≥100 kotasyonlu piyasa; kötümser sınırda P1a/P1b'nin piyasa-kümeli alt CI>0 ve en iyi 3 hariç pozitif → pasif edge var; üst CI≤0 → "pasif kotasyon edge'i bu veriyle yok (REJECTED)"; arada → UNDERPOWERED. Örneklem yetersizse kapı düşürülmez.
**Çalıştırılabilir kod:** `code/passive_replay.py` (REST bandı ve kamu baskılarıyla şimdiden çalışıyor; delta kaydı geldiğinde `load_tape` girişi değişir). Regresyon: `code/test_passive_replay.py` (kuyruk/sınır/limit/hedge/boşluk, 5 test geçti).
**Bu görevde deploy edilmedi.** Kayıt tasarımı: `record_books.py`'nin WebSocket sürümü + `/trades` sayfalayıcı; ayrı görevle başlatılmalı.

**Mevcut REST bandıyla ön sonuç (bilinen karşı örnek dönemi, kanıt değil):**

| Kol | S dönemi 14 piyasa (bilinen karşı örnek): dolum / PnL / en iyi 3 hariç | Kör 10 piyasa 18:00–20:30 UTC: dolum / PnL / en iyi 3 hariç / en kötü piyasa |
|---|---:|---:|
| P1a dokunuş, kötümser | 94 / −6,85 / −12,25 | 73 / +9,15 / −4,30 / −5,00 |
| P1a dokunuş, iyimser | 100 / +9,55 / −5,55 | 70 / −2,60 / −12,75 / −4,85 |
| P1b dokunuş−1, kötümser | 92 / −4,80 / −17,50 | 70 / +17,40 / +2,20 / −2,85 |
| P1b dokunuş−1, iyimser | 97 / −12,35 / −19,10 | 74 / +4,70 / −4,50 / −4,70 |
| P2 dokunuş+hedge, kötümser | 92 / −4,57 / −5,49 (ücret 1,82) | 67 / +0,31 / −3,91 / −2,80 |
| P2 dokunuş+hedge, iyimser | 93 / +1,48 / −4,03 | 63 / −1,20 / −1,50 / −0,47 |
| P0 aday, gerçek defter | 3 / −1,30 / −1,83 | 0 giriş / 0,00 (karar defteri tek taraflı/bayat 11, Chainlink eksik 1) |

24 piyasa, tek gün: UNDERPOWERED. Kör 10 piyasada kötümser/iyimser sıralaması tutarsız (iyimser sınır kötümserden düşük çıkabiliyor: kuyrukta ilk olmak daha erken ve daha çok ters dolum getiriyor), en iyi 3 hariç değerler çoğunlukla negatif; aday hiç girmiyor. Sonuç "REST bandıyla pasif edge yok" yönünde ama karar için yetersiz.

---

## 8. Hata ve eksik listesi (önem sırası)

1. **[karar değiştiren] Gözlem birimi** — `F/analyze.py:152-207,213-258` etiketleri dolum; `R/study.py:248-268`; kök: doğru hesabın yanlış yorumu; düzeltme: rol etiketi + "emir görünmüyor" notu; regresyon: `code/role_classifier.py` öz-test + 156/156 sunucu, 303/303 zincir. DOĞRULANDI.
2. **[karar değiştiren] Taker uygulama modeli** — `R/candidate.py:40-73,107-127`; düzeltme: yeni sürümde pasif kotasyon + kuyruk modeli (bölüm 7). DOĞRULANDI.
3. **[karar değiştiren] replay look-ahead** — `R/candidate.py:160-181`; düzeltme: uygulama fiyatı = karar anındaki/önceki örnek, gelecekle filtreleme yok; etkilenen: 21.276 senaryo satırı, 36 kombinasyon; regresyon: "gelecek örnek fiyatını değiştir → intent değişmemeli" testi (`agents/D2_causality/code/replay_lookahead.py` örnekleri). DOĞRULANDI (ajan; doğrulama turunda).
4. **[karar değiştiren] Sonradan kaliper** — `F/analyze.py:61-63`; kronolojik −11,62 → +7,10 (2¢/20 sn/15 $) / −8,33 (5¢/60 sn/50 $) (ajan D4 yeniden çalıştırma); düzeltme: kaliperi ön kayıtla sabitle, duyarlılık tablosu zorunlu. DOĞRULANDI (ajan).
5. **[karar değiştiren] No-add kontrolü = akış yok** — `F/analyze.py:259-286`; düzeltme: kontrolü "emir var/yok" olarak kurmak kamu verisiyle mümkün değil; yalnız defter kaydıyla. DOĞRULANDI.
6. **[önemli] Olasılık modeli erken dönemde piyasadan kötü** — `results/calibration_check.json`; düzeltme: modeli giriş kapısı yapma. DOĞRULANDI.
7. **[önemli] Yoğunlaşma** — ex-top10 −4,89 $ (geç maker), toplam %86 (10 piyasa). DOĞRULANDI.
8. **[önemli] Yeni dönem negatif** — S −254 (geç), sonrası −87 (toplam). KARŞI KANIT, UNDERPOWERED.
9. **[önemli] protocol.json yeniden yazımı** — `R/report.py:86`. DOĞRULANDI (ajan D10).
10. **[önemli] Portföy limitleri kodda yok** — `R/candidate.py:33-37`. DOĞRULANDI (ajan D5/D10; README zaten belirtiyor).
11. **[küçük] fair_twap 5 dk sabitleri** — ortalama ~0,002 olasılık farkı (ajan D6). Küçük.
12. **[küçük] aynı saniye sıra belirsizliği** — 17/598 piyasa; toplam sabit, etiket değişebilir (ajan D1).
13. **[küçük] histories gecikmesi** — medyan 33 sn, p75 43 sn; RAPOR'un "35–45 sn" ifadesi kısmen doğru (ajan D2).
14. **[küçük, düzeltildi] rol sınıflandırıcı mutlak tolerans** — 92/14.014 kayıt (uç fiyat). Bu raporun bütün sayıları ücrete göreli toleranslı sürümle.

**Doğrulama turu sonucu** (`results/audit_verification.json`, `.md`): 263 ajan; 110 bulgu (10 boyut + 8 boşluk görevi), her biri 1–3 bağımsız mercekle çürütülmeye çalışıldı; 91 hayatta, 19 çürütüldü (karar değiştiren 27'nin 21'i, önemli 40'ın 31'i, küçük 43'ün 39'u hayatta). Çürütülenler ve bu rapordaki karşılığı: D3 "tx başına 3,55 dolum" (sahip filtresi; kendi hesabımla 303/303 birebir), D9 F2/F3 (yanlış grup alıntısı ve "7/8 grup ≥%90" hatası; bölüm 4 tablosu benim hesabım), D9 F5 ("mekanizma farkı" ifadesi; 561 saatlik piyasa aynı Binance kuralı), D9 "en iyi 3 hariç 4.648 $" (doğru 3.025,27), D7-001 (RAPOR doğru), D7-006 "işlemsiz pencerede Bosona-benzeri bid yok" (yalnız best bid'e bakılmış; derinlikte 0,4–0,75 aralığında >30 paylık bid'ler var → ÖLÇÜLEMİYOR), D8-F5 (7,4 saat değil 4,4 saat), D10-001 (manifest donmuş kopyayı doğrular), CONC-F1 yorumu ve CONC-F3 (20/190 olay; tam sette ters işaret), GAP-3 kotasyon yaşı/adverse selection (karıştırıcı), GAP-M2-1 ("nakit PnL negatif → risk azaltımı başarısız" yanlış eşitliği), real_ask GAP-1/4/5 (%61,8 yerine 19/32; "book −5 sn sonra" yanlış okuma). Karar değiştiren ve hayatta kalan başlıklar: gözlem birimi/rol, taker uygulama modeli, replay look-ahead (+düzeltilmiş yeniden koşu), kaliperler, no-add kontrolü, kalibrasyon, yoğunlaşma, yeni dönem, S tamamlamalarının maker payı, çapraz-grup batching 0, kapanış sınırı.

---

## 9. Tekrar üretim

```bash
cd /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/fable_review_20260921
P=/home/taygun/Masaüstü/KararAtlas/base1/bin/python3
$P code/role_classifier.py                      # sınıflandırıcı öz-test
$P code/btc15_role_tables.py                    # rol×faz, gün, yoğunlaşma, vekil adverse
$P code/s_period_role_book.py && $P code/s_period_level_age.py
$P code/calibration_check.py
$P code/cross_asset_table.py && $P code/paths.py
$P code/test_passive_replay.py
S=../btc15_followup/status_20260921_1800; M=/home/taygun/Masaüstü/polymarket-bosona
OPENBLAS_NUM_THREADS=1 $P code/passive_replay.py --tape $S/raw/book_validation_prefix.json.gz --markets $S/raw/new_period_markets --trades raw/market_trades --cld $M/data/tape_cl_direct/cld_20260921_1{3,4,5,6,7}.jsonl.gz --out results/replay_s_period --only-full
$P code/new_period_summary.py                   # raw/new_period önbelleğinden (ağ gerekmez)
$P -m ruff check code/
```

Kamu istekleri URL ve alım zamanıyla `raw/**` içinde; Polygon receipt'leri `agents/D3_order_identity/raw/receipts/`. Tohum: replay deterministik; bootstrap kullanılmadı (örneklem yetersiz). Kütüphaneler: Python 3.12.3, numpy 2.3.5, scipy 1.16.3, scikit-learn 1.8.0, ruff 0.15.7. Hash manifesti `results/manifest.json`.

## 10. Doğrulama

- `role_classifier.py` öz-test; sunucu bayrağı 156/156; zincir rolü 303/303.
- `test_passive_replay.py` 5/5; ruff `code/` temiz; py_compile temiz.
- S sayıları (13.219 snapshot, 126 dolum, +165,63, −254,17) birebir; RAPOR ana tablosu (D1/D9/D10) birebir; örnek piyasalar ±0.
- Bağımsız kalibrasyon (20.487 bağlam) D6 ile uyumlu.
- Çalıştırılmayan/ölçülemeyen: gerçek defterle adverse selection (S), taker hedge olasılığının riskle ilişkisi, emir yerleştirme zamanı, kuyruk önceliği.
