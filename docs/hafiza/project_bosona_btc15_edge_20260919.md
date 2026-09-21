---
name: bosona-btc15-edge-20260919
description: bosona'nin BTC15 kenari olculdu - dokunusun ALTINDA (mid-3,5 kr) dinlenen tek klip +20,51 kr/pay GA[+7,5;+33,8]; dokunus +2,96 (sifir); fark icra/iptal, yerlesim degil
metadata:
  type: project
---

**Paket:** `data/analysis/bosona_btc15_edge_20260919_v1/REPORT.md` (+ `../bosona_24h_market_20260919_v1/`).

**24 saat, pazar bazli (749 pazar):** BTC15 **+$3.037** (1.), BTC5m +$2.888, BTC saatlik +$1.161,
ETH5m +$553; toplam +$8.008, +2,65 kr/pay. BTC15'te medyan pencere +6,7$, **en iyi 10 haric +69$**.

**19 gun cuzdan etiketli (XM_TRADES, 1.824 pazar, yalniz-alim hucreleri):** bosona +$3.349,
285 pazar, +9,63 kr/pay, GA **[+1.000, +6.032]** → BTC15 kenari gercek. Daha buyukler var:
0x2b5fbe8d +$15.523 (266 pazar, 402 islem, 17/18 gun), 0x7e5d2991 +$18.934 (1,2M pay, +1,57).

**MEKANIZMA (422 dolum × 25 seviyeli defter birlestirmesi):**
- **maker_below (dokunusun ALTI, medyan mid−3,5 kr, seviye sirasi 2): +20,51 kr/pay, GA [+7,5;+33,8], 16/19 gun, ex-top3 +1.464$** ← kenarin TAMAMI burada
- maker_touch (dokunus): +2,96, GA sifiri kapsiyor, ex-top3 EKSI → dokunus kotasyonu bos
- taker: +3,72 ama GA [−7,4;+13,9], ex-top3 +44$ → gurultu
- Profil: klip 50 pay, pazar basina medyan 1 dolum, cift KURMUYOR, t medyan 562 sn, markout +7,3 kr @60sn (ters secim YOK)

**NEDEN BIZ KAYBEDIYORUZ:** Haziran Family H (9.326 pazar, 3 ay) ayni yerlesimi test etti:
bid−0,02 → **−8,66 kr/pay, ters secim −28,4 puan**, dolum %54,6. Fark yerlesim degil ICRA:
bizim simulasyonda emir hic iptal edilmiyor, fiyat degince hep doluyoruz; o 285 pazarda 109 dolum
aliyor ve zehirli olanlari almiyor. Kill list zaten "icra avantaji olmadan acma" diyordu.

**09-21 16:50 TSI — KULVAR TAKIBI EKLENDI (`live_follow`, runner_v8.py):** 24 saatlik okuma:
o **+$1.344 (+7,75 kr/pay, 316 pazar, 17.338 pay)**, mirror_15m +$148 (+0,17 kr/pay, 439 pazar,
86.297 pay) → 5x hacim, 1/45 marj. BTC15'e kilitli dunyalarin onunla ORTAK PENCERESI SIFIR cunku
o kulvar degistirdi (son 24 saat: eth-5m $6.290, btc-15m $2.144; iki gunde BTC5m→BTC15→ETH5m).
Duzeltme: `runner_v8.py` her bloktan once onun kamu islemlerini 6 saatlik pencerede tarar
(tekillestirilmis), hacminin >=%10'unu ve >=100 payi aldigi kulvarlari aktif sayar, politikaya verir,
`ACTOR_LANES.json` olarak bloga yazar. Politikaya `max_market_shares=60` (onun 55 pay/pazar olcusu).
Dunyalar: follow, follow_notaker, follow_nocheap, all_lanes (kontrol). **Aktor-kosullu: kopya, kenar
kaniti degil.** Disk 363 GB, ~130 GB/gun.

