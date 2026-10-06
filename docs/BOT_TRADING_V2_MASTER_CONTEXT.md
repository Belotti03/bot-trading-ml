# BOT TRADING ML --- MASTER CONTEXT V2

## Purpose

Canonical handoff of the ongoing work on `Belotti03/bot-trading-ml`. V1
is a benchmark/research artifact. V2 should be a clean reconstruction
informed by V1, not a blind patch.

## Collaboration

-   ChatGPT: independent research/audit layer; challenge conclusions and
    review Claude/Cursor work.
-   Claude/Cursor: repository-aware quant researcher/developer; inspect
    the real repo and implement only after research/design approval.
-   The repository is the long-term memory; chats are temporary.
-   Distinguish VERIFIED / INFERRED / HYPOTHESIS / UNKNOWN.

## Current repository

Repository: https://github.com/Belotti03/bot-trading-ml Claude verified
on 2026-09-30 that the public repo can be cloned read-only. HEAD
checked: `bd4359f`. Reported contents: 112 tracked files, 18 workflows,
backtest/portfolio results, dynamic-universe CSVs, ML validation report,
trading log, tracked **pycache**, tracked model binaries, 187 commits on
main.

Updated 2026-10-06, VERIFIED: HEAD on `origin/main` is `640ca0e`, 193
commits on main, 111 tracked files, 18 workflows. `__pycache__` is no
longer tracked: the seven tracked `.pyc` were removed from the index in
`06006e3`, which also added the project's first `.gitignore`. New files
since the 2026-09-30 snapshot: `safe_state.py` (shared validation and
recency policy), `tests/test_nan_guards.py` (50 tests), `.gitignore`,
`docs/V2_RESEARCH_ROADMAP.md`.

## V1 active flow

`model_engine.py -> scout_signals.json -> main.py -> portfolio_state.json + Telegram`
This is a simulated/scout portfolio, not broker execution.

Universe: BTC-USD, ETH-USD, NVDA, AMD, MSTR, COIN, TSM, PLTR, ARM, SMCI,
TSLA, META, AMZN, GOOGL, AAPL, MSFT, QQQ, GLD. Daily timeframe. Model
family: XGBoost + LightGBM + RandomForest ensemble. Current HEAD
`model_engine.py` was verified to use 4 features: Returns, SMA_10,
SMA_50, RSI. Earlier research/backtests used a 6-feature set including
Return_5d and SMA_ratio. Historical results must therefore be tied to
exact code provenance before comparison.

V1 thresholds: long \> .55; high conviction \>= .60; exit \< .45.
Position caps: 30% / 40%. Max new positions: 5 per signal date. V1 also
used ATR stops/trailing, SPY SMA200 macro filtering and a circuit
breaker. Live/scout and backtest implementations are not identical.

## Critical V1 NaN incident

At HEAD `bd4359f`, Claude verified: - `portfolio_state.json`:
`cash = NaN`, `day_start_val = NaN` - `scout_signals.json`: NVDA price =
NaN - 16 NaN occurrences reported - corruption starts at/around commit
`18d54d7` on 2026-09-26 and persists through following commits - three
open positions reported: PLTR, COIN, AMZN

RESOLVED 2026-10-04 to 2026-10-06. The causal chain is proven, the
guards are merged, the state is reconstructed and the fix is validated
in production. Full detail in `docs/RESEARCH_LOG.md`; summary:

-   Root cause: `scout.get(t, {}).get("price", default)` returned a
    present-but-NaN value, because the default only fires on a missing
    key. The ML exit branch had no price guard, so `cash += qty * NaN`.
    Stop branches never fired because comparisons with NaN are False.
-   Guards merged in PR #1 (`5177e86`): single validated bar for
    features/price/`asof`, fail-closed state schema, shared
    producer/consumer recency policy, atomic writes with
    `allow_nan=False`.
-   State reconstructed in `40bba21` from verified history, with the
    single irrecoverable value (TSLA exit price) supplied externally and
    its temporal correctness proven.
-   Validated in production on 2026-10-06 in the exact post-20:00 ET
    window that previously failed: zero NaN, `asof` on all 18 tickers.

**V1 cron pause is therefore REVOKED.** `run_bot.yml` is active again as
of 2026-10-05; `retrain.yml` remains `disabled_manually`. The standing
rule that corrupted-state evidence must not be erased remains in force:
the incident is reconstructable from git history and must stay so.

## Key V1 results already obtained

Exact portfolio run #10: - Initial €10,000 - Final €7,980.02 - Return
-20.20% - Max DD -45.57% - Sharpe -0.2496 - 302 trades - Win rate
49.34% - Profit factor .8787

