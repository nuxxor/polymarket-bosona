# M1 — Pasif teklifin gerçekleşebilirliği

21 Eylül 2026. Sonlu, emir göndermeyen tarihsel deney.

**Sonuç:** Basitçe en iyi alışın bir sent gerisine beş paylık teklif bırakmak bu örnekte kazanç göstermedi. Görünen kuyruğun arkasında çok az dolum hesaplanıyor; kuyruk önünde olma senaryosu da toplamda negatif. **Bu kural yeni bir işlem shadow'una yükseltilmedi.** Sonuç, bütün maker stratejilerinin veya Bosona'nın kârsız olduğu anlamına gelmiyor.

## Deney ve kapsam

19 Eylül 15:20 ≤ başlangıç < 21 Eylül 18:30 UTC arasındaki **614 takvim slotundan**, her UTC gününde hash sırasıyla 32 slot seçildi: **96 piyasa**. Bosona'nın dolumu, kazanılan para veya sonuç seçime girmedi. Eski tarihlerin tekrar araştırılması nedeniyle temiz dış örneklem değil.

Her slotta t=30,120,210,280: toplam **384 gözlem noktası**. Her iki token için bağımsız 5 paylık teklif:
- En iyi bid sent ızgarasına aşağı yuvarlanır; ana fiyat bunun **0,01 dolar altı**. Aynı yuvarlanmış seviyeye teklif kontrolü ayrıca tutulur.
- Karar +250 ms'de varsayımsal aktivasyon; +1.000 ms'de iptal isteği, +1.250 ms'de etkili iptal.
- Kaynak zamanındaki +350…+1.150 ms işlemleri değerlendirilir: iki uçta 100 ms saat payı. Bu gerçek emir kabul/iptal gecikmesinin ölçümü değil, sabit mühendislik varsayımı.
- Karar ve aktivasyon anlarında sadece o ana kadar alınmış defter kullanılır. Emir fiyatı sonradan iyi görünen seviyeye taşınmaz.
- Sonuç etiketi yalnız ödeme hesabında kullanılır. Sonuç ters çevrilince fiyat/karar/dolum miktarı değişmiyor; testle doğrulandı.
- Maker komisyonu ve rebate sıfır varsayımı; gas/sabit gider dahil değil. Kâr rakamları gerçek cüzdan sonucu değildir.

Bunlar ayrı teklif problarıdır; envanter/risk bütçesiyle kendini yöneten tek bir bot veya yeniden yatırım yapan portföy değildir. Kontroller toplanıp uygulanabilir günlük gelir gibi sunulamaz.

## Gerçek veri ne kadar yeterli?

Yerel 100 GB'lık defter DB'si salt okunur açıldı; yalnız sabit kesitler alındı. 96 slotun 92'sinde piyasa abonelik kaydı var; eksik dört slot silinmedi.

**1.089 işlem mesajının 1.087'si (%99,82), miktarın %99,91'i** zincirle uzlaştı. Toplam görünen taker miktarı 27.553,836444; eşleşen 27.528,374592 pay. İki transaction için iki kamu RPC'sinde receipt bulunamadı; bunlar sıfır hacim sayılmadı.

Eşlemede yalnız Bosona değil, transaction'ın **bütün katılımcıları** için gerçek pUSD/CTF transferleri kontrol edildi. Her exchange match'in aktif emri, maker bacakları, tokeni, yönü ve miktarı ayrıldı. Aynı transaction'daki çoklu fiyatlar korunuyor; görünen mesaj hacmi her seviyeye tekrar yazılmıyor.

Kaynak: R1'de doğrulanan decoder ve [resmî V2 exchange arayüzü](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/interfaces/ITrading.sol). Kamu akışında book, price_change, last_trade_price ve tick_size_change alanları için [resmî şema](https://docs.polymarket.com/market-data/realtime-data) kontrol edildi. Bu akış emir-sırası içeren L3 veri değildir.

| Gün | Atanan gözlem | Kullanılabilen bağlam |
|---|---:|---:|
| 19 Eylül | 128 | 80 |
| 20 Eylül | 128 | 101 |
| 21 Eylül | 128 | 123 |
| **Toplam** | **384** | **304 — %79,17** |

