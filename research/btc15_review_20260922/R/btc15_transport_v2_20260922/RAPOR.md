# BTC15: emir ve iptal saatlerini ayırma

22 Eylül 2026. Odak BTC15. G1'den yalnız teknik saat/olay kanıtı kullanıldı;
G1'in BTC5 stratejisi, net 5 pay sınırı, fiyat bandı veya kârı aktarılmadı.

**Sonuç:** uygulama modeli iyileştirildi; güvenilir yeni bir kârlı aday
çıkmadı. Bir sent geriden pasif teklifin olumlu görünen sonucu, önceki
500 ms işlem-saati stresinde tersine döndü. Mevcut P0 adayı donuk kalıyor.

## Teknik olarak ne değişti?

Eski motor borsada etkinleşme ile cevap alınmasını aynı gecikme
parametresine bağlıyordu. İptalin etkili olmasından sonra kapanış
öğrenilmesi de kabul gecikmesi kadar bekliyordu. Bu ölçülmüş bir ilişki
değildi. Ayrı kopyada şimdi beş saat var:

1. Gönderimden borsada etkinleşmeye kadar geçen varsayılan süre.
2. POST cevabının ve emir kimliğinin istemciye gelmesi.
3. İptal isteğinden borsada iptalin etkili olmasına kadar geçen süre.
4. İptal sonrası son miktar ve kapanışın hesapta öğrenilmesi.
5. Gerçekleşen dolum miktarının karar motorunca öğrenilmesi.

POST cevabı beklenirken iptal niyeti kaybolmuyor; emir kimliği gelince
gönderiliyor. Dolum borsada gerçekleşmiş olsa da istemciye henüz
bildirilmemişse kararda bilinmiyor. İptal teyidi gelmeden kalan rezerv
kaldırılmıyor. Kısmi dolum ile sonraki kümülatif bildirim aynı maliyeti
iki kere yazmıyor. Gerçek borsa envanteri ve öğrenilmiş envanter ayrı.

Yeni uygulama `execution.py`; eski kaynak değişmedi. Varsayılan eski
hızlı/yavaş profillerde **192 gerçek BTC15 yolu birebir aynı** çıktı.
Giriş, yön, fiyat filtresi, yeniden fiyatlama ve dengeleme kuralları aynı.
5 pay klip / 10 net pay / 15 dolar piyasa nakdi / −5 dolar en kötü sonuç,
t30–839 karar ve t840 iptal sınırları korundu.

## Teknik sürelerin dayanağı ve sınırı

Önceki salt okunur incelemenin donmuş kayıtları kullanıldı: 63 kabul
edilen emrin POST/özel PLACEMENT, 27 iptal edilmiş emrin iptal isteği /
özel CANCELED / get_order teyidi ve 40 gerçek dolumun kamu/özel/öğrenme
eşleştirmesi. Hepsi aynı Londra makinesinin monotonik saat alanında.

Etkinleşmenin kesin borsa saati yok. POST için ilk kabul kanıtının
(HTTP cevabı veya özel PLACEMENT alınması) zamanı yalnız üst sınırdır.
İptalde de özel CANCELED veya durum teyidinin ilk alınması üst sınırdır.
Tablodaki etkinleşme süreleri bu sınırların deneyde kullanılan vekilleri.

| Sabit profil | Etkinleşme vekili ms | POST cevabı ms | İptal etkisi vekili ms | İptal isteğinden teyide ms | Kamu alımından dolum öğrenmeye ms |
|---|---:|---:|---:|---:|---:|
| Önceki hızlı | 250 | ayrı model yok | 250 | 500 | 0 |
| Önceki yavaş | 750 | ayrı model yok | 750 | 1500 | 500 |
| Gözlemsel p50 | 38 | 41 | 44 | 163 | 132 |
| Gözlemsel p95 | 94 | 102 | 146 | 2506 | 623 |
| Gözlenen maksimumlar | 1099 | 2244 | 234 | 2525 | 784 |

Üç yeni profil, sonuç görülmeden p50/p95/maksimum ve yukarı tam ms
yuvarlama olarak sabitlendi. Bunlar ayrı marjinal niceliklerin birleşimi;
tek bir gözlenmiş ortak olay veya olasılık ağırlıklı gecikme dağılımı
değildir. İki eski profilde kabul/iptal cevabı etkiden sonra kabul gecikmesi
kadar varsayılıyordu; yeni profillerde baştan sona süreler ayrı uygulanır.

