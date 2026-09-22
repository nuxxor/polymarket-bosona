# Ultra + Fable: BTC15dk ortak karar ve karşı denetim

**Karar:** Pasif ağırlıklı alım/birikim ve bazı aktif risk azaltan karşı alımlar,
mevcut sabit-zamanlı taker adayından daha iyi bir davranış açıklamasıdır. Ancak
“sürekli taze kotasyonla kâr eden piyasa yapıcı çözüldü” sonucu kanıtı aşar.
Fable'nin rol analizi kullanılmalı; Ultra'nın muhasebe/faz/zaman düzeltmeleriyle
birleştirilmeli. Yeni pasif replay, aşağıdaki kusurlar giderilmeden ekonomik
karar veya ileri deney için doğrulanmış motor sayılamaz. Mevcut aday kontrol
olarak korunur; eşikleri değiştirilmedi, yeni süreç başlatılmadı.

Bu tur iki ana rapor, Ultra hata/deney belgeleri, Fable plan/özet ve karar
değiştiren kaynaklar okundu. Fable'nin beş mevcut replay testi yeniden geçti;
rol sayımları kaynak dolumlardan yeniden hesaplandı; üç küçük karşı örnek ve
kayıtlı replay limit taraması çalıştırıldı. Bütün zincir/istatistik araştırması
baştan çalıştırılmış değildir. Kanıt ve kaynak hashleri: [checks.json](checks.json).

## 1. Birlikte desteklenen sonuçlar

- BTC15dk toplam API nakit PnL'si +4.428,55$. Toplamın doğru olması davranış
  etiketinin, kalan envanterin veya uygulama modelinin doğru olduğunu kanıtlamaz.
- Fable sınıflandırıcısını donmuş 5.441 doluma yeniden uyguladım: 4.387 maker,
  1.054 taker. Eski geç-add tanımında 1.099 maker / 74 taker yeniden çıktı.
  Ücret imzası rol tahminidir; Fable'nin 156 API ve 303 zincir mutabakatı ayrıca
  raporlanmıştır, bu tur receipt decoder yeniden çalıştırılmadı.
- Adayın sabit t180/t600 taker giriş/eklemesi, Bosona'nın baskın uygulama
  biçimini temsil etmiyor. Bu, her olası taker stratejisinin ekonomik olarak
  reddedildiğini veya küçük mevcut deneyin yeterli olduğunu göstermez.
- Tamamlama bazen çift maliyeti 1$ üstündeyken de en kötü ödemeyi iyileştiriyor.
  Aktif alımların hepsi hedge değil; aynı yöne büyük risk açan kayıp örnekleri var.
- Tarihsel geç ekleme katkısı yoğunlaşmış ve küçük yeni dönemde negatif.
  Maker rolüne atfedilen kâr, maker olmanın nedensel kazancı değildir.
- Emir yerleştirme/iptal, dolmayan emir ve gerçek sıra gözlenmeden özel fiyat,
  boy ve iptal kuralı tek biçimde çıkarılamıyor.

## 2. Fable'de daraltılması gereken hükümler

**“Taze emir” doğrulanmış değil.** `s_period_level_age.py`, aynı fiyatta toplam
bid boyunun dolum miktarından büyük kaldığı ardışık snapshot süresini ölçüyor.
Bu seviyedeki miktarın Bosona'ya ait olduğunu bilmiyor. Eski emir kısmi dolumla
kalmış olabilir; yeni emir eskiden beri görünen seviyeye katılmış olabilir.
Dört saniyelik seviye süresi emir yaşının güvenilir alt/üst sınırı değildir.
İlk-son dolum aralığı da yerleştirme zamanını göstermez. Maker olması yeni
karar alınmadığını kanıtlamaz: kotasyonun fiyatı/boyu da bir karardır.

