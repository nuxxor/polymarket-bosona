# G2 yürütme ve aynı-piyasa denetimi — ULTRA alt çalışması

G2 faydalı bir mühendislik kontrolüdür; bu örnekte Bosona'ya davranışça yakın
olduğu veya yalnız çıkış tetikleyicisi eksik olduğu sonucunu desteklemiyor.
Giriş zamanı/yönü, parent sayısı, büyütme ve çok küçük hesabın minimum emir
geometrisi de farklı. Seçici taker azaltımı ayrı bir araştırma adayıdır;
otomatik olarak en yüksek getirili canlı yama değildir.

## Gerçek yürüyen G yolu

`lanes/g_continuous/identity_fix/bot/G_RELEASE.json` içindeki 16 dosyanın
hash'i yeniden hesaplandı ve hepsi uyumlu. `ab.py` SHA25fca69d..., politika
fbac759d... doğrulandı. `g.py:8` `--lane-g` ekler; `ab.py:12` G'yi ve miras
alınan F/D altyapı bayraklarını açar. G sinyali `ab.py:967` ile model/ref
girdisi kullanmadan oluşur; hedef `g_policy.py:19`, kalite `g_policy.py:35`.

- Teklif best bid−$0,01 ve gerçek tick'e aşağı yuvarlama; `.001` tickte
  bir tick değildir (`g_policy.py:27`). Yeni risk t<240, azaltım t<290.
- `ab.py:1034` dolmuş miktar + aynı yöndeki açık/belirsiz rezerv ile
  net envanteri sınırlar. `ab.py:1067` yeni emirde 5 pay minimumunu korur.
- `ab.py:1400` mutabakat/bütçe bozulduğunda mevcut emirleri de iptal eder.
  `ab.py:1420` kalite ve miktar izinliyse bid ile bid−2sent arasındaki
  emri tutar. İptal bakımı yeni emir cooldown'ına takılmaz.
- `ab.py:1440` civarındaki teklif dalında minimum boy, karşı açık teklif
  ile çakışma ve taraf başı kümülatif maliyet/rezerv $10 kapısı uygulanır.
  Hesap zarar kesicisi bundan ayrıdır. Taker tamamlama `ab.py:1808`
  fonksiyonunda var, ancak `TAMAMLA_ACIK=False`; G'de etkin değildir.
- Kimlik yaması ortak mutabakat girişinde (`ab.py:509`, `603`) token ve
  condition ile999'u düzeltir, uyuşmazlığı reddeder, ham satırı değiştirmez.

**Protokol özetinin sakladığı gerçek bakım davranışı:** `pencere_bakim`
(`ab.py:1890`) `denge_koru`yu (`ab.py:1697`) G için de çağırıyor. Bu eski
koruma t>=180'de net fark>=0,01 ise ağır taraftaki açık emri iptal ediyor.
Gerçek fonksiyon/sahte borsa testi: 5 pay emrin2payı dolmuşken t179'da
tutuldu, t180'de kalan iptal edildi. Bu, G kalite kontrolünün t240'ına
ek bir kuraldır. **İncelenen gerçek pilotta bu iptal gözlenmedi:**
`DENGE_SINIRI` olay sayısı0; yerel son state içindeki G emirlerinde
`kapanis=denge_siniri` sayısı0. Kayıpların nedeni diye sunulamaz.

**Minimum emirden doğan kilitlenme:** 2Up/0Down ve açık emir yokken gerçek
`d_miktar` yeniden aynı yönde3, karşı yönde2pay izin veriyor; ikisi de
5pay minimumunun altında. Bu durum t180 koruması olmadan da kısmi
dolumdan sonra oluşabilir. Pilot6pencerenin2'si tam5'e ulaşmayan netle
bitiyor: `1790070300` −0,004285pay, `1790070600` −4,990371pay. Son9işlemli
kapalı pencerede üçüncü örnek `1790073600` −2,32pay. Aynı minimumu taşıyan
bir taker kapanışını eklemek tek başına bu geometrik sorunu çözmez;
platformun farklı emir türü minimumları ayrıca doğrulanmalıdır.

## Yerel kesit ve normalize davranış

Yerelde yalnız `cuts/1790075698` var: toplama başlangıcı11:14:58UTC,
`latest.json` derleme saati11:15:54,136UTC.11:10penceresi sonucu bekliyor.
Bu kayıtların tamamı G2'nin12:07:30UTC başlangıcından **önce**; G2 sonrası
ekonomik sonuç değildir. Zamanlanmış ileri bitiş tamamlanmış veri sayılmaz.

22aktör×piyasa hesabı ham activity ile yeniden hesaplandı, bütün işlem
receipt'leri yeniden decode edilip nakit/miktar/parent/rol karşılaştırıldı.
Bağımsız `BUY ödeme−nakit` toplamı transfer-aware ledger ile eşleşti;
bu dar kohortta pencere öncesi BUY ve SELL yok. Pencere takvimindeki
atamalar, işlemsiz piyasa ve mutabakat yüzünden atlanan piyasa ayrıldı.

