---
name: project-wave-selector-lane-20260914
description: Dalga seçici kulvarı (09-14 akşam, kullanıcı onayı): aktörlerin "hangi satış dalgasına girilir" elemesini kamu-veriyle öğrenme; kayıtçı çalışıyor, boru hattı 1 günde uçtan uca çalıştı (14.065 dalga, dolum %11, koşulsuz kenar ≈0); ≥2 gün ve kapı bekleniyor
metadata:
  type: project
---

**2026-09-14 akşam.** Kullanıcı "pes etmek kolay" dedi, plan onaylandı ("Olur"). Paket
`data/analysis/pm_wave_selector_20260914_v1/` (CONTRACT.md donuk, RUNBOOK.md, record_flow.py, build_waves.py,
add_flow.py, train.py). Canlı emir YOK.

**Fikir:** aktörlerin kenarı dalga seçimi (satıcının o an yanlış olduğunu bilmek). Bugüne kadar kimse bu elemeyi
kamu özellikleriyle MODEL olarak kurmadı; denenenler tek-özellikli filtrelerdi. Yeni özellikler: Binance perp+spot
agresör akışı (1/5/30 sn), aynı coinin 15m pazarının ikinci görüşü (5m dalga varken 15m kıpırdıyor mu), çapraz coin
mid/spot değişimi; artı dalga şekli, defter derinliği, Φ-adil − fiyat.

