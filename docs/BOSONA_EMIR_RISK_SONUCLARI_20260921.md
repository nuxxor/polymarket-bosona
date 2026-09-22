# Bosona BTC5m: emir kimliği ve risk azaltımı sonucu

21 Eylül 2026. Mod: sonlu kamu-verisi araştırması; gerçek veya sanal emir gönderilmedi.

**Karar:** Maker ağırlığı ve dolumların aynı emre ait parçalar olması artık yalnız ücret izinden çıkarılmış tahminler değil; bu örneklemde zincir olaylarıyla doğrulandı. Zarar kilitleyen karşı alımlar da yaygın bir davranış. Ancak bunları bağımsız seçen ve para kazandıran karar kuralı henüz çıkmadı. Eski shadow'lar kapalı; yerlerine varsayımlı bir maker kâr simülasyonu başlatılmadı.

## 1. Evren, kaynak ve doğrulama

Sonuçlara bakılmadan sabitlenen grup: önceki 1.842 gözlenen BTC5m piyasasının her UTC gününden SHA256 sırasıyla sekiz piyasa; 13–20 Eylül için toplam **64**. Bu seçim geçmiş PnL'ye göre yapılmadı, fakat önceden araştırılmış tarihler kullanıldı. Temiz ileri doğrulama değildir; 1.842 işlemli/gözlenen piyasa evreni de 2.286 takvim slotunun tamamı değildir.

Önceden incelenen son-20-saniye ekleme grubunun **66** piyasası ayrı tanısal grup; **14** bilinen örnek ve çokluk kontrolü üçüncü grup. Gruplar örtüşür; toplamları toplanmaz. Birleşim:

- **137 piyasa; 2.066 BUY kaydı; 2.041 transaction; 96.059,619427 pay.**
- 137 piyasanın tam public activity sayfaları yeniden alındı; BUY çokluğu tarihsel ham kayıtlarla birebir aynı.
- 2.041 receipt'in tamamı çözüldü. **2.066/2.066 kayıt ve payların %100'ü** eşlendi; her transaction'ın gerçek nakit ve CTF token transferleri exchange dolumlarıyla uzlaştı.
- API nakdi için en çok 10 mikro-dolar yuvarlama toleransı; zincir transferleri–exchange hesabında tam tamsayı eşitliği.
- Her günden bir transaction iki ayrı Polygon RPC üzerinden doğrulandı: **8/8 aynı**.
- İlk turdaki 12 HTTP 429 saklandı; sınırlı tekrar ve yavaşlatmayla tamamlandı. Son toplamada hata yok.
- Ham aynı-görünümlü gerçek dolumlar korunuyor. Transaction yalnız receipt'i bir kez indirmek için tekilleştiriliyor; işlem satırları silinmiyor.

**Muhasebe sınırı:** BUY nakdi/tokeni zincir transferleriyle doğrulandı. MERGE/REDEEM bu aşamada public activity üzerinden kontrol edildi; bu olayların bütün receipt'leri ayrıca çözülmedi. Başlangıç envanteri, condition'ın tam public geçmişinde sıfır varsayımıdır; harici transfer yokluğu zincir bakiyesiyle kanıtlanmış değildir. Beş piyasadaki küçük kaybeden-token artıkları korundu; kazanç sayılmadı.

Veri manifesti ve kaynak hash'leri: `data/analysis/btc5m_parent_research_20260921/`. API ve zincir kayıtları hesapları yeniden üretmek için saklandı.

## 2. Maker ve emir parçalanması

| Ölçü | 64 piyasalık seçim | Önceki geç-ekleme grubunun 66 piyasası |
|---|---:|---:|
| BUY / exchange dolumu | 629 | 1.352 |
| Ayrı actor orderHash | **305** | **644** |
| Birden fazla dolumu olan emir | 131 | 293 |
| Hem maker hem taker dolumu olan aynı emir | 6 | 24 |
| Maker pay oranı | **%86,57** | **%81,39** |
| Maker dolum-kayıt oranı | **%93,00** | **%92,46** |

64 piyasada maker pay oranının tarihsel gün-blok aralığı %80,34–92,93. Bu, küçük ve geçmişte incelenmiş sekiz günlük örneklemin tanısal aralığıdır; gelecekteki oran garantisi değildir.

Rol, yalnız `OrderFilled.maker` alanından veya sıfır ücretten atanmadı. İlgili `OrdersMatched` aktif emir kimliğiyle birleştirildi; miktar, yön, karşı taraf, nakit ve token transferleri kontrol edildi. Şema kaynağı: [resmî V2 arayüzü](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/interfaces/ITrading.sol).

