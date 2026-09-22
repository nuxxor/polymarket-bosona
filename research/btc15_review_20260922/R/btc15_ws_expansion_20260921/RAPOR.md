# BTC15 yeni pencere karşılaştırması

**Sonuç: kârlı taklit kanıtı yok.** Yeni üç atamanın biri bağlantı kopması nedeniyle eksik; iki pencere koşullu simülasyona uygun. Ana 250ms/kuyruk-arkası senaryosunda pasif bid ve aynı kurala dengeleme eklenmiş kol toplam −1,84033524$; bid−1sent −4,45$. Eski aday iki geçerli pencereye de girmedi (0$). Bu 0$, eksik veri nedeniyle değil, geçerli giriş filtreleri nedeniyle.

Kohort 21 Eylül 21:50 UTC civarında sonuç tablosu açılmadan takvimle sabitlendi. Uygulama motoru bu kesitte geliştirilip denetlendi; bu küçük çalışma temiz bir kör ekonomik doğrulama değildir. Önceki 20:45–21:00 pencerenin sonucu bu toplamlara eklenmedi.

## Veri ve mutabakat

| UTC pencere | Receipt | WS mesajı / pencere içi | Uygun defter noktası | Karar |
|---|---:|---:|---:|---|
| 21:00–21:15 | 517 | 515 / 497 | 901/901 | MISSING_DATA |
| 21:15–21:30 | 731 | 731 / 711 | 900/901 | PASS_OBSERVED_FLOW_GATE |
| 21:30–21:45 | 511 | 511 / 500 | 901/901 | PASS_OBSERVED_FLOW_GATE |

Toplam 1759 receipt ve 1757 WS mesajının gerçek miktar/nakitleri uzlaştı; 1708 mesaj sözleşme pencerelerinin içinde. Her piyasada ilk ve ikinci taker API listesi ile tüm katılımcı listesi zincirle eşleşiyor; bu kesitte API çokluk farkı yok. Her piyasada iki receipt ikinci ücretsiz RPC ile kontrol edildi.

21:00 penceresinde 901/901 defter örneği iyi olsa da 21:10:47.580 UTC bağlantı kopması var. Sıfır kâr diye sayılmadı. 21:15 penceresinin ilk geniş önek kontrolündeki iki ters-saat uyarısı başlangıçtan 250 saniye önceki yeniden bağlantıya ait: eski delta ile yeni tam görüntü 1ms ters. Yeni hesap başlangıçtan önce alınmış son tam çift-token görüntüden başlar. Eski ham kontrol `report.json`, pencereye ait gerekçe `eligibility.json` içinde korunur. 21:15 penceresinde t520’de tek defter-derinliği aynalama uyuşmazlığı kalır; önceki %95 uygun örnek kapısı değiştirilmedi. Bu bir kalibrasyon veya kusursuz defter iddiası değildir.

Fiyat adımı sonradan alınmış Gamma değerinden geriye yazılmaz; karar ve kabul anlarında alınmış book/tick_size_change olayından okunur. Eski bağımsız 16 kısa kotasyon deneyi bu tur koşulmadı; karşılaştırma tek envanter izleyen tam politikalarla yapıldı.

## Aynı kuralların yeni sonuçları

**Aşağıdakiler varsayımlara koşullu simülasyon dolarlarıdır; ekonomik PnL bütün kollarda null.** 5 pay klip, 10 net, 15$ nakit, −5$ en kötü sonuç; t30..839 her saniye karar, t840 iptal. Fiyatlar veya eşikler kâra göre taranmadı. Maker iadesi sıfır varsayıldı; taker ücreti nakitte dahil.

| Kol / kuyruk / gecikme | 21:15 | 21:30 | İki uygun pencere toplamı | En iyi pencere hariç |
|---|---:|---:|---:|---:|
| M1_bid:queue_back:250 | -1.0344 | -0.8059 | -1.8403 | -1.0344 |
| M1_bid:queue_back:750 | BELİRSİZ | +0.2000 | BELİRSİZ | BELİRSİZ |
| M1_bid:queue_front:250 | -4.5000 | -3.2167 | -7.7167 | -4.5000 |
| M1_bid:queue_front:750 | +0.0000 | -2.4067 | -2.4067 | -2.4067 |
| M1_bid_minus_cent:queue_back:250 | -4.1000 | -0.3500 | -4.4500 | -4.1000 |
| M1_bid_minus_cent:queue_back:750 | BELİRSİZ | +1.7000 | BELİRSİZ | BELİRSİZ |
| M1_bid_minus_cent:queue_front:250 | -2.2599 | -4.2000 | -6.4599 | -4.2000 |
| M1_bid_minus_cent:queue_front:750 | -2.3599 | -4.0000 | -6.3599 | -4.0000 |
| M2_bid_hedge:queue_back:250 | -1.0344 | -0.8059 | -1.8403 | -1.0344 |
| M2_bid_hedge:queue_back:750 | BELİRSİZ | +0.1803 | BELİRSİZ | BELİRSİZ |
| M2_bid_hedge:queue_front:250 | -4.5000 | +0.0295 | -4.4705 | -4.5000 |
| M2_bid_hedge:queue_front:750 | +0.0320 | +0.0320 | +0.0640 | +0.0320 |
| P0 mevcut aday / 250 veya 750ms | 0 | 0 | 0 | 0 |

