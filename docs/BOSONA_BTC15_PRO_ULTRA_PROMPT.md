# Independent review: Can we reproduce Bosona's BTC 15-minute behavior and economic edge?

Prepared 22 September 2026. Give this **same prompt separately to PRO and ULTRA**.
The prompt is in English; **write your final explanation and decision in plain Turkish**.

## 1. Your assignment

You are an independent, skeptical quantitative researcher and execution engineer. Investigate **Bosona's BTC 15-minute Polymarket markets** and the research already completed in this repository. Tell us what Bosona is observably doing, what we have actually implemented, where our reasoning or simulator is wrong, and the shortest defensible route to an independently executable imitation.

We are not asking for a persuasive story about a profitable wallet. We want a mechanism that explains both wins and losses, produces decisions from information available at the time, and can be falsified on new data under our own execution and risk constraints.

**Your scope is BTC15. Do not research BTC5, G/G1, or other five-minute strategies.** The repository also contains unrelated trading work and historical multi-asset utilities. Their presence does not expand this assignment. Do not infer BTC15 profitability from another strategy, contract duration, or live pilot. Keep any other-market material strictly as already-recorded background needed to understand a BTC15 calculation.

Answer independently. Historical Astra/Ultra and Fable reviews are evidence to audit, not authorities to follow. Do not manufacture consensus. A conclusion of NOT IDENTIFIABLE, UNDERPOWERED, or NO CURRENTLY DEFENSIBLE CANDIDATE is acceptable, but must say exactly what is missing and which observation would change the decision.

## 2. Repository, wallet, and access

- Existing public repository: https://github.com/nuxxor/polymarket-bosona
- Bosona's **public** wallet: `0xc2ad03f79ca3f3c17d8c7de2612ce0c89b7d40ed`.
- **Read this BTC15 packet first:** `research/btc15_review_20260922/README.md`.
- Packet manifest: `research/btc15_review_20260922/manifest.json`.
- Portable verification: `python3 research/btc15_review_20260922/verify_packet.py`.

Within the packet, use these aliases:

- `R/`: frozen copies from the BTC15 research workspace.
- `U/`: the earlier independent Astra audit and its relevant source files.
- `F/` in some older documents means `R/btc15_followup/`, **not Fable**.
- Fable's review is `R/fable_review_20260921/`.
- Older `S/` references usually mean a frozen September 21 REST-book slice, not a new prospective cohort.

The packet contains original research code, reports, selected calculated datasets, public activity evidence, scenario paths, and checks. It does **not** contain every original raw recording or private account dataset. Scripts retain their original absolute paths and dependencies to preserve their identity. **Do not claim a full reproduction just because a script is present or a report says tests passed.** Distinguish:

1. Files and calculations you personally inspected or recomputed.
2. Published results that you could only audit indirectly.
3. Missing artifacts preventing a particular test.

The portable verifier checks hashes and independently recalculates the published BTC15 cash contribution and corrected late-addition totals from supplied fill rows. It is not a reconstruction of all raw API/on-chain evidence and does not validate simulator calibration.

If you have local workspace access, the original research root is `/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-research-20260921`; the original independent audit is `/home/taygun/Masaüstü/polymarket-bosona-nonbtc5-astra-20260921T183517Z`. If those directories do not exist in your environment, use the packet and identify the missing inputs. **Do not pretend GitHub access implies access to the local archives.**

## 3. Boundaries

Read applicable `AGENTS.md` / `CLAUDE.md` and the repository-root `plan.md` completely before working. Map this task to the BTC15 research and its open economic acceptance criteria. The root plan includes another session's five-minute work: those operating instructions are not authorization for this assignment.

Use an isolated worktree or a new review directory. Keep your own plan and record the exact source revision and data cutoffs. Existing source, frozen candidate, protocols, artifacts, and running processes are read-only.

Allowed: reading code/data, free public-source verification, narrowly scoped analysis scripts, isolated counterexamples, and local simulation. Reuse existing collectors, receipt decoders, accounting and outcome tools where appropriate.