**Bu BTC15 kalibrasyonu değildir.** Süre örneklemi farklı sözleşme
süresinden ve Londra'dan; eski BTC15 kamu kayıtlarının ağ yolu da farklı.
Yeni profiller yalnız teknik duyarlılık deneyi. Gözlenen bir dolum
öğrenmesi kamu mesajından yaklaşık 47 ms önceydi; bu negatif gözlem
protokolde tutuldu. Sabit pozitif üç profil bütün olası bildirim
sıralarını kapsamıyor. Taker örneği yok; M2'nin taker yürütme saatleri
ayrıca ölçülmüş sayılmaz. LTP yayım zamanı hâlâ eşleşme zamanının vekili.

## Aynı BTC15 örnekleminin sonucu

Önceki sekiz atama aynen korundu: 21 Eylül 20:45, 21:00, 21:15, 21:30,
21:45, 22:00, 22:15, 23:00 UTC. Kopma/eksik işlem nedeniyle iki piyasa
null; altı uygun piyasa hesaplandı. 23:00'ın sonradan API mutabakatı
etiketi korundu. Bu yeni kör veri veya bağımsız çok gün örneklemi değil.

480 ana yol = 6 piyasa × 5 süre profili × 2 kuyruk × 2 olay sırası ×
4 sabit kol. Aşağıdaki tablo kuyruk arkası / aynı-ms yaşam döngüsü önce
koşullu toplamlarıdır; **gerçek veya kalibre kazanç değildir**.
Ücretler nakitte, iadeler ve piyasa etkisi yok. P0 yeniden seçilmedi;
önceki donmuş kontrol sonucu yalnız referans olarak taşındı.

| BTC15 kolu | Eski hızlı $ | Eski yavaş $ | p50 $ | p95 $ | Maksimumlar $ |
|---|---:|---:|---:|---:|---:|
| Pasif bid | −2,6953 | −5,7000 | −2,2894 | +3,7000 | −1,7055 |
| Pasif bid−1 sent | −11,9500 | −6,6500 | −2,2769 | +3,6968 | +3,2500 |
| Bid + taker dengeleme | −2,7680 | −5,6707 | −4,2069 | −0,6356 | +0,4923 |
| Rezervli dengeleme | −1,7141 | −5,1000 | −2,6350 | −1,4733 | −2,6505 |

İki olay sırası çoğu yolda aynı; iki bağımsız başarı sayılmaz.
Kuyruk önündeki yeni pasif sonuçlar negatif. Ön/arka senaryolarının PnL
sırası garantili değildir: daha erken dolmak sonraki envanteri ve
işlem yolunu değiştirir. Bunlar matematiksel kazanç alt/üst sınırları değil.
Sekiz atamanın tamamı için toplam ve kalibre ekonomik PnL **null** kalır.

## Olumlu ipucuna karşı denemeler

Bir sent geride, p95/arka kuyruğun +3,6968 doları en iyi piyasa çıkarılınca
da +1,9968 kalıyordu. Bu yüzden ayrıntılandırıldı. Bu adım ilk sonucu
gördükten sonraki tanıdır; yeni bir ön kayıt başarısı diye sunulmuyor.
İki pasif kolun üç yeni profilinin tümünde, iki kuyruk ve iki olay
sırasıyla 288 ek yol çalıştırıldı. Eşik taranmadı.

İlk müdahale önceki araştırmadaki sabit −500 ms LTP kaydırmasıdır;
kamu mesajının istemciye alınması erkene çekilmez. İkinci müdahale
yalnız iptal teyidini eski `iptal etkisi + kabul gecikmesi` varsayımına
döndürür; etkinleşme, POST cevabı, dolum öğrenmesi ve politika aynı kalır.

| Kol / profil; arka kuyruk | Ana toplam $ | İşlem vekili 500 ms erken $ | İptal teyidi eski formülle $ |
|---|---:|---:|---:|
| Bid / p95 | +3,7000 | +4,0602 | −4,1002 |
| Bid−1 sent / p95 | +3,6968 | **−3,3500** | **−3,0000** |
| Bid−1 sent / maksimumlar | +3,2500 | **−2,3000** | +1,2000 |

