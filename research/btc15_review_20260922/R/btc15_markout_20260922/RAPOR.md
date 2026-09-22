# BTC15 maker fiyat avantajı — üç adımın sonucu

**Karar: Bosona’ya ait sağlam, kopyalanabilir kısa vadeli fiyat avantajı kanıtlanmadı.** Diğer makerlara göre küçük bir fark var; tek piyasa ve az sayıda zaman eşleşmesi taşıyor. Sınanan iki önbilgi kuralı bunu güvenilir biçimde açıklamıyor. Mevcut aday korunmalı; bu çalışmadan yeni ekonomik shadow adayı çıkmıyor.

## Kapsam ve ölçüm

21 Eylül 2026’nın önceden atanmış sekiz BTC15 penceresi: altısı kullanılabilir. 5,240 zincir-doğrulanmış maker BUY parçası; Bosona 22 dolum / 14 parent / 5 işlemli piyasa. Bir uygun piyasada Bosona dolumu yok. Tek gün ve görülmüş veri; kör test değil.

| Başlangıç UTC | Veri durumu | Tüm maker BUY | Bosona dolum / parent |
|---|---|---:|---:|
| 20:45 | Uygun | 1218 | 9 / 6 |
| 21:00 | Eksik; dışarıda | — | — / — |
| 21:15 | Uygun | 941 | 0 / 0 |
| 21:30 | Uygun | 757 | 2 / 1 |
| 21:45 | Uygun | 426 | 2 / 1 |
| 22:00 | Uygun | 1339 | 6 / 4 |
| 22:15 | Eksik; dışarıda | — | — / — |
| 23:00 | Sonradan uzlaştırıldı | 559 | 3 / 2 |

21:00 bağlantı boşluğu ve 22:15 eksik WS işlemi sıfır sonuca çevrilmedi. 23:00’ın ilk başarısız API kapısı değiştirilmedi; sonraki tam uzlaşma ayrı etiket. Sözleşmeler Gamma başlangıç/bitiş, token kimliği ve Chainlink TWAP60 kuralıyla doğrulandı.

**Markout = gelecekteki orta fiyat − gerçek maker dolum fiyatı**, sent/pay. Ana saat kamu dolum mesajının ilk alınması; gerçek eşleşme veya emir yerleştirme saati değil. Defter sonradan gelen örnekle doldurulmaz: hedef saate kadar alınan son durum kullanılır. İki token hazır/taze (≤3sn), bid<ask ve tamamlayıcı miktarlar eşit olmalı. Eksik/boş defter ve kapanış sonrası ufuklar null. Orta fiyattan satış yapılabildiği, kuyrukta dolum alınabildiği veya rebate kazanıldığı varsayılmıyor.

Ana ağırlık: parent içindeki dolumlar eşit, piyasa içindeki parentlar eşit, piyasalar eşit. Dolum parçalanması sahte örnek büyüklüğü yaratmaz. Pay ağırlığı ayrıca verilir. Piyasa çıkarma aralığı güven aralığı değildir; aynı gün içi bağımlılık sürer.

## 1. Dolumdan sonra fiyat ne yapıyor?

| Ufuk | Bosona markout | Pay ağırlıklı | Mesaj anındaki fark | Sonraki fiyat hareketi |
|---|---:|---:|---:|---:|
| 1 sn | +0.678 | +1.445 | +0.942 | -0.264 |
| 5 sn | -0.225 | -0.086 | +0.942 | -1.167 |
| 10 sn | -0.417 | -0.535 | +0.942 | -1.358 |

Bosona’nın 22 dolumunda üç ufuk da ölçülebildi. Mesaj ulaştığında orta fiyatın altında bir dolum fiyatı görülüyor; sonraki hareket bu farkı siliyor. Bu, tek başına gelecekteki yönü iyi tahmin ettiğini desteklemiyor. Diğer makerların ham ortalaması farklı koşulları karıştırdığı için asıl karşılaştırma aşağıdaki eşleştirilmiş gruptur.

## 2. Benzer koşullarda başka makerlarla karşılaştırma

Ana kural sonuç hesaplanmadan sabitlendi: aynı piyasa/token, ≤2¢ fiyat, ≤30sn zaman, farklı transaction. Normalize zaman+fiyat uzaklığıyla tek en yakın dolum; sonuç/gelecek fiyatı kullanılmaz. Kontrol tekrar seçilebilir ve eksik sonucu varsa değiştirilmez. 22/22 dolum eşleşti; 17 kontrol parentı / 11 cüzdan; en fazla iki kez parent kullanımı. Ortanca fiyat farkı 0¢, zaman farkı 442ms. Baştan sabit 5¢/60sn kontrolü aynı çiftleri seçti.

