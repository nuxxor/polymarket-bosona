# BTC5m Top-Actor Hunt — Polymarket btc-updown-5m, 2026-08-14 .. 2026-09-02 (TWAP60 regime)

Source: Telonex Pro `onchain_fills` (every fill of every market, maker+taker wallets) + `trades` (CLOB ms clock)
+ Binance Vision spot aggTrades / USDT-M futures. Package: this directory. Raw fills:
`data/parquet/telonex_pm_btc5m_actor_hunt_20260814_20260902/` (5,793 files, 3.1 GB).

## 0. Verdict (all numbers recomputed in the main session)

* Ledger is exact: 19,236,533 fills → 38,473,066 party rows, 43,373 wallets, 5,402 resolved markets.
  Per-market invariant Σwallet PnL = −Σ taker fees holds to 0.000000. Independent cross-check vs the
  Densa public cash-flow audit (`densa_twap60_actor_audit_20260828_v1`): 498 markets, cost $15,068.75,
  PnL +$2,895.08 — identical to the cent.
* Venue economics (20 days): $3,009,059 taker fees; $259M buy notional; 10,662 wallets positive
  (+$1.87M pre-rebate), 63 wallets above +$5k (+$943k). Everyone else funds the fees.
* Regular winners (≥12 active days, ≥60% positive days, daily t≥2, PnL survives removing best 3
  markets): 25 wallets (`LEADERBOARD_REGULAR.csv`). Activity-timing correlation + identical first/last
  fill seconds show three multi-wallet operators:

| operator / wallet | PnL 20d (pre-rebate) | fees paid | days pos/20 | machine |
|---|---:|---:|---:|---|
| **A: 0x32ed2e54 + 0xc2ad03f7 + 0x3725d52f** | **+$142.6k** | $17.0k | 17 | calibrated buyer: maker bids below fair all window + last-minute TWAP/close-call taker |
| **0xce50c96b** (single) | **+$49.1k / 255 mkts** | $8.4k | 15/17 | selective 1–3 min BTC reversal signal, calm hours 04–11 UTC |
| **B: 0x3048d653 + 0xc53375ff + 0x0ca4e9d2** | +$94.8k | $146.7k | 17 | sub-parity pair assembly (pair cost 0.967), lives on gross + rebates |
| 0xbc588795 | +$33.7k | $10.9k | 18 | two-sided maker+taker incl. pre-start |
| 0x3387ac61 | +$27.5k | $0 | 18 | pure maker, ALL fills in the 40 s before open (reference-formation edge) |
| W3 0xeebde7a0 (E022 king) | +$25.5k | $71.4k | 12 | latency taker + heavy maker; pre-rebate marginal |
| **C: 0x5e2b9261 + 0x5d4aba8a + 0x75cc3b63 + 0x20d2309c** | +$51.7k | $35.2k | **20/20** | latency stale-quote pickoff after Binance moves (daily t 5–7) |
| 0xee65685d | +$20.3k | $0.8k | 13/17 | buys the near-certain winner at 0.89–0.99 late ($5.6M notional, ROI 0.4%) |
| 0xb0f85baa / 0x2011550a / 0xcd4a4057 / 0xe114e5ca | +$20.3k / +$10.2k / +$12.9k / +$14.1k | $0 | 16–18 | pure two-sided makers (spread capture, + maker rebates not observable) |
| 0x6fc44ec4 | +$7.5k, **100% win rate** | $0.16k | 19/19 | post-end winner sweep at 0.97–0.99 (271 markets) |
| W2 0x0cb03848 (E022 W2) | −$4.4k | **$159.9k** | — | rebate farmer: gross ≈ fees, profit = rebates only |

## 1. Method

