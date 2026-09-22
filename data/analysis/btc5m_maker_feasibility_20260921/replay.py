"""Finite L2/receipt execution probes. Queue scenarios, never guaranteed paper fills."""
from collections import Counter, defaultdict
from decimal import Decimal
from hashlib import sha256
from itertools import groupby
from pathlib import Path
import gzip
import importlib.util
import json
import statistics

OUT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('probe',OUT.parent/'btc5m_order_identity_20260921/check.py')
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)
UNIT = 1000000


def read(path):
    return json.loads(path.read_text())


def units(value):
    result = Decimal(str(value))*UNIT
    assert result.is_finite() and result==result.to_integral_value()
    return int(result)


def matches(receipt):
    """Keep every exchange match; use the R1 transfer checks for every participant."""
    owners = {probe.address(event['topics'][2]) for event in receipt['logs']
              if event['address'].lower()==probe.EXCHANGE and event['topics'][0]==probe.FILLED}
    fills = [fill for owner in sorted(owners) for fill in probe.decode(receipt,owner)]
    by_log = {fill['log_index']:fill for fill in fills}
    assert len(by_log)==len(fills)
    result, pending = [], []
    for event in receipt['logs']:
        if event['address'].lower()!=probe.EXCHANGE:
            continue
        ident = int(event['logIndex'],16)
        if event['topics'][0]==probe.FILLED:
            pending.append(by_log[ident])
        elif event['topics'][0]==probe.MATCHED:
            active, = [f for f in pending if f['role']=='taker']
            gross = active['cash_cost']-active['fee'] if active['side']==0 else -active['cash_cost']+active['fee']
            result.append(dict(tx=receipt['transactionHash'],match_log=ident,active=active,
                               gross=gross,makers=[f for f in pending if f['role']=='maker']))
            assert sum(f['qty'] for f in result[-1]['makers'])==active['qty']
            pending=[]
    assert not pending and result
    return result


def trade_flows(events, groups, tokens):
    """Attach only uniquely described active matches; retain ambiguous clocks as ranges."""
    messages = defaultdict(list)
    errors, flows, metrics = [], [], Counter()
    for event in events:
        if event['k']!='last_trade_price':
            continue
        payload = event['p']
        metrics['ws_messages']+=1
        qty, px = units(payload['size']), Decimal(payload['price'])
        metrics['ws_quantity_units']+=qty
        tx = payload.get('transaction_hash')
        if tx not in groups:
            errors.append('unreconciled_trade_receipt')
            continue
        side = {'BUY':0,'SELL':1}[payload['side']]
        # WS prices are rounded; .6 has dropped its trailing zero. Never use this
        # rounded aggregate as the maker-level execution price or volume split.
        resolution=min(Decimal('.01'),Decimal(10)**px.as_tuple().exponent)
        candidates=[g for g in groups[tx] if g['active']['token']==payload['asset_id']
                    and g['active']['side']==side and g['active']['qty']==qty
                    and abs(Decimal(g['gross'])-px*qty)<=qty*resolution/2+2]
        if len(candidates)!=1:
            errors.append('ambiguous_or_unmatched_active_trade')
            continue
        group = candidates[0]
        messages[(tx,group['match_log'])].append(event)
        metrics['mapped_messages']+=1
        metrics['mapped_message_units']+=qty
    for (tx,log), observations in messages.items():
        group = next(g for g in groups[tx] if g['match_log']==log)
        metrics['matches']+=1
        metrics['ws_price_not_vwap']+=abs(Decimal(group['gross'])-Decimal(observations[0]['p']['price'])*group['active']['qty'])>2
        metrics['matched_taker_units']+=group['active']['qty']
        metrics['repeat_messages']+=len(observations)-1
        obs = [int(e['p']['timestamp']) for e in observations]
        received = [e['rcv'] for e in observations]
        for maker in group['makers']:
            assert maker['token'] in tokens
            side = tokens.index(maker['token'])
            price = (maker['cash_cost']-maker['fee'])/maker['qty'] if maker['side']==0 else (-maker['cash_cost']+maker['fee'])/maker['qty']
            if maker['side']==1:
                side, price = 1-side, 1-price
            flows.append(dict(tx=tx,log_index=maker['log_index'],side=side,price=price,
                qty=maker['qty']/UNIT,obs_lo=min(obs),obs_hi=max(obs),received=min(received),
                max_delay=max(e['rcv']-int(e['p']['timestamp']) for e in observations),
                min_delay=min(e['rcv']-int(e['p']['timestamp']) for e in observations),
                route='direct_buy' if maker['side']==0 else 'complementary_sell'))
    return flows, sorted(set(errors)), dict(metrics)


