# BTC5dk dışı bağımsız muhasebe ve gözlem birimi denetimi

Bu alt çalışma kaynakları salt okunur kullanır. 13 Eylül 00:00–21 Eylül 12:00 UTC tarihsel kohort ve S kesiti ayrı hesaplandı. Başka inceleyici sonucu kullanılmadı. Decimal ödeme/maliyet ve FIFO sıfırdan hesaplandı; resmî sınıf/sonuç için yalnız donmuş saf yardımcı kullanıldı. Ana soru tek toplamın doğruluğu değil, dolumların doğru ekonomik parçaya ve piyasa kimliğine atanmasıdır.

## Hüküm

- **DOĞRULANDI:** 3.503 piyasa, 14.014 BUY, 29 grup; resmî sonuç ödemesi eksi API nakit maliyeti **+13.393,820008 USD**. Her dolumun FIFO neti, tamamlanan/açılan miktarı ve çift katkısı yayımlanan kaynakla 1e-5 içinde eşleşti. Rakam gerçek cüzdanın bütün dönem servet değişimi veya rebate/sabit gider dahil net gelir değildir.
- **DOĞRULANDI — yeni veri hatası:** `activity_key` conditionId içermediği için farklı piyasalardaki MERGE/REDEEM aynı anahtara düşüyor. 213 çakışan anahtar; eski taze düzeltmelerden sonra kohortta **10 gerçek MERGE / 575 USD** hâlâ eksik. Onunun tamamı yeni kamu cevabıyla doğrulandı. 143 sıfır tutarlı REDEEM de geri geldi. BUY/PnL değişmiyor; cash/inventory geçmişi eksikti.
- **DOĞRULANDI — gözlem birimi hatası:** ilk saniyedeki 558 satır/365 piyasa ekleme diye yazılmış; BTC15dk altkümesi 151/100. Geç BTC15dk kümesine giren 23 satır/12 piyasa ilk alışın parçaları. Düzeltme 1.173→1.150 dolum, 277→274 piyasa, +3.389,908592→**+3.364,652672 USD**; piyasa toplamı değişmez.
- **DOĞRULANDI — model girdisi hatası:** gerçekleşmiş MERGE düşülmediğinden H2 mevcut denge ölçüsü kümülatif alış oranı. Risk setinde **788/3.524 durum, 123 piyasa** etkileniyor; doğru imbalance artışı medyan **0,637006**, en çok **0,9999997**. Net yön, ödeme vektörü ve piyasa riski bu hatadan değişmez.
- **KARŞI KANIT:** yeni S döneminde 14 tam/12 işlemli piyasada 126 dolum **+165,630507**, 8 piyasanın 54 geç eklemesi **−254,167917 USD**. İlk-saniye hatası bu 54 içinde yok. Tarihsel pozitif faz atfı bağımsız alım sinyali değildir.

## Veri ve kapsam

61 tamamlanmış ham activity diliminin (57 ilk dilim +4 taze dönem kontrolü) kaynakla aynı anahtarlı maksimum çokluk birleştirmesi 65.511 satırı birebir üretti (eklenen/çıkan 0). Analiz daha sonra **conditionId içeren düzeltilmiş anahtarla** yeniden birleştirdi, 158 taze piyasa cevabını öncelikli uyguladı. Böylece asıl PnL doğrulaması kaynak hatasını tekrar etmekle sınırlı kalmadı. Son kohort 14.014 BUY, 970 MERGE, 5.067 REDEEM içeriyor. SELL/SPLIT/CONVERSION yok; kod SELL görünce açık hata verir, sessiz düşürmez.

9.110 resmî kapanmış kohort sözleşmesi = 3.503 işlemli + 5.607 gözlenen işlemsiz. Ana sekiz grubun 7.956 planlı sözleşmesi tam; kalan 21 grubun yalnız işlemli evreni kapsanıyor. Bu gruplarda işlemsiz sayısı **bilinmiyor**, sıfır değildir. İncelenen kohortta metadata eksiği/çözülmemiş sonuç 0; 1.423 daha eski/yeni veya bitişi kesiti aşan piyasa açıkça kohort dışı. Kesit sonrasına uzanan günlükler çözülmemiş kohort sıfırı diye sayılmadı.