Previous corrected run #9: - Final €9,276.17 - Return -7.24% - Max DD
-45.33% - Sharpe \~0.01 - 279 trades - Win rate 49.82% - PF .956

Earlier diagnostics: - ML ON: +16.54%, DD -35.35%, Sharpe .39 - ML OFF:
+117.56%, DD -48.60%, Sharpe .87 - B&H: +73.08%, DD -25.44%, Sharpe 1.02
These are historical experiments and require provenance checks before
new conclusions.

Target-horizon screening (LogisticRegression, not final V1 ensemble): -
1d: accuracy 50.65%, AUC .5046, Brier .2554, logloss .7051 - 3d: 50.28%,
.4930, .2632, .7249 - 5d: 49.26%, .4908, .2709, .7461 - 10d: 49.45%,
.4895, .2822, .7854 No meaningful predictive skill demonstrated.

Dynamic-universe fair comparison: **DECLARED INVALID AND NOT COMPARABLE
on 2026-10-06 by independent audit 002**, see
`docs/audits/AUDIT_RESULT_002.md`. Do not quote these figures as
evidence and do not call this comparison fair. The decision it supported
is suspended, not reversed.

Three defects, all VERIFIED:

1.  The "Static 18" leg is not a buy & hold. `static_equal_weight()` in
    `dynamic_universe_final_comparison.py` averages the 18 asset returns
    every day, which is an equal-weight portfolio **rebalanced daily**,
    and then hardcodes `g["Turnover"]=0.0`.
2.  The comparison is therefore not cost-matched. The summary CSV
    assigns the static leg an average daily turnover of 0.21% against
    21.61% for Top-8, while the implied rebalancing is the same.
3.  The selection uses day `d` close and volume in full, selects on day
    `d`, and credits the close-to-close return from `d` to `d+1`, with
    no signal lag and no next-open execution.

Corrected figures as actually recorded in
`dynamic_universe_fair_summary.csv`, for provenance only and not as
evidence: Static 18 total return +87.15%, **CAGR +38.11%, max drawdown
-27.20%**, Sharpe 1.1551, 487 observations. A figure withdrawn from this
entry is recorded in the "Do not do" list of `docs/RESEARCH_LOG.md`.
Top-8 +79.74%, CAGR +35.27%, DD -29.51%, Sharpe 1.0805, turnover 21.61%.
Top-12 +54.05%, CAGR +24.93%, DD -28.00%, Sharpe 0.8652, turnover
14.20%.

The same summary CSV contains **two different rows for TopK 18**.
EXPLAINED 2026-10-06 by audit 003 and independently confirmed in
`dynamic_universe_fair_comparison.py`. They are two functions, plus a
cost bug, not two candidate true benchmarks.

- 487 observations, +87.15%, turnover 0.205%: `simulate(panel, k=18)`.
  Days where all 18 have Score and NextRet; top-18 of 18 is equal-weight
  on the complete-panel calendar.
- 711 observations, −16.26%, DD −57.13%, turnover 0:
  `static_18(with_costs=True)`. Mean NextRet on every date with at least
  one asset, including crypto weekends. The comment says one initial
  cost; the code subtracts `COST_PER_SIDE` from **every** row.
  VERIFIED: `(1-0.0015)**711 ≈ 0.344` applied to the no-cost equity
  ≈ 8373, matching the CSV.

R0.1 attributes each row to its function. It does not elect a true
static benchmark. Both remain invalid as buy & hold. The figure
historically cited in these documents is the 487-day row.

## V1 audit conclusions

Confirmed or strongly indicated: - live/backtest divergence -
feature/data/timing mismatch - current directional ML has not
demonstrated robust skill - probabilities are not demonstrated as
calibrated - sizing is aggressive - exposure/correlation controls are
limited - data failures can corrupt persistent state - research has
repeated on overlapping periods, creating data-snooping risk - benchmark
comparability needs audit Do not treat every hypothesis as proven until
code/results are checked.

## V2 objective

Search for a genuine, robust quantitative/predictive edge. Do NOT assume
ML must be the core. Candidate families: trend following,
momentum/cross-sectional momentum, mean reversion, breakout,
volatility/regime signals, ranking, volatility forecasting,
meta-labeling, pooled ML, and other economically/statistically justified
signals. Trend/momentum are candidate hypotheses and baselines, not an
alternative objective. ML must demonstrate incremental value versus
appropriate non-ML baselines.

## V2 research hierarchy

1.  Clean data and point-in-time rules
2.  Reproduce/characterize V1
3.  Establish baselines: cash, equal-weight B&H, SPY/QQQ where
    appropriate, simple trend/momentum, volatility-targeted baseline, V1
    without ML, V1 with ML
