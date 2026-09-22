# BTC15dk kamu zincir alt denetimi

Yalnız bu dizine yazılır. S bilinen keşif dönemi; parent/rol tahmini receipt görülmeden selection.json içinde sabitlendi.

- [x] MAIN/R/F planları ve üç ana rapor okundu; ortak saf decoder incelendi.
- [x] Kazanç/kayıp/no-add dört piyasa, tüm görünen TRADE satırları (42) seçildi.
- [x] Resmi V2 exchange/ABI/rol kaynağı SHA ile sabitle.
- [x] En çok 50 tx, iki ücretsiz sağlayıcıda receipt ve chainId kontrolü; ham yanıt/zaman/hash.
- [x] API miktar/nakit ile gerçek token/cash transferlerini uzlaştır; parent/faz/rol ayrımı.
- [x] Negatif decoder regresyonları, lint/syntax ve offline aynı sonuç tekrarı.
- [x] Türkçe bulgu/sınır, tek sonlu deney.

Sonuç: 42/42 tx API/token/nakit uzlaştı; 26 parent,38 maker/4taker dolum. İkiRPC kontrolü geçti. Tekparent t849–850 yedi dolum/reopen+add içeriyor; zarar piyasası18geç dolum14parent. Bütün geç risk eski emrin devamı değil. Emir placement/cancel zamanı çözülmedi. Sonlu seçici8gerçek tam günde32piyasa seçti;10gün kapısı korunarak UNDERPOWERED.

Son bakiye kontrolü: aynı17:00piyasasının t816 MERGE’i önkayıt ekiyle1receipt olarak eklendi;43unique tx.298,272939 iki token yakımı/USDC.e nakit doğrulandı; başka condition166$ işlem aynı piyasaya yazılmadı. Gerçek bakiye replay’i ve iki negatif MERGE regresyonu geçti.

Ek istek: MERGE-aware kanonik alanlar ana inceleyiciye bildirildi; root dosyalarına yazılmadı.24postcloseBTC15dolum içinden iki farklı piyasa önkayıtla seçildi;2receipt/2block doğrulandı. API timestamp blok zamanıylaaynı;1.877/986sn postclose settlement gerçek, karar/match zamanı bilinmiyor. Toplam45unique tx, üst sınır50korundu.
