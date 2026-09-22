# Ultra — tarihsel bağlam yeniden kurulumu

**6/26 sınırı arşiv sınırı değilmiş: aynı 26 taker azaltımın 19'unda hem kamu saniyesi−5 hem −10 için taze defter, spot, TWAP ve o anda alınmış başlangıç referansı var.** Yeni 13 bağlamın 11'i mevcut eski gzip cache'inin erken saniyelerinden, ikisi 20 Eylül SQLite yeniden oynatımından geldi. Olayları sonuçlarına göre seçmedik; R1'in özgün hash-seçimli 64 piyasası ve mevcut 262 sınıflanmış parent aynen korundu.

`bosona_derin.extract_file` her piyasanın t10..299 saniyelerini ve +250ms kesitlerini saklamış. `load_snapshots` bunları t>=180 ile, `feature_rows` da dolumları t>200 ile kesiyor. Yeni kod geç-işlem filtresini kullanmıyor. `exchange_age` kamu WS `last_trade_price.timestamp` alanından geliyor; Bosona karar/emir gönderim saati değil.

## Kapsam

`events.json`: 262 özgün sınıflı parent + **bütün 64 piyasada** t120/t240'a bağlanan 128 sabit gözlem; toplam390. Sabit gözlemlerin46'sı, özgün R1'de azaltıcı dolum gözlenmeyen23 piyasada. Bu etiket gizli, dolmamış veya iptal edilmiş karşı teklifi dışlamaz. Kontrol zamanı kamu saniyesi benzetmesiyle tutulduğundan `lag5` gerçek girdileri t115/235, `lag10` t110/230'dur.

| Küme | Olay | −5 tam bağlam | −10 tam bağlam |
|---|---:|---:|---:|
| Taker azaltım |26|19|19|
| Maker azaltım |48|30|30|
| Maker aynı yöne ekleme |101|68|70|
| Maker ters yöne geçiş |14|8|9|
| Maker ilk açılış |67|44|43|
| Sabit gözlemler |128|83|85|

Taker erken (t<=200):13/19; geç:6/7. Gün bazında13–20Eylül sırasıyla4/5,2/2,7/7,1/1,3/3,0/1,0/3,2/4. Erken/geç ve gün kaybı rastgele eksiklik sayılmaz.

Kısmi girdiler silinmedi: örneğin −5 sabit gözlemlerde83 tam birleşime karşı86 defter,97 spot,96 başlangıç referansı var. Maker tersine dönüşlerde8 tam birleşim ama9 defter var. `summary.json` her bileşenin paydasını ayrı verir. Eski cache yalnız iki tarafı da geçerli defterleri saklıyor; SQLite replay tek tarafı da koruyor. Bütün ham arşivde tek taraflı ek bağlam kalmadığı iddia edilmiyor.

## Erişilebilir kaynak ve kalan7 taker olayı

- Harici ham arşiv gerçekten mevcut:124gzip,18.654.478.980bayt; dosya adları13Eylül13UTC–18Eylül22UTC.64piyasanın40ilgili saat cache'i66.878.108bayt olarak okundu. Manifestteki ham dosya boyları doğrulandı; bütün18,65GB'ın yeniden hash'i alınmadı.
- Tam defter SQLite dosyası da erişilebilir: `/home/taygun/Masaüstü/polymarket/data/db/polymarket_orderbook.db`. BTC5m abonelik aralığı19Eylül15:10'dan başlıyor; örneğin9/64piyasası burada. Sadece bu piyasalar, ilgili hedef zamanlar ve başlangıç snapshotları sorgulandı; tümDB taranmadı.
- Piyasa1789290300/t144:13Eylül09:05, erişilebilir ham defter kaydından önce.
-1789775400/t253,1789776900/t82,1789793400/t24,1789814100/t32: eski kasetin bitişiyle yeniDBbaşlangıcı arasındaki18Eylül23:50–19Eylül10:35 aralığı.
-1789909800/t63 ve t141:20Eylül13:10.13saatinin BTC ve Chainlink gzip dosyalarının ilk verisi13:13:47UTC; bu iki olayın karar öncesi girdileri kayıt kesintisinde. Aynı pencerenin sonrasındaki verinin bulunması erken anı kurtarmıyor.
- Sonradan alınanTWAP backfill parquetleri mevcut. Bunları olay öncesinde alınmış fiyat diye kullanmadık. Daha eski/uzak kayıt kesinlikle hiç yoktur demiyoruz; bu yerel kaynak haritasında yedi olayın gerekli yüksek frekanslı girdisi yok.

## Saat, envanter ve yürütme sınırı

Her fiyatın alınma ve kamu kaynak zamanı karar kesitinden önce olmalı ve en fazla3saniye eski olmalı. Eski cache için en fazla1,25saniyelik geriye-asof kesit kullanılıyor; gerçek `snapshot_ms` ayrıca saklı. Bu tarihler emir gönderim saati veya exchange aktivasyon saati değildir.19taker olayın kamuWS transaction eşleşmesi var; hiçbir−5/−10girdisi eşleşenWS kaynak zamanından sonraya düşmedi. Gerçek Bosona karar anı bundan yine çıkmaz.

