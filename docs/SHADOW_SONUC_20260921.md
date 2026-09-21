# Jev ve iki shadow: 21 Eylül 2026 ara sonuçları

Kesim: **21 Eylül 13:15 Türkiye saati (10:15 UTC)**. Aşağıdaki saatler Türkiye saati.
Londra'daki kayıtlar donduruldu; kapanmış pencerelerin sonuçları kamu Gamma API'sinden
yeniden doğrulandı. Bunlar **beş paylık sanal alımların**, kayıtlı satış teklifleri
ve taker ücretiyle hesaplanan sonuçlarıdır; gerçek dolum veya cüzdan kazancı değildir.
API ve sunucu giderleri işlem PnL'sine dahil değildir. Farklı zaman kolları ayrı
stratejilerdir; sonuçları bir portföy gibi toplanmaz.

**Çalışma durumu ve süre**

| Deney | Ölçülen dönem | Durum |
|---|---|---|
| Jev V2, son dakika kararı | 01:20–02:45; 17 pencere | İki saatlik ortak pilot bütçesinin süresi doldu; 02:47'de normal kapandı |
| İlk shadow, üç kural | 02:20–13:15; 131 pencere / 10 saat 55 dakika | Çalışıyor; planlı atama bitişi 22 Eylül 02:20 |
| Yeni rebound shadow | 03:50–13:15; 113 pencere / 9 saat 25 dakika | Çalışıyor; planlı atama bitişi 24 Eylül 03:50 |

Jev'in ilk sürümü 00:44'te başlamıştı; V2'ye geçiş aynı 02:44 karar bitişini
korudu. Gece boyunca 12 saat Jev tahmini birikmedi. İki shadow ve ayrı gecikme
gözlemcisinin süreçleri çalışıyor; kaynak hash'leri sabit manifestlerle eşleşiyor.
Bu incelemede süre, kaynak, strateji veya çalışan süreç değiştirilmedi.

**Jev V2**

| Aynı 11 nihai karardaki yöntem | Kazanan / işlem | Ücret sonrası sanal PnL |
|---|---:|---:|
| Jev, bütün girdiler | 10 / 11 | **+$12,53070** |
| Jev, yalnız teknik girdiler | 10 / 11 | +$12,53070 |
| Basit piyasa favorisi | 9 / 11 | +$4,68269 |

17 atanmış pencerede 119 ara/nihai tahmin var. Altısında veri/tazelik/defter
engeli nedeniyle zamanında nihai işlem oluşmadı; bunlar kazanmış veya kaybetmiş
işlem sayılmadı. Jev, aynı 11 işlemde favoriden $7,84801 daha iyi sonuç verdi.
İki Jev görünümünün nihai yönleri aynıydı. Piyasa verisini eklemenin ayrıca
kazanç sağladığı gösterilmedi.

11 işlem çok küçük örnek. İlk 30 saniyedeki tahminlerde Jev 7/17, favori 11/17
doğruydu; son dakika başarısı bütün ara tahminlerin güçlü olduğu anlamına gelmiyor.
Nihai Brier hatası Jev 0,06954, teknik görünüm 0,08122, favori 0,14430.
Jev V2'nin en yüksek birikimli düşüşü $2,13467; en iyi üç işlem çıkarılırsa
sonuç +$4,33575. Bunlar kalıcı avantaj kanıtı değildir.

Önceki V1: bir sanal işlem, −$1,26384. İki sürümün salt muhasebe toplamı
+$11,26686; V2 değerlendirmesine eski sürüm karıştırılmadı. Bütün sürümler ve
bağlantı denemesi için kayıtlı token/fiyat hesabı **yaklaşık $0,01750 API
gideri**; gerçek hesap ekstresi değildir. V2 API medyanı 514 ms; API hata kaydı 0.

**İlk shadow: favori ve iki filtre**