* One asset file per market (sibling files are exact mirrors: price' = 1−price, same amount/fee/tx).
  Accounting: p_maker = price if not mirrored else 1−price; maker trades `amount` of maker_asset at p_maker,
  taker trades `amount` of taker_asset (sibling for buy/buy mints, sell/sell merges) at 1−p_maker, pays
  `taker_fee` (USDC; = 0.07·p·(1−p)·shares, verified median 0.0700). Payout = net winning shares × $1
  (split/merge $1-neutral ⇒ exact). Pre-rebate (maker/taker rebates are off-chain credits, not in fills).
* Clock: CLOB match time from `trades` (trade_id = tx_hash), 95.3% coverage; block time is 2.44 s later
  (p5 1.44, p95 3.46). Fallback block−2.44 s.
* Fair value model: Binance spot 100 ms; settlement S = mean price over [240,300) s vs reference =
  mean over [−60,0) s. **Verified empirically**: this definition matches the official result in 96.7% of
  markets (full-range TWAP 86%, spot reference 92%); the 3.3% misses are close calls (|margin| 0.2–0.3 bps,
  Chainlink composite ≠ Binance). Model is calibrated (fair 0.5→48%, 0.9→87%; Brier 0.060 at t=240).
  Market prices are calibrated too (control buys: price 0.524→realized 0.531, 0.933→0.939) — the venue as a
  whole is efficient; winners exploit specific pockets.

## 2. Decoded mechanisms (evidence in `PROFILES/`, `analyze_state_batch.txt`, `STATE_FEATURES.parquet`)

1. **Operator A (0x32ed family, +$142.6k).** Buy-only. 64% of fills as maker: resting bids are filled
   2–9 c below model fair at every clock (below_fair 63–75%), realized +1–3 c early; as taker they take
   momentum early (little realized edge) and, decisively, **buy underdogs/close calls in the last minute**:
   240–270 s taker buys at 0.283 vs model 0.387 → realized 0.376 (+9.8 c/share); 270–300 s +13.2 c. Crowd's
   cheap late buys realize ≈ price (0.294→0.289), so A selects which underdogs. 20% of A's PnL ($30k) comes
   from the 3.5% of markets where Binance and Chainlink disagree, at 7× the per-market rate ⇒ A prices the
   real resolution feed (Chainlink TWAP60) better than the Binance-thinking crowd. No BTC prediction
   (future BTC drift after their fills ≈ 0 or adverse).
2. **0xce50c96b (+$49.1k in 255 markets, $192/market).** Trades 4.7% of markets, almost only 04–11 UTC
   and calm σ (0.42 vs 0.49 bps/√s), concentrated days (Aug 22 Sat +$16.7k, Aug 18/25 Tue). Taker buys at
   0.527 when model fair is 0.482 (against the current Binance direction and against 60 s momentum: spot
   −1.4 bps, perp −1.6 bps, flow imbalance 43% agree) — and BTC then reverts **+2.2–2.6 bps over the next
   60–120 s** (control +0.1; robust on block clock). Realized win 70% at 0.53 in 120–180 s (+15 c/share).
   Net side wins 68% of markets, first entry median t=48 s, adds pyramid with the reversal. Not explained
   by: Chainlink divergence (5.8% of PnL), PM flow (53% agreement), informed makers' position (54%), Binance
   signed flow, futures basis, or generic reversion (grid test: calm-hour 1–4 bps moves do NOT revert on
   average). ⇒ a private microstructure filter for which dips revert. Highest edge density on the venue,
   not copyable without the signal.
3. **Operator B (0x3048 family, +$94.8k pre-rebate, $147k fees).** 98% two-sided, taker legs $2.8M, pair
   cost median 0.967 → ~3.3 c/pair locked; every leg is bought at ≈ model fair (edge_model +0.2–0.9 c) and
   realizes +1.7–2.2 c. Gross ≈ +$130k − fees $87k (0x3048 alone). With 30–50% rebates the operator
   likely nets +$140–170k. This is the Jet mechanism industrialised; the Aug-18 naive replay lost because it
   lacked B's leg selection.
4. **Operator C (+$51.7k, 20/20 positive days) & W3 taker legs.** Buy after fresh Binance moves
   (10 s flow agreement 73%, 15 s momentum 65–75%), price 1–2 c above model fair but BTC continues
   +0.5–0.9 bps within 5–60 s; tight per-market distribution (0x20d2 p01 −$93 / p99 +$93, max DD $96).
   Classic stale-quote pickoff; requires speed. Makers in aggregate lose −$457k gross during 0–240 s to
   this family (maker gross by clock: pre-start +$52k, 0–240 s −$457k, 240–300 s +$62k, post-end +$40k).
5. **Pre-start reference-formation edge (0x3387, 0xbc58, W3/0xbc58 taker side).** In [−60,0) s the opening
   reference (TWAP of that minute) is forming; spot vs the partial reference tells which side opens
   in-the-money. Causal test on all fills: makers filled on the with-reference side at −30..−10 s earn
   +2.4 c/share (+$41k/20 d), at −60..−30 s +3.8 c (+$37k); against-side makers lose −$65k. Takers on the
   with-side at −30..−10 s: 0.523→0.546, 0.543→0.575, 0.583→0.607 (+$65k gross, ≈ +0.6–1.5 c net of fee).
   0x3387 executes this purely as maker (median fill t = −8 s, q25 −20 s, $27.5k, zero fees, 18/20 days).
   Pre-start takers lose most days (−$14.6k, −$16.1k, −$12.1k …) ⇒ persistent.
6. **Certain-favorite / post-end sweeps.** 0xee65 buys 0.89–0.99 favorites late ($5.6M notional, +$20k);
   0x6fc4 bids 0.99 for the winner after t≥270/post-end (271 markets, 0 losses, $711k notional, +$7.5k;
   29% of it in Binance/Chainlink-disagreement markets).

## 3. What is replicable for us (ranked by evidence × capacity)

1. **Pre-start reference-formation maker** (mechanism 5): post bids on both sides at 0.48–0.49 from
   t=−60 s, cancel the side opposite to spot-vs-forming-reference as it forms, hold to settlement.
   Population evidence +2.4–3.8 c/share on the with-side, zero fee, ~5M with-side shares/20 d available
   pre-start; single operator (0x3387) makes ~$1.4k/day. Needs our book recorder for fill-ratio truth.
2. **Last-minute close-call pricing** (mechanism 1, taker or maker): requires the Chainlink BTC/USD TWAP60
   stream (resolution source). Value: A earns ~$23k/20 d from 240–300 s taker buys on $158k notional and
   ~$30k from the 3.5% close-call markets. Pre-req: Chainlink Data Streams access + causal replay.
3. **Post-end winner bid at ≤0.99** (mechanism 6): small, mechanical, 100% win when the resolution feed is
   read correctly; ~$400/day at 0x6fc4's size.
Not replicable: 0xce50's signal (private), latency pickoff (needs colocation + speed we don't have),
rebate farming (volume tier).

