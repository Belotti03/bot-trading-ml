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

The exact causal chain has NOT yet been proven. Do not erase/reset
corrupted state before forensic reconstruction. V1 cron should remain
paused until this is understood.

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

Dynamic-universe fair comparison, 2024-10-15 to 2026-09-24: - Static 18:
+87.15%, DD -38.11%, Sharpe 1.155 - Dynamic Top-8: +79.74%, DD -29.51%,
Sharpe 1.081, turnover 21.61% - Dynamic Top-12: +54.05%, DD -28.00%,
Sharpe .865, turnover 14.20% Decision: dynamic universe is not a
mandatory replacement; potentially a future regime/risk module.

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

## V2 architecture target

`DataProvider/Snapshot -> Validation -> Features -> Models/Baselines -> Model Gate -> Signals -> Portfolio Construction -> Risk -> Execution Simulator -> State/Ledger -> Reporting`

Contracts: - fail-closed data validation - exclude incomplete bars -
explicit leakage/embargo controls - signal generation does not own
sizing - portfolio layer owns allocation/exposure - risk layer owns
stops/DD/cluster limits - execution owns next-open
fills/costs/slippage - state has invariants and validated writes -
live/scout should share the same core engine as backtest where possible

## Immediate next task

Before V2 implementation: 1. Keep V1 cron paused. 2. Forensically audit
actual HEAD. 3. Prove or bound the NaN propagation chain. 4. Verify
which code version produced each important historical result. 5. Audit
trade CSV definitions and benchmark comparability. 6. Produce V2
research methodology and candidate-alpha test plan. 7. Only then approve
implementation.

## New-chat rule

At the start of a new Cursor/Claude chat, read this file first, then
inspect current repository code. Never modify files unless explicitly
authorized.
