---
name: project-bosona-btc5m-gun-ve-cift-20260919
description: "bosona BTC5m gün-bazlı zincir PnL (19/19 gün artı, +2,27 kr/pay, ~110k pay/gün), bugün +0,12 dip gün; işlem PnL'i tamamen ÇİFT MALİYETİ ile açıklanıyor; rebate günde $663 (maker 526 + taker 138); bacak anatomisi; /activity 5.000 olay sınırı"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0e095c2e-d109-4b41-8066-a0b2005c3a13
  modified: 2026-09-19T17:20:32.205Z
---

# bosona BTC5m — gün dağılımı ve çift maliyeti (2026-09-19, polymarket-d1)

**Zincir defteri (FILL_PARTY_LEDGER, 14 Ağu–1 Eyl, ücretler dahil):** 4.074 pencere, 2,12M pay,
**+$47.518, +2,27 kr/pay ort (medyan +1,36, std 2,12), 19/19 gün artı**, günlük +0,26…+6,91 kr/pay,
günde 55-170k pay (~550 pay/pencere), taker payı %7-27, ücret 19 günde $4.769.

**Bugün (09-19, /activity, 187 pencere, 104k pay): +$121 = +0,12 kr/pay** → dağılımın dibi.
12:16Z sonrası tek başına −$806. Saatlik ±$450 salınıyor → **Polygonscan bakiyesine gün-gün bakarak
yargı verilmez**, günlük varyans büyük.

