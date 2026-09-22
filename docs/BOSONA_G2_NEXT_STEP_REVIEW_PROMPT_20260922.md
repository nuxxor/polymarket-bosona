# Independent review: what should follow G2, and can we recover Bosona's selective exit policy?

You are an independent quantitative researcher and trading-systems reviewer. Inspect the repository and do substantive, reproducible analysis, then recommend our next move. This identical brief is being given independently to Ultra and Fable. Do not manufacture consensus or assume that your own earlier review was correct. Form your conclusion before consulting the other reviewer's new output.

Repository: https://github.com/nuxxor/polymarket-bosona

Local workspace, when available: `/home/taygun/Masaüstü/polymarket-bosona`

Brief date: 22 September 2026. All times below are UTC unless explicitly labeled TR. The original local HEAD was `01ea1dc6be98a8cbc57b796dc066c4e6a8404cc1`. This publication adds the G2 source, selective-exit research and selected public evidence on top of remote commit `9945a89ca238add70e397baf6e791089fdece204`; see `docs/BOSONA_G2_PUBLICATION_20260922.md` for exact inclusion and reproduction limits. The shared local workspace may still contain newer/uncommitted work. Record your actual commit, dirty-file hashes, data cutoffs and accessible inputs. Do not silently substitute the older `add159d` experiment for the current bot. If a required artifact is absent, list it, continue with the evidence you can inspect, and clearly limit the resulting claims.

## Objective and the question you must challenge

We want to understand Bosona's **BTC Up/Down five-minute** behavior well enough to construct an independently executable small-account policy. We are especially interested in when it keeps directional inventory, adds to it, reduces it through an opposite purchase, or crosses through flat into the opposite direction. We ultimately care about executable net economics, not superficial similarity in fill counts.

We have progressed from several unsuccessful or inconclusive strategies to G1/G2, a small passive quoting baseline with inventory controls and improved measurement. The operator suspects that a few evidence-based changes—especially selective active risk reduction—could meaningfully improve it. **Do not accept the premise that only a few tweaks remain.** Determine whether that is plausible, whether entry/quoting/execution is the bigger problem, or whether the current baseline is still structurally unlike Bosona.

The desired outcome is not a generic new RSI strategy or an automatic stop-loss invented because a recent trade lost. It is a defensible account of what Bosona does, the strongest implementable implication of that account, and the smallest decisive next experiment. A successful unrelated strategy must be labeled as such.

Scope: BTC5m only. Exclude Jev/LLM experiments and other assets/durations. This assignment authorizes **research and isolated offline analysis**, not operational trading changes. Do not place/cancel orders, start/stop/restart services, deploy, change live/shadow parameters, reset budgets, or execute launch scripts. Do not access or output credential values, keys or wallet material. Public read-only queries are appropriate. Preserve existing artifacts; write your analysis to a reviewer-specific output directory. Read applicable repository instructions and the complete root `plan.md` first.

## What G2 actually is

The authoritative current source package is `lanes/g_continuous/identity_fix/bot/`, not an arbitrary root `bot/ab.py` or an older lane.

- G2 is the operator's name for an **infrastructure revision of G1**, not a newly optimized strategy. Internal lane/path names still say G.
- Source `ab.py` SHA256: `25fca69d4ad75a3a28db9f62903f4c300a8adafdc7e923bc942f87eb6699d64c`.
- Unchanged `g_policy.py` SHA256: `fbac759df25cecf10ea01bbf9db9da5e07dd90f3b33e844125c51e434eaf2f61`.
- Five-share clips, post-only maker orders. Both sides eligible; quote one **cent**, not necessarily one tick, below best bid, rounded down to the actual tick. No cheap-side/favorite/RSI entry gate.
- Net directional lead limited to five shares, including relevant outstanding/uncertain orders. Completion size cannot intentionally overbuy into new reverse exposure; exchange minimum size can prevent completing small residuals.
- New directional risk before t240; reducing maker quotes before t290. Quotes may be retained from best bid to two cents behind it. Verify the actual maintenance/cancellation code rather than inferring it solely from this summary.
- Cumulative spend/reserve cap of $10 **per side per market**, plus a separate account-level loss guard for the operator's existing $10 experiment budget. These are different limits. Budget guard accounts for unresolved risk and uncertain orders; it is not merely a check after a market settles.
- No universal 98-cent pair cap. A permitted opposite maker fill can lock a loss. **Selective taker risk reduction has not been implemented.** No prospective rebate is credited.
- G2 fixes a real API inconsistency: the correct Up token was returned with `outcomeIndex=999`, closing the reconciliation gate and suppressing subsequent quotes. Normalization now uses validated market/condition/token identity. Identity conflicts still fail closed; raw fills and multiplicity are preserved.

