# BTC5m shadow kapanışı ve emir kimliği araştırması

21 Eylül 2026. Operatör mevcut shadow'ları durdurma/revize etme seçimini verdi.

## Uygulanan seçim

Mevcut yedi BTC5m politika shadow'u ve bağlı gecikme gözlemcisi, **18:19:02 UTC / 21:19:02 Türkiye** zamanında kendi `STOP_SHADOW` mekanizmalarıyla normal kapandı. Eski ve yeni sürümler birlikte kapatıldı. Sekizinin de son kaydı `stop / stop_file`; PID'leri artık yok. 18:26 UTC ikinci süreç kontrolünde de ilgili süreç bulunmadı. Kaynaklara yama yapılmadı; Jev süreçlerine ve ham veri kaydedicilerine durdurma komutu gönderilmedi.

Kapananlar: ilk üç-kurallı geç-giriş shadow'u; rebound ilk/v2/v3; inventory v1/v2; participation v1; rebound'a bağlı latency gözlemcisi. Buradaki dört inventory sanal kolu, tek süreç içindeki ayrı portföylerdir.

Günlükler, manifestler ve kapanış kanıtları Londra'da `/home/ubuntu/bosona-shadow-stop-20260921/` ve yerelde [kapanış arşivinde](../data/analysis/btc5m_retire_20260921/) korundu. Kapanış öncesi günlük byte önekleri ve son dosya hash'leri doğrulandı. Yazılmış kayıtlar veya geçmiş PnL silinmedi.

Bu, 72 saatlik kabul testlerinin başarıyla tamamlandığı anlamına gelmiyor: **operatör kararıyla erken sonlandırıldılar**. 18:15–18:20 penceresi kısmen çalıştı. Kapanış anında sonucu günlüğe henüz işlenmemiş sanal pozisyonlar ayrıca saklandı; sıfır PnL veya kapanmış pozisyon sayılmadı. Son tam takvim penceresi 18:10–18:15; günlüğün çözüm kaydı ayrıca gecikebilir. Yeni gerçek emir veya pozisyon tasfiyesi yapılmadı.

## Yeni çalışma: R1 — emir kimliği ve gerçekleşme rolü

Yeni bir alış/satış shadow'u açmadım. Ayrı, emir göndermeyen **sonlu bir araştırma kontrolü** hazırladım ve Londra'da gerçek kamu verisiyle çalıştırdım. Sürekli çalışan yeni servis yok; mevcut ham veri kaydı araştırmanın kaynağı olmaya devam ediyor.

İlk soru: Ultra'nın 14 Eylül 16:10 BTC5m piyasasında t=256'da gördüğü yedi dolum, aynı emrin parçaları mı?

**İlk cevap artık emir kimliğiyle doğrulandı:**

| Ölçü | Sonuç |
|---|---:|
| Activity kaydı | 7 |
| Ayrı transaction | 7 |
| Aktöre ait exchange dolum olayı | 7 |
| Ayrı actor orderHash | **1** |
| Toplam pay | **297** |
| Taker rolünde pay | **49,72** |
| Maker rolünde pay | **247,28** |

Ortak emir kimliği:

```text
0x957afc43514d18ee719c30c2264828029b5c1873580348d5517794abcd9fd661
```

Yedi receipt'in tamamında token miktarı ve ücret dahil nakit, hem activity hem gerçek transfer olaylarıyla uzlaştı. İlk receipt iki bağımsız kamu RPC sağlayıcısında aynı block hash ve loglarla doğrulandı; ikisi de Polygon chain ID 137 döndürdü. Receipt dosyaları hash'leriyle saklandı.

Rol, yalnız `OrderFilled` içindeki `maker` adresinin adına veya ücret sıfır olmasına bakılarak atanmadı. Her eşleşme grubunda `OrdersMatched` aktif emir kimliği ile `OrderFilled` eşleştirildi; diğer emirlerin karşı tarafı ve aktif emrin miktarları kontrol edildi. [Resmî V2 olay şeması](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/interfaces/ITrading.sol), [eşleştirme uygulaması](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/mixins/Trading.sol).

