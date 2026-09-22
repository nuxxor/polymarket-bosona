# BTC15dk zaman, olasılık ve uygulanabilirlik denetimi

**Karar: mevcut aday ekonomik olarak doğrulanmadı.** Donmuş kod ve protokol
değişmedi. Gerçek S defterleriyle sonlu tekrar 14 tam kapanmış piyasada iki
giriş, sıfır ekleme üretiyor. Tamamlama kolu ve yönetilen kol aynı; ücretli
senaryo sonucu −1,30057 dolar. İlk alımı tutma +0,78343 dolar. Fark, aynı
girişten sonra yapılan tek karşı alımdır; risk azalır fakat gerçekleşen
sonuçta kazanç 2,084 dolar azalır. Bu küçük örnekte bile “ucuza tamamlama”
ile “sonucu daha iyi tahmin etme” ayrı hedeflerdir.

Kaynak kısaltmaları ana prompttaki MAIN/R/F/S ile aynı. Bu dizindeki bütün
çıktılar bağımsızdır; MAIN/R/F/S yalnız okundu. S, bilinen karşı örnektir;
S sonrası fiyat/defter/sonuç bu alt analizde açılmadı.

## 1. Gerçek zaman hatası: gereksiz eksik veri ve değişen olasılık

**DOĞRULANDI.** `R/btc15_context.py:58–62,79` ve
`R/src/bosona_derin.py:331–336`, örneğin karar t anında t−10 fiyatını
isterken, fiyatın t−10'a kadar **alınmış** olmasını da zorunlu kılıyor.
t−10 olayının t−9'da gelmiş olması, t anında tamamen bilinebilir olduğu
halde bu gözlemi dışlar veya daha eski örneğe kaydırır. Bu gelecek sızıntısı
değil; tarihsel örnek zamanı ile bilgi erişim zamanının karışmasıdır.

Kendi `audit.py:60` işlevim geçmiş hedefe göre en yeni olay zamanını seçer;
alınma zamanı yine **karar zamanından geç olamaz**. Güncel spot/TWAP için
hem olay hem alınma yaşı ≤3000 ms kalır. Geçmiş örneğin olay yaşı da kendi
hedefinden ≤3000 ms kalır. Eşik gevşetilmedi. Bu küçük düzeltme modelin
sigma/olasılık girdisini değiştirdiğinden yalnız “veri kapsamı onarımı”
adıyla ekonomik sonuç karşılaştırması yapılmamalı.

| Ölçü | Donmuş davranış | Olay zamanı geçmişi |
|---|---:|---:|
| 28.920 istekten geçerli bağlam | 20.533 | 20.881 |
| 816×12 planlı aday kararından geçerli fiyat bağlamı | 7.046 | 7.158 |
| t180 giriş bağlamı | 591 | 600 |
| S 168 planlı karardan geçerli fiyat bağlamı | 167 | 168 |

348 bağlam geri gelir; 112'si aday ızgarasındadır. Ortak 20.533 bağlamın
18.736'sında olasılık değişir. En büyük eksik hâlâ 7.473 istekte başlangıç
referansının olmamasıdır; bu düzeltme onları kurtarmaz. Eski 20.533
olasılık, kaynakların SHA kontrolü sonrası **1e−10 toleransla birebir**
yeniden üretildi. Kaynak toplamı ~32 MB sıkıştırılmış çıkarılmış arşiv;
18 GB ham banda girilmedi.

Donmuş adayın 36 eski fiyat senaryosu aynı kaynak kodla, yalnız bu bağlam
değiştirilerek kendi dizinimde tekrar çalıştı. Ana sıfır kaymalı indirim
girişleri 21→23: dört eski giriş gider, altı yeni giriş gelir. Ortak 17
girişin sonraki yolları aynı; ekleme yine yalnız birdir. Yönetilen kolun
örnek-fiyat sonucu +6,03304→+10,33716 dolardır. Bu artış bir strateji
önerisi veya gerçekleşebilir geçmiş kazanç değildir; hatanın gerçekten
karar seçimini değiştirdiği kanıtıdır. Bütün 36 karşılaştırma korunmuştur.

