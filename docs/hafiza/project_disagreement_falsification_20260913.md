---
name: project-disagreement-falsification-20260913
description: "Aktörler uyuşmazlık pencerelerinde gizli bilgi okuyor" hipotezi üç kontrolde de çürüdü
metadata:
  type: project
---

2026-09-13: Aktörlerin (tmsd-test, mo-money, bosona, nagi777) kârının, Binance vekilinin gerçek
Chainlink sonucundan ayrıştığı %3,34'lük pencerelerde yoğunlaştığı bulundu (tmsd'nin net kârının
TAMAMI orada). Ön-kayıtlı üç kontrolün üçü de hipotezi çürüttü:

1. **Popülasyon:** O pencerelerde iki taraflı alan HERKES +0,94¢ kazanıyor (tüm maker nüfusu).
   Kalabalık −1,56¢ kaybediyor. Kârın bir kısmı bilgi değil, aritmetik.
2. **Yakınlık:** Uyuşmazlık pencerelerinin medyan sonuç farkı 1,02; uyumlularda 37,24 →
   "uyuşmazlık" aslında "kıl payı pencere"nin kılığı. Yakınlık sabitlenince aktör fazlası
   +0,6…+1,8¢'e düşüyor ≈ mekanik taban (+0,94¢).
3. **Zamanlama (belirleyici):** Kenar pencerenin İLK dakikasında en yüksek (mo-money +12,23¢).
   t=30s'te settlement okunamaz — o veri henüz yok. Bilgi hipoteziyle bağdaşmıyor.

Ek: uyuşmazlık pencerelerinde son dakikada kazanan tokenin ortalama fiyatı 0,727 — piyasa
yanlış tarafı ucuza satmıyor, sömürülecek bariz yanlış fiyat yok.

**Why:** Bu, "aktörlerin sırrı = gizli veri kaynağı" fikrinin sonu. Kenarları pencerenin
başında ve geniş sonuçlu pencerelerde de var → kâr sonucu bilmekten değil, **sürekli iki taraflı
kotasyondan ve nerede kota verdiklerinden** geliyor. `pm_fill_diff_vs_actors_20260913_v1` ile
aynı yeri işaret ediyor: fark "hangi dolumu aldığımız" değil, "nereye kota verdiğimiz".

**How to apply:** Paket `data/analysis/pm_disagreement_falsification_20260913_v1/`
(CONTRACT.md sonuçlardan önce yazıldı; `evidence.py` tüm tabloları sıfırdan üretir → EVIDENCE.json).
Bu hipotezi tekrar açma. Devam yönü [[project-chainlink-streams-unlocked-20260913]].


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [❌ UYUŞMAZLIK HİPOTEZİ ÇÜRÜDÜ (09-13): 'aktörler gizli kaynak okuyor' 3/3 kontrolde kaldı — mekanik taban +0,94¢ (tüm makerlar), 'uyuşmazlık'=kıl payı pencere kılığı, kenar pencerenin İLK dakikasında en yüksek (settlement daha okunamaz); kâr = nerede kota verdikleri](project_disagreement_falsification_20260913.md)
