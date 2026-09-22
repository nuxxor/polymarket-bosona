# BTC15dk geç ekleme — 21 Eylül 2026 devam araştırması

**Mevcut aday korunmalı.** Bosona'nın geç eklemelerini kaçırmasının başlıca nedeni
ilk girişten başlayan farklı pozisyon yolu. Sadece 55¢ tavanını gevşetmeyi destekleyen
kanıt yok. Benzer koşullardaki ekleme olmayan kontroller ve kronolojik model kıyası,
gözlenen geç ekleme kârını bağımsız uygulanabilir avantaja dönüştürmedi.

Adayın kodu, protokolü ve önceki sonuçları SHA256 ile aynı. Ana repo ve Londra'daki
süreçlerde değişiklik yapılmadı. Ayrı yerel kamu defteri kaydı başladı; yeni shadow yok.

## 1. BTC5dk muhasebesi: hata var, toplam küçük farkı gizliyor

Eski `activity_key → dict` yolu, aynı işlemdeki gerçekten eşit iki dolumu tek satıra
indiriyor. Örtüşen indirmeleri tekilleştirmek gerekir; aynı cevabın içindeki gerçek
çokluğu silmek gerekmez. 65 şüpheli BTC5dk piyasası taze `/activity` ile; sekiz gerçek
eşit işlem çifti ayrıca `/trades` ile doğrulandı. Resmî sonuçlar Gamma'dan kontrol edildi.

Önceki **13 Eylül–20 Eylül 22:30 UTC, 1.842 piyasa** hesabında yedi eksik dolum:
**1.039 pay, 648,21 dolar maliyet; PnL 8.319,438464 → 8.313,228464 dolar**.
Net fark **−6,21 dolar**, fakat dört piyasanın kâr/zarar işareti değişiyor.

| Piyasa başlangıç UNIX'i (`btc-updown-5m-…`) | Eksik pay | Eksik maliyet $ | Eski piyasa PnL $ | Düzeltilmiş $ | Fark $ |
|---|---:|---:|---:|---:|---:|
| 1789295100 | 148 | 136,16 | −83,15 | −71,31 | +11,84 |
| 1789339500 | 148 | 143,56 | −146,31 | −141,87 | +4,44 |
| 1789449300 | 148 | 50,32 | +132,94 | +82,62 | −50,32 |
| 1789539000 | 148 | 47,36 | −20,86 | +79,78 | +100,64 |
| 1789554900 | 148 | 76,96 | −22,71 | +48,33 | +71,04 |
| 1789804200 | 50 | 32,00 | −13,11 | +4,89 | +18,00 |
| 1789931100 | 249 | 161,85 | +85,26 | −76,59 | −161,85 |

Dönem dışındaki `1789185300` için ayrıca 148 pay/121,36 dolar ve **+26,64 dolar**
PnL farkı var. Ana toplama katılmadı. FIFO eşleşmiş/açık bacak atıfları da değişiyor;
piyasa bazındaki bütün farklar `results/btc5_audit.json` içinde.

57 piyasanın eski ham `REDEEM` tekrarları taze API'de doğrulanmadı. Ham satırların
hepsini körlemesine toplamak da yanlış: gerçek işlem çokluğu ile indirme/kaynak
tekrarını ayırmak gerekiyor. PnL'yi alış maliyeti ve resmî ödeme üzerinden hesapladım;
redeem tutarını ikinci kez gelir yazmadım. Bu denetim strateji eşiklerini yeniden sınamaz.

**Kendi botumuz:** `muhasebe.py` içindeki `api_trades`, kaset ve sonraki `api` sözlükleri
aynı yapısal riski taşıyor. Elde bulunan 20 Eylül mutabakatının **96 penceresi / 304
kamu işlemi**, taze activity ile karşılaştırıldı: **eksik eşit dolum 0; PnL farkı 0**.
Bu sonuç o kayıt dönemi içindir; Londra'nın daha sonraki D/E dönemi için genel temizlik
belgesi değildir. Botun emir bazında kümülatif `size_matched` farkını izleyen hesap yolu
ayrı; bu hata doğrudan orada gösterilmedi. Kod düzeltilmedi, canlı hesaplar değiştirilmedi.

