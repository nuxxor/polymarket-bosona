| aşama | boyut | id | başlık | önem | ajan hükmü | çürüten/oy | sonuç |
|---|---|---|---|---|---|---:|---|
| audit | D1_accounting | D1-1 | BTC15dk muhasebe yeniden üretimi | important | DOĞRULANDI | 0/3 | hayatta |
| audit | D1_accounting | D1-2 | Diğer grupların PnL toplamları | important | DOĞRULANDI | 0/3 | hayatta |
| audit | D1_accounting | D1-3 | MERGE/REDEEM ödeme sınırı ihlali kontrolü | important | DOĞRULANDI | 0/3 | hayatta |
| audit | D1_accounting | D1-4 | usdcSize alanı ücret semantiği | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D1_accounting | D1-5 | Kazanç örneği btc-updown-15m-1789708500 | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D1_accounting | D1-6 | Kayıp örneği btc-updown-15m-1789564500 | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D1_accounting | D1-7 | Aynı saniye belirsizliği sıklığı ve etkisi | minor | GÖZLEMSEL DESTEK | 0/1 | hayatta |
| audit | D2_causality: Zaman sızıntısı ve nedensellik denetimi | D2-1 | candidate.replay() gelecek fiyat kullanımı (look-ahead bias) | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| audit | D2_causality: Zaman sızıntısı ve nedensellik denetimi | D2-2 | btc15_context.py::price() tazelik kontrolü doğru (iki katmanlı rcv+obs) | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D2_causality: Zaman sızıntısı ve nedensellik denetimi | D2-3 | bosona_derin.py::spot_at() nedensellik kontrolü doğru | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D2_causality: Zaman sızıntısı ve nedensellik denetimi | D2-4 | bosona_derin.py::fair_twap() 5dk→15dk adaptasyonu matematiksel olarak doğru | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D2_causality: Zaman sızıntısı ve nedensellik denetimi | D2-5 | fair_twap::known_seconds hesabı mevcut saniyeyi hariç tutuyor (nedensel) | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D2_causality: Zaman sızıntısı ve nedensellik denetimi | D2-6 | analyze.py::models() StandardScaler yalnız train'de fit | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D2_causality: Zaman sızıntısı ve nedensellik denetimi | D2-7 | study.py::at() age limiti gelecek verisini engelliyor | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D2_causality: Zaman sızıntısı ve nedensellik denetimi | D2-8 | Chainlink veri gecikmesi ölçüldü: medyan 1.19 sn | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D2_causality: Zaman sızıntısı ve nedensellik denetimi | D2-9 | histories fiyat yaşı: medyan 33 sn, '35-45 sn geride' iddiası kısmen doğru | minor | GÖZLEMSEL DESTEK | 1/1 | çürütüldü |
| audit | order_identity | D3-F1 | Activity API tek satır/tx gösteriyor, zincir 3.55 fill/tx içeriyor | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| audit | order_identity | D3-F2 | Geç ekleme (age≥600) TÜMÜ yeni emir, erken parent devamı 0 | decision_changing | DOĞRULANDI | 1/3 | hayatta |
| audit | order_identity | D3-F3 | Maker/taker fill oranı 2.55:1, eşit paylarla 773:303 | important | DOĞRULANDI | 1/3 | hayatta |
| audit | order_identity | D3-F4 | Emir ömrü (ilk dolum→son dolum) ölçülebilir ama emir oluşturma zamanı yok | minor | ÖLÇÜLEMİYOR | 0/1 | hayatta |
| audit | order_identity | D3-F5 | Zaman pencere paketleme orderHash'i undercount ediyor (1sn:5.1, 5sn:5.8, 10sn:6. | important | GÖZLEMSEL DESTEK | 1/3 | hayatta |
| audit | order_identity | D3-F6 | Transaction'ların %23.1'i hem Up hem Down alışı içeriyor | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | order_identity | D3-F7 | OrderHash'lerin %99.5'i tek rol (maker veya taker), %0.5'i karma | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D4_controls_stats | D4-01 | Kaliperler post-hoc eklendi; sonuçlar kaliper seçimine son derece duyarlı | decision_changing | DOĞRULANDI | 1/3 | hayatta |
| audit | D4_controls_stats | D4-02 | No-add kontrolleri 'gözlenen işlem yok' durumlarını kullanıyor; 'emir yok' değil | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| audit | D4_controls_stats | D4-03 | Lojistik model ceiling_pass/probability_pass özellikleri mekanik olarak fiyat/ed | important | GÖZLEMSEL DESTEK | 0/3 | hayatta |
| audit | D4_controls_stats | D4-04 | Bootstrap sadece 3 günle yapılıyor; day clustering zayıf, geniş CI | important | DOĞRULANDI | 0/3 | hayatta |
| audit | D4_controls_stats | D4-05 | 'En iyi 3 hariç' kriteri sonucu %131 değiştiriyor | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| audit | D4_controls_stats | D4-06 | Conditional completion selection bias içerir; policy backtest değil | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| audit | D5_candidate_execution | F1 | Candidate models taker execution; Bosona is 81% maker | decision_changing | DOĞRULANDI | 1/3 | hayatta |
| audit | D5_candidate_execution | F2 | Tight value filters yield 3.6% entry rate (21/591) | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D5_candidate_execution | F3 | Only 1 addition in 21 entries (4.8% addition rate) | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D5_candidate_execution | F4 | unit_cost() formula correct for taker, does not implement maker fee | important | DOĞRULANDI | 0/3 | hayatta |
| audit | D5_candidate_execution | F5 | Portfolio and cross-market limits not implemented | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D5_candidate_execution | F6 | Completion ages: continuous vs discrete mismatch is benign | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D5_candidate_execution | F7 | Tests pass: internal logic correct | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D6_mechanism_probability | D6-F1 | Model advantage limited to final 300 seconds | important | DOĞRULANDI | 0/3 | hayatta |
| audit | D6_mechanism_probability | D6-F2 | fair_twap() uses 5m constants for 15m markets | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D6_mechanism_probability | D6-F3 | Chainlink reference observable within 2.5s | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D6_mechanism_probability | D6-F4 | BTC15m mechanism 100% validated | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D6_mechanism_probability | D6-F5 | BTC hourly mechanism 100% validated | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D6_mechanism_probability | D6-F6 | Drift probability poorly calibrated | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D7_selection_first_entry | D7-001 | Sept 21 morning maturation claim incorrect | important | DOĞRULANDI | 2/3 | çürütüldü |
| audit | D7_selection_first_entry | D7-002 | Rol sınıflandırması (557 maker / 41 taker) doğrulandı | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D7_selection_first_entry | D7-003 | Paket miktarları (49.8 / 70.5 / 80.9) doğrulandı | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D7_selection_first_entry | D7-004 | Chainlink uyumu çok düşük (27.8% olasılık, 41.7% momentum) | decision_changing | DOĞRULANDI | 1/3 | hayatta |
| audit | D7_selection_first_entry | D7-005 | İlk yön ucuz/pahalı taraf tercihi yok (49.1% ucuz) | important | DOĞRULANDI | 1/3 | hayatta |
| audit | D7_selection_first_entry | D7-006 | İşlemsiz pencerelerde Bosona-benzeri bid YOK | decision_changing | DOĞRULANDI | 3/3 | çürütüldü |
| audit | D7_selection_first_entry | D7-007 | İşlemsizlik Pazartesi/Pazar yoğunlaşması (87%) | important | DOĞRULANDI | 1/3 | hayatta |
| audit | D7_selection_first_entry | D7-008 | Seçim modelleri: 'already_entered' 3131 boşluk | important | DOĞRULANDI | 1/3 | hayatta |
| audit | D7_selection_first_entry | D7-009 | ETH/SOL 15dk hepsi maker, BTC15 ise %93 maker | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| audit | D8_new_period_books | D8-F1 | Yetersiz örneklem boyutu | important | DOĞRULANDI | 1/3 | hayatta |
| audit | D8_new_period_books | D8-F2 | Ücret imzası rol sınıflandırıcısı doğrulandı | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D8_new_period_books | D8-F3 | Geç ekleme PnL küçük tutarsızlık | minor | KARŞI KANIT | 1/1 | çürütüldü |
| audit | D8_new_period_books | D8-F4 | Maker dolumların %60,5'i önceden var olan emirlerde | important | DOĞRULANDI | 1/3 | hayatta |
| audit | D8_new_period_books | D8-F5 | Dönem kapsama sınırlı (7,4 saat) | important | DOĞRULANDI | 3/3 | çürütüldü |
| audit | D8_new_period_books | D8-F6 | S defter kalitesi sayıları doğrulandı | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D9_cross_asset | F1 | RAPOR ana tablo sayıları doğrulandı | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| audit | D9_cross_asset | F2 | BTC15dk maker-dominant + taker-negatif yapısı 7/8 grupta tekrar ediyor | important | DOĞRULANDI | 2/3 | çürütüldü |
| audit | D9_cross_asset | F3 | Geç ekleme (add) maker-ağırlıklı ve pozitif; tamamlama taker-ağırlıklı ve negati | decision_changing | DOĞRULANDI | 2/3 | çürütüldü |
| audit | D9_cross_asset | F4 | "Aynı bot" sorusuna kanıt yetersiz - ilk giriş zamanlaması grup içinde tutarlı,  | important | KANIT YETERSİZ | 1/3 | hayatta |
| audit | D9_cross_asset | F5 | Saatliklerde Binance 1H mekanizması ile 5/15 dk Chainlink mekanizmasının davranı | important | GÖZLEMSEL DESTEK | 2/3 | çürütüldü |
| audit | D9_cross_asset | F6 | Düşük yoğunlaşma: en iyi 3 piyasa toplam PnL'nin %3,5-12% ini oluşturuyor | important | GÖZLEMSEL DESTEK | 0/3 | hayatta |
| audit | D10_code_repro_numbers | D10-001 | İki kaynak dosyanın MAIN sürümü donmuş kopyadan farklı | important | DOĞRULANDI | 2/3 | çürütüldü |
| audit | D10_code_repro_numbers | D10-002 | report.py protocol.json'ı her çalıştırmada yeniden yazıyor | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D10_code_repro_numbers | D10-003 | Portföy geneli limitler (max_portfolio_open_worst_loss, max_overlapping_new_risk | important | DOĞRULANDI | 1/3 | hayatta |
| audit | D10_code_repro_numbers | D10-004 | check_research.py test kapsamı sınırlı: sabit toplam varlığı kontrol eder, hata  | minor | GÖZLEMSEL DESTEK | 1/1 | çürütüldü |
| audit | D10_code_repro_numbers | D10-005 | src/ modüllerinde __file__ tabanlı yol belirleme: farklı konumdan çalıştırmada y | minor | GÖZLEMSEL DESTEK | 1/1 | çürütüldü |
| audit | D10_code_repro_numbers | D10-006 | Tüm kontrol edilen sayısal iddialar kaynaklarla eşleşiyor | minor | DOĞRULANDI | 0/1 | hayatta |
| audit | D10_code_repro_numbers | D10-007 | Reproduksiyon başarılı: 14 R/results ve 16 F/results dosyası deterministic hash' | minor | DOĞRULANDI | 0/1 | hayatta |
| gap | gap_real_ask_completion_backtest | GAP-1 | Real ask backtest veri kapsamı %100 ama timing sınırlı | important | DOĞRULANDI | 2/3 | çürütüldü |
| gap | gap_real_ask_completion_backtest | GAP-2 | Completion'ların %61.8'i maker fill - 'assumed taker opportunity' modeli yanlış | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| gap | gap_real_ask_completion_backtest | GAP-3 | Book spread'leri çok geniş (bid 0.001, ask 0.999), completion execution spread i | minor | DOĞRULANDI | 0/1 | hayatta |
| gap | gap_real_ask_completion_backtest | GAP-4 | 'Conditional completion FIFO ≤0.98' kuralının gerçek ekonomik maliyeti ölçülemiy | decision_changing | GÖZLEMSEL DESTEK | 2/3 | çürütüldü |
| gap | gap_real_ask_completion_backtest | GAP-5 | D4-F6 sorusunun yanlış çerçevesi: 'ask geçiş backtest' yerine 'maker fill olasıl | important | DOĞRULANDI | 2/3 | çürütüldü |
| gap | D2_causality | D2-1-lookahead-confirmed | candidate.replay() decision filters use future execution prices (0.25-90s ahead) | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| gap | D2_causality | D2-1-bosona-comparison-invalid | Candidate-Bosona karşılaştırması look-ahead bias nedeniyle geçersiz | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| gap | D2_causality | D2-1-gap-categories-shift | Gap kategorileri execution-time'dan decision-time'a kaydı | important | DOĞRULANDI | 0/3 | hayatta |
| gap | D2_causality | D2-1-fix-validation | Düzeltilmiş kod tüm testleri geçiyor, entry consistency korunuyor | minor | DOĞRULANDI | 0/1 | hayatta |
| gap | single_vs_multi_bot_concurrency | CONC-F1 | Pozisyon çakışması median 8 grup | decision_changing | DOĞRULANDI | 2/3 | çürütüldü |
| gap | single_vs_multi_bot_concurrency | CONC-F2 | Çapraz grup transaction batching sıfır | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| gap | single_vs_multi_bot_concurrency | CONC-F3 | Risk korelasyonu grup-bağımsız | important | DOĞRULANDI | 3/3 | çürütüldü |
| gap | single_vs_multi_bot_concurrency | CONC-F4 | Aynı coin kısa periyotlar yakın zamanlı başlıyor | important | GÖZLEMSEL DESTEK | 0/3 | hayatta |
| gap | single_vs_multi_bot_concurrency | CONC-F5 | 1d periyodu diğer periyotlardan ayrışıyor | important | DOĞRULANDI | 1/3 | hayatta |
| gap | single_vs_multi_bot_concurrency | CONC-F6 | Fill eşzamanlılık düşük | minor | DOĞRULANDI | 0/1 | hayatta |
| gap | gap_eth_sol_bnb_hourly_mechanism | GAP-1 | ETH/SOL/BNB saatlik Binance mekanizması BTC ile %100 aynı | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| gap | gap_eth_sol_bnb_hourly_mechanism | GAP-2 | BNB 153 piyasa, ETH/SOL 204 - mekanizma farkı yok | minor | DOĞRULANDI | 0/1 | hayatta |
| gap | gap_eth_sol_bnb_hourly_mechanism | GAP-3 | D9-F5 'Binance 1H mekanizması farkı' iddiası DOĞRULAMASIZ | decision_changing | KARŞI KANIT | 1/3 | hayatta |
| gap | gap_untrade_48_markets_root_cause | GAP-001 | 48 Sep 21 untrade markets: post-shutdown temporal boundary | decision_changing | DOĞRULANDI | 1/3 | hayatta |
| gap | gap_untrade_48_markets_root_cause | GAP-002 | Pre-shutdown untrade pattern: Monday/Sunday effect | important | GÖZLEMSEL DESTEK | 1/3 | hayatta |
| gap | maker_placement_timing_adverse_selection | GAP-1 | Bid presence rates confirm prior t-1 finding | minor | DOĞRULANDI | 0/1 | hayatta |
| gap | maker_placement_timing_adverse_selection | GAP-2 | Bid stability: sadece %20.7 gerçekten pasif | important | DOĞRULANDI | 0/3 | hayatta |
| gap | maker_placement_timing_adverse_selection | GAP-3 | Pasif maker KÖTÜ adverse selection, aktif maker İYİ | decision_changing | DOĞRULANDI | 2/3 | çürütüldü |
| gap | maker_placement_timing_adverse_selection | GAP-4 | Adverse selection = sonuç çözümü, likidite riski DEĞİL | decision_changing | DOĞRULANDI | 1/3 | hayatta |
| gap | maker_placement_timing_adverse_selection | GAP-5 | D3-F2 contradiction resolved: geç dolum ≠ pasif bekleme | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| gap | maker_placement_timing_adverse_selection | GAP-6 | Data gap: %42.2 fill hiç book'ta yok | important | GÖZLEMSEL DESTEK | 2/3 | çürütüldü |
| gap | gap_first_entry_time_pattern | F1 | İlk giriş zamanı SABİT DEĞİL - geniş dağılım gözlendi | important | DOĞRULANDI | 0/3 | hayatta |
| gap | gap_first_entry_time_pattern | F2 | Piyasa koşulları (spread/volatility/edge) ile korelasyon YOK | important | DOĞRULANDI | 1/3 | hayatta |
| gap | gap_first_entry_time_pattern | F3 | Zamansal clustering: hour/day etkisi orta düzeyde | minor | DOĞRULANDI | 0/1 | hayatta |
| gap | gap_first_entry_time_pattern | F4 | Dış likidite bekleme modeli en uygun açıklama | important | GÖZLEMSEL DESTEK | 0/3 | hayatta |
| gap | gap_first_entry_time_pattern | F5 | selection_rows already_entered boşluğu dolduruldu | minor | DOĞRULANDI | 0/1 | hayatta |
| gap | gap_first_entry_time_pattern | F6 | Çok erken girişler önemli kısım oluşturuyor | minor | DOĞRULANDI | 0/1 | hayatta |
| gap | gap_m1_m2_mechanism_test | GAP-M1-1 | İlk giriş %93 maker - M1 pasif kotasyon destekleniyor | important | DOĞRULANDI | 0/3 | hayatta |
| gap | gap_m1_m2_mechanism_test | GAP-M1-2 | Maker ilk girişlerde adverse selection pozitif (lehine) - M1 destekliyor | important | DOĞRULANDI | 1/3 | hayatta |
| gap | gap_m1_m2_mechanism_test | GAP-M1-3 | Geç ekleme (600-899 sn) %93.7 maker - dinlenen emirler dolması | important | DOĞRULANDI | 0/3 | hayatta |
| gap | gap_m1_m2_mechanism_test | GAP-M1-4 | S period maker dolumlarının %57.8'inde önceden bid liquidity vardı | important | DOĞRULANDI | 0/3 | hayatta |
| gap | gap_m1_m2_mechanism_test | GAP-M2-1 | Tamamlamalar taker-ağırlıklı ama negatif PnL - M2 'risk azaltımı' hipotezi çeliş | decision_changing | DOĞRULANDI | 2/3 | çürütüldü |
| gap | gap_m1_m2_mechanism_test | GAP-M1M2-1 | M1 vs M2 ayırıcı kontrollü test eksik - piyasa-bazında mekanizma sınıflandırması | decision_changing | DOĞRULANDI | 0/3 | hayatta |
| gap | gap_m1_m2_mechanism_test | GAP-M2-2 | Envanter trajectory (net position grow → completion → shrink) visualizasyonu/tes | important | DOĞRULANDI | 1/3 | hayatta |
| gap | gap_m1_m2_mechanism_test | GAP-M2-3 | FIFO cost trajectory (cost >1 ise completion) testi eksik | important | GÖZLEMSEL DESTEK | 0/3 | hayatta |