| Grup | İşlemli | İşlemsiz | Dolum | PnL $ | İlk saniye yaşı/pay medyanı | İki taraf % | En iyi3 hariç $ |
|---|---:|---:|---:|---:|---:|---:|---:|
| bnb_15m | 11 | bilinmiyor | 28 | 66.79 | 797.00/42.00 | 27.3 | -35.94 |
| bnb_1d | 5 | bilinmiyor | 19 | 19.92 | 45,733.00/4.35 | 20.0 | -1.51 |
| bnb_1h | 153 | bilinmiyor | 1026 | 623.48 | 1,177.00/10.00 | 60.8 | 479.76 |
| bnb_4h | 24 | bilinmiyor | 67 | 50.56 | 8,067.50/20.00 | 70.8 | 8.78 |
| bnb_5m | 88 | bilinmiyor | 131 | 45.65 | 162.50/10.00 | 19.3 | 22.25 |
| btc_15m | 598 | 218 | 5441 | 4,428.55 | 151.00/49.80 | 71.2 | 3,025.27 |
| btc_1d | 7 | bilinmiyor | 63 | -68.20 | 11,080.00/40.00 | 57.1 | -299.69 |
| btc_1h | 193 | 11 | 1494 | 3,351.10 | 174.00/49.78 | 71.0 | 2,095.78 |
| btc_4h | 33 | bilinmiyor | 183 | 453.32 | 3,588.00/50.00 | 66.7 | -5.64 |
| doge_15m | 100 | bilinmiyor | 161 | 304.54 | 318.00/19.77 | 13.0 | 219.88 |
| doge_1d | 6 | bilinmiyor | 21 | -3.54 | 66,144.00/39.46 | 33.3 | -17.45 |
| doge_1h | 27 | bilinmiyor | 32 | 51.75 | 798.00/4.55 | 11.1 | 24.45 |
| doge_4h | 21 | bilinmiyor | 38 | 78.11 | 1,477.00/16.06 | 28.6 | 31.83 |
| doge_5m | 219 | bilinmiyor | 276 | 526.07 | 160.00/17.14 | 11.0 | 467.23 |
| eth_15m | 131 | 685 | 210 | 85.69 | 202.00/19.61 | 9.9 | 11.10 |
| eth_1d | 7 | bilinmiyor | 242 | -33.63 | 9,436.00/17.49 | 100.0 | -140.88 |
| eth_1h | 136 | 68 | 700 | -155.38 | 657.00/22.94 | 75.7 | -328.96 |
| eth_4h | 31 | bilinmiyor | 160 | -127.40 | 5,142.00/34.62 | 67.7 | -252.14 |
| eth_5m | 643 | 1805 | 1673 | 1,529.10 | 119.00/23.61 | 17.7 | 693.86 |
| sol_15m | 154 | 662 | 370 | 167.97 | 204.00/30.00 | 39.6 | 108.73 |
| sol_1d | 7 | bilinmiyor | 101 | -104.38 | 7,651.00/8.65 | 85.7 | -165.73 |
| sol_1h | 81 | 123 | 213 | 239.69 | 747.00/17.86 | 37.0 | 132.29 |
| sol_4h | 18 | bilinmiyor | 48 | -45.31 | 9,341.00/13.68 | 55.6 | -81.40 |
| sol_5m | 413 | 2035 | 620 | 1,307.11 | 154.00/22.19 | 9.0 | 1,111.38 |
| xrp_15m | 3 | bilinmiyor | 10 | -9.31 | 627.00/30.00 | 66.7 | 0.00 |
| xrp_1d | 7 | bilinmiyor | 74 | -171.67 | 13,561.00/5.53 | 100.0 | -175.80 |
| xrp_1h | 29 | bilinmiyor | 59 | 112.77 | 348.00/13.70 | 31.0 | 39.08 |
| xrp_4h | 22 | bilinmiyor | 79 | -8.27 | 6,574.50/45.49 | 86.4 | -90.48 |
| xrp_5m | 336 | bilinmiyor | 475 | 678.74 | 188.00/15.00 | 11.0 | 543.57 |

