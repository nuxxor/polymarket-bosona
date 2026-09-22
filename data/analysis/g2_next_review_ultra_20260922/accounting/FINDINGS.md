# Ultra — muhasebe ve parent alt denetimi

Bu alt çalışma tamamen çevrimdışı; yeni G2/Fable incelemesi okunmadı. Sonuçlar `audit.py` ile ham geçmiş ve receipt'lerden yeniden üretildi. Üretim kodu, deney parametresi ve donmuş çıktı değiştirilmedi. Ana raporun karar-öncesi bağlam incelemesine muhasebe temeli sağlar; burada tetikleyici keşfedildiği iddia edilmez.

## Doğrulanan evren ve muhasebe

36 bitişik/tam activity parçasında ana piyasa evreni 1.842 gözlenen piyasa, 2.286 takvim slotu, 19.768 BUY. Eski birleşik activity/ledger 19.761'e düşüyordu: yedi gerçek tekrarın kaybı, toplam sonuca **+$6,21 yapay artış** vermiş. Ham çoklukla alış nakdi $375.049,792805; kazanan token ödemesi $383.363,021269; sonuç **+$8.313,228464**. Yedi işlem kimliği `results.json → historical.real_multiplicity_correction` içinde. İade/sabit gider dışarıda; bütün hesap geliri değil. Ana arşivde 383 MERGE, 3.309 REDEEM var; tam piyasa muhasebesi R1 alt kümesinde ayrıca denetlendi. 36 BUY'ın kamu saati piyasa sonuna eşit/sonra: bu gerçek emir zamanı veya kapanış sonrası işlem kanıtı değildir.

R1 hash seçimini pencere listesinden yeniden kurdum: gün başına sekiz, toplam64; 66 geç-ekleme ve14 tanısal piyasa örtüşerek137 oluşturuyor. 2.041 receipt baştan decode edildi: 2.066 dolum,986 parent,96.059,619427 pay; **$47.351,874451 gerçek transfer nakdi**, bunun içinde **$218,732940 receipt fee**. API ve zincir nakdi farkı toplamda ve her transaction/token grubunda tam0; yeni fee tahmini veya rebate eklenmedi.

137 tam activity geçmişindeki2.066 BUY,51 MERGE,256 REDEEM mikro-birim tamsayılarla yürütüldü. Her piyasada `N + U*Y + D*(1-Y)` tam uzlaşıyor; negatif gözlenen token bakiyesi yok. Pencere öncesi BUY/taşınan gözlenen envanter0. Bu, bütün cüzdanın başlangıç zincir bakiyesinin0 olduğunu veya dış transfer bulunmadığını ispatlamaz; MERGE/REDEEM receipt'leri ayrıca çözülmedi. Tam API geçmişi ile tüm zincir bakiyesi kanıtı farklı kapsamdır.

## Sayım, miktar ve yeniden risk açılması

64'lük örnekte305 parent;262 sınıflı,43 sıra/zaman belirsiz. Maker230 =67open+101add+48reduce+14reverse; taker30 =2open+2add+26reduce; mixed2reduce. Ana sınıflandırma aynen korundu. 26taker azaltımı22piyasada; t24–286, medyan152; kapanan pay medyanı%99,9209874, ≥%99 olan15.

**Yeni güçlü ayrım:** 26'nın14'ünde `q = floor(abs(net)*100)/100` tam eşit. Beşinde gerçek tamsayı sıfır; dokuzunda0–0,01pay arası toz kalıyor. ≥%99 grubundaki15'inci örnek1,033077pay artık bırakıyor; aynı yuvarlama açıklamasına zorlanmadı. Sınıflı26taker parent'ın tamamının tüm gözlenen dolum ömrü aynı kamu saniyesi: ilk grup miktarıyla tam parent miktarı eşit. Bu örneklerde eski aynı-parent devamı açıklaması elenir; gönderim zamanı/tam gönderilmiş miktar/emir türü yine bilinmiyor. İki ondalık pay kuralıyla uyum, Bosona'nın belirli SDK/FOK/FAK kullandığı kanıtı değildir.

14tam-yuvarlama kapanışının10'unda daha sonra farklı bir parent ilk kez doluyor: dört eski taşınan yönde, altı karşı yönde;9–131sn sonra, dokuz maker/bir taker. Beş exact-flat kapanışın dördünde; dokuz toz bırakanın altısında bu yol var. ≥%99olan15'in tamamında11sonraki parent var. Bu **pencereyi terk eden kalıcı stop** açıklamasına ters kanıt; pozisyonu yeniden ayarlama açıklamasıyla uyumlu. Fakat sonraki parent daha önce gönderilmiş de olabilir: yeni ilk dolum, yeni emir gönderimi demek değildir.

Tamsayı toz ayrıca etiketleri yanıltabiliyor:14maker `reverse` olayının sekizi0,01paydan küçük,11'i5paydan küçük önceki neti aşıyor. Bunları büyük yön dönüşü saymak yanıltıcıdır. Ana sayım değiştirilmedi; `strict_maker_reverse_sensitivity` büyüklük duyarlılığını ayrı verir.

43belirsizdeki8taker için parent-first-second toplamlarını bölmeden tüm parent permütasyonları denendi: altısı her permütasyonda `reduce`; biri `reduce/reverse`; biri t303. Bu sınırlı duyarlılık, aynı parent içi parçaların iç içe sırasını veya gerçek placement saatini çözmez; ana262/43 dışlamasını kaldırmaz. Mevcut%68,4–89,5kabaca tanımlama aralığı ekonomik veya istatistiksel güven aralığı değildir.

