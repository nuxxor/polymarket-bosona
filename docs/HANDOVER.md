# HANDOVER — Polymarket BTC 5dk maker kulvari
**Yazildi:** 2026-09-19 ~16:40 UTC · **Onceki oturum:** Opus 5

Bu belge, devralan oturumun **once bunu okuyup** sonra is yapmasi icin.
Hicbir sayi hafizadan yazilmadi; hepsi loglardan/olcumlerden alindi.

---

## 0. TEK CUMLE
BTC 5dk Up/Down pazarinda iki-tarafli derin maker merdiveni calistiriyoruz;
bugun **pencere secimi** (BTC oynaklik kapisi) adli ilk ornek-disi dogrulanmis
bulguyu canliya aldik, ve **kuyruk pozisyonu**nu ilk defa olcmeye basladik.
Kulvarin karli oldugu KANITLANMADI; canli PnL hala gurultuden ayrismiyor.

---

## 1. CALISAN SURECLER (hepsi arka planda, `setsid nohup`)

| surec | PID* | ne yapar | cikti |
|---|---|---|---|
| `ab.py --live` | 3436703 | CANLI BOT (gercek para) | `data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl` |
| `scripts/record_polymarket_orderbook.py` | 3404951 | PM defteri (book+delta+son islem) | `data/db/polymarket_orderbook.db` |
| `scripts/record_fills_tape.py` | 3485227 | **cuzdan etiketli TUM dolumlar** (btc/eth/sol/xrp 5dk) | `data/tape_fills/fills_YYYYMMDD_HH.jsonl` |
| `scripts/record_btc_tape.py` | 3478024 | BTC fiyat (Binance aggTrade + 1sn mum) | `data/tape_btc/btc_YYYYMMDD_HH.jsonl.gz` |
| `scratchpad/bosona_kayit.py` | 3474964 | bosona `/activity` surekli kayit | `data/bosona_canli/activity.jsonl` |

*PID'ler bu oturuma ait; once `ps -eo pid,etime,args | grep -E "ab.py --live|record_"` ile DOGRULA.

**Monitor'ler (oturum omurlu, devralanda OLMAYACAK — yeniden kur):**
- A/B skorkarti (30 dk) — `scratchpad/ab_skor.py <utc_ms>`
- Kuyruk olcumu (saatlik) — `scratchpad/kuyruk.py <utc_ms>`
- BIZ vs BOSONA saatlik ozet — `scratchpad/yanyana_saatlik.py`
- Bot problem sinyalleri (kesici/cokme/API)

> NOT: scratchpad `/tmp/claude-1000/.../b4197893-.../scratchpad/` altinda ve
> OTURUMA OZEL. Kalici olmasi gereken betikleri `scripts/` altina tasi.
> Bugun bir betik tam bu yuzden kayboldu (eski tape recorder, 13,5 saat veri kaybi).

---

## 2. CANLI BOT — YAPILANDIRMA (logdan, `SURUM` + `hazir` olaylari)

```
kaynak_sha      be84f831cb2b        klip           5.0 pay
vol_kapisi      True                kesici         -100.0
vol_esik        15.0 bps            denge_siniri   10.0
a_oran          0.5  (A/B %50-%50)  px_tavan_maker 0.40
gec_kes         200.0               kapi (eski)    False
ucuz_esik       0.25  (KOL A)       tamamla_acik   False
gec_ust         0.10  (KOL B)       boy_testi      False

KOL A (kontrol): FIYATLAR   = [.34 .30 .26 .22 .20 .16]  t>=200'de px<=0.25 iptal
KOL B (deney)  : FIYATLAR_B = [.20 .16 .12 .09 .06 .03]  t>=200'de px>0.10  iptal
```

