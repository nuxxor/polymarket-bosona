#!/usr/bin/env python3
"""Link selected on-chain inventory paths to pre-fill books; no policy backtest."""
from collections import defaultdict
from decimal import Decimal as D
import bisect
import gzip
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
R=Path('/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921')
S=R/'btc15_followup/status_20260921_1800'
sys.path.insert(0,str(R))
import research as r  # noqa: E402


def main():
    chain=r.read(HERE/'onchain/results.json')
    with gzip.open(S/'raw/book_validation_prefix.json.gz','rt') as stream:
        tape=json.load(stream)['rows']
    books=defaultdict(list)
    for event in tape:
        if event['kind']=='books':
            books[event['S']].append(event)
    windows={w['slug']:w for w in r.read(S/'results/windows.json')}
    cases=[]
    for slug in sorted({x['slug'] for x in chain['rows']}):
        w=windows[slug]
        market=r.read(S/'raw/new_period_markets'/f'{slug}.json')['data']
        tokens=json.loads(market['clobTokenIds'])
        events=books[w['S']]
        times=[x['received_ms'] for x in events]

        def quote(when,side,qty=5):
            i=bisect.bisect_right(times,when)-1
            if i<0:
                return dict(missing='before_book_start')
            e=events[i]
            book=next(b for b in e['books'] if b['asset_id']==tokens[side])
            asks=sorted((float(x['price']),float(x['size'])) for x in book['asks'])
            bids=sorted((float(x['price']),float(x['size'])) for x in book['bids'])
            value=dict(requested_ms=e['requested_ms'],received_ms=e['received_ms'],observed_ms=int(book['timestamp']),
                age_ms=when-int(book['timestamp']),bid=bids[-1][0] if bids else None,ask=asks[0][0] if asks else None)
            assert e['received_ms']<=when
            if not 0<=value['age_ms']<=3000:
                return dict(value,missing='stale')
            try:
                cost,fee=r.base.ask_cost(dict(asks=asks),market,qty)
                value.update(cash_5=cost+fee,unit_5=(cost+fee)/qty)
            except ValueError:
                value['missing']='depth_or_fee'
            return value

        rr=sorted((x for x in chain['rows'] if x['slug']==slug),key=lambda x:(x['block_number'],x['transaction_index'],x['log_index']))
        steps=[]
        for x in rr:
            qty=D(x['qty'])/D(1000000)
            cash=D(x['cash_cost'])/D(1000000)
            before=[D(v)-D(x['pre_cost']) for v in x['pre_qty']]
            after=[D(v)-D(x['post_cost']) for v in x['post_qty']]
            steps.append(dict(age=x['age'],side=['Up','Down'][x['outcome']],role=x['role'],parent=x['order_hash'],
                parent_origin=x['parent_origin'],phase=x['phase'],qty=str(qty),cash=str(cash),
                pre_qty=x['pre_qty'],pre_cash=x['pre_cost'],before_payout_pnl=list(map(str,before)),
                after_payout_pnl=list(map(str,after)),worst_improvement=str(min(after)-min(before)),
                hold_to_settlement=str(before[w['winner']]),after_to_settlement=str(after[w['winner']]),
                incremental_terminal=str(after[w['winner']]-before[w['winner']]),
                book_minus5=quote((x['api_ts']-5)*1000,x['outcome']),
                note='Book precedes public chain second; actual order decision/placement time unavailable.'))
        at600=[x for x in rr if x['age']<600]
        noadd=None
        if at600 and not any(x['age']>=600 for x in rr):
            last=at600[-1]
            q=list(map(D,last['post_qty']))
            cash=D(last['post_cost'])
            side=int(q[1]>q[0])
            noadd=dict(age=600,qty=list(map(str,q)),cash=str(cash),before_payout_pnl=[str(v-cash) for v in q],
                books=[quote((w['S']+600)*1000,i) for i in (0,1)],
                observed_action='No fill in [600,900); orders and cancellations unknown',
                held_side=['Up','Down'][side],official_winner=['Up','Down'][w['winner']],terminal=str(q[w['winner']]-cash))
        cases.append(dict(slug=slug,winner=['Up','Down'][w['winner']],pnl=w['pnl'],steps=steps,no_add_control=noadd))
    (HERE/'case_paths.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n')
    assert len(cases)==4 and sum(len(x['steps']) for x in cases)==42
    assert any(x['no_add_control'] for x in cases)
    print(json.dumps([dict(slug=x['slug'],pnl=x['pnl'],steps=len(x['steps']),no_add_control=x['no_add_control']) for x in cases],ensure_ascii=False))


if __name__=='__main__':
    main()
