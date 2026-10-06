# R0.1 PROVENANCE LEDGER

Forensic only. Written 2026-10-06. Authorised independently of Phase 0A.
Does not adopt thresholds, universe, engine, or any strategy conclusion.

Scope, per audit 004: provenance per file; attribution of the two TopK-18
rows; inventory of `auto_adjust`, feature sets, and costs; the
`features.py` `dropna()` axis. No strategic conclusions.

HEAD at time of writing: local `06006e3`, `origin/main` `640ca0e`. No
raw snapshot exists in the repository. No artefact here is reproducible
from source market data.

## 1. Inventory

VERIFIED: 52 CSV files.

| Family | Count | Producing script (current tree) |
| --- | --- | --- |
| `backtest_results/` | 20 | `backtest_oos.py` |
| `portfolio_backtest_results/` | 21 | `portfolio_backtest.py` |
| dynamic-universe, repo root | 10 | `dynamic_universe_screen.py`, `dynamic_universe_fair_comparison.py`, `dynamic_universe_final_comparison.py` |
| `trading_log.csv` | 1 | production logger, not a research result |

Scripts that write CSVs **not present** in the tree (artefacts absent):
`portfolio_target_horizon_ml_screen.py` (`horizon_screen_*.csv`),
`portfolio_ml_ab_test.py`, `portfolio_ml_off_robustness.py`,
`portfolio_stop_sensitivity.py`, `portfolio_trailing_stop_sensitivity.py`,
`portfolio_temporal_robustness.py`, `portfolio_buy_hold_benchmark.py`,
`portfolio_buy_hold_period_benchmark.py`,
`portfolio_target_horizon_analysis.py`,
`portfolio_target_horizon_analysis_v2.py`,
`portfolio_asset_selection_analysis.py`,
`portfolio_asset_selection_analysis_corrected.py`.

UNKNOWN: which commit, if any, produced the quoted ML ON / ML OFF and
AUC figures. Those complete artefacts are not in the repository.

## 2. Per-file windows

Date columns as stored. Observation count is row count after the header.

### `backtest_results/` — `backtest_oos.py`

Costs in current script: `FEE_RATE = 0.001`, `SLIPPAGE_RATE = 0.0005`.
Download: `auto_adjust=False`.

| File | Rows | First | Last |
| --- | --- | --- | --- |
| AAPL_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| AMD_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| AMZN_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| ARM_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| COIN_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| GLD_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| GOOGL_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| MSFT_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| MSTR_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| NVDA_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| PLTR_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| QQQ_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| SMCI_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| TSLA_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| TSM_oos_predictions.csv | 332 | 2025-05-21 | 2026-09-16 |
| META_oos_predictions.csv | 325 | 2025-06-02 | 2026-09-16 |
| BTC-USD_oos_predictions.csv | 561 | 2025-03-05 | 2026-09-17 |
| ETH-USD_oos_predictions.csv | 561 | 2025-03-05 | 2026-09-17 |
| all_trades.csv | 705 | 2025-03-05 | 2026-09-15 |
| backtest_summary.csv | 18 | (none) | (none) |

`backtest_summary.csv` has no date column. It is 18 per-ticker rows of
InitialCapital, FinalEquity, TotalReturn, MaxDrawdown, Sharpe, Trades,
WinRate, ProfitFactor, BuyHoldReturn.

### `portfolio_backtest_results/` — `portfolio_backtest.py`

Costs in current script: `FEE_RATE = 0.001`, `SLIPPAGE_RATE = 0.0005`.
Download: `auto_adjust=False`. Thresholds in current script:
`LONG_THRESHOLD = 0.55`. Features: six-name `MODEL_FEATURES` (see §4).

| File | Rows | First | Last |
| --- | --- | --- | --- |
| AAPL_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| AMD_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| AMZN_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| ARM_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| COIN_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| GLD_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| GOOGL_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| MSFT_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| MSTR_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| NVDA_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| PLTR_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| QQQ_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| SMCI_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| TSLA_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| TSM_predictions.csv | 331 | 2025-06-02 | 2026-09-24 |
| META_predictions.csv | 324 | 2025-06-11 | 2026-09-24 |
| BTC-USD_predictions.csv | 561 | 2025-03-15 | 2026-09-26 |
| ETH-USD_predictions.csv | 561 | 2025-03-15 | 2026-09-26 |
| portfolio_equity.csv | 562 | 2025-03-14 | 2026-09-26 |
| portfolio_trades.csv | 302 | 2025-03-17 | 2026-09-24 |
| portfolio_summary.csv | 1 | (none) | (none) |

