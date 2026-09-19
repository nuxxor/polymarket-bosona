---
name: project-chainlink-streams-unlocked-20260913
description: Chainlink Data Streams aboneliği çalıştırıldı; settlement TWAP-60 feed'i tespit edildi ve 29 günlük geçmişle %100 doğrulandı
metadata:
  type: project
---

2026-09-13: Operatörün aylık $150 Chainlink Data Streams aboneliği ÇALIŞIYOR. Önceki turdaki
401/403 kimlik sorunu değildi — iki ayrı tuzak vardı:

1. **Cloudflare 1010**: `Python-urllib` UA'sı bloklanıyor. Tarayıcı User-Agent'ı şart.
2. **Kimlik**: `Authorization` başlığı `STREAMS_API_KEY` DEĞİL, **`STREAMS_USERNAME`** olmalı.
   HMAC anahtarı `STREAMS_API_SECRET`. Host `api.dataengine.chain.link` (testnet 401 verir).
   İmza: `HMAC-SHA256("GET <path> <sha256(body)> <clientId> <ts_ms>", secret)`.
   Değerler `~/.config/chainlink_streams/creds.env` — asla basılmaz.

**Feed kimlikleri (canlı tape ile 18 hane birebir doğrulandı):**
- `0x00039d9e...75b8` = BTC/USD spot (v3)
- `0x0002e6b0...c087` = TWAP-30
- `0x0002ee67...d95f` = **TWAP-60 — Polymarket BTC5m settlement'ı bunu kullanıyor**

**Doğrulama:** Binance vekilinin yanıldığı 159 pencerede gerçek TWAP-60 feed'i 159/159 = %100.
Spot'tan elle hesaplanan TWAP ile sadece %86,8 → vekil/yaklaşım yetmiyor, feed'in kendisi şart.
Kural: Up kazanır ⟺ TWAP60(S+300) ≥ TWAP60(S).

**Kapasite:** 29 gün geçmiş, sayfa başına 100 saniye (`/api/v1/reports/page`, limit max 100),
~13 sayfa/sn (6 thread). 4.621 pencere backtest'e hazır — canlı tape'i beklemeye gerek yok.

**Why:** Bu, bugüne kadarki tüm kulvarlardan farklı: ilk kez sonucu BELİRLEYEN kaynağın kendisi
elimizde, piyasanın çoğu Binance vekiline bakıyor. Edge iddiası için ilk defa bir *mekanizma* var.

**How to apply:** Kod `data/analysis/pm_chainlink_history_20260913_v1/` (cl_client.py + fetch*.py,
README_TR.md). Karar kapıları `pm_true_twap_fair_20260913_v1/CONTRACT.md`'de MÜHÜRLÜ — sonuca
bakarak değiştirilmez, ücret sonrası (taker: −0,07·p·(1−p); maker: 0) raporlanır.
Bkz. [[project-disagreement-falsification-20260913]].


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🔓 CHAINLINK STREAMS AÇILDI (09-13): $150'lık abonelik çalışıyor — hata kimlik değil, Cloudflare UA + Authorization=STREAMS_USERNAME (API_KEY değil); TWAP-60 feed'i `0x0002ee67...d95f` = Polymarket settlement kaynağı, tape ile 18 hane birebir; Binance'in yanıldığı 159 pencerede 159/159 %100; 29 gün geçmiş = 4.621 pencere backtest'e hazır](project_chainlink_streams_unlocked_20260913.md)