**“Ekleme yok = satıcı gelmedi” fazla kesin.** Bildiğimiz yalnız gözlenen dolum
olmadığıdır. Emir olmayabilir, iptal edilmiş olabilir, sıra gelmemiş olabilir;
karşı outcome BUY/mint eşleşmesi nedeniyle düz satıcı hikâyesi de eksiktir.
L2 delta kaydı bu belirsizliği azaltır ama emir sahibi/sırası vermediğinden,
iptalin kendi varsayımsal sıramızın önünde olduğunu tek başına söylemez.
Resmî [market stream şeması](https://docs.polymarket.com/market-data/realtime-data)
fiyat/seviye boyu yayımlar; burada emir-sırası çıkarılamaması şemadan yaptığımız
çıkarımdır, tam L3 kayıt varmış gibi davranılmamalıdır.

**Fable'nin “aritmetik/veri hatası yok” cümlesi dar kapsamlıdır.** Ultra'nın
conditionId çakışması, ilk-saniye fazı, MERGE sonrası denge ve tarihsel fiyat
alım-zamanı kusurları bununla çürütülmüyor. Fable rol×faz tabloları eski fazları
kullanıyor: 1.173 eski geç dolum ile Ultra'nın düzeltilmiş 1.150 dolumu farklı
kümedir. Nihai rol×faz tablosu aynı düzeltilmiş evrenle yeniden kurulmalı.

**Gelecek uygulama fiyatı otomatik look-ahead değildir.** `candidate.py:157`
niyeti önce mevcut bilgiyle seçiyor; 170–178'de karar anındaki olasılık ve
sabit 55¢ tavanını sonraki fiyata uyguluyor. Karar anında belirlenmiş limitin
ileride pahalı uygulamayı reddetmesi gerçekleştirilebilir bir davranıştır.
[Resmî limit emir tanımı](https://docs.polymarket.com/trading/place-orders)
fiyat sınırı ile sonraki eşleşmeyi ayırır. Küçük kontrol aynı ilk niyetin farklı
sonraki fiyatlarda kabul/red alabileceğini gösteriyor; bu kendi başına karar
sızıntısı kanıtı değildir. Buna rağmen 90sn'ye kadar sonraki dakikalık fiyat,
ask/derinlik ve emir ömrü olmadığı için eski hesap gerçek işlem testi değildir.
Başarısız uygulama beklerken scheduler'ın nasıl ilerlediği ayrıca denetlenmeli.
“Uygulamayı önceki fiyattan yap” önerisi eksikliği çözmez; önceki fiyatın işlem
anında hâlâ alınabilir olduğunu varsayar. Niyet, limit, aktif süre ve gerçek
sonraki uygulama gözlemi ayrı tutulmalıdır.

## 3. Fable pasif replay: doğrudan çalıştırılmış karşı örnekler

Kaynak: `fable_review_20260921/code/passive_replay.py`.

| Kusur | Yeniden üretim | Sonuç / anlam |
|---|---|---|
| 198–204: seviye altı printte miktar kontrolü yok | 40¢ alış kotasyonu; 39¢'de yalnız 1 pay print | Kötümser mod 5 pay dolmuş yazıyor. Seviye aşılması tek başına 5 pay gerçekleşme garantisi değil. |
| 191–208: sessiz >3sn boşluk kontrolünden önce dolumlar işleniyor | t30 ve t35 snapshot; t32'de print | Boşlukta 5 pay doluyor. “Boşlukta askıda” varsayımı her akışta uygulanmıyor. |
| 216–227: hedge alışında nakit sınırı özellikle atlanmış | Dört 5-pay pasif alım ve iki 10-pay hedge | Nakit 20,336$; rapordaki 15$ ortak sınır aşılmış. |
| 235–245: iki açık kotasyon için ortak nakit rezervi yok | Kayıtlı çıktılarda P1 kolu denetimi | Hedge olmayan kollarda da limit aşımı var; yalnız P2 istisnası değil. |

Kayıtlı S replay'inde **12 farklı piyasada 19 piyasa×kol sonucu 15$ üstünde**;
bunların ikisi P1, diğerleri P2. Azami nakit **24,90693$**. `replay_after_s`
dosyasında altı piyasada 13 piyasa×kol aşımı; üçü P1. İki dosyanın piyasaları
örtüşür; bu sayılar birbirine eklenerek bağımsız piyasa sayısı yapılamaz.
Tek başına bu kusurlardan düzeltilmiş toplam PnL'nin yönü çıkarılamaz.

Ayrıca kod kotasyon yerleştirme/iptalini anlık, hedge'i aynı snapshot ask'ından
kabul ediyor; emir kabul/iptal gecikmesi ve iptal sırasında dolum sınanmıyor.
Kamu activity saniyesini eşleşme saniyesi yapıyor. Ultra BTC15dk'da bitişten
çok sonra zincire yazılan örnekler göstermişti; sabit 2–3sn gecikme tüm olaylara
taşınamaz. API printlerinin eksiksizliği/çokluğu ve gerçek maker fiyat/miktarı
kontrol edilmeden kuyruk tüketimi kesinleşmez.

**“İyimser/kötümser PnL alt–üst sınırı” matematiksel sınır değil.** Fable'nin
kendi S tablosunda P1b kuyruk-arkası −4,80$, kuyruk-önü −12,35$; sonrası
+10,45$ ve −0,60$. Daha fazla/erken dolum sonraki envanteri ve fırsatları
değiştirir, zararlı dolumları da artırabilir. Bu iki yol dolum varsayımı
senaryolarıdır; PnL sıralaması veya güven aralığı değildir. Bir kötümser
senaryonun negatifi bütün pasif stratejileri reddetmez. Kolların tamamının
aynı risk/gün/kapsam tanımıyla değerlendirilmesi gerekir.

## 4. Tek sonraki işin sırası

**Önce birleşik BTC15dk emir/rol/gerçekleşme denetimi; ardından ekonomik replay.**
Bu iki ayrı bot başlatma önerisi değildir:

1. Ultra'nın kimlik/faz/envanter/zaman düzeltmelerini ayrı araştırma sürümünde
   Fable rol etiketiyle birleştir. Aynı piyasada dolum, parent ve rol toplamları
   uzlaşsın; eski aday kontrol olarak korunsun.
2. Sonuçtan bağımsız seçilmiş küçük BTC15dk kohortunda bütün emirleri ve risk
   yollarını çöz. Salt maker oranı için on gün beklemek gerekmiyor; uzun
   gözlem, davranışın yaygınlığı ve ekonomi için gereklidir. Kamu verisinin
   çözemediği yerleştirme/iptal zamanları belirsiz kalmalı.
3. Mevcut BTC15dk verisinin gerçekten yettiği yerlerde miktar korunumu,
   kısmi dolum, ortak bütçe rezervi, veri boşluğu, iki-token/mint eşleşmesi,
   nedensel saat ve kabul/iptal gecikmesi denetimlerini geçen replay kur.
   Yetmeyen L2 delta/işlem kaydı ayrı ihtiyaç olarak tarif edilsin; mevcut
   recorder bu incelemede değişmedi. Yeni recorder veya shadow başlatılmadı.
4. Ancak bu kapı geçilince önceden sabitlenmiş pasif alım ve aynı riskli
   tamamlama kontrolünü ileri veride kıyasla. Eski ekonomik kabul kapısı
   korunur; ≥100 kotasyonlu piyasa, ≥100 gerçekleşebilir giriş ve ≥50
   eklemeli piyasanın yerine otomatik geçmez.

## 5. Doğrulama ve teslim sınırı

`PYTHONDONTWRITEBYTECODE=1 python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/ultra_fable_synthesis_20260921/check.py`

Beş mevcut replay testi, rol öz-test/sayımı, üç karşı örnek, kayıtlı limit
kontrolü, hedefli Ruff ve syntax geçti. Yeni kontroller kusurların varlığını
belgeleyen karakterizasyonlardır; replay düzeltilmiş sayılmaz. Beş donmuş
aday/veri hash'i aynı. Kaynak ve inceleyici çıktıları değiştirilmedi.

İnceleme anında Fable'nin atıf yaptığı `results/audit_verification.json`
bulunmuyordu; rapor kendi karşıt doğrulama turunun sürdüğünü söylüyor. Tam
bitmiş bağımsız kabul turu varmış gibi değerlendirilmedi. Fable'nin rol kanıtı
ile başlığının kesinliği, Ultra'nın hata kanıtı ile gelecek deneyin henüz
çalıştırılmamış olması ayrı tutuldu.
