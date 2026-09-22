# BTC15 yürütme ölçümü ve dengeleme nakdi — 21 Eylül 22:23 UTC

Kullanıcı mevcut emir saatlerini incelemeyi ve ayrı nakit-ayırma kolunu onayladı.
Ana çoklu-piyasa araştırması / önceki WS genişletmesinin devamı. MAIN, aday,
eski araştırma çıktıları ve çalışan kayıtlar salt okunur. Bu dizin ve kendi
kök planı dışında yazma yok. Emir/LIVE/shadow, süreç/ayar/bütçe değişikliği yok.

Sonuç görmeden sabit yeni kohort: 21:45, 22:00, 22:15 UTC başlayan üç BTC15
sözleşmesi (1790027100/1790028000/1790028900). Sonu+120sn alım kesiti.
İlk ikisi kapanmış fakat analiz edilmemiştir; üçüncüsü bu plan anında sürer.
Bu temiz kör deney diye sunulmaz. İki saatlik mevcut pilot boyut/süre sınırında
biterse eksik pencere seçkiden silinmez, bilinmeyen olarak raporlanır.

1. [x] M4v2 donmuş12emir kayıtları: tüm kabul/dolmayanlar, istek/cevap,
   iptal son durum ve dolumu öğrenme eşlemesi. Yalnız SDK/bildirim gecikmesi;
   BTC5 stratejisi araştırılmaz. Exchange saatini yerel saatten icat etme,
   aynı-anda çalışan GET ile gerçekten sonraki GET'i ayır. Kaynak/hash koru.
2. [x] Mevcut M2 kontrolüne tek fark: tüm olası açık emir dolum köşelerinde
   C + abs(qUp-qDown) <= 15. Burada C ücret dahil harcanan nakittir; kalan
   net pay başına1$ kapanma rezervi. Doğrulanmış .07/exponent1 ücretinde
   p+.07p(1-p)<=1. Her kısmi dolum kombinasyonu da kapsanır. Bu derinlik,
   gerçekleşme, iptal veya yeni eklenmiş bir stop garantisi değildir.
   Fiyat, 10net hedge eşiği,5klip/15nakit/−5risk, t30..839/t840 değişmez.
3. [x] Rezervsiz M2 ve rezervli M2 aynı250/750ms ve kuyruk önü/arkasıyla;
   P0 donmuş aday aynı girdide kontrol. Ölçüm yeterli değilse yeni nokta
   gecikme uydurma. Önceki kayıp kesit yalnız hata/uygulama karşı örneği.
4. [x] Gerçek BTC15 defter/receipt/resmi sonuç kapısı, pencereler ayrı,
   PnL/risk/kaçan dolum/nakit yüzünden reddedilen hedge kıyası. Eksik/null
   sıfır kâr değildir. Ekonomik kabul ve özel yürütme kalibrasyonu ayrı.
5. [x] Anlamlı rezerv/kısmi dolum/iptal/telemetri karşı örnekleri, eski kol
   eşdeğerliği, syntax/Ruff, gerçek veri ve iki aynı-hashli yeniden üretim.

Rezerv eşiği kâra göre seçilmez; sözleşmenin bir paylık üst kapanma nakdinden
türetilir. Dengeleme kolunun kâr değil finansman uygulanabilirliği düzeltilir.

Tamamlanan sınırlı adım: RAPOR.md.624olay/309istek,12kabul/4dolum/8iptal;
SDK saatleri ölçüldü, eşleşme saati ve private gecikme bilinmiyor.
1.915receipt/1.908WS eşleşmesi: üçüncü pencerede zincirdeki bir işlem
WS'de yok; pencere ekonomik çıktısı null kaldı. İki geçerli pencerenin
750ms/arka koşullu toplamı eski−0,801005$, rezervli−0,90$. Rezervli
sekiz yolda bütçe güvencesi çalıştı ama taker hedge dolumu yok; risk
açılışını engelliyor. Bu yeni ekonomik üstünlük veya deployment adayı değil.
P0/M1 aynı; Fable180girişin102'sinin55¢üzerinde gerçekleştiği doğrulandı.
17kontrol, syntax/Ruff ve25aynı-hashli çıktı geçti. Uzun dönem ekonomik
kabul ve BTC15 özel yürütme kalibrasyonu açık; gerçek emir/ayar değişimi yok.
WS pilotu22:33:54UTC'de kendi depolama sınırında kapandı; üç kesit tamam.
