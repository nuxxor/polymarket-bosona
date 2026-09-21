# İki shadow ve aynı dönemde Bosona — 21 Eylül 2026

**Mevcut sonuçlar, Bosona'nın karar akışına yaklaştığımızı henüz göstermiyor.**
İlk shadow'un ana kolunda sade favori küçük artıda, iki ek filtre ekside.
Yeni adayın ölçülebilen ikincil kolu ekside; asıl son 20 saniye testi bilinen
mum yenileme hatası nedeniyle ölçülemedi. Bosona aynı dönemde kâr etmiş,
ancak bunu bizim sabit zamanda tek alım yapan kurallarımızla açıklayamıyoruz.

**Kesim ve kapsam**

Bütün saatler Türkiye saati. Kesim **21 Eylül 15:00 / 12:00 UTC**.
İlk shadow: 02:20–15:00, **12 saat 40 dakika / 152 atanmış BTC5m penceresi**.
Yeni shadow: 03:50–15:00, **11 saat 10 dakika / 134 pencere**.
Bu iki başlangıç birbirine eşitlenmedi. Jev bu incelemenin dışında.
Çalışan kaynaklar, süreçler, süreler ve stratejiler değiştirilmedi.

Shadow sonuçları beş paylık, karar sonrası satış tekliflerinden ve taker
ücretinden hesaplanan **sanal PnL**. Bosona sonuçları kamu dolumları ve
API `usdcSize` maliyetiyle resmî sonuç ödemesinin farkı. İade ve sabit giderler
dahil değil; bütün cüzdanın bu saatlerdeki değer değişimi değil.
Gerçek dolumla sanal alım aynı uygulama başarısı ölçüsü sayılmamalı.

Bosona kohortu, ilgili shadow başladıktan sonra **başlayıp kesime kadar
biten sözleşmeler**. Önceden bu sözleşmelere yapılan alımları kaçırmamak için
üç günlük önceki aktivite de okundu; oluşturulma tarihleri bu kapsam içinde.
Kamu dolum zamanı emir gönderme zamanı değildir. Aynı saniyedeki karşıt
dolumların sırası bir BTC5m penceresinde belirsiz; FIFO dağılımı özel niyetin
kanıtı olarak kullanılmadı.

**Shadow performansı**

| Zaman / kural | Kazanan / sanal işlem | Ücret sonrası PnL |
|---|---:|---:|
| İlk shadow, **son 60 sn / ana: favori** | **40 / 46** | **+$2,43761** |
| İlk shadow, son 60 sn: BTC uyumlu favori | 33 / 38 | −$3,44569 |
| İlk shadow, son 60 sn: daha sıkı uzaklık filtresi | 23 / 27 | −$7,93189 |
| İlk shadow, son 90 sn / ikincil: favori | 74 / 86 | −$5,63125 |
| İlk shadow, son 90 sn: BTC uyumlu favori | 67 / 75 | −$2,24575 |
| İlk shadow, son 90 sn: sıkı filtre | 41 / 45 | −$7,56453 |
| İlk shadow, son 30 sn / ikincil: favori | 15 / 15 | +$7,12001 |
| İlk shadow, son 30 sn: BTC uyumlu favori | 9 / 9 | +$3,76829 |
| İlk shadow, son 30 sn: sıkı filtre | 1 / 1 | +$0,23337 |
| Yeni shadow, son 60 sn / ikincil: ucuz tarafta toparlanma | 1 / 10 | **−$5,95631** |
| Yeni shadow, aynı 38 uygun pencerede favori kontrolü | 34 / 38 | +$7,09882 |
| Yeni shadow, son 30 sn ve **son 20 sn / ana** | Geçerli karar yok | **Ölçülemedi** |

Önceki 13:15 kesimine göre ana favori +$6,63'ten +$2,44'e geriledi.
Uyum filtresi +$4,63'ten −$3,45'e, sıkı filtre −$3,35'ten −$7,93'e,
yeni adayın ikincil kolu −$3,32'den −$5,96'ya indi.
Ek filtrelerin bu dönemde toplam dolara olumlu katkısı yok.

