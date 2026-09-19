---
name: project-gec-pencere-twap-kilitlenme-20260917
description: Aktorlerin EN GUCLU hucresi — son 40 sn, fiyat>=0,65 alim: 19/19 gun arti, %97 isabet, +9,3 kr/pay; TAKER surumu de calisiyor (kuyruk YOK); mekanizma TWAP60'in kismen KILITLENMESI
metadata:
  type: project
---

Zincir-kesin defter (`FILL_PARTY_LEDGER`, 08-14..09-01, 4.425.807 etiketli pay,
iki cuzdan toplam +2,28 kr/pay) hucre taramasi. Butun hucreler +1..+3 civarinda,
AMA son 40 saniye firliyor:

## HUCRE: t >= 260 sn, odenen fiyat >= 0,65
| rol | pay | isabet | NET kr/pay | %95 GA | artida gun |
|---|---|---|---|---|---|
| maker (0,65-0,80) | 18.212 | %91,9 | **+18,85** | [+13,10,+23,48] | 15/18 |
| **taker (0,65-0,80)** | 9.096 | %94,6 | **+19,83** | [+9,42,+24,48] | 11/12 |
| maker (0,80-1,00) | 93.268 | %98,2 | +6,58 | [+4,80,+8,09] | 18/19 |
| **taker (0,80-1,00)** | 22.401 | %99,2 | +8,44 | [+6,74,+10,42] | 15/15 |
| 0,50-0,65 maker | 12.971 | %71,7 | +15,57 | [+2,51,+28,80] | 11/15 |

Hucre toplami (fiyat>=0,65, her iki rol/cuzdan): **19/19 GUN ARTIDA**,
143.000 pay, isabet %97, +9,3 kr/pay. Ic yarilar: +8,66 / +10,10 (sonme YOK).
Eylul 14-16 (API, yalniz 2 gun): +7,63 / -2,71, toplam +0,99 — ZAYIF ama n=2 gun.

## NEDEN ONEMLI
**TAKER surumu de calisiyor (+19,83 ve +8,44).** Taker'da KUYRUK YOK ->
bu projede her backtesti kiran tek belirsizlik (kuyruk modeli) ORTADAN KALKIYOR.
Yurutme birebir modellenebilir: ask'i al, 0,07*p*(1-p) ucreti ode, bitti.

## MEKANIZMA (hipotez, test edilecek)
Settlement = TWAP60(S+300) >= TWAP60(S). TWAP60(S+300) penceresi [S+240, S+300].
t=260'ta o 60 saniyenin 20'si ZATEN GOZLENMIS, t=280'de 40'i. Yani sonuc
son 40 saniyede giderek HESAPLANABILIR hale geliyor; kalan saniyelerde sonucu
cevirmek icin gereken fiyat hareketi ucuzlasarak imkansizlasiyor.
Isabetin %85,9'dan %97'ye cikmasi tam bunu gosteriyor.
Aktorler bu kismi-kilitlenmeyi piyasadan once/dogru fiyatliyor olabilir.

**ELIMIZDE KAYNAK VAR:** [[project-chainlink-streams-unlocked-20260913]] —
TWAP-60 feed `0x0002ee67...d95f` Polymarket settlement kaynagiyla 18 hane birebir,
29 gun gecmis. Yani kismi TWAP'i t=260..290'da HESAPLAYABILIRIZ ve piyasa
fiyatiyla kiyaslayabiliriz. Tamamen kamu verisi, kuyruk yok, taker yurutme.

