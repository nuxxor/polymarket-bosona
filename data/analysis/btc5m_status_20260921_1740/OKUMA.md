# BTC5m shadow kontrolü — 21 Eylül, 20:40 Türkiye kesimi

Londra kayıtları **17:46:05 UTC / 20:46:05 Türkiye** anında alındı.
Güncel seçici inventory_v2, rebound_v3 ve participation_v1 süreçleri aynı
PID'lerle çalışıyor; kaynaklar kendi donmuş manifestleriyle birebir.
Çalışan kaynak, kural, süre veya bütçe değiştirilmedi. Eski, bilinen veri
kusurları bulunan sürümler bu sonuçlarla birleştirilmedi.

## Aynı 35 kapanmış pencere

**14:45–17:40 UTC / 17:45–20:40 Türkiye**, toplam 2 saat 55 dakika.
Atanmış ama alım yapılmamış pencereler paydada; veri eksikleri ayrıca aşağıda.
Sonuçlar alınabilir satış derinliği ve ücretle hesaplanan **sanal PnL**;
rebate/sabit gider ve gerçek emir yürütme sonucu değildir. Her kol bağımsız
portföydür; satırlar toplanmaz. 35 piyasanın resmi sonucu doğrulandı.

| Politika | 250 ms: işlemli pencere / dolum | 250 ms PnL | Ek beklemesiz PnL |
|---|---:|---:|---:|
| Seçici, yalnız tamamlama | 19/35 · 48 | +$3,70987 | +$5,61414 |
| Seçici, eklemeli | 19/35 · 68 | **+$8,76225** | +$9,59677 |
| Her pencereye katılım, yalnız tamamlama | 35/35 · 93 | −$3,81524 | −$5,95229 |
| Her pencereye katılım, eklemeli | 35/35 · 115 | **+$2,28290** | −$0,62028 |

Eklemeli seçici kol, kendi kontrolüne göre +$5,05238; katılım kolu kendi
kontrolüne göre +$6,09814 daha iyi. Bunlar değişen envanter yollarının toplam
politika farkları; tek tek ek alımların izole nedensel katkısı değildir.
Katılım eklemeli kol seçiciden $6,47935 geride; aynı dönemde alış nakdi
$227,71710'a karşı $121,23775, yani aynı gerçekleşmiş risk/sermaye kullanımı yok.

En iyi üç pencere hariç seçici eklemeli **+$1,48018**, katılım eklemeli
**−$8,54943**. Kapanmış sonuçların zaman sırasından hesaplanan düşüş sırasıyla
$2,96524 ve $10,83050; anlık mark-to-market düşüşü değil. Katılımın hızlı
kolu negatifken gecikmeli kolun pozitif olması da yürütme duyarlılığını gösterir;
250 ms beklemenin genel olarak daha iyi olduğunu kanıtlamaz.

Seçici sürümün kendi başlangıcından **13:50–17:40 UTC, 46 pencere** toplamı:
yalnız tamamlama +$1,24830, eklemeli +$8,57018 (250 ms). Eklemelinin bu daha
uzun dönemde en iyi üç pencere dışındaki sonucu yalnız +$0,06381. Küçük ve
tek günlük örneklem, kalıcı avantaj veya Bosona kopyası iddiasına yetmez.

Bağımsız geç-giriş rebound_v3: ana **t280**, 35 atamanın 28'inde geçerli karar,
5 alım, **−$0,37406**. İkincil t240: 33 geçerli/3 alım/−$0,16041;
t270: 30 geçerli/6 alım/−$2,90257. Bunlar ayrı sanal stratejiler.
Favori karşılaştırmasında t280 yalnız üç alınabilir işlem var; 25 seçilmiş
favorinin satış derinliği yok ve PnL `null`. Bu eksikleri sıfır sayarak veya
farklı kapsamlı toplamlarla kural üstünlüğü çıkarmıyoruz.

## Çalışma ve ölçüm sağlığı

- İki envanter shadow'unda da 945 planlı andan 944 karar + 1 kayıtlı geç
  karar var. Sessizce kaybolan planlı an yok. Tek gecikme 16:28:40 UTC
  kararında; sonrasında normal kayıt devam etmiş. Bu kesit tek başına
  gecikmenin ağ mı başka bekleme mi olduğunu kanıtlamaz.
- Seçicide 120/944, katılımda 114/944 kararın giriş fiyat bağlamı eksik/eski.
  Katılımın ilk alımı ve ekonomik tamamlama bu seçici bağlama zorunlu değil;
  dolayısıyla bu sayılar gerçekleşmiş dolum yokluğu anlamına gelmez.
- Rebound 105 planlı andan 91 geçerli, 14 eski/eksik bağlam. Eksik gözlemler
  başarılı bekleme kararı veya sıfır kazanç sayılmadı.
- Ücret, gerçek satış derinliği, FIFO tamamlama, pencere riskleri, karar/işlem
  gecikmesi, defter tazeliği, tekillik ve resmi sonuç/Decimal nakit hesabı geçti.
- Kesim sonrasındaki pozisyonlar toplama eklenmedi: snapshot anında katılım
  kolunda 17:40 penceresinde dengeli 5+5 pay/$4,26822 maliyet ve 17:45
  penceresinde 5 Up/$1,82963 maliyet vardı. Her bağımsız kol ayrı tutuldu.

## Bosona aynı piyasalarda

35 sözleşmenin 33'ünde **282 kamu BUY kaydı**, **24.581,693057 pay**;
API alış nakdi $14.266,657856, terminal ödeme hakkı eksi alış nakdi
**−$1.671,549952**. Bunun **−$1.631,824136** kısmı tek 16:30 UTC
penceresinden geliyor. Rebates/sabit giderler hariç, hesap-geneli sonuç değil.
Tam piyasa geçmişleri alındı; gerçek aynı-görünümlü dolumlar korunarak
activity/trades çoklukları, tokenlar ve bütün resmi sonuçlar eşleşti.

Bu ham dolarları bizim küçük paylarımızla doğrudan performans sıralaması
sayamayız. İlk yön seçicide 7/19, katılımda 17/33 ortak işlemli pencerede
aynı. Yakın ±15 saniyede tek Bosona yönü bulunan karşılaştırmalarda seçici
10/20, katılım 13/28 aynı. Gözlenen katılım arttı; Bosona'nın yön/zaman
kararlarını çözdüğümüz gösterilmiş değil. Kamu dolumlarından görünmeyen
yerleştirme/iptal/ana-emir kararları çıkarılmadı.

## Tekrar kontrol

Bu dizindeki `check.py`, `snapshot.json` ve önbelleğe alınmış kamu API
yanıtlarından `report.json` üretir. Eksik cevap gerektiğinde yalnız kamu
GET yapar; Londra'ya veya çalışan botlara yazmaz. Ruff/compile geçti;
önbellekten ikinci çalışma raporu aynı SHA256 ile yeniden üretti:
`a17830f77758425ce4ff4d79e3e3abcf8b58104a2c258ac4fa3029bf775d6222`.