## 2. Aday eklemeleri nerede kaçırıyor?

13–20 Eylül'de Bosona: **277 piyasada 1.173 geç ekleme dolumu**, 600–899. saniyeler,
marjinal ödeme eksi kayıtlı maliyet **+3.389,91 dolar**. Bu dolum sayısı emir sayısı değil.
Aday aynı bütün evrende 21 ilk giriş ve bir ekleme üretiyor; bunlar eski fiyat
örnekleriyle yapılan senaryo sonuçları, gerçekleşebilir defter dolumları değil.

Geç ekleme görülen 277 piyasayı, adayın 180. saniyedeki ilk giriş yoluna göre ayırdım:

| İlk giriş sonucu | Piyasa | Sonraki Bosona geç dolumları | Bu dolumların PnL'si $ |
|---|---:|---:|---:|
| Karar verisi eksik | 79 | 325 | +1.183,26 |
| Olasılık avantajı <5¢ | 50 | 226 | −87,88 |
| Olasılık geçiyor, fiyat >55¢ | 82 | 305 | +1.180,34 |
| Karar geçiyor, sonraki fiyat örneği kabul edilmiyor | 59 | 281 | +1.039,58 |
| Gerçekleşmiş sayılan ilk giriş var | 7 | 36 | +74,61 |

59 senaryo reddinin 44'ünde sonraki fiyat örneğinde olasılık avantajı kayboluyor,
15'inde 55¢ tavanı aşılıyor. Bu **borsa emri reddi değil**, eski senaryonun fiyat
örneği koşulu. Gerçek ask olmadığı için ikisini eşitlemiyoruz.

- **İlk giriş zamanı:** Bosona ilk girişi 137 piyasada 180. saniyeden önce, 139'unda
  sonra; yalnız birinde tam 180. saniyede. Medyan 184 saniye tek bir sabit anı doğrulamaz.
- **Yön ve envanter:** Girilen yedi piyasanın dördünde aday geç ekleme anından önce
  tamamlanmış, net pozisyon sıfırlanmış. Bu 13 dolumu kaçırıyor. Geriye üç piyasada
  23 dolum kalıyor; bunlarda açık yön Bosona'nın ekleme yönüyle aynı. Bu alt kümede
  karşı yönde açık kalma veya önceki ekleme hakkını tüketme ana neden değil.
- **Zaman:** Aday yalnız 600. saniyede ekleme kararı alır. Bosona dolumlarının yalnız
  ikisi tam bu saniyede; 99'u 600–629 aralığında. Dolum zamanı karar zamanı olmadığı
  için tam saniye sayısı mekanizma kanıtı sayılamaz. Ancak adayın pozisyonunun da
  uygun olduğu 23 dolumun tamamı 630'dan sonra: sabit zaman engeli somut.
- **55¢:** Gerçek dolum fiyatında 671 kayıt geçiyor, 502 geçmiyor. İki küme de tarihsel
  kârlı: +1.706,96 ve +1.682,95 dolar. Tavan tek açıklama değil.
- **Olasılık:** Ücret varsayımı dahil, dolumdan 5sn önceki model avantajı 349 kayıtta
  ≥5¢, 485'inde düşük; 339'unda veri yok. Geçemeyen gözlemler de +1.244,87 dolar
  getiriyor. 10sn gecikme kontrolünde geçenlerin PnL'si +962,05'ten +659,92'ye düşüyor.
- **Risk sınırı:** Adayın açık yönünün uygun olduğu 23 kaydın beşinde varsayımsal
  5 pay ekleme kendi risk sınırını aşar. Kalan 18 kayıt −5sn verisinde fiyat,
  olasılık ve riskten geçer; **zaman yüzünden geçmez**. −10sn kontrolünde 17 kalır.

Fiyat kapıları ham işlem fiyatıyla; gerçekleşen maliyet/PnL `usdcSize` ile hesaplandı.
74 geç dolumda nakit birim maliyeti ham fiyattan anlamlı derecede yüksek; bu maliyetin
üzerine aynı taker ücretini tekrar eklemedim. Varsayımsal taker kapısı ham fiyata ücret ekler.

