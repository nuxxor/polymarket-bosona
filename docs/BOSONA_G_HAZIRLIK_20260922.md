# G1 hazırlığı — 22 Eylül 2026

G1, Londra'ya ayrı paket olarak yerleştirildi. Hazırlık boyunca gerçek emir gönderilmedi, yeni bütçe açılmadı. Finansal başlatma operatöre bırakıldı. Bu bir **30 dakika / 5 pay / $10 araştırma pilotu**; kârlılığı kanıtlanmış Bosona kopyası değil.

## Ne değişti?

G1, F'nin emir, dolum, iptal ve muhasebe altyapısını kullanıyor; F'nin yön tahminini kullanmıyor. Tahtada mevcut alışın bir sent altında pasif teklif veriyor. İki taraf da uygun olabilir. Bir taraf dolduğunda aynı yönde büyümeyi sınırlandırıp karşı tarafla açık miktarı azaltabiliyor. Kârlı çift kurma zorunluluğu yok: mevcut riski azaltan bir karşı alış toplamda zarar da kilitleyebilir.

Bu seçim, araştırmalardaki iki güçlü davranış bulgusunu sınar: pasif emir gerçekleşmeleri ve envantere göre risk azaltma. Bir sent mesafe, teklif yenileme aralığı ve zaman sınırları bizim sabit deney değerlerimizdir; Bosona'nın keşfedilmiş parametreleri değildir. RSI, favoriyi alma ve ucuz taraf seçme koşulları bu adayın giriş kuralı değil.

- Tek teklif 5 pay; açık/belirsiz emir rezervleri dahil net yön farkı en fazla 5 pay. Karşı alış, eksik miktarı aşamaz. 5 paylık borsa minimumunun altındaki kalıntı yukarı yuvarlanmaz; açık kalabilir.
- Yeni yön riski t240'tan itibaren açılmaz. Risk azaltan pasif teklif t290'a kadar mümkün. Ardından açık teklifler iptal edilir.
- Uygun teklif en iyi alış ile iki sent altı arasında korunur; dışına çıkarsa iptali teyit edilerek yenilenir. Taraf başına saniyede en fazla bir gönderim, piyasa başına en fazla 60 girişim, taraf başına toplam $10 maliyet/rezerv sınırı vardır.
- Gerçek tick API'den doğrulanır. Eski/ilerideki saat, snapshot olmadan delta, geriye giden kaynak zamanı, bozuk hesap mutabakatı ve bütçe kontrolü yeni emri engeller. Mutabakat/bütçe bozulması mevcut teklifin korunması yolunda da kontrol edilir.
- Tüm gönderimler post-only. Agresif satış/alış eklenmedi. Rebate tahmini kâra yazılmaz.

## Ölçümde kapatılan ve açık kalan konular

İki bağımsız tam kaydın 15 dakikalık gerçek testinde beş kamu bağlantı kopuşu görüldü. Kopuş-toparlanma aralığındaki 28/28 kontrol anında diğer kayıtta güncel iki taraflı defter vardı. Etkilenen kayıtta olmayan 66 LTP mesajı diğerinde korundu. Bunlar 66 ayrı ekonomik dolum diye sayılmadı. [Ham test ve sınırları](BOSONA_M7_CIFT_KAYIT_20260922.md).

G pilotu iki bağımsız kamu/özel hesap kaydını birlikte başlatır. Başlangıçta her ikisinde iki kanalın gerçek PONG yanıtını bekler. Kayıtçı süreç/dosya ilerlemesi ve emir telemetrisi ayrıca kontrol edilir. Bu kontrol, upstream olay tamlığının kanıtı değildir. G'nin işlem defteri kendi güncel snapshot/akışını kullanır; iki arşivden otomatik canlı defter birleştirme yapılmaz.

Kamu API mutabakatında aynı görünen gerçek satır çokluğu korunur. Sayfalar arasında aynı anahtar görünürse tekrar mı ayrı dolum mu olduğu tahmin edilmez; mutabakat durur. Kimliği/bakiyesi belirsiz emir rezervden düşürülmez. SDK hata metinleri yerine hata sınıfı kaydedilir.

**1013 kopuşunun kök nedeni, upstream tamlık ve kendi gerçek dolumlarımızla kuyruk kalibrasyonu hâlâ açık.** Fiyatın teklife değmesi dolum sayılmıyor; L2 miktar düşüşü iptal diye yazılmıyor. G'nin kuru koşusu yalnız teklif niyetini sınar, sanal dolum veya PnL üretmez. İlk gerçek G pilotunun amacı bu eksik emir/dolum kanıtını toplamak ve adayın gerçekleşen davranışını ölçmektir.

## Paket ve doğrulama

Son paket: `/home/ubuntu/polymarket-bosona-g-v2/bot`. Buradaki v2, G1 hazırlığında bulunan mutabakat/korunan teklif düzeltmesinin paket revizyonudur. Önceki `g` ve `g-v1` kuru koşuları ayrı korunur; başlatma komutu onları kullanmaz.

