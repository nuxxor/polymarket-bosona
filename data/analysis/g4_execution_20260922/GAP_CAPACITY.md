# G4: fiyat farkı, ek kapasite ve PRO/Opus değerlendirmesi

22 Eylül 2026. Mevcut tarihsel veri üzerinde tanısal çalışma; temiz dış
örneklem, uygulanabilir bağımsız alpha veya Bosona'nın keşfedilmiş kuralı değil.
G4, operatör isteğiyle 17:40:28 UTC'de normal durdu. G5 ayrı bir canlı
deneme olarak başlatılmadı.

## Fiyat farkı: yön bilgisi var; zamandan bağımsız kesinlik yok

13–20 Eylül arasındaki 2.286 takvim slotunda, sabit pencere yaşlarında
alınmış fiyatlara baktık. 1.671 piyasada 13.302 spot/referans gözlemi var.
Eksik slotlar sıfır işlem/kayıp sayılmadı. Bosona dolumu olması koşulu yok.
Başlangıç referansı, o anda alınmış resmi TWAP60 raporundan; market
metadata'sıyla çelişen referanslar mevcut yardımcı tarafından eleniyor.
Referansın ve fiyatın yerel alınma zamanı kararın sonrasında olamaz.

Ekrandaki fark $166,07, yani yaklaşık 19,25 baz puan. Ekranın “current price”
alanını otomatik spot saymadık: alınmış Chainlink spot ve resmi TWAP60
farklarını ayrı hesapladık. Aşağıdaki tablo **TWAP60** içindir; eşik 20 bps
önceden sabit tanısal kova, keşfedilmiş optimum değildir.

| Kalan süre | Fark ≥20 bps: gözlem | O sırada önde olan tarafın kazanması |
|---|---:|---:|
| 240 sn | 7 | 6/7 |
| 180 sn | 33 | 29/33 |
| 120 sn | 60 | 57/60 |
| 90 sn | 71 | 70/71 |
| 60 sn | 90 | 90/90 |

Her satır farklı koşullu örneklem; aralarındaki fark süreyi değiştirmenin
nedensel etkisi değildir. Aynı piyasaların farklı saatleri bağımsız örnek
sayılmaz. 90/90 gelecekte hiç dönüş olmayacağı anlamına gelmez.

120 sn kalmışken fark ≥20 bps grubunda **57/60 yön isabeti** var. Fakat
beş pay için arşivde derinlik/maliyet ölçülebilen **32** olayda, 250 ms
sonraki alış maliyeti ve arşiv ücret modeliyle toplam **−$7,404** çıkıyor.
Spot ölçümünde aynı saat/kovada 70/71 yön isabeti; fiyatlanabilen 27 olay
**−$2,367**. Bunlar aynı kapsamda olmayan örneklemler; 57/60'ı 32 işlemin
kazanma oranı gibi kullanmıyoruz. Pozitif çıkan diğer kovalar da raporda
korunur; örneğin TWAP, 90 sn ve ≥20 bps: fiyatlanabilen yalnız 8 olay,
+$1,153. Bunlardan en iyisini seçip canlı eşik yapılmadı.

Mevcut kitap arşivi iki taraflı tazelik/derinlik koşulları taşıyor. Özellikle
sonuca çok yaklaşmış tek taraflı kitaplarda fiyat kapsamı hızla düşüyor;
eksikler rastgele değil. Erken saatlerde alış maliyeti yok. 250 ms ölçülmüş
emir gecikmesi değil, koşullu kâğıt yürütme senaryosu. Spot oynaklığıyla
`|spot-ref|/(sigma*sqrt(kalan))` ayrıca kaydedildi; kalibre kazanma olasılığı
veya resmi terminal TWAP'ın yeniden üretimi diye sunulmadı.

