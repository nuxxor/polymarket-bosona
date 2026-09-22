# Karar — BTC15dk bağımsız denetim

**Bosona'nın stratejisi çözülmedi; fakat yanlış modellediğimiz noktalar somutlaştı. Yeni bot veya eşik değişikliği için ekonomik kanıt yok.**

1. **Dolum, karar değil.** Dört BTC15dk piyasasında 42 kamu kaydı 26 imzalı emre ayrıldı. Bir emir yedi parçayla hem yön değiştirme hem ekleme gibi görünüyor. Buna karşılık zarar eden piyasada ayrı 300 paylık taker alımları var: bütün davranış eski pasif emirle açıklanamıyor.
2. **Toplam kâr doğru, bazı etiketler ve envanter girdileri yanlış.** 3.503 piyasanın +13.393,82 doları yeniden üretildi. İlk alış parçaları geç eklemeye karışmış; MERGE sonrası denge 788 durumda yanlış hesaplanmış. Ayrıca piyasa kimliği eksik anahtar, toplam 575 dolarlık 10 MERGE kaydını kaybettirmiş. Bu son hata PnL'yi değiştirmiyor, nakit/pozisyon akışını eksiltiyor.
3. **“Geç ekleme kazandırıyor” bağımsız kural değil.** Düzeltilmiş tarihsel katkı +3.364,65 dolar; piyasa başına eşit nakitle −69,92 dolar. Yeni 14 tam pencerede −254,17; genişletilmiş 16 pencerede −329,59 dolar. Boy, seçilim ve dolum fiyatı sonucu değiştiriyor.
4. **Mevcut adayın temel farkı ilk giriş ve kendi pozisyon yolu.** Gerçek defterli 14 pencerelik yerel simülasyonda iki giriş, sıfır ekleme ve −1,30 dolar oluştu. Aynı girişleri tutma +0,78 dolar. Veri/zaman düzeltmesi bu küçük sonucu değiştiriyor; hiçbiri başarı kabulü değil.
5. **Önce veri ve gözlem birimini düzelt; sonra tek emir-kimliği deneyini büyüt.** Sonuçtan bağımsız seçilmiş piyasaların bütün dolumlarını parent/rol/risk düzeyinde izle. İptal ve dolmayan emir görülmeden maker kârı uydurma. Yeni canlı/shadow veya kaydedici başlatılmadı; donmuş aday ve protokol aynı.

[Ayrıntılı rapor](RAPOR.md) · [Hatalar ve düzeltmeler](HATALAR.md) · [Tek sonraki deney](DENEY.md) · [Tekrar çalıştırma](README.md)
