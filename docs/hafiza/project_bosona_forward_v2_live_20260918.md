---
name: bosona-forward-v2-live-20260918
description: "Bosona shadow goal resumed 09-18 14:03 UTC; forward_v2 continuous prospective paper runner live_v1 frozen at 14:15 UTC, 7 worlds, primary favorite_inventory_reset; disk risk from dual capture"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4683f064-74bf-4999-a3cc-7a65e2b411ca
  modified: 2026-09-18T14:04:39.490Z
---

**Durum (2026-09-18 14:05 UTC):** Kullanıcı "kaldığı yerden devam et" dedi; devir belgesinin
2-3-4 adımları uygulandı. `data/analysis/bosona_shadow_goal_20260918_v1/forward_v2/runner.py`
= timeline_v2 (15 dk değişmez bloklar, 20 dk olgunlaşma) + causal_replay_v2 checkpoint/restore
+ native_venue_v2 motor. `forward_v2/live_v1` **14:15:00 UTC aktivasyon** (1789740900000),
PID `live_v1/PROCESS.json`; ilk blok 14:50'de olgunlaşır. Birincil dünya önceden ilan:
`favorite_inventory_reset`; 6 kontrol dünyası. Skor: `forward_v2/score.py` (diagnostik).

**live_v2 (14:45 UTC, PID `live_v2/PROCESS.json`):** mid−δ dünyaları mid2 (birincil)/mid4/mid2_reset via `runner_v2.py`+`mid_policy.py`; runner.py/candidate_policy.py değiştirilmedi. Kullanıcı 09-18: "kalan her şeyi sen yönetiyorsun" (tam yetki, operatör onayı gerektiren tek şey süreç öldürme). Bosona açık-bacak kulvar ölçümü: SOL5 %85,8 @72,8 kr, DOGE5 %89 @73,3, ETH5 %49,4 @44,2, BTC5 %32,7 @37 → açık bacak favori taraf, taraf seçimi ayrı karar katmanı.

**09-21 19:05 TSİ CANLI = `forward_v2/live_follow2`** (runner_v8: kulvar takibi + 60 pay/pazar tavanı), etiket kaynağı `native_flow_live_v1/runtime_fast` (12 işçi). Çözümleyici darboğazı: 12.584 iş/saat gelirken 5.771 çözülüyordu → işçi 4→12, throughput 21.000/saat. Serbest RPC uçlarının hepsi kapalı (yalnız publicnode + drpc çalışıyor).

**09-20 00:15 TSİ = `forward_v2/live_mirror2`** (ayna, 4 dünya). live_mirror 16 blok sonra durdu: 174 işlemin zincirde MAKBUZU YOK → timeline kurucusuna 45 dk pes etme eşiği eklendi (`RETRY_GIVE_UP_NO_RECEIPT`, 16/16 test). 1rpc.io kotası doldu, 2 sağlayıcı kaldı. Ayna dolum oranı sorunu: 38 pencerenin 2'sinde dolum (o: 9 işlem/pazar).