Sonuç: fark hipotezini koruyoruz, fakat G5'e “fark büyükse al/kapat” kuralı
koymuyoruz. Yüksek isabetin yanı sıra ödenen fiyatın da avantaj bırakması
gerekir. [Resmi TWAP zaman ve hesaplama sınırları](https://docs.polymarket.com/market-data/chainlink-twap).

## PRO'nun marjinal ikinci-parent testi

İlk altı G4 penceresi önceden dondurulmuş 16:45–17:15 UTC kesitidir.
SDK'de dolumun **öğrenildiği sıraya** göre işlem öncesi envanter kuruldu;
nihai miktar geçmiş karara taşınmadı. 889 in-process envanter kaydı bu
yeniden kurmayla eşleşiyor. İlk kez net5'te engellenip net10'da izin alan
POST denemesini aldık; reddedilen ve dolmayan denemeleri de koruduk.

| UTC pencere | İlk ek deneme | Gerçek dolum | Ek tokenların terminal katkısı |
|---|---|---:|---:|
| 16:45 | Down 5 @0,69 | 5 | −$3,45 |
| 16:50 | Up 5 @0,66 | 0 | $0 |
| 16:55 | Down 5 @0,27 | 0 | $0 |
| 17:00 | Up 5 @0,29; red | 0 | $0 |
| 17:05 | Up 5 @0,28 | 0 | $0 |
| 17:10 | Up 5 @0,62 | 5 | −$3,10 |

Toplam **−$6,55**; altı fırsat, beş kabul, iki dolmuş parent, bir UTC gün.
Sonraki yenilemeleri veya gelecekteki G4 işlemlerini alternatif envantere
aynen uygulamadık. Bu **net5 botu $6,55 daha çok kazanırdı** demek değildir.
İlk denemelerin çok erken olması Opus'un faz uyarısıyla uyumlu; altı
gözlemden genelleme yapılmaz. +1/+5 saniye tam-miktar yürütülebilir satış
derinliği bu dar çıkarımda yok; mid veya touch onun yerine konmadı.

889 canlı teklif snapshot'ında `[x−O_D,x+O_U]` uçları **[−10,+10]** içinde.
Gerçek G5/G4 miktar fonksiyonu ayrıca 1.152 uygun net/pending durumunda
sınandı. Karşı bekleyen emir gerçekleşmiş hedge olarak düşülmüyor.
Snapshot denetimi kesintisiz her nanosaniyenin kanıtı değildir; POST
öncesi kilitli aynı-taraf rezerv ve kod kontrolleri tamamlayıcı kanıttır.

## Opus: doğrulanan hata ve sınırı

Eski t180 `denge_koru`, G4'ün t240'a kadar izin verdiği ağır taraf teklifini
iptal ediyor. Gerçek quote/maintenance/reader döngüleri, sahte borsayla
178→242 saniye sınamasında **60 POST, 59 bakım iptali** üretti. Aynı
test G5 paketinin her iki kolunda **2 POST, sıfır bakım iptali** üretti;
t240 yeni risk ve t290 azaltım kesmeleri korundu. A–F yolu değişmedi.

Gerçek G4 kaydında 17:38:10 UTC'ye kadar dört `DENGE_SINIRI` olayı var;
ikisi 17:30 penceresinin t235/t236 anlarında ardışık. Bir diğer olay
t15'te tam dolmuş ağır tarafta; dört olayın hepsi aynı geç döngü değildir.
Canlıda 60 hak tüketildiği iddia edilmiyor. Simülasyondaki 60/59 bunun
mümkün olduğunu gösteriyor.

Opus'un “bid altındaki alış ancak önce fiyat aleyhe giderse dolar” cümlesi
katı bir yürütme yasası değildir: agresif satış bekleyen seviyeye ulaşabilir.
Belirleyici kanıt gerçekleşmiş markout ve emir yaşam döngüsüdür. Önceki
G4 ölçümünde yukarı yenilenen teklifler daha kötü markout aldı; bu gözlem
de “aynı emri tutsaydık kesin dolardı” karşıolgusunu doğrulamıyor.

G5 bu nedenle kapasiteyi/çıkışı/zamanı birlikte değiştirmiyor. Ortak hata
düzeltmesi üzerine, yalnız yeni-risk teklifini yukarı kovalamama kolunu
düzeltilmiş G4 kontrolüyle karşılaştırmak üzere **parkta** hazırlandı.
Tamamlama ve aşağı yeniden fiyatlama korunur. G5'in daha iyi veya Bosona'yla
aynı olduğu henüz gösterilmiş değil.

## Tekrar üretim

Repo kökünden `python3 data/analysis/g4_execution_20260922/gap.py` ve
`python3 data/analysis/g4_execution_20260922/capacity.py`.
Gap mevcut yerel arşiv yardımcılarını kullanır; özel `capture.jsonl.gz` ve
runtime dosyaları GitHub'a yayımlanmaz. `gap_results.json`,
`gap_protocol.json` ve `capacity_summary.json` paylaşılabilir özetlerdir.
Tarihsel arşiv ve özel kesit olmadan bu iki komutun ham yeniden üretimi
mümkün değildir; G5 mühendislik testleri ağsız bağımsız çalışır.
