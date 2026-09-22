"""Frozen G1 close: exact cash arithmetic; pending resolution stays pending."""
from decimal import Decimal
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    checkpoint = ROOT/('complete' if (ROOT/'complete/result.json').exists() else 'recheck')
    result = json.loads((checkpoint/'result.json').read_text())
    state = json.loads((checkpoint/'reconciled_state.json').read_text())
    rows = [json.loads(x) for x in (ROOT/'original/LOG_g.jsonl').read_text().splitlines()]
    assert rows[-1]['k'] == 'bitti' and rows[-1]['sebep'] == 'sure'
    assert result['open_orders'] == 0 and not result['live_writers']
    assert len(result['windows']) == 6
    settled = Decimal(0)
    low = high = Decimal(0)
    accepted = filled = pending = 0
    for item in result['windows']:
        window = state['pen'][item['key']]
        amounts = [Decimal(0), Decimal(0)]
        cost = Decimal(0)
        for order in window['emir']:
            assert order['durum'] in ('kapali', 'dolu') and not order.get('gonderiliyor')
            quantity = Decimal(str(order.get('pay', 0)))
            amounts[order['oi']] += quantity
            cost += quantity*Decimal(str(order['p']))+Decimal(str(order.get('ucret', 0)))
            accepted += bool(order.get('oid'))
            filled += quantity > 0
        assert abs(cost-Decimal(str(item['cost']))) < Decimal('0.000001')
        if window['cozuldu']:
            pnl = amounts[window['kazanan']]-cost
            assert abs(pnl-Decimal(str(item['pnl']))) < Decimal('0.000001')
            settled += pnl
        else:
            assert item['pnl'] is None and item['winner'] is None
            pending += 1
            low += min(amounts)-cost
            high += max(amounts)-cost
    assert abs(settled-Decimal(str(result['settled_pilot_pnl']))) < Decimal('0.000001')
    assert pending == result['pending']
    assert abs(settled+low-Decimal(str(result['terminal_range'][0]))) < Decimal('0.000001')
    assert abs(settled+high-Decimal(str(result['terminal_range'][1]))) < Decimal('0.000001')
    print(json.dumps(dict(passed=True, accepted=accepted, filled_orders=filled, pending=pending,
                          settled=str(settled), terminal_range=[str(settled+low), str(settled+high)])))


if __name__ == '__main__':
    main()
