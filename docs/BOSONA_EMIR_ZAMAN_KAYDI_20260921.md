# M3 — Emir zaman kaydı hazır; canlı kalibrasyon henüz yok

21 Eylül 2026. M2'deki eksik iptal saatlerini gelecekte kaydetmek için
ortak emir yoluna gözlem eklendi. Ana depo ve F çalışma kopyası hazırlandı.
Londra'ya dağıtım, yeni emir, bütçe veya shadow başlatma yapılmadı.

## Değişiklik

`bot/emir_iz.py`, mevcut SDK çağrısını aynı argümanlarla çalıştırıp aynı
cevabı/istisnayı geri verir. Strateji, fiyat, miktar ve iptal kararı değişmez.
`bot/ab.py` içindeki toplu/tekil POST, tekil/toplu iptal, açık emir sorgusu,
emir durum sorgusu ve miktar artışına bağlandı. FAK tamamlama yolu da dahil.
F dağıtım dosya listesine modül eklendi, yerel kaynak manifesti yenilendi;
bütçe dosyası ve geçmiş muhasebe değiştirilmedi.

Canlı başlatmada mevcut logun yanında `LOG_*_emir_iz.jsonl` açılır.
Kuru mod kendi başına bu dosyayı açmaz. Test kayıtlarında `mode=MOCK` vardır.
Dosya yazma dışında ağ, ek SDK isteği veya yeni iş parçacığı oluşturmaz.

## Saat ve kimliklerin anlamı

- `session`: süreç başına kimlik; başlangıçta bot/modül kaynak hash'leri.
- `attempt`: her SDK çağrısına ayrı kimlik. Botun tekrar denemeleri ayrıdır;
  SDK içindeki olası HTTP tekrarlarının sayısı veya wire-send saati değildir.
- `request`: çağrı niyeti dosyaya yazılmadan hemen önceki yerel saat.
- `begin/end`: SDK çağrısından hemen önce/sonra UTC ve monotonic nanosaniye.
  `duration_ns` monotonic farktır; duvar saati sıçramasından etkilenmez.
  İmzalama ve request kaydını yazma bu süreye dahil değildir.
- POST girdisindeki token/fiyat/miktar, yanıttaki order ID ile aynı deneme
  üzerinden bağlanır. Toplu yanıtta `slots_match=false` ise sıra eşlemesi
  güvenilir sayılmaz. Kimliği bilinmeyen POST çözümlenmiş sayılmaz.
- İptal yanıtındaki `canceled/not_canceled` üyelikleri ayrı kaydedilir;
  eksik alan `null` olur. Sonraki `LIVE` sorgusu korunur. Cevap gelmesi
  emrin kapandığının kanıtı değildir; çelişkili kayıt birleştirilmez.
- `fill_observed`: botun miktar artışını işlediği an; `exchange_ns=null`.
  Durum sorgusunun dönüş saati ayrıca vardır. Gerçekleşme/iptalin borsa
  saati bu kayıtlardan icat edilmez; defter kaydedicisinin saatleri ayrıdır.

Ham imza, istek gövdesi, header, API anahtarı, yanıt/istisna metni yazılmaz.
Dosya hatası kabul edilmiş emir cevabını yutmaz; stderr'e sabit bir uyarı
verir, sonraki kayıtlarda `errors>0` taşır. Böyle oturumlar kalibrasyonda
kullanılamaz. Sıra boşluğu, eksik başlangıç/bitiş, cevapsız deneme ve
bozuk satır da eksikliktir. `errors=0` tek başına veri yeterliliği değildir.
Dosya her olayda kapatılır, fsync yapılmaz: elektrik kesintisinde son
kayıtların kalıcılığı garanti edilmez. Yazım gecikmesi gerçek emir yoluna
eklenir; bu sürümle ölçülecek gecikme eski sürüme geriye uygulanamaz.

## Doğrulama

Gerçek ortak fonksiyonlar sahte SDK ve kapalı ağ erişimiyle çalıştırıldı.
Ana kaynak ve `--lane-f` için ayrı ayrı **37 çağrı / 79 olay / 3 miktar artışı**
üretildi. Kısmi iptal, LIVE çelişkisi, geciken POST sırasında iptal,
eşzamanlı sorgu, timeout/tekrar, bozuk yanıt, geri sıçrayan UTC saati,
tekrarlanan dolum ve dosya arızası kontrol edildi. Yapay gizli metin
kayıtlarda bulunmadı; arıza oturumları açıkça işaretlendi.

Her iki kaynakta yerleşik test **121/121**. F muhasebe, D, D arşiv, E, F,
bütçe ve devir testleri geçti; kaynak manifesti doğrulandı. Yeni dosyaların
Ruff kontrolü ve değişen kaynakların syntax kontrolü geçti.

**Mevcut ana depo tamamen yeşil değil:** `test_muhasebe.py`, eski `ab.py`'nin
desteklemediği `cozumle(..., tekrar=True)` çağrısında başarısız. Değişiklik
öncesi kaynakta aynı hata tekrar üretildi. Ayrıca ana kaynağın eski self-test
bölümünde koşullu `collections` kullanımına ait F821 uyarısı hem önce hem
sonra var. F'de bu iki sorun yok. Bunlar bu gözlem eklemesinde değiştirilmedi;
ana kaynağa canlı uygunluk onayı verilmedi.

Londra salt okunur kontrolü **20:32:44 UTC**: eski sekiz PID yok, taranan
Bosona LIVE/shadow Python süreçleri yok. Uzak D/E/F kaynakları değişmedi,
telemetri modülü uzakta bulunmuyor. Jev/kaydediciler bu kontrolün konusu değil.

## Tekrar çalıştırma

```bash
python3 /home/taygun/Masaüstü/polymarket-bosona/bot/test_emir_iz.py
python3 /home/taygun/Masaüstü/polymarket-bosona/bot/test_emir_iz.py /home/taygun/Masaüstü/polymarket-bosona-f/bot/ab.py /tmp/f-emir-iz-yeni.jsonl --lane-f
```

İkinci komutta daha önce bulunmayan bir çıktı yolu kullanılmalı.
Testte görülen `EMIR_IZ_ARIZA` uyarısı kasıtlı dosya arızası kontrolüdür.
Kanıtlar: `data/analysis/btc5m_order_telemetry_20260921/`.
`*_before*` ve patch dosyaları önceki kaynakları; `*_smoke_final*` son
ölçüm testini; `verification.json` regresyonları saklar. Önceki smoke ve
eksik dosyalı ilk test ortamının çıktıları son doğrulama yerine kullanılmaz.

## Açık kalan kapı

Hazırlanan kaynak canlı çalıştırılmadı; gerçek iptal verisi hâlâ yok.
M2'nin `NOT_CALIBRATED_MISSING_CANCEL_CLOCKS` sonucu değişmedi. Sonraki
ölçümde dolmuş/dolmamış bütün emirlerin saat kapsamı ve iptal çelişkileri
incelenmeden kuyruk modeli kalibre, strateji de kârlı ilan edilemez.
