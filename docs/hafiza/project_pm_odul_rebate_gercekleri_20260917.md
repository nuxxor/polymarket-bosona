---
name: project-pm-odul-rebate-gercekleri-20260917
description: PM likidite odulleri BTC 5m'de FONLANMIYOR (rates null); min qualifying size 50 pay (bizim klip 5); maker rebate 20% aktif, tavan 0,35 kr/pay -> "olcegi buyut rebate'ten kazan" plani bu sayilarla calismaz
metadata:
  type: project
---

# PM ODUL/REBATE GERCEKLERI (09-17, resmi dokuman + API ile dogrulandi)

Kaynak: docs.polymarket.com/programs/liquidity-rewards, /programs/maker-rebates,
/trading/market-making + gamma & clob API canli sorgu.

## 1. LIKIDITE ODULLERI — BIZIM PAZARDA SIFIR
- `btc-updown-5m`: `clobRewards = null`, clob `rewards.rates = null` -> FONLANMIYOR.
- Karsilastirma kontrolu: `xi-jinping-out-before-2027` -> `rates:[{rewards_daily_rate:300}]`
  DOLU geliyor. Yani alan fonlanınca doluyor; bizimkinde gercekten para yok.
- Dokuman teyit ediyor: Agustos'taki **$1M kripto TWAP odul programi BITTI**
  ("This program has ended. The August allocation is no longer active.").
- Ayar yine de duruyor: **rewardsMinSize=50 pay, rewardsMaxSpread=4,5 kurus**
  (btc/eth, 5m ve 15m hepsinde ayni).
- **BIZIM KLIP 5 PAY = nitelik esiginin 1/10'u.** Bu kulvarda attigimiz hicbir emir
  likidite odulu icin hic sayilmadi. (Fonlu olsa bile sayilmazdi.)

## 2. SKOR FORMULU (fonlu pazarlar icin, ileride lazim)
- `S(v,s) = ((v-s)/v)^2 * b`  (v=max spread, s=ayarlanmis mid'e uzaklik)
- `Q_one = S*BidSize_m + S*AskSize_m'` ; `Q_two = S*AskSize_m + S*BidSize_m'`
- mid 0,10-0,90 arasi: `Q_min = max(min(Q1,Q2), max(Q1/c, Q2/c))`, c=3 (tek taraf 1/3 puan)
- mid <0,10 veya >0,90: `Q_min = min(Q1,Q2)` -> **ZORUNLU cift taraf**
- ONEMLI: defter AYNALI oldugu icin bizim "Up bid + Down bid" yapimiz zaten
  Q_one ve Q_two'nun IKISINI de besliyor -> tam cift-taraf orani. Yapi dogru,
  eksik olan tek sey BOY (50 pay) ve FON.
- Gunluk, UTC gece yarisi dagitim; min $1 odeme.

## 3. MAKER REBATE — AKTIF, AMA TAVAN DUSUK
- `feesEnabled=true`, `feeSchedule={rate:0.07, takerOnly:true, rebateRate:0.2}`
- `fee_equivalent = C * feeRate * p * (1-p)`, `rebate = payin/toplam * havuz`
- Kripto rebate orani **%20**; maker ucreti 0. Minimum boy YOK, gunluk $1 esigi var.
- Tavan: 0,20 * 0,07 * 0,25 = **0,35 kr/pay** (p=0,5'te; uclarda cok daha az).
- **Olcumlenen kaybimiz -3,24 kr/pay.** Rebate bunun ~%11'ini kapatir.
  -> "Basabas olsak bile boyu 4-5 kat buyutup rebate'ten kazaniriz" plani
  BU SAYILARLA CALISMAZ: rebate pay basina sabit, kayip da pay basina sabit;
  olcek ikisini de ayni oranda buyutur. Once pay basina kenar >= -0,35 olmali.

## 4. DOKUMANDAN CIKAN ISE YARAR TEKNIK MADDE
- "Submit related price levels as a **batch**"; "her emir BAGIMSIZ degerlendirilir,
  batch'i tek basari/basarisizlik gibi ele alma" -> SDK'da `post_orders(args,
  post_only=True)` ve `cancel_orders(hashes)` var. Sirali gonderim post-only
  reddimizin muhtemel sebebi (Up konurken defter kayiyor). v3 batch'e gecti.
- Emir duzenlenemez: iptal + yeniden gonder.
- Envanter: split/merge/redeem dongusu; cikarken "complete set"leri merge et.

## 5. YENI KULVAR IZI (kovalanmadi, tetik yazildi)
Fonlu odul pazarlari VAR: ornek `xi-jinping-out-before-2027` gunluk $300,
min_size 200, max_spread 3,5. Bu 5dk kripto isinden TAMAMEN farkli bir is
(yavas pazar, 200 pay cift taraf, mid'e 3,5 kurus). TETIK: 5dk kulvarinda
pay basina kenar >= -0,35'e cikmazsa, fonlu odul pazarlarinin taranmasi
(gunluk rate / rekabet eden Q_min toplami / envanter riski) sonraki hamle.
