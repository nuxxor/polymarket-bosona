# Kısa karar özeti — Bosona BTC15dk (Fable, 21 Eylül 2026)

**Sonuç tek cümleyle:** Bosona'nın BTC15dk kârı "doğru anda alım kararı" veren bir stratejiden değil, sürekli taze alış kotasyonları koyup (maker, ücretsiz) bunlar vurulunca biriken pozisyonu gerektiğinde spread'i geçerek (taker) dengeleyen bir piyasa yapıcıdan geliyor; bizim aday ise ücret ödeyerek alan, tek bir anda karar veren bir alıcı. Aynı şeyi ölçmüyoruz.

## En önemli 5 bulgu

1. **Dolumların çoğu pasif.** 5.441 BTC15dk dolumunun 4.387'si maker (ücret ödenmemiş), 1.054'ü taker. "Geç ekleme" dediğimiz 1.173 dolumun 1.099'u maker. Sınıflandırma sunucu bayrağıyla 156/156, zincir kayıtlarıyla 303/303 uyuştu. Yani "600. saniyede ekleme kararı" diye bir şey yok; önceden konmuş bid'ler vuruluyor.
2. **Aday yanlış problemi çözüyor.** Aday %100 taker varsayıyor ve t=180'de olasılık modeliyle giriyor. Ama Bosona'nın ilk alımlarının 557/598'i maker; olasılık modeli de ilk 10 dakikada piyasa fiyatından daha kötü kalibre (yalnız son 5 dakikada daha iyi). Gerçek defterde aday 14 piyasada 2 kez girdi, −1,30 $.
3. **Geç ekleme kârı 10 piyasaya yığılı.** +2.926 $'ın en iyi 10 piyasa dışındaki kısmı −5 $. Toplam BTC15dk kârının %86'sı 10 piyasadan; en iyi 20 hariç −1.848 $. Yeni gerçek defterli dönemde geç ekleme −254 $ (14 piyasa); sonraki 10 piyasada Bosona toplam +310 $ ama bu taker dolumlarından (+322 $), maker −12 $ ve geç maker ekleme −20 $.
4. **Kotasyonlar taze ve saniyeler içinde vuruluyor.** Dolum fiyatındaki seviye çoğu zaman dolumdan 1–4 saniye önce beliriyor (seviye yaşı medyan 4 sn); aynı emrin dolumları en fazla 9 saniyeye yayılıyor. Kuyruk önceliği belirleyici ama 1 saniyelik REST defter kaydıyla ölçülemiyor. Kendi kotasyonlarımızı kuyruk sonuna koyduğumuz replay'de dolumların 88/94'ü yalnız fiyat seviyeyi aşınca gerçekleşti (yani hep ters yönde).
5. **Eski kontroller yapısal olarak kusurlu.** Replay gelecekteki fiyata bakıp işlemi atlıyor; kazanan–kaybeden eşleştirmesinin kaliperleri sonuçtan sonra seçilmiş ve sonuç kalipere göre işaret değiştiriyor; "ekleme yok" kontrolü aslında "satıcı gelmedi" demek.

## Hangi eski iddia değişti

- "BTC15dk geç eklemelerinde tekrar eden avantaj var" → yoğunlaşmış, yeni dönemde ters; mekanizma pasif dolum.
- "Tamamlama ucuz çift için" → tamamlamalar ağırlıkla taker ve nakit-PnL'de negatif (−3.085 $), ama en kötü sonucu 895 kayıttan 870'inde iyileştiriyor: risk azaltımı.
- "H1/H2 açıklama modelleri" → etiketleri dolum olduğu için karar değil akış tahmin ediyorlar.

## Ne kadar yakınız

Mekanizma ailesi belli (pasif taze kotasyon + taker hedge). Kâr üreten fiyat/boy/iptal kuralı ve kuyruk önceliği bu veriyle **tanımlanamıyor**: aynı dolumları birden fazla kotasyon kuralı üretebilir; emir yerleştirme/iptal zamanları kamu verisinde yok.

## Önce ne yapılmalı

1. Adayın t=180 taker tasarımını bırak (donmuş dosya aynen kalır; yeni sürüm ayrı).
2. Her dolum tablosuna maker/taker etiketini ekle (`code/role_classifier.py`) ve eski karşılaştırmaları rol ayrımıyla yeniden kur.
3. Tek deney: WebSocket L2 delta + kamu piyasa-geneli işlem baskısı kaydıyla kuyruk-konumlu pasif kotasyon replay'i (kötümser/iyimser dolum sınırları; kollar ve kabul kapısı `RAPOR_FABLE.md` bölüm 7; kod `code/passive_replay.py` hazır). Mevcut 1 sn REST bandı bu soru için yetersiz.

Mevcut REST bandıyla ön sonuç (24 piyasa, tek gün, karar için yetersiz): dokunuşa pasif kotasyon S döneminde kötümser −6,85 / iyimser +9,55 $; kör 10 piyasada kötümser +9,15 (en iyi 3 hariç −4,30) / iyimser −2,60 $; aday gerçek defterde 24 piyasada 2 giriş. Denetim: 263 ajan, 110 bulgu, 91'i üç mercekli karşıt doğrulamadan geçti; çürütülen 19 bulgu rapora yansıtılmadı veya düzeltildi.

Ayrıntı: `RAPOR_FABLE.md`. Kaynak, hash ve komutlar orada.