**En değerli düzeltme:** Son 20 saniyedeki eski “ekleme” grubunun **271 kaydı, 120 farklı emre** ait. Her kaydı yeni bir yön/ekleme kararı sayamayız.

Bu 271 kaydın her biri tekil tx + log_index ile eşlendi. Saat sırasına hiçbir varsayım koymadan, aynı emrin ilk dolumu dışındaki devam parçalarının:

- kayıt sayısı **151–165**, yani **%55,72–60,89**;
- miktarı **2.473,523118–6.297,035281 pay**, toplam 11.889,227392 payın **%20,80–52,96**'sı

arasında kalıyor. Her emrin en çok bir ilk dolumu olabilir; aynı saniyedeki büyük/küçük parçanın hangisinin önce geldiğini bilinmeyen bıraktığımız için miktar aralığı geniş.

Dolayısıyla **kayıtların çoğu yeni emir değil** diyebiliriz. **Payların çoğu eski emrin devamı** diyemeyiz. Bu ayrım, kayıt başına beş payla yapılan eski normalizasyonun niçin yanıltıcı olabileceğini somutlaştırıyor.

Ek zaman teşhisi: 51 satırın aynı parent'ında daha eski kamu saniyesi var; 156 satırda yalnız aynı saniyede başka parça görüyoruz. Bunlar emir gönderim zamanı değildir. Zincir settlement sırası da CLOB gerçekleşme sırasının yerine geçirilmedi. İptal, ilk emir gönderimi, dolmayan miktar ve kuyruktaki yer hâlâ görünmüyor. 249 pay / 5 ms / 0,75 saniye gibi kesin Bosona parametreleri bu çalışmadan çıkmadı.

## 3. İlk karşı alım: kâr kilidi mi, yön riskini azaltma mı?

Her piyasada ilk risk azaltan public-saniye grubuna geldik. Tek bir parent'a güvenilir biçimde atanabiliyorsa, azaltılan miktar için aynı mevcut pozisyondan iki yerel sonuç karşılaştırıldı:

- mevcut tarafı sonuca kadar taşımak;
- aynı miktarı gözlenen karşı alımla eşlemek.

İki hesaba sonraki Bosona işlemleri eklenmedi. Tek emrin o saniyedeki birkaç parçası birlikte ele alındı; gelecekteki bütün emir ömrü kullanılmadı. Ters tarafa taşan, farklı fiyatlı parçaların azaltıcı kısmı belirsizse sonuç null bırakıldı.

`yerel_fark = q × (1 − karşı_alım_nakit_fiyatı − eldeki_tarafın_sonuç_ödemesi)`

Eski maliyet toplam piyasa PnL'sinde duruyor; bu aynı-girişli farkta birbirini götürüyor. Sonuç ödemesi yalnız değerlendirme etiketi.

| Ölçü | 64 piyasalık seçim | 66 geç-ekleme piyasası |
|---|---:|---:|
| Ayrılabilen ilk karşı-alım olayı | 32 | 56 |
| Karşı alım olmayan; yerel katkısı sıfır | 23 | 5 |
| Sıra / miktar / kapanış saati belirsiz | **9** | **5** |
| Hesaplanabilen pencere sayısı | **55/64** | **61/66** |
| Yerel katkı toplamı | **+165,37 $** | **−736,36 $** |
| Hesaplanabilen pencere başına | +3,01 $ | −12,07 $ |
| En iyi üç çıkarılınca | **−153,79 $** | **−1.139,47 $** |
| Tarihsel gün-blok %95 toplam aralığı | −208,58 … +512,82 $ | −1.740,89 … +201,15 $ |

**Bunlar bizim botun kazanabileceği para değil.** Gerçek Bosona miktarlarıyla, onun seçtiği olayda yapılan yerel yönetim hesabı. İki grup da ortalama pozitif yönetim katkısını güvenilir biçimde doğrulamıyor. Belirsiz piyasalar sıfır sayılmadı; ekonomik karşılaştırmanın kapsamı %95'e ulaşmadığı için tam teyit kapısı geçilmiş sayılmıyor. En iyi üçü çıkarmak duyarlılık göstergesi; birincil toplamdan bu kazançlar silinmedi.

64 piyasada, ayrılan 32 olayın **15'inde** en ucuz uygun eski lotları seçsek bile eski maliyet + karşı alım **1 doların üzerinde**. Bu olaylar ilk karşı alımlarda kapatılan payın **%46,07'sini** oluşturuyor. Tanısal geç-ekleme grubunda 56 olayın 25'i, miktarın %52,70'i bu durumda.

Bu, katı 0,98 kârlı-çift kuralının Bosona'nın genel politikası olmadığına güçlü karşı kanıt. Ama 0,98'i bizim botta kaldırmanın getirisini kanıtlamıyor.

