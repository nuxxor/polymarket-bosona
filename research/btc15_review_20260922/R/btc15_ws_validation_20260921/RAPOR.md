# BTC15dk — yeni defter ve gerçekleşme kontrolü

21 Eylül UTC / 22 Eylül Türkiye. **İlk tam piyasanın kamu akışı kullanılabilir
çıktı. Kârlılık ve emir yürütme kalibrasyonu henüz doğrulanmadı.** Eski aday ve
çalışan kaynaklar korunarak, ayrı veri kesiti ve ağsız tekrar üretim hazırlandı.

## Sabit kapsam ve sonuç

Sonuca bakmadan seçilen pilotun ilk tam penceresi: **20:45–21:00 UTC**,
`btc-updown-15m-1790023500`. Resmî başlangıç/bitiş, 900sn süre, Chainlink TWAP60
kuralı ve iki token doğrulandı. Veri kesimi yerel alım saatiyle 21:02 UTC.
Başlangıç defterini korumak için aynı piyasanın 20:35 sonrasındaki ön kayıtları
da saklandı; pencere öncesi/sonrası işlemler pencerenin içine taşınmadı.

| Kontrol | Gerçek sonuç |
|---|---:|
| Saklanan defter/işlem olayı ve bağlantı kaydı | 288.975 |
| 15dk içindeki 1sn aralıklı defter kontrol noktası | **901/901 geçerli** |
| İki tokenin aynalı fiyat ve miktar uyumsuzluğu | 0 |
| Kesit içinde açık kopma, geçmişe giden veya gelecekteki defter saati | 0 |
| Kamu API'sindeki aktif işlem / tüm tarafların dolum kaydı | 932 / 2.609 |
| İndirilen ve nakit/token transferleri çözülen makbuz | **932/932** |
| Kaydedilmiş WS işlemlerinin zincirle eşleşmesi | **923/923**, 33.178,539061 pay |
| İkinci kamu RPC'siyle çapraz kontrol | 2/2 aynı |

923 WS mesajının **892'si resmî 15dk içinde**, 29'u öncesinde, 2'si sonrasında.
Pencere içindeki miktar 30.638,711674 pay. API'deki kalan 9 işlemin blokları
kayıt başlangıcından önce; bunlar 20:45–21:00 aralığında WS kaybı değildir.
Bu nedenle toplam WS sayısı ile tam piyasa tarihi aynı payda değildir.

Başlangıç kaydı, delta ve gerçek işlem kimliğiyle kontrol kapısı
`PASS_OBSERVED_FLOW_GATE`. Bu, bilinmeyen bütün işlemlerin matematiksel olarak
imkânsız olduğu veya kuyruk sırasının görüldüğü iddiası değildir.
[Hesap çıktısı](results/report.json), [gerçek maker akışı](results/flows.json).

## Yeni bulunan sayfalama sorunu

İlk `takerOnly=true` cevabında iki işlem ikinci sayfada tekrarlandı, iki başka
işlem eksikti. **Toplam satır sayısı yine 932 idi.** Yalnız toplamı kontrol etmek
bu hatayı yakalamıyor. Tekrarlananlar ilk sayfanın 498/499, ikinci sayfanın 0/1
indekslerindeydi. Eksiklerin blok saatleri 21:00:24 ve 21:00:40 UTC.
Bu desen sayfalar arasındaki sıralamanın/verinin değişmesiyle uyumlu; sunucunun
iç nedenini bilmiyoruz.

İlk dosya korundu. Yeni bir dosyaya alınan ikinci tam liste, 932 aktif işlemin
tamamında zincir miktarı ve nakit karşılığıyla uzlaştı. `takerOnly=false`
listesindeki 2.609 kayıt zaten uzlaşıyordu. Eşit satırları keyfî silmedim.
İlk ve teyit edilmiş farklar [aynı raporda](results/api_reconciliation.json).
Eski `tüm liste − taker liste` yaklaşımı bu kontrol olmadan yanlış maker akışı
üretebilir; bu piyasanın strateji PnL'sini değiştirdiği sonucu çıkarılmadı.

## Zaman ve fiyatı artık daha iyi ayırıyoruz

