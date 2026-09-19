# ARAŞTIRMA DİSİPLİN PLAYBOOK'U — hangi hataları BİR DAHA yapmayacağız
*Son güncelleme: 2026-07-05. Bu dosya 4+ aylık Polymarket araştırmasının kanla yazılmış
dersleridir. Her kural gerçek bir yaradan gelir (parantezde hangi olaydan). Bu repoda
çalışan HER model/insan önce bunu okumalı. Kardeş dosya: `CRYPTO_BINARY_MM_HANDOFF.md`
(aktif proje). Detaylı geçmiş: Claude memory dizini + `tasks/lessons.md` + CLAUDE.md.*

## A. ÇEKİRDEK SÜREÇ — her yeni fikir bu döngüden geçer, istisnasız

1. **Önce pre-registration:** kural, örneklem penceresi, KILL/PASS eşikleri ve falsifier
   listesi SONUÇ GÖRÜLMEDEN yazılır. Sonuç ne çıkarsa çıksın gate uygulanır — pazarlık,
   "bir şans daha", "ama şu dilim pozitif" YOK. (Bunu ihlal etmenin maliyetini hiç
   ödemedik çünkü hiç ihlal etmedik; etrafındaki her kısayol denendi ve yandı.)
2. **Gate'ler koda gömülür** (read-only reporter script; runner'ı durdurmaz, insana
   söyler). Örnekler: `scripts/event_shadow_decision_gate.py`,
   `data/analysis/crypto_binary_mm_paper_20260705/gate2_report.py`.
