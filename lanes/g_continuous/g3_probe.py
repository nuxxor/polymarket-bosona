"""Observed G2 quote lifetimes, not hypothetical G3 fills or profit. No network."""
from collections import defaultdict
from decimal import Decimal
from hashlib import sha256
import gzip
import json
from pathlib import Path
from statistics import median
import sys

HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(HERE/'transport_fix/bot'))
import g_policy  # noqa: E402


def fresh(book,stamp):
    # Bot timestamps are rounded milliseconds: exclude the boundary millisecond.
    return (book is not None and book['received']['utc_ns']<=stamp-1000000
            and 0<=stamp-book['source_ns']<=3000000000
            and 0<=stamp-book['received']['utc_ns']<=3000000000)


def stats(values):
    return dict(n=len(values),minimum=min(values),median=median(values),maximum=max(values)) if values else dict(n=0)


def main():
    stamp=10000000000
    sample={'source_ns':stamp-2000000,'received':{'utc_ns':stamp-1500000}}
    assert fresh(sample,stamp) and not fresh(None,stamp)
    assert not fresh({**sample,'source_ns':stamp+1},stamp)
    assert not fresh({**sample,'received':{'utc_ns':stamp}},stamp)
    assert not fresh(sample,stamp+3000000001)
    capture=HERE/'validation/G3_capture.jsonl.gz'
    with gzip.open(capture,'rt') as f:rows=[json.loads(line) for line in f]
    head,tail=rows[0],rows[-1]
    assert head['kind']=='capture_start' and tail['kind']=='capture_end' and tail['source_unchanged']
    protocol=json.loads((HERE/'G3_PROTOCOL.json').read_text())
    assert head['source_sha256']==protocol['base_sha256'] and g_policy.SHA==protocol['policy_sha256']
    assert (head['start_S'],head['end_S_exclusive'])==(protocol['london_capture']['start_S'],protocol['london_capture']['end_S_exclusive'])
    assert all(r['boot_id']==head['boot_id'] for r in tail['recordings'])
    log=[r['row'] for r in rows if r['kind']=='bot']
    sdk=[r['row'] for r in rows if r['kind']=='sdk']
    accepted={r['oid']:r for r in log if r['k']=='taze_koy'}
    assert len(accepted)==tail['accepted_parents']
    tokens={(r['S'],r['oi']):r['asset'] for r in head['tokens']}
    placements,known,cancels,terminal=(defaultdict(list) for _ in range(4))
    private_trades={};acks={};cancel_rtt=[];offsets=[];books={}
    for row in rows:
        if row['kind']=='book_sample':
            key=(row['lane'],row['decision_ns'],row['asset'])
            if row['received']['utc_ns']>books.get(key,{}).get('received',{}).get('utc_ns',0):books[key]=row
            offsets.append(row['received']['utc_ns']-row['received']['mono_ns'])
        if row['kind']!='private':continue
        e=row['row'];p=e['payload'];when=e['received']['utc_ns']
        offsets.append(when-e['received']['mono_ns'])
        if p['event_type']=='order' and p['id'] in accepted:
            oid=p['id']
            if p['type']=='PLACEMENT':placements[oid].append(when)
            if Decimal(p.get('size_matched','0'))>0:known[oid].append(when)
            if p.get('status') in ('MATCHED','CANCELED'):terminal[oid].append(when)
        if p['event_type']=='trade' and p['status']=='MATCHED':
            for m in p['maker_orders']:
                oid=m['order_id']
                if oid not in accepted:continue
                known[oid].append(when)
                key=(p['id'],oid);value=(Decimal(m['matched_amount']),Decimal(m['price']))
                assert key not in private_trades or private_trades[key]==value, 'A/B trade disagreement'
                private_trades[key]=value
    for e in sdk:
        offsets.append(e['utc_ns']-e['mono_ns'])
        if e['event']=='request' and e.get('op')=='cancel':
            for oid in e['meta']['oids']:cancels[oid].append(e['utc_ns'])
        if e['event']=='fill_observed':known[e['oid']].append(e['utc_ns'])
        if e['event']!='response':continue
        reply=e['reply']
        if e['op']=='post_batch':
            for item in reply.get('items',[]):
                if item.get('success') and item['oid'] in accepted:acks[item['oid']]=e['end']['utc_ns']
        if e['op']=='cancel':
            cancel_rtt.append(e['duration_ns']/1e6)
            for item in reply.get('items',[]):
                if item.get('canceled'):terminal[item['oid']].append(e['end']['utc_ns'])
        if e['op']=='get_order':
            if float(reply.get('matched') or 0)>0:known[reply['oid']].append(e['utc_ns'])
            if reply.get('status') in ('MATCHED','CANCELED'):terminal[reply['oid']].append(e['utc_ns'])
    lifetime={};missing=[]
    for oid,order in accepted.items():
        stops=cancels[oid]+known[oid]+terminal[oid]
        if not placements[oid] or oid not in acks or not stops:
            missing.append(oid);continue
        lifetime[oid]=(max(acks[oid],min(placements[oid]),order['utc_ms']*1000000),min(stops))
    final={r['S']:r for r in log if r['k']=='COZULDU'}
    assert set(final)==set(range(head['start_S'],head['end_S_exclusive'],300))
    bot_qty={r['oid']:Decimal(str(r.get('pay',0))) for w in final.values() for r in w['emirler'] if r['oid'] in accepted}
    actual_qty=defaultdict(Decimal);actual_cash=defaultdict(Decimal)
    for (_,oid),(q,p) in private_trades.items():actual_qty[oid]+=q;actual_cash[oid]+=q*p
    quantity_mismatch=[oid for oid in accepted if oid not in bot_qty or abs(bot_qty[oid]-actual_qty[oid])>Decimal('.000001')]
    cash_difference=sum(actual_cash[oid]-actual_qty[oid]*Decimal(str(accepted[oid]['p'])) for oid in accepted)
    for oid in accepted:
        # Reported price ratios can include sub-micro-dollar cash rounding per fill.
        tolerance=Decimal('.000001')*sum(key[1]==oid for key in private_trades)
        assert abs(actual_cash[oid]-actual_qty[oid]*Decimal(str(accepted[oid]['p'])))<=tolerance, 'unexpected maker execution price'
    seen=set();open_seen=set();signals=[];ambiguous=0
    for i,e in enumerate(log[:-1]):
        if e['k']!='G_KARAR':continue
        q=log[i+1]
        if q['k']!='G_KALITE' or (q['S'],q['oi'])!=(e['S'],e['oi']):continue
        stamp=q['utc_ms']*1000000
        eligible=[oid for oid,(a,b) in lifetime.items() if a+1000000<stamp<b-1000000
                  and (accepted[oid]['S'],accepted[oid]['oi'])==(e['S'],e['oi'])]
        if len(eligible)>1:ambiguous+=1
        if len(eligible)!=1:continue
        oid=eligible[0];order=accepted[oid]
        if q['p']!=order['p']:continue
        seen.add(oid)
        if not q['uygun'] or q['neden']!='open' or not e['mutabakat']:continue
        s=q['kaynak']
        assert s['model_sha']==g_policy.SHA
        if not 0<=q['utc_ms']-s['book_ms']<=3000:continue
        open_seen.add(oid);amounts=[e['up'],e['down']]
        target=g_policy.target(e['bb'],e['ba'],s['tick'],amounts[e['oi']],amounts[1-e['oi']])
        if target is None or not (e['bb']-.02-1e-9<=order['p']<=e['bb']+1e-9 and order['p']>target+1e-9):continue
        asset=tokens[(e['S'],e['oi'])];context={}
        for lane in ('A','B'):
            b=books.get((lane,stamp,asset))
            context[lane]={'fresh':fresh(b,stamp),'sample':b}
        signals.append(dict(oid=oid,S=e['S'],oi=e['oi'],flag_ms=q['utc_ms'],price=order['p'],bid=e['bb'],ask=e['ba'],
                            target=target,up=e['up'],down=e['down'],books=context,
                            until_known_match_ms=(min(known[oid])-stamp)/1e6 if known[oid] else None))
    first={}
    for signal in signals:first.setdefault(signal['oid'],signal)
    joined=[s for s in first.values() if all(b['fresh'] for b in s['books'].values())]
    one_joined=[s for s in first.values() if any(b['fresh'] for b in s['books'].values())]
    matched=[s for s in first.values() if actual_qty[s['oid']]>0]
    joined_fraction=len(joined)/len(first) if first else None
    # Unknown/pending reservations and every-loop timing are absent from the 1Hz log.
    result=dict(status='OBSERVATIONAL_ONLY_NOT_A_LIVE_GATE_PASS',windows=len(final),accepted_parents=len(accepted),
                lifecycle_joined_parents=len(lifetime),lifecycle_missing=missing,
                private_unique_trade_parent_pairs=len(private_trades),filled_parents=sum(q>0 for q in actual_qty.values()),
                private_shares=str(sum(actual_qty.values())),ws_fill_cash=str(sum(actual_cash.values())),
                ws_vs_limit_cash_difference=str(cash_difference),
                quantity_mismatch=quantity_mismatch,quantity_reconciled_parents=len(accepted)-len(quantity_mismatch),
                prefill_quote_parents=len(seen),fresh_open_prefill_parents=len(open_seen),ambiguous_samples=ambiguous,
                candidate_samples=len(signals),flagged_parents=len(first),flagged_later_filled=len(matched),
                flagged_later_unfilled=len(first)-len(matched),both_recorder_fresh_first_flags=len(joined),
                any_recorder_fresh_first_flags=len(one_joined),
                both_recorder_join_fraction=joined_fraction,required_join_fraction=protocol['technical_gate']['required_join_fraction'],
                until_known_match_ms=stats([s['until_known_match_ms'] for s in matched if s['until_known_match_ms'] is not None]),
                cancel_rtt_ms=stats(cancel_rtt),clock_offset_span_us=(max(offsets)-min(offsets))/1000,
                observed_g2_pnl_by_window=[{'S':s,'pnl':w['pnl']} for s,w in sorted(final.items())],
                simulated_g3_pnl=None,prevented_fills=None,first_flags=list(first.values()),
                limitations=['No G3 orders or fills: no economic comparison.',
                             'First-match receipt is not execution time; cancel RTT is not effective cancel time.',
                             '1Hz decision log misses some prefill lifetimes and lacks exact uncertainty/reservation state.',
                             'A sample inside the rounded-millisecond boundary is uncertain, not proof of missing market data.',
                             'Book A/B snapshots arrived before the logged cut; independent connections can disagree.',
                             'Final quantity reconciliation is verification only; never a prefill decision input.'],
                capture_sha256=sha256(capture.read_bytes()).hexdigest(),script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                live_actions=0)
    out=HERE/'validation/G3_probe.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('first_flags','limitations')},indent=2))


if __name__=='__main__':main()
