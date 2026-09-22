#!/usr/bin/env python3
"""Generate the Turkish report and the frozen, undeployed experiment specification."""
import hashlib

import research as r


def num(x,d=2):
    return f'{x:,.{d}f}'.replace(',','_').replace('.',',').replace('_','.')


def name(g):
    sym,unit = g.split('_')
    return sym.upper()+' '+dict(m5m='5dk',m15m='15dk',m1h='saatlik',m4h='4saat',m1d='günlük')['m'+unit]


def build():
    summary = r.read(r.OUT/'summary.json')
    groups = summary['groups']
    behavior = r.read(r.OUT/'behavior.json')
    selection = r.read(r.OUT/'selection.json')['models']
    style = r.read(r.OUT/'style_models.json')
    choice = r.read(r.OUT/'next_side_models.json')
    conditional = r.read(r.OUT/'conditional_completion.json')['groups']['btc_15m']
    windows = r.read(r.OUT/'windows.json')
    fills = r.read(r.OUT/'fills.json')
    table = ['| Piyasa | İşlemli / doğrulanmış evren | Dolum | İşlem PnL $ | İlk saniye / fiyat ¢ / pay (medyan) | İki yön % |',
             '|---|---:|---:|---:|---:|---:|']
    risk = ['| Piyasa | Ekleme / tamamlama, payların %’si | FIFO çift / kalan yön PnL $ | Tepe zarar riski, medyan / en yüksek $ | Sonda eşleşmeyen pay, medyan | En iyi 3 hariç PnL $ |',
            '|---|---:|---:|---:|---:|---:|']
    for g in r.PRIMARY:
        v = groups[g]
        table.append(f'| {name(g)} | {v["markets"]} / {v["universe"]} | {v["fills"]} | {num(v["pnl"])} | '
          f'{num(v["first_age_median"],1)} / {num(v["first_price_median"]*100,1)} / {num(v["first_share_median"],1)} | {num(100*v["both_sides"]/v["markets"],1)} |')
        risk.append(f'| {name(g)} | {num(100*v["add_share"],1)} / {num(100*v["completion_share"],1)} | '
          f'{num(v["pair_cash_pnl"])} / {num(v["residual_cash_pnl"])} | {num(v["median_peak_risk"])} / {num(v["maximum_peak_risk"])} | '
          f'{num(v["median_residual_qty"],1)} | {num(v["ex_top3"])} |')
    extra = ['| Diğer grup | İşlemli piyasa | PnL $ | İki yön % | En iyi 3 hariç $ |',
             '|---|---:|---:|---:|---:|']
    for g,v in sorted(groups.items()):
        if g not in r.PRIMARY and v['markets']>=50:
            extra.append(f'| {name(g)} | {v["markets"]} | {num(v["pnl"])} | {num(100*v["both_sides"]/v["markets"],1)} | {num(v["ex_top3"])} |')
    late = behavior['btc_15m']['late_third_add']
    cases = []
    for g in ('btc_15m','btc_1h','sol_5m'):
        ww = [w for w in windows if w['group']==g]
        for label,w in [('kazanç',max(ww,key=lambda w:w['cash_cost_pnl'])),('kayıp',min(ww,key=lambda w:w['cash_cost_pnl']))]:
            ff = [f for f in fills if f['slug']==w['slug']]
            cases.append(dict(label=label,window=w,fills=ff))
    r.save(r.OUT/'cases.json',cases)
    ctable = ['| Örnek (resmî sözleşme) | İlk fiyat / saniye | Toplam PnL $ | Son üçte bir ekleme $ |',
              '|---|---:|---:|---:|']
    for c in cases:
        w = c['window']
        latep = sum(f['marginal_cash_pnl'] for f in c['fills'] if f['opening_kind']=='add' and 2/3<=f['age']/f['duration']<1)
        ctable.append(f'| [{name(w["group"])} {c["label"]}](https://polymarket.com/event/{w["slug"]}) | '
                      f'{num(w["first_price"]*100,1)}¢ / {w["first_age"]}sn | {num(w["cash_cost_pnl"])} | {num(latep)} |')
    protocol = dict(status='RESEARCH_CANDIDATE_NOT_ECONOMICALLY_VALIDATED_NOT_DEPLOYED',
        market='btc_15m',name='btc15_inventory_discount_v0',
        selection_reason='Strongest observed late-addition contribution; independent rule remains weak and unstable.',
        source_sha256=hashlib.sha256((r.HERE/'candidate.py').read_bytes()).hexdigest(),
        source_context_sha256=hashlib.sha256((r.HERE/'btc15_context.py').read_bytes()).hexdigest(),
        entry=dict(age_seconds=180,qty=5,max_ask_vwap=.55,min_probability_minus_fee_inclusive_ask=.05,
          probability='Uncalibrated zero-drift normal final60s-TWAP model, sigma from preceding60s observed spots sampled5s.',
          reference='Exact Chainlink TWAP60 observed at official start, received before decision; no retrospective-only reference.'),
        addition=dict(age_seconds=600,max_times=1,qty=5,side='own unmatched side',same_value_filter_as_entry=True),
        completion=dict(ages=list(range(240,841,60)),priority='before addition',
                        qty='min(5,abs(own Up-Down))',max_fifo_pair_fee_inclusive_cost=.98,no_overcompletion=True),
        exit='Hold remaining exposure to verified official settlement. No simulated stop-loss without an executable bid.',
        limits=dict(max_unmatched_shares=10,max_purchase_cash_per_market=15,max_worst_outcome_loss_per_market=5,
                    max_portfolio_open_worst_loss=5,max_overlapping_new_risk_markets=1,
                    soft_loss_cutoff=10,soft_cutoff_action='Stop new risk; continue pre-budgeted risk-reducing completion; no guaranteed -10 stop.'),
        arms=dict(primary='managed',control='completion_only',diagnostic='entry_only',
                  secondary='unfiltered_add; exploratory only; same entry and same hard limits'),
        data=dict(decision_max_age_ms=3000,max_spread=.03,execution_request_delay_ms=250,
                  execution_max_delay_ms=3000,full_depth_required=True,market_token_and_fee_validation=True,
                  future_price_never_decision_input=True,missing_never_zero_signal=True),
        timing='Starts only after a separate operator deployment instruction; no historical or prospective start date claimed.',
        success=dict(min_complete_utc_days=10,min_executed_markets=100,min_addition_markets=50,
                     min_data_coverage=.95,require_absolute_fee_net_pnl=True,
                     require_primary_minus_control_cluster_ci_lower_above_zero=['market','UTC day'],
                     require_ex_top3_positive=True,all_arms_reported=True,
                     inadequate_data='UNDERPOWERED; no threshold adjustment after results',
                     similarity='Same-market first-side/time/price and action-role proportions on public fills, with +/-5/10s uncertainty; report separately from PnL.'),
        practical_limit='Only one addition occurred in 21 historical proxy entries. This design does NOT qualify as a strong profitable model; do not deploy merely because this file exists.')
    r.save(r.HERE/'protocol.json',protocol)
    text = f'''# Bosona’nın BTC5dk dışındaki işlemleri — 21 Eylül 2026

**Birden fazla davranış ailesi görünüyor; Bosona’ya benzeyen ve ekonomik avantajı doğrulanmış bir karar kuralı henüz bulunmadı.**
En güçlü kazanç ipucu BTC15dk’deki geç eklemeler. Fakat ilk girişi, miktarı ve alınabilir fiyatı açıklamadan bu katkıyı kopyalayamıyoruz.
Aynı yazılımın farklı piyasa koşullarına uyarlanması hâlâ mümkün. Ayrı bot/kod veya tek ortak gizli amaç fonksiyonu bu veriden belirlenemez.

**Kapsam ve güvenilirlik.** 13 Eylül 00:00–21 Eylül 12:00 UTC (Türkiye: 13 Eylül 03:00–21 Eylül 15:00), 8,5 gün.
BTC5dk hariç **{num(summary['total_markets'],0)} işlemli piyasa, {num(summary['total_fills'],0)} BUY dolumu, 29 varlık×süre grubu**.
Önceki alımlar için aktivite 10 Eylül’e uzanıyor. PnL, resmî sonuç ödemesi eksi API `usdcSize` maliyeti; iade ve sabit giderler hariç.
MERGE/REDEEM ikinci kez gelir yazılmadı. Bu rakamlar bütün cüzdanın dönemsel servet değişimi değildir.
13–17 Eylül keşif, 18–20 Eylül kronolojik kontrol, 21 Eylül ayrı yarım gün; önceki günler önceden incelendiği için kör test değiller.

**Muhasebede düzeltilen eksik:** aynı işlem kimliği/fiyat/miktar her zaman tek dolum demek değil.
Kapsam içindeki üç piyasada aynı görünen ikinci dolum, güncel `/trades` ve `/activity` çokluklarıyla doğrulandı.
BTC15dk toplamı önceki aynı 598 piyasada 4.563,55 $ yerine **4.428,55 $**; iki eksik kaydın etkisi −135 $.
Eski BTC saatlik örneğe bir dolumun etkisi +84 $. Örtüşen indirmeler birleştirildi, gerçek çokluk korundu.
Ayrıca eski kaynakta tekrarlanmış 136 REDEEM ve 20 MERGE kaydı 158 taze piyasa sorgusuyla düzeltildi; kalan ödeme sınırı ihlali yok.
Ana repo veya eski raporlar değiştirilmedi. [Farklar](results/refresh_changes.json), [çokluklar](raw/multiplicity.json).

**Ana tablo.** Evren, Bosona işlem yapmasa da resmî bilgisi alınmış bütün planlı sözleşmeleri içerir.
İlk giriş, ilk kamu saniyesindeki dolumların toplamıdır; ilk emir veya bütün emir miktarı değildir.

{chr(10).join(table)}

**Pozisyon yönetimi ve açık risk.** Ekleme yalnız mevcut açık yönün büyütülen kısmı; tamamlama yalnız karşı pozisyonla eşleşen kısım.
Tamamlamayı aşan miktar ayrıca “yeniden risk” sayılır; bütün parça toplamları PnL ile uzlaşır.
Tepe risk = pencere boyunca `alış maliyeti − min(Up, Down)`, sıfırın altına düşmez.
Sondaki açık miktar çözümleme öncesindeki yön riskidir; bugün hâlâ açık cüzdan pozisyonu değildir.
FIFO çift/kalan ayrımı muhasebedir, nedensel kâr atfı değildir.

{chr(10).join(risk)}

BTC15dk’nin ilk saniye miktar medyanı 49,8 pay; ilk 5 saniye 70,5, ilk 10 saniye 80,9 pay.
Bu fark, ilk dolumu emir boyu saymanın neden yanlış olacağını gösteriyor.
BTC15dk tamamlamalarının 237’si karşı açığı aşarak yeni yön riski açıyor; SOL15dk’de bu sayı sıfır.
BTC15dk son yön miktarı medyanda 148 payken ETH saatlikte yalnız 3,3 pay: aynı risk hedefi görünmüyor.
ETH saatlikte iki yön oranının yüksek olması kâr kilitlendiği anlamına gelmiyor; çift katkısı −448,66 $.
Örneğin 0,80 $’lık Up’a sonradan 0,40 $’lık Down eklemek 0,20 $ zararı sabitler;
önceki 0,80 $ azami kaybı azaltır, fakat kârlı arbitraj değildir.

**Yeterli gözlemi olan diğer gruplar.** Bu gruplarda yalnız işlemli piyasa kapsamı tamamlandı;
işlem yapılmayan bütün sözleşmeler indirilmediği için seçim oranı veya üstünlük sonucu çıkarılmadı.

{chr(10).join(extra)}

4 saatlik ve günlükler de [29 grubun sayısal raporunda](results/summary.json).
Günlüklerde grup başına 5–7 gözlem var; model seçimi için yetersiz.

**Hangi piyasayı ne zaman seçiyor?**

Sabit gece saati açıklaması desteklenmiyor. Önceki BTC5dk referansında Türkiye 00–06 dilimindeki pay 19 Eylül’de %65,7, 20 Eylül’de %7,1 idi;
diğer tam geceler farklıydı. Yeni veride 21 Eylül 00–12 UTC’de BTC15dk dolumu **yok**; 1.195 son dönem işlem kaydı taze API ile birebir eşleşti.
Bir geceden tekrarlanan saat stratejisi çıkarılamaz.

Bosona’nın henüz girmediği sözleşmelerde, pencerenin başlangıcı/üçte biri/üçte ikisindeki girdilerle sonraki aralıkta ilk dolum oluşmasını tahmin ettim.
18–20 Eylül’de tahmin hatası (küçük daha iyi): varlık/süre/zaman tabanı **{selection['baseline']['chronological']['logloss']:.4f}**;
saat eklenince **{selection['clock']['chronological']['logloss']:.4f}**; fiyat hareketi/oynaklık/hacim eklenince **{selection['market']['chronological']['logloss']:.4f}**.
Piyasa bağlamı küçük bir iyileşme sağlıyor; saat tek başına sağlam açıklama değil. Bu bir nedensellik testi değil.
Gözlenen diğer açık envanteri eklemek kontrol döneminde iyileştirmedi.
Gizli emirler, BTC5dk ve kapsam öncesinden taşınan sermaye bu envanter ölçüsünde yok; tam cüzdan bütçesi test edilmiş sayılmaz.

**İlk yön, fiyat ve büyüklük.** SOL15dk’nin ilk alımlarında 5 saniye önceki Binance yönüyle uyum 131/144 kayıt;
BTC15dk’de 235/489. BTC15dk’yi yalnız “mevcut yönü al” diye açıklayamıyoruz.
SOL5dk ilk fiyatı yüksek olsa da en iyi pencere 31¢’ten Down alımı; en kötü örnek 80¢’ten Down alıp −80 $.
Yüksek fiyat tek başına avantaj veya karar anındaki favori demek değil.
Dakikalık kamu fiyat serisi ilk girişlerde medyanda 35–45 saniye geride; anlık defterin favorisi olarak kullanılamaz.
ETH/SOL kısa sözleşmelerindeki Binance başlangıcı yalnız vekil; resmî Chainlink referansı yerine geçirilmedi.

**Ortak mekanizma mı, ayrı aileler mi?** İlk fiyat, göreli zaman, ilk miktar, oynaklık, hareket ve hacim kontrol edildiğinde bile piyasa kimliği bilgi taşıyor.
İki yönlü pozisyon tahmininde sonraki günlerin hata ölçüsü ortak modelde **{style['shared']['chronological']['logloss']:.4f}**, piyasa kimliği eklenince **{style['by_market']['chronological']['logloss']:.4f}**.
21 Eylül kesitinde de fark sürüyor. Betimleyici aileler: BTC15dk’de sık iki taraf + büyük kalan yön;
BTC saatlikte daha belirgin eşleştirme katkısı; ETH/SOL kısa sürelerde daha seyrek karşı taraf;
ETH saatlikte dengeleme sık, sonuç zayıf. Eksik spread/likidite ve özel hedefler yüzünden ayrı algoritma sonucuna gidilmez.

**Hipotezler ve karşı kanıtlar.**

| Hipotez | Destek | Karşı örnek / sınır | Yanlışlama koşulu |
|---|---|---|---|
| BTC15dk geç eklemelerinde tekrar eden avantaj var | Son üçte bir: {late['actual']['n']} dolum / {late['actual']['markets']} piyasa, {num(late['actual']['pnl'])} $; en iyi üç hariç {num(late['actual']['ex_top3'])} $ | Eşit beş pay/pencere {num(late['equal5']['pnl'])} $; piyasa bazlı %95 aralık {num(late['equal5']['market_ci95'][0])}…{num(late['equal5']['market_ci95'][1])} $, sıfırı kapsıyor. 14 ve 16 Eylül negatif | Bosona dolumuna ihtiyaç duymayan, alınabilir fiyatlı ileri kural masraf sonrası avantaj üretmezse ekonomik kopyalama hipotezi reddedilir |
| Tamamlama yalnız ucuz çift kurmak için | BTC saatlikte çift katkısı +{num(groups['btc_1h']['pair_cash_pnl'])} $ | BTC15dk 902 tamamlama kaydında çift maliyeti 1 $ üstünde; −12.052,19 $ çift katkısı. Bunların 794’ünde toplam en kötü sonuç yine iyileşiyor | Bütün tamamlamayı ≤0,98 çifte bağlayan kural mevcut kayıtlarla zaten çürük; ortak açıklama risk azaltmayı da içermeli |
| Önceki açık miktar sonraki yönü belirliyor | Tamamlama miktarı açığa göre anlamlı; bazı alımlar tam kapatıyor veya aşıyor | Sonraki yön tahmininde piyasa modeli {choice['market']['chronological']['logloss']:.4f}, envanter eklenince {choice['market_inventory']['chronological']['logloss']:.4f}; iyileşme yok | Yeni günlerde envanter modeli aynı dış girdilerden daha iyi tahmin üretmezse bu basit karar modeli reddedilir |
| Kazanmak için ucuzlayana ekliyor | BTC15dk ucuzlayan tarafta eklemeler +2.165,67 $ | Pahalılaşan tarafta +3.586,45 $; iki türde de kayıplar var. SOL5dk geç eklemeleri sonraki dönemde eşit payla −1,05 $ | Fiyat düşüşü tek başına sabit ve bağımsız kuralda pozitif fark vermezse reddedilir |
| Basit kapanış olasılığı ucuz eklemeleri ayırıyor | BTC15dk gerçek Chainlink bağlamında 5sn önceki ≥5¢ fark grubunun eşit-pay katkısı +19,50 $ | 10sn öncesine geçince +2,78 $; gerçek miktarda en iyi üç hariç +169,76→−269,64 $. Momentumun karşı yönünde de kazanç var | Gecikme/örnek dışı kalibrasyon ve gerçek ask testinde kaybolursa reddedilir; şu an güvenilir yön modeli değil |

Bosona’nın ilk girişine koşullu, beş pay alıp yalnız gözlenen uygun karşı dolumda ≤0,98 çift tamamlamak:
belirsiz sıralı pencereler dışarıda **{conditional['delta']['n']} piyasa**, ilk alımı tutma {num(conditional['hold'])} $, tamamlama {num(conditional['complete'])} $.
Fark keşifte +46,09 $, **18–20 Eylül’de −0,34 $**. İki güven aralığı da sıfırı kapsıyor.
Bu karşılaştırma bizim o fiyattan dolacağımızı veya bağımsız giriş kuralını bulduğumuzu kanıtlamıyor.

**Somut kazanç ve kayıplar:**

{chr(10).join(ctable)}

BTC15dk kazanan örnekte tepe olası zarar 586,79 $, kaybedende 461,20 $.
“Büyük ekleme iyi çalışır” çıkarımı kaybeden örneği de açıklamak zorunda.
Tam dolum yolları ve önceki/sonraki iki sonuç ödemesi [cases.json](results/cases.json) içinde.

**Bağımsız yerel model deneyi.**

BTC15dk’nin bütün uygun sözleşmelerinde t=180’de üç giriş denendi: ucuz taraf; referans yönündeki uygun fiyat;
son 60sn ortalama kapanışının basit, kalibre edilmemiş olasılığına göre en az 5¢ fark.
Aynı girişler dört yönetim koluna verildi: tut; yalnız tamamlama; tamamlama + filtreli t600 ekleme; filtresiz t600 ekleme.
0/2/5¢ fiyat stresiyle **36 keşif karşılaştırmasının tamamı** saklandı; başarısızlar elenmedi.

591/816 pencerede karar bağlamı var. Bunlar gerçek defter değil, geçmiş dakikalık kamu fiyatlarıyla **senaryo hesapları**.
Uygulamada karar sonrasındaki ilk örnek (en çok 90sn sonra) + ücret kullanıldı; maker dolumu veya derinlik uydurulmadı.
Fiyat zamanlarının gerçek bağlantımıza ulaşma kanıtı yok. Dolayısıyla aşağıdakiler uygulanabilir geçmiş bot PnL’si değildir.
Senaryolar her pencereyi ayrı hesaplar; portföyün −10 $ yeni-risk kesicisi geçmiş sonuçlara uygulanmadı.

| Ek fiyat stresi yok, ücret var | Giriş | Senaryo PnL $ | En iyi üç hariç $ |
|---|---:|---:|---:|
| Ucuz taraf, tut | 524 | −36,51 | −49,15 |
| Referans yönü, tut | 64 | −0,31 | −8,89 |
| Olasılık farkı, tut | 21 | +11,29 | +0,68 |
| Aynı 21 giriş + tamamlama | 21 | +2,66 | −5,24 |
| Aynı 21 giriş + tamamlama + filtreli ekleme | 21 | +6,03 | −5,24 |

Son kol yalnız **bir ekleme** üretti; Bosona’nın yüzlerce geç eklemesini açıklamıyor.
Olasılık girişindeki aynı 21 işlemi sabit tutup fiyatı 5¢ kötüleştirince toplam +5,99 $, en iyi üç hariç −3,86 $.
Yalnız yüksek maliyet senaryosunda kalan işlemleri seçerek görülen artışı dayanıklılık saymadım.
21 Eylül’de bu kuralın uygun veri bulunan 48 penceresinde **sinyal yok**; bunu veri eksiği veya kazanç diye yazmadım.

**Sonraki shadow için karar.** Güçlü/kârlı model eşiğini geçen aday **yok**.
Tek ileri araştırma önceliği olarak **BTC15dk envanter + fiyat farkı v0** tasarımı donduruldu; “Bosona çözüldü” iddiası değil.
Şimdiki kanıt yalnız düşük bütçeli sanal yanlışlama testini gerekçelendiriyor. Bu görevde shadow kurulmadı/başlatılmadı.

- Giriş: resmî başlangıçtan 180sn sonra; alınabilir beş pay fiyatı ≤0,55, ücret sonrası tahmini ödeme farkı ≥0,05; tam referans ve taze veri zorunlu.
- Ekleme: yalnız t600’de, bir kez beş pay, kendi açık yönüne; giriş filtresi yeniden geçerli olmalı. Başka piyasadaki Bosona dolumu tetikleyici değil.
- Tamamlama: t240…840, 60sn aralıkla; önce tamamlama kontrolü; FIFO maliyet + yeni ücretli maliyet ≤0,98; en çok açık miktar ve beş pay. Fazla alım/reopen yok.
- Çıkış: kalan miktarı resmî sonuca taşı; hayalî stop fiyatı yok. En çok 10 açık pay, piyasa başına 15 $ alış ve 5 $ en kötü sonuç riski; portföyde bir yeni risk piyasası.
- Kontrol: aynı ilk giriş, aynı izin verilen limitler, aynı tamamlama, **ekleme yok**. “Yalnız ilk alımı tut” ayrıca tanı kolu. Kolların sanal dolarları tek portföy gibi toplanmaz.
- Veri/uygulama: fiyat ve referans en fazla 3sn eski; spread ≤3¢, beş pay gerçek ask derinliği, piyasanın resmî ücreti;
  karardan en az 250ms sonra yeni defter, en geç 3sn içinde; fiyat ve risk sınırı uygulamada tekrar kontrol edilir.
- Başarı: ≥10 tam UTC gün, ≥100 girişli piyasa **ve ≥50 eklemeli piyasa**, ≥%95 veri kapsamı;
  ücret sonrası mutlak PnL ve kontrole fark pozitif; piyasa/gün kümeli %95 alt sınırlar >0; en iyi üç hariç pozitif.
  Hedefi tutmayan süre UNDERPOWERED. Gün içi −10 $ eşiği yeni riski keser, garanti edilmiş toplam zarar sınırı değildir.

Parametreler yeni sonucu gördükten sonra oynatılmayacak. Eklemeyi nadiren seçmesi nedeniyle bu deney uzun sürebilir;
14 günlük ilk değerlendirmede sayı yetmezse olumlu karar verilmez. Ekonomi ve davranış benzerliği ayrı ölçülür.
[Çalıştırılabilir karar/defter uyarlayıcısı](candidate.py), [tam sabit protokol](protocol.json).

**Eksik bilgi ve resmî kurallar.**

Ana sekiz grubun 7.956 sözleşmesi yerel defter DB’sinde salt okunur sorgulandı: **sıfır tarihsel defter kaydı**.
Bu, bütün olası uzak arşivlerde veri olmadığı iddiası değil; bu araştırmanın doğrulanabilen defter kapsamı.
18.220 tokenın 18.218’inde toplam 2.749.016 kamu fiyat örneği alındı. Örnek fiyat spread, derinlik, likidite veya maker kuyruk sırası değildir.
Gamma’nın sonradan görülen hacim/likidite alanlarını karar girdisi yapmadım.
BTC15dk için mevcut kayıtların gerçek alım zamanlarıyla 20.533 Chainlink bağlamı üretildi; bulunmayan referanslar dışlandı.
ETH/SOL kısa sürelerde aynı nitelikte tarihsel Chainlink/defter yok; kapalı Binance dakikası yalnız açıkça etiketli vekil.

Sınıf, isimden değil resmî `eventStartTime`, `endDate`, `resolutionSource`, açıklama ve token eşleşmesinden doğrulandı.
5/15dk ve incelenen 4saatlikler Chainlink TWAP60; saatlikler Binance 1H açılış/kapanışı.
Günlükler iki farklı gündeki ET öğlen 1dk mum **kapanışlarını** karşılaştırıyor; eşitlikte 50–50 kuralı var.
Saatlik eşitlik Up olurken günlük eşitlik farklı; bu mekanizmalar birleştirilmedi. Örneklemde eşit günlük sonuç yok.
[TWAP kaynağı](https://docs.polymarket.com/market-data/chainlink-twap),
[saatlik sözleşme örneği](https://polymarket.com/event/ethereum-up-or-down-september-20-2026-8pm-et),
[günlük sözleşme örneği](https://polymarket.com/event/bitcoin-up-or-down-on-september-19-2026).

**Yeniden üretim ve kontroller.**

İzole alan: `{r.HERE}`. Ana repo, Londra süreçleri, Jev, shadow’lar, kaydediciler ve bütçelerine yazılmadı; emir/ücretli servis kullanılmadı.
Önceki indirme, FIFO, Decimal muhasebe, sonuç ve ücret araçları `src/` altında hash ile dondurularak yeniden kullanıldı.
Yeni uyarlama yalnız arşiv örtüşmesi ile gerçek dolum çokluğunu ayırıyor.
9.110 resmî sonuç kontrolü; 9.107’sinde metadata başlangıç/son fiyatı da mevcut; Binance saatlik/günlük sonuçlar mumlarla ayrıca eşleşti.
39 piyasanın bağımsız endpoint kayıt çokluğu/miktar/brüt PnL kontrolü; tüm pencerelerde nakit PnL/FIFO/parça/ödeme sınırı kontrolleri geçti.
Taze son 12 saat, 1.195 işlem: eklenen/eksilen sıfır. [Kontroller](results/checks.json), [API denetimi](results/api_validation.json).
Gelecek/bayat fiyat, aynı başlangıçtaki farklı piyasaları karıştırmama, çoklu kayıt, ücret/derinlik, kısmi tamamlama ve risk sınırı testleri var.
Hedefli Ruff ve Python derlemesi çalıştırıldı. Tam komutlar [README](README.md) içinde; ana kodu çalıştırmaz.

Veri kaynakları: [kamu activity](https://docs.polymarket.com/api-reference/core/get-user-activity),
[kamu trades](https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets),
[Gamma sözleşmeler](https://docs.polymarket.com/api-reference/markets/list-markets),
[toplu fiyat geçmişi](https://docs.polymarket.com/api-reference/markets/get-batch-prices-history),
[ücret hesabı](https://docs.polymarket.com/trading/fees),
[Binance mumları](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints).
Kamu dolum saati emir saati değildir; gerçekleşmeyen emirler, iptaller, özel hedef envanter ve gerçek uygulama başarısı bilinmiyor.
'''
    (r.HERE/'RAPOR.md').write_text(text)
    print('RAPOR.md and protocol.json generated')


if __name__=='__main__':
    build()
