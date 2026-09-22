"""Finite, offline timing sensitivity. Prior candidates and raw artifacts are read-only."""
from collections import Counter
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch
import gzip
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parent
W = R/'btc15_ws_validation_20260921'
E = R/'btc15_ws_expansion_20260921'
Z = R/'btc15_execution_reserve_20260921'
N = R/'btc15_feed_integrity_20260922'
sys.path.insert(0,str(W))
import study as a  # noqa: E402
prior = a.module('timing_prior_helpers',E/'run.py')
ex = a.module('timing_execution',HERE/'execution.py')
legacy = a.module('timing_legacy_execution',Z/'execution.py')
PROTOCOL = a.read(HERE/'protocol.json')
ARMS = [('M1_bid',D(0),False,False),('M1_bid_minus_cent',D('.01'),False,False),
        ('M2_bid',D(0),True,False),('M2_reserved',D(0),True,True)]


def source(start):
    if start==1790023500:
        return W
    if start==1790031600:
        return N/'market'
    return (E if start<1790027100 else Z)/'markets'/str(start)


def protect():
    a.protected()
    assert a.sha(HERE/'protocol.json')==(HERE/'protocol.sha256').read_text().strip()
    for root in (Z,N):
        for name,digest in a.read(root/'delivery_manifest.json')['sha256'].items():
            assert a.sha(root/name)==digest,str(root/name)
    for name,digest in a.read(E/'dependencies.json').items():
        assert a.sha(Path(name))==digest,name
    path = HERE/'sources.json'
    if not path.exists():
        paths = [R/'candidate.py',R/'protocol.json',W/'study.py',E/'run.py',Z/'execution.py',
                 Z/'delivery_manifest.json',N/'delivery_manifest.json',E/'dependencies.json']
        a.save(path,{str(p):a.sha(p) for p in paths})
    for name,digest in a.read(path).items():
        assert a.sha(Path(name))==digest,name


def prepare():
    protect()
    path = HERE/'raw/chainlink.jsonl.gz'
    if not path.exists():
        # Closed byte prefix only; no writes to the running price recorder.
        src = Path('/home/taygun/Masaüstü/polymarket/data/tape_cl_direct/cld_20260921_23.jsonl.gz')
        tmp = HERE/'raw/cld_source_prefix.gz'
        tmp.parent.mkdir(parents=True,exist_ok=True)
        with src.open('rb') as f:
            tmp.write_bytes(f.read(src.stat().st_size))
        rows,open_tail = [],False
        try:
            with gzip.open(tmp,'rt') as f:
                for line in f:
                    row = json.loads(line)
                    if row['rcv']<=1790032620000:
                        rows.append(row)
        except EOFError:
            open_tail = True
        path.write_bytes(gzip.compress(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows).encode(),mtime=0))
        a.save(HERE/'raw/chainlink_manifest.json',dict(source=str(src),prefix_sha256=a.sha(tmp),
            normalized_sha256=a.sha(path),rows=len(rows),open_tail=open_tail,max_received_ms=max(r['rcv'] for r in rows)))
    a.public.cached(HERE/'raw/market_result_1790031600.json',
                    'https://gamma-api.polymarket.com/markets/slug/btc-updown-15m-1790031600')
    p = HERE/'raw/manifest.json'
    if not p.exists():
        a.save(p,{str(f.relative_to(HERE)):a.sha(f) for f in (HERE/'raw').glob('*') if f.is_file()})
    protect()