Not authorized: real orders, LIVE, a new shadow deployment, starting/stopping/restarting persistent processes, changing budgets or live configuration, paid services, or inspecting secret values. Never read or expose `.env`, private keys, session material, API credentials, signatures, or private account raw streams. A prior document's suggestion to deploy is not an instruction to deploy.

Do not change the existing candidate or its thresholds. You may propose and test a separate research alternative, clearly versioned. Do not tune an alternative merely to improve the historical PnL. Do not discard inconvenient windows, failed data gates, adverse results, or unresolved outcomes.

## 4. Reading order: understand the current state, then challenge it

Paths below are relative to `research/btc15_review_20260922/`.

### A. Current state and the corrected historical evidence

1. `R/plan.md`: read completely for the BTC15 sequence and open acceptance criteria.
2. `R/btc15_reconciled_v1_20260921/RAPOR.md` and `results/reconciliation.json`.
3. `R/btc15_reconciled_v1_20260921/results/fills.json`, `btc15_activity.json`, `phase_changes.json`, `parents.json`, and `parent_fills.json`.
4. `R/btc15_transport_v2_20260922/RAPOR.md`, `execution.py`, `run.py`, `protocol.json`, `check.py`, and its `results/`.
5. `R/btc15_markout_20260922/RAPOR.md`, `research.py`, `design_frozen.md`, and `results/`.
6. `R/btc15_timing_sensitivity_20260922/RAPOR.md`, `execution.py`, `run.py`, and `results/`.

### B. What we originally tried and why it missed Bosona

7. `R/candidate.py`, `R/btc15_context.py`, and `R/protocol.json`.
8. `R/btc15_followup/RAPOR.md`, `analyze.py`, and `results/misses.json`, `miss_rows.json`, `matched_win_loss.json`, `no_add_controls.json`.
9. `R/btc15_ws_validation_20260921/` and `R/btc15_ws_expansion_20260921/`: reports, execution source, and results.
10. `R/btc15_execution_reserve_20260921/`: report, source, replay outputs, and `results/fable_price_limit_review.json`.
11. `R/btc15_feed_integrity_20260922/`: report, audit/check source, and results.

### C. Independent disagreement and superseded claims

12. `U/KARAR.md`, `U/RAPOR.md`, `U/HATALAR.md`, and `U/DENEY.md`.
13. `R/fable_review_20260921/OZET.md`, `RAPOR_FABLE.md`, relevant `code/` and `results/`.
14. `R/ultra_fable_synthesis_20260921/SENTEZ.md` and its checks.
15. `R/RAPOR.md` and the original study/research source, as needed to trace a claim.

Do not treat a longer or newer report as automatically correct. Trace changes in cohort, identity, phase definition, cash treatment, and event time to explain differences. If a required file is unavailable, state the exact missing path and the conclusion it blocks.

## 5. Verified starting points — audit these, do not merely repeat them

### Historical BTC15 behavior

The examined historical BTC15 cohort has **598 traded markets and 5,441 fills**, with reported cash trading contribution approximately **+$4,428.55**, excluding rebates and fixed operating costs. Reported execution roles: **4,387 maker and 1,054 taker fills**.

The corrected analysis changed 164 BTC15 phase labels. Older reports used 1,173 late additions, including 1,099 maker fills. After correcting first-fill batches and phase accounting, the relevant count is **1,150 late same-side additions**, including **1,077 maker and 73 taker**; late means `600 <= market age < 900` seconds in this calculation.

Corrected late-addition contribution:

| Subset | Fills / markets | Cash contribution | Excluding its best 10 markets |
|---|---:|---:|---:|
| All late additions | 1,150 / 274 | +$3,364.652672 | +$1.234196 |
| Maker late additions | 1,077 / 264 | +$2,901.312562 | -$29.390092 |
| Taker late additions | 73 / 57 | +$463.340110 | -$802.309970 |

These are accounting contributions of observed fills, not returns from an independently executable policy. Each row has its own top-ten exclusion set. Scaling maker late additions to $5 cash per market gave approximately -$20.98; proportional scaling is not proof that those fills were attainable at that size.

