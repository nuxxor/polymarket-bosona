# Independent research review: reverse-engineering Bosona's BTC 5-minute policy

You are an independent quantitative researcher reviewing an ongoing attempt to understand and reproduce a trader's observable decision policy. Challenge our work; agreement with the existing researchers is not the objective. The same brief is being given independently to three reviewers. Do not assume their conclusions or manufacture consensus.

**Repository:** https://github.com/nuxxor/polymarket-bosona

**Brief prepared:** 21 September 2026. All times below are UTC. Record the exact repository commit and data cutoff you inspect. The repository receives periodic updates; a local source file, an archived release, and a running experiment can have different hashes. Statements below describe dated evidence, not a promise about current runtime.

## 1. The actual objective

Our first priority is to **explain Bosona's BTC 5-minute trading policy well enough to derive testable, independently executable rules**. A profitable unrelated strategy would be useful, but would not establish that we have understood Bosona. Similar trade counts or occasional matching directions would not establish that either.

We want to understand when Bosona enters, which side and price it chooses, how much it buys, when it adds to exposed inventory, when it buys the opposite side, and when it reopens risk after pairing. Ultimately we want a smaller implementation with a credible economic edge after executable costs.

The question is: **Are our experiments converging toward the mechanism behind Bosona's results, or drifting into a generic cheap-side mean-reversion and inventory strategy? What is the most valuable clue or change of research direction we have missed?**

Focus on BTC Up/Down **5-minute** contracts. Leave Jev/LLM prediction experiments and other assets/durations outside this assignment. This is research: do not start or stop services, change live/shadow rules, place orders, change budgets, or access credentials. Public-data queries and isolated, reproducible analysis are appropriate. If tools or data are unavailable, identify the precise limitation and still evaluate the accessible evidence; never imply that you inspected or executed something you could not access.

## 2. Evidence map

Read applicable repository instructions and `plan.md` first. Most reports are in Turkish. Use primary records and code to verify the reports; their conclusions are hypotheses to audit. If possible, form a preliminary behavioral account from the ledgers before reading our preferred strategy's rationale, to reduce anchoring.

Start with these repository-relative paths:

| Purpose | Files |
|---|---|
| Research history, late additions | `docs/BOSONA_GEC_ARASTIRMA_20260921.md`, `docs/BOSONA_DERIN_20260921.md` |
| Earlier forward comparison against Bosona | `docs/SHADOW_BOSONA_20260921.md` |
| Current inventory experiments and version chronology | `docs/BOSONA_ENVANTER_SHADOW_20260921.md` |
| Historical actor accounting | `data/analysis/bosona_gec_20260921/report.json`, `windows.json`, `fill_ledger.json`, `activity.json` in that directory |
| Feature research and all screened candidates | `data/analysis/bosona_derin_20260921/`: `features.json`, `screen.json`, `mechanism.json`, `policy.json`, `policy_rows.json`, `statistics.json`, `coverage.json`, `prospective_protocol.json` |
| Inventory rationale | `data/analysis/bosona_inventory_20260921/inventory_research.json` and `research.py` |
| Feed corrections and runtime evidence | `data/analysis/btc5m_feed_fix_20260921/` |
| Small, reproducible common-window checkpoint | `data/analysis/btc5m_status_20260921_1420/`: `OKUMA.md`, `report.json`, `check.py`, journals and frozen per-market activity/trades/market responses |
| New participation experiment | `data/analysis/btc5m_participation_20260921/`: `watch_manifest.json`, `runtime_verified.json`, `entry_coverage.json`, `shadow_forward.jsonl` |

Key source files under `analiz/izleme/`:

- `bosona_gec_arastirma.py`: public data, ledger/FIFO attribution, inputs, books and fee calculations.
- `bosona_derin.py`: historical features, settlement forecasts and candidate comparisons.
- `bosona_rebound_shadow.py`: independent entry experiments at t=240/270/280 seconds; t=280 is primary.
- `bosona_inventory_shadow.py`: repeated decisions, pairing, additions, reopening and optional `--participate` profile.
- `check_inventory_shadow.py`: executable scheduler and accounting regression checks.
- `muhasebe.py`: accounting support.

The six-window `check.py` uses the included cached public responses and recomputes its report. Run it in your own checkout if available. `runtime_check.py` in the participation directory instead expects a particular London installation; do not treat it as a portable offline test. Historical raw tape was approximately 18.65 GB and may not all be available in the GitHub checkout. State which conclusions require missing raw data, rather than treating derived features as independently verified raw evidence.

## 3. What our research currently reports — verify, do not accept blindly

The historical BTC5m cohort covers 13 September 00:00 through 20 September 22:30 UTC: **1,842 markets and 19,761 BUY records**, with reported API cash-cost PnL of approximately **+$8,319.44**, excluding rebates and fixed costs. Check accounting scope, fees, other cash flows, pagination and fill multiplicity before relying on this total.

