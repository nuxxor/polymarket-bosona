# BTC5dk dışı Bosona araştırması

[Türkçe rapor](RAPOR.md) · [Çalışma planı](plan.md) · [Sabit aday protokolü](protocol.json)

Bu dizin ana repodan bağımsız bir analiz alanıdır. Ağ çağrıları yalnız kamu verisi içindir.
Anahtar, emir, SSH, deployment veya süreç yönetimi yok. `src/` önceki araçların değiştirilmeyen
kopyalarını içerir; bu kopyaların kendi `fetch/watch` komutları çalıştırılmaz.

Python 3.12; yerelde zaten bulunan numpy, scipy, scikit-learn ve ruff kullanıldı.
Kesin sürümler `results/checks.json` içinde. Yeni bağımlılık veya ücretli servis kurulmadı.

**Donmuş veriden tekrar üretim** (internete ve ana repoya yazma gerektirmez):

```bash
python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/research.py analyze
OPENBLAS_NUM_THREADS=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/study.py behavior
OPENBLAS_NUM_THREADS=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/study.py selection
OPENBLAS_NUM_THREADS=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/study.py mechanism
OPENBLAS_NUM_THREADS=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/candidate.py replay
OPENBLAS_NUM_THREADS=1 python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/check_research.py
python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/report.py
```

**İlk veri ediniminin tekrar çalıştırılması** (mevcut önbellek korunur, eksikler kamu API’sinden alınır):

```bash
python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/research.py fetch
python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/research.py fresh_interval
python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/research.py analyze
python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/research.py refresh
python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/research.py analyze
python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/research.py histories
python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_context.py
python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/research.py validate
python3 /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/research.py source_audit
```

`fetch` ana repodaki tamamlanmış ham aktivite dilimlerini ve önceki mumları salt okunur kullanır;
resmî sözleşme eksiklerini tamamlar. `refresh`, çokluğu belirsiz 158 piyasanın activity yanıtını
saklar. Kapsam kesimi sabittir; komutu yeniden çalıştırmak güncel dönemi kendiliğinden eklemez.
Yeni dönem ayrı dizin ve yeni ön kayıt gerektirir.

`btc15_context.py` ana repodaki **önceden kurtarılmış** fiyat akışlarını okur; 18 GB ham tape’i
yeniden taramaz. 20 Eylül 23–21 Eylül 11 UTC saatlerinin ek fiyatları bu dizine donduruldu.
Taşınabilir tekrar üretim için `raw/btc15_context.json` yeterlidir; bütün eski arşivi kopyalamaz.
Bağlamı ham fiyatlardan yeniden çıkarmak için manifestteki eski salt okunur dosyalar gerekir.

**Dosyalar:**

| Dosya | İçerik |
|---|---|
| `raw/activity/*.json`, `raw/activity_checks/*.json` | Sayfalaması tamamlanmış kaynaklar ve taze çokluk denetimi |
| `raw/markets/*.json` | Resmî zaman, kural, sonuç ve token bilgileri |
| `raw/histories/*.json` | Kamu fiyat tarihi sorgusu, cevabı, alınma zamanı |
| `raw/*_1m.json` | BTC/ETH/SOL/BNB/DOGE/XRP kapalı Binance dakikaları |
| `results/windows.json`, `results/fills.json` | Nakit/FIFO ve ilk/ek/tamamlama/yeni risk; önceki/sonraki olası ödemeler |
| `results/summary.json`, `results/behavior.json` | 29 grubun tüm sonuçları, başarısız alt gruplar dahil |
| `results/selection*.json`, `results/style_models.json`, `results/next_side*.json` | Sabit kronolojik tahmin karşılaştırmaları |
| `results/btc15_mechanism.json` | Gerçek referansla 5/10sn duyarlılık ve karşı hipotezler |
| `results/conditional_completion*.json` | Bosona dolumlarına koşullu, uygulanabilirlik iddiası olmayan karşılaştırma |
| `results/candidate_price_scenarios.json`, `results/candidate_scenario_rows.json` | 36 senaryo ve her sanal pencerenin yolu; gerçek ask backtest’i değildir |
| `candidate.py` | Bağımsız karar motoru, FIFO/risk yönetimi ve sonradan alınmış defterle yerel uygulama adaptörü |
| `results/api_validation.json`, `results/checks.json` | API, resmî sonuç, Decimal ve regresyon kanıtları |
| `artifact_manifest.json`, `results/reproduction.json` | Dosya hash’leri ve aynı girdilerden aynı çıktı kontrolü |

**Sınırlar:** Kamu fiyat örneği ask/derinlik değildir; canlı maker dolumu varsayılmaz.
Karar motoru ve defter adaptörü çalıştırılabilir, fakat bir üretim shadow servisinin scheduler,
kilit, kalıcı portföy, restart ve portföy geneli kesici entegrasyonu bu dizinde yok.
Bu görevde yeni servis istenmedi; protokolün bu kuralları ileri uygulamanın kabul koşullarıdır.
Geçmiş senaryonun piyasa başına limitleri kodda uygulanır; portföy geneli −10 $ kesici uygulanmaz.
Ölçülemeyen piyasa sıfır getirili işlem değildir. Sonuçlar temiz kör test değildir.

```bash
python3 -m ruff check /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/research.py /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/study.py /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/candidate.py /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_context.py /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/check_research.py /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/report.py
```