def books_at(events, tokens, checkpoints):
    books = {t:dict(BUY={},SELL={},obs=-1,rcv=-1,ready=False) for t in tokens}
    result, issues, i = {}, Counter(), 0
    for when in sorted(checkpoints):
        while i<len(events) and events[i]['rcv']<=when:
            event = events[i]
            i+=1
            payload, kind = event['p'], event['k']
            if kind not in ('book','price_change','tick_size_change'):
                continue
            obs = int(payload['timestamp'])
            if obs>event['rcv']:
                issues['future_source_clock']+=1
                continue
            if kind=='tick_size_change':
                issues['tick_size_change']+=1
                continue
            changes = [payload] if kind=='book' else payload.get('price_changes',[])
            for change in changes:
                token = change['asset_id']
                assert token in books
                book = books[token]
                if obs<book['obs']:
                    issues['out_of_order_book']+=1
                    continue
                if kind=='book':
                    for side,key in [('BUY','bids'),('SELL','asks')]:
                        book[side]={units(x['price']):units(x['size']) for x in payload[key] if units(x['size'])>0}
                    book['ready']=True
                elif book['ready']:
                    px, qty = units(change['price']), units(change['size'])
                    assert 0<px<UNIT and qty>=0 and change['side'] in ('BUY','SELL')
                    if qty:
                        book[change['side']][px]=qty
                    else:
                        book[change['side']].pop(px,None)
                book.update(obs=obs,rcv=event['rcv'])
        result[when]=[{**books[t],'BUY':dict(books[t]['BUY']),'SELL':dict(books[t]['SELL'])} for t in tokens]
    return result,dict(issues)


def queue_fill(ahead, quantity, flow):
    assert ahead>=0 and quantity>=0 and flow>=0
    consumed=min(ahead,flow)
    return ahead-consumed,min(quantity,flow-consumed)


