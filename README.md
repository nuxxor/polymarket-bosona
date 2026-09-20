# polymarket-bosona — BTC 5dk Up/Down'da "bosona" mekanizması ve kol C botu

Bu depo, Polymarket BTC 5 dakikalık Up/Down pazarında en kârlı cüzdanlardan `bosona`
(`0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed`) üzerine yapılan çalışmanın ve ona göre
kurulan canlı botun **tam** kopyasıdır (19-20 Eylül 2026 oturumu). Kimlik dosyaları hariç
hiçbir şey atlanmadı.

**20 Eylül muhasebe kontrolü:** 96 atanmış pencerenin kamu işlemleri ve resmî
sonuçlarla toplamı **−15,19 USD**, C'nin 15 penceresi **−2,56 USD** (ücret/iadeler
hariç). Eski özetlerin yerine [muhasebe raporunu](docs/MUHASEBE_20260920.md)
ve yeniden üretme komutunu kullanın. Altı tarihsel yerel kayıt farkı korunuyor.

## Ana bulgular (özet; ayrıntı `docs/hafiza/`)
- bosona yön tahmini yapmıyor. İki tarafa da alış yazan bir maker; kârı **çift maliyeti** belirliyor
  (Up+Down < $1). Zincir defterinde 19/19 gün artı, +2,27 kr/pay, günde ~110k pay; rebate günde $663.
- Mekanizma: dokunuşa yakın **taze oluşan seviyede ilk emir** onun (seviye yaşı medyan 2-3 sn, %81-90 kısmi dolum).
  Biz derin/eski/ucuz seviyelerde duruyorduk (seviye yaşı 5 dk, 0,20 civarı).
- Kol C ("taze seviye") bu mekanizmayı canlıda test ediyor: `bot/ONKAYIT_TAZE_KOL_C_20260919.md` (v1→v3).
- Londra (AWS eu-west-2) gecikme 43 ms vs Türkiye 116 ms; post-only red oranı %52 → %25.

## Dizinler
- `bot/` — `ab.py` (v4.1 + muhasebe yaması, yerel), `ab_v2_LONDRA_CANLI.py` (eski Londra sürümü), ön kayıtlar,
  `STATE_ab.json`, `LOG_ab.jsonl` (canlı olay logu), kuru koşu logları, `arsiv/` (tüm eski sürümler).
  Çalıştırma: `python3 ab.py --test` (öz-test, 121 test), `python3 ab.py --etiket kuru --dk 12` (kuru koşu),
  `python3 ab.py --live` (canlı; `.env.live` ister — bu depoda YOK).
- `kaydediciler/` — `record_polymarket_orderbook.py` (CLOB websocket defter → sqlite),
  `record_fills_tape.py` (cüzdan etiketli TÜM dolumlar, sayfalı), `record_btc_tape.py` (Binance spot),
  `bosona_kayit.py` (`/activity` sürekli kayıt), `collect_chainlink_rtds.py`, `chainlink/` (Data Streams
  TWAP-60 kaydedici + 29 gün geçmiş çekici; kimlik `~/.config/chainlink_streams/creds.env`, depoda yok),
  `polymarket_bot/` (kaydedicilerin bağımlılığı).
- `analiz/izleme/` — `bacak_anatomisi.py` (dolum kuyruk-önü/seviye-yaşı ölçümü, tx-hash hizalı),
  `kuyruk.py`, `ab_skor.py`, `c_rapor.py`, `yanyana_saatlik.py`, `cl_oku.py`.
  `analiz/bu_oturum/` (kol C yaması, Londra geçiş betiği), `analiz/eski_oturum/` (önceki oturumun 70 analiz betiği).
- `data/bosona/` — `activity.jsonl` (12:16Z'den itibaren her hareketi: trade/merge/redeem/rebate; profil ile
  birebir doğrulandı), 18 saatlik `bosona_activity_7g.json`, pencere bazlı `bosona_pen_0919.json`,
  zincir defterinden gün-bazlı `bosona_ledger_pen.csv`.
- `data/tape_fills/` — 15:15Z'den itibaren btc/eth/sol/xrp 5dk TÜM dolumlar, cüzdan etiketli (gzip).
  `fills_backfill_*` dosyaları da okunmalı (ilk sürümün %70 kaybını kapatan geri doldurma).
- `data/tape_cl_direct/` — Chainlink Streams spot/twap30/twap60 (19:16Z→) + bugünün TWAP-60 geçmişi (parquet).
  Price to beat = twap60(S); sonuç = twap60(S+300) ≥ twap60(S) (184/184 + 32/32 doğrulandı).
- `data/tape_btc/` — Binance spot aggTrade + 1 sn mum. `data/db/chainlink_history.db` — RTDS fiyatları.
- `data/referans/hunt_kazanan.json` — pencere kazananları (14 Ağu–1 Eyl).
- `docs/` — HANDOVER.md, araştırma disiplini, günün dersleri/todo, `hafiza/` (tüm bulgu notları),
  `analiz_paketleri/` (zincir defteri, Chainlink, kazanan avı paketlerinin kod+md'si).

## Depoda OLMAYANLAR (boyut ya da gizlilik)
- `.env.live`, `*.pem`, Chainlink `creds.env` — kimlik. Yerelde `/home/taygun/Masaüstü/polymarket/.env.live`.
- `data/db/polymarket_orderbook.db` (5,4 GB, CLOB defteri 15:15Z→) — yerelde `polymarket/data/db/`.
- `FILL_PARTY_LEDGER/{maker,taker}.parquet` (1,1 GB, 14 Ağu–1 Eyl zincir-kesin dolumlar) —
  `polymarket/data/analysis/btc5m_top_actor_hunt_20260902_v1/`.

## Canlı durum (20 Eyl 2026 kontrolü)
Operatöre göre bot bilerek durdurulmuş durumda. Bu depodaki muhasebe yaması
canlıya dağıtılmadı; kaynak doğrulaması kuru koşu ve sahte borsa testleriyle yapıldı.
Depodaki state 71, son log 96 pencere içeriyor; eski state ile canlı başlangıç
engelleniyor. Sunucunun güncel state'i bu incelemede alınmadı.
Kural: aynı hesapta iki canlı bot asla aynı anda çalışmaz.
