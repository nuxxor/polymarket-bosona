---
name: project-kamu-akis-tek-fiyat-20260916
description: Polymarket kamu last_trade_price akışı bir işlemi token başına HER ZAMAN tek toplu fiyattan yayınlıyor (667.032/667.032) — çok seviyeli süpürme imzası canlı hesaplanamaz
metadata:
  type: project
---

# KAMU AKIŞI TEK FİYAT YAYINLIYOR (2026-09-16, köprü kapısı)

**Soru:** Zincirde `fiyat aralığı > 0,08` gösteren eşleşmeler kamu akışında kaç fiyattan görünüyor?
(Bu, "çok seviyeli süpürme" imzasının canlı tetikleyiciye çevrilip çevrilemeyeceğinin kapısıydı.)

**Veri:** `data/tape/` — 37 tam saatlik dosya, 15–16 Eylül. Yalnız ham `pm:last_trade_price` mesajları;
zincirden sonradan tamamlama YOK, defter azalması işlem sayılmadı.

## SONUÇ — kesin
| | |
|---|---:|
| kamu işlem mesajı | 667.032 |
| `(tx_hash, asset_id)` grubu | 667.032 |
| **grupta 1 fiyat** | **667.032 = %100,00** |
| grupta >1 fiyat | **0** |

**Bir işlem, o token için her zaman TEK toplu fiyattan yayınlanıyor.** Zincirdeki çok seviyeli
fiyat yürüyüşü kamu akışında görünmüyor ⇒ `aralık>0,08` imzası CANLI KURULAMAZ. Tetikleyici elendi.

## Gecikme (ayrımı koru)
`rcv − src` = **sunucu damgası → yerel alım**, "eşleşme → biz" DEĞİL (gerçek gecikme ≥ bu).
- Kamu işlem akışı: medyan **50 ms**, %95 585 ms, maks 17,8 sn
- Kimlikli aktör akışı (polling): medyan **169,2 sn**, <5 sn olan %0,8, <60 sn olan %13,7
  (21.082 bildirim; %95 → 303,7 sn, yani 300 sn'lik pencere kapanmış)

## Kapsam sınırı
Yalnız `last_trade_price` incelendi. `pm:price_change` seviye seviye defter değişimi taşıyor ama
PRO kuralı: defter azalması gerçekleşmiş işlem sayılmaz. Bu sonuç "tüm anonim veri yolları imkânsız"
demek DEĞİL — yalnız bu tetikleyici elendi. Başka göstergeye sessizce geçilmeyecek.

## Bağlam
İmza bulgusu kendisi geçerliydi (tam defter, holdout): aralık>0,08 → **+4,42 kr/pay** [+1,40, +8,70]
vs tek-fiyatlı eşleşme −0,40. Ama bu **tamamlanmış işlemin zincir kaydından** okunuyor, kamu akışından değil.
Bkz [[project-ayni-eslesme-ayristirma-20260916]]


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🚧 KÖPRÜ KAPISI KAPANDI (09-16): kamu `last_trade_price` bir işlemi token başına HER ZAMAN tek toplu fiyattan yayınlıyor (667.032/667.032 = %100) → çok-seviyeli süpürme imzası CANLI HESAPLANAMAZ, tetikleyici elendi; kamu akışı gecikmesi medyan 50 ms vs kimlik akışı 169 sn](project_kamu_akis_tek_fiyat_20260916.md)
