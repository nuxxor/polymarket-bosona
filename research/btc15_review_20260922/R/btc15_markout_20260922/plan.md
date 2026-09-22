# BTC15 dolum sonrası fiyat avantajı — 22 Eylül 2026

Kapsam: kullanıcının onayladığı üç adım sırayla tamamlanır. Ana planın kamu
emir kimliği/veri tamlığı ve ekonomik avantajı ayırma ölçütleri uygulanır.
BTC5 stratejisi, mevcut aday/protokol ve çalışan süreçler değişmez. Önceki
sekiz atanmış WS piyasası kullanılır; yeni emir, shadow veya kayıt servisi yok.

## Sonuç hesaplanmadan sabit tasarım

- Sekiz atama, önceki kapıyla beş uygun ve daha sonra tam uzlaştırılmış bir
  piyasa. İki eksik piyasa kapsam tablosunda kalır. Tek gün, görülmüş veri;
  yeni kör deney veya dış kayıt sisteminde ön kayıt değildir.
- Zincirin gerçek maker BUY parçaları, `(transaction, logIndex)` kimliği;
  SELL normalizasyonuyla sahte BUY üretilmez. Parent `(owner, orderHash)`.
- Ana saat ilk kamu mesajının alınmasıdır. 1/5/10 saniye sonraki as-of orta
  fiyat eksi gerçek dolum fiyatı (sent/pay); bunlar uygulanabilir satış/PnL
  değildir. Mesaj anındaki fiyat farkı ve sonraki hareket ayrı hesaplanır.
  Alınma−500 ms yalnız saat duyarlılığıdır; eşleşme saatinin sınırı değildir.
- İki token defteri hazır, kaynak/alınma yaşı ≤3sn, bid<ask, tamamlayıcı
  defterler birebir. Spread için sonuç seçen üst sınır yok. Kapanış sonrası
  ufuk sansürlenir; eksik gözlem sıfıra veya resmî ödemeye dönüştürülmez.
- Ana kontrol: başka sahibin maker BUY dolumu; aynı piyasa/token, fiyat
  farkı ≤2¢, alınma zamanı farkı ≤30sn, farklı transaction. Normalize fiyat
  ve zaman uzaklığı toplamıyla en yakın kayıt; eşitlikte zaman/tx/log sırası.
  İade ile eşleştirme: kontrol tekrar kullanılabilir, tekrar sayısı gösterilir.
  Kontrol seçimi markout/sonuca bakmaz, eksik sonucu olan kontrol değiştirilmez.
  Önceden sabit tek duyarlılık ≤5¢/60sn; iyi çıkan kaliper seçilmez.
  Aynı agresör eşleşmesindeki diğer makerlar ayrı eşzamanlı tanısal kontrol.
- Dolum ortalaması yanında pay ağırlığı, parent ortalaması ve eşit piyasa
  ortalaması; temel karşılaştırma parent içinde eşit dolum, piyasa içinde eşit
  parent, sonra eşit piyasa. Eşitlikler, tekrar kullanılan kontroller ve
  piyasa çıkarma aralığı raporlanır. Tek gün/az piyasa ile anlamlılık iddiası yok.
- Kazanan/kaybeden token grupları ve en iyi/en kötü parent örnekleri birlikte;
  resmî sonuç yalnız sonradan tanısal etiket, eşleştirme/seçici girdisi değil.

## En fazla iki açıklama, sonuç öncesi sabit

H1: kısa fiyat devamlılığı. Dolum mesajından 1sn önce bilinen token orta
fiyatı, bunun 5sn öncesine göre artmışsa (+), azalmışsa (−), aynıysa nötr.
H2: yönlü kamu akışı. Aynı 5sn aralığında token lehine normalize edilmiş
agresör hacmi eksi aleyhte hacim; pozitif/negatif/nötr. Aktör kimliği ve
zincirden sonradan öğrenilen veriler seçici girdisi değildir; ham public
LTP'nin token/BUY/SELL/size alanı kullanılır. Tekrar mesaj tekilleştirmesi
yalnız tek aktif eşleşme olduğu zincirle doğrulanmış bu örneklemde geçerlidir.
Ek saat koruması 5sn (aynı 5sn geçmiş) baştan sabittir. Sonradan başka eşik,
birleşik filtre veya üçüncü hipotez denenmez.

Her hipotez için Bosona/kontrol özelliği, 10sn sonraki orta fiyat hareketi,
eşleştirilmiş farkın aynı özellikte kalan alt grubu, olumlu/olumsuz/nötr
karşı örnekler raporlanır. Kod aynı özellikleri her saniye iki token için
aktör dolumuna ihtiyaç duymadan hesaplar. Bu ızgarada gelecekteki 10sn fiyat
hareketi ayrıca gösterilir; bütün noktalar dolum veya PnL sayılmaz.
Destek için iki saat korumasında aynı yön, piyasa çıkarınca korunma ve
izleyen bağımsız çok günlü test gerekir; burada son koşul karşılanamaz.

## Kabul

- [x] 1. Gerçek maker parçaları/parent kimlikleri ve 1/5/10sn markout tablosu.
- [x] 2. Sonuçtan bağımsız kontrol eşleştirmesi, kapsam/tekrar/kayıp/karşı örnekler.
- [x] 3. İki önbilgi hipotezi, dolumdan bağımsız seçici, açık yanlışlama sonucu.
- [x] Kimlik/rol/fiyat, as-of/gelecek değişimi, ufuk sansürü, match bağımsızlığı
      ve küme ağırlığı regresyonu; Ruff/syntax, gerçek ağsız çalışma ve aynı hash.
- [x] Kaynakların korunduğu doğrulansın; kısa Türkçe rapor ve tekrar komutu.

## Gerçek çalışma sonucu

Üç sonlu adım tamamlandı. 8 atama/6 uygun/5 Bosona işlemli piyasa; 5.240
maker BUY, Bosona 22 dolum/14 parent. Ana 1/5/10sn markout +0,678/−0,225/
−0,417 sent/pay; gerçekleşebilir PnL değil. 22/22 sabit koşullu kontrol;
10sn göreli fark +1,072 sent, %93'ü 22:00 piyasasından. Tek parent çıkınca
işaret değişebiliyor; saat kaydırması da piyasa-dışı sonucu değiştiriyor.
H1 zayıf/zamana duyarlı, H2 desteklenmedi. Yeni güçlü aday çıkarılmadı.
34 diğer maker parçasında ücret bulundu: rolün genel tanımı ücret=0 değil.
Bosona ve seçilen kontrollerin ücretleri sıfır; fiyat karşılaştırması değişmedi.
10 kontrol (48 gerçek nedensellik bağlamı), hedefli Ruff/syntax geçti.
İki tam ağsız çalışmada 12 çıktı (rapor ve kontrol dahil) aynı SHA256.
Karşı örnekler, bütün eşleştirmeler, eksikler ve actor-free 10.548 bağlam
results/ altında. Kaynak/aday/protokol korundu; yeni süreç veya emir yok.
Ekonomik kabul ve çok günlü bağımsız doğrulama açık. Donmuş tasarım
design_frozen.md içinde; bu sonuç bölümü protokolü geriye dönük değiştirmez.
