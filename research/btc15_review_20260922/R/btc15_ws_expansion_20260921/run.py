"""Fixed three-window public-only continuation; reuse the frozen audit helpers."""
from pathlib import Path
from collections import Counter
from decimal import Decimal as D
import json
import subprocess
import sys
from datetime import datetime,timezone

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parent
W = R/'btc15_ws_validation_20260921'
sys.path.insert(0, str(W))
import study as a  # noqa: E402

STARTS = (1790024400, 1790025300, 1790026200)
ex = a.module('expanded_execution', HERE/'execution.py')


def select(start):
    a.HERE = HERE/'markets'/str(start)
    a.HERE.mkdir(parents=True, exist_ok=True)
    a.START, a.END, a.CUT = start, start+900, (start+1020)*1000
    a.SLUG = f'btc-updown-15m-{start}'


def protect():
    a.protected()
    p = HERE/'protected.json'
    if not p.exists():
        files = list(W.glob('*.py'))+list((W/'results').glob('*.json'))
        files += list(a.V.glob('*.py'))+list((a.V/'results').glob('*.json'))
        a.save(p, {str(x):a.sha(x) for x in files})
    for path, digest in a.read(p).items():
        assert a.sha(Path(path))==digest, path
    p = HERE/'dependencies.json'
    if not p.exists():
        modules = (a,ex.engine,ex.engine.old,ex.engine.old.c,ex.engine.old.r,
                   ex.engine.old.r.base,ex.engine.old.r.deep,ex.engine.old.r.cross)
        a.save(p,{str(Path(m.__file__)):a.sha(Path(m.__file__)) for m in modules})
    for path,digest in a.read(p).items():
        assert a.sha(Path(path))==digest,path


def fetch():
    protect()
    for start in STARTS:
        select(start)
        a.freeze()
        a.fetch()
        a.confirm()
    protect()


def analyze():
    protect()
    # The old independent 1-second quote probes require a constant tick. This
    # cohort tests the full inventory policy below, with event-time tick checks.
    def inventory_only(*_):
        return dict(rows=[],status_counts={},note='Not run: independent short quotes are outside this inventory experiment.')
    a.quote_probes = inventory_only
    for start in STARTS:
        select(start)
        a.analyze()
        audit = a.read(a.HERE/'results/report.json')
        tokens = json.loads(a.read(a.HERE/'raw/market_start.json')['data']['clobTokenIds'])
        events, origin = book_events(a.events(),tokens)
        snaps,issues = a.m1.books_at(events,tokens,[(start+n)*1000 for n in range(901)])
        bad = []
        for t,bb in snaps.items():
            if (any(not b['ready'] or not 0<=t-b['rcv']<=3000 or not 0<=t-b['obs']<=3000
                    or (b['BUY'] and b['SELL'] and max(b['BUY'])>=min(b['SELL'])) for b in bb)
                or any(bb[s]['BUY']!={1000000-p:q for p,q in bb[1-s]['SELL'].items()} for s in (0,1))):
                bad.append(t)
        fail = (audit['explicit_gaps'] or issues.get('future_source_clock') or issues.get('out_of_order_book')
                or len(bad)>.05*901 or audit['flow_errors'] or audit['receipt_failures'] or audit['bad_flow_clocks']
                or any(audit['api_differences'][k] for k in ('true_confirmed','false'))
                or any(x['in_window_by_block_clock'] for x in audit['chain_matches_without_ws']))
        a.save(a.HERE/'results/eligibility.json',dict(data_gate='MISSING_DATA' if fail else 'PASS_OBSERVED_FLOW_GATE',
            original_gate=audit['data_gate'],book_origin_ms=origin,book_issues=issues,invalid_book_times=bad,
            valid_book_samples=901-len(bad),
            reason='Restart from latest paired complete snapshot received before start; earlier connection history retained in raw audit.'))
    protect()


