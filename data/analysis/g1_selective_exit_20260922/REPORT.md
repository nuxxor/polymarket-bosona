# Bosona'nın seçici karşı alımları — 22 Eylül 2026

**Bulgumuz bir kapanış davranışı; bağımsız uygulanabilir karar kuralı değil.**
Bosona'nın ücret ödeyerek aldığı taraf, çoğu ölçülebilir örnekte mevcut açık
yönün tersi. Açık miktarı yaklaşık tamamen kapatması, taker işlemleri yalnız
“yeni yön tahmini” olarak yorumlamanın eksik olduğunu gösteriyor.

## Kapsam ve yöntem

Önceden incelenmiş R1 arşivindeki 137 piyasa/2.066 alış kullanıldı. Ana tablo,
her UTC gününden hash ile seçilen sekizer **gözlenen** piyasadan oluşan 64'lük
alt kümedir; bütün takvim veya temiz ileri doğrulama değildir. Geç eklemeye
göre seçilmiş diğer piyasalar ana tabloya karıştırılmadı.

Receipt ile doğrulanmış emir kimliğinin ilk dolduğu kamu saniyesi incelenir.
Aynı parent'ın sonraki parçaları yeni karar sayılmaz. Aynı saniyede farklı
parent veya taraflar varsa niyet sırası atanmaz. Belirsiz grubun bütün gerçek
dolumları sonraki envantere yine eklenir. Mikro-paylar tam sayı tutulur;
ufak artık pozisyonlar kayan nokta ile sıfırlanmaz. Canlı döneminde yalnız
BUY/MERGE olması kontrol edilir; merge net yönü değiştirmez.

305 parent'ın 262'si sınıflandırıldı; 43'ü sıra/zaman belirsizliği nedeniyle
ayrı tutuldu. Hiç dolmayan/iptal edilen teklifler bu veride yok. Bir emrin ilk
dolum saniyesi, gönderim saniyesi veya bütün emrin büyüklüğü değildir.
Rol aşağıda ilk gözlenen saniyelik gruba aittir; bütün ömrü için sabit rol
veya karşı alımın niyeti varsayılmadı.

## Somut ayrım

| İlk dolum grubunun rolü | Parent | Yeni açılış | Aynı yöne ekleme | Risk azaltma | Sıfırı aşıp tersine dönme |
|---|---:|---:|---:|---:|---:|
| Maker | 230 | 67 | 101 | 48 | 14 |
| Taker | 30 | 2 | 2 | **26** | 0 |
| Aynı parent'ta maker+taker | 2 | 0 | 0 | 2 | 0 |

Taker grubunda 26/30 parent, 22 ayrı piyasada risk azaltıyor. Bu ilk grupların
pay ağırlığıyla %78,34'ü risk azaltan miktar. Kapanan açık miktarın medyanı
**%99,921**; 26 örneğin 15'inde en az %99 kapanıyor. %99 burada yalnız betimleme
sınırı; keşfedilmiş Bosona parametresi veya önerilmiş bot kuralı değildir.

Belirsiz 43 parent'ın sekizi ilk grupta taker. Bu sekizinin hiçbiri veya tamamı
risk azaltıyor varsayıldığında taker parent oranı 26/38–34/38, yani %68,4–89,5
arasında kalır. Bu örneklem içi tanımlama sınırıdır, istatistiksel güven aralığı
veya tüm Bosona işlemlerine genelleme değildir.

Maker'ın risk azaltan veya tersine çeviren 62 ilk grubunda kapanma medyanı
%71,0. Daha küçük ilk maker dolumu, pasif emrin tüm miktarının küçük olduğunu
göstermez; parçalı dolum etkisi sürer. Bu yüzden tabloyu farklı niyetin tek
başına kesin kanıtı saymıyoruz.

## Hangi saniyede, hangi fiyatta?

26 taker azaltımında kamu dolum yaşı **24–286 saniye**, medyan152. Karşı tokenin
nakit/pay maliyeti **0,0425–0,9720**, medyan0,5772. Nakit maliyeti ücret içerir;
bu değerleri kotasyon fiyatı olarak sunmuyoruz. Tek bir geç-saniye veya yüksek
fiyat koşulu bu grubun tamamını açıklamıyor; alt politikalar olabilir.

