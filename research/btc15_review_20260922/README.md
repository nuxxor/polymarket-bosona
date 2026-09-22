# Bosona BTC15 independent review packet

This packet supplies the BTC15 research missing from the earlier main-repository
publication. It accompanies [the common PRO/ULTRA prompt](../../docs/BOSONA_BTC15_PRO_ULTRA_PROMPT.md).
Scope: Bosona BTC 15-minute behavior, its imitation, accounting, execution, and
economic falsification. No new five-minute strategy work or deployment is included.

## Start here

1. Read the common prompt.
2. Run `python3 research/btc15_review_20260922/verify_packet.py` from the repository root.
3. Read `R/btc15_reconciled_v1_20260921/RAPOR.md` for corrected historical counts.
4. Read `R/btc15_transport_v2_20260922/RAPOR.md` and its code/results for the latest execution analysis.
5. Read `R/btc15_markout_20260922/RAPOR.md` for the tested predictive explanations.
6. Use earlier reports to trace disagreements, not to overwrite later corrections without checking.

## What is actually included

- `R/`: frozen original source files, protocols, plans and reports from the BTC15
  workspace; selected calculated results and public market activity evidence.
- `U/`: earlier independent audit reports and analysis source.
- `R/fable_review_20260921/`: earlier independent Fable reports, code and selected results.
- `R/ultra_fable_synthesis_20260921/`: audit of disagreements and replay defects.
- `manifest.json`: exact original-copy paths, byte counts and SHA256 hashes.

The original project began with multiple non-BTC5 markets, so a few shared
helpers and historical result files also contain other assets/durations. The
review and portable calculation below explicitly select `group == btc_15m`.
Do not treat unrelated tables as additional BTC15 observations.

## What this is not

This is a review packet, not a live bot release or a complete raw-data mirror.
Large raw L2/Chainlink recordings, the full raw API/receipt cache, source-linked
external workspaces, and private account streams are not included. Some older
report links therefore refer to unavailable raw evidence or calculations.
Original scripts retain absolute local paths and original dependencies; running
all of them directly from a fresh GitHub checkout is **not** claimed to work.
The copies have not been silently rewritten to make old hashes or tests appear
valid. If a full reproduction needs a missing file, report that exact dependency.

The portable verifier runs without network, credentials, third-party packages
or any trading code. It checks supplied-file hashes and independently sums
BTC15 terminal payout minus API cash cost from the provided corrected fill rows,
including maker/taker and late-addition/top-ten totals. This checks consistency
of the supplied derived evidence; it does not independently prove raw coverage,
settlement correctness, parent ownership, causal identification, or queue calibration.

## Result interpretation

Historical BTC15: 598 traded markets, 5,441 fills, approximately +$4,428.55 cash
trading contribution. Corrected late maker additions: 1,077 fills, +$2,901.312562;
excluding their best ten markets: -$29.390092. These are observed-fill accounting.
Latest simulation: 8 assigned / 6 usable markets, 480 primary plus 288 diagnostic
paths; some positive paths reverse under clock stress. The same six markets are
not hundreds of independent samples. No calibrated, robust BTC15 edge is established.

Frozen checks/results describe previous runs. Only the portable verifier and
publication checks are freshly executed for this packet; this publication does
not claim to have rerun every historical study. No order or recorder is started.