A prior 303-row receipt sample also contained hourly BTC trades. The verified BTC15 subset is **19 markets / 283 fills / 157 parent orders**, with 242 maker and 41 taker fills. Do not present all 303 as BTC15. This was a selected audit cohort, not a representative prospective sample.

### Mechanism: what is supported versus still inferred

Passive accumulation and some aggressive, risk-reducing opposite-side purchases fit the observed roles better than a single timed taker entry/addition rule. But **maker-heavy fills do not, by themselves, identify a market-making strategy or its quoting policy**. Passive directional betting, inventory-based quoting, selective liquidity provision, and common external signals can produce overlapping observations.

The earlier Fable explanation emphasized fresh bid levels and short parent fill spans. A price level appearing shortly before a fill is **not proof of the age or owner of Bosona's resting order**. An order's first/last fill time is not its placement/cancellation time. Decide how much of the claimed “fresh continuously refreshed quotes” mechanism actually survives these distinctions.

Likewise, a cash-negative completion may improve the worst terminal outcome. It is not automatically an execution mistake. Conversely, reducing risk is not proof of positive expected value. Separate observed terminal cash attribution, locked payout, risk reduction, and incremental strategy value.

Do not classify maker/taker universally by zero versus positive fee: a later BTC15 control cohort contained **34 maker pieces with positive fees**. Use actor-filtered exchange events where available; account for contract/fee regime and uncertainty. Multiple real fills may share an API identity key; a dictionary deduplication can erase real quantity. Repeated delivery of the same event is a different problem.

### Our frozen original candidate, P0

`R/protocol.json` defines an unvalidated BTC15 taker research candidate:

- First entry at age 180 seconds, 5 shares.
- Ask VWAP <= $0.55 and model probability minus fee-inclusive ask cost >= $0.05.
- One possible same-unmatched-side addition at age 600, using the same value filters.
- Opposite-side completion every 60 seconds from ages 240 through 840; completion precedes addition.
- Complete at most `min(5, abs(Up - Down))` shares when FIFO fee-inclusive pair cost <= $0.98; no overcompletion.
- Hold remaining risk to officially verified settlement.
- Intended per-market caps: 5-share clip, 10 unmatched shares, $15 purchase cash, $5 worst terminal loss.

Check intended versus implemented portfolio limits separately. A constant in a protocol is not proof of a working portfolio breaker, restart discipline, or executable stop.

P0 is preserved as a control, **not endorsed as a good imitation**. Earlier reports identified look-ahead in an execution adapter, conditional control selection, and an uncalibrated probability gate. A claimed fix that increased entries from 21 to 180 also allowed **102 of those executions above 55 cents** in a subsequent audit. Removing look-ahead and silently changing the price-protection contract are not the same correction. Trace the exact version and decision-versus-arrival semantics before comparing counts or PnL.

### BTC15 passive alternatives already tested

These are diagnostic local policies, not deployed or calibrated profitable strategies:

- **M1 bid:** passive 5-share quotes at best bid, respecting data/price/risk gates.
- **M1 bid minus one cent:** same idea with a fixed one-cent distance. One cent is not automatically the current tick size.
- **M2:** the bid policy plus cancel-and-taker inventory reduction when absolute net reaches 10 shares, in clips up to 5.
- **Reserved M2:** reserve funding for future reduction inside the same cash budget; check simultaneous pending-fill corners, not only current inventory.

The current BTC15 diagnostic loop uses market ages 30 through 839, then cancellation at 840. Quotes require a valid fresh two-token book and a decision spread <= 3 cents. Price changes cause cancel/ack/requote paths. Unsettled exposure remains part of the result.

They use the same per-market risk/cash limits. Do not mistake independent per-market simulations for a fully implemented shared portfolio budget.

### Current BTC15 sample and results

