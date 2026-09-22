# BTC15 WS genişletme — 21 Eylül 21:50 UTC

Kullanıcı aynı kurallarla yeni pencereleri sınamayı onayladı. Ana çoklu piyasa
araştırmasının WS veri kapısı devamı. MAIN, eski aday/protokol, W/V sonuçları ve
çalışan kayıtlar salt okunur. Bu dizin ve kendi araştırma kök planı yazılabilir.
Emir, LIVE, shadow, süreç/ayar/bütçe değişimi veya ücretli servis yok.

Sonuçlar açılmadan sabit seçim: 21:00–21:15, 21:15–21:30, 21:30–21:45 UTC;
başlangıçlar 1790024400, 1790025300, 1790026200. Her pencere sonu+120sn alınmış
WS öneki. Önceki 20:45–21:00 ayrı önceki gözlem; yeni sonuçlarla karıştırılmaz.
Bosona katılımı/sonuç/kâr seçime girmez; kopan pencere MISSING_DATA olarak kalır.

1. [x] Eski dondurma/receipt/rol/defter araçlarını yeniden kullan. Tüm-katılımcı
   API çokluğu, gerçek maker nakit/tokenleri, WS ve resmi BTC15 sonuç/kurallar
   uzlaşsın. Eksik/tekrar/zaman ve tick değişimleri açık ayrılsın.
2. [x] Aynı M1 bid, M1 bid−1sent ve M2 bid+hedge kuralları: 5 pay klip,
   10 net, 15$ nakit, −5$ en kötü; t30..839 saniyelik karar, t840 iptal.
   Kuyruk arkası/önü senaryoları, PnL alt–üst sınırı değildir. Mevcut 250ms
   ve sabit 750ms gecikme; yavaş senaryoda öğrenmeye ek500ms. Kabul/iptal/
   uzlaşma varsayımları kalibrasyon sayılmaz. Karara göre tick bilgisi kullan.
3. [x] P0 donmuş karar kuralı aynı piyasa/defter/bütçede kontrol. Nedensel
   Chainlink bağlamı bulunamazsa null; yok veri sıfır işlem değildir. P0
   kaynağı veya olasılık/55sent/zaman eşikleri değişmez. Gelecek fiyatı karar
   girdisi yapma; uygulama reddi karar anında sabitlenen limitten türesin.
4. [x] Pencere bazlı sonuç/risk, kuyruk/gecikme duyarlılığı, kazanan/kaybeden
   ve en iyi pencere hariç sonuç. Yeni parametre/kâr taraması yok. Bir günlük
   birkaç pencere için ekonomik PnL null; genel on gün/100giriş/50ekleme açık.
5. [x] Anlamlı regresyon, hedefli Ruff/syntax, gerçek veri ve iki ağsız koşuda
   aynı çıktı hashleri; kaynak koruma ve kısa Türkçe rapor.

Veri/uygulama engelinde çalıştırılabilir en küçük eksik adımı belirt; eksik
kohortu veya başarısız kolu toplamdan sessizce çıkarma. Kamu WS sunucu saati
özel eşleşme/kabul saati, görünen defter gerçek kuyruk sahipliği değildir.

## Tamamlanan sonlu karşılaştırma

1.759 receipt / 1.757 WS mesajı uzlaştı; 6 ikinci-RPC teyidi. İlk pencere
kopma nedeniyle eksik olarak korundu. İkinci penceredeki eski bağlantıdan
devreden saat uyarısı, başlangıç öncesi son tam çift görüntüden başlatmayla
ayrıldı; ham ilk rapor korundu. Pencere içindeki bir aynalama uyuşmazlığı
(900/901 uygun) raporda; eski %95 veri kapısı değiştirilmedi. Son pencere
901/901. Tick olayları karar/kabul zamanında işlendi. Eski bağımsız 16 kısa
kotasyon tanısı kapsam dışı kaldı; tek- envanterli tam politika karşılaştırıldı.

İki uygun pencerede 24 M1/M2 senaryosu: 21 koşullu sonuç, 3 saat-eşitliği
belirsizliği; para/risk ihlali yok. 250ms/arkada M1 ve M2 −1,84033524$,
bid−1sent −4,45$. P0 2/2 geçerli giriş bağlamında filtrelenerek sıfır dolum;
veri eksikliğinin sıfır işlem sayılması değil. 36/36 planlı Chainlink bağlamı
var. Tüm ekonomikPnL alanları null. Üç atanmış piyasanın tam toplamı yok.

M2 için bir karşı örnek: t46, 14,50$ harcandıktan sonra 3,084$ hedge
gerekiyor; nakit üst sınırı reddediyor. Eşik/bütçe değiştirerek giderilmedi.
Bosona uygun iki piyasada sırasıyla0 ve2maker dolum/-22$; aynı küçük risk
kollarına ham dolar üstünlüğü kıyası yapılmadı. Ekonomik avantaj kanıtı yok.

16 kontrol, hedefli Ruff/syntax, iki ağsız koşuda 21 aynı-hashli çıktı geçti.
`RAPOR.md`, `results/reproduction.json`, `results/runtime_check.json` kanıt.
Eski aday/protokol, W/V kaynakları ve sonuçları hash ile korundu. Ayrı WS
pilotu ve eski REST kaydı kontrolde güncel/çalışıyor; süre ve kaynak aynı.
Özel yürütme gecikmesi, gerçek kuyruk konumu ve on günlük kabul hâlâ açık.
