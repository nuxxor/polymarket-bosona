# BTC15dk: birleşik hesap ve düzeltilmiş simülasyon

21 Eylül 2026. **Pasif alım/birikim ve bazı aktif risk azaltan karşı alımlar,
eski sabit-zamanlı taker adayından daha iyi bir davranış açıklaması. Kopyalanabilir
kârlı politika henüz kanıtlanmadı.** Ultra'nın hesap düzeltmeleri ile Fable'nin
rol ölçümünü aynı kayıtlarda birleştirdim. Mevcut aday kontrol olarak korundu;
55¢ tavanı, olasılık eşiği ve diğer kuralları değiştirilmedi.

## Hesap artık aynı evrende

Ham activity dilimleri conditionId ve gerçek dolum çokluğuyla yeniden birleştirildi.
Resmî sözleşme/token/sonuç, ilk saniye paketi, MERGE sonrası gerçek envanter ve
rol etiketleri birlikte kontrol edildi. İlk saniye paketi gerçek emir kimliği değildir.
BTC5dk dışındaki 3.503 piyasa/14.014 dolumun toplamı **13.393,820008$** ile aynı.
BTC15dk: 598 piyasa/5.441 dolum, **4.428,55$**; maker 4.387, taker 1.054.

BTC15dk'da 164 dolumun faz etiketi değişti. Geç aynı-yön ekleme
(`600≤yaş<900`) sayısı 1.173'ten **1.150**'ye indi; 23 ilk-paket parçası artık
ayrı ekleme sayılmıyor. Düzeltilmiş geç eklemelerin %93,7'si maker.

| Geç ekleme | Dolum / piyasa | Gerçek nakit katkısı | En iyi 10 piyasa hariç | Her piyasayı 5$ nakde ölçekleme |
|---|---:|---:|---:|---:|
| Tümü | 1.150 / 274 | +3.364,65$ | +1,23$ | −69,92$ |
| Maker | 1.077 / 264 | +2.901,31$ | **−29,39$** | **−20,98$** |
| Taker | 73 / 57 | +463,34$ | −802,31$ | −21,67$ |

Satırlar kendi piyasa kümelerinde ölçeklenir; ölçekli sütunlar birbirine eklenmez.
5$ sütunu gerçekleşmiş aynı dolumların piyasa başına oransal muhasebesidir;
bu dolumları bizim elde edebileceğimizi göstermez. En iyi 10, her satırın kendi
katkısına göre çıkarılır. Fable'nin maker ex-top10 −4,89$ sonucu eski faz kümesiydi;
aynı rol sınıflandırıcısı düzeltilmiş kümede −29,39$ veriyor. Kazanç yoğunlaşması
ortadan kalkmadı. Tam rol×faz ve 29 grup tablosu: [reconciliation.json](results/reconciliation.json).

Karar öncesi tarihsel fiyatın erişim saati için Ultra'nın düzeltilmiş bağlam
arşivi kullanıldı; karar sonrasında alınan fiyat kabul edilmiyor. Gelecekteki
karma dolum nedeniyle önceki anı atan filtre kaldırıldı: 131 an geri geldi.
600–870 saniye ızgarasında 5.077 durum var; 294 ekleme, 397 karşı alım,
41 karma, 7 sıra belirsizliği, **4.338 gözlenen dolum yok**. 1.379 anın model
bağlamı eksik; sıfır sinyal yapılmadı. Dolum yok, emir yok veya satıcı yok demek değil.
Bu tur bu ızgarada yeni eşleştirme/olasılık modeli uydurulmadı.

## Zincir kontrolü neyi söylüyor?

Fable'nin önbellekteki 303 satırı, aktör filtreli receipt decoder ile yeniden
uzlaştırıldı. Gerçekte bu dosyada 20 piyasa var; resmî metadata sonrası
BTC15dk alt kümesi **19 piyasa, 283 dolum, 157 parent**. Kalan 20 dolum BTC saatlik.
283/283 BTC15dk kaydında miktar/nakit ve rol uzlaştı; 242 maker, 41 taker.
19 piyasanın her birinde tarihsel dolum kapsamı tam.

