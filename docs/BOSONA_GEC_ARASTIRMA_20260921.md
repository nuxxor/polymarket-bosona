# Bosona BTC5m: geç dolum araştırması — 21 Eylül 2026

İlk araştırma turu ve ileri kayıt kurulumu tamamlandı. **Kârlı bir uygulama kuralı doğrulanmadı.**
Londra'da 24 saatlik, gerçek emir vermeyen kayıt çalışıyor. F/LIVE kaynak, bütçe ve süreçlerine müdahale edilmedi.

## Kapsam ve veri

13 Eylül 00:00–20 Eylül 22:30 UTC sözleşmeleri; Bosona'nın **1.842 piyasada 19.761 BUY kaydı**.
Pencere bitiminden en az 20 dakika geçmiş veriler kullanıldı. Altı saatlik ayrık zaman
aralıklarında /activity sayfalandı; atlanan parça yok. Önceki günden de veri çekilerek
pencere öncesi alımlar kapsandı. Beş tarihe yayılmış piyasa, ayrı /trades uç noktasında
`takerOnly=false` ile kontrol edildi: paylar ve brüt sonuç birebir aynı. Bu örnek kontrolü,
API'nin bütün tarih boyunca eksiksiz olduğunun zincir üstü kanıtı değildir.

Dönem yalnız BTC5m'dir; diğer piyasa kazançları veya cüzdan bakiyesiyle karıştırılmaz.
`usdcSize` alış maliyeti ve sonuç ödemesi hesabı **+8,319.44 USD**;
`size×price` ile brüt hesap **+10,109.29 USD**. Rebate ve sabit giderler dahil değildir.
Bu sayı tam hesap net geliri veya gerçekleşmiş nakit akışı değildir. MERGE ödemeleri
ayrıca kâr eklenerek ikinci kez sayılmaz.

## 1. Kazanç hangi davranışlarda görünüyor?

Nedensel sırayla FIFO eşleme muhasebesinde çift katkısı **+14,799.08 USD**,
açık kalan miktarın katkısı **-6,479.64 USD**. Toplam, bağımsız
alış–ödeme hesabıyla uzlaşıyor. Maliyet dağıtımı bir muhasebe seçimidir; bu ayrım
tek başına çift tamamlama becerisinin veya bir stratejinin kanıtı değildir.

Son 100 saniyedeki 6.242 kaydın toplam işlem katkısı **+4,603.64 USD**.
Aşağıdaki katkı, ilgili miktarın nihai ödemesi eksi alış maliyetidir:

| Geç dolumun rolü | Pay | Katkı, USD | En iyi 3 pencere hariç |
|---|---:|---:|---:|
| İlk dolum | 7,338 | +450.12 | -204.34 |
| Mevcut açık yönü artırma | 132,394 | +2,784.24 | +912.52 |
| Karşı yönü tamamlama | 111,945 | +1,098.53 | -453.23 |
| Yeniden açma / tamamlamayı aşan kısım | 24,408 | +270.76 | -537.44 |

En büyük geç katkı mevcut açık yöne eklemelerde. Ancak aynı kuralın tüm günlerde
kazandırdığı sonucu çıkmıyor. Mevcut maliyetin altında ekleme grubunun en iyi üç
pencere hariç sonucu **-117.16 USD**;
“ucuzladıysa ekle” tarifi de hazır bir kazanç kuralı değil.

Bir dolum hem tamamlama hem yeniden risk açma miktarı içerebilir. 41 pencerede
aynı saniyedeki karşıt yönlü kayıtların sırası belirsiz; toplam PnL bundan etkilenmez,
bacak etiketleri etkilenebilir. İlk dolum, ilk emrin tamamı demek değildir.
Kamu zamanı pencere sonuna/sonrasına düşen 36 kayıt ayrıca tutuldu
(**+132.76 USD**); blok zamanını emir zamanı saymıyoruz.

