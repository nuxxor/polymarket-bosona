# G2 sonrası bağımsız inceleme — ULTRA, 22 Eylül 2026

**Birkaç çıkış ayarıyla Bosona'ya ulaştığımızı düşünmek için yeterli kanıt yok.
G2 korunmaya değer bir yürütme ve muhasebe tabanı; Bosona'nın fiyatlama ve hedef
envanter mekanizması hâlâ eksik. İlk ekonomik deney önceliğim, yeni taker stop
eklemekten önce mevcut maker teklifinin aleyhe fiyat değişiminde korunmasını
sınamak.** Bu önceliğe güvenim orta; “G2 artık Bosona'ya yakın” iddiasının
kanıtlanmadığına güvenim yüksek. Seçici taker azaltımının gerçekten var olduğuna
güven yüksek, bağımsız kârlı tetikleyicisinin bulunduğuna ilişkin kanıt yok.

Bu sonuç yalnız eski raporların özeti değil: 2.041 receipt yeniden çözüldü,
erken fiyat bağlamları arşivden kurtarıldı, sabit zamanlı kontrollerde iki basit
çıkış fikri hesaplandı ve kendi gerçek maker dolumlarımızın sonraki fiyatı ölçüldü.
Başka incelemecinin yeni G2 çıktısı okunmadı. İlk hipotezler yeni bağlam
sonuçlarından önce `mechanism_protocol.json` içine yazıldı; geçmiş günler
önceden araştırılmış olduğundan bu kör ön kayıt değildir.

**Erişim, sürüm ve kesim.** Gerçek HEAD
`01ea1dc6be98a8cbc57b796dc066c4e6a8404cc1`; çalışma ağacı kirliydi.
Yetkili kaynak `lanes/g_continuous/identity_fix/bot/`; `ab.py` SHA256
`25fca69d4ad75a3a28db9f62903f4c300a8adafdc7e923bc942f87eb6699d64c`,
politika SHA256 `fbac759df25cecf10ea01bbf9db9da5e07dd90f3b33e844125c51e434eaf2f61`.
Release içindeki 16 dosya doğrulandı. G2, G1'in kimlik/mutabakat düzeltmesidir;
strateji değişikliği değildir. Başlangıç manifesti 238 ilgili dosyanın hash'ini,
alt hesaplar kullanılan diğer girdilerin hash'lerini saklıyor.
Son kontrolde bu 238 girdinin 236'sı aynı kaldı; değişenler ortak `plan.md`
ve eşzamanlı yayın çalışmasında açıklaması güncellenen brief idi. İnceleme
başlangıcındaki G2 kaynakları ve ekonomik veri kesimi değişmedi. Ortak planda
sonradan açılan API kesintisi çalışması bu incelemenin kapsamına alınmadı.

Yerel karşılaştırmada yalnız `cuts/1790075698` bulunuyor: toplama başlangıcı
**22 Eylül 11:14:58 UTC**, derleme **11:15:54.136 UTC**. On kapanmış ve bir
sonucu bekleyen piyasa var. İki saatlik ileri toplama tamamlanmış değil.
G2'nin **12:07:30 UTC / 15:07:30 TR** başlangıcı, `runtime_after_operator.json`
arşivinden doğrulanan tarihli kanıt; bu çalışma güncel Londra runtime kontrolü
yapmadı. Yerel ekonomik karşılaştırmanın tamamı G2 öncesidir. Yeni canlı 999
olayı görülmüş sayılmadı; tarihsel gerçek olay izole testte yeniden üretildi.

Tüm yeni hesaplar [ULTRA dizininde](../data/analysis/g2_next_review_ultra_20260922/).
Bu inceleme üretim kodunu, state'i, bütçeyi, servisleri ve donmuş araştırma
çıktılarını değiştirmedi.

**1. Veri envanteri ve 6/26 dar boğazının gerçek nedeni**

| Girdi | Bu incelemede doğrulanan kapsam | Sınır |
|---|---|---|
| Ana tarihsel activity | 13 Eylül 00:00–20 Eylül 22:30 UTC; 2.286 takvim slotu, 1.842 gözlenen piyasa, 19.768 BUY, 36 bitişik sorgu dilimi | 444 diğer slot otomatik sıfır işlem değildir |
| R1 | 137 piyasa, 2.066 BUY, 2.041 transaction, 986 dolmuş parent; bütün receipt'ler yeniden çözüldü | 64 hash örneği, 66 geç-ekleme ve 14 tanısal piyasa örtüşür; birleşim temsil örneği değildir |
| Ana mekanizma örneği | Önceden seçilmiş aynı 64 piyasa; 305 parent, 262 sınıflı, 43 belirsiz | Evren sonuçlara göre değiştirilmedi |
| Yeni bağlam hesabı | 262 parent + tüm 64 piyasada iki sabit kontrol = 390 satır; her birinde kamu zamanı−5/−10 saniye | Kontrollerin 46'sı azaltıcı dolum gözlenmeyen 23 piyasadan; “hedge etmemeyi seçti” etiketi yok |
| Eski ham tape | Harici belirtilen yolda 124 gzip saat, yaklaşık 18,65 GB; sıkıştırılmış çıkarımlar mevcut | Tüm ham arşiv yeniden taranmadı; seçili cache'ler ve hedefli ham doğrulama kullanıldı |
| Yeni defter veritabanı | Yaklaşık 142 GB SQLite erişilebilir; seçili 9 piyasada hedefli olay yeniden kurma | Büyük dosyanın varlığı bütün günlerde BTC5m kapsamı demek değil |
| Ek arşivler | `data/bosona/activity.jsonl`: 19–21 Eylül, 448 piyasa/4.392 BUY; eski CSV: 14 Ağustos–1 Eylül, 4.074 türetilmiş satır | Örtüşme/çokluk/parent kapsamı baştan denetlenmedi; ana toplama eklenmedi |