The operator ran the prepared update command. Archived evidence confirms a new LIVE start on 22 September at **12:07:30 UTC / 15:07:30 TR**, successful reconciliation at 12:07:32, unchanged strategy and original budget/RUN bytes, and two active recorders. This is a dated snapshot, not a claim that you inspected current runtime. No new live recurrence of the 999 anomaly had occurred at that verification; the fix was tested by replaying the actual historical incident.

Inspect `protocol.json`, `g_policy.py`, `g.py`, the relevant paths in `ab.py`, `G_RELEASE.json`, and the identity-fix README/tests. Distinguish inherited A–F code from the G path that actually executes. A source file existing is not proof that its branch is live.

## Evidence map and reading order

Use primary inputs and executable calculations to audit these reports, not as unquestionable authority.

1. **Current patch and runtime identity:** `lanes/g_continuous/identity_fix/README.md`, `runtime_before_operator.json`, `runtime_after_operator.json`, `real_public_replay.json`, `remote_tests.json`, and `bot/` under that directory. Do not execute `operator_resume.py --operator-restart` or any `londra_*` launcher.
2. **First G1 pilot, including where its profit came from:** `docs/BOSONA_G_ILK_CANLI_OKUMA_20260922.md`; primary calculation and evidence under `lanes/g_continuous/validation/g1_first_pilot/`.
3. **Own G versus Bosona on identical recent markets:** `data/analysis/g1_comparison_20260922/CASE.md`, `REPORT.md`, `protocol.json`, `latest.json`, `paths.json`, `study.py`, `check.py`, `cuts/`, `receipts/`, and `operational_evidence.json`. Inspect the actual local cutoff: a scheduled end time does not mean collection is complete. A later London snapshot might not have been copied locally.
4. **Latest selective-exit analysis:** `data/analysis/g1_selective_exit_20260922/REPORT.md`, `analyze.py`, `results.json`, `verification.json`. Audit its parent grouping, excluded groups, integer inventory, feature joins, and interpretations.
5. **Receipt-backed historical parent/role research (R1):** `data/analysis/btc5m_parent_research_20260921/manifest.json`, `report.json`, `summary.json`, `analyze.py`, `check.py`, `activity.json`, `full_activity/`, `receipts/`, `contexts.json`, and `fetch_manifest.json`; narrative `docs/BOSONA_EMIR_RISK_SONUCLARI_20260921.md`.
6. **Broader history and features:** `data/analysis/bosona_gec_20260921/` and `data/analysis/bosona_derin_20260921/`; extraction/feature logic in `analiz/izleme/bosona_gec_arastirma.py` and `analiz/izleme/bosona_derin.py`. The old `fill_ledger.json` still has a known multiplicity issue: do not treat it as the corrected truth merely because the fix is documented elsewhere.
7. **Earlier independent reviews and synthesis:** `docs/BOSONA_BTC5M_INDEPENDENT_REVIEW_20260921.md`, `docs/BOSONA_UC_INCELEME_SENTEZI_20260921.md`, and `data/analysis/bosona_review_synthesis_20260921/calculations.json`. Preserve worthwhile hypotheses and counterexamples; do not simply repeat their conclusions.
8. **Execution-model limitations and subsequent instrumentation:** `docs/BOSONA_M6_UYUSMAZLIKLAR_20260922.md`, `docs/BOSONA_M7_OLCUM_20260922.md`, `docs/BOSONA_M7_CIFT_KAYIT_20260922.md`, `docs/BOSONA_G_HAZIRLIK_20260922.md`. Earlier replay models both invented fills and missed actual fills; measurement improved afterward, but no exact public-L2 queue simulator has been established.

Inspect extraction manifests and the data inventory before declaring inputs unavailable. The historical extractor points to `/home/taygun/Masaüstü/polymarket/data/tape`; prior work described roughly 18.65 GB of raw tape. Compressed snapshots/caches may already avoid a full re-extraction. Earlier archives may extend beyond the main eight-day cohort. Verify what actually exists in your environment; do not assume a GitHub clone contains external raw files.

## Reported findings to verify, not assume

### Available history

The main historical cohort is `[2026-09-13 00:00, 2026-09-20 22:30)` UTC: **2,286 calendar slots**, **1,842 observed BTC5m markets**, and **19,768 BUY records after preserving real multiplicity**. The older derived ledger had 19,761. Corrected reported trading PnL is approximately +$8,313.23, excluding rebates/fixed costs; verify its accounting basis before using it. Observed markets are not the full assigned calendar.