**Önceden konan %95 bağlam kapısı geçmedi.** Son gün %96,09 olsa da geçmiş eksikler silinmedi ve bütün deney başarılı ilan edilmedi. Bu nedenle aşağıdaki ekonomi yalnız ölçülebilen alt kümenin tanısal sonucu.

Eksik nedenleri örtüşebilir: 62 çıkarılamayan başlangıç bağlamı; 11 eski/eksik defter, 5 akış boşluğu, 5 sıralama/tick belirsizliği, 2 geç işlem saati ve 1 bağlamda receipt eksikliği. Tam ve güncel bir defterde boş bid, “veri yok” diye sayılmadı: teklif üretilemeyen geçerli durum ayrı kaydedildi. Boş ask tek başına geçerli pasif alışa engel yapılmadı.

## Kuyruk nasıl hesaplandı?

**Arkada:** Kendi fiyatımızdaki görünen miktar önümüzde kabul edildi; karar ve aktivasyon görüntülerindeki miktarın büyüğü kullanıldı. İptal kaynaklı miktar azalması otomatik sıra avantajı sağlamadı. Gerçekleşen uygun yönlü hacim önce bu miktarı, sonra bizim beş payı tüketti.

**Önde:** Aynı fiyat, zaman ve hacimle önümüzde sıfır miktar varsayıldı. Bu elde edebildiğimiz sıra değil, hassasiyet senaryosu.

Bir fiyatın yalnızca görülmesi/dokunulması dolum sayılmadı. Akış gerçek maker seviyelerine bölündü. Diğer tokenin maker satışları, tamamlayıcı fiyattan aynı ekonomik bid tarafına dönüştürüldü; karar ve aktivasyon anlarında aynalı seviyelerin fiyatı ve miktarı kontrol edildi.

Bu iki hesap **kesin gerçek dolum veya PnL alt/üst sınırı değildir**. İptaller, gerçek sıra, iletilmeyen olaylar, piyasa etkisi ve kendi emrimizin gerçekleşme zincirini değiştirmesi bilinmiyor. Daha az dolum, daha az zarar da yaratabilir. Ama fiyat değmesini dolum sayan ölçümün yerine denetlenebilir hacim hesabı koyar.

## Sonuç

| Sabit teklif | Senaryo | Dolan teklif / uygun teklif | Pay | Tanısal sonuç |
|---|---|---:|---:|---:|
| **Bir sent geriden** | Görünen kuyruğun arkası | **9 / 501** | **45,00** | **−8,35 $** |
| Bir sent geriden | Kuyruk önü varsayımı | 89 / 501 | 422,14 | −46,93 $ |
| Yuvarlanmış en iyi alış | Görünen kuyruğun arkası | 18 / 488 | 87,13 | −9,31 $ |
| Yuvarlanmış en iyi alış | Kuyruk önü varsayımı | 269 / 488 | 1.278,13 | −22,82 $ |

Ana teklifte öndeki görünen miktarın medyanı **420 pay**. Bizim teklif 5 pay. Arkada senaryosunda dolum oranı yalnız **%1,80**. Bu, sabit teklifimizin önündeki hacmin önemini gösteriyor; Bosona'nın gerçek kuyruk yerini göstermiyor.

Ana teklifin arkada sonucu günlere göre −5,20 / −4,50 / +1,35 dolar. Son gün yalnız iki dolum var. Son güne veya başarılı bir saate yeni eşik seçilmedi. Dokuz dolum ve eksik kapsamdan kalıcı zarar/kazanç oranı çıkarılmadı.

**Çıkarım:** Maker ağırlığını doğrulamış olmak, düz bir pasif alış kuralını kârlı yapmıyor. Bu testte kuyruğun önünü varsaymak bile kâra yetmedi. Dolayısıyla burada “yalnız daha hızlı olursak tamamdır” veya “yalnız kuyruk rantı var” kanıtı bulunmadı. Bosona'nın teklif seçimi, yenilemesi, iptali ve envantere göre davranışı hâlâ belirleyici adaylar.

## Uygulama sırasında bulunan ölçüm hataları

