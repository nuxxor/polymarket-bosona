#!/usr/bin/env python3
"""Fee-signature execution-role classifier for Polymarket public /activity BUY rows.

Maker fills carry no fee: usdcSize == size*price. Taker fills on fee-enabled markets pay
fee = rate*size*price*(1-price) (rate 0.07, exponent 1 for BTC/ETH/SOL up-down markets):
usdcSize == size*price + fee. Anything else is 'other' (never silently assigned).
Validated: 156/156 agreement with the server takerOnly=true flag on 8 BTC15m markets
(MY/results/taker_only_crosscheck.json) and 303/303 with on-chain OrdersMatched roles
(MY/results/order_identity_recomputed.json).
"""
import math


def role(price, cash_price, qty, rate=0.07):
    """price = raw fill price; cash_price = usdcSize/size; qty = size."""
    if not (math.isfinite(price) and math.isfinite(cash_price) and math.isfinite(qty)) or qty <= 0 or not 0 < price < 1:
        return 'other'
    prem = (cash_price-price)*qty
    fee = rate*price*(1-price)*qty
    # Tolerance relative to the fee itself (API rounds usdcSize to 1e-6 and price to <=1e-10):
    # an absolute per-share tolerance would misclassify takers at extreme prices where fee/share < tolerance.
    tol = 2e-6+0.25*fee
    if abs(prem) <= tol:
        return 'maker'
    if abs(prem-fee) <= tol:
        return 'taker'
    return 'other'


def role_of_row(a, rate=0.07):
    q = float(a['size'])
    return role(float(a['price']), float(a['usdcSize'])/q if q else float('nan'), q, rate)


def _test():
    assert role(0.40, 0.40, 100) == 'maker'
    assert role(0.40, 0.40+0.07*0.4*0.6, 100) == 'taker'
    assert role(0.40, 0.40+0.07*0.4*0.6*0.5, 100) == 'other'      # half fee: neither
    assert role(0.40, 0.41, 5) == 'other'                          # +1c premium on 5 shares: not a fee
    assert role(0.016, 0.016, 5.08125) == 'maker'                  # tiny price, S-period example
    assert role(0.02, 0.021507503, 5.08125) == 'taker'             # S-period taker at 2c (fee 0.07*.02*.98)
    for q in (1, 5, 50, 500, 5000):                                # scale invariance
        assert role(0.55, 0.55+0.07*0.55*0.45, q) == 'taker' and role(0.55, 0.55, q) == 'maker'
    assert role(float('nan'), 0.4, 5) == 'other' and role(0.4, 0.4, 0) == 'other' and role(1.0, 1.0, 5) == 'other'
    # rounding: API cash rounded to 1e-6 per share must still classify
    assert role(0.4, round(0.4+0.07*0.4*0.6, 6), 3.3) == 'taker'
    print('role_classifier: all checks passed')


if __name__ == '__main__':
    _test()
