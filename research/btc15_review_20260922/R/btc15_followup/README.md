# Tekrar çalıştırma

Bu klasör ana repoya yazmaz. Üst klasördeki candidate.py, protocol.json, donmuş src/
ve önceki raw/results girdilerini kullanır. baseline_hashes.json aday değişmezliğini
kontrol eder. `audit.py` yalnız kamu API'lerini okur; `--offline` eksik cache'te durur.

```bash
python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_followup/audit.py --offline
python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_followup/analyze.py
python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_followup/book_quality.py
python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_followup/new_period.py --offline
python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_followup/check.py
ruff check /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_followup/*.py
python -m compileall -q /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_followup
```

Python 3.12, mevcut NumPy/sklearn ve Ruff kullanıldı; bağımlılık kurulmadı.
`book_quality.py` ilk değerlendirdiği kayıt dilimini `raw/book_validation_prefix.json.gz`
olarak dondurur ve sonraki çalışmalarda aynı dilimi okur. Tam dönem büyüyen ham kayıtlar
`raw/books_72h/books_*.jsonl.gz`; metadata `raw/books_72h/markets/`; güncel durum
`raw/books_72h/status.json`. Son açık gzip dosyasının footer'ı süreç bitene/saat değişene
kadar eksik olabilir; okuyucu bunu son dosyada açık kayıt olarak işaretler.

**Mevcut recorder zaten çalışıyor; tekrar başlatmayın.** Başlatılan komutun eşdeğeri:

```bash
python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_followup/record_books.py --out /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_followup/raw/books_72h --seconds 259200
```

Aynı dizine ikinci süreç dosya kilidiyle engellenir. Süre sınırı 72 saat; yerel diskte
2 GiB boş alan altına düşerse kendi kaydını kapatır. Bilgisayar/bağlantı kesintisi için
servis veya otomatik yeniden başlatma kurulmadı. Kayıt REST örnekleridir, bütün olaylar değil.
Mevcut recorder, bot, shadow, ayar veya bütçe değiştirilmedi; ücretli servis ve emir yok.

Temel çıktılar:

- `results/btc5_audit.json`: sekiz piyasa, yedisi yayımlanmış dönem; parasal/FIFO farklar.
- `results/own_btc5_audit.json`: eldeki 96 bot penceresinin taze kamu mutabakatı.
- `results/miss_rows.json`, `entry_rows.json`: değişmeyen adayın koşul dökümü.
- `results/late_events.json`, `matched_win_loss.json`: saniye/yön paketleri ve yakın çiftler.
- `results/risk_set.json`, `no_add_controls.json`: nedensel özellikler ve gözlenen işlemsizlik kontrolü.
- `results/hypothesis_models.json`, `prediction_rows.json`: sabit iki hipotez ve kronolojik tahminler.
- `hypotheses.py`: sadece kendi envanteriyle hesaplanan açıklayıcı skor; işlem politikası değil.
- `results/book_quality.json`: gerçek defter dilimi doğrulaması; yeterli ileri dönem testi değil.
- `results/checks.json`, `reproduction.json`, `manifest.json`: kontrol/tekrar/hash kanıtı.

Geçmiş fiyat örnekleri ask/derinlik değildir. Gözlenen dolumsuz aralık, emir olmadığı
anlamına gelmez. Modeller sonraki30sn gözlenen eklemeyi açıklar; kârlılık kanıtı sağlamaz.
Karar ızgarası yalnız 600–870sn; en son 30sn dahil, karar öncesi son5sn dolumu olan
noktalar belirsiz envanter nedeniyle dışarıda. İlk öğrenme 13–17, kontrol18–20 Eylül;
21 Eylül eski güncellemesinde BTC15dk dolumu yok. Yeni kayıt henüz kısa.

`coarse_*` dosyaları ilk inceleme arşividir; `coarse_matched_win_loss.json`
ilk nakit-birim-fiyatlı eşleştirmeyi içerir. Nihai ham işlem fiyatı ve dar
yakınlık kontrolü `matched_win_loss.json` içindedir. Eski tanısal sonuçlar
strateji seçimi için kullanılmadı.