- Son `ab.py` SHA256: `d45ee6731e35b1b189770fe308f7ab8f0cb6814bfb18667f6aa7606c2c4bdd1a`.
- Politika SHA256: `fbac759df25cecf10ea01bbf9db9da5e07dd90f3b33e844125c51e434eaf2f61`.
- `G_RELEASE.json` 14 kaynak/protokol dosyasını sabitler. Değişiklik veya eksik manifest canlı başlangıcı reddeder.
- Yerel ve Londra testleri: politika, gerçek rezerv/risk hesabı, kısmi/tekrarlanan dolum, belirsiz iptal, STOP, çokluk mutabakatı, eski defter, bağlantı yenileme ve bozuk mutabakatta mevcut teklifi iptal etme.
- Salt okunur başlatma, süre/bütçe/tek kullanımlık aktivasyon, kaynak değişikliği, kayıtçı yokluğu ve gerçek SSH yerine sahte SSH ile başlatma komutu kontrol edildi. Lint ve derleme sonuçları `lanes/g/validation/local_final.json` içinde.
- Ayrı 45 saniyelik gerçek kayıtçı başlangıç kontrolü 4,41 saniyede hazır oldu; iki kayıtçı normal bitti, bitince sağlık kontrolü olumsuza döndü. Bu testte finansal işlem/özel dolum yoktu.
- Son kaynakla gerçek defterli 480,117 saniyelik KURU koşu: iki piyasa, 870 karar ve 120 teklif niyeti. Süre sonu normal, tüm kuru emirler kapalı. Kaydı `lanes/g/validation/runtime_final.json` ve arşivinde bulunur. İki piyasa, teklif mesafesi, 5 pay, zaman sınırı, normal kapanış ve sıfır ekonomik dolum ayrıca denetlenir.

Salt okunur son hesap kontrolünde 79 eski pencere ve 638 emir uzlaştırıldı: nihai yerel/public PnL **−$15,234894**, açık emir **0**, açık risk **0**. Önceki yerel −$15,334894'ün $0,10 düzeltmesi ayrı uzlaştırılmış kopyaya işlendi. Eski M4v2 kaynak, state ve bütçe dosyaları değiştirilmedi. G canlı başlarken bu kontrol tekrar yapılır; mevcut rapor sabah için geçerlilik garantisi yerine kullanılmaz.

## Operatör komutu

```bash
bash "/home/taygun/Masaüstü/polymarket-bosona/londra_g_baslat.sh"
```

Bu komut ilk kullanıldığında yeni $10 sınırını ve 30 dakikalık süreyi açar. Kontrol başarısızsa LIVE başlamaz. Komutun “başlatma istendi” yazması LIVE teyidi değildir; `/home/ubuntu/polymarket-bosona-g-v2/bot/console.log` içinde `mod=LIVE`, `lane=G`, kaynak hash'i ve `basladi` kontrol edilmelidir. Tekrar çalıştırma bütçe/süreyi sıfırlamaz. Eski hesabın PnL'si silinmez. Kuru state canlıya taşınmaz.

Durdurma:

```bash
ssh -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -i "/home/taygun/İndirilenler/polymarket-test-key2.pem" ubuntu@18.135.99.14 'touch /home/ubuntu/polymarket-bosona-g-v2/bot/STOP_G'
```

STOP yeni teklifleri kesip mevcut emirlerin normal iptal/mutabakat kapanışını başlatır. Piyasa pozisyonlarını otomatik satarak kapatmaz; mevcut tokenler sonuca taşınabilir. $10 sınırı, açık/belirsiz emirlerin kötü sonuçlarını da hesaba katan araştırma bütçesidir; yalnız kapanmış PnL sayacı değildir.

## Sonraki okuma

İlk pilotta net dolar/atanmış pencere (sıfır dolumlu pencereler dahil), net envanter yolu, kısmi dolumlar, parent emir başına gerçekleşme, iptal/ret ve veri eksikleri birlikte okunacak. Sadece daha çok işlem veya daha çok eşleşmiş çift başarı sayılmayacak. Anlamlı dolum yoksa sonuç “kârlı” değil, gerçekleşme yönünden yetersiz gözlem olacak. G'nin bütün sabit parametreleri sonuç görülmeden korunacak; yeni bütçe otomatik açılmayacak.


Tekrar çalıştırma (canlı başlatmaz):

```bash
"/home/taygun/Masaüstü/KararAtlas/base1/bin/python3" "/home/taygun/Masaüstü/polymarket-bosona/lanes/g/validation/check_release.py"
"/home/taygun/Masaüstü/KararAtlas/base1/bin/python3" "/home/taygun/Masaüstü/polymarket-bosona/lanes/g/validation/check_runtime.py"
```

Ham Londra kanıtı `lanes/g/validation/validation_final.tar` içinde; açılmış
kopyası `runtime_v2/`. `local_final.json`, `runtime_final.json`,
`telemetry_final_check.json` ve `startup_final.json` farklı kontrollerdir;
sahte SDK/dolum testi gerçek canlı sonuç olarak sunulmaz.