Somut BTC15 yolu: 21:15 UTC piyasasında bu pasif kol ana p95 saatle
yalnız 5 Up'ı 4 dolara alıyor; Up sonucu +1 dolar. İşlem vekili 500 ms
erkene alınırken bildirim saati aynı tutulduğunda t767,659 ve t791,841'de
iki ayrı 5 Down alımı daha oluşuyor. İlki açığı kapatıp toplam 6,65 dolar
maliyetle −1,65 dolar kilitliyor; ikincisi yeni net Down riski açıyor.
Son durumda 5 Up / 10 Down, 8,45 dolar maliyet ve **−3,45 dolar** var.
Aynı ilk alımdan farklı geç tamamlama/yeniden risk yolu çıkıyor; farkı
yalnız isabet oranıyla açıklamak mümkün değil. Bu yol gerçek Bosona
dolumu değil, aynı BTC15 verisindeki uygulama varsayımı karşı örneğidir.

Bid/p95 erken işlem testinde pozitif kalsa da en iyi piyasa çıkarılınca
−1,5754 dolar. Bid−1 sent/maksimumlar, eski teyit formülünde en iyi
piyasa hariç −2 dolar. Ana bid−1 sent/p95'te en iyi üç çıkarılınca da
−0,2032 dolar kalıyor. Kârlı strateji seçmek için sağlam dayanak yok.

**Çıkarım:** iptal teyidini beklemek yeni emirlerin zamanını ve açık
envanteri değiştiriyor. Bir tabloda pozitif sonuç üretmesi, daha yavaş
teyidin avantaj olduğunu göstermez. Kendi tam emir yollarıyla
doğrulanmamış yürütme varsayımları burada strateji sonucunun işaretini
değiştirebiliyor. Saatleri ayırmak teknik ilerleme; olumlu hücreyi
kazanç filtresine çevirmek için kanıt yok.

## Kontroller ve devam kararı

17 kontrol: değişmeyen BTC15 karar kodu, eski motor eşdeğerliği, POST öncesi dolum/iptal niyeti,
gecikmiş kapanış rezervi, iptal sırasında kısmi dolumun tek maliyeti,
gelecek defter/işlemlerin önceki kararı değiştirememesi, gerçek kohort
risk/miktar/nakit ve eksik veri ayrımı. Ana 480 ve ek 288 yolun tamamı
limitler içinde; 192 eski yol birebir korunuyor. Hedefli Ruff/syntax geçti.
Dokuz hesap çıktısı ağ kapalıyken aynı SHA256 ile yeniden üretildi;
kanıt `results/reproducibility.json` içinde.

Mevcut aday değiştirilmez. Bu altı pencere üzerinde yeni kârlı eşik
aranmaz. Sonraki ekonomik değerlendirme yeni BTC15 döneminde, karar
anında kaydedilmiş tam akışla ve bu ayrı saat modeliyle yapılmalı.
Kuyruk modeli kendi dolan **ve dolmayan** emirlerle doğrulanmadan
simülasyon kârı ekonomik avantaj diye adlandırılmamalı.

Bu çalışma canlı G1'e, eski aday/protokole, MAIN'e, Londra süreçlerine
ve bütçelere müdahale etmedi. Çalışma alanı bu ayrı dizin ve araştırma
kök planı; ana görevin çok günlük ekonomik kabulü açık kalıyor.

```bash
P=/home/taygun/Masaüstü/KararAtlas/base1/bin/python3
N=/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_transport_v2_20260922
OPENBLAS_NUM_THREADS=1 "$P" -B "$N/run.py" repeat
"$P" -B "$N/check.py"
"$P" -m ruff check --no-cache "$N/run.py" "$N/execution.py" "$N/check.py"
```

`repeat`, mevcut dokuz hesap çıktısını ağ kapalıyken yeniden üretip
hashlerini karşılaştırır. `run` ve `challenge` ayrı da çalışır.
`protocol.json` gerçek teknik örnekleri ve sonuç öncesi sabit profilleri;
`results/markets/` tüm dolum/öğrenme/rezerv yollarını;
`results/challenges.json` bütün karşı denemeleri saklar.
Eski kaynaklar `sources.json` ve önceki teslim manifestleriyle korunur.