Eight assigned September 21 windows: **20:45, 21:00, 21:15, 21:30, 21:45, 22:00, 22:15, and 23:00 UTC**. Six were usable; 21:00 had a connection gap, 22:15 a missing WS trade. The 23:00 cohort was reconciled later and retains that label. Missing markets are not zero-PnL markets.

In the earlier timing study, the main conditional six-market totals were:

| Policy | Conditional total |
|---|---:|
| M1 bid | -$2.69533524 |
| M1 bid minus one cent | -$11.95 |
| M2 | -$2.7680, approximately |
| Reserved M2 | -$1.7141, approximately |
| Frozen P0 comparison | +$0.4857, approximately; only one traded market |

The latest BTC15 execution revision separates venue activation, POST response, effective cancellation, cancellation confirmation, and fill learning. Venue and client-known inventory are distinct; unknown orders retain reserves. The BTC15 decision rules were preserved; 192 legacy paths matched exactly.

There were 480 primary and 288 diagnostic challenge paths with no recorded risk-cap violation. **768 paths are repeated assumptions on six markets, not 768 independent market observations.** Execution profiles are stress assumptions, not a validated BTC15 latency distribution.

A seemingly promising M1 bid-minus-one-cent profile produced +$3.6968, but became **-$3.35** with the already-defined 500ms earlier trade-time stress and **-$3.00** with the older cancellation-notice assumption. Best-three exclusion was also negative. A different bid profile's positive result was concentrated and reversed under another clock assumption.

The current honest conclusion is: improved execution modeling, **no robust independently executable BTC15 edge established**. Calibrated economic PnL and the all-assigned-window total remain null where the evidence does not support them. Queue-front/queue-back scenarios are not mathematical PnL bounds for an adaptive inventory policy; different fills alter later decisions.

### Markout and competing explanations

In the usable BTC15 cohort, 5,240 maker BUY pieces included **22 Bosona fills / 14 parents / 5 traded markets**. Balanced parent/market-weighted Bosona 1/5/10-second markouts were approximately **+0.678 / -0.225 / -0.417 cents per share**.

Matched-maker relative 10-second difference was about +1.072 cents, but roughly **93% came from one market**, and removing a parent could reverse the sign. Same-aggressor controls provide useful identity/price checks, not independent evidence of forecasting skill. Midprice markout is not an executable liquidation price or realized strategy PnL.

Two fixed pre-observation explanations were tested: prior five-second price continuation and signed public trade flow. Neither provided robust evidence sufficient to replace P0. Do not flip a failed signal's sign or search thresholds after seeing these results without explicitly labeling a new exploratory hypothesis.

## 6. Diagnose the actual research problem

Start with a clear answer: **Are we closer to reproducing Bosona's BTC15 behavior, or mainly improving measurement without learning its decision policy? What now limits progress most?**

Separate these five questions:

1. Are the fills, amounts, roles, cash flows, merges/redemptions, initial inventory, and official outcomes correct?
2. What behavior is identified by those observations, and what remains observationally equivalent?
3. Can our policy produce orders without using Bosona's fill as its trigger or knowing the eventual winner?
4. Could our own orders receive the assumed fills with our information, latency, queue, and capital constraints?
5. Does that independently executable policy have evidence of positive net economics?

Passing a lower-level technical check does not answer the next question. Conversely, do not demand perfect knowledge of every hidden queue state before proposing a useful falsifiable experiment. Explain what can be identified or bounded with imperfect data, and where the bounds are too wide to support a decision.

Critique our research sequence itself. Have we spent too long repeating six observed windows and changing execution assumptions? Are we collecting the missing observations that distinguish plausible policies, or building increasingly detailed simulations of a mechanism we do not know? Name the highest-value missing measurement, not a generic request for “more data.”

## 7. Required substantive audit

### A. Market selection and entry

Establish the denominator: all eligible BTC15 contracts, traded and untraded, verified using official start/end, tokens, resolution source, and rules. A slug is discovery metadata, not a contract definition. Do not import hourly settlement assumptions.