Bu kapılar örtüşür; hepsinin elenen tutarını toplamak hatadır. Eksik veri, sinyal
reddi, tamamlanmış envanter ve fiyat örneği gecikmesi ayrı tutuldu.
Tek aday eklemesi `btc-updown-15m-1789848000` içindedir; Bosona'nın bu geç ekleme
kümesiyle örtüşmez. `miss_rows.json` her dolumun bütün koşullarını saklar.

## 3. Kazanan, kaybeden ve gözlenen ekleme olmayan durumlar

Aynı saniye/yön parçalarını birleştirdim; aynı saniyede iki yön bulunan belirsiz
piyasaları ana eşleştirmeden çıkardım. Açık risk = **max(0, harcanan − min(Up,Down))**,
yani iki sonuçtan kötü olanındaki azami kayıp. Bu piyasa bazındaki net ödeme riskidir;
sermaye, emir rezervi ve diğer piyasalardaki portföy riski değildir.

Önceden sabit 10¢/60sn/risk katmanları tek başına yeterince yakın eşleştirmedi.
Bu nedenle farkı ≤3¢, ≤30sn ve ≤25 dolar ile sınırlayan kalite kontrolü uygulandı;
kaba sonuçlar `coarse_*` dosyalarında korundu. PnL eşiği taranmadı.

**68 kazanan–kaybeden çifti:** ortalama fiyat 40,96¢ / 40,85¢; kalan süre
171,40 / 171,25sn; açık risk 46,23 / 47,18 dolar. İki tarafta da ortalama maliyete
çok yakın ekleme var. Uygun Chainlink verisi olan 38 çiftte modelin ücret sonrası
avantajı kazananlarda **1,73¢**, kaybedenlerde **0,99¢**. Fark yalnız 0,74¢;
bu kalibre edilmemiş model için güçlü bir ayrım kanıtı değil. Küçük momentum farkı da tek başına
kural ilan etmeye yetmez.

Somut karşı örnek (`btc-updown-15m-…`):

| | Kazanan: 1789641000 | Kaybeden: 1789530300 |
|---|---:|---:|
| Ekleme fiyatı | 52¢ | 51¢ |
| Kalan süre | 189sn | 191sn |
| Önceki açık risk | 67,70 $ | 77,27 $ |
| Ekleme miktarı | 150 | 127 |
| Açık bacağın ortalama maliyeti | 34,52¢ | 66,00¢ |
| Model avantajı, ücret varsayımı sonrası | 1,52¢ | 11,99¢ |
| Ekleme PnL'si | +72,00 $ | −64,77 $ |

Kazanan örnek pahalılaşmış yöne büyüyor; kaybeden örnek ucuzlayan tarafa ekliyor ve
olasılık filtresinden daha rahat geçiyor. Tersi örnekler de veri setinde var.

**Ekleme yok kontrolleri:** her 30sn'de, 600–870 arasında, önceden gözlenen açık
pozisyonu olan durumlar. Sonraki 30sn yalnız sonuç etiketi; gelecek dolumlar özellik
olarak kullanılmadı. Son 5sn'de henüz hesaba girmemiş dolumu olan durumlar çıkarıldı.
3.524 kullanılabilir durum: 231 aynı yön ekleme; 3.035 gözlenen işlem yok; 258 başka
hareket. Karşı yön sayacı 287; aynı aralıkta iki hareket olabildiğinden örtüşebilir.

Aynı fiyat/süre/risk ve aynı araştırma döneminde, başka piyasadan kontrollerle:

| Dönem | Yakın çift | Ekleme / kontrol kazanma oranı | Piyasa başına 5 paya normalize toplam fark $ |
|---|---:|---:|---:|
| 13–17 Eylül | 127 | %35,43 / %33,07 | +12,00 |
| 18–20 Eylül | 46 | %36,96 / %41,30 | **−11,62** |