## Ekonomik katkı ve karşıörnekler

Bağımsız Fraction hesabı32geçerli ilk azaltım,23azaltan dolum gözlenmeyen piyasa,9belirsiz sonucunu aynen verdi. İlk azaltımı taker15'in10'unda en ucuz eski lotla bile çift maliyeti>1. Yerel close-hold toplamı **+$273,91252**; en iyi3çıkarılınca **−$9,57836**. Bu15'in10'u olumlu/5'i olumsuz;15Eylül+$145,31935, toplamın%53,05'i. Bütün55hesaplanabilir piyasada **+$165,37045216**, en iyi3hariç **−$153,78977784**; sabit tohumlu10.000gün-blok toplam bootstrap aralığı[−$204,63448,+$508,89154]. Tarihsel ve aktör aksiyonuna koşullu; bağımsız politika değeri değil. 26ayrı parent azaltımının yerel fark toplamı+$214,76770 da aynı portföyün karşıolgusal PnL'si sayılamaz; aynı piyasalardaki ardışık aktör aksiyonları farklı başlangıç envanterlerine zorla taşınmadı.

Tanısal uç örnekler sonuç görüldükten sonra seçildi; başarı oranı tahmini değildir. Tam kimlikler ve tüm piyasa yolları `diagnostic_cases` içinde:

- **Yararlı kapanış,1789456200/t211:**150,700268Up'a karşı148Down, nakit/pay0,095732973. Down sonucu kapanışın yerel farkı+$133,83152; gerçek bütün piyasa sonucu+$65,047699. Parent `0x3b84211bbdbdfc395d345e84de2ba6f3872d2fcc301c58b58a61574af0eddcdc`; tx `0x19002fa1caae1a4de84598074aebc6b6caa97717ea1ddfcdc174d48261ae0233`.
- **Zararlı kapanış,1789924800/t123:**84,221821Down'a karşı84,22Up, nakit/pay0,704972928; en ucuz çift1,374972939. Down kazanınca yerel fark−$59,37282; sonraki gerçek işlemlerle bütün piyasa+$100,39038. Toplam kazanç, bu kapanışın katkısını olumlu yapmıyor. Parent `0x1abceb8e28dcd9d9df1d111039d66b6c0d6e41b3c30e0418484bc420989974df`; tx `0x2fdea257fffec4270141306a7d9039a8ba72ac30fecf0e094b413a45ce4845f6`.
- **Taşıma kazancı,1789580400:**t16–93arasında altı maker parent,510,059147Down, karşı alış yok;+$378,071972. t93tek297pay parent `0xcdf7d678459a416631f398f5f629737a0cf2a4b46de9609a9ce6944df4463eed`, tx `0x1ff68a63d9b7be2597f454db4e257c664999faddfdbc623a6bc1a5d77dd5c170`.
- **Taşıma kaybı,1789739700:**t11'de499Up@0,20, t81'de14Up@0,11; iki maker parent, karşı alış yok;−$101,34. İlk parent `0xeebde346ed97a9d196006607dc2f1038813c3ec621851458a20379b22236b2fc`; ilk iki tx `0x2f731d0cbafde0f596e68b0abbb7a541f2f5f7207c29215dfeb75e013c56f470`, `0x5ea87835487f798b68cfbd23cf0302cd83050db459ab025347baf3132c330812`.
- **Kalıcı stop karşıörneği,1789468500:**t145'te21Up@0,56maker; t169'da21Down, nakit0,5175taker ile tam sıfır; çift1,0775. **t178'de aynı0,5175nakit/paydan148Down yeni taker parent**: kapanıştan9sn sonra çok daha büyük ters net. Kapanış parent `0x50a191362345627c1137113cee4a186cfc50f5e21eb0cd21022bbc7f594e8e75`, tx `0x2102dbbdcda563c858cc419e05530786d3287775c2f8300cbcf6f04a7dd51ec1`; yeni parent `0x974d03abd0c6e4f4881beababdbcba301e84b713db80192487e2a5c766857a03`, tx `0x1c7db2f55424fc351b9f24302ac91f07fda9583d25034814774942a27b231639`.

Kaynaklar: `data/analysis/btc5m_parent_research_20260921/full_activity/<S>.json`, `markets.json` ve `receipts/<tx>.json`. Gözlenmeyen karşı dolum, hedge etmeme kararı veya karşı emir yokluğu değildir. Üstteki saatler kamu dolum saatidir; önceden bilinen fiyat bağlamı yerine kullanılamaz.

## Gerçekten çalıştırılan kontroller

`python3 .../accounting/audit.py`: ham çokluk,64hash seçimi,2.041receipt transfer doğrulaması,137tam hesap, bağımsız ilk azaltım hesabı,262/43sınıflama, miktar yuvarlama, sonraki parent yolları, permütasyon duyarlılığı; sınıflandırıcı regresyonları ve sentetik nakit/sonuç kontrolleri. Hedefli `python3 -m ruff check .../audit.py` ve bellekte `compile()` geçti. Tam ikinci çalıştırma byte-identical `results.json` verdi; SHA ve kanıt `verification.json` içinde. Eski `analyze.py/check.py` giriş noktaları çalıştırılmadı; salt-okunur saf decoder/classifier fonksiyonları yeniden kullanıldı.
