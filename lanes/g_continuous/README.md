# G5 hazırlığı ve önceki deneyler

G4 durduruldu; G5 yalnız hazırlanmış ve park edilmiştir, canlı değildir.
G5 adayı `staging/g5/bot/`, protokol ve kanıtlar `staging/g5/README.md` içindedir.
Aşağıdaki G4 yayın kaydı tarihsel kaynak tarifidir.

Bu yayında `bot/` dizini gerçek Londra G4 kaynağının okunabilir kopyasıdır:
`ab.py` SHA256 `0fd30f9faee281d59ca57597005391579b0debbf5ff131ea66ee5a2bb9182ee1`.
`G_RELEASE.json` bütün kaynak dosyalarını doğrular. Kök `bot/ab.py` güncel
G4 çalıştırıcısı değildir. G2 karşılaştırma tabanı `transport_fix/bot/`,
G3 aday/operatör farkları `G3.patch` / `G3_LIVE.patch`, G4 farkı `G4.patch`.

Operatörün 22 Eylül 16:42:23 UTC LIVE başlangıcı ve ilk 16:45 pencere kaydı
`validation/G4_launch_20260922.json` içinde. Bu tarihli bir başlangıç
kesitidir; güncel canlı durum veya G4 kârlılık sonucu olarak okunmamalı.
Kaynak/bütçe geçişi ve ilk iki5pay dolumu doğrulandı; seçici taker çıkışı yok.
G4 $100 zarar sınırı,5pay klip,10pay net kapasite kullanır; G2/G3 dönüşümlü
kontrol içermez. Bu üç değişkenin tarihsel kıyası saf tek-etken deneyi değildir.

Yayında kaynak paketleri, emirsiz testler, kamu akışı kuru kayıtları,
G3'ün seçilmiş bot/SDK izlem kesiti ve tamamlanmış ULTRA incelemesi bulunur.
Ham özel hesap WS mesajları içeren `validation/G3_capture.jsonl.gz`, diğer
ham özel kayıtlar, canlı STATE/RUN/BUDGET dosyaları, büyük harici tape/DB
ve devam eden Fable scratch çıktıları yayımlanmadı. G3 probe'un özel
eşleşme hesabı ve ULTRA'nın harici ham arşiv çıkarımı yalnız GitHub'dan
tam tekrar edilemez; bunların kaydedilmiş sonuçları sınırlarıyla korunur.
Eski aşağıdaki bölümler tarihsel kayıt olup güncel kaynak/sürüm tarifinin
yerine geçmez. Bu yayın canlı stratejiye veya bütçeye müdahale etmez.

## G1 — süre sınırı olmadan operatör başlangıcı

```bash
bash "/home/taygun/Masaüstü/polymarket-bosona/londra_g_sinirsiz_baslat.sh"
```

Aynı G1 politikası, 5 pay, yeni başlangıçtan $10 zarar kesici. Önceki
+$9,206315 muhasebede kalır. Başlangıçta hesap yeniden mutabıklaştırılır;
son kontrolde anchor −6,028580 ve buna göre kesici −16,028580 olurdu.
Bu toplam geçmiş PnL tabanıdır; yeni koşunun kaybı anchor'a göre ölçülür.
Sabit bitiş saati yok; kâr zirvesinden kayan stop değildir.

Operatör komutu öncesi hesap ve iki kayıtçı kontrol edilir; bot bu hazırlıkta
canlı başlatılmadı. RUN işareti tekrar bütçe açılmasını engeller. Otomatik
restart yok. Strateji politika hash'i önceki pilotla birebir aynı.

Kayıtçılar A/B ayrı süreçte, 15dk parçalar ve ilk B'de ek5dk ile
piyasa listesini yeniler. gzip level1; eski kayıtlar silinmez. İki kayıtçı
başlangıçta zorunlu, çalışırken en az biri güncel olmalı. Disk2GiB rezervi,
belirsiz muhasebe veya veri arızası botu durdurabilir. Süresiz çalışma,
fiziksel disk veya API geçmiş sınırının kalkması demek değildir.