def select(start):
    root = source(start)
    a.HERE,a.START,a.END,a.CUT = root,start,start+900,(start+1020)*1000
    a.SLUG = f'btc-updown-15m-{start}'
    a.verify_inputs()
    special = start==1790031600
    report = a.read((N/'channels/A' if special else root)/'results/report.json')
    gatepath = root/'results/eligibility.json'
    gate = a.read(gatepath)['data_gate'] if gatepath.exists() else report['data_gate']
    reasons = []
    if gate!='PASS_OBSERVED_FLOW_GATE':
        reasons.append('frozen_data_gate_failed')
    if special:
        chain = a.read(N/'results/independent_chain.json')
        comparison = a.read(N/'results/comparison.json')
        diag = a.read(N/'results/api_diagnostic.json')['rows']
        assert not chain['new_to_api_ws_universe'] and not chain['known_receipts_absent_from_scan']
        assert not comparison['only_a'] and not comparison['only_b']
        assert all(x['only_missing_row_added'] for x in diag)
        # First gate remains failed; subsequent exact reconciliation is a new offline label.
        confirmed = a.read(N/'channels/A/results/api_reconciliation.json')
        assert len(confirmed['true_confirmed']['differences'])==1 and not confirmed['false']['differences']
        assert report['api_differences']==dict(true_initial=1,true_confirmed=1,false=0)
        reasons = ['LATER_RECONCILED_API_ONLY']
    eligible = gate=='PASS_OBSERVED_FLOW_GATE' or reasons==['LATER_RECONCILED_API_ONLY']
    return root,dict(start=start,frozen_data_gate=gate,offline_status='RECONCILED_LATER' if special else gate,
                     replay_eligible=eligible,reasons=reasons,economic_pnl=None)


def ticks_with_initial(events,tokens,checkpoints,initial):
    """A received pre-window metadata observation seeds tick state; future values cannot."""
    when=initial.get('received_ms')
    tick=initial['data'].get('orderPriceMinTickSize')
    seed=[]
    if when is not None and tick is not None:
        assert D(str(tick)) in (D('.1'),D('.01'),D('.001'),D('.0001'))
        # Internal tick-only input to the existing helper, never a fabricated raw book.
        seed=[dict(k='book',rcv=when,p=dict(asset_id=t,timestamp=str(when),tick_size=str(tick))) for t in tokens]
    return prior.ticks_at(sorted(seed+events,key=lambda e:e['rcv']),tokens,checkpoints)


def load(start):
    root,row = select(start)
    if not row['replay_eligible']:
        return row,None
    path = N/'channels/A/events.jsonl.gz' if start==1790031600 else root/'raw/events.jsonl.gz'
    with gzip.open(path,'rt') as f:
        events = [json.loads(line) for line in f]
    initial = a.read(root/'raw/market_start.json')
    market = initial['data']
    tokens = json.loads(market['clobTokenIds'])
    events,origin = prior.book_events(events,tokens)
    checks = [(start+n)*1000 for n in range(30,841)]
    client,issues = a.m1.books_at(events,tokens,checks)
    assert not issues.get('future_source_clock') and not issues.get('out_of_order_book')
    ct = ticks_with_initial(events,tokens,checks,initial)
    # Offline venue reconstruction only. Policies never receive this stream.
    published = sorted([dict(e,rcv=int(e['p']['timestamp'])) for e in events
                        if e['k'] in ('book','price_change','tick_size_change')],key=lambda e:e['rcv'])
    venue,vt = {},{}
    for delay in (250,750):
        times = [t+delay for t in checks]
        venue[delay],_ = a.m1.books_at(published,tokens,times)
        vt[delay] = ticks_with_initial(published,tokens,times,initial)
    groups = {p.stem:a.m1.matches(a.read(p)['data']) for p in (root/'raw/receipts').glob('*.json')}
    flows,errors,_ = a.m1.trade_flows(events,groups,tokens)
    assert not errors
    makers = {(tx,m['log_index']):m for tx,gg in groups.items() for g in gg for m in g['makers']}
    prints = []
    for f in flows:
        m = makers[f['tx'],f['log_index']]
        gross = m['cash_cost']-m['fee'] if m['side']==0 else -m['cash_cost']+m['fee']
        cash = gross if m['side']==0 else m['qty']-gross
        assert f['obs_lo']==f['obs_hi'] and f['received']>=f['obs_lo']
        prints.append(dict(side=f['side'],qty=D(m['qty'])/ex.UNIT,gross=D(cash)/ex.UNIT,
            obs=f['obs_lo'],rcv=f['received'],tx=f['tx'],log=f['log_index']))
    rp = HERE/'raw/market_result_1790031600.json' if start==1790031600 else root/'raw/market_result.json'
    result = a.read(rp)['data']
    for m in (market,result):
        meta = a.accounting.ref.classify(m)
        assert (meta['group'],meta['S'],meta['end'],meta['mechanism'])==('btc_15m',start,start+900,'chainlink_twap60')
        assert json.loads(m['clobTokenIds'])==tokens
        assert m['feesEnabled'] and D(str(m['feeSchedule']['rate']))==D('.07') and m['feeSchedule']['exponent']==1
    row.update(winner=a.accounting.ref.base.outcome(result),book_origin_ms=origin,prints=len(prints),
               initial_metadata_received_ms=initial.get('received_ms'),
               initial_metadata_tick=market.get('orderPriceMinTickSize'),
               resolution_received_ms=a.read(rp).get('fetched_ms'),arms={},control={})
    return row,dict(client=client,venue=venue,ct=ct,vt=vt,prints=prints,market=market,result=result)


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
        if not ex.arrival_valid(b,when):
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