| Saat varsayımı | 1sn fark | 5sn fark | 10sn fark | 10sn pay ağırlıklı fark |
|---|---:|---:|---:|---:|
| Mesaj alındı | -0.017 | +1.647 | +1.072 | +0.292 |
| Alınma−500ms duyarlılığı | +0.033 | +1.806 | +0.833 | +0.391 |

10sn ana farkın +0.375 senti mesaj anındaki fiyat farkı, +0.697 senti sonraki göreli harekettir. Tek parent çıkarıldığında fark -1.128…+2.472 sent aralığına geliyor. 500ms kaydırma eşleşmenin gerçek saati için doğrulanmış sınır değil; saat duyarlılığıdır.

| Piyasa UTC | Bosona 10sn | Kontrole göre 10sn fark | 500ms kaydırılmış fark |
|---|---:|---:|---:|---:|
| 20:45 | -3.083 | +0.361 | -0.333 |
| 21:30 | +1.000 | +0.000 | +0.000 |
| 21:45 | +0.500 | +0.000 | +0.000 |
| 22:00 | +1.500 | +5.000 | +5.000 |
| 23:00 | -2.000 | +0.000 | -0.500 |

22:00 piyasası ana göreli fark toplamının yaklaşık %93’ünü taşıyor. Bu piyasa çıkarılınca fark +0,090¢; 500ms saat duyarlılığında −0,208¢. Aynı agresör eşleşmesindeki 13 Bosona dolumu için diğer makerlarla fark +0,167¢; gelecek fiyat hareketi farkı tam 0. Aynı token ve aynı saat bunu zaten gerektirir; bu kontrol yön tahmini kanıtı değil, fiyat farkı/kimlik denetimidir.

**Karşı örnekler (sonuç görüldükten sonra seçilmiş açıklayıcı örnekler):**

| Piyasa / yaş | Token ve resmî sonuç | Bosona fiyat / 10sn | Kontrol yaş / fiyat / 10sn | Fark |
|---|---|---:|---:|---:|
| 22:00 / 823.989sn | Down / kaybetti | 43.00¢ / -0.500¢ | 832.730sn / 44.00¢ / -38.500¢ | +38.000¢ |
| 22:00 / 741.659sn | Up / kazandı | 22.00¢ / +0.500¢ | 750.300sn / 22.00¢ / +16.500¢ | -16.000¢ |
| 20:45 / 660.438sn | Down / kaybetti | 30.00¢ / -7.500¢ | 660.933sn / 30.00¢ / -7.500¢ | +0.000¢ |
| 23:00 / 305.785sn | Down / kaybetti | 16.00¢ / -3.500¢ | 305.754sn / 16.00¢ / -3.500¢ | +0.000¢ |

En büyük +38¢ göreli fark, Bosona’nın para kazandığı bir alım değil: kendi 10sn markoutu −0,5¢ ve token sonunda kaybediyor. 8,741sn sonraki kontrol çok daha sert düşüşü yaşıyor. −16¢ örneğinde ise Bosona’nın tokenı sonunda kazanıyor. Bunlar kısa ufuk farkını resmî sonuç kârıyla karıştırmamak ve zaman eşleştirmesinin hızlı hareketlerde sınırlı olduğunu görmek için önemli. Bütün çiftler matches.json’da.

## 3. En fazla iki önbilgi açıklaması

H1: önceki 5sn’de token orta fiyatı yükseliyorsa o yönde pasif alışa izin ver. H2: önceki 5sn kamu agresör hacmi token lehine net pozitifse izin ver. Eşik her ikisinde sıfır; nötr ayrı. İkisi birleştirilmedi, eşik taranmadı. Bilgi son noktası dolum mesajından 1sn ve ayrı duyarlılıkta 5sn öncesi. Bu, kendi alınma saatimiz açısından nedensel; Bosona’nın emir gönderiminden önce bilindiğini kanıtlamaz.

| Hipotez / bilgi koruması | Bosona + / nötr / − | Pozitif grupta Bosona 10sn markout | Dolumdan bağımsız pozitif sinyalde 10sn fiyat hareketi |
|---|---:|---:|---:|
| H1 / 1sn | 9 / 2 / 11 | -0.917 | +0.235 |
| H1 / 5sn | 12 / 5 / 5 | -1.167 | +0.018 |
| H2 / 1sn | 7 / 0 / 15 | -0.583 | -0.031 |
| H2 / 5sn | 7 / 0 / 15 | -1.250 | -0.029 |

**H1: zayıf ve zamana duyarlı ipucu.** Aktörsüz ızgarada +0,235¢ hareket 5sn korumayla +0,018¢’e düşüyor; ikinci durumda tek piyasa çıkarma aralığı −0,075…+0,183¢. Bosona pozitif H1 dolumlarında da negatif markout taşıyor. Bir kayıp karşı örnek: 20:45 piyasası Down, yaş 696,354sn, fiyat 26¢; önceki fiyat hareketi +1¢ ve akış +6,68 pay iken sonraki markout −4,5¢. Basit fiyat devamlılığı Bosona’nın avantajını açıklamış sayılmıyor.