Durdurma (normal emir kapatma yolu):
```bash
ssh -T -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -i "/home/taygun/İndirilenler/polymarket-test-key2.pem" ubuntu@18.135.99.14 'touch /home/ubuntu/polymarket-bosona-g-continuous/bot/STOP_G'
```

Dört test grubu, hedefli Ruff/syntax, sahte SSH, Londra hesap GET,
120s gerçek kuru koşu, çift kayıtçı başlangıç/rotasyon ve gzip okuma geçti.
Kanıt: validation/proof.tar.gz. Eski pilotun kaynak/state/bütçesi korunur.

## İlk başlangıç sonrası düzeltme

Operatör13:33TR'de başlattı.13:42'de pozisyon API'sinin HTTP hatası,
`maruziyet_teyitsiz` güvenlik kapanışını tetikledi. Süre/kesici kapanışı değil.
Aynı kaynak paketinin düzeltmesinde yalnız ağ hataları üç kez denenir;
ilk hata yeni teklifi kapatır ve mevcut G iptal yolunu devreye sokar.
Geçerli hesap ve mutabakat dönmeden teklif açılmaz. Kalıcı hata yine durdurur.

Aynı başlatma komutu artık RUN mevcutsa `--resume` kullanır. İlk bütçenin
anchor/cutoff/id ve RUN dosyaları aynen korunur; eski state arşivlenir,
yalnız yeni salt-okunur mutabakat sonucu devam state'ine aktarılır.
Kayıtçıların bitmiş parçaları silinmeden arşivlenir. Otomatik restart yok.

Kayıt kullanılabilirliği eski G1 gibi ayrı kapıdır; ayrıştırılmamış mesajlar
olay tamlığı hesabında eksik sayılır ve güvenli hata sınıfıyla kaydedilir.
Süreç/yazma/PONG/kuyruk taşması/disk kapıları korunur. Yeni gerçek testte
iki kayıtçıda birer kamu kopuşu ve birer enum reddi gözlendi;70/70 sağlık
örneği geçerliydi. Bu sıfır veri kaybı değildir. Eski kayıtları koruyan gerçek
kayıtçı yeniden başlangıcı ayrıca test edildi.

Son doğrulama13:53TR: önceki ilk30dk+$9,206315ayrı; yenioturumiki
pencere−$0,3992. Açıkemir/risk0. Orijinal10USD bütçeden kalan yaklaşık9,60USD.
Süre yok; devam komutu yeni10açmaz. Kaynak1c46c9bb8070; politika aynı.
Kanıt:validation/fix2_proof.tar.gz. Paket son kontrolde parkta.

## G3 adayı — 22 Eylül, çevrimdışı hazırlık

G3.patch, güncel G2 ulaşım düzeltmesinin üzerine uygulanacak tek politika
değişikliğidir. Açık yönü artıran alışın fiyatı güncel `bid − 0,01` hedefinin
üzerinde kalırsa iptal edilir. Yenisi ancak iptal teyidi, güncel miktar ve
mevcut yeniden-emir beklemesi sonrasında verilebilir. Azaltıcı teklifler,
5 pay/net limit, minimum miktar, t180/240/290 ve bütçe değişmez. Taker çıkışı
eklenmedi. Bu, Bosona'dan doğrulanmış bir kural değil, teklif bakımı hipotezi.

Kaynak sabitleri G3_PROTOCOL.json içinde: G2 `a5cd853493a6`, aday
`f5cac8add11b`, politika `fbac759df25c`. Canlı kaynağa uygulanmadı; yeni
servis/checkout açılmadı. Test geçici kopyayı bu dizinin validation alanında
oluşturup temizler; gerçek borsa istemcisini kullanmaz.