| Grup | Ekleme / tamamlama pay % | FIFO çift / kalan $ | Tepe risk medyan/en yüksek $ |
|---|---:|---:|---:|
| bnb_15m | 17.5 / 21.8 | -19.09 / 85.89 | 10.13 / 29.50 |
| bnb_1d | 58.1 / 16.7 | 4.42 / 15.50 | 15.75 / 54.75 |
| bnb_1h | 54.0 / 26.3 | 62.59 / 560.89 | 17.62 / 149.34 |
| bnb_4h | 10.9 / 34.4 | 57.74 / -7.18 | 2.80 / 65.32 |
| bnb_5m | 13.2 / 18.6 | -2.46 / 48.11 | 7.62 / 36.50 |
| btc_15m | 44.0 / 33.0 | -2,220.64 / 6,649.19 | 101.64 / 810.90 |
| btc_1d | 64.5 / 17.8 | -57.38 / -10.82 | 122.00 / 525.40 |
| btc_1h | 39.8 / 36.8 | 2,513.48 / 837.61 | 81.20 / 664.85 |
| btc_4h | 32.2 / 35.6 | -147.95 / 601.26 | 110.05 / 423.32 |
| doge_15m | 21.4 / 9.7 | -144.96 / 449.50 | 18.16 / 58.87 |
| doge_1d | 18.7 / 17.8 | -10.04 / 6.49 | 23.32 / 36.36 |
| doge_1h | 1.2 / 4.2 | -1.77 / 53.52 | 3.28 / 34.00 |
| doge_4h | 17.1 / 23.3 | 44.77 / 33.34 | 5.20 / 45.98 |
| doge_5m | 7.7 / 7.0 | -106.20 / 632.27 | 11.62 / 66.80 |
| eth_15m | 23.0 / 8.3 | 1.66 / 84.03 | 13.50 / 51.55 |
| eth_1d | 40.1 / 48.7 | -26.59 / -7.04 | 141.77 / 171.11 |
| eth_1h | 31.5 / 37.1 | -448.66 / 293.28 | 30.03 / 146.75 |
| eth_4h | 26.3 / 37.4 | -58.42 / -68.98 | 21.12 / 164.62 |
| eth_5m | 34.2 / 14.3 | -603.90 / 2,133.00 | 13.50 / 690.65 |
| sol_15m | 22.6 / 24.3 | -325.14 / 493.11 | 23.85 / 82.74 |
| sol_1d | 45.8 / 37.1 | -154.86 / 50.48 | 103.59 / 156.43 |
| sol_1h | 30.8 / 17.0 | -141.10 / 380.79 | 21.50 / 103.55 |
| sol_4h | 21.8 / 37.3 | -65.45 / 20.14 | 6.18 / 129.72 |
| sol_5m | 19.0 / 5.2 | -439.22 / 1,746.33 | 21.66 / 179.00 |
| xrp_15m | 0.0 / 38.5 | -3.31 / -6.00 | 6.00 / 10.20 |
| xrp_1d | 30.3 / 48.2 | -179.77 / 8.11 | 28.30 / 157.10 |
| xrp_1h | 8.4 / 24.4 | -13.86 / 126.63 | 8.18 / 56.00 |
| xrp_4h | 22.1 / 36.2 | 100.96 / -109.23 | 15.70 / 51.75 |
| xrp_5m | 13.6 / 7.5 | -61.64 / 740.37 | 8.05 / 84.33 |

Bu tabloda faz miktarları eski satır tabanlı etiketlerle karşılaştırılabilirlik için korunmuştur; ilk-paket düzeltmesi aşağıda ayrı. Tepe risk bir piyasanın iki sonuçtaki ödeme vektörünün kötü tarafıdır; sermaye rezervi veya bütün cüzdan riski değildir. FIFO çift/kalan ayrımı sıra ve maliyet atfıdır; ayrı ekonomik strateji değildir.

## Kök nedenler, etkileri ve küçük düzeltme

