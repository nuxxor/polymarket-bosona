# M2 — Gerçek D/E/F emirleriyle yürütme kontrolü

21 Eylül 2026. Salt okunur tarihsel çalışma; yeni emir veya shadow yok.

**Karar: yürütme simülatörü henüz kalibre değil.** Kendi geçmiş emirlerimizin miktar ve nakdi eksiksiz uzlaştı. Ancak başarılı iptallerin istek/cevap saatleri kayıtlı değil. Ayrıca görünen ilk kuyruğu yalnız işlemlerle eriten model, gerçek dolumların önemli bir kısmını yeniden üretemiyor. Bu model üstünde yeni strateji seçimine geçilmedi.

## 1. Dondurulan gerçek evren

Londra'dan alınan D/E/F log ve state dosyalarının hash'leri saklandı. E/F'ye devredilmiş eski emirler tekrar sayılmadı. İlk kabul **20 Eylül 15:10:06.824**, son kabul **21:56:21.428 UTC**.

| Kol | Kabul edilmiş emir | En az kısmen dolmuş | Hiç dolmamış | Gerçek pay |
|---|---:|---:|---:|---:|
| D | 536 | 113 | 423 | 557,674205 |
| E | 71 | 51 | 20 | 252,799834 |
| F | 17 | 6 | 11 | 30,000000 |
| **Toplam** | **624** | **170** | **454** | **840,474039** |

70 state penceresinin 59'unda kabul edilmiş emir var. Diğer 11 pencere kabul-emri kalibrasyonunun paydasında değil; yok sayılmış dolmayan emir değiller. Reddedilmiş niyetler de kabul edilmiş emir gibi değerlendirilmedi.

Bu 59 condition'ın tam kamu activity geçmişi alındı: **203 BUY kaydı / 203 transaction / 203 zincir dolumu**. Her dolum gerçek orderHash'e, token miktarına ve pUSD/CTF transferlerine bağlandı. Toplam nakit çıkışı **385,432141 dolar**. Nihai state ile 624 emrin tamamının miktarı uzlaştı; 454 sıfır dolum da korundu. Yeni bir PnL, rebate veya strateji geliri hesabı yapılmadı.

**203/203 dolum maker.** Bunun önemi: pasif emir vermek bizim eski botlarımızda zaten var. Bosona'nın maker ağırlığını bulmuş olmak tek başına eksik kazanç mekanizmasını çözmüyor.

## 2. Saatlerin gerçek anlamı

`NIYET → ack_ms`, rezerv kaydından sonra başlayıp emir kurma/imzalama ve POST cevabını kapsayan süre. Saf ağ gecikmesi veya borsadaki kesin aktivasyon saati değil. Gerçek aktivasyon bu sürenin içinde olabilir.

| Ortam / kol | Emir | Medyan | %95 alt ampirik yüzdelik |
|---|---:|---:|---:|
| Türkiye D | 56 | 125,5 ms | 493 ms |
| Londra D | 480 | **70 ms** | 366 ms |
| Londra E | 71 | **69 ms** | 207 ms |
| Londra F | 17 | **96 ms** | 126 ms |

F örneği küçük. D'nin bütün konumlar karışık medyanı 79 ms; Londra ölçüsü 70 ms. Bu ölçüm dünyanın en hızlı altyapısı veya kesin kuyruk önceliği iddiasını desteklemiyor.

`dolum_ms` ise botun `get_order`/mutabakat üzerinden dolumu **öğrendiği** zaman. Exchange gerçekleşme zamanı değil. Uygun kamu akışıyla eşleşen kayıtlarda öğrenme farkının medyanı D/E/F için 394/371/318 ms. Bazı farklar saniyeler; birkaç küçük negatif fark saat/yayın belirsizliği içinde. Bunları gerçek negatif işlem gecikmesi diye yorumlamadık.

Zincir orderHash/log kimliği ile kamu `last_trade_price` aktif eşleşmesi birleştirildi:

- **183/203 dolum** zaman kalite kuralını geçti; miktar kapsamı **%89,77**.
- 13 dolumun yerel alınma gecikmesi 1 saniyeyi aşıyor.
- Bir dolumda kamu kaynak saati, botun dolumu öğrenmesinden 209 ms sonra; saat anlamı/belirsizliği nedeniyle dışarıda.
- Altı dolum için bu DB kesitinde uygun WS işlem kaydı bulunmadı.

Kamu WS kaynak saati de doğrulanmış özel exchange execution timestamp'i değildir. Zincir blok sırası CLOB işlem sırası yerine kullanılmadı.

