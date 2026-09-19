import math
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


# ============================================================
# CONFIG
# ============================================================

INITIAL_CAPITAL = 10_000.0

LONG_THRESHOLD = 0.55
HIGH_CONVICTION_THRESHOLD = 0.60
EXIT_THRESHOLD = 0.45

MAX_POSITION_55 = 0.30
MAX_POSITION_60 = 0.40
MAX_NEW_POSITIONS_PER_SIGNAL_DATE = 5

STOP_ATR_MULTIPLIER = 2.0
TRAILING_ATR_MULTIPLIER = 2.5

FEE_RATE = 0.001
SLIPPAGE_RATE = 0.0005

ATR_PERIOD = 14

MIN_TRAIN_SIZE = 120
STEP_SIZE = 20

LOOKBACK_PERIOD = "2y"

ASSETS = [
    "BTC-USD",
    "ETH-USD",
    "NVDA",
    "AMD",
    "MSTR",
    "COIN",
    "TSM",
    "PLTR",
    "ARM",
    "SMCI",
    "TSLA",
    "META",
    "AMZN",
    "GOOGL",
    "AAPL",
    "MSFT",
    "QQQ",
    "GLD",
]

MODEL_FEATURES = [
    "Return_1d",
    "Return_5d",
    "SMA_10",
    "SMA_50",
    "SMA_ratio",
    "RSI",
]


# ============================================================
# DATA DOWNLOAD
# ============================================================

def download_data(ticker):
    print(f"Downloading {ticker}...")

    df = yf.download(
        ticker,
        period=LOOKBACK_PERIOD,
        interval="1d",
        progress=False,
        auto_adjust=False,
    )

    if df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close"]

    if not all(column in df.columns for column in required):
        return pd.DataFrame()

    df = df[required].copy()

    df = df.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    df.dropna(inplace=True)

    if isinstance(df.index, pd.DatetimeIndex):
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

    df.index = pd.to_datetime(df.index)

    df = df[
        ~df.index.duplicated(keep="last")
    ]

    return df


# ============================================================
# FEATURES
# ============================================================

def calculate_features(df):
    data = df.copy()

    data["Return_1d"] = (
        data["Close"].pct_change(1)
    )

    data["Return_5d"] = (
        data["Close"].pct_change(5)
    )

    data["SMA_10"] = (
        data["Close"]
        .rolling(10)
        .mean()
    )

    data["SMA_50"] = (
        data["Close"]
        .rolling(50)
        .mean()
    )

    data["SMA_ratio"] = (
        data["SMA_10"]
        / data["SMA_50"]
    )

    delta = data["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = (
        gain
        .rolling(14)
        .mean()
    )

    avg_loss = (
        loss
        .rolling(14)
        .mean()
    )

    rs = (
        avg_gain
        / avg_loss.replace(
            0,
            np.nan,
        )
    )

    data["RSI"] = (
        100
        - (
            100
            / (1 + rs)
        )
    )

    # --------------------------------------------------------
    # ATR
    # --------------------------------------------------------

    previous_close = (
        data["Close"].shift(1)
    )

    tr1 = (
        data["High"]
        - data["Low"]
    )

    tr2 = (
        data["High"]
        - previous_close
    ).abs()

    tr3 = (
        data["Low"]
        - previous_close
    ).abs()

    data["TR"] = pd.concat(
        [
            tr1,
            tr2,
            tr3,
        ],
        axis=1,
    ).max(axis=1)

    data["ATR"] = (
        data["TR"]
        .rolling(ATR_PERIOD)
        .mean()
    )

    # --------------------------------------------------------
    # Target: next day's close is higher than today's close.
    # The final row has no target and is removed later.
    # --------------------------------------------------------

    next_close = (
        data["Close"].shift(-1)
    )

    data["Target"] = np.where(
        next_close.notna(),
        (
            next_close
            > data["Close"]
        ).astype(int),
        np.nan,
    )

    return data