FIFO attribution assigns about **+$14,799.08** to paired inventory and **−$6,479.64** to unmatched inventory. This is an accounting allocation, **not proof that pairing itself caused the edge**. Different lot allocation or counterfactual inventory paths can change the interpretation.

Reported final-100-second contribution is about **+$4,603.64**, with additions to the already exposed side contributing about **+$2,784.24**. Final-20-second additions comprise **271 fill records across 66 markets**, contributing **+$1,888.81**, or **+$975.73** excluding the best three markets. An exchange-time-matched subset has 157 records/40 markets, +$1,190.61, or +$460.42 excluding its best three. These are overlapping, selected subsets, not independent confirmations.

Some cheap late additions lose frequently yet pay enough when they win: in the reported <30¢ final-20-second group, average cash cost was 12.8¢ and eventual payout 36.9¢ per share. This describes observed fills, not an executable rule to buy everything cheap. Other observed additions occurred at **88–91¢**. A cheap-only policy cannot explain the whole behavior.

Timing and execution materially change the picture. In a matched sample, public transaction timestamps lag exchange timestamps by a median about 2.74 seconds. On the same measurable final-100-second additions, normalizing each record to five shares produces about **+$53.24 at Bosona's observed prices versus −$217.02 at the ask five seconds after public time, including modeled fees**. This is a diagnostic price comparison, not a real copy-trading experiment or proof of a specific latency strategy.

Our broad screen considered roughly 60 metrics and **10 rules × 5 entry times**. The selected cheap-side rebound candidate at t=280 chose 23 of 140 eligible windows, returning about +$19.93 in historical paper execution, or +$7.47 excluding its best three. Its later-period +$11.21 included +$10.73 from one day. Previously examined chronological splits and confidence intervals after candidate selection are **not clean out-of-sample validation**.

In a separate, more recent 89-market cohort, Bosona's reported +$984.66 became **−$92.55 without the best three markets**. Results are sensitive to cohort and concentration. Do not infer a stable edge or its absence from either cherry-picked cohort.

## 4. What our current shadows actually do

The corrected selective inventory experiment began assigned windows at **21 September 13:50 UTC**, with a planned 72-hour run. Every ten seconds from t=30 through t=290 it manages independent paper portfolios:

- **First entry/reopening:** through t=200, buy the cheaper side only if ask <50¢, that side's simple 14-period RSI on closed one-minute bars is <40, and its last-ten-second BTC momentum is positive.
- **Completion:** buy only up to the unmatched quantity when its FIFO acquisition cost plus the new fee-inclusive ask cost is ≤98¢ per pair. Previously paired cheap inventory cannot subsidize an expensive new pair.
- **Addition candidate:** add to the exposed side when the rebound condition holds again, with at least 20 seconds between buys. The control does not make these additions.
- **Limits per window:** five-share clips, at most ten unmatched shares, $15 acquisition cash, and worst settlement payoff no worse than −$5. These are experimental limits, not estimated Bosona parameters or known optima.
- **Execution:** independent fast and ≥250 ms delayed paper portfolios; fresh public HTTP ask depth and fees are rechecked. These are neither real fills nor measurements of maker queue position, cancellation timing or order acceptance latency. Do not add the four portfolios' PnL as if they were one portfolio.

A separate participation experiment began at **21 September 14:45 UTC**. Its first entry seeks the least expensive fee-inclusive executable five-share side from t=30..200, without RSI/momentum/50¢ gating. Later additions/reopening remain selective; completion and per-window limits remain unchanged. It targets every window but does not fabricate fills when data, depth or execution are unavailable. Only its initial operation was verified at this brief's evidence cutoff; no economic success is claimed. More participation also means different aggregate risk even with identical per-window limits.

This participation change was motivated by the operator's desire to observe more windows. **It was not a discovery of Bosona's entry mechanism.** Critique whether it is an informative control, an unjustified directional exposure, or both.

At the **13:50–14:20 UTC checkpoint**, on six identical resolved markets:

| Observation | Result |
|---|---|
| Selective pair-only, delayed | 3 traded windows, 7 paper fills, **−$0.39053** |
| Selective pair+add, delayed | 3 traded windows, 10 paper fills, **+$0.23117** |
| Bosona | 6 traded windows, 134 public BUY records, **−$158.631739** API cash-cost PnL; much larger quantities, rebates/fixed costs excluded |
| First-side agreement | 2 of 3 common traded windows |
| Nearby single-direction comparisons, ±15 seconds | 2 of 4 agreed |

These tiny samples establish neither superiority nor behavioral convergence. Bosona's median first entry was 71 seconds/29¢ versus ours 150 seconds/16¢, on different traded cohorts. The journals had 162/162 scheduled inventory decisions, but only 144 valid contexts; 18 real price gaps remain. Missing observations are not successful decisions to wait.

## 5. Measurement traps you must address

