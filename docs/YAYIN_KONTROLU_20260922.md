# Public yayın kontrolü — 22 Eylül 2026

Depo: https://github.com/nuxxor/polymarket-bosona (public).
Kaynaklar 11:07 UTC civarında ayrı worktree içine alınmıştır. Ana çalışma ağacı,
index ve çalışan bot/kaydedicilere müdahale edilmemiştir. Kaynak kodlar ve hash ile
sabitlenmiş paketler yeniden biçimlendirilmeden yayınlanmıştır.

## Kapsam

- Güncel bot/ölçüm kodu, G/G1 paketleri, protokoller, testler ve seçilmiş araştırma özetleri.
- Yeni `.env*`, anahtar/oturum dosyaları, özel hesap olayları, canlı state/log ve ham arşivler hariç.
- Önceden yayınlanmış tarihsel veriler ve Git geçmişi korunur.
- Ayrı BTC15 araştırma dizinleri bu ana repo kopyasına dahil değildir.
- Bazı analizler yerel veri ve mutlak dosya yollarına ihtiyaç duyar; ham verisiz tam yeniden üretim iddia edilmez.

## Kontroller

- Gitleaks 8.30.1: 44 commit ve yayın ağacı tarandı; iki eşleşme gerçek kimlik bilgisi değildi (`plan.md:476`, `analiz/eski_oturum/yama_vol.py:15`).
- Yeni staged içerikte genel secret ve ek cüzdan anahtarı/mnemonic kuralları: bulgu yok. Ek cüzdan kuralları Git geçmişinde de bulgu vermedi.
- Arşiv taraması 5,26 GB açılmış içerik işledi. Bazı önceden yayınlanmış `.gz` dosyaları eksik/bozuk olduğundan bütünü okunamadı; eski ham arşivlerin tamamı için güvence verilmez. `.gz.json` adlı normal JSON dosyaları ayrıca düz metin taramasına girdi.
- 14 kimlik/özel kayıt örnek yolu için `.gitignore` kontrolü geçti.
- 100 Python dosyası derleme, 5 shell dosyası `bash -n` kontrolünden geçti.
- Ağ/emir kullanmayan 8 kontrol geçti: `bot/test_emir_iz.py`, `test_stream_iz.py`, `test_ws_reader.py`, `test_m4.py`; `lanes/g_continuous/bot/test_g.py`, `test_g_pilot.py`, `test_g_stream.py`, `test_continuous.py`.
- G/G1 release manifestlerindeki 14 ve 16 dosyanın hash'leri yayın kopyasıyla uyumlu.

## Korunan mevcut sorunlar

- Eski `bot/test_muhasebe.py`, `cozumle(..., tekrar=True)` çağrısı yüzünden başarısızdır. Önceki commit'te de fonksiyon bu parametreyi almıyordu; bu yayın hatayı oluşturmamıştır.
- Hedefli Ruff kontrolünde iki eski `F821` uyarısı var: ana `bot/ab.py` öz-testindeki koşullu `collections` kullanımı ve bunun `main_before.py` kopyası.
- Snapshot kaynaklarında mevcut sonda boşluk uyarıları korunmuştur; release hash'lerini değiştirmemek için biçim düzeltmesi yapılmamıştır. Yayın için düzenlenen `.gitignore`, README ve plan diff kontrolü temizdir.

Bu işlem deploy, yeni shadow veya gerçek emir başlatmaz.