# ============================================================
# MODELS
# ============================================================

def train_models(train):
    from sklearn.ensemble import RandomForestClassifier
    from xgboost import XGBClassifier
    from lightgbm import LGBMClassifier

    X = train[
        MODEL_FEATURES
    ]

    y = train[
        "Target"
    ].astype(int)

    models = [
        XGBClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            eval_metric="logloss",
            random_state=42,
        ),
        LGBMClassifier(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            verbosity=-1,
            random_state=42,
        ),
        RandomForestClassifier(
            n_estimators=300,
            max_depth=6,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
        ),
    ]

    for model in models:
        model.fit(X, y)

    return models


def predict_probability(models, row):
    X = row[
        MODEL_FEATURES
    ].to_frame().T

    probabilities = []

    for model in models:
        probabilities.append(
            model.predict_proba(X)[0, 1]
        )

    return float(
        np.mean(probabilities)
    )


# ============================================================
# WALK-FORWARD OOS
# ============================================================

def generate_oos_predictions(df):
    data = calculate_features(df)

    data = data.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    data = data.dropna(
        subset=MODEL_FEATURES
        + [
            "ATR",
            "Target",
            "Open",
            "High",
            "Low",
            "Close",
        ]
    ).copy()

    if len(data) <= MIN_TRAIN_SIZE:
        return pd.DataFrame()

    predictions = []

    test_start = MIN_TRAIN_SIZE

    while test_start < len(data):
        test_end = min(
            test_start + STEP_SIZE,
            len(data),
        )

        train = data.iloc[
            :test_start
        ]

        test = data.iloc[
            test_start:test_end
        ]

        models = train_models(train)

        for index, row in test.iterrows():
            probability = predict_probability(
                models,
                row,
            )

            predictions.append(
                {
                    "Date": pd.Timestamp(index),
                    "Open": float(row["Open"]),
                    "High": float(row["High"]),
                    "Low": float(row["Low"]),
                    "Close": float(row["Close"]),
                    "ATR": float(row["ATR"]),
                    "Probability": probability,
                }
            )

        test_start = test_end

    result = pd.DataFrame(
        predictions
    )

    if result.empty:
        return result

    result = (
        result
        .sort_values("Date")
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Signals used by the portfolio engine refer to the
    # previous available bar.
    # --------------------------------------------------------

    result["PreviousProbability"] = (
        result["Probability"].shift(1)
    )

    result["PreviousATR"] = (
        result["ATR"].shift(1)
    )

    # --------------------------------------------------------
    # Each asset uses its own next available trading date.
    # --------------------------------------------------------

    result["NextAvailableDate"] = (
        result["Date"].shift(-1)
    )

    return result


# ============================================================
# PORTFOLIO VALUATION
# ============================================================

def mark_to_market(
    cash,
    positions,
    last_prices,
):
    equity = float(cash)

    for ticker, position in positions.items():
        price = last_prices.get(ticker)

        if price is None:
            continue

        equity += (
            position["shares"]
            * price
        )

    return float(equity)


# ============================================================
# CLOSE POSITION
# ============================================================

def close_position(
    ticker,
    position,
    exit_date,
    raw_exit_price,
    reason,
    cash,
    trades,
):
    execution_price = (
        raw_exit_price
        * (1 - SLIPPAGE_RATE)
    )

    shares = position["shares"]

    gross_value = (
        shares
        * execution_price
    )

    exit_fee = (
        gross_value
        * FEE_RATE
    )

    net_value = (
        gross_value
        - exit_fee
    )

    cash += net_value

    pnl = (
        net_value
        - position["entry_cost"]
    )

    trade_return = (
        pnl
        / position["entry_cost"]
    )

    trades.append(
        {
            "Ticker": ticker,
            "EntryDate": position["entry_date"],
            "ExitDate": exit_date,
            "EntryPrice": position["entry_price"],
            "ExitPrice": execution_price,
            "Shares": shares,
            "EntryCost": position["entry_cost"],
            "PnL": pnl,
            "Return": trade_return,
            "Reason": reason,
        }
    )

    return cash


# ============================================================
# LEDGER CHECK
# ============================================================

def check_cash_ledger(
    cash,
    positions,
    trades,
    current_date,
):
    invested_cost = sum(
        float(position["entry_cost"])
        for position in positions.values()
    )

    realized_pnl = sum(
        float(trade["PnL"])
        for trade in trades
    )

    ledger_value = (
        cash
        + invested_cost
        - realized_pnl
    )

    if cash < -0.01:
        raise RuntimeError(
            "CASH CONSISTENCY ERROR | "
            f"date={current_date} | "
            f"cash={cash:.2f} | "
            f"invested_cost={invested_cost:.2f} | "
            f"realized_pnl={realized_pnl:.2f} | "
            f"ledger_value={ledger_value:.2f} | "
            f"positions={list(positions.keys())}"
        )

    if not np.isclose(
        ledger_value,
        INITIAL_CAPITAL,
        rtol=0.0,
        atol=0.05,
    ):
        raise RuntimeError(
            "LEDGER CONSISTENCY ERROR | "
            f"date={current_date} | "
            f"cash={cash:.2f} | "
            f"invested_cost={invested_cost:.2f} | "
            f"realized_pnl={realized_pnl:.2f} | "
            f"ledger_value={ledger_value:.2f} | "
            f"expected={INITIAL_CAPITAL:.2f} | "
            f"positions={list(positions.keys())}"
        )


# ============================================================
# PORTFOLIO ENGINE
# ============================================================

def run_portfolio_backtest(all_predictions):
    # --------------------------------------------------------
    # Prepare asset data.
    # --------------------------------------------------------

    data_by_asset = {}
    all_dates = set()

    for ticker, df in all_predictions.items():
        clean = df.copy()

        clean["Date"] = pd.to_datetime(
            clean["Date"]
        )

        clean = (
            clean
            .sort_values("Date")
            .reset_index(drop=True)
        )

        data_by_asset[ticker] = clean

        all_dates.update(
            clean["Date"].tolist()
        )

    all_dates = sorted(all_dates)

    if not all_dates:
        raise RuntimeError(
            "No dates available for portfolio backtest."
        )

    # --------------------------------------------------------
    # Direct bar lookup.
    # --------------------------------------------------------

    bar_map = {}

    for ticker, df in data_by_asset.items():
        for _, row in df.iterrows():
            date = pd.Timestamp(
                row["Date"]
            )

            bar_map[
                (ticker, date)
            ] = row

    # --------------------------------------------------------
    # Entry events.
    #
    # Signal is generated on one bar.
    # Entry occurs on the asset's next available bar.
    # Candidates are ranked by probability on each signal
    # date, with a maximum of five new signals.
    # --------------------------------------------------------

    entry_events = {}

    for signal_date in all_dates:
        candidates = []

        for ticker, df in data_by_asset.items():
            rows = df[
                df["Date"] == signal_date
            ]

            if rows.empty:
                continue

            row = rows.iloc[0]

            probability = float(
                row["Probability"]
            )

            next_date = row[
                "NextAvailableDate"
            ]

            if pd.isna(next_date):
                continue

            if probability < LONG_THRESHOLD:
                continue

            candidates.append(
                {
                    "Ticker": ticker,
                    "Probability": probability,
                    "SignalDate": signal_date,
                    "ExecutionDate": pd.Timestamp(
                        next_date
                    ),
                    "ATR": float(row["ATR"]),
                }
            )

        candidates.sort(
            key=lambda item: item["Probability"],
            reverse=True,
        )

        candidates = candidates[
            :MAX_NEW_POSITIONS_PER_SIGNAL_DATE
        ]

        for candidate in candidates:
            execution_date = candidate[
                "ExecutionDate"
            ]

            entry_events.setdefault(
                execution_date,
                [],
            ).append(candidate)

    # --------------------------------------------------------
    # Portfolio state.
    # --------------------------------------------------------

    cash = INITIAL_CAPITAL
    positions = {}
    trades = []
    last_prices = {}
    equity_curve = []

    # --------------------------------------------------------
    # Explicit initial equity point.
    # --------------------------------------------------------

    first_date = pd.Timestamp(
        all_dates[0]
    )

    initial_record_date = (
        first_date
        - pd.Timedelta(seconds=1)
    )

    equity_curve.append(
        {
            "Date": initial_record_date,
            "Equity": INITIAL_CAPITAL,
            "Cash": INITIAL_CAPITAL,
            "OpenPositions": 0,
            "Phase": "INITIAL",
        }
    )

    # --------------------------------------------------------
    # Main event-driven loop.
    # --------------------------------------------------------

    for current_date in all_dates:
        current_date = pd.Timestamp(
            current_date
        )

        exited_today = set()

        # ----------------------------------------------------
        # Update latest available prices before valuation.
        # ----------------------------------------------------

        for ticker in data_by_asset:
            row = bar_map.get(
                (ticker, current_date)
            )

            if row is not None:
                last_prices[ticker] = float(
                    row["Close"]
                )

        # ----------------------------------------------------
        # 1. ML EXITS AT OPEN
        #
        # Use the previous available probability, so today's
        # close is never used to decide today's open exit.
        # ----------------------------------------------------

        for ticker in list(positions.keys()):
            row = bar_map.get(
                (ticker, current_date)
            )

            if row is None:
                continue

            previous_probability = (
                row["PreviousProbability"]
            )

            if pd.isna(previous_probability):
                continue

            if (
                float(previous_probability)
                < EXIT_THRESHOLD
            ):
                position = positions[ticker]

                cash = close_position(
                    ticker=ticker,
                    position=position,
                    exit_date=current_date,
                    raw_exit_price=float(
                        row["Open"]
                    ),
                    reason="ML_EXIT",
                    cash=cash,
                    trades=trades,
                )

                del positions[ticker]
                exited_today.add(ticker)

        check_cash_ledger(
            cash,
            positions,
            trades,
            current_date,
        )

        # ----------------------------------------------------
        # 2. ENTRIES AT OPEN
        # ----------------------------------------------------

        todays_entries = entry_events.get(
            current_date,
            [],
        )

        todays_entries = sorted(
            todays_entries,
            key=lambda item: item["Probability"],
            reverse=True,
        )

        entries_executed = 0

        for event in todays_entries:
            if (
                entries_executed
                >= MAX_NEW_POSITIONS_PER_SIGNAL_DATE
            ):
                break

            ticker = event["Ticker"]

            if ticker in exited_today:
                continue

            if ticker in positions:
                continue

            row = bar_map.get(
                (ticker, current_date)
            )

            if row is None:
                continue

            portfolio_equity = mark_to_market(
                cash,
                positions,
                last_prices,
            )

            probability = float(
                event["Probability"]
            )

            if (
                probability
                >= HIGH_CONVICTION_THRESHOLD
            ):
                allocation_pct = MAX_POSITION_60
            else:
                allocation_pct = MAX_POSITION_55

            target_value = (
                portfolio_equity
                * allocation_pct
            )

            allocation = min(
                target_value,
                cash,
            )

            if allocation <= 0:
                continue

            raw_open = float(
                row["Open"]
            )

            execution_price = (
                raw_open
                * (1 + SLIPPAGE_RATE)
            )

            entry_fee = (
                allocation
                * FEE_RATE
            )

            net_position_value = (
                allocation
                - entry_fee
            )

            shares = (
                net_position_value
                / execution_price
            )

            cash -= allocation

            # Peak starts at entry price. Today's high is not
            # used here because the position did not exist
            # before today's open.
            positions[ticker] = {
                "entry_date": current_date,
                "entry_price": execution_price,
                "shares": shares,
                "entry_cost": allocation,
                "entry_atr": float(event["ATR"]),
                "peak_price": execution_price,
            }

            entries_executed += 1

            check_cash_ledger(
                cash,
                positions,
                trades,
                current_date,
            )

        # ----------------------------------------------------
        # 3. INTRADAY STOPS
        #
        # ATR comes from the previous available bar.
        # Entry-day positions are eligible because the entry
        # occurred at today's open.
        # ----------------------------------------------------

        for ticker in list(positions.keys()):
            row = bar_map.get(
                (ticker, current_date)
            )

            if row is None:
                continue

            position = positions[ticker]

            entry_price = float(
                position["entry_price"]
            )

            peak_before_bar = float(
                position["peak_price"]
            )

            previous_atr = row["PreviousATR"]

            if pd.isna(previous_atr):
                atr = float(
                    position["entry_atr"]
                )
            else:
                atr = float(
                    previous_atr
                )

            fixed_stop = (
                entry_price
                - (
                    STOP_ATR_MULTIPLIER
                    * atr
                )
            )

            trailing_stop = (
                peak_before_bar
                - (
                    TRAILING_ATR_MULTIPLIER
                    * atr
                )
            )

            effective_stop = max(
                fixed_stop,
                trailing_stop,
            )

            current_open = float(
                row["Open"]
            )

            current_low = float(
                row["Low"]
            )

            exit_price = None
            reason = None

            # ------------------------------------------------
            # Gap through stop.
            # ------------------------------------------------

            if current_open <= effective_stop:
                exit_price = current_open
                reason = "STOP_GAP"

            # ------------------------------------------------
            # Intraday stop.
            # ------------------------------------------------

            elif current_low <= effective_stop:
                exit_price = effective_stop
                reason = "ATR_STOP"

            if exit_price is not None:
                cash = close_position(
                    ticker=ticker,
                    position=position,
                    exit_date=current_date,
                    raw_exit_price=exit_price,
                    reason=reason,
                    cash=cash,
                    trades=trades,
                )

                del positions[ticker]

                exited_today.add(ticker)

                continue

            # ------------------------------------------------
            # Update peak only AFTER the risk check.
            #
            # Today's High is allowed here because the position
            # survived the stop check and the new peak is used
            # only by future bars.
            # ------------------------------------------------

            current_high = float(
                row["High"]
            )

            position["peak_price"] = max(
                peak_before_bar,
                current_high,
            )

        check_cash_ledger(
            cash,
            positions,
            trades,
            current_date,
        )

        # ----------------------------------------------------
        # 4. END-OF-DAY MARK TO MARKET
        # ----------------------------------------------------

        equity = mark_to_market(
            cash,
            positions,
            last_prices,
        )

        equity_curve.append(
            {
                "Date": current_date,
                "Equity": equity,
                "Cash": cash,
                "OpenPositions": len(positions),
                "Phase": "EOD",
            }
        )

    # ========================================================
    # FINAL LIQUIDATION
    # ========================================================

    final_test_date = pd.Timestamp(
        all_dates[-1]
    )

    for ticker in list(positions.keys()):
        position = positions[ticker]

        df = data_by_asset[ticker]

        if df.empty:
            continue

        last_row = df.iloc[-1]

        final_date = pd.Timestamp(
            last_row["Date"]
        )

        final_close = float(
            last_row["Close"]
        )

        cash = close_position(
            ticker=ticker,
            position=position,
            exit_date=final_date,
            raw_exit_price=final_close,
            reason="END_OF_TEST",
            cash=cash,
            trades=trades,
        )

        del positions[ticker]

    final_equity = float(cash)

    # --------------------------------------------------------
    # Replace the final EOD point with the actual post-
    # liquidation portfolio value.
    # --------------------------------------------------------

    if equity_curve:
        equity_curve[-1] = {
            "Date": final_test_date,
            "Equity": final_equity,
            "Cash": final_equity,
            "OpenPositions": 0,
            "Phase": "FINAL_LIQUIDATED",
        }

    # ========================================================
    # SAFETY INVARIANTS
    # ========================================================

    if final_equity < 0:
        raise RuntimeError(
            "FATAL: final equity is negative."
        )

    if not np.isfinite(final_equity):
        raise RuntimeError(
            "FATAL: final equity is not finite."
        )

    if positions:
        raise RuntimeError(
            "FATAL: positions remain after final liquidation."
        )

    check_cash_ledger(
        cash,
        positions,
        trades,
        final_test_date,
    )

    # ========================================================
    # DATAFRAMES
    # ========================================================

    equity_df = pd.DataFrame(
        equity_curve
    )

    trades_df = pd.DataFrame(
        trades
    )

    equity_df["Date"] = pd.to_datetime(
        equity_df["Date"]
    )

    equity_df = (
        equity_df
        .sort_values("Date")
        .reset_index(drop=True)
    )

    # ========================================================
    # METRICS
    # ========================================================

    if equity_df.empty:
        max_drawdown = 0.0
        sharpe = 0.0
    else:
        # ----------------------------------------------------
        # EOD equity only.
        # ----------------------------------------------------

        eod_equity = (
            equity_df.loc[
                equity_df["Phase"].isin(
                    [
                        "EOD",
                        "FINAL_LIQUIDATED",
                    ]
                ),
                "Equity",
            ]
            .astype(float)
            .reset_index(drop=True)
        )

        # ----------------------------------------------------
        # Include initial capital explicitly in drawdown.
        # ----------------------------------------------------

        drawdown_series = pd.concat(
            [
                pd.Series(
                    [INITIAL_CAPITAL]
                ),
                eod_equity,
            ],
            ignore_index=True,
        )

        running_max = (
            drawdown_series
            .cummax()
        )

        drawdowns = (
            drawdown_series
            / running_max
        ) - 1.0

        max_drawdown = float(
            drawdowns.min()
        )

        # ----------------------------------------------------
        # Sharpe uses actual EOD-to-EOD returns only.
        # ----------------------------------------------------

        returns = (
            eod_equity
            .pct_change()
            .replace(
                [np.inf, -np.inf],
                np.nan,
            )
            .dropna()
        )

        if (
            len(returns) > 1
            and returns.std(ddof=1) > 0
        ):
            sharpe = float(
                (
                    returns.mean()
                    / returns.std(ddof=1)
                )
                * math.sqrt(252)
            )
        else:
            sharpe = 0.0

    # --------------------------------------------------------
    # Total return.
    # --------------------------------------------------------

    total_return = (
        final_equity
        / INITIAL_CAPITAL
    ) - 1.0

    # ========================================================
    # TRADE STATISTICS
    # ========================================================

    trades_count = len(trades_df)

    if trades_count > 0:
        wins = (
            trades_df["PnL"] > 0
        ).sum()

        win_rate = (
            wins
            / trades_count
        )

        gross_profit = (
            trades_df.loc[
                trades_df["PnL"] > 0,
                "PnL",
            ].sum()
        )

        gross_loss = abs(
            trades_df.loc[
                trades_df["PnL"] < 0,
                "PnL",
            ].sum()
        )

        if gross_loss > 0:
            profit_factor = (
                gross_profit
                / gross_loss
            )
        else:
            profit_factor = np.inf
    else:
        win_rate = 0.0
        profit_factor = 0.0

    # ========================================================
    # FINAL CONSISTENCY CHECK
    # ========================================================

    if not np.isclose(
        final_equity,
        float(
            equity_df.iloc[-1]["Equity"]
        ),
        rtol=1e-10,
        atol=1e-8,
    ):
        raise RuntimeError(
            "FATAL: FinalEquity does not match "
            "the final equity curve value."
        )

    summary = {
        "InitialCapital": INITIAL_CAPITAL,
        "FinalEquity": final_equity,
        "TotalReturn": total_return,
        "MaxDrawdown": max_drawdown,
        "Sharpe": sharpe,
        "Trades": trades_count,
        "WinRate": win_rate,
        "ProfitFactor": profit_factor,
    }

    return (
        summary,
        equity_df,
        trades_df,
    )


# ============================================================
# MAIN
# ============================================================

def main():
    output_dir = Path(
        "portfolio_backtest_results"
    )

    output_dir.mkdir(
        exist_ok=True
    )

    all_predictions = {}

    print()
    print(
        "=================================================="
    )
    print(
        "GENERATING WALK-FORWARD OOS PREDICTIONS"
    )
    print(
        "=================================================="
    )
    print()

    # --------------------------------------------------------
    # Generate OOS predictions for every asset.
    # --------------------------------------------------------

    for ticker in ASSETS:
        try:
            df = download_data(ticker)

            if df.empty:
                print(
                    f"{ticker}: NO DATA"
                )
                continue

            predictions = (
                generate_oos_predictions(
                    df
                )
            )

            if predictions.empty:
                print(
                    f"{ticker}: NO OOS DATA"
                )
                continue

            all_predictions[ticker] = (
                predictions
            )

            predictions.to_csv(
                output_dir
                / f"{ticker}_predictions.csv",
                index=False,
            )

            print(
                f"{ticker}: "
                f"{len(predictions)} OOS rows"
            )

        except Exception as error:
            print(
                f"{ticker}: ERROR -> "
                f"{error}"
            )

    if not all_predictions:
        raise RuntimeError(
            "No OOS predictions generated."
        )

    print()
    print(
        "=================================================="
    )
    print(
        "RUNNING EVENT-DRIVEN PORTFOLIO BACKTEST"
    )
    print(
        "=================================================="
    )
    print()

    (
        summary,
        equity_df,
        trades_df,
    ) = run_portfolio_backtest(
        all_predictions
    )

    # --------------------------------------------------------
    # Save results.
    # --------------------------------------------------------

    equity_df.to_csv(
        output_dir
        / "portfolio_equity.csv",
        index=False,
    )

    trades_df.to_csv(
        output_dir
        / "portfolio_trades.csv",
        index=False,
    )

    pd.DataFrame(
        [summary]
    ).to_csv(
        output_dir
        / "portfolio_summary.csv",
        index=False,
    )

    # --------------------------------------------------------
    # Print results.
    # --------------------------------------------------------

    print()
    print(
        "=================================================="
    )
    print(
        "PORTFOLIO OOS BACKTEST COMPLETED"
    )
    print(
        "=================================================="
    )

    print(
        f"Initial capital : "
        f"€{summary['InitialCapital']:,.2f}"
    )

    print(
        f"Final equity    : "
        f"€{summary['FinalEquity']:,.2f}"
    )

    print(
        f"Total return    : "
        f"{summary['TotalReturn']:.2%}"
    )

    print(
        f"Max drawdown    : "
        f"{summary['MaxDrawdown']:.2%}"
    )

    print(
        f"Sharpe          : "
        f"{summary['Sharpe']:.2f}"
    )

    print(
        f"Trades          : "
        f"{summary['Trades']}"
    )

    print(
        f"Win rate        : "
        f"{summary['WinRate']:.2%}"
    )

    print(
        f"Profit factor   : "
        f"{summary['ProfitFactor']:.3f}"
    )

    print()
    print(
        "Results saved in:"
    )
    print(
        "portfolio_backtest_results/"
    )


if __name__ == "__main__":
    main()
