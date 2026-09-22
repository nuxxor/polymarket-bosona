# G4 teklif kaynağı ve dolum sonrası fiyat — 22 Eylül 2026

**Karar:** Yukarı yeniden fiyatlama, takip edilmeye değer bir olumsuz dolum
örüntüsü gösteriyor. Altı pencere bunu bağımsız strateji üstünlüğüne veya
canlı yama kararına dönüştürmeye yetmez. G4 kaynağı, bütçesi ve süreçleri
değiştirilmedi. Opus/PRO G4 incelemeleri geldiğinde bu donmuş kesitle karşılaştırılacak.

## Kesit ve doğrulama

İlk altı tam G4 penceresi: **16:45 ≤ başlangıç < 17:15 UTC**
(19:45–20:15 TR). G4 başlangıcı 16:42:23 UTC. Tek günlük betimleyici
kesittir; bağımsız doğrulama veya sonuca kör yeni deney değildir.

- 87 kabul edilmiş emir: 47 dolmuş, 40 dolmamış.
- 56 ayrı trade×parent dolumu, 234,957753 pay. A/B kayıtçılarında ayrı ayrı
  aynı miktarlar; iki akışın 112 bildirimi ekonomik olarak 56 olaydır.
- Her kabul edilmiş emir için SDK POST kaydı var. Özel MATCHED dolum
  miktarları, 87 emrin saklanan muhasebesiyle mikropay toleransında eşleşti.
- 5.526 SDK kaydı tek oturumda sıra boşluğu ve yazma hatası olmadan okunuyor.
- 55/56 dolumda tekil işlem hash'iyle kamu LTP kaynak milisaniyesi
  eşleşti. Bir saat eksik/uygunsuz; fiyat analizinde sıfır sonuç sayılmadı.
- +10 saniye fiyatı 55 dolumda, +30 saniye fiyatı 54 dolumda uygun.
  Pencere sonrasına taşan veya bayat/eksik fiyatlar null.

Kaynak SHA: `0fd30f9faee281d59ca57597005391579b0debbf5ff131ea66ee5a2bb9182ee1`.
G4 bütçe kimliği: `9e510ca7460ed5970db5`.
Kaynak veri `capture.jsonl.gz`, tekrar hesap `analyze.py`, sonuç `results.json`.
Bu dosyalar özel hesap akışından izinli işlem alanları içerir; otomatik
kamu yayını yapılmadı. Anahtar/auth okunmadı, yeni borsa isteği gönderilmedi.

## Teklif türü nasıl ayrıldı?

**Yukarı taşınmış:** Aynı piyasa ve taraftaki önceki kabul edilmiş emir,
tam dolmadan önce kayıtta teyitli iptal edilmiş; bunu en fazla 10 saniye
sonra daha yüksek fiyatlı yeni emir izlemiş. İptal sonucu, yeni POST'tan
önce kaydedilmiş olmalı. Sonradan öğrenilen nihai dolum bu sınıfa geriye
doğru karar girdisi yapılmadı.

Ana alt grup, bu yeni emrin bildirilen dolum zamanına kadar en fazla
10 saniye geçmiş olmasıdır. Bunlar Fable'ın önerdiği tanısal zaman
seçimleridir; Bosona'nın bulunmuş parametreleri veya optimize edilmiş
eşikler değildir. Diğer grup ilk giriş, dolum sonrası yeni emir,
aşağı/aynı fiyata yenileme ve daha uzun bekleyen teklifleri içerir.
Dolayısıyla bütün kontrol grubuna "hiç değiştirilmemiş teklif" denmez.

## Fiyat sonucu

Tablo dolum fiyatına göre sonraki piyasa orta fiyatını gösterir; **pay
başına cent**. Piyasa ortasından satış yapılabileceği varsayılmadı.
Rebate, varsayımsal satış ve kurtarılmış işlem kârı eklenmedi.

| Grup | +10 sn pay ağırlıklı | +30 sn pay ağırlıklı |
|---|---:|---:|
| Yakın zamanda yukarı yenilenmiş; 13 dolum / 10 parent | −5,70 c | −8,30 c |
| Diğer uygun dolumlar | +1,56 c | −0,47 c |
| Bütün uygun dolumlar | −0,02 c | −2,21 c |

Parent eşit ağırlığında işaretler aynı. Piyasa eşit ağırlığında yukarı
yenilenen grup −4,15/−6,35 c; diğer grup +1,68/+0,09 c. Fiyat/yaş dağılımı
ve envanter farklılıkları bu ham farkın bir bölümünü açıklayabilir.

Aynı **piyasa, taraf, 20-cent fiyat bandı ve 30-saniye yaş dilimi** içinde
iki grubun bulunduğu yalnız **6 karşılaştırma hücresi / 5 piyasa** var.
Hücre içi parent eşit ağırlığıyla yukarı yenileme eksi kontrol:

- +10 saniye: **−3,58 c/pay**; hücrelerin dördü negatif, biri pozitif,
  biri sayısal olarak sıfır.
- +30 saniye: **−5,50 c/pay**; altı hücrenin altısı negatif.
- Bir piyasa sırayla çıkarılınca ortalama fark +10 sn'de
  −5,60…−0,75 c; +30 sn'de −6,40…−4,60 c.

Bu küçük, geniş bantlarla yapılmış gözlemsel eşleme; bağımsız altı deney
değildir. Envanter, emir sırası ve fiyat patikasının tamamı eşlenmedi.
Güvenilir gün-kümeli aralık için tek gün yeterli değil. Şu aşamada
"yukarı yenilemeyi yasaklasaydık şu kadar kazanırdık" hesabı üretilemez:
dolmayan emirler ve sonraki envanter yolu da değişirdi.