```bash
/home/taygun/Masaüstü/KararAtlas/base1/bin/python3 -B /home/taygun/Masaüstü/polymarket-bosona/lanes/g_continuous/test_g3.py
/home/taygun/Masaüstü/KararAtlas/base1/bin/python3 -B /home/taygun/Masaüstü/polymarket-bosona/lanes/g_continuous/g3_probe.py
```

11 gerçek karar/iptal-yolu senaryosu ve 6 mevcut regresyon betiği geçti.
İptal belirsizken yeni POST yok; iptal sırasında iki pay dolarsa kalan üç
pay minimum altında olduğundan yeni POST yok. Hedefli lint/syntax geçti.
Kanıt: validation/G3_checks.json.

Önceden sabitlenen dört Londra penceresi: 13:05 ≤ başlangıç < 13:25 UTC.
38/38 parent'ın ACK, özel PLACEMENT ve ilk dolum/iptal yaşam yolu eşleşti;
38/38 nihai miktar özel trade kayıtlarıyla uzlaştı (23 farklı trade-parent
çifti, 99,991763 pay). A/B tekrarları trade-id + parent kimliğiyle birleştirildi;
aynı görünen farklı işlemler korundu. Özel kayıt fiyatlarının alt-mikrodolar
yuvarlaması toplamda 0,00000037 dolar fark verdi; zincir nakit denetimi değil.

Bir Hz karar kaydında 29/38 emrin dolum öncesi teklifi görülebildi; 13'ünde
taze açılış bağlamı vardı. İki ek iptal sinyali bulundu. İlk yerel dolum
bildirimine 52,94 ve 74,13 ms vardı; gerçek iptal RTT medyanı 37,65 ms,
aralığı 26,10–132,01 ms. Bunlar iptalin exchange'de yetişeceğini göstermez.
İki sinyalde de en az bir taze kayıtçı var. İki kayıtçıyı birlikte ve yuvarlak
ms sınırının en az 1 ms öncesinde isteyen kontrolde yalnız 1/2 geçerli:
diğerindeki B verisi 0,538 ms önce alınmış, dolayısıyla zaman sınırı belirsiz.
İlk sinyalde A/B fiyatları da bir cent farklı. Bunu veri yokluğu saymıyoruz.

Önceki ULTRA pilotu ayrı kesittir: 63 parent, 10 sinyal, 8 sonraki dolum;
bu yeni 38 parent ile birleştirilmedi. Dört yeni pencerenin gözlenen G2
sonucu −5,45339963 dolar; G3 sonucu veya önlenmiş zarar hesaplanmadı.
Canlıya geçiş için %95 tam bağlam/zaman kapısı henüz doğrulanmış değil.
Sıradaki ölçüm, her gerçek kararın monoton zamanı ve o andaki emir/rezerv
durumuyla iptal yarışını gözlemek; ardından aynı bütçe içinde önceden
atanmış G2/G3 karşılaştırması. Ekonomik deney henüz başlamadı.

validation/G3_capture.jsonl.gz salt-okunur kaynak kesiti ve hashlerini,
G3_probe.json yeniden çalıştırılabilir hesabı içerir. 16:41:45 TR kontrolünde
G2 writer 178758 çalışıyordu; kaynak/politika/bütçe/RUN/protokol hashleri
korundu (G3_live_unchanged.json). Bu hazırlıkta canlı emir/süreç değişmedi.

## G3 operatör komutu hazır — ölçüm deneyi

```bash
bash "/home/taygun/Masaüstü/polymarket-bosona/londra_g3_baslat.sh"
```