def book_events(events,tokens):
    paired = {}
    for e in events:
        if e['k']=='book' and e['rcv']<=a.START*1000:
            paired.setdefault(e['rcv'],set()).add(e['p']['asset_id'])
    origin = max(t for t,sides in paired.items() if sides==set(tokens))
    return [e for e in events if e['rcv']>=origin],origin


def ticks_at(events, tokens, checkpoints):
    ticks, result, cursor = {t:None for t in tokens}, {}, 0
    for now in sorted(checkpoints):
        while cursor<len(events) and events[cursor]['rcv']<=now:
            e = events[cursor]
            cursor += 1
            p = e['p']
            if e['k'] in ('gap','connect'):
                ticks = {t:None for t in tokens}
            elif e['k'] in ('book','tick_size_change'):
                assert int(p['timestamp'])<=e['rcv']
                value = p.get('tick_size') if e['k']=='book' else p['new_tick_size']
                if value is not None:
                    value = D(value)
                    assert value in (D('.1'),D('.01'),D('.001'),D('.0001'))
                    ticks[p['asset_id']] = value
        result[now] = [ticks[t] for t in tokens]
    return result


def candidate(client, venue, market, streams, starts, delay):
    """Frozen P0 decisions; full-size taker execution with a predecision cash limit."""
    c = ex.engine.old.c
    s, gaps, trace = c.state(), Counter(), []
    for age in range(180,841,60):
        now = (a.START+age)*1000
        # Once a valid entry decision said no, the unchanged rule cannot enter later.
        if age>180 and not s['entered'] and not gaps:
            continue
        try:
            f = ex.engine.old.context(streams, starts, a.START, a.END, now/1000)
            books = client[now]
            if any(ex.engine.quote(ex.book_tuple(b),now) is None for b in books):
                raise ValueError('missing_decision_book')
            prices = [float(D(min(b['SELL']))/ex.UNIT) for b in books]
        except (ValueError,KeyError) as err:
            gaps[str(err)] += 1
            continue
        intent = c.decide(s,age,prices,f)
        trace.append(dict(age=age,context=f,prices=prices,intent=intent))
        if intent is None:
            continue
        side,qty = intent['side'],intent['qty']
        if intent['kind']=='complete':
            old_cost = c.complete_cost(s,side,qty,0)
            limit = D('.98')-D(str(old_cost))
        else:
            prob = f['final_up_prob'] if side==0 else 1-f['final_up_prob']
            limit = min(D(str(prob))-D('.05'),D(str(c.unit_cost(.55,.07))))
        # Existing inventory/risk constraints also form part of the sent limit.
        q = s['q'].copy()
        q[side] += qty
        limit = min(limit,D(str((15-s['cash'])/qty)),D(str((5+min(q)-s['cash'])/qty)))
        trace[-1]['sent_cash_limit'] = limit
        when = now+delay
        b = venue[when][side]
        if ex.engine.quote(ex.book_tuple(b),when) is None:
            gaps['missing_arrival_book'] += 1
            continue
        try:
            cost = ex.engine.ask_cost(ex.book_tuple(b)[1],D(str(qty)),market)
        except ValueError:
            trace[-1]['execution'] = 'insufficient_depth'
            continue
        if cost>limit:
            trace[-1]['execution'] = 'price_limit_rejected'
            continue
        # The next decision is 60 seconds later; both assumed notification delays finish first.
        assert delay*2<60000
        price = float(D(min(b['SELL']))/ex.UNIT)
        assert c.apply(s,intent,price,0,(when+delay)/1000,quoted_unit_cost=float(cost))
        trace[-1]['execution'] = 'filled'
    return dict(state=s,gaps=dict(gaps),trace=trace,economic_pnl=None)


