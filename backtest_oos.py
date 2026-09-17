import json
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
EXIT_THRESHOLD = 0.45

MAX_POSITION_60 = 0.40
MAX_POSITION_55 = 0.30

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


# ============================================================
# DATA
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

    for col in required:
        if col not in df.columns:
            return pd.DataFrame()

    df = df[required].copy()
    df.dropna(inplace=True)

    return df


# ============================================================
# FEATURES
# ============================================================

def calculate_features(df):
    data = df.copy()

    data["Return_1d"] = data["Close"].pct_change(1)
    data["Return_5d"] = data["Close"].pct_change(5)

    data["SMA_10"] = data["Close"].rolling(10).mean()
    data["SMA_50"] = data["Close"].rolling(50).mean()

    data["SMA_ratio"] = data["SMA_10"] / data["SMA_50"]

    delta = data["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    data["RSI"] = 100 - (100 / (1 + rs))

    # True Range / ATR
    prev_close = data["Close"].shift(1)

    tr1 = data["High"] - data["Low"]
    tr2 = (data["High"] - prev_close).abs()
    tr3 = (data["Low"] - prev_close).abs()

    data["TR"] = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    data["ATR"] = data["TR"].rolling(ATR_PERIOD).mean()

    data["Target"] = (
        data["Close"].shift(-1) > data["Close"]
    ).astype(float)

    return data


# ============================================================
# MODEL
# ============================================================

def train_model(train):
    from sklearn.ensemble import RandomForestClassifier
    from xgboost import XGBClassifier
    from lightgbm import LGBMClassifier

    features = [
        "Return_1d",
        "Return_5d",
        "SMA_10",
        "SMA_50",
        "SMA_ratio",
        "RSI",
    ]

    X = train[features]
    y = train["Target"].astype(int)

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

    return models, features


def predict(models, features, row):
    X = row[features].to_frame().T

    probabilities = []

    for model in models:
        probabilities.append(
            model.predict_proba(X)[0, 1]
        )

    return float(np.mean(probabilities))


# ============================================================
# WALK-FORWARD PREDICTIONS
# ============================================================

def generate_oos_predictions(df):
    data = calculate_features(df)

    data = data.replace([np.inf, -np.inf], np.nan)

    features = [
        "Return_1d",
        "Return_5d",
        "SMA_10",
        "SMA_50",
        "SMA_ratio",
        "RSI",
        "ATR",
    ]

    # Target is deliberately excluded from final prediction rows.
    train_features = features[:-1]

    data = data.dropna(
        subset=train_features + ["Target", "ATR"]
    ).copy()

    predictions = []

    test_start = MIN_TRAIN_SIZE

    while test_start < len(data):

        test_end = min(
            test_start + STEP_SIZE,
            len(data)
        )

        train = data.iloc[:test_start].copy()
        test = data.iloc[test_start:test_end].copy()

        models, model_features = train_model(train)

        for idx, row in test.iterrows():

            probability = predict(
                models,
                model_features,
                row
            )

            predictions.append({
                "Date": idx,
                "Close": float(row["Close"]),
                "ATR": float(row["ATR"]),
                "Probability": probability,
            })

        test_start = test_end

    return pd.DataFrame(predictions)


# ============================================================
# SINGLE ASSET BACKTEST
# ============================================================

def backtest_asset(predictions, ticker):

    if predictions.empty:
        return None, pd.DataFrame()

    cash = INITIAL_CAPITAL

    position = 0.0
    entry_price = None
    peak_price = None

    trades = []
    equity_curve = []

    for _, row in predictions.iterrows():

        date = row["Date"]
        close = row["Close"]
        atr = row["ATR"]
        probability = row["Probability"]

        # ----------------------------------------------------
        # EXISTING POSITION
        # ----------------------------------------------------

        if position > 0:

            peak_price = max(
                peak_price,
                close
            )

            stop_price = (
                entry_price
                - STOP_ATR_MULTIPLIER * atr
            )

            trailing_price = (
                peak_price
                - TRAILING_ATR_MULTIPLIER * atr
            )

            exit_reason = None

            if close <= stop_price:
                exit_reason = "STOP"

            elif close <= trailing_price:
                exit_reason = "TRAILING_STOP"

            elif probability < EXIT_THRESHOLD:
                exit_reason = "ML_EXIT"

            if exit_reason:

                execution_price = (
                    close * (1 - SLIPPAGE_RATE)
                )

                gross_value = (
                    position * execution_price
                )

                fee = gross_value * FEE_RATE

                cash += gross_value - fee

                pnl = (
                    execution_price - entry_price
                ) * position

                trades.append({
                    "Ticker": ticker,
                    "EntryDate": entry_date,
                    "ExitDate": date,
                    "EntryPrice": entry_price,
                    "ExitPrice": execution_price,
                    "Shares": position,
                    "PnL": pnl,
                    "Return": (
                        execution_price / entry_price
                    ) - 1,
                    "Reason": exit_reason,
                })

                position = 0.0
                entry_price = None
                peak_price = None

        # ----------------------------------------------------
        # NEW ENTRY
        # ----------------------------------------------------

        if position == 0 and probability >= LONG_THRESHOLD:

            if probability >= 0.60:
                allocation_pct = MAX_POSITION_60
            else:
                allocation_pct = MAX_POSITION_55

            allocation = min(
                cash,
                cash * allocation_pct
            )

            if allocation > 0:

                execution_price = (
                    close * (1 + SLIPPAGE_RATE)
                )

                fee = allocation * FEE_RATE

                position_value = (
                    allocation - fee
                )

                position = (
                    position_value / execution_price
                )

                cash -= allocation

                entry_price = execution_price
                entry_date = date
                peak_price = close

        # ----------------------------------------------------
        # EQUITY
        # ----------------------------------------------------

        equity = (
            cash
            + position * close
        )

        equity_curve.append({
            "Date": date,
            "Equity": equity,
            "Cash": cash,
            "PositionValue": position * close,
            "Probability": probability,
        })

    # --------------------------------------------------------
    # FORCE CLOSE AT END
    # --------------------------------------------------------

    if position > 0:

        last = predictions.iloc[-1]

        execution_price = (
            last["Close"] * (1 - SLIPPAGE_RATE)
        )

        gross_value = position * execution_price
        fee = gross_value * FEE_RATE

        cash += gross_value - fee

        pnl = (
            execution_price - entry_price
        ) * position

        trades.append({
            "Ticker": ticker,
            "EntryDate": entry_date,
            "ExitDate": last["Date"],
            "EntryPrice": entry_price,
            "ExitPrice": execution_price,
            "Shares": position,
            "PnL": pnl,
            "Return": (
                execution_price / entry_price
            ) - 1,
            "Reason": "END_OF_TEST",
        })

        position = 0

        equity_curve[-1]["Equity"] = cash

    equity_df = pd.DataFrame(equity_curve)
    trades_df = pd.DataFrame(trades)

    final_equity = (
        equity_df["Equity"].iloc[-1]
        if not equity_df.empty
        else INITIAL_CAPITAL
    )

    total_return = (
        final_equity / INITIAL_CAPITAL
    ) - 1

    if not equity_df.empty:

        running_max = (
            equity_df["Equity"]
            .cummax()
        )

        drawdown = (
            equity_df["Equity"] / running_max
        ) - 1

        max_drawdown = drawdown.min()

        daily_returns = (
            equity_df["Equity"]
            .pct_change()
            .dropna()
        )

        if daily_returns.std() > 0:
            sharpe = (
                daily_returns.mean()
                / daily_returns.std()
                * math.sqrt(252)
            )
        else:
            sharpe = 0.0

    else:
        max_drawdown = 0.0
        sharpe = 0.0

    trades_count = len(trades_df)

    if trades_count > 0:

        wins = (
            trades_df["PnL"] > 0
        ).sum()

        win_rate = wins / trades_count

        gross_profit = (
            trades_df.loc[
                trades_df["PnL"] > 0,
                "PnL"
            ].sum()
        )

        gross_loss = abs(
            trades_df.loc[
                trades_df["PnL"] < 0,
                "PnL"
            ].sum()
        )

        profit_factor = (
            gross_profit / gross_loss
            if gross_loss > 0
            else float("inf")
        )

    else:
        win_rate = 0.0
        profit_factor = 0.0

    result = {
        "Ticker": ticker,
        "InitialCapital": INITIAL_CAPITAL,
        "FinalEquity": final_equity,
        "TotalReturn": total_return,
        "MaxDrawdown": max_drawdown,
        "Sharpe": sharpe,
        "Trades": trades_count,
        "WinRate": win_rate,
        "ProfitFactor": profit_factor,
    }

    return result, trades_df


# ============================================================
# BUY & HOLD
# ============================================================

def calculate_buy_hold(df):

    if df.empty:
        return None

    data = calculate_features(df)

    data = data.dropna(
        subset=["Close"]
    )

    if data.empty:
        return None

    start_price = float(
        data["Close"].iloc[0]
    )

    end_price = float(
        data["Close"].iloc[-1]
    )

    return (
        end_price / start_price
    ) - 1


# ============================================================
# MAIN
# ============================================================

def main():

    results = []
    all_trades = []

    output_dir = Path("backtest_results")
    output_dir.mkdir(exist_ok=True)

    for ticker in ASSETS:

        try:

            df = download_data(ticker)

            if df.empty:
                print(f"{ticker}: no data")
                continue

            predictions = generate_oos_predictions(df)

            if predictions.empty:
                print(f"{ticker}: no OOS predictions")
                continue

            predictions.to_csv(
                output_dir / f"{ticker}_oos_predictions.csv",
                index=False,
            )

            result, trades = backtest_asset(
                predictions,
                ticker
            )

            if result is None:
                continue

            result["BuyHoldReturn"] = (
                calculate_buy_hold(df)
            )

            results.append(result)

            if not trades.empty:
                all_trades.append(trades)

            print(
                f"{ticker}: "
                f"{result['TotalReturn']:.2%} "
                f"| DD {result['MaxDrawdown']:.2%} "
                f"| Sharpe {result['Sharpe']:.2f} "
                f"| Trades {result['Trades']}"
            )

        except Exception as e:

            print(
                f"ERROR {ticker}: {e}"
            )

    # --------------------------------------------------------
    # SAVE RESULTS
    # --------------------------------------------------------

    results_df = pd.DataFrame(results)

    results_df.to_csv(
        output_dir / "backtest_summary.csv",
        index=False,
    )

    if all_trades:

        trades_df = pd.concat(
            all_trades,
            ignore_index=True
        )

        trades_df.to_csv(
            output_dir / "all_trades.csv",
            index=False,
        )

    # JSON summary
    summary = {
        "initial_capital": INITIAL_CAPITAL,
        "fee_rate": FEE_RATE,
        "slippage_rate": SLIPPAGE_RATE,
        "long_threshold": LONG_THRESHOLD,
        "exit_threshold": EXIT_THRESHOLD,
        "stop_atr_multiplier": STOP_ATR_MULTIPLIER,
        "trailing_atr_multiplier": TRAILING_ATR_MULTIPLIER,
        "assets_tested": len(results),
    }

    if not results_df.empty:

        summary["average_return"] = float(
            results_df["TotalReturn"].mean()
        )

        summary["median_return"] = float(
            results_df["TotalReturn"].median()
        )

        summary["average_max_drawdown"] = float(
            results_df["MaxDrawdown"].mean()
        )

        summary["average_sharpe"] = float(
            results_df["Sharpe"].mean()
        )

    with open(
        output_dir / "backtest_summary.json",
        "w",
    ) as f:

        json.dump(
            summary,
            f,
            indent=4,
        )

    print("\n===================================")
    print("BACKTEST COMPLETED")
    print("===================================")

    print(
        f"Assets tested: {len(results)}"
    )

    if not results_df.empty:

        print(
            f"Average return: "
            f"{results_df['TotalReturn'].mean():.2%}"
        )

        print(
            f"Median return: "
            f"{results_df['TotalReturn'].median():.2%}"
        )

        print(
            f"Average max DD: "
            f"{results_df['MaxDrawdown'].mean():.2%}"
        )

        print(
            f"Average Sharpe: "
            f"{results_df['Sharpe'].mean():.2f}"
        )


if __name__ == "__main__":
    main()