**Rebate (activity'de MAKER_REBATE / TAKER_REBATE, her gece 00:10-00:45Z, TÜM pazarlar):**
$525,90 + $137,50 = **$663/gün**, varyanssız. Bugün gibi bir günde 5m gelirinin tamamı bu.

**İşlem PnL'inin tek açıklayıcısı ÇİFT MALİYETİ (bugün, pencere-düzeyi):**
| çift maliyeti | pencere | kr/pay | PnL |
|---|---|---|---|
| <0,85 | 52 | **+10,02** | +$3.114 |
| 0,85-0,95 | 26 | +2,45 | +$373 |
| 0,95-1,00 | 16 | +0,83 | +$89 |
| 1,00-1,10 | 25 | −1,90 | −$366 |
| >1,10 | 38 | **−13,90** | −$2.759 |

**Bacak anatomisi (medyan):** 1. bacak her grupta aynı: ort 0,53 @ t≈80 s (ilk alım t≈10 s).
Fark 2. bacakta: ucuz çiftte **0,19 @ t188** (fiyat savrulunca ölen tarafı topluyor; 30/52'de bir bacak <0,20),
pahalı çiftte **0,78 @ t143** (ters savrulmada zararı kilitlemek için pahalıya kapatıyor — taker rebate'i
de bunu gösteriyor). "Son 60 sn" payı her grupta %0 medyan → 09-18'deki "son 60 sn'de 5-14 kuruşa toplama"
o 3 saatin özelliğiymiş; 0,847 çift maliyeti de öyle (bugün medyan 0,958).

**Vol kapımız onun için tutmuyor (bugün):** önceki-5dk menzil [8,15) +2,39, [15,25) −10,55 (14 pen), [0,8) −0,18.
Küçük n; vol kapısı KENDİ dolumlarımız için doğrulandı, onun için değil.

**Ölçek:** aynı 1-2 kr/pay kenar bizim 5-10 pay/pencerede $1-2/gün eder; onun $2.500/gün'ü boydan geliyor.

**Sıradaki (A1):** tam dolum kasedi + canlı defterle onun 2. bacak dolumları kısmi mi (kuyrukta önde) yoksa
süpürme mi; bizimkiyle yan yana. `scripts/izleme/kuyruk.py` hattı + `data/tape_fills/` (backfill dahil).

**API sınırı:** data-api `/activity` offset ≤5.000 (400 döner) → ~18 saat geriye gidiyor; uzun geçmiş için zincir.
İlgili: [[project-bosona-cift-maliyeti-cozuldu-20260918]], [[project-devir-ve-ortam-20260919]], [[project-vol-kapisi-20260919]]

## A1 SONUCU (17:35Z) — KUYRUK ÖNÜ, SÜPÜRME DEĞİL
`scripts/izleme/bacak_anatomisi.py` (kaset tekil + tx içi rol: en büyük satır = taker; defterle **tx-hash hizalı**,
zincir ts CLOB'dan medyan 2,8 sn sonra gelir, hash yoksa −4,5 sn). 15:15Z'den, BTC5m maker BID dolumları:
- **HERKES: 29.332 dolum, %81 KISMİ** (seviye süpürülmüyor, dolan = kuyruğun önündeki). "Yalnız süpürülünce doluyoruz" modeli YANLIŞ.
- **bosona: 39 dolum, %90 kısmi, önünde medyan 578 pay, seviye yaşı medyan 3,2 sn (p25 0,3 sn), px 0,47, t=83 sn.**
  685 paylık seviyeden 5 pay alıyor = kuyruğun EN ÖNÜNDE. Seviye yaşı = seviyenin >0 olduğu süre = ilk emir onun.
  Yani taze oluşan dokunuşa-yakın seviyelerde İLK o var; arkasına 3 sn içinde 500+ pay diziliyor.
  Yaş dağılımı (pay): <1 sn 61 | 1-10 sn 512 | 10-60 sn 231 | >60 sn 21 → **re-quote hızı yarışı**, erken yerleşim değil.
- **BİZ (0xfcdc…): 19 dolum, %68 kısmi, önde medyan 60, seviye yaşı medyan 470 sn, px 0,20, t=62 sn** → derin, eski, ucuz
  seviyelerde doluyoruz (ters seçim bölgesi); onun oyunu taze seviyede önde olmak.
- Colocation sorusu artık somut: gecikme bu mekanizmada SAYAR (seviye oluşumundan sonra ilk ~100-300 ms).
  Eski "kaskad testi → colocation hayır" sonucu bizim dolum profilimiz içindi, bosona'nın profili için değil.

## KOL C "TAZE SEVIYE" CANLI (09-19 21:00Z, operatör: "canlıda çözelim")
`ab.py` sha 0459eae11d1a, ön kayıt `ONKAYIT_TAZE_KOL_C_20260919.md` (v1.0 kural, v1.1 yenileme, v1.2 WS okuyucu).
Atama: C %50, A/B %25/%25 (tohumlu). C: websocket defter; spread ≥2 tik → bb+1 tik (seviyeyi biz kurarız),
spread 1 tik → bb'ye yalnız seviye ≤30 pay ise; bant 0,15-0,60; t∈[3,200); taraf başına tek 5 paylık emir;
dokunuşun ≤1 tik altındaysa yerinde kalır, 2+ tik geride kalınca iptal; p+q≥1 çapraz engeli; ≥1 sn/taraf; ≤60 post/pencere;
TARAF_TAVAN $10, DENGE 10 pay, kesici −100. Vol kapısı KAPALI (operatör 19:09Z).
Kuru koşularda: 33-46 post/pencere (fiyat hızlı kayınca), WS "1013 slow consumer" → okuyucu ayrı iş parçacığına alındı, 0 hata.
KILL: 60 dolumlu C penceresi sonunda C kr/pay ≤ (A+B) − 2 → C kapanır. Mekanizma ön koşulu: C dolumlarının kısmi oranı ≥%80, seviye yaşı <10 sn.
Bot 20:58:52Z STOP'ta PnL −$15,34 (19:10Z kapısız yeniden başlatmadan beri ~−$24).

## bosona GECE DAVRANIŞI (09-19 21:40Z → 09-20 00:10Z, operatör gözlemi + veri)
21:39:26Z'den sonra BTC5m'de HİÇ işlem yok (kaset 101 dolumda sabit, activity 0 satır); aynı sürede BTC15m'de
52 işlem / 2.853 pay, 90 dk nakit akışı +$2.063, ETH günlük +$304. Yani gece (Cumartesi 21:40Z+) 5m'e girmiyor,
15m'e odaklanıyor — muhtemelen hacim/oynaklık eşiği (5m gece cumartesi sakin). Sonuç: 5m kıyası GÜNDÜZ aynı
saatlerde yapılmalı; gece C'nin 5m'de tek başına kalması "onu geçtik" demek değil.
Denetim 2 (b471fab) kabul edilen tespitler: Londra sonrası +10,65'in 9,75'i TR'de açılmış B pencereleri;
Londra-başlangıçlı 13 pencere +0,90; kabul edilen 56 C emrinin 1'i spread içi/27 dokunuş/28 altında.
v4.1 ile kapatılanlar ve deney adayları D1-D5: `ONKAYIT_TAZE_KOL_C_20260919.md`.