Ana favoride 152 pencerenin **46'sı ölçülebilir**; 81 defter eksiği,
23 eski fiyat ve iki başlangıç referansı eksiği var. Uyum/sıkı filtrelerin
bu 46 pencere içindeki işlemsiz sekiz/19 penceresi veri eksiğinden ayrıdır.
Son 30 saniyede yalnız 15 pencere ölçülebilir; 15/15 isabeti daha iyi bir
strateji bulundu diye sunamayız. Ana favorinin en büyük birikimli düşüşü
$6,10840; en iyi üç işlem çıkarılırsa sonuç −$3,35972.

Yeni adayın son 60 saniyesinde **38 uygun pencere**, 10 işlem, 28 sinyalsiz
pencere var. Diğer 96 pencere veri eksiği. Ana son 20 saniyede 123 defter
eksiği + 11 eski bağlam reddi var. Kendi hazırlık döngümüzdeki mum yenileme
hatası önceki raporda yeniden üretilmişti; bu tur düzeltilmedi. 134 pencere
geçmiş olması 134 geçerli ana test anlamına gelmiyor.

**Bosona'nın aynı dönemdeki görünür sonucu**

İlk shadow döneminde resmî sonucu doğrulanmış **322 Up/Down piyasasının
toplam işlem sonucu +$2.053,44207**. Bunların 89'u BTC5m.

| Piyasa | İşlemli, sonucu doğrulanmış pencere | Bosona işlem PnL |
|---|---:|---:|
| BTC 5dk | 89 | **+$984,65532** |
| ETH 5dk | 68 | +$354,51367 |
| SOL 5dk | 41 | +$100,30806 |
| BTC saatlik | 11 | +$314,47856 |
| ETH saatlik | 9 | +$95,15815 |
| SOL saatlik | 5 | +$17,20431 |
| Diğer süreler/varlıklar | 99 | +$187,12401 |

Yeni shadow'un daha geç başlangıcından itibaren toplam 274 kapanmış piyasa
+$1.427,09301; bunun BTC5m kısmı **78 pencere / 463 dolum / +$805,20634**.

Veri kesitinde resmî sonucu henüz doğrulanmamış üç saatlik piyasa ayrı tutuldu.
Dönemden önce başlamış sözleşmelerde bu saatler içinde 70 alış kaydı
($1.786,757132 maliyet) var; bunların 63'ü hâlâ açık günlük BTC/ETH/SOL
sözleşmelerinde. Bu devreden piyasalar yeni başlangıç kohortunun PnL'sine
katılmadı. Dolayısıyla +$2.053,44 tam hesap geliri değildir.

Bu saatlerde **$228,15 maker + $54,0014 taker iadesi** de görünmüş.
Hangi günün/piyasanın işlemlerine ait olduğu bu karşılaştırmada
eşleştirilmediğinden kohort kârına eklenmedi. MERGE ve REDEEM ödemeleri
zaten hesaplanan sonuç değerinin üzerine ikinci kez kâr yazılmadı.

BTC5m'de **535 dolum / 38.965,62 pay**, 44 pozitif ve 45 negatif pencere var.
En iyi üç pencere +$1.077,20349; bunlar çıkarıldığında kalan **−$92,54818**.
Her pencerenin bütün dolumları orantılı olarak toplam beş paya indirildiğinde
toplam **+$0,76805**. Bu bir muhasebe ölçeklemesidir; aynı risk bütçesinde
gerçekleştirilebilir bot sonucu veya optimal miktar seçiminin kanıtı değil.
Ancak ham $985'i sadece daha doğru yön tahminiyle açıklamak yetersiz kalıyor;
işlemlerin dağılımı ve miktarı sonucu ciddi biçimde etkiliyor.

**Ne kadar benzer hareket ettik?**

