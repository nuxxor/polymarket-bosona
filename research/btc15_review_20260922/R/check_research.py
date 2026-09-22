#!/usr/bin/env python3
"""Small offline accounting/policy regression and real-artifact checks."""
from collections import Counter
from decimal import Decimal
import hashlib
import importlib.metadata
import sys

import candidate
import research as r
import study


def check():
    r.base.check()
    study.check()
    candidate.check()
    row = dict(transactionHash='t',timestamp=r.START,type='TRADE',asset='a',outcomeIndex=0,
               side='BUY',size=150,price=.44,usdcSize=66,slug='a')
    parts = [dict(complete=True,rows=[row,row]),dict(complete=True,rows=[row,row])]
    combined, detail = r.merge_slices(parts)
    assert len(combined)==2 and detail[0]['count']==2
    assert len(r.merge_slices([dict(complete=True,rows=[row])]*2)[0])==1
    for p in (r.RAW/'markets').glob('eth-updown-5m-1789257600.json'):
        m = r.read(p)
        assert r.classify(m)['group']=='eth_5m'
        wrong = dict(m,endDate='2026-09-13T01:00:00Z')
        # Official duration takes precedence over the slug label.
        assert r.classify(wrong)['duration']==3600
        bad = dict(m,resolutionSource='https://example.com/not-an-oracle')
        try:
            r.classify(bad)
            raise AssertionError('unverified source accepted')
        except ValueError:
            pass
    kk = r.load_bars()['eth']
    now = r.START+180
    before = r.features(kk,r.START,now)
    times,values = list(kk[0]),[list(a) for a in kk[1]]
    for i,t in enumerate(times):
        if t+2000>now*1000:
            values[i][4] = '999999'
    assert r.features((times,values),r.START,now)==before
    windows,fills = r.read(r.OUT/'windows.json'),r.read(r.OUT/'fills.json')
    assert all(w['group']!='btc_5m' for w in windows)
    assert len({w['slug'] for w in windows})==len(windows)
    assert not r.read(r.OUT/'payout_violations.json')
    for w in windows:
        assert abs(w['qty'][w['winner']]-w['cost']-w['cash_cost_pnl'])<1e-5
        assert abs(w['pair_cash_pnl']+w['residual_cash_pnl']-w['cash_cost_pnl'])<1e-5
    for f in fills:
        assert abs(f['qty']-f['completion_qty']-f['opening_qty'])<1e-6
        for lag in (5,10):
            c = f[f'context_{lag}']
            if c:
                assert c['bar_close_ms']+2000<=(f['ts']-lag)*1000
    sums = r.read(r.OUT/'summary.json')
    assert abs(sum(w['cash_cost_pnl'] for w in windows)-sum(g['pnl'] for g in sums['groups'].values()))<1e-5
    exact = sum(Decimal(x['decimal_pnl']) for x in r.read(r.OUT/'accounting_checks.json'))
    assert abs(float(exact)-sum(w['cash_cost_pnl'] for w in windows))<1e-5
    uv = [w for w in r.read(r.OUT/'universe.json') if w['group'] in r.PRIMARY]
    expected = Counter(dict(btc_15m=816,btc_1h=204,eth_5m=2448,eth_15m=816,eth_1h=204,
                            sol_5m=2448,sol_15m=816,sol_1h=204))
    assert Counter(w['group'] for w in uv)==expected
    validation = r.read(r.OUT/'api_validation.json')
    assert validation['outcome_count']==len(r.read(r.OUT/'universe.json'))
    interval = r.read(r.OUT/'fresh_interval_check.json')
    assert not interval['added'] and not interval['removed'] and interval['btc15_trades']==0
    raw_sources = r.read(r.HERE/'source_manifest.json')
    assert all(hashlib.sha256(r.Path(x['copy']).read_bytes()).hexdigest()==x['sha256'] for x in raw_sources.values())
    scenarios = r.read(r.OUT/'candidate_scenario_rows.json')
    assert all(x['peak_risk']<=5+1e-8 and x['cash']<=15+1e-8 for x in scenarios)
    assert all(abs(x['q'][0]-x['q'][1])<=10+1e-8 for x in scenarios)
    assert all(x['S']+180<=e['time']<x['S']+900 for x in scenarios for e in x['events'])
    summary = dict(windows=len(windows),fills=len(fills),universe=len(r.read(r.OUT/'universe.json')),
          primary_universe=dict(expected),decimal_cash_pnl=str(exact),api_trade_checks=len(validation['trades']),
          scenario_rows=len(scenarios),zero_payout_violations=True,tests='passed',
          python=sys.version.split()[0],packages={n:importlib.metadata.version(n) for n in ('numpy','scipy','scikit-learn','ruff')})
    r.save(r.OUT/'checks.json',summary)
    print(r.json.dumps(summary,indent=2))


if __name__=='__main__':
    check()
