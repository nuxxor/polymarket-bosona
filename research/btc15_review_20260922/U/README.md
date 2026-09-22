# Bosona BTC5dk dışı bağımsız denetim — tekrar üretim

Önce [KARAR.md](KARAR.md), ardından [RAPOR.md](RAPOR.md). Hatalar [HATALAR.md](HATALAR.md), 29 grup [GROUPS.md](GROUPS.md), tek gelecek ölçüm [DENEY.md](DENEY.md) içinde. Alt denetimlerin raporları: [muhasebe](accounting/RAPOR.md), [zaman/uygulama](execution/RAPOR.md), [zincir](onchain/RAPOR.md). `onchain/README.md`, resmi exchange deposundan alınan kaynak belgedir.

Bu dizin tek yazılabilir çıktı alanıdır. MAIN/R/F/S kaynakları değiştirilmez. Komutlar emir göndermez, süreç başlatmaz/durdurmaz ve mevcut kaydediciyi yeniden yapılandırmaz. Hiçbir gizli anahtar gerekmez; yeni bağımlılık kurulmadı.

## Tek komutla çevrimdışı denetim

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/reproduce.py
```

Komut mevcut ham cache üzerinde muhasebe, kamu kimlik mutabakatı, zincir, fiyat bağlamı, donmuş aday, yeni kesit, istatistik ve somut yolları yeniden hesaplar. F/analyze.py saf hesapları yalnız bu dizine yönlendirilir. Negatif regresyonlar, bütün yerel Python dosyalarının syntax/Ruff kontrolü, önemli çıktıların önce/sonra SHA karşılaştırması yapılır. Sonuç [verification.json](verification.json), adım logları `verification/` içindedir. Gelecek veri eksikliği başarıya çevrilmez; seçicinin negatif kontrolleri onchain/check.py içindedir.

## Veri ve zaman sınırları

| Kaynak | Sürüm / kesim | Kanıt |
|---|---|---|
| R tarihsel araştırma | 13 Eylül 00:00–21 Eylül 12:00 UTC | [provenance.json](provenance.json), [accounting/inputs.json](accounting/inputs.json) |
| F takip araştırması | 13–17 keşif, 18–20 kronolojik; kaynak manifesti | `statistics/reproduced`, [istatistik](statistics/audit.json) |
| S gerçek defter kesiti | 14 tam kapanış, 21 Eylül 14:30–18:00 UTC | S kaynak hashleri; [execution/results.json](execution/results.json) |
| Yeni yerel sabit kesit | 21 Eylül 18:38:32.532 UTC; 16 tam kapanış | [freeze_manifest.json](new_period/freeze_manifest.json), [sonuç](new_period/results/summary.json) |
| Kamu zinciri | Seçilmiş 4 BTC15 piyasasında 42 TRADE + 1 MERGE; 2 ek geç-zincir kontrolü | `onchain/selection.json`, `merge_selection.json`, `postclose_selection.json`, `raw/`, `official_sources.json` |
| Kimlik çakışması taze doğrulama | Eksik 10 MERGE'in tümü | `accounting/raw_collision_checks`, `collision_result.json` |

Yeni kesit byte sınırıyla dondurulmuştur; sonraki çalıştırma canlı kaydı sessizce genişletmez. `snapshot.py --offline`, aynı kesimi ve cache'i kullanır. İlk eksik pencere, kesimde açık pencere, işlem olmayan pencere ve eksik kayıt ayrı tutulur. Başlangıçtan önceki işlemleri kaçırmamak için her 18 piyasanın kamu geçmişi ayrıca start=1 ile doğrulanmıştır.

`onchain/probe.py`, `accounting/collision_check.py` varsayılan olarak cache üzerinden çalışır. `--fetch` yalnız önceden seçilmiş eksik kamu yanıtlarını alır; tekrar üretimde kullanılmaz. Ham cevaplar istek URL/parametreleri, alım zamanı ve SHA içerir. Resmî mekanizma/API/sözleşme kaynakları alt dizinlerde arşivlenmiştir.

Python ve kurulu kütüphane sürümleri `provenance.json` içinde. İstatistik seed'i 20260921; bootstrap 4.000 tekrar. Eski 36 fiyat senaryosu ve bu denetimin duyarlılıkları raporda açıkça sayılmıştır. Eski kaynak manifestlerinden farklı R/F plan dosyaları kayıtlıdır; korunan aday/protokol/bağlam dosyaları değişmemiştir.

Yerel nihai dosya boyutları ve SHA'ları `artifact_manifest.json` içindedir. Kaydedici kendi yetkili çalışma akışında yeni veri yazmaya devam edebilir; onun canlı dosyalarının değişmesi bu araştırmanın kaynak kodu değiştirdiği anlamına gelmez.
