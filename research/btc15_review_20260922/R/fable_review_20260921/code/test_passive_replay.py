#!/usr/bin/env python3
"""Synthetic regression tests for passive_replay: queue semantics, bounds, limits, hedge, gaps."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import passive_replay as pr  # noqa: E402

UP, DOWN = 'tokUp', 'tokDown'
TOKENS = [UP, DOWN]
S = 1_000_000
MARKET = dict(feesEnabled=True, feeSchedule=dict(exponent=1, rate=.07))


def snap(age, up_bid, up_ask, dn_bid, dn_ask, bid_size=100., gap=False):
    rms = (S+age)*1000
    if gap:
        return dict(received_ms=rms, requested_ms=rms-100, gap=True)
    books = {UP: ([(up_bid, bid_size), (round(up_bid-.01, 2), 50.)], [(up_ask, 100.)], rms-50),
             DOWN: ([(dn_bid, bid_size), (round(dn_bid-.01, 2), 50.)], [(dn_ask, 100.)], rms-50)}
    return dict(received_ms=rms, requested_ms=rms-100, books=books, gap=False)


def prints(*items):
    return [dict(ts=S+t, token=tok, price=p, size=q, wallet='x') for t, tok, p, q in items]


def run(snaps, pp, mode='pess', off=0, hedge=False):
    return pr.run_passive(snaps, TOKENS, pp, S, mode, off, hedge, MARKET)


def test_queue_pessimistic_vs_optimistic():
    snaps = [snap(a, .40, .42, .58, .60, bid_size=20.) for a in range(30, 200)]
    # 10 shares print at our price at t=100: queue ahead 20 → pessimistic not filled, optimistic filled
    pp = prints((100, UP, .40, 10.))
    s = run(snaps, pp, 'pess')
    assert s['q'] == [0., 0.], s['q']
    s = run(snaps, pp, 'opt')
    assert s['q'][0] == 5. and abs(s['cash']-2.0) < 1e-9
    # cumulative 25 shares (20 ahead + 5 ours) at our price → pessimistic filled
    pp = prints((100, UP, .40, 12.), (101, UP, .40, 13.))
    s = run(snaps, pp, 'pess')
    assert s['q'][0] == 5. and s['fills'][0]['kind'] == 'passive' and s['fills'][0]['role'] == 'maker'
    # a print BELOW our price (traded through) fills pessimistically regardless of queue
    pp = prints((100, UP, .39, 1.))
    s = run(snaps, pp, 'pess')
    assert s['q'][0] == 5.
    # prints before placement (ts < placed) are ignored; prints above our price are ignored
    pp = prints((10, UP, .39, 100.), (100, UP, .41, 100.))
    s = run(snaps, pp, 'pess')
    assert s['q'] == [0., 0.]


def test_requote_resets_queue_and_touch_minus_one():
    snaps = [snap(a, .40, .42, .58, .60, bid_size=20.) for a in range(30, 100)]
    snaps += [snap(a, .41, .43, .57, .59, bid_size=20.) for a in range(100, 200)]
    pp = prints((99, UP, .40, 15.), (150, UP, .41, 10.))
    s = run(snaps, pp, 'pess')          # queue reset at requote: 15 (old) + 10 (new) never reaches 25 at one level
    assert s['q'] == [0., 0.]
    assert s['quotes_cancelled'] >= 2
    # touch-1 quote at .40 after 100s; queue ahead = 50 (second level) → 30 shares not enough, 60 fills
    s = run(snaps, prints((150, UP, .40, 30.)), 'pess', off=1)
    assert s['q'] == [0., 0.]
    s = run(snaps, prints((150, UP, .40, 60.)), 'pess', off=1)
    assert s['q'][0] == 5. and s['fills'][0]['unit_cash'] == .40


def test_limits_and_reducing_side_only():
    snaps = [snap(a, .40, .42, .58, .60, bid_size=0.) for a in range(30, 400)]
    pp = prints(*[(40+i, UP, .40, 5.) for i in range(0, 60)])   # steady flow at our price, no queue ahead
    s = run(snaps, pp, 'pess')
    # cash limit 15 and net limit 10 (Up 10 → only Down side may quote, Down bid .58 → cash 2*... )
    assert abs(s['q'][0]-s['q'][1]) <= 10+1e-9
    assert s['cash'] <= 15+1e-9
    assert min(s['q'])-s['cash'] >= -5-1e-9


def test_hedge_arm_buys_reducing_side_at_ask_with_fee():
    snaps = [snap(a, .40, .42, .58, .60, bid_size=0.) for a in range(30, 400)]
    pp = prints(*[(40+i, UP, .40, 5.) for i in range(0, 4)])   # four passive Up fills → net 10 → hedge Down at ask .60
    s = run(snaps, pp, 'pess', hedge=True)
    assert s['hedges'] and s['hedges'][0]['side'] == 1 and s['hedges'][0]['qty'] == 10.
    assert abs(s['hedges'][0]['unit']-(.60+.07*.60*.40)) < 1e-9
    # after a hedge net is 0, quoting resumes and a second hedge follows the next 10 Up fills
    assert s['q'][0] == s['q'][1] and s['q'][0] >= 10.
    assert all(h['side'] == 1 and h['qty'] == 10. for h in s['hedges'])
    assert s['fee'] > 0
    # without hedge the same flow stops at net 10 (Up only)
    s0 = run(snaps, pp, 'pess', hedge=False)
    assert s0['q'] == [10., 0.] and not s0['hedges']


def test_gap_and_window_bounds():
    snaps = [snap(a, .40, .42, .58, .60, bid_size=0.) for a in range(0, 30)]      # before 30s: no quotes
    snaps += [snap(a, .40, .42, .58, .60, bid_size=0.) for a in range(30, 60)]
    snaps += [snap(60, 0, 0, 0, 0, gap=True)]                                       # gap cancels quotes
    snaps += [snap(a, .40, .42, .58, .60, bid_size=0.) for a in range(66, 900)]     # 6s hole → suspended first snapshot
    pp = prints((10, UP, .40, 50.), (60, UP, .40, 50.), (66, UP, .40, 50.), (850, UP, .40, 50.))
    s = run(snaps, pp, 'pess')
    assert all(f['when']-S not in (10, 60, 66, 850) for f in s['fills'])
    assert s['fills'] == []
    # wide spread (>3c) blocks quoting
    snaps = [snap(a, .40, .45, .55, .60, bid_size=0.) for a in range(30, 200)]
    assert run(snaps, prints((100, UP, .40, 50.)), 'pess')['fills'] == []


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
    print('passive_replay regression: all passed')
