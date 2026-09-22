"""Exploratory quote-buffer flags on observed order lifetimes; never a fill replay."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
from statistics import median
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FINAL = ROOT / 'lanes/g/validation/final_20260922'
PRIVATE = ROOT / 'lanes/g_continuous/validation/g1_first_pilot'
BOT = ROOT / 'lanes/g_continuous/identity_fix/bot'
sys.dont_write_bytecode = True
sys.path.insert(0, str(BOT))
import g_policy  # noqa: E402


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def distribution(values):
    return dict(n=len(values), minimum=min(values), median=median(values), maximum=max(values)) if values else dict(n=0)


def main():
    log = rows(FINAL/'original/LOG_g.jsonl')
    telemetry = rows(FINAL/'original/LOG_g_emir_iz.jsonl')
    accepted = {r['oid']: r for r in log if r['k'] == 'taze_koy'}
    assert len(accepted) == 63
    placements, fills, first_known_match, cancels, terminal = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for lane in ('A', 'B'):
        for e in rows(PRIVATE/f'{lane}_private.jsonl'):
            p = e.get('payload', {})
            when = e.get('received', {}).get('utc_ns', 0)
            if p.get('event_type') == 'order' and p.get('id') in accepted:
                oid = p['id']
                if p['type'] == 'PLACEMENT':
                    placements[oid].append(when)
                if float(p.get('size_matched', 0)) > 0:
                    first_known_match[oid].append(when)
                if p.get('status') in ('MATCHED', 'CANCELED'):
                    terminal[oid].append(when)
            if p.get('event_type') == 'trade' and p.get('status') == 'MATCHED':
                for m in p['maker_orders']:
                    if m['order_id'] in accepted:
                        fills[m['order_id']].append(when)
                        first_known_match[m['order_id']].append(when)
    post_ack, cancel_rtt = {}, []
    for e in telemetry:
        if e['event'] == 'request' and e.get('op') == 'cancel':
            for oid in e['meta']['oids']:
                cancels[oid].append(e['utc_ns'])
        if e['event'] == 'fill_observed':
            first_known_match[e['oid']].append(e['utc_ns'])
        if e['event'] != 'response':
            continue
        if e.get('op') == 'post_batch':
            for item in e.get('reply', {}).get('items', []):
                if item.get('success') and item['oid'] in accepted:
                    post_ack[item['oid']] = e['end']['utc_ns']
        if e.get('op') == 'cancel':
            cancel_rtt.append(e['duration_ns']/1e6)
        if e.get('op') == 'get_order':
            r = e['reply']
            if float(r.get('matched') or 0) > 0:
                first_known_match[r['oid']].append(e['utc_ns'])
            if r.get('status') in ('MATCHED', 'CANCELED'):
                terminal[r['oid']].append(e['utc_ns'])
    assert len(post_ack) == 63 and len(fills) == 36
    lifetimes = {}
    for oid, order in accepted.items():
        assert placements[oid], 'No independent private placement observation'
        start = max(post_ack[oid], min(placements[oid]), order['utc_ms']*1000000)
        stops = cancels[oid]+terminal[oid]+first_known_match[oid]
        assert stops, 'No observed prefill-lifetime endpoint'
        lifetimes[oid] = (start, min(stops))
    signals = []
    observed_prefill, observed_open_prefill = set(), set()
    for i, e in enumerate(log[:-1]):
        if e['k'] != 'G_KARAR':
            continue
        quality = log[i+1]
        assert quality['k'] == 'G_KALITE' and (quality['S'], quality['oi']) == (e['S'], e['oi'])
        stamp = quality['utc_ms']*1000000
        eligible = [oid for oid, order in accepted.items() if (order['S'], order['oi']) == (e['S'], e['oi'])
                    and lifetimes[oid][0] < stamp < lifetimes[oid][1]]
        if len(eligible) != 1:
            continue
        oid = eligible[0]
        order = accepted[oid]
        if quality['p'] == order['p']:
            observed_prefill.add(oid)
        if not quality['uygun'] or quality['neden'] != 'open' or quality['p'] != order['p']:
            continue
        s = quality['kaynak']
        assert s['model_sha'] == g_policy.SHA
        if not (0 <= quality['utc_ms']-s['book_ms'] <= 3000 and e['mutabakat']):
            continue
        observed_open_prefill.add(oid)
        amounts = [e['up'], e['down']]
        target = g_policy.target(e['bb'], e['ba'], s['tick'], amounts[e['oi']], amounts[1-e['oi']])
        if target is None or not (e['bb']-.02-1e-9 <= order['p'] <= e['bb']+1e-9 and order['p'] > target+1e-9):
            continue
        signals.append(dict(oid=oid, S=e['S'], oi=e['oi'], flag_ms=quality['utc_ms'],
                            price=order['p'], bid=e['bb'], ask=e['ba'], new_target=target,
                            up=e['up'], down=e['down'], source_age_ms=quality['utc_ms']-s['book_ms'],
                            first_match_received_ms=min(fills[oid])/1e6 if fills[oid] else None,
                            until_first_match_ms=(min(fills[oid])-stamp)/1e6 if fills[oid] else None,
                            until_first_known_match_ms=(min(first_known_match[oid])-stamp)/1e6 if first_known_match[oid] else None,
                            until_actual_cancel_request_ms=(min(cancels[oid])-stamp)/1e6 if cancels[oid] else None))
    first = {}
    for signal in signals:
        first.setdefault(signal['oid'], signal)
    filled = [x for x in first.values() if x['first_match_received_ms'] is not None]
    assert all(x['until_first_match_ms'] > 0 and x['until_first_known_match_ms'] > 0 for x in filled)
    result = dict(candidate='Risk-increasing quote only: cancel when p > current target and current retained band still holds; reducing quotes unchanged.',
                  exploratory=True, accepted_parents=63, actual_filled_parents=36,
                  parents_with_identified_prefill_quote=len(observed_prefill),
                  filled_parents_with_identified_prefill_quote=len(observed_prefill & set(fills)),
                  parents_with_fresh_open_prefill_quote=len(observed_open_prefill),
                  filled_parents_with_fresh_open_prefill_quote=len(observed_open_prefill & set(fills)),
                  observed_candidate_samples=len(signals), flagged_parents=len(first),
                  flagged_eventually_filled_parents=len(filled), flagged_unfilled_parents=len(first)-len(filled),
                  until_first_match_ms=distribution([x['until_first_match_ms'] for x in filled]),
                  until_first_known_match_ms=distribution([x['until_first_known_match_ms'] for x in filled]),
                  observed_cancel_rtt_ms=distribution(cancel_rtt),
                  first_flags=list(first.values()), all_flags=signals,
                  limitations=['Signals use ~1 Hz recorded decisions, not every production-loop observation.',
                               'Flag time strictly follows local POST ACK and independent private PLACEMENT receipt.',
                               'Lifetime stops at first cancel request, first matched quantity observation, or terminal state; ambiguous concurrent parents excluded.',
                               'First private MATCHED receipt is later than exchange execution; positive lead time does not establish a cancellable order.',
                               'SDK cancellation roundtrip is not exchange cancel effect time or a guaranteed latency bound.',
                               'Changed cancel/requote would change queue and later fills/inventory; no prevented-loss or counterfactual PnL estimate.',
                               'Fresh quote and open quality fields do not reconstruct unlogged uncertain reservations exactly.'],
                  inputs={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in (
                      FINAL/'original/LOG_g.jsonl', FINAL/'original/LOG_g_emir_iz.jsonl',
                      PRIVATE/'A_private.jsonl', PRIVATE/'B_private.jsonl', BOT/'g_policy.py')})
    (HERE/'buffer_probe.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('first_flags','all_flags','inputs','limitations')}, indent=2))


if __name__ == '__main__':
    main()