| Ölçüm | G | Bosona |
|---|---:|---:|
| Kapalı tüm10pencerede BUY/filled parent |54 /50|63 /26|
| Toplam pay |247,666086|3.490,907799|
| Taker pay |0|720,92|
| İkisinin de aldığı8pencerede ilk dolum medyanı |10sn|147,5sn|
| Aynı8'de ilk dolum nakit fiyatı medyanı |$0,40|$0,345|
| Aynı8'de gözlenen ilk yön uyumu |3/8|—|
| Aynı8'de tam sıfırdan yeniden açılma |16|0|
| Aynı8'de pencere başına toplam5pay normlu PnL toplamı |+$1,699060|−$1,172011|
| Aynı8'de5toplampaya normlu mutlak pay×saniye medyanı |195|292,9004|

Normlama `5*PnL/toplam alınan pay` şeklindedir; aynı bütçeli veya aynı
riskli uygulanabilir politika simülasyonu değildir. Tam sıfırdan yeniden
açılma ölçüsü Bosona'nın mikropay kalıntılarından etkilenir; sıfır sonucu
hiç yeniden risk açmadığını göstermez. Kamu saniyesinde netin işaret
değişmesi tek emirle reversal kanıtı değildir. Aynı saniyede iki G parent'ı
−5'ten+5'e geçirebilir, aralarında sıfır görülemez.

İlk altı pilot penceresinde iki aktörün de aldığı beş piyasada ilk yön
uyumu **0/5**. G ilk dolum medyanı11sn(6piyasa), Bosona163sn(5piyasa).
Bu dar kesitte ilk yön/zaman ayrımı taker çıkışından önce ortaya çıkıyor.
Bu, G'nin daha kötü kazandığını kanıtlamaz; hedef davranışa yaklaşıldığı
iddiasını sınırlar. Bosona'nın daha geç ilk gözlenen dolumu daha geç emir
verdiği veya ilk dakikalarda hiç teklif taşımadığı anlamına gelmez.

11:00 `1790074800` G−$2,30/Bosona−$27,39 örneğinde G kapısı erken
mutabakat anomalisinde kapandı.11:05 G ataması atlandı;11:09:09'da başarılı
mutabakat döndü. `operational_evidence.json` içindeki6geçersiz kayıt ve
2mutabakat başarısızlığı strateji davranışına dönüştürülmedi.

## İlk pilotun parası ve dolum sonrası fiyat

Yerel kesin hesap yeniden üretildi: +$9,20631474; son envanterin her
piyasadaki en kötü terminal ödemesi toplamı−$5,79797026; gerçekleşen ödeme
bunun+$15,004285 üzerinde. Kamu nakit karşılığı+$9,206314: $0,00000074
fark yerel limit-fiyat çarpımı ile zincir/API nakit hassasiyeti arasındadır.
Bu ayrım karşıolgusal strateji veya yönsel alpha hesabı değildir.

Yeni dar tanı: ilk pilotun A/B özel kayıtlarından40benzersiz trade×parent,
36dolmuş parent ve179,986086pay, bütün63kabul edilmiş parent'ın son
miktarıyla eşleşti. Aynı pilotun3.192 `G_KARAR` kaydı yaklaşık1Hz defter
kotasyonu verir;60sn aralıklı state snapshot'ı yerine bunlar kullanıldı.

Saat ekseni A/B'deki ilk alınan `MATCHED` özel mesajdır; tam execution saati
değildir. Hedef andan ileri kotasyon kullanılmadı; en son karar kaydı en
fazla1,5sn eski, kaynak defteri en fazla3sn eski ve bid<ask olmalı.
40dolumun40'ında5/10/30sn sonrası bağlam,38'inde hemen receipt öncesi
bağlam var. Receipt öncesi bağlam da execution sonrasında alınmış olabilir.

| Pay ağırlıklı tanı, sent/pay |+5sn|+10sn|+30sn|
|---|---:|---:|---:|
| Son mid − ödenen fiyat |+0,1804|−0,5280|+1,3885|
| Son bid − ödenen fiyat |−0,3335|−1,0280|+0,8885|
| Son mid − receipt öncesi mid,38dolum |−1,0738|−1,8533|−0,3535|

10sn mid−fiyat katkısı6pencerenin5'inde negatif;30sn toparlanmasının en
büyük katkısı ilk pencereden+$3,025. Fiyatların düşmesi/kısa ufuk ters
seçim kaygısını destekliyor; tek ufuk seçip garanti zarar veya ideal iptal
süresi çıkarmak doğru değil. Mid satılabilir fiyat değildir; bid derinlik ve
taker ücretini içermediğinden gerçek tasfiye getirisi de değildir.

## Gerçekte çalıştırılanlar ve tekrar

- `python -B .../execution/recompute.py`:16release hash'i,22ham aktör hesabı,
  receipt nakit/miktar/rol eşleşmesi, bağımsız terminal hesap,2zamanlı gerçek
  bakım kontrolü ve minimum emir kilitlenmesi assert'leri.
