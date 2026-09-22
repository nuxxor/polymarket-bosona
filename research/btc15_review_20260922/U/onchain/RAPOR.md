# BTC15dk: API satırı, parent emir ve rol ayrımı

**DOĞRULANDI:** S içinden önceden seçilmiş dört BTC15dk piyasasında 42 API satırı / 42 transaction, 42 Bosona `OrderFilled` ve **26 farklı orderHash** var. 38 dolum maker, 4 dolum taker; 2.554,614330 payın %66,5883'ü maker. Tüm miktar, 1.120,123201 dolar nakit ve resmî sonuç PnL'leri gerçek CTF/pUSD transferleriyle uzlaştı. Bunlar seçilmiş bilinen vakalar; BTC15dk genel maker oranı veya bağımsız test sonucu değildir.

**GÖZLEMSEL DESTEK:** Bazı “eklemeler” tek emrin parçaları. **KARŞI KANIT:** Zarar piyasasındaki 18 geç dolum hâlâ 14 ayrı parent içeriyor; ikisi taker. Bütün geç risk artışını eski ilk emrin pasif devamı saymak bu örneklerde yanlış.

## Seçim ve kaynak

`selection.json` receipt indirilmeden yazıldı; dört piyasanın tüm görünen işlemleri alındı, başarılı receipt seçilmedi. 42 unique tx, önceden belirlenmiş 50 üst sınırın altında. S kapanış/sonuç bilgisi vaka seçmekte kullanıldığı için bu **keşif ve karşı örnek** örneklemidir.

| Başlangıç UTC / slug sonu | Gerekçe | API/parent | Maker / taker pay | Toplam PnL $ |
|---|---|---:|---:|---:|
| 14:45 / 1790001900 | Toplam ve geç katkı kayıp | 20 / 15 | 624,661573 / 600 | −221,927132 |
| 16:30 / 1790008200 | Pozitif geç katkı | 3 / 3 | 319,218388 / 0 | +74,924300 |
| 15:00 / 1790002800 | Önceden açık envanter, geç dolum yok | 7 / 3 | 131,39 / 0 | +40,751200 |
| 17:00 / 1790010000 | Pozitif toplam, iki taraf ve yön değişimi | 12 / 5 | 625,804369 / 253,54 | +16,081188 |