Rol ayrımı da bilgi veriyor: 64 piyasadaki ilk karşı alımların 16'sı maker, 15'i taker, biri karma. >1 maliyetli 15 kapanışın 10'u taker. Genel akış çoğunlukla maker olsa da pozisyon azaltımında aktif alım ayrı bir bileşen olabilir. Rol başına yerel katkının işareti gruplar arasında değişiyor; buradan “taker kapatmayı aç, kâr gelir” kuralı seçilmedi.

## 4. Uygulanan karar ve sıradaki tek deney

**Mevcut durum:** Yedi eski politika shadow'u ve gecikme gözlemcisi kapalı. Londra'da 21 Eylül **18:50:38 UTC / 21:50:38 Türkiye** kontrolünde sekiz eski PID de yok; ilgili yeni shadow süreci de bulunmadı. Jev ve ham kaydedicilerin ayarları değiştirilmedi. Kamu-verisi toplama işi sonlu olarak tamamlandı; sürekli yeni servis veya para harcayan lane açılmadı.

**Araştırma kararı:** Önceki ucuz-taraf RSI shadow'unu maker diye yeniden adlandırıp çalıştırmak bu bulguyu sınamaz. Taklit edeceğimiz nesne, gerçekleşmiş satırdan önce var olan emir ve kendi envanteriyle aldığı risk olmalı.

Sıradaki tek deney **M1: pasif alışın bizim için gerçekleşebilir fiyat/kuyruk kontrolü**. Henüz çalışan bir shadow veya doğrulanmış kâr kuralı değildir:

1. Mevcut book ve trade arşivinde iki token için kaynak/alınma zamanı, işlem yönü, hacim ve kopukluk kapsamını çıkar. Parent kimliği rol ve parçalanma ölçümünde kullanılabilir; bağımsız denemenin giriş sinyali Bosona'nın dolumu olamaz.
2. Küçük sabit miktarlı pasif teklif için karar anında görülen derinliği kuyruğun önüne yaz. Fiyatın değmesi tek başına dolum değildir; emir önündeki hacmi eritmeye yeterli, yönü doğrulanmış gerçekleşen işlemler gereklidir. İptalleri bizim önümüzden olmuş varsayarak kuyruk avantajı üretme.
3. Aynı tekliflerin kuyruk önünde/arkasında kalmasına ilişkin sonuçları ayrı sınırlarla değerlendir. Kopuk defter ve belirsiz gerçekleşme null kalsın. Ask'tan alışla maker sonucu birbirine karıştırılmasın; varsayılan rebate sıfır.
4. Önce bu yürütme kontrolü ekonomik olarak anlamlı ve ölçülebilir çıkmalı. Sonra tek bağımsız shadow, kendi başlangıç pozisyonu ve risk bütçesiyle dondurulmalı. Gerekirse risk azaltma tek ek yönetim kolu olarak aynı girişe karşı sınanır; bu rapordaki actor zamanları/miktarları karar girdisi yapılmaz.

**Şimdilik yeni işlem shadow'u açmamanın somut nedeni:** maker davranışı doğrulandı; fakat bizim teklifimizin hangi fiyat ve sıradan dolacağını, hangi güncel sinyalle tutulup iptal edileceğini ve risk azaltımının ek değerini henüz doğrulamadık. Bir simülasyona “fiyat değince doldu” yazmak bu eksikliği kapatmaz.

## 5. Yeniden çalıştırma ve kontroller

Aşağıdaki komutlar yalnız yerel, saklanmış kamu verisini okur:

```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_parent_research_20260921/analyze.py"
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_parent_research_20260921/check.py"
```

`collect.py` kamu RPC/API istekleri yapar; cache'i korur, sınırlı 429 tekrarı uygular. Hiçbir script imzalama/özel anahtar/emir API'si kullanmaz.

Kontroller: ilk risk azaltımı, gelecekteki işlemlerin etkisizliği, aynı-saniye belirsizliği, sıfırı geçme, lot maliyeti sınırları, takvim sonu belirsizliği ve parçalanma aralıkları; bozuk dört receipt çeşidinin reddi; gerçek örneklem/miktar/kimlik kontrolleri. Hedefli Ruff ve syntax denetimi; tam hesap yeniden çalıştırıldığında raporun birebir aynı olması ayrıca doğrulandı.

Sonuç dosyaları: `report.json` (her piyasa, parent/rol/dolum ve yerel hesap), `manifest.json`, `fetch_manifest.json`, `fetch_attempt1.json`, `verification.json`, `runtime_check.json`. Eski shadow sonuçları ve önceki muhasebe arşivleri üzerine yazılmadı.
