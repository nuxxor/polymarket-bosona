#!/usr/bin/env python3
"""Small regression and actual artifact checks; network and orders never used."""
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import research as r  # noqa: E402
import candidate as c  # noqa: E402
import analyze  # noqa: E402
import audit  # noqa: E402
import hypotheses  # noqa: E402
import record_books  # noqa: E402


def check():
    for filename,sha in r.read(HERE/'baseline_hashes.json').items():
        assert hashlib.sha256(Path(filename).read_bytes()).hexdigest()==sha,filename
    trade=dict(slug='btc-updown-5m-1789539000',timestamp=1789539139,transactionHash='same',type='TRADE',
        asset='public-token',outcomeIndex=0,side='BUY',size=148,price=.32,usdcSize=47.36)
    rows,_=r.merge_slices([dict(complete=True,rows=[trade,trade]),dict(complete=True,rows=[trade,trade])])
    assert len(rows)==2  # Two equal fills, two overlapping downloads: 2, neither 1 nor 4.
    assert audit.exact(rows,0)['pnl']==201.28
    assert audit.exact([trade],0)['pnl']==100.64
    assert analyze.bucket(.29,120,99)==(2,1,1)
    assert analyze.comparable(dict(price=.3,age=650,risk=50),dict(price=.32,age=675,risk=70))
    assert not analyze.comparable(dict(price=.3,age=650,risk=50),dict(price=.32,age=675,risk=76))
    s=c.state()
    assert c.apply(s,dict(side=0,qty=5.,kind='first'),.4,.07,180)
    row=dict(events=s['events'])
    assert not analyze.policy_state(row,179)['entered']
    assert analyze.policy_state(row,600)['entered']
    for name in ('H1_continuous_value','H2_inventory_cost'):
        f=dict(final_up_prob=.6,momentum10=.1)
        a=hypotheses.score(name,650,[.4,.6],f,s)
        assert 0<a<1 and hypotheses.score(name,650,[.4,.6],dict(f,winner=1),s)==a
        assert hypotheses.score(name,650,[.4,.6],f,c.state()) is None
    books=[dict(asset_id=t,market='condition',timestamp='123',asks=[dict(price='.4',size='5')],bids=[]) for t in ('a','b')]
    record_books.validate(books,['a','b'],'condition')  # Empty side retained, not fabricated.
    try:
        record_books.validate(books,['wrong','b'],'condition')
        raise AssertionError('wrong token accepted')
    except ValueError:
        pass
    a=r.read(HERE/'results/btc5_audit.json')
    assert a['published']['missing_fills']==7 and abs(a['published']['delta_pnl']+6.21)<1e-8
    own=r.read(HERE/'results/own_btc5_audit.json')
    assert own['windows']==96 and not own['multiplicity_changes'] and not own['all_differences']
    matched=r.read(HERE/'results/matched_win_loss.json')
    for x in matched['all_pairs']:
        assert analyze.comparable(x['win'],x['loss']) and x['win']['win'] and not x['loss']['win']
    misses=r.read(HERE/'results/miss_rows.json')
    for x in misses:
        assert x['actual_ceiling_pass']==(x['price']<=.55)
        if 'actual_edge_5' in x:
            assert -1.1<x['actual_edge_5']<1.1
    controls=r.read(HERE/'results/no_add_controls.json')
    for x in controls['pairs']:
        assert x['add']['add'] and x['control']['no_trade'] and analyze.comparable(x['add'],x['control'])
    grid=r.read(HERE/'results/risk_set.json')
    assert all(x['ts']==x['S']+x['age'] and 600<=x['age']<900 for x in grid)
    pre0,_=r.base.ledger([trade],0)
    pre1,_=r.base.ledger([trade],1)
    assert [(x['pre_net'],x['pre_unmatched_cash_cost']) for x in pre0]==[(x['pre_net'],x['pre_unmatched_cash_cost']) for x in pre1]
    new=r.read(HERE/'results/new_period_rows.json')
    assert len(new)==7 and sum(x['opening_kind']=='add' and x['age']>=600 for x in new)==1
    for x in new:
        for lag in (5,10):
            b=x[f'book_{lag}']
            if 'received_ms' in b:
                assert b['received_ms']<=1000*(x['ts']-lag)
    c.check()
    result=dict(passed=True,btc5_affected=7,own_audit_windows=96,late_grid=len(grid),strict_win_loss_pairs=matched['pairs'],
        strict_no_add_pairs=len(controls['pairs']),candidate_hash_unchanged=True)
    r.save(HERE/'results/checks.json',result)
    print(json.dumps(result))


if __name__=='__main__':
    check()