**Durum:** Binance akış kayıtçısı 14 Eyl 17:23Z'den beri `data/tape_flow/` (100 ms bin, fut+spot, 5 coin;
PID `flow.pid`; **fut `@aggTrade` bu makinede sessiz, `@trade` çalışıyor**; IPv4 zorlandı). Boru hattı bugünün
çok-pazar tape'inde uçtan uca çalıştı: 14.065 satış dalgası (5 coin, 5m), varsayımsal emir touch−3¢/25 pay/TTL 3 sn,
dolum %11,3, koşulsuz kenar −0,05¢ (BTC +1,27¢ 22,6k pay; altlar eksi, az dolum). Beklenen: koşulsuz ≈0.
train.py ≥2 gün ister (eşik yalnız eğitimde). Kapı: test ≥2.000 dalga, seçilenlerde gün/coin-kümeli GA>0,
ex-top3>0, iki yarı>0, seçim oranı ≥%2; kontrol = model aktör dalgalarına yüksek skor vermeli.
Geçmezse varyant yok, kulvar kapanır. Geçerse yerel dry gölge 1 hafta → Londra hız testi (dalga tepkisi 160 ms;
TR'den POST 367 ms yetmez).

**Sonraki adım:** her gün RUNBOOK sırası (fetch_binance → build_waves reparse → add_flow → train). Tape hour-15
dosyasında gzip hatası (kuyruk kayıp). İlgili: [[project-actor-breakthrough-tour-20260914]].

## EK (14 Eyl gece) — PM→Binance öncülük ölçüldü (`pm_leadlag_20260914_v1/`)
Synth'in Kalshi bulgusu Polymarket'te de var: Londra 270 pencere, PM mid'in 2 sn değişimi Binance'in sonraki 0-2 sn'sini
0,061 (t∈[0,240]: 0,100), 2-4 sn 0,037, 8-10 sn 0,008 korelasyonla öngörüyor; ters yön 0-2 sn 0,061 sonra ≈0. Kova tablosu
monoton (>5¢ PM hareketi → 10 sn'de ±0,4 bp). Kalshi Ağustos 0,173 ile aynı sınıf. Mekanizma doğrulandı: PM fiyatı Binance'in
sonraki saniyelerinin tahminini içeriyor = aktör kenarı akıştan kısa-vadeli tahmin. Doğrudan ticaret yok (0,4 bp < perp ücreti
2-5 bp). Sonuç: dalga seçici lane'in hedefi "kalabalık kadar iyi 10 sn Binance tahmini" — çıta bu.

## EK 2 (14 Eyl gece) — "erken sinyal" kaynağı = PERP (`pm_leadlag_20260914_v1/threeway.py, slopes.py, perp_jump_probe.py`)
1 saatlik kayıtçı çakışması: perp→spot 0-2 sn r=0,145; PM ile perp aynı zamanlama sınıfı (0,04-0,07 iki yön); perp
agresör dengesizliği spotu öngörüyor (0,056), PM'i değil (0,02) → kalabalık perp akışını zaten kullanıyor. |perp|≥5 bp
sonrası PM 10 sn'de +2…+4¢ sürükleniyor (alt), BTC +2,6¢. Ama taker sondası (tetik+400 ms, gözlenen ask): ask'lerin
%56'sı 400 ms içinde ortalama +9,6¢ yeniden fiyatlanmış; ücret sonrası toplam −5¢; bayat kalan %44 karışık, n küçük.
Karar: spot yerine perp px+akışı tüm adil değer girdilerine koy (kayıtta); perp-sıçrama taker'ı yalnız Londra gecikmesiyle
anlamlı; Türkiye'den yok. Gamma sonuç önbelleği `gamma_cache.json`.

## EK 3 (14 Eyl gece) — 17 GÜNLÜK DEFTER BACKTEST'İ (`ledger/build_ledger_waves.py`, `ledger/train_ledger.py`)
Dalga = aynı saniyedeki maker-alım dolumları (token/pencere), etiket = o dalganın pay-ağırlıklı (won−vwap) kenarı
(dolum-koşullu, kalabalığın dolumları), özellikler t0 = blok−4 sn'de 1 sn perp/spot akışı (1/5/30), spot getirileri,
dist, vol, derinlik vekili, satış payı; 1,48M dalga / 224M pay. Gün bölmesi 10/9.
SONUÇ: test tüm dalgalar −0,18 [−0,28;−0,09]; eğitimde seçilen en iyi %2 = +32¢ (aşırı uyum) → testte **+0,00 [−1,57;+1,85]**,
ex-top3 −1,15, yarılar −1,23/+1,81 → KAPI GEÇMEDİ. Ama sıralama var: test desil 1 −1,90 … desil 10 +0,59; alt %20 −1,45
[−1,91;−0,96] anlamlı. Kamu özellikleriyle tavan ≈ +0,6¢ (kötüden kaçınma +0,3¢). Aktör dalgalarının skoru diğerlerinden
YÜKSEK DEĞİL (−0,0003 vs +0,0022) → aktör seçimi bu özelliklerde yok. Tek-özellik quintilleri de kuruş altı.
Bir saatlik tape'teki +19/−7 ayrışması şanslı saatti. Kalan umut: ms defter (Londra 2 gün + perp aggTrades indirildi
`ledger/LONDON_PERP_100MS.parquet`) ve 15m/çapraz-coin özellikleri (çok-pazar tape'te birikiyor) — tavanın +0,6'yı geçip
geçmediği sorusu.

## EK 4 (15 Eyl 00:xx) — LONDRA ms VERİ SETİ (`london/build_train_london.py`): kalan yol da GEÇMEDİ
270 pencere (9-10 Eyl), 93.612 satış dalgası, varsayımsal emir touch−3¢/25 pay/TTL 3 sn, rcv saati, perp aggTrades
(binance-vision) 212 ms gecikmeli, 30 ms-özellik (defter, 120 ms dalga şekli, süpürme yoğunluğu, spot/perp getiri-akış, basis).
Taban −1,06¢ (12.068 dolum); aktörlerin girdiği 2.552 dalgada varsayımsal emir −2,23¢ (onların dalgasına aynı fiyattan girmek
işe yaramıyor). Zaman bölmesi 50/50: test seçili %2 → +2,07 [−6,76;+11,30], ex-top3 −3,43; quintiller monoton değil
(−0,95/−0,93/−4,28/−0,37/+1,14); aktör dalga skoru diğerlerinden yüksek değil (−0,042 vs −0,039).
SONUÇ: 1 sn (17 gün) ve ms (2 gün) çözünürlükte, perp akışı dahil kamu özellikleriyle aktör seçimi ÖĞRENİLEMEDİ; tavan
≈+0,6¢ (defter) / gürültü (Londra). Kulvarın kalan tek test edilmemiş sınıfı: 15m ikinci görüş + çapraz coin (çok-pazar
tape'te birikiyor). Kill koşulu: çok-günlü tape modelinde de aktör kontrolü düşerse kulvar kapanır; sonrası yalnız
kimlik-temelli tailgating (Londra kutusu) kalır.


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🧠 DALGA SEÇİCİ KULVARI (09-14 akşam, onaylı): aktör elemesini kamu-veriyle ML olarak kurma; Binance akış kayıtçısı çalışıyor (fut @trade, `data/tape_flow/`); boru hattı 1 günde çalıştı (14.065 dalga, dolum %11, koşulsuz ≈0); ≥2 gün + CONTRACT kapısı bekleniyor; canlı yok; EK: PM→Binance öncülük Londra'da doğrulandı (0-2 sn 0,06-0,10, 10 sn sürüyor; Kalshi 0,17 ile aynı sınıf; 0,4 bp < perp ücreti → doğrudan ticaret yok)](project_wave_selector_lane_20260914.md)
