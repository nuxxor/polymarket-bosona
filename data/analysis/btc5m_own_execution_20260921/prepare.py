"""Freeze own accepted orders, including nonfills; never infer precise cancellation times."""
from hashlib import sha256
from pathlib import Path
import gzip
import json
import sqlite3

OUT = Path(__file__).resolve().parent
DB = Path('/home/taygun/Masaüstü/polymarket/data/db/polymarket_orderbook.db')


def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n')


def orders_from(snapshot):
    final = snapshot['F']['windows']  # Contains the inherited D/E windows exactly once.
    state = {r['oid']: (int(key.split('|')[1]), w, r)
             for key, w in final.items() for r in w['emir'] if r.get('oid')}
    events = sorted((e for lane in snapshot.values() for e in lane['events']), key=lambda e:e['utc_ms'])
    accepted = [e for e in events if e['k']=='taze_koy']
    assert len(accepted)==len({e['oid'] for e in accepted})==len(state)
    result = []
    for e in accepted:
        start, window, r = state[e['oid']]
        assert (start,window['kol'],r['oi'],r['p'],r['boy'])==(e['S'],e['kol'],e['oi'],e['p'],e['boy'])
        intents = [x for x in events if x['k']==e['kol']+'_NIYET' and x.get('S')==start
                   and x['oi']==r['oi'] and x['p']==r['p'] and r['snap_ms']<=x['utc_ms']<=r['ack_ms']]
        intent, = intents
        assert r['snap_ms']<=intent['utc_ms']<=r['ack_ms']<=e['utc_ms']
        assert 0<=r['pay']<=r['boy']+1e-6
        tokens, = [x['tokens'] for x in events if x['k']=='pencere' and x.get('S')==start and x.get('kol')==e['kol']]
        # The next same-side intent requires the old order to be non-active;
        # terminal fill discovery and settlement are also only upper bounds.
        bounds = [dict(ms=x['utc_ms'],kind=x['k']) for x in events if x['utc_ms']>r['ack_ms'] and (
            (x.get('S')==start and x['k'].endswith('_NIYET') and x['oi']==r['oi']) or
            (x.get('S')==start and x['k']=='COZULDU') or
            (x['k']=='BELIRSIZ_COZULDU' and e['oid'].startswith(x['oid']) and x['borsa'] in ('MATCHED','CANCELED')) or
            (x['k']=='dolum' and x.get('oid')==e['oid'] and x['toplam']>=r['boy']-1e-6))]
        bound = min(bounds,key=lambda x:x['ms']) if bounds else None
        result.append(dict(oid=e['oid'],lane=e['kol'],S=start,token=tokens[r['oi']],tokens=tokens,oi=r['oi'],
            price=r['p'],quantity=r['boy'],actual_filled=r['pay'],state_status=r['durum'],
            exchange_status=r.get('borsa_durum'),snapshot_ms=r['snap_ms'],intent_ms=intent['utc_ms'],
            ack_ms=r['ack_ms'],accepted_log_ms=e['utc_ms'],terminal_upper=bound,
            cancel_request_ms=None,cancel_response_ms=None,first_fill_observed_ms=r.get('dolum_ms'),
            observed_fills=r.get('dolumlar',[]),close_reason=r.get('kapanis')))
    return sorted(result,key=lambda r:(r['ack_ms'],r['oid']))


