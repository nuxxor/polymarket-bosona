---
name: project-codex-artir-kurali-cozumleme-20260915
description: Codex v2 "artır kuralı" adayı çözüldü — sinyal eksi kenarlı, +$267'yi üreten envanter kapısı (bahis yoğunlaştırıcı); mekanizma "kim işlem yapacak ≠ ne kazanacak"
metadata:
  type: project
---

Codex `data/analysis/pm_actor_rule_reconstruction_20260915_v2` üç dönem bildirdi
(24-26 Ağu −$99,71 / 27 Ağu-1 Eyl +$267,18 / 2-4 Eyl donmuş model +$12,38).
Opus bağımsız çözümledi (detay: `data/analysis/KAPANIS_BTC5M_MAKER_20260915.md` §22).

**Üç dönem tek sayı:** kural hep ~44,7 sente alıyor; taker başabaş tutturma %46,3.
Tutturma %42,0/%48,2/%46,6 → $267 ile −$99 arası sadece 6 puanlık tutturma farkı.

**Ücret kârın iki katı:** 11 gün/1.830 market/21.660 pay → brüt +2,44, taker ücreti
−1,61 ($347,78), net +0,83 kr/pay, GA [−0,92,+2,76]. Kazanç $180, ücret $348.

**BELİRLEYİCİ — sinyal eksi:** PREDICTIONS.parquet niyet düzeyinde (kasa kısıtı ve
envanter kapısı YOK), 12.585 imitatör seçimi: brüt −0,89 / net −2,50 kr/pay,
GA [−3,12,−1,87]. Her fiyat bandında eksi. Codex'in −0,867'si tekrarlandı.

**GERİ ÇEKİLEN İDDİALAR (Codex denetimi, Opus kendi hesabıyla doğruladı):**
(a) "model seçmemekten kötüsünü seçiyor" ÇÜRÜDÜ — gün×2kr fiyat×30sn yaş
eşleştirmesinde fark −0,44 kr/pay GA [−1,18,+0,45], sıfırı kapsıyor.
(b) "+$267'nin tamamı bahis yoğunlaştırmasından" DOĞRULANMADI — yalnız-ilk-alım
(biriktirme yok): val −2,36 / test +0,41 / havuz −0,61 [−2,04,+0,83]; Codex replay'i
−1,36/+0,60/+1,01 ile işaretler uyuşuyor. Artı sonuç biriktirmeden de oluşuyor.
(c) "aktörler maker, ücret ödemez" YANLIŞ — whiskas hacminin ~%75'i TAKER
(bkz [[project-whiskas-rebate-reconciliation-20260910]]).
(d) "isabet−fiyat−ücret daha hızlı oturan ölçüt" YANLIŞ — cebirsel olarak pay başına
PnL'in kendisi; yorum için yararlı, istatistiksel güç için değil.

**KAPININ GERÇEK MEKANİZMASI (niyet düzeyi, kasa yolu ve yoğunlaşma YOK):**
İLK alım −0,16 [−1,52,+1,24] | SONRAKİ aynı yön −1,88 [−4,09,+1,33] |
SONRAKİ ters yön **−4,09 [−7,92,−1,40]** | ARTIR−AZALT +2,21 [−2,52,+9,05].
Kapı boş iş yapmıyor: engellediği şey (ters yön sonraki alımlar) ölçülebilir biçimde
kötü — tüm sette GA'sı sıfırı dışlayan TEK etki bu. Ama kapının faydasının kendisi
kanıtlanmış değil (fark GA'sı sıfırı kapsıyor), Codex'in aktör verisindeki
+1,827 [−0,625,+4,092] bulgusuyla aynı sınıfta.

**Sağ kalan yapı:** yalnız-ilk-alım net −0,16 → BRÜT ≈ +1,6 kr/pay (p≈0,46'da taker
ücreti ~1,74). Kenar var ama ücret kadar; bağlayıcı kısıt ÜCRET.

**Tek sağ kalan + TETİK:** piyasa-geneli ucuz taraf +0,85 kr/pay brüt (ort. 0,272,
136.801 karar, model gerekmez, favori-longshot sapması). Engel maliyet: o bantta
taker ücreti 1,38 kr/pay. AÇIK SORU = 0,20-0,35 bandında MAKER dolum kenarı; bizim
−5,26 kr/pay ölçümümüz tüm fiyatların havuzuydu, bu bant ayrı ölçülmedi, veri diskte.
Bu bantta maker kenarı GA'sı sıfırın üstünde kalırsa kulvar açılır.

ÖLÇÜT hatırlatması: bu tezgâhta >1 kr/pay gösteren backtest presümtif olarak hatalıdır.


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [⚖️ CODEX "ARTIR KURALI" — AÇIK, ÇÖZÜLMEDİ (09-15): saf imitatör biriktirmeli −2,50 kr/pay GA[−3,13,−1,85] ZAYIF; ama 3 iddiam GERİ ÇEKİLDİ (eşleştirmede "kötüsünü seçiyor" −0,44 GA sıfırı kapsıyor; yalnız-ilk-alım da artı verebiliyor → yoğunlaştırma tek açıklama DEĞİL; whiskas %75 TAKER, "maker ücret ödemez" yanlış); kapı boş iş yapmıyor: ters-yön sonraki alımlar −4,09 GA[−7,92,−1,40] tek sıfır-dışlayan etki; ilk-alım net −0,16 → brüt ≈+1,6, BAĞLAYICI KISIT ÜCRET](project_codex_artir_kurali_cozumleme_20260915.md)