Ana geçmişte gerçek çoklukla alış nakdi **$375.049,792805**, kazanan token
ödemesi **$383.363,021269**, işlem sonucu **+$8.313,228464**. Eski 19.761
kayıtlı ledger yedi gerçek tekrarı silerek sonucu **$6,21 fazla** gösteriyordu;
düzeltme kârı azaltıyor. Bu hesap rebate ve sabit gider hariç BTC5m alışlarının
terminal değeridir; bütün hesap geliri değildir. Kimlikler ve UTC gün dökümü
`accounting/results.json` içinde; ana evrenin dışında kalan eski CSV eklenmedi.

R1'in 137 tam API geçmişinde 2.066 BUY, 51 MERGE ve 256 REDEEM mikro-birim
tamsayılarla yürütüldü; her piyasada nakit artı kalan kazanan token terminal
servetle tam uzlaştı. Gözlenen pencere öncesi BUY ve negatif token bakiyesi
yok. 2.041 BUY receipt'inde API/zincir miktar ve nakit farkı sıfır;
$47.351,874451 nakde dahil $218,732940 ücret tekrar eklenmedi. **Başlangıç
zincir bakiyesinin sıfır olduğu, harici TRANSFER olmadığı veya MERGE/REDEEM
receipt'lerinin ayrıca çözüldüğü iddiası yok.** Kamu geçmişi bu sınırları
ortadan kaldırmaz.

Eski `bosona_derin.py:79` çıkarıcısı t10–299'u saklıyor; `:399` okuyucusu
t180 öncesini, `:514` özellik çalışması da erken dolumları dışlıyor.
Dolayısıyla **6/26, bütün arşivin sınırı değildi**. Erken cache'leri açıp yeni
SQLite olaylarını nedensel olarak yeniden kurunca **19/26** için taze defter,
spot, TWAP60 ve karar öncesinde yayımlanmış başlangıç referansı bulundu:
**13 erken + 6 geç olay**. Burada erken/geç ayrımı t200'dür.

| Sınıf | Toplam | −5sn birleşik bağlam | −10sn birleşik bağlam |
|---|---:|---:|---:|
| Taker azaltım | 26 | 19 | 19 |
| Maker azaltım | 48 | 30 | 30 |
| Maker ekleme | 101 | 68 | 70 |
| Maker sıfırı aşma | 14 | 8 | 9 |
| Tüm sabit kontroller | 128 | 83 | 85 |

Tek tek defter, spot, referans, TWAP, derinlik ve saat kapsamları
`context/summary.json` içindedir; hepsini gerektirmeyen testler kendi geçerli
paydasını kullanır. Örneğin tam aktör envanterini defterden kapatacak derinlik
−5sn'de yalnız 9/26 olayda doğrulanıyor; beş paylık fiyatın bulunması yüzlerce
payın aynı maliyetle kapatılabileceği anlamına gelmez.

Eksik yedi olayın nedenleri somut:

- Bir olay, erişilen ham tape'in 13 Eylül 13:00 başlangıcından önce.
- Dört olay, eski tape sonu ile 19 Eylül 15:10'daki yeni BTC5m DB başlangıcı
  arasındaki kapsam boşluğunda.
- Aynı 20 Eylül 13:10 piyasasının t63 ve t141 olaylarında kayıt kesilmiş;
  ilgili saat dosyalarının ilk kaydı 13:13:47'de. Bu iki hedef an kaydedilmemiş.

Bu yokluk hükmü **erişilen arşivlerdeki bu anlar** içindir; dünyada başka kayıt
olmadığı iddiası değil. Sonradan alınmış backfill dosyaları mevcut; bunları o
anda alınmış fiyat gibi kullanmadım. Londra'nın yeni G2 kamu kayıtları bu yerel
pakette yok; hiç üretilmedikleri sonucunu çıkarmadım. Bosona'nın dolmayan
emirleri, kesin gönderim/iptal saatleri ve kuyruk sırası kamu L2'den çıkmıyor.

