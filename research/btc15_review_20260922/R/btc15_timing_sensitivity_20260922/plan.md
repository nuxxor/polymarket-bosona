# BTC15 karar bilgisi ve yürütme duyarlılığı — 22 Eylül 2026

Kullanıcı üç adımı onayladı. Ana planın çoklu-piyasa araştırması ve araştırma
kökünün ham akış tamlığı sonrası aşaması. Sadece bu dizin ve araştırma kök
planı yazılır; MAIN/eski aday/protokol/süreç/bütçe ve bütün eski çıktılar korunur.
Yeni emir, hesap bağlantısı, shadow, recorder veya ücretli servis yok.

1. [x] Gelecek bilgisini ayır: client kitap/tick/Chainlink yalnız received<=now;
   resmî sonuç ve sonradan gelen receipt/API yalnız ortam muhasebesi. Geç
   API düzeltmesi eski kapıyı değiştirmez; ayrı ex-post mutabakat etiketi.
2. [x] 8 mevcut atama: 20:45/21:00/21:15/21:30/21:45/22:00/22:15/23:00 UTC.
   Eski kopma ve kayıp akış dışlamaları kalır; sıfır değil null. Kör test denmez.
   23:00 için A önceden birincil, B yalnız aynı-hacim teyidi. Yeni sonuç
   gerekirse ayrı kamu cache; sonuç beklenirse PnL null.
3. [x] Aynı P0, M1 bid, M1 bid-1sent, M2 bid, M2 rezervli bid. 5 pay/10 net/
   15$ nakit/5$ en kötü kayıp; t30..839 saniyelik karar, t840 iptal. Eşik tarama
   yok. Rezervli M2 önceki opsiyon, bu tur yeni politika değil.
4. [x] Altı sabit yürütme profili: eski hızlı/yavaş; LTP varsayılan eşleşmesi
   500ms erken; erken-LTP+hızlı iptal/yavaş kabul; erken-LTP+yavaş iptal;
   yalnız geç öğrenme. 250/750ms eski değerler; 500ms önceki ölçüm karşı
   örneğinden yuvarlak stres, kalibre sınır değil. Kitap saatini LTP ile
   zorla kaydırma. Kuyruk ön/arka, aynı-ms işlem önce/yaşam-döngüsü önce;
   bunlar tüm olası saat/sıra yollarını kapsamaz, PnL alt/üst sınırı değildir.
5. [x] Eski motorla sıfır değişiklik eşdeğerliği; prefix/gelecek fiyat/sonuç
   mutasyonları; dolum-iptal yarışı ve geç bildirim; ortak risk/çokluk testleri.
   Gerçek kohort, lint/syntax, ağsız iki aynı-hashli koşu ve Türkçe rapor.

Başarı pozitif PnL bulmak değil, aynı kuralların hangi yürütme varsayımında
nasıl değiştiğini gösteren tekrar üretilebilir sonuç. Kalibre ekonomi null;
tam veri olmayan tüm atamalar için toplam null. Yeni 10 gün/100 piyasa
kabul eşiği bu küçük geriye dönük çalışmayla geçilmiş sayılmaz.

23:43 UTC adaptör kontrolü: yeni ham WS başlangıç tick alanı taşımıyor;
22:56:09.006 UTC alınmış Gamma market_start orderPriceMinTickSize=.01
karar-öncesi kanıt olarak ayrı tick okuyucusuna verildi. Kapanış metadatası
kullanılmıyor; ilk null koşunun nedeni initial_tick_diagnosis.json içinde.

23:49 UTC kanıtlanmış uygulama kusuru: 14 belirsiz yolun kabul defteri taze
ama spread 4–5 sent; kararın 3 sent filtresi kabul anında veri yokluğu
sanılmış. Eski kaynak/sonuçlar ayrı korunur. Yeni yerel uygulama kontrolü
taze ve geçerli gerçek defter, post-only/tick/fiyat sınırı kullanır; gönderim
kararı hâlâ 3 sent. P0 adaptörünün aynı kabul kontrolü de ayrılır; aday
karar kaynağı, 55 sent limiti ve protokol değişmez. Bu düzeltme sonuç
eşiği gevşetme değil; gözlenen defter ile karar filtresinin ayrılmasıdır.

Tamamlandı — 21 Eylül 23:58 UTC / 22 Eylül Türkiye. Sekiz atama; iki
kayıp/kopma penceresi null, beş ilk kapısı geçen ve bir sonradan API
mutabakatlı pencere. 6×96=576 koşullu yol; limit ihlali0. Gelecek fiyat/ref
silme testinde72gerçekbağlam aynı; P0/55sent ve eşikler korundu.
Karar spread filtresinin kabul verisi kontrolüne karışması düzeltildi:
yalnız14eski-belirsiz yol değişti,562yol/P0kontrolleri birebir aynı.
Pasif bid bütün24senaryoda negatif; ana toplam−2,69533524$. Dengeleme
ana−2,76801024$, rezervli−1,71414524$. M2yalnız kuyruk-önü/geç-öğrenme
profilinin iki sıra varyantında+1,70630443; en iyi pencere hariç−3,31655265$.
P0tekpencerede+0,485675$, diğer5'te geçerli filtreyle0; üstünlük kanıtı değil.
23kontrol, hedefliRuff/syntax;8hesapçıktısı ağsız iki koşuda aynı hash,
rapor da iki üretimde aynı. Kaynak/adayı/protokoller/eski çıktı ve süreçler
korundu; REST PID1714322 çalışıyor. Yeni emir/LIVE/shadow/recorder yok.
Kalibre ekonomi/uzun ileri kabul açık; bu üç sonlu çalışma tamamlandı.
