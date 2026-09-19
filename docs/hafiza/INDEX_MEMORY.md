# Polymarket Trading Bot - Memory

One line per memory. Detail lives in the linked topic file — open it before acting.
Pre-2026-07-26 verbose index: [archive-20260726](project_index_archive_20260726.md); pre-2026-06-09: [archive-20260609](project_index_archive_20260609.md).

## Emekli — yeniden başlatma yasak

- 🪦 **HL RS AGENT SHADOW (08-29):** edge doğrulanmadı; operatör emriyle cron, runtime, kaynak, test, handover ve veri artefaktları silindi. Yeni açık operatör talebi olmadan yeniden oluşturma, çalıştırma veya schedule etme.

## Aktif kulvarlar (yeniden eskiye)
- [📊 BOSONA BTC5m GÜN+ÇİFT (09-19): zincirde 19/19 gün artı +2,27 kr/pay ~110k pay/gün; bugün +0,12 = dip gün; işlem PnL'i tamamen çift maliyeti (<0,85 +10 / >1,10 −13,9); rebate $663/gün; 2. bacak 0,19 (kazanç) vs 0,78 (hedge)](project_bosona_btc5m_gun_ve_cift_20260919.md)
- [Devir + ortam 09-19](project_devir_ve_ortam_20260919.md) — Binance vadeli WS bu ağdan veri vermiyor (spot çalışıyor); dolum kasedi limit=500 yüzünden %70 eksikti → sayfalı sürüm + backfill; bosona /activity tam; izleme betikleri scripts/izleme/
- [⏸️ VOL KAPISI KAPATILDI 09-19 19:09Z (operatör: %85 atlıyordu; 4 açılan / ~30 atlanan gölge kaydı duruyor)] - [🚪 VOL KAPISI CANLI (09-19 15:47Z, fikir KULLANICIDAN): kazanan pencere ONCEDEN secilebiliyor — oynaklik kalici (Spearman +0,676), ORNEK DISI KARARLI (egitim +2,21 / test +2,09), A kapisiz +0,48[-0,26,+1,28] → vol5>15: +1,67[+0,49,+2,75], B de ayni; eski rejim kapisi ayni olcumu yapiyordu ama YANLIS EYLEM (kol degistiriyordu, pencere atlamiyordu) → "dogru olcum + yanlis eylem = curumus gorunur"](project_vol_kapisi_20260919.md)
- [🧲 KUYRUK OLCUMU BASLADI (09-19 15:15Z): defter kaydedicisi calisiyor (`data/db/polymarket_orderbook.db`), ILK DOGRUDAN olcum — 5 paylik emrimizin ONUNDE 383-3.692 pay (medyan 710) → seviyenin TAMAMI supurulunce doluyoruz = tam olarak kaybettiren durum; olcum hatti `scratchpad/kuyruk.py`, saatlik kalici olcumde](project_kuyruk_olcumu_20260919.md)
- [🧪 IZGARA v3 A/B CANLI (09-19): 30 hucrelik haritada ulasabildigimiz uzayda ARTIDA HUCRE YOK (taban -0.39, 7 hucre eksi ayrisiyor); bosona'nin kenari tamamen >0.40 pencerelerinde (<=0.40 pencerelerinde O DA -3.53) ama onu maker kopyalamak -19.74 (0.80'e duran alis ancak fiyat DUSUNCE dolar); "gec cift +6.79" ve "iki bacak <=0.40 +13.55" SECIM ARTEFAKTI, marjinal dolum SIFIR; simulasyon v2 icin +0.19 dedi canli +14.2 verdi -> modelin becerisi yok, kazanan izgara kapatilmadi, RASTGELE A/B kuruldu (A=v2 kontrol, B=v3 derin [.20..03])](project_izgara_v3_ab_20260919.md)
- [🎯 **PROFİL TEŞHİSİ (09-19)**: canlı −1,85 UYGULAMA HATASI DEĞİL — zincirde bizim tam profilimiz (5-9 pay + t<60 + ort 0,25-0,33) **−2,47** [−6,11,+0,85]. Bandımız DOĞRU (+0,77), zamanlamamız yanlıştı: t<60 −0,65 / t60-150 −1,73 / **t150+ +0,31**. GEC_KES=60 geri alındı. **Metodoloji dersi (#58): dolum düzeyi "t<60 +2,34" derken cüzdan-pencere düzeyi "−0,65" diyor — strateji kararı CÜZDAN-PENCERE biriminde verilir.** Ayrıca "ilk bacak paraya yakın" çürüdü (0,20-0,35 → +0,64 en iyi), tavan PnL'i değiştirmiyor (ikisi de ~0)](project_profil_teshisi_20260919.md)
- [📉 **UCUZ BANT DENEYİ BİTTİ (09-19)**: 142/300 pencere, **−1,85 kr/pay**, −$38,35 → **BELİRSİZ** (sıfırdan 0,82σ, ama bütçe projeksiyonu kesiciyi aşıyordu; bot 12sa MAX_SAAT'te kendi durdu). Yapı net: **çift kurulunca +15,40 / tek taraflı −25,41**, eksik olan ÇİFT KURMA SIKLIĞI (biz %41, bosona %65). **Replay modeli doğrulandı** (mevcut politikayı −0,645 dedi, canlı −1,85) → cancel60'ın +2,06 tahminine güven. 0,40 tavanı 142 pencerede %100 tuttu](project_ucuz_bant_deney_sonucu_20260919.md)
- [🔬 **GPT ULTRA DENETİMİ (09-19)**: aday **GEC_KES=60/UCUZ_ESIK=0.40** (+$966 replay, medyan +$0,70, en iyi-3 %1,96 → #47 geçiyor) AMA kapsam %95'te −1,10, aile p=0,129, kararlılık kapısı BAŞARISIZ, kendi dolumlarımızda GA sıfırı kapsıyor → **deney, terfi değil**. **Rebate formülü: `0.014·q·p·(1−p)`, 5 pay yeterli** (0,24@0,22 → 0,336@0,40); rebate farmlama optimum DEĞİL. Benim 4 iddiam çürüdü (klip boyu, sabit rebate, kaskad ayrımı, +5,20 aritmetiği) + 2 kod kusurum bulundu](project_gpt_ultra_denetim_20260919.md)
- [💵 **MAKER REBATE ÖDENİYOR (09-19)**: $13/24sa, 4.820 pay üzerinden **0,27 kr/pay** — dokümante 0,35 tavanıyla uyumlu. Likidite ödülünden AYRI program (o hâlâ fonlanmıyor). Kol A: işlem kenarı +0,70 + rebate 0,27 = **+0,97 kr/pay**, ve rebate VARYANSSIZ. Tam gün ~$13,6/gün. Hacimle ölçekleniyor mu, eşiği var mı — HİÇ optimize edilmedi](project_maker_rebate_gercek_20260919.md)
- [🎯 **BOSONA BTC15 KENARI ÇÖZÜLDÜ (09-19)**: kenar dokunuşta DEĞİL, dokunuşun ALTINDA — mid−3,5 kr, seviye sırası 2, 50 pay, pazar başına 1 dolum, çift YOK: **+20,51 kr/pay GA[+7,5;+33,8]**, 16/19 gün; dokunuş +2,96 (GA sıfır, ex-top3 eksi), taker gürültü. Haziran Family H aynı yerleşimde −8,66. GECE: 216 hücrelik ızgara hiçbiri GA sıfırı dışlamıyor (en iyi +2,93 [−0,05;+5,88]); fark markout'ta (o +7,3 / biz −0,35 @60sn); **kaskad testi: zehirli ve iyi dolum öncesi defter AYNI → hız ayıramaz, COLOCATION HAYIR**; ileri gölge live_v9 05:45'te başladı. 24 saatte en çok kazandığı aile BTC15 +$3.037; **/activity ucu MERGE+REBATE gösteriyor ($38.735 merge, günde $663 rebate); KENAR İCRA DEĞİL YÖN (+8,3 puan, geç pencerede) ama yön kuralı bulunamadı: momentum/referans-takibi/fade/hız 5 hipotez de elendi; günlük std 13,3 ve %60'ı 3 günden**](project_bosona_btc15_edge_20260919.md)
- [🗺️ **FİYAT×ZAMAN HARİTASI (09-19)**: 19 gün/220M pay/4.430 pencere zincir verisi, pencere-eşit, 17 hücrenin GA'sı sıfırı dışlıyor. **Ucuz+ERKEN artı** (0,10-0,20 @t<60 **+7,53**), **ucuz+GEÇ eksi** (0,20-0,30 @t≥240 **−9,66**) — aynı fiyat ters işaret. **En güçlü hücre 0,60-0,80 @ t≥240 = +10,92 [+9,40,+12,23]** ve oraya HİÇ girmedik. 0,40-0,50 her zaman eksi (kol B'nin evi). Kaybımız strateji değil YER ve ZAMAN](project_fiyat_zaman_haritasi_20260919.md)
- [🔓 **KÜÇÜK KLİPLİ KAZANANLAR (09-19) — PARK GERİ ÇEKİLDİ**: zincir defterinde ≥50k paylık 475 cüzdanın %49'u artıda, **bosona ancak 22.**; küçük klipli sınıfta (medyan ≤15 pay) 229 cüzdanın 132'si artıda. `0x5d5f7080` **medyan 5 pay** / 2.562 pencere / +3,23 GA[+1,56,+4,96] / 17-19 gün artı. "Kenar boy ister" ÇÜRÜDÜ. En az 3 profil: sığ-ucuz-erken (%100 hacim 0-0,30, t=28, +4,67), pencere-öncesi (t=−8, +2,82), pahalı-bantta-seçici (+5,20 vs piyasa −1,97)](project_kucuk_klipli_kazananlar_20260919.md)
- [🅿️ **BTC5m MAKER PARK (09-19)**: sinyal ÇÖZÜLDÜ (Chainlink marjı ≥3bps → t=270'te **1.006 pencerede 0 hata**), arz var (130-350 pay/pencere @0,99), ama önde **medyan 24.000 pay** — iyimser kuyrukta %74 dolum, gerçekçi kuyrukta %1,2. **Bağlayıcı kısıt sermaye DEĞİL, kuyruk önceliği** ($4k da $540 da aynı yerde). Ölen: derin merdiven (sabit boyla 0,20-0,40 bandı −5,28), mid takibi (%39 hacim ≥0,45'te), rejim kapısı (hacim çeyreği öngörülemez, Spearman ~0), boy (1.526+ pencere gerek), hızlı iptal (dolumların %94'ünü siliyor). 6 hipotezim kendi verimle çürüdü, hiçbiri canlıya girmedi](project_btc5m_maker_kapanis_20260919.md)
- [🧭 **BREAKTHROUGH REVIEW (09-19)**: BTC5m derin merdiven maker'da pozitif EV YOK — kayıp = kaskad (kalabalık 100-250 ms'de çekiliyor, biz artık likidite) + bilgili akışa 7x maruziyet; bosona BTC5m 515 pencere +0,82 GA sıfırı kapsıyor, brief'in +5,06'sı elverişli dilim, kârı BTC15m'de (+3,21 GA dışlıyor); hızlı iptal kurtarmıyor; geç-favori maker 1.415 pencerede negatif; boy testi yapılamaz; TWAP kilidi gerçek ama kamuya açık. DÜZELTME: 19 günlük zincir defterinde bosona BTC5m maker +1,95 GA[+0,96,+2,95] (2 gün çözemiyordu); geç-favori maker ASLINDA AÇIK: Chainlink kilidiyle tüm maker'lar ≥0,95 son 60 s +0,40 GA dışlıyor, bosona +3,78 — sıradaki test replay+gölge; A ucuz bantta seçime, B ≥0,45'te banda kaybediyor](project_breakthrough_review_20260919.md)
- [🚨 **takerOnly HATASI (09-18)**: data-api /trades VARSAYILANI takerOnly=true → bosona hakkındaki TÜM sayılarımız onun yalnız taker akışından. Aynı 48 pencerede düzeltilmiş: kenarı **+5,06 kr/pay** (taker görünümü +6,33 diyordu, %25 abartı) ama tam akışta GA sıfırı DIŞLIYOR; hacmi 3,4x, eşleşmesi %75,9, **çift maliyeti 0,8699 — bizim A kolundan (0,5745) KÖTÜ**. Yani çift maliyeti kaldıraç DEĞİL. Aynı pencerelerde biz +3,20](project_takeronly_hatasi_20260918.md)
- [🚪 REJİM KAPISI CANLI (09-18 18:13Z): önceki pencere BTC salınımı >=16.4 bps -> A, altı -> B; oynaklık %79 kalıcı (rho +0.72) yani önden bilinebilir, trend/savrulma ekseni DEĞİL (rho −0.07). Yön 3 bağımsız dilimde aynı (A oynak +1.7…+5.6 / sakin −6.1) AMA kapılı karmanın GA'sı sıfırı kapsıyor ve B yarısı ölçü değişince kırılıyor. Tek gün, eşik medyandan, 2×2 tarandı](project_rejim_kapisi_20260918.md)
- [⚖️ ÇİFT EKONOMİSİ A vs B + REDDEDİLEN DÜZELTME (09-18): A çifti **0.584**'e kuruyor (0/22 pencere 1.00 üstü), B **0.968**'e (12/39 = %31 garantili zarar); çift kârı A +21 / B +1.7 kr/pay. "Çift tavanı" düzeltmesi yazıldı ama karşı-olgusal replay ÇÜRÜTTÜ (12 iyileşti 15 kötüleşti, medyan etki 0.00, GA95[−37,+78], kazancın %170'i 3 pencereden) -> canlıya HİÇ girmedi. KURAL: korelasyon + dar GA deploy için yetmez](project_cift_ekonomisi_A_vs_B_20260918.md)
- [📏 ÖLÇEK KANITI (09-18): aynı pencerede çift maliyetimiz bosona'dan İYİ (0.473 vs 0.525) ama **40 pay vs 404 pay** -> kaybettiğimiz strateji değil ÖLÇEK. "Ölçekli ızgara" hipotezim çürüdü (sakin pencerede A DAHA ÇOK doluyor: 0.22 seviyesi %49 vs %33). 0.10/0.06/0.03 seviyeleri 196 konup 2 doldu = dekor. METODOLOJİ: kamu akışı pencereyi parça parça doldurur, erken okuma 2 kez yanlış çıkarım ürettirdi](project_olcek_kaniti_20260918.md)
- [🟢 BOSONA FORWARD v2 CANLI (09-19 01:30 TSİ, capture_v2): `forward_v2/live_v7` = quote_control + favorite_quote + open_favorite + cheap_ladder (bosona 4 saat analizinden); 3 saatlik kesit: quote_control +240 (ex-top3 +117), mid−δ çürüdü, bosona +437 (BTC15 ucuz taraf yığın); ÖRNEK DIŞI backtest 156 pencere: **favorite_quote iki kesitte artıda** (+122, 78/118), cheap_ladder −241 çürüdü, bosona −30; v1-v6 arşiv; WAL/yazma şişmesi dersleri; kullanıcı tam yetki verdi; etiket gecikmesi p99 752 s; DİSK: çift capture ~140 GB/gün ≈ 5 gün](project_bosona_forward_v2_live_20260918.md)
- [❌ GEÇ FAVORİ ALIMI ÇÜRÜDÜ (09-18, 4 ay/33.509 gözlem/7.941 pencere BTC 15dk Telonex defteri): **isabet oranı ask fiyatının AYNISI** (0,9279→%93,2 · 0,9740→%97,6 · 0,9843→%98,6), kenar +0,03 kr/pay, 30 hücrenin hepsinde GA sıfırı kapsıyor, ay ay tutarsız, derinlik sorun değil (medyan 156 pay). bosona'nın 12/12'si ŞANS (0,931²⁵=%16,6). Arşivdeki +9,3 METODOLOJİK HATA: gerçekleşmiş işlem fiyatı ≠ alınabilir ask — o MAKER tarafının kazancıydı, yani bizim derin merdivenimizin KARŞI tarafı. Kopyalama da kapalı: kamu API gecikmesi medyan 298 sn](project_gec_favori_curudu_20260918.md)
- [🔬 **EŞSİZ BACAK = YAPISAL ARTEFAKT (09-18, dış denetim)**: "16/16 kaybetti = −26,7 puan ters seçim" ÇÜRÜDÜ — simetrik merdiven + adil martingalede eşsiz bacak %100 kaybeder ve EV=0 (kendi simülasyonum: 0/3887). Çift maliyeti de tek başına ölçüt değil (lot eşleştirmeye göre 0,50-0,62, PnL sabit). "Denge sınırını kaldır +3,19$" geçersiz (kod hatam: t≥180 kuralı hep açıktı). Kalan GERÇEK fark: eşsiz KAZANAN pay oranı biz %0 (yapısal taban), bosona **%8,64** → onun merdiveni simetrik değil ya da sıçrama lehine. Gerçek kenar ~0,6-1,5 kr/pay, YÜZLERCE pencere gerek. Risk çift sayımı düzeltildi](project_essiz_bacak_yapisal_artefakt_20260918.md)
- [🪜 DERİN MERDİVEN v4 CANLI (09-18): bosona mekanizması uygulandı — MUTLAK fiyat noktaları [0,40..0,03], 5 pay/seviye, pencere boyunca açık. **Çift maliyeti 0,52-0,66 → GİRİŞ FİYATI SORUNU ÇÖZÜLDÜ** (bosona 0,847, v3 0,976). Ama 8 pencerede BAŞABAŞ (+1,19$): kâr çift kurulunca geliyor, tek taraf kalınca kayıp. Tape 145 pencere: çift ancak **%16,6** pencerede kurulabiliyor (model 9x iyimser). 4 kusur canlıda düzeltildi (sabit tik ofseti −12,15$ dersi, kısmi dolumda denge sınırı atlanması, data-api 999, tek yöne sınırsız birikim). Sıradaki: ÇOKLU PAZAR](project_derin_merdiven_v4_20260918.md)
- [🏆 **BOSONA ÇÖZÜLDÜ (09-18)**: kâr YÖN DEĞİL — yön kenarı **−0,7 puan yani SIFIR** (0,3489'dan alıp %34,2 kazanıyor); kârın tamamı ÇİFTTEN (+7,71 kr/pay), tek tarafı zararda. Fark tek sayıda: çifti **$0,847**'ye topluyor, biz **$0,976**'ya → **6,48 kr/pay**. Mekanizma: derin iki-taraflı merdiven + pencere içi savrulmanın İKİ ucunu da yakalamak + son 60 sn'de ölen tarafı 5-14 kuruşa toplamak. Aynı pencerede biz +$0,30, o +$602. Simülasyon 6. kez yanılttı (merdiven testi)](project_bosona_cift_maliyeti_cozuldu_20260918.md)
- [💸 ÖDÜL/REBATE GERÇEKLERİ (09-17, resmi dok + API): BTC 5m'de likidite ödülü **FONLANMIYOR** (clobRewards=null; kontrol: politika pazarı $300/gün dolu geliyor), Ağustos $1M TWAP programı bitti; nitelik eşiği **50 pay** (klibimiz 5) ve 4,5 krş; maker rebate aktif ama tavan **0,35 kr/pay** vs ölçülen −3,24 → 'ölçeği büyüt rebate'ten kazan' planı bu sayılarla çalışmaz; batch emir + fonlu ödül pazarları izi](project_pm_odul_rebate_gercekleri_20260917.md)
- [🅿️ PM BTC5m PARK (09-17, operatör emri): bot kapalı, kayıp −$21,60…](project_pm_btc5m_park_20260917.md)
- [🔴 DIŞ DENETİM 3 HATAMI BULDU, ÜÇÜ DE DOĞRULANDI (09-17): ters seçim −22,59 ÇÜRÜDÜ (post-only red), seviye tablom ters sıralanmış (dokunuş +0,11 / bir tik alt −6,04), çift≠eşleşmiş; 4 kod hatası; NÜANS: red düzeltmesi kârı garanti etmez, t=120 çıkışı kârlı çifti bozardı → v3 muhasebe düzeltmeleri 18/18 test + kuru koşu doğrulandı](project_dis_denetim_v1_duzeltmeleri_20260917.md)
- [🔬 DOLUM KALİTESİ CANLI (09-17, 3 saat, BİTTİ): 108 emir **%95,4 dolum** (sim %10-25 diyordu = TAMAMEN YANLIŞ), 465 pay, **PnL −$15,05 = −3,24 kr/pay** GA[−10,76,+3,76]; yapı base.py ile AYNI → çift +2,76 (18/20 artıda), **tek taraf −22,59** (kazanma %27,3 vs adil %49,9 = TERS SEÇİM DOĞRULANDI); seviye 0 −4,43 / seviye 1 −1,79; 1,5 saatteki "seviye 1 +7,61, ters seçim yok" okumam GÜRÜLTÜYMÜŞ (4. kez küçük örnek dersi); çıkış kuralıyla projeksiyon başabaş…+1,37 kr/pay](project_dolum_kalitesi_canli_20260917.md)
- [🔚 SON TUR (09-17): bosona taker adli — 09-15te +$1.570 taker (BTC %95,6, isabet %64,4, +12,12) ama BTC momentumu açıklamıyor (yön uyumu ~%50) ve TEK GÜN (19 günde +0,64 GA sıfırı kapsıyor); MERDİVEN testi — 222 pay/pencereye kadar çıkıldı, hepsi −6,9…−9,9, genişlik cevap DEĞİL; 15dk pazarları — sinyal SIFIR hata (235-263 pencere) ama piyasa yine 0,99. Geriye tek soru: kuyruk varsayımı doğru mu, ve o yalnız KENDİ canlı dolumlarımızla sınanır](project_son_tur_taker_ve_merdiven_20260917.md)
- [🔑 HAYATTA KALMA YANILGISI — BİLMECE ÇÖZÜLDÜ (09-17): modelin seçtiği hücrelere kuyruk arkasından YENİ emir = **−7,21** (model +2,21 öngörmüştü, 9,4 kuruş fark); ama aynı hücrelerde kalabalık derin kuyrukta bile +0,91. → Kalabalığın +1,72si HAYATTA KALMA YANILGISI: o emirler defterde ZATEN duruyordu. **Kenar hücrede değil, hücrede ÖNCEDEN duruyor olmakta.** 5 yolun 5inin de neden öldüğü tek mekanizmayla açıklandı. bosona 118 gündür kendi emir-düzeyi verisini biriktiriyor, bizde 0 gün](project_hayatta_kalma_yanilgisi_20260917.md)
- [🧱 GÖZLEMLENEBİLİRLİK DUVARI (09-17): ucuz-taraf koşulsuz +1,62 de kuyruktan sağ çıkmadı (dolum %74-85 ama kenar −2,5…−4,2) → **aynı mekanizma 4. kez**: hücre düzeyinde kenar görünüyor, dolum düzeyinde kayboluyor. Aktörlerin neden maruz kalmadığı PRENSİP OLARAK ölçülemez (kamu veride dolmayan/iptal emir yok). Tek açık kapı: ucuz tarafta ASK var mı — hiç bakılmadı](project_maker_gozlemlenebilirlik_duvari_20260917.md) | SON KAPI DA KAPANDI: ucuz tarafta ASK VAR (%100, makas 1 kuruş) ama taker almak −4,04/−4,62 kr/işlem, 1/4 gün → maker kulvarı TAM kapandı (4 maker + 1 taker yolu, beşi de eksi)
- [🗺️ FİYAT×ZAMAN YÜZEYİ (09-17): hücre kalitesi ÖNGÖRÜLEBİLİR — OOS test en iyi %10 **+3,43** (tümü −0,09); ve sinyal tamamen **px × t**te (iki özellik +5,73, 10 özellik +3,58, diğerleri katkısız). Dönem-kararlı harita: geç-favori ailesi (0,55-0,85 @ t≥210, +2,7…+7,7) ve **YENİ: erken-ucuz ailesi** (0,00-0,30 @ t<90, +2,2…+4,4). UYARI: hücre düzeyi, kuyruk/ters seçim YOK — TWAP kulvarı tam burada öldü](project_fiyat_zaman_yuzeyi_20260917.md) | DÜZELTME (fiyat-eşleştirilmiş kontrol): ucuz bantta (px<0,20) model KATKI YAPMIYOR (−0,29), orada kalabalık koşulsuz +1,62 alıyor = basit kalibrasyon sapması, seçim DEĞİL; modelin tüm değeri px 0,50-0,80de (+4,7…+10,0 fark) ki orası TWAP pilotunun ters seçimden öldüğü bölge
- [🔓 HÜCRE SEÇİMİ BULGUSU (09-17, AKTÖRLERİN ASIL İŞİ): kenarın **%82i hücre seçimi** — aktörün dokunduğu (pencere,token,fiyat) hücresinde ALIM YAPAN HERKES **+1,72 kr/pay**, dokunmadığında −0,19 (203M pay). FİYAT KONTROLÜNDEN GEÇTİ (her seviyede fark +0,4…+3,5). Kuyruk sırası ÇÜRÜDÜ (aktörler sıra-1de daha AZ, kenar derin kuyrukta). Eski "dalga seçici −0,50" ölçümüyle çelişiyor çünkü o PENCERE düzeyindeydi, bu FİYAT NOKTASI düzeyinde. Henüz kural değil: dairesel, öngörü modeli gerek. 568.222 hücre / 26.060 pozitif etiket hazır](project_hucre_secimi_bulgusu_20260917.md) | **4 KONTROLDEN DE GEÇTİ** (fiyat, mide uzaklık, kuyruk derinliği, cüzdan kompozisyonu): AYNI 457 cüzdan aktörlü hücrede +1,75 aktörsüzde −0,10, eşleşmiş işaret testi 336/457=%73,5. Mekanizma SAĞLAM; öngörücü özellik bulunamadı (fiyat ve mide-uzaklık ikisi de açıklamıyor)
- [🔐 TWAP KİLİDİ (09-17): settlement penceresi [S+241,S+300] → t=270'te sonuç %100 bilinebiliyor (597/597 ve 581/581, pencerelerin %75'i)…](project_twap_kilidi_20260917.md) | PARK EDİLDİ 09-17: canlı durdu, pozisyon 0; cl_direct_rec kapatıldı, tape.py devam; tetikler: (1) |z|>6 bandında dolum yolu, (2) piyasanın 0,97 altı kotasyon verdiği durum, (3) 15m/4h TWAP pazarları — hiç bakılmadı
- [🔴 TWAP CANLI PİLOT SONUCU (09-17, 8 saat): 76 emir 5 dolum **PnL −$4,25**…](project_twap_canli_pilot_sonuc_20260917.md)
- [🔚 TWAP GERİYE UZATMA KAPANDI (09-17): sinyal t=120den itibaren var (t=220de %1,62 hata) AMA kesin tarafın medyan işlem fiyatı **t=180den beri 0,990** → başabaş %1,0, kenar ancak…](project_twap_geri_uzatma_kapandi_20260917.md)
- [📐 ÖLÇEKLİ EŞİK + FİYAT TAVANI (09-17): z=(P−gerekli)/(σ√(n₂/3)) ile sinyal t=242ye iniyor, hata %0,34 (sabit eşik orada −24,91 veriyordu)…](project_olcekli_esik_ve_fiyat_tavani_20260917.md)
- [🟢 TWAP + MAKER ÖLÇÜLDÜ (09-17): sinyal hatası **%0,33** (3.062 pencere/2 dönem, 10 yanlış), başabaş %2-7 → **6x güvenlik payı**…](project_twap_maker_olcum_20260917.md)
- [🛑 TWAP TAKER TASARIMI YAPISAL OLARAK ÇALIŞMAZ (09-17): kazanan tarafın ASK'ı YOK (PM defteri aynalı, kaybedene bid koyan yok) → taker olarak alınacak şey yok…](project_twap_taker_yapisal_kusur_20260917.md)
- [🚧 KÖPRÜ KAPISI KAPANDI (09-16): kamu `last_trade_price` bir işlemi token başına HER ZAMAN tek toplu fiyattan yayınlıyor (667.032/667.032 = %100) → çok-seviyeli süpürme imzası…](project_kamu_akis_tek_fiyat_20260916.md)
- [🎯 GEÇ-PENCERE TWAP KİLİTLENMESİ (09-17, EN GÜÇLÜ ADAY): zincir defterde t≥260sn & fiyat≥0,65 alım **19/19 gün artıda**, 143k pay, isabet %97, +9,3 kr/pay…](project_gec_pencere_twap_kilitlenme_20260917.md)
- [⛓️ ZİNCİR-KESİN 19 GÜN (09-17): FILL_PARTY_LEDGER ile her iki cüzdan **her iki rolde de artıda, 4/4 GA sıfırı dışlıyor** (mo-money maker +2,26 [+1,55,+3,04] 17/19 gün…](project_zincir_kesin_19gun_rol_20260917.md)
- [🧭 ROL AYRIMI — İKİ CÜZDAN İKİ FARKLI İŞ (09-17): **bosona kârının %90ı TAKER** (+11,06 kr/pay net, kuyruk YOK), **mo-money kârının %98i MAKER** (+2,50)…](project_rol_ayrimi_iki_farkli_is_20260917.md)
- [⚖️ DIŞ DENETİM DÜZELTMESİ (09-17): "%50,2 kazanma oranı = yön kenarı yok" çıkarımım **GERİ ÇEKİLDİ** (pazar-sayısı ≠ pay-ağırlıklı)…](project_denetim_duzeltmesi_kazanma_orani_20260917.md)
- [🔑 BOSONA BAKİYE TESTERESİ + VOL-KOŞULLU TEST (09-16): PUSD bakiyesi hafta boyu birikip HER PAZARTESİ ~26k tabanına süpürülüyor → +22,3k/hafta = **+5,73 kr/pay**, zincir replay…](project_bosona_bakiye_ve_vol_kosullu_20260916.md)
- [🧨 AKTÖR PARADOKSU (09-16): bosona %83,6 / mo-money %73,3 MAKER (ortak zaman penceresiyle ölç, ham toplam yanıltır), ikisi de %50,2 kazanma oranı (80bin pazar = YÖN YOK), ikisinin…](project_aktor_paradoksu_odul_hipotezi_20260916.md)
- [🎯 PEER_FULL_FLOW_V1 + AYNI-EŞLEŞME (09-16): peer cüzdanlar YALNIZ hedefle aynı eşleşmedeyken artıda (+1,26 GA[+0,37,+2,21]), kendi genel akışları −0,05 → "derin likidite sağlamak…](project_ayni_eslesme_ayristirma_20260916.md)

- [🟡 0,98 HÜCRESİ — İKİ SORU KAPANDI, ÜÇÜNCÜSÜ AÇILDI (09-16): PM defteri ZATEN AYNALI (Up bid@p ≡ Down ask@1−p birebir, 630/630) → tamamlayıcı likiditeyi ayrıca EKLEME…](project_098_hucresi_dogrulama_20260916.md)
- [📉 DELTA TARAMASI — base.py KOTASYON POLİTİKASI TÜKENDİ (09-16): 6 DELTA × 2 çıkış × 24 saat = hepsi EKSİ (−6,02…−8,48 kr/pay, GA sıfırı dışlıyor, 0/4 gün, **0/24 saat**)…](project_delta_tarama_kapanis_20260916.md)
- [🔬 UYGUNLUK TESTİ (09-16): canlı 48 emir kayıtlı defterde yeniden oynatıldı — dolum modeli İYİMSER DEĞİL KÖTÜMSER (motor 33/48, gerçek 38/48…](project_uygunluk_dolum_modeli_20260916.md)
- [🎯 BOSONA GEÇ-FAVORİ → HÜCRE ÖLÜ (09-16): dürüst kuyruk motoru 2.026 pencere/5 coin, R2=%0 (sahte kuyruk YOK) → 0,70-0,90 geç favori **−14,61 kr/pay**…](project_bosona_gec_favori_20260916.md)
- [🕰️ PENCERE-ÖNCESİ ÇİFT MAKER'I (09-16, YENİ): ters seçim bilgi ister, pencere açılmadan bilgi yok — artan envanter %49,9 kazanıyor (pencere içi %37,8)…](project_prewindow_pair_maker_20260916.md)
- [🧲 KUYRUK POZİSYONU = ASIL DEĞİŞKEN (09-15 gece): maker ilk-alım sıranın SONUNDA −5,72 kr/pay GA[−7,90,−3,14], sıranın BAŞINDA **+3,09 GA[+1,16,+5,14]** → kuyruk ~8,8 kr/pay…](project_maker_ilk_alim_ters_secim_20260915.md)
- [🅿️ AKTÖR-KOPYA KULVARI PARK (09-15 03:00): araştırma takibi — H1 ampirik ölü, RTDS kimlik 2,8-3,2 sn geç, hız=enabler, çok-borsa+Kalshi modeli aktör AUC 0,46, taklit AUC 0,84 ama…](project_research_followup_20260915.md)
- [⚖️ CODEX "ARTIR KURALI" — AÇIK, ÇÖZÜLMEDİ (09-15): saf imitatör biriktirmeli −2,50 kr/pay GA[−3,13,−1,85] ZAYIF…](project_codex_artir_kurali_cozumleme_20260915.md)
- [🔒 PM BTC5m MAKER KULVARI KAPANDI (09-15): 40 günde −5,26 kr/pay [−6,12,−4,39], 40 günün 1'i artıda…](project_btc5m_maker_kapanis_20260915.md)
- [⚖️ BULGU RAPORU DENETİMİ (09-14 gece): kardeş oturumun 'bayat iptal +2,80/+3,14 ilk tekrarlanan bulgu' iddiası — teşhis doğru (whiskas maker modeli), boy çürüdü: aynı-süpürme saat…](project_bulgu_raporu_refute_20260914.md)
- [🔑 POLYMARKET HESAP KİMLİK HARİTASI (09-14): nuxxor=0xfCdC/.env.live, nuxxor2=0x7d9f/.env.live2, nuxxor4=0x899d92/poly-lpbot/ops/accounts/taygun.env…](project_polymarket_account_identity_map_20260914.md)
- [🧠 DALGA SEÇİCİ KULVARI (09-14 akşam, onaylı): aktör elemesini kamu-veriyle ML olarak kurma…](project_wave_selector_lane_20260914.md)
- [🧩 AKTÖR BREAKTHROUGH TURU (09-14, Fable): kâr çift marjı DEĞİL tek taraflı yön envanteri (%75-95, +4,7¢ @0,544 %59)…](project_actor_breakthrough_tour_20260914.md)
- [🎯 PM GEÇ-PENCERE TASFİYE (09-14): kenar zamanda — son 35 sn favori 0,75-0,90 maker alım +9,58 kr/pay (17 gün, iki yarı ayrı geçti)…](project_pm_late_window_liquidation_20260914.md)
- [🧭 KUYRUK YAŞI/ÖLÇEK/YERLEŞİM ZAMANI (09-14): '18¢ fark' kalibrasyon artefaktı (aktör 28g +1,9¢, biz touch −2,5¢)…](project_queue_age_scale_20260914.md)
- [🔓 CHAINLINK STREAMS AÇILDI (09-13): $150'lık abonelik çalışıyor — hata kimlik değil, Cloudflare UA + Authorization=STREAMS_USERNAME (API_KEY değil)…](project_chainlink_streams_unlocked_20260913.md)
- [❌ UYUŞMAZLIK HİPOTEZİ ÇÜRÜDÜ (09-13): 'aktörler gizli kaynak okuyor' 3/3 kontrolde kaldı — mekanik taban +0,94¢ (tüm makerlar), 'uyuşmazlık'=kıl payı pencere kılığı, kenar…](project_disagreement_falsification_20260913.md)
- [🌗 PM BTC15m MOMENTUM GÖLGESİ (09-13 00:42Z, YEREL/Türkiye): para ve anahtar yok, 3 eşik × 2 klip, 2 hafta ölçüm…](project_pm_btc15m_momentum_shadow_20260913.md)
- [🔚 PM BTC15m STRATEJİ ARAMASI (09-13): 9.785 pencere/7 aile/50 parametre ön-kayıtlı → ADAY YOK…](project_pm_btc15m_strategy_search_20260913.md)
- [⚖️ BTC15 KARAR (09-13): sızıntı 0,70-0,80 bandı…](project_btc15_verdict_20260913.md)
- [⏹️ BTC15 + TÜM TOKYO DURDURULDU (09-12 23:23-23:55Z…](project_btc15_edge_decay_stop_20260912.md)
- [🚀 BTC15 V15 STREAK GATE CANLI (09-11 17:49Z): önceki seçimli pencere kayıpsa atla (fail-closed, skip-only)…](project_btc15_v15_streak_gate_20260911.md)
- [🎯 BTC15 STREAK BULGUSU (09-11): kayıp serileri rastgele DEĞİL (gün-içi p=0,0003)…](project_btc15_streak_research_20260911.md)
- [⏹️▶️ OPS 09-11: 5m CONTROL KAPALI (taban −40 dolu)…](project_ops_shutdown_20260911.md)
- [🧪 SPOT vs FUTURES TETİK (09-11): yerel kayıt 22:50Z, 3 saatlik RESULT_3H.txt bekleniyor…](project_spot_vs_futures_trigger_20260911.md)
- [🧊 CONTROL Q60 SOĞUK PAKET V7 (09-11): 30→60 pay/$60 aktif/−120 taban…](project_control_q60_cold_package_20260911.md)
- [🟢 BTC15 V14 CANLI (09-11 00:48Z kabul: risk_snapshot 800→111 ms, POST +0,9→+0,19 s…](project_btc15_admission_fix_20260911.md)
- [🔎 TOKYO CANLI İNCELEME (09-10 18:00Z): CONTROL 5m hızlı DEĞİL — tick→socket 165 ms (reserve 90 +…](project_tokyo_live_review_20260910.md)
- [🟢 GTC-REST CANLI KANARYA (09-10 Londra): taze-tick sonrası ask fiyatına post-only bid, 5 pay, $50…](project_gtcrest_live_canary_20260910.md)
- [🔬 LONDRA ms ÇÜRÜTME TURU (09-10 gece): Eylül kuyruk-gerçek replay 27/27 NEGATİF (−4,7…−11,7¢),…](project_operator_a_london_ms_20260910.md)
- [⛔ OPERATÖR A MAKER KURALI GERİ ÇEKİLDİ (09-10 akşam): üç saat sızıntısı (G[floor(t)] ileri bakış /…](project_operator_a_maker_policy_20260910.md)
- [🟢 BTC-15m SON-2-DK TAKER (09-11, Fable Ek 16): adil−ask ≥5¢ taker alımları diğer taker'lar için OOS…](project_operator_a_maker_policy_fable_20260910.md)
- [🟢 ALT-PİYASA ADİL-DEĞER MAKER (09-11): ETH/SOL/XRP/DOGE 5m/15m'de t≥0,6·T & Φ-adil−bid ≥5¢ hücresi…](project_operator_a_maker_policy_fable_20260910.md)
- [🅿️ OPERATÖR A MAKER POLİTİKASI PARK (09-10/11, Fable): TANIMLANMIŞ, KOPYALANAMAZ — yerleşim…](project_operator_a_maker_policy_fable_20260910.md)
- [WHISKAS REBATE (09-10): 24h taker $4549+maker $534 kamu API doğrulandı; rebate hariç −$921 cüzdan…](project_whiskas_rebate_reconciliation_20260910.md)
- [WHISKAS GECİKME (09-10):42emir/8exactdolum−$6.95;prep5.3ms/SDK214.5ms,ACK≠match.4Eyl14UTC…](project_whiskas_latency_root_cause_20260910.md)
- [WHISKAS DEVAM (09-10): OKX/15m/saatlik sabit kurallar FAIL; düzeltilmiş tick kaynak100+emir30ms…](project_whiskas_temporal_crossmarket_20260910.md)
- [WHISKAS FABLE önceki tur (09-10): özgün+$3475tickmodeli bağımsız doğrulandı; eski “kesin actor…](project_whiskas_selection_fable_20260910.md)
- [🧪 PREDICT FRESH-TICK V2 CHECK(09-09 19:21UTC):Tokyo sağlıklı,restart/OOM0;212replayPASS;130ms…](project_predict_btc5m_fresh_tick_check_20260909T1918Z_v1.md)

- [🧷 PREDICT FRESH-TICK KALICI BAĞLANTI (09-09):initial5pay/nonce/deadline+cache gerçek SQLite lane'e…](project_predict_btc5m_fresh_tick_durable_handoff_20260909_v1.md)

- [🧪 PREDICT FRESH-TICK COLD ENTEGRASYON (09-09):292test+13compile PASS; hata/restart/PnL/exposure…](project_predict_btc5m_fresh_tick_cold_integration_20260909_v1.md)

- [🧪 PREDICT FRESH-TICK DEVAM (09-09): V2 61/61 replay/7market; ana filtre0 seçim, edgeWAIT. BTC15…](project_predict_btc5m_fresh_tick_followthrough_20260909_v1.md)

- [🧪 PREDICT SELECTIVE V2 (09-09): Tokyo19:20TSİ no-order;3/5bp+repricing…](project_predict_btc5m_fresh_tick_selective_20260909_v2.md)

- [🧪 PREDICT BTC5m FRESH-TICK RACE (09-09): yeni Tokyo no-order observer15:06UTC…](project_predict_btc5m_fresh_tick_race_20260909.md)

- [🛑 BTC5m BAĞIMSIZ TUR KAPANDI (09-08→09-11, Fable, operatör emriyle 09-11 11:52Z): venue taker gecikmesi 150 ms (4 Eyl) T7b/taker yolunu kapattı…](project_btc5m_independent_research_20260908.md)
- [🏆 BTC5m TOP-ACTOR HUNT (09-02, Telonex Pro tam venue): 43k cüzdan exact ledger (Densa ile kuruşu…](project_btc5m_top_actor_hunt_20260902.md)
- [🧷 LIVE-CODE ADVERSARIAL AUDIT (09-02): P0 yok; guard-source bellek boğulması (P1, operatör…](project_predict_live_code_adversarial_audit_20260902.md)
- [🧪 BTC5m TWAP60 GEÇ-FAVORİ (09-02, önkayıtlı tek bakış): UNDERPOWERED (+$29/63 fill); asıl bulgu =…](project_btc5m_twap60_late_favorite_20260902.md)
- [🏙️ LONDRA V100E CANLI DEĞERLENDİRME (09-02, SSM ile doğrulandı) + KAYIP MEKANİZMASI (09-02 öğle):…](project_london_v100e_live_assessment_20260902.md)
- [🅿️ QWEN-27B PREDICT BTC5m TAHMİN DENEYİ PARK (08-29): LLM piyasayı yener (%94 gün) ama incumbent…](project_predict_btc5m_qwen27b_shadow_20260828.md)
- [🌡️ WEATHER DEADRUNG PROBE (08-29, ninedol tweet tetikli): gün-içi ölü-rung bayatlığı ÖLÇÜLDÜ —…](project_weather_deadrung_probe_20260829.md)
- [🧭 VENUE KEŞFİ→KALSHI KILL (08-29): iki yönlü maker cf de negatif (8/8 ve 6/6 hücre, in-play akış…](project_venue_discovery_20260828.md)
- [🔬 NATIVE NO-FILL EXEC AUDIT (08-28): client bug YOK (32/32 wire temiz); ~84% yapısal (venue…](project_predict_native_nofill_execution_audit_20260828.md)

- [🌉 PM↔PREDICT CROSS-VENUE ARB TAM ÇALIŞMA (08-28): parite %99.86 (kripto-dışı ayrışma ≈0); latency…](project_pm_predict_crossvenue_arb_20260828.md)

- [🔎 ÇİFT-VENUE DERİN DENETİM (08-27): PM S30 owner-override canlı, kampanya +$32.72 exact; Predict pmlead…](project_btc5m_dual_venue_deep_audit_20260827.md)

- [🩻 SHADOW REDTEAM + SAATLİK ADAY (08-18): eski XGB shadow zombi (0/16 skor); TWAP shadow temiz; YENİ…](project_crypto_shadow_redteam_20260818.md)
- [🅿️ JET/FLICKER SAGASI TAM PARK (08-19 akşam, kullanıcı emri): 6 falsifier hepsi KILL, gerçek para…](project_e022_forensic_audit_20260818.md)

- [🧪 EXP260 (08-05): son ham aile (spot/fut depth) KILL — kayıtlı public feature uzayı count sorusu…](project_exp260_phase0_depth_episode_count_20260805.md)
- [🔎 TRUTH AUDIT (08-05): likidite BINDING DEĞİL; gözlemlenebilirlik %90-100; Jet→B kimlik bağlama…](project_observability_truth_audit_20260805.md)
- [🔍 EXP249 AUDIT (08-04): 247-episode-budget exec CLEAN bit-exact; causal claim…](project_exp249_independent_episode_budget_audit_20260804.md)

- [📍 EXP248 PLACEMENT (08-04): KILL/COUNT_LIMITED — gerçek bütçeyle first-K ≈ oracle (headroom ≤%0.9)](project_exp248_placement_falsification_20260804.md)

- [🎛️ EXP247 ORDINAL-BUDGET (08-04): arm DEAD](project_exp247_joint_ordinal_budget_20260804.md)

- [🧪 EXP242 HEDGE GATE (08-04, owner): bounded KILL; C242_A4 merge/successor YASAK](project_exp242_causal_conviction_gate_20260804.md)

- [🎯 EXP241 ORACLE CAPACITY (08-04): PASS — ROBUST_MIN +$414.10 EXACT](project_exp241_hedge_oracle_capacity_20260804.md)

- [💰 REBATE v2 + P0 (08-04): anchor +$6,672.26 (682/2007 chain-exact, %31.938); eski 6715.01/32.03% anma](project_rebate_accounting_layer_20260804.md)
- [🧷 EXP236 KAPALI (08-04, owner): exec ACCEPT / B-relative SECONDARY / absolute FAIL / promotion HOLD](project_exp236_sealed_transport_hedge_falsification_20260804.md)

- [🔬 LPBOT TWO-AGENT AUDIT (08-01): count-latch FALSIFIED; kill-switch İNERT; CONDITIONAL GO $20 canary](project_lpbot_two_agent_breakthrough_audit_20260801.md)
- [🧊 CONTROLLER SCAFFOLD KABUL (08-01): TWAP sidecar + inventory-controller shadow frozen](project_controller_scaffold_build_20260801.md)
- [⚖️ BAĞIMSIZ DENETİM (08-01): kanonik sayılar reprodüse; TWAP rejim kırılması 08-04 kritik](project_independent_strategic_audit_20260801.md)
- [🧨 R25 CONFORMANCE (07-30): gate = regime lottery; stale = sign bug; karar R26-C redesign](project_r25_conformance_review_20260730.md)
- [🔎 EXP156 REVIEW (07-29): dense kontroller depth test edemez; dedektör onaylı; EXP156-A placement…](project_exp156_external_review_20260729.md)
- [🔴 CANDIDATE D REJECTED (07-28): prereg KILL — seviye doğru, yerleşim yanlış; dedektör bileşen olarak sakla](project_fable_candidate_d_20260728.md)
- [🧱 FABLE SLOW-DEPTH (07-27): slow state public'te YOK; aday collapse-detector fallback; OPS:…](project_fable_slow_depth_lane_20260727.md)
- [🔎 FABLE DEVAM (07-27): 18/19 onset gerçek; çöküş upstream ordinal-count modelinde; Jet 30-share…](project_fable_continuation_audit_20260727.md)
- [⛔ JET COUNT-OBSERVABILITY (07-26): Exp120 count sonucu aritmetik artefakt; count public'te doymuş](project_jet_count_observability_20260726.md)
- [🧾 SOL-PRO DENETİM (07-25): KARAR=SHADOW ONLY; taker FAK ölçülmüş negatif](project_c3_sol_pro_audit_20260725.md)
- [🔑 MAKER SEAT (07-25): C3 taker lane yapısal ölü; makers zero fee; tek gerçek gelir lpbot $17.50/gün](project_maker_seat_finding_20260725.md)
- [📐 JET REPLICA CEILING (07-25): F1 tavanı = count MAE formülü; 2.36→≤1.61 gerekli; timing değil…](project_jet_replica_count_ceiling_20260725.md)
- [🎯 C3 ANA DOSYA (07-20..22): raw@trade canlı; fair-value P=Φ(dist/σ√τ) ilk OOS hayatta-kalan koşullama](project_raw_trade_feed_lever_20260720.md)
- [🔎 C3 FRESH-AUDIT (07-21): limitleri KORU; 0 kritik bug; canlı 24h +$10.77 ama CI sıfırı içeriyor](project_c3_fresh_audit_20260721.md)
- [🏁 JET-MODEL NİHAİ KILL (07-21, 3 reviewer): ramp −$35.5k; gölge = Jet-rejim monitörü](project_jet_model_shadow_20260720.md)
- [🪦 TAKER-SHADOW KULVARI KULLANICI EMRİYLE ÖLÜ (07-30): v3+v4+tüm dosyalarım emirle silindi](project_taker_shadow_v2_invalid_20260719.md)
- [⚡ C3 LATENCY ROOT-CAUSE + FIX (07-19): sorun order-path; asyncio.to_thread GIL açlığı; fast_exec.py](project_c3_latency_fix_20260719.md)
- [🟢 C3 POLY_1271 FIX + DUBLIN DEPLOY (07-19): deposit-wallet imza fix zincirde MATCHED; hız = edge kanıtı](project_c3_first_live_attempt_20260718.md)
- [🔍 JET-GATE DOĞRULAMA (07-19): in-sample gerçek ama jet-gate F1'i DÜŞÜRÜR; copytrader DB 0-bayt = OOS blokeri](project_jetgate_verify_20260719.md)
- [🎯 CAPTURE-FIRST C3 (07-19): 4 kusur düzeltildikten sonra da ayakta; motor hash-donuk](project_capture_first_replica_20260718.md)
- [🧭 90-GÜN STRATEJİ (07-18): C3 %45 + lpbot %30 + boundary %15; recorder ~07-28'de ölüyor → uzatma şart](project_strategy_direction_20260719.md)
- [🚀 C3 LIVE RUNNER HAZIR (07-18): dry-run+shadow geçti; canlı = operatörün 3 adımı](project_c3_live_runner_20260718.md)
- [⚖️ PUBLIC UP/DOWN ADJUDICATION (07-16): verdikt BOUNDARY-TAKER-01; fee v2 = 0.07·p·(1−p), min DEĞİL](project_public_updown_adjudication_20260716.md)
- [🔬 JET SEAT+NET+REBATE (07-14..17): TRUE medyan +$998 zincir-kesin; %61 çıta Platinum'a ait](project_jet_seat_study_20260714.md)
- [🕐 HOUR-SCHEDULE (07-09): ince saat = gürültü; hafta-içi 12-21 UTC stabil zehir zonu](project_hour_schedule_study_20260709.md)
- [🎯 Event-edge programı AKTİF (06-10): Phase 0 cheap-YES cebi negatif; forward shadow sırada](project_event_edge_phase01.md)
- [📦 Telonex ham arşivi (417GB) Drive'da (07-19); lokalde manifest+türevler](reference_telonex_archive_20260719.md)
- **📘 HANDOFF (07-05, repo kökü):** `CRYPTO_BINARY_MM_HANDOFF.md` + `RESEARCH_DISCIPLINE_PLAYBOOK.md` (30 kural, kapalı-mezarlık + reopen tetikleri). Yeni bilgi çıktıkça İKİSİNİ DE güncelle.

## Kapanmış / park edilmiş kulvarlar (özet)

- [🔒 20d230 KESİN PARK ~%95 (07-10): 27-ajan denetim 7/7 kill; Codex clean-rebuild dahil](project_20d230_final_audit_exit_close_20260710.md)
- [🟡 Spor pre-match LP parkta; reopen tetikleri Eyl-Eki](project_sports_prematch_lane_20260707.md)
- [🔒 News-sniping ailesi KESİN KAPALI (07-05, kullanıcı kararı): bir daha ÖNERME](project_news_sniping_retro_pending.md)
- [⚠️ Event-edge misc cheap-YES: kapasite çıkmazı; V2 gate ~08-20](project_event_edge_misc_survivor.md)
- Diğer kapalı kulvarlar (parity-arb, weather, delta-hedge MM, rule-scanner, informed-flow, paper-shadow, saturday-YES, range-edge ×3, bias-leverage, HL-maker, xsec-faktör, pivot-landscape, taker-shadow): [archive-20260726](project_index_archive_20260726.md)

## Ops durumu

- [🔧 LPBOT restart'sız deploy (07-18): rowcount-dedup fix + Stage C tier sözleşmesi](project_lpbot_no_restart_deploy_20260718.md)
- [🟢 LPBOT canlı + DRILL-1 tam başarı (07-11/12): rotation parkta; HER restart öncesi tam F26 reçetesi](project_lpbot_maine_deploy_review_20260711.md)
- [🔍 LPBOT audit v2 triage (07-10): 25/30 verified; ALP öncesi F29 zorunlu](project_lpbot_audit_v2_triage_20260710.md)
- [🚨 LPBOT pair-completion PROD-GÜVENSİZ (07-09): F2/F3/F4 kritik doğrulandı; adım 0 kullanıcı onayı bekliyor](project_lpbot_audit_triage_20260709.md)
- [🟢 LPBOT Round-5 iki-taraf pilot #7 canlı (07-06): tahminci 5-60× şişkindi, gerçek ≈$7-14/gün](project_lpbot_round5_research_20260706.md)
- [LP-bot fix turu 2 (07-04): 16 fix / 1874 test yeşil; colocation gereksiz](project_lpbot_fix_round2_20260704.md)
- [poly-lpbot derin denetim (06-10): botun tek karnesi kendi logları; cüzdan-lifetime PnL'i bota karne YAPMA](project_lpbot_deep_dive_20260610.md)
- [poly-lpbot fix turu 1 (06-10) tamamlandı: kaçış flag'leri + manuel ekleme güvenlik kapısı](project_lpbot_fix_round1_20260610.md)
- [🏁 5DK MAKER KULVARI PARK (07-14): yetim %25, hedge replay −$0.21; reopen = rebate artışı/ürün değişimi](project_updown_handover_audit_20260710.md)
- [🟡 Spor fresh-spec grace kodu lokalde hazır, deploy bekliyor (07-09)](project_sports_fresh_spec_grace_20260709.md)
- [🔧 Shadow ops devralındı (07-08): GERI crash-loop fixli; saturday daemon kırık](project_shadow_ops_takeover_20260708.md)
- [Ops denetimi (06-10): collector kapalı, range verisi kayıp riski, updown_ti_v2 Mart sonuçları gerçek para DEĞİL](project_ops_status_20260610.md)

## BTC5m kendi-sistem araştırması — KAPALI 2026-06-09 (deploy edilebilir edge yok)

- 14 alt-dosya (calibration/fade/E08/first-principles/direction-v2/maker-proxy/follower vb.) hepsi KILL — detay: [archive-20260726](project_index_archive_20260726.md); tek şart: 06-09 burned-window merceği.

## JetFadil replica (eski, 06-06 kapandı; 07-07 rebate düzeltmesi)

- [🚨 Jet'in gizli geliri = MAKER REBATES (07-07): Nisan $337.6k dağıtıcı](project_jetfadil_rebate_channel_20260707.md)
- Diğer 15 eski replica dosyası (breakeven, MM-compete, fair-gap, queue-rent, pasta, ladder, iki-taraflı-hold vb.): [archive-20260726](project_index_archive_20260726.md)

## Proje yapısı

- Ana canlı runner: `scripts/run_live_updown_ti.py`; supervisor `scripts/live_updown_ti_supervisor.sh`; monitor `scripts/performance_monitor.py`
- Config `.env.live`; collector `scripts/collect.py`; state `data/live/updown_ti_v2/` (aktif), `data/live/_archive/`
- BTC Up/Down 5m mikro-marketler, mom_fast/mom_strict, FAK execution, risk cap'leri (detay arşivde)

## Kullanıcı direktifleri ve feedback

- [🚩🚩🚩 SİMÜLASYON YANILTTI — CANLI ŞART (09-17): sim-canlı ayrışması aynı gün 4 ölçümde İKİ YÖNDE de büyük (dolum %17,6→%6,6; çift %83,6→%53; 33/48→39/48; merdiven −7→erken artı, dolum %100). Hata 5-10 kuruş, kovaladığımız kenar 1-3 kuruş → **simülasyon karar verdirecek hassasiyette DEĞİL**. Kural: hiçbir kulvar yalnız simülasyonla ÖLDÜRÜLMEZ, hiçbir kural yalnız simülasyonla CANLIYA ALINMAZ/BÜYÜTÜLMEZ](feedback_simulasyon_yaniltti_canli_sart_20260917.md)

- [🚨 GPU DONANIM DİSİPLİNİ (08-29): 11 saatlik kesintisiz yerel LLM yükü sistemi izsiz dondurdu (beyaz…](feedback_gpu_hardware_discipline_20260829.md)
- [🚩🚩🚩 CANLI-İŞLEM PROTOKOLÜ (08-19, −$50.63 dersi): PnL devre-kesicisiz canlı bot ASLA; izle=kesintisiz…](feedback_live_trading_discipline_20260819.md)

- [🚩🚩 FABLE-ONLY, SUBAGENT YOK (08-01): platform tüm subagent'ları Sonnet'e düşürüyor — ağır işi ana…](feedback_fable_only_no_subagents_20260801.md)
- [🚩🚩 ENGLISH ONLY (07-29): user directive — all replies in English; 08-18 GÜNCELLEME: kullanıcı…](feedback_english_only_20260729.md)
- [🚩🚩 VERIFY AGENT OUTPUT YOURSELF (07-29): subagent reports are leads, not evidence —…](feedback_verify_agent_output_20260729.md)
- [🚩🚩 MORAL DİSİPLİNİ (07-28, CLAUDE.md §8): mesaja ASLA "imkansız/%X şans" ile başlama](feedback_moral_disiplini_20260728.md)
- [🚩 "Kapatıyoruz/pes" dili YASAK (07-18): kulvar öldürme = park + tetik + yeni saldırı yönü formatında](user_no_quit_directive_20260718.md)
- [Kısa anlat: final mesaj 5-10 satır, teknik olmayan dil, detay memory'de kalsın](feedback_kisa_anlat.md)
- [LP bakiye/genişlik tuzağı: resting emir para harcamaz, market sayısını bakiyeye bölerek SINIRLAMA](feedback_lp_balance_breadth_trap.md)
- [Scope disiplini: adlandırılmış botu iyileştir, yan-bulgu otomatik iş değil](feedback_scope_discipline_20260610.md)
- [Ağır analizde RAM disiplini: ağır DuckDB ajanlarını serileştir, paralel fan-out OOM yapıyor](feedback_ram_discipline_heavy_analysis.md)
- [NO emotional swinging: 2-3h penceresiyle umut↔vazgeçme salınımı yok, sadece büyük-n drift](feedback_no_emotional_swinging.md)
- [Polymarket read-only guardrails: DB salt-okunur; live/collector/systemd dosyalarına dokunma](feedback_polymarket_readonly_guardrails.md)
- [🚩 pgrep/pkill -f SELF-MATCH — 4. kez kabuk öldü; tek güvenli reçete: pkill -f yasak, pgrep ile listele, $$/$PPID dışla, /proc/PID/cmdline doğrula, PID ile kill](feedback_pgrep_self_match_recipe.md)
- [Dublin VPS recorder ops tuzakları: canlı DB'ye ağır sorgu yok; pgrep -f self-match → PID ile öldür](feedback_dublin_recorder_ops.md)
- [Claude.ai Research Mode: "+" menüsünden aktif edilir](feedback_claude_ai_research.md)
- [ChatGPT Deep Research: sol sidebar, "Başla" ile onay](feedback_chatgpt_research.md)