**H2: bu yöndeki açıklama desteklenmedi.** 22 dolumun 15’i aleyhte akış sonrasında geliyor. Aktörsüz pozitif akışta 10sn hareket iki korumada da yaklaşık −0,03¢. 22:00 piyasası Up, yaş 842,393sn: önceki akış −529,60 pay olmasına rağmen 94¢ dolumun 10sn markoutu +4,5¢. Ters işaretli yeni strateji bu sonucu görünce üretilmedi.

H1 lehine kalan gözlem de saklandı: aynı piyasa içindeki pozitif eksi negatif özellik gruplarında sonraki fiyat hareketi farkı 1sn korumada +3,375¢ (yalnız iki ortak piyasa), 5sn korumada +1,000¢ (tek ortak piyasa). Bu alt gruplar ve toplam markout farklı ölçülerdir; tek başına kârlı seçim anlamına gelmez. Eşleştirilmiş kontrole göre pozitif H1 görülme farkı eşit piyasa ağırlığıyla yalnız −1,67 / +1,67 yüzde puan. H2 için aynı piyasa hareket farkı iki korumada da negatif. Aynı koşuldaki diğer makerların da taşıdığı özellikler Bosona’ya özgü bir kuralı tanımlamıyor.

Seçici `research.py:features()` yalnız defter/kamu akışından H1/H2 işaretini üretir; pozitif işaret ilgili hipotezin izin koşuludur. Her saniye iki token için 10.548 sabit bağlam çalıştırıldı; tamamlayıcı tokenlar bağımsız iki gözlem değildir, ufuklar da örtüşür. Eksik defter/özellik null olarak durur. Bu ızgara kotasyon veya dolum varsaymaz; markout/PnL backtest’i değildir. Olumlu/olumsuz/nötr, aynı özellikli çiftler, ortak piyasadaki işaret farkları ve iki saat kaydırması bütün JSON çıktılarında saklandı.

**Yanlışlanma/kabul:** H1 için daha eski bilgiyle etkinin kaybolması, H2 için pozitif akışın daha iyi sonraki hareket vermemesi bu kesitte karşı kanıttır. Bunlar Bosona’nın bütün stratejisini çürütmez. İlerlemek için değişmeyen kuralla farklı günlerde, parent/piyasa kümeleriyle aynı yönün korunması ve kendi uygulanabilir dolum modelinde maliyet sonrası sonuç gerekir. Bu koşullar karşılanmadı; iki hipotezden hiçbiri mevcut adayın yerini almıyor.

## Kontroller, düzeltme ve sınırlar

Rol, ücret imzasından değil OrdersMatched/OrderFilled zincir ilişkisinden geliyor. Kontrol havuzunda 34 maker parçasında toplam 0.80805$ ücret var (9 cüzdan); Bosona’da ve seçilen kontrol dolumlarında sıfır. İlk kontrol testindeki “bütün maker ücretleri sıfırdır” varsayımı bu gerçek karşı örnekle kaldırıldı; sınıflandırıcı veya veri değiştirilmedi. Bu yüzden salt ücretle genel rol çıkarmak güvenli değil. [Resmî V2 kaynak kodu maker ücretini ayrı parametre olarak destekliyor.](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/mixins/Trading.sol)

Kamu defter ve işlem olaylarının alanları [resmî akış belgesinde](https://docs.polymarket.com/market-data/realtime-data) ayrı tanımlı. Fiziksel eşleşme saati, emir yerleştirme/iptalleri, dolmayan emirler, gerçek kuyruk yeri ve diğer makerların portföy riski bilinmiyor. Aynı fiyat/zaman bu gizli koşulları eşitlemez. Bu çalışma yalnız dolmuş emirler üzerindeki ilişkiyi ölçer, hangi emirlerin dolacağını açıklamaz.

Kimlik/fiyat/rol, parent ağırlığı, eksik ve kapanış sansürü, sonuçtan bağımsız eşleştirme, public akış çokluğu ve 48 gerçek bağlamda geleceği silme kontrolleri `verification.json` içinde. Ham kaynaklar delivery manifestleriyle salt okunur doğrulanır; ağ bağlantısı analiz sırasında engellenir. Aynı hashli tekrar `reproducibility.json`, çıktı manifesti `delivery_manifest.json` içindedir.

## Tekrar çalıştırma

```bash
P=/home/taygun/Masaüstü/KararAtlas/base1/bin/python3
D=/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_markout_20260922
$P "$D/research.py" all
$P "$D/check.py"
$P "$D/report.py"
$P -m ruff check "$D/research.py" "$D/check.py" "$D/report.py"
```

Aday, eşikler, eski protokoller, ana repo, Londra ve çalışan kaydediciler değiştirilmedi. Araştırma hesabı tamamlandı; ekonomik avantajın doğrulanması açık.