1. **Piyasa kimliği kaybı.** `R/src/bosona_gec_arastirma.py:50` anahtarda conditionId yok; `R/research.py:207` sample.update eşit anahtardaki bütün çokluğu son piyasanın satırına taşır. Asset boş olan nontrade kayıtlar etkilenir. Ham dilimlerde 193 REDEEM/20 MERGE anahtar çakışması; işlemli nonBTC5 kohortta nihai eksik 143 sıfır-REDEEM ve 10 MERGE/575 USD. `condition_identity.patch` tek alan ekler; gerçek eşit aynı-condition dolumları korur. `collision_check.py` sentetik iki-condition örneği ve on canlı endpoint cevabıyla düzeltmeyi sınar. Kaynak dosya değişmedi. Bu hata eski rapordaki tekrar-MERGE anlatısının bir kısmına somut kök neden verir.

2. **İlk alış satırı ile ilk paket karışıyor.** `R/src/bosona_gec_arastirma.py:149` ilk satırdan sonra ever_opened=True yapar. Aynı saniyedeki kalan dolumlar, karar öncesinde envanter olmadığı halde add etiketini alır. `R/research.py:412` bu etiketleri faz tablolarına; `R/study.py:90` ve `F/analyze.py:152` geç-ekleme kümelerine taşır. `first_batch.patch` ilk zaman grubunun açılış parçalarını first etiketler. Ek olarak dört ilk-saniye reopen açılış parçası da first olur (bunlardan biri BTC15dk); aynı saniyedeki karşı yön ve tamamlamanın gerçek sırası hâlâ belirsiz. Patch emir kimliği çıkarmıyor. `check.py` gerçek regresyonda eski kodun first/add, düzeltilmiş kodun first/first ürettiğini ve nakit toplamının aynı kaldığını doğrular.

3. **Envanter yerine kümülatif alış dengesi.** `F/analyze.py:225` yalnız BUY toplamlarını toplar; `:251` imbalance=abs(net)/sum(q) der. MERGE k kadar çift çözdüyse doğru payda sum(q)−2k. Karşılığında nakit maliyeti de k azalır; q_side−cost ve net yön değişmez. Bu nedenle önceki PnL ve risk hesaplarını yanlış ilan etmek doğru değildir. Düzeltilmiş tarihsel kohortta son dolumdan önce 556 MERGE/373 piyasa; BTC15dk 164 MERGE. `risk_set_actual_inventory.json` yalnız 788 imbalance alanını düzeltir; tüm diğer alanlar aynı. `merge_imbalance_changes.json` önce/sonra gerçek miktarları saklar. H2 yeniden öğrenimi ana raporun istatistik bölümünde ayrıca yapılmalıdır.

4. **SELL ve başka envanter hareketleri.** Bu örneklemde yok. `R/research.py:326` SPLIT/CONVERSION dışlaması, `:329` BUY assert ve frozen ledger:125 SELL hatası var. Dolayısıyla eldeki sonucun sessiz SELL atlamasından etkilendiği iddiası yok. Gelecekte bu hareket geldiğinde kapsam dışı kayıt açık gösterilmeli; BUY-only ledger genel cüzdan muhasebesi gibi sunulmamalı.

## BTC15dk paketleme ve sıra duyarlılığı

5.441 kamu dolumunun aynı saniye / başlangıca sabit 5sn / 10sn zaman paketleri sırasıyla **4.014 / 3.178 / 2.828**. Bunların **18 / 61 / 92** paketinde iki yön birden var. İlk paket pay medyanı **49,805 / 70,501613 / 80,875172**. Paketler parent emir sayısı değildir; 5/10sn aralıkları ilk üyeye sabitlenmiş, zincirleme genişletilmemiştir.

| İlk paket dışlandıktan sonra | Geç dolum | Piyasa | Katkı $ | En iyi3 hariç $ | Piyasa başına5pay $ |
|---|---:|---:|---:|---:|---:|
| 0sn | 1150 | 274 | 3,364.65 | 2,011.97 | 49.35 |
| 5sn | 1134 | 269 | 3,252.47 | 1,899.79 | 46.75 |
| 10sn | 1122 | 266 | 3,126.96 | 1,774.27 | 41.97 |

