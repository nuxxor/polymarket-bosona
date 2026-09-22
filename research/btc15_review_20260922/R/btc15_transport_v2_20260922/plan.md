# BTC15 yürütme saatlerini ayırma — 22 Eylül 2026

Kullanıcı odak BTC15, G1 yalnız teknolojik referans diye düzeltti.
Ana planın çoklu piyasa/gerçekleşme doğrulama aşaması; G1 stratejisi
veya BTC5 kârı aktarılmaz. Yalnız bu alan ve araştırma kök planı yazılır.
P0, eski M1/M2 karar/risk kuralları, ana repo, mevcut recorder/Londra süreçleri
ve bütçeleri korunur. Yeni emir, LIVE, shadow veya ücretli hizmet yok.

Sonuçlar hesaplanmadan sabit kapsam:
1. [x] Aynı saatli gerçek SDK/özel-kamu kayıtlarından teknik süreleri ayır:
   etkinleşme için gözlemsel üst sınır, POST yanıtı, iptal etkinleşmesi için
   üst sınır, hesapta kapanış öğrenilmesi, dolum öğrenilmesi. Borsa iç zamanı
   bilinmiyor. Yalnız maker kayıtları; BTC15 kalibrasyonu ilan edilmez.
2. [x] Önceki motorun ayrı kopyasına bu saatleri ve POST yanıtı bekleyen
   emirde iptal ertelemeyi ekle. Nakit rezervi teyit gelmeden kalkmaz;
   kısmi/geç bildirimler kümülatif miktarla bir kez işlenir. Kararlar t30..840,
   5 pay/10 net/15 dolar nakit/5 dolar en kötü kayıp aynen korunur.
3. [x] Eski hızlı/yavaş profil eşdeğerliği + önceden sabit p50/p95/maksimum
   teknik stres profilleri. Nicelikler yukarı tam ms yuvarlanır; ayrı
   marjinal nicelikler ortak bir gözlenmiş gecikme dağılımı sayılmaz.
   Kuyruk ön/arka ve aynı-ms iki olay sırası; M1 bid, bid−1sent, M2,
   rezervli M2. Parametre/PnL taraması veya G1 politikası karşılaştırması yok.
4. [x] Eski sekiz BTC15 ataması; aynı iki eksik piyasa null, altı uygun
   piyasada bütün yollar. Yeni kör örneklem değil. P0 eski donmuş sonuçla
   karşılaştırma referansı; ekonomik PnL null. Nihai sonuç karar girdisi değil.
5. [x] POST yanıtından önce dolum ve iptal isteği, gecikmiş iptal teyidi,
   miktar/kasa/risk, geleceği silme, eski eşdeğerlik karşı örnekleri;
   gerçek veri koşusu, Ruff/syntax, ağsız aynı-hash tekrar ve Türkçe rapor.

Başarı kazancı yükseltmek değil; uygulama zamanı varsayımının etkisini
ayrı ve tekrarlanabilir ölçmek. Tam kuyruk kalibrasyonu ve ileri 10 gün/
100 piyasa ekonomik kabul bu küçük teknik denetimle tamamlanmış sayılmaz.

İlk sonlu sonuçtan sonra tanısal karşı deneme — 10:44 UTC:
P95/arka-kuyrukta pasif bid +3,70; bid−1sent +3,6968 ve en iyi piyasa
hariç +1,9968 göründü. Bu yeni başarı ön kaydı değildir. İki pasif kolun
üç yeni profilinin TAMAMINDA önceki −500ms LTP stresi ve eski
iptal_etkisi+kabul_gecikmesi teyit varsayımı ayrı karşılaştırılacak.
Eşik araması yok; amaç saat duyarlılığını ve uzun teyidin katkısını ayırmak.
Bu tanı ana protokolü/480yolu ve eski karşılaştırmaları değiştirmez.

Tamamlandı — 10:55 UTC. Teknik saatler ayrıldı; BTC15 karar dalı aynen
korundu. 480 ana + 288 tanısal yol, limit ihlali0; 192 eski yol birebir.
Bid−1sent p95/arka +3,6968, −500ms işlem stresinde −3,35; yalnız eski
iptal teyidi varsayımıyla −3,00. Pozitif hücre yeni aday yapılmadı.
17 kontrol, hedefli Ruff/syntax; dokuz hesap çıktısı ağsız aynı SHA256.
RAPOR.md ve results/ teslim kanıtı. Londra/canlı/ana kaynak/adayı/bütçe
değişmedi. Sayısal süreler farklı süre/ağ yolundan teknik stres örnekleri;
BTC15 kuyruk kalibrasyonu ve çok günlük ekonomik kabul hâlâ açık.