def replay():
    protect()
    chain = a.read(HERE/'raw/chainlink_manifest.json')
    for path, info in chain.items():
        assert a.sha(HERE/path)==info['sha256']
    streams, refs = ex.engine.old.chainlink_streams([HERE/p for p in chain])
    output = []
    for start in STARTS:
        select(start)
        a.verify_inputs()
        audit = a.read(a.HERE/'results/eligibility.json')
        row = dict(start=start,data_gate=audit['data_gate'],arms={},control={})
        ee = a.events()
        row['tick_events'] = [e for e in ee if e['k']=='tick_size_change']
        if audit['data_gate']!='PASS_OBSERVED_FLOW_GATE':
            row.update(economic_pnl=None,reason='incomplete observed feed; whole assigned market retained')
            output.append(row)
            continue
        market = a.read(a.HERE/'raw/market_start.json')['data']
        tokens = json.loads(market['clobTokenIds'])
        ee,_ = book_events(ee,tokens)
        checkpoints = [(start+n)*1000 for n in range(30,841)]
        client,_ = a.m1.books_at(ee,tokens,checkpoints)
        client_ticks = ticks_at(ee,tokens,checkpoints)
        source = sorted([dict(e,rcv=int(e['p']['timestamp'])) for e in ee
                         if e['k'] in ('book','price_change','tick_size_change')],key=lambda e:e['rcv'])
        groups = {p.stem:a.m1.matches(a.read(p)['data']) for p in (a.HERE/'raw/receipts').glob('*.json')}
        flows,errors,_ = a.m1.trade_flows(ee,groups,tokens)
        assert not errors
        makers = {(tx,m['log_index']):m for tx,gg in groups.items() for g in gg for m in g['makers']}
        prints = []
        for f in flows:
            m = makers[f['tx'],f['log_index']]
            gross = m['cash_cost']-m['fee'] if m['side']==0 else -m['cash_cost']+m['fee']
            cash = gross if m['side']==0 else m['qty']-gross
            assert f['obs_lo']==f['obs_hi'] and f['received']>=f['obs_lo']
            prints.append(dict(side=f['side'],qty=D(m['qty'])/ex.UNIT,gross=D(cash)/ex.UNIT,
                               obs=f['obs_lo'],rcv=f['received']))
        result_market = a.read(a.HERE/'raw/market_result.json')['data']
        for m in (market,result_market):
            meta = a.accounting.ref.classify(m)
            assert (meta['group'],meta['S'],meta['end'],meta['mechanism'])==( 
                'btc_15m',start,start+900,'chainlink_twap60')
            assert json.loads(m['clobTokenIds'])==tokens
            assert m['feesEnabled'] and D(str(m['feeSchedule']['rate']))==D('.07')
            assert m['feeSchedule']['exponent']==1
        official_ref = next(e['eventMetadata']['priceToBeat'] for e in result_market['events']
                            if e['slug']==a.SLUG)
        row['reference_matches'] = start in refs and abs(refs[start][1]-float(official_ref))<1e-6
        winner = a.accounting.ref.base.outcome(result_market)
        assert winner in (0,1), 'official result not final'
        row['winner'] = winner
        actor = [(f,role) for gg in groups.values() for g in gg
                 for role,ff in (('taker',[g['active']]),('maker',g['makers'])) for f in ff
                 if f['owner']==a.public.WALLET and f['token'] in tokens]
        actor_q = [sum((D(f['qty'])*(1 if f['side']==0 else -1)/ex.UNIT for f,_ in actor if f['token']==t),D(0)) for t in tokens]
        actor_cash = sum((D(f['cash_cost'])/ex.UNIT for f,_ in actor),D(0))
        row['bosona'] = dict(fills=len(actor),roles=dict(Counter(role for _,role in actor)),
            buys=sum(f['side']==0 for f,_ in actor),q=actor_q,trade_cash=actor_cash,
            trade_pnl=actor_q[winner]-actor_cash,
            note='All public trades for this contract, including pre-start. No rebate or transfer-balance claim; not equal-risk policy comparison.')
        for delay,extra in ((250,0),(750,500)):
            times = [t+delay for t in checkpoints]
            venue,_ = a.m1.books_at(source,tokens,times)
            venue_ticks = ticks_at(source,tokens,times)
            p0 = candidate(client,venue,market,streams,refs if row['reference_matches'] else {},delay)
            p0['conditional_pnl'] = (p0['state']['q'][winner]-p0['state']['cash']) if not p0['gaps'] else None
            row['control'][str(delay)] = p0
            for name,offset,hedge in (('M1_bid',D(0),False),('M1_bid_minus_cent',D('.01'),False),('M2_bid_hedge',D(0),True)):
                for mode in ('queue_back','queue_front'):
                    value = ex.run(client,venue,prints,market,mode,offset,hedge,
                                   delay,extra,client_ticks,venue_ticks)
                    value['conditional_pnl'] = value['actual']['q'][winner]-value['actual']['cash'] if not value['unknown'] else None
                    value['economic_pnl'] = None
                    row['arms'][f'{name}:{mode}:{delay}'] = value
        output.append(row)
        print('Replayed',start,flush=True)
    a.save(HERE/'results/replay.json',dict(markets=output,status='CONDITIONAL_UNCALIBRATED',
        assumptions=dict(delays_ms=[250,750],extra_maker_learning_ms=[0,500],
        queue='visible static queue back or first in queue; no cancellation credit',
        clocks='public WS server clock proxies venue; public receive proxies private learning',
        scope='three consecutive assigned markets; missing markets are not zero PnL',
        rebate=0,market_impact='ignored',portfolio='each arm is independent; no cross-arm cash sharing')))
    protect()