Üç düzeltme de kaynak/ara çıktı ile saklandı; ilk deneme başarı diye sunulmadı.

1. **Tam görüntü yaşı ile defter yaşı farklı.** İlk çıkarım, tam görüntü üç saniyeden eskiyse bağlamı atlıyordu. Aradaki gerçek güncellemeleri uygulamak **55 bağlamı** geri kazandırdı: çıkarılan bağlam 267 → 322. Güncel defterin üç saniyelik tazelik kuralı gevşetilmedi. İlk çıktı ve kaynak `extraction_v1.tar.gz` içinde.
2. **Kapanış sonrası tick geçmişe taşınamaz.** Gamma'nın güncel alanında 92 piyasanın 89'u 0,001 tick gösteriyordu; bunun karar anındaki değer olduğu doğrulanmamıştı. Bunu kullanan ön hesap geçersiz sayıldı ve `invalid_tick_trial_v1.tar.gz` içinde saklandı. V2, bilinen sent ızgarasında sabit 0,01 dolar mesafe kullanıyor. İlk protokol korunuyor; değişiklik, gerekçe ve hash'ler `protocol_v2.json / revision_manifest.json` içinde. Bu nedenle ekonomik sonuç ön-kayıtlı kör başarı testi diye sunulamaz.
3. **Mesaj fiyatı her bacağın fiyatı değil.** 70 eşleşmede mesaj fiyatı zincirdeki tam ağırlıklı fiyatla birebir aynı değildi; raporlanan ondalık hassasiyette yuvarlamayla uyumlu. Örneğin 50 pay için mesaj 0,46, gerçek ortalama 0,461088; farklı bacaklar 0,46 ve 0,47. Eşleme tx/token/yön/tam miktarla ve yuvarlama sınırıyla doğrulandı; kuyruk hesabında gerçek maker bacakları kullanıldı.

## Sonraki tek adım

**Yeni strateji lane'i açmak yerine, bu yürütme modelini kendi geçmiş gerçek emirlerimizle sınamak.** D/E/F kayıtlarında gönderim/kabul, iptal ve gerçek dolumları bilinen emirleri; dolmayanları da dahil ederek aynı defter ve zincir olaylarıyla karşılaştırmak gerekir.

Somut kabul: “model doldu dedi / gerçekte doldu” ve “model dolmadı dedi / gerçekte doldu” ayrımı, miktar ve saat belirsizliğiyle raporlanmalı. Gerçek sıra/iptal etkisiyle tutarsız bir simülatör üstünde yeni kârlı kural seçilmemeli. Bu kalibrasyondan sonra tek bağımsız, kendi envanterini kullanan teklif yönetimi shadow'u anlamlı olur. **Bu sonraki kalibrasyon henüz çalıştırılmadı.**

## Doğrulama ve runtime

Para/kuyruk/erken-geç işlem zamanı, eski tam görüntü + güncel delta, boş defter, tekrarlanan WS mesajı, farklı fiyatlı eşleşme ve bozuk exchange logu kontrolleri geçti. Sonucu ters çevirme testi dolum kararını değiştirmedi. Her simüle dolumun arkasındaki hacim kimlikleri, miktar sınırı ve PnL'si bağımsız Decimal hesabıyla kontrol edildi. Ruff, syntax ve tam veriden byte-identical tekrar denetlendi.

Londra 19:22:53 UTC kontrolü: sekiz eski shadow/gözlemci PID'si yok; ilgili çalışan shadow süreci yok. M1 yalnız sonlu kamu-verisi topladı. Jev, gerçek botlar, bütçeler ve ham kaydediciler değiştirilmedi.

Tekrar çalıştırma:

```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_maker_feasibility_20260921/replay.py"
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_maker_feasibility_20260921/check.py"
```

Kanıt dizini: `data/analysis/btc5m_maker_feasibility_20260921/`. `report.json` her teklifi, hacim/işlem kimliklerini, eksik nedenlerini, günlük sonuçları ve kaynak hash'lerini içeriyor. Ham kesitler, receipt'ler, önceki geçersiz deneme ve manifesto dosyaları korunuyor.