def main():
    if (OUT/'protocol.json').exists():
        print('Frozen preparation already exists.')
        return
    snapshot = json.load(gzip.open(OUT/'snapshot.json.gz','rt'))
    orders = orders_from(snapshot)
    write('orders.json',orders)
    # Small outcome-independent sample for book/flow diagnostics, not optimization.
    selected = sorted(r['oid'] for lane in 'DEF' for r in sorted(
        [r for r in orders if r['lane']==lane],key=lambda r:sha256(('M2:'+r['oid']).encode()).hexdigest())[:12])
    write('protocol.json',dict(mode='FINITE_READ_ONLY_CALIBRATION_AUDIT',selection='12 accepted order hashes per lane, seed M2; no fill/outcome selection',
        selected=selected,all_accepted=len(orders),clock_guard_ms=100,max_book_age_ms=3000,
        missing_cancel='No confusion matrix or exact-lifetime prediction without cancellation evidence',
        diagnostics='Own onchain fills and WS timestamps; pre-submission book only; bounded lifecycle, not an independent strategy',
        fees_rebates_pnl='Not an economic strategy test; no PnL tuning'))
    con = sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True)
    con.execute('BEGIN')
    max_id = con.execute('select max(id) from market_events').fetchone()[0]
    markets, extraction = {}, []
    for start in sorted({r['S'] for r in orders}):
        rows=con.execute('select asset_id,condition_id,side from subscribed_assets where start_ts=? and end_ts=?',(start,start+300)).fetchall()
        if len(rows)!=2:
            continue
        own = next(r for r in orders if r['S']==start)
        assert all(token==own['tokens'][['Up','Down'].index(side)] for token,_,side in rows)
        cid, = {x[1] for x in rows}
        markets[str(start)]=dict(conditionId=cid,tokens=own['tokens'])
    write('markets.json',markets)
    # Full-window LTP only is compact and lets own public fills be located without
    # treating block inclusion time as the exchange execution time.
    with gzip.open(OUT/'trades.jsonl.gz','wt') as output:
        for start,market in markets.items():
            rows=con.execute("select id,ts_ms,raw_json from market_events where condition_id=? and ts_ms between ? and ? and event_type='last_trade_price' and id<=? order by ts_ms,id",
                (market['conditionId'],(int(start)-60)*1000,(int(start)+360)*1000,max_id))
            for ident,received,raw in rows:
                output.write(json.dumps(dict(S=int(start),id=ident,rcv=received,k='last_trade_price',p=json.loads(raw)))+'\n')
    with gzip.open(OUT/'books.jsonl.gz','wt') as output:
        for order in orders:
            if order['oid'] not in selected:
                continue
            market=markets.get(str(order['S']))
            if market is None:
                extraction.append(dict(oid=order['oid'],status='missing_market'))
                continue
            when=order['intent_ms']-100  # Avoid adding our accepted order to its own queue.
            full=[con.execute("select id,ts_ms from market_events where asset_id=? and event_type='book' and ts_ms<=? and id<=? order by ts_ms desc,id desc limit 1",
                              (t,when,max_id)).fetchone() for t in order['tokens']]
            if not all(full):
                extraction.append(dict(oid=order['oid'],status='missing_snapshot'))
                continue
            rows=con.execute('select id,ts_ms,event_type,raw_json from market_events where condition_id=? and ts_ms between ? and ? and id<=? order by ts_ms,id',
                (market['conditionId'],min(f[1] for f in full),when,max_id)).fetchall()
            for ident,received,kind,raw in rows:
                if kind in ('book','price_change','tick_size_change'):
                    output.write(json.dumps(dict(oid=order['oid'],id=ident,rcv=received,k=kind,p=json.loads(raw)))+'\n')
            extraction.append(dict(oid=order['oid'],status='extracted',book_at_ms=when,initial_ids=[f[0] for f in full]))
    con.close()
    write('extraction.json',dict(db=str(DB),db_max_id=max_id,markets=len(markets),probes=extraction))
    public=json.loads((OUT.parents[2]/'data/referans/muhasebe_20260920_kaynak.json').read_text())
    wallet, = {r['proxyWallet'].lower() for r in public['islemler']}
    write('public_wallet.json',dict(address=wallet,source='data/referans/muhasebe_20260920_kaynak.json; public trades, not credentials'))
    write('input_manifest.json',{name:sha256((OUT/name).read_bytes()).hexdigest() for name in (
        'snapshot.json.gz','manifest.json','orders.json','protocol.json','markets.json','trades.jsonl.gz','books.jsonl.gz','extraction.json','public_wallet.json',
        'd_lifecycle.py.txt','e_lifecycle.py.txt','f_lifecycle.py.txt')})
    print(json.dumps(dict(orders=len(orders),markets=len(markets),sample=len(selected))))


if __name__=='__main__':
    main()
