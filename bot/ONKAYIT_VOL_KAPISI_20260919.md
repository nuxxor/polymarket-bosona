# ON KAYIT — BTC OYNAKLIK KAPISI (pencere ATLAMA)
2026-09-19 ~15:45 UTC. Kod HENUZ degistirilmedi (playbook #52).
Fikir kullanicidan geldi: "kazanan pencereleri bulup orada emir koymak".

## 1. BULGU
Zincir defteri (4.506 pencere) uzerinde kendi merdivenimiz simule edildi;
pencere PnL'i ile pencere ACILMADAN ONCE bilinen BTC oynakligi karsilastirildi.
BTC fiyati: HIST_spot.parquet (Chainlink, saniyelik, 16 Agu-2 Eyl).
vol5 = [S-300,S) araliginda BTC menzili, baz puan.

### (a) Kar ASIRI yogun ve kazanan pencere TEK degiskenle ayrisiyor
  en iyi 10 pencere = toplam karin %47 | artida biten pencere %36
  pencere ICI savrulmaya gore: en sakin -24,23 / en oynak +24,30 kr/pay
  (UYARI: bu ic-olcum kismen DONGUSEL, islem goren fiyatlardan turetiliyor)

### (b) OYNAKLIK KALICI — ve bu DONGUSEL DEGIL
  onceki 5dk BTC vol -> pencere ici menzil: Spearman **+0,676** (n=3.913)
  (Benim ilk "kalicilik +0,048" olcumum Polymarket-turevi kirli olcuttu.)

### (c) ORNEK DISI KARARLI (asiri uyum YOK)
  esik ilk yarida ogrenildi, ikinci yaride test edildi:
    vol5>19 bps: EGITIM farki +2,21 | TEST farki +2,09
  Egitim ve test farki neredeyse ayni -> iliski kararli.

### (d) GUN-KUMELI GA, IKI KOLDA DA CALISIYOR (3.913 pencere / 17 gun)
  KOL A: kapisiz +0,48 [-0,26,+1,28]  ->  vol5>15: +1,67 [+0,49,+2,75]
  KOL B: kapisiz +0,88 [+0,12,+1,59]  ->  vol5>15: +1,69 [+0,59,+2,62]
  Kapi, A kolunun GA'sini sifirdan AYIRIYOR. Elenen pencereler A'da -0,45.

## 2. NEDEN ESKI REJIM KAPISI BUNU KACIRDI
Koddaki KAPI_ACIK zaten AYNI olcumu yapiyor (Binance 1m klines, ESIK_BPS=16,4
— tam bu tatli noktada). Ama yanlis EYLEMI yapiyordu: pencereyi ATLAMAK yerine
KOL DEGISTIRIYORDU (oynaksa A, sakinse B). IPW sonucu +0,70 GA[-3,65,+4,74] =
CURUME DEGIL, GUCSUZLUK. Bu on kayit farkli bir eylemi test ediyor.

## 3. DEGISIKLIK
1. VOL_KAPISI=True, VOL_ESIK=15.0
   Pencere acilmadan once onceki_oynaklik(S) < VOL_ESIK ise PENCERE ATLANIR.
   Esik secimi: 15 bps hem A hem B'de $/gun'u en yuksek veriyor ve A/B icin
   daha cok ornek birakiyor (%39 pencere). 19 bps nokta tahmini daha yuksek
   (+1,99) ama %28 pencere -> A/B yavaslar. Bu bir YARGI, onceden yaziliyor.
2. KAPI_ACIK (kol degistiren eski kapi) KAPALI KALIR. Karismasin.
3. Olcum BASARISIZ olursa (Binance hatasi) pencere ACILIR (fail-open).
   Gerekce: kapi bir RISK kontrolu degil, bir SECIM kontrolu; olcemedigimizde
   eski davranisa (hepsini oyna) donmek tarafsizdir.
4. Baska HICBIR sey degismiyor. Izgaralar, A_ORAN=0.5, klip, kesici ayni.

## 4. ONCEDEN YAZILAN BEKLENTI (hedef kaydirmak YASAK)
- Pencere sayisi ~%39'a DUSECEK. Bu KESIN ve mekanik.
- A/B deneyi ~2,5x YAVASLAYACAK. Kabul ediliyor.
- kr/pay'in YUKSELMESINI bekliyorum ama simulasyon MUTLAK seviyede becerisiz
  (v2 icin +0,19 dedi, canli +14,2 verdi). Bu yuzden MUTLAK hedef koymuyorum.
- BASARI OLCUTU: ATLANAN pencerelerin (golge olarak kaydedilecek) kr/pay'i
  ACILAN pencerelerinkinden DUSUK olmali. Bu, kapinin kendi verimizle testidir.
- KILL: 200 acilan pencere sonunda acilan-atlanan farki <= 0 ise kapi kapanir.

## 5. GOLGE KAYDI (sart)
Atlanan her pencere icin `vol_atla` olayi loglanacak (S, vol, esik). Boylece
atlanan pencerelerin sonucu SONRADAN kamu veriden hesaplanabilir ve kapi
kendi canli verimizle sinanabilir. Kapi olcusuz calistirilmayacak.

## 6. NE IDDIA EDILMIYOR
- Bu kulvari karli yapmaz iddiasinda degilim. Kapi, 30 hucrelik haritadaki
  yapisal tavani degistirmez; yalnizca en kotu pencereleri elemektedir.
- Kuyruk pozisyonu sorunu (5 pay vs 383-3.692 pay onde) BU DEGISIKLIKTEN
  BAGIMSIZ ve hala acik.