Yerel alım − WS sunucu zamanı: medyan **44ms**, aralık 34–1.054ms.
Blok zamanı − WS sunucu zamanı: medyan **2.197ms**, aralık 1.022–3.883ms.
Bu kesitte sabit bir blok gecikmesi kullanmak doğru değil; özel eşleşme ve
emir kabul saati yine doğrudan gözlenmiyor.

923 mesajın **90'ında** mesajdaki fiyat tam hacim ağırlıklı fiyat değildi;
zincirdeki gerçek maker fiyat/miktarlarına açılınca yuvarlama sınırları içinde
uzlaştı. Yuvarlanmış mesaj fiyatı tek bir gerçek maker seviyesi yapılmadı.
İki-token/mint ve karşı-token satış yolları aynı exchange log'u üzerinden
bir kez sayıldı. Resmî [market stream şeması](https://docs.polymarket.com/market-data/realtime-data)
fiyat, miktar, zaman ve transaction hash alanlarını tanımlar; emir sahibi/sırası
sağlamaz. Sahiplik ve seviyeler burada makbuzlardan çözüldü.

## Kısa kotasyon kontrolleri

Mevcut giriş/ekleme/son-kontrol zamanlarından 30/180/600/840sn'de iki tarafa
bid ve bid−1¢ için bağımsız 5-pay kontrolleri yapıldı: toplam 16 örnek.
250ms kabul ve 1.250ms etkili iptal varsayımı, sınırda 100ms pay bırakılması
önceki kısa M1 kontrol aracından gelir. Bunlar yeni ön kayıtlı strateji deneyi
değildir; sonuç bilinirken yapılan uygulama kontrolleridir. Parametre taraması yok.

- 15 koşullu teklif değerlendirilebildi. Görünen kuyruk arkasında toplam **5 pay**,
  kuyruk başında toplam **32 pay**; sırasıyla 1 ve 7 teklif dolum alıyor.
- t600 Up örneğinde 52¢ teklifte önümüzde 327 pay, ilgili sürede yalnız 10 pay
  akış var: kuyruk başı varsayımı 5 pay, kuyruk arkası 0 yazıyor.
- t840 Up 87¢ teklif, varsayılan kabul anında 87¢ ask'a ulaşıyor. Post-only
  olsaydı pasif olarak kabul edilemezdi. Önceki bid'e bakıp maker dolumu yazmak
  burada geçersiz olurdu. Gerçek emir gönderilmedi.

Fiyat karşılaştırması yuvarlanmış WS fiyatıyla değil, gerçek maker mikro-nakit
ve miktarıyla yapıldı. 5 pay klip ve hacim korunumu kontrol edildi.
[Tek tek kotasyon kayıtları](results/quote_probes.json).

**Bu 16 bağımsız teklifi bir portföyün kazancı diye toplamadım.** Kuyruk önü
ve arkası PnL sınırı değil. Ardından ayrı envanterli olay motoru çalıştırıldı;
aşağıdaki rakamlar o motorun koşullu sonuçlarıdır.

## Envanterli M1 / M2 karşılaştırması

[execution.py](execution.py) simüle edilen borsa envanterini botun öğrendiği
envanterden ayırır. Karar yalnız alınmış defter ve öğrenilmiş envanterle verilir;
Bosona dolumu tetikleyici değildir. Kabul, post-only ret, kısmi dolum, iptal ve
son durum bildirimi ayrı olaydır. İptal giderken dolan miktar korunur; daha geç
gelen aynı kümülatif bildirim yeniden sayılmaz. Bütçe, henüz öğrenilmemiş dolum
ve sonuçlanmamış emir için ayrılmış kalır.

Kurallar önceki kolları korur: 30–840sn, saniyelik karar, 5 pay klip,
10 net pay, 15$ toplam alış ve −5$ en kötü ödeme. M1 bid'e pasif teklif;
bid−1¢ aynı mekanizmanın fiyat kontrolü. M2 aynı bid kolunda net 10'a ulaşınca
pasifleri iptal edip, durum uzlaşınca en çok 5 pay taker adımlarıyla neti kapatmayı
dener. Her hedge de aynı bütçeye tabidir; yeni giriş ve kalan risk yeniden
açılabilir. Gerçek ask derinliği, karar anında sabitlenen ücretli fiyat limiti
ve tam-miktar kabul koşulu kullanıldı. Kalan envanter resmî ödemeye taşındı.

| Koşullu sonuç, tek piyasa | Görünen kuyruk arkası | Kuyruk önü |
|---|---:|---:|
| M1 bid | +0,10$ | 0,00$ |
| M1 bid−1¢ | −0,75$ | 0,00$ |
| M2 bid + tamamlama | +0,10$ | +5,02752$ |

M2 kuyruk-arkası yolunda hedge tetiklenmedi; M1 ile aynı kaldı. Kuyruk-önünde
iki hedge doldu, bir hedge fiyat nedeniyle reddedildi. +5,03$ sonucunda kapanışta
20 Up / 10 Down ve 14,97248$ maliyet var: **10 pay Up riski hâlâ açık**.
Aynı son portföyün diğer sonuç ödemesi −4,97248$ olurdu. Tamamlamanın genel
üstünlüğü veya risksiz getiri gösterilmedi.

Altı yolun tamamında gerçeklenen sanal envanter ile öğrenilmiş son envanter
uzlaştı; nakit, açık-emir rezervi, net pay ve en kötü ödeme sınırı ihlali **0**.
M1 bid kuyruk-arkasında 270 teklifin 26'sı varsayılan kabul anındaki fiyat
nedeniyle post-only reddi aldı. Bu ayrımı atlayan model başka bir yolu test eder.
[Olay, envanter ve varsayım kayıtları](results/execution.json).

**Bunlar kalibre edilmemiş senaryolardır.** 250ms kabul, 250ms etkili iptal ve
iptalden 250ms sonra bütün gerçekleşmeleri içeren durum cevabı varsayıldı.
Maker dolumu öğrenme için gözlenen kamu WS alım zamanı vekil; gerçek özel
bildirim gecikmesi değil. Taker öğrenmesi 250ms varsayımı. Emirlerimizin piyasayı
değiştirmediği, iptallerin kuyrukta bize kredi vermediği kabul edildi. Kuyruk önü
alternatifi de gerçek sıra kanıtı değildir. Kod bu sabit, gözlenmiş 1¢ tick
piyasasıyla sınırlı; tick değişirse destek eklenmeden çalışmaz. Eski P0 aday
değişmedi; bu tur onunla yeni ekonomik üstünlük karşılaştırması yapılmadı.

Bütün `economic_pnl` alanları null; tablo `conditional_pnl`. Politika bu veride
geliştirilip sınandığı için temiz kör test değildir. Sonraki ihtiyaç, aynı
kuralları daha fazla tam/gapsız pencereye taşımak, gecikme ve sıra varsayımlarını
ölçmek ve P0 kontrolünü aynı veri/uygulama şartlarında değerlendirmek.
Ekonomik kabul hâlâ 10 tam gün / 100 uygulanabilir giriş / 50 eklemeli piyasa,
%95 kapsam, masraf sonrası mutlak ve kontrol farkında pozitiflik, piyasa/gün
kümeli alt sınır >0, en iyi 3 hariç pozitiflik; 10/20 hariç duyarlılık da korunur.
Bu tek piyasa bu koşulları sağlamıyor. Mevcut aday ve 55¢ eşiği değişmedi.

İki saatlik pilot sürüyor. İlk kesitten sonra bir kopma/reconnect görüldü;
bu, incelenen kesitteki 0 kopmayı değiştirmez. Sonraki pencereler ayrıca
kontrol edilmeli; sürekli eksiksiz kayıt varmış gibi birleştirilemez.

## Tekrar üretim

```bash
/home/taygun/Masaüstü/KararAtlas/base1/bin/python3 -B /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_ws_validation_20260921/study.py repeat
```

Ağsız iki çalıştırmada **6 çıktı aynı SHA256**, **18 regresyon**, syntax ve Ruff
geçti. [Tekrar kanıtı](results/reproduction.json). Toplama komutları aynı
scriptte `fetch`, ardından `confirm`; mevcut önbelleği korur. Ham URL/alım
zamanları ve SHA kayıtları `raw/freeze.json`, `fetch.json`, `confirmation.json`
ile receipt/block zarflarında. Önceki Bitcoin5m araştırması yeniden yapılmadı;
yalnız mevcut doğrulanmış genel receipt/defter yardımcıları salt okunur kullanıldı.
