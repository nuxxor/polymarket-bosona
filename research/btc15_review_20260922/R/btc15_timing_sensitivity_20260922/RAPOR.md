# BTC15: gelecek bilgisi, saat sırası ve aynı kurallar

**Üç çalışma tamamlandı. Güçlü, kopyalanabilir kâr kanıtı çıkmadı.** Aşağıdaki dolarlar koşullu yerel simülasyondur; kalibre ekonomik PnL bütün kollarda null. Sekiz atama aynı görülen UTC gününden; altısı sonradan muhasebesi doğrulanabilen veriyle değerlendirildi. Bu kör ileri test veya bağımsız günler örneklemi değildir.

## 1. Karar anı ile sonradan doğrulanan bilgi ayrıldı

Defter, fiyat adımı ve Chainlink yalnız alınma saati karar anını geçmiyorsa kullanılabiliyor. Sonradan tamamlanan API, receipt ve resmî kazanan yalnız ortam/muhasebe doğrulamasında. P0 adaptöründe resmî açılış referansıyla sonradan uyuşma artık geçmiş karar girdisini kapatmıyor; karar kaydedilmiş referansı kullanıyor, sonradan uyuşma ayrıca raporlanıyor. Bu kohortta referanslar zaten uyuşuyor; bu ayrımın kâr artışı olduğu iddia edilmiyor.

23:00 sözleşmesinin ilk iki taker API listesinde bir gerçek satış eksikti. Sonraki listede yalnız bu satır eklendi; bağımsız blok taraması ve iki WS ile miktar doğrulandı. Eski MISSING_DATA sonucu korundu; bu çalışma ayrı RECONCILED_LATER etiketi kullanır. Geç doğrulama, o anda kullanılabilen işlem sinyali yapılmadı.

Yeni ham WS ilk tick değerini vermediği için ilk deneme belirsizdi. Başlangıçtan önce 22:56:09.006 UTC alınmış Gamma yanıtındaki 1¢ adımı kullanıldı; gelecekteki tick değişimleri geçmişe taşınmadı. Yeni resmî sonuç ayrı önbelleğe alındı; eski yanıtlar aynı.

| UTC başlangıç | Donmuş veri kapısı | Bu çalışmadaki kapsam |
|---|---|---|
| 20:45 | PASS_OBSERVED_FLOW_GATE | PASS_OBSERVED_FLOW_GATE |
| 21:00 | MISSING_DATA | MISSING_DATA |
| 21:15 | PASS_OBSERVED_FLOW_GATE | PASS_OBSERVED_FLOW_GATE |
| 21:30 | PASS_OBSERVED_FLOW_GATE | PASS_OBSERVED_FLOW_GATE |
| 21:45 | PASS_OBSERVED_FLOW_GATE | PASS_OBSERVED_FLOW_GATE |
| 22:00 | PASS_OBSERVED_FLOW_GATE | PASS_OBSERVED_FLOW_GATE |
| 22:15 | MISSING_DATA | MISSING_DATA |
| 23:00 | MISSING_DATA | RECONCILED_LATER |

21:00 bağlantı kopması, 22:15 kimlikli eksik WS işlemi nedeniyle tüm atamaların toplamı null. Eksik piyasa sıfır işlem/kâr sayılmadı; yalnız altı hesaplanabilir pencerenin koşullu toplamları aşağıda.

## 2. Kabul, dolum, iptal ve öğrenme sırası sınandı

Altı profil sonuç hesabından önce sabitlendi. Kuyruk önü/arkası ve aynı milisaniyede işlem önce/yaşam döngüsü önce olmak üzere kol başına 24 senaryo. 500 ms kaydırma ölçülmüş hata sınırı değil, önceki saat çelişkisinden hareketle sabit stres. Bütün gerçekçi gecikme/sıra yollarını kapsamaz; aşağıdaki en düşük/en yüksek sonuçlar matematiksel sınır değildir.