Bu ilk-paket dışlaması ilk giriş parçalamasını düzeltir; sonraki reopen paketinin ikinci parçası da satır düzeyinde add görünebilir. İkinci kontrol aynı saniye/yönün **tüm parçalarını önce birleştirip** FIFO etiketini sonra üretir; aynı pakette iki yön bulunan piyasanın tamamı dışlanır. 0sn atomik karşılaştırmada aynı belirsizsiz evrenin eski geç katkısı **+3.079,381490**, yeni 659 paket/245 piyasada **+2.911,078100**. 5/10sn atomik sürümler sırasıyla +2.456,11/+870,47; fakat dışlanan piyasa ve 600sn sınır üyeliği de değişir. Bu farklar strateji karşılaştırması veya iyimser/kötümser kesin sınır değildir.

Kaynak aynı saniyeyi transactionHash alfabetik sırasıyla çözer (`ledger:118`); bu gerçek zincir log sırası değildir. Sabit aynı veride Up-önce geç fazı +3.279,992382, Down-önce +3.480,596940; kaynak +3.389,908592. Aynı saniyedeki bütün hash sırasını ters çevirmek +3.127,575541 üretir (75 piyasada faz/FIFO farkı). Toplam BTC15dk PnL bütün sıralarda **+4.428,552489**. Bu dört senaryo olası tüm sıralamanın kesin min/max sınırı değildir. `result.json.ordering` etkilenen piyasa ve tutarı verir.

## Tamamlama ucuz çiftle aynı davranış değil

**DOĞRULANDI:** BTC15dk 1.919 tamamlamanın 902’sinde FIFO çift maliyeti >1; çift katkısı −12.052,190729 USD. 794’ünde bütün dolumdan sonra en kötü ödeme yine iyileşiyor. 237 tamamlama karşı neti aşarak yeni yön riski açıyor. Aynı başlangıçta açık k paya fiyat p ile en fazla k karşı pay alındığında kötü sonuç q*(1−p) iyileşir; eski alış maliyeti çiftin arbitraj kârını belirler, bugünkü risk azaltımını engellemez. Tamamlama/etmeme iki-sonuç vektörü karşılaştırması koşulludur; aktörün dolum fiyatını kendi uygulanabilir ask fiyatımız saymaz.

## Yeni defterli S karşı örneği ve somut yollar

**DOĞRULANDI:** S tam kapalı 14 piyasa, 12 işlemli/2 gözlenen işlemsiz; +165,630507 USD. 54 geç ekleme/8 piyasa −254,167917; en iyi3 hariç −361,678817; piyasa başına5pay −1,851834. İlk yarım yakalanan 14:15 piyasası ve açık18:00 ayrı. S için yalnız dondurulmuş ham activity ve market kaynakları okundu; eski yazan check.py çalıştırılmadı.

| Yol | Resmî sonuç | Up / Down pay | Nakit maliyet $ | Toplam $ | Geç katkı $ |
|---|---|---:|---:|---:|---:|
| btc-updown-15m-1789564500 (historical) | Down | 883.94 / 301.06 | 762.26 | -461.20 | -230.54 |
| btc-updown-15m-1789708500 (historical) | Up | 1,236.95 / 15.00 | 601.79 | 635.16 | 589.22 |
| btc-updown-15m-1790001900 (status) | Up | 0.00 / 1,224.66 | 221.93 | -221.93 | -185.93 |
| btc-updown-15m-1790001000 (status) | Up | 553.81 / 1,452.02 | 353.04 | 200.77 | -136.80 |
| btc-updown-15m-1790002800 (status) | Up | 131.39 / 0.00 | 90.64 | 40.75 | 0.00 |

S 14:30 kazananının toplamı +200,77 iken geç eklemeleri −136,80: faza bakıp tüm yolun zarar ettiğini söylemek yanlış. S 14:45 kaybedeninin 18 geç dolumu −185,93; pozisyonun tamamı kaybeden Down. S 15:00 kontrolünde gözlenen geç ekleme yok; dolmayan/iptal emirleri bilinmiyor. Her yolun bütün dolumları, öncesi/sonrası iki ödeme vektörü, FIFO ve marginal nakdi `cases.json` ve `CASES.md` içinde. Emir ilk gönderim/iptal zamanı ve kesin maker/taker bu muhasebe alt görevinden belirlenmez; zincir rol denetimi ayrı kanıt ister.

