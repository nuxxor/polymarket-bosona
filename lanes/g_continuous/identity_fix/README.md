# G2 — outcomeIndex999 altyapı düzeltmesi

Operatör bu sürümü G2 olarak adlandırdı. G2 strateji değişikliği değil,
G1'in aynı politikayla çalışan muhasebe/veri kimliği revizyonudur. Mevcut
laneG, süreç/dizin adları ve bütçe kimliği korunur; adlandırma için canlı
kaynak veya release hash'i değiştirilmez. Bosona'nın seçici taker kapanışı
bu sürüme eklenmedi.

22 Eylül2026. **Kullanıcı komutu sonrası yama uygulandı ve15:07:30TR'de
LondraLIVEbaşlangıcı doğrulandı.** Writer177479, yeni kaynak25fca69d4ad7,
kayıtçılar177772/177773aktif. Aynı bütçe4527c3ca7a69abf92a33;
RUN/BUDGETorijinalbaytları değişmedi.15:07:32ilk mutabakat başarılı.
Kanıt: runtime_after_operator.json. Yeni canlı999tekrarı henüz görülmedi;
normalleştirme eski gerçek olay replay'iyle doğrulandı.

Kök neden: gerçek Up tokeniyle gelen outcomeIndex999, mutabakatı kapatıp
14:00penceresinin devamında emirleri engelliyordu. Yeni kaynak doğrulanmış
slug/condition/token eşlemesiyle yönü mutabakatın ortak girişinde düzeltir.
Çelişen yön, farklı token/condition ve eksik piyasa bilgisi reddedilir.
Ham kayıt değiştirilmez; kanonik işlem anahtarı ve çokluk API düzelince de
aynı kalır. G'nin yeni pencereleri token keşfinde kimlik önbelleğini doldurur;
önbelleksiz eski0/1tarihçesine topluca yeni metadata denetimi eklenmedi.

Yalnız runtime ab.py ve onun release hash'i değişir. Yeni SHA:
25fca69d4ad75a3a28db9f62903f4c300a8adafdc7e923bc942f87eb6699d64c.
Politika, miktar, bütçe, RUN ve state korunur. Yerel ana bot/ab.py ve
orijinal lanes/g_continuous/bot kaynağına dokunulmadı.

Londra'da7emirsiz kontrol geçti: yama uygulama, varsayılan park doğrulaması,
gerçek999vakası, Gpolitikası/rezerv, pilot, sürekli bütçe/kaydedici veWS.
Gerçek kamu API/Gamma verisiyle beş işlemlik replay−$2,30 ve açık mutabakat
üretti; gerçek geçmiş999alanı testte yeniden eklendi. SDK/emir çağrısı yok.
Önceki kaynak aynı olay kontrolünü geçemedi. Kanıtlar: old_regression.json,
remote_tests.json,real_public_replay.json. Hedefli RuffF/E9, Python derleme,
bash sözdizimi ve sahteSSH ile launcher argüman testi geçti.

Operatör komutu:

```bash
bash "/home/taygun/Masaüstü/polymarket-bosona/londra_g_999_duzelt_devam.sh"
```

Komut normalSTOP_Gkapanışını bekler; zorla süreç öldürmez. Kaynak ve manifest
yedeğini alıp yamalar; mevcut pilotun emirsiz hesap/çözüm kontrollerinden
sonra aynı bütçeyleLIVEresume ister. Yeni$10açmaz. Eski süreç kapanmazsa,
dosya hash'i değişmişse, bütçe tükenmişse veya hesap doğrulanmazsa kapalı kalır.
Finansal restart dalı test amacıyla çalıştırılmadı; gerçek başlatmayı kullanıcı
yaptı. LIVEbaşlangıcı, yeni kaynak hash'i, bütçe kimliği ve iki kaydedici
komuttan sonra salt-okunur araçlarla ayrıca doğrulandı.

Remote: /home/ubuntu/g-identity-fix-20260922/operator.console.log.