| Gözlenen davranış | Bosona BTC5m | Bizim ana shadow kararı |
|---|---|---|
| İlk alış zamanı, medyan | Pencerenin 90. saniyesi | 240. saniye civarı |
| İlk alış fiyatı, medyan; kamu nakit maliyeti/pay | 42¢ | Favori kolunda ücret dahil 90,16¢ |
| Aynı pencerede iki taraftan da alış | 44 / 89, **%49,4** | Yok; tek yönde beş pay |
| Pencere içinde ekleme / karşı tarafı tamamlama | Var | Yok |
| Boy | Dolum ve pencereye göre değişiyor | Her seçilen işlem beş pay |

Bu satırlar kendi gözlenen örneklemlerinin betimlemesidir; ilk shadow'un
ölçemediği 106 pencereyi Bosona'yla eşleştirilmiş karar gibi göstermiyoruz.
Gölgedeki hipotezler tüm Bosona pozisyon akışının kopyası olarak uygulanmadı.

**Aynı piyasa ve benzer zaman kontrolü:** shadow kararının ±15 saniyesindeki
Bosona dolumları toplandı; daha fazla pay alınan yön karşılaştırıldı.
İki taraf da alınmışsa bu ayrıca kaydedildi. Bu, gizli emir kararını değil
yakın zamanlı görünür alımları ölçer.

| Kol | Shadow işlemi | Bosona'nın da işlem yaptığı ortak piyasa | ±15 sn alım olan pencere | Aynı ağırlıklı yön |
|---|---:|---:|---:|---:|
| Favori, ana son 60 sn | 46 | 32 | 16 | **8 / 16** |
| BTC uyumlu favori | 38 | 27 | 14 | 7 / 14 |
| Sıkı filtre | 27 | 19 | 8 | 3 / 8 |
| Rebound, ikincil son 60 sn | 10 | 7 | 5 | **2 / 5** |

±5 sn kontrolünde favori 2/5, rebound 0/3; ±30 sn'de 11/22 ve 3/6.
Paydalar küçük; bu oranlardan güvenilir bir “kopyalama başarı yüzdesi” çıkmaz.
Ana rebound t280 için karşılaştırma yok, sıfır benzerlik skoru yazılmadı.
Karşılaştırılabilen t240 anlarında favori shadow Bosona'nın açıkta taşıdığı
yönle 8/28, rebound 2/6 kez aynı tarafta. Karşı yönden alım kimi zaman
yeni tahmin değil, eski pozisyonun tamamlanması olabilir.

Ortak piyasalarda, Bosona'nın her piyasadaki bütün alımlarını toplam beş
paya orantıladığımızda:

| Aynı pencereler | Shadow sanal PnL | Bosona'nın beş toplam paya ölçeklenen sonucu |
|---|---:|---:|
| Favori kolunun 32 ortak penceresi | +$0,81094 | +$2,87909 |
| Rebound kolunun yedi ortak penceresi | −$4,11772 | +$5,23303 |

Bu ikinci sütun onun gözlenen dolumlarına koşullu bir karşılaştırmadır;
bizim aynı fiyatlardan dolabileceğimizi veya sermaye/riskin eşit olduğunu
kanıtlamaz. Bosona'nın gerçek miktarlı sonuçları bu iki kümede sırasıyla
+$634,96720 ve +$172,76090.

**Somut örnek: 14:50–14:55 BTC5m**

Bosona önce 156,526266 Down'ı yaklaşık 33¢'ten aldı. Kamu zamanına göre
t240'ta 156,52 Up'ı 30¢'ten alarak neredeyse tamamını eşleştirdi.
Sonra yaklaşık 29,42 Up daha aldı. Sonuç Up; toplam **+$67,08189**.
FIFO dağılımında yaklaşık +$55,61 eşleşmiş kısım, +$11,47 açık kalan Up.
Bu dağılım karar niyetinin kanıtı değildir.

