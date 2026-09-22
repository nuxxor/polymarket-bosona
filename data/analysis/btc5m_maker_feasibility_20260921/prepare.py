"""Freeze calendar-selected local L2 excerpts. No actor signal or order submission."""
from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import gzip
import json
import sqlite3
import sys

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT/'analiz/izleme'))
import bosona_derin as deep  # noqa: E402

DB = deep.base.BOOK_DB
START, END = 1789831200, 1790015400  # First complete DB calendar slot; fixed 21 Sep 18:30 UTC cut.


def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2)+'\n')


def main():
    resume = '--complete-context' in sys.argv
    if (OUT/'manifest.json').exists() and not resume:
        print('Frozen inputs already exist; not changing the cohort.')
        return
    con = sqlite3.connect(DB.as_uri()+'?mode=ro', uri=True)
    days = defaultdict(list)
    for start in range(START,END,300):
        days[start//86400].append(start)
    selected = sorted(s for slots in days.values() for s in sorted(slots,
        key=lambda s:sha256(f'M1-20260921:{s}'.encode()).hexdigest())[:32])
    policy = dict(mode='FINITE_OFFLINE_EXECUTION_PROBES_NO_ORDERS', start=START,end=END,
        calendar_slots=(END-START)//300,selected=selected,seed='M1-20260921',selection='32 calendar slots per UTC day by SHA256; missing DB slots retained',
        ages=[30,120,210,280],shares=5,primary_ticks_behind=1,control_ticks_behind=0,
        activation_ms=250,cancel_request_ms=1000,cancel_effective_ms=1250,clock_guard_ms=100,
        max_book_age_ms=3000,max_event_delay_ms=1000,max_stream_gap_ms=1000,
        rebates=0,gate='>=95% eligible context and >=95% trade quantity/count reconciliation, separately; historical not clean OOS',
        scope='Independent probes, not a reinvesting portfolio. No actor actions in quote placement.',
        collector_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    if resume:
        policy=json.loads((OUT/'protocol.json').read_text())
        previous=json.loads((OUT/'extraction.json').read_text())
    else:
        previous=dict(probes=[])
        write('protocol.json',policy)  # Before reading trade outcomes or replay results.
    available = deep.markets()
    markets, missing = {}, []
    # Source snapshot metadata: reads only; no checkpoint, vacuum or DB mutations.
    con.execute('BEGIN')
    max_id = previous.get('db_max_id') or con.execute('select max(id) from market_events').fetchone()[0]
    subscribed = con.execute('select * from subscribed_assets where start_ts>=? and end_ts<=?',(START,END)).fetchall()
    for start in selected:
        slots = [r for r in subscribed if r[4]==start and r[5]==start+300]
        if len(slots)!=2 or {r[3] for r in slots}!={'Up','Down'}:
            missing.append(start)
            continue
        market = available.get(start)
        if market is None:
            market = deep.base.get(f'https://gamma-api.polymarket.com/markets/slug/btc-updown-5m-{start}')
        tokens = json.loads(market['clobTokenIds'])
        assert market['slug']==f'btc-updown-5m-{start}'
        assert all(r[1]==market['conditionId'] and r[0]==tokens[['Up','Down'].index(r[3])] for r in slots)
        markets[str(start)] = market
    write('markets.json',markets)
    transactions=set()
    probes={(row['S'],row['age']):row for row in previous['probes']}
    def keep_transaction(row):
        decision=(row['S']+row['age'])*1000
        payload=row['p']
        if row['k']=='last_trade_price' and payload.get('transaction_hash') and decision+350<=int(payload['timestamp'])<=decision+1150:
            transactions.add(payload['transaction_hash'])
    with gzip.open(OUT/'events.next.gz','wt') as stream:
        if resume:
            with gzip.open(OUT/'events.jsonl.gz','rt') as old:
                for line in old:
                    keep_transaction(json.loads(line))
                    stream.write(line)
        for start in selected:
            market = markets.get(str(start))
            if market is None:
                continue
            cid = market['conditionId']
            tokens = json.loads(market['clobTokenIds'])
            for age in policy['ages']:
                if probes.get((start,age),{}).get('status')=='extracted':
                    continue
                decision = (start+age)*1000
                full = [con.execute("select id,ts_ms from market_events where asset_id=? and event_type='book' and ts_ms<=? and id<=? order by ts_ms desc,id desc limit 1",
                                    (token,decision,max_id)).fetchone() for token in tokens]
                if not all(full):
                    probes[(start,age)]=dict(S=start,age=age,status='missing_initial_snapshot')
                    continue
                begin = min(r[1] for r in full)
                rows = con.execute('select id,ts_ms,event_type,raw_json from market_events where condition_id=? and ts_ms between ? and ? and id<=? order by ts_ms,id',
                    (cid,begin,decision+2250,max_id)).fetchall()
                for ident,received,kind,raw in rows:
                    payload = json.loads(raw)
                    assert payload.get('market',cid)==cid
                    row=dict(S=start,age=age,id=ident,rcv=received,k=kind,p=payload)
                    keep_transaction(row)
                    stream.write(json.dumps(row,separators=(',',':'))+'\n')
                probes[(start,age)]=dict(S=start,age=age,status='extracted',events=len(rows),initial_snapshot_ids=[r[0] for r in full])
            print('extracted',start,flush=True)
    con.close()
    (OUT/'events.next.gz').replace(OUT/'events.jsonl.gz')
    write('transactions.json', sorted(transactions))
    write('extraction.json',dict(probes=list(probes.values()),missing_markets=missing,db_max_id=max_id,
        source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        db_path=str(DB),db_bytes=DB.stat().st_size,subscribed_markets=len({r[4] for r in subscribed})))
    names=['protocol.json','markets.json','events.jsonl.gz','transactions.json','extraction.json']
    write('manifest.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),
        files={name:sha256((OUT/name).read_bytes()).hexdigest() for name in names}))
    print(json.dumps(dict(selected=len(selected),markets=len(markets),transactions=len(transactions),probes=len(probes))))


if __name__=='__main__':
    main()
