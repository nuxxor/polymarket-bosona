"""Read sanitized, closed execution traces; never import the trading bot."""
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median

import run as r

SOURCE = Path('/home/taygun/Masaüstü/polymarket-bosona/data/analysis/btc5m_m4_v2_20260922')


def stats(values):
    values = sorted(values)
    if not values:
        return dict(n=0)
    return dict(n=len(values),min=min(values),median=median(values),
                p95=values[math.ceil(.95*len(values))-1],max=max(values))


def analyze(rows):
    assert rows[0]['event']=='session_start' and rows[-1]['event']=='session_end'
    assert len({x['session'] for x in rows})==1
    assert [x['seq'] for x in rows]==list(range(1,len(rows)+1))
    assert all(x['errors']==0 and x['event']!='exception' for x in rows)
    requests = {x['attempt']:x for x in rows if x['event']=='request'}
    responses = [x for x in rows if x['event']=='response']
    assert Counter(x['attempt'] for x in responses)==Counter({k:1 for k in requests})
    assert len(requests)==sum(x['event']=='request' for x in rows)
    for x in responses:
        assert x['duration_ns']==x['end']['mono_ns']-x['begin']['mono_ns']>=0
        assert requests[x['attempt']]['op']==x['op']
        assert requests[x['attempt']]['mono_ns']<=x['begin']['mono_ns']<=x['end']['mono_ns']<=x['mono_ns']
    posts = [x for x in responses if x['op']=='post_batch']
    orders = {}
    rejected = 0
    for x in posts:
        assert x['reply']['slots_match']
        submitted = requests[x['attempt']]['meta']['orders']
        assert len(submitted)==len(x['reply']['items'])
        for sent,reply in zip(submitted,x['reply']['items']):
            if not reply['oid']:
                rejected += 1
                continue
            assert reply['success'] and reply['oid'] not in orders
            orders[reply['oid']] = dict(sent=sent,post=x,gets=[],cancels=[],observations=[])
    missing_gets = []
    for x in responses:
        if x['op']=='get_order':
            oid = requests[x['attempt']]['meta']['oid']
            if x['reply']['oid'] is None:
                assert all(v is None for v in x['reply'].values())
                missing_gets.append(dict(seq=x['seq'],order_id=oid))
                continue
            assert x['reply']['oid']==oid
            orders[oid]['gets'].append(x)
        elif x['op']=='cancel':
            for item in x['reply']['items']:
                assert item['oid'] in requests[x['attempt']]['meta']['oids']
                orders[item['oid']]['cancels'].append(dict(response=x,item=item))
    for x in rows:
        if x['event']=='fill_observed':
            assert x['exchange_ns'] is None
            orders[x['oid']]['observations'].append(x)
    details = []
    for oid,o in orders.items():
        gets = sorted(o['gets'],key=lambda x:x['end']['mono_ns'])
        assert gets and gets[-1]['reply']['status'] in ('CANCELED','MATCHED')
        positives = [x for x in gets if float(x['reply']['matched'] or 0)>0]
        filled = []
        for seen in o['observations']:
            proof = [x for x in positives if x['end']['mono_ns']<=seen['mono_ns']
                     and float(x['reply']['matched'])==float(seen['total'])]
            assert proof
            learned = proof[-1]
            zeros = [x for x in gets if not float(x['reply']['matched'] or 0)
                     and x['end']['mono_ns']<learned['begin']['mono_ns']]
            filled.append(dict(delta=seen['delta'],source=seen['source'],exchange_time=None,
                get_end_to_local_observation_ms=(seen['mono_ns']-learned['end']['mono_ns'])/1e6,
                last_zero_to_positive_response_ms=(learned['end']['mono_ns']-zeros[-1]['end']['mono_ns'])/1e6 if zeros else None,
                match_to_observation_ms=None))
        cancels = []
        for cc in o['cancels']:
            x = cc['response']
            ack = x['end']['mono_ns']
            live = [g for g in gets if g['reply']['status']=='LIVE' and g['end']['mono_ns']>ack]
            later = [g for g in gets if g['begin']['mono_ns']>ack and g['reply']['status'] in ('CANCELED','MATCHED')]
            cancels.append(dict(acknowledged=cc['item']['canceled'],
                sdk_ms=x['duration_ns']/1e6,
                overlapping_live_responses=sum(g['begin']['mono_ns']<=ack for g in live),
                initiated_after_ack_live_responses=sum(g['begin']['mono_ns']>ack for g in live),
                ack_to_first_later_terminal_response_ms=(later[0]['end']['mono_ns']-ack)/1e6 if later else None))
        details.append(dict(order_id=oid,quantity=o['sent']['size'],price=o['sent']['price'],
            post_sdk_ms=o['post']['duration_ns']/1e6,final_status=gets[-1]['reply']['status'],
            matched=gets[-1]['reply']['matched'],fills=filled,cancels=cancels))
    assert sum(float(x['matched']) for x in details)==sum(float(f['delta']) for x in details for f in x['fills'])
    cc = [c for x in details for c in x['cancels']]
    ff = [f for x in details for f in x['fills']]
    return dict(events=len(rows),requests=len(requests),accepted=len(orders),rejected=rejected,
        missing_gets=missing_gets,
        final_states=dict(Counter(x['final_status'] for x in details)),
        sdk_ms={op:stats([x['duration_ns']/1e6 for x in responses if x['op']==op]) for op in sorted({x['op'] for x in responses})},
        accepted_post_ms=stats([x['post_sdk_ms'] for x in details]),
        local_fill_processing_ms=stats([f['get_end_to_local_observation_ms'] for f in ff]),
        cancel_live_overlap=sum(c['overlapping_live_responses'] for c in cc),
        cancel_live_after_ack=sum(c['initiated_after_ack_live_responses'] for c in cc),
        cancel_terminal_confirmation_ms=stats([c['ack_to_first_later_terminal_response_ms'] for c in cc if c['ack_to_first_later_terminal_response_ms'] is not None]),
        unobservable=['exchange_accept_time','exchange_cancel_time','match_time','private_notification_delay'],
        orders=details)


def main():
    r.protect()
    manifest = r.HERE/'raw/telemetry_manifest.json'
    if not manifest.exists():
        info = {}
        for name,source in [('orders.jsonl',SOURCE/'final_0112/LOG_f_emir_iz.jsonl'),
                            ('emir_iz_source.py',SOURCE/'package/bot/emir_iz.py')]:
            copy = r.HERE/'raw'/name
            copy.parent.mkdir(parents=True,exist_ok=True)
            copy.write_bytes(source.read_bytes())
            info[name] = dict(source=str(source),sha256=r.a.sha(copy))
        r.a.save(manifest,info)
    for name,v in r.a.read(manifest).items():
        assert r.a.sha(r.HERE/'raw'/name)==v['sha256']
        assert r.a.sha(Path(v['source']))==v['sha256']
    data = analyze([json.loads(s) for s in (r.HERE/'raw/orders.jsonl').read_text().splitlines()])
    r.a.save(r.HERE/'results/telemetry.json',data)
    print(json.dumps({k:v for k,v in data.items() if k!='orders'},indent=2))
    r.protect()


if __name__=='__main__':
    main()