Bu örnekte “yedi dolum = yedi yeni ekleme kararı” açıklaması desteklenmiyor. Aynı imzalı emir kimliği birden çok transaction'da ve iki rolde gerçekleşmiş. **Emrin kaç kez gönderildiğini, ilk gönderim saatini, toplam ömrünü veya iptal geçmişini bu kayıtlar tek başına göstermiyor.** Tek örnekten bütün geç eklemelerin aynı yapıda olduğunu çıkarmıyoruz.

Saat ayrımı için somut karşı kontrol de var: aynı blokta 65,52 paylık maker parçası transaction index 72'de, taker parçası 75'te yerleşmiş. Buna karşılık arşivde transaction ile eşleşen exchange zamanı vekili taker için t=253,302, o maker parçası için t=253,629 gösteriyor. Yedi exchange zamanı vekilinin aralığı yaklaşık 417 ms, kamu zamanlarının hepsi t=256. Dolayısıyla blok/log sırasını doğrudan emir kararı veya exchange gerçekleşme sırası yerine koymuyoruz. [Ayrı saat/sıra tablosu](../data/analysis/btc5m_order_identity_20260921/settlement_order.json).

## Buradan sonraki sıra

1. **Emir kimliği kapsamını büyüt:** Önceden belirlenmiş kazanç/kayıp örneklerinde aynı decoder'ı çalıştır; gerçek kayıt çokluğunu koru. Geç eklemelerin ne kadarının aynı parent'ın devamı olduğunu kayıt, pay ve parent ağırlığıyla ayrı ölç. Çözülemeyen olayları eksik bırak; ücret vekiliyle kesin emir kimliği üretme.
2. **Risk azaltımını ayır:** Kendi önceki envanteri üzerinden ilk/ek/azaltıcı/tersine dönen parçaları sınıflandır. PRO'nun aynı başlangıçtan taşıma/tek karşı alım karşılaştırmasını uygula. Daha önce verilen emrin devamını yeni kapama kararı sanma.
3. **Sonra yeni işlem shadow'u:** Yeterli miktar/kimlik ve zaman kapsamı elde edilirse, küçük pasif teklifler ve ayrı risk azaltımı içeren tek aday dondur. Kuyrukta dolum belirsizliğini, gerçek tick'i, ücret ve iade koşullarını modelle. Yeni adayın girişi, miktarı ve karar zamanı Bosona'nın gelecekteki dolumundan bağımsız olsun.

Bu sıranın ilk kontrolü tamamlandı; bütün tarihsel evren çözülmüş değil. Yeni lane'in fiyatlama, boy ve iptal eşikleri henüz seçilmedi. Önceki RSI/t280/katılım kollarının sonuçları yeni modele eklenmeyecek.

## Kanıt ve tekrar

- [R1 hesap sonucu](../data/analysis/btc5m_order_identity_20260921/report.json)
- [RPC veri manifesti](../data/analysis/btc5m_order_identity_20260921/fetch_manifest.json)
- [Doğrulama](../data/analysis/btc5m_order_identity_20260921/verification.json)
- [Kapanış özeti ve sanal açık pozisyonlar](../data/analysis/btc5m_retire_20260921/closure.json)

```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_order_identity_20260921/check.py"
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_retire_20260921/check.py"
```

Londra'daki anahtarsız kamu verisi kontrolü:

```bash
python3 /home/ubuntu/bosona-order-research-20260921/check.py --fetch
```

Bu komut yalnız JSON-RPC okur ve yerel araştırma dosyaları yazar; işlem imzalama/gönderme içermez. Londra ve yerel kaynak/girdi dosyaları eşleşti; iki ortamın hesap sonucu aynı. Yinelenmiş log, eksik `OrdersMatched`, yanlış exchange adresi ve tek taban birimlik nakit farkı kontrollü testlerde reddedildi. İki kontrol dosyasında Ruff ve syntax doğrulaması geçti.

Not: İlk kapanış özetindeki `filled_unresolved` yardımcı alanı yanlış olay adından türetilmişti. Orijinal arşiv korunarak `after_corrected.json` üretildi; güncel kapanış kontrolü gerçek `execution.fills`/maliyet/seçim kayıtlarını kullanıyor. Ham shadow günlükleri değiştirilmedi.