**09-19 03:00 TSİ = `forward_v2/live_v8a` + `live_v8b`** (runner_v4.py + favorite_variants.py), aktivasyon 00:15 UTC, capture_v2, iki süreç/altı dünya: a=quote_control+favorite_quote+fav_clip30, b=fav_clip50+fav_5m+fav_15m. cheap_ladder/open_favorite kapatıldı. **OLAY: 22:02 UTC'de earlyoom TÜM kayıt süreçlerini öldürdü; live_v7 boş bloklar üretti, 22:02-23:42 UTC veri boşluğu. Kayıt 23:42'de elle yeniden başlatıldı (PID'ler yeni), nöbetçi monitör kuruldu.** Ders: [[lesson-earlyoom-capture-death]].

**09-19 02:40 BACKTEST (örnek dışı, 16:30-19:45 TSİ, 156 pencere):** favorite_quote +$122 (+2,75; 78/118; ex-top3 +46) → akşam kesitiyle (+99, 114/142) İKİ BAĞIMSIZ KESİTTE ARTIDA, en sağlam aday; quote_control +97 (ex-top3 −27, yoğun); cheap_ladder −241 (3/24, çürüdü); open_favorite +4; bosona −30 (31 pencere). Dış rapor uyarısı: dokunuş dolumları %98 iptal kaskadıyla vuruluyor, shadow bunu göremez. Dizinler `forward_v2/backtest_v7_1330_1645` (2 blok) + `backtest_v7_seg_1415/1500/1545`.

**09-19 01:10 TSİ:** CANLI = `forward_v2/live_v7` (runner_v3.py + bosona_policy.py: quote_control, favorite_quote, open_favorite[birincil], cheap_ladder), aktivasyon 22:30 UTC = 01:30 TSİ (1789770600000), capture_v2. v5 (hash) / v6 (operatör: mid−δ çürüdü) HALT. Bosona 4 saat analizi: BTC15 %94 ucuz taraf, 300-700 pay yığın, düşerken ekleme, +448 (8/15); altcoin ilk 3-6 sn favori 100-150 pay tek atış +129. Kurucu: seq sınırları, parçalı/snapshot'sız okuma, ön-getirme (WAL 4,5 GB dersi). Araçlar tüm günlük dosyaları okur.

**23:20 TSİ 3 SAATLİK KESİT (191 pencere):** bosona +$437 (26 pencere; BTC15 ucuz-taraf 300-700 pay, düşerken aynı tarafa ekleme, açık 4.108/çift 637); quote_control +$240 (+2,15, ex-top3 +117, 90/165 artı); favorite_quote +$99 (114/142 artı); mid2 +$2 (ex-top3 −115 → mid−δ hipotezi tutmadı); mid4 +$85 (ex-top3 −10); mid2_reset −$113; through −$1.102. Araçlar: `forward_v2/compare_actor.py --per-market`, `markout.py`. Kullanıcı 3 saatlik kesit istiyor (7 gün değil); TSİ = UTC+3 yaz.

**16:30 UTC:** CANLI = `forward_v2/live_v5` (dokunuş 7 dünya) + `live_v6` (mid−δ), kaynak **capture_v2** (v1'de 24 WS kopması/2 sa, v2 sıfır), aktivasyon **16:45 UTC** (1789749900000). Runner olay yazımı tamponlandı (satır-satır WAL yazımı replay'i disk beklemesine sokuyordu). 7 dünyalı replay capture_v2'de 0,4-0,6x gerçek zaman → yetişir. v1..v4 arşiv/HALT.

**15:17 UTC (eski):** live_v1/live_v2 arşiv (timeline kurucusu 55x yazma şişmesi → pragma düzeltmesi hash'i değiştirdi, kendiliğinden HALT). CANLI: `forward_v2/live_v3` (dokunuş 7 dünya, runner.py) + `forward_v2/live_v4` (mid−δ, runner_v2.py), aktivasyon **15:45 UTC** (1789746300000). 7 dünyalı replay 15 dk bloğa 18,7 dk → v3 geride kalır (geçerli). Ders: [[lesson-sqlite-write-amplification]].

**Ölçümler:** native etiket hazırlık gecikmesi n=8.357: p50 544 s / p99 752 s / azami 934 s.
5 dk blok replay'i 132-245 s (7 dünya) → 15 dk blok 7-12 dk; yoğun saatte gecikme birikebilir.
Dev kontrol `forward_v2/dev_check_1320_1330_v1` 2 blok 300 dolum geçti (ekonomik iddia yok).

**Why:** Devir notundaki "düzeltilmiş v2 için sürekli ileri runner yazılmadı" boşluğu buydu;
kâr kanıtı ancak ileri veriyle (200 pazar/kulvar, 7 tam gün) gelir.

**How to apply:** Yeni oturumda önce `live_v1/STATUS.json` + `HALT.json` var mı bak; sonra
`score.py --output forward_v2/live_v1`. Kaynak dosyaları DEĞİŞTİRME (FREEZE hash'i → HALT);
değişiklik = yeni output + yeni aktivasyon. Beş eski süreç (capture v1/v2, shadow_v1, monitor,
native producer) dokunulmadı. **Disk:** capture v1 ~2,5 GB/sa + v2 ~3,4 GB/sa, 742 GB boş ≈ 5 gün;
7 gün için kullanıcı birini kapatmalı (kill onayı gerekir). İlgili: [[project_derin_merdiven_v4_20260918]],
[[project_bosona_cift_maliyeti_cozuldu_20260918]].
