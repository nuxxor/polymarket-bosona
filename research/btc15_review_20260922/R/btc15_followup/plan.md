# BTC15dk geç ekleme — devam görevi

Aday ve protocol.json SHA256 ile korunur; ana repo salt okunur. BTC5dk yalnız
muhasebe etkisi: Bosona tarihsel hesapları ve yerel kamu mutabakatı ayrı denetlenir.

- [x] Ham dilim çoklukları, taze activity/trades ve resmî sonuçla BTC5dk tutar farkı.
- [x] Adayı değiştirmeden ilk giriş/yön/zaman/55¢/olasılık/envanter kapı dökümü.
- [x] Kazanan/kaybeden geç eklemeleri fiyat (10¢), kalan süre (60sn), açık risk
      (0–50/50–100/100–200/200+ dolar) katmanlarında karşılaştır. Kesimler PnL
      sonucu görülmeden sabit. Aynı piyasa/saniye parçaları emir sayılmadan birleştirilir.
- [x] 600–870sn arasında 30sn karar ızgarası: o anda gözlenen envanter varsa
      sonraki30sn ekleme / karşı yön / gözlenen işlem yok kontrolü. Fiyat ve risk
      eşleştirme; aynı sözleşme/gün bağımlılığı; kazanç etiketleri özellik olamaz.
- [x] En fazla iki mekanik hipotez, eşik taraması yok. 13–17 keşif, 18–20 kronolojik
      kıyas. Açıklama performansı ve ekonomik avantaj açıkça ayrılır.
- [x] Ayrı yerel recorder: kamu BTC15dk iki taraf tam L2 REST snapshot, 1sn hedef,
      istek/alım/borsa zamanları, hatalar ve eksik aralıklar, resmî kontrat metadata.
      72 saat üst sınır, emir/cüzdan/kimlik yok; mevcut servisler değişmez.
- [x] Offline kontrol, hedefli lint, gerçek veri çalıştırması, aday hash kontrolü,
      kısa Türkçe rapor ve birebir tekrar komutları.

Gerçek tarihsel spread/derinlik bulunmadığı yerde fiyat örneği vekildir. Gözlenen
alım olmaması emir olmadığı anlamına gelmez. Yeni kaydın yeterli gün biriktirmesi
beklenen açık iş; bu oturumda 72 saatin tamamlandığı ileri sürülmez.

Eşleştirme kalite düzeltmesi: ilk kaba katmanlarda kazanan/kaybeden ortalama
risk farkı 15,19 dolardı; 200+ hücresi sınırsızdı. Eski sonuç coarse_* olarak
korundu. Ana kıyas için fiyat farkı<=3¢, süre<=30sn ve risk farkı<=25 dolar
sabit yakınlık koşulu eklendi. Bu PnL optimizasyonu/eşik taraması değil,
istenen benzer risk koşulunu gerçekten sağlamak için kalite kontrolüdür.

Son kontrol: fiyat kapıları ham işlem fiyatıyla, PnL usdcSize ile tutuldu.
74 dolumda nakit fiyat farkı var; nakit maliyetine tekrar varsayımsal ücret
eklememek için tanısal fiyat kapıları ham fiyatı kullanır. Son ana eşleşme
68 kazanan/kaybeden çifti; ilk nakit-fiyatlı kaba çıktı arşiv niteliğindedir.

## Sonuç ve açık ileri dönem
Tüm yerel kabul kontrolleri geçti. Aday değişmedi. BTC5 muhasebe farkı çıkarıldı,
68 yakın kazanan/kaybeden çifti ve 173 ekleme/kontrol çifti üretildi. İki modelin
kronolojik üstünlüğü gösterilemedi. 72 saatlik bağımsız kayıt başladı; kayıt
halen sürüyor; 72 saatlik veri/ekonomik başarı tamamlandı sayılmaz. Gözlem toplanınca
önce veri kapsamı ve masraflı uygulama sınanacak; eşik değişikliği veya shadow yok.

## 21 Eylül 18:00 UTC ara kontrol
Kullanıcı geçen yaklaşık üç saatin durumunu istedi. Ayrı status_20260921_1800/
kesitinde salt okunur süreç/hash, defter kapsamı ve yeni Bosona BTC15dk dolumları;
tam kapanmış / baştan eksik / açık piyasa ayrı. Aday, recorder ve diğer süreçler
aynı kalır. Kabul: kamu sonuç/çokluk muhasebesi, somut veri boşlukları, kısa rapor.

18:05 UTC kesiti tamamlandı:13.219çift snapshot/2kısa timeout;14tam kapalı
pencerede126Bosona dolumu/+165,630507USD;54geç ekleme/−254,167917USD.
15piyasada activity/tradesçokluk,Decimal/FIFO,hash,Ruff/syntax kontrolleri
geçti. Kanıt status_20260921_1800/OKUMA.md; süreç/aday değişmedi.