## Yeniden üretim

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/accounting/audit.py
PYTHONDONTWRITEBYTECODE=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/accounting/collision_check.py
PYTHONDONTWRITEBYTECODE=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/accounting/check.py
PYTHONDONTWRITEBYTECODE=1 python3 -m ruff check --no-cache /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/accounting/audit.py /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/accounting/collision_check.py /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/accounting/check.py
```

Yeni kamu indirmesi yalnız `collision_check.py --fetch` ile; on cevap zaten önbellekte. URL, alınma zamanı, condition ve tam ham cevap `raw_collision_checks/` altında. `inputs.json` ile `collision_inputs.json` okunan ham dosyaların SHA256 değerlerini taşır. Rastgelelik/değer optimizasyonu yok; stdlib Decimal precision28, Python3.12.3 kullanıldı. 5 frozen-source hash, R14 ve F16 reproduction hashleri ve S manifesti kontrol edildi. Kaynak checksum eşleşmesi tek başına aritmetiğin doğruluğu sayılmadı. Atomik paketler ve iki düzeltme regresyonu, syntax, Ruff ve gerçek veri koşusu geçti.

**Sınır:** ayrı endpoint eşleşmesi bağımsız zincir olayı demek değildir; tüm ticaret emirlerini tanımlamıyoruz. Toplam hesap ve belirli API kimlik kusurları doğrulandı; tam Bosona karar kuralı bu hesaplardan tanımlanamaz. Yeni avantaj iddiası, önceden mevcut bilgi ve gerçek alınabilir fiyatla bağımsız politika kontrolü geçmeden değişmez.

## Karar zamanı için ek veri anomalisi

**DOĞRULANDI / YORUM ÖLÇÜLEMİYOR:** resmî endDate veya sonrasında tüm kohortta 92 satır/55 piyasa, -702.926086 USD katkı var; BTC15dk 24 satır/5 piyasa, 141.420815 USD. İlk alım da resmi bitişten sonra olan piyasalar: bnb-updown-4h-1789833600, bnb-updown-5m-1789268100, bnb-updown-5m-1789314900, bnb-updown-5m-1789386000, bnb-updown-5m-1789461300, bnb-updown-5m-1789482300, bnb-updown-5m-1789487400, bnb-updown-5m-1789548000, bnb-updown-5m-1789575900, bnb-updown-5m-1789730700, bnb-updown-5m-1789821300, btc-updown-15m-1789846200, doge-updown-15m-1789519500, doge-updown-15m-1789760700, doge-updown-5m-1789282500, doge-updown-5m-1789431000, doge-updown-5m-1789472400, doge-updown-5m-1789518600, doge-updown-5m-1789649700, doge-updown-5m-1789818000, doge-updown-5m-1789845900, eth-updown-15m-1789674300, eth-updown-15m-1789849800, eth-updown-15m-1789863300, eth-updown-5m-1789845300, eth-updown-5m-1789878300, sol-updown-5m-1789296900, sol-updown-5m-1789365000, sol-updown-5m-1789393200, sol-updown-5m-1789557000, sol-updown-5m-1789845300, xrp-updown-5m-1789275300, xrp-updown-5m-1789705200, xrp-updown-5m-1789845300. Özellikle btc-updown-15m-1789845300 age1331..2777 dolumları ve arada REDEEM içerir. API timestamp'i karar/emir zamanı saymak bu noktada savunulamaz; işlem/condition/token eşleşmesi geçmiştir, gerçek zincir zamanı ve olası geç settlement ayrı kontrol ister. PnL bu kayıtları taşır; 600<=age<900 geç-ekleme kümesi bunları içermez. `postclose_fills.json` bütün kayıtları saklar. REDEEM sonrası kayıp token yakım miktarı kamu satırından belli olmadığında gerçek miktarı null bıraktım; sıfır veya uydurma stok yazmadım.
