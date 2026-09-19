---
name: project-gpt-ultra-denetim-20260919
description: GPT Ultra derin incelemesi — cancel60 adayı (+$966 replay ama üç ciddi çekince), rebate formülü çözüldü (0.014·q·p·(1−p), 5 pay yeterli), ve benim 4 iddiam çürüdü
metadata:
  type: project
---

# GPT ULTRA DERİN İNCELEME (2026-09-19)

Rapor: `data/analysis/btc5m_maker_deep_review_20260919_v1/REPORT.md`
27 betik, 66 konfigürasyon, 393,9M satır defter akışı, 248.080 karar durumu.

## ÇÖZÜLEN: REBATE FORMÜLÜ
- **$13,424800** ödendi (00:45:34 UTC), zincirde doğrulandı. 18 Eylül tahakkuku:
  4.721,08 pay → **0,284358 kr/pay**.
- **Formül: `0.014 · q · p · (1−p)` dolar.** Yani FİYATA BAĞLI:
  0,22'de **0,240 kr/pay**, 0,40'ta **0,336 kr/pay**. Sabit 0,27 varsayımı YANLIŞ.
- **5 pay yeterli** — 50 paylık eşik LİKİDİTE ÖDÜLÜ içindi, maker rebate'i için değil.
- Rebate farmlama doğrudan test edildi ve **optimum DEĞİL**: cancel60 rebate'te
  $113,30 kaybediyor ama işlemde $966,32 kazanıyor, net +$853,02.

## ADAY: GEC_KES=60, UCUZ_ESIK=0.40 (hepsini 60. saniyede iptal et)
```
tam replay 4.378 pencere/19 gun: +2,061 kr/pay [+0,468,+3,693]
mevcut politikaya gore fark: +$966,32 [$361,36,$1.623,99]
2.310 iyilesen / 1.014 kotulesen / 1.054 ayni | medyan +$0,70 | en iyi 3 = %1,96
```
Playbook #47 kontrol listesini GEÇİYOR. **AMA üç ciddi çekince:**
1. Kapsam %95'e çıkarılınca **−1,102 [−3,469,+1,030]** kr/pay oluyor — mutlak
   kârlılık popülasyon kısıtına DAYANIKLI DEĞİL.
2. Aile geneli işaret-çevirme p=**0,129** (anlamsız); o ailenin kazananı cancel**200**.
3. Geliştirme döneminin ikinci yarısında eşleşmiş kazanç **negatif** (−$21,88) —
   ön kayıtlı kararlılık kapısını GEÇEMİYOR (rapor bunu saklamamış).
4. Kendi dolumlarımızla karşı-olgusal: +$19,65 **[−$4,50,+$43,50]** — sıfırı kapsıyor.
→ Verdikt doğru: **sıradaki DENEY, terfi DEĞİL.**

## BENİM ÇÜRÜYEN İDDİALARIM (dördü de)
1. "Bizim klip boyumuzda kazanan cüzdanlar" — `0x5d5f7080`'in hacminin **%74,7'si
   5 paydan BÜYÜK emirlerden**. ≤5 pay kesiti +0,408 [−1,196,+2,051], sıfırı kapsıyor.
   Medyan dolum boyu küçük olması emrin küçük olduğunu KANITLAMAZ.
2. "Rebate her rung'da 0,27" — hayır, fiyata bağlı (0,24 → 0,336).
3. "Kaskadsız dolum = iptal yok" — 187 kaskadsız gözlemin **177'sinde** ≥100 pay brüt
   çekilme var; eklemeler çekilmeyi gizlemiş. Kaskad ayrımı yanıltıcıydı.
4. `0x361528e2`'nin 0,60 üstü kenarı **+5,20 değil +2,027** [−1,777,+5,388] — benim
   aritmetik hatam.

## BULDUĞU İKİ KOD KUSURU (ikisi de benim 09-18 gecesi eklediğim)
- `ab.py` `tokens=list(tk)` → `tk` SÖZLÜK, `[0,1]` logluyordu, token kimlikleri değil.
  Markout'u gamma'dan bağımsız kılma amacı tamamen boşa gitmişti. **Düzeltildi.**
- `--test` canlı LOG'a yazıyordu (sahte client gerçek `log()`'u çağırıyor). 5 sahte
  `toplu_emir_hata` olayı sızmış. **Düzeltildi**; log'a NOT satırı eklendi.
  Ayrıca: "23:42'deki hatalar çöküşten" demiştim — o da test sızıntısıymış,
  **bot gerçek toplu-emir hatası hiç yaşamadı.**

## DİĞER BULGULAR
- **Aktör seçimi ileriye taşınıyor:** erken tanımlı kârlı/kârsız gruplar, sonraki
  9 günde **+0,333 kr/pay [0,125,0,533]** ayrışıyor (2.005 ortak pencere).
- **Karşı taraf kalitesi kalıcı:** en kötü eğitim beşte biri sonradan maker
  rakiplerine −1,499 [−1,828,−1,170] kr/pay veriyor (17M pay). Ama karşı taraf
  kimliği emir dolmadan ÖNCE bilinemiyor.
- **Builder kullanımı:** altı aktörde sıfır, `0x3615`'te %100; `0x5d5f`'in kalıntısını
  yalnız +0,040 değiştiriyor. Açıklayıcı değil.
- $5,60'lık muhasebe farkı çözüldü: iki eski pencere (+$6,80 ve −$1,20).
- 376/489 kamu dolum imzası TEKİL DEĞİL → kesin eşleşme zamanı **KISMEN GÖZLENEBİLİR**.
  Çözen tek alan: kendi emir kimliğimiz + kimlikli eşleşme zaman damgası.

İlgili: [[project-maker-rebate-gercek-20260919]], [[project-kucuk-klipli-kazananlar-20260919]]