Assess participation regimes and inactivity. Can clock time explain selection after accounting for liquidity, spread, volatility, price opportunity, concurrent positions and overlapping contracts? Which of those variables are actually observable before the event? One night's pattern is not a schedule.

For first exposure, distinguish a first partial fill, first-second batch, parent order and first decision. Compare side, price, elapsed/remaining time, size and prior inventory. Where submission time is unknown, identify intervals or limits rather than inventing a timestamp.

### B. Inventory management and late additions

Separate first exposure, same-side additions, risk-reducing opposite purchases, overcompletion, and reopening after a flat/merged position. Handle same-second ambiguity and parent fragmentation explicitly.

For representative wins and losses, reconstruct the prior inventory, unmatched cost, two terminal payoffs, pending reservations, and the change caused by each relevant fill. Show whether the same alleged rule would have produced both outcomes.

Use the corrected late-addition cohort. Compare winners, losers, and observed no-fill intervals under similar price, remaining time and open risk. State why **no observed fill does not mean no order or no intention to add**. Do not turn this censored sample into a labeled quote-placement dataset.

Distinguish a behavioral explanation from a profitable policy. A purchase that looked irrational under our simple probability model may reveal a bad model, unobserved inventory, or execution selection; a subsequent win alone proves none of those.

### C. The gap between P0, our passive policies, and Bosona

Give a reason-coded gap analysis: first-entry timing, side selection, quote price, 55-cent cap, probability filter, inventory state, completion priority, clip size, risk/cash constraints, cancellation/repricing, fill availability, and missing inputs.

Use the existing miss analysis where valid, and identify where maker role or censored orders invalidates its interpretation. Do not relax thresholds to mimic profitable historical fills. State which differences are intentional risk restrictions rather than defects.

Evaluate whether frequent repricing sacrifices queue position; whether inventory skew, preserving existing quotes, market-level participation, price-sensitive sizing or selective risk reduction is more explanatory. These are possibilities to discriminate, **not a menu to optimize over the same six windows**.

### D. Execution, timing and money

Inspect actual code paths, not just protocol text:

- Decision-available information versus venue-environment observations versus later accounting truth.
- Event time, local receive time, block time, request/response time and client fill learning.
- Partial and repeated fills, actor filtering, parent identity, and public complementary-token/mint routes.
- Snapshot plus delta reconstruction, tick at the relevant time, stale/out-of-order messages, reconnects and missing flow.
- Queue initialization at activation, cancellation ahead versus behind, trade depletion versus double-counted L2 size changes, and effects of our hypothetical size on the historical book.
- Post-only rejections; fills during cancellation; delayed acknowledgments and unknown-order reserves.
- Shared cash and worst-outcome limits across all simultaneously pending fills; whether hedge funding really remains available.
- Taker fees, maker fees where applicable, price protection and rebates. Do not count unallocated rebates as proven strategy income or double-count MERGE/REDEEM proceeds.

The original taker replay's future sample may legitimately be used as an execution outcome **only if the order was already committed under a fixed limit**. Using that future sample to decide whether an earlier order existed is leakage. Make this distinction concretely.

### E. Statistical and economic validity

Report parent/market/day dependence, survivor/participation conditioning, historical reuse and post-result diagnostic choices. A chronological slice that has already been inspected is not an untouched holdout. A hash-valid result can still answer the wrong question.

Use per-market/day distributions, risk-adjusted or equal-risk comparisons where meaningful, and concentration checks excluding top 1/3/10/20 markets when sample size permits. Do not give fake precision from a one-day cluster bootstrap. Separate actual PnL, observed-fill counterfactual contribution, conditional simulation, and markout.

Check whether economic acceptance thresholds are genuinely implemented. The preserved protocol asks for at least 10 complete UTC days, 100 executed markets, 50 addition markets, >=95% data coverage, fee-net positive performance and positive control difference with market/day clustered lower bounds, plus top-three exclusion. These are **necessary protocol gates, not automatic proof of edge**. Do not lower them after seeing outcomes; propose justified prospective amendments separately if the design itself needs correction.

## 8. Force a choice: at most two hypotheses, then one next experiment

