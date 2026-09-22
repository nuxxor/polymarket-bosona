"""Offline accounting/multiplicity checks plus any downloaded real cut."""
from copy import deepcopy
from decimal import Decimal as D
import json
from pathlib import Path
from unittest.mock import patch

import study as s

market = dict(conditionId='condition',clobTokenIds='["u","d"]',outcomes='["Up","Down"]',
              outcomePrices='["1","0"]',closed=True)


def row(oi, qty, cash, timestamp=10, kind='TRADE'):
    return dict(conditionId='condition',proxyWallet='wallet',transactionHash='tx',timestamp=timestamp,
                type=kind,asset=('u','d')[oi],outcomeIndex=oi,side='BUY',size=qty,usdcSize=cash,price=0.4)


def fails(call):
    try:call()
    except (AssertionError,ValueError):return
    raise AssertionError('invalid input silently accepted')


def main():
    rows=[row(0,5,2),row(0,5,2),row(1,5,3,20)]
    with patch.object(s.public,'request',return_value=rows):
        assert len(s.fetch_activity('wallet',market)['rows'])==3
    with patch.object(s.public,'request',side_effect=[[rows[0]]*500,[rows[0]]]), patch.object(s.time,'sleep'):
        fails(lambda:s.fetch_activity('wallet',market))
    value=s.ledger(rows,market,0)
    assert value['bought']==[10,5] and value['pnl']==3 and value['reducing_buy_shares']==5
    merged=rows+[row(0,5,5,30,'MERGE')]
    assert s.ledger(merged,market,0)['pnl']==3
    redeemed=merged+[row(0,5,5,40,'REDEEM')]
    redeemed[-1]['outcomeIndex']=999
    assert s.ledger(redeemed,market,0)['pnl']==3
    assert s.ledger(redeemed,market,0)['trade_terminal_payoffs']==[3,-2]
    blank=deepcopy(redeemed);blank[-1].update(asset='',outcomeIndex=0)
    assert s.ledger(blank,market,0)['pnl']==3 and s.ledger(blank,market,0)['redeem_missing_asset']==1
    blank[-1]['outcomeIndex']=999
    fails(lambda:s.ledger(blank,market,0))
    unknown_index=row(0,5,2);unknown_index['outcomeIndex']=999
    assert s.ledger([unknown_index],market,0)['bought']==[5,0]
    bad=deepcopy(redeemed);bad[-1]['usdcSize']=10
    fails(lambda:s.ledger(bad,market,0))
    bad=deepcopy(redeemed);bad[-1]['asset']='unknown'
    fails(lambda:s.ledger(bad,market,0))
    fails(lambda:s.ledger([row(0,5,5,30,'MERGE')],market,0))
    pending={**market,'closed':False,'outcomePrices':'["0.8","0.2"]'}
    assert s.ledger(rows,pending,0)['pnl'] is None
    mixed=s.ledger([row(0,5,2),row(1,5,3)],market,0)
    assert mixed['ambiguous_buy_shares']==10 and mixed['increasing_buy_shares']==0
    zero_cross=s.ledger([row(1,5,2),row(0,8,4,20)],market,0)
    assert zero_cross['reducing_buy_shares']==5 and zero_cross['increasing_buy_shares']==8
    screenshot=s.ledger([row(0,10,6.6),row(1,15,5.7,20)],market,0)
    assert screenshot['pnl']==D('-2.3') and screenshot['trade_terminal_payoffs']==[D('-2.3'),D('2.7')]
    checked=0
    latest=Path(__file__).parent/'latest.json'
    if latest.exists():
        result=s.read(latest)
        cut=Path(__file__).parent/'cuts'/Path(result['cut']).name
        for item in result['rows']:
            for actor,record in item['actors'].items():
                if record['status']=='missing':continue
                raw=s.read(cut/f"{item['S']}_{actor}.json")
                actual=s.ledger(raw['rows'],s.read(cut/f"{item['S']}_market.json"),item['S'])
                assert json.loads(json.dumps(actual,default=str))=={k:record[k] for k in actual}
                decoded=s.roles(raw['rows'],s.read(cut/f"{item['S']}_market.json"),
                                s.read(Path(__file__).parent/'protocol.json')['wallets'][actor],limit=0)
                assert json.loads(json.dumps(decoded,default=str))==record['execution']
                checked+=1
        incident=Path(__file__).parent/'operational_evidence.json'
        if incident.exists():
            errors=[r for r in s.read(incident)['events'] if r['k']=='mutabakat_GECERSIZ']
            tokens=json.loads(s.read(cut/'1790074800_market.json')['clobTokenIds'])
            assert len(errors)==6 and all(s.side(dict(r['islem'],type='TRADE'),tokens)==0 for r in errors)
    print(json.dumps(dict(synthetic='PASS',real_actor_windows_reproduced=checked)))


if __name__=='__main__':main()