## İptalde öğrenilme ile iptal sırasında gerçekleşme ayrıldı

SDK'de 51 miktar artışının 16'sı `kapat:taze_yenile` ile öğrenilmiş.
Bu parent'ların 19 ayrı özel dolum parçasının **17'si ilk iptal isteğinden
önce özel akışta zaten alınmış**, ikisi saat toleransında çakışıyor.
Bu parent düzeyi bir çapraz tablodur; her parçanın hangi toplam artışta
öğrenildiği aynı şey değildir.

56 gerçek dolumun tamamında:

| Zaman sınıfı | Adet |
|---|---:|
| İptal isteği yok | 22 |
| İlk iptal isteğinden önce özel akışta görülmüş | 31 |
| Bildirilen kaynak saati ±100 ms ile iptal SDK çağrısıyla çakışıyor | 3 |

Son üçü **kanıtlanmış kaybedilmiş iptal yarışı değil**. Exchange'de etkin
iptal zamanı elimizde yok. Sıfır toleransta ikisinin kaynak zamanı iptal
cevabından sonra görünüyor; 100/250 ms toleransta üçü de belirsiz çakışma.
LTP kaynak saatini fiziksel gerçekleşme anıyla özdeşleştirmek bu yüzden
yanlış olur. Bu üç olayın +10/+30 sn ortalama fiyat sonucu da pozitif;
bu kesit, iptalle çakışan bütün dolumları kötü diye silmeyi desteklemiyor.

Fiyatlar yaklaşık 1 Hz G_KARAR kaydından, hedef andan önceki son kayıtla
alındı: kayıt mesafesi en fazla 1,5 sn, kitap yaşı en fazla 3 sn. Bu ölçüm
dolum sonrası tanı içindir; saniye-altı karar veya kuyruk fırsatını çözmez.

## Gerçek işlem sonucu ve canlı kontrol

Donmuş ilk çıkarımda son pencere henüz çözülmemişti; `results.json` bunu
korur ve ilk beşin +10,10282434 dolarını gösterir. Sonraki **17:22:39 UTC
/20:22:39 TR** salt-okunur runtime kesitinde altıncı da sonuçlanmıştır:

| Başlangıç UTC | İşlem PnL, USD |
|---|---:|
| 16:45 | +0,15000000 |
| 16:50 | −3,25000000 |
| 16:55 | +6,30000000 |
| 17:00 | +5,30602432 |
| 17:05 | +1,59680002 |
| 17:10 | +0,14040000 |
| **İlk altı toplam** | **+10,24322434** |

İade/sabit gider hariç işlem sonucu; sonraki iki açık pencere dahil değil.
En iyi üç pencere çıkarılırsa ilk altı toplamı −2,9596 dolar; pilot
başarısı kalıcı avantaj veya G2/G3'e nedensel üstünlük olarak sunulmaz.

`runtime.json`: tek LIVE writer185637, iki kayıtçı186232/186233 sağlıklı;
kaynak/manifest aynı, SDK yazma hatası0, belirsiz emir sayacı0. Son
mutabakat17:22:00UTC'de yerel/kamu −5,09 dolar, risk3,75 dolar. Eski
hesap toplamı G4 sonucu değildir. Bütçe anchor−15,3345 / limit100 /
cutoff−115,3345 aynı. STOP yok; yeniden başlatma veya finansal müdahale yok.

Saklanan STATE114 saniye eskiydi; güncel emir/risk yorumu yalnız bu dosyaya
dayandırılmadı, SDK/log canlıydı. Kayıtçıların enum-reddedilen mesaj sayıları
A3/B2, taşma0. Sağlıklı olmaları eksiksiz bütün-mesaj kapsamı demek değil;
bu altı penceredeki özel dolum miktarları ayrıca uzlaştırıldı.

Son teslim kontrolü **17:27:02 UTC /20:27:02 TR**:
`runtime_handoff.json` içinde aynı writer/kaynak/bütçe ve iki sağlıklı
kayıtçı tekrar teyitli. Yedinci pencere +1,80297144 ile çözülünce G4'ün
sonuçlanmış toplamı **+12,04619578 dolar**; iki pencere hâlâ bekliyor.
17:26:24 mutabakatında yerel/kamu aynı (−3,29), kayıtlı risk4,75 dolar;
SDK yazma hatası0. Bu sonraki kesit ilk-altı dolum analizine eklenmedi.

## Sıradaki karar

Mevcut G4 ölçüm referansı olarak kalır. Opus/PRO incelemelerinde özellikle
yukarı yenilemenin neden gerekli olduğu, bekleme halinde kaçan iyi dolumlar,
envanter koşulları ve bu küçük karşılaştırmanın seçilim etkisi sorgulanmalı.
Bu bulgu bağımsız günlerde sürerse, tek bir kovalamayan-teklif değişikliği
aynı risk/bütçeyle tasarlanabilir. Şimdi G5, taker çıkışı veya yeni canlı
ayar uygulanmadı; yeni sürekli analiz servisi başlatılmadı.

Tekrar hesap (yalnız yerel donmuş kayıtlar; canlıya erişmez):

```bash
python3 /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g4_execution_20260922/analyze.py
python3 /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g4_execution_20260922/check.py
```

Zaman sızıntısı/bayat kayıt/pencere sonu, iptal öncesi bildirim ve belirsiz
saat kontrolleri; gerçek dolum çokluğu/miktarı, POST kapsamı, tam SDK sırası
ve sonucun birebir tekrar hesabı geçti. Hedefli Ruff F/E9 ve syntax geçti.