İkinci dönem 39 ekleme piyasası içeriyor; en iyi üçü çıkarılınca fark **−26,90 dolar**.
Piyasa bootstrap %95 aralığı **[−52,39; +30,01]**, gün aralığı da sıfırı içeriyor.
Kaba eşleştirmede ikinci dönem farkı −1,35 dolardı; eşleştirme seçimine duyarlılık da
kanıtın zayıflığını gösteriyor. Fiyatlar geçmiş örnekler; **ask/derinlik içermeyen
koşullu senaryo**, gerçek alım simülasyonu değil. Tekrarlanan piyasa durumları ve
kontroller bağımlı; aralıklar nedensel etki iddiası taşımaz.

Gözlenen işlem yok demek **emir yok** demek değildir. Maker kuyruğu, iptal ve dolmayan
emirler görünmüyor. BTC15dk karar verisi eksik 1.412 ızgara noktası da seçilim yaratır.

## 4. En fazla iki hipotez: ikisi de şimdilik adayın önüne geçmiyor

**H1 — sürekli değer fırsatı.** Tek bir 600. saniye yerine kalan süre içinde model
olasılığı eksi masraflı fiyat ve yönlü momentum ekleme yoğunluğunu açıklıyor olabilir.
Destek: adayda açık pozisyonu kalan bazı uygun fırsatlar çok daha geç geliyor.
Karşı kanıt: avantajı çok daha yüksek olan kaybeden karşı örnek var; toplu
ayrım küçük ve kronolojik kıyas iyileşmiyor. Eksik: gerçek ask, piyasa referansının zamanında erişilebilirliği,
olasılık kalibrasyonu. Yanlışlanma: yeni tam defterli günlerde önceden kayıtlı farkın
ve yönlü momentumun ekleme tahminini ve masraf sonrası kontrol farkını iyileştirmemesi.

**H2 — envanter ve ortalama maliyet.** Ekleme, kendi açık bacağının maliyetine göre fiyat,
net miktar ve iki tarafın dengesine bağlı olabilir. Destek: çok taraflı pozisyonlar ve
adayın erken tamamlayıp riskini sıfırlaması önemli. Karşı kanıt: ucuzlayan kaybeden
örnekler; dar eşleştirmede maliyet indirimi kazananı ayırmıyor. Eksik: diğer piyasalardaki
pozisyonlar, açık emir rezervleri ve hedef miktar. Yanlışlanma: bu üç envanter değişkeninin
aynı fiyat/süre/riskte yeni günler üzerinde ek açıklama sağlamaması.

13–17 Eylül'de bir kez öğrenilen lojistik modeller, **2.443 eğitim / 1.081 kronolojik
kontrol** durumu. Hiperparametre/eşik taraması yok. Her model aynı fiyat, süre ve açık
risk kontrollerini kullanır. Aday satırı, değişmeyen adayın kapılarını özellik yapan
bir açıklama modeli; adayın kendi kârı veya doğrudan işlem doğruluğu değildir.

| Açıklama | Kontrol log kaybı ↓ | AUC ↑ | Adaya göre iyileşme |
|---|---:|---:|---:|
| Yalnız temel sıklık | 0,252281 | 0,500 | −0,002989 |
| Fiyat/süre/risk | 0,252841 | 0,538 | −0,003548 |
| Mevcut adayın koşulları | **0,249292** | **0,632** | — |
| H1 sürekli değer | 0,253290 | 0,559 | −0,003998 |
| H2 envanter/maliyet | 0,250642 | 0,571 | −0,001350 |

H2 Brier ölçüsünde çok küçük iyileşiyor; log kaybı/AUC üstünlüğü yok. İkisinin de
piyasa ve gün bazında fark güven aralığı sıfırı içeriyor; kontrolde yalnız üç gün var.
**Hangisi daha açıklayıcı? Bu veride hiçbiri için söyleyemiyoruz.** Önceki günler zaten
incelenmiş olduğundan kronolojik ayrım gerçek kör test de değil.

