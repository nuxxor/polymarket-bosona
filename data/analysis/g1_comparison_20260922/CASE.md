# G1 açıkta kalan yön riski: Bosona aynı durumlarda ne yaptı?

22 Eylül 2026. Saatler Türkiye saati. İşlem saniyeleri **kamu API dolum yaşıdır**;
emir gönderme veya karar zamanı değildir. İlk kesit 11 piyasayı/22 aktör-piyasa
hesabını kapsar; dokuz geçmiş pencere ile iki ileri pencere ayrı tutulur.
Kaynaklar: `latest.json`, kesitin ham activity/market dosyaları, `receipts/`,
`paths.json`, `case_1790074800_own_events.json`, `operational_evidence.json`.

## Gönderilen ekran: 14:00–14:05, S=1790074800

G'nin bütün dolumları:

| Kamu dolum yaşı | Alış | İşlem sonrası Up − Down |
|---:|---|---:|
| 9 sn | 5 Down × 0,47 | −5 |
| 18 sn | 5 Up × 0,62 | 0 |
| 19 sn | 5 Down × 0,39 | −5 |
| 27 sn | 5 Up × 0,70 | 0 |
| 28 sn | 5 Down × 0,28 | −5 |

10 Up + 15 Down; maliyet 12,30 dolar. Up sonucunda ödeme 10: **−2,30 dolar**.
Ekranın 0,99/0,01 değerlemesi −2,25 gösterir; kesin sonuç ödemesiyle fark 5 centtir.
FIFO'da ilk iki beşlik çiftin maliyeti ayrı ayrı 1,09; toplam eşleşmiş zarar
0,90 dolar. Son beş Down maliyeti 1,40 dolar ve kaybediyor. Bu muhasebe ayrımı,
o tamamlamalar yapılmasa bütün stratejinin daha iyi olacağını kanıtlamaz.

**Bosona aynı piyasada yalnız 201. saniyede 249 Down × 0,11 almış.**
Tam condition activity sorgusunda bundan önce alım, bundan sonra karşı alım
veya satış yok; ardından sıfır ödemeli Down redeem var. Sonuç **−27,39 dolar**.
Zincir receipt'i bir dolum/bir parent ve **maker** rolünü doğruluyor.
Dolayısıyla bu, açık Down'a ekleme değil, gözlenen ilk pozisyon açılışı.
“201. saniyede karar verdi” veya “hiç kurtarma emri vermedi” diyemeyiz:
önceden bekleyen ve hiç dolmayan/iptal edilen emirler kamu kaydında yok.

### Bu pencere saf strateji sınavı değil: veri geçerlilik kapısı kapandı

11:00:29 UTC'de trades API, 0,70'lik Up dolumu için doğru token kimliğinin
yanında `outcomeIndex=999` döndürmüş. `ab.py:islem_anahtari()` yalnız 0/1 kabul
ediyor. İki mutabakat çevriminde toplam altı doğrulama reddi ve iki
`mutabakat_hata` var. G, güvenlik kapısı kapalıyken mevcut emirleri iptal edip
yeni emir üretmeyi kesiyor. Karar kayıtları:

- 5,649–26,855 saniye: 42 ölçümde mutabakat açık.
- 27,721–299,344 saniye: 544 ölçümde mutabakat kapalı.
- Sonraki 14:05 penceresi `atla_mutabakat` ile atlanmış.
- 14:09:09'da mutabakat yeniden başarılı olmuş; takip eden pencerede dolum var.

Dolayısıyla “model son 4,5 dakika tamamlamak istemedi” yorumu yanlış olur.
30–290 saniye arasında Up için 256 fiyat-kalite ölçümünün 74'ü, beş payla
mevcut 10 dolarlık taraf harcama sınırına sığıyor. Bu, gerçekleşebilir dolum
veya kurtarılabilecek kesin kâr hesabı değildir; ayrıca kapalı olan veri kapısı
nedeniyle bu hedefler emir hâline gelememiştir.

**Öncelikli altyapı düzeltmesi:** yalnız doğrulanmış condition→token→outcome
eşlemesiyle 999 alanını normalleştirmek; bilinmeyen token ve çelişkili 0/1
alanını yine reddetmek. Geçersiz satırı silmek veya güvenlik kapısını kaldırmak
çözüm değildir. Bu araştırma turunda çalışan bot kaynağı değiştirilmedi.
Altı sorunlu kaydın varlık kimliği arşiv piyasanın Up tokeniyle eşleşiyor;
kontrol betiği bunu yeniden doğruluyor. Kayıtçılardaki enum reddinin aynı
olaydan geldiği ayrıca kanıtlanmış değildir.