def evaluate(start, age, events, market, groups, config):
    decision=(start+age)*1000
    activation=decision+config['activation_ms']
    cancel=decision+config['cancel_effective_ms']
    tokens=json.loads(market['clobTokenIds'])
    relevant=[e for e in events if decision<=e['rcv']<=cancel+config['max_event_delay_ms']]
    all_times=[decision,activation,cancel]
    # Actual pre-decision book and arrival book; future records only evaluate execution.
    snapshots, issues=books_at(events,tokens,all_times)
    trade_events=[e for e in events if e['k']=='last_trade_price'
                  and activation+config['clock_guard_ms']<=int(e['p']['timestamp'])<=cancel-config['clock_guard_ms']]
    flows, errors, metrics=trade_flows(trade_events,groups,tokens)
    common=dict(S=start,age=age,metrics=metrics,book_issues=issues)
    interval=[decision]+[e['rcv'] for e in relevant if e['rcv']<=cancel]+[cancel]
    if max(b-a for a,b in zip(interval,interval[1:]))>config['max_stream_gap_ms']:
        errors.append('stream_gap')
    if issues.get('future_source_clock') or issues.get('out_of_order_book') or issues.get('tick_size_change'):
        errors.append('book_clock_or_tick_uncertain')
    if any(f['min_delay']<0 or f['max_delay']>config['max_event_delay_ms'] for f in flows):
        errors.append('late_trade_clock')
    decision_books, arrival_books=snapshots[decision],snapshots[activation]
    for moment in (decision,activation,cancel):
        for book in snapshots[moment]:
            if not book['ready'] or not 0<=moment-book['rcv']<=config['max_book_age_ms'] or not 0<=moment-book['obs']<=config['max_book_age_ms']:
                errors.append('missing_or_stale_book')
    if any(b['BUY'] and b['SELL'] and max(b['BUY'])>=min(b['SELL']) for b in decision_books+arrival_books):
        errors.append('crossed_book')
    if errors:
        return [dict(common,status='missing',reasons=sorted(set(errors)))],flows
    def mirrored(bid,ask):
        return (not bid and not ask) or (bool(bid) and bool(ask) and max(bid)+min(ask)==UNIT)
    mirror_ok=all(mirrored(bb[0]['BUY'],bb[1]['SELL']) and mirrored(bb[1]['BUY'],bb[0]['SELL'])
                  for bb in (decision_books,arrival_books))
    if not mirror_ok:
        return [dict(common,status='missing',reasons=['complement_book_mismatch'])],flows
    tick=units(config['price_step'])
    winner_prices=list(map(float,json.loads(market['outcomePrices'])))
    winner=winner_prices.index(1.) if market['closed'] and sorted(winner_prices)==[0.,1.] else None
    results=[]
    for side in (0,1):
        for ticks in (config['primary_ticks_behind'],config['control_ticks_behind']):
            if not decision_books[side]['BUY']:
                results.append(dict(common,side=side,ticks_behind=ticks,status='no_quote_no_bid',price=None,
                    back_shares=0,front_shares=0,back_pnl=0,front_pnl=0))
                continue
            px=(max(decision_books[side]['BUY'])//tick-ticks)*tick
            row=dict(common,side=side,ticks_behind=ticks,price=px/UNIT,status='valid')
            if px<=0 or px%tick or (arrival_books[side]['SELL'] and px>=min(arrival_books[side]['SELL'])):
                results.append(dict(row,status='post_only_rejected_or_invalid_price',
                    back_shares=0,front_shares=0,back_pnl=0,front_pnl=0))
                continue
            ahead=max(b[side]['BUY'].get(px,0) for b in (decision_books,arrival_books))/UNIT
            mirror_depth_equal=all(b[side]['BUY'].get(px,0)==b[1-side]['SELL'].get(UNIT-px,0)
                                   for b in (decision_books,arrival_books))
            if not mirror_depth_equal:
                results.append(dict(row,status='missing',reasons=['queue_depth_mirror_mismatch']))
                continue
            eligible=[f for f in flows if f['side']==side and f['price']<=px/UNIT+1e-6
                      and f['obs_lo']>=activation+config['clock_guard_ms']
                      and f['obs_hi']<=cancel-config['clock_guard_ms']]
            volume=sum(f['qty'] for f in eligible)
            _,back=queue_fill(ahead,config['shares'],volume)
            _,front=queue_fill(0,config['shares'],volume)
            row.update(ahead=ahead,eligible_flow=volume,back_shares=back,front_shares=front,
                back_pnl=back*((side==winner)-px/UNIT) if winner is not None else None,
                front_pnl=front*((side==winner)-px/UNIT) if winner is not None else None,
                flow_ids=[[f['tx'],f['log_index']] for f in eligible],winner=winner)
            results.append(row)
    return results,flows


def main():
    for name,digest in read(OUT/'manifest.json')['files'].items():
        assert sha256((OUT/name).read_bytes()).hexdigest()==digest
    fetch=read(OUT/'fetch_manifest.json')
    for name,digest in fetch['files'].items():
        assert sha256((OUT/name).read_bytes()).hexdigest()==digest
    revision=read(OUT/'revision_manifest.json')
    assert sha256((OUT/'manifest.json').read_bytes()).hexdigest()==revision['base_manifest_sha256']
    assert sha256((OUT/'protocol_v2.json').read_bytes()).hexdigest()==revision['protocol_v2_sha256']
    config,markets=read(OUT/'protocol_v2.json'),read(OUT/'markets.json')
    groups,failures={},[]
    for tx in read(OUT/'transactions.json'):
        try:
            groups[tx]=matches(read(OUT/'receipts'/f'{tx}.json'))
        except (OSError,ValueError,KeyError,AssertionError) as error:
            failures.append(dict(tx=tx,error=type(error).__name__,reason=str(error)[:160]))
    results,all_flows,seen=[],[],set()
    with gzip.open(OUT/'events.jsonl.gz','rt') as stream:
        events=(json.loads(line) for line in stream)
        for (start,age),batch in groupby(events,key=lambda e:(e['S'],e['age'])):
            assert (start,age) not in seen
            seen.add((start,age))
            rows,flows=evaluate(start,age,list(batch),markets[str(start)],groups,config)
            results.extend(rows)
            all_flows.extend(dict(S=start,age=age,**f) for f in flows)
    for start in config['selected']:
        for age in config['ages']:
            if (start,age) not in seen:
                results.append(dict(S=start,age=age,status='missing',reasons=['missing_extracted_context']))
    summary={}
    for ticks in (config['primary_ticks_behind'],config['control_ticks_behind']):
        valid=[r for r in results if r.get('ticks_behind')==ticks and r['status']=='valid']
        summary[str(ticks)]=dict(valid_quote_probes=len(valid),
            back_shares=sum(r['back_shares'] for r in valid),front_shares=sum(r['front_shares'] for r in valid),
            back_filled_quotes=sum(r['back_shares']>0 for r in valid),front_filled_quotes=sum(r['front_shares']>0 for r in valid),
            back_diagnostic_pnl=sum(r['back_pnl'] for r in valid if r['back_pnl'] is not None),
            front_diagnostic_pnl=sum(r['front_pnl'] for r in valid if r['front_pnl'] is not None),
            median_ahead=statistics.median(r['ahead'] for r in valid) if valid else None)
    reason_counts=Counter(reason for r in results for reason in r.get('reasons',[]))
    by_context={(r['S'],r['age']):r for r in results}
    metrics=Counter()
    for row in by_context.values():
        metrics.update(row.get('metrics',{}))
    days={}
    for day in sorted({r['S']//86400 for r in results}):
        rows=[r for r in results if r['S']//86400==day]
        contexts={(r['S'],r['age']) for r in rows if 'ticks_behind' in r and r['status']!='missing'}
        days[str(day)]=dict(valid_contexts=len(contexts),status_counts=dict(Counter(r['status'] for r in rows)),
            prices={str(k):{model:dict(shares=sum(r.get(model+'_shares',0) for r in rows if r.get('ticks_behind')==k),
              diagnostic_pnl=sum(r.get(model+'_pnl',0) for r in rows if r.get('ticks_behind')==k))
              for model in ('front','back')} for k in (1,0)})
    valid_contexts=len({(r['S'],r['age']) for r in results if 'ticks_behind' in r and r['status']!='missing'})
    reconciliation=dict(messages=metrics['mapped_messages']/metrics['ws_messages'],
                        quantity=metrics['mapped_message_units']/metrics['ws_quantity_units'])
    gate=valid_contexts>=.95*len(config['selected'])*len(config['ages']) and min(reconciliation.values())>=.95
    output=dict(mode=config['mode'],assigned_contexts=len(config['selected'])*len(config['ages']),
        valid_contexts=valid_contexts,context_coverage=valid_contexts/(len(config['selected'])*len(config['ages'])),
        metrics=dict(metrics),days=days,reconciliation=reconciliation,gate='PASS' if gate else 'FAIL_DATA_GATE',
        summary=summary,missing_reasons=dict(reason_counts),receipt_failures=failures,results=results,flows=all_flows,
        limits='Queue scenarios conditional on observed L2 and matched trades; missing prints, cancel priority, hidden state and market impact not proven. No independent policy PnL or clean OOS claim.',
        source_sha256={str(p):sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),Path(SPEC.origin))})
    (OUT/'report.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ('results','flows','receipt_failures')},indent=2))
    print('Receipt failures:',len(failures))


if __name__=='__main__':
    main()