| Profil | Kabul ms | İptal ms | Ek öğrenme ms | İşlem saati kaydırma ms |
|---|---:|---:|---:|---:|
| legacy_fast | 250 | 250 | 0 | 0 |
| legacy_slow | 750 | 750 | 500 | 0 |
| earlier_trade | 250 | 250 | 0 | -500 |
| slow_accept_fast_cancel | 750 | 250 | 500 | -500 |
| fast_accept_slow_cancel | 250 | 750 | 500 | -500 |
| late_notice | 250 | 250 | 500 | 0 |

L2 yayım saati kabul ortamının vekili; LTP yayım saati işlem saatinin vekili. İşlem 500 ms erkene taşındığında kamu mesajının alınması erkene çekilmedi. Kabul/iptal durum cevabının dönüş süresi kabul gecikmesiyle aynı varsayıldı. Özel dolum bildirimi ölçülmüş değil; kamu alım saati + senaryo gecikmesiyle temsil edildi. Kamu kitap/işlem ve hesap order/trade bildirimleri ayrı akışlardır. [Kamu akışı](https://docs.polymarket.com/market-data/realtime-data), [hesap olayları](https://docs.polymarket.com/trading/realtime-order-updates).

**Somut karşı örnek:** 20:45, M1 bid/kuyruk arkası: eski hızlı saatle +0,10 $, işlemi 500 ms erken sayınca −4,80 $. Her ikisinde altı dolum var; ilkinde 15 Up/15 Down ve 14,90 $ maliyet, ikincide 10 Up/20 Down ve 14,80 $ maliyet. Up kazanıyor. Fark işlem adedinden değil, açık yön riskinden geliyor.

## 3. Aynı kuralların sonucu

P0 karar kaynağı/55¢ limiti aynı. M1 bid, M1 bid−1 sent, M2 bid ve önceki rezervli M2 aynı. Her piyasa/kol bağımsız: 5 pay klip, 10 net, 15 $ nakit, −5 $ en kötü sonuç. t30..839 her saniye karar; t840 iptal. İadeler sıfır, taker ücreti nakitte; piyasa etkisi ve bilinmeyen iptal kuyruk kredisi yok. Bunlar ortak portföyün 15 $ bütçesi değildir.

| Kol | Tam senaryo / 24 | Pozitif toplam | Koşullu toplam aralığı $ | En iyi pencere hariç aralık $ |
|---|---:|---:|---:|---:|
| Pasif bid | 24 | 0 | -15.4389…-1.5660 | -15.8167…-2.2003 |
| Pasif bid−1¢ | 24 | 0 | -14.6599…-4.0599 | -15.5099…-8.3500 |
| Bid + dengeleme | 24 | 2 | -9.5647…+1.7063 | -9.6647…-2.2003 |
| Bid + rezervli dengeleme | 24 | 0 | -5.1000…-1.7141 | -5.6500…-2.4141 |

Dengelemenin iki pozitif hücresi aynı kuyruk-önü/geç-öğrenme profilinin iki sıra varyantıdır: +1,7063 $. En iyi tek pencere çıkarılınca −3,3166 $ kalır. İki bağımsız başarı değildir.

Ana karşılaştırma: eski hızlı profil, kuyruk arkası, aynı-ms yaşam döngüsü önce.

| UTC | Pasif bid | Bid−1¢ | Dengeleme | Rezervli dengeleme | P0 |
|---|---:|---:|---:|---:|---:|
| 20:45 | +0.1000 | -0.7500 | +0.1000 | -0.6500 | +0.4857 |
| 21:15 | -1.0344 | -4.1000 | -1.0344 | -0.8844 | +0.0000 |
| 21:30 | -0.8059 | -0.3500 | -0.8059 | -0.2559 | +0.0000 |
| 21:45 | -1.5550 | +0.2000 | -1.2039 | -0.4000 | +0.0000 |
| 22:00 | +0.1000 | -3.8000 | +0.1000 | +0.7000 | +0.0000 |
| 23:00 | +0.5000 | -3.1500 | +0.0762 | -0.2238 | +0.0000 |
| Altı pencere | -2.6953 | -11.9500 | -2.7680 | -1.7141 | +0.4857 |

P0 yalnız bir pencerede işlem yaptı; altı uygun pencerede 250/750 ms sonuçları aynı. Bu küçük pozitif P0 toplamı da kopyalanabilir strateji kanıtı değil.

## Simülatörde düzeltilen somut kusur

İlk koşunun 14 yolu “kabul defteri bilinmiyor” oldu. Kayıtlar defterin taze (0–26 ms) olduğunu, spread’in yalnızca 4–5¢’ye açıldığını gösterdi. Kararın 3¢ spread filtresi yanlışlıkla kabul anına da uygulanıyordu. Yeni kabul kontrolü gerçek defter tazeliği/geçerliliği, post-only, tick ve gönderilmiş fiyat sınırını kullanır. **Yeni emir kararı hâlâ 3¢ spread filtresine tabidir.** Aynı ayrım P0 uygulama adaptöründe yapıldı. Eski aday ve eski sonuçlar değiştirilmedi; bu turun eski davranışı legacy_arrival_source/ ve legacy_arrival_results/ içinde korunuyor. null_diagnostic.json kusurun somut fiyat/saat kanıtıdır.

## Karar

Basit “bid’e katıl ve gerektiğinde karşı tarafı al” mekanizmasının sağlam kazanç kanıtı yok. Sonuç saat/kuyruk varsayımına bağlı; birkaç pozitif hücre bir üstünlük testi değildir. Bosona’nın maker ağırlığı bu mekanizmayı araştırmayı gerekçelendiriyor; onun fiyatlama, iptal, boy veya piyasa seçme kuralını bildiğimiz anlamına gelmiyor.

Bu sonuçlarla aynı basit kolları kârlı aday diye uzun shadow’a taşımayı önermiyorum. Sonraki teknik ihtiyaç aynı saat alanında kabul/iptal/kendi dolum kanıtıyla yürütmeyi doğrulamak. Bu görevde yeni hesap bağlantısı, emir, LIVE, shadow veya kaydedici başlatılmadı. Gerçek saat kanıtı gelene kadar koşullu senaryo ve kalibre ekonomik PnL ayrımı korunmalı.

## Tekrar üretim ve sınırlar

```bash
P=/home/taygun/Masaüstü/KararAtlas/base1/bin/python3
N=/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_timing_sensitivity_20260922
OPENBLAS_NUM_THREADS=1 "$P" -B "$N/run.py" repeat
"$P" -B "$N/check.py"
"$P" -B "$N/run.py" report
"$P" -m ruff check --no-cache "$N/run.py" "$N/execution.py" "$N/check.py"
```

repeat HTTP/RPC çağrılarını engelleyerek iki tam koşu yapar. Eski aday/protokol, ham kayıt, kaynak ve önceki teslim manifestleri hash ile denetlenir. results/markets/ her yolun nakit/envanter/dolum/öğrenme saatlerini ve karar özet hash’ini içerir. results/checks.json negatif kontrolleri; results/reproducibility.json aynı-hashli çıktıları gösterir. Ham Chainlink açık gzip dosyasının sabit byte önekinden alındı; gereken son kararların sonrasına kadar kayıt var, kesilmiş kuyruk tamamlanmış arşiv sayılmadı.

Bir gün/altı uygun pencere ekonomik kabul için yetersizdir. Senaryolar aynı piyasaların tekrarlarıdır; bağımsız 576 gözlem değildir. Eski 10 gün/100 piyasa kabul ölçütü açık.

Doğrulama: 23 kontrol geçti; 8 hesap çıktısı ağsız iki koşuda aynı hash ile üretildi. 576 yolun tamamında risk limitleri korundu. Kabul kontrolü düzeltmesi yalnız 14 eski belirsiz yolu değiştirdi; diğer 562 yol ve P0 kontrolleri birebir aynı. 72 gerçek karar bağlamında bütün gelecek fiyat/ref kayıtları silinince bağlam değişmedi; varsayılan motorun 16 gerçek piyasa yolu eski motorla eşdeğer.