`hypotheses.py:score` her iki modeli yalnız fiyat/karar öncesi bağlam/**kendi** FIFO
envanteriyle çalıştırır. Bosona dolumu tetikleyici değildir; çıktı emir veya alım kararı
üretmez. Geçmişte açıklanan durum Bosona'nın envanteri, ileri değerlendirmede simülasyonun
kendi envanteri olacaktır; bu aktarım ayrıca sınanmalıdır. Mevcut adayın giriş/ekleme/
tamamlama/risk kurallarında değişiklik önerilmiyor.

## 5. Yeni gerçek defter kaydı ve doğrulama

Ayrı yerel süreç **PID 1714322**, başlangıç **21 Eylül 14:25:08 UTC**, planlı bitiş
**24 Eylül 14:25:08 UTC**; en fazla 72 saat. Bir saniye hedef aralıkla aktif resmî BTC15dk
sözleşmesinin **iki tokenının bütün bid/ask seviyeleri** kamu REST `/books` üzerinden
kaydediliyor. Sözleşme değişiminde başlangıç/bitiş, iki sonuç, Chainlink 60sn TWAP
mekanizması doğrulanıyor. İstek, alım, borsa zamanları, hatalar, hash ve ücret metadata'sı
saklanıyor. Tekilleştirme yapılmıyor. Bosona etkinliği abonelik/karar tetikleyicisi değil.

Dondurulmuş ilk kontrol **14:25:08–14:36:56 UTC**: iki sözleşmede **709 çift snapshot /
1.418 taraf defteri**, HTTP/kayıt hatası 0. Borsa zaman yaşı hepsinde ≤3sn; medyan
aralık 1sn, en uzun 1,218sn. **282 taraf defteri tek taraflı/boş**; bunlar doldurulmadı,
saklandı. Kalan **1.136** taraf gözleminde güncellik, ≤3¢ spread ve 5 pay derinlik
kontrolü geçti. Dolayısıyla “API cevabı var” ile “işlem yapılabilir” aynı şey değil.

Aynı kısa dilimde **7 yeni BTC15dk dolumu**, biri geç ekleme; beşinde dolumdan
5sn önce geçerli gerçek ask derinliği mevcut. `1790000100` piyasasında 647. saniyedeki
Down eklemesi 1,02 pay / 1,2¢: öncesindeki ask 2¢, ücretli taker maliyeti yaklaşık
2,137¢. Bu ekleme resmî sonuçta kaybetti (−0,01224 dolar). Tek bir küçük karşı örnek;
Bosona fiyatından taker olarak dolabileceğimiz varsayımını doğrulamıyor. Emir türünü
de kanıtlamıyor: fiyat, zaman ve sıra farkları mümkün. Küçük dolum miktarı
için hesaplanan defter maliyeti, asgari emir miktarı/bedeli koşullarının sağlandığı
anlamına da gelmez. Diğer piyasanın sonucu kayıt
alındığında henüz kesin değildi; PnL alanı boş bırakıldı. Ayrıntı `new_period_rows.json`.

Kayıt her değişimi yakalayan WebSocket bandı değildir; saniye arası hareketleri ve
maker kuyruğundaki yerimizi göstermez. Başlangıçta yarım yakalanan sözleşme tam pencere
testinden çıkarılacak. İlk kısa kayıt, ekonomik avantaj veya 72 saatlik kapsam kanıtı
sayılmaz. Mevcut fiyat kaydedicileri salt okunur kullanılacak; yeni dönemin tam Chainlink
bağlamı/sonuçları ve yeterli gün sayısı oluşmadan aday lehine karar verilmeyecek.

Kontroller: gerçek çokluğu ve örtüşen indirmeyi ayıran regresyon; resmî ödeme ve FIFO;
aynı aday hash'i; gelecek sonucun özellikleri değiştirmemesi; eşleştirme yakınlıkları;
boş/yanlış token defteri; gerçek kayıt/ücret/derinlik; Ruff ve syntax; offline birebir tekrar.

Kaynaklar: [kamu activity API](https://docs.polymarket.com/api-reference/core/get-user-activity),
[kamu tam defter isteği](https://docs.polymarket.com/api-reference/market-data/get-order-books-request-body),
önceki donmuş araştırmanın activity/market/fiyat/Chainlink arşivi. Taze yanıtların URL ve
alım zamanları `raw/` içinde. Çalıştırma komutları README.md; sonuç ve kanıtlar `results/`.
