# G5 — hazır, canlı kapalı

22 Eylül 2026. **G4 normal durduruldu; G5 başlatılmadı.** Londra'daki
çalışan kaynak değiştirilmedi. Bu dizindeki kaynak ve paket yalnız
`staging/g5` altında parkta. Yeni gerçek bütçe oluşturulmadı.

## Tam olarak ne değişiyor?

1. **Ortak hata düzeltmesi:** eski `denge_koru` G kolunu artık yönetmez.
   Miktar/rezerv ve t240/t290 kontrolleri gerçek teklif döngüsünde kalır.
   Böylece t180 sonrasında bir döngünün koyduğunu diğerinin iptal etmesi
   önlenir. A–F davranışı değişmez.
2. **Tek deney farkı:** G5, mevcut yeni-risk alışını yalnız en iyi alış
   yükseldi diye yukarı taşımaz. Örneğin 0,40 teklif varken alış 0,45'e
   çıkarsa G5 geçerli 0,40 emrini korur; G4_FIXED doğrulanmış iptalden sonra
   0,44'e yenileyebilir. Fiyat düşünce, veri/bütçe/kimlik bozulunca veya
   süre dolunca gereken iptaller devam eder. Azaltıcı teklifler iki kolda
   da eski fiyat bandıyla yönetilir.
3. **Karşılaştırılabilir kayıt:** aynı 5 pay, net10, taraf başına $10
   harcama+rezerv ve aynı toplam bütçe altında G5/G4_FIXED ataması.
   Her on dakikalık UTC blokta hash ilk kolu seçer, sonraki beş dakika
   diğer kol olur. Restart atamayı değiştirmez. Emir nesli, önceki parent,
   kapanış nedeni, karar anındaki envanter, rol ve net5/net10 kapasitesi
   POST öncesinde; sonuç/oid POST sonrasında kaydedilir.

Net10'u korumak değerinin ispatlandığı anlamına gelmez: ilk altı G4
penceresinde ilk ek POST'ların yerel katkısı −$6,55 çıktı. Kapasite,
bakım ve bütçeyi yine beraber değiştirmemek için yeni karşılaştırmada
net10 iki kolda da aynıdır. Bu, Opus'un “net10 kesin doğrudur” diye
yorumlanması veya aynı boyu büyütme önerisi değildir.

t180 iptalinin kaldırılması, iki kolda da ağır taraftaki ikinci teklifin
t240'a kadar kalabilmesini sağlar. Net sınırı aynı olsa da eski G4'e göre
180–240 saniye arası fiilî risk artabilir; “geç fazda hiç artış yok” demiyoruz.

Bu kural **yukarı yön tahmini, taker çıkış veya Bosona kopyası değil**.
Ucuzda bekleyen teklif yine kötü bir akışla dolabilir; daha az işlem
yapmak ve yükselen piyasada fırsat kaçırmak mümkün. “Hiç yukarı yeniden
giriş yapmaz” da demiyoruz: korunan mevcut emir yoksa, güvenlik/rol
değişimi sonrasında veya tam dolumdan sonra yeni karar kendi kurallarını
izler. Ekonomik üstünlük henüz gösterilmedi.

## Donmuş ölçüm ve karar

Asıl sözleşme [bot/protocol.json](bot/protocol.json). İlk gerçek
başlatmadan sonraki ilk tam UTC gününden 14 gün; iki kol ortak hesap
kaybı sınırına bağlı. Bütçe biterse bu deney durur; bütçe eklenmez, sıfırlanmaz ve süre
uzatılmaz. Yedi tam gözlem günü veya diğer kapsam kapıları sağlanmadan
biterse sonuç **DATA_LIMITED / veri yetersiz** olur. Bütçe nedeniyle
14 günlük sabit bitişten önce kesilen her koşu, yedi gün geçse bile,
yalnız betimsel fark raporlar; başarı teyidi sayılmaz. Asgari gün/piyasa/parent kapsamı
güç garantisi değildir. Birincil teşhis +30 sn gerçek dolum markout'u;
kâr kararı ayrıca ücret sonrası dolar/atanmış pencereye dayanır.
Sıfır dolum, eksik veri, süresi ufku aşan dolum ve çözülmemiş sonuç ayrılır.
Gün kümeli belirsizlik, en iyi üç piyasa hariç ve gün çıkarma kontrolleri
geçmeden ekonomik başarı ilan edilmez.

