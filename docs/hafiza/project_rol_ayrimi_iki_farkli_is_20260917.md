---
name: project-rol-ayrimi-iki-farkli-is-20260917
description: bosona ve mo-money AYNI ISI YAPMIYOR — bosona karinin %90'i TAKER, mo-money %98'i MAKER; haftalardir ikisini tek olgu sandik
metadata:
  type: project
---

2026-09-17. "Ayni fiyat, 12,9 puan kazanma farki" cercevesini kovalarken PnL'i
role (maker/taker) gore ayirdim. Sonuc kulvari degistiriyor.

Yontem: data-api `/trades` takerOnly=true kumesinde OLMAYAN islem = maker.
Iki sorgu farkli derinlige sayfaliyor -> **ORTAK zaman araligina kisitla**
(yoksa maker/taker orani saclamalar verir). Taker ucreti 0,07*p*(1-p) dusuldu.

## IKI CUZDAN IKI FARKLI IS YAPIYOR
| | hacim | NET kr/pay | karin payi |
|---|---|---|---|
| **bosona** maker | %81 | +0,29 | **%10** |
| **bosona** TAKER | %19 | **+11,06** | **%90** |
| **mo-money** MAKER | %76 | **+2,50** | **%98** |
| **mo-money** taker | %24 | +0,14 | %2 |

(bosona 34 sa / 73.728 pay; mo-money 32 sa / 173.234 pay; ikisi de SATIS YAPMIYOR)

## MAKER ISI — DOGRU HEDEF mo-money, bosona DEGIL
| | pay | odedigi | pay-agirlikli kazanma | kenar |
|---|---|---|---|---|
| bosona | 59.529 | 43,00 kr | %43,3 | +0,29 |
| **mo-money** | 131.699 | **41,67 kr** | **%44,2** | **+2,50** |
| **bizim politika (sim)** | 9.003 | 43,41 kr | **%35,3** | **-8,07** |

mo-money DAHA UCUZA aliyor (41,67 vs bizim 43,41) VE daha cok kazaniyor
(%44,2 vs %35,3). Acik ~9 puan. Bu hala aciklanmadi.

## BUNUN ANLAMI
- Haftalardir maker kuralini **bosona'dan** ogrenmeye calistim; oysa bosona'nin
  maker isi sifira yakin (+0,29). Kismen YANLIS CUZDANI inceledim.
- **bosona'nin taker kulvari ayri ve cazip:** +11,06 kr/pay NET, 14.199 pay/34 saat.
  Taker'da KUYRUK YOK -> backtest'i kiran tek belirsizlik ortadan kalkiyor,
  yurutme birebir modellenebilir. Eksik olan tek sey SINYAL.
  Karakteri (n=158 islem, zayif ornek): 200-500 paylik buyuk islemler
  +25,48 kr/pay %84 isabet (hacmin %42'si); 0,20 altinda alimlar -9,99 %0 isabet;
  ilk 120 sn ve 260-285 sn guclu.
- AYNA TESTI (bosona'nin maker noktalarina motorumuzu koyduk, 639 nokta):
  bosona -1,28 / biz -0,99 -> o alt kumede ikisi de eksi, fark YOK.
  Motorun "dolmayiz" dedigi noktalarin kazanma orani %59,6, "doluruz"
  dediklerinin %42,1 -> dusuk kuyruklu SESSIZ noktalar iyi, bize gelmiyor.

## SIRADAKI IKI KULVAR
A) mo-money maker kurali: ayni fiyatta ~9 puan neden?  (kuyruk modeli riski VAR)
B) bosona taker sinyali: +11,06 kr/pay, KUYRUK YOK, yurutme kesin. (sinyal aranacak)

Ilgili: [[project-denetim-duzeltmesi-kazanma-orani-20260917]],
[[project-bosona-bakiye-ve-vol-kosullu-20260916]]


---
**INDEX ÖZETİ (tam, kısaltma öncesi):**
- [🧭 ROL AYRIMI — İKİ CÜZDAN İKİ FARKLI İŞ (09-17): **bosona kârının %90ı TAKER** (+11,06 kr/pay net, kuyruk YOK), **mo-money kârının %98i MAKER** (+2,50); haftalardır maker kuralını yanlış cüzdandan (bosona, maker +0,29) öğrenmeye çalışmışım. Maker hedefi artık mo-money: 41,67 kr ödeyip %44,2 kazanıyor, biz 43,41 ödeyip %35,3 → ~9 puan açık. maker/taker ölçerken ORTAK zaman aralığına kısıtla](project_rol_ayrimi_iki_farkli_is_20260917.md)


---
## ⚠️ DÜZELTME 09-19 — BU DOSYANIN ANA İDDİASI YANLIŞ
Yöntem olarak `takerOnly=true` kümesinde OLMAYAN işlemi maker saymak kullanılmış.
data-api varsayılanı zaten takerOnly=true; bu yol maker bacağının büyük kısmını
GÖRMÜYOR. Zincir-kesin defterle (FILL_PARTY_LEDGER, 19 gün, 19,2M kayıt):
    bosona MAKER +1,95 kr/pay GA[+1,04,+2,93]  (1.751.446 pay)
    bosona TAKER +3,63 kr/pay GA[+1,20,+7,14]  (366.408 pay)
    -> kârın **%72'si MAKER**, %28 taker
Yani "kârının %90'ı taker" iddiası ÇÜRÜDÜ. Bkz [[project-takeronly-hatasi-20260918]].
