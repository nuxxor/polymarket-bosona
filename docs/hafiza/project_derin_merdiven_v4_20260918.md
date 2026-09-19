---
name: project-derin-merdiven-v4-20260918
description: bosona mekanizmasinin kendi botumuzda uygulanmasi - MUTLAK fiyat merdiveni (0,40..0,03). Cift maliyeti 0,52-0,66 (bosona 0,847) YANI GIRIS FIYATI SORUNU COZULDU; ama eslesme orani dusuk, 8 pencerede basabas. Tape: cift ancak %16,6 pencerede kuruluyor
metadata:
  type: project
---

# DERIN MERDIVEN v4 (09-18 gecesi, CANLI)

Kod: `data/analysis/pm_merdiven_20260918_v4/merdiven.py`
Olcum: `olc4.py`  Log: `LOG_v4.jsonl`  Yedek: `data/backups/merdiven_v4_20260918_0158.tar.gz`

## TASARIM
- Iki tarafta da MUTLAK fiyat noktalarina post-only alis: **[0,40 0,30 0,22 0,15 0,10 0,06 0,03]**
- 5 pay/seviye, pencere boyunca ACIK kalir, t=297'de teyitli iptal
- DENGE_SINIR=10 pay (0,5 tolerans): bir taraf 10 pay one gecerse O TARAFIN kalan
  seviyeleri iptal edilir; hafif taraf acik kalir
- Cift tamamlama KAPALI (v3'te olculdu, kenar getirmiyor)
- KESICI -60; tek taraf maruziyeti FIYATTAN BAGIMSIZ **$6,30** tavanli

## SONUCLAR (8 pencere, gece 22:05-22:55)
- **cift maliyeti 0,52-0,66** (medyan ~0,62) — bosona 0,847, v3 dokunus 0,976
  => **GIRIS FIYATI SORUNU COZULDU**, hatta aktoru gectik
- PnL: +5,79 / +3,90 / -3,50 / +1,90 / -0,35 / -3,50 / -4,60 / +1,55 = **+1,19$**
  (4 artida 4 eksida, BASABAS)
- Seviye dolum orani: 0,40 %100 | 0,30 %100 | 0,22 %75 | 0,15 %50 | 0,10 %25 |
  **0,06 ve 0,03 %0** (bu ikisi bosuna duruyor, cikarilabilir)

## ACIK SORUN: ESLESME ORANI
Kar yalniz CIFT kurulunca geliyor; tek taraf kalinca kaybediyoruz.
- bosona %65 eslesme, biz v3'te %12, v4 tik merdiveninde %21, v4 mutlakta degisken
- KAYITLI TAPE OLCUMU (145 pencere, 09-17): **cift ancak %16,6 pencerede kurulabiliyor**,
  %66 tek taraf, %18 hic dolum. Cift kurulunca maliyet 0,443 (cok ucuz).
  Tape beklentisi +1,38$/pencere AMA canli gercek +0,15$/pencere -> **model ~9x IYIMSER**.
  Dolum varsayimi ("piyasa fiyatimizin altina inerse doluruz") iptal edilmis emirleri
  saymiyor. PLAYBOOK #38: simulasyon karar araci DEGIL.

## YOLDA DUZELTILEN 4 KUSUR (hepsi canlida gorulup duzeltildi)
1. **Sabit tik ofseti YANLIS**: bb=0,76'da merdiven 0,71/0,66/... oluyordu ->
   maruziyet $13,95 (tahminimin 2 kati) ve dolumlar ort 0,608 = HIC UCUZ DEGIL.
   Mutlak fiyat noktalarina gecildi. Tek basina en pahali dersimiz: -$12,15.
2. **Denge siniri kismi dolumda atlanıyordu**: 4,995 paylik dolum farki 9,995'te
   birakip esigi BINDE BESLE atlatti. 0,5 pay tolerans eklendi.
3. **data-api 999 (hiz siniri)**: mutabakat 120 sn'de 2000 islem cekiyordu ->
   MUTABAKAT_ARA=180, sayfalama 1000, sayfalar arasi 0,6 sn, 999'da 20 sn geri cekilme.
   Bot bu sirada fail-closed davrandi (mutabakatsiz pencere acmadi) - DOGRU.
4. Tek yone birikim sinirsizdi -> DENGE_SINIR eklendi.

## SIRADAKI AYARLAR (oncelik sirasi)
1. **COKLU PAZAR** — en buyuk kaldirac. bosona 3 saatte 87 pazar (btc/eth/sol/xrp/doge,
   5m/15m/4h), biz 1. BTC tek yone trend yapinca TUM maruziyetimiz ayni yone diziliyor;
   bes coinde dagilir ve eslesme orani yukselir.
2. 0,06 ve 0,03 seviyelerini cikar (11 pencerede %0 dolum, bosuna emir).
3. DENGE_SINIR'i 10'dan 5-7'ye indirmeyi dene (tek taraf kaybini kucultur).
4. Fiyat noktalarini rejime gore ayarla (oynak saatte derin, sakin saatte sig).