Saat düzeltmesi önemlidir: eski `exchange_age`, `bosona_derin.py:577` içinde
kamu WS mesajının `obs` zamanından geliyor; gerçek exchange/karar saati değil.
Yeni bağlamda kaynak ve alınma saati karar kesiminden ileri olamaz; defter
tazeliği en fazla 3 saniye, cache eşlemesi en fazla 1,25 saniye geridir.
Taker azaltımlarında −5sn ile dolum öncesi arasında dört, −10sn'de altı olayın
neti değişmiş. Özellik kesimindeki envanteri ayrıca hesapladım; aşağıdaki
ana koşul karşılaştırması bu farkı taşımayan satırları kullanıyor.
Buradaki envanter yaşı, piyasanın ilk gözlenen dolumundan geçen süredir;
mevcut yönün kesintisiz yaşı değildir. Netin aynı kalması araya hiç dolum
girmediğini genel olarak kanıtlamaz. DB yeniden kurmada tazelik ve L1
tutarlılığı sınandı; bağlantı boşluğunda kaçmış bütün derinlik deltalarının
yokluğu kanıtlanmadı. Bu yüzden fiyatlanan derinlik tam yürütme garantisi değil.

**2. G2 hangi açıdan ilerledi, hangi açıdan hâlâ farklı?**

G yolu `g.py:8` ile `--lane-g` açıyor; F altyapısını devralması F sinyalini
kullandığı anlamına gelmiyor. `g_policy.py:19` hedefi gerçek tick'e aşağı
yuvarlanan **bid−1 sent**; `:35` yeni risk için t240, azaltım için t290 sınırı.
`ab.py:1034` gerçekleşmiş miktar ve açık/belirsiz rezervleri birlikte sayıyor.
`ab.py:1420` uygun emri bid ile bid−2 sent arasında tutuyor. Taraf başı
**kümülatif** $10 harcama/rezerv ile hesap zarar bütçesi ayrı. Evrensel 98 sent
çift tavanı veya etkin taker kapanışı yok. Rebate peşinen yazılmıyor.

İki yeni teknik bulgu da gerçek fonksiyonlarla sınandı:

- **Küçük miktar kilitlenmesi:** Açık emir kalmadan 2 Up/0 Down varsa aynı
  yönde yalnız 3, karşı yönde 2 pay izinli; ikisi de mevcut 5 pay minimumunun
  altında. İlk pilotun 2/6 penceresi kesirli netle bitti: −0,004285 ve
  −4,990371 pay. Minimumu aynı kalan bir taker eklemek bu sorunu tek başına
  çözmez. Sırf kapatmak için 5'e yukarı yuvarlamak yeni ters risk açar.
- **Miras bakım kuralı:** `pencere_bakim` (`ab.py:1890`), G'de de
  `denge_koru`yu (`:1697`) çağırıyor. t180 sonrası net fark≥0,01 ise ağır
  taraftaki kısmi açık emri iptal ediyor. Sahte borsada t179/t180 farkı
  yeniden üretildi; incelenen gerçek pilotta bu iptal gözlenmedi. Bu yüzden
  geçmiş kayıpların açıklaması diye kullanılmadı. Protokolün t240 özeti
  gerçek bütün bakım yolunu anlatmıyor.

| Aynı yakın dönem ölçüsü | G | Bosona |
|---|---:|---:|
| On kapanmış piyasada BUY / dolmuş parent | 54 / 50 | 63 / 26 |
| Pay / taker payı | 247,666086 / 0 | 3.490,907799 / 720,92 |
| İkisinin de işlem yaptığı sekiz piyasada ilk dolum medyanı | t10 | t147,5 |
| Aynı sekizde ilk dolum nakit fiyatı medyanı | 0,40 | 0,345 |
| İlk taraf uyumu | 3/8 | — |
| Piyasa başına toplam beş alınan paya ölçeklenmiş sonuç | +$1,699060 | −$1,172011 |
| Aynı ölçekle mutlak net envanterin zaman integrali, sekiz piyasa medyanı | 195,00 pay·sn | 292,90 pay·sn |

Ölçeklenmiş sonuç farklı turnover'ı betimler; aynı sermaye/riskte uygulanabilir iki
politika değildir. İlk altı pilotun ortak beş piyasasında ilk yön uyumu 0/5.
Bosona'nın ilk **dolumunun** geç olması, teklif vermeye geç başladığı kanıtı
değildir. G daha kârlı göründüğü için modeli doğru, Bosona daha büyük olduğu
için modeli üstün ilan edilemez. Güncel G bir klip net sınırıyla çalışırken
Bosona aynı yönde çok sayıda ayrı parent ile büyüyebiliyor.
Son satır tutma süresi ve büyüklüğü birlikte ölçer; yalnız saniye cinsinden
ortalama pozisyon ömrü değildir. Aynı sekizde G tam sıfırdan 16 kez yeniden
açılıyor. Bosona için mikro-artıklar bu dar tanımı bozduğundan sıfır çıkan
aynı sayaç “yeniden açılmıyor” diye yorumlanamaz; tarihsel yakın-sıfır yolları
aşağıda parent düzeyinde ayrıca incelendi.

