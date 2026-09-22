"""Read-only G/Bosona study; public full-condition snapshots, no trading SDK."""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal as D
from hashlib import sha256
import json
from pathlib import Path
import shutil
import time
import urllib.parse

import identity
import public_data as public

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, default=str, indent=2)+'\n')
    temporary.replace(path)


def event_key(row):
    return tuple(str(row.get(k, '')) for k in ('conditionId', 'transactionHash', 'timestamp',
                 'type', 'asset', 'outcomeIndex', 'side', 'size', 'price', 'usdcSize'))


def fetch_activity(wallet, market):
    rows, previous = [], set()
    for offset in range(0, 5001, 500):
        query = urllib.parse.urlencode(dict(user=wallet, market=market['conditionId'],
                limit=500, offset=offset, sortBy='TIMESTAMP', sortDirection='ASC'))
        batch = public.request('https://data-api.polymarket.com/activity?'+query)
        assert isinstance(batch, list) and len(batch)<=500
        assert all(r['proxyWallet'].lower()==wallet and r['conditionId']==market['conditionId'] for r in batch)
        keys = set(map(event_key, batch))
        assert not previous.intersection(keys), 'ambiguous overlap between API pages'
        previous.update(keys)
        rows.extend(batch)  # Never deduplicate equal-looking fills within a page.
        if len(batch)<500:
            return dict(rows=rows, pages=offset//500+1, fetched_ms=round(time.time()*1000), complete=True)
        time.sleep(.5)
    raise ValueError('activity pagination exhausted')


def side(row, tokens):
    assert row.get('asset') in tokens, 'unmapped token (including unknown redeem)'
    actual = tokens.index(row['asset'])
    assert row.get('outcomeIndex') in (actual, 999), 'token/outcome conflict'
    return actual


def ledger(rows, market, start):
    tokens = json.loads(market['clobTokenIds'])
    names = json.loads(market['outcomes'])
    assert names==['Up', 'Down'] and len(tokens)==2
    prices = list(map(D, json.loads(market['outcomePrices'])))
    winner = prices.index(D(1)) if market.get('closed') and sorted(prices)==[D(0),D(1)] else None
    q, cash = [D(0),D(0)], D(0)
    trades, steps, reduction, increase, ambiguous = [], [], D(0), D(0), D(0)
    groups = defaultdict(list)
    for row in rows:
        groups[int(row['timestamp'])].append(row)
    for timestamp, group in sorted(groups.items()):
        net_before = q[0]-q[1]
        buys = [r for r in group if r['type']=='TRADE' and r['side']=='BUY']
        sides = {side(r,tokens) for r in buys}
        all_buy = all(r['type']=='TRADE' and r['side']=='BUY' for r in group)
        if timestamp < start+300 and buys:
            amount = sum(D(str(r['size'])) for r in buys)
            if len(sides)==1 and all_buy:
                direction = 1 if next(iter(sides))==0 else -1
                reducing = min(abs(net_before),amount) if net_before*direction<0 else D(0)
                reduction += reducing
                increase += amount-reducing
            else:
                ambiguous += amount
        for row in group:
            amount, usd = D(str(row['size'])), D(str(row['usdcSize']))
            assert amount.is_finite() and usd.is_finite() and amount>=0 and usd>=0
            kind = row['type']
            if kind=='TRADE':
                oi=side(row,tokens)
                assert row['side'] in ('BUY','SELL')
                sign=1 if row['side']=='BUY' else -1
                q[oi] += amount*sign
                cash -= usd*sign
                trades.append(row)
            elif kind=='MERGE':
                q=[x-amount for x in q]; cash+=usd
            elif kind=='SPLIT':
                q=[x+amount for x in q]; cash-=usd
            elif kind=='REDEEM':
                oi=side(row,tokens);q[oi]-=amount;cash+=usd
            else:
                raise ValueError('unsupported balance-changing activity: '+kind)
        assert min(q)>=D('-.00002'), 'negative public inventory; history/multiplicity incomplete'
        if timestamp < start+300:
            steps.append(dict(age=timestamp-start, net=q[0]-q[1]))
    terminal = [cash+v for v in q]
    # Merge/redeem change cash and token balances, not the realised trade outcome.
    bought = [sum(D(str(r['size'])) for r in trades if r['side']=='BUY' and side(r,tokens)==oi) for oi in (0,1)]
    spend = sum(D(str(r['usdcSize'])) for r in trades if r['side']=='BUY')
    buys = [r for r in trades if r['side']=='BUY']
    first = min((r['timestamp'] for r in buys),default=None)
    return dict(status='resolved' if winner is not None else 'pending', winner=winner,
                pnl=terminal[winner] if winner is not None else None, terminal_payoffs=terminal,
                cash=cash, remaining=q, bought=bought, buy_cash=spend, trade_records=len(trades),
                first_fill_age=None if first is None else first-start,
                first_sides=sorted({side(r,tokens) for r in buys if r['timestamp']==first}),
                cash_vwap=[None if bought[i]==0 else sum(D(str(r['usdcSize'])) for r in buys if side(r,tokens)==i)/bought[i] for i in (0,1)],
                reducing_buy_shares=reduction, increasing_buy_shares=increase,
                ambiguous_buy_shares=ambiguous, net_path=steps,
                clock='public API seconds; same-second mixed directions are not ordered')


def roles(rows, market, wallet, limit=100):
    groups = defaultdict(list)
    for row in rows:
        if row['type']=='TRADE':groups[row['transactionHash']].append(row)
    tokens = json.loads(market['clobTokenIds'])
    fills, failures = [], []
    for tx, group in groups.items():
        try:
            path=ROOT/'receipts'/f'{tx}.json'
            if not path.exists():
                if limit<=0:raise ValueError('receipt cycle limit; pending')
                public.receipt(tx); limit-=1
            receipt=read(path)
            assert receipt['transactionHash']==tx
            decoded=[f for f in identity.decode(receipt,wallet) if f['token'] in tokens]
            for token in {r['asset'] for r in group}|{f['token'] for f in decoded}:
                for action in ('BUY','SELL'):
                    api=[r for r in group if r['asset']==token and r['side']==action]
                    actual=[f for f in decoded if f['token']==token and f['side']==(0 if action=='BUY' else 1)]
                    assert abs(sum(D(str(r['size'])) for r in api)-sum(D(f['qty'])/1000000 for f in actual))<=D('.000001')
                    cash=sum(D(str(r['usdcSize'])) for r in api)
                    chain=sum(D(f['cash_cost'])/1000000 for f in actual)*(1 if action=='BUY' else -1)
                    assert abs(cash-chain)<=D('.00001'), 'chain/API cash difference'
            fills.extend(decoded)
        except (OSError, ValueError, AssertionError, KeyError, TypeError) as error:
            failures.append(dict(tx=tx,error=type(error).__name__,reason=str(error)[:100]))
    parents=defaultdict(list)
    for fill in fills:parents[fill['order_hash']].append(fill)
    quantity=sum(D(f['qty'])/1000000 for f in fills)
    return dict(complete=not failures, failures=failures, fills=len(fills), parents=len(parents),
                split_parents=sum(len(g)>1 for g in parents.values()), decoded_shares=quantity,
                maker_shares=sum(D(f['qty'])/1000000 for f in fills if f['role']=='maker'),
                taker_shares=sum(D(f['qty'])/1000000 for f in fills if f['role']=='taker'),
                parent_shares=[sum(D(f['qty'])/1000000 for f in g) for g in parents.values()])


def health(protocol):
    bot=Path(protocol['bot'])
    result=dict(at_ms=round(time.time()*1000),source_same=sha256((bot/'ab.py').read_bytes()).hexdigest()==protocol['source_sha'])
    state=read(bot/'STATE_g.json');budget=read(bot/'BUDGET_G.json')
    result.update(pnl=state['st']['pnl'],local_pnl=state['st']['pnl_yerel'],budget_id=budget['id'],
                  cutoff=budget['cutoff'],end_ms=budget['end_ms'],recorders={})
    for lane in ('A','B'):
        p=bot/f'measurement/run1/{lane}.health.json'
        if p.exists():
            r=read(p)
            result['recorders'][lane]={k:r.get(k) for k in ('status','rejected','queue_overflow')}
            result['recorders'][lane]['age_seconds']=(time.time_ns()-r['at_ns'])/1e9
    logs=[json.loads(line) for line in (bot/'LOG_g.jsonl').read_text().splitlines()]
    start=max(i for i,e in enumerate(logs) if e['k']=='SURUM')
    session=logs[start:]
    pid=session[0]['oturum']
    result['live_pid']=int(pid) if (Path('/proc')/pid/'cmdline').exists() else None
    result['stop']=next((e for e in reversed(session) if e['k']=='bitti'),None)
    result['counts']=dict(Counter(e['k'] for e in session))
    result['active_windows']=[dict(key=k,quantities=[sum(o.get('pay',0) for o in w['emir'] if o['oi']==oi) for oi in (0,1)],
                                  unknown_orders=sum(o.get('durum')=='belirsiz' for o in w['emir']))
                               for k,w in state['pen'].items() if not w.get('cozuldu')]
    with (ROOT/'health.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
    return result


def snapshot(protocol):
    now=int(time.time());cut=ROOT/'cuts'/str(now);cut.mkdir(parents=True,exist_ok=False)
    bot=Path(protocol['bot'])
    shutil.copyfile(bot/'STATE_g.json',cut/'own_state.json')
    state=read(cut/'own_state.json')
    report=[]
    for start in protocol['historical']+protocol['forward_slots']:
        if start>now:continue
        item=dict(S=start,cohort='forward' if start in protocol['forward_slots'] else 'historical',actors={})
        try:
            market=public.request('https://gamma-api.polymarket.com/markets/slug/btc-updown-5m-'+str(start))
            assert market['slug']=='btc-updown-5m-'+str(start)
            save(cut/f'{start}_market.json',market)
        except (OSError,ValueError,AssertionError) as error:
            item.update(status='missing_market',error=type(error).__name__);report.append(item);continue
        for actor,wallet in protocol['wallets'].items():
            try:
                raw=fetch_activity(wallet,market);save(cut/f'{start}_{actor}.json',raw)
                value=ledger(raw['rows'],market,start)
                value['snapshot_ms']=raw['fetched_ms']
                value['execution']=roles(raw['rows'],market,wallet)
                if actor=='G':
                    window=state['pen'].get('btc|'+str(start))
                    value['assigned_by_bot']=window is not None
                    if window:
                        ownq=[sum(D(str(o.get('pay',0))) for o in window['emir'] if o['oi']==oi) for oi in (0,1)]
                        value['local_bought']=ownq
                        value['quantities_match_local']=all(abs(a-b)<=D('.00002') for a,b in zip(ownq,value['bought']))
                        value['local_accepted_parents']=sum(bool(o.get('oid')) for o in window['emir'])
                        value['local_filled_parents']=sum(o.get('pay',0)>0 for o in window['emir'])
                item['actors'][actor]=value
            except (OSError,ValueError,AssertionError,KeyError,TypeError) as error:
                item['actors'][actor]=dict(status='missing',error=type(error).__name__,reason=str(error)[:140])
            time.sleep(1)
        report.append(item)
        save(cut/'report.json',report)
    summary=dict(as_of_ms=round(time.time()*1000),cut=str(cut),rows=report)
    save(ROOT/'latest.json',summary)
    print(json.dumps(dict(cut=str(cut),windows=len(report),resolved={actor:sum(r['actors'].get(actor,{}).get('status')=='resolved' for r in report) for actor in protocol['wallets']})),flush=True)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch',action='store_true')
    args=parser.parse_args()
    protocol=read(ROOT/'protocol.json')
    public.OUT=ROOT
    (ROOT/'receipts').mkdir(exist_ok=True)
    for name,digest in protocol['inherited_source_sha'].items():assert sha256((ROOT/name).read_bytes()).hexdigest()==digest
    next_analysis=0
    while True:
        try:
            health(protocol)
            if time.time()>=next_analysis:
                snapshot(protocol)
                next_analysis=time.time()+protocol['analysis_period_seconds']
        except (OSError,ValueError,AssertionError,KeyError,TypeError) as error:
            with (ROOT/'errors.jsonl').open('a') as f:f.write(json.dumps(dict(at_ms=round(time.time()*1000),type=type(error).__name__,reason=str(error)[:140]))+'\n')
            if not args.watch:raise
            next_analysis=time.time()+protocol['analysis_period_seconds']
        if not args.watch or time.time()>=protocol['watch_end']:
            break
        time.sleep(protocol['health_period_seconds'])


if __name__=='__main__':
    main()
