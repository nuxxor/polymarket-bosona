---
name: project-vol-kapisi-20260919
description: 09-19 BTC oynaklik kapisi — kazanan pencere ONCEDEN secilebiliyor; ornek disi kararli (egitim +2,21 / test +2,09), iki kolda da GA sifiri disliyor; canlida
metadata:
  type: project
---

# BTC OYNAKLIK KAPISI — PENCERE SECIMI (2026-09-19, CANLI)

## KAYNAK
Fikir KULLANICIDAN geldi: "kar 2 pencerede yogunlasmis dedin, bu pencereler
dinamik mi statik mi, kazanan pencereleri bulup orada emir koysak?"
Ben o an baska seye bakiyordum. Fikir dogru cikti.

## BULGU
Zincir defteri 4.506 pencere, kendi merdivenimiz simule edildi.
1. KAR ASIRI YOGUN: en iyi 10 pencere = toplam karin %47; artida biten
   pencere yalnizca %36.
2. OYNAKLIK KALICI: onceki 5 dk BTC menzili -> pencere ici menzil
   **Spearman +0,676** (n=3.913). (Ilk olcumum "+0,048" idi ama o
   Polymarket islem fiyatlarindan turetilmis KIRLI olcuttu — dongusel.)
3. ORNEK DISI KARARLI: esik ilk yarida ogrenildi, ikinci yaride test edildi.
   vol5>19 bps -> EGITIM farki +2,21 | TEST farki +2,09. Asiri uyum YOK.
   (Bugune kadar curuyen her fikir tam burada cokuyordu.)
4. GUN-KUMELI GA, IKI IZGARADA DA (3.913 pencere / 17 gun):
     KOL A kapisiz +0,48 [-0,26,+1,28] -> vol5>15: **+1,67 [+0,49,+2,75]**
     KOL B kapisiz +0,88 [+0,12,+1,59] -> vol5>15: **+1,69 [+0,59,+2,62]**
   Kapi A kolunun GA'sini sifirdan AYIRIYOR; elenen pencereler A'da -0,45.

## NEDEN DAHA ONCE BULUNAMADI (onemli ders)
Kodda bu kapi ZATEN VARDI: `onceki_oynaklik()` + `ESIK_BPS=16,4` — olcum
DOGRUYDU ve esik tam tatli noktadaydi. Ama YANLIS EYLEMI yapiyordu:
pencereyi ATLAMAK yerine KOL DEGISTIRIYORDU (oynaksa A, sakinse B).
Yani kotu pencerelerde oynamaya devam ediyordu, sadece baska izgarayla.
Eski IPW sonucu +0,70 GA[-3,65,+4,74] = CURUME DEGIL, GUCSUZLUK + yanlis eylem.
DERS: dogru olcum + yanlis eylem = curumus gibi gorunur. Bkz playbook.

## CANLI YAPILANDIRMA (15:47Z)
    VOL_KAPISI=True, VOL_ESIK=15.0 (bps)
    onceki_oynaklik(S) < 15 -> pencere ATLANIR (log: vol_atla)
    olculemezse pencere ACILIR (fail-open; kapi RISK degil SECIM kontrolu)
    KAPI_ACIK (eski kol-degistiren kapi) KAPALI kalir
    Acilan pencereler de vol'u ile loglanir -> kill olcutu olculebilir kalsin
    79/79 test gecti.
NOT: onceki_oynaklik Binance'ten limit=12 1dk mum ceker -> yalnizca SON ~12
dakikayi olcebilir. Canlida sorun degil (pencere acilirken cagriliyor) ama
GECMISE DONUK hesaplanamaz; bu yuzden vol'u ANINDA loglamak SART.

## ON KAYIT + KILL
`data/analysis/pm_merdiven_ab_20260918_v5/ONKAYIT_VOL_KAPISI_20260919.md`
KILL: 200 acilan pencere sonunda (acilan kr/pay - atlanan kr/pay) <= 0 ise kapi kapanir.
Atlanan pencereler golge olarak kaydediliyor, kamu veriden degerlendirilecek.

## BU NEYI COZMUYOR
30 hucrelik haritadaki yapisal tavani degistirmiyor; en kotu pencereleri
eliyor. Kuyruk pozisyonu sorunu ([[project-kuyruk-olcumu-20260919]]:
5 pay vs onumuzde 383-3.692 pay) BUNDAN BAGIMSIZ ve hala acik.