## 2. Yalnız geç tamamlamaya izin vermek yeterli mi?

Keşif amaçlı karşılaştırma: ilk 200 saniyedeki alımlar aynen korunuyor; son 100 saniyede
yalnız mevcut açığı kapatan ve FIFO nakit maliyeti toplamı 0,98'i aşmayan miktar alınıyor.
Fiyat ve dolum mevcudiyeti Bosona'nın gerçekleşmiş işlemlerinden geliyor. Bu bizim
botumuzun çalıştırılabilir backtest'i veya o fiyatlarda dolum garantisi değildir.

- Değişen 364 pencere: **88 iyileşme, 276 kötüleşme**.
- Toplam fark: **+244.95 USD**; en iyi üç pencere çıkarılınca **-814.94 USD**.
- Pencere bootstrap %95 aralığı: **[-2,084, 2,575] USD**.
- Sırası belirsiz pencereler çıkarılınca fark **+352.96 USD**; sonuç yine üstünlük kanıtı değil.
- En kötü sonuç riski hiçbir pencerede artmıyor; risk azalması ile ortalama kazanç artışı aynı şey değil.

## 3. Önceden belirlenen üç basit kural

Birincil karar t=240; t=210 ve 270 ikincil kontroller. 5 sanal pay, karar anındaki
favori, en az 250 ms sonraki ask derinliği ve o piyasanın taker ücreti kullanıldı.
Maker dolumu varsayılmadı. Ücret formülü ve piyasa parametreleri
[resmî ücret belgesine](https://docs.polymarket.com/trading/fees) göre; iade varsayımı sıfır.

| t=240 kuralı | İşlem seçilen pencere | Sanal sonuç, USD | Uygun pencere başına USD |
|---|---:|---:|---:|
| Piyasa favorisi | 131 | -21.66 | -0.165 |
| Favori + spot/TWAP uyumu | 108 | -30.48 | -0.233 |
| Uyum + en az 1 oynaklık birimi uzaklık | 60 | -19.19 | -0.147 |

Karşılaştırmalar aynı **131 uygun pencere** üzerinde;
sinyal üretmeyen geçerli pencere sıfır katkıyla dahil. Eksik veri ayrı. Kullanılabilir
defter/fiyat kesişimi yalnız 19–20 Eylül: bu sonuç sekiz günlük politika testi değildir.
339 kayıtlı pencere × üç zamanda, son kapsam: {"missing_prices": 226, "missing_books": 412, "eligible": 379}.
Tümü negatif nokta tahmini; birincil güven aralıkları sıfırı kapsıyor.
Bu örnekler canlıya geçiş veya tüm ailenin başarısızlığı kararı vermiyor.

Dolum öncesi spot/TWAP bilgisi 5 saniye geriden **5710/19.761** kayıtta mevcut;
10 saniye gecikme kontrolü ayrıca raporda. Eksik saatler ve bozuk gzip parçaları gizlenmedi.
Ham fiyat dosyaları son sürümde donduruldu; kod alınma zamanına göre as-of eşleme yapar.
13–17 Eylül keşif, 18–20 Eylül kronolojik kontroldür; daha önce görülen günler olduğundan
hiç dokunulmamış bir kör test iddiası yoktur. Basit yön uyumu, kontrol günlerindeki
kazançlı geç dolumları güvenilir biçimde ayıramadı.

## 4. Dolum fiyatı mı, seçilen an mı?

İşlem hash'iyle CLOB zamanına eşlenen ve dolumdan 250 ms önceki defteri bulunan
**403 kayıt / 67 pencere** incelendi; yalnız iki gün.
Gerçek miktarla katkı +1,008.62 USD. Orta fiyata göre muhasebe ayrımı:
sonuca doğru hareket +999.12 USD, ödenen fiyatın orta
fiyata göre farkı +9.49 USD. Mid alınabilir fiyat değildir;
bu hesap yön becerisinin veya iptal/kuyruk avantajının bağımsız kanıtı değildir.

Her kaydı eşit 5 paya indirince kendi alış fiyatıyla +95.45,
dolum öncesi ask+ücretle +20.19 USD.
Ask karşılaştırmasında en iyi üç pencere hariç sonuç -94.34 USD.
Bu da pozitif kural kanıtı değil: zamanları Bosona'nın gerçekleşmiş işlemleri seçiyor.
API fiyatı birden çok dolumun ortalaması olabilir. Sonuç, yalnız alış fiyatındaki
indirime bakarak stratejiyi açıkladığımızı söylemememiz gerektiğini gösteriyor.

## 5. Londra ileri kayıt

- Süre: **20 Eylül 23:20 → 21 Eylül 23:20 UTC**; Türkiye **21 Eylül 02:20 → 22 Eylül 02:20**.
- Son sonuçları toplamak için en geç 25 dakika daha bekler.
- Oturum: `bosona-gec-shadow`; ilk doğrulanan PID 90794.
- Üç kural sabit; t=210/240/270 ayrı sanal dünyalar. Birincil sonuç t=240.
- Yalnız kamu GET çağrıları ve mevcut fiyat kaydı. Cüzdan/özel anahtar/gerçek emir yok.
- İlk pencerede 210 ve 240 kararları zamanında kaydedildi; 270'te boş/uygunsuz defter
  nedeniyle ölçüm boşluğu kaydı var. Boşluk işlem yapılmış gibi doldurulmadı.
- Kural/source hash'i **1f33a277c694b781ca3b5f30f3f5369b39ae1497cdae4cd76ceeb26d70652086**. Yerel araştırma sürümü daha sonra
  rapor fonksiyonlarıyla ilerledi; Londra'daki dondurulmuş kurallar değiştirilmedi.
- İleri ekonomik sonuç henüz tamamlanmadı. >=3 ayrı gün ve >=100 pencere, iki kümeleme
  yönteminde alt güven sınırı >0 ve en iyi üç pencere hariç pozitif sonuç olmadan
  avantaj iddiası yok. 24 saatlik ilk kayıt tek başına bu kanıtı sağlayamaz.

İleri dosyalar: `/home/ubuntu/polymarket-bosona-research/data/bosona_gec_forward/`.
STOP dosyası bu dizindeki `STOP_SHADOW`; yalnız bu ölçüm sürecine aittir.

## Tekrar çalıştırma ve doğrulama

Betik: `analiz/izleme/bosona_gec_arastirma.py`; yardımcı `muhasebe.py` yeniden kullanıldı.
Komutlar: `check`, `fetch`, `analyze`, `audit`, `counterfactual`.
Aynı veriyle ağsız ana rapor için `analyze`; API snapshotları, defter kesitleri ve
`price_snapshot/` korunmalı. Eksik cache olursa yalnız kamu verisi istenir.

FIFO/karşı tarafa fazla dolum, tekrar çağrıda değişmezlik, gelecekteki fiyatın etkisizliği,
ikili price_change mesajı, gecikmiş ilk defter, bayatlık, metin fiyatı, ask derinliği,
ücret ve tamamlama risk kontrolleri geçti. Ruff ve Python derleme kontrolü geçti.
Gerçek veride tüm miktar/PnL bölümleri uzlaşıyor; karar/defter/işlem zaman sıraları
assert ile denetlendi. Gerçek Londra kararları ve çalışan kaynak hash'i doğrulandı.

Kanıtlar: `data/analysis/bosona_gec_20260921/` altında `report.json`, `fill_ledger.json`,
`windows.json`, `policy.json`, `policy_risk.json`, `execution_audit.json`,
`completion_counterfactual.json`, `independent_api_check.json`, `forward_validation.json`.
Analiz kaynak hash'i: `0cbcd565c0e6c61ad02825b90e18342f95875a25d67c1262a8c0aa42d05dac2b`.