999 normalizasyonu, çokluğu koruyan mutabakat, özel emir/trade kaydı ve çift
kayıtçı **ölçüm/işletim ilerlemesidir**. Maker rolü ve envanter sınırı davranışın
iki unsuruna yaklaşır. Giriş zamanı/yönü, fiyat seçimi ve hedef risk büyüklüğü
bakımından yakınsama kanıtı yok. 11:00 piyasasındaki G−$2,30/Bosona−$27,39
karşılaştırması ayrıca kesintilidir: G'nin mutabakat kapısı yaklaşık t27,7'den
kapanışa kadar kapalıydı; sonraki pencere de atlandı.

İlk pilotun **+$9,20631474** sonucu yeniden üretildi. Son envanterin en kötü
terminal ödemeleri toplamı **−$5,79797026**, gerçekleşen ödeme bunun
**$15,004285** üstünde. Bu bir son-pozisyon muhasebesi; alpha veya alternatif
strateji hesabı değil. API/zincir nakdiyle yerel çarpım arasında yalnız
$0,00000074 hassasiyet farkı var.

Kendi 40 benzersiz trade×parent dolumunda A/B'nin ilk özel `MATCHED` alınma
zamanını ve 3.192 `G_KARAR` kaydını eşledim. Kayıt tazeliği kontrol edilerek
pay ağırlıklı **mid−ödenen fiyat**, +5/+10/+30 saniyede sırasıyla
**+0,1804 / −0,5280 / +1,3885 sent/pay**; bid karşılığı
**−0,3335 / −1,0280 / +0,8885**. On saniye katkısı altı pencerenin beşinde
negatif; 30 saniye toparlanması yoğunlaşmış. Bu kısa vadeli aleyhe fiyat
hareketi için somut bulgudur; her kayıp doluma “adverse selection” denmedi.
Alınma saati execution saati değildir; mid yürütülebilir fiyat, bid de
derinlik/ücret dahil tasfiye değeri değildir.

**3. Seçici azaltımın lehindeki ve aleyhindeki güçlü kanıt**

Ana 64 piyasada sınıflandırma aynen doğrulandı:

| İlk dolan parent grubu | Aç | Ekle | Azalt | Sıfırı aş | Toplam |
|---|---:|---:|---:|---:|---:|
| Maker | 67 | 101 | 48 | 14 | 230 |
| Taker | 2 | 2 | 26 | 0 | 30 |
| Karışık | 0 | 0 | 2 | 0 | 2 |

