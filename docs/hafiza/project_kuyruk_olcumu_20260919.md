---
name: project-kuyruk-olcumu-20260919
description: 09-19 ilk DOGRUDAN kuyruk pozisyonu olcumu — 5 paylik emrimizin onunde 383-3692 pay var; defter kaydedicisi calisiyor, olcum hatti kuruldu
metadata:
  type: project
---

# KUYRUK POZISYONU — ILK DOGRUDAN OLCUM (2026-09-19)

## NEDEN ONEMLI
Gunlerdir "son olculmemis mekanizma" dedigim sey. Daha once olculemiyordu
cunku defter (orderbook) verimiz yoktu. 09-19 15:15Z'de
`scripts/record_polymarket_orderbook.py` baslatildi (PM market websocket:
book snapshot + price_change delta + last_trade_price, SQLite).
DB: `data/db/polymarket_orderbook.db` (market_events tablosu).

## ILK OLCUM (12 emir, dogrulama orneği — ama KUYRUK DERINLIGI bir OLCUM,
## sonuc degil; kucuk ornek sorunu yok)
BIZIM 5 PAYLIK emrimizin ONUNDE duran pay:
    0.20 ->   515      0.09 -> 1,199
    0.16 ->   502      0.06 ->   844
    0.12 ->   383      0.03 -> 3,692
MEDYAN 710 pay.

## ANLAMI
5 pay, 500-3700 payin ARKASINDA. Biz ancak seviyenin TAMAMI supurulunce
doluyoruz = fiyat oradan gecip giderken = tam olarak kaybettiren durum.
Bu, "dolum duzeyinde kenar var ama bizde yok" bilmecesinin (4+ kez
tekrarlandi) mekanik aciklamasi olabilir.
Hafizadaki bosona notuyla ortusuyor: o seviyenin %15'i / son boyun %48'i =
kuyrugun ONUNDE; biz ARKASINDA. Bkz [[project-hayatta-kalma-yanilgisi-20260917]]
("Kenar hucrede degil, hucrede ONCEDEN duruyor olmakta").

## OLCUM HATTI
`scratchpad/kuyruk.py <utc_ms>` — kendi LOG'umuzdaki emirleri (COZULDU
icindeki emirler: oi, p, pay, gecikme_ms) defter kaydiyla eslestirir:
son `book` snapshot + ona kadarki `price_change` deltalari ile emri
koydugumuz andaki BID boyunu kurar. Cikti: onumuzdeki paya gore dolum orani,
kola gore, basamaga gore.
Saatlik kalici olcum calisiyor (Monitor).

## HENUZ BILINMEYEN
- Dolum orani ile onumuzdeki pay arasindaki iliski (ornek yetersiz, gece birikecek)
- Kuyrugun INCE oldugu (fiyat, zaman) hucreleri var mi -> varsa somut kaldirac
- bosona'nin kuyruk pozisyonu ayni yontemle olculebilir mi (kamu veride emir
  sahibi gorunmuyor; ancak DOLUM sirasindan dolayli cikarim denenebilir)