S'de tek kurtarılan karar `1790003700` t600'dür; aday o piyasaya hiç
girmediği için işlem değişmez. Ayrı olarak, sigma değişimi `1790007300`
t180 Down girişini kaldırır: donmuş ücret sonrası model farkı 5,04445¢,
düzeltilmiş fark 4,49952¢. Düzeltmeyle S bir girişe ve +0,52906 dolara
döner. Eşik değiştirilmedi; kaybın sonradan kaldırılması başarı sayılmaz.

## 2. Başlangıç/son TWAP ve erişim saati

**DOĞRULANDI.** S'nin 14 başlangıç referansı kaydedilmiş tam başlangıç
olay-zamanlı TWAP'tır; sonradan Gamma'dan uydurulmadı. Alınma gecikmeleri
882–1781 ms ve t180'den öncedir. 14 başlangıç fiyatı resmî `priceToBeat`
ile tam eşit. Nihai fiyat alanı bulunan 13 piyasada bitiş TWAP'ı da tam
eşit; son piyasada Gamma `finalPrice` eksik, tamamlanmış token sonucu
mevcut. Bitiş TWAP karşılaştırması 14/14 token sonucuyla uzlaşır.
Son fiyat yalnız doğrulamaya kullanıldı; hiçbir karara verilmedi.
Kanıt: `s_reference_checks.json`.

**DOĞRULANDI — fiyat kaynağı yereldir.** Salt okunur `/proc` gözlemi:
PID 63900, 20 Eylül'den beri `python3 -u cl_direct_rec.py`; çalışma dizini
`/home/taygun/Masaüstü/polymarket/data/analysis/pm_chainlink_history_20260913_v1`;
açık fd yerel `data/tape_cl_direct/cld_20260921_18.jsonl.gz`.
`MAIN/kaydediciler/chainlink/cl_direct_rec.py:34` yerel `time.time()` ile
rcv yazar; 45–46'da diske yazıp flush eder. Süreç kaynak dosyası ile
MAIN kopyasının SHA'sı aynıdır. 14–17 kapalı saatlerin özgün yerel dosya
SHA'ları da MAIN aynasıyla birebir eşleşir. Özgün dosyaların kapanma
mtime'ları 15/16/17/18 UTC; MAIN kopyaları 18:35'te güncellenmiştir.
Kopyalama yolu `MAIN/analiz/izleme/depo_senkron.sh:18`'dir.

Dolayısıyla MAIN aynasının 18:35 mtime'ı fiyatın olay/alım zamanı değildir.
Kaynak veri aynı makinede daha önce vardı. Karar motorunun o anda okumuş
olduğunu iddia etmiyoruz: karar yazıcısı çalıştırılmadı, rcv→flush→tüketici
gecikmesi ayrıca kaydedilmedi. `local_price_provenance.json` dar kanıttır;
Londra alım saati diye sunulmamalıdır. Çalışan sürece müdahale edilmedi,
kimlik bilgileri okunmadı veya kimlik doğrulamalı istek yapılmadı.

Tarihsel `priceToBeat` kontrolü (`btc15_context.py:74–77`) sonradan alınan
metadata ile veri doğrulamasıdır. İleri üretimde “metadata bugün eksikse
geçmiş karar yok” filtresine dönüştürülmemeli. Eski kayıtlarla birebir
yeniden üretimde referans uyuşmazlığı yüzünden atılmış ek bağlam yok.
Binance kapalı mum+2sn, `R/research.py:250` için açık bir yayın varsayımıdır;
gerçek HTTP erişim zamanını kanıtlamaz. BTC15 adayında Binance girdisi yoktur.

## 3. Olasılık: matematik doğru, kalibrasyon güvenilir değil