Bu komut kullanıcı tarafından çalıştırılınca mevcut G2'ye normal STOP
gönderir, süreçlerin ve kayıtçıların kapanmasını bekler, eski kaynağı
yedekleyip hashli G3 paketini aynı bot dizinine uygular. Son pencereler ve
hesap uzlaşmadan yeni emir başlamaz. İki kayıtçı başlangıcı mevcut pilot
yolundadır. 5 pay ve süresiz çalışma korunur; BUDGET_G/RUN_G baytları,
başlangıcı ve kesicisi değişmez. Tükenmiş bütçeyle başlamaz, yeni $10 açmaz.
Geçerli G3 zaten çalışıyorsa ikinci geçiş yapılmaz. Zorla süreç öldürmez.

G3 paketi önceden sabit `sha256('ULTRA-Q1|'+str(S))` ilk baytının alt bitine
göre pencere başına G2 kontrol / G3 deney atar. Dolum veya sonuç atamayı
değiştirmez; yaklaşık yarı yarıya dağılımdır, her iki ardışık pencere için
birer tane garantisi değildir. Kontrol yalnız yeni koruma iptalini kullanmaz.
Diğer strateji/risk kuralları ve iki koldaki kayıt yükü aynıdır.

İlk çevrimdışı G3.patch/G3_PROTOCOL.json korunmuştur. Operatör paketi
G3_LIVE.patch, G3_LIVE_PROTOCOL.json ve G3_package.tar.gz ile tanımlıdır;
çalışacak kaynak `f1f175671b6f`, ortak G politika hash'i değişmedi. Paket
Londra'da mevcut dizinin `staging/g3/` alanında park edilmiştir; yeni canlı
model dizini/servisi kurulmadı. Asistan --operator-restart çalıştırmadı.

Yeni SDK kayıtları `g3_quote` ve `g3_cancel_result`: geçerli aktif teklif
bakım kararında UTC/monoton saat, kilit altında alınmış defter zamanı,
envanter, açık/belirsiz emirler ve risk bilgisi; ardından teyitli iptal
sonucu ve öğrenilen dolum. Borsa iptalinin etkinleşme zamanı bilinmediğinde
null kalır. `G3_ATAMA` kayıtları sıfır dolumlu atamaları da izlemeye yarar.
Operatör aktivasyon kaydı boot kimliğini ve saat çiftini saklar. Kayıt
arızası yeni POST'u engeller ve mevcut normal kapanış yolunu tetikler.

Yerel ve Londra: 16 gerçek quote-loop senaryosu + altışar regresyon betiği
geçti. 10 operatör/geçiş kontrolü, sahte SSH ile gerçek shell komutu,
Ruff F/E9 ve syntax geçti. Londra'da Ruff kurulu değil; aynı kaynak hash'i
üzerindeki yerel lint kanıtı doğrulandı, Londra syntax/testleri ayrıca koştu.
360 saniyelik gerçek kamu akışı kuru koşusu iki piyasa/G3 ve G2'yi kapsadı:
1.086/1.086 tam teklif kaydı, 120 kuru teklif/iptal, 31 G3 koruma iptali,
0 kayıt hatası ve 0 WS kopuşu. Gerçek emir/dolum 0; sanal PnL üretilmedi.
Kuru emirler borsa iptal gecikmesini veya canlı kuyruğu doğrulamaz.

Bu, teknik olarak hazırlanmış operatör ölçüm deneyidir. Eski tarihsel %95
bağlam kapısı geçmemiştir; bu boşluk yeni kuru kayıtlarla doldurulmuş
sayılmaz. Canlı iptalin yetişmesi, kaçan iyi dolumlar ve ekonomik fark
henüz ölçülmedi. Sonuç için aynı atanmış pencere başına ücretli net dolar,
belirsiz emirler, risk ve önceden ilan edilmiş ekonomik kapılar geçerlidir.

Kanıtlar: validation/G3_LIVE_checks.json, G3_remote_checks.json,
G3_operator_checks.json, G3_smoke.json ve ham kuru kayıtlar.
Canlı operatör konsolu:
`/home/ubuntu/polymarket-bosona-g-continuous/staging/g3/G3_operator.console.log`.
Gerçek LIVE başlangıcı ayrıca `bot/LOG_g.jsonl` ve SDK oturumundan teyit edilir.

