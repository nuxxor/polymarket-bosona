# Chainlink Data Streams geçmişi — settlement kaynağı ÇÖZÜLDÜ
Tarih: 2026-09-13

## Ne bulundu
Operatörün aylık $150'lık Chainlink Data Streams aboneliği **çalışıyor**. Önceki turda alınan
401/403 kimlik hatası değildi:

1. **Cloudflare 1010** — `Python-urllib` user-agent'ı bloklanıyor. Tarayıcı UA'sı ile geçiyor.
2. **Kimlik kombinasyonu** — `Authorization` başlığı `STREAMS_API_KEY` değil **`STREAMS_USERNAME`**
   olmalı; HMAC anahtarı `STREAMS_API_SECRET`. (Değerler `~/.config/chainlink_streams/creds.env`,
   asla basılmaz.) Host: `api.dataengine.chain.link` (testnet DEĞİL).
3. İmza: `HMAC-SHA256( "GET <path> <sha256(body)> <clientId> <ts_ms>", secret )`.

## Hesaptaki 3 feed — kimlikleri doğrulandı
Canlı tape'teki Polymarket yayınıyla **18 ondalık hane birebir** eşleşme ile:

| Feed ID | Nedir | Tape karşılığı |
|---|---|---|
| `0x00039d9e...75b8` | BTC/USD spot (v3, bid/ask'li) | `w=0` |
| `0x0002e6b0...c087` | BTC/USD **TWAP-30** (v2) | `w=30` |
| `0x0002ee67...d95f` | BTC/USD **TWAP-60** (v2) | `w=60` ← **settlement bunu kullanıyor** |

## Doğrulama — settlement'ı birebir üretiyor
Binance vekilinin **yanıldığı 159 pencerede** (tanım gereği vekil %0):
- Gerçek TWAP-60 feed'i: **159/159 = %100**
- (Spot'tan kendi hesapladığım TWAP ile: %86,8 — yani vekil yaklaşımı değil, feed'in kendisi şart.)

Kural doğrulandı: **Up kazanır ⟺ TWAP60(S+300) ≥ TWAP60(S)**.

## Neden önemli
- 29 günlük geçmiş erişilebilir → **4.621 pencere**, canlı tape'i beklemeden backtest.
- Aynı pencereler `btc5m_top_actor_hunt_20260902_v1` tam zincir defteriyle örtüşüyor
  → her aktör dolumu, o anki gerçek settlement durumuyla hizalanabiliyor.
- Önceki `pm_true_twap_fair` turu 23 pencereyle güçsüzdü; şimdi 200× veri var.

## Dosyalar
- `cl_client.py` — imzalı REST istemcisi (sır basmaz)
- `fetch.py` / `fetch_windows.py` / `fetch_all.py` — toplu çekiciler (sayfa başına 100 saniye, limit 100)
- `HIST_twap60.parquet`, `HIST_spot.parquet` — 28 günlük 1Hz geçmiş
- `DISAGREE_TWAP60.parquet` — doğrulama dilimi (159 pencere, %100)

## Sıradaki
`pm_true_twap_fair_20260913_v1/CONTRACT.md` içindeki mühürlü kapılar bu veriyle koşulur.
Kapılar sonuca bakılarak DEĞİŞTİRİLMEZ; ücret sonrası (taker ve maker sürümü) raporlanır.