R1 separately audited **137 markets / 2,066 BUY records**, including a 64-market sample of eight hash-selected observed markets per UTC day, a selected late-addition cohort, and diagnostic cases. These cohorts overlap. Do not combine them into a representative sample or treat previously researched days as clean out-of-sample evidence. Later 21–22 September observations exist separately.

### Current selective-exit result

In the 64-market sample, 305 filled parents were identified. The latest analysis classified 262 first-filled public-second parent groups and excluded 43 ambiguous groups/parents from that classification:

| First observed group's role | Open | Add to same direction | Reduce | Cross through flat | Total |
|---|---:|---:|---:|---:|---:|
| Maker | 67 | 101 | 48 | 14 | 230 |
| Taker | 2 | 2 | 26 | 0 | 30 |
| Mixed maker/taker | 0 | 0 | 2 | 0 | 2 |

The 26 taker reductions span 22 markets; median fraction of the pre-existing net position closed is **99.921%**, with 15 closing at least 99%. Eight additional taker parents are in the ambiguous set. Public fill ages range **24–286 seconds**, median152; fee-inclusive cash cost per opposite share ranges about **0.0425–0.9720**, median0.5772. These are observed executions, not known order-placement times, full submitted sizes, or proven trigger thresholds.

Only **6/26** currently have the combined book/reference/spot/TWAP/time context accepted by that analysis. **This is NOT proof that the raw archive contains only six usable cases.** The existing feature table was designed for late fills; unnecessarily requiring every feature can also create a hidden selection filter. Determine how much early/missing context can be recovered from existing inputs and how much is genuinely unrecorded. Do not use an inherited `exchange_age` field as exact exchange/decision time without tracing its source; some such fields are observed public WS timestamps.

The earlier first-reduction local test found 32 valid first reductions,23 markets without an observed reduction,9 ambiguous among the64. Fifteen valid first reductions were taker;10 of those cost more than $1 per pair even with the cheapest eligible old lot. Their local hold-versus-close contribution was +$273.91. Across all55 evaluable markets, the local contribution was +$165.37, becoming −$153.79 without the best three; day-block uncertainty crossed zero. **Economic benefit of a transferable exit policy is not established.** The 15 first reductions and26 reducing parent groups are different denominators.

### Recent counterexamples and our own results

- Market start `1790074800` (22 September11:00UTC): Bosona bought249Down@0.11 at public age201, one maker parent; no later observed opposite purchase/sale, result−$27.39. G lost$2.30 with10Up/15Down. G's reconciliation gate was closed from aboutt27.7 through the window by the999 anomaly; this was not an uninterrupted test of its policy.
- `1790073300` (10:35UTC): Bosona first accumulated112.195381Down, then bought10Up as maker att114 and102.19Up as taker att126, almost flattening. Opposite purchases improved the same-position outcome by$11.8406, yet total market PnL remained−$27.4278.
- `1790070900` (09:55UTC): Bosona crossed fromDown toUp and subsequently increasedUp. Six late fills came from one parent, not six independent decisions.
- G1's first six-market pilot returned+$9.206315, but the sum of each final position's worst terminal payoff was−$5.797970; realized payouts were$15.004285 above that sum. Five markets settledUp. This is a final-inventory decomposition, not a counterfactual strategy PnL or a proof of alpha.
- A later user screenshot showed20Up costing$8.50 and15Down costing$8.85. Down settlement yields−$2.35;Up yields+$2.65. Buying5Down at0.99 would lock−$2.30 before fees: late flattening can salvage only cents while eliminating upside. Do not equate hedging, adverse-selection prevention, and profit creation.

## Required investigation

### A. Audit whether we are actually near the target

Compare G2 with Bosona's observable behavior: first fill timing/side, quote/execution prices, maker/taker roles, distinct-parent changes, size relative to existing inventory, holding duration, reopening after flat, and exposure paths. Normalize carefully; a different-size dollar PnL comparison is not model superiority. Reconcile operational interruptions separately from strategic choices.

Is G2 a useful controlled baseline or a materially different strategy? Which apparent progress is measurement improvement, which is behavioral convergence, and which has economic support? Challenge the suggestion that adding an exit rule is necessarily the next highest-value change.

### B. Recover selective-exit evidence from the archive