def repeat():
    hashes = []
    for _ in range(2):
        analyze()
        replay()
        report()
        paths = sorted((HERE/'markets').glob('*/results/*.json'))
        paths += [HERE/'results/replay.json',HERE/'results/summary.json',HERE/'RAPOR.md']
        hashes.append({str(p.relative_to(HERE)):a.sha(p) for p in paths})
    assert hashes[0]==hashes[1], 'offline outputs changed'
    subprocess.run([sys.executable,'-B',str(HERE/'check.py')],check=True,cwd=HERE)
    for p in HERE.glob('*.py'):
        compile(p.read_text(),str(p),'exec')
    subprocess.run([sys.executable,'-m','ruff','check','--no-cache',str(HERE)],check=True,cwd=HERE)
    a.save(HERE/'results/reproduction.json',dict(identical_runs=2,hashes=hashes[0],
        checks_sha256=a.sha(HERE/'results/checks.json'),syntax='PASS',ruff='PASS',
        sources={str(p):a.sha(p) for p in HERE.glob('*.py')}))
    protect()


def report():
    rows = a.read(HERE/'results/replay.json')['markets']
    valid = [x for x in rows if x['arms']]
    summary = {}
    for key in sorted({k for x in valid for k in x['arms']}):
        values = [x['arms'][key]['conditional_pnl'] for x in valid]
        known = [D(v) for v in values if v is not None]
        summary[key] = dict(assigned_markets=len(rows),feed_eligible_markets=len(valid),
            resolved_scenarios=len(known),per_market=values,
            eligible_cohort_pnl=sum(known,D(0)) if len(known)==len(valid) else None,
            excluding_best=sum(known,D(0))-max(known) if len(known)==len(valid) and len(known)>1 else None,
            all_assigned_pnl=None,economic_pnl=None)
    a.save(HERE/'results/summary.json',summary)
    def cash(value):
        return 'BELİRSİZ' if value is None else f'{D(str(value)):+.4f}'
    lines = ['# BTC15 yeni pencere karşılaştırması',
        '', '**Sonuç: kârlı taklit kanıtı yok.** Yeni üç atamanın biri bağlantı kopması nedeniyle eksik; '
        'iki pencere koşullu simülasyona uygun. Ana 250ms/kuyruk-arkası senaryosunda '
        'pasif bid ve aynı kurala dengeleme eklenmiş kol toplam −1,84033524$; '
        'bid−1sent −4,45$. Eski aday iki geçerli pencereye de girmedi (0$). '
        'Bu 0$, eksik veri nedeniyle değil, geçerli giriş filtreleri nedeniyle.',
        '', 'Kohort 21 Eylül 21:50 UTC civarında sonuç tablosu açılmadan takvimle sabitlendi. '
        'Uygulama motoru bu kesitte geliştirilip denetlendi; bu küçük çalışma temiz bir kör '
        'ekonomik doğrulama değildir. Önceki 20:45–21:00 pencerenin sonucu bu toplamlara eklenmedi.',
        '', '## Veri ve mutabakat', '',
        '| UTC pencere | Receipt | WS mesajı / pencere içi | Uygun defter noktası | Karar |',
        '|---|---:|---:|---:|---|']
    totals = Counter()
    for row in rows:
        root = HERE/'markets'/str(row['start'])
        audit,gate = a.read(root/'results/report.json'),a.read(root/'results/eligibility.json')
        fetch_info = a.read(root/'raw/fetch.json')
        label = datetime.fromtimestamp(row['start'],timezone.utc).strftime('%H:%M')
        n,ws = len(fetch_info['transactions']),audit['metrics']['mapped_messages']
        totals.update(receipts=n,ws=ws,in_window=audit['trade_time_segments']['in_window'])
        lines.append(f"| {label}–{datetime.fromtimestamp(row['start']+900,timezone.utc):%H:%M} | {n} | {ws} / {audit['trade_time_segments']['in_window']} | {gate['valid_book_samples']}/901 | {row['data_gate']} |")
    lines += ['',f"Toplam {totals['receipts']} receipt ve {totals['ws']} WS mesajının gerçek miktar/nakitleri uzlaştı; "
        f"{totals['in_window']} mesaj sözleşme pencerelerinin içinde. Her piyasada ilk ve ikinci taker "
        'API listesi ile tüm katılımcı listesi zincirle eşleşiyor; bu kesitte API çokluk farkı yok. '
        'Her piyasada iki receipt ikinci ücretsiz RPC ile kontrol edildi.',
        '', '21:00 penceresinde 901/901 defter örneği iyi olsa da 21:10:47.580 UTC bağlantı kopması var. '
        'Sıfır kâr diye sayılmadı. 21:15 penceresinin ilk geniş önek kontrolündeki iki ters-saat uyarısı '
        'başlangıçtan 250 saniye önceki yeniden bağlantıya ait: eski delta ile yeni tam görüntü 1ms ters. '
        'Yeni hesap başlangıçtan önce alınmış son tam çift-token görüntüden başlar. Eski ham kontrol '
        '`report.json`, pencereye ait gerekçe `eligibility.json` içinde korunur. '
        '21:15 penceresinde t520’de tek defter-derinliği aynalama uyuşmazlığı kalır; '
        'önceki %95 uygun örnek kapısı değiştirilmedi. Bu bir kalibrasyon veya kusursuz defter iddiası değildir.',
        '', 'Fiyat adımı sonradan alınmış Gamma değerinden geriye yazılmaz; karar ve kabul anlarında '
        'alınmış book/tick_size_change olayından okunur. Eski bağımsız 16 kısa kotasyon deneyi '
        'bu tur koşulmadı; karşılaştırma tek envanter izleyen tam politikalarla yapıldı.',
        '', '## Aynı kuralların yeni sonuçları', '',
        '**Aşağıdakiler varsayımlara koşullu simülasyon dolarlarıdır; ekonomik PnL bütün kollarda null.** '
        '5 pay klip, 10 net, 15$ nakit, −5$ en kötü sonuç; t30..839 her saniye karar, t840 iptal. '
        'Fiyatlar veya eşikler kâra göre taranmadı. Maker iadesi sıfır varsayıldı; taker ücreti nakitte dahil.',
        '', '| Kol / kuyruk / gecikme | 21:15 | 21:30 | İki uygun pencere toplamı | En iyi pencere hariç |',
        '|---|---:|---:|---:|---:|']
    for key,v in summary.items():
        lines.append('| '+key+' | '+' | '.join(cash(x) for x in v['per_market'])+
                     f" | {cash(v['eligible_cohort_pnl'])} | {cash(v['excluding_best'])} |")
    lines += ['| P0 mevcut aday / 250 veya 750ms | 0 | 0 | 0 | 0 |',
        '', 'Üç atamanın tamamının toplamı hiçbir kol için hesaplanabilir değil. 750ms/kuyruk-arkası '
        '21:15 yollarında bir kamu mesajı tam varsayılan emir yaşam-döngüsü zamanına denk geliyor. '
        'Önce doldu/önce iptal oldu sırası seçilmedi; üç hücre BELİRSİZ kaldı. '
        'Kuyruk önü ve arkası PnL alt–üst sınırı değildir: önde olmak zararlı dolumları da artırabilir.',
        '', '## Eski aday neden girmedi?', '',
        '| UTC başlangıç | Up ask | Model Up | Ücret sonrası Up avantajı | Engel |',
        '|---|---:|---:|---:|---|']
    for row in valid:
        entry = row['control']['250']['trace'][0]
        p,prob = entry['prices'][0],entry['context']['final_up_prob']
        edge = prob-ex.engine.old.c.unit_cost(p,.07)
        reasons = []
        if edge<.05:
            reasons.append('olasılık avantajı <5¢')
        if p>.55:
            reasons.append('55¢ tavanı')
        lines.append(f"| {datetime.fromtimestamp(row['start'],timezone.utc):%H:%M} | {100*p:.1f}¢ | %{100*prob:.2f} | {100*edge:.2f}¢ | {', '.join(reasons)} |")
    lines += ['', 'Her iki pencerede 12/12 planlı bağlam için nedensel Chainlink verisi bulunuyor; '
        'kaydedilmiş açılış TWAP’ı resmî referansla eşleşiyor. P0 ilk kararından sonra giriş imkânı '
        'bulunmayan pencereyi tekrar açmaz. İlk giriş olmadığı için sonraki ekleme/envanter kapıları '
        'devreye girmiyor. 55¢ tavanı veya olasılık eşiği değiştirilmedi.',
        '', '## Dengeleme neden her zaman çalışmıyor?', '',
        '21:15 kuyruk-önü/250ms yolunda t46’da 10 Up / 20 Down var; 14,50$ harcanmış. '
        '5 Up hedge için 3,084$ gerekiyor, toplam 17,584$ olacağı için 15$ sınırı reddediyor. '
        'Dengeleme zararı azaltabilecek olsa da kullanabileceği nakit kalmamış. '
        'Kod bütçeyi aşmadı; mevcut mekanizma dengelemeye her zaman bütçe bırakmıyor. '
        'Bu bulgu limitleri artırma veya geçmişe göre hedge eşiği değiştirme gerekçesi yapılmadı.',
        '', 'Ana kuyruk-arkası/250ms yollarında net 10 paya ulaşmadığı için iki piyasada da taker '
        'dengelemeye geçilmiyor; M1 ve M2 aynı. Başka senaryodaki küçük pozitif hedge sonucu genel '
        'üstünlük kanıtı değildir. Tüm sonuçlarda gerçekleşen ve öğrenilmiş envanter ayrı; iptal '
        'yoldayken dolum ve gecikmiş kümülatif bildirim aynı dolumu iki kez yaratmaz.',
        '', '## Bosona aynı piyasalarda ne yaptı?', '',
        '| UTC başlangıç | Dolum | Maker / taker | İşlem nakit PnL |',
        '|---|---:|---:|---:|']
    for row in valid:
        b = row['bosona']
        lines.append(f"| {datetime.fromtimestamp(row['start'],timezone.utc):%H:%M} | {b['fills']} | {b['roles'].get('maker',0)} / {b['roles'].get('taker',0)} | {cash(b['trade_pnl'])} |")
    lines += ['', 'Bosona sonuçları ilgili sözleşmenin tüm kamu alım/satımlarından ve resmî ödemeden; '
        'pencere öncesi alımlar dahil, iadeler ve harici transfer bakiyesi hariç. Ham dolarlar küçük '
        'sanal kollarla eşit-risk kıyası değildir. İkinci piyasada iki maker alımı toplam 200 Down payı '
        '22$’a almış; Up kazandı. Dolum yapmaması emir koymadığını kanıtlamaz. '
        'Bizim her pencereye kotasyon veren mekanizmamız onun piyasa seçimini henüz açıklamıyor.',
        '', '## Karar ve sınanacak sonraki açık', '',
        'M1’in basit bid fiyatlaması yeni iki uygun pencerede ana senaryoda kazanmadı. M2’nin '
        'dengelemeye geçebilmesi envanter eşiği kadar kalan nakde de bağlı. Bunlar aynı iki hipotezin '
        'karşı kanıtlarıdır; üçüncü bir strateji veya yeni seçilmiş eşik üretilmedi. '
        'Pasif rolü anlamaya ilerledik; Bosona’nın fiyat/iptal/boy/piyasa seçimini çözmüş değiliz.',
        '', 'Bir sonraki ayırıcı iş, emir kabul/iptal/öğrenme zamanlarını eldeki ölçüm kayıtlarıyla '
        'kalibre etmek ve aynı sabit kolları daha fazla kesintisiz günde sınamak. 250/750ms '
        'bir ölçüm sonucu değil. Kuyruk sahipliği L2’den çözülemez. Dengeleme için nakit ayırma '
        'gerekirse ayrı ileri protokol olur; bu tur uygulanmadı. On gün/100giriş/50ekleme '
        'ekonomik kabul eşiği açık; bu veriden güvenilir üstünlük aralığı çıkmaz.',
        '', '## Tekrar üretim', '', '```bash', f'cd {HERE}',
        'P=/home/taygun/Masaüstü/KararAtlas/base1/bin/python3',
        'OPENBLAS_NUM_THREADS=1 "$P" -B run.py repeat', '```',
        '', '`run.py fetch` yalnız eksik kamu önbelleğini tamamlar. `repeat` ağ kullanmadan iki '
        'tam koşu, para/zaman/tick/P0 karşı örnekleri, Ruff ve syntax kontrolünü yapar; '
        '`results/reproduction.json` SHA kanıtıdır. `protected.json` eski W/V kaynak ve sonuçlarını, '
        '`dependencies.json` yeniden kullanılan kaynakları, eski baseline aday/protokolü korur.',
        '', 'Ham veriler `markets/<başlangıç>/raw/`; URL, istek/alım zamanı, receipt/block ve ikinci RPC '
        'kontrolleri içerir. Canlı gzip dosyalarının yalnız sabit byte öneki kopyalandı. Açık Chainlink '
        'gzip kuyruğu tamamlanmış arşiv sayılmaz; seçilen karar zamanlarının sonrasına kadar geçerli '
        'satırlar hash ile sabitlendi. Kaynak: [resmî WS olay şeması](https://docs.polymarket.com/market-data/realtime-data).',
        '', 'Bu çalışma yeni shadow/LIVE/emir, ücretli servis veya çalışan recorder değişikliği yapmadı.']
    (HERE/'RAPOR.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    {'fetch':fetch,'analyze':analyze,'replay':replay,'report':report,'repeat':repeat}[sys.argv[1]]()
