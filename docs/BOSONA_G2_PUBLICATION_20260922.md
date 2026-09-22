# G2 ve BTC5m bağımsız inceleme paketi — 22 Eylül 2026

Uzak main9945a89 üzerine ayrı worktree içinde hazırlanmıştır. Önceki G/G1 ve
BTC15 yayınları korunur. Ortak yerel çalışma ağacı/index, devam eden ULTRA
incelemesi ve çalışan Londra süreçlerine müdahale edilmez. Bu yayın deploy
veya yeni araştırma sonucu değildir; mevcut kanıtı incelemecilere ulaştırır.

## Dahil edilenler

- `lanes/g_continuous/identity_fix/`: tam G2 kaynak/test/release paketi,
  önceki kaynak, gerçek999olayının kamu-verisi fixture'ı ve emirsiz test kanıtı.
  Kullanıcının12:07:30UTC/15:07:30TRbaşlangıcını doğrulayan salt-okunur
  runtime özeti; aynı bütçe ve politika hash'leri.
- `data/analysis/g1_selective_exit_20260922/`: sınıflandırma kodu, rapor,
  sonuçlar ve kontroller.26/30taker azaltım davranışıdır; kapanış tetikleyicisi
  veya bağımsız ekonomik avantaj bulunduğu iddiası değildir.
- `data/analysis/btc5m_parent_research_20260921/`: önceki kod/özetlere ek
  137tam kamu piyasa geçmişi,2.041kamu transaction receipt'i ve gereken JSON
  girdileri.2.066BUYçokluğu, parent ve rol sonuçları denetlenebilir.
- `data/analysis/g1_comparison_20260922/`:11piyasa/22aktör-piyasa hesabının
  kamu activity/market/receipt kesiti, hesaplar, kod, tanısal özet ve raporlar.
  Bu yerel snapshot'tır; Londra'daki ileri çalışmanın son kesiti olduğu
  veya iki saatlik ileri takibin tamamlandığı varsayılmaz.
- Ortak İngilizce inceleme promptu ve operatör başlatıcısı. Başlatıcı
  yayımlanması onu çalıştırma talimatı veya finansal eylem değildir.

## Bilinçli kapsam sınırı

Anahtar/kimlik dosyaları, ham özel hesap WS akışları, `own_state.json`,
`case_1790074800_own_events.json`, çalışma logları, paket tar/zip arşivleri ve
devam eden bağımsız ULTRA çıktıları eklenmedi. Seçilmiş ekonomik/runtime
özetleri ve kamu işlem kayıtları dahildir. G1ilk pilotunun yayımlanmış özeti
korunur; özel A/Bham akışlarına dayanan bütün hesapları GitHub'dan tekrar
üretme garantisi yoktur. Harici büyük L2/BTC/Chainlink arşivinin tamamı
bu commit'e taşınmadı. Eksik ham girdi, kaydı olmayan olay diye yorumlanmaz.

## Yayın kopyasında çalıştırılan kontroller

Dokuz emirsiz kontrol geçti:

```bash
python3 lanes/g_continuous/identity_fix/check_patch.py
python3 lanes/g_continuous/identity_fix/bot/test_identity.py
python3 lanes/g_continuous/identity_fix/bot/test_g.py
python3 lanes/g_continuous/identity_fix/bot/test_g_pilot.py
python3 lanes/g_continuous/identity_fix/bot/test_continuous.py
python3 lanes/g_continuous/identity_fix/bot/test_g_stream.py
python3 data/analysis/btc5m_parent_research_20260921/check.py
python3 data/analysis/g1_comparison_20260922/check.py
python3 data/analysis/g1_selective_exit_20260922/analyze.py
```

Kontroller geçerli bir yerelPythonortamıyla izole yayın kopyasında çalıştı;
bazıları sonuç dosyasını yeniden yazar. Gerçek22aktör-piyasa hesabı ve
cached receipt/parent toplamları tekrar doğrulandı. R1'deki2.041receipt'in
tamamı bu yayın turunda baştan decode edilmedi; mevcut R1kontrolü ve
veri manifestleri kullanıldı.16releasehash'i eşleşti;24Pythonkaynağı
derleme, hedefliRuffF/E9 ve bashsözdizimi geçti. Önceki yayının ilgisiz eski
test/lint sınırları `YAYIN_KONTROLU_20260922.md` içinde korunur.

Yeni içeriğin dosya/byte/SHA manifesti ve yayın kontrol özeti:
`data/analysis/g2_publication_20260922/manifest.json`, `checks.json`.
Gizli veri taraması yalnız yeni yayın içeriğini kapsar; önceki Gitgeçmişinin
tamamına ilişkin yeni denetim iddiası yoktur.

Gitleaks8.30.1genel taramasında tek eşleşme, önceki yayında incelenmiş
`plan.md:476`Türkçe metnidir; satırın uzak ana commit ile aynı olduğu
doğrulandı. Yeni gerçek secret bulgusu0; ek özel anahtar/mnemonic kuralları0.
İki exact kaynak snapshot'ındaki dört eski trailing-space uyarısı, canlı ve
önceki kaynak hash'lerini korumak için değiştirilmedi; diğer staged içerikte
`git diff --check`temiz. Bu sınırlar kontrol JSON'unda da kayıtlıdır.