PRO'nun ikinci-parent katkısı ve fiyat farkı araştırması:
[GAP_CAPACITY.md](../../../../data/analysis/g4_execution_20260922/GAP_CAPACITY.md).
Fiyat farkı yön açısından bilgi taşıyor; pahalı tokeni almak otomatik
kâr üretmiyor. G5'e fiyat farkı, RSI veya geç taker kuralı eklenmedi.

## Doğrulama

- Yerel ve Londra: 29 gerçek quote/maintenance senaryosu; eski hata
  60 POST / 59 bakım iptaliyle üretildi, düzeltilmiş iki kolda 2 POST /
  sıfır bakım iptali. t240/t290, risk, bayat veri, belirsiz iptal ve
  minimum altı kısmi miktar korumaları geçti.
- Gerçek miktar fonksiyonunda 1.152 uygun net/pending durumu; 1.000
  çift pencere ataması; altı mevcut regresyon betiği geçti.
- G4 ortak geçiş aracının eski G4 testleri tekrar geçti. G5 geçişi
  yalnız geçici dosyalarda sınandı: ayrı bütçe kimliği, geçmişin
  korunması, tekrar aktivasyon ve yanlış marker reddi.
- 120 sn kamu akışı, iki kuru kol, sentetik 5 Up başlangıç envanteri:
  1.513 teklif kaydı, SDK kayıt hatası sıfır, gerçek emir/dolum sıfır.
  G4_FIXED 60/60, G5 42/40 kuru POST/iptal; G5'te bir WS yeniden bağlantısı.
  Eski bakım iptali sıfır. Kotasyon hareketi hâlâ 60 deneme sınırına
  ulaşabiliyor; bu ekonomik başarı veya bütün iptallerin giderildiği
  anlamına gelmez. İlk, çok geç saatli kamu koşusunda teklif yoktu;
  o koşu başarılı sayılmadı.

**60 deneme izlemi:** ilk tamamlanan pencere, 30. dakika ve ilk gün
saatlik kontrolde her kolun sınıra ulaşan pencere sayısı/oranı raporlanır.
Yetkili sayaç `taze_bitti.koy` / state içindeki `taze.koy`; kabul edilen
emir sayısı değildir. Sayaç artıp gönderimden vazgeçilen denemeler olabilir.
Eksik kapanış kaydı sıfır sayılmaz; ilk sınıra ulaşma anı veya sonrasındaki
azaltım engeli kanıtlanamıyorsa bilinmiyor kalır. Sınır etkisi ana paydadan
pencere silerek gizlenmez; sık/farklı doygunlukta sonuç yalnız teklif
koruma + mevcut 60 sınırı birleşiminin etkisi diye okunur. Deney içinde
limiti yükseltip devam etmeyiz. Bu kontrol takvimi operatör runbook'udur;
yeni bir arka plan izleyicisi kurulduğu anlamına gelmez.

Kaynak, paket ve kanıt hash'leri [READY.json](READY.json) içinde.
G4 kapanışının son salt-okunur teyidi 17:58:41 UTC: açık emir=0,
risk=0, LIVE yazıcı yok; 153 geçmiş pencere uzlaştı. Kümülatif işlem
PnL −$12,686919; G4 bütçe anchor'ına göre yaklaşık +$2,647581.
Rebate/sabit gider sonucu değil. Kaynak STATE dosyası yeniden yazılmadı;
son uzlaşma salt-okunur yeniden hesapta teyit edildi.

## Çalıştırılabilir kontroller

Repo kökünden:

```bash
python3 lanes/g_continuous/staging/g5/check.py lanes/g_continuous/bot
python3 lanes/g_continuous/staging/g5/check_transition.py lanes/g_continuous/bot
```

İkinci argüman yayımlanmış G4 kaynak dizinidir; yerel kirli çalışma
ağacındaki eski G1 dizini kullanılmamalı. Bu iki komut emirsizdir.
`smoke.py 120` gerçek kamu akışı kullanır; erken/orta pencere sırasında
çalıştırılmalı, kuru niyetleri dolmuş işlem saymaz.

`g5_operator.py` varsayılanı yalnız park edilmiş paketi ve hedef kaynağı
denetler. **Bu görevde `--operator-start` kullanılmadı.** Gelecekteki
explicit operatör başlatması; bütün eski pencerelerin mutabakatı, tek
yazıcı, yeni G5 aktivasyon kimliği ve iki kayıtçı kontrolünü tekrar yapar.
Yeni bağımsız $100 bütçe ancak o aşamada oluşabilir; tekrar komut bu
bütçeyi sıfırlamaz. G4 bütçesi G5 bütçesi diye kabul edilmez.
