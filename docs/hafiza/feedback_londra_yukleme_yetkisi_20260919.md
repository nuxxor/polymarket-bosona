---
name: feedback-londra-yukleme-yetkisi-20260919
description: "Operatör 09-19 23:10Z — \"bundan sonra Londra'ya olacak her şey ve sormana gerek yok\"; bot değişiklikleri Londra sunucusuna sormadan yüklenir (ön kayıt + test şartıyla)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0e095c2e-d109-4b41-8066-a0b2005c3a13
  modified: 2026-09-19T23:06:03.743Z
---

**Kural (operatör, 2026-09-19 23:10Z):** Canlı bot Londra sunucusunda çalışır; ab.py değişiklikleri
ön kayıt yazılıp `--test` geçtikten sonra **sorulmadan** Londra'ya yüklenir (`scripts/izleme/londra_yukle.sh`:
scp → STOP ile temiz kapanış → yeniden başlat → SURUM doğrula). Yerelde canlı bot asla başlatılmaz.

**Why:** Operatör hızlı döngü istiyor ("15-20 dk'da bir kontrol", "canlıda çözelim"); her yükleme için onay
beklemek pencere kaybettiriyor.

**How to apply:** Kural değişikliği yine ÖN KAYIT ister (ONKAYIT dosyasına vN notu) ve testler geçmeli;
sonra yükle ve kısa raporla (ne değişti, sha, saat). Kill koşulları/risk tavanları değişiyorsa yine de bildir.
İlgili: [[project-devir-ve-ortam-20260919]]