Üç atamanın tamamının toplamı hiçbir kol için hesaplanabilir değil. 750ms/kuyruk-arkası 21:15 yollarında bir kamu mesajı tam varsayılan emir yaşam-döngüsü zamanına denk geliyor. Önce doldu/önce iptal oldu sırası seçilmedi; üç hücre BELİRSİZ kaldı. Kuyruk önü ve arkası PnL alt–üst sınırı değildir: önde olmak zararlı dolumları da artırabilir.

## Eski aday neden girmedi?

| UTC başlangıç | Up ask | Model Up | Ücret sonrası Up avantajı | Engel |
|---|---:|---:|---:|---|
| 21:15 | 57.0¢ | %61.74 | 3.02¢ | olasılık avantajı <5¢, 55¢ tavanı |
| 21:30 | 77.0¢ | %98.87 | 20.63¢ | 55¢ tavanı |

Her iki pencerede 12/12 planlı bağlam için nedensel Chainlink verisi bulunuyor; kaydedilmiş açılış TWAP’ı resmî referansla eşleşiyor. P0 ilk kararından sonra giriş imkânı bulunmayan pencereyi tekrar açmaz. İlk giriş olmadığı için sonraki ekleme/envanter kapıları devreye girmiyor. 55¢ tavanı veya olasılık eşiği değiştirilmedi.

## Dengeleme neden her zaman çalışmıyor?

21:15 kuyruk-önü/250ms yolunda t46’da 10 Up / 20 Down var; 14,50$ harcanmış. 5 Up hedge için 3,084$ gerekiyor, toplam 17,584$ olacağı için 15$ sınırı reddediyor. Dengeleme zararı azaltabilecek olsa da kullanabileceği nakit kalmamış. Kod bütçeyi aşmadı; mevcut mekanizma dengelemeye her zaman bütçe bırakmıyor. Bu bulgu limitleri artırma veya geçmişe göre hedge eşiği değiştirme gerekçesi yapılmadı.

Ana kuyruk-arkası/250ms yollarında net 10 paya ulaşmadığı için iki piyasada da taker dengelemeye geçilmiyor; M1 ve M2 aynı. Başka senaryodaki küçük pozitif hedge sonucu genel üstünlük kanıtı değildir. Tüm sonuçlarda gerçekleşen ve öğrenilmiş envanter ayrı; iptal yoldayken dolum ve gecikmiş kümülatif bildirim aynı dolumu iki kez yaratmaz.

## Bosona aynı piyasalarda ne yaptı?

| UTC başlangıç | Dolum | Maker / taker | İşlem nakit PnL |
|---|---:|---:|---:|
| 21:15 | 0 | 0 / 0 | +0.0000 |
| 21:30 | 2 | 2 / 0 | -22.0000 |

Bosona sonuçları ilgili sözleşmenin tüm kamu alım/satımlarından ve resmî ödemeden; pencere öncesi alımlar dahil, iadeler ve harici transfer bakiyesi hariç. Ham dolarlar küçük sanal kollarla eşit-risk kıyası değildir. İkinci piyasada iki maker alımı toplam 200 Down payı 22$’a almış; Up kazandı. Dolum yapmaması emir koymadığını kanıtlamaz. Bizim her pencereye kotasyon veren mekanizmamız onun piyasa seçimini henüz açıklamıyor.

## Karar ve sınanacak sonraki açık

M1’in basit bid fiyatlaması yeni iki uygun pencerede ana senaryoda kazanmadı. M2’nin dengelemeye geçebilmesi envanter eşiği kadar kalan nakde de bağlı. Bunlar aynı iki hipotezin karşı kanıtlarıdır; üçüncü bir strateji veya yeni seçilmiş eşik üretilmedi. Pasif rolü anlamaya ilerledik; Bosona’nın fiyat/iptal/boy/piyasa seçimini çözmüş değiliz.

Bir sonraki ayırıcı iş, emir kabul/iptal/öğrenme zamanlarını eldeki ölçüm kayıtlarıyla kalibre etmek ve aynı sabit kolları daha fazla kesintisiz günde sınamak. 250/750ms bir ölçüm sonucu değil. Kuyruk sahipliği L2’den çözülemez. Dengeleme için nakit ayırma gerekirse ayrı ileri protokol olur; bu tur uygulanmadı. On gün/100giriş/50ekleme ekonomik kabul eşiği açık; bu veriden güvenilir üstünlük aralığı çıkmaz.

## Tekrar üretim

```bash
cd /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_ws_expansion_20260921
P=/home/taygun/Masaüstü/KararAtlas/base1/bin/python3
OPENBLAS_NUM_THREADS=1 "$P" -B run.py repeat
```

`run.py fetch` yalnız eksik kamu önbelleğini tamamlar. `repeat` ağ kullanmadan iki tam koşu, para/zaman/tick/P0 karşı örnekleri, Ruff ve syntax kontrolünü yapar; `results/reproduction.json` SHA kanıtıdır. `protected.json` eski W/V kaynak ve sonuçlarını, `dependencies.json` yeniden kullanılan kaynakları, eski baseline aday/protokolü korur.

Ham veriler `markets/<başlangıç>/raw/`; URL, istek/alım zamanı, receipt/block ve ikinci RPC kontrolleri içerir. Canlı gzip dosyalarının yalnız sabit byte öneki kopyalandı. Açık Chainlink gzip kuyruğu tamamlanmış arşiv sayılmaz; seçilen karar zamanlarının sonrasına kadar geçerli satırlar hash ile sabitlendi. Kaynak: [resmî WS olay şeması](https://docs.polymarket.com/market-data/realtime-data).

Bu çalışma yeni shadow/LIVE/emir, ücretli servis veya çalışan recorder değişikliği yapmadı.
