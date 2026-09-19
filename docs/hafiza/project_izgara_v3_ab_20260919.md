---
name: project-izgara-v3-ab-20260919
description: 09-19 izgara turu — ulasabildigimiz uzayda artida hucre YOK, bosona'nin kenari 0.40 ustunde, onu maker kopyalamak -19.74; v2 vs v3 derin izgara RASTGELE A/B'ye alindi
metadata:
  type: project
---

# IZGARA v3 / A-B (2026-09-19)

## 1. 30 HUCRELIK (fiyat x zaman) HARITASI — kulvarin tavani
Zincir-kesin maker ALIS dolumlari, kiyas sinifi = cuzdan-pencerede hic >0.40
alim yok (bizim kisitimiz). 1.406.171 dolum / 21.314.667 pay / 19 gun.
Havuzlanmis kr/pay + GUN-KUMELI esli bootstrap.

**TABAN -0.39 kr/pay. 30 hucrenin HICBIRI artida sifirdan ayrismiyor. 7'si EKSIDE.**
En kotu: px 0.28-0.34 @ t240-301 = -6.67 | 0.22-0.28 @ t240-301 = -4.53
En iyi (notr): px 0.00-0.10 @ t120-240 = +0.63 / +0.34 (GA sifiri iceriyor)

Bu, ulasabildigimiz uzayda maker merdiveninin ustunde YAPISAL BIR TAVAN oldugunu
soyluyor. Izgara ayari bu tavani asamaz.

## 2. BOSONA'NIN KENARI NEREDE (19 gun, 1.78M pay, zincir-kesin)
    pencere tamamen <=0.40 (BIZIM OYUN):  -3.53 kr/pay
    pencerede >0.40 alim VAR           :  +1.51 kr/pay [+0.43,+2.64]
**bosona bizim oyunumuzu oynadiginda O DA kaybediyor.**
Ayrica: tum makerlar px 0.00-0.40 = +0.73 ama YALNIZ <=0.40 alanlar = -0.39.
=> Ucuz bacak ancak PAHALI bacagin yarisi olarak karli; tek basina eksi.

## 3. AMA ONU MAKER OLARAK KOPYALAMAK IMKANSIZ
TAM EV simulasyonu (4506 pencere, essiz bacak kayiplari DAHIL):
    0.80/0.02 (bosona'nin 14:25Z cifti) = **-19.74 kr/pay** [-20.78,-18.66]
    0.70/0.15 = -12.63 | 0.34/0.34 = +0.32 | 0.26/0.26 = +1.44 | 0.08/0.20 = +2.64
MEKANIZMA: 0.80'e duran ALIS emri ancak fiyat oraya DUSUNCE dolar = favori
zayiflarken alirsin = ters secimin tanimi. bosona o bacagi taker olarak ya da
kuyrugun onunde aliyor. Bu kapi bize kapali.

## 4. IKI SECIM ARTEFAKTI (kendi olcumlerim, geri cekildi)
- "gec cift kuranlar +6.79 kazaniyor" -> olen tarafi 0.05'ten ancak ILK BACAGIN
  KAZANIYORSA alabilirsin. Marjinal dolum duzeyinde (t>=200 & px<=0.25):
  karsi taraf VAR -0.08, YOK +0.02 = SIFIR.
- "iki bacak da <=0.40 olanlar +13.55" -> ayni sey (gidis-donusun tamamlanmasina
  kosullanma).
Kodda yazili eski "gec+ucuz -14.86 kaybeder" gerekcesi de curudu (7 dolumdu).

## 5. SIMULASYONUN BECERISI YOK — KAZANAN IZGARAYI KAPATMADIK
TAM EV merdiven simulasyonu v2 izgarasi icin **+0.19 kr/pay** ongordu.
Canli v2, 16 pencerede **+$27.70 / 195 pay = +14.2 kr/pay** verdi.
Model bizim gercek dolum surecimizi ongormede beceri gostermedi (ve BIZIM
LEHIMIZE yanildi). O yuzden v3'e tek tarafli gecilmedi; RASTGELE A/B kuruldu.

## 6. CANLI YAPILANDIRMA (15:10Z itibariyle)
    KOL A (kontrol, degismedi): FIYATLAR  =[.34 .30 .26 .22 .20 .16], t>=200'de px<=0.25 iptal
    KOL B (deney, PAKET)      : FIYATLAR_B=[.20 .16 .12 .09 .06 .03], t>=200'de px>0.10 iptal
    A_ORAN=0.5 (rastgele, tohumlu). 69/69 test gecti.
B'nin gec kurali A'nınkinin TERSI olmak ZORUNDA: B'nin tum basamaklari <=0.20,
eski kural B'nin TUM emirlerini keserdi. B bu yuzden bir PAKET; iki degisiklik
mantiken ayrilamaz ve on kayitta boyle yazildi.

ON KAYIT: data/analysis/pm_merdiven_ab_20260918_v5/ONKAYIT_IZGARA_V3_DERIN_20260919.md
Ilgili: [[project-profil-teshisi-20260919]] [[project-btc5m-maker-kapanis-20260919]]