Bu seçilmiş bir denetim örneklemidir, yeni sonuçtan bağımsız örneklem değildir.
Fable'nin geniş 34-piyasa kapsam ifadesi bu 303 satırlık dosyanın fiilî kapsamı
yerine kullanılamaz. Emir hash'i parçalanmayı gösterir; ilk dolum zamanı
yerleştirme zamanı değildir. Eşleşme ve ilk gönderim saatleri bilinmeyen kaldı.
[Parent kapsamı ve kimlikler](results/parents.json).

## Simülasyonda düzeltilenler

- Bir paylık piyasa işlemi artık beş pay dolum yaratmıyor; kısmi dolum korunuyor.
- İki açık emir aynı 15$ bütçeden rezerv ayırıyor. İptal isteği rezervi hemen açmıyor.
- Aktif tamamlama da 5 pay klip, 10 net, 15$ nakit ve −5$ en kötü sonuç sınırına bağlı.
- Kabul/iptal için 250ms varsayımı açık. İlerideki gerçekleşme, önceden belirlenmiş
  limitten geçiyor; ilerideki fiyat karar girdisi değil. 250ms ölçülmüş gecikme değil.
- Veri boşluğu dolumdan önce kontrol ediliyor. Açık emir varken boşluk varsa sonuç
  bilinmeyen; bedelsiz iptal veya sıfır zarar yazılmıyor. Alt-sent bid yuvarlanmıyor.

Gerçek S arşivindeki 14 piyasa × 6 senaryoda nakit/risk sınırı ihlali **0**.
Eski kayıtlı Fable S sonucunda 12 piyasadaki 19 kol 15$ sınırını aşıyordu.
Bu bir uygulama düzeltmesi; aynı kârlılığı koruma amacıyla eşik aranmadı.

**Ekonomik sonuç bütün piyasalarda `null / MISSING_DATA`.** Eski 1sn REST
defteri ve blok saniyeli printler gerçek eşleşme/kuyruk testi için yeterli değil.
[Replay çıktısındaki](results/replay.json) `diagnostic_pnl` yalnız varsayımsal yol;
kol seçme veya getiri tahmini için kullanılmamalı. Kuyruk önü/arkası PnL alt–üst
sınırı değildir; geçersiz yol sayıları da farklıdır. Yeni motor henüz WS olaylarını,
iki-token/mint eşleşmesini ve portföy kesicisini doğrulayan ekonomik motor değildir.

## Eksik veri artık ayrı kaydediliyor

90 saniyelik gerçek kamu WebSocket denemesi: iki token için başlangıç defteri,
8.355 fiyat değişimi, 19 işlem mesajı ve 4 tick değişimi; hata yok. Yerel alım
eksi sunucu zamanı medyan 33ms. Bu fark eşleşme gecikmesi veya emir kabul süresi
diye yorumlanmaz. İşlem mesajlarının 19 farklı transaction hash'i var; henüz
receipt ile saat/çokluk bakımından uzlaştırılmadılar. [Veri kontrolü](results/ws_quality.json).

Ardından ayrı **iki saatlik kamu veri pilotu** başladı:
21 Eylül **20:35:57–22:35:57 UTC**; Türkiye saati 23:35:57–22 Eylül 01:35:57.
En çok 1 GiB sıkıştırılmamış olay veya en az 2 GiB boş alan sınırı daha erken
bitirebilir. Çıktı `raw/ws_pilot_v1/`; güncel sağlık `status.json`, kapanışta
`closed_hashes.json`. Mevcut ve sonraki BTC15dk sözleşmeleri resmî metadata ile
doğrulanır; tam defter, delta, tick, işlem ve yerel alım/monoton saat kaydedilir.
Kopma/reconnect açık kayıttır. Bu bir emir veya shadow süreci değildir.