183 kullanılabilir kaydın 50'si kamu saatine göre niyetten sonraki ilk 250 ms içinde. 100 ms saat payı uygulayınca **13 kayıt** bu sınırdan hâlâ önce. **41 kayıt** 1.250 ms'den sonra; örnek bir E emri son parçasını yaklaşık 91,45 saniyede alıyor. Dolayısıyla M1'in 250 ms aktivasyon / yaklaşık bir saniyelik teklif ömrü, kendi geçmiş botlarımızın ölçülmüş zaman modeli değildi. Bu, her yeni teklif için bu süreleri tersine çevirip kâr hesaplamaya izin vermez.

## 3. Asıl eksik: başarılı iptalin saati

`kapat()` iptal çağrısı yapıyor, ardından emir durumu sorguluyor. Başarılı yol durum/sebep kaydediyor; **iptal isteği başlangıcını ve iptal cevabı bitişini kaydetmiyor**. Hata/sonradan teyit olayları bazı emirler için var. Yeni aynı-taraf niyeti, tam dolumun öğrenilmesi ve nihai çözüm kaydı kapanışa yalnız üst sınır verebiliyor.

624 emirden hiçbirinde tam iptal istek/cevap saat çifti yok. Özellikle 454 dolmayan emirde bu bilgi olmadan:

> “Model doldurdu ama gerçekte dolmadı” ile “gerçek emir o işlem gelmeden önce iptal edilmişti” ayrıştırılamıyor.

Sonraki emrin saatini öncekinin kesin iptal saati saymadık. Pencere başlangıcından varsayımsal emir saati üretmedik. `confusion_matrix` ve tam-ömür tahmini bu yüzden **null**; başarı oranı sıfır veya %100 değil. Dolu emirlerin kapanışı için iptal gerekmemesi, dolmayan emirlerdeki bu eksikliği gidermez.

Diskteki yaşam döngüsü fonksiyonları ayrıca kaydedildi. Güncel D dosyası ile canlıda kullanılmış `1c29c157c576` arşivinin incelenen yedi fonksiyon hash'i birebir aynı; kanıt `source_audit.json` içinde. Diğer başlangıç hash'leri logda korunuyor; bütün eski kaynak sürümleri yeniden bulunmuş sayılmıyor.

## 4. Buna rağmen sınanabilen şey: statik kuyruk gerçek dolumu kaçırıyor mu?

Sonucu/dolumu kullanmadan her koldan orderHash sırasıyla **12 emir** seçildi: 36. Niyetten 100 ms önceki defterler yeniden kuruldu; 36/36 başlangıç bağlamı geçerli. Kendi yeni emrimizi kuyruğunun önüne ikinci kez eklememek için kabul-sonrası görüntü kullanılmadı. İki tokenin aynı ekonomik seviyesindeki miktarlar karşılaştırıldı.

Bu 36 emrin 16'sı gerçekte dolmuş. Tam kullanılabilir dolum saati bulunan **14'ünde** ek, açıkça aktöre koşullu tanısal kontrol yapıldı:

1. Gerçek fiyat ve miktar kullanıldı.
2. İlk görünen seviyedeki miktar önde kabul edildi; iptallerden sıra ilerlemesi verilmedi.
3. Model lehine geniş zaman aralığı: niyet −100 ms'den **gerçek son dolum +100 ms'ye** kadar tüm uygun işlem hacmi.
4. 548 işlem transaction'ı ayrıca alındı. Gerçek maker bacakları ve bütün katılımcıların nakit/token transferleri uzlaştı; aynalı işlem tekrar sayılmadı.

**Bitiş zamanı gerçek dolumdan seçildiği için bu bağımsız ileri tahmin değildir.** Soru yalnız şu: ihtiyaç duyduğu süreyi bile verdiğimiz statik model, olmuş dolumu açıklayabiliyor mu?

| Ölçü | Sonuç |
|---|---:|
| İncelenen gerçek dolmuş emir | 14 |
| Gerçek dolum | **69,982214 pay** |
| Statik kuyruk hesabı | **35 pay** |
| Gerçekte dolduğu hâlde modelde sıfır | **7 emir** |
| Modelin biraz fazla doldurduğu kısmi emir | 2; toplam 0,017786 pay fark |

Örnekler, 20 Eylül UTC:

| Pencere / kol | Limit | Başlangıçta görünen ön miktar | Aralıkta uygun işlem hacmi | Gerçek / model |
|---|---:|---:|---:|---:|
| 16:15 D | 0,45 | 189 | 20 | **5 / 0** |
| 18:55 E | 0,40 | 55 | 20 | **5 / 0** |
| 21:50 F | 0,73 | 134 | 19,993704 | **5 / 0** |

