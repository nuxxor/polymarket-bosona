"""G1 frozen engineering baseline, not an inferred Bosona alpha signal."""
from decimal import Decimal, ROUND_FLOOR
from hashlib import sha256
import math
from pathlib import Path


def append_page(previous, page, key):
    """Preserve real same-looking fills; ambiguous overlapping API pages stop reconciliation."""
    if {key(r) for r in previous} & {key(r) for r in page}:
        raise ValueError('overlapping public pages: multiplicity unknown')
    previous.extend(page)

SHA = sha256(Path(__file__).read_bytes()).hexdigest()
ENTRY_END = 240
REDUCE_END = 290


def target(bid, ask, tick, own, opposite):
    try:
        if not all(math.isfinite(x) for x in (bid, ask, tick, own, opposite)):
            return None
        if not 0 < bid < ask <= 1 or tick not in (.01, .001) or min(own, opposite) < 0:
            return None
        if own-opposite >= 5-1e-6:
            return None
        # Fixed one cent, not one terminal-market tick inferred from later data.
        grid = Decimal(str(tick))
        price = ((Decimal(str(bid))-Decimal('.01'))/grid).to_integral_value(rounding=ROUND_FLOOR)*grid
        return float(price) if grid <= price <= 1-grid and price < Decimal(str(ask)) else None
    except (ValueError, TypeError):
        return None


def quality(window, side, price, signal, now_ms):
    try:
        if side not in (0, 1) or not signal or signal.get('model_sha') != SHA:
            return False, 'policy_or_side'
        if not 0 <= now_ms-signal['karar_ms'] <= 1500 or not 0 <= now_ms-signal['book_ms'] <= 3000:
            return False, 'stale'
        bid, ask = signal['bb'], signal['ba']
        if not all(math.isfinite(x) for x in (price, bid, ask)) or not .001 <= price <= .999:
            return False, 'invalid_quote'
        tick = signal['tick']
        if tick not in (.01, .001) or abs(price/tick-round(price/tick)) > 1e-6:
            return False, 'tick'
        if not 0 < bid < ask <= 1 or price > bid+1e-9 or price >= ask-1e-9:
            return False, 'not_passive'
        amounts = [math.fsum(r.get('pay', 0) for r in window['emir'] if r['oi'] == i) for i in (0, 1)]
        if any(not math.isfinite(q) or q < 0 for q in amounts):
            return False, 'invalid_inventory'
        reducing = amounts[1-side] > amounts[side]+1e-6
        age = now_ms/1000-signal['S']
        if not 3 <= age < (REDUCE_END if reducing else ENTRY_END):
            return False, 'time_limit'
        return True, 'reduce' if reducing else 'open'
    except (ValueError, KeyError, TypeError, OverflowError):
        return False, 'missing_data'