## DIKKAT — CELISKI ACIK
Benim Eylul testim ayni bandi (t=270, favori bid 0,70-0,90, touch'a maker)
**-14,61 kr/pay** vermisti; dolum-kosullu isabet %68,3 iken aktorlerinki %97.
Donemler ortusmuyor (benim tape 09-13+, defter 09-01'de bitiyor) -> dogrudan
uzlastirilamiyor. Fark ya donem, ya da onlarin bandin ICINDE secim yapmasi.
Kismi-TWAP hipotezi ikinci secenegi aciklar.

## TEST YAPILDI — SINYAL DOGRULANDI (ayni gun)
`data/analysis/pm_twap_kilit_20260917_v1/BULGU.md`
- Settlement kurali 3.485/3.485 = %100 dogrulandi.
- Kismi TWAP marji: t=S+270'te |m|>=5bp olan pencerelerde isabet %99,7+;
  pencerelerin **%74'u 30 sn kala fiilen bitmis**. AGUSTOS (n=3.167) ve
  EYLUL (kendi tape, n=734) ayri ayri dogruladi — SONME YOK.
- Alinabilir hacim (Agustos, t>=268 & |m|>=5bp & fiyat<0,98, TAKER):
  **+6,40 kr/pay, GA[+4,38,+8,44], 12/12 gun, %0,00 yanlis taraf**,
  ~5.784 pay/gun. t>=262'de %1,36 hata girer -> t>=268 sifir-hata noktasi.
- ACIK: Eylul ALIM simulasyonu hatali kostu (gevsek ornekleme kapisi),
  yeniden kosulacak; rekabet payi modellenmedi.

## ESKI PLAN (tamamlandi)
t=260..290 arasi kismi TWAP60'i Chainlink'ten hesapla, gerekli-kalan-hareketi
cikar, piyasa fiyatiyla kiyasla. Esik asildiginda TAKER al. Kamu verisi,
kuyruk yok, 29 gun gecmis hazir.

Ilgili: [[project-zincir-kesin-19gun-rol-20260917]],
[[project-pm-late-window-liquidation-20260914]] (ayni hucre, +9,58 bagimsiz olcum)

## EYLUL ALIM KOSUSU: VERI KALITESI SORUNU (ayni gun, cozuldu)
Eylul simulasyonu -11,90 kr/pay / %77,9 yanlis taraf verdi. Kok neden:
**tape'in `cl` serisi 1/sn'ye dusurulmus ve bosluklu** — settlement kuralini
yalnizca %97,57 uretiyor (Agustos'un tam cozunurluklu HIST_spot/twap60'i %100).
Tanik: btc|1789482300, gercek TWAP farki +4,7 bp (kil payi), eksik saniyeler
246/280/297, benim seri isareti CEVIRIYOR ve 36.906 payla tek basina gunu batiriyor.

Karsilastirma:
| veri | settlement uretimi | alim penceresi | pencere isabeti | pay isabeti |
|---|---|---|---|---|
| Agustos (tam cozunurluk) | %100 | 51 | **%100** | **%100** |
| Eylul (tape cl, 1/sn) | %97,57 | 30 | %66,7 | %22,1 |

**DERS 1:** ham sinyal testi PENCERE sayar, alim simulasyonu HACIM agirliklandirir.
Kil payi tek pencere dev hacimle gelip sonucu cevirebiliyor. Ikisini birden raporla.
**DERS 2:** marj olcegi zamanla sisiyor (60/n2 carpani). t=268'de 5bp ile t=295'te
5bp ayni guven DEGIL. Esik `~k*60/n2` seklinde OLCEKLENMELI.
**DERS 3 (acik):** Eylul'de ucuz hacim tam modelin yanildigi pencerelerde cikti.
Agustos'ta 51/51 dogru oldugu icin artefakt gibi duruyor ama secilim etkisi
olabilir — temiz veriyle yeniden test sart.

SIRADAKI: Chainlink Streams'ten Eylul icin tam cozunurluklu seri cek, esigi
zamana gore olcekle, simulasyonu yeniden kos.

## COZULDU — UC FEED KARISIKLIGI (ayni gun)
Eylul cokusunun kok nedeni: tape'te ayni saniyede UC Chainlink feedi var
(`w=0` SPOT, `w=30` TWAP30, `w=60` TWAP60). Ilk cikarimim saniyede ILK geleni
aliyordu -> seri UC FEEDIN KARISIMIYDI. Ayirinca twap60 dogrudan **711/711 = %100**.
**DERS: cok-feed'li kayitlarda her zaman feed kimligine gore AYIR; 'saniyede bir
ornek' yeterli degil.**

Ayrica esik olceklendi: `mt = m*n2/60` (TWAP-esdeger bp), t'den bagimsiz.

### NIHAI DURUM — IKI DONEM, IKI BAGIMSIZ KAYNAK, IKISI DE TEMIZ
| donem | kaynak | pay | yanlis | kenar | %95 GA | gun | pencere |
|---|---|---|---|---|---|---|---|
| Agustos 08-16..09-01 | Streams HIST parquet | 69.413 | %0,00 | **+6,40** | [+4,38,+8,44] | 12/12 | 51/51 |
| Eylul 09-13..09-17 | canli tape (w ayrilmis) | 18.284 | %0,00 | **+8,83** | [+6,43,+10,03] | 4/4 | 30/30 |

Kural: t>=262, TWAP-esdeger marj |mt|>=2 bp, 2 sn gecikme payi, kesin kazanan
tarafta fiyat<0,98 baskilarini TAKER al. 1 bp'de hata giriyor (%8,6) -> 2 bp temiz.
Hacim ~4.500-5.800 pay/gun.

KALAN KAPILAR: (1) rekabet modellenmedi, (2) canli gecikme butcesi <2 sn,
(3) toplam 81 pencerelik ornek, (4) yalniz BTC 5m.

## GERCEK GECIKME + BUYUK ORNEKLEM (ayni gun) — IDDIA ZAYIFLADI
Uretim gecikmesi (kayitcinin kendi rcv-src'si, n=21.282): Chainlink besleme
**medyan 1.520 ms / p90 1.953 / p99 2.332**; PM POST->ACK medyan 562 / p90 857.
**TOPLAM medyan 2.102 ms** -> simulasyondaki 2 sn payi YETERSIZ.

Kural gercek gecikmeye dayaniyor ama zayifliyor. AGUSTOS BUYUK ORNEK
(t>=262, olcekli 2bp esik, **369 pencere** — onceki 51 degil):
| gecikme | pay | YANLIS% | kr/pay | %95 GA | gun |
|---|---|---|---|---|---|
| 2 sn | 755.633 | %2,91 | +6,38 | [+2,09,+9,13] | 15/17 |
| 4 sn | 833.819 | %6,24 | +5,55 | [+0,45,+9,19] | 14/17 |
| 6 sn | 888.232 | %7,42 | +5,98 | [+0,54,+9,63] | 15/17 |

**GERI CEKILEN IDDIA: "%0,00 hata".** 51 pencerelik ve 30 pencerelik kosularda
gorulen sifir hata KUCUK-ORNEKLEM ARTEFAKTIYDI (%3 hatada 30 pencerede sifir
gorme sansi ~%40). Gercek hata ~%3 (2 sn), gecikmeyle ~%7.

**DERS: ayni gun IKI KEZ kucuk ornekten fazla sey iddia ettim** (bosona taker
+11,06 -> 19 gunde +0,64; "%0,00 hata" -> %2,91). Bir hucre dar gorunuyorsa
ONCE esigi gevsetip ornegi buyut, sonra iddia et.

**KRITIK KALDIRAC: besleme gecikmesi 1.520 ms.** Dusurulurse hem hata hem kenar
duzelir. Kayitcinin Chainlink Streams tuketim yolu incelenmeli.

## BESLEME YOLU INCELENDI (ayni gun)
Kayitci Chainlink'i DOGRUDAN degil **Polymarket relay'inden** aliyor:
`wss://ws-live-data.polymarket.com`, topics `crypto_prices_chainlink` /
`_twap_thirty` / `_twap_sixty` (tape.py:116-117).
DOGRUDAN Streams WS kayitcisi ZATEN VAR ve calisiyor:
`pm_chainlink_history_20260913_v1/cl_direct_rec.py` ->
`wss://ws.dataengine.chain.link/api/v1/ws?feedIDs=...`, cikti `data/tape_cl_direct/`.

AYNI DONEM KIYASI (09-15 14:00-16:19, n~8.2k/feed):
| yol | medyan | p90 | p99 |
|---|---|---|---|
| DOGRUDAN Streams | **1.257 ms** | 1.717 | 2.135 |
| Polymarket relay | 1.512 ms | 1.981 | 2.444 |
| **kazanc** | **+255 ms** | +264 | +309 |

Yeni toplam butce: 1.257 + 20 (hesap) + 562 (POST) = **1.839 ms** medyan
(relay ile 2.102 idi). Kuralin EN IYI olculen satiri 2 sn rejimi
(+6,38 kr/pay, %2,91 hata, GA[+2,09,+9,13]) -> 1,84 sn ile o rejimdeyiz.

**TABAN:** 1.257 ms'nin buyuk kismi Chainlink'in KENDI rapor yayin gecikmesi.
Tesisatla daha asagi inilmez. ~1,26 sn fizik.

**STRATEJIK NOT:** PM relay'ini kullanan HERKES bizden 255 ms GERIDE.
Bayat ask'i almak icin gereken kenar tam olarak bu tur bir fark.

## DOGRUDAN KAYITCI CANLI (09-17 01:07 yerel / 22:07 UTC)
`cl_direct_rec.py` yeniden baslatildi (salt-kayit: emir/imza/para yolu YOK,
yalniz `data/tape_cl_direct/cld_*.jsonl.gz`'e yaziyor).
CANLI OLCUM (n=1.821): spot 1.197 / twap30 1.247 / twap60 1.239 ms,
**TUMU medyan 1.227 ms, p90 1.732**.
Relay 1.512 -> **KAZANC +285 ms**. Toplam butce **1.809 ms** = kuralin en iyi
olculen 2.000 ms rejiminin ICINDE.

TUZAK NOTU: dosya boyutu yaniltici — gzip tamponu + seyrek flush
(`rcv % 20000 < 60`) yuzunden diskte 7 dakika 1 satir gorunuyordu; kayitci
saglikliydi. Ham WS probe'u 25 sn'de 51 mesaj dogruladi. Kayitcinin canli olup
olmadigini DOSYA BOYUTUYLA degil, ham probe veya surec+zaman ile dogrula.


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🎯 GEÇ-PENCERE TWAP KİLİTLENMESİ (09-17, EN GÜÇLÜ ADAY): zincir defterde t≥260sn & fiyat≥0,65 alım **19/19 gün artıda**, 143k pay, isabet %97, +9,3 kr/pay; **TAKER sürümü de çalışıyor** (0,65-0,80 +19,83 GA[+9,42,+24,48]; 0,80-1,00 +8,44 GA[+6,74,+10,42]) → KUYRUK YOK, yürütme birebir modellenebilir. Mekanizma hipotezi: TWAP60 penceresi [S+240,S+300] olduğu için son 40 snde sonuç kısmen KİLİTLENİYOR; Chainlink feedi elimizde (29 gün). Eylül 2 günü zayıf (+0,99)](project_gec_pencere_twap_kilitlenme_20260917.md) — **09-17 SONUÇ: sinyal Ağustos VE Eylülde doğrulandı, %74 pencere 30 sn kala bitmiş, isabet %99,7; Ağustosta alım simülasyonu +6,40 kr/pay GA[+4,38,+8,44] 12/12 gün %0,00 hata** | EYLÜL KOŞUSU VERİ KALİTESİNDEN ÇÖKTÜ (tape cl 1/sn+boşluklu, settlementi %97,57 üretiyor; Ağustos tam çözünürlük %100 → 51/51 pencere). Ders: ham sinyal PENCERE sayar, alım sim HACİM ağırlıklandırır; marj eşiği 60/n2 ile ÖLÇEKLENMELİ | **ÇÖZÜLDÜ: tape 3 feed içeriyor (w=0/30/60), karıştırmışım; ayırınca twap60 711/711=%100. EYLÜL DE DOĞRULANDI: +8,83 kr/pay GA[+6,43,+10,03] 4/4 gün %0,00 hata 30/30 pencere. Eşik: TWAP-eşdeğer mt=m*n2/60 >= 2bp** | GERÇEK GECİKME medyan 2.102ms (besleme 1.520 baskın); büyük örneklemde (369 pencere) hata %0 DEĞİL **%2,91**, kenar **+6,38 GA[+2,09,+9,13] 15/17 gün**; "%0,00 hata" iddiam küçük-örneklem artefaktıydı, GERİ ÇEKİLDİ | BESLEME: kayıtçı PM relayinden alıyor (1.512ms); DOĞRUDAN Streams WS zaten kurulu (cl_direct_rec.py, 1.257ms) → **+255ms kazanç, toplam bütçe 2.102→1.839ms**; 1,26sn Chainlinkin kendi yayın gecikmesi = TABAN; relay kullanan herkes bizden 255ms geride | DOĞRUDAN KAYITÇI CANLI (09-16 22:07 UTC): medyan **1.227 ms**, relaye göre +285ms, toplam bütçe **1.809 ms** = en iyi rejimin içinde