3. **Amendment sadece "pre-results" döneminde meşrudur** (ilk settled/ilk sonuç
   kaydından ÖNCE, tarihli ve gerekçeli). İlk sonuç düştükten sonra gate'e dokunmak =
   veri madenciliği. (V1 shadow amendment geleneği; gate-2 prereg'in 16:13Z yarışı.)
4. **Hiçbir agent/Codex/model çıktısı doğrulanmadan yutulmaz.** Bu repoda adversarial
   doğrulama üç kez projeyi kurtardı: pin-rezerv hesabı (50×şişkin), paper fill motoru
   (3 iyimser bug), fizibilite verdiktinin yanlış gerekçesi. Doğrulama = bağımsız kaynaktan
   kendi sorgunla aynı sayıyı yeniden türetmek; "koda baktım mantıklı" değildir.
5. **Tasarım ölür, makine ölmez:** bir gate KILL bastığında ölen şey o tasarımın
   İDDİASIDIR; veri toplayıcı bedavaysa koşmaya devam edebilir. Öğrenilen şekle göre YENİ
   pre-reg tur tasarlamak meşrudur — mevcut gate'i esnetmek DEĞİLDİR. (Gate-1/gate-2 örneği.)
6. **Karar metriği asla PnL'in kendisi değildir** — mekanizma + pre-reg metrik.
   Kaybeden seansta "bot bozuk", kazanan seansta "bot iyi" demek sonsuz döngüdür.
   (JetFadil-replica CLAUDE.md kuralı; her lane'e uygulanır.)

## B. ÖLÇÜM TUZAKLARI KATALOĞU — sayı üretmeden önce kontrol listesi

7. **İyimser fill proxy'si = ölüm.** Maker paper-fill SADECE strict price-through
   (gerçek taker print'i senin seviyenden STRICT iyi fiyatta) sayılır; depletion-proxy,
   mid-touch, "book'u iyileştirirdik" fill'leri yasak. (v60 calm-maker: +3.9% hayalet kâr,
   price-through'da her yer negatifti. 2026-07-05'te paper sim'de AYNI hata yeniden doğdu
   ve yakalandı.)
8. **Fill yönü:** BID'i sadece taker-SELL, ASK'i sadece taker-BUY doldurur. Fill fiyatı =
   SENİN quote fiyatın (trade fiyatı değil). Gelir = fill-anı MARKET MID'ine karşı —
   asla kendi modelinin fair'ine karşı değil (o, adverse selection'ı kâr diye defterlemektir).
9. **Fee'ler gün-1'den modele girer.** (GERI paper fills fee-free bug'ı: ~7pp sessiz
   iyimserlik; 20 fill'de ~$140 şişkinlik.)
10. **Trade-price ≠ executable price.** Tape'teki fiyattan "girilebilirdi" deme; ask+fee+
    derinlik yürüt. (Box-office retro "+8.88% favori-takip" = artefakt; executable forward
    aynı fikri −39%'da settle etti.)
11. **Lookahead denetimi mekanik olsun:** sinyal timestamp'i < işlem timestamp'i, kayıtta
    ve spot-check'lenebilir. (ASOF lag assert'leri; paper sim'in quote_ts+2s < trade_ts kuralı.)
12. **"Quote var ≠ tradable book."** Event marketlerin ~%50'sinde book bayat/boş çıktı
    (Telonex pilotu). Tazelik ölç, varsayma.
13. **Karışım kohortunun aggregate'ini ASLA okuma.** Kural değiştiyse era'ları ayır;
    summary.json'lar era-bazlı olsun. (V1 shadow: 3 era tek ROI'de — anlamsız sayı.)
14. **Event-cluster her istatistiğin zorunlu adımıdır.** Satır değil bağımsız gerçek-dünya
    olayı say; bootstrap'i cluster üstünden, deterministik seed'le yap. (misc_5k'nın
    "+1.54"ü = TEK Anthropic haber kümesi; kümeleyince −5.7pp.)
15. **Konsantrasyon her rapora:** top-1/top-3 kazanç payı. Tek fill/gün/hafta taşıyorsa
    sonuç yok demektir. (GERI top-3 %64; BO 6/26 haftası tek bracket %87.)
16. **Post-hoc dilim = hipotez DEĞİL, aday.** Pozitif dilimi ancak yeni pre-reg forward
    test doğrular. (Era-C dilimleri; "14:00 ANY" rank #796/38978.)
17. **Sign-flip yasağı:** negatif bulguyu ters çevirip strateji yapma ("burst'leri
    fade'le" dürtüsü) — o, bilinen bias'ın (favorite-longshot) yeni kılığıdır.
18. **Rejim beta'sını edge sanma.** PnL'in piyasa yönüyle korelasyonunu HER retro'da bas;
    down-günler kaldırılınca ölüyorsa o bir yön bahsidir. (GERI corr −0.83, flat/up 0W;
    price-bucket "hit $X" = bull-beta, up-ay %86 vs down-ay %58.)
19. **Winner's curse:** grid/leaderboard kazananı population + holdout + permutation-null
    ister. (34,282 cüzdan×aile hücresinde beklenen şans kazananı 116 vs gerçek 16, p=1.0;
    pre-start fade "+5.8%" = sample-luck.)
20. **Cüzdan-lifetime PnL bota karne yapılmaz; attribution önce.** (lpbot dersi — kullanıcıyı
    iki kez kızdırdı.) Nansen "PnL"i muhasebedir, nakit değil (Jet +$98k görünüp −$13.6k çıktı).
21. **Data API, NegRisk maker fill'lerinin %83-90'ını GİZLER** → maker-ağır cüzdan/strateji
    analizi zincir verisi ister.
21b. **İki taraflı MM'de dürüst muhasebe tek başına yetmez — spread gelirine bak.** Fill'ler
    doğru fiyatta doğru yönde defterlense bile, spread geliri NEGATİFse taker'lar seni
    repricing penceresinden hızlı eziyor demektir (adverse selection). Bu, hedge'den bağımsız
    ve yapısaldır. (Crypto binary MM: 30s quote refresh → spread geliri −$26; "boş koltuk"
    başta olumlu okundu, sonra koltuğun neden boş olduğu = negatif ekonomi ölçüldü.
    Ders: boş koltuğun nedenini öğrendiğinde nedenine inan.) (7/7 ikizi: MAKER_REBATE feed'i $1 gösterdi, zincir gerçeği
    $337.6k — teşvik geliri hükmü de zincirden verilir, API'den değil. Ve: buys+redeems
    aritmetiği "cash" DEĞİLDİR; cüzdan kârlılığı = TÜM ERC20 counterparty akışları. Ve:
    bir kontrol "parametre değişmemiş" (rebateRate 0.2) derken o parametre modelde hiç
    yoksa bu ayrı bir bulgudur — "değişmedi" ≠ "hesaba katıldı". JetFadil rebate vakası.)

21c. **Sessiz-atlama fetch zehri (07-08 denetim dersi):** veri çekicisi hata yiyince chunk'ı
    SESSİZCE atlarsa "0 sonuç" ile "veri yok" ayırt edilemez olur — rebates_*.json'ı boş
    sanmamızın sebebi buydu (publicnode getLogs 403'ü range-hatası sanılıp atlandı; ödemeler
    zincirdeydi). KURAL: fetch atlarsa SAYAÇLA raporla; "0 bulundu" ancak "0 atlandı" ile anlamlı.
21d. **Replay counterfactual'ı birim-bazlı kur:** "kural X şunu kurtarırdı" iddiasında her
    birim (pencere/fill) için ayrı counterfactual; toplam-fark kısayolu 07-08 denetiminde bir
    ajanın tüm kurallara counterfactual=0 yazmasıyla patladı.
21e. **API lookup'ları timestamp-çıpalı yap:** "son N kayıt" ile dönem karşılaştırması yapma
    (A4 ajanının "%100 gizli" yanlışı; MAKER_REBATE "%100 model" pencere hatam) — her sorguya
    açık start/end; dönem uzunlukları rapora yazılır.

## C. API / AGENT OPERASYON TUZAKLARI (hepsi başımıza geldi)

22. Gamma: default UA 403 yer → browser User-Agent. Resolved marketler `?slug=`
    sorgusundan KAYBOLUR → `/markets/{numeric_id}`. Default sayfalama eski marketleri
    döndürür → "ürün kapanmış" yanılsaması (canlılık kontrolü: slug'ı doğrudan sorgula,
    örn. `btc-updown-5m-<epoch//300*300>`).
23. CLOB book parse: best bid = EN YÜKSEK bid, best ask = EN DÜŞÜK ask — dizinin yanlış
    ucunu okuyan agent "98c spread" uydurdu. Şüpheli mikroyapı sayısını HEP kendin yeniden çek.
24. X/Twitter zamanı: tweet ID = snowflake → ms hassasiyetli UTC. Görünen saat dakika
    hassasiyetindedir, hesap onunla yapılmaz.
25. Heavy analiz RAM disiplini: market-bazlı işle, dev join'leri serileştir; sqlite WAL;
    population-scale veri işini orkestratör yapar, agent'a örnekletme (3 kez sampled-data
    kazası).
26b. Gamma `condition_ids` sorgusu resolved marketleri GİZLER (slug gibi) → closed=true
    ikinci geçiş. NegRisk sepet analizi: event `negRiskAugmented=true` ise aday listesi AÇIK,
    subset-YES<1 arb değil; TAM market listesi events/{id}'den doğrulanır. Polymarket CLOB
    tek-kitap: NO_bid≡1−YES_ask → parite/sepet koşullarının ayna-görünümleri çift sayılmaz.
26. sqlite CLI bu makinede YOK → python3 stdlib, read-only URI (`file:...?mode=ro`).

## D. KAPALI MEZARLIK — yeniden kazma; sadece reopen tetiği tetiklenirse aç

| aile | verdict | reopen tetiği |
|---|---|---|
| BTC 5m/15m/4h updown (taker+maker+hız, tüm aileler) | kalıcı NULL: kalibre book × %7 fee × maker adverse × hız-alakasız; ⚠️ 7/7: research-dönemi maker matematiğinde rebate bacağı (taker fee'nin %20'si) EKSİKTİ ama per-fill ~%0.3-1.4 ≪ adverse → kapanış bize göre ayakta | fee/reward/queue/sustained-high-vol; aylık bakışa EK: 0x520bf77d gece disperse toplamı (rebate havuzu ~10× büyürse rebate-dahil maker re-eval meşru) |
| BTC5m geç-pencere favori taker (TWAP60 era, analitik terminal-TWAP modeli; 15m T−45 portu) | KILL 2026-09-02 (önkayıtlı tek bakış, `data/analysis/btc5m_twap60_late_favorite_20260902_v1`): birincil T−45 UNDERPOWERED (+$29/63 fill); geç-favori primi legacy/TWAP30'da anlamlı (p≤0.003), TWAP60 sonrası tüm saatlerde EV≈0; market Brier modelden iyi; kesinleşince favori ask yok (%58) | settlement kuralı/fee değişimi; veya London no-order shadow'da T−30 hücresi ≥150 fill gün-LCB>0 |
| JetFadil replica/copy | ⚠️ 7/7 DÜZELTME: Jet'in trading bacağı ≈ break-even AMA gizli gelir = MAKER REBATES ("Polymarket: Distributor" 0x05cd9922 → 8-30 Nis $337.6k; şimdi ~$140-270/gün). "Nakit-negatif, pasta yok" hükmü yanlıştı; iş modeli = rebate-farm (+airdrop opsiyonu). Detay: memory `project_jetfadil_rebate_channel_20260707.md` | rebate havuzu Nisan seviyesine (~$15k/gün) dönerse "rebate-farm koltuğu" ayrı tez olarak değerlendirilebilir |
| Copy-trade (cüzdan keşfi/hızlı kopya/akış takibi, TÜM varyantlar) | permutation-null p=1.0; post-burst fiyat etkin (+0.6c≤gate) | — |
| News-sniping/release-leak ailesi | KILL + **KULLANICI KARARIYLA kapalı — bir daha ÖNERME**; tweet SON bilgi olayı (Sonnet 0.999 @ T0−29s); drift'i 200-433 cüzdanlık kalabalık taşıyor | kullanıcı açıkça isterse |
| Weather model-pricing (GEFS post-process vs temp ladder, taker) | K1 DIE 7/7: OOS market > model −0.023/−0.030 Brier (p=1.0, 0/3 sezon, Tier-2 fail); model>NBM ama market>model; burn-in +0.039 = kış-rejim artefaktı | kitaplar ≥5× / rewards; Faz-5 intraday METAR = ayrı yeni pre-reg |
| Rule&Reality scanner | 130 markette 0 flag; piyasa kural-düzeyinde olgun | epizodik manuel fırsat olur, sistem kurulmaz |
| Box-office (taker+maker-timing+LP) | edge=forecast-skill (%87 taker-executed), bize kapalı; incumbent'lar da drawdown'da | gross-forecast modelimiz olursa |
| Price-bucket "hit $X" | bull-beta (up-ay %86 vs down-ay %58); ≈fee'li kaldıraçlı long | gerçek-zamanlı rejim classifier tezi gelirse (o zaman da perp muhtemelen daha ucuz) |
| Event misc cheap-YES (V1/V2) | V1 iki pre-reg kol formal KILL; V2 5k_v1 gate'i ~Tem ortası basacak (KILL muhtemel, PRE-COMMITTED) | gate çıktısı ne derse o |
| GERI lower-YES | bearish beta; paper devam, **checkpoint 2026-10-01: fee-adj fill<6 → PARK**; fee fix (`range-bot/scripts/paper_fills.py`) fill sayılmadan önce şart | — |
| Crypto binary MM (delta-hedge, European strike) | KAPANDI 2026-07-07: 3g paper, basis 0/18 TEMİZ ama spread geliri NEGATİF (adverse selection) + hedge churn → kaba net −$359; koltuk boştu çünkü ekonomi negatif | strike marketlere rewards / aile hacmi 3-5× / bedava sub-second quote altyapısı |
| HL maker, xsec faktör, bias×kaldıraç, BTC5m own-system tüm dalları | NULL (detay memory) | dosyalarındaki falsifier'lar |
| Parity/basket arb (binary YES+NO<1 + negRisk sepet, fee era) | NO-GO 2026-07-10: instant $0.02/14g (36M eval, min gap $0.006/set; tick-grid+maker disiplini = dislokasyon yok); "kilitli $610" %100 negRiskAugmented set-eksik = arb değil; pencerelerin %90'ı UNTAKEN | mint/merge motor arızası (kalıcı self-cross) / yeni fee-free+oynak kategori / tick 0.1¢ + near-gap p1<0.2¢ / kapalı-set canlı-şok tezi ayrı pre-reg |
| Saturday YES alert (BTC daily-range center-YES TP10 scalp, Telegram) | DENETİM KILL 2026-07-13: "19/19 %100" = in-sample (100+ konfig, n=23, tape-print TP, sıfır fee — 7% taker VAR); gerçek OOS Nis25-Tem11 TP10 7/10, brüt +0.9%/tr, fee ile NET −EV; canlı 3 alertin 2'si settle NO (06-13, 06-20). Kod dürüst (parite birebir), backtest geçersiz. Rapor `data/analysis/saturday_yes_audit_20260713/REPORT.md` | fee'li+executable-fill pre-reg forward paper 20 sinyalde net>0 gösterirse (bar yüksek; mevcut kanıt negatif) |

## E. AKTİF İŞLER + RUTİN BAKIM (2026-07-06 itibarıyla)

- ~~#1: Crypto binary MM~~ → KAPANDI 2026-07-07 (mezarlık tablosunda; handoff mühürlü).
- **#2 Weather model-pricing lane: K1 DIE (2026-07-07T22:19Z) — PARK.** Tam yaşam döngüsü 2.5 gün,
  $0 sermaye: Faz-0 (K0a park → v0.3 micro-clip) → Faz-1/1b lakeleri (join %95.97 doğrulanmış) →
  gate freeze → Faz-2 (M2 LightGBM şampiyon; burn-in'de markete +0.039 önde göründü) → **OOS'ta
  tersine döndü: market M2'yi −0.023/−0.030 Brier yener (p=1.0, ECE fail, 0/3 sezon, Tier-2 fail).**
  Model NBM'i yeniyor (+0.015) ama market ikisinden de iyi → "retail vibes" tezi day-ahead'de ölü;
  burn-in farkı kış-rejim artefaktıydı (pre-reg walk-forward+sezon gate'leri tam bunun için vardı).
  Detay: `WEATHER_ECON_EDGE_PLAN.md` K1 VERDICT bölümü + `weather-edge/reports/.../K1_REPORT_M2.md`.
  Reopen: kitaplar ≥5× derinleşir/rewards gelirse; veya Faz-5 intraday METAR tezi YENİ pre-reg turu olarak.
- V2 misc gate ilk okuma ~Tem ortası: `python3 scripts/event_shadow_decision_gate.py` → çıktıya uy.
- ~10 Tem: price-bucket pending 91 kripto satırı TEK okuma (kural sabit: clustered mean ≤0 → kill teyit).
- GERI: 1 Eki checkpoint'i; fee fix hâlâ yapılmadıysa fill'ler sayılmaz.
- Aylık: canlı updown + strike marketlerde `feeSchedule`+`rewards` bakışı (tek Gamma sorgusu).
- Leftover: `record_hl_tape.py` (PID 152247, Haz-10'dan beri) — kullanıcı kararı bekliyor.

## F. İLETİŞİM & KARAR KÜLTÜRÜ

27. Türkçe konuş; sayıları yuvarlamadan ver; kötü haberi önce söyle.
28. Kullanıcının fayda fonksiyonuna sen karar verme: "ayda $500 az" DEME — riski/emeği
    dürüst göster, eşiği kullanıcı seçer. (MM projesinde bu hatayı yaptım, kullanıcı
    düzeltti, proje o sayede yaşıyor.)
29. Kolay dalların gerçekleşmesine büyük kanaat güncellemesi verme; günlük PnL'e bakıp
    plan değiştirme (no-emotional-swinging). Kanaati zor soruların cevapları oynatır
    (pin testi, settled-cohort, rejim değişimi).
30. Her kapanış falsifier listesiyle kapanır ("şu olursa yeniden bak") — böylece "acaba"
    sonsuza kadar geri gelmez; mezarlık tablosundaki tetikler bunun ürünü.

## G-ek (2026-07-08): Agent feature-build tuzağı — cross-asset join
- Subagent'ın ürettiği multi-asset feature tablosunda px kolonu TÜM sembollerin union'ından
  asset filtresiz ASOF join'lenmişti (ETH fill'ine BTC fiyatı). Belirti: window-level sinyal
  güçlü (%96-99 agreement) İKEN fill-level model düz (Brier 0.25) — bu kombinasyon imkânsızdır.
- KURAL: Frozen artefakt (model/feature parquet) downstream'e geçmeden orkestratör 1 dakikalık
  bağımsız "bariz-sinyal-var-mı" spot-check koşar. Grup-bazlı sanity assert: her asset için
  |px_now/kendi_kline_close − 1| medyanı <%1.
- Mikro: pd.read_json unix-ts'yi datetime'a çevirir (convert_dates=False); dedup daima full-row
  (txHash dahil) — alt-küme dedup meşru çoklu-maker satırlarını siler.

---
## Ek kurallar (2026-07-08 second-opinion denetiminden)
31. **Seçilmiş-fill kanıtı ≠ kural kanıtı.** Bir cüzdanın kendi fill'lerindeki bucket-net'i, aynı eşiği mekanik kurala çevirince yaşamayabilir (burada +8.4% → −8.4%). Kural-üretimli çok-gün sim, deploy öncesi ZORUNLU aşama; tek-gün sim gün-seçilimi riski taşır (tek pozitif gün tam da o gündü).
32. **Doğrulayıcı ajan HAM veriden başlar.** Denetlenen ajanın ara-parquet'ini tüketen "bağımsız" doğrulayıcı aritmetiği doğrular, konstrüksiyonu doğrulamaz (token-flip bug'ı böyle kaçtı; corr-by-group spot-check ile yakalandı). Token/side/asset eşlemelerinde grup-bazlı corr imza testi standart olsun.
33. **Gate metriği ile sim ekseni aynı büyüklük olmalı.** "Latency" gate'i loop-gecikmesini ölçüp sim'in bilgi-bayatlığı eksenine kıyaslanırsa gate vacuous'laşır (fark p50 0.76s idi). Pre-reg'de referans olayın tanımı tek cümleyle: "sinyali ÜRETEN tick".
34. **Overlap-koşullu PnL = teşhis, strateji değil.** "Hedef cüzdan da aynı anda aldı mı" ayrımı seleksiyonun yükünü ölçer ama gerçek-zamanda gözlemlenemez (copytrade olur). Deploy edilebilir versiyon: seleksiyonun GÖZLEMLENEBİLİR korelatlarını ayrı pre-reg ile aramak.
35. **Arka plan ajanına yürütme yetkisini açıkça yaz** ("execute to completion, no user decision needed") ve uzun koşumları PID-bazlı izle (pgrep -f self-match tuzağı).

## Ek kurallar (2026-07-10 researcher-triangülasyonundan)
1. **`seconds_delay` ≠ taker gecikmesi yok.** `itode: true` ayrı bir alandır ve 250ms marketable-emir bekletmesi demektir (resmi doc). Bir mikro-yapı parametresini tek alandan okuyup "yok" deme; şemadaki TÜM ilgili alanları tara.
2. **Tick'i hard-code etme.** Up/Down marketlerinde tick dinamik (0.01→0.001); kapanmış marketin API'si SON değeri gösterir. Replay'ler tick_size_change'i işlemeli.
3. **Data-API activity satırlarının ~%30'u VWAP-agregasyondur** (aynı emrin çoklu fill'i tek satır, grid-dışı fiyat). "price = book seviyesi" varsayan her analiz (merdiven kovaları, tick analizi) bulanır. Cash-muhasebesi etkilenmez.
4. **Brief/rapor sayısını zincir kaydıyla doğrula.** "$1.7k/gün rebate, 11/11 pozitif gün, $12.2k PnL" üçü de yanlıştı ($1.275/gün Platinum; 9/11; $9.75k). Bir sayı iki rapora kopyalandı diye doğrulanmış olmaz.
5. **Tolerans-tabanlı sınıflayıcıya pozitif kontrol şart.** "Maker %2" bulgusu tolerans hatasıydı (küçük-fee taker'lar); ce25e2 (gerçek maker'lı cüzdan) pozitif kontrolü olmadan yayınlanamazdı. Sınıflayıcının iki sınıfı da GERÇEKTEN gördüğünü kanıtla.
6. **Leg-attribution ≠ skill-attribution.** SELL satırlarının markout taşıması, satış becerisinin bağımsız alpha olduğunu göstermez; karşı-olgu (hold-all) testi olmadan bacaklara "edge" dağıtma. (Entry-only +$296 vs fiili +$9.75k ancak counterfactual'la görüldü.)
7. **İki bağımsız ölçüm örtüşüyorsa kalibrasyondur, tesadüf değil:** T3 book-survival %71-76 ↔ P0.5 canlı fill-rate %68-75. Canlı mikro-arm'lar simülasyon kalibrasyonunun en ucuz doğrulayıcısıdır.
8. **Data-API `timestamp` ≠ CLOB olay zamanı.** Aktivite timestamp'i on-chain kayıttır; CLOB print'i medyan ~2.27s ÖNCEDİR (p5 −3.13/p95 −1.30). Tape-eşleme veya "fill anındaki book" analizi aynı-saniye varsayımıyla yapılamaz — offset-farkındalıklı pencere şart. (Bu hata match-rate'i %79 yerine %5 gösterdi.)
9. **Fonksiyonun girdi dict'ini mutate etmesi = çok-çağrı zehiri.** `pair_fills_chronological` fill'lere `_used` yazıyordu; 2.+ çağrıda paired=0 döndü ve satışlar sessizce simülasyondan düştü. Paylaşılan veri üzerinde çalışan yardımcılar ya saf olmalı ya da her çağrıda temiz kopya almalı; "aynı girdiyle 2. çağrı aynı sonucu veriyor mu" testi ucuzdur.

## Ek kurallar (2026-07-10 gece-2, causal-replay dersinden — AĞIR DERS)
10. **Counterfactual'ın TANIMINI adversarial doğrula, sadece uygulamasını değil.** K2 replay'de lookahead/bayat-book/self-trade/kapsam hepsi temizdi; çürük olan muhasebe DÖNÜŞÜMÜYDÜ (ex-post pairing). Dış hakem tek soruyla yakaladı: "pairing üyeliği geleceği kullanıyor mu?" → Evet'se her sonuç şüphelidir.
11. **Tape üzerinde ex-post netting/pairing/gruplama = hindsight kaldıracı.** Pencere-sonu min(UP,DOWN) eşlemesi, ardışık yön-değiştirmelerin yol maliyetini "neutral pair"e çevirip sildi (+$20k artefakt vs causal −$52k). Her envanter dönüşümü SADECE geçmişten hesaplanabilir olmalı; leg-gap dağılımı (bizde %86 >10s) ilk teşhis aracıdır.
12. **wV formülü: wV = 32.857 × fee** (= C·p(1−p)·2.3). "shares×(1−p)×2.3" YANLIŞ (Obsidian öngörür, gözlenen Platinum'la çelişirdi). Formülü her zaman gözlenen tier/ödemeyle kapat.
13. **Data-API activity `type=SPLIT/MERGE/REDEEM` görür.** "API split'i göremez" varsayımı yanlıştı; 20d230'da SPLIT=0/MERGE=0 (gerçekten kullanmıyor). İddia etmeden önce type parametresini sorgula.
14. **Kör-test disiplini:** canlı shadow koşarken izleme health-only olmalı; PnL'i loop'a bağlamak optional-stopping kirliliğidir (dış hakem uyarısı üzerine düzeltildi).
15. **Kline close[t], t+1'de öğrenilir.** 1s-kline sinyalli backtestte close[sec]'i sec anında kullanıp sec+250ms'te fill etmek = ~0.75s lookahead; bu tek off-by-one, 11 günde +$6.3k'yı −$6.3k'ya çevirdi ($12.6k salınım). Her kline-tabanlı sinyalde indeks kuralı: karar anında bilinen = close[sec−1]. Pozitif çıkan her hızlı-sinyal backtestinde İLK kontrol bu.

## Ek kurallar (2026-07-10 gece-3, bağımsız denetim + exit-hazard kapanışından)
16. **Cüzdan yaşını zincirden doğrula, pencereyi "örneklem" sanma.** 20d230'un 11-gün penceresi tüm ömrüydü (inception 06-27, 4 asset'te 2dk14sn içinde eşzamanlı başlangıç imzası). "Geçmiş rejimde de kârlı mıydı?" sorusu vacuous olabilir; her cüzdan-analizi inception-tarihi tespitiyle başlar (ilk-tx + çok-asset eşzamanlılık imzası).
17. **Fill'lerden öğrenilen exit-imitasyonu pozisyonel korelasyon öğrenir, karar kalitesini DEĞİL.** Hazard model (AUC 0.64-0.67) yaş/boy/saat öğrendi, mark-PnL/mikro-yapı önemi SIFIR çıktı; medyan 40s'de çıkıp (onun 171s) çifte adverse selection'a kilitlendi → hold-all'dan −$23.5k KÖTÜ. "Davranışı taklit et" ≠ "edge'i taklit et"; feature-importance'ta karar-değişkenlerinin sıfır çıkması erken ölüm sinyalidir.
18. **Ara-baseline raporlama: en temiz counterfactual'ı manşet yap.** q20 −$52k raporlandı ama doğru causal taban q0 −$62k idi (split-kredisi artefaktı). Sonuç değişmese de "hangi sayı manşet" seçimi güven maliyeti yaratır; denetçi her zaman q0'ı arar.
19. **Kapanışı mühürlemenin en ucuz yolu = düşman denetim + son boşluğun bounded koşumu.** 8-denetçi×3-lens audit her sayıyı reprodüse etti (maliyet ~1 gece, $0); tek bulgusu coverage-boşluğuydu (exit) ve aynı gece prereg'li deneyle kapandı. "Acaba bir şey mi kaçırdım" döngüsünün antidotu tekrar-analiz değil, bağımsız reprodüksiyon + kalan boşluğun kill-gate'li testi.

## ADDENDUM 2026-07-14 — Mezarlığa yeni satır: 5dk maker-rebate kulvarı (updown-pilot)

**PARK (LC41_DECISION.md, hash-pinli).** 12 gözetimli burn-denemesi (~-$8) + 2 bağımsız araştırma
raporu + para-sız dört-aksiyon replay (n=32 BTC+ETH, +250ms gerçek book, %7 fee): yetim oranı %25
(başabaş ≤%8-11), mevcut politika -$0.23..-0.26/olay, taker-hedge bile -$0.21/olay negatif.
KİLLER MEKANİZMA: iki-taraflı pasif fill'in non-atomikliği × adverse selection (yetim bacak %30-32
kazanıyor = zehirli akış imzası) — btc5m mezarlığındaki "maker adverse-selection" mekanizmasının
5dk'lık kuzeni. Rebate garnitür (~$0.037/çift), yemek değil; oran Polymarket takdirinde.
REOPEN TETİKLERİ: kripto maker rebate oranı belirgin artarsa | fee/ürün yapısı değişirse |
fill-sonrası book toksisitesi ölçülebilir şekilde düşerse. YENİ DERSLER: (1) hedge maliyetini
fill-SONRASI gerçek book'tan ölçmeden L tahmin etme (zarf-arkası -$0.13 vs gerçek -$0.21+);
(2) güvenlik sertifikasyonu ile ekonomik hipotezi aynı faz sanma — ekonomiyi ÖNCE tape'ten öldürmeyi
dene (LC41 bir akşamda, sıfır parayla cevapladı); (3) venue'suz-testnet ortamda gözlem araçları
canlı sistemi öldürebilir (observer-effect, lc29); (4) audited-bytes=running-bytes disiplini
anlatıyla değil attestasyonla sağlanır. MİRAS: supervisor/preflight/recovery/replay iskeleti +
integer-grid/event-proof desenleri yeniden kullanılabilir (updown-pilot/.artifacts/).

- **#36 (2026-07-20, imitasyon-F1 placebo zorunlu):** Kadans/dağılım eşleyen her imitasyon
  botu için UNIFORM-zaman placebo koş. JM-1'de max-card F1@30 0.53-0.61'in ~%97'si salt
  kadans-tabanından çıktı (placebo 0.52-0.59); placebo'suz bu "timing becerisi" olarak
  raporlanabilirdi. Ayrıca: mod-tabanlı deterministik örneklemede adım modulusu bölerse
  (300 % 20 == 0) residü sabitlenir — anahtarı karıştır (`win//300 + k`).

- **#37 (2026-09-10, hız-edge'i kova ile test etme):** Binance 100-ms kovası + "pencere karardan ≥200 ms önce bitsin" koruması tick-reaktif
  edge'i (0-200 ms) yapısal olarak görünmez kılar; 11 replay bu yüzden FAIL'di. Hız kuralı için tetik saati ham ms işlem verisi (tick anında),
  icra saati ayrı (t+L), L'ye duyarlılık (130/200/300) ve saat-sapması (+50/100/150 ms) zorunlu rapor. Dolum-koşullu "quotes verimli" bulgusu
  ilk-taker (tick+130 ms) kümesi için geçerli değildir. Kesin eşleşme zamanı = tüketilen seviyenin kitap olayı (eşik max(0,3q,1), q'ya en yakın
  düşüş; dağılım tek-tepeli olmalı). Örnek: `pm_whiskas_selection_fable_20260910_v1/CONTRACT.md` T7a/T7b.

- **#38 (2026-09-17, SİMÜLASYON KARAR ARACI DEĞİLDİR — operatör direktifi):** Aynı gün, aynı
  motorla dört ölçümde simülasyon-canlı ayrışması **iki yönde de** büyük çıktı: TWAP maker dolum
  oranı sim %17,6 → canlı %6,6; base.py çift tamamlanma sim %83,6 → canlı %53-62; uygunluk testinde
  tam dolan emir sim 33/48 → gerçek 39/48; geniş merdiven sim −6,9…−9,9 kr/pay ve düşük dolum →
  canlı ilk pencerelerde artı ve **%100 dolum (12/12)**. Kök neden kuyruk/dolum modeli: "gözlenen
  seviye boyutunun tamamı önümüzde" varsayımı dokunuşa konan emirde fazla kötümser, rekabet
  saymadığı için derin seviyede fazla iyimser. **Hatanın büyüklüğü (5-10 kuruş) kovaladığımız
  kenarın (1-3 kuruş) kat kat üstünde.** KURAL: (a) hiçbir kulvar YALNIZ simülasyonla ÖLDÜRÜLMEZ —
  simülasyonla öldürülmüş kulvarlar yeniden değerlendirilebilir; (b) hiçbir kural YALNIZ
  simülasyonla CANLIYA ALINMAZ veya büyütülmez; (c) simülasyonun rolü ELEME ve HİPOTEZ ÜRETME,
  KARAR DEĞİL; (d) canlı test ucuz ve hızlı — TWAP pilotu 8 saatte $4,25'e cevap verdi, aynı soru
  simülasyonda haftalar aldı. Canlı protokolü değişmez: zarar kesici ZORUNLU, küçük klip, STOP
  dosyası, borsadan mutabakat, fail-closed açılış.

39. **Ofset mutlak mı göreli mi — riski FİYAT SEVİYESİNDE kontrol et.** (09-18, −$12,15)
    "Dokunuşun N tik altı" diye kurulan bir merdiven, fiyat seviyesine göre tamamen
    farklı şey yapar: bb=0,76'da 5 tik = %7 indirim (hiç ucuz değil), bb=0,20'de %25.
    Maruziyet tavanını `bb=0,50` varsayarak hesaplama — EN KÖTÜ fiyat seviyesinde
    hesapla, ya da mutlak fiyat noktaları kullan (tavan fiyattan bağımsız olur).

40. **Eşikleri kısmi dolum tıraşlar.** (09-18) 4,995 paylık kısmi dolum, "fark < 10"
    eşiğini 9,995 ile atlattı ve risk sınırı tetiklenmedi. Pay/miktar eşiklerine
    her zaman tolerans koy (≥ %5 klip).

41. **Kendi ölçüm çağrın hız sınırına takılıp botu durdurabilir.** (09-18) 120 sn'de
    2000 işlem çeken mutabakat data-api'den 999 aldı; bot fail-closed davranıp işlem
    açmadı (doğru) ama ölçüm durdu. Sayfalar arası gecikme + geri çekilme + seyrek
    çağrı; ölçüm altyapısını da bir bağımlılık gibi ele al.

42. **"Gerçekleşmiş işlem fiyatı" ile "alınabilir ask" aynı şey değildir.** (09-18)
    Aktör verisinde 0,65'ten alım görmek, o fiyattan ALABİLECEĞİN anlamına gelmez —
    o kişinin BEKLEYEN EMRİ dolmuştur, yani maker'dır; sen aynı anda ask'tan alsan
    0,95 ödersin. Arşivdeki "+9,3 kr/pay geç favori" bulgusu bu yüzden yanlıştı ve
    4 aylık defter verisiyle kenar SIFIR çıktı. Aktörün işleminden strateji
    çıkarırken önce **hangi tarafta olduğunu** belirle: maker mı, taker mı?

43. **Yüksek isabet oranı kenar değildir.** (09-18) 0,93'ten alıp %93 kazanmak
    tam olarak adil fiyatlamadır. Bir stratejinin isabetini DEĞİL, isabet ile
    ÖDEDİĞİ FİYAT arasındaki farkı ölç. 33.509 gözlemde isabet oranı her eşikte
    ask fiyatının aynısı çıktı.

44. **Küçük örneklemde "hepsi kazandı" sıradan bir olaydır.** (09-18) Aktörün
    25 işleminin 25'ini de kazanması, ortalama fiyat 0,931 iken %16,6 olasılıklı —
    altıda bir. Heyecanlanmadan önce `p^n` hesapla.

45. **Ölçüm altyapısının sabit tavanları örneklem büyüdükçe kırılır.** (09-18)
    Hız sınırını çözmek için mutabakatın sayfalamasını 500 kayda indirdim; 8 saat
    sonra oturumun işlem sayısı 500'ü aşınca "görülen işlemler yanıtta yok" koruması
    tetiklendi ve bot **yeni pencere açmayı sessizce durdurdu**. Fail-closed davranış
    doğruydu, tavan yanlıştı. Her tavanı (sayfa boyu, log kapasitesi, state boyutu,
    saklanan tx sayısı) **hedeflenen koşu süresine göre** boyutlandır ve tavana
    yaklaşıldığında uyaran bir kontrol koy — tavana dayanmak sessiz durma üretir.

46. **Test düzeneği canlı duruma YAZMAMALI — log'u yönlendirmek yetmez.** (09-18, gerçek kayıp)
    Canlı botun modülünü import edip bir fonksiyonunu çağırarak test ettim. `LOG`u
    /tmp'ye yönlendirdim ama `STATE`i yönlendirmedim; fonksiyonun içindeki
    `state_kaydet()` **canlı durum dosyasını boş sayaçlarla ezdi** — PnL tabanı ve
    158 pencerelik geçmiş silindi. Kesici sıfırdan saymaya başladı ve izin verdiği
    zarar iki katına çıktı (fark edilip düzeltildi).
    Kural: yan etkisi olan fonksiyonlar **canlı mod dışında yazmayı reddetmeli**
    (`if not LIVE: return`). Yönlendirme listesi yapmak yerine yazmayı kapat —
    unutulacak bir yol her zaman kalır.

## 09-18 turu — yeni kurallar

**#47 — Korelasyon + dar güven aralığı, müdahale için YETMEZ.**
Bir değişkenin kötü PnL ile güçlü korelasyonu (rho −0.45) ve alt grubun GA'sının
sıfırı dışlaması (−6.51, GA95[−9.8,−2.6]) bir düzeltmeyi haklı çıkarmaz.
Deploy öncesi ZORUNLU: (a) karşı-olgusal replay — o emri engelleseydik ne olurdu,
(b) pencere bazında kaç iyileşti / kaç kötüleşti, (c) MEDYAN etki, (d) önyükleme GA,
(e) kazancın en iyi 3 pencereden yüzde kaçı geldiği. "Çift tavanı" bu testlerin
dördünde de çöktü (medyan 0.00, GA[−37,+78], %170 üç pencereden) — ama ilk iki
sayıya bakıp deploy edilmek üzereydi.

**#48 — En güçlü sinyal, ticarete dönüşmeyebilir.**
A kolunun en keskin ayrışması trend/savrulma ekseninde (+6.61 vs −11.86) ama o
eksen ardışık pencerelerde KALICI DEĞİL (rho −0.07) -> önden bilinemez, kapıya
konulamaz. Daha zayıf ama kalıcı olan eksen (oynaklık, rho +0.72) kullanıldı.
Bir sinyali stratejiye çevirmeden önce SORU: bu değişkenin değerini emir
koyarken biliyor muyum?

**#49 — Kamu trade akışı pencereyi ZAMAN İÇİNDE doldurur.**
data-api bir pencerenin işlemlerini parça parça yayınlar (medyan gecikme 298 sn,
kuyruk daha uzun). Erken okuma "aktör tek taraflı pozisyon almış" gibi SAHTE
yapı üretir. Bugün iki kez yanlış çıkarım ürettirdi. Aktörün pencere düzeyinde
çift/eşsiz ayrımı, pencere bitiminden EN AZ 20 dk sonra okunmadan yorumlanmaz.

**#50 — Son N gözlemden desen okuma = seçilmiş dilim.**
"t>=250'de 5/5 kazanmış" dedim; tam örneklem 10/12 ve GA95[−22.4,+31.8].
Desen ilk gözlendiği dilimde değil, TAM örneklemde raporlanır.

**#51 — Test betiği canlı LOG'a yazmasın.**
Kapı fonksiyonunu kuru test ederken `log()` canlı LOG_ab.jsonl'e 4 sahte KAPI
satırı yazdı. (Bkz #46: aynı sınıf hata STATE ile yaşanmıştı.) Test harness'i
LOG, STATE ve her türlü kalıcı çıktıyı yönlendirmeden çalıştırma.

**#52 — Ön kayıt koddan ÖNCE değişir, sonra değil.**
18 Eylül: "kod değişmeyecek, kapı yalnız sonradan hesaplanacak" diye ön kayıt
yazdım, 20 dakika sonra kolu deterministik seçen kodu canlıya aldım ve belgeyi
güncellemedim. Dış denetim çelişkiyi dosyalardan çıkardı. Kural: davranış
değişikliği yapılacaksa ÖNCE ön kayıt yeniden yazılır (eski sürüm silinmez,
ihlal kaydıyla birlikte durur), SONRA kod deploy edilir. Aksi halde elde kalan
şey deney değil pilottur ve öyle etiketlenmelidir.

**#53 — "Fayda gösterilemedi" ile "zararlı olduğu kanıtlandı" ayni sey degildir.**
Çift tavanını reddederken "replay çürüttü" dedim; doğrusu "fayda gösterilemedi".
Medyan etkinin sıfır olması ve kazancın birkaç pencereden gelmesi tek başına
çürütme değildir — nadir büyük kazançla çalışan bir stratejide beklenen değer
yine pozitif olabilir. Reddin gerekçesi "kanıt yetersiz + uygulama riski", ve
hipotez KAPATILMAZ, ertelenir.

**#54 — Batık maliyet çift maliyetine karışmaz.**
"1,00 üstü çift = garantili zarar" yanlıştı. Eski bacağın fiyatı batıktır;
ikinci bacak ayrı bir marjinal karardır ve koşullu değeri fiyatından yüksekse
çifti 1,00 üstüne çıkarsa bile beklenen değeri İYİLEŞTİREBİLİR.

**#55 — Kendi emrimiz mid'i tutar; boy deneyi markout'u yapay düzeltebilir.**
400 payın 395'i defterde kalınca bid düşmez, mid yüksek kalır, ölçülen markout
kendiliğinden iyi çıkar — ödeme olasılığı hiç değişmeden. Boy deneyinde kendi
miktarımızdan arındırılmış referans ve terminal PnL zorunludur.

**#56 — `if not LIVE: return` oncesinde biten kuru kosu, CANLI YOLU HIC SINAMAZ.**
19 Eylul: `koy_toplu` 4'lu demete cevrildi, yanit isleme kismindaki bir acilim
3'lu kaldi. 53 birim test ve 2 pencerelik kuru kosu GECTI; canlida ilk pencerede
coktu, 11 yetim emir borsada kaldi, biri doldu. Kural: her canli-ozel kod yolu
(LIVE bayragi arkasindaki her sey) sahte client ile test edilir. Test SAYISI
degil KAPSAMI onemli.

**#57 — Cokme sonrasi ONCE borsayi sorgula, sonra yeniden baslat.**
Bot coktugunde yerel state'te olmayan emirler borsada CANLI kalir. Yeniden
baslatmak onlari gormez ve ikinci bir kume ekler. Sira: acik emirleri cek ->
iptal et -> teyit et (iptal yaniti "canceled" dese bile yeniden sorgula, ~8 sn
yayilma gecikmesi var) -> pozisyonu kontrol et -> sonra baslat.

**#58 — OLCUMUN BIRIMI, KARARIN BIRIMIYLE AYNI OLMALI.**
19 Eylul, ayni veriden UC kez zit sonuc cikti, hepsi toplama biriminden:
  (a) fiyat bandi kenari: PAY-agirlikli +1,85  vs  PENCERE-esit -5,28
  (b) fiyat x zaman haritasi: pencere-esit harita, gercek sonucumuzla
      korelasyon -0,931 (yani TERSINI soyluyordu)
  (c) zaman kurali: DOLUM duzeyinde "t<60 kenari +2,34" -> GEC_KES=60 yaptim;
      CUZDAN-PENCERE duzeyinde "isi t<60'ta biten katilimci -0,65" -> geri aldim.
Kural: bir olcumu stratejiye cevirmeden once sor — "bu olcumun birimi ile benim
karar verdigim birim ayni mi?" Biz PENCERE basina karar veriyoruz (izgarayi koy,
sonucu al). O halde kiyas da cuzdan-pencere duzeyinde olmali. Dolum duzeyi
olcumu 'hangi dolum iyi' der, 'hangi politika iyi' DEMEZ.

**#59 — KENDI PROFILINI KIYAS POPULASYONUNDA ARA.**
"Neden kaybediyoruz" sorusunun en dogrudan cevabi: zincir defterinde bizim
TAM profilimize (klip boyu x zaman penceresi x fiyat bandi) uyan cuzdan-pencere
kayitlarini bul ve onlarin getirisine bak. 19 Eylul: bizim hucre -2,47
[-6,11,+0,85], canlimiz -1,85. Ortusuyordu -> uygulama saglam, PROFIL yanlis.
Bu ayrim olmadan haftalarca 'kod hatasi' aranabilirdi.

**#60 — PAYLASILAN VERI YUKLEYICI, TEK HATAYI HER SONUCA TASIR.**
`data-api /trades` varsayilani `takerOnly=true`. Bu, tek bir yardimci fonksiyonda
yazildi ve her yeni analiz onu kopyaladi. UC AY boyunca aktor hakkinda uretilen
her sonuc (yon kenari, rol ayrimi, cift maliyeti, markout) bu akisin %18'ine
bakiyordu. Kimse veri KAYNAGINI sorgulamadi; herkes onun ustundeki ANALIZI
sorguladi. Uzerine yazilan hafiza kayitlari da yanlisi dogru kabul edip
pekistirdi -> yanlis temel kendini dogrulatti.
KURAL: (a) her dis veri cagrisinin VARSAYILAN parametreleri acikca yazilir,
(b) yeni bir kulvara baslarken veri yukleyici bir kez bagimsiz dogrulanir
(ornek: iki farkli parametreyle cek, fark var mi diye bak),
(c) bir hafiza kaydi bir olcume dayaniyorsa, olcumun YONTEMI de kayda girer ki
sonradan cürütülebilsin.
NOT: bu hatayi proje ici hicbir tur bulmadi; DIS denetim buldu (PRO, 09-18),
cunku projenin hafizasina bagli degildi ve "bu cagriniin varsayilani ne?" diye
sordu — uc aydir kimsenin sormadigi soru.

## 61. "Basarili olanlar sunu yapiyor" -> once SECIM ARTEFAKTI diye oku
2026-09-19. "Gec cift kuranlar +6.79 kr/pay kazaniyor, demek ki gec kalmali"
dedim. YANLIS. Olen tarafi 0,05'ten ancak ILK BACAGIN KAZANIYORSA alabilirsin;
"gec cift kurdum" kosulu "ilk bacagim kazandi" kosuluyla ayni sey. Ayni tuzaga
"iki bacak da <=0,40 olanlar +13,55" olcumunde de dustum.
KURAL: bir DAVRANISIN getirisini olcerken, o davranisin GERCEKLESMIS OLMASI
sonucun kendisine bagliysa sayiyi kullanma. Dogru birim MARJINAL KARAR:
"o emri acik birakmak neye mal oldu" -> ayni kesitte marjinal dolum -0,08/+0,02
yani SIFIR cikti, +6,79 degil.
TEST: "bu grubu tanimlayan sey, olcmek istedigim sonucun bir fonksiyonu mu?"
Evet ise grup gecersiz.

## 62. Modelin ONGORU BECERISI kanitlanmadan model KAZANAN'i kapatamaz
2026-09-19. TAM EV merdiven simulasyonu canli izgaramiz (v2) icin +0,19 kr/pay
ongordu; canli 16 pencerede +14,2 verdi. Ayni model derin izgara icin +0,96
diyordu ve buna dayanip v2'yi kapatmak uzereydim.
KURAL: bir modelle CANLI ve ARTIDA olan bir yapilandirmayi degistirecegin anda
once sor: bu model o yapilandirmanin canli sonucunu ongorebildi mi? Ongoremediyse
model sıralama icin de guvenilir degildir. Cozum tek tarafli gecis DEGIL,
RASTGELE ATAMALI A/B: kontrol kolu dokunulmadan kalir.
NOT: bunun tersi de gecerli — 16 pencere gurultudur, o yuzden v2 "kazandi" da
denmez. A/B ikisini de dogru sekilde askida birakir.

## 63. Bir kolun iki degisikligi ayrilamiyorsa PAKET oldugunu ON KAYITTA yaz
2026-09-19. Derin izgara (tum basamaklar <=0,20) mevcut gec-kesme kurali
(px<=0,25 iptal) altinda TUM emirlerini kaybederdi. Yani "izgara" ve "gec kural"
ayrilamaz. Kol B bu yuzden bir PAKET; sonucu "izgara kazandi" diye okumak YASAK,
"paket kazandi" denir ve ayristirma ayri bir deney olur.

## 64. DOGRU OLCUM + YANLIS EYLEM = "curumus" gibi gorunur
2026-09-19. Rejim kapisi 09-18'de kuruldu, 09-19'da "IPW ile curudu" diye
kapatildi (+0,70 GA[-3,65,+4,74]). Meger OLCUM DOGRUYDU ve esik (16,4 bps) tam
optimumdaydi; yanlis olan EYLEMDI: sakin pencerede TICARETI DURDURMAK yerine
KOL DEGISTIRIYORDU. Yani kaybettiren pencerelerde oynamaya devam ediyordu.
Dogru eylemle ayni olcum: A kolu +0,48 [-0,26,+1,28] -> +1,67 [+0,49,+2,75],
ornek disi kararli (egitim +2,21 / test +2,09).
KURAL: bir sinyal "curudu" demeden once sor: sinyali mi test ettim, yoksa
sinyal + O SINYALE BAGLI BELIRLI BIR EYLEMI mi? Ikincisiyse, olumsuz sonuc
sinyali degil EYLEMI curutur. Sinyalin kendisi ayrica test edilmelidir.
Ayrica: GA sifiri kapsiyorsa bu "curudu" DEGIL "gucsuz"dur (#? ile ayni hat).

## 65. Kalicilik olcerken OLCUTUN KENDISI dongusel olmasin
2026-09-19. "Kazanan pencere onceden bilinebilir mi?" sorusuna once
Polymarket islem fiyatlarindan turetilmis "savrulma" ile baktim: kalicilik
Spearman +0,048 -> "bilinemez" dedim. Ama o olcut bizim dolumlarimizla AYNI
veriden geliyordu (islem gormeyen seviye = kucuk savrulma = dolum yok).
BAGIMSIZ kaynaktan (BTC spot) olculunce kalicilik **+0,676** cikti.
KURAL: X sonucu ongoruyor mu diye bakarken, X'i sonucun uretildigi veriden
turetme. Bagimsiz kaynak yoksa bulgu "yok" degil "OLCULEMEDI"dir.

## 66. `pkill -f` ASLA kendi komut satirinla ayni pakette olmasin (3. tekrar)
2026-09-19, ucuncu kez. `pkill -f "record_fills_tape"` yazdim; kabugun KENDI
komut satirinda da o metin geciyordu -> pkill kabugu oldurdu (exit 144).
Ilk iki seferde zarar gorunurdu (betik yazilmadi, fark ettim). UCUNCUSUNDE
SESSIZ zarar verdi: ayni pakette pkill'den SONRA gelen `cat > betik.py <<EOF`
hic calismadi, diskte ESKI BOZUK surum kaldi, ben de onu baslattim ve
5 dakika bos kayit yapti. Hata mesaji yoktu.
KURAL:
  1. pkill/pgrep -f desenini ASLA ayni komut paketinde kullanma; ayri cagri yap.
  2. Oldurmek icin PID kullan (`pgrep` ciktisini once oku, sonra `kill <pid>`).
  3. Bir betigi yazip baslatiyorsan, BASLATMADAN ONCE icerigini dogrula
     (ornegin `grep -c <eski_ifade> betik.py` -> 0 bekle). Yazdigini varsayma.
