---
name: project-ayni-eslesme-ayristirma-20260916
description: Aktör avantajının %89'u OLAY SEÇİMİ, %11'i aynı eşleşmedeki fiyat — aynı taker emriyle dolan sıradan makerlar da +2,75 kr/pay kazanıyor
metadata:
  type: project
---

# AYNI-EŞLEŞME AYRIŞTIRMASI (2026-09-16, PRO talebi)

> ⚠️ **KAPSAM DÜZELTMESİ (aynı gün, sonradan yakalandı):** Aşağıdaki tablo `STATE_FEATURES.parquet`
> ile üretildi. O dosya `build_state_features.py:38-43` uyarınca **yalnız 25 hedef cüzdanın maker
> satırlarını** taşıyor (+ diğerlerinin taker satırlarının %2'si). Yani "peer" = venue'nun diğer
> top MM'leri, "kontrol" = yine hedef cüzdanlar. **"Sıradan cüzdanlar" okuması GEÇERSİZ.**
> Ayakta kalan tek sayı: `A−P = +0,33` [+0,25, +0,41] (saf aynı-eşleşme fiyat farkı).
> **Süpürme derinliği gradyanı (−0,29→+1,51) ve emir boyu gradyanı GERİ ÇEKİLDİ** — tam defterde
> (15,9M bacak, 10.536 cüzdan) çok-maker eşleşmesi yalnız +0,11 [−0,02, +0,21] veriyor.
> Doğru sonuç için bkz. aşağıdaki PEER_FULL_FLOW_V1.

**Soru:** mo-money/bosona'nın kazancı "iyi olayı seçmek"ten mi, "aynı olayda daha iyi fiyat almak"tan mı?

**Yöntem:** Zincir defteri `btc5m_top_actor_hunt_20260902_v1/STATE_FEATURES.parquet`
(7,1M satır, 16.904 cüzdan, 5.303 pencere, 14 Ağu–2 Eyl = TWAP-60 rejimi).
Grup = `(tx_hash, start_ts, outcome_idx)` — aynı doğrulanmış taker eşleşmesi, aynı token.
Özdeşlik: aynı tx + aynı token → terminal ödeme aynı ⇒ **g_A − g_P = p_P − p_A** (sonuç bilmeye gerek yok).
Ağırlık: her üç grupta da aktörün kendi payı. Kontrol C = 1 krş × 15 sn hücre ortalaması, hedefler hariç.
mo-money `0x32ed2e546b187ca15e2841edc82b22c713cf8ec3`, bosona `0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed`.

## Sonuç (iki aktör, kapsanan kısım, kr/pay, gün-kümeli %95 GA)

| ölçüt | değer | GA |
|---|---:|---|
| AKTÖR (brüt) | +3,08 | [+2,09, +4,14] |
| AYNI EŞLEŞMEDEKİ diğer makerlar (P) | **+2,75** | [+1,79, +3,80] |
| KONTROL (fiyat×zaman, hedefler hariç) | +0,18 | [+0,09, +0,28] |
| **A−P — aynı eşleşmede fiyat farkı** | **+0,33** | **[+0,25, +0,41]** |
| **P−C — OLAY SEÇİMİ** | **+2,57** | **[+1,61, +3,63]** |
| A−C toplam | +2,90 | [+1,92, +3,97] |

**Avantajın %89'u olay seçimi, %11'i aynı olaydaki fiyat.** Aktörle aynı taker emriyle dolan
SIRADAN cüzdanlar kazancın neredeyse tamamını alıyor → "gizli bilgi / daha iyi pazarlık" resmi büyük ölçüde yanlış.

## Kapsam (dürüst bölünme)
- Aktör bacaklarının **%20,3'ünde**, payların **%54,3'ünde** aynı eşleşmede başka maker var. Sonuç YALNIZ bu kısım için.
- **Kapsanmayan %45,7 pay çok daha zayıf:** aktör +0,87, kontrol +0,00, fark +0,87.
- ⇒ Avantaj tek-maker'lı küçük olaylarda değil, **çok-maker'lı süpürmelerde** yoğunlaşıyor.

## Yakalanan kusurlar (ikisi de düzeltildi)
1. İlk koşumda `ts` **mikrosaniye** olduğu için `t=ts−start_ts` hepsi 300'e kırpıldı → zaman kovası çöktü,
   kontrol yalnız fiyat oldu (101 hücre). Düzeltilince 2.067 hücre; sonuç neredeyse değişmedi (P−C 2,50→2,57).
2. PRO'nun uyardığı taker toplu-dolum satırı (`wallet==counterparty`) bu deftere hiç girmemiş — elenen 0.

## Çözülmemiş gerilim
Kendi canlımız da süpürülüyor (dolum oranı kuyruk derinliğinden bağımsız, %76-88) ama **−5,83 kr/pay**
kaybediyor. Peer'lar +2,75 kazanırken biz kaybediyoruz. Farkın nerede olduğu AÇIK:
fiyat düzeyi (peer 0,5605 vs biz ~0,45), çift-taraflı alım, ya da dönem farkı (14 Ağu–2 Eyl vs 15-16 Eyl).

## Kapanan
Çapraz fiyat skoru (`R = e − b − k`) kulvarı PRO kararıyla KAPANDI: aktör dışı alımlarda
ΔG=+0,25 kr/pay GA[−1,31,+1,80] = sıralama gücü gösterilemedi; skor bant geometrisini seçiyordu (dB=−0,46).
Yeni eşiklerle kurtarma YASAK. Bkz [[project-btc5m-maker-kapanis-20260915]]


---

# PEER_FULL_FLOW_V1 (2026-09-16) — TAM DEFTER, PRO'nun ikinci senaryosu çıktı

**Veri:** `FILL_PARTY_LEDGER/maker.parquet` — 15,9M maker BUY bacağı, **10.536 cüzdan**, 5.305 pencere, 20 gün.
**Yöntem:** Dönem kronolojik ikiye bölündü. 1. parçada (14–23 Ağu) mo-money/bosona ile aynı doğrulanmış
eşleşmede bulunan **2.569 peer cüzdan** kâra BAKILMADAN sabitlendi. 2. parçada (23 Ağu–2 Eyl) bu cüzdanların
**bütün** maker BUY akışı ölçüldü; küçük/tek-maker/zararlı dolumlar dışlanmadı.

| satır | bacak | kr/pay | %95 GA (gün-kümeli) |
|---|---:|---:|---|
| BÜTÜN maker BUY akışı | 6.356.118 | **−0,05** | [−0,16, +0,03] |
| **hedef AYNI EŞLEŞMEDE var** | 80.206 | **+1,26** | **[+0,37, +2,21]** |
| hedef aynı eşleşmede yok | 6.275.912 | −0,08 | [−0,19, −0,00] |
| — yok & tek-maker | 2.666.845 | −0,52 | [−0,74, −0,28] |
| — yok & çok-maker | 3.609.067 | +0,11 | [−0,02, +0,21] |
| peer-dışı tüm maker BUY | 1.193.997 | −0,53 | [−0,86, −0,22] |

## HÜKÜM (PRO'nun kendi karar kuralıyla)
Bu cüzdanlar **yalnız hedeflerle aynı eşleşmedeyken** artıda. Kendi genel akışları düz/eksi.
⇒ **"Genel derin likidite sağlamak yeter" açıklaması ÖLDÜ.** Kenar olay seçiminde.
⇒ Çok-maker'lı süpürmeye katılmak tek başına değersiz (+0,11, GA sıfırı kapsıyor).

## Açık sınır
`takerOrderHash` veride yok ⇒ tx'in tek bir `matchOrders` çağrısı olduğu KANITLANMADI.
tx'lerin %100'ünde tek taker cüzdanı + tek pencere, %90'ında tek token — yakınsak ama kanıt değil.
`wallet==counterparty` = 0; borsa sözleşmesi adresi karşı-taraf sütununda baskın değil (en sık %2,4).

## Ölçütün sınırı
`g = Y − p` yalnız **alış bacağının vadeye tutulduğundaki brüt katkısı**. Cüzdanın toplam strateji
PnL'i DEĞİL — sonraki satışlar/merge dahil değil. Maker ücreti 0.


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🎯 PEER_FULL_FLOW_V1 + AYNI-EŞLEŞME (09-16): peer cüzdanlar YALNIZ hedefle aynı eşleşmedeyken artıda (+1,26 GA[+0,37,+2,21]), kendi genel akışları −0,05 → "derin likidite sağlamak yeter" ÖLDÜ, kenar OLAY SEÇİMİNDE; süpürme-derinliği ve emir-boyu gradyanları GERİ ÇEKİLDİ (STATE_FEATURES yalnız 25 hedef cüzdan taşıyor)](project_ayni_eslesme_ayristirma_20260916.md)