Önceden seçilmiş ana karşılaştırma **son 60 saniye**. Favori: tahtanın daha
yüksek fiyat verdiği yön. Uyum filtresi: anlık BTC ve hesaplanan kapanış
ortalaması da o yönde. Sıkı filtre: buna ek olarak kapanış ortalaması farkının
oynaklığa göre en az bir birim olması.

| Kalan süre | Kural | Geçerli pencere | İşlem / kazanan | Ücret sonrası PnL |
|---|---|---:|---:|---:|
| 90 sn, ikincil | Favori | 70 | 70 / 62 | +$2,28668 |
| 90 sn, ikincil | BTC uyumlu favori | 70 | 61 / 56 | +$4,16919 |
| 90 sn, ikincil | Sıkı filtre | 70 | 37 / 34 | −$3,87301 |
| **60 sn, ana** | **Favori** | **40** | **40 / 36** | **+$6,63001** |
| **60 sn, ana** | **BTC uyumlu favori** | **40** | **34 / 31** | **+$4,62804** |
| **60 sn, ana** | **Sıkı filtre** | **40** | **25 / 22** | **−$3,35196** |
| 30 sn, ikincil | Favori | 12 | 12 / 12 | +$5,22495 |
| 30 sn, ikincil | BTC uyumlu favori | 12 | 8 / 8 | +$3,58173 |
| 30 sn, ikincil | Sıkı filtre | 12 | 1 / 1 | +$0,23337 |

Ana kolda 131 pencerenin yalnız **40'ı (%30,5)** ölçülebilir. Kalan 91:
69 boş/geçersiz defter, 20 eski fiyat, iki başlangıç referansı eksik.
Geçerli ama filtre nedeniyle işlemsiz altı/15 pencere, bu veri boşluklarından
ayrıdır. 90/30 saniye kollarında sırasıyla 61/119 veri boşluğu var.

Ana favori kolunda en yüksek birikimli düşüş $5,31979. En iyi üç işlem
çıkarılırsa favori +$1,37263, uyum filtresi −$0,23830, sıkı filtre −$5,32582.
Bu kesitte ek filtreler toplam doları artırmadı. Ancak kapsama düşük ve
bir günlük örnek bile tamamlanmadı; kazançlı sistem ilan edilemez.

**Yeni rebound shadow: ana test henüz ölçülemedi**

Kural: ucuz tarafta RSI14 <40, son 10 saniyede o yönde toparlanma ve alış
fiyatı <0,50. Önceden belirlenen ana zaman **son 20 saniye**.

| Kalan süre | Geçerli / atanmış pencere | Seçilen işlem / kazanan | Ücret sonrası PnL |
|---|---:|---:|---:|
| 60 sn, ikincil | 32 / 113 | 9 / 1 | **−$3,31884** |
| 30 sn, ikincil | 0 / 113 | — | Ölçülemedi |
| **20 sn, ana** | **0 / 113** | **—** | **Ölçülemedi** |

60 saniye kolunda 23 geçerli pencere sinyal üretmedi. Aynı 32 pencerede
favoriyi alan kontrol 30/32 kazandı, +$9,11713. Dolayısıyla ölçülebilen
ikincil aday bu kesitte kontrolün gerisinde. Ana zaman için sıfır PnL veya
başarısız strateji sonucu yazmak yanlış olur: geçerli karar yok.

**Kendi uygulamamızda mum yenileme zamanlaması hatası var.** Mum verisi
yaklaşık t=225,6'da alınıyor. t=245'te henüz 30 saniye eskimediğinden
yenilenmiyor, fakat hazırlık zaman damgası güncelleniyor. Sonraki fırsat
t=260 olduğunda izin verilen hazırlık aralığı bitmiş oluyor. Böylece
t=270/280'de son kapalı mum 90/100 saniye eski kalıyor; 62 saniyelik
tazelik kontrolünü geçemiyor. Dondurulmuş kaynak bloğu çalıştırılarak ve
15 adet t270 + 10 adet t280 gerçek bağlam hatasıyla doğrulandı.