Do actual bounded reconstruction beyond the already summarized6/26 wherever accessible data permits. Include taker reductions, maker reductions, additions/reversals, and comparable periods with no **observed reducing fill**. Do not label the latter “decided not to hedge”; unfilled/canceled quotes are hidden. Cover winners and losers, early and late periods. Preserve the original cohort and explicitly identify any expansion and its selection method.

Before using future outcomes, compare conditions known before the candidate action: net inventory and its age, attainable opposite ask versus held-token bid, spread/depth and recent repricing, outstanding-order uncertainty where observable, recent BTC/official-reference movements, remaining time, and cash/risk scale. Distinguish an inventory-sized taker close from a coincidental complementary fill or remaining portion of an older order. Ask whether rounding/minimum-size rules explain near-flat quantities. Recover histories around events and suitable controls rather than rescreening dozens of unrelated indicators.

Consider and try to falsify a small number of mechanisms: inventory/risk thresholds, deterioration in executable exit value, reversal of relative value, settlement-reference changes, time-dependent unwind, reopening/quote-regime transitions, or reward/fee economics. You may find a better explanation. Historical cost, a stop threshold, or a fair-value model must earn its place in the evidence; none is supplied as the correct answer.

### C. Separate behavior, causation, and implementability

Represent terminal wealth as `N + U*Y + D*(1-Y)` and net direction as`U-D`, while tracking operational liquidity separately. Opposite buying reduces exposure only up to the pre-existing imbalance; excess opens new opposite risk. Preserve pre-window inventory, real cash/token movements, exact multiplicity and ambiguous ordering.

For a fixed existing position, the local close-versus-hold difference is `q*(1-p_opposite_cash-Y_held)`. The final outcome is an evaluation label only. A positive actor-conditioned difference does not tell us when to trade independently. Do not replay future Bosona actions unchanged into counterfactual inventories. Paired FIFO profit is not the marginal benefit of pairing. Compare opposite buying and selling the held token using actual executable costs where available.

Account for taker fees, actual depth, timestamp uncertainty, partial fills, cancel/ack latency and adverse selection. Do not turn price touches or unexplained L2 size decreases into guaranteed maker fills or cancellation credit. Do not claim an exact Bosona cancel TTL, quote owner or queue rank from aggregate books. Rebates must be separated into actual cash, defensible attribution and assumptions; Bosona's tier is not automatically our small account's tier. Verify official market/fee/reward rules if using them economically.

Avoid fishing for the best threshold on repeatedly examined history. Report exclusions, selection sensitivity, concentration, day effects and failure cases. Missing observations are not zeros. A losing trade alone is not adverse-selection evidence; examine post-fill price behavior and the execution mechanism.

## What to deliver

Produce a decisive independent judgment, not just a general research plan. Save a report under `docs/BOSONA_G2_NEXT_REVIEW_<REVIEWER>_20260922.md` and reproducible calculations/checks under a distinct reviewer-specific directory in `data/analysis/`. Use your reviewer name to avoid overwriting the other review. Final human-facing report and summary should be **Turkish**; code may be English.

Include:

1. A clear answer: **Are a few modifications plausibly enough, or is the model still missing a larger mechanism? What should we do next?** Calibrate confidence to the evidence.
2. A verified inventory of accessible days/markets/fills/parent identities and context coverage. Distinguish existing-but-unprocessed, recoverable, inaccessible-in-this-environment, and genuinely absent data. Audit the6/26 bottleneck rather than repeating it.
3. The strongest evidence for and against selective taker reduction as the next change. Show concrete closing and carrying counterexamples with source paths, identities and causal-time limits. Report any corrected numbers and the original error.
4. At most three ranked mechanisms. For each, specify its observable inputs, prediction, supporting evidence, contradictory evidence, and what would reject it. If a trigger remains unidentified, say exactly why.
5. **One prioritized next experiment or patch candidate**, with a precise decision rule if justified, the needed data, a fair baseline/control, execution assumptions, budget/exposure comparability, and predeclared evaluation/failure criteria. Label invented research thresholds as such. Distinguish “can code now,” “can test offline now,” and “ready for an operator-controlled live trial.” No deployment in this assignment.
6. Reproducible checks for nontrivial calculations and a concise list of what you actually ran. Some existing checks write into frozen output directories or expect London; inspect them before running and isolate outputs. No claim that code or runtime was verified merely because a report says so.

Finish with a short operator-facing answer: **what is worth preserving, what should change first, what should stop, and the strongest concrete clue we had overlooked**. If the best conclusion is that the next useful change is not a selective exit, say so. If we already have enough data to derive and falsify a candidate, do that work rather than defaulting to “collect more.” If we do not, identify the smallest specific missing measurement that changes the decision.