Kullanılan dönem V2 exchange ile uyumludur: receipt `to` ve olay adresi `0xe111180000d2663c0091e4f400237545b87b996b`; pUSD `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb`. Resmî [deployment listesi](https://github.com/Polymarket/ctf-exchange-v2/blob/main/README.md), [V2 ABI](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/interfaces/ITrading.sol), [emisyon kodu](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/mixins/Events.sol) ve [eşleştirme uygulaması](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/mixins/Trading.sol) ham dosya/alım zamanı/SHA ile `official_sources.json` içinde. Nisan 2026 geçişi [resmî duyuruda](https://help.polymarket.com/en/articles/14762452-polymarket-exchange-upgrade-april-28-2026) yer alıyor; bu dönem eski USDC.e/V1 ABI'siyle çözümlenmedi.

İki ücretsiz RPC (`polygon-bor-rpc.publicnode.com`, `polygon.drpc.org`) chainId137 döndürdü; ilk receipt'in transactionHash/blockHash/status/logs alanları birebir aynı. 42 TRADE ana receipt + 1 ikinci sağlayıcı receipt + 1 gerekçeli MERGE receipt; blok başlıkları da kaydedildi. Her ham JSON-RPC cevabı isteği, URL'yi, yerel request/receive zamanını ve ham response SHA'sını taşır (`raw/`). Hiçbir ücretli/kimlik doğrulamalı API yok.

## API satırı tek match veya tek karar değildir

**DOĞRULANDI:** `1790010000`, t604: bir API satırı ve bir Bosona taker `OrderFilled`, 205 Down içeriyor. Aynı `OrdersMatched` grubunda dört karşı emir var: 10+5+10 Down SELL ve 180 Up BUY. Böylece doğrudan token alışları ve karşı outcome mint eşleşmesi aynı aktör satırında toplanıyor. t741'deki tek 48,54 Down satırı üç karşı Up BUY emriyle eşleşiyor. `results.json/tx_details` tüm `OrderFilled` ve `OrdersMatched` sayılarını saklar; ham receipt'ler miktarları gösterir. Bu nedenle API satırı sayısına “tekil match” adı da verilmemeli.

**DOĞRULANDI:** `OrderFilled.maker` alanı emir sahibidir; piyasa maker rolünü tek başına göstermez. `OrdersMatched.takerOrderHash` ile işaretlenen aktör emri aktif/taker; aynı grubun diğer emirleri maker olarak atanır. Taker `OrderFilled`'ındaki karşı taraf exchange adresidir. Kod kanıtı: `src__exchange__interfaces__ITrading.sol:19`, `src__exchange__mixins__Events.sol:64`, `src__exchange__mixins__Trading.sol:131`, `decoder.py:85`. Böylece aynı boy, fiyat, en büyük miktar veya karşı-token görünümünden rol uydurulmaz.

**DOĞRULANDI:** Dört taker dolumun toplam ücreti **9,382210 dolar**, API `usdcSize` içinde zaten var. İki 300 pay zarar alımında ham 0,10/0,30 fiyat; gerçek nakit 31,89/94,41 dolardır. Aynı ücreti API maliyetine tekrar eklemek PnL'yi 9,382210 dolar fazla düşürür. Seçilmiş 38 maker dolumunda event fee sıfır. Hesap pUSD transferini uzlaştırır; API alan adının USDC olması güncel collateral'ı USDC.e yapmaz. Rebate/gas/sabit giderler ölçülmedi.

## Aynı parent ile farklı fazlar

`1790010000`, `0x9caa67c235f26fa5336052bac6d2c97fa44dd0c1637502a2faa9e82bb7469c9f`:

- t849–850 arasında **7 transaction / 7 dolum, tek maker parent**, 281,071430 Down, 241,721430 dolar.
- t816’daki 298,272939 çift MERGE sonrası parent başlamadan gerçek bakiye Up1,727061, Down0; net nakit maliyeti23,268812 dolar.
- Tek parent bu 1,727061 payı tamamlıyor; **279,344369 pay yeni Down riski** açıyor. Sonraki altı dolumun `add` etiketi altı ayrı yeni emir kararı değildir.
- Bu parent boyunca piyasanın en kötü sonucu −23,268812'den −263,263181 dolara düşüyor. Risk azaltımıyla başlayan parçayı bütün emrin amacı saymak da yanlış.

**DOĞRULANDI:** `1790002800` t210–211'de 5 transaction / 52,72 pay tek maker parent. Buna karşı `1790008200` t879–881'de üç dolum **üç farklı parent**; aynı 5/10sn paketine girmek aynı emir değildir. `1790001900` t802 ve t819'da eşit 300 paylık alımlar iki farklı taker parent. Eşit büyüklük de parent kimliği değildir.

26 geç-add dolumunun zincir sırasıyla ayrımı (`probe.py:133`, `probe.py:266`):

| Geç-add dolumu görünümü | Satır | Pay | Pay ağırlığı |
|---|---:|---:|---:|
| Parent'ın ilk gözlenen dolumu | 16 | 1.026,213545 | %69,4606 |
| Önceki saniyede zaten görülen parent'ın devamı | 6 | 231,071430 | %15,6404 |
| Aynı saniyede görülen parent'ın sonraki parçası | 4 | 220,118028 | %14,8990 |

Parent sayıları bu üç satır arasında toplanmaz; bir parent birden çok türde dolum üretir. “İlk gözlenen parent dolumu” **yeni gönderim anı** anlamına gelmez. Bu örneklemde aynı parent'ın en uzun gözlenen ilk–son dolum aralığı **3 saniye**, t600 sınırını geçen parent **0**. Dolayısıyla dakikalar önce verilmiş emrin geç faza sarktığı savı bu küçük örneklemde gösterilemedi. Yeniden dolmuş parent'ların kısa sürede parçalanması gösterildi.

## Kazanç, kayıp ve dolumsuz kontrol yolları

Her 42 olayın −5sn ask'ı, parent/rolü, önceki neti ve iki-sonuç en kötü ödemesi [PATHS.md](PATHS.md) içinde. Nakit ve paylar mikro birim tam sayılarla, resmî ödeme Decimal ile yeniden kuruldu. Zincir sırası `(blockNumber, transactionIndex, logIndex)`; bu borsa karar/gönderim sırası olarak sunulmaz. Aynı saniyede karşı yön bulunmadığı için bu dört vakada yön sırası belirsizliği yok.

- **Kayıp / KARŞI KANIT:** `1790001900` t399'da aynı parent ile 100+200 Down. t753–819'daki 18 geç dolum 14 başka parent; 600 pay taker risk büyümesi var. Up çözülünce toplam −221,927132 dolar. “Tek pasif emrin kalan kısmı” açıklaması tüm yolu kapsamıyor.
- **Kazanç / GÖZLEMSEL DESTEK:** `1790008200` t879, t881, t881'de 17,548388 / 1,67 / 300 Down, üç maker parent. Down çözülünce +74,924300 dolar. Üç imzalı payload'ın ayrı oluşu bilinir; üçünün ne zaman gönderildiği bilinmez.
- **İki yön / KARŞI KANIT:** `1790010000` ilk300 Up'a taker205 ve48,54 Down karşı alımları; ardından maker44,732939 Down tamamlama. Son maker281,071430 Down parent'ı kalan küçük açığı aşarak ters risk büyütüyor. Toplam +16,081188; tek bir faz etiketi bütün karar paketini temsil etmiyor.
- **Gözlenen geç ekleme yok / ÖLÇÜLEMİYOR:** `1790002800` son dolum t211; sonraki 600–899 aralığında dolum yok. Açık131,39 Up, maliyet90,6388, en kötü−90,6388; Up sonucu+40,7512. t600/t750'de zamanında gerçek Up ask0,99/0,998 ve Down ask0,02/0,01 var. t870'de Up ask yok, Down bid yok; eksik taraf uydurulmadı. Üç ham kontrol snapshot'ı `no_add_books.json`. Dolum yokluğu açık/iptal edilmiş emir yokluğu değildir.

## MERGE: gerçek bakiye ve nominal PnL

**DOĞRULANDI:** Son bakiye kontrolü `1790010000` t816’da bir MERGE gösterdi. İndirmeden önce `merge_selection.json` ekiyle1ilave transaction seçildi; 43unique tx/50sınırı korunuyor. İki tokenın298,272939’ar yakımı, condition kimliği ve298,272939USDC.e ödemesi [CTF merge olayları](https://github.com/gnosis/conditional-tokens-contracts/blob/master/contracts/ConditionalTokens.sol) ile uzlaştı. Aynı transaction başka condition için166USDC.e de ödüyor; toplam464,272939piyasaya yazılmadı. `probe.py:101` condition/token ayrımını ve bütün transaction transfer korunumunu kontrol eder.

MERGE eşit iki outcome’u ve eşit nominal maliyeti azaltır; net yön, iki-sonuç riski ve nihai PnL değişmez. MERGE’i görmezden gelen yalnız BUY toplamı bunları doğru verebilirken gerçek bakiye/bütçeyi yanlış verir. Replay artık gerçek miktarları azaltıyor (`results.json/merge_records`). TRADE nakdi pUSD, bu doğrudan MERGE nakdi USDC.e: PnL önceki raporlarla aynı nominal dolar hesabıdır; collateral dönüşüm ücreti/likiditesi varsayılarak yeni uygulanabilir bütçe sonucu çıkarılmadı.

## Kimliğin çözemediği şey

**KANIT YETERSİZ / NOT IDENTIFIABLE:** parent hash; ilk submit, her yeniden iletim, iptal, queue position veya kesintisiz resting zamanını vermez. [Hashing.sol](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/mixins/Hashing.sol) hash'i EIP712 emir alanlarından üretir; imza hash girdisi değildir (`src__exchange__mixins__Hashing.sol:22`). Aynı payload'ın yeniden iletilmesi hash'i değiştirmez. Bu mantıksal sınır, CLOB'un belirli iptal sonrası yeniden gönderimi kabul ettiğinin kanıtı değildir. Emir kabul/iptal geçmişi olmadan kesintisiz beklemeyi doğrulayamayız.

42/42 API timestamp blok saniyesiyle aynı. Bu yalnız **settlement zaman damgası** uzlaşmasıdır; karar, borsa match veya activity'nin ilk görünür olduğu zaman ölçülmüş olmaz. İnceleme alım saatleri ham cevaplarda; bunlar eski dolum anına taşınamaz. Kamu L2 bandı iptal/gizli emir veya bizim kuyruk payımızı çözmez. Maker oranından kopyalanabilir pasif getiri çıkarılamaz.

## Sonlu tekrar ve sonraki seçici

```bash
python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/onchain/probe.py
python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/onchain/check.py
```

İlk komuta `--fetch` verilirse seçilmiş42 TRADE ve gerekçeli1 MERGE için eksik cache indirilir; 50tx üst sınırı var. Mevcut cache ile ağ çağrısı yok. `decoder.py` önceki ortak saf V2 decoder'ın hashli kopyasıdır; BTC5dk veri/sonuçları analize katılmadı. Sekiz TRADE receipt/API, iki MERGE ve iki eksik-veri seçici negatif kontrolü, üç parent kimliği kontrolü, taker-owner karışıklığı ve aynı parent'ın faz aşması testi geçti. Hedefli Ruff/compile ve offline sonuç hash'i birebir tekrar geçti (`checks.json`).

`next_selection.py` 65 satırlık **yalnız manifest üreten** çevrimdışı seçicidir. Resmî BTC15 universe ve `complete:true` kamu activity dilimleri ister; her tam UTC günde96slot ve kesintisiz activity kapsamı zorunlu. Yokluğu işlem yok yapmaz. Her günden `sha256('btc15-parent-v1:'+slug)` sırasıyla4 işlemli piyasa; 96slotluk payda ve observed-no-trade piyasalar korunur. Sonuç/PnL/fiyat kullanmaz. Seçili piyasaların tüm işlemleri ayrıca uzlaştırılmadan parent sonucu üretilmez.

13–20 Eylül gerçek8tamgün demo: 768slot,32seçim, **UNDERPOWERED**. Aynı girdide tekrar SHA aynı; sonuç/PnL/önceki `traded` etiketi ve giriş sırası değişince örnek seçimi aynı. S14tam pencere/0tamUTC gün: UNDERPOWERED. 22Eylül00UTC–2Ekim00UTC ileri10gün girdisi bugün bulunmadığından `MISSING_DATA`, çıkış kodu2; başarısızlık dosyası `future_selection_blocked.json`. On tam gün kapısı düşürülmedi. Bu örnekleyici ekonomik kabulü veya veri toplama/deploy'u gerçekleştirmez; birleşik sonraki ölçüm protokolü ana rapordadır.

```bash
python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/onchain/next_selection.py --universe /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/results/universe.json --activity-dir /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/raw/activity --start 2026-09-13 --end 2026-09-21 --out /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/onchain/historical_selection_demo.json
```

Fikri değiştirecek gözlem: PnL'den bağımsız yeni10gün örneğinde geç risk artışının çoğu, önceden görülen aynı parent'tan gelir ve faz ayrımı parent düzeyinde kaybolursa “dolumları yeni karar sayıyoruz” açıklaması güçlenir. Ayrı parent/taker risk artışı sürerse tek pasif-devam açıklaması yetersiz kalır. İki durumda da masraf sonrası bağımsız politika avantajı ayrıca sınanmalıdır.

## Ek kontrol: kapanış sonrası API zamanı zincirde gerçek mi?

**DOĞRULANDI:** Muhasebe denetimindeki24 BTC15dk kapanış-sınırı/sonrası dolumdan, farklı iki piyasanın en büyük zaman sapmaları receipt indirilmeden `postclose_selection.json` içinde seçildi. İki ilave receipt ve iki blok başlığı ücretsiz alındı; tüm bu alt araştırma45unique transaction/50sınırında kaldı. `postclose_results.json`:

| Piyasa | API ve mined blok zamanı UTC | Resmî kapanıştan sonra | Rol / pay / nakit |
|---|---|---:|---|
| 1789845300 | 19Eylül20:01:17 | 1.877sn | taker /13,12 /1,117190$ |
| 1789846200 | 19Eylül20:01:26 | 986sn | maker /5 /2,75$ |

İkisinde API timestamp gerçek block timestamp ile birebir aynı; resmî endDate, condition/token, miktar ve transfer nakdi uzlaştı. Bu iki sapma yalnız API’ye geç eklenirken yanlış zaman yazılması değildir: zincir uzlaşması gerçekten kapanış sonrası gerçekleşmiş. **ÖLÇÜLEMİYOR:** Gönderim veya borsa eşleşmesi kapanıştan önce mi sonra mı; receipt bu zamanları içermiyor. Bu nedenle t>=900 dolumları kapanış sonrası yeni karar/avantaj diye modellemek geçerli değil; önceki24sayacın tamamının zincirde doğrulandığı da söylenmez.

Sonlu tekrar: `python /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z/onchain/postclose.py`; `--fetch` yalnız seçilmişiki receipt ve iki header için eksik cache indirir. Offline tekrar SHA'sı aynı, resmî kapanış/token/miktar/nakit assertleri geçti (`postclose_checks.json`).