Son 20 saniyedeki 113 denemenin 103'ü önce boş/geçersiz defter kontrolünde,
diğer 10'u bu eski mum sorunuyla elendi. Son 30 saniyede dağılım
97 defter + 15 eski bağlam + bir referans eksiği. Defter denetimi iki
tarafın da alış ve satış seviyelerini istiyor; kapanışa yakın düşük kapsama
tek başına ağ gecikmesi veya veri sağlayıcı kesintisi diye yorumlanamaz.
Önce bu ölçüm yolu düzeltilip yeni kaynak/sürümle ayrı dönem başlatılmalı;
kaçırılan kararlar sonradan gerçekleşmiş işlem gibi doldurulmamalı.
Bu raporda çalışan dondurulmuş deney değiştirilmedi.

**Gecikme karşılaştırması**

31 aynı kararın yeni HTTP fiyatları eşleşti; eksik çift yok. Hepsi ikincil
son 60 saniye kolunda. İlk karar gözlemci başlamadan önce olduğu için
bu eşleşmeye dahil değil. Fiyat alma medyanı ek beklemesiz **31 ms**,
250 ms beklemeli sürümde **278 ms**.

| Aynı eşleşmiş kararlar | Ek beklemesiz | 250 ms beklemeli | Hızlı sürüm farkı |
|---|---:|---:|---:|
| Rebound, dokuz sanal işlem | −$3,26431 | −$3,31884 | +$0,05453 |
| Favori kontrolü, 31 sanal işlem | +$9,48590 | +$9,07060 | +$0,41530 |

Bunlar HTTP defter fiyatlarıdır; gerçek emir kabulü veya dolum ölçümü değildir.
Bu örnekte daha hızlı fiyat almak rebound zararını gidermedi.

**Kapsam ve doğrulama**

Jev ve rebound dönemleri hiç örtüşmüyor. Jev ile ilk shadow'un ana kolunda
yalnız iki ortak geçerli nihai pencere var. Bu yüzden tablodaki mutlak
PnL'ler Jev/shadow üstünlüğünü gösteren aynı dönem yarışı sayılmaz.
Kararı bulunan ve kesime kadar kapanmış bütün işlemlerin sonucu alındı;
bu tablolarda sonucu bekleyen seçili işlem yok. Veri boşlukları sıfır getirili
gözlem olarak sunulmadı. Üç gün ve yeterli geçerli/seçili işlem ile ileri
doğrulama koşulları karşılanmadı.

Kayıtlı derinlik/miktar/ücretlerden maliyetler yeniden hesaplandı;
ücret yöntemi [resmî ücret açıklamasıyla](https://docs.polymarket.com/trading/fees)
kontrol edildi. 98 kamu piyasa kaydı, 17 dondurulmuş dosya hash'i,
18 kural/grubun bağımsız Decimal nakit akışı toplamı, zaman/kapsama/sonuç
eşleşmeleri doğrulandı. Öz-test, Ruff, compile ve gerçek kayıt üzerinde
analiz geçti; ikinci çalıştırmada sonuç dosyası birebir aynı kaldı.

- [Sayısal sonuçlar](../data/analysis/shadow_status_20260921_1016/score.json)
- [İşlem bazlı nakit akışları](../data/analysis/shadow_status_20260921_1016/trade_rows.json)
- [Süreç ve manifest kanıtı](../data/analysis/shadow_status_20260921_1016/runtime.json)
- [Bağımsız kontroller](../data/analysis/shadow_status_20260921_1016/verification.json)
- [Yeniden hesaplama aracı](../analiz/izleme/shadow_skor.py)

```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/analiz/izleme/shadow_skor.py" check
python3 "/home/taygun/Masaüstü/polymarket-bosona/analiz/izleme/shadow_skor.py" analyze
```