**Testler: 79/79 geciyor** (`python3 ab.py --test`). Kuru kosu: `python3 ab.py`
(ayri log/state'e yazar, canliya BULASMAZ — bu bugun duzeltildi).

**Durdurma:** `touch STOP` → bot tum acik emirleri IPTAL EDER, pencereleri
cozer, mutabakat yapar, state kaydeder, cikar. **`kill` KULLANMA** — yeniden
baslatmada acik emirler "kapali" isaretlenir ve borsada YETIM emir kalir.

---

## 3. CANLI SONUC (durust, sishirilmemis)

```
16:34Z  PnL $+8.76 | risk $0.00 | 24 pencere | 350 pay

Izgara v2 donemi (13:30Z sonrasi):
  kol A:  29 pen | 315 pay | $+7.70 | +2.44 kr/pay
  kol B:   7 pen |  70 pay | $+0.95 | +1.36 kr/pay
  TOPLAM: 36 pen | 385 pay | $+8.65 | +2.25 kr/pay
  pencere-bootstrap GA95: [-11.68, +15.56]   <- SIFIRI KAPSIYOR
  artida biten pencere: 8/36
```

**UYARI (onemli):** 15:11'de PnL $27.85'ti, 16:34'te $8.76. O tepe noktasinin
%103'u IKI pencereden geliyordu; sonrasinda geri verdi. **Bu rakamlara bakarak
karar alma.** Kol basina ~100+ pencere gerekiyor.

Gece kosusu icin kiyas: **09-18 23:37 → 09-19 12:34, 144 pencere, -$42.85,
-2.02 kr/pay** (izgara [.40 .30 .22 .15 .10 .06 .03], gec_kes 200/0.25).

---

## 4. BUGUN AYAKTA KALAN TEK BULGU — VOL KAPISI (fikir KULLANICIDAN geldi)

Kullanici sordu: *"kar 2 pencerede yogunlasmis, kazanan pencereleri onceden
bulup orada emir koysak?"* — dogru cikti.

```
Zincir defteri, 3.913 pencere / 17 gun, gun-kumeli GA:
  oynaklik kaliciligi (onceki 5dk BTC menzili -> pencere ici menzil): Spearman +0.676
  KOL A  kapisiz +0.48 [-0.26,+1.28]  ->  vol5>15 bps: +1.67 [+0.49,+2.75]
  KOL B  kapisiz +0.88 [+0.12,+1.59]  ->  vol5>15 bps: +1.69 [+0.59,+2.62]
  ORNEK DISI: esik ilk yarida ogrenildi -> EGITIM farki +2.21 | TEST farki +2.09
```

Egitim ve test farkinin ayni olmasi kritik: bugune kadar curuyen her fikir tam
burada cokuyordu. **Bu, bugun ornek-disi testi gecen TEK bulgu.**

**Canli dogrulama (15:47Z sonrasi, 10 karar):**
```
acilan 4 (vol 29.5 / 21.4 / 27.0 / 22.9)
atlanan 6 (vol 6.7 / 10.1 / 10.1 / 6.4 / 8.7 / 12.3)
atlama orani %60  (zincir verisinde beklenen ~%61 — ortusuyor)
```

**Neden daha once bulunamadi (kritik ders):** Kodda bu kapi ZATEN vardi
(`onceki_oynaklik()` + `ESIK_BPS=16.4`) ve olcum DOGRUYDU. Yanlis olan EYLEMDI:
sakin pencerede **durmak yerine KOL DEGISTIRIYORDU**. Yani kaybettiren
pencerelerde oynamaya devam ediyordu. 09-19'da "IPW ile curudu" diye
kapatmistim — curuyen sinyal degil, ona bagladigim eylemmis.
→ playbook #64.

**On kayit:** `data/analysis/pm_merdiven_ab_20260918_v5/ONKAYIT_VOL_KAPISI_20260919.md`
**KILL kosulu:** 200 acilan pencere sonunda (acilan kr/pay − atlanan kr/pay) ≤ 0 → kapi kapanir.
Atlanan pencereler `vol_atla` olayiyla golge kaydediliyor, kamu veriden degerlendirilecek.

---

## 5. ACIK OLAN ASIL SORU — KUYRUK POZISYONU

Gunlerdir "son olculmemis mekanizma". Bugun ILK DEFA olculebilir hale geldi
(defter kaydedicisi 15:15Z'de basladi).

**Ilk sonuc (81 emir / 10 pencere — AZ, ama yon net):**
```
ONUMUZDEKI PAY     emir   dolan   dolum %
100-499              37      8     21.6%
500-1999             34      6     17.6%
2000+                10      0      0.0%

kol A:  21 emir | dolum %23.8 | medyan onde 355 pay
kol B:  60 emir | dolum %15.0 | medyan onde 631 pay
```

5 paylik emrimiz 355-631 paylik kuyrugun arkasinda. **Biz ancak seviyenin
TAMAMI supurulunce doluyoruz** = fiyat oradan gecip giderken = kaybettiren durum.

Beklenmedik bulgu: **derin izgara (kol B) kuyrugu KISALTMIYOR, UZATIYOR.**

**Olcum hatti:** `scratchpad/kuyruk.py <utc_ms>` — bot logundaki emirleri
(COZULDU icindeki `emirler`: oi, p, pay, gecikme_ms) defter kaydiyla eslestirir.

**Siradaki soru:** kuyrugun INCE oldugu (fiyat, zaman) hucreleri var mi?
Varsa ilk somut kaldirac; yoksa tavan orada.

---

## 6. BUGUN CURUYEN FIKIRLER (hicbiri canliya girmedi — tekrar denemeyin)

1. **bosona'nin pahali bacagini kopyalamak** (0.80/0.02 cifti).
   Pencere duzeyinde onun **zarari**: bir bacagi >=0.80 olan 544 penceresi
   **-11.50 kr/pay**; ikisi de <0.80 olan 1.722 penceresi **+3.24**.
2. **Sig izgara (kol C, [.46..26])** — kurmadan once olculdu:
   -0.83 [-1.66,-0.05], maruziyet $17.30. Gercek dolumlar da ayni yonde
   (cuzdanin en yuksek alimi 0.35-0.45 ise -2.11, 0.45-0.55 ise -1.16).
3. **"Gec cift kurmak kazandirir" (+6.79)** — SECIM ARTEFAKTI. Olen tarafi
   0.05'ten ancak ilk bacagin kazaniyorsa alabilirsin. Marjinal dolum duzeyinde
   t>=200 & px<=0.25: karsi taraf VAR -0.08, YOK +0.02 = SIFIR.
4. **"Iki bacak da <=0.40 olanlar +13.55"** — ayni artefakt.
5. **Simulasyonun -19.74'u** ("pahali bant imkansiz") — GERI CEKILDI.
   Gercek dolum verisi ayni bantta **-1.42** diyor. 18 puan artefakt:
   simulasyon "fiyat degdigi her an dolarsin" varsayiyor.

---

## 7. YAPISAL TAVAN (bunu bilmeden plan yapma)

30 hucrelik (fiyat x zaman) haritasi, bizim kisit sinifimiz
(cuzdan-pencerede hic >0.40 alim yok), 1.406.171 dolum / 21,3M pay / 19 gun,
gun-kumeli GA:

**Taban -0.39 kr/pay. 30 hucrenin HICBIRI artida sifirdan ayrismiyor. 7'si
EKSIDE ayrisiyor.** En iyi (notr) bolge: px 0.00-0.10 @ t120-240.

Yani izgara ayariyla bu tavan asilmiyor. Vol kapisi tavani degistirmiyor,
sadece en kotu pencereleri eliyor.

**bosona karsilastirmasi (zincir-kesin, 19 gun, 1,78M pay):**
```
pencere tamamen <=0.40 (BIZIM OYUN):  -3.53 kr/pay   <- O DA kaybediyor
pencerede >0.40 alim VAR           :  +1.51 [+0.43,+2.64]
```
Ucuz bacak ancak pahali bacagin yarisi olarak karli; tek basina eksi.

---

## 8. VERI VARLIKLARI

| ne | nerede | kapsam |
|---|---|---|
| Zincir-kesin dolum defteri (rol etiketli, ucretler zincirden) | `data/analysis/btc5m_top_actor_hunt_20260902_v1/FILL_PARTY_LEDGER/{maker,taker}.parquet` | 14 Agu - 1 Eyl, 19,2M satir |
| Pencere kazananlari | `data/analysis/pm_ayni_fiyat_20260917_v1/hunt_kazanan.json` | ayni donem |
| BTC fiyat gecmisi (Chainlink, saniyelik) | `data/analysis/pm_chainlink_history_20260913_v1/HIST_spot.parquet` | 16 Agu - 2 Eyl, 1,33M satir |
| PM defteri (CANLI) | `data/db/polymarket_orderbook.db` | 19 Eyl 15:15Z → |
| Cuzdan etiketli dolumlar (CANLI) | `data/tape_fills/` | 19 Eyl 16:36Z → |
| bosona activity (CANLI) | `data/bosona_canli/activity.jsonl` | 19 Eyl 12:16Z → |
| BTC tape (CANLI) | `data/tape_btc/` | 19 Eyl 16:29Z → |

Disk: ~558 GB bos. Yeni kayitlar toplam ~2-3 GB/gun.

---

## 9. KAMU VERIDE OLMAYAN (kapatilamaz)
- Duran emirler (defter ANONIM — kimin emri oldugu yazmaz)
- Iptaller
- Emir sahipligi / kuyruk sirasi

**Tek dolayli yol:** defter (kuyruk derinligi) + cuzdan etiketli dolumlar
(kim doldu) birlesimi → "seviye supuruldugunde kim onceydi" cikarilabilir.
Bu veri bugun toplanmaya BASLADI, henuz analiz edilmedi.

---

## 10. DEVRALAN ICIN ILK 30 DAKIKA

1. `ps -eo pid,etime,args | grep -E "ab.py --live|record_"` → 5 surec ayakta mi?
2. `tail -5 data/analysis/pm_merdiven_ab_20260918_v5/LOG_ab.jsonl` → bot yaziyor mu?
3. Monitor'leri yeniden kur (bolum 1) — oturum omurlu, dustuler.
4. Gece verisi biriktiyse SIRASIYLA:
   - **Kapi testi:** acilan vs atlanan pencerelerin kr/pay'i (KILL kosulu)
   - **A/B:** kol A vs kol B, pencere-bootstrap GA ile
   - **Kuyruk:** `scratchpad/kuyruk.py` — dolum orani vs onumuzdeki pay
5. Hicbirinde ornek yetersizse **DOKUNMA, BEKLE.** Bugun iki kez ust uste
   restart yapip ~2 pencere kaybettik.

---

## 11. DISIPLIN (bugun ogrenilenler — `RESEARCH_DISCIPLINE_PLAYBOOK.md`)

- **#61** "Basarili olanlar sunu yapiyor" → once SECIM ARTEFAKTI diye oku.
  Grubu tanimlayan sey sonucun fonksiyonuysa, sayi gecersiz.
- **#62** Modelin ONGORU BECERISI kanitlanmadan model KAZANAN'i kapatamaz.
  (Simulasyon v2 icin +0.19 dedi, canli +14.2 verdi → A/B'ye gecildi.)
- **#63** Bir kolun iki degisikligi ayrilamiyorsa PAKET oldugunu on kayitta yaz.
- **#64** DOGRU OLCUM + YANLIS EYLEM = "curumus" gibi gorunur. (Vol kapisi.)
- **#65** Kalicilik olcerken OLCUTUN KENDISI dongusel olmasin. (Savrulmayi
  Polymarket islemlerinden olcunce +0.048, BTC'den olcunce +0.676.)
- **#66** `pkill -f` ASLA kendi komut satirinla ayni pakette olmasin.
  Bugun 3. kez; bu sefer SESSIZ zarar verdi (heredoc calismadi, eski bozuk
  betik diskte kaldi, 5 dk bos kayit).

**Degismeyen kurallar:** on kayit koddan ONCE (#52); strateji karari
CUZDAN-PENCERE biriminde (#58); GA sifiri kapsiyorsa "curudu" degil "gucsuz".

---

## 12. BUGUN CANLIDA BULUNAN VE KAPATILAN HATALAR
1. **`yenile` fonksiyonu** kol B'yi sabit derin izgaraya cevirdikten sonra hala
   "mid'i takip et" yapiyordu → ilk B penceresinde 12 derin emri iptal edip
   mid'e `Down@0.40` koydu ve doldu. KAPATILDI + regresyon testi.
   *(15:15Z penceresi bu yuzden A/B analizinde KIRLI sayilmali.)*
2. **Acilis kapilari** tek denemede pes ediyordu → 999 hiz limitinde 4 kez
   ust uste BASLAMIYOR, bot 4 dk kapali (15:20 penceresi kacti). Sinirli
   tekrar eklendi (6 deneme, artan bekleme); fail-closed KORUNDU + test.
3. **Denetim boslugu:** acilan pencerelerin vol'u loglanmiyordu; Binance sadece
   son 12 dk'yi verdigi icin geriye donuk hesaplanamazdi → KILL olcutu
   olculemez hale gelirdi. Duzeltildi.

---

## 13. DURUST DEGERLENDIRME
- Kulvarin karli oldugu **kanitlanmadi**. 30 hucrelik harita yapisal bir tavan
  gosteriyor ve canli PnL gurultuden ayrismiyor.
- Bugun **bir** fikir ayakta kaldi (vol kapisi, ornek-disi dogrulandi) ve
  **bes** fikir curudu — ucu para harcanmadan, olcum sayesinde.
- En umut verici acik yol: **kuyruk pozisyonu**. Ilk defa olculebiliyor.
  Kuyrugun ince oldugu hucreler varsa kaldirac var; yoksa tavan kesinlesir.
- Kullanici park kararini acikca reddetti (09-19). Kulvar ACIK.
