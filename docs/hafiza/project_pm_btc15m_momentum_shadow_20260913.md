---
name: pm-btc15m-momentum-shadow-20260913
description: Polymarket BTC15m momentum kuralının YERELDE (Türkiye) gölge ölçümü — 13 Eyl 00:42Z başladı, systemd user servisi pm-btc15m-momentum-shadow, para/anahtar yok; 3 eşik × 2 klip yan yana; Tokyo 12 Eyl 23:58Z TERMINATE edildi, 13 GB yedek tek kopya
type: project
---

# PM BTC15m momentum gölgesi (yerel) — 2026-09-13

Klasör: `data/shadow/pm_btc15m_momentum_20260913_v1/` (shadow.py, readout.py, README.md, windows/).
Servis: `~/.config/systemd/user/pm-btc15m-momentum-shadow.service` (enabled, Restart=always,
MemoryHigh 400M, gizli env değişkenleri UnsetEnvironment ile siliniyor). Başlangıç 2026-09-13 00:42Z.

**Neden yerel:** backtest'te emri 60 sn geç vermek sonucu bozmuyor (10bp'de +$11,5 → +$16,4/gün),
sinyal sonrası ask ortalama −0,64c hareket ediyor → hız yarışı değil. Tokyo'ya gerek yok.
Binance spot ws Türkiye'den 1 sn'de bağlanıyor, 146 ms gecikme; fstream (vadeli) ws bu denemede
bağlanmadı, spot kullanıldı (sinyal göreli hareket olduğu için bazis farkı önemsiz).

**Kural:** t=pencere+60s, move=1e4·ln(spot/strike); |move| ≥ eşik ise o yönü en iyi ask'ten al,
sonuca kadar tut. Ücret 0,07·p·(1−p). Eşikler 5/10/20 bp ve klipler 100/300 pay AYNI ANDA kaydediliyor
(sonradan seçim yapılmıyor, hepsi önceden yazıldı). Dolum, görünen seviyeler yürünerek hesaplanıyor.

**Kayıt:** her pencere (sinyalsizler dahil) `windows/<gün>.jsonl`; Polymarket resmi sonucu VE Binance
türevi sonuç ayrı ayrı yazılıyor (Polymarket çözünürlüğü Chainlink BTC-USD TWAP-60s, Binance değil →
uyum oranı ölçülüyor). Okuma: `python3 readout.py`.

**Beklenti (backtest):** 100 pay ile ~$11,5/gün, 300 pay ile ~$11/gün; 10bp'de günde ~5 işlem.
Kapasite sınırı: sinyal anında en iyi ask medyan 170 pay. 2 hafta sonra gerçek rakam backtest'in
belirgin altındaysa veya sıfıra yakınsa kulvar kapanır.

**Tokyo:** i-03234a5b5d5423cb3 kullanıcı tarafından 2026-09-12 23:58Z TERMINATE edildi, disk de silindi.
`data/tokyo_backup_20260911/` (13 GB, 191.970 dosya) artık TEK KOPYA; cüzdan SQLite 404 intent, integrity ok.


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🌗 PM BTC15m MOMENTUM GÖLGESİ (09-13 00:42Z, YEREL/Türkiye): para ve anahtar yok, 3 eşik × 2 klip, 2 hafta ölçüm; Tokyo TERMINATE, 13 GB yedek tek kopya](project_pm_btc15m_momentum_shadow_20260913.md)