def run_one(data,profile,mode,tie,arm,trace=False):
    name,offset,hedge,funded = arm
    return ex.run(data['client'],data['venue'][profile['accept']],data['prints'],data['market'],mode,offset,
        hedge,profile['accept'],profile['learn'],data['ct'],data['vt'][profile['accept']],funded,
        cancel_delay=profile['cancel'],trade_shift=profile['shift'],tie_order=tie,trace=trace,separate_arrival=True)


def run_all():
    protect()
    for name,digest in a.read(HERE/'raw/manifest.json').items():
        assert a.sha(HERE/name)==digest
    clpaths = [HERE/'raw/chainlink.jsonl.gz']
    for stage in (E,Z):
        manifest = a.read(stage/'raw/chainlink_manifest.json')
        for name,info in manifest.items():
            assert a.sha(stage/name)==info['sha256']
            clpaths.append(stage/name)
    streams,refs = ex.engine.old.chainlink_streams(clpaths)
    rows = []
    for start in PROTOCOL['starts']:
        row,data = load(start)
        if data is None:
            rows.append(row)
            continue
        # Neither final winner nor later reference validation can change a decision.
        row['reference_matches_afterward'] = any(e.get('eventMetadata',{}).get('priceToBeat') is not None
            and start in refs and abs(float(e['eventMetadata']['priceToBeat'])-refs[start][1])<1e-6
            for e in data['result'].get('events',[]))
        for delay in (250,750):
            p0 = candidate(data['client'],data['venue'][delay],data['market'],streams,refs,delay)
            p0['conditional_pnl'] = D(str(p0['state']['q'][row['winner']]))-D(str(p0['state']['cash'])) if row['winner'] in (0,1) and not p0['gaps'] else None
            row['control'][str(delay)] = p0
        for profile in PROTOCOL['profiles']:
            for mode in PROTOCOL['queues']:
                for tie in PROTOCOL['ties']:
                    for arm in ARMS:
                        v = run_one(data,profile,mode,tie,arm)
                        v['conditional_pnl'] = v['actual']['q'][row['winner']]-v['actual']['cash'] if row['winner'] in (0,1) and not v['unknown'] else None
                        v['economic_pnl'] = None
                        key = ':'.join((arm[0],profile['name'],mode,tie))
                        row['arms'][key] = v
        a.save(HERE/'results/markets'/f'{start}.json',row)
        # Keep a compact table in RAM; complete per-path audit stays in market file.
        rows.append({**row,'arms':{k:{kk:v[kk] for kk in ('conditional_pnl','unknown','max_cash','max_net','min_worst','lifecycle','max_funding')} for k,v in row['arms'].items()}})
        print('Replayed',start,len(row['arms']),flush=True)
    a.save(HERE/'results/cohort.json',dict(markets=rows,status='CONDITIONAL_TIMING_SENSITIVITY',economic_pnl=None))
    summary(rows)
    protect()


