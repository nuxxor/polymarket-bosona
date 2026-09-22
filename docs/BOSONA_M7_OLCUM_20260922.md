# M7 — Hesap olaylari ve kamu defteri ayni Londra saatinde

Bu adim yeni bir strateji degil. M6'da eksik kalan olcumu hazirlar:
kendi emrimizin kabul/degisim/iptal bildirimi ve dolum parcalari, kamu
defteri/islem akisi ile ayni sunucuda kaydedilir. Emir gondermez, iptal
yapmaz, finansal bot baslatmaz; onceki hesap ve butceyi degistirmez.

Uygulama `bot/stream_iz.py`; parkli Londra paketi
`/home/ubuntu/polymarket-bosona-m7-v3`. Mevcut `emir_iz.saat()` kullaniliyor.
SDK telemetrisiyle order ID / trade ID / transaction hash ve UTC saatleri
uzerinden birlesebilir; monotonic saatler ayni sunucu acilisina aitse
karsilastirilir. Kayitta sunucunun boot ID'si var.

Her WS mesaji alinir alinmaz UTC/monotonic saat alinir; JSON ayirma ve
disk yazmasindan once. Dosyaya yazma saati ayri tutulur. Iki okuyucu bir
tamponlu yaziciya gider. Tum book/price_change/LTP/tick olaylari ve
hesap order/trade bildirimleri kaynak zamanlariyla korunur. Aynı trade'in
MATCHED ve CONFIRMED bildirimleri ya da tekrar gelen mesajlari yeni
ekonomik dolumlar diye toplanmaz; bu katman yalniz olay kaydidir.

API anahtari olabilen `owner`, `order_owner`, `trade_owner`, icteki maker
owner alanlari, auth, imza ve serbest hata metinleri dosyaya girmez.
Kimlik, sayi ve enum alanlari izin listesiyle dogrulanir; bozuk/veri disi
mesaj reddi sayilir. Fiyat/miktar ondalik metni korunur. Credentials
yalniz resmi CLOB'daki GET derivation ve acik-emir GET kontrolu ile,
ardindan resmi kullanici WS aboneliginde kullanilir; yeni anahtar yaratılmaz.