Bizim rebound shadow o pencerenin t240 kararında **yeni Down** seçti;
karar sonrası sanal alımın ücretli maliyeti $2,63747, sonucu **−$2,63747**.
Başlangıçta yönler aynı görünse de işlemin görevi farklı: onun sonraki Up
alımı önceki Down'ı tamamlıyor; bizim Down alımımız tek başına yeni risk.
Kamu saniyesiyle gerçek emir gönderme anı aynı kabul edilmedi.

**Eski son 20 saniye hipotezi yeni dönemde ne yaptı?**

Son 100 saniyedeki aynı açık yöne ekleme ilk shadow döneminde +$95,81346;
yeni shadow başladıktan sonraki alt dönemde −$151,49539. Son 60 saniyedeki
eklemeler sırasıyla −$224,30864 ve −$356,35299.
Son 20 saniye eklemeleri +$73,55380 ama **yalnız bir piyasada on dolum**.
Alış fiyatları 88–91¢; eski ucuz-taraf toparlanma adayını genel açıklama
saymayı desteklemiyor. Bu alımların tam özel emir karar anındaki defter/RSI
koşulları kamu dolum fiyatından çıkarılamaz.

BTC5m toplamının FIFO muhasebe ayrımı +$119,86067 eşleşmiş kısım,
+$864,79465 açık kalan kısım. Dolayısıyla bütün kârı “ucuza çift kurma”ya
da bağlayamayız. Pencere seçimi, miktar, erken maliyet ve sonraki ekleme/
tamamlama kararlarının birlikte değerlendirilmesi gerekiyor.

**Bir sonraki adım:** önce son 20 saniye ölçüm yolunu düzeltip ayrı kaynak
sürümüyle yeniden veri biriktirmek; sonra ilk alım, aynı yöne ekleme ve
karşı tarafı tamamlama kararlarını mevcut miktar/maliyetle birlikte sınamak.
Sadece “favoriyi al” veya “ucuz tarafta dönüş ara” kuralı mevcut görünür
Bosona akışını açıklamıyor. Bu sonuçlardan canlı boy büyütme gerekçesi çıkmadı.

**Doğrulama ve tekrar üretim**

Tam sayfalı aktivite; ilk 321 eski kayıt ayrıca taze sorguyla eşleşti.
89 BTC5m piyasanın tamamı ve diğer gruplardaki kazanç/kayıp uçları dahil
**120 piyasa**, bağımsız `/trades` API'siyle kimlik/çokluk/miktar/brüt PnL
bakımından eşleşti. 322 piyasada MERGE/REDEEM ödeme sınırları kontrol edildi.
Sekiz Londra dosyasının hash'i doğrulandı. Ücret ve derinlik hesabı,
FIFO toplamları, eşleme toleransı, eşit pay ölçeği, eksik veri ayrımı,
öz-test/Ruff/compile ve gerçek kayıt analizi geçti.

Kaynak alanları: [Polymarket activity](https://docs.polymarket.com/api-reference/core/get-user-activity),
[Polymarket trades](https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets).
Emir iptalleri, gerçekleşmeyen teklifler, özel hedef envanter ve gerçek
emir zamanları bu kamu dolumlarından gözlenmiyor.

- [Sayısal rapor](../data/analysis/shadow_bosona_20260921_1200/report.json)
- [Bosona pencere muhasebesi](../data/analysis/shadow_bosona_20260921_1200/windows.json)
- [Dolum sırası ve envanter](../data/analysis/shadow_bosona_20260921_1200/fills.json)
- [Bağımsız API doğrulaması](../data/analysis/shadow_bosona_20260921_1200/validation.json)
- [Yeniden üretim kodu](../analiz/izleme/shadow_bosona.py)

```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/analiz/izleme/shadow_bosona.py" check
python3 "/home/taygun/Masaüstü/polymarket-bosona/analiz/izleme/shadow_bosona.py" analyze
python3 "/home/taygun/Masaüstü/polymarket-bosona/analiz/izleme/shadow_bosona.py" validate
```
