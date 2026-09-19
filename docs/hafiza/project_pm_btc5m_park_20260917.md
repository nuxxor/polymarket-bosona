---
name: project-pm-btc5m-park-20260917
description: BTC5m aktör-kopya programı operatör emriyle PARK (2026-09-17) — ne bilindiği, ne elendiği, hangi tetikle açılacağı
metadata:
  type: project
---

# 🅿️ PM BTC5m PARK (2026-09-17, operatör emri "durdur her şeyi")

**Durum:** bot kapalı, açık emir 0, toplam gerçekleşmiş kayıp **−$21,60**. Kayıtçı (`tape.py`) açık
bırakıldı — salt okuma, yalnız disk maliyeti; durdurulursa veri boşluğu KALICI olur.

## KESİN BİLİNENLER (ölçülmüş, tekrar ölçme)
1. **Aktör kârı gerçek:** bosona +$57.224 / +2,20 kr/pay, mo-money +$63.073 / +2,30 kr/pay
   (14 Ağu–4 Eyl, bağımsız Decimal ile yeniden kuruldu).
2. **Kenarın ayrışması (gerçek defter, 15.438 işlem):** toplam +1,38 kr/pay
   = **+0,44 makasın yarısı** (mekanik, her maker alır) + **~+1,0 orta fiyatı yenmek**.
3. **Avantaj KALICI, kısa süreli sapma DEĞİL:** 5 sn yeniden fiyatlanma −0,38 [−0,53,−0,24]
   (aleyhlerine), 30 sn +0,01; **30 sn sonra kalan artık +1,08** [−0,09,+2,53]. ⇒ terminal bilgi.
4. **Hacimlerinin %87'si t≈129 sn'de**, TWAP durumu daha OLUŞMAMIŞKEN (+1,52 kr/pay).
   TWAP kilidi destekli işlem hacmin yalnız **%0,6'sı**.
5. **Çift stratejisi oynamıyorlar:** çift oranı %37-52; bizim başabaşımız %79,8 istiyordu.
6. **TWAP kilidi gerçek ama erişilemez:** |marj|≥5bp'de 597/597 ve 2.525/2.529 isabet,
   pencerelerin %75'i. AMA karar anında ask tarafı 594/597 pencerede BOŞ; bid kuyruğu
   0,90 üstünde medyan **34.443 pay** ve akış medyan **0**. Taker de maker de kapalı.

## ELENEN YOLLAR (bir daha açma)
çapraz fiyat skoru · süpürme derinliği · emir boyu · derine yerleşim (DELTA 0,03-0,15)
· aktör bildirimini takip (brüt +0,24/+0,12, ücret öldürüyor) · hız (aynı olaylarda 3sn vs 169sn
medyan fark **sıfır**) · "gizli veri kaynağı" (3/3 kontrol, 09-13) · Pyth/alternatif feed
(settlement Chainlink; kenar t≈129'da, o an hiçbir feed settlement söyleyemez)
· maker kotasyon politikası (DÜZELTİLMİŞ motorla bile 12/12 eksi, 0/4 gün artıda)

## AÇIK KALAN TEK SORU
**PM'nin kendi orta fiyatının ÜSTÜNE terminal bilgi ekleyebiliyor muyuz?**
Aktörlerin ölçüsü **+1,08 kr/pay**. `PM_CONDITIONAL_INFO_V1` (scratchpad/kosullu.py) yazıldı
ve ön-kayıtlandı ama PARK emriyle koşum tamamlanmadı.

## YENİDEN AÇMA TETİKLERİ
- `PM_CONDITIONAL_INFO_V1` koşulur ve OOS üst çeyreğin `E[Y−m]`'si pozitif + GA sıfırı dışlarsa
- Emir düzeyi veri erişimi çıkarsa (kabul/iptal/dolmayan emirler) — her denetim aynı boşluğu
  işaret etti: aktör yerleşim mekanizması CAUSALLY_UNIDENTIFIED
- Venue ücret/rebate yapısı değişirse

## DAĞITIM ÖLÇÜTÜ (canlıya dönülürse)
7 ardışık gün, $500 tepe nakit+rezerv tavanı, gün-kümeli %95 ALT sınır sıfırın üstünde,
her yetim ve ücret dahil, tüm denenen emirler kayıtlı. Devre kesici ZORUNLU.

## YARIM KALAN İŞLER
- `scratchpad/cikar2.py` — kalıcı token haritalı düzeltilmiş olay çıkarımı (koşum yarıda kesildi)
- `scratchpad/tara_duzeltilmis.py` — DÜZELTİLMİŞ kuyruk motoru (DUZ=True/False), ÇALIŞIR durumda
- `uygunluk.py` gerçek-dolum hatası: 70 emrin 1'ini etkiliyor (gerçek ama küçük)

Bkz [[project-twap-kilidi-20260917]], [[project-ayni-eslesme-ayristirma-20260916]],
[[project-delta-tarama-kapanis-20260916]]


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🅿️ PM BTC5m PARK (09-17, operatör emri): bot kapalı, kayıp −$21,60; aktör kenarı = +0,44 makas + ~+1,0 orta fiyatı yenmek, 30 sn sonra artık +1,08 → KALICI terminal bilgi, hacmin %87'i t≈129'da; 9 yol elendi; tek açık soru PM fiyatının üstüne bilgi eklenebiliyor mu](project_pm_btc5m_park_20260917.md)
