"""Diagnose static-ahead misses on real fills; intentionally actor-conditioned end time."""
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import gzip
import json

from analyze import m1

OUT=Path(__file__).resolve().parent
DATA=OUT/'flow_probe'


def read(path):
    return json.loads(path.read_text())


def eligible(flow, price):
    # A micro-cash rounding residual is not a different quoted price.
    return (Decimal(str(flow['price']))-Decimal(str(price)))*Decimal(str(flow['qty']))<=Decimal('.000002')


def main():
    protocol=read(DATA/'protocol.json')
    assert sha256((DATA/'source_report.json').read_bytes()).hexdigest()==protocol['source_report_sha256']
    orders={r['oid']:r for r in read(OUT/'orders.json')}
    books={r['oid']:r for r in read(OUT/'report.json')['pre_submission_books']}
    quality={r['oid']:r for r in read(DATA/'quality.json')}
    manifest=read(DATA/'fetch_manifest.json')
    for name,digest in manifest['files'].items():
        assert sha256((DATA/name).read_bytes()).hexdigest()==digest
    groups={p.stem:m1.matches(read(p)) for p in (DATA/'receipts').glob('*.json')}
    events=[json.loads(line) for line in gzip.open(DATA/'events.jsonl.gz','rt')]
    results=[]
    for probe in protocol['probes']:
        order=orders[probe['oid']]
        context=books[order['oid']]
        selected=[e for e in events if e['S']==probe['S'] and probe['lo']<=int(e['p']['timestamp'])<=probe['hi']]
        flows,errors,metrics=m1.trade_flows(selected,groups,order['tokens'])
        if context['status']!='valid':
            errors.append('missing_initial_book')
        if quality[order['oid']]['max_receipt_gap_ms']>1000:
            errors.append('stream_gap')
        late=sum(f['min_delay']<0 or f['max_delay']>1000 for f in flows)
        accepted=[f for f in flows if f['side']==order['oi'] and eligible(f,order['price'])]
        volume=sum(m1.units(f['qty']) for f in accepted)
        _,predicted=m1.queue_fill(m1.units(context['ahead']),m1.units(order['quantity']),volume)
        # Broader source-clock interval, smaller pre-send queue and all mapped
        # late reports deliberately favor the static model. A miss is diagnostic;
        # reproducing a fill is not prospective validation.
        results.append(dict(oid=order['oid'],lane=order['lane'],S=order['S'],price=order['price'],
            actual=order['actual_filled'],ahead=context['ahead'],eligible_flow=volume/m1.UNIT,
            predicted=None if errors else predicted/m1.UNIT,errors=sorted(set(errors)),
            late_flow_reports=late,metrics=metrics,clock_interval_ms=probe['hi']-probe['lo'],
            backing=[dict(tx=f['tx'],log_index=f['log_index'],qty=f['qty'],price=f['price']) for f in accepted]))
    valid=[r for r in results if r['predicted'] is not None]
    result=dict(scope=protocol['scope'],assigned=len(results),reconciled=len(valid),
        actual=sum(r['actual'] for r in valid),static_predicted=sum(r['predicted'] for r in valid),
        missed_entirely=sum(r['predicted']==0 and r['actual']>0 for r in valid),
        underpredicted=sum(r['predicted']<r['actual']-1e-6 for r in valid),
        overpredicted=sum(r['predicted']>r['actual']+1e-6 for r in valid),rows=results,
        source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        inputs={n:sha256((DATA/n).read_bytes()).hexdigest() for n in ('protocol.json','events.jsonl.gz','quality.json','source_report.json','transactions.json','fetch_manifest.json')})
    (DATA/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','inputs')},indent=2))


if __name__=='__main__':
    main()
