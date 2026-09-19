---
name: project-bulgu-raporu-refute-20260914
description: Kardeş oturumun BULGU_RAPORU (bayat-emir iptali CEK=0,05 → +2,80/+3,14¢ "ilk tekrarlanan bulgu") denetimi: teşhis DOĞRU (whiskas maker modeli, kayıp artan envanterde), tedavi boyu ÇÜRÜDÜ (aynı-süpürme saat artefaktı + 9-konfig seçimi; dürüst motorda +0,1…+0,9¢, GA sıfırı kapsıyor)
metadata:
  type: project
---

**2026-09-14 gece.** Rapor `data/analysis/BULGU_RAPORU_20260914.md`; kod `pm_actor_model_20260914_v1/sim8.py`,
`pm_multi_tape_20260914_v1/tape_sim3.py`. Denetim paketi `pm_bulgu_refute_20260914_v1/` (core/same_sweep.py,
core/tape_honest.py, 4 hakem klasörü, VERDICT_TR.md).

**Doğru (kendi defterimle):** whiskas maker-only defteri tek başına artı (+3,57¢/çift, %75 maker-maker eşleşme,
artan −0,98¢, ≈+$1.100/gün); mo-money/bosona yön seçici; kaybımız artan envanterde.
**Çürüyen:** (1) Feed'de süpürmenin best_bid-düşüş mesajı, aynı süpürmenin print'inden %99,9 oranında ~100 ms ÖNCE
geliyor (65k süpürme, src ve rcv) → sıfır gecikmeli iptal olmuş dolumdan kaçıyor; "kenar <200 ms'de yaşıyor" eğrisi
bu artefaktın sönmesi. (2) 9 konfigürasyon taranmış, 4/9 artı; bölüm 6 (merdiven) CEK 5¢ = −1,46, bölüm 7 (tek
emir) +2,80 — farklı taban. (3) Taze tape 400 ms'de +0,30 [−6,98,+8,52]; üst 3 pencere kârın %925'i. (4) tape_sim3
bilgiyi geciktiriyor, icrayı değil.
**Benim dürüst motorum:** Londra 156 pencere: iptalsiz +1,02; tetik ≥300/500 ms eski (aynı süpürmeden kaçamaz) +1,64/+2,17;
eşleştirilmiş fark +0,1…+0,95¢, GA hepsi sıfırı kapsıyor, 8-24 pencere etkileniyor. Bugünkü tape (158 pencere):
taban −2,03; CEK Türkiye gecikmesi +0,68 [−1,47,+2,90]. → mekanizma küçük/olası, kanıt yok; hız değil örneklem eksik.
**Karar:** raporun dondurduğu kural, dürüst motorla (tetik yaşı ≥ RTT, aynı-süpürme kaçışı yasak) her gün tape'e
uygulanacak; ~5 günde ~100 etkilenen pencere; GA sıfırın üstüne çıkmazsa kapanış. Londra harcaması öncesi bu.
Ders: [[project-actor-breakthrough-tour-20260914]], lessons 09-14 (PC-before-TR).


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [⚖️ BULGU RAPORU DENETİMİ (09-14 gece): kardeş oturumun 'bayat iptal +2,80/+3,14 ilk tekrarlanan bulgu' iddiası — teşhis doğru (whiskas maker modeli), boy çürüdü: aynı-süpürme saat artefaktı (PC düşüş mesajı print'ten ~100 ms önce, %99,9), 9-konfig seçimi, taze 400 ms +0,30 GA[−7,+8,5]; dürüst motor +0,1…+0,9¢ GA sıfır; kural dürüst motorla 5 gün tape'te izlenecek](project_bulgu_raporu_refute_20260914.md)