26 taker azaltımının 22 piyasaya yayılması ve kapanma oranı medyanının
**%99,92099** olması güçlü davranış kanıtı. Daha kuvvetli miktar bulgusu:
**14/26, `floor(abs(net)*100)/100` ile birebir**. Beşi tam sıfır, dokuzu
0,01 paydan küçük artık bırakıyor. Tüm sınıflı 26 taker parent'ın bütün
gözlenen dolumları tek kamu saniyesinde; burada eski aynı-parent devamı
açıklaması geçerli değil. Tam gönderilmiş boy ve gönderim saati hâlâ bilinmiyor.
Resmî limit emir miktarı iki ondalığa aşağı yuvarlanır ve piyasa minimumu
ayrıca denetlenir; desen bununla uyumlu, kullanılan SDK/emir tipinin kanıtı
değildir. [Resmî emir miktarı kuralları](https://docs.polymarket.com/trading/place-orders).

**Kapanış piyasayı terk etmek anlamına gelmiyor:** Bu 14 olayın 10'undan sonra
başka parent ilk kez doluyor; dördü eski taşınan, altısı karşı yönde, 9–131
saniye sonra. Yeni ilk dolum, yeni gönderim zamanı demek değildir. Ayrıca
14 maker “reverse” olayının sekizinde önceki net<0,01 pay; bunların önemli
kısmı ekonomik olarak yeniden açılıştır, büyük yön dönüşü değil.

Belirsiz 43 parent korunuyor. İçindeki sekiz taker için parent toplamlarını
bölmeden bütün sıralamalar denendi: altısı hep azaltım, biri azaltım/tersine
geçiş, biri t303. Bu sınırlı duyarlılık aynı-parent içi iç içe dolumları
çözmez; ana 262/43 paydasını iyimser şekilde değiştirmedim.

Para hesabı `N + U·Y + D·(1−Y)`, net yön `U−D`. MERGE nakdi serbest bırakır;
aynı terminal serveti ikinci kez kâr yapmaz. Karşı alış yalnız mevcut fark
kadar azaltır, fazlası yeni ters pozisyondur. Sabit pozisyonda yerel fark:

```text
kapama − taşıma = q × (1 − karşı tokenin ücretli nakit fiyatı − eldeki tarafın sonuç ödemesi)
```

Eski alış maliyeti iki kolda birbirini götürür. FIFO çift kârı bu marjinal
fark değildir. Beş Down'ı 0,99'dan almak, verilen 20Up/15Down örneğinde
ücret öncesi −$2,35 kötü sonucu −$2,30'a çıkarırken +$2,65 olasılığını da
−$2,30'a indirir. Bu yalnız beş sent kurtarmak için yapılan bir sigortadır.

İlk azaltımı taker olan **15** piyasanın yerel farkı **+$273,91252**; en iyi
üçü çıkarınca **−$9,57836**. Onunda en ucuz eski lotla bile çift maliyeti>1.
15 Eylül tek başına +$145,31935, bu toplamın yaklaşık %53'ü; gün yoğunlaşması
sonucun başka güne taşınacağına güveni azaltıyor.
Bu 15'lik seçili grubun gün bootstrap aralığı pozitiftir; bunu saklamıyorum,
ancak aktörün gerçekleşmiş eylemine koşulludur. Tüm **55** değerlendirilebilir
piyasada fark **+$165,37045216**, en iyi üç hariç **−$153,78977784**; yeni
10.000 gün-blok hesabı yaklaşık **[−$204,63,+$508,89]**. 26 parent'ın farklarını
toplayıp bağımsız bir botun PnL'si gibi sunmak yanlış olur.

Somut kapanış ve taşıma karşıörnekleri:

| Piyasa / kamu dolum yaşı | Gözlenen yol | Ne gösteriyor? |
|---|---|---|
| `1789456200`, t211 | 150,700268 Up'a karşı 148 Down, ücretli 0,095733 | Down sonucunda kapamanın yerel faydası +$133,83152 |
| `1789924800`, t123 | 84,221821 Down'a karşı 84,22 Up, ücretli 0,704973 | Down sonucunda kapama −$59,37282 katkı; bütün piyasa yine +$100,39038 |
| `1789580400`, t16–93 | Altı maker parent ile 510,059147 Down, karşı dolum yok | Taşıma +$378,071972; koşulsuz kapama zorunluluğuna karşı örnek |
| `1789739700`, t11/t81 | 499 Up@0,20 +14 Up@0,11, iki maker parent | Karşı dolum yok ve −$101,34; taşıma da güvenli değil |
| `1789468500`, t169/t178 | 21 Down taker ile tam sıfır; dokuz saniye sonra **aynı ücretli 0,5175 fiyattan 148 Down**, farklı taker parent | Kalıcı stop değil; risk hedefi/yön rejimi değişimi güçlü aday |

Son örneğin kapanış parent'ı
`0x50a191362345627c1137113cee4a186cfc50f5e21eb0cd21022bbc7f594e8e75`,
transaction'ı `0x2102dbbdcda563c858cc419e05530786d3287775c2f8300cbcf6f04a7dd51ec1`;
ardından `0x974d03abd0c6e4f4881beababdbcba301e84b713db80192487e2a5c766857a03`
parent'ı geliyor. Her örneğin tam kimliği ve yolu
[muhasebe bulgularında](../data/analysis/g2_next_review_ultra_20260922/accounting/FINDINGS.md),
ham girdisi R1 `full_activity/<S>.json` ve `receipts/<tx>.json` altında.
Örnekler açıklayıcı seçimdir, başarı oranı örneklemi değildir.

**4. Üç açıklamanın sınanması**

**Birinci: Duruma göre değişen hedef envanter ve geçici risk sıfırlama.**
Girdiler mevcut net, ilk dolumdan geçen süre, mevcut nakit/risk kapasitesi ve dolmuş
parent geçmişi. Miktarın mevcut nete uyması, sonra yeniden risk alınması
beklenir; 14 tam yuvarlama ve 10 sonraki parent bunu destekliyor.
Ancak sabit mutlak risk eşiği yeterli değil: taker azaltım öncesi net
**5,341466–508,498740** pay, medyan **124,5665**; maker eklemelerde net
**0,001821–753,731921**, medyan **99,991819**. Büyük envanter her zaman
azaltılmıyor, küçük envanter de azaltılabiliyor. Bosona'nın hesap-geneli
kapasitesi/bekleyen emirleri bilinmediğinden evrensel dolar eşiği çıkarılamaz.
Yeni bağımsız örnekte miktar-net bağı kaybolur veya yakın-sıfır sonrası yol
yalnız eski parent devamlarından oluşursa bu açıklama zayıflar.

**İkinci: Yürütülebilir değerin bozulması / göreli değer değişimi.**
Girdiler eldeki bid, karşı ask ve derinlik, kısa fiyat yolu, o anda alınmış
spot/referans/TWAP ve süre. Taker azaltımlarda aleyhe değişimin kontrol
durumlarından ayrılması beklenir. Neti −5sn'den beri aynı kalanlarda:

| Koşul | Taker azaltım | Maker azaltım | Maker ekleme | Azaltıcı dolum gözlenmeyen sabit kontroller |
|---|---:|---:|---:|---:|
| Elde tutulan bid son 10sn'de düştü | 10/16 | 10/23 | 31/58 | 9/22 |
| Spot başlangıç referansına göre eldeki yöne ters | 8/16 | 9/23 | 39/60 | 21/29 |
| TWAP eldeki yöne ters | 7/16 | 8/23 | 28/60 | 19/29 |

Bunlar aynı rastgele fırsat evreninde olasılık tahminleri değildir: parent
satırları gerçekleşen eylemlere koşullu; kontroller sabit zamanlıdır.
Yine de tekdüze stop açıklamasına açık karşıörnekler verir. −10sn'de taker
bid-düşüşü **8/14**; net değişimi olanları çıkarmanın etkisi raporlu.
Kapanış sırasında ters spot/TWAP zorunlu olmadığı gibi, aynı terslik taşıma
kontrollerinde de sık. Daha sonraki bağımsız, aynı risk/zaman koşullarında
ek ayrıştırma sağlamaması bu girdilerle tetikleyici iddiasını reddeder.

Fiyatları gerçekten karşılaştırınca başka sınır çıktı: −5/−10sn'de
iki yöntem için beş paylık derinlik bulunan **19/19** taker olayında karşı
alışın sentetik çıkış değeri ile eldeki tokeni ücret sonrası satmanın değeri
yaklaşık aynı (en büyük fark $0,00001). Karşı BUY burada kendiliğinden ucuz
çıkış yaratmıyor. Büyük aktör miktarının tamamı için bu eşitlik varsayılmadı.

**Üçüncü: Zamanın daralmasıyla mekanik çözülme.**
Girdi kalan süredir; G'deki mevcut t240 sınırını sabit eşik alırsak
azaltımların çoğunun daha sonra olması beklenirdi. Gerçekte taker azaltım
**4/26 t≥240**, yaş aralığı **24–286**, medyan **152**; maker azaltım
22/48 t≥240. Erken kapatıp yeniden açılan örnekler de var. Dolayısıyla
“son dakika taker unwind” genel mekanizma olarak reddedildi. Zamana bağlı
bir bileşen tamamen dışlanmıyor; tek başına politika yapılamıyor.

Ücret/iade ayrı tutuldu. Tarihsel piyasa metadata'sının 137'sinde ücret
oranı0,07; onchain gerçek nakde yeniden ücret eklenmedi. Yeni hipotetik
kotasyonlarda `q×rate×p×(1−p)` ve yuvarlama kullanıldı. Resmî programda
maker ücreti0, kripto maker havuz payı%20; Gold taker iadesi%18 olsa da
2.000 ağırlıklı hacim altı hesapta oran0. Bu, Bosona'nın tarihsel kademesini
ve bizim gelirimizi ispatlamaz. [Ücretler](https://docs.polymarket.com/trading/fees),
[taker programı](https://docs.polymarket.com/programs/taker-rebates).
Gerçek iade nakdi veya savunulabilir piyasa ataması bulunmadan PnL'ye eklenmedi.

**5. Mevcut veride gerçekten denenen çıkış hesabı**

Yalnız gözlenen kapanışları seçmedim: aynı 64 piyasanın her birinde nominal
t120 ve t240'ı aldım. −5sn bağlamı gerçek karar t115/t235, −10sn bağlamı
t110/t230 demektir. Karar kesiminde en az beş net pay varsa beş paylık
dilimi ya taşıdım ya **250ms sonraki** mevcut ask derinliği ve ücretle
karşı aldım; sonradan gelen hiçbir Bosona işlemi iki hesaba eklenmedi.
Bu, aynı mevcut pozisyonun yerel tanısıdır; bağımsız girişli G backtest'i
veya garantili taker dolumu değildir. Açık emir iptal/ACK'sı bilinmediği için
tam operasyonel politika sayılmaz. Her sütun ayrı deney; toplanamaz.

| Kural | t115→115,25 | t110→110,25 | t235→235,25 | t230→230,25 |
|---|---:|---:|---:|---:|
| Her uygun durumda kapat | 30 / −$6,81580 | 29 / −$10,00838 | 28 / −$8,47419 | 31 / −$12,11137 |
| Yalnız eldeki bid son10sn'de düştüyse | 12 / −$2,19943 | 14 / −$7,22844 | 13 / **+$5,44858** | 18 / **−$2,99242** |
| Yalnız spot eldeki yöne tersse | 19 / −$11,41528 | 19 / −$11,53175 | 19 / −$6,90360 | 19 / −$10,29802 |

Hücreler işlem sayısı / taşımaya göre fark. Eksik veri sıfır getiri sayılmadı.
Yalnız 13 işlemli olumlu hücreyi seçersek en iyi üç hariç+$1,07425 ve
gün aralığı yaklaşık[+$0,28,+$12,88] görebiliriz. **Beş saniye daha erken
kesimde işaretin dönmesi**, farklı uygunluk ve envanter yolları da dikkate
alındığında, bunu hazır sinyal saymayı engelliyor. İki evrenin farklılığı
tek başına aynı işlemin beş saniye gecikmeyle zarar ettiğini kanıtlamaz.
Tam satırlar, günler, dışlamalar ve sonuç-etiketi ters çevirme testi
`mechanisms.py` / `mechanisms.json` içinde. Daha iyi eşik aramadım.

**6. Tek öncelikli sonraki deney: aleyhe hareket eden maker teklifi bakımı**

Seçici taker çıkışını canlıya eklemeyi şu kanıtla önermiyorum. Önce daha
erken soruyu ayıralım: **G'nin bir sentlik mesafesi fiyat gerileyince
tükenmişken teklifi tutması, kötü dolumları artırıyor mu?** Bu Bosona'nın
çözülmüş gizli kuralı değil; kendi kotasyon kalitemize yönelik dar bir
mühendislik hipotezidir. Giriş yönünü, boyunu, zamanını veya RSI filtresini
aynı deneyde değiştirmemek gerekir.

Aday karar kuralı: yalnız yeni yön riski artırabilen mevcut emirde,
doğrulanmış taze defterin `target=floor_tick(best_bid−0.01)` değeri mevcut
emir fiyatının altına düştüğünde **iptal iste, kapanışı teyit et, sonra
normal G hedefinden yeniden teklif ver**. Azaltıcı emirlerde mevcut bakım
kuralını koru. Belirsiz emir rezervden düşmez; iptal cevabı gelmeden yenisi
açılmaz. Tick, veri, minimum boy, t240/t290, net5 ve bütün bütçe kapıları
korunur. Özellikle p=bid olduğunda mevcut G tutabiliyor; aday bir sent
korumayı yeniden ister. Yalnız fiyat yükseldiği için daha çok yeniden
kotasyon yapan ikinci bir kol eklenmez.

Bu adayı gerçek pilotta **ayrıca çalıştırdım**: 63 kabul edilmiş parent'ın
52'sinde dolum öncesi teklif kaydı, 35'inde taze risk artırıcı teklif bulundu.
19 karar satırında, **10 ayrı parent'ta** tetiklendi; sekizi sonra doldu,
ikisi dolmadı. Sekiz dolan parent'ta ilk sinyalden ilk özel MATCHED alınmasına
**185–3.118ms**, medyan **1.360ms** var. Sinyaller ilk herhangi bir dolum
bilgisinin alınmasından da önce. Ancak 36 dolan parent'ın dördünde dolum
öncesi 1Hz kayıt yok; bunlar “tetik yok” sayılamaz. 54 gerçek iptalin SDK
gidiş-dönüşü 22–1.030ms, medyan37,6ms; bu bir exchange iptal-etki sınırı
değildir. Kod ve tüm parent'lar `execution/buffer_probe.py` / `buffer_probe.json`.

Bu, adayın gözlenebilir olduğunu gösterir; **iptal edildi varsayıp
gerçekleşmiş kötü dolumu silmek yasak**. Bildirim exchange eşleşmesinden
sonra gelir; pozitif zaman aralığı iptalin yetişeceğini kanıtlamaz. Yerel
1Hz `G_KARAR` günlüğü iptal/gerçek eşleşme yarışını çözmez. Aday karara
emir kimliği, kalan miktar, risk rolü, UTC/monotonic ve defter saatlerinin
bağlanması gerekir. Gereken en küçük ek veri,
zaten çalışan kayıtçıların **G2 dönemindeki kamu A/B parçalarını**, aynı
boot/UTC/monotonic eksenindeki kendi PLACEMENT/UPDATE/MATCHED ve SDK iptal
istek/cevaplarıyla birlikte yerel analize almak. Yeni indikatör, başka
strateji veya yeni servis gerekli değil. Kararı değiştiren ölçüm, aday
iptal sinyalinin gerçek kendi dolumu kesinleşmeden önce oluşup oluşmadığı
ve iptal gecikmesinde hâlâ dolan miktardır; kamu L2 azalışından kuyruk
kredisi üretilmez.

Bu tek adayın kapıları önceden şöyle sabitlenmeli:

- **Çevrimdışı teknik kapı:** bütün kabul edilmiş parent'ları, dolmayanları
  da tut; miktar/nakit mutabakatı tam olsun. Tetikleyicilerin ≥%95'inde
  taze defter ve kendi emir yaşamı bağlanabilsin. Eksik zamanlı vakalar
  negatif veya kurtarılmış dolum sayılmasın. Aday yalnız zaten kapanmış
  emirlere yetişiyorsa bu gerekçeyle elensin.
- **Daha sonra operatör onaylı ekonomik test:** takvim pencerelerini
  `sha256('ULTRA-Q1|'+S)` ile 1:1 mevcut G/adaya ata; aynı piyasada iki kolu
  birbirinin kuyruğuna sokma. Her kolda5pay klip/net5, aynı taraf başı
  harcama ve aynı zarar disiplini; ortak mevcut kalan hesap bütçesi aşılmaz,
  otomatik yeni $10 açılmaz. Sıfır dolumlu atamalar da sonuca girer.
- **Birincil ölçüt:** tüm atanmış kapanmış pencerelerde ücretli işlem
  USD/pencere farkı; gerçek atfedilemeyen rebate hariç. ≥3 ayrı gün ve her
  kolda≥100 dolumlu pencere olmadan kalıcı fayda iddiası yok; bütçe daha
  erken biterse sonuç yetersizdir. Gün ve pencere kümeli alt güven sınırı>0,
  en iyi üç hariç fark>0, en kötü terminal risk ve belirsiz emir miktarı
  artmamış olmalı. Üst sınır≤0 ise adayın üstünlüğü reddedilir; diğer
  sonuçlar belirsiz. Bunlar araştırma kabul eşikleridir, Bosona parametresi
  veya yeterli istatistiksel güç garantisi değildir.

**Şimdi kodlanabilir:** izole iptal tetikleyicisi ve gerçek emir yoluna
regresyon. **Şimdi çevrimdışı sınanabilir:** mevcut pilotta tetiklenme,
zaman kapsamı ve yanlış envanter/saat durumları; arşiv kopyalanınca G2
olayları da. **Operatör kontrollü LIVE'a hazır:** henüz değil; adayın
tam emir/iptal yarışı doğrulanmadı ve ekonomik üstünlük gösterilmedi.
Bu rapor hiçbir dağıtım veya finansal başlatma yapmadı. Miras t180 kuralı
ayrı teknik bulgu olarak kayıtlı; aynı deney içine ikinci değişiklik
olarak sessizce sokulmamalı.

**7. Tekrar üretim ve doğrulama**

Ana hesaplar Python standart kütüphanesi ve mevcut receipt/defter
yardımcılarını kullanıyor. Donmuş eski analizlerin yazan giriş noktaları
çalıştırılmadı. Çalıştırılan komutların çıktı/hash özeti alt dizinlerdeki
`verification.json` dosyalarında ve üstteki `verification.json` içindedir.
Son toplu kontrol: [doğrulama kaydı](../data/analysis/g2_next_review_ultra_20260922/verification.json).

```bash
python3 -B /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/accounting/audit.py
python3 -B /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/context/reconstruct.py
python3 -B /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/context/check.py
python3 -B /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/execution/recompute.py
python3 -B /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/execution/markouts.py
python3 -B /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/execution/buffer_probe.py
python3 -B /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/mechanisms.py
python3 -B /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/inventory.py
python3 -B /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/accounting/crosscheck.py
```

Yeniden çözülen R1 transfer/miktar/nakit, hash64 seçimi, tamsayı envanter,
çokluk, terminal servet, parent/sıra duyarlılığı, gerçek pilot ve karşılaştırma
hesapları; G2 kimlik/politika/WS izole testleri; geçmiş sonuçları ters
çevirince karar özelliklerinin değişmemesi; nedensel saat/derinlik/eksik
veri kontrolleri ve hedefli Ruff/syntax sınandı. Tam kuyruk simülatörü,
Bosona özel emirleri veya güncel runtime doğrulandı iddiası yok.
Bağımsız çapraz hesap 390 bağlam, 278 fiyat bacağı ve 118 beş-pay karşılaştırmasını
doğruladı. Ücretin beş ondalığa float/Decimal yuvarlanma duyarlılığı en fazla
$0,00001/bacak; sonuçları değiştirmiyor. Ham tape'in iki dosyasından yaklaşık
695MB açılmış ön bölüm ve dört cache-defter eşleşmesi ayrıca kontrol edildi;
bu, bütün arşivin derinlik doğrulaması değildir.

**Operatöre kısa cevap:** G2'nin muhasebesini, belirsiz emir rezervini ve
kayıt altyapısını koru. İlk deneyde maker teklifinin aleyhe hareket sırasında
korunmasını değiştirip ölç; taker stop için tetikleyici henüz çıkmadı.
Eşik taramayı, dolum sayısını karar saymayı ve küçük pilot kârını yakınsama
kanıtı saymayı bırak. Gözden kaçan en güçlü ipucu, **0,01 paya tam yuvarlanmış
kapanıştan yalnız dokuz saniye sonra aynı fiyatla çok daha büyük ters
taker parent açılması**: çözmemiz gereken yalnız çıkış değil, hedef
envanterin ne zaman ve neden değiştiği.