**09-20 16:10 TSI — ILK TAKIP OKUMASI (live_mirror3, 00:45-09:43 UTC, 565 settle pazar):**
bosona **−$65 (−0,27 kr/pay)** · mirror_15m **−$165 (−0,45)** · mirror_btc15 −$520 (−3,03) ·
notaker −$400 · single −$184. **Isaret uyumu 0,56-0,70, korelasyon 0,39-0,43** (30-61 ortak pencere).
→ O kaybetti, biz de kaybettik: YON TAKIBI CALISIYOR; BUYUKLUK 2-12x sapiyor (onun kr/pay'i cok daha kucuk).
Operatorun olcutune gore dogru yoldayiz. Sistem: makine 12:48 UTC reboot, surecler 09:44'te olmus
(3,3 saat bosluk); capture v1 KAPALI birakildi (disk 492 GB, ~85 GB/gun → ~5,8 gun). CANLI: `live_mirror4`
(13:15 UTC aktivasyon, 4 ayna dunyasi).

**09-20 03:30 TSI — O BTC15'E KAYDI, UCUZ CIFT TAMAMLAMA AYNAYA EKLENDI:** son 90 dk hacminin
%84'u btc-updown-15m (3 saat once %34, BTC5m sifir). Olculdu: 0,20 alti alimlarin **83/94'u elinde
karsi taraf varken** (cift tamamlama), medyan t=746 sn, medyan fiyat 0,07, medyan 22 pay.
`mirror_policy.py`'ye eklendi (t>=600, seviyeler 0,12/0,07/0,03, 64 paya kadar). CANLI: `live_mirror3`
(00:45 UTC). UYARI: ayni donemde cift maliyeti **1,1107** = ciftlerden ZARAR; 64 pencerenin 19'unda
cift 0,95 altinda. Takip hedefi geregi zarari da kopyaliyoruz.

**MEKANIZMA AVI SONUCU (09-19 19:30 TSI): KENAR ICRA DEGIL YON, AMA YON KURALI BULUNAMADI.**
422 dolum/19 gun: ort.alis 0,551 · dolum anindaki mid 0,559 → iskonto sadece +0,76 kr; kazanan pay %64,2
vs mid'in ima ettigi %55,9 → **+8,30 puan YON**. Gecikme testi gecti (mid'i 10/30/60/120 sn onceden
okuyunca toplam +8,5…+9,1 sabit). Kenar GEC PENCEREDE: 9-12 dk +12,44 GA[+4,8;+20,4], 12-15 dk +21,17
GA[+7,6;+34,3]; 0-3 ve 6-9 dk eksi. Ucuz tarafta (<0,30) +11,87.
**BES HIPOTEZ ELENDI:** (1) fiyat momentumu 18 hucre sifir; (2) **Chainlink referansini TAKIP ETMIYOR —
518 isleminin yalniz %44,7'si referansla ayni yonde, 9-12 dk diliminde %20,7 = TERSINE**; (3) hareketi
fade eden dinlenen alis 15 hucre, en iyi +1,48 GA sifiri kapsiyor; (4) icra iskontosu kenarin %8'i;
(5) hiz/iptal — zehirli ve iyi dolum oncesi defter AYNI.
**ISTIKRAR UYARISI:** gunluk kr/pay −10,7…+35,8, std 13,3, 13/19 gun arti, **en iyi 3 gun haric
+1.220$/+3.057$**; son 26 saatte +3,21. Yani "kenar" ornekten ornege +3…+9 arasi oynuyor.

**/activity UCU: MERGE + REBATE GORUNUYOR (09-19, operatorun bulgusu, dogrulandi):**
`/trades` sadece BUY/SELL veriyor; `/activity` TRADE/MERGE/REDEEM/MAKER_REBATE/TAKER_REBATE veriyor.
16,5 saatlik akis: 4.635 TRADE, 183 MERGE, 672 REDEEM. **MERGE: 147 kayit, $38.735** — eslesen Up+Down'i
pencere ICINDE 1,00'e nakde ceviriyor (BTC5m medyan t=230/300 sn, 377 pay; BTC15 medyan t=755/900 sn, 207 pay),
sermayeyi geri alip tekrar kotasyon veriyor. Merge KAR'i degistirmez (cift zaten 1,00 eder) ama SERMAYE
SINIRINI serbest birakir → 9 islem/pazar boyle mumkun. **REBATE: MAKER_REBATE $525,90 + TAKER_REBATE $137,50
tek gunde** → eski "BTC5m odulu FONLANMIYOR" notu bu cuzdan icin gecersiz; gunluk ~$663 ek gelir (islem
kari +$8.008'in ~%8'i). Ayna politikasi merge'i sermaye etkisiyle modelliyor (at_risk = cost − cift).