1. **Observed fills are selected outcomes of hidden orders.** Public data does not reveal all posted/canceled orders, queue position, rejected intentions or hedges elsewhere. A fill timestamp is not an order-decision timestamp. No observed fill does not prove a deliberate no-trade decision. Distinguish identifiable policy features from observationally equivalent mechanisms.
2. **Multiplicity and inventory:** another research branch found real, identical-looking fills had been collapsed by deduplication. That does not prove this BTC5m ledger is wrong. Audit it; the latest six-market checkpoint compares activity/trades multiplicities with `Counter`, rather than indiscriminately deduplicating. Account for same-second ordering ambiguity, pre-window acquisitions and other inventory-changing events where present.
3. **Causal clocks:** distinguish market/exchange event time, local receipt time, public API time and decision time. Historical features must have been available by the decision cutoff. Corrected code selects historical event-time observations from data already received at the current decision time. Closed-candle publication and stale/partial-book handling also changed. Do not pool old and corrected versions into one forward result.
4. **Missingness and costs:** unavailable data, no signal, rejected execution, unresolved outcome and realized zero are different. Compare policies on consistent eligible universes, while reporting exclusions. Missing favorite quotes have `null` cost/PnL, not zero. Ask-depth paper execution is useful but can be an imperfect proxy for Bosona's execution economics. Verify current official fee/settlement rules when needed.
5. **Selection and capital:** conditionally profitable actor fills are not an independent strategy. Reusing Bosona's quantities while changing its actions breaks the inventory path. Equal-share normalization is descriptive unless the resulting actions and prices were executable. Report concentration, turnover, unmatched exposure and capital usage alongside dollars.

London deployment is verified. The operator describes the infrastructure as very fast, but exchange colocation and end-to-end executable latency have not been established. Treat latency advantage as a hypothesis to measure, not an explanation granted in advance.

## 6. Your research assignment

Investigate the mechanisms supported by evidence, including alternatives to our favored explanation. Useful distinctions include settlement/TWAP pricing versus spot direction; favorable prices versus simple winner prediction; inventory management versus fresh directional alpha; passive liquidity provision versus active selection; and size/selection effects versus a repeatable signal. These are possible explanations to discriminate, not a checklist of indicators to add.

**A. Audit our direction.** Identify the strongest evidence that we are learning Bosona's behavior, the strongest evidence against it, and where we substituted a convenient heuristic for an inferred mechanism. Does “late additions made money” justify a one-shot late-entry rule? Does an early cheap-side strategy with a strict profitable-pair cap explain the actor's paths? What important behavior does each exclude?

**B. Trace actual paths.** Reconstruct at least one informative profitable market and one losing or counterexample market from accessible records. Show contemporaneously available information, observed fills, inventory before/after, and final contribution. Include a case that challenges your preferred hypothesis. Avoid claiming a hidden intention from a realized result.

**C. Rank at most three mechanisms.** For each provide: supporting and contradicting evidence; the exact causal inputs; what it predicts about timing, side, price, size or inventory; a diagnostic distinguishing it from the nearest alternative; and an explicit falsification result. Rank by explanatory power and testability, not in-sample PnL alone. If you find a stronger clue, follow it beyond its first correlation.

**D. Specify the single highest-value next experiment.** Give executable pseudocode or a precise analysis specification, a baseline/ablation, the minimum additional data, the assigned window universe, and precommitted continue/reject criteria. Separate descriptive actor-conditioned tests from deployable policies: a deployable policy must use its own inventory and contemporaneous public inputs, not Bosona's future fills. Consider a fixed-entry ablation to isolate management from entry quality, followed by a free-running test only if justified. Choose the design based on what actually remains unidentified.

Evaluate **behavioral fidelity and economic value separately**. Side accuracy alone is insufficient. Use a small justified set of comparisons covering action timing/type, entry prices, inventory paths or sizing, and fee-net dollars per assigned window with missing coverage and risk reported. Address repeated experimentation, clustered uncertainty and top-market concentration. “Three days/100 trades” is not automatically adequate statistical power.

Be resourceful and quantitative, but do not build a large framework or recommend another broad parameter sweep by default. A small reproducible analysis that rules out a mechanism is more useful than ten new loosely justified shadows. Do not stop at “collect more data”: specify exactly what observation would resolve which competing explanations. If the hidden policy is not identifiable from available public data, explain the ambiguity and propose the smallest useful surrogate policy or additional measurement.

## 7. Required output

Write the final assessment in Turkish; retain code and technical identifiers as needed. Deliver:

1. A short verdict: **on track, partially on track, or materially off track**, with calibrated confidence and evidence.
2. The most consequential methodological or implementation problems, citing exact repository paths/lines or reproducible calculations. Separate verified defects from suspicions.
3. Your ranked mechanisms and the supporting/counterexample market paths.
4. **Your single most valuable insight for cracking Bosona's BTC5m policy**, followed by one concrete next experiment. Say what we should keep, stop, or change.
5. A short list of what remains unidentifiable or unverified, including inaccessible inputs and checks you did not run.

Do not promise profitability, invent a success probability, treat our existing reports as proof, or reassure us because we have invested effort. We want a defensible explanation and the next discriminating test, including a candid conclusion that our current approach is wrong if that is what the evidence supports.
