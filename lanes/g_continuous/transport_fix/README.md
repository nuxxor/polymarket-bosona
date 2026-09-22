# G2 — geçici pozisyon API kesintisinde güvenli bekleme

22 Eylül 2026, 15:29:23 TR: G2, pozisyon API'sinin 429/408/429 yanıtları
sonrası `maruziyet_teyitsiz` ile kapandı. Zarar kesici veya 999 yön kimliği
olayı değildi. 15:45:21 TR salt-okunur hesap kontrolü: açık emir 0, risk 0,
uzlaşmış PnL −6,823289. Aynı bütçenin başlangıcı −6,0286; fark −0,794689 USD.

Değişiklik yalnız `ab.py` ve kaynak manifestidir. G stratejisi, beş pay,
RUN/BUDGET/STATE ve politika dosyaları değiştirilmedi. Yeni kaynak:
`a5cd853493a6f01ab395495574150bf31c6dec7201783dfb563e98a6e2fa3ca7`.

- Geçici 408/429/5xx ve bağlantı/zaman aşımında G tamamen çıkmak yerine
  emir kapısı kapalı bekler. Mevcut kotasyon döngüsü iptal ister; teyitsiz
  emir rezervini bırakmaz. Devam eden POST kabulü de kapı kapalıysa iptal edilir.
- İlk tekrar 30 saniye, yinelenen pozisyon hatalarında 60/120/240/260 saniye;
  arada normal döngü STOP, zarar limiti ve kayıtçı sağlığını kontrol eder.
- Hem pozisyon okuması hem normal mutabakat geçmeden kapı açılmaz.
  Bozuk/eksik veri ve 401/403 aynı şekilde durdurur; geçici diye yutulmaz.
- Bu değişiklik geçmişteki boş pencerelere geriye dönük emir vermez.
  Eski süreç yeniden başlatılmadı; sonraki LIVE başlangıcı operatöre aittir.

Yerel ve Londra'da yedi emirsiz kontrol geçti. `bot/test_transport.py`, gerçek
429/408/429 dizisini ana döngüde yeniden üretir; eksik ikinci mutabakatı,
STOP/zarar/kayıtçı kapılarını, bozuk veriyi ve POST yarışlarını sınar.
`test_g_stream.py` hesap kapalıyken mevcut emrin iptalini gerçek okuyucu/döngü
üzerinde sınar. 999 kimlik, risk/rezerv, bütçe ve kaynak yaması kontrolleri
korundu. Hedefli Ruff F/E9 ve dört kaynak için sözdizimi kontrolü geçti.

Yama, süreç bulunmadığı ve eski release eşleştiği doğrulandıktan sonra
15:51:54 TR Londra'ya uygulandı. Önceki kaynak yedeklendi; korunan beş
dosyanın bayt hashleri aynı kaldı. Bu bir LIVE teyidi değildir.

Operatörün mevcut başlatma komutu aynı bütçeyi korur:

```bash
bash "/home/taygun/Masaüstü/polymarket-bosona/londra_g_sinirsiz_baslat.sh"
```

Kanıt: `checks.json`, `remote_tests.json`, `deployed.json`, `runtime_check.json`.
Remote paket: `/home/ubuntu/g-transport-fix-20260922`.

Kullanıcı komutundan sonra 16:04:59 TR yeni kaynak a5cd853493a6 ile LIVE
başladı. Writer 178758; kayıtçılar 178762/178763 sağlıklı, iki kanal da
taze. 16:05:01 ilk mutabakat geçti; aynı bütçe kimliği/anchor/cutoff ve
RUN/protokol/politika baytları korundu. İlk emirler ve dolumlar görüldü.
16:06:35 salt-okunur ikinci kontrolde belirsiz emir 0, devam eden POST 0;
bir açık emir ve sonuçlanmamış tek piyasa vardı. Bu açık pencere PnL'si
kesinleşmiş sonuç değildir. Yeni canlı API kesintisi henüz yaşanmadı;
bekleme/toparlanma davranışının kanıtı bu aşamada hata-enjeksiyon testidir.
Kanıt: runtime_after_operator.json ve
runtime_followup.json. Asistan yeniden başlatma/emir işlemi yapmadı.