## Operatör sonrası izlem — 22 Eylül 14:14–14:59 UTC

LIVE 14:20:33'te başladı; eski pencere teyidi beklemesi izlem süresine dahil.
14:59:29 kesitinde aynı kaynak ve bütçe, tek writer ve iki sağlıklı kayıtçı;
asistan finansal işlem veya durdurma yapmadı. Yedi atamanın beşi sonuçlandı:
G3 −$2,20 (iki sıfır-dolum dahil), G2 +$2,90; toplam +$0,70. İki bekleyen
pencerenin mevcut terminal aralıkları G2 −$0,555..−$0,54638 ve G3 −$1,25..+$3,75.
Bütçe kısıtı iki G3 penceresini etkiledi; küçük örnek üstünlük kanıtı değil.
On koruma iptali: sekiz dolumsuz, iki dolumlu kapandı. Bu kurtarılmış kâr
hesabı değildir. 4.320 SDK kaydının sırası, 467 kararın saat/kol/rolü geçti.
SDK yazma hatası yok; user enum reddi ve B market yeniden bağlantısı
ölçüm eksikliği olarak korunur. Kesintisiz ham veri kapsamı iddia edilmez.

Kanıtlar `validation/G3_monitor_20260922_polls.json`,
`G3_monitor_session_20260922.jsonl.gz`, `G3_monitor_20260922_summary.json`.
Yerel ve ağsız tekrar kontrolü:
```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/lanes/g_continuous/validation/G3_monitor_check.py"
```
15:03:13 UTC teslim kontrolünde 14:50 G2 sonucu −$0,5463796 olarak geldi;
izlenen kohortun kesinleşen toplamı +$0,1536204, 14:55 G3 sonucu bekliyor.
Sonraki 15:00 penceresi bu karşılaştırmaya katılmadı. Ham 14:59 kesiti
korunur; ek teyit polls JSON içindeki `post_monitor_handoff` alanındadır.

## G4 — bağımsız bütçeli envanter kapasitesi deneyi

G4, G2'nin pasif fiyat bakımını kullanır; G3'ün ek bir-sent iptal kuralını
kullanmaz. Beş paylık emir boyu aynı, net kapasite 5 yerine 10 paydır.
Örneğin 5 Up / 0 Down sonrasında bir 5 Up daha verilebilir; açık/belirsiz
emir rezervi de bu sınırdadır. 10 Up'ta yeni Up yasaktır. Karşı alım hâlâ
yalnız açık fark kadar olabilir; 2 Up / 0 Down durumunda 5 Down ile ters
risk açılmaz. Aynı durumda en fazla 5 yeni Up mümkün olur: kısmi dolum
kilidinin azalması daha fazla yön riski taşımak pahasına gerçekleşir.

