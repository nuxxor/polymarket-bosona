# M7: iki tam kayıt testi — 22 Eylül 2026

**Dar kapsama testi geçti.** A kaydı üç, B kaydı iki kez `1013` ile koptu.
Her kopuş ve yeni snapshot ile toparlanma arasında diğer kayıtta güncel
iki-token defteri vardı. Kopan kaydın bütün dosyasında bulunmayan **66 LTP
mesajı** diğer kayıtta korunmuştu. Bu 66 bağımsız ekonomik dolum demek değildir.

İki ayrı süreç, aynı Londra sunucusu, aynı önceden sabitlenmiş piyasa listesi,
değişmeyen M7-v3 kaynak: kişi başına 900 saniye, ortak süre 900,020 saniye.
Dört aktif BTC5m penceresi kapsandı. Finansal emir gönderilmedi.

| Ölçü | A | B |
|---|---:|---:|
| Zaman damgalı kayıt | 575.328 | 576.650 |
| Kamu bağlantı kopuşu | 3 | 2 |
| LTP mesajı | 5.568 | 5.605 |
| Yazma gecikmesi p99 | 1,89 ms | 2,20 ms |
| En büyük yazma gecikmesi | 9,78 ms | 8,80 ms |
| Kaynak zamanı geriye giden defter güncellemesi | 22 | 76 |

İki ham dosya ayrı saklandı. Ortak fingerprint çokluğu 5.528;
yalnız A'da 40, yalnız B'de 77 kayıt var. Zaman alanını çıkarmak bu farkı
değiştirmiyor. Bu farkların tamamı tespit edilmiş kopuşlara bağlanmadı;
**iki bağlantı, upstream olay eksiksizliğinin ispatı değil.** Aynı görünen
gerçek tekrarlar korunur; A+B hacmi veya PnL toplamı üretilmez.

100 ms aralıklı 9.001 nedensel kontrolün 8.972'sinde iki defter, 28'inde
yalnız bir defter günceldi. Bir başlangıç kontrolünde henüz snapshot yoktu.
Kopuş-toparlanma içindeki 28 kontrolün tamamında yedek günceldi. Son kopuş
öncesi mesajdan başlayan daha ihtiyatlı belirsizlik aralıklarında da yedek
bayatlığı görülmedi. Kopuşların toparlanması yaklaşık 0,55–0,76 saniye.
100 ms'den kısa ara durumlar bu örneklemede tamamen dışlanamaz.

Tazelik eşiği önceden 3.000 ms; kaynak saati için en çok 100 ms ileri
tolerans. Her kontrol yalnız o anda alınmış mesajları kullanır. Kopuşta
önbellek silinir; yeni snapshot gerekir. Kaynak zamanı gerileyince ilgili
defter yeni snapshot'a kadar geçersizdir. Bu son durum G okuyucusuna da
taşındı; eski fiyat yeni alınma saatiyle tazelenmiş sayılmaz.

Bu çalışma canlı veri seçici/failover servisi kurmadı. İki tam kayıt
toplamak ve geçmişte nedensel kapsama kontrolü yapmak, canlı emir kaynağını
otomatik değiştirmekle aynı şey değildir. Sunucu `1013` hatası çözülmüş
sayılmıyor; gerçek kendi dolumları ve kuyruk sırası hâlâ ayrı doğrulama ister.

Kaynak/ham dosya hashleri, çokluk, sıralama, snapshot, gizli alan ve zaman
kontrolleri geçti. Tekrar hesaplanan JSON sonuç aynı. Kontrol programındaki
ilk Python-int/JSON-string anahtar karşılaştırması normalleştirildi; bu bir
kapsama sonucu değişikliği değildir. Önceki finansal kaynak/state/bütçe
hashleri aynı; son hesap GET'inde açık emir sıfır, iki gözlemci sona ermiş.

Kanıt: `data/analysis/btc5m_m7_dual_20260922/`.

```bash
"/home/taygun/Masaüstü/KararAtlas/base1/bin/python3" "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_m7_dual_20260922/check.py"
```
