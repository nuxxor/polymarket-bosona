# BTC15: gerçek yürütme saatleri ve dengeleme nakdi

21 Eylül 2026 UTC / 22 Eylül Türkiye. Önceki WS araştırmasının sınırlı devamı.

Nakit ayırma kuralı finansman açığını önlüyor; ekonomik avantaj göstermiyor.
Gerçek emir kaydı kabul/iptal cevabını ölçtü, eşleşmeden dolumu öğrenmeye kadar
geçen süreyi ölçemedi. Eski aday P0 ve önceki M2 korunuyor. Yeni sürüm yalnız
ayrı yerel simülasyon kolu; emir, LIVE veya shadow başlatılmadı.

## Değişiklik ve sınırı

Önceki karşı örnek: 14,50$ harcama sonrası gereken 3,084$ hedge, 15$ toplam
bütçeye sığmıyordu. Yeni kol, her yeni emirden önce mevcut nakit harcaması
ve **bekleyen emirlerin tüm olası dolum kombinasyonları** için şunu ister:

`ücret dahil harcanan nakit + |Up payı − Down payı| <= 15$`

Net pay başına 1$ ayırır. Bu sözleşmelerde `p + 0,07 p(1−p) <= 1` olduğundan
karşı tarafa alımla kapama nakdi yeterlidir. İfade dışbükeydir; köşe kontrolü
kısmi dolumları da kapsar. İptal talebi rezervi serbest bırakmaz; motor nihai
durum ve kısmi dolumları öğrenene kadar yükümlülüğü taşır.

Bu **nakit garantisidir**. Derinlik, fiyat, emir kabulü, minimum miktar/yuvarlama,
gerçek sıra veya fiilî kapanma garantisi değildir. Hedge tetikleyicisi hâlâ
`|net|>=10`; örneğin 5 net payla biten pozisyon kendiliğinden kapanmaz.
5 pay klip, 10 net, 15$ nakit, −5$ en kötü sonuç; fiyatlama, karar aralığı ve
840. saniyede iptal aynı kaldı. Eşik taraması yapılmadı.

## Gerçek emir saatleri: ne ölçüldü?

Kaynak: MAIN `data/analysis/btc5m_m4_v2_20260922/final_0112/LOG_f_emir_iz.jsonl`.
BTC5 stratejisi araştırılmadı; kapanmış oturumun genel emir yürütme kaydı
salt okunur incelendi. Sanitizasyon kodu metin olarak okundu, bot içe aktarılmadı.
624 olay, 309 istek/cevap çifti; 12 kabul, 2 ret; 4 dolan ve 8 iptal edilen emir.
Dolmayan emirler örneklemden çıkarılmadı. İki GET boş/kimliksiz yanıt verdi;
bunlar sıfır dolum veya başarılı durum sorgusu sayılmadı.

| Yerel SDK çağrısı | n | Ortanca ms | En yüksek ms |
|---|---:|---:|---:|
| Kabul edilen POST | 12 | 57,402 | 125,210 |
| Bütün POST cevapları | 14 | 48,165 | 125,210 |
| İptal cevabı | 9 | 23,746 | 74,704 |
| GET order | 285 | 16,597 | 242,227 |

SDK çağrısının başı/sonu monoton saatle ölçülür. İmzalama ve istek loglama bu
sürenin dışında; kabulün borsada gerçekleştiği an kaydedilmemiştir. Örneklem
başka süreli sözleşmelerden, küçük ve aynı oturumdandır. Bu sayılar BTC15
emir gecikmesinin dağılımı diye kullanılamaz.

İptal ACK'inden sonra dönen iki LIVE cevabı ayrıldı: birinin sorgusu ACK'ten
önce başlamıştı; öteki gerçekten ACK'ten sonra başladı. İkinci emirde sonraki
terminal GET cevabı ACK'ten 286,553 ms sonra geldi. Bu, iptalin tam o anda
etkinleştiğini göstermez. Sekiz pozitif iptal ACK'i ve dolum nedeniyle bir
negatif ACK vardır; dolan miktar kayıtlarda bir kez muhasebeleştirildi.