**OPERATOR YONU DEGISTI (09-19 17:00 TSI): "kendi model uretme, bosona ne yapiyorsa aynisini yap; kar sart degil, ONUNLA BIRLIKTE hareket et".**
→ `forward_v2/mirror_policy.py` + `runner_v7.py` + `live_mirror` (aktivasyon 14:15 UTC). Her parametre olculmus: iki tarafli (81/104 pazar), mid alti merdiven 1,5/3,5/6,5 kr (109 dolumun p25/medyan/p75), klip 25 pay, t=90-860, taker kolu envanter farkini kapatir (%19), satis yok. Olcut: `forward_v2/tracking.py` → ortak pencerede onun net'i vs bizim, isaret uyumu, korelasyon. live_v9 ve v10 kapatildi.
**GOLGE DOLUM ORANI DERSI:** simulasyonum pazarlarin %68'inde dolum diyordu, gercek native motor 191 emirde 3 dolum (%1,5) verdi → XM tabanli dolum modelim COK IYIMSER. mid-2 kr daha sik doluyor ve -14,50 kr/pay kaybediyor (ters secim canli dogrulandi).

**GECE DENEYLERI (19 Eyl 02:00-05:20 UTC) SONUCU:**
- Simulator kuruldu (`sim.py`, 1.824 pencere ladder cikarimi); temel kontrol −10,14 kr/pay = Family H'yi yeniden uretti.
- **216 hucrelik izgara (zaman × derinlik × taraf × iptal kredisi): HICBIRI GA sifiri dislamıyor.** En iyi: favori/t=180/mid−5kr +2,93 GA[−0,05;+5,88], 15/19 gun.
- **Fark markout'ta:** bosona giris +6,61 → +7,32 @60sn; biz +4,33 → **−0,35** @60sn. Yerlesim ayni, dolum kalitesi farkli.
- **HIZ BU FARKI KAPATMIYOR:** iptal kurali dolumlarin %70'ini eliyor kalan sifir kazaniyor; tam cozunurluklu kaskad testinde zehirli ve iyi dolum oncesi defter BIREBIR AYNI. → **Colocation onerisi HAYIR.**
- Zayif ama dogru isaretli tek ayrim: fiyat uzerimize yuruyerek dolduran dolumlar −2,31 kr/pay, once uzaklasip geri cekilenler +1,7…+2,8 (GA'lar sifiri kapsiyor).
- Ileri golge kuruldu: `forward_v2/live_v9` (runner_v5+deep_passive), aktivasyon 19 Eyl 05:45 TSI, 15dk kulvarlari, 4 dunya. Dev kontrolde 21 emir 0 dolum → simulasyonun dolum modeli IYIMSER, golgenin ilk isi bunu olcmek.

**ESKI PLAN (kismen yapildi):** 131 gun/12.508 pencere L25 defter + bosona'nin 427 dolumu dolum
modeli CAPASI olarak → mid−δ koşusu, sonra IPTAL KURALIYLA 50/200/500 ms gecikme senaryolari.
Colocation'in fiyati = 50 ms ile 500 ms farki. Kill kosulu: 50 ms'de bile GA alt siniri <0 ise kapat.

**Why:** Kullanici "tamamen btc15'e odaklan, edgesini coz" dedi; shadow kulvari (dokunus maker)
Family H ile curutuldu ve durduruldu. Iliskili: [[project-gec-favori-curudu-20260918]],
[[project-bosona-forward-v2-live-20260918]].