Kritik ek kontrol: özgün `net_before_units`, kamu dolum saniyesinden hemen önceki envanterdir. Fiyatı−5saniyeden almak aynı envanteri garanti etmez.26taker azaltımın4'ünde−5,6'sında−10kesiti ile dolum arasında net miktar değişmiş. Yeni `net_at_cutoff_units` ve `inventory_changed_since_cut` bu farkı gösterir; held-side özellikleri **kesitte gerçekten görülen net yönle** hesaplanır. İlk/son gözlenen dolum yaşı da kesitten ölçülür. İlk dolum yaşı, sonraki sıfırlanma/yeniden açılma sonrası net pozisyon yaşıyla eşanlamlı değildir.

`opposite_buy_inventory` ve `held_sell_inventory` bütün net miktara ancak gösterilen derinlik yeterliyse fiyat verir. Eski cache tam seviyeleri saklamadığından, büyük miktarda yalnız en iyi seviyenin yeterli olduğu durumlar fiyatlanır; aksi null.5pay için cache'deki tam ask sweep maliyeti de kullanılabilir.−5taker örneklerinin yalnız9'unda bütün o-an envanteri için iki yürütme yolu fiyatlanabilir;19defter bulunması19tam-boy uygulanabilir kapatma demek değildir. Fiyatlanan maliyetler arşivdeki feeSchedule'a dayanır; gerçek emir, gerçek dolum veya kişisel rebate hakkı değildir.

128sabit gözlemin her iki gecikme duyarlılığında `execution250`, karar kesitinden250ms sonraki ayrı yürütme görüntüsüdür; **sinyal girdisi değildir**.128satır içinde−5kolunda69,−10kolunda71karşıalış5pay için bu alan fiyat verebilir; satış için68/70. Bu sayılara5paydan küçük/boş envanter filtresi henüz uygulanmamıştır. Ekonomik analiz kendi uygun-pozisyon filtresini uygulamalı.250ms gecikme burada araştırma varsayımıdır, gerçek emir-ACK gecikmesi ölçümü değildir.

## Mekanizma açısından somut sınama

Tam bağlam ve değişmemiş−5envantere sahip16taker azaltımda önceki10saniyelik held-bid değişimi10kez negatif,6kez pozitif. Tek başına “eldeki tarafın fiyatı düşünce taker stop” açıklaması tüm gözlemleri açıklamıyor. Örneğin1789449300/t165, parent`0x96b47e2088542...`, yaklaşık%99,993kapanma öncesinde held bid0,70ve10saniyelik değişim+0,08; spot eldeki tarafı15,33USD desteklerkenTWAP−13,66USD tersindedir. Buna karşı1789468500/t169, parent`0x50a1913623456...`, tamamını kapatmadan önce bid değişimi−0,17ama spot veTWAP hâlâ eldeki tarafı destekler. Ortak bir sonuç etiketi seçilmeden elde edilen bu karşıt girdiler, basit tek-fiyat/tek-referans tetikleyicisini zorlar. Kârlılık veya yeni doğru eşik iddiası yok.

Özgün43belirsiz parent bu işlemle sınıflanmış hale getirilmedi. Geçmiş dış transferler/sıfır başlangıç bakiyesi onchain kanıtı, gizli outstanding emirler, parent'ın tam gönderilmiş miktarı ve iptal saati bu dosyalardan çözülemez.

## Çalıştırılan kontroller

```bash
PYTHONDONTWRITEBYTECODE=1 python /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/context/reconstruct.py
PYTHONDONTWRITEBYTECODE=1 python /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/context/check.py
ruff check /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/context/reconstruct.py /home/taygun/Masaüstü/polymarket-bosona/data/analysis/g2_next_review_ultra_20260922/context/check.py
```

Gerçek yeniden kurulum,780kesit-envanter kontrolü,256yürütme etiketi kontrolü, sonuç etiketini ters çevirme, gelecekte alınmış fiyatı reddetme, yetersiz derinlik ve kaynak hash'leri geçti. İki ham saat dosyasının toplam694.873.844bayt açılmış prefixi yeniden okundu; erken1789449300/t165ve geç1789546200/t226olaylarının−5/−10için kullanılan dört defter görüntüsü cache ile birebir aynı. Ham dosyaların tamamı okunmuş sayılmadı. `verification.json` ayrıntıları ve nihai `events.json` hash'ini saklar. İlk ham kontrol denemesinde nominal zamanın cache asof zamanı ile aynı olması gerektiği yanlış test varsayımı yakalandı; test gerçek `snapshot_ms` üzerinden düzeltilip yeniden geçti. Araştırma verisi veya canlı kod bu nedenle değiştirilmedi.