Dört dolumda pozitif GET cevabından yerel `fill_observed` olayına süre
0,164–0,205 ms. **Bu eşleşmeden haberdar olma gecikmesi değildir.** İkisinde
önceki sıfır ile ilk pozitif GET cevabı aralığı 515,832 / 541,056 ms;
diğer ikisinde önceki geçerli sıfır cevabı yok. Hepsinde `exchange_ns=null`.
Public WS alım saatini private emir bildirimi yerine koyma varsayımı sürüyor.

Üç piyasanın ayrı zaman damgalı CLOB cevabında `itode=true`, ücret oranı0,07,
üstel1 görüldü. Resmî belge bu bayrakta marketable emir için250ms bekleme
tanımlar; bu süre ağ gidiş/dönüşü değildir. Cevaplar piyasa kapandıktan sonra
alındığından geçmişteki ayarın değişmezliğini ayrıca kanıtlamaz.
[Polymarket emir yaşam döngüsü](https://docs.polymarket.com/concepts/order-lifecycle).

250/750ms eski karşılaştırma senaryoları iki kolda aynen korundu; ölçülmüş
kalibrasyon sayılmadı. 250ms toplam taker senaryosu, bu beklemeye ek taşıma
süresini ayrıca temsil etmez. Gerçekçi yürütme için maker kabulü, taker
beklemesi, iptal ve dolumu öğrenme ayrı saatler olarak ele alınmalıdır.

## Yeni verinin kapısı

Pencereler sonuç hesaplanmadan seçildi. İlk ikisi seçim anında kapanmıştı;
üçüncüsü sürüyordu. Bu, temiz kör deney olarak sunulmuyor. Her pencerenin
kesiti bitiş+120sn; aynı uygunluk koşulları kullanıldı.

| Başlangıç UTC | Receipt | WS eşleşmesi | Geçerli defter kontrolü | Kullanım |
|---|---:|---:|---:|---|
|21:45|319|316|900/901|Koşullu replay|
|22:00|984|984|901/901|Koşullu replay|
|22:15|612|608|901/901|Eksik işlem; PnL bilinmiyor|

1.915 receipt; 1.908 kaydedilmiş WS eşleşmesinin miktar/rol mutabakatı;
6 receipt ikinci kamu RPC'den de doğrulandı. Receipt sayısı, WS mesajı ve
Bosona dolumu aynı gözlem birimleri değildir; sayı farkını kayıp dolum
diye toplamadık. Öncesi/sonrası işlemleri ayrı tutuldu.

Üçüncü pencerede `0x38653423aa33191fa36714e9463daed61a437d5043c4325bd38f46a064f90003`
işleminin424numaralı eşleşme logu zincirde var; tüm kapanmış22UTC WS dosyasında
transaction hash'i yok. Blok zamanı22:21:40UTC, pencere içi. Tam eşleşme saati
bilinmediğinden blok saatine yerleştirip hacim uydurulmadı. Açık bağlantı
kopması olmaması ve901/901 görüntü, eksiksiz işlem akışını kanıtlamıyor.
Kayıp mesajın sağlayıcı mı yerel kayıt mı kaynaklı olduğu belirlenemiyor.

Aynı pencerenin ilk taker API listesinde21 miktar/anahtar farkı çıktı; ayrı
tekrar listesi receipt'lerle uyuştu. İlk cevap korundu. Yeni liste, WS'deki
eksik eşleşme saatini doldurmaz; pencere eksik kalır.

## Aynı bütçede karşılaştırma

Tutarlar USD; ücretler dahil, rebate0. İki piyasa×dört varsayım bağımsız sekiz
ekonomik gözlem değildir. “Kuyruk önü/arkası” PnL alt/üst sınırı değildir;
farklı envanter yolları üretir. Gerçek sıra bilinmiyor ve piyasa etkisi yok
varsayılıyor. Tüm `economic_pnl` alanları hâlâ `null`.

| UTC | Kuyruk / gecikme | Eski M2 koşullu PnL | Rezervli M2 koşullu PnL |
|---|---|---:|---:|
|21:45|Arka /250ms|Bilinmiyor|Bilinmiyor|
|21:45|Arka /750ms|−1,286960|−0,900000|
|21:45|Ön /250ms|−3,750000|−0,250000|
|21:45|Ön /750ms|−3,650000|−0,250000|
|22:00|Arka /250ms|+0,100000|+0,700000|
|22:00|Arka /750ms|+0,485955|0,000000|
|22:00|Ön /250ms|+0,377777|−1,872223|
|22:00|Ön /750ms|+0,927777|−1,872223|

İlk satırda public kaynak saati ile varsayılan emir yaşam döngüsü saati eşit;
olay sırasına keyfî öncelik verilmedi. İki kol da belirsiz bırakıldı.
22:15 penceresinin bütün kolları ayrıca eksik; tablodan ekonomik toplam çıkarılmaz.

İki uygun pencerenin750ms/arka senaryosu eski−0,801005$, rezervli−0,90$.
22:00/ön/750ms örneği karşı kanıt: eski+0,927777$, rezervli−1,872223$.
Bu kural daha iyi kâr kuralı olarak seçilemez.

Eski M2'nin21:45'te dört yolunda da hedge nakit sınırına takıldı. Örneğin
750ms/arka: harcanan11,28696$, net5Up; istenen5Down4,43696$; toplam15,72392$.
Rezervli kolda simüle edilen `nakit+|net|` en fazla14,30$; kısıt ihlali ve
nakit nedeniyle bloke hedge yok. Fakat **sekiz rezervli yolda taker hedge
dolumu da yok**: kural daha erken risk açmayı engelledi. Sentetik test hedge
yolunu çalıştırıyor; gerçek veri taker kapamanın uygulanabilirliğini doğrulamıyor.

Rezervli21:45/750ms/arka kol10Up/5Down,5,90$harcamayla bitiyor. Net5 için
nakit ayrılmış olsa da sabit10pay hedge tetikleyicisi çalışmıyor. Karşı tarafın
gelmesini bekleyen ve pozisyonu sonuçlanmaya taşıyan bir politika sürüyor.
Reddedilen karar sayıları saniyelik yeniden denemeleri içerir; “kaçan farklı
emir/fırsat sayısı” diye okunmamalı. Kod yalnız rezerv nedeniyle reddedilen
ile eski risk kontrolünün de reddedeceği kararı ayrıca sayar.

P0 iki veri-uygun piyasada da sıfır giriş yaptı; bağlam eksikliği yok.
21:45 t180'de Down ask75¢ ve modelDown≈%98,63;55¢tavanı engelliyor.
22:00'de Down ask30¢, ücretli maliyet31,47¢, modelDown≈%36,384;
avantaj≈4,914¢ ve5¢kapısını geçmiyor. Eşikleri değiştirmedik. M1 kolları
ve P0 iki sürümde birebir aynı. P0'nun sıfır işlemi tek başına kârlı model
olduğunu veya yanlış filtre kullandığını kanıtlamaz.

Bosona'nın aynı iki sözleşmedeki kayıtlı işlemlerinin sonuç nakdi sırasıyla
−34,7073$ (2maker) ve−32,223185$ (6maker/3taker). Miktar/bütçeler bizimkinden
farklı; bu, eşit riskli performans karşılaştırması değildir. Maker ağırlığı
tek başına kâr garantisi değildir.

## Fable'ın son sürümünden alınan ve sınırlandırılan bulgu

Maker ağırlığı ve taker risk azaltımı ana yönü destekliyor. “Karar değil
kotasyon dolumu” ifadesi, fiyatı/yönü/miktarı seçen bir karar mekanizmasının
olmadığını göstermez. Dört saniyelik seviye görünürlüğü Bosona'nın emrinin
yerleştirme yaşı değildir; kamu defterindeki seviye birden fazla emri içerir.
263 ajan/110 bulgu sayısı bağımsız ekonomik kanıt sayısı değildir.

Fable'ın `gap_candidate_replay_lookahead_fix` kod ve sonuçları da okundu.
Sıfır kayma/discount/managed180ilk girişin102'si gerçekleşirken55¢üstünde;
en yüksek fiyat89,5¢. Düzeltme ilk giriş/ekleme için gerçekleşme anındaki
fiyat ve avantaj korumasını kaldırıyor; karar anındaki filtre kalıyor.
Bu180giriş, eski fiyat koruması aynen tutularak yalnız saat hatası giderilmiş
sonuç diye sunulamaz. Kârı artırması ekonomik doğrulama değildir.

Bizde karar ve gönderilen limit karar anında sabittir; sonra gelen defter
yalnız o limitte gerçekleşip gerçekleşemeyeceğini belirler. Gelecekteki
fiyatla niyeti yeniden seçmek ile önceden gönderilmiş limitin dolmaması
farklı olaylardır. Orijinal aday dosyasına dokunulmadı; Fable sonucu yeniden
optimize edilmedi. Sayım `results/fable_price_limit_review.json` içindedir.

## Karar ve sonraki iş

Rezerv kuralını ayrı finansman kontrolü olarak koru; strateji adayı diye
yükseltme. Düşük bütçenin net10 hedge tetikleyicisiyle etkileşimi artık açık;
bunu kazanç için eşik tarayarak gizleme. Önce sabit tetikleyiciye gerçekten
ulaşılan yeni, eksiksiz yollar gerekir.

Bir sonraki ölçümde öncelik, public işlem akışındaki sessiz eksikleri
receipt/API mutabakatıyla işaretlemek ve zaman sözleşmesini doğru kurmak.
Maker kabulü ile gecikmeli taker uygulamasını tek gecikmeyle açıklamamak;
varsa zaten üretilmiş özel emir kayıtlarını salt okunur eşlemek. Kamu L2
akışı tek başına kendi kuyruk sıramızı veya private bildirim gecikmesini
vermez. Bunlar bilinmiyorsa sonuç koşullu kalır; canlı deney bu yetkide yok.
Uzun dönem ekonomik kabul,10tamgün/100piyasa ve yoğunlaşma/karşı-kol
ölçütleri hâlâ açık; bu iki piyasa kabul için yeterli değildir.

## Tekrar çalıştırma ve korunan kaynaklar

Python: `/home/taygun/Masaüstü/KararAtlas/base1/bin/python3`.
Ağsız tekrar (bütün atanan üç piyasanın ham dosyaları mevcut):

```bash
OPENBLAS_NUM_THREADS=1 /home/taygun/Masaüstü/KararAtlas/base1/bin/python3 -B /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_execution_reserve_20260921/run.py repeat
/home/taygun/Masaüstü/KararAtlas/base1/bin/python3 -B /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_execution_reserve_20260921/check.py
```

`run.py fetch` ayrı kamu edinim adımıdır; tekrar sırasında çağrılmaz.
`execution.py`: tek ek rezerv kuralı; `telemetry.py`: kapalı emir izi analizi;
`check.py`: eski motor eşdeğerliği, kısmi dolum/iptal/hedge/bozuk kayıt sınamaları.
Önceki muhasebe, resmî sonuç, piyasa sınıflandırma, kamu toplama ve replay
yardımcıları hash kontrolüyle yeniden kullanıldı. Kökten bağımsız kurulum
paketi değil; yerel kaynak yolları `sources.json`/`dependencies.json` içinde.

`protocol.json` ayrı hash ile sabit; rapor üretimi protokol yazmaz. Ham API
cevaplarında URL ve alım zamanı, receipt/defter dosyalarında hash manifestleri
var. `results/checks.json` ve `results/reproducibility.json` gerçek kontrol
ve tekrar sonuçlarını taşır:17kontrol geçti;25çıktı iki ağsız çalıştırmada
aynı SHA256 verdi. Dört Python dosyasının syntax kontrolü ve hedefli Ruff geçti.

WS pilotu22:33:54,241UTC'de kendi depolama sınırına ulaşıp kapandı; üçüncü
kesit22:32UTC tamamlanmıştı. PID2201967 artık yok; süreç bizce durdurulmadı.
Kapanmış üç gzip hash'i doğrulandı. Eski REST kaydedici PID1714322 çalışıyordu;
kodu aynı. MAIN/Londra, eski aday/protokol, Ultra/Fable çıktıları ve diğer
araştırma dizinleri değiştirilmedi. Anahtar içeriği okunmadı.