Kaynak: [Polymarket kamu market stream şeması](https://docs.polymarket.com/market-data/realtime-data).
Fiyat seviyesi kaydı emir sahibi veya kesin kuyruk sırası vermez. Pilot veri
toplama/şema denemesidir; on günlük deneyin başladığı anlamına gelmez.

## Sonraki ekonomik adım ve durma şartı

En fazla iki mekanizma korunuyor: **M1 pasif kotasyonla birikim**, **M2 aynı
birikim yolunda aktif risk azaltımı**. Gelecek kurallar Bosona dolumunu tetikleyici
yapmayacak. Mevcut `candidate.py` / `protocol.json` P0 kontrolü olarak donuk.

Mevcut tanısal M1 kolları pencere yaşı 30–840sn arasında, taze iki taraflı
defter ve ≤3¢ spread ile bid'e veya bid−1¢'e 5 pay kotasyon koyar; hedef bid
değişince iptal/onaydan sonra yeniler. 1¢ bir fiyat mesafesi, dinamik bir tick
iddiası değildir. M2 bid kolunda net mutlak 10'a ulaştığında pasifleri iptal
edip aynı bütçeyle, en çok 5 pay adımlarla neti kapatmayı dener. Kalan pozisyon
resmî ödemeye taşınır. Bu kurallar kâr taramasıyla seçilmedi; Fable kollarının
limitleri uygulanmış tanısal sürümüdür. M2'nin daha iyi olması gösterilmedi.

Önce pilotun kapanmış tam pencerelerinde L2 akışı yeniden kurulacak; aynı hash'in
WS, piyasa-geneli işlem ve receipt miktarları uzlaştırılacak. Sayfa/print çokluğu,
iki-token eşleşmesi, saat, tick ve boşluk sorunu çözülmeden ekonomik kapı açılmaz.
Pilotun bütün tam pencereleri paydada kalır; kazanç veya Bosona varlığıyla seçilmez.
Bu tur yalnız mevcut seçilmiş parent kohortu uzlaştırıldı; Ultra'nın önceden
sabitlenmiş 22 Eylül–2 Ekim, hash ile günlük seçimli yeni kohortu henüz toplanmadı.

Ardından aynı giriş/risk altında M1–M2 ve korunmuş P0 karşılaştırılır. En az
10 tam UTC gün, 100 gerçekleşebilir giriş, 50 eklemeli piyasa, %95 veri kapsamı,
masraf sonrası mutlak ve kontrol farkında pozitiflik, piyasa/gün kümeli alt sınır
>0 ve en iyi 3 hariç pozitiflik korunur; en iyi 10/20 hariç de raporlanır.
Yetersiz veri `UNDERPOWERED`; kapı düşürülmez. Portföy rezervi/kesicisi tamamlanmadan
bu tek-piyasa motoru ileri işlem politikasına dönüştürülemez.

## Tekrar çalıştırma ve teslim kontrolü

```bash
/home/taygun/Masaüstü/KararAtlas/base1/bin/python3 -B /home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921/btc15_reconciled_v1_20260921/reproduce.py
```

Ağsız çalışır; canlı kaydı tekrar başlatmaz. Ham kaynak yolları/SHA değerleri
`results/input_manifest.json`, `parent_inputs.json`, `replay_inputs.json` içinde.
İki tam çalıştırmada **13 çıktı aynı SHA256**; **16 regresyon kontrolü**, syntax ve
Ruff geçti. [Doğrulama](results/reproduction.json). Beş donmuş çekirdek hash ve
eski REST recorder başlangıç kod hash'i aynı. MAIN, Ultra/Fable kaynakları ve
çalışan eski süreçlere müdahale edilmedi. Yalnız bu sürümün çıktıları ve kendi
araştırma planı yazıldı; yeni kamu pilotu ayrı, süreli süreçtir.