Give **at most two** decision mechanisms that can run without Bosona's fill as a trigger. For each specify:

- The observable decision-time inputs and state.
- Its causal ordering and explicit action/no-action rule.
- The existing evidence it explains better than P0 or a simple passive baseline.
- Its strongest counterexample and an alternative explanation.
- The exact new observation or result that would falsify it.
- Whether our current data can test it; if not, the smallest missing artifact.

Then select **one next experiment**, not several deployments or a broad parameter search. It may be a fixed-policy paper experiment, a measurement/identification test, or an execution-model falsification if that is the genuine bottleneck. Justify why this experiment changes a real decision.

Specify BTC15 universe and assignment before outcomes, decision inputs, quote placement/preservation/repricing, size, additions, completion/hedge, exit/settlement, shared risk limits, latency assumptions, control arm and stopping conditions. If a trading policy cannot yet be specified honestly, say so and give the identification experiment instead of inventing one.

Use equal capital/risk and comparable opportunities. Preserve P0 as an archived control rather than silently rewriting it. Define data-quality failures, zero activity, unresolved outcomes and invalid simulation separately. Set prospective sample and analysis rules before collecting results. Include success, rejection and UNDERPOWERED outcomes; success cannot be “some paths made money.”

No real-money test or persistent deployment is authorized by this review. If some missing quantity cannot be learned without own live orders, identify that limitation and deliver a reviewable plan for a later operator decision; do not place orders now.

## 9. Deliverables

Lead with a short Turkish decision, then the technical evidence needed to audit it.

1. **Verdict:** what we know about Bosona BTC15, what remains conjecture, whether profitable imitation is currently supported, and the dominant obstacle.
2. **Claim ledger:** each consequential claim marked REPRODUCED, SUPPORTED BUT NOT IDENTIFIED, CONTRADICTED, NOT REPRODUCED, or MISSING DATA; exact file/function/row references, counterevidence and practical consequence.
3. **Our mistakes:** ranked concrete defects or mistaken assumptions; root cause, smallest justified correction, effect on conclusions, and how to verify. Distinguish “already fixed,” “still present,” and “not a bug.”
4. **Behavior gap:** Bosona versus frozen P0 versus current BTC15 passive/hedging policies, using the same cohort where possible. Explain both profitable and losing examples.
5. **At most two hypotheses and one experiment:** rules, controls, required data, falsification and economic acceptance. Include a compact decision loop or state machine if it makes the proposal executable.
6. **Practical next steps:** what to do first, what work to stop because it does not resolve the bottleneck, what artifact proves the first step is complete, and what remains unavailable without new observations.
7. **Reproduction/access record:** commands actually run, source/data hashes or versions, observed outputs, exact missing files, tests and limitations. If you write analysis code, include the runnable check that could catch its main failure mode.

Where terminal access exists, write `VERDICT.md`, `REVIEW.md`, `NEXT_EXPERIMENT.md` and any small necessary analysis scripts in your own review directory. If you only have repository-reading access, give the same substantive deliverables in the response and explicitly mark unexecuted checks. Do not spend the review on cosmetic refactoring or generating a large scaffolding project.

Finish by answering these questions plainly in Turkish:

- Bosona BTC15'te gözlenebilir olarak ne yapıyor?
- Biz şu anda onu hangi noktalarda yanlış veya eksik taklit ediyoruz?
- Kanıt ölçümde mi, karar kuralında mı, ekonomik avantajda mı ilerledi?
- Mevcut sonuçlarda seni en çok ikna eden kanıt ve en güçlü karşı kanıt ne?
- Tek bir sonraki işe zaman ayıracak olsak hangisi, neden, hangi sonuçta vazgeçeriz?

**Be willing to conclude that our current strategy is wrong, our simulator is misleading, or the accessible observations cannot identify the policy. Be equally willing to identify a narrow useful mechanism if it survives the counterexamples. Do not turn uncertainty into optimism, and do not turn incomplete identification into an excuse for an endless infrastructure project.**
