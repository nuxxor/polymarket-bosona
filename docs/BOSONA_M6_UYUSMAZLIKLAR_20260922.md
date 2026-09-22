# M6 — Sabit kuyruk varsayimi neden yanlis sonuc veriyor?

22 Eylul 2026, 01:48 TR kesiti. M4v2'nin ayni 12 kabul edilen emri;
onceki M5, M1 ve M2 kaynak/sonuclari korunarak yeni tanisal hesap yapildi.
Gercek islem, yeni shadow, strateji veya butce degisikligi yok.

**Sonuc:** iki sahte dolum, eski baslangic derinligi varsayimina duyarlı.
Diger iki dolumda baslangictaki kuyrugun sabit kalmadigi goruluyor.
Bunlari tek sabit gecikme veya tek yeni kuyruk sayisiyla duzeltmek yeterli
degil. Dort hatanin veri yollarini ayirdik; tam kalibre simulator uretmedik.

## Ayni 12 emirde kontrol

ACK, SDK'nin kabul cevabini aldigi andir; kesin borsa aktivasyonu degildir.
Asagidaki derinlik, **o fiyattaki toplam gorunen paydir**, gercekten onumuzde
bulunan pay degil. Kendi emrimiz ve sonradan arkamiza gelenler de bulunabilir.

| Emir | Taraf / fiyat | Gercek dolum | Gonderimden 100 ms once derinlik | Gonderimde | ACK aninda | Eski model | ACK-derinlik duyarliligi |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 / c9d704cd | Down 0,71 | 0 | 0 | 5 | 321,99 | 5–5 | 0–0 |
| 3 / 3d24e091 | Down 0,74 | 0 | 0 | 28,53 | 341,52 | 5–5 | 0–0 |
| 6 / 3925b5c5 | Up 0,50 | 5 | 663 | 663 | 663 | 0–0 | 0–0 |
| 12 / f158b17e | Down 0,48 | 5 | 518,40 | 518,40 | 518,40 | 0–0 | 0–0 |

Duyarlilik hesabinda sadece baslangic sayisi `max(0, ACK_derinligi - 5)`
oldu. Bes payin cikarilmasi kendi emrimizi iki kez kuyruga yazmama
senaryosudur; gercek sira kaniti degildir. M5'in kaynak zaman araliklari,
100 ms payi, fiyat/yon filtresi ve islem miktarlari aynen korundu.

11 zaman-kullanilabilir emirde, iki senaryonun da disinda kalan emir sayisi
4'ten 2'ye indi. **Bu ileri dogrulama veya %82 dogruluk sonucu degildir.**
Ustelik 4 numarali sifir-dolum kontrolu once 0–0 iken 0–5 oldu: yeni
derinlik secimi onun sonucunu daha belirsiz yapiyor. Bir saat-null emir
hâlâ null. Butun 12 emrin sonucu `report.json` icinde, secilmis dortle sinirli degil.

## Iki gercek dolumu neden kaciriyor?

6 numarali Up emrinde ilk seviyedeki 663 pay, ilk uygun kamu islem
zamanindan once alinmis kayitta 15 paya kadar iniyor. Eski model 663'u
koruyor. Sonraki zincir kayitlarinda ayni seviyede diger iki emir toplam
10 pay, bizim emir 1,34 + 3,66 pay aliyor. Bu yol, sabit 663 payin neden
uygun bir varsayim olmadigini gosteriyor. 15 payin o anki kesin sirasi,
iptallerin kimligi ve daha once eslesip henuz bildirilmemis miktar gorulmuyor.

12 numarali Down emrinde ilk 518,40 pay, ilk uygun kamu islem zamanindan
once alinmis kayitta 49 paya kadar dusuyor; devaminda seviye yeniden
degisiyor. Kendi bes payimiz, ayni fiyatta toplam 20 paylik bir zincir
eslesmesinin parcasi. Yalniz ilk 518,40 payi tuketmeye calisan model bunu
kaciriyor. Daha gec defter degisimlerini emir kararinda biliniyormus gibi
geri tasimadik; kaynak saati ile bizim alinma saatimiz ayrica saklandi.

**Derinlik azalmasi otomatik olarak iptal veya bize dolum demek degil.**
Eslesme de ayni derinligi azaltabilir. Ardindan gelen kamu trade mesaji
tekrar kuyruktan dusulurse ayni olay iki kez sayilabilir. Yeni inceleme
bu azalmalardan otomatik sira kredisi/dolum uretmiyor.

## Saat problemi: tek 100 ms duzeltmesi yetmiyor

