---
name: project-devir-ve-ortam-20260919
description: "09-19 16:43Z devir — canlı bot/kayıtçı ops durumu, Binance vadeli websocket bu ağdan veri vermiyor (spot çalışıyor), izleme betikleri scripts/izleme/, eş oturum çakışma tehlikesi"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0e095c2e-d109-4b41-8066-a0b2005c3a13
  modified: 2026-09-19T16:49:30.694Z
---

**Devir (2026-09-19 16:43Z, polymarket-d1 oturumu):** HANDOVER.md'deki 5 süreç ayaktaydı,
bot (`ab.py --live`, cwd `data/analysis/pm_merdiven_ab_20260918_v5/`) sağlıklıydı, STOP yoktu.

**Ortam gerçeği (kalıcı):** Binance **vadeli** websocket (`fstream.binance.com`, hem `/stream` hem `/ws`)
bu ağdan bağlanıyor ama HİÇ mesaj göndermiyor (17 dk sıfır olay, ping'ler yanıtlandığı için
"KOPTU" da demiyor). **Spot** akışı (`stream.binance.com:9443`, `data-stream.binance.vision`) çalışıyor;
REST `fapi.binance.com` de çalışıyor (botun `onceki_oynaklik()` REST kline kullanıyor, etkilenmedi).
`scripts/record_btc_tape.py` 16:45Z'de spot akışına çevrildi. Sessiz başarısızlık: dosya hiç oluşmuyor.

**İzleme betikleri kalıcı yere taşındı:** `scripts/izleme/{ab_skor,kuyruk,yanyana_saatlik,bosona_kayit}.py`
(eski oturumun /tmp scratchpad'inden; `bosona_kayit.py` süreci hâlâ /tmp yolundan çalışıyor, yeniden
başlatılırsa `scripts/izleme/` yolunu kullan).

**Eş oturum çakışması:** devir sırasında önceki oturum (`polymarket-c8`, claude PID 2031997) hâlâ
komut çalıştırıyordu ve aynı düzeltmeyi 2 dk önce yapmıştı; ben kopya kaydedici başlatıp durdurmak
zorunda kaldım. Devralırken ÖNCE `ListAgents` + `ps` ile eski oturumun canlı olup olmadığına bak,
süreçlere dokunmadan önce eş oturuma mesaj at.

**Why:** aynı canlı botu iki oturumun yönetmesi çift restart / yetim emir / bozuk gz üretir.
**How to apply:** süreç müdahalesi tek oturumdan; `pkill -f` yerine PID ile `kill`; bot için `touch STOP`.
İlgili: [[project-vol-kapisi-20260919]], [[project-kuyruk-olcumu-20260919]]

**Dolum kasedi %70 eksikti (17:00Z'de bulundu ve düzeltildi):** `record_fills_tape.py` ilk sürümü her turda
yalnız en yeni 500 satırı alıyordu; data-api işlemleri ~5 dk gecikmeyle eski timestamp'le eklediğinden geciken
satırlar 2.000+ yeni satırın arkasında kalıp hiç görülmüyordu (3 pencerede %69-72 kayıp, bosona'nın 5 işleminin 4'ü yoktu).
Sayfalı sürüm 16:58Z'de canlı (PID 3506907), 16:35-16:45Z pencereleri `fills_backfill_20260919_1635.jsonl` ile
geri dolduruldu (`_backfill=1`). **16:36-16:58Z arası hourly dosya TEK BAŞINA eksik; analizde backfill dosyasını da oku.**
bosona `/activity` kaydı doğrulandı: `/trades?user=` ile 823/825 örtüşüyor; kapasite 1000 olay/45 sn, ölçülen tepe 23/dk.
Kural: "yazıyor" ≠ "tam" — kaydediciyi bağımsız tam çekimle satır sayısı kıyaslamadan canlıya alma.

**Chainlink kaydı yeniden başlatıldı (19:16Z, operatör isteği):** RTDS toplayıcı (`scripts/collect_chainlink_rtds.py`,
`data/db/chainlink_history.db`) + Chainlink Streams doğrudan kaydedici (`data/analysis/pm_chainlink_history_20260913_v1/cl_direct_rec.py`,
`data/tape_cl_direct/cld_*.jsonl.gz`, feed: spot/twap30/twap60). **Price to beat = twap60(S)**, sonuç = twap60(S+300) ≥ twap60(S).
Kimlik `~/.config/chainlink_streams/creds.env` (var; `ls | head` kesmişti, "boş" sanma). Eski CLD.log'daki "no close frame"
satırları 09-15 tarihli, yeni koşuda hata yok. Toplam 7 süreç: bot + defter + dolum kasedi + BTC tape + bosona + RTDS + Streams.

**BOT LONDRA'DA (09-19 22:24Z):** AWS eu-west-2 `ubuntu@18.135.99.14`, anahtar `~/İndirilenler/polymarket-test-key2.pem`,
venv `~/polymarket/venv` (Python 3.14; py-clob-client 0.34.6 + **py-clob-client-v2 1.1.0** — canlı mod bunu ister, `--test` istemez;
ilk başlatma bu yüzden çöktü), dizin yolu yerelle birebir (`/home/taygun/Masaüstü/polymarket/...`), `.env.live` orada (600).
Gecikme: CLOB TCP 2-3 ms, WS ilk mesaj 34 ms (TR: TCP 26 ms, emir gönderim 124 ms). Yerel `LOG_ab.jsonl` sunucudan
15 sn'de bir eklenerek senkronlanır (prefix özelliği: sunucudaki dosya yerelin kopyası + eklemeler) → yerel monitör/raporlar aynen çalışır.
**Kural:** aynı hesapta iki canlı bot asla; yerelde `ab.py --live` başlatma. Durdurmak: sunucuda `touch STOP`.
Kayıtçılar (7 süreç) yerelde kalmaya devam ediyor.