Mevcut feature arşivi yalnız geç dolumları içeriyor. Book, spot, TWAP, referans
ve gözlenen WS zamanından önceki bağlamı birlikte sağlayan yalnız **6/26**
taker azaltımı var. Bunların üçünde spot alınan tarafı, üçünde TWAP alınan
tarafı destekliyor. Sıra/timestamp belirsizliği giderilmiş bir karar anı değil;
`exchange_age` alanı gözlenen WS saatinden geliyor. Bu altı örnekten genel
tetikleyici, eşik veya “TWAP işe yaramıyor” sonucu çıkarılamaz. Eski feature
dosyasındaki envanter/ekleme etiketleri kullanılmadı; envanter receipt
dolumlarından yeniden kuruldu. Sonuç kazananı aksiyon sınıfının girdisi değil.

## Risk azaltma ile kazanç ayrı sorular

Önceki R1'in ilk risk azaltımı testi aynı 64 piyasada32 geçerli,23 karşı
dolum yok,9 belirsiz olay bulmuştu. İlk azaltımı taker olan15 örneğin10'unda,
en ucuz uygun eski lotla bile çift maliyeti1'in üzerinde. Toplam yerel
taşıma/kapama farkı bu15 olayda+$273,91; bütün değerlendirilebilir55piyasada
+$165,37. En iyi üç çıkarılınca−$153,79; tarihsel gün bloklu aralık sıfırı
kesiyor. **Kapanış davranışı var; bizim uygulayınca para kazanacağımız
kanıtlanmış değil.** Bunlar eski sabit-giriş yerel hesabıdır; sonradan gelen
Bosona işlemleri alternatif portföylere zorla eklenmez. Rebate varsayımı yok.

Bugünkü farklı yollar da korunmalı:

- 14:00 TR: Bosona201.sn249Down@0,11; daha sonra karşı dolum yok;−$27,39.
- 13:35 TR: önceDown;114.sn makerUp,126.sn takerUp ile neredeyse düz.
  Karşı alımlar aynı pozisyonu taşımaya göre+$11,8406 katkı; toplam−$27,4278.
- 12:55 TR: Down'danUp'a dönüp sonraUp büyütme. Geç altı dolum tekparent.

Kaynak: ../g1_comparison_20260922/CASE.md ve doğrulanmış receipt dosyaları.
“Karşı dolum yok” hiçbir karşı emir verilmedi demek değildir.

## Kullanıcının son ekranı

20Up maliyet$8,50 +15Down maliyet$8,85 = toplam$17,35. Down sonuçlanırsa
ödeme$15, işlem sonucu−$2,35; Up kazanırsa+$2,65. Henüz sona ermemiş ekranda
anlık değerleme, sonuç ödemesinden farklı olabilir. Bu ekran tek başına
adverse selection veya yazı tura olduğunu ispatlamaz.

Yalnız ekonomik örnek: karşıDown0,99 iken5Down almak$4,95 harcar, iki sonuçta
ödemeyi20'ye eşitleyip−$2,30 kilitler; ücret hariç. Down kazanırsa önceki
−$2,35'e kıyasla yalnız5cent kurtarır; Up'a dönüşün+$2,65 fırsatını kaldırır.
Bu bir işlem önerisi veya o anda yürütülebilir fiyat doğrulaması değildir.
Dolayısıyla son anda eşitlemek geçmiş zararı silmez; kapanış seçimi ve zamanı
araştırmanın asıl konusudur.

## Sonraki araştırma sınırı

Canlıya yeni kapatma kuralı eklenmedi. Yeni RSI/tetikleyici taraması veya yeni
shadow açılmadı. Mevcut ileri 24slot kaydı sürüyor. Doğrulanmış taker karşı
alımlarının öncesindeki fiyat/net-envanter yolları ile benzer durumda açık
taşınan yollar karşılaştırılmalı; yalnız kaybedenler seçilmemeli. Erken
olayların eksik bağlamı sağlanmadan ortak kapanış koşulu bulunduğu söylenemez.
Bağımsız uygulama aşamasında aktörün sonradan görülen işlemi karar girdisi
olamaz; aynı fiyatın bize ulaşılabilirliği ayrıca sınanır.

Tekrar: `python3 analyze.py`. Dahili kontroller parçalı parent, aynı-saniye
belirsizliği, mikro-pay kalıntısı, tersine geçiş ve sonuç etiketinden
bağımsızlığı kapsıyor. Girdi/kod SHA'ları `results.json` içinde. Bu çalışma
R1'in doğrulanmış çıktısını kullanır;2.041receipt baştan decode edilmedi.