Bu üç örnekte geç WS raporu yok. Uzun 19:40 E örneğinde 26 maker akışı geç ulaşıyor; kontrol modele avantaj sağlayarak bunları da hacme dahil ediyor. Yine sıfır hesaplıyor. Tek tek kayıp/kazanç sonucu kullanılarak kural seçilmedi.

**Yorum:** Başlangıçtaki görünen kuyruğun kalıcı olduğu varsayımı gerçek yürütmeyi yeterince temsil etmiyor. Önümüzdeki emirlerin iptali/yeniden fiyatlanması, gerçek aktivasyon anındaki farklı sıra ve L2'nin sınırlı gözlemi olası açıklamalar. Bunların hangisinin ne kadar payı olduğu bu veriyle ayrıştırılmadı. “Bütün miktar azalışları önümüzdeki iptaldi” varsayımına geçmek de doğru olmaz; bu kez olmayan dolumlar üretebiliriz.

7/14 **genel hata oranı değildir**: alt küme zaten dolmuş emirlerden oluşuyor, piyasa/gün bağımsızlığı zayıf ve bitiş gerçek dolumdan geliyor. Yalnız statik yaklaşımın somut yeniden-üretim başarısızlığıdır. M1'in −8,35 doları kendi varsayımlarındaki çıktı olarak kalır; güvenilir maker-strateji hükmüne yükseltilemez.

## 5. Kontrol sırasında yakalanan küçük para hassasiyeti

Gerçek bir 0,022728 paylık parçanın nakdi 0,012728 dolar. Bölüm 0,56001408 çıkıyor; emir limiti 0,56. Aradaki fark **0,32 mikro-dolar**. Küçük miktarda nakit yuvarlaması fiyat bölümünde büyüyor.

Bu kontrolde fiyatı sabit mutlak epsilon ile karşılaştırmak yerine tam miktar üzerinden nakit tutarlılığı denetlendi. Tanısal akış karşılaştırmasında da iki mikro-dolarlık nakit toleransı kullanıldı. 0,561'lik gerçek daha pahalı beş pay, 0,56 seviyesine yanlışlıkla dahil edilmiyor; negatif kontrol var. Eski dondurulmuş M1 kaynak/çıktısı değiştirilmedi.

## 6. Sonraki kapı ve gerçek runtime

Yeni kârlı strateji lane'i için henüz yeterli yürütme kanıtı yok. Tam kalibrasyonun eksik girdisi **emir kimliğine bağlı gönderim, kabul, her iptal isteği/cevabı ve dolum olaylarının ayrı kaynak/alınma saatleri**. Bunlar gelecekteki gerçek emir kaydında bulunmadan geçmişteki boşluğu dolduramayız. Bu çalışma yeni gerçek emir başlatmadı veya bu kayıtların toplanmış olduğunu iddia etmedi.

Sonraki yürütme testi, aynı emirler üzerinde statik kuyruk ile miktar azalışlarını ihtiyatlı biçimde ele alan modelin hem dolan hem dolmayan emirlerde karşılaştırılması olmalı. İptal verisi eksik olan bu 454 emirle model parametresi optimize edilmemeli. Yeni risk açmak veya kâr gösteren bir shadow üretmek, bu eksik ölçümün yerine geçmez.

21 Eylül **19:47:20.831 UTC** kontrolünde sekiz eski shadow/gözlemci PID'si ve ilgili shadow süreci yok. Jev, gerçek botların kaynak/state/bütçeleri ve ham kaydediciler değiştirilmedi. Yalnız sonlu kamu GET/RPC toplaması çalıştı; sürekli servis kurulmadı.

Tekrar:

```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_own_execution_20260921/analyze.py"
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_own_execution_20260921/flow_probe.py"
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_own_execution_20260921/check.py"
```

Emir çokluğu, eksik/çift niyetin reddi, gelecekte alınmış defterin karara sızmaması, eski defter, nakit yuvarlaması, gerçek transferler ve akış hesabı kontrolleri; hedefli Ruff/derleme ve iki raporun **byte-identical** tekrarı geçti. Yazılım kontrollerinin geçmesi tam kalibrasyon kapısının geçmesi değil.

Kanıtlar: `data/analysis/btc5m_own_execution_20260921/`. Ana rapor bütün 624 emrin mutabakatını, 203 dolumun zaman durumunu ve 36 defter bağlamını; `flow_probe/report.json` 14 tanısal emrin her bir hacim kaynağını içeriyor. Ham kaynak hash'leri, filtrelenmiş log/state kesiti, public activity, receipt'ler, kaynak fonksiyonları ve doğrulama manifestleri saklandı.
