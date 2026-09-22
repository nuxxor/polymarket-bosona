# G1 ilk pilot — gerçekleşme ve kârın kaynağı

09:27–09:57 UTC /12:27–12:57 TR, altı BTC5m piyasası. Bu rapor ilk
30dk pilotuna aittir; sonraki süresiz koşu ile birleştirilmez.

Sonuç **+$9,206315**, dört artı/iki eksi pencere. Rebate ve sabit gider hariç.
İki bağımsız özel hesap akışı, son mutabık state ile **63/63 parent emrin
miktarını** doğruladı: 36 dolmuş emir, 40 ayrı trade×parent gerçekleşmesi,
179,986086 pay. Aynı gerçekleşmenin MATCHED/MINED/CONFIRMED mesajları
üç yeni işlem sayılmadı. Botun 37 dolum artışı gözlemi ayrı bir sayımdır;
bir yoklama birden fazla gerçek parçayı birlikte öğrenebilir.

40 gerçekleşmenin hepsinde kendi order hash'imiz maker_orders içinde,
trader_side=MAKER; gönderimler post-only. Bu, pasif yürütmenin somut
kanıtıdır. Kuyruk sırası, Bosona'nın aynı emir politikasına sahip olması
ve kalıcı kârlılık bundan çıkmaz. Maker_orders alanının anlamı için
[resmî özel akış belgesi](https://docs.polymarket.com/trading/realtime-order-updates).

Başarılı POST medyanı43,57ms. Botun dolumu öğrenmesi, iki özel kayıttan
ilk alınan eşdeğer miktar kanıtına göre medyan132,28ms sonra; aralık
−46,72ms /+785,95ms. Aynı makinenin monotonic saati kullanılır.
Negatif değer, SDK yoklamasının bu iki WS mesajından önce öğrenebildiğini
gösterir. Bu sayılar emir kuyruğunda bekleme veya exchange gecikmesi değildir.

## Son envanterin ödeme aralığı

| TR başlangıç | Gerçek sonuç | Gerçek PnL | İki sonuçtan kötüsündeki PnL |
|---|---|---:|---:|
|12:30|Up|+5,15|+0,15|
|12:35|Up|+3,10|−1,90|
|12:40|Up|+0,75|+0,75|
|12:45|Down|−0,198115|−0,202400|
|12:50|Up|−2,345571|−2,345571|
|12:55|Up|+2,75|−2,25|
|Toplam||+9,206315|−5,797970|

Taban=min(sonUp,sonDown)−toplamMaliyet. Gerçek ödeme bu tabanın15,004285
üzerinde; bunun15doları üç pencerede kazanan tarafta kalan5'er fazla paydan.
Bu bir **sabit son envanter ödeme ayrımıdır**; farklı sonuçta botun aynı
emirleri vereceği varsayılmaz. FIFO çift getirisi veya nedensel politika
karşılaştırması değildir. Dolayısıyla güzel başlangıcın tamamını yön
bağımsız çift kârı diye yorumlamamalıyız. Altı pencerenin beşinde Up çıktı;
yön seçme avantajı veya şans payı bu örneklemden ayrıştırılamaz.

## Veri sınırı ve sonraki iş

Her özel kayıtçıda altı ayrıştırılmamış mesaj, kamu tarafında A4/B3 bağlantı
kopuşu var. Dolum miktarları iki akışta ve mutabakatta tam uzlaşsa da tüm
olaylar eksiksiz kaydedildi denemez. Önceki kayıt bu reddin ham içeriğini
saklamadığı için türü henüz bilinmiyor. Ayrı salt-okunur tanısal kayıt ve
sabit güvenli hata sınıfları eklendi; serbest mesaj/kimlik bilgisi yazılmaz.

Kayıtçı kullanılabilirliği ile olay tamlığı ayrı raporlanır. Birincide
süreç, güncel yazma, PONG, kuyruk taşması ve disk rezervi izlenir. İkincide
reddedilen mesaj ve gap sayıları saklanır. Bunlar sıfır diye gizlenmez.
G1 politikası ve pay büyüklüğü bu sonuç görülerek değiştirilmedi.

Tekrar hesap: `lanes/g_continuous/validation/g1_first_pilot/analyze.py`.
İki özel kaset, manifest, kaynak SHA'ları ve `analysis.json` aynı dizinde.
Decimal/miktar/çokluk/rol/gönderim ve saat kontrolleri ile hedefli Ruff geçti.