6 numarali emrin iki eslesmesi icin, ayni seviyedeki 4,34 ve 3,66 paylik
defter azalmalarinin kaynak saatleri kamu trade saatinden 40 ve 36 ms once.
Her biri 1 saniyelik inceleme alaninda tek miktar-eslesen aday; kesin
kimlikli baglanti sayilmadi.

8 numarali, M5'te null birakilan emirde daha belirgin bir ornek var:

| Olay | SDK gonderimine gore sure |
|---|---:|
| Defterde 66 -> 32,67 pay azalmasinin kaynak saati | +189,59 ms |
| Bu defter kaydinin yerel alinmasi | +226,59 ms |
| Botun 5 pay MATCHED cevabini almasi | +512,05 ms |
| Kendi emrimizi iceren 33,33 paylik islemin kamu kaynak saati | +653,59 ms |
| Kamu trade mesajinin yerel alinmasi | +690,59 ms |

Zincir eslesmesindeki 33,33 pay ile defter azalmasi ayni miktarda;
aralarindaki kaynak-saati farki **464 ms**. Bu, miktar ve fiyatla uyumlu
bir baglanti adayidir; L2 mesajinda orderHash olmadigi icin ispatlanmis
eslesme zamani degildir. Buna karsilik MATCHED cevabindan **141,54 ms
sonra gelen kamu kaynak zamani**, zaten daha once tamamlanmis kendi
dolumumuzun kesin eslesme saati olarak kullanilamaz.

En yakin esit-miktar azalmasini secmek de guvenilir cozum degil:
12 numarali emrin 20 paylik eslesmesine ayni saniyede **dort** miktar
uyumlu azalma adayi var. Diger bir bes-pay dolumunda iki aday var.
Uygun gorunen adayi secip tum islemleri geriye tarihlemek yapilmadi.
Sabit saat farki veya bilgisayarlar arasi UTC eszamanliligi bu dosyalardan
kanitlanmis degil. Ayni ms'deki L2 durumlari son gorunume birlesiyor;
bu da emir sirasini geri kurdugumuz anlamina gelmiyor.

## Yapilan degisiklik ve kalan is

`data/analysis/btc5m_m6_20260922/diagnose.py`, mevcut R1 decoder ve M1
defter okuyucusunu yeniden kullanir. Her emirde eski/gonderim/ACK
derinligi, tum seviye yolu, gercek maker emir kimlikleri, SDK durumlari,
kamu kaynak/alinma saatleri ve olasi azalmalari birlikte raporlar.
Kalibre dolum tahmini bilerek null; ACK tablosu yalniz karsilastirmadir.

Sonraki gereken olcum belli: ayni Londra surecinde, ayni UTC ve monotonic
saatle **kendi emir PLACEMENT/UPDATE/CANCELLATION ve trade olaylarini**
kamu book/trade akisi ve mevcut SDK kayitlariyla birlikte kaydetmek.
Resmi [hesap olay akisi](https://docs.polymarket.com/trading/realtime-order-updates)
emir kimligi, eslesen miktar ve trade icindeki maker emirlerini tasir;
[kamu L2 akisi](https://docs.polymarket.com/market-data/realtime-data)
seviye fiyat/miktarini tasir. Hesap akisinda `owner` alaninin API anahtari
olabilmesi nedeniyle ham mesaj kaydi uygun degil; yalniz izinli ekonomik
alanlar kaydedilmeli. Bu tur yeni dinleyici veya pilot baslatilmadi.

Bu olcum baskalarinin tum kuyruk/iptal kimligini acmaz; kendi emrimizin
yerlesme, parcali dolum ve kapanis olaylarini daraltir. Dinamik kuyruk
icin iptal/eslesme cift sayimini onleyen tek kural, bundan sonra ayri
veride sinanmali. Dort sonucu ezberleyen yeni model yazilmadi.

## Dogrulama

- 12 emir / 20 gercek pay / 5 zincir dolumu ve eski M5 degerleri korunuyor.
- Ham girdi/531 receipt/telemetri ve donmus kaynak-sonuc hashleri dogrulandi.
- Gercek 227.264 olayla hesap tekrarinda `report.json` byte-byte ayni.
- Tek runnable kontrol: gelecekte alinan kaydin gecmise sizmamasi,
  aynali miktar uyusmazliginin reddi, coklu azalma adaylarinin korunmasi,
  12 emrin kontrolu ve null'un sifira cevrilmemesi.
- M1 ve M5 regresyonlari, yeni iki Python dosyasinda Ruff ve syntax gecti.
- 01:48:38 TR Londra kontrolunde M4v2 PID yok; kaynak/state/butce hashleri
  donmus M4v2 ile ayni. Hesaba emir gonderilmedi; yeni muhasebe iddiasi yok.

```bash
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_m6_20260922/diagnose.py"
python3 "/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_m6_20260922/check.py"
```