## Karşı örnek: 13:35 penceresinde riski kapatmış

S=1790073300, sonuç Up:

| Kamu dolum yaşı | Alış | Net Up − Down | Gerçek rol |
|---:|---|---:|---|
| 3 sn | Toplam 112,195381 Down ≈0,35 | −112,195381 | maker |
| 114 sn | 10 Up ×0,87 | −102,195381 | maker |
| 126 sn | 102,19 Up ×0,89; nakit 91,6494 | −0,005381 | taker |

İlk yedi Down kaydı **tek parent**; iki karşı alış iki farklı parent.
İlk Down alışlarının nakdi 39,268384 dolar. Karşı alışların nakdi toplam
100,3494; ek Up ödemesi 112,19. Aynı pozisyonu taşımaya göre yerel katkı
**+11,8406 dolar**; toplam piyasa sonucu yine **−27,427784 dolar**.
Bu kez zarar kilitleyerek risk azaltma gözleniyor. Sonucun bilinmesi burada
değerlendirme etiketidir; o an doğru sinyal bulunduğunu kanıtlamaz.

## Başka yol: 12:55'te ters yöne geçip o yönde büyümüş

S=1790070900, sonuç Up. Önce 132. saniyede 3 Down ×0,63; 166. saniyede
7,16 Up ×0,24 ile net yön Up'a dönüyor. 219. saniyede toplam 222,250001 Up
≈0,88; 246–247. saniyelerde 251 Up ×0,95 geliyor. Net Up 477,410001;
toplam sonuç +42,771600 dolar. Son altı yüksek fiyatlı dolum **tek parent**;
247. saniyedekiler daha önce dolmaya başlamış emrin devamı. Altı yeni karar
saymak yanlış. Bütün bu örneğin gerçekleşmeleri maker.

## Şimdilik çıkarım

Bosona bazen tek tarafı sonuca taşır, bazen pahalı karşı alımla riski azaltır,
bazen ters yöne geçip büyür. Üç yolun varlığı doğrulanıyor; hangi gözlenebilir
koşulun hangisini seçtirdiği henüz bulunmuş değil. Bu örnekler sıklık veya
nedensel başarı tahmini için seçilmedi. Kaybeden bir dolum tek başına adverse
selection teşhisi değildir; dolum sonrası fiyat yolu ve emir bağlamı gerekir.

Aynı dokuz geçmiş pencerede G 54 gerçek dolum/50 dolmuş parent, Bosona
55 dolum/24 dolmuş parent. G payları %100 maker; Bosona %78,94 maker.
Bosona'nın işlemli sekiz penceresindeki ilk dolum yönü G ile yalnız 3/8 aynı.
G'nin ilk dolum medyanı 10 saniye; Bosona'nınki 147,5 saniye. Bu küçük,
parçalı tarih aralığında **maker yürütmede yakınlık var; giriş zamanı ve
envanter yönetimi aynı değil**. Farklı miktarlı dolar sonuçları üstünlük
kanıtı olarak karşılaştırılmıyor.

## Devam eden ölçüm

14:05–16:05 TR için önceden sabitlenen 24 slot Londra'daki salt-okunur
araştırmayla izleniyor; 16:20'ye kadar sonuç gecikmesi payı var. G'nin
politika, boy, bütçe ve süreçlerine dokunulmadı. Kamu satırları, chain
parent/rolü, yön büyütme-azaltma yolu ve operasyonel kesintiler ayrı tutuluyor.
Worker başlangıcı 14:16:40 TR; öncesi botun kendi kayıtlarından ve tam kamu
geçmişinden okunuyor. İki saatlik nihai sonuç henüz oluşmadı.

Kontrol: `python3 check.py` sentetik muhasebe/çokluk/sıra belirsizliği
kontrolleri ve 22 gerçek aktör-piyasa hesabı ile receipt/parent tekrar hesabı
geçti. Hedefli Ruff ve sözdizimi kontrolü geçti. Boş tokenlı redeem'lerde
ödeme hesabı uzlaşır; yakılan tüm kaybeden tokenların zincir bakiyesi ayrıca
doğrulanmış değildir. Rebate ve sabit giderler dahil değil.