Baglanti donemi, PONG, kopus, ret, sira numarasi ve kayit kuyrugu tasmasi
ayri izlenir. Tasarsa kayit durur ve sonuc gecersizdir. Baglanti donmesi,
arada kacmis kullanici olaylarini geri getirmis sayilmaz. Bu bir hesap
yoneticisi olmadigindan kendiliginden state/mutabakat yazmaz. Resmi
[kullanici akisi](https://docs.polymarket.com/trading/realtime-order-updates)
ve [kamu akisi](https://docs.polymarket.com/market-data/realtime-data)
abonelik bicimleri ve 10 saniyelik uygulama PING'i kullanilir.

Kendi PLACEMENT/UPDATE/CANCELLATION olaylarini ve parcali dolumlari test
borsasiyla uretiyoruz; bu gerçek dolum gozlemi sayilmiyor. Bot kapaliyken
gercek kullanici olayinin gelmemesi beklenir. Iki kanal PONG'u ve basarili
hesap GET'i, gercek bir emrin tum olay zincirinin teyidiyle ayni sey degil.

Yerel ve Londra testleri: iki gercek okuyucu dongusunde iki piyasa,
parcali/tekrarli/gec bildirimler, ic ice gizli-alan temizligi, yanlis
token reddi, kopus/yeniden baglanti ve kuyruk tasmasi. Ek yerel hata
kontrolunde disk yazma arizasi okuyuculari durdurup gecersiz sonuc uretti;
STOP_M7 kontrolunde normal son kayit yazildi. Ilgili SDK telemetri
regresyonu, Ruff ve syntax de kontrol edildi.

Tekrar emirsiz kayit baslatma komutu:

```bash
bash "/home/taygun/Masaüstü/polymarket-bosona/londra_m7_izle.sh"
```

Bu komut yalniz 35 dakikalik dinleyici acar; 30 dakikalik olasi bir
pilotun oncesi/sonrasi icin bes dakika pay birakir. Islem botu baslamaz.
Tekrar komutlari ayrica bir finansal pilot veya yeni zarar butcesi degildir.
`bosona-m7-observe` tmux oturumu varsa ikinci ayni oturum acilmaz.
Kayitlar `capture/<session>.jsonl` ve `capture/<session>.summary.json`.
Sure dolunca otomatik kapanir; normal erken durus isareti:
`/home/ubuntu/polymarket-bosona-m7-v3/capture/STOP_M7`.
Bu isaret varsa komut tekrar kayit baslatmaz.

Kayit kontrolu:

```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/bot/test_stream_iz.py"
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_m7_20260922/check_capture.py" "/tam/yol/kayit.jsonl.gz" "/tam/yol/kayit.summary.json"
```

Ikinci kontrol sonlu Londra deneyi icindir: iki gercek BTC5m penceresinde
veri, eksiksiz sira/son kayit, snapshot oncesi delta olmamasi, iki kanal
kalp atisi, izinli alanlar ve kaynak hash'leri dogrulanir. Sirf bos bir
kullanici kanalindan tam kalibrasyon sonucu uretilmez. Baslatilacak sonraki
finansal pilotta bu kayitla SDK/gercek dolum kimliklerinin eslenmesi hâlâ
gereklidir; baskalarinin gorunmeyen kuyruk sirasi yine otomatik cozulmez.

Kanıt dizini: `data/analysis/btc5m_m7_20260922/`.

## Gercek Londra sonucu

Saatler 21 Eylul 2026 UTC; Turkiye +3 saat, yani 22 Eylul gecesi.
Uc kosu da emirsiz: her acilis GET'inde acik emir 0, kendi WS order/trade
olayi 0. PONG, gercek emir/dolum zincirinin teyidi sayilmadi.

| Kosu | Baslangic UTC | Sure sn | Kamu olayi | Kamu kopusu | Iki aktif pencere | p99 yazma ms |
|---|---|---:|---:|---:|---|---:|
| 1 | 23:00:27 | 360.02 | 217,100 | 1 | evet | 1.288 |
| 2 | 23:11:23 | 120.01 | 65,168 | 1 | hayir | 1.542 |
| 3 | 23:21:55 | 120.02 | 92,655 | 0 | hayir | 1.399 |

Ilk kosuda piyasa gecisi var ama kopus yuzunden eksiksiz veri kapisi
gecmedi. Ikinci kosuda ConnectionClosedError / 1013 tekrarlandi;
izinli neden sinifi bilinmiyor. Ilk surum kodu kaydetmediginden ilk
kopusa geriye donuk 1013 atanmadi. Yeniden abonelik yaklasik 0,53 sn
sonra gonderildi; bu, eksik verinin geri geldigi veya boslugun tam
suresinin 0,53 sn oldugu anlamina gelmez.

Son kosuyla eszamanli, ayri surecte JSON ayirmayan/disk yazmayan basit
bir kamu dinleyicisi calisti. Ikisi de 0 kopus / 12 PONG ile bitirdi.
Kayitci CPU 11,43 sn, basit dinleyici 3,39 sn. Surekli isleme yetersizligi
bu kosuda gorulmedi; iki tarafta da kopus olmadigi icin onceki 1013'un
sunucu/ag/istemci nedenlerini bu kontrol ayirmiyor. Baglanti baslangiclari
birebir ayni degil; frame sayisi farki kayip sayilmadi.

Uc kosuda ret/tasma/yazici hatasi 0; en buyuk yazma gecikmesi 4,824 ms.
Bu recv() sonrasi olcudur; kutuphane tamponu/ag gecikmesini kapsamaz.
Son temiz 120 sn tek aktif pencereye dustu: transport_ok=true fakat
rollover_observed=false. Birlesik iki-pencere kontrolu bu nedenle exit 1
verdi; kriter gevsetilmedi. Iki onceki kopus korunuyor, kalici cozum
iddiasi yok.

Acilis kusuru yeniden uretildi: liste sorgusu var olan 1790032200
piyasasi icin bos dizi verdi; closed=false ve dogrudan slug sorgulari
ayni condition'i buldu. API/cache ic nedeni bilinmiyor. Bilinen piyasa
icin liste yerine resmi [tek piyasa sorgusu](https://docs.polymarket.com/api-reference/markets/get-market-by-slug)
kullanildi. Hicbir pencere atlanmadi. Testte onceki pencere korunuyor,
yanlis slug reddediliyor. Londra'da 35dk evreninin 10 piyasa / 20 tokeni
bu yolla teyit edildi; 35dk WS kosusu yapildigi iddiasi degil.

Ilk/v2/final kaynak ve kayitlar ayri korundu. Son calisan kaynak SHA256:
4ae34533bf793bb5cf45f2f7af7d697d383775dd03841b21c97e81fef1a78dff.
Ikinci/ucuncu ham kaydin yerel gzip tekrarindan uretilen JSON Londra
sonucuyla birebir esit. Ilk kayittaki sira tekrari, gizli alan enjeksiyonu
ve eksik son kayit negatif kontrolleri reddedildi. Son kodun hedefli
Ruff/syntax ve yerel/Londra iki-kanal testleri gecti.

Paket parkli; olcum surecleri bitti. M4v2 PID yok; kaynak/state/butce
hash'leri M6 sonuyla ayni (final_state.json). **M7 dinleyici hazirligi
tamam; kesintisiz iki-pencere veri kapisi ve kendi gercek emir olaylariyla
kalibrasyon henuz gecmedi.** Bu sonuc yeni strateji veya LIVE acilisi degil.