`R/src/bosona_derin.py:339` sıfır sürüklenmeli Brownian yaklaşımında son
60 saniyelik ortalamanın varyansını kalan süre r≥60 iken σ²(r−40),
r<60 iken σ²r³/10800 hesaplıyor. İki formül r=60'ta birleşir. Bağımsız
sayısal kovaryans integrali kontrolü geçti. Son dakikada bilinen bölüm
1 saniyelik sol Riemann toplamıdır. Adayın son kararı t840 olduğundan
aday kararında kısmen bilinen son dakika dalı kullanılmaz; aktör geç
dolumlarının betimlenmesinde kullanılır.

Bu formül Chainlink hesabının tam kopyası değildir. Resmî belge özel
TWAP'ın örnekleme, ağırlık, yuvarlama ve eksik-girdi kurallarının
yayımlanmadığını belirtiyor. Gerçek başlangıç ve bitiş için imzalı
akış değeri gerekir. [Resmî TWAP belgesi](https://docs.polymarket.com/market-data/chainlink-twap).

**KARŞI KANIT.** 18–20 Eylül ortak piyasalarda donmuş olasılık ile aynı
karar noktasındaki kamu Up fiyatı karşılaştırıldı. Fiyat örneği gerçek
ask değildir; gecikmesi aşağıdadır. Piyasa başına bir gözlem tutulmuştur.

| Yaş | n | Model Brier | Fiyat Brier | Model log kaybı | Fiyat log kaybı | Fiyat yaşı ort. |
|---|---:|---:|---:|---:|---:|---:|
| 180 | 173 | 0,22876 | 0,22773 | 0,67433 | 0,64578 | 45,65sn |
| 600 | 170 | 0,19933 | 0,16623 | 1,08277 | 0,49668 | 45,01sn |
| 840 | 170 | 0,04591 | 0,09430 | 0,22159 | 0,31549 | 45,81sn |
| 870 | 170 | 0,01313 | 0,03610 | 0,09191 | 0,11573 | 17,34sn |

t600'de %99'dan emin 64 tahminin dokuzu yanlış. p≥0,9 grubunda 59 piyasa,
ortalama tahmin %98,12, gerçekleşen Up oranı %81,36. p<0,1 grubunda 42
piyasa, tahmin %1,41, Up oranı %14,29. Bu modelin 5¢ farkını güvenilir
beklenen gelir diye okumak hatalıdır. Geç dakikada düşük Brier, gecikmeli
fiyat kontrolüne kıyas üstünlük gösterebilir; alınabilir güncel defterde
ekonomik üstünlüğü göstermez. Yeniden kalibrasyon veya ters sinyal seçimi
yapılmadı. Üç kontrol günü önceden görülmüştür; temiz test değildir.

## 4. S karar kapsamı, gerçek gecikme ve uygulama sınırlamaları

**DOĞRULANDI.** 14×12=168 planlı karar tutuldu. 156'sında iki taraf da
taze, ≤3¢ spread ve 5 pay ask derinliği bakımından uygundur; kalan 12
kararda iki tarafın da bid/ask eksiktir. Tek geçerli taraflı karar yok.
Donmuş fiyat bağlamı ile ortak kapsam 155/168=%92,26; düzeltilmiş geçmişle
156/168=%92,86. Tam protokolün ≥%95 kapısı geçilmez. Snapshotların
%90,89'luk taraf uygunluğu ile karar ızgarası kapsamı farklı paydalardır.

168 noktanın hepsinde karardan ≥250ms sonra istenen ve ≤3sn içinde
alınmış bir sonraki snapshot bulunur. Alım gecikmesi minimum399,
medyan1039,5, maksimum1393ms'dir. Bu bant tam +250ms uygulama fiyatı
vermez; ölçülen yaklaşık bir saniyelik sonraki defter senaryosunu verir.

Bütün 14 giriş anının fiyat ve iki defter verisi tamdır. Donmuş model
dokuz kez 5¢ farkında, üç kez 55¢ tavanında elenir; iki niyet gerçekleşebilir
derinlik varsayımında kabul edilir. Eksik veri ile sinyal yok ayrıdır.
Kayıt başlangıcı sonrası tam slot tanımı, ilk saniyenin karar öncesi
defterini garanti etmez: tam 14 piyasadaki 126 aktör dolumunun ikisinde
−5sn ve altısında −10sn defter yoktur; hepsi ilk saniye grubundadır.
İlk snapshot slot başlangıcından 278–1218ms sonradır. 54 geç eklemede
bu özel boşluk yoktur. Gözlenen küçük dolum, bağımsız yeni emir değildir.

**DOĞRULANDI.** Kamu ücret formülü pay×oran×p×(1−p), kripto oranı0,07;
beş ondalık ücret yuvarlaması `ask_cost` ile uyumlu. Maker ücretini
Bosona'ya tekrar eklemedik; yeni politika yalnız taker senaryosudur.
[Resmî ücret](https://docs.polymarket.com/trading/fees).

**DOĞRULANDI — adaptör tam uygulama değildir.** `R/candidate.py:107–129`
token, istek/alım/borsa zamanı, spread, derinlik, son fiyat farkı ve
FIFO/risk sınırını kontrol eder. Ancak conditionId, minimum emir miktarı,
güncel tick ve context karar zamanını ayrıca doğrulamaz. Dört ayrı
sentetik negatif kontrol, bu eksiklerin gerçekten kabul edildiğini
gösterir (`check.py`, `checks.json`). S'de yanlış-token/condition/context
girdisi verilmedi; kendi bağımsız okuyucum bunları doğru eşledi. Gerçek
kabul edilen üç sanal dolumun tamamı 5 paydır. Bu sınır eksiklerini
S'deki zararların nedeni saymıyoruz.

26.438 taraf snapshotının minimumu 5 paydır; 2.996'sının tick'i0,001,
23.442'sinin0,01. Gamma başlangıç tick'i0,01 olduğundan 2.996 snapshotta
Gamma ile güncel defter farklıdır. İşlem anı tick'ini snapshot/olay
akışından okumak gerekir. Tam 14 piyasanın 16 dolumu, geç eklemelerin
sekizi 5 paydan küçüktür; bunlar büyük parent emrin kısmi dolumları
olabilir. Bunları yeni bağımsız emir diye kopyalamak minimumu ihlal eder;
Bosona'nın emrinin geçersiz olduğunu kanıtlamaz.
[Emir koşulları](https://docs.polymarket.com/trading/place-orders),
[defter alanları](https://docs.polymarket.com/api-reference/market-data/get-order-books-request-body).

Adaptörün tam derinlik istemesi FOK benzeri tümü/hiçi varsayımıdır;
emir tipi, gerçek kabul/dolum ve kuyruk yoktur. VWAP ekonomik maliyet
tavanıdır; gönderilebilir limit fiyatıyla aynı şey değildir. Tick'e
uygun en kötü tüketilen fiyat ve kısmi dolum muhasebesi bir üretim
adaptöründe ayrıca tanımlanmalı. Bunları hayalî başarılı dolumlarla
doldurmadık; test yalnız mevcut snapshot karşısındaki sonlu simülasyondur.

## 5. Kendi envanterindeki somut yollar ve portföy sınırı

| Piyasa/yaş | Karar öncesi | Sanal uygulama ve risk | Resmî sonuç |
|---|---|---|---|
| 1790007300 /180 | Up olasılığı0,58363; Down ask0,35; 5¢ fark ancak geçiyor; envanter0 | +5Down, nakit1,82963; en kötü−1,82963 | Up: −1,82963 |
| 1790011800 /180 | Up olasılığı0,42630; Down karar ask0,48; envanter0 | Sonraki ask0,46; +5Down, nakit2,38694; en kötü−2,38694 | Down; yalnız tutarsa+2,61306 |
| Aynı /240 | 5Down; Up ask0,47; karar çift maliyeti≤0,98 | Sonraki defterde çift limiti kaybolur; işlem yok | Önceki envanter korunur |
| Aynı /300 | 5Down; Up karar ask0,37 | Sonraki ask0,40; +5Up, yeni nakit2,08400; toplam4,47094; her iki sonuç+0,52906 | Down: +0,52906 |
| Aynı /600 | 5Up+5Down, açık yön0 | Ekleme yok; aday yeniden risk açmaz | Sonuç değişmez |

Diğer 12 piyasada kendi giriş yok; bu sıfır sinyal/reddin sonucudur.
Bosona `1790007300` piyasasında hiç işlem yapmamışken aday kaybeden
Down'a girer: aday, aktör ilk giriş seçilimini taklit etmiyor. Tarihsel
21 girişin dokuzu t600 öncesinde bir tamamlama almış; 12'si sonda tamamen
nötrdür. Envanteri erken kapatma ve hiç yeniden açmama, yüzlerce Bosona
eklemesini açıklayamamanın somut yapısal nedenidir. Erken tamamlama
mutlaka kötü değildir; kötü sonuç riskini düşürür.

`candidate.py:32` piyasa başına15 dolar alış/10 açık pay/5 dolar en kötü
kayıp uygular; FIFO kısmi tamamlama ve fazlayı engelleme regresyonu geçer.
Portföy bütçesi, çözümlenmeyi bekleyen para, bütün varlıkların envanteri,
gün içi−10 yeni-risk kesicisi, kalıcı state/restart ve scheduler yoktur.
README bunları zaten açık eksik sayıyor; varmış gibi ekonomik kabul
uygulanamaz. S'nin iki girişi arasında75dk var ve zarar−10'a ulaşmıyor;
bu kısa tekrar portföy eksikliğinin sayısal kayıp etkisini göstermiyor.

## 6. Tekrar ve doğrulama

Çalıştırılan komutlar (çıktılar yalnız bu dizinde):

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/execution/audit.py
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/execution/sensitivity.py
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/execution/check.py
python3 -m ruff check --no-cache /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/execution/*.py
```

`audit.py` bütün eski bağlamı yeniden üretir, güncel olmayan S kesitini
dondurulmuş `s_prices.json.gz` üzerinden tekrar eder. Gzip kendi dosyalarında
mtime0 ile deterministiktir. `sensitivity.py` donmuş aday kodunu yalnız
kendi çıktı kökü ve düzeltilmiş bağlam ile çağırır; ortak dosyaya yazma
assert ile reddedilir. Yeni bağımlılık yok. `check.py` tarih erişimi,
gelecek veri, güncel3sn reddi, varyans integrali, adaptör negatif kontrolleri,
14 gerçek piyasa, eş girişli kollar, risk/FIFO/nötrden açılmama, syntax ve
korunan hashleri doğrular. Ruff geçti.

Son tam tekrar `audit.py → sensitivity.py → check.py` ile çalıştırıldı;
11 hesap/veri artifact'i aynı SHA256 üretti (`reproduction.json`).
Gerçek S defterinden bağımsız Decimal fiyat+ücret hesabı da uzlaştı.

`official_sources.json` resmî Markdown URL'leri, istek/alım zamanları ve
SHA'ları; `official/` ham cevapları içerir. Fiyat ham prefixi, kitap SHA'sı,
korunan kaynak SHA'ları `results.json` içindedir. Ana istatistikler
`calibration*.json`, kararlar `s_decisions.json`, envanter yolları
`s_candidate_replay.json`, tarihsel etki `history_policy_sensitivity.json`.

Son hüküm: zaman erişimi düzeltmesi ve eksik adaptör sözleşmeleri önce
onarılmalı; kalibrasyon ve aynı başlangıç envanterinde risk azaltımı
araştırılmalı. Daha çok ekleme üreten yeni eşik seçmek için kanıt yok.
S ve tarihsel senaryolar stratejinin kabul kapısını geçmez: **UNDERPOWERED**;
Bosona'nın emir seçimini kamu dolumundan tek başına çıkarmak **NOT IDENTIFIABLE**.