def summary(rows):
    good = [r for r in rows if r['replay_eligible']]
    tables = {}
    for key in sorted({k for r in good for k in r['arms']}):
        values = [r['arms'][key]['conditional_pnl'] for r in good]
        complete = all(v is not None for v in values)
        vv = [D(v) for v in values if v is not None]
        tables[key] = dict(per_market=values,complete=len(vv),conditional_total=sum(vv,D(0)) if complete else None,
            without_best=sum(vv,D(0))-max(vv) if complete else None,all_assigned_total=None)
    pairs = {}
    for name in ('M2_bid','M2_reserved'):
        for profile in PROTOCOL['profiles']:
            for mode in PROTOCOL['queues']:
                for tie in PROTOCOL['ties']:
                    suffix=':'.join((profile['name'],mode,tie))
                    one,two = tables['M1_bid:'+suffix],tables[name+':'+suffix]
                    pairs[name+':'+suffix] = (D(two['conditional_total'])-D(one['conditional_total'])) if one['conditional_total'] is not None and two['conditional_total'] is not None else None
    a.save(HERE/'results/summary.json',dict(assigned=len(rows),eligible_starts=[r['start'] for r in good],
        excluded_starts=[r['start'] for r in rows if not r['replay_eligible']],scenarios=tables,hedge_minus_passive=pairs,
        economic_pnl=None,warning='Observed scenario extrema are not mathematical PnL bounds. One already-seen UTC day.'))


def repeat():
    hashes=[]
    with patch.object(a.public,'get',side_effect=AssertionError('offline HTTP')),patch.object(a.m1.probe,'rpc',side_effect=AssertionError('offline RPC')):
        for _ in range(2):
            run_all()
            hashes.append({str(p.relative_to(HERE)):a.sha(p) for p in (HERE/'results').rglob('*.json') if p.name not in ('reproducibility.json','checks.json')})
    assert hashes[0]==hashes[1]
    a.save(HERE/'results/reproducibility.json',dict(identical=True,sha256=hashes[0]))


def diagnose():
    """Explain conservative nulls; do not turn a failed execution gate into profit."""
    protect()
    output=[]
    rows=a.read(HERE/'results/cohort.json')['markets']
    for row in rows:
        keys=[k for k,v in row.get('arms',{}).items() if v['unknown']]
        if not keys:
            continue
        _,data=load(row['start'])
        # Equal tie variants have the same missing-book cause; inspect one per profile/arm/queue.
        for key in keys:
            arm_name,profile_name,mode,tie=key.split(':')
            if tie!='lifecycle_first':
                continue
            profile=next(p for p in PROTOCOL['profiles'] if p['name']==profile_name)
            arm=next(x for x in ARMS if x[0]==arm_name)
            failed=[]
            original=ex.engine.quote
            def quote(book,now):
                value=original(book,now)
                if value is None and now%1000:
                    bids,asks,stamp=book
                    failed.append(dict(now=now,age_ms=now-stamp,bid=bids[0][0] if bids else None,
                                       ask=asks[0][0] if asks else None))
                return value
            with patch.object(ex.engine,'quote',side_effect=quote):
                value=run_one(data,profile,mode,tie,arm)
            output.append(dict(start=row['start'],key=key,unknown=value['unknown'],failed_acceptance_checks=failed))
    a.save(HERE/'null_diagnostic.json',output)
    protect()


