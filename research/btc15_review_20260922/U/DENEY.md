# Tek sonraki deney: sonuçtan bağımsız parent, rol ve risk ölçümü

**Karar:** yeni işlem politikası için kanıt yetersiz. Sonraki çalışma, dolum parçalanmasının ve risk azaltan karşı alışın payını birbirinden ayıran sonlu bir ölçüm deneyidir. Emir, deploy veya sürekli süreç içermez. Eski ekonomik kabul kapısını geçmeyi amaçlayan bir backtest değildir.

## Önkayıt ve seçim

- Sabit gelecek aralık: **22 Eylül 2026 00:00 UTC dahil, 2 Ekim 2026 00:00 UTC hariç**, on tam gün. Tarihler veya eşikler sonuçlara göre uzatılmaz/değiştirilmez. Veri yetmezse UNDERPOWERED kalır.
- Her günün 96 resmî BTC15dk sözleşmesi paydada tutulur. Metadata ile 900sn süre ve Chainlink 60sn TWAP kuralı doğrulanır. Eksiksiz cüzdan aktivite dilimleri yoksa işlem yok etiketi konmaz: MISSING_DATA.
- Her gün işlemli piyasaları `sha256('btc15-parent-v1:'+slug)` artan sırasına koy; ilk dördü seç. PnL, kazanan yön, volume, likidite veya geçmiş bir model skoru seçim girdisi değildir. Bir gün dört işlemli piyasa yoksa başka günden tamamlama yapılmaz.
- Seçilen 40 piyasanın bütün TRADE/MERGE/REDEEM kayıtları, doğru dönem sözleşmesi/ABI'si ve receipt/block/log sırası alınır. Kısmi API cevabı ve sayfa sınırı eksiksiz diye işaretlenmez. SELL/SPLIT/CONVERSION görülürse mevcut BUY-only decoder sessizce devam etmez; o piyasa analizi desteklenene kadar eksiktir.
- Ham cevap, URL/istek/yerel alım zamanı, SHA ve seçim manifesti saklanır. Parent anahtarı doğru exchange ve orderHash'tir; aynı tx veya aynı miktar yeterli değildir. Görülen ilk fill, emir gönderim zamanı sayılmaz.

## Ölçümler, aday ve kontrol

**M1 — parçalanma:** Aynı veri üzerinde iki açıklamayı kıyasla: her API satırına ayrı eylem diyen mevcut etiket ve tek imzalı parent'ın envanter yolunu takip eden etiket. Geç aralık `600≤age<900` olarak sabit kalır. İlk saniye parçaları ayrıca ilk paket sayılır. Her geç-add satırı için parent'ın ilk görülme zamanı, daha önce dolmuş olup olmadığı, maker/taker rolü ve pay miktarı raporlanır. Sınırı aşan parent ayrıca gösterilir. Satır sayısı ve miktar ağırlıklı “önceden görülen aynı parent devamı” oranı ayrı ana çıktılardır.

**M2 — envanter yönetimi:** Parent'ın ilk dolumundan hemen önce gerçek Up/Down, MERGE/REDEEM sonrası net nakit, FIFO açık maliyeti ve iki sonuç ödeme vektörünü çıkar. Emir parçalarının her birini bu yolda tut; tek parent hem kapatma hem ters risk açabilir. Karşı alışın neti kapatan kısmı ile aşan kısmını ayır. FIFO çift maliyeti >1 olan kapatmalar için iki sonuç tabanı değişimini ve resmî sonuçta marjinal nakit katkısını birlikte raporla. “Ucuz çift” (`≤1`) ve yalnız tutma aynı başlangıç envanterindeki aritmetik kontrollerdir; sonuca göre kontrol seçilmez.

Gözlenen dolumsuz kontrol anları, seçilmiş piyasalarda `t=600,630,…,870`, önceden açık net ve önceki 5sn içinde dolum yok şartıyla çıkarılır. Gelecekteki karma dolum yüzünden geçmiş an atılmaz; sonraki 30sn etiketleri `add`, `karşı`, `karma`, `dolum yok`, `belirsiz` ayrılır. Dolum yok, emir yok değildir. Aynı gün/süre/fiyat/ön-riskte eşleştirme yalnız bağlam gerçekten o anda mevcutsa yapılır; kontrol bulunmazsa eksik kalır. Mevcut defter kaydı planlanan on günün tamamını kapsamıyor: **bu deney için kayıt süresi uzatılmadı; defter dışı günlere ask/queue/fill uydurulamaz.**