`portfolio_summary.csv` (run #10 figures, internally consistent):

InitialCapital 10000, FinalEquity 7980.019492172576, TotalReturn
-0.20199805078274236, MaxDrawdown -0.45568075110848305, Sharpe
-0.24960162356543775, Trades 302, WinRate 0.49337748344370863,
ProfitFactor 0.8787340930579208.

UNKNOWN: the producing commit of this exact CSV. The current
`portfolio_backtest.py` is consistent with the columns and the trade
count, not proven to be the bit-identical producer.

### Dynamic-universe root files

| File | Rows | First | Last | Current producer |
| --- | --- | --- | --- | --- |
| dynamic_universe_equity_k4.csv | 1194 | 2021-12-21 | 2026-09-24 | `dynamic_universe_screen.py` |
| dynamic_universe_equity_k6.csv | 1194 | 2021-12-21 | 2026-09-24 | same |
| dynamic_universe_equity_k8.csv | 1194 | 2021-12-21 | 2026-09-24 | same |
| dynamic_universe_equity_k10.csv | 1194 | 2021-12-21 | 2026-09-24 | same |
| dynamic_universe_equity_k12.csv | 1194 | 2021-12-21 | 2026-09-24 | same |
| dynamic_universe_screen_results.csv | 6 | (none) | (none) | same; k in {4,6,8,10,12,18}; k=18 has 1766 observations, unlike the equity files |
| dynamic_universe_latest_ranking.csv | 2 | (none) | (none) | same |
| dynamic_universe_fair_comparison.csv | 8 | 2024-10-15 | 2026-09-25 | `dynamic_universe_fair_comparison.py` |
| dynamic_universe_fair_summary.csv | 4 | 2024-10-15 | 2026-09-25 | same script, a subset of the 8-row file |
| dynamic_universe_final_comparison.csv | 3 | 2024-10-15 | 2026-09-24 | `dynamic_universe_final_comparison.py` |

### Production

`trading_log.csv`: 27 rows after header. Dates 2026-07-31 to 2026-08-24
on the `Data` column (first four rows inspected; last date from full
scan in audit 002). Not a research result.

## 3. Two TopK-18 rows

Source file: `dynamic_universe_fair_summary.csv`, produced by
`dynamic_universe_fair_comparison.py` writing that path (current tree).
The 8-row `dynamic_universe_fair_comparison.csv` is the full grid.

VERIFIED in current source:

| Row | Function | Filter | Costs in code | CSV |
| --- | --- | --- | --- | --- |
| 487 obs, +87.15%, turnover 0.205%, Sharpe 1.1551, end 2026-09-24 | `simulate(panel, k=18, with_costs=True)` | skip day if `len(day) < k` after dropna on Score and NextRet | `turnover * COST_PER_SIDE` | summary row 3; fair_comparison row `18,True,18715.35,...487` |
| 487 obs, +87.43%, same turnover, Sharpe 1.1575 | `simulate(..., with_costs=False)` | same | none | fair_comparison only |
| 711 obs, −16.26%, DD −57.13%, turnover 0, Sharpe 0.0111, end 2026-09-25 | `static_18(panel, with_costs=True)` | mean NextRet on every date with at least one asset | `g["Return"] -= COST_PER_SIDE` on **every** row | summary row 4; fair_comparison row `18,True,8373.71,...711` |
| 711 obs, +143.21%, DD −48.38%, turnover 0, Sharpe 1.043 | `static_18(..., with_costs=False)` | same | none | fair_comparison only; FinalEquity 24321.16 |

Comment on `static_18` says "One initial allocation cost only". The
code subtracts `COST_PER_SIDE` (0.0015) from all 711 returns. Audit 003
identity: `(1-0.0015)**711 ≈ 0.344`; 24321.16 × 0.344 ≈ 8373. Not
recomputed in this ledger; mechanism re-verified in the file.

`dynamic_universe_final_comparison.csv` "Static 18 equal-weight" matches
the 487-day `simulate(k=18)` equity 18715.35, with `AvgDailyTurnover`
stored as 0.0. `static_equal_weight()` in `dynamic_universe_final_comparison.py`
uses `count==len(ASSETS)` and subtracts cost on the **first** row only,
then hardcodes turnover 0.

This ledger attributes rows to functions. It does not elect a true
static benchmark. Both 487 and 711 remain invalid as buy & hold, per
audits 002–004.

## 4. Feature sets

| Location | Names | Count |
| --- | --- | --- |
| `model_engine.py` live | Returns, SMA_10, SMA_50, RSI | 4 |
| `portfolio_backtest.py`, `portfolio_stop_sensitivity.py`, `portfolio_target_horizon_analysis*.py` via `MODEL_FEATURES` | Return_1d, Return_5d, SMA_10, SMA_50, SMA_ratio, RSI | 6 |
| `portfolio_target_horizon_ml_screen.py` | Return_1d, Return_5d, SMA_10, SMA_50, SMA_ratio, RSI | 6 |
| `features.py` `create_features` | return_1d, return_5d, volatility_7d, sma_10, sma_50, sma_ratio, rsi_14, volume_change, plus target | 8 + target |

VERIFIED: live scout generation and the portfolio_backtest CSVs do not
share a feature list in the current tree.

## 5. `auto_adjust`

VERIFIED, current Python tree:

| Setting | Files |
| --- | --- |
| `auto_adjust=True` (1) | `portfolio_target_horizon_ml_screen.py` |
| `auto_adjust=False` (7) | `dynamic_universe_screen.py`, `dynamic_universe_fair_comparison.py`, `dynamic_universe_final_comparison.py`, `portfolio_stop_sensitivity.py`, `portfolio_buy_hold_period_benchmark.py`, `portfolio_backtest.py`, `backtest_oos.py` |
| implicit, no keyword (4) | `model_engine.py` `Ticker.history(period="2y")`; `main.py` `yf.download` ticker 1mo; `main.py` `yf.download` SPY 1y; `data_loader.py` `yf.download` period 4y |

Live scout uses the implicit `history()` default. Persisted backtests
use explicit `False`, except the missing horizon-screen artefacts which
would have used `True`.

## 6. Cost constants in current scripts

| File | Fee | Slippage | Combined |
| --- | --- | --- | --- |
| `config.py` (live config module) | 0.001 | (none declared) | 0.001 |
| `backtest_oos.py` | 0.001 | 0.0005 | 0.0015 per side |
| `portfolio_backtest.py` | 0.001 | 0.0005 | 0.0015 per side |
| `portfolio_stop_sensitivity.py` | 0.001 | 0.0005 | 0.0015 |
| `portfolio_buy_hold_period_benchmark.py` | 0.001 | 0.0005 | 0.0015 |
| `dynamic_universe_*.py` (three files) | 0.001 | 0.0005 | `COST_PER_SIDE = 0.0015` |

UNKNOWN whether every persisted CSV was produced with these numbers.
The current scripts contain them.

## 7. `pct_change` and `features.py` dropna

VERIFIED: 31 `pct_change()` calls in 15 Python files, none with
`fill_method=`.

`features.py` `create_features`:

1. Builds returns, SMAs, RSI, volume_change.
2. Sets `target = (Close.shift(-1) > Close).astype(int)`.
3. Calls `df.dropna()` on the whole frame.

Effects, INFERRED from that code, not measured on a snapshot:

- The last bar always loses the target and is dropped.
- Any NaN in Volume (or in an intermediate column) drops the entire
  row, including feature rows that live `model_engine.py` may keep if
  it only dropna-s the live feature subset.

Live `model_engine.py` dropna is on the 4 FEATURES plus the train
target construction in that file, not on `features.py`. The two paths
are not the same function. Treat as a V1 live/backtest non-comparability
axis. Not quantified here.

## 8. What this ledger does not do

It does not choose a static benchmark.
It does not say which universe is better.
It does not say V1 has or lacks edge.
It does not admit any CSV as confirmatory evidence.
It does not start Phase 0A.
