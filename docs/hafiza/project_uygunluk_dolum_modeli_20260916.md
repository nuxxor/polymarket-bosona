---
name: project-uygunluk-dolum-modeli-20260916
description: Canli emirler kayitli defterde yeniden oynatildi — dolum modeli iyimser DEGIL kotumser; %83,6 vs %53 farki motordan gelmiyor
metadata:
  type: project
---

2026-09-16 gecesi canli bot (S+1 politikasi) kesiciyle durdu (-$21,60).
Kardes oturumun teshisi: "dolum modeli iyimser, backtest %83,6 dedi canli %53 verdi".

**Bu teshis YANLIS.** Uygunluk testi yapildi: canli LOG.jsonl'deki 48 emrin her biri
`data/tape` tam merdiven defterinde yeniden oynatildi (25 pencere, 01:15-03:25 UTC).
Detay: `data/analysis/pm_uygunluk_20260916_v1/BULGU.md`

- Motor 33/48 tam dolum ongordu, GERCEK 38/48. Motor 165 pay, gercek 190 pay.
- "motor doldu dedi dolmadi": 1. "motor dolmaz dedi doldu": 6.
- Ayni 23 pencerede cift-tamamlanma: motor **%48**, gercek **%65**, backtest iddiasi %83,6.
- Yani motor o gece icin zaten KAYIP ongoruyordu (basabas %79,8).
  %83,6 rakami baska bir ornege ait; pencereden pencereye degisim cok buyuk.

**Mekanizma:** dolmayan bacakta sorun kuyruk degil, AKIS yoklugu — kaybeden tarafta
tuketim siklikla 0. Q~400 payken tuketim 0 ise dolum imkansiz.

**81 gunluk OOS testi icin:** motor bu politikada NEGATIF yanli (4 ayrismanin 4'u de
"motor tek dedi gercek cift"). FAIL cikarsa bir kismi motor kotumserligidir; PASS
cikarsa sonuc oldugundan guclu. Test SAAT KIRILIMI ile raporlanmali — canli ornegin
tamami gece (01-03 UTC) ve [[project-btc5m-independent-research-20260908]] zaten
"00-10Z saatleri zayif, gunduz +$17 gece -$63" diyor.

Ilgili: [[project-bosona-gec-favori-20260916]] (ayni durust motor, ayni tape)


---
**INDEX ÖZETİ (tam, 2026-09-16 kısaltma öncesi):**
- [🔬 UYGUNLUK TESTİ (09-16): canlı 48 emir kayıtlı defterde yeniden oynatıldı — dolum modeli İYİMSER DEĞİL KÖTÜMSER (motor 33/48, gerçek 38/48; "dolmaz dedi doldu" 6, tersi 1); %83,6 vs %53 farkı motordan DEĞİL örneklemden; aynı 23 pencerede motor %48 gerçek %65; mekanizma kuyruk değil AKIŞ yokluğu; 81 günlük OOS negatif yanlı + saat kırılımı şart](project_uygunluk_dolum_modeli_20260916.md)