Bu sayı Bosona'nın keşfedilmiş parametresi değildir. Gözlenen maker eklemeleri
bu mekanizmayı sınamayı gerekçelendirir; uygun ekleme zamanı/fiyatı veya
ekonomik üstünlük bulunmuş sayılmaz. Taker çıkışı eklenmedi. Miras t180 ağır
taraf bakımı, t240 yeni-risk / t290 azaltım, taraf başına kümülatif $10,
tazelik, kimlik, belirsiz rezerv ve kayıtçı kontrolleri korunur. Bu yüzden
net10 her saniyede ikinci emir veya her pencerede dolum garantisi değildir.
Piyasanın fiyat adımı ve minimum miktarı uygulanır; minimum altı tamamlamayı
yukarı yuvarlamak bağımsız bir yeni risk kararıdır.
[Resmî emir kuralları](https://docs.polymarket.com/trading/place-orders).

Operatör önce yeni $10 dedi, ardından araştırma bütçesini artırma yetkisi
verdi. G4 için seçilen toplam zarar sınırı **yeni $100**; tek emir 5 paydır.
G4 başlangıcı ancak G3 normal kapandıktan ve bütün eski pencereler/emirler
uzlaştıktan sonra olabilir. Toplam hesap geçmişi silinmez: yeni bütçe
anchor'ı başlangıçtaki uzlaşmış PnL, G4 sonucu bunun farkıdır. Aynı G4
tekrarında bütçe/anchor yenilenmez; tükenirse tekrar komut çalıştırmaz.

```bash
bash "/home/taygun/Masaüstü/polymarket-bosona/londra_g4_baslat.sh"
```

Komut, mevcut Londra G dizinindeki `staging/g4/g4_operator.py` aracını
çağırır. Yalnız açık `--operator-start` normal STOP ve yeni bütçeyi aktive
eder. Varsayılan çağrı paket/kaynak denetimidir. Yeni masaüstü veya canlı
model kopyası yok. `G4_before_activation` eski kaynak/RUN/BUDGET/state'i
korur; `G4_ACTIVATION.json` tek aktivasyonu sabitler. Yarım kurulum veya
bilinmeyen kaynak kapalı kalır, otomatik budget reset yapılmaz.

`G4_ATAMA`, `g4_quote` ve `g4_cancel_result` kayıtları tüm uygun pencerelerde
G4 etiketi taşır. G2/G3 dönüşümlü kontrol yoktur. Tarihsel sürüm farkları
eş-zamanlı rastgele deney sayılmaz; atanmış/sıfır-dolum/eksik/bekleyen ve
bütçe kısıtlı pencereler ayrı raporlanmalıdır. Gerçek net dolar, net miktar,
en kötü ödeme ve açık-pay-saniye birlikte izlenmelidir. Eski dolumlara ikinci
emir eklenerek hayali G4 kârı hesaplanmaz.

Ağsız tekrar kontrolü:
```bash
python3 -B "/home/taygun/Masaüstü/polymarket-bosona/lanes/g_continuous/test_g4.py"
```

Paket `G4_package.tar.gz`, kaynak farkı `G4.patch`, kimlik `G4_PROTOCOL.json`.
Operatör günlüğü:
`/home/ubuntu/polymarket-bosona-g-continuous/staging/g4/G4_operator.console.log`.
LIVE başlangıcı ayrıca gerçek `bot/LOG_g.jsonl` ve bütçe kaydıyla teyit edilir.

22 Eylül16:25UTC hazırlık teyidi: kaynak `0fd30f9faee2`, yerel/Londra altışar
regresyon ve dokuz gerçek teklif-döngüsü senaryosu geçti. Yeni bütçe/aynı
bütçeyle devam/tükenme/yarım kurulum testleri geçti; yerel Ruff ve iki ortamda
syntax temiz. 120sn gerçek kamu kuru koşusunda790teklifkaydı,60kuruPOST ve
60iptal,0SDKhatasi/0WSkopuşu var. Gerçek emir/dolum0, kâr simülasyonu yok.
Canlı G3 kaynak ve bütçe hashleri korunuyor. `validation/G4_READY.json`
hazırlık sınırlarını ve yerel/uzak test/kuru koşu kanıtlarını bağlar.

## G5 hazırlığı — 22 Eylül, canlı kapalı

G4 operatör isteğiyle17:40:28UTC'de normal durdu. G5, t180 bakım çelişkisi
giderilmiş ortak kaynak üstünde yeni-risk teklifini yukarı kovalamama
deneyi olarak hazırlandı. G4_FIXED kontrolüyle aynı net10/5pay sınırları
ve sabit pencere ataması kullanır. Canlı aktivasyon veya yeni bütçe yok.
Okunabilir aday kaynak, protokol, test ve açıklama:
[staging/g5/README.md](staging/g5/README.md). Yayımlanmış `bot/` G4'ün
donmuş kaynağıdır; G5 adayı `staging/g5/bot/` içindedir.