def report():
    from datetime import datetime,timezone
    rows=a.read(HERE/'results/cohort.json')['markets']
    sums=a.read(HERE/'results/summary.json')
    good=[r for r in rows if r['replay_eligible']]
    def cash(x):
        return 'BELİRSİZ' if x is None else f'{D(str(x)):+.4f}'
    def hour(s):
        return datetime.fromtimestamp(s,timezone.utc).strftime('%H:%M')
    labels=dict(M1_bid='Pasif bid',M1_bid_minus_cent='Pasif bid−1¢',M2_bid='Bid + dengeleme',M2_reserved='Bid + rezervli dengeleme')
    lines=['# BTC15: gelecek bilgisi, saat sırası ve aynı kurallar',
        '', '**Üç çalışma tamamlandı. Güçlü, kopyalanabilir kâr kanıtı çıkmadı.** '
        'Aşağıdaki dolarlar koşullu yerel simülasyondur; kalibre ekonomik PnL bütün kollarda null. '
        'Sekiz atama aynı görülen UTC gününden; altısı sonradan muhasebesi doğrulanabilen veriyle değerlendirildi. '
        'Bu kör ileri test veya bağımsız günler örneklemi değildir.',
        '', '## 1. Karar anı ile sonradan doğrulanan bilgi ayrıldı',
        '', 'Defter, fiyat adımı ve Chainlink yalnız alınma saati karar anını geçmiyorsa kullanılabiliyor. '
        'Sonradan tamamlanan API, receipt ve resmî kazanan yalnız ortam/muhasebe doğrulamasında. '
        'P0 adaptöründe resmî açılış referansıyla sonradan uyuşma artık geçmiş karar girdisini kapatmıyor; '
        'karar kaydedilmiş referansı kullanıyor, sonradan uyuşma ayrıca raporlanıyor. '
        'Bu kohortta referanslar zaten uyuşuyor; bu ayrımın kâr artışı olduğu iddia edilmiyor.',
        '', '23:00 sözleşmesinin ilk iki taker API listesinde bir gerçek satış eksikti. Sonraki listede '
        'yalnız bu satır eklendi; bağımsız blok taraması ve iki WS ile miktar doğrulandı. '
        'Eski MISSING_DATA sonucu korundu; bu çalışma ayrı RECONCILED_LATER etiketi kullanır. '
        'Geç doğrulama, o anda kullanılabilen işlem sinyali yapılmadı.',
        '', 'Yeni ham WS ilk tick değerini vermediği için ilk deneme belirsizdi. '
        'Başlangıçtan önce 22:56:09.006 UTC alınmış Gamma yanıtındaki 1¢ adımı kullanıldı; '
        'gelecekteki tick değişimleri geçmişe taşınmadı. Yeni resmî sonuç ayrı önbelleğe alındı; eski yanıtlar aynı.',
        '', '| UTC başlangıç | Donmuş veri kapısı | Bu çalışmadaki kapsam |', '|---|---|---|']
    for r in rows:
        lines.append(f"| {hour(r['start'])} | {r['frozen_data_gate']} | {r['offline_status']} |")
    lines+=['', '21:00 bağlantı kopması, 22:15 kimlikli eksik WS işlemi nedeniyle tüm atamaların toplamı null. '
        'Eksik piyasa sıfır işlem/kâr sayılmadı; yalnız altı hesaplanabilir pencerenin koşullu toplamları aşağıda.',
        '', '## 2. Kabul, dolum, iptal ve öğrenme sırası sınandı',
        '', 'Altı profil sonuç hesabından önce sabitlendi. Kuyruk önü/arkası ve aynı milisaniyede '
        'işlem önce/yaşam döngüsü önce olmak üzere kol başına 24 senaryo. '
        '500 ms kaydırma ölçülmüş hata sınırı değil, önceki saat çelişkisinden hareketle sabit stres. '
        'Bütün gerçekçi gecikme/sıra yollarını kapsamaz; aşağıdaki en düşük/en yüksek sonuçlar matematiksel sınır değildir.',
        '', '| Profil | Kabul ms | İptal ms | Ek öğrenme ms | İşlem saati kaydırma ms |', '|---|---:|---:|---:|---:|']
    for p in PROTOCOL['profiles']:
        lines.append(f"| {p['name']} | {p['accept']} | {p['cancel']} | {p['learn']} | {p['shift']} |")
    lines+=['', 'L2 yayım saati kabul ortamının vekili; LTP yayım saati işlem saatinin vekili. '
        'İşlem 500 ms erkene taşındığında kamu mesajının alınması erkene çekilmedi. '
        'Kabul/iptal durum cevabının dönüş süresi kabul gecikmesiyle aynı varsayıldı. '
        'Özel dolum bildirimi ölçülmüş değil; kamu alım saati + senaryo gecikmesiyle temsil edildi. '
        'Kamu kitap/işlem ve hesap order/trade bildirimleri ayrı akışlardır. '
        '[Kamu akışı](https://docs.polymarket.com/market-data/realtime-data), '
        '[hesap olayları](https://docs.polymarket.com/trading/realtime-order-updates).',
        '', '**Somut karşı örnek:** 20:45, M1 bid/kuyruk arkası: eski hızlı saatle +0,10 $, '
        'işlemi 500 ms erken sayınca −4,80 $. Her ikisinde altı dolum var; '
        'ilkinde 15 Up/15 Down ve 14,90 $ maliyet, ikincide 10 Up/20 Down ve 14,80 $ maliyet. '
        'Up kazanıyor. Fark işlem adedinden değil, açık yön riskinden geliyor.',
        '', '## 3. Aynı kuralların sonucu',
        '', 'P0 karar kaynağı/55¢ limiti aynı. M1 bid, M1 bid−1 sent, M2 bid ve önceki rezervli M2 aynı. '
        'Her piyasa/kol bağımsız: 5 pay klip, 10 net, 15 $ nakit, −5 $ en kötü sonuç. '
        't30..839 her saniye karar; t840 iptal. İadeler sıfır, taker ücreti nakitte; '
        'piyasa etkisi ve bilinmeyen iptal kuyruk kredisi yok. Bunlar ortak portföyün 15 $ bütçesi değildir.',
        '', '| Kol | Tam senaryo / 24 | Pozitif toplam | Koşullu toplam aralığı $ | En iyi pencere hariç aralık $ |', '|---|---:|---:|---:|---:|']
    for arm in labels:
        v=[x for k,x in sums['scenarios'].items() if k.startswith(arm+':') and x['conditional_total'] is not None]
        totals=[D(x['conditional_total']) for x in v]
        exbest=[D(x['without_best']) for x in v]
        lines.append(f"| {labels[arm]} | {len(v)} | {sum(x>0 for x in totals)} | {cash(min(totals))}…{cash(max(totals))} | {cash(min(exbest))}…{cash(max(exbest))} |")
    lines+=['', 'Dengelemenin iki pozitif hücresi aynı kuyruk-önü/geç-öğrenme profilinin iki sıra varyantıdır: '
        '+1,7063 $. En iyi tek pencere çıkarılınca −3,3166 $ kalır. İki bağımsız başarı değildir.',
        '', 'Ana karşılaştırma: eski hızlı profil, kuyruk arkası, aynı-ms yaşam döngüsü önce.',
        '', '| UTC | Pasif bid | Bid−1¢ | Dengeleme | Rezervli dengeleme | P0 |', '|---|---:|---:|---:|---:|---:|']
    for r in good:
        vv=[r['arms'][arm+':legacy_fast:queue_back:lifecycle_first']['conditional_pnl'] for arm in labels]
        lines.append('| '+hour(r['start'])+' | '+' | '.join(cash(v) for v in vv)+f" | {cash(r['control']['250']['conditional_pnl'])} |")
    vv=[sums['scenarios'][arm+':legacy_fast:queue_back:lifecycle_first']['conditional_total'] for arm in labels]
    p0=[r['control']['250']['conditional_pnl'] for r in good]
    lines.append('| Altı pencere | '+' | '.join(cash(v) for v in vv)+' | '+cash(sum(D(v) for v in p0) if all(v is not None for v in p0) else None)+' |')
    lines+=['', 'P0 yalnız bir pencerede işlem yaptı; altı uygun pencerede 250/750 ms sonuçları aynı. '
        'Bu küçük pozitif P0 toplamı da kopyalanabilir strateji kanıtı değil.',
        '', '## Simülatörde düzeltilen somut kusur',
        '', 'İlk koşunun 14 yolu “kabul defteri bilinmiyor” oldu. Kayıtlar defterin taze '
        '(0–26 ms) olduğunu, spread’in yalnızca 4–5¢’ye açıldığını gösterdi. Kararın 3¢ spread '
        'filtresi yanlışlıkla kabul anına da uygulanıyordu. Yeni kabul kontrolü gerçek defter '
        'tazeliği/geçerliliği, post-only, tick ve gönderilmiş fiyat sınırını kullanır. '
        '**Yeni emir kararı hâlâ 3¢ spread filtresine tabidir.** Aynı ayrım P0 uygulama adaptöründe yapıldı. '
        'Eski aday ve eski sonuçlar değiştirilmedi; bu turun eski davranışı legacy_arrival_source/ '
        've legacy_arrival_results/ içinde korunuyor. null_diagnostic.json kusurun somut fiyat/saat kanıtıdır.',
        '', '## Karar',
        '', 'Basit “bid’e katıl ve gerektiğinde karşı tarafı al” mekanizmasının sağlam kazanç kanıtı yok. '
        'Sonuç saat/kuyruk varsayımına bağlı; birkaç pozitif hücre bir üstünlük testi değildir. '
        'Bosona’nın maker ağırlığı bu mekanizmayı araştırmayı gerekçelendiriyor; onun fiyatlama, '
        'iptal, boy veya piyasa seçme kuralını bildiğimiz anlamına gelmiyor.',
        '', 'Bu sonuçlarla aynı basit kolları kârlı aday diye uzun shadow’a taşımayı önermiyorum. '
        'Sonraki teknik ihtiyaç aynı saat alanında kabul/iptal/kendi dolum kanıtıyla yürütmeyi '
        'doğrulamak. Bu görevde yeni hesap bağlantısı, emir, LIVE, shadow veya kaydedici başlatılmadı. '
        'Gerçek saat kanıtı gelene kadar koşullu senaryo ve kalibre ekonomik PnL ayrımı korunmalı.',
        '', '## Tekrar üretim ve sınırlar',
        '', '```bash', 'P=/home/taygun/Masaüstü/KararAtlas/base1/bin/python3', f'N={HERE}',
        'OPENBLAS_NUM_THREADS=1 "$P" -B "$N/run.py" repeat', '"$P" -B "$N/check.py"',
        '"$P" -B "$N/run.py" report', '"$P" -m ruff check --no-cache "$N/run.py" "$N/execution.py" "$N/check.py"', '```',
        '', 'repeat HTTP/RPC çağrılarını engelleyerek iki tam koşu yapar. Eski aday/protokol, '
        'ham kayıt, kaynak ve önceki teslim manifestleri hash ile denetlenir. '
        'results/markets/ her yolun nakit/envanter/dolum/öğrenme saatlerini ve karar özet hash’ini içerir. '
        'results/checks.json negatif kontrolleri; results/reproducibility.json aynı-hashli çıktıları gösterir. '
        'Ham Chainlink açık gzip dosyasının sabit byte önekinden alındı; gereken son kararların '
        'sonrasına kadar kayıt var, kesilmiş kuyruk tamamlanmış arşiv sayılmadı.',
        '', 'Bir gün/altı uygun pencere ekonomik kabul için yetersizdir. Senaryolar aynı piyasaların '
        'tekrarlarıdır; bağımsız 576 gözlem değildir. Eski 10 gün/100 piyasa kabul ölçütü açık.']
    if (HERE/'results/checks.json').exists() and (HERE/'results/reproducibility.json').exists():
        checks=a.read(HERE/'results/checks.json')
        repro=a.read(HERE/'results/reproducibility.json')
        lines+=['', f"Doğrulama: {len(checks['checks'])} kontrol geçti; {len(repro['sha256'])} hesap çıktısı "
            'ağsız iki koşuda aynı hash ile üretildi. 576 yolun tamamında risk limitleri korundu. '
            'Kabul kontrolü düzeltmesi yalnız 14 eski belirsiz yolu değiştirdi; diğer 562 yol ve '
            'P0 kontrolleri birebir aynı. 72 gerçek karar bağlamında bütün gelecek fiyat/ref '
            'kayıtları silinince bağlam değişmedi; varsayılan motorun 16 gerçek piyasa yolu eski motorla eşdeğer.']
    (HERE/'RAPOR.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    {'prepare':prepare,'run':run_all,'repeat':repeat,'diagnose':diagnose,'report':report}[sys.argv[1]]()