## 4. Caveats

* Pre-rebate; TAKER/MAKER rebates (≈30–50% of fees for top tiers) would raise operators B, W2, W3 a lot.
* 346 markets (6%) have no fill files in Telonex for the window; Sep 2 is partial (59 markets).
* Fair-value model is Binance-based; the 3.3% Chainlink/Binance disagreement is the floor of its accuracy.
* Operator clusters inferred from activity correlation (0.62–0.82) and identical first/last fill
  seconds, not from on-chain funding traces.
* All wallet edges are measured outcome-exposed on 20 days; only mechanism 5 has been tested causally
  population-wide (the rest are actor-conditional).

## 5. Next experiments (concrete, today-runnable)

* E1 (pre-start maker shadow): replay with London book recorder BBO (Aug 14–29): quote 0.49/0.49 at
  t=−60, skew by partial reference; measure fill ratio + realized; gate +1.5 c/share after 300 fills.
* E2 (close-call pricing): obtain Chainlink TWAP60 stream history; causal replay of 240–300 s underdog
  buys with model+stream; gate: reproduce ≥50% of A's late-window edge on non-A fills.
* E3 (0xce50 signal search): condition on their 255 markets; test Binance trade-size/queue-depletion
  features at their entries vs matched controls (requires book data, not trades alone).