4.  Test candidate alpha families
5.  Test incremental ML value
6.  Portfolio construction/risk
7.  Locked holdout / forward validation
8.  Shadow paper trading
9.  Only later consider real capital

Selection must consider net return, drawdown, Sharpe/Sortino/Calmar,
turnover, costs, beta/exposure, rolling stability, parameter
sensitivity, cost sensitivity, leave-one-asset-out and
placebo/counterfactual tests.

Two points that were UNRESOLVED against roadmap v2 are settled by the
adopted v4 plan. First, item 3 above keeps simple trend/momentum as a
**canonical trend baseline** in Phase 1, distinct from hypothesis H2
research. Second, live and backtest share one identical core with
separate adapters; "one identical core" remains UNKNOWN as a property
until the conformance suite in Phase 1 passes. Plugin lifecycle:
experimental / validated / deployable, with confirmatory shadow occupancy
limited to one frozen strategy.

## V2 architecture target

`DataProvider/Snapshot -> Validation -> Features -> Models/Baselines -> Model Gate -> Signals -> Portfolio Construction -> Risk -> Execution Simulator -> State/Ledger -> Reporting`

Contracts: - fail-closed data validation - exclude incomplete bars -
explicit leakage/embargo controls - signal generation does not own
sizing - portfolio layer owns allocation/exposure - risk layer owns
stops/DD/cluster limits - execution owns next-open
fills/costs/slippage - state has invariants and validated writes -
live/scout should share the same core engine as backtest where possible

## Immediate next task

Before V2 implementation: 1. ~~Keep V1 cron paused.~~ CLOSED and
revoked on 2026-10-06, see the NaN section above; `run_bot.yml` is
active and `retrain.yml` is `disabled_manually`. 2. Forensically audit
actual HEAD. 3. Prove or bound the NaN propagation chain. 4. Verify
which code version produced each important historical result. 5. Audit
trade CSV definitions and benchmark comparability. 6. Produce V2
research methodology and candidate-alpha test plan. 7. Only then approve
implementation.

Progress as of 2026-10-06: items 1, 2 and 3 are closed. Item 1 was
closed by resolution rather than by continued pause, see the NaN section
above. Item 6 is closed as a **plan** by `docs/V2_RESEARCH_ROADMAP.md` version
4, adopted 2026-10-06 after audit 004 APPROVED. It is not an executable
protocol. Item 6 no longer blocks planning; Phases 0A–0C and the freeze
still block candidates. Mandates remain Filippo's to close.
Item 4 is tracked there as R0.1. Item 5 is tracked as R0.1 for the trade
CSV definitions and as Phase 1 for benchmark comparability; note that
the v1 labels R0.4 and R0.5 no longer exist after the roadmap was
restructured into Phases 0A, 0B and 0C.

Two findings recorded on 2026-10-06 reorder that hierarchy. They were
corrected by audits 001–003 and are stated here in the form required by
roadmap v4 §1 and §2.1. They are not a substitute for the evidence
hierarchy.

First, **one** Sharpe has a computed IID interval that contains zero:
SR 1.155, q 252, T 1.941 (the 487-observation row, 2024-10-15 to
2026-09-24) gives SE 0.7187 and 95% interval [-0.254, 2.564]. The
plural claim that individual Sharpes on this window are not
distinguishable from zero is **INFERRED, not VERIFIED**. Every other
quoted Sharpe must be recomputed with its own duration, frequency and
dependence. `q = 252` is an equity-calendar approximation, not a global
constant. IID intervals are not sufficient; HAC or block bootstrap is
required before a claim is used as evidence. Paired differences on the
same days can have far smaller variance than either Sharpe; whether any
specific comparison is decidable is UNKNOWN until those tests are run.

Second, the recent window is INFERRED contaminated for strategies,
assets and parameters already explored, and cannot be presented as a
clean holdout. Extent UNKNOWN until R0.1. Sources of evidence are not
interchangeable. Nested walk-forward, frozen external markets and
leave-one-cohort-out are **robustness** evidence: they can block
promotion to validated/deployable, they cannot grant it. An unused
historical block is confirmatory only if R0.1 proves it was quarantined.
A paired test on data already used to design the hypothesis is
comparative inference, not confirmation. Experimental paper runs are
development. The confirmatory shadow cohort is at most one frozen
strategy, peeking sealed until Filippo reveals. See
`docs/V2_RESEARCH_ROADMAP.md` §1.

## New-chat rule

At the start of a new Cursor/Claude chat, read this file first, then
inspect current repository code. Never modify files unless explicitly
authorized.