Gerçek boy, parent başına 5 pay ve parent başına 5 dolar nakit ölçeği ayrı verilir. Gerçekleşmiş tepe riskiyle ölçekleme yalnız sonradan duyarlılıktır. Aynı eldeki miktarda tutma/kapama karşılaştırması gerçek aktör yolu üstünde koşullu hesap olduğundan bağımsız işlem kuralı sayılmaz. Bosona dolumu veya sonradan görülen cüzdan bilgisi kendi botumuzun tetikleyicisi olmaz. Bu aşamada finansal aday ve sanal işlem yok; pozisyon bütçesi ayırmıyoruz.

## Yeterlilik, destek ve yanlışlanma

Ölçümün raporlanabilirlik kapısı: 10 tam gün, 40 piyasa, en az 100 doğrulanmış parent ve en az 50 geç aralıkta parent; seçili bütün piyasalarda API miktar/nakit çokluğunun %100 uzlaşması ve parent/rol kapsamının en az %95 olması. Bunlar davranış ölçüm eşikleridir; eski >=100 uygulanabilir giriş/>=50 eklemeli piyasa kapısının yerine geçmez. Eşiklerden biri eksikse UNDERPOWERED; kimlik veya nakit uzlaşmazsa ilgili piyasa MISSING_DATA olur, seçilmiş başka piyasayla değiştirilmez.

Oranlar piyasa ve gün düzeyinde ayrı kümelenmiş, sabit tohum `20260921` ile 4.000 tekrar aralıkla raporlanır; on günün sınırlılığı ve en iyi üç hariç sonuç ayrıca gösterilir. Aynı piyasa iki kolda kullanılıyorsa bağlı piyasa bileşenleri tek birimdir. Sonuç seçmek için farklı eşik/model taranmaz.

- M1'in **baskın** açıklama olması, miktar ağırlıklı geç-add devam payının hem piyasa hem gün %95 alt sınırının %50'yi aşmasıyla desteklenir. Her iki üst sınır %50'nin altındaysa baskınlık reddedilir; aradaysa belirsiz. Bu ölçü, ilk dolumundan çok önce yerleştirilmiş fakat henüz dolmamış emirleri saptayamaz; pasif stratejinin varlığını bütünüyle reddetmez.
- M2'nin sınırlı iddiası, pahalı karşı alışların neti kapatan kısmının daha kötü ödeme durumunu gerçekten iyileştirmesidir. Sayım, miktar ve aşan yeni risk birlikte verilir. Bu aritmetik destek tek başına özel politika tanımlamaz. “Yalnız ucuz çift” açıklaması, doğru kimlik/nakit ile tek bir >1 aktif kapatma tarafından yanlışlanabilir; mevcut örnekte zaten yanlışlanmıştır. Yeni örnek bunun yaygınlığını ölçer.
- Emir yerleştirme/iptal, hiç dolmayan emir ve sıra bilgisi yoksa M1 ile M2'nin özel kontrolcü olarak ayrımı **NOT IDENTIFIABLE** kalabilir. Bu sonucu kapatmak için yeni kârlılık hikâyesi yazılmaz.

Ekonomik kabul değişmez: >=10 tam UTC gün, >=100 gerçekleşebilir giriş, >=50 eklemeli piyasa, >=%95 karar/veri kapsamı, masraf sonrası mutlak ve eşit giriş/risk kontrolüne göre pozitif sonuç, piyasa/gün alt sınırları >0 ve en iyi üç hariç pozitiflik. Bu ölçüm deneyinin başarılı olması bu şartları sağlamaz.

## Çalıştırılabilir parça ve bugünkü sonuç

[next_selection.py](onchain/next_selection.py) yalnız seçim manifestini üretir. Eksik dönem verisinde çıkış kodu 2 verir. 13–20 Eylül gerçek verisindeki deneme 768 resmî slot/32 seçilmiş piyasa ile **UNDERPOWERED**; gelecekteki sabit dönem şu an **MISSING_DATA**. Sonuç/PnL ve giriş sırasını değiştirme, eksik gün ve eksik activity negatif kontrolleri [selection_checks.json](onchain/selection_checks.json) içinde.

```bash
PYTHONDONTWRITEBYTECODE=1 python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/onchain/next_selection.py --universe /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/results/universe.json --activity-dir /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/raw/activity --start 2026-09-13 --end 2026-09-21 --out /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/onchain/historical_selection_demo.json
```

Gelecek dönem ölçümü, ilgili on günün eksiksiz kamu kayıtları sağlanınca aynı seçiciye bu tarih aralığı verilerek yapılır. Bugünkü çalıştırılmış kanıt, 42 TRADE ve bir MERGE'in sonlu zincir denetimidir; gelecek deney yürütülmüş diye sunulmaz.
