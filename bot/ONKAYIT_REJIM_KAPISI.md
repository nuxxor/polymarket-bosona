# ÖN KAYIT — Rejim Kapısı
## SÜRÜM 2 (2026-09-18 19:50 UTC) — v1 İHLAL EDİLDİ, bu belge onu düzeltir

### Önce: v1'e ne oldu
v1 (18:10 UTC) şunu yazıyordu:

> "Kod DEĞİŞMİYOR. Kol ataması rastgele kalıyor (A %25 / B %75). Kapı yalnızca
> sonradan hesaplanıp değerlendirilecek — davranışı etkilemeyecek."

**18:13'te kolu deterministik seçen kodu canlıya aldım ve bu belgeyi güncellemedim.**
Paket dış denetime bu çelişkiyle gitti; denetim bunu `ab.py` satır 677 ve 704-709
ile `LOG 1391` (18:15:05 ilk gerçek kapı ataması) üzerinden doğruladı.

Sonucu somut ve geri alınamaz: 18:15'ten sonra **yüksek oynaklıkta B ve düşük
oynaklıkta A gözlemi ÜRETİLMEDİ**. Bu yüzden o pencerelerden kapının rastgele
atamaya kattığı değer ölçülemez. Elde kalan şey, sabit kapılı politikanın
mutlak getirisidir — bir A/B karşılaştırması değil.

**Doğru etiket: bu bir deney değil, PİLOT.** Aşağısı buna göre yazılmıştır.

---

## Ölçülecek şey
Sabit kapılı politikanın (oynaklık >= 16.4 bps -> A, altı -> B) **mutlak**
pencere başına net USD getirisi. Kapının katkısı DEĞİL.

## Dondurulmuş kural
    oynaklik_bps = 1e4 * (max(high) - min(low)) / open[0]
    Binance fapi 1dk mumlari, [S-300, S) araligi, 5 tamamlanmis mum
    >= 16.4  -> A   |   < 16.4  -> B   |   olculemezse -> rastgele (KAPI_DUSTU)
Eşik 16.4 bps donduruldu. Bu eşik 18 Eylül verisinin MEDYANINDAN seçildi —
yani in-sample'dır ve bu pilotun bir çıktısı değil, girdisidir.

## Başlangıç
İlk gerçek kapı ataması: **S=1789755300, 18:15:05 UTC**.
Sayım "bu andan sonra ATANAN" pencerelerle yapılır — "bu andan sonra çözülen"
ile değil (18:10'da atanıp 18:18'de çözülen pencere bu pilota ait DEĞİLDİR).

## Neyi kanıtlayamaz
- Kapının rastgele atamaya üstünlüğünü (karşı-olgu üretilmiyor).
- Aynı rejimde öteki kolun ne yapacağını.
- 18:15 öncesi verilerle karşılaştırma: atama olasılığı 17:00 öncesi %50,
  sonrası %25'ti. Düzeltilmemiş havuz karşılaştırması GEÇERSİZDİR; gerekiyorsa
  ters-olasılık ağırlığı (IPW) ile yapılır:
      V(g) = (1/N) * SUM_i [ 1{A_i = g(X_i)} * R_i / pi_i(A_i) ]

## Durdurma ve değerlendirme
- Kontrol noktası: kapı sonrası **40 atanmış pencere**.
- Sonuç üç kategoriden biri olarak kaydedilir: **belirgin artı / belirgin eksi /
  BELİRSİZ**. Güven aralığı sıfırı kapsıyorsa sonuç BELİRSİZ yazılır —
  "işaret pozitif, demek ki çalışıyor" YASAK.
- Para sınırı önceden: bu pilot için azami **$40** kümülatif kayıp. Tükenirse
  pilot biter; sayaç sıfırlanıp yeni aday eklenmez.
- Sıfır dolumlu ve atlanan pencereler de kayda girer (seçim yanlılığı önlemi).

## Bu belge değişirse
Kural veya protokol değişecekse **önce burası yeniden yazılır, sonra kod**.
v1'de bunun tersi yapıldı; tekrarı playbook #52'de yasaklandı.
