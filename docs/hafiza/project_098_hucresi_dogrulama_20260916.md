---
name: project-098-hucresi-dogrulama-20260916
description: 0,98-1,00 gec-favori hucresi — rekabet ve tamamlayici likidite sorulari KAPANDI, kenar saglam; kalan tek kapi dolum-kosullu kuyruk riski (0/59)
metadata:
  type: project
---

`data/analysis/pm_098_dogrulama_20260916_v1/SONUC.md` — 1.844 pencere / 5 coin / 4 gun.
Kural: t=S+270'te favori best_bid 0,98-1,00 ise o fiyata post-only alis, kuyrugun
arkasina, 297'de iptal. Hucreye dusen 630 emir.

**Q2 CEVAP — duzeltme gerekmiyor.** PM defteri ZATEN AYNALI: Up bid@p ile
Down ask@(1-p) her seviyede birebir ayni (630/630 tam esitlik, tum merdiven boyunca).
Olculen kuyruk zaten birlesik kuyruktu; toplamak cift sayim olurdu.
Bu, gelecekteki her kuyruk hesabi icin gecerli: **tamamlayici likiditeyi AYRICA EKLEME.**

**Q1 CEVAP — saglam.** Kuyrugu 3x buyutup tasmanin yalnizca %25'ini alsak bile
kenar +1,03 kr/pay; taban senaryo +0,95 GA[+0,85,+1,10], 4/4 gun artida, dolan
kayip 0. Sebep: kenar dolum SAYISINA bagli degil, her dolum kazaniyor.
Kapasite: 162.271 pay = +$800/4 gun (~$200/gun); en kotu senaryoda ~$27/gun.

**KALAN TEK KAPI (yeni, asil olan):** odenen 0,9905 -> kazanan +0,95 kr,
kaybeden -99 kr; basabas kayip orani %0,95.
- populasyon 0/630 -> %95 ust sinir %0,48 GECER
- **dolum-kosullu 0/59 -> %95 ust sinir %5,08 GECMEZ**
Ters secim gorulmedi ama 59 dolumla kurulamiyor. ~315 dolmus pencere gerekiyor
(~21 gun, 5 payla ~15 dolum/gun). Iki yol: kayitciyi 3 hafta daha calistir (risksiz)
veya 5 paylik canli pilot (pencere basina azami kayip $4,95, beklenen ~$0,71/gun,
KAR icin degil KAPI icin). Olcek ancak bundan SONRA.

Ilgili: [[project-bosona-gec-favori-20260916]] (hucrenin kaynagi),
[[project-delta-tarama-kapanis-20260916]] (ayni motor, base.py politikasi olu)


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🟡 0,98 HÜCRESİ — İKİ SORU KAPANDI, ÜÇÜNCÜSÜ AÇILDI (09-16): PM defteri ZATEN AYNALI (Up bid@p ≡ Down ask@1−p birebir, 630/630) → tamamlayıcı likiditeyi ayrıca EKLEME; rekabet sağlam (kuyruk 3x + taşmanın %25i → hâlâ +1,03 kr/pay, 4/4 gün, 0 kayıp); kapasite ~$200/gün; KALAN KAPI: dolum-koşullu kuyruk riski 0/59 → üst sınır %5,08 vs başabaş %0,95, ~315 dolum (~21 gün) gerek](project_098_hucresi_dogrulama_20260916.md)