- `python -B .../execution/markouts.py`:40trade×parent tekilliği, A/B
  fiyat/miktar eşliği,63parent nihai miktarı ve nedensel kotasyon eşlemesi.
- İzole kaynak kopyasında `test_identity.py`, `test_g.py`, `test_g_stream.py`:
  üçü geçti. `safe_run.py` ağ bağlantısını ve credential dosyası okumayı
  reddetti; geçici dosyalar bu çıktı dizininin `tmp/` yoluna yönlendirildi.
- Yeni üçPython kaynağında Ruff F/E9 ve AST/sözdizimi kontrolü; sonuç JSON'ları
  yeniden okundu, tekrar çalıştırma hash'leri aynı. Kontrol özeti
  `verification.json`; kaynak/input hash'leri `results.json`, `markouts.json`.

Üretim kaynağı, bütçe, frozen rapor, state veya servis değişmedi. Canlı
999tekrarını gözledik denmiyor; gerçek geçmiş vaka emirsiz replay'i geçti.

## Ek dar deney adayı: risk artıran teklifin1sent tamponu

Bu aday markout'lar görüldükten sonra kuruldu; önkayıtlı başarı testi değildir.
Yalnız risk artıran (`G_KALITE.neden=open`) mevcut emir için güncel
`g_policy.target(bb,ba,tick,envanter)` fiyatı p'nin altına düştüğünde
iptal iste + teyit et + normal yeniden teklif yoluna dön. Azaltıcı emrin
mevcut koruma kuralını değiştirme. Geçerli eski tutma bandının dışındaki
emir zaten iptal edileceğinden ek aday sayılmadı.

`buffer_probe.py` gerçek kabul kimliği + SDK POST ACK + A/B özel
PLACEMENT ile mevcut parent'ı yaklaşık1Hz karar kaydına bağlar. İncelenen
aralık ilk iptal isteğinde, ilk herhangi bir dolum bilgisi alındığında veya
terminal durumda biter. Bu dar aralıkta G_KALITE.p'nin parent fiyatıyla
eşleşmesi, tek parent, açık mutabakat ve kaynak yaşı<=3sn zorunlu.
Dolum henüz bilinmezken alınmış8işlemli aday gerçekten bulunuyor:

| Kapsam | Parent sayısı |
|---|---:|
| Gerçek kabul / sonra dolan |63 /36|
| İlk dolumdan önce kimlikli karar kotasyonu olan |52; dolanların32'si|
| Taze risk artırıcı kotasyon gözlenen |35; dolanların19'u|
| Tampon kuralı en az bir kez tetiklenen |10;8dolan +2dolmayan|

Toplam19aday karar kaydı var. İlk adaydan ilk özel MATCHED mesajının
alınmasına fark,8parent için **185,22–3.117,55ms; medyan1.360,07ms**.
İlk herhangi bir matched-miktar gözlemine göre de hepsi pozitiftir
(en az185,00ms). Örnek `1790069400`,
`0xe223045cb09ccd8cedb93d30f64be90a27d320e29a34b63a55d2243c26c38693`:
t6,854'te p=bid0,45, yeni hedef0,44; MATCHED receipt3.117,55ms sonra.
`1790070900` parent
`0x727790a184b3bdfec3ad92591e972d806d172f45cd6e23576309eb9b45817703`:
t13,612'de p=bid0,41, yeni hedef0,40; receipt185,22ms sonra.

Gerçek54SDK iptal roundtrip'i22,22–1.029,67ms, medyan37,64ms. **Bunları
aday farkından çıkarmak kurtarılan dolum hesabı vermez:** exchange match
receipt'ten önce olmuş olabilir; SDK yanıtı exchange iptal-etki saati
değildir ve1.029,67ms gelecek gecikmenin üst sınırı değildir. İptal sonrası
tekrar giriş kuyruk konumunu, sonraki dolumu ve envanteri değiştirir.
Dolmayan2parent da ekonomik kontrollere dahil kalmalıdır. Dört dolmuş
parent'ın ilk dolumdan önce uygun1Hz kaydı yok; onlar “aday yok” sayılmaz.

Sonuç: adayın **kodlanabilir ve gerçek kararlarda sınanabilir** olduğu
mevcut kayıtlarla gösterildi; kazançlı olduğu veya Bosona'nın kuralı
olduğu gösterilmedi. Yeni bir simülatör gerekmedi. Ekonomik testin ayırt
edici en küçük kaydı her aday kararında `oid/kalan miktar/artırıcı-azaltıcı
sınıf/UTC+mono/defter kaynak+alınma saati` ile var olan iptalistek/cevap,
özel dolum ve yeniPOST kayıtlarının aynı kimlikle bağlanmasıdır. Yaklaşık1Hz
ara log yerine gerçek iptal kararının kaydı gerekir. Karşıolgusal maker
dolumu veya kâr bu çalışmada hesaplanmadı; üretime müdahale edilmedi.
